# Décision d’architecture — App Dashboard canonique

## Décision

L’implémentation canonique du dashboard est le package racine **`dashboard`**.

Le namespace historique **`apps.dashboard`** ne doit pas être utilisé dans le chemin actif (imports, routage, configuration Django).

## Règles à respecter

1. `INSTALLED_APPS` doit déclarer **`'dashboard'`** (et non `apps.dashboard`).
2. Le routeur principal doit inclure **`include('dashboard.urls')`** dans `config/urls.py`.
3. Les imports applicatifs (vues, services, tests) doivent cibler le namespace **`dashboard...`**.
4. Toute réintroduction de `apps.dashboard` doit être considérée comme une régression d’architecture.

## Motivation

Cette convention supprime les ambiguïtés de résolution d’imports, évite les incohérences de namespace URL et réduit le risque de divergence entre deux implémentations concurrentes.
