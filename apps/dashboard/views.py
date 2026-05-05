from django.http import HttpResponse


def dashboard_home(request):
    return HttpResponse("Tableau de bord")
