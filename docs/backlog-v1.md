# Backlog v1 — User stories prioritaires par module

> Objectif : cadrer le périmètre fonctionnel de la v1 par module, sans définir les modèles de données ni les détails techniques d’implémentation.

## Légende
- **Priorité** : P1 (critique), P2 (importante), P3 (utile)
- **Format** : User story + critères d’acceptation succincts + dépendances inter-modules

---

## 1) Schools

### US-SCH-01 (P1) — Créer et configurer une école
**En tant qu’** administrateur plateforme, **je veux** créer une école avec ses informations de base, **afin de** l’activer sur la plateforme.

**Critères d’acceptation**
- L’administrateur peut créer une école avec les informations minimales requises.
- Une école nouvellement créée est visible dans la liste des écoles.
- Une école peut être activée/désactivée.

**Dépendances**
- Aucune (module fondation).

### US-SCH-02 (P1) — Gérer les campus/entités rattachées
**En tant qu’** administrateur d’école, **je veux** gérer les entités (campus/sites) d’une école, **afin de** structurer l’organisation.

**Critères d’acceptation**
- Ajout, modification et désactivation d’un campus.
- Chaque campus est rattaché à une école existante.

**Dépendances**
- Schools (US-SCH-01).

---

## 2) Accounts

### US-ACC-01 (P1) — Authentification des utilisateurs
**En tant qu’** utilisateur, **je veux** me connecter/déconnecter, **afin de** sécuriser l’accès à mes fonctionnalités.

**Critères d’acceptation**
- Connexion avec identifiants valides.
- Message d’erreur explicite si échec de connexion.
- Déconnexion possible à tout moment.

**Dépendances**
- Schools (pour le contexte école en environnement multi-écoles).

### US-ACC-02 (P1) — Attribution des rôles et permissions
**En tant qu’** administrateur d’école, **je veux** attribuer des rôles, **afin de** contrôler les droits d’accès.

**Critères d’acceptation**
- Attribution d’un rôle à un utilisateur d’une école.
- Les menus/fonctionnalités affichés respectent le rôle.
- Un utilisateur sans droit ne peut pas accéder à une action protégée.

**Dépendances**
- Schools, Accounts (US-ACC-01).

---

## 3) Academics

### US-ACA-01 (P1) — Gérer l’année et les périodes académiques
**En tant qu’** responsable académique, **je veux** définir l’année scolaire et ses périodes, **afin de** planifier les activités pédagogiques.

**Critères d’acceptation**
- Création d’une année scolaire avec dates de début/fin.
- Définition de périodes (trimestres/semestres) dans l’année.
- Une seule année scolaire peut être active à la fois par école.

**Dépendances**
- Schools, Accounts.

### US-ACA-02 (P1) — Structurer classes et matières
**En tant qu’** responsable académique, **je veux** configurer classes et matières, **afin de** organiser l’enseignement.

**Critères d’acceptation**
- Création et mise à jour de classes/niveaux.
- Création et mise à jour de matières.
- Les classes et matières sont rattachées à l’école active.

**Dépendances**
- Schools, Accounts, Academics (US-ACA-01).

---

## 4) Students

### US-STU-01 (P1) — Inscrire un étudiant
**En tant qu’** agent de scolarité, **je veux** enregistrer un étudiant, **afin de** l’intégrer à l’établissement.

**Critères d’acceptation**
- Saisie des informations minimales d’identité.
- Génération d’un identifiant étudiant unique dans l’école.
- L’étudiant apparaît dans la liste des étudiants actifs.

**Dépendances**
- Schools, Accounts.

### US-STU-02 (P1) — Affecter un étudiant à une classe
**En tant qu’** agent de scolarité, **je veux** affecter un étudiant à une classe, **afin de** finaliser son inscription académique.

**Critères d’acceptation**
- Affectation possible uniquement à une classe existante et active.
- Historisation minimale des changements d’affectation (au moins l’affectation courante).
- Affichage de la classe actuelle sur la fiche étudiant.

**Dépendances**
- Students (US-STU-01), Academics (US-ACA-02).

---

## 5) Finance

