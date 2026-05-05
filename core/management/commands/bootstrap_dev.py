import os

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = (
        "Crée (ou met à jour) les comptes de développement admin/admin et user/user "
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

        admin_lookup = {username_field: "admin"}
        admin_user, admin_created = user_model.objects.get_or_create(
            **admin_lookup,
            defaults={
                "is_staff": True,
                "is_superuser": True,
            },
        )

        # Idempotent : on normalise les flags et le mot de passe à chaque exécution.
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.set_password("admin")
        admin_user.save()

        if admin_created:
            self.stdout.write(self.style.SUCCESS("Superuser 'admin' créé avec succès."))
        else:
            self.stdout.write(self.style.WARNING("Superuser 'admin' déjà existant, mis à jour."))

        user_lookup = {username_field: "user"}
        default_user, user_created = user_model.objects.get_or_create(
            **user_lookup,
            defaults={
                "is_staff": False,
                "is_superuser": False,
            },
        )

        default_user.is_staff = False
        default_user.is_superuser = False
        default_user.set_password("user")
        default_user.save()

        if user_created:
            self.stdout.write(self.style.SUCCESS("Utilisateur par défaut 'user' créé avec succès."))
        else:
            self.stdout.write(self.style.WARNING("Utilisateur par défaut 'user' déjà existant, mis à jour."))

        self.stdout.write(
            "Mots de passe définis sur 'admin' et 'user'. Changez-les immédiatement en dehors du dev."
        )
