# ADR 0004 — Contrat d'abord : OpenAPI 3.1 et interfaces générées

- Statut : acceptée, 24 octobre 2026
- Origine : Conception détaillée du M0, section « Contrats d'API » ; étape 6 du processus du cahier des charges.

## Contexte

Le front-end et le back-end avancent en parallèle ; ils doivent parler exactement la même langue.

## Décision

Le contrat `contracts/afrikcareunited-m0-openapi.yaml` (75 opérations) est la source de vérité. Le back-end génère à la construction les interfaces Spring (openapi-generator, interfaces seules) que ses contrôleurs implémentent ; le front-end génère ses types (openapi-typescript). Le CI valide le contrat (Redocly CLI, openapi-spec-validator, contrôles du projet) et vérifie que les types du front-end sont à jour.

## Conséquences

Une divergence entre le contrat et le code casse la construction. Toute évolution de l'API commence par le contrat, relu comme du code.
