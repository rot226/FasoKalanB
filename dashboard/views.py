import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import render

from .services import DEFAULT_ROLE, ROLE_WIDGETS, build_dashboard_context, get_dashboard_alerts

logger = logging.getLogger(__name__)


@login_required
def dashboard_home(request):
    """Affiche la page d'accueil du tableau de bord (authentifiée)."""
    user = request.user

    if not user.is_active:
        return HttpResponseForbidden("Compte inactif.")

    role = "admin" if (user.is_superuser or user.is_staff) else None
    if role is None:
        known_roles = set(ROLE_WIDGETS.keys())
        user_roles = set(user.groups.values_list("name", flat=True))
        if not user_roles:
            role = DEFAULT_ROLE
        else:
            intersection = known_roles.intersection(user_roles)
            role = next(iter(intersection), None)

    if role is None:
        return HttpResponseForbidden("Rôle utilisateur non reconnu.")

    try:
        context = build_dashboard_context(user)
        context.update(
            get_dashboard_alerts(
                sort_key=request.GET.get("alert_sort", "criticite"),
                sort_dir=request.GET.get("alert_dir", "desc"),
            )
        )
    except Exception:
        logger.exception("Échec de collecte des données du dashboard pour l'utilisateur %s", user.pk)
        messages.error(
            request,
            "Certaines données du tableau de bord sont momentanément indisponibles."
            " Un affichage partiel est proposé.",
        )
        alerts_payload = get_dashboard_alerts(
            sort_key=request.GET.get("alert_sort", "criticite"),
            sort_dir=request.GET.get("alert_dir", "desc"),
        )
        context = {
            "dashboard_role": role,
            "summary_cards": [],
            "quick_links": [],
            "charts_data": {"kpi_values": {}, "alerts_by_severity": {}},
            "empty_state": {
                "show": True,
                "title": "Données partiellement indisponibles",
                "description": (
                    "Nous n'avons pas pu charger tous les indicateurs pour le moment."
                    " Veuillez réessayer dans quelques instants."
                ),
            },
            **alerts_payload,
        }

    return render(request, "dashboard/home.html", context)
