from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Dict, Iterable, List, Optional

from django.apps import apps
from django.core.cache import cache
from django.db.models import Count, F, Model, Q, QuerySet, Sum
from django.db.models.functions import TruncMonth

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
        DashboardWidget("effectif_total", "Effectifs", "/students/"),
        DashboardWidget("nouveaux_inscrits", "Nouveaux inscrits", "/students/"),
        DashboardWidget("groupes_utilisateurs", "Groupes utilisateurs", "/accounts/"),
        DashboardWidget("paiements_mois", "Paiements (total)", "/finance/"),
        DashboardWidget("impayes", "Échéances en retard", "/finance/"),
        DashboardWidget("echeances_proches", "Échéances proches", "/academics/"),
        DashboardWidget("anomalies", "Anomalies", "/students/"),
        DashboardWidget("classes_actives", "Classes actives", "/academics/"),
        DashboardWidget("sessions_actives", "Sessions actives", "/academics/"),
        DashboardWidget("evenements_imminents", "Évènements imminents", "/academics/"),
        DashboardWidget("anomalies_planification", "Anomalies planification", "/academics/"),
    ],
    "scolarite": [
        DashboardWidget("effectif_total", "Effectifs", "/students/"),
        DashboardWidget("nouveaux_inscrits", "Nouveaux inscrits", "/students/"),
        DashboardWidget("groupes_utilisateurs", "Groupes utilisateurs", "/accounts/"),
        DashboardWidget("echeances_proches", "Échéances proches", "/academics/"),
        DashboardWidget("anomalies", "Anomalies", "/students/"),
        DashboardWidget("classes_actives", "Classes actives", "/academics/"),
        DashboardWidget("sessions_actives", "Sessions actives", "/academics/"),
        DashboardWidget("evenements_imminents", "Évènements imminents", "/academics/"),
        DashboardWidget("anomalies_planification", "Anomalies planification", "/academics/"),
    ],
    "finance": [
        DashboardWidget("paiements_mois", "Paiements (total)", "/finance/"),
        DashboardWidget("impayes", "Échéances en retard", "/finance/"),
        DashboardWidget("echeances_proches", "Échéances proches", "/academics/"),
    ],
    "direction": [
        DashboardWidget("effectif_total", "Effectifs", "/students/"),
        DashboardWidget("paiements_mois", "Paiements (total)", "/finance/"),
        DashboardWidget("impayes", "Échéances en retard", "/finance/"),
        DashboardWidget("anomalies", "Anomalies", "/students/"),
        DashboardWidget("classes_actives", "Classes actives", "/academics/"),
        DashboardWidget("sessions_actives", "Sessions actives", "/academics/"),
        DashboardWidget("evenements_imminents", "Évènements imminents", "/academics/"),
        DashboardWidget("anomalies_planification", "Anomalies planification", "/academics/"),
    ],
}

DEFAULT_ROLE = "direction"
CACHE_TIMEOUT_SECONDS = 300
CRITICAL_CACHE_TIMEOUT_SECONDS = 120
SECONDARY_CACHE_TIMEOUT_SECONDS = 180
RECENT_ACTIVITIES_CACHE_TIMEOUT_SECONDS = 60


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




def _get_academics_models() -> Dict[str, Optional[type[Model]]]:
    return {
        "class": _get_model("academics", ["Class", "Classe", "AcademicClass"]),
        "session": _get_model("academics", ["Session", "AcademicSession", "CourseSession"]),
        "calendar": _get_model("academics", ["CalendarEvent", "AcademicEvent", "Event", "Calendrier"]),
        "result": _get_model("academics", ["Result", "ExamResult", "Grade", "Note"]),
    }


def _resolve_boolean_filter_fields(model_fields: set[str], candidates: list[str]) -> Optional[str]:
    for name in candidates:
        if name in model_fields:
            return name
    return None


