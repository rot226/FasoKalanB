from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Dict, Iterable, List, Optional

from django.apps import apps
from django.db.models import Model, Q, QuerySet, Sum

from students.models import (
    aggregate_new_students,
    aggregate_students_by_level_and_class,
    aggregate_total_students,
)


@dataclass(frozen=True)
class DashboardWidget:
    key: str
    label: str
    url: str


ALERT_SEVERITY_ORDER = {
    "critique": 0,
    "elevee": 1,
    "moyenne": 2,
    "faible": 3,
}

ROLE_WIDGETS: Dict[str, List[DashboardWidget]] = {
    "admin": [
        DashboardWidget("effectif_total", "Effectif total", "/students/"),
        DashboardWidget("nouveaux_inscrits", "Nouveaux inscrits", "/students/"),
        DashboardWidget("paiements_mois", "Paiements du mois", "/finance/"),
        DashboardWidget("impayes", "Impayés", "/finance/"),
        DashboardWidget("echeances_proches", "Échéances proches", "/academics/"),
        DashboardWidget("anomalies", "Anomalies", "/students/"),
    ],
    "scolarite": [
        DashboardWidget("effectif_total", "Effectif total", "/students/"),
        DashboardWidget("nouveaux_inscrits", "Nouveaux inscrits", "/students/"),
        DashboardWidget("echeances_proches", "Échéances proches", "/academics/"),
        DashboardWidget("anomalies", "Anomalies", "/students/"),
    ],
    "finance": [
        DashboardWidget("paiements_mois", "Paiements du mois", "/finance/"),
        DashboardWidget("impayes", "Impayés", "/finance/"),
        DashboardWidget("echeances_proches", "Échéances proches", "/academics/"),
    ],
    "direction": [
        DashboardWidget("effectif_total", "Effectif total", "/students/"),
        DashboardWidget("paiements_mois", "Paiements du mois", "/finance/"),
        DashboardWidget("impayes", "Impayés", "/finance/"),
        DashboardWidget("anomalies", "Anomalies", "/students/"),
    ],
}

DEFAULT_ROLE = "direction"


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
    role_order = ["admin", "scolarite", "finance", "direction"]

    if user.is_superuser or user.is_staff:
        return "admin"

    user_groups = set(user.groups.values_list("name", flat=True))
    for role in role_order:
        if role in user_groups:
            return role

    return DEFAULT_ROLE


def _get_model(app_label: str, model_names: Iterable[str]) -> Optional[type[Model]]:
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
    model_fields = {f.name for f in queryset.model._meta.get_fields()}
    amount_field = "amount" if "amount" in model_fields else "montant" if "montant" in model_fields else None
    if not amount_field:
        return Decimal("0")
    return queryset.aggregate(total=Sum(amount_field)).get("total") or Decimal("0")


def _resolve_date_field(model_fields: set[str], candidates: List[str]) -> Optional[str]:
    for name in candidates:
        if name in model_fields:
            return name
    return None


def _build_status_unpaid_q(model_fields: set[str]) -> Q:
    status_field = "status" if "status" in model_fields else "statut" if "statut" in model_fields else None
    if not status_field:
        return Q()
    return ~Q(**{f"{status_field}__in": ["paid", "paye", "payé"]})


