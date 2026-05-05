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

### Bootstrap admin de développement

Une commande idempotente permet de créer (ou mettre à jour) automatiquement un superuser local `admin` avec le mot de passe `admin` :

```bash
python manage.py bootstrap_dev
```

Par sécurité, cette commande n'est autorisée que si :

- `DEBUG=True`, **ou**
- la variable d'environnement `AUTO_CREATE_DEV_ADMIN=1` est définie.

Après exécution, changez immédiatement le mot de passe du compte via :

- `/admin/password_change/`
- (template associé) `templates/registration/password_change_form.html`

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

## Vision multi-tenant

Cette section décrit une **orientation d’architecture** pour préparer une future gestion multi-tenant, sans activer de complexité technique à ce stade.

### Stratégie potentielle

- **Tenant par école** : chaque établissement scolaire est considéré comme un tenant logique.
- **Séparation logique des données** : les données métier restent dans une base unique, mais chaque enregistrement métier sera, à terme, rattaché explicitement à une école (`school_id` ou relation équivalente).
- **Portée applicative** : l’isolation se fera d’abord au niveau applicatif (règles de requêtage et services), sans partitionnement physique immédiat de la base.

### App candidate pour la gestion des tenants

- **`schools`** : candidate naturelle pour porter l’entité tenant (identité école, métadonnées, statut, etc.).
- **`accounts`** : candidate pour porter le rattachement des utilisateurs à un tenant (membership, rôles, permissions par école).
- **`settings` (configuration projet)** : emplacement privilégié pour centraliser plus tard les options globales liées au multi-tenant (feature flags, stratégie active, garde-fous d’environnement).

### Conventions de nommage à suivre

- Utiliser le terme **`school`** comme nom canonique du tenant dans le code métier.
- Préférer des noms explicites et stables :
  - `school_id` pour les clés de rattachement.
  - `*_by_school` ou `for_school(...)` pour les helpers/scopes orientés tenant.
  - `is_active`, `slug`, `code` pour les attributs d’identification fonctionnelle (selon besoins futurs).
- Éviter la multiplication de synonymes (`tenant`, `organization`, `campus`) dans le code tant qu’une convention unique n’est pas formellement révisée.

> Note : aucune implémentation active (middleware, routing spécifique, modèle dédié) n’est introduite ici ; il s’agit d’un cadrage documentaire pour faciliter les extensions futures.

## Prochaine étape

Aucun modèle métier n’est encore implémenté : la prochaine étape consiste à définir et coder les modèles du domaine (élèves, établissements, scolarité, paiements, etc.).
