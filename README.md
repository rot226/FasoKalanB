# FasoKalan Bâ

## Présentation courte du projet FasoKalan Bâ

**FasoKalan Bâ** est une base de projet Django orientée gestion scolaire. Elle fournit une structure applicative modulaire pour démarrer rapidement le développement.

## Prérequis

- Python **3.11+**
- `pip`
- Un terminal (PowerShell recommandé sous Windows 11)
- Base de données locale prête (SQLite par défaut dans ce projet)

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

## Windows 11 - démarrage rapide

Depuis **Windows PowerShell** à la racine du projet :

```powershell
py -3.11 -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python manage.py migrate
python manage.py bootstrap_dev
python manage.py runserver
```

Accès utiles après démarrage :

- Application : `http://127.0.0.1:8000/`
- Admin Django : `http://127.0.0.1:8000/admin/`

## Configuration `.env`

Créer un fichier `.env` à la racine (même niveau que `manage.py`) avec au minimum :

```env
SECRET_KEY=django-insecure-change-me
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
```

Vous pouvez adapter ces variables selon votre environnement local.

## Migrations et admin local (méthode officielle)

```bash
python manage.py migrate
python manage.py bootstrap_dev
```

La commande `bootstrap_dev` est la **seule méthode officielle documentée** pour initialiser l'admin local de démonstration.

## Création de données de démonstration

Pour créer un jeu de données local de démonstration :

```bash
python manage.py migrate
python manage.py bootstrap_dev
```

Cette commande prépare les données minimales nécessaires pour tester l’authentification et l’accès au dashboard en local.


### Mécanisme alternatif (non officiel)

Un script Django shell est également disponible pour le **seed local de démonstration** :

```bash
python manage.py shell < scripts/seed_local_admin.py
```

Cette voie alternative est fournie pour dépannage local uniquement.

Par sécurité, cette commande n'est autorisée que si :

- `DEBUG=True`, **ou**
- la variable d'environnement `AUTO_CREATE_DEV_ADMIN=1` est définie.

Ne jamais utiliser ni versionner un mot de passe de production dans ce mécanisme. Le mot de passe `admin` est strictement réservé à l'environnement local de démonstration.

Après exécution, changez immédiatement le mot de passe du compte via :

- `/admin/password_change/`
- (template associé) `templates/registration/password_change_form.html`

## Compte admin de développement

Pour l'environnement local de développement, le compte d'administration initialisé utilise les identifiants suivants :

- **Identifiant par défaut** : `admin`
- **Mot de passe par défaut** : `admin` (local uniquement)

## Rôles de test

Après exécution de `bootstrap_dev`, utilisez les rôles de test suivants :

- **Admin** : accès global à l’administration Django et aux écrans applicatifs.
- **Utilisateur connecté (non staff)** : vérification des écrans accessibles hors administration.

> Si vous avez besoin d’autres rôles métier (direction, enseignant, comptabilité, etc.), créez-les via l’admin Django selon vos règles de permissions cibles.

## Ce qui doit apparaître après login

Après une connexion réussie :

1. Redirection vers l’accueil applicatif / dashboard.
2. Affichage du layout principal (menu, zone centrale, messages flash éventuels).
3. Présence de contenus dashboard (cartes/KPI/listes) si les données de démo ont bien été créées.
4. Pour un compte staff/admin, accès possible à `/admin/`.

Si l’un de ces éléments est absent, consultez la section **Dépannage — dashboard vide** ci-dessous.

⚠️ **Obligation de sécurité** : ce mot de passe doit être changé immédiatement après la première connexion, même en environnement local.

## Erreurs fréquentes

### `NoReverseMatch: 'home' not found`

Cette erreur indique que Django ne trouve pas la route nommée `home` au moment d'exécuter un `redirect(...)`, un `{% url 'home' %}` ou un `reverse('home')`.

Causes probables :

- **Namespace non pris en compte** : la route existe mais sous un namespace (ex. `core:home` au lieu de `home`).
- **`include(...)` manquant** dans le routeur principal (`config/urls.py`) vers les URLs de l'application concernée.
- **Nom de route différent** : la vue est enregistrée avec un autre `name=...` que `home`.

Checklist de correction (4-5 points) :

1. Vérifier le `name='home'` (ou le nom réel) dans le fichier `urls.py` de l'app ciblée.
2. Vérifier si un `app_name` est défini et, si oui, utiliser le namespace complet (`<app_name>:home`).
3. Confirmer que `config/urls.py` inclut bien les URLs de l'app (`path(..., include('...urls'))`).
4. Mettre à jour tous les templates et redirections pour utiliser exactement le même nom de route.
5. Relancer le serveur Django et retester la navigation après correction.

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

## Note dashboard

Le dashboard complet dépend des US-DAS-01/02.

Décision d'architecture active : l'app canonique est `dashboard` (package racine), avec `'dashboard'` dans `INSTALLED_APPS` et `include('dashboard.urls')` dans `config/urls.py`.

Voir aussi : `docs/architecture-dashboard.md` pour les garde-fous contre la réintroduction du doublon `apps.dashboard`.

## Dépannage — dashboard vide

Checklist rapide :

1. Vérifier que les migrations sont appliquées : `python manage.py migrate`
2. Rejouer les données de démo : `python manage.py bootstrap_dev`
3. Vérifier le compte utilisé (connecté et actif).
4. Vérifier le rôle/permissions (staff, groupes, droits).
5. Ouvrir `/admin/` pour confirmer que des données existent réellement.
6. Redémarrer le serveur : `python manage.py runserver`
7. Actualiser la session (déconnexion/reconnexion).

## Prochaine étape

Aucun modèle métier n’est encore implémenté : la prochaine étape consiste à définir et coder les modèles du domaine (élèves, établissements, scolarité, paiements, etc.).