def build_kpi_snapshot(user) -> Dict[str, object]:
    today = date.today()
    month_start = today.replace(day=1)
    next_month_start = (month_start + timedelta(days=32)).replace(day=1)
    near_deadline = today + timedelta(days=7)

    student_model = _get_model("students", ["Student", "Eleve", "Enrollment"])
    payment_model = _get_model("finance", ["Payment", "Paiement", "Invoice"])
    schedule_model = _get_model("academics", ["Schedule", "Echeance", "AcademicPeriod"])

    students_qs = filter_queryset_by_scope(_base_queryset(student_model), user)
    payments_qs = filter_queryset_by_scope(_base_queryset(payment_model), user)
    schedule_qs = filter_queryset_by_scope(_base_queryset(schedule_model), user)

    payment_fields = {f.name for f in payments_qs.model._meta.get_fields()}
    payment_date_field = _resolve_date_field(payment_fields, ["paid_at", "payment_date", "date_paiement", "created_at"])

    schedule_fields = {f.name for f in schedule_qs.model._meta.get_fields()}
    due_field = _resolve_date_field(schedule_fields, ["due_date", "date_echeance"])

    nouveaux_inscrits = aggregate_new_students(students_qs, today=today)
    repartition = aggregate_students_by_level_and_class(students_qs)

    paiements_mois = Decimal("0")
    if payment_date_field:
        paiements_mois = aggregate_payment_amount(
            payments_qs.filter(**{f"{payment_date_field}__gte": month_start, f"{payment_date_field}__lt": next_month_start})
        )

    impayes = 0
    echeances_proches = 0
    if due_field:
        unpaid_q = _build_status_unpaid_q(schedule_fields)
        impayes = schedule_qs.filter(Q(**{f"{due_field}__lt": today}) & unpaid_q).count()
        echeances_proches = schedule_qs.filter(
            Q(**{f"{due_field}__gte": today, f"{due_field}__lte": near_deadline}) & unpaid_q
        ).count()

    anomalies = aggregate_student_anomalies(students_qs)

    return {
        "effectif_total": aggregate_total_students(students_qs),
        "nouveaux_inscrits": nouveaux_inscrits,
        "paiements_mois": paiements_mois,
        "impayes": impayes,
        "echeances_proches": echeances_proches,
        "anomalies": anomalies,
        "repartition_niveaux": repartition["by_level"],
        "repartition_classes": repartition["by_class"],
    }


def aggregate_student_anomalies(queryset: QuerySet) -> int:
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


def _build_summary_cards(kpis: Dict[str, object], role: str) -> List[Dict[str, object]]:
    widgets = ROLE_WIDGETS.get(role, ROLE_WIDGETS[DEFAULT_ROLE])
    cards: List[Dict[str, object]] = []
    for widget in widgets:
        cards.append(
            {
                "key": widget.key,
                "label": widget.label,
                "value": str(kpis.get(widget.key, 0)),
                "link": widget.url,
            }
        )
    return cards


def build_dashboard_context(user) -> Dict[str, object]:
    role = _resolve_role(user)
    kpis = build_kpi_snapshot(user)
    alerts_payload = get_dashboard_alerts()

    quick_links = ROLE_WIDGETS.get(role, ROLE_WIDGETS[DEFAULT_ROLE])
    quick_links_payload = [{"label": item.label, "url": item.url} for item in quick_links]

    summary_cards = _build_summary_cards(kpis, role)
    charts_data = {
        "kpi_values": {
            key: float(value) if isinstance(value, Decimal) else value for key, value in kpis.items()
        },
        "alerts_by_severity": {
            "critique": len([a for a in alerts_payload["alerts"] if a["severity"] == "critique"]),
            "elevee": len([a for a in alerts_payload["alerts"] if a["severity"] == "elevee"]),
            "moyenne": len([a for a in alerts_payload["alerts"] if a["severity"] == "moyenne"]),
            "faible": len([a for a in alerts_payload["alerts"] if a["severity"] == "faible"]),
        },
    }

    empty_state = {
        "show": not summary_cards,
        "title": "Aucune donnée disponible",
        "description": "Les données de votre périmètre ne sont pas encore disponibles.",
    }

    return {
        "dashboard_role": role,
        "summary_cards": summary_cards,
        "alerts": alerts_payload["alerts"],
        "quick_links": quick_links_payload,
        "charts_data": charts_data,
        "empty_state": empty_state,
    }


def get_dashboard_context(user) -> Dict[str, object]:
    """Alias de compatibilité pour l'ancienne API de vue."""
    return build_dashboard_context(user)