def build_academics_snapshot(user, today: date) -> Dict[str, int]:
    models = _get_academics_models()

    classes_qs = filter_queryset_by_scope(_base_queryset(models["class"]), user)
    sessions_qs = filter_queryset_by_scope(_base_queryset(models["session"]), user)
    events_qs = filter_queryset_by_scope(_base_queryset(models["calendar"]), user)

    classes_fields = {f.name for f in classes_qs.model._meta.get_fields()} if models["class"] else set()
    sessions_fields = {f.name for f in sessions_qs.model._meta.get_fields()} if models["session"] else set()
    events_fields = {f.name for f in events_qs.model._meta.get_fields()} if models["calendar"] else set()

    active_classes = classes_qs
    class_active_field = _resolve_boolean_filter_fields(classes_fields, ["is_active", "active", "actif"])
    if class_active_field:
        active_classes = classes_qs.filter(**{class_active_field: True})

    active_sessions = sessions_qs
    session_active_field = _resolve_boolean_filter_fields(sessions_fields, ["is_active", "active", "actif"])
    if session_active_field:
        active_sessions = sessions_qs.filter(**{session_active_field: True})

    event_start_field = _resolve_date_field(events_fields, ["start_date", "date_debut", "event_date", "date"])
    event_end_field = _resolve_date_field(events_fields, ["end_date", "date_fin"])

    near_window = today + timedelta(days=14)
    imminent_events = 0
    scheduling_anomalies = 0
    if event_start_field:
        imminent_events = events_qs.filter(**{f"{event_start_field}__gte": today, f"{event_start_field}__lte": near_window}).count()
        if event_end_field:
            scheduling_anomalies = events_qs.filter(
                Q(**{f"{event_end_field}__isnull": True}) | Q(**{f"{event_start_field}__gt": F(event_end_field)})
            ).count()

    return {
        "classes_actives": active_classes.count(),
        "sessions_actives": active_sessions.count(),
        "evenements_imminents": imminent_events,
        "anomalies_planification": scheduling_anomalies,
    }


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
    academics_kpis = build_academics_snapshot(user, today=today)

    return {
        "effectif_total": aggregate_total_students(students_qs),
        "nouveaux_inscrits": nouveaux_inscrits,
        "paiements_mois": paiements_mois,
        "impayes": impayes,
        "echeances_proches": echeances_proches,
        "anomalies": anomalies,
        "repartition_niveaux": repartition["by_level"],
        "repartition_classes": repartition["by_class"],
        **academics_kpis,
    }


def build_recent_activities(user, limit: int = 10) -> List[Dict[str, object]]:
    students_model = _get_model("students", ["Student", "Eleve", "StudentProfile"])
    payments_model = _get_model("finance", ["Paiement", "Payment"])

    activities: List[Dict[str, object]] = []

    if students_model is not None:
        students_qs = filter_queryset_by_scope(_base_queryset(students_model), user)
        student_fields = {f.name for f in students_qs.model._meta.get_fields()}
        student_date_field = _resolve_date_field(
            student_fields,
            ["date_inscription", "created_at", "created_on", "enrolled_at"],
        )
        student_actor_field = _resolve_date_field(
            student_fields,
            ["full_name", "nom_complet", "name", "nom", "matricule", "registration_number"],
        )

        if student_date_field:
            for student in students_qs.order_by(F(student_date_field).desc(nulls_last=True), "-pk")[:limit]:
                actor_value = getattr(student, student_actor_field, None) if student_actor_field else None
                activities.append(
                    {
                        "type": "Inscription",
                        "acteur": str(actor_value or student),
                        "date": getattr(student, student_date_field),
                        "detail_url": "/students/",
                        "detail_label": "Ouvrir Students",
                    }
                )

    if payments_model is not None:
        payments_qs = filter_queryset_by_scope(_base_queryset(payments_model), user)
        payment_fields = {f.name for f in payments_qs.model._meta.get_fields()}
        payment_date_field = _resolve_date_field(
            payment_fields,
            ["date_paiement", "payment_date", "date", "created_at", "created_on"],
        )
        payment_actor_field = _resolve_date_field(
            payment_fields,
            ["reference_operation", "reference", "client_nom", "payer_name"],
        )

        if payment_date_field:
            for payment in payments_qs.order_by(F(payment_date_field).desc(nulls_last=True), "-pk")[:limit]:
                actor_value = getattr(payment, payment_actor_field, None) if payment_actor_field else None
                activities.append(
                    {
                        "type": "Paiement",
                        "acteur": str(actor_value or payment),
                        "date": getattr(payment, payment_date_field),
                        "detail_url": "/finance/",
                        "detail_label": "Ouvrir Finance",
                    }
                )

    def sort_key(item: Dict[str, object]):
        value = item.get("date")
        if isinstance(value, datetime):
            return value
        if isinstance(value, date):
            return datetime.combine(value, datetime.min.time())
        return datetime.min

    return sorted(activities, key=sort_key, reverse=True)[:limit]


