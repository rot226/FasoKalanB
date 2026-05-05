from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, List

from django.apps import apps
from django.contrib.auth.models import Group


@dataclass(frozen=True)
class DashboardWidget:
    title: str
    value: str
    link: str
    severity: str


def _count_records_for_app(app_label: str) -> int:
    """Retourne le nombre total d'enregistrements pour tous les modèles d'une app."""
    try:
        app_config = apps.get_app_config(app_label)
    except LookupError:
        return 0

    total = 0
    for model in app_config.get_models():
        total += model.objects.count()
    return total


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


def get_dashboard_context(user) -> Dict[str, object]:
    """Construit le contexte dynamique du dashboard selon le rôle."""
    role = _resolve_role(user)

    students_total = _count_records_for_app("students")
    finance_total = _count_records_for_app("finance")
    academics_total = _count_records_for_app("academics")
    user_groups_count = Group.objects.count()

    role_widgets: Dict[str, List[DashboardWidget]] = {
        "admin": [
            DashboardWidget("Enregistrements élèves", str(students_total), "/students/", "info"),
            DashboardWidget("Enregistrements finance", str(finance_total), "/finance/", "warning"),
            DashboardWidget("Enregistrements académiques", str(academics_total), "/academics/", "primary"),
            DashboardWidget("Groupes utilisateurs", str(user_groups_count), "/admin/auth/group/", "secondary"),
        ],
        "scolarite": [
            DashboardWidget("Dossiers élèves", str(students_total), "/students/", "primary"),
            DashboardWidget("Suivi académique", str(academics_total), "/academics/", "info"),
        ],
        "finance": [
            DashboardWidget("Éléments financiers", str(finance_total), "/finance/", "warning"),
            DashboardWidget("Base élèves (référence)", str(students_total), "/students/", "secondary"),
        ],
        "direction": [
            DashboardWidget("Vue globale élèves", str(students_total), "/students/", "info"),
            DashboardWidget("Vue globale finance", str(finance_total), "/finance/", "warning"),
            DashboardWidget("Vue globale académique", str(academics_total), "/academics/", "primary"),
        ],
    }

    widgets = [asdict(widget) for widget in role_widgets.get(role, [])]

    return {
        "dashboard_role": role,
        "widgets": widgets,
    }
