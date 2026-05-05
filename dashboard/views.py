from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .services import get_dashboard_context


@login_required
def dashboard_home(request):
    """Affiche la page d'accueil du tableau de bord (authentifiée)."""
    context = get_dashboard_context(request.user)
    return render(request, 'dashboard/home.html', context)
