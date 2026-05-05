"""Seed local-only admin user for demo environments.

Usage:
    python manage.py shell < scripts/seed_local_admin.py
"""

import os

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured

allow_by_env = os.getenv("AUTO_CREATE_DEV_ADMIN", "").strip() == "1"

if not (settings.DEBUG or allow_by_env):
    raise ImproperlyConfigured(
        "Script refusé : activez DEBUG=True ou définissez AUTO_CREATE_DEV_ADMIN=1."
    )

User = get_user_model()
username_field = User.USERNAME_FIELD

lookup = {username_field: "admin"}
user, created = User.objects.get_or_create(
    **lookup,
    defaults={
        "is_staff": True,
        "is_superuser": True,
    },
)

user.is_staff = True
user.is_superuser = True
user.set_password("admin")
user.save()

if created:
    print("Superuser local 'admin' créé avec succès.")
else:
    print("Superuser local 'admin' déjà existant, mis à jour.")

print("Mot de passe défini sur 'admin' (uniquement pour la démo locale).")
