from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def dashboard_home(request):
    """Affiche la page d'accueil du tableau de bord (authentifiée)."""
    return render(request, 'dashboard/home.html')
