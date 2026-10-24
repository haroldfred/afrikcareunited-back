# ADR 0006 — Livraison en deux dossiers, sans dépôt partagé

- Statut : acceptée, 24 octobre 2026
- Origine : Décision D-24 (remplace en partie D-15).

## Contexte

Le commanditaire reçoit le code à chaque livraison, sans dépôt GitHub pour l'instant.

## Décision

Deux dossiers livrés en archives : `afrikcareunited-front` et `afrikcareunited-back`. Le dossier back porte aussi le contrat d'API (source de vérité), l'environnement local (`infra/`) et la documentation technique ; le dossier front a une copie du contrat. Chaque dossier contient ses workflows de CI GitHub Actions, prêts pour un dépôt futur. Chaque livraison joint ses résultats réellement obtenus (`RESULTATS-LIVRAISON.md`).

## Conséquences

La copie du contrat côté front doit rester identique à l'original : le CI du front vérifie que ses types générés correspondent au contrat ; une comparaison d'empreintes est indiquée dans chaque livraison.
