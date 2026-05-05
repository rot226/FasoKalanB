from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .services import get_dashboard_context


ALERT_SEVERITY_ORDER = {
    "critique": 0,
    "elevee": 1,
    "moyenne": 2,
    "faible": 3,
}


def _get_dashboard_alerts():
    """Retourne les alertes du dashboard triées côté serveur."""
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


@login_required
def dashboard_home(request):
    """Affiche la page d'accueil du tableau de bord (authentifiée)."""
    context = get_dashboard_context(request.user)
    alerts = _get_dashboard_alerts()

    alert_sort = request.GET.get("alert_sort", "criticite")
    if alert_sort not in {"criticite", "date"}:
        alert_sort = "criticite"

    alert_dir = request.GET.get("alert_dir", "desc")
    if alert_dir not in {"asc", "desc"}:
        alert_dir = "desc"

    alerts = _sort_alerts(alerts, alert_sort, alert_dir)

    context.update(
        {
            "alerts": alerts,
            "alerts_sort": alert_sort,
            "alerts_dir": alert_dir,
        }
    )
    return render(request, 'dashboard/home.html', context)
