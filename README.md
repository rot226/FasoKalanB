# FasoKalanB

## Stack & conventions

### Stack recommandée

- **Python recommandé : `3.12.x`** (version stable moderne et largement supportée).
- **Framework web : Django LTS** (Long Term Support), pour garantir un cycle de maintenance plus long et une meilleure stabilité en production.

### Arborescence attendue

Structure de référence pour organiser le projet :

```text
.
├── config/       # Paramètres globaux du projet (settings, urls, ASGI/WSGI)
├── apps/         # Applications métier Django (domaines fonctionnels)
├── templates/    # Templates HTML globaux et partagés
├── static/       # Fichiers statiques (CSS, JS, images)
└── media/        # Fichiers uploadés par les utilisateurs
```

### Convention de nommage (apps et modules)

- Utiliser des noms **courts, explicites et en minuscules**.
- Utiliser le **snake_case** pour les noms de modules Python.
- Éviter les abréviations ambiguës.
- Préférer des noms orientés domaine métier (ex. `users`, `billing`, `catalog`).
- Une app Django = une responsabilité principale.

### Configuration via variables d’environnement

Principe recommandé : **ne pas coder en dur les secrets ni les paramètres dépendants de l’environnement**.

- Lire la configuration depuis des variables d’environnement (`DJANGO_SECRET_KEY`, `DEBUG`, `DATABASE_URL`, etc.).
- Utiliser des valeurs différentes selon les contextes (local, test, production).
- Ne jamais versionner les secrets dans Git.
- Centraliser l’accès à ces variables dans la couche `config/`.

### Prérequis Windows 11

Pour un poste de développement sous Windows 11 :

1. Installer **Python 3.12.x** (depuis le site officiel) en cochant l’option d’ajout au `PATH`.
2. Vérifier l’installation :
   - `python --version`
   - `pip --version`
3. Créer un environnement virtuel :
   - `python -m venv .venv`
4. Activer l’environnement virtuel (PowerShell) :
   - `.\.venv\Scripts\Activate.ps1`
5. Mettre à jour `pip` (recommandé) :
   - `python -m pip install --upgrade pip`
