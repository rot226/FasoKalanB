from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal

from django.db import models
from django.db.models import F, Q, Sum
from django.utils import timezone


class Facture(models.Model):
    """Facture client servant de base aux calculs de recouvrement."""

    class Statut(models.TextChoices):
        BROUILLON = "brouillon", "Brouillon"
        EMISE = "emise", "Émise"
        PARTIELLEMENT_REGLEE = "partiellement_reglee", "Partiellement réglée"
        REGLEE = "reglee", "Réglée"
        ANNULEE = "annulee", "Annulée"

    reference = models.CharField(max_length=40, unique=True)
    client_nom = models.CharField(max_length=255)
    date_emission = models.DateField()
    date_echeance = models.DateField()
    montant_ttc = models.DecimalField(max_digits=12, decimal_places=2)
    statut = models.CharField(max_length=32, choices=Statut.choices, default=Statut.EMISE)

    class Meta:
        ordering = ["date_echeance", "reference"]

    def __str__(self) -> str:
        return f"{self.reference} - {self.client_nom}"

    @property
    def total_encaisse(self) -> Decimal:
        return self.paiements.aggregate(total=Sum("montant"))["total"] or Decimal("0")

    @property
    def reste_a_recouvrer(self) -> Decimal:
        reste = self.montant_ttc - self.total_encaisse
        return max(reste, Decimal("0"))


class Paiement(models.Model):
    """Encaissement rattaché à une facture."""

    class Mode(models.TextChoices):
        ESPECES = "especes", "Espèces"
        VIREMENT = "virement", "Virement"
        CARTE = "carte", "Carte"
        MOBILE_MONEY = "mobile_money", "Mobile Money"

    facture = models.ForeignKey(Facture, related_name="paiements", on_delete=models.CASCADE)
    date_paiement = models.DateField()
    montant = models.DecimalField(max_digits=12, decimal_places=2)
    mode = models.CharField(max_length=32, choices=Mode.choices, default=Mode.VIREMENT)
    reference_operation = models.CharField(max_length=80, blank=True)

    class Meta:
        ordering = ["-date_paiement", "-id"]


@dataclass(frozen=True)
class AlerteRecouvrement:
    criticite: int
    date: timezone.datetime.date
    type_alerte: str
    facture_id: int
    facture_reference: str
    client_nom: str
    montant_restant: Decimal
    lien_traitement: str


class RecouvrementQuerySet(models.QuerySet):
    def actives(self) -> "RecouvrementQuerySet":
        return self.exclude(statut__in=[Facture.Statut.BROUILLON, Facture.Statut.ANNULEE])


class RecouvrementService:
    """Services métier pour KPIs et alertes de recouvrement."""

    @staticmethod
    def _base_queryset() -> RecouvrementQuerySet:
        return RecouvrementQuerySet(model=Facture, using=Facture.objects.db).actives()

    @classmethod
    def encaissements_du_mois(cls, reference_date=None) -> Decimal:
        reference_date = reference_date or timezone.localdate()
        debut_mois = reference_date.replace(day=1)
        total = Paiement.objects.filter(
            date_paiement__gte=debut_mois,
            date_paiement__lte=reference_date,
        ).aggregate(total=Sum("montant"))["total"]
        return total or Decimal("0")

    @classmethod
    def reste_a_recouvrer(cls) -> Decimal:
        total_factures = cls._base_queryset().aggregate(total=Sum("montant_ttc"))["total"] or Decimal("0")
        total_paiements = Paiement.objects.filter(
            facture__in=cls._base_queryset(),
        ).aggregate(total=Sum("montant"))["total"] or Decimal("0")
        return max(total_factures - total_paiements, Decimal("0"))

    @classmethod
    def top_retards(cls, limit=5):
        today = timezone.localdate()
        qs = cls._base_queryset().filter(date_echeance__lt=today).annotate(
            montant_regle=Sum("paiements__montant"),
            jours_retard=today - F("date_echeance"),
        )
        items = []
        for facture in qs:
            montant_regle = facture.montant_regle or Decimal("0")
            restant = max(facture.montant_ttc - montant_regle, Decimal("0"))
            if restant > 0:
                items.append((facture, restant))
        items.sort(key=lambda x: (x[0].date_echeance, -x[1]))
        return items[:limit]

    @classmethod
    def echeances_a_venir(cls, jours):
        today = timezone.localdate()
        date_limite = today + timedelta(days=jours)
        qs = cls._base_queryset().filter(
            date_echeance__gte=today,
            date_echeance__lte=date_limite,
        ).annotate(montant_regle=Sum("paiements__montant"))
        return [
            (facture, max(facture.montant_ttc - (facture.montant_regle or Decimal("0")), Decimal("0")))
            for facture in qs
            if max(facture.montant_ttc - (facture.montant_regle or Decimal("0")), Decimal("0")) > 0
        ]

    @classmethod
    def alertes(cls):
        today = timezone.localdate()
        alertes = []

        for facture, restant in cls.top_retards(limit=20):
            jours_de_retard = (today - facture.date_echeance).days
            criticite = 1 if jours_de_retard >= 30 else 2 if jours_de_retard >= 15 else 3
            alertes.append(
                AlerteRecouvrement(
                    criticite=criticite,
                    date=facture.date_echeance,
                    type_alerte="retard",
                    facture_id=facture.id,
                    facture_reference=facture.reference,
                    client_nom=facture.client_nom,
                    montant_restant=restant,
                    lien_traitement=f"/finance/factures/{facture.id}/recouvrer/",
                )
            )

        for horizon, criticite in ((7, 4), (15, 5)):
            for facture, restant in cls.echeances_a_venir(jours=horizon):
                alertes.append(
                    AlerteRecouvrement(
                        criticite=criticite,
                        date=facture.date_echeance,
                        type_alerte=f"echeance_{horizon}j",
                        facture_id=facture.id,
                        facture_reference=facture.reference,
                        client_nom=facture.client_nom,
                        montant_restant=restant,
                        lien_traitement=f"/finance/factures/{facture.id}/",
                    )
                )

        return sorted(alertes, key=lambda item: (item.criticite, item.date))
