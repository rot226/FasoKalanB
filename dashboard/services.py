from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Dict, Iterable, List, Optional

from django.apps import apps
from django.contrib.auth.models import Group
from django.db.models import Model, Q, QuerySet, Sum


@dataclass(frozen=True)
class DashboardWidget:
    title: str
    value: str
    link: str
    severity: str



ALERT_SEVERITY_ORDER = {
    "critique": 0,
    "elevee": 1,
    "moyenne": 2,
    "faible": 3,
}


def _build_default_alerts() -> List[Dict[str, object]]:
    return [
        {
            "title": "Paiements en retard",
            "severity": "critique",
            "created_at": datetime(2026, 5, 4, 9, 30),
            "created_at_label": "04/05/2026 09:30",
            "scope": "Finance",
            "link": "/finance/",
        },
        {
            "title": "Dossiers élèves incomplets",
            "severity": "elevee",
            "created_at": datetime(2026, 5, 3, 14, 15),
            "created_at_label": "03/05/2026 14:15",
            "scope": "Élèves",
            "link": "/students/",
        },
        {
            "title": "Planning pédagogique à valider",
            "severity": "moyenne",
            "created_at": datetime(2026, 5, 2, 11, 0),
            "created_at_label": "02/05/2026 11:00",
            "scope": "Académique",
            "link": "/academics/",
        },
    ]


def _sort_alerts(alerts, sort_key: str, sort_dir: str):
    reverse = sort_dir == "desc"
    if sort_key == "date":
        return sorted(alerts, key=lambda alert: alert["created_at"], reverse=reverse)
    return sorted(
        alerts,
        key=lambda alert: (
            ALERT_SEVERITY_ORDER.get(alert["severity"], 99),
            alert["created_at"],
        ),
        reverse=reverse,
    )


def get_dashboard_alerts(sort_key: str = "criticite", sort_dir: str = "desc") -> Dict[str, object]:
    if sort_key not in {"criticite", "date"}:
        sort_key = "criticite"
    if sort_dir not in {"asc", "desc"}:
        sort_dir = "desc"

    alerts = _sort_alerts(_build_default_alerts(), sort_key, sort_dir)
    return {
        "alerts": alerts,
        "alerts_sort": sort_key,
        "alerts_dir": sort_dir,
    }

def _resolve_role(user) -> str:
    """Détermine le rôle principal utilisé pour l'affichage du dashboard."""
    role_order = ["admin", "scolarite", "finance", "direction"]

    if user.is_superuser or user.is_staff:
        return "admin"

    user_groups = set(user.groups.values_list("name", flat=True))
    for role in role_order:
        if role in user_groups:
            return role

    return "direction"


def _get_model(app_label: str, model_names: Iterable[str]) -> Optional[type[Model]]:
    """Retourne le premier modèle existant dans app_label parmi model_names."""
    for name in model_names:
        try:
            return apps.get_model(app_label, name)
        except LookupError:
            continue
    return None


def _base_queryset(model_class: Optional[type[Model]]) -> QuerySet:
    if model_class is None:
        return apps.get_model("auth", "User").objects.none()
    return model_class.objects.all()


def _resolve_scope_ids(user) -> set:
    """Résout les identifiants de périmètre autorisé (école) pour l'utilisateur connecté."""
    candidate_attrs = ["school_id", "ecole_id", "tenant_id"]
    scope_ids = {
        getattr(user, attr)
        for attr in candidate_attrs
        if getattr(user, attr, None) is not None
    }

    profile = getattr(user, "profile", None)
    if profile is not None:
        for attr in candidate_attrs:
            value = getattr(profile, attr, None)
            if value is not None:
                scope_ids.add(value)

    return scope_ids


def filter_queryset_by_scope(queryset: QuerySet, user) -> QuerySet:
    """Applique un filtrage de périmètre selon les colonnes school/ecole disponibles."""
    if user.is_superuser:
        return queryset

    model_fields = {f.name for f in queryset.model._meta.get_fields()}
    if "school" in model_fields:
        scope_ids = _resolve_scope_ids(user)
        return queryset.filter(school_id__in=scope_ids) if scope_ids else queryset.none()
    if "ecole" in model_fields:
        scope_ids = _resolve_scope_ids(user)
        return queryset.filter(ecole_id__in=scope_ids) if scope_ids else queryset.none()

    if "user" in model_fields:
        return queryset.filter(user=user)
    if "created_by" in model_fields:
        return queryset.filter(created_by=user)

    return queryset.none()


def aggregate_count(queryset: QuerySet) -> int:
    return queryset.count()


