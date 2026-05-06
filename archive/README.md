# Archive du projet

Ce dossier conserve uniquement de la documentation d’archivage.

## Dashboard (implémentation officielle)

- **Implémentation officielle active**: package racine `dashboard`.
- Références de routage et chargement Django:
  - `INSTALLED_APPS` -> `'dashboard'` dans `config/settings.py`
  - `path('dashboard/', include('dashboard.urls'))` dans `config/urls.py`

## Historique

La duplication historique `apps.dashboard` a été retirée pour éviter toute ambiguïté d’import/routage.
