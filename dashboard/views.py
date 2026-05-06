import logging
import time

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import render

from .services import (
    DEFAULT_ROLE,
    ROLE_WIDGETS,
    _resolve_role,
    build_dashboard_context,
    build_secondary_dashboard_context,
    get_dashboard_alerts,
)

logger = logging.getLogger(__name__)


@login_required
def dashboard_home(request):
    """Affiche la page d'accueil du tableau de bord (authentifiée)."""
    user = request.user

    if not user.is_active:
        return HttpResponseForbidden("Compte inactif.")

    role = _resolve_role(user)

    if role not in ROLE_WIDGETS and role != DEFAULT_ROLE:
        return HttpResponseForbidden("Rôle utilisateur non reconnu.")

    try:
        start_perf = time.perf_counter()
        context = build_dashboard_context(user)
        context.update(
            get_dashboard_alerts(
                sort_key=request.GET.get("alert_sort", "criticite"),
                sort_dir=request.GET.get("alert_dir", "desc"),
            )
        )
        context["secondary_data_url"] = "/dashboard/secondary/"
        context["server_render_time_ms"] = round((time.perf_counter() - start_perf) * 1000, 2)
        logger.info(
            "dashboard.primary_render user=%s duration_ms=%.2f",
            user.pk,
            context["server_render_time_ms"],
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


@login_required
def dashboard_secondary(request):
    start_perf = time.perf_counter()
    payload = build_secondary_dashboard_context(request.user)
    duration_ms = round((time.perf_counter() - start_perf) * 1000, 2)
    logger.info("dashboard.secondary_render user=%s duration_ms=%.2f", request.user.pk, duration_ms)
    return render(
        request,
        "dashboard/partials/secondary_content.html",
        {
            **payload,
            "secondary_render_time_ms": duration_ms,
        },
    )