### US-FIN-01 (P1) — Définir les frais de scolarité
**En tant qu’** responsable financier, **je veux** paramétrer les frais par niveau/classe, **afin de** cadrer la facturation.

**Critères d’acceptation**
- Création de grilles de frais par période académique.
- Les frais sont liés à une classe/niveau et à une année scolaire.
- Version active identifiable pour éviter les ambiguïtés.

**Dépendances**
- Schools, Accounts, Academics.

### US-FIN-02 (P1) — Enregistrer un paiement étudiant
**En tant qu’** caissier, **je veux** enregistrer un paiement, **afin de** mettre à jour le solde de l’étudiant.

**Critères d’acceptation**
- Paiement rattaché à un étudiant existant.
- Mise à jour du solde immédiatement après validation.
- Émission d’un reçu consultable.

**Dépendances**
- Students, Finance (US-FIN-01).

---

## 6) Notifications

### US-NOT-01 (P2) — Notifier les événements critiques
**En tant qu’** administrateur, **je veux** envoyer des notifications ciblées (in-app/email), **afin de** informer rapidement les acteurs.

**Critères d’acceptation**
- Déclenchement sur événements clés (ex. paiement validé, affectation classe).
- Ciblage par rôle ou groupe d’utilisateurs.
- Traçabilité du statut d’envoi (succès/échec).

**Dépendances**
- Accounts, Students, Finance.

### US-NOT-02 (P3) — Préférences de notification
**En tant qu’** utilisateur, **je veux** configurer mes préférences, **afin de** recevoir les alertes pertinentes.

**Critères d’acceptation**
- Activation/désactivation par canal supporté.
- Les préférences sont prises en compte pour les nouveaux envois.

**Dépendances**
- Notifications (US-NOT-01), Accounts.

---

## 7) Dashboard

### US-DAS-01 (P2) — Vue synthétique par rôle
**En tant qu’** utilisateur, **je veux** voir un tableau de bord adapté à mon rôle, **afin de** suivre mes indicateurs clés.

**Critères d’acceptation**
- Widgets affichés selon rôle (admin, scolarité, finance, direction).
- Données limitées au périmètre école autorisé.
- Indicateurs mis à jour à l’actualisation de la page.

**Dépendances**
- Accounts, Students, Finance, Academics.

### US-DAS-02 (P3) — Alertes opérationnelles
**En tant qu’** administrateur, **je veux** visualiser les alertes (impayés, échéances, anomalies), **afin de** prioriser les actions.

**Critères d’acceptation**
- Liste d’alertes triable par criticité/date.
- Chaque alerte renvoie vers l’écran de traitement.

**Dépendances**
- Dashboard (US-DAS-01), Finance, Students, Notifications.

---

## 8) Reports

### US-REP-01 (P2) — Générer les rapports standards
**En tant qu’** direction d’école, **je veux** générer des rapports (effectifs, encaissements), **afin de** piloter l’activité.

**Critères d’acceptation**
- Sélection d’une période et d’un périmètre école/campus.
- Génération d’un rapport lisible à l’écran.
- Export disponible (au moins un format : PDF ou tableur).

**Dépendances**
- Accounts, Students, Finance, Academics.

### US-REP-02 (P3) — Historique et relance des exports
**En tant qu’** utilisateur autorisé, **je veux** retrouver mes exports récents, **afin de** éviter de régénérer inutilement.

**Critères d’acceptation**
- Historique des exports par utilisateur.
- Téléchargement d’un export existant encore valide.

**Dépendances**
- Reports (US-REP-01), Accounts.

---

## Dépendances transverses (vue d’ensemble)
- **Socle v1** : Schools → Accounts → Academics/Students → Finance.
- **Modules de valorisation** : Notifications, Dashboard, Reports dépendent du socle et consomment ses événements/données.
- **Ordre recommandé de livraison** :
  1. Schools
  2. Accounts
  3. Academics
  4. Students
  5. Finance
  6. Dashboard
  7. Reports
  8. Notifications

## Hors périmètre explicite de ce backlog v1
- Modélisation détaillée des entités et schémas techniques.
- Règles d’intégration externes (SMS provider, passerelles de paiement, etc.).
- Optimisations non-fonctionnelles avancées (scalabilité fine, BI avancée).