def aggregate_payment_amount(queryset: QuerySet) -> Decimal:
    """Agrège un montant total depuis amount ou montant."""
    model_fields = {f.name for f in queryset.model._meta.get_fields()}
    amount_field = "amount" if "amount" in model_fields else "montant" if "montant" in model_fields else None
    if not amount_field:
        return Decimal("0")
    return queryset.aggregate(total=Sum(amount_field)).get("total") or Decimal("0")


def aggregate_overdue_count(queryset: QuerySet, today: Optional[date] = None) -> int:
    """Compte les échéances dépassées sur due_date/date_echeance non payées."""
    today = today or date.today()
    model_fields = {f.name for f in queryset.model._meta.get_fields()}

    due_field = "due_date" if "due_date" in model_fields else "date_echeance" if "date_echeance" in model_fields else None
    status_field = "status" if "status" in model_fields else "statut" if "statut" in model_fields else None

    if not due_field:
        return 0

    q = Q(**{f"{due_field}__lt": today})
    if status_field:
        q &= ~Q(**{f"{status_field}__in": ["paid", "paye", "payé"]})
    return queryset.filter(q).count()


def aggregate_student_anomalies(queryset: QuerySet) -> int:
    """Compte les dossiers élèves incomplets via colonnes usuelles."""
    model_fields = {f.name for f in queryset.model._meta.get_fields()}
    anomaly_filters = Q()

    if "registration_number" in model_fields:
        anomaly_filters |= Q(registration_number__isnull=True) | Q(registration_number="")
    if "matricule" in model_fields:
        anomaly_filters |= Q(matricule__isnull=True) | Q(matricule="")
    if "birth_date" in model_fields:
        anomaly_filters |= Q(birth_date__isnull=True)

    if not anomaly_filters:
        return 0
    return queryset.filter(anomaly_filters).count()


def build_kpi_snapshot(user) -> Dict[str, object]:
    student_model = _get_model("students", ["Student", "Eleve", "Enrollment"])
    payment_model = _get_model("finance", ["Payment", "Paiement", "Invoice"])
    schedule_model = _get_model("academics", ["Schedule", "Echeance", "AcademicPeriod"])

    students_qs = filter_queryset_by_scope(_base_queryset(student_model), user)
    payments_qs = filter_queryset_by_scope(_base_queryset(payment_model), user)
    schedule_qs = filter_queryset_by_scope(_base_queryset(schedule_model), user)

    return {
        "effectifs": aggregate_count(students_qs),
        "paiements": aggregate_payment_amount(payments_qs),
        "echeances_en_retard": aggregate_overdue_count(schedule_qs),
        "anomalies_eleves": aggregate_student_anomalies(students_qs),
    }


def get_dashboard_context(user) -> Dict[str, object]:
    """Construit le contexte dynamique du dashboard selon le rôle."""
    role = _resolve_role(user)
    user_groups_count = Group.objects.count()
    kpi = build_kpi_snapshot(user)

    role_widgets: Dict[str, List[DashboardWidget]] = {
        "admin": [
            DashboardWidget("Effectifs", str(kpi["effectifs"]), "/students/", "info"),
            DashboardWidget("Paiements (total)", str(kpi["paiements"]), "/finance/", "warning"),
            DashboardWidget("Échéances en retard", str(kpi["echeances_en_retard"]), "/academics/", "primary"),
            DashboardWidget("Groupes utilisateurs", str(user_groups_count), "/admin/auth/group/", "secondary"),
        ],
        "scolarite": [
            DashboardWidget("Effectifs", str(kpi["effectifs"]), "/students/", "primary"),
            DashboardWidget("Anomalies dossiers", str(kpi["anomalies_eleves"]), "/students/", "danger"),
        ],
        "finance": [
            DashboardWidget("Paiements (total)", str(kpi["paiements"]), "/finance/", "warning"),
            DashboardWidget("Échéances en retard", str(kpi["echeances_en_retard"]), "/academics/", "secondary"),
        ],
        "direction": [
            DashboardWidget("Effectifs", str(kpi["effectifs"]), "/students/", "info"),
            DashboardWidget("Paiements (total)", str(kpi["paiements"]), "/finance/", "warning"),
            DashboardWidget("Anomalies dossiers", str(kpi["anomalies_eleves"]), "/students/", "danger"),
        ],
    }

    widgets = [asdict(widget) for widget in role_widgets.get(role, [])]
    return {"dashboard_role": role, "widgets": widgets, "kpi_snapshot": kpi}
