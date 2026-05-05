from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .services import get_dashboard_alerts, get_dashboard_context


@login_required
def dashboard_home(request):
    """Affiche la page d'accueil du tableau de bord (authentifiée)."""
    context = get_dashboard_context(request.user)
    context.update(
        get_dashboard_alerts(
            sort_key=request.GET.get("alert_sort", "criticite"),
            sort_dir=request.GET.get("alert_dir", "desc"),
        )
    )
    return render(request, "dashboard/home.html", context)
