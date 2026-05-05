# FasoKalan Bâ v1.0

## Présentation

**FasoKalan Bâ v1.0** est une application web Django de gestion scolaire.
Elle fournit un socle pour :

- l’authentification (`accounts`),
- la gestion établissement/scolarité/élèves (`schools`, `academics`, `students`),
- la finance (`finance`),
- les notifications et reporting (`notifications`, `reports`),
- le pilotage via tableau de bord (`dashboard`).

L’objectif de la version **v1.0** est de livrer une base fonctionnelle claire, modulaire et prête à évoluer.

## Prérequis (Windows 11)

Sur **Windows 11**, installer au préalable :

1. **Python 3.12.x** (avec l’option *Add Python to PATH*).
2. **pip** (inclus avec Python, à vérifier).
3. *(Optionnel recommandé)* **Git for Windows**.

Vérifications rapides :

```powershell
python --version
pip --version
git --version
```

## Installation

Depuis la racine du projet :

```powershell
# 1) Créer l’environnement virtuel
python -m venv .venv

# 2) Activer le venv (PowerShell)
.\.venv\Scripts\Activate.ps1

# 3) Mettre pip à jour
python -m pip install --upgrade pip

# 4) Installer les dépendances
pip install -r requirements.txt
```

## Commandes (Windows 11)

Depuis la racine du projet.

### 1) Création / activation du venv

**PowerShell**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**CMD**

```cmd
python -m venv .venv
.\.venv\Scripts\activate.bat
```

### 2) Installation des dépendances

**PowerShell / CMD**

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3) Migrations

**PowerShell / CMD**

```powershell
python manage.py migrate
```

### 4) Création superuser

**PowerShell / CMD**

```powershell
python manage.py createsuperuser
```

### 5) Lancement serveur

**PowerShell / CMD**

```powershell
python manage.py runserver
```

### 6) Accès aux pages

- `/` → `http://127.0.0.1:8000/`
- `/accounts/login/` → `http://127.0.0.1:8000/accounts/login/`
- `/dashboard/` → `http://127.0.0.1:8000/dashboard/`

## Configuration `.env`

Créer un fichier `.env` à la racine du projet (au même niveau que `manage.py`) avec les variables minimales :

```env
SECRET_KEY=django-insecure-change-me
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
# Optionnel : chemin SQLite personnalisé
# DB=C:/chemin/vers/db.sqlite3
```

Variables prises en charge actuellement :

- `SECRET_KEY`
- `DEBUG` (`True/False`, `1/0`, etc.)
- `ALLOWED_HOSTS` (liste séparée par virgules)
- `DB` (chemin vers le fichier SQLite)

## Migrations et lancement serveur

Toujours avec le venv activé :

```powershell
# Appliquer les migrations
python manage.py migrate

# Créer un superutilisateur (optionnel)
python manage.py createsuperuser

# Lancer le serveur de dev
python manage.py runserver
```

Par défaut, le serveur démarre sur :

- `http://127.0.0.1:8000/`

## URLs importantes

- **Accueil** : `http://127.0.0.1:8000/`
- **Login** : `http://127.0.0.1:8000/accounts/login/`
- **Dashboard** : `http://127.0.0.1:8000/dashboard/`
- **Admin Django** : `http://127.0.0.1:8000/admin/`

## Structure des apps

```text
apps/
├── accounts       # Authentification / sessions
├── schools        # Entités établissement
├── academics      # Référentiel académique
├── students       # Élèves et inscriptions
├── finance        # Paiements / frais
├── notifications  # Messages/notifications
├── dashboard      # Indicateurs et vue de pilotage
├── reports        # Exports et rapports
└── core           # Pages transverses (accueil, socle commun)
```

## Prochaines étapes v1

1. **Modéliser les entités métier prioritaires** (élèves, inscriptions, paiements).
2. **Ajouter des formulaires CRUD** par app avec validations métier.
3. **Renforcer la sécurité** (`DEBUG=False`, `ALLOWED_HOSTS`, gestion des secrets).
4. **Mettre en place des tests automatisés** (unitaires + intégration Django).
5. **Préparer le déploiement** (collectstatic, configuration production, sauvegarde DB/media).

---

Si vous travaillez sous Windows 11, gardez ce cycle simple :
**activer le venv → installer/mettre à jour dépendances → migrer → lancer le serveur**.
