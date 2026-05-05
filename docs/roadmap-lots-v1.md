# Roadmap v1 en lots (Lot 0 → Lot 5)

## Objectif
Cette roadmap transforme le backlog fonctionnel en un plan de livraison progressif, avec un **ordre conseillé** pour limiter les refontes, sécuriser les dépendances et produire des livrables testables à chaque étape.

## Principes d’ordonnancement (anti-refonte)
1. **Stabiliser le socle technique et la qualité** avant les fonctionnalités métier (Lot 0).
2. **Poser les fondations organisationnelles et de sécurité** (Schools + Accounts) avant les modules consommateurs (Lot 1–2).
3. **Construire le flux métier cœur de bout en bout** (élève → inscription/académique → paiement) avant les vues analytiques (Lot 3–4).
4. **Finir par la valorisation et l’industrialisation** (dashboard/reports/notifications + hardening) pour éviter de recoder des agrégations sur des modèles instables (Lot 5).

---

## Lot 0 — Cadrage, architecture et socle d’exécution
**Durée estimative :** 1 à 2 semaines

### Objectifs
- Cadrer les conventions techniques (structure apps, nommage, gestion des settings par environnement).
- Mettre en place le socle qualité : lint, tests de base, pipeline CI minimale.
- Sécuriser l’environnement de dev (variables d’environnement, secrets, gestion DEBUG).

### Prérequis techniques
- Python 3.12+ et dépendances installables depuis `requirements.txt`.
- Environnement local reproductible (venv, migrations initiales).
- Choix des standards de code/tests validé par l’équipe.

### Livrables
- Charte technique courte (architecture Django, conventions de migration, stratégie de tests).
- Pipeline CI (au minimum : installation, checks Django, tests).
- Matrice d’environnements (dev / préprod / prod) et variables de configuration documentées.

### Risques majeurs
- Sous-estimation de la dette de structure dès le départ (génère des refontes coûteuses ensuite).
- Couverture de tests trop faible, rendant les lots suivants risqués.
- Paramétrage sécurité incomplet (exposition de secrets, DEBUG mal géré).

---

## Lot 1 — Fondations métier : Schools + Accounts
**Durée estimative :** 2 à 3 semaines

### Objectifs
- Implémenter la gestion des écoles/campus (fondation multi-entité).
- Stabiliser l’authentification et les rôles/permissions.
- Garantir l’isolation des données par école selon les droits.

### Prérequis techniques
- Lot 0 validé (CI + base de tests + conventions).
- Modèle d’autorisation choisi (Group/Permission Django ou équivalent).
- Stratégie de contextualisation “école active” définie (session, middleware, filtre systématique).

### Livrables
- CRUD écoles et campus avec activation/désactivation.
- Authentification opérationnelle (login/logout) + rôles de base.
- Contrôles d’accès minimums sur routes et vues critiques.
- Jeux de tests d’accès (permissions, isolation inter-écoles).

### Risques majeurs
- Mauvaise modélisation multi-école provoquant des fuites de données.
- Rôles trop rigides ou trop permissifs, entraînant des reprises dans tous les modules.
- Couplage fort UI/permissions rendant les évolutions difficiles.

---

## Lot 2 — Référentiel académique : Academics
**Durée estimative :** 2 semaines

### Objectifs
- Gérer l’année scolaire, périodes, classes/niveaux et matières.
- Poser un référentiel académique stable pour les inscriptions élèves et la facturation.

### Prérequis techniques
- Lot 1 livré (écoles + comptes + permissions).
- Règles métier validées : unicité année active par école, hiérarchie classe/niveau.
- Stratégie d’archivage/versioning des référentiels (au minimum statut actif/inactif).

### Livrables
- Écrans et services de gestion année/périodes/classes/matières.
- Validations métier (cohérence dates, unicité année active).
- Données de démonstration minimales pour tests transverses.

### Risques majeurs
- Référentiel instable (renommages fréquents de classes/niveaux) impactant Students/Finance.
- Règles calendaires floues (chevauchements de périodes, ambiguïtés d’année active).
- Absence de stratégie d’historisation, source d’incohérences futures.

