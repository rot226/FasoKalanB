import os

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = (
        "Crée (ou met à jour) le superuser admin/admin pour le développement "
        "quand DEBUG=True ou AUTO_CREATE_DEV_ADMIN=1."
    )

    def handle(self, *args, **options):
        allow_by_env = os.getenv("AUTO_CREATE_DEV_ADMIN", "").strip() == "1"

        if not (settings.DEBUG or allow_by_env):
            raise CommandError(
                "Commande refusée : activez DEBUG=True ou définissez "
                "AUTO_CREATE_DEV_ADMIN=1 pour autoriser bootstrap_dev."
            )

        user_model = get_user_model()
        username_field = user_model.USERNAME_FIELD

        lookup = {username_field: "admin"}
        user, created = user_model.objects.get_or_create(
            **lookup,
            defaults={
                "is_staff": True,
                "is_superuser": True,
            },
        )

        # Idempotent : on normalise les flags et le mot de passe à chaque exécution.
        user.is_staff = True
        user.is_superuser = True
        user.set_password("admin")
        user.save()

        if created:
            self.stdout.write(self.style.SUCCESS("Superuser 'admin' créé avec succès."))
        else:
            self.stdout.write(self.style.WARNING("Superuser 'admin' déjà existant, mis à jour."))

        self.stdout.write(
            "Mot de passe défini sur 'admin'. Changez-le immédiatement via "
            "/admin/password_change/."
        )
