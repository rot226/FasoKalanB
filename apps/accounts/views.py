from django.http import HttpResponse


def login_view(request):
    return HttpResponse("Connexion")


def logout_view(request):
    return HttpResponse("Déconnexion")
