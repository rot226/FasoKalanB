from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Dict, Iterable, Optional

from django.db import models
from django.db.models import Count, QuerySet


@dataclass(frozen=True)
class StudentFieldMap:
    """Cartographie des champs utilisés pour les agrégations élèves."""

    statut: Optional[str]
    date_inscription: Optional[str]
    niveau: Optional[str]
    classe: Optional[str]


def _resolve_first_existing_field(model_fields: set[str], candidates: Iterable[str]) -> Optional[str]:
    for candidate in candidates:
        if candidate in model_fields:
            return candidate
    return None


def identify_student_fields(queryset: QuerySet) -> StudentFieldMap:
    """Identifie les champs utiles présents sur le modèle élève."""
    model_fields = {field.name for field in queryset.model._meta.get_fields()}
    return StudentFieldMap(
        statut=_resolve_first_existing_field(model_fields, ["status", "statut", "etat"]),
        date_inscription=_resolve_first_existing_field(
            model_fields,
            ["date_inscription", "created_at", "created_on", "enrolled_at"],
        ),
        niveau=_resolve_first_existing_field(model_fields, ["niveau", "level", "grade"]),
        classe=_resolve_first_existing_field(model_fields, ["classe", "classroom", "classe_id"]),
    )


def aggregate_total_students(queryset: QuerySet) -> int:
    return queryset.count()


def aggregate_new_students(queryset: QuerySet, today: Optional[date] = None) -> int:
    reference_date = today or date.today()
    month_start = reference_date.replace(day=1)
    next_month_start = (month_start + timedelta(days=32)).replace(day=1)

    field_map = identify_student_fields(queryset)
    if not field_map.date_inscription:
        return 0

    return queryset.filter(
        **{
            f"{field_map.date_inscription}__gte": month_start,
            f"{field_map.date_inscription}__lt": next_month_start,
        }
    ).count()


def aggregate_students_by_level_and_class(queryset: QuerySet) -> Dict[str, list[dict[str, object]]]:
    field_map = identify_student_fields(queryset)

    by_level: list[dict[str, object]] = []
    if field_map.niveau:
        by_level = list(
            queryset.values(field_map.niveau)
            .annotate(total=Count("id"))
            .order_by(field_map.niveau)
        )

    by_class: list[dict[str, object]] = []
    if field_map.classe:
        by_class = list(
            queryset.values(field_map.classe)
            .annotate(total=Count("id"))
            .order_by(field_map.classe)
        )

    return {
        "by_level": by_level,
        "by_class": by_class,
    }