---

## Lot 3 — Cycle de vie élève : Students
**Durée estimative :** 2 à 3 semaines

### Objectifs
- Enregistrer les élèves et gérer l’affectation en classe.
- Structurer le cycle “création dossier élève → inscription/académique”.

### Prérequis techniques
- Lot 2 stabilisé (référentiel classes/années disponible).
- Politique d’identifiant élève unique par école définie.
- Décision sur l’historique minimal d’affectation (modèle courant + traces).

### Livrables
- CRUD élève + recherche/liste + statut actif.
- Mécanisme d’affectation à une classe active.
- Historique minimum des changements d’affectation.
- Tests fonctionnels de parcours d’inscription.

### Risques majeurs
- Dédoublonnage élève insuffisant (doublons d’identité).
- Affectations hors contraintes académiques (classe inactive, année incohérente).
- Complexité sous-estimée de la reprise de données existantes (si migration externe).

---

## Lot 4 — Monétisation : Finance
**Durée estimative :** 2 à 3 semaines

### Objectifs
- Paramétrer les grilles de frais.
- Enregistrer les paiements et produire un reçu.
- Calculer un solde élève fiable en temps réel.

### Prérequis techniques
- Lot 3 en production interne (élèves et affectations fiables).
- Règles comptables minimales validées (annulation, correction, traçabilité).
- Choix sur l’atomicité transactionnelle des écritures (intégrité DB).

### Livrables
- Paramétrage des frais par classe/niveau/période.
- Enregistrement de paiements avec reçu consultable.
- Moteur de calcul du solde et journal d’événements financiers.
- Tests d’intégrité (double encaissement, annulation, concurrence simple).

### Risques majeurs
- Incohérences de solde dues à des traitements non transactionnels.
- Refacturation rétroactive mal gérée si le référentiel académique évolue.
- Risques d’auditabilité insuffisante (modifications sans traces).

---

## Lot 5 — Valorisation & industrialisation : Dashboard, Reports, Notifications + hardening
**Durée estimative :** 3 à 4 semaines

### Objectifs
- Exploiter les données consolidées via tableaux de bord, rapports et notifications.
- Finaliser la robustesse opérationnelle (sécurité, performance, exploitation).

### Prérequis techniques
- Lots 1 à 4 stabilisés (modèles et événements métier peu volatils).
- Indicateurs KPI définis avec métiers (finance, scolarité, direction).
- Stratégie d’export (format, volumétrie, historisation) validée.

### Livrables
- Dashboard par rôle (widgets clés, alertes opérationnelles prioritaires).
- Rapports standards (effectifs, encaissements) + export.
- Notifications ciblées sur événements critiques (paiement, affectation, échéance).
- Checklist de mise en production : sécurité Django, logs, sauvegarde/restauration, supervision.

### Risques majeurs
- KPIs non alignés métier (tableaux de bord peu exploitables).
- Exports lents/instables sur volumes réels.
- Notifications bruyantes (fatigue utilisateur) ou non fiables (perte d’événements).

---

## Ordre conseillé global (pour limiter les refontes)
**Lot 0 → Lot 1 → Lot 2 → Lot 3 → Lot 4 → Lot 5**

### Pourquoi cet ordre est optimal
- Les modules de **valorisation** (Dashboard/Reports/Notifications) dépendent fortement de la qualité des données produites en amont.
- La **finance** doit s’appuyer sur un référentiel académique stable et des inscriptions élèves fiables.
- Le **socle sécurité/permissions** doit être figé tôt pour éviter de réécrire les contrôles d’accès dans chaque lot.

## Macro-planning indicatif (v1)
- **Durée totale estimée :** 12 à 17 semaines (selon taille équipe, disponibilité PO, niveau d’automatisation tests/CI).
- **Jalons recommandés :**
  - Fin Lot 1 : démonstration “accès sécurisé multi-école”.
  - Fin Lot 3 : démonstration “parcours élève complet”.
  - Fin Lot 4 : démonstration “encaissement + solde + reçu”.
  - Fin Lot 5 : revue de readiness production.
