from django.shortcuts import render


def home(request):
    """Affiche la page d'accueil publique."""
    return render(request, 'home.html')
