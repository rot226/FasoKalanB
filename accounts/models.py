from django.db import models

# Réserve d'architecture (future multi-tenancy) :
# cette app est candidate pour gérer le rattachement utilisateur <-> école
# (membership, rôles/permissions par tenant), sans implémentation métier à ce stade.
