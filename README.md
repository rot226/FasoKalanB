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

## Architecture applicative légère

### Vue d’ensemble des apps

| App | Responsabilité principale | Données gérées |
| --- | --- | --- |
| `accounts` | Authentification, gestion des profils utilisateurs, gestion des rôles et permissions. | Utilisateurs, profils, rôles, groupes, droits d’accès. |
| `schools` | Gestion des entités école et de leurs paramètres fonctionnels. | École, campus (si applicable), paramètres de l’établissement, préférences globales. |
| `academics` | Référentiel académique. | Années scolaires, classes, sections, découpages pédagogiques. |
| `students` | Cycle de vie élève. | Élèves, parents/tuteurs, liens de responsabilité, inscriptions par année/classe. |
| `finance` | Gestion financière scolaire. | Frais, échéanciers, paiements, reçus, statuts de règlement. |
| `notifications` | Production et envoi de communications aux parents/tuteurs. | Modèles de message, événements de notification, historique d’envoi. |
| `dashboard` | Pilotage directionnel via indicateurs. | Agrégats/KPI calculés depuis plusieurs apps (lecture seule). |
| `reports` | Exports et génération documentaire. | Exports CSV/Excel, fichiers de synthèse, documents administratifs. |
| `core` | Socle transverse de l’application. | Pages globales, utilitaires communs, composants partagés techniques. |

### Frontières entre apps (anti-couplage fort)

1. **Dépendances unidirectionnelles vers les référentiels**
   - `students` dépend de `academics` (classe/section/année) et `schools` (contexte établissement), mais l’inverse est interdit.
   - `finance` dépend de `students` pour les inscriptions et de `schools` pour le contexte de facturation.

2. **`accounts` reste transverse mais isolé**
   - Les autres apps consomment l’identité utilisateur (FK vers user) sans embarquer de logique d’authentification.
   - Toute règle de rôles/permissions reste centralisée dans `accounts`.

3. **Apps de sortie en lecture seule métier**
   - `dashboard` et `reports` lisent les données des apps métier (`students`, `finance`, `academics`, etc.) sans modifier leur état.
   - Interdire les écritures métier depuis `dashboard` et `reports`.

4. **`notifications` réagit à des événements métier**
   - `notifications` ne porte pas les règles cœur d’inscription/paiement ; elle consomme des événements (ex. inscription validée, paiement reçu).
   - Préférer des signaux/domain events ou services applicatifs explicites plutôt que des imports croisés profonds.

5. **`core` ne devient pas une app “fourre-tout”**
   - `core` contient uniquement des briques génériques (helpers, mixins, vues globales non métier).
   - Aucune logique métier spécifique (`finance`, `students`, etc.) ne doit migrer vers `core`.

6. **Contrats d’intégration explicites**
   - Exposer les interactions inter-apps via services (`services.py`), sélecteurs/repositories ou API internes clairement nommés.
   - Éviter l’accès direct aux modèles internes d’une app depuis plusieurs autres apps si un contrat applicatif existe.

### Schéma de dépendances recommandé

```text
accounts        schools        academics
    │              │               │
    └──────┬───────┴───────┬───────┘
           │               │
        students        finance
           │               │
           └──────┬────────┘
                  │
            notifications

(dashboard, reports) -> lecture seule sur students/finance/academics/schools
core -> utilitaires transverses sans logique métier
```