def build_minimal_timeseries(user, months: int = 6) -> Dict[str, List[Dict[str, object]]]:
    today = date.today()
    month_start = today.replace(day=1)
    window_start = (month_start - timedelta(days=32 * (months - 1))).replace(day=1)

    students_model = _get_model("students", ["Student", "Eleve", "Enrollment"])
    payments_model = _get_model("finance", ["Paiement", "Payment", "Invoice"])

    students_qs = filter_queryset_by_scope(_base_queryset(students_model), user)
    payments_qs = filter_queryset_by_scope(_base_queryset(payments_model), user)

    student_fields = {f.name for f in students_qs.model._meta.get_fields()}
    payment_fields = {f.name for f in payments_qs.model._meta.get_fields()}

    student_date_field = _resolve_date_field(
        student_fields,
        ["date_inscription", "created_at", "created_on", "enrolled_at"],
    )
    payment_date_field = _resolve_date_field(
        payment_fields,
        ["date_paiement", "payment_date", "paid_at", "created_at", "created_on"],
    )
    payment_amount_field = _resolve_date_field(payment_fields, ["amount", "montant"])

    months_index = []
    cursor = window_start
    for _ in range(months):
        months_index.append(cursor.strftime("%Y-%m"))
        cursor = (cursor + timedelta(days=32)).replace(day=1)

    inscriptions_map = {key: 0 for key in months_index}
    paiements_map = {key: Decimal("0") for key in months_index}

    if student_date_field:
        student_rows = (
            students_qs.filter(**{f"{student_date_field}__gte": window_start})
            .annotate(month=TruncMonth(student_date_field))
            .values("month")
            .annotate(total=Count("pk"))
            .order_by("month")
        )
        for row in student_rows:
            month = row["month"]
            if month is not None:
                inscriptions_map[month.strftime("%Y-%m")] = row["total"] or 0

    if payment_date_field and payment_amount_field:
        payment_rows = (
            payments_qs.filter(**{f"{payment_date_field}__gte": window_start})
            .annotate(month=TruncMonth(payment_date_field))
            .values("month")
            .annotate(total=Sum(payment_amount_field))
            .order_by("month")
        )
        for row in payment_rows:
            month = row["month"]
            if month is not None:
                paiements_map[month.strftime("%Y-%m")] = row["total"] or Decimal("0")

    inscriptions_series = []
    paiements_series = []
    max_inscriptions = max(inscriptions_map.values()) if inscriptions_map else 0
    max_paiements = max(paiements_map.values()) if paiements_map else Decimal("0")
    for key in months_index:
        label = datetime.strptime(key, "%Y-%m").strftime("%m/%Y")
        ins_value = inscriptions_map[key]
        pay_value = paiements_map[key]
        inscriptions_series.append(
            {
                "month": label,
                "value": int(ins_value),
                "width_pct": int((ins_value / max_inscriptions) * 100) if max_inscriptions else 0,
            }
        )
        paiements_series.append(
            {
                "month": label,
                "value": float(pay_value),
                "width_pct": int((pay_value / max_paiements) * 100) if max_paiements else 0,
            }
        )

    return {
        "inscriptions_par_mois": inscriptions_series,
        "paiements_par_mois": paiements_series,
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
    cache_key = f"dashboard:critical:v1:user:{user.pk}"
    cached_payload = cache.get(cache_key)
    if cached_payload is not None:
        return cached_payload

    role = _resolve_role(user)
    kpis_cache_key = f"dashboard:kpis:v1:user:{user.pk}"
    kpis = cache.get(kpis_cache_key)
    if kpis is None:
        kpis = build_kpi_snapshot(user)
        cache.set(kpis_cache_key, kpis, CRITICAL_CACHE_TIMEOUT_SECONDS)
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

    widgets = [
        {"key": card["key"], "title": card["label"], "value": card["value"], "link": card["link"], "severity": "primary"}
        for card in summary_cards
    ]

    payload = {
        "dashboard_role": role,
        "summary_cards": summary_cards,
        "widgets": widgets,
        "alerts": alerts_payload["alerts"],
        "alerts_sort": alerts_payload["alerts_sort"],
        "alerts_dir": alerts_payload["alerts_dir"],
        "quick_links": quick_links_payload,
        "charts_data": charts_data,
        "empty_state": empty_state,
    }
    cache.set(cache_key, payload, CACHE_TIMEOUT_SECONDS)
    return payload


def build_secondary_dashboard_context(user) -> Dict[str, object]:
    cache_key = f"dashboard:secondary:v1:user:{user.pk}"
    cached_payload = cache.get(cache_key)
    if cached_payload is not None:
        return cached_payload

    activities_key = f"dashboard:activities:v1:user:{user.pk}"
    recent_activities = cache.get(activities_key)
    if recent_activities is None:
        recent_activities = build_recent_activities(user, limit=10)
        cache.set(activities_key, recent_activities, RECENT_ACTIVITIES_CACHE_TIMEOUT_SECONDS)

    timeseries_key = f"dashboard:timeseries:v1:user:{user.pk}"
    timeseries = cache.get(timeseries_key)
    if timeseries is None:
        timeseries = build_minimal_timeseries(user, months=6)
        cache.set(timeseries_key, timeseries, SECONDARY_CACHE_TIMEOUT_SECONDS)

    payload = {
        "recent_activities": recent_activities,
        "timeseries": timeseries,
    }
    cache.set(cache_key, payload, SECONDARY_CACHE_TIMEOUT_SECONDS)
    return payload


def get_dashboard_context(user) -> Dict[str, object]:
    """Alias de compatibilité pour l'ancienne API de vue."""
    return build_dashboard_context(user)
