# FasoKalan Bâ

## Présentation courte du projet FasoKalan Bâ

**FasoKalan Bâ** est une base de projet Django orientée gestion scolaire. Elle fournit une structure applicative modulaire pour démarrer rapidement le développement.

## Prérequis

- Python **3.11+**
- `pip`

## Installation

Depuis la racine du projet :

```bash
python -m venv venv
```

Activation de l'environnement virtuel :

- Linux/macOS :

```bash
source venv/bin/activate
```

- Windows :

```powershell
venv\Scripts\activate
```

Installation des dépendances :

```bash
pip install -r requirements.txt
```

## Configuration `.env`

Créer un fichier `.env` à la racine (même niveau que `manage.py`) avec au minimum :

```env
SECRET_KEY=django-insecure-change-me
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
```

Vous pouvez adapter ces variables selon votre environnement local.

## Migrations et superuser

```bash
python manage.py migrate
python manage.py createsuperuser
```

## Lancement serveur

```bash
python manage.py runserver
```

## Structure du projet

Applications Django principales :

- `accounts`
- `academics`
- `students`
- `schools`
- `finance`
- `notifications`
- `dashboard`
- `reports`
- `core`

Dossiers globaux :

- `apps/` : organisation des applications métier
- `config/` : configuration Django (settings, urls, wsgi, asgi)
- `templates/` : templates HTML
- `static/` : assets statiques
- `media/` : fichiers média
- `docs/` : documentation projet

## Prochaine étape

Aucun modèle métier n’est encore implémenté : la prochaine étape consiste à définir et coder les modèles du domaine (élèves, établissements, scolarité, paiements, etc.).
