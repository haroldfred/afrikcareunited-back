# ADR 0003 — Isolation des organisations par Row-Level Security forcée

- Statut : acceptée, 24 octobre 2026
- Origine : Décision D-03 : un seul code multi-tenant, en SaaS mutualisé ou en instance dédiée.

## Contexte

Une erreur de code ne doit pas suffire à montrer les données d'une organisation à une autre.

## Décision

Toutes les tables d'une organisation portent son identifiant, des clés étrangères composées (organisation, identifiant) et sont en `FORCE ROW LEVEL SECURITY`. Les rôles de connexion (`acu_app`, `acu_platform`, `acu_audit`) n'ont pas BYPASSRLS et ne changent jamais de rôle ; le serveur fixe l'organisation au début de chaque transaction. Les chemins qui traversent les organisations passent par des fonctions `SECURITY DEFINER` dédiées, possédées par `acu_definer` (sans connexion), chacune avec ses tests. Les migrations utilisent `acu_owner`, jamais l'application.

## Conséquences

Une ressource d'une autre organisation répond 404 ; les tests d'isolation tournent sur toutes les opérations. Règles vérifiées sur PostgreSQL 18.4 au lot L1 (voir `docs/architecture.md`).
