# Hypothèses de calcul des KPI dashboard

Ce document aligne les hypothèses produit/technique pour les indicateurs affichés au tableau de bord.

## 1) Effectifs
- **Source principale** : modèle `students.Student` (fallback `Eleve`, `Enrollment` si renommage futur).
- **Query** : `count()` sur le queryset filtré par périmètre autorisé.
- **Périmètre** :
  - superuser : accès global,
  - sinon : filtre par `school`/`ecole` si la colonne existe,
  - sinon : filtre par `user`/`created_by` si la colonne existe,
  - sinon : aucun accès (queryset vide).

## 2) Paiements
- **Source principale** : modèle `finance.Payment` (fallback `Paiement`, `Invoice`).
- **Query** : `aggregate(Sum('amount'))` (fallback sur `montant`), valeur par défaut `0`.
- **Sortie KPI** : montant total brut sur le périmètre autorisé.

## 3) Échéances en retard
- **Source principale** : modèle `academics.Schedule` (fallback `Echeance`, `AcademicPeriod`).
- **Query** :
  - date d'échéance sur `due_date` (ou `date_echeance`),
  - filtre `< date du jour`,
  - exclusion des statuts `paid/paye/payé` si colonne `status`/`statut` disponible.
- **Sortie KPI** : nombre d'éléments en retard.

## 4) Anomalies dossiers élèves
- **Source principale** : modèle étudiant filtré au périmètre.
- **Règles d'anomalies** (OR logique) :
  - `registration_number` vide/null,
  - `matricule` vide/null,
  - `birth_date` null.
- **Sortie KPI** : nombre de dossiers comportant au moins une anomalie.

## Notes d'implémentation
- Les fonctions d'agrégation sont centralisées dans `dashboard/services.py` pour alléger la vue.
- Les fonctions sont conçues pour être réutilisables et tolérantes aux variantes de nommage de champs/modèles.
