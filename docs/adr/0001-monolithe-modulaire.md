# ADR 0001 — Monolithe modulaire : un seul projet Maven, un paquet par fonctionnalité

- Statut : acceptée, 24 octobre 2026
- Origine : Décision du commanditaire D-04 (Java 25, Spring Boot 4.1, Spring Modulith) et D-25 (un seul pom.xml, chaque fonctionnalité dans un paquet).

## Contexte

Le M0 et les modules suivants (patients, consultations, laboratoire, facturation…) partagent l'identité, les droits, le journal et la session. Une équipe réduite doit livrer vite, sans multiplier les déploiements.

## Décision

Un seul projet Maven et un seul déployable. Chaque fonctionnalité est un paquet direct de `com.afrikcareunited`, module applicatif Spring Modulith : ses classes publiques de premier niveau forment son interface, ses sous-paquets sont internes. Chaque `package-info.java` déclare les modules dont il peut dépendre. Les échanges entre modules passent par ces interfaces ou par des événements publiés dans la transaction (boîte d'envoi de Spring Modulith).

## Conséquences

Frontières vérifiées à chaque construction (`ModularityTests`, `ArchitectureTests`) ; documentation des modules générée. Un module pourra être extrait plus tard si la charge l'exige, ses frontières étant déjà nettes.
