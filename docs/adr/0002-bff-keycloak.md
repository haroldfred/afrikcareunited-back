# ADR 0002 — BFF devant Keycloak : aucun jeton dans le navigateur

- Statut : acceptée, 24 octobre 2026
- Origine : Décisions D-04 et D-16 ; RFC 10017 (OAuth 2.0 pour les applications navigateur).

## Contexte

Une application de santé ne doit pas exposer de jeton d'accès au JavaScript du navigateur (vol par script injecté). Les comptes et la double authentification relèvent d'un fournisseur d'identité éprouvé.

## Décision

Keycloak 26.8 authentifie (mot de passe, TOTP, codes de secours, blocage après 5 échecs). Le back-end est un client confidentiel (`acu-bff`, code d'autorisation avec PKCE), garde les jetons dans la session serveur (Spring Session JDBC) et pose un cookie HttpOnly `__Host-acu_session`. Toute modification porte le jeton CSRF (`X-XSRF-TOKEN`). Le back-end tient lui-même le verrouillage (15 min), la durée maximale verrouillée (2 h) et la durée absolue (12 h) ; les durées de Keycloak ne sont qu'un filet. Deux realms : les organisations, et l'équipe AfrikCareUnited à part.

## Conséquences

Le navigateur ne voit jamais de jeton. Le déverrouillage passe par une fenêtre Keycloak (`prompt=login`, `max_age=0`), vérifiée par le back-end (même personne, heure d'authentification, second facteur). La console de compte de Keycloak est désactivée : Mon compte passe par le back-end.
