# Référentiel KPI Dashboard par rôle (version de travail)

## Objectif
Ce document décrit, **par rôle**, la liste des KPI à afficher, leur définition de calcul, la période de calcul, le périmètre de données (école/campus) et la règle de priorité d’affichage.

> Statut : **à valider avec les responsables métier** avant implémentation complète.

## Période et périmètre — conventions globales

- **Date de référence** : date courante serveur (UTC) au moment du calcul.
- **Fuseau fonctionnel recommandé** : fuseau local de l’établissement (à figer en validation métier).
- **Période par défaut dashboard** :
  - KPI de stock (effectifs, anomalies, retards) : valeur **instantanée à date**.
  - KPI de flux monétaire (paiements) : **mois en cours**, du 1er jour 00:00:00 au dernier jour 23:59:59.
- **Périmètre de données** :
  - **Global réseau** : toutes les écoles/campus autorisés à l’utilisateur.
  - **École** : une école donnée.
  - **Campus** : un campus donné (si la donnée campus existe).

---

## Catalogue des KPI et formules de calcul

### KPI-01 — Effectifs élèves
- **Définition** : nombre d’élèves actifs dans le périmètre sélectionné.
- **Formule** : `COUNT(students)` après filtres de périmètre + filtres d’accès.
- **Période** : instantané (à date).
- **Périmètre** : global réseau / école / campus.

### KPI-02 — Paiements encaissés
- **Définition** : montant total encaissé sur la période.
- **Formule** : `SUM(payment.amount)` avec statut de paiement validé/encaissé.
- **Période** : mois en cours (par défaut).
- **Périmètre** : global réseau / école / campus.

### KPI-03 — Échéances en retard
- **Définition** : nombre d’échéances passées non soldées.
- **Formule** : `COUNT(echeances WHERE due_date < aujourd’hui AND status NOT IN ('paid','payé','paye'))`.
- **Période** : instantané (à date).
- **Périmètre** : global réseau / école / campus.

### KPI-04 — Dossiers élèves avec anomalies
- **Définition** : nombre de dossiers avec au moins une donnée obligatoire manquante.
- **Formule** : `COUNT(students WHERE registration_number IS NULL/VIDE OR matricule IS NULL/VIDE OR birth_date IS NULL)`.
- **Période** : instantané (à date).
- **Périmètre** : global réseau / école / campus.

---

## KPI par rôle (liste exacte à afficher)

## 1) Direction réseau (super-admin)
- **KPI affichés (ordre cible)** :
  1. Effectifs élèves (KPI-01)
  2. Paiements encaissés (KPI-02)
  3. Échéances en retard (KPI-03)
  4. Dossiers avec anomalies (KPI-04)
- **Période** :
  - KPI-01/03/04 : instantané
  - KPI-02 : mois en cours
- **Périmètre** : global réseau (toutes écoles/campus autorisés).
- **Priorité d’affichage** :
  - si surcharge d’écran, garder au minimum KPI-02 puis KPI-03 (priorité métier finance/risque),
  - ensuite KPI-01,
  - enfin KPI-04.

## 2) Direction d’école
- **KPI affichés (ordre cible)** :
  1. Effectifs élèves (KPI-01)
  2. Paiements encaissés (KPI-02)
  3. Échéances en retard (KPI-03)
  4. Dossiers avec anomalies (KPI-04)
- **Période** : identique Direction réseau.
- **Périmètre** : école courante (et campus rattachés, selon droits).
- **Priorité d’affichage** :
  - priorité 1 : KPI-03,
  - priorité 2 : KPI-02,
  - priorité 3 : KPI-01,
  - priorité 4 : KPI-04.

## 3) Comptabilité / Finance
- **KPI affichés (ordre cible)** :
  1. Paiements encaissés (KPI-02)
  2. Échéances en retard (KPI-03)
- **Période** :
  - KPI-02 : mois en cours,
  - KPI-03 : instantané.
- **Périmètre** : école/campus selon rattachement utilisateur.
- **Priorité d’affichage** :
  - toujours KPI-02 en premier,
  - puis KPI-03,
  - masquer les autres KPI pour éviter le bruit.

## 4) Scolarité / Vie scolaire
- **KPI affichés (ordre cible)** :
  1. Effectifs élèves (KPI-01)
  2. Dossiers avec anomalies (KPI-04)
- **Période** : instantané.
- **Périmètre** : école/campus selon rattachement utilisateur.
- **Priorité d’affichage** :
  - KPI-04 en surbrillance si valeur > 0,
  - sinon KPI-01 en premier plan.

---

## Règles de priorité d’affichage (fallback technique)

En cas d’espace limité ou d’indisponibilité partielle des données :

1. Afficher d’abord les KPI critiques du rôle (cf. section par rôle).
2. En cas d’égalité de priorité, utiliser l’ordre : `KPI-02 > KPI-03 > KPI-01 > KPI-04`.
3. Si un KPI échoue au calcul, l’afficher avec état "indisponible" sans bloquer les autres cartes.

---

## Validation métier obligatoire avant implémentation complète

### Parties prenantes à valider
- Responsable métier Finance,
- Responsable Scolarité,
- Direction d’établissement,
- Référent Produit.

### Points de validation
- Liste exacte des KPI par rôle,
- Définition métier finale des statuts de paiement « encaissé » et « en retard »,
- Granularité de périmètre (école seule vs école + campus),
- Fuseau horaire de référence pour les calculs,
- Ordre/priorité d’affichage final.

### Critère de sortie
Implémentation complète autorisée uniquement après approbation explicite (compte-rendu ou ticket validé) des points ci-dessus.
