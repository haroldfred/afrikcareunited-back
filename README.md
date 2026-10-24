# AfrikCareUnited — back-end (afrikcareunited-back)

API et BFF de la plateforme AfrikCareUnited : Java 25, Spring Boot 4.1, Spring Modulith 2.1, PostgreSQL 18 avec
Row-Level Security, Keycloak 26.8. Module en cours : **M0 Socle**.
Livraison du 24 octobre 2026 : lots **L0** (projet, outillage, CI) et **L1** (environnement local).

Ce dossier porte aussi, pour les deux applications (D-24) :

- le **contrat d'API**, source de vérité : `contracts/afrikcareunited-m0-openapi.yaml` (copie dans `afrikcareunited-front`) ;
- l'**environnement local** : `infra/` (PostgreSQL, Keycloak et ses deux realms, Mailpit) ;
- la **documentation technique** : `docs/` (architecture, décisions d'architecture, versions).

## État de cette livraison — à lire

Le dépôt Maven central n'était pas joignable depuis l'environnement où ce code a été écrit : **le projet Maven n'a
été ni compilé ni testé**. Les sources Java ont seulement été analysées par `javac` 21 (aucune erreur de syntaxe ;
les seules erreurs portent sur les dépendances absentes). Tout ce qui pouvait être exécuté l'a été :
contrôles du contrat, des realms et de l'environnement local, initialisation de PostgreSQL sur une instance 18.4 réelle.
Le détail est dans `RESULTATS-LIVRAISON.md`. La compilation et les tests Java commencent au lot L2.

## Structure : un seul pom.xml, un paquet par fonctionnalité (D-25)

```
src/main/java/com/afrikcareunited/
  AfrikCareUnitedApplication.java   point d'entrée (@Modulithic)
  shared/        noyau partagé : erreurs RFC 9457, UUIDv7, horloge, contexte, idempotence (ouvert)
  contract/      interfaces et objets générés depuis le contrat, à la construction (ouvert)
  session/       BFF : connexion Keycloak, session, verrouillage, contexte affiché
  home/          éléments « À traiter » de l'accueil
  identity/      identité unique, Mon compte, confirmations par e-mail, événements Keycloak
  organization/  organisations et établissements
  access/        rôles, permissions, affectations, calcul des droits
  membership/    utilisateurs et invitations
  audit/         journal d'audit chaîné, points de contrôle, export
  support/       accès de support, administrateur de secours
  notification/  e-mails transactionnels FR/EN par la boîte d'envoi
```

Chaque module déclare dans son `package-info.java` ce qu'il contient, ses lots et les seuls modules dont il peut
dépendre ; `ModularityTests` (Spring Modulith) et `ArchitectureTests` (ArchUnit) le vérifient à chaque construction.

## Prérequis

- JDK 25 (Eclipse Temurin 25.0.5 utilisé pour les versions) et Maven 3.9.11 ou plus récent.
- Docker et Docker Compose v2, pour l'environnement local et les tests d'intégration (Testcontainers).
- Python 3 avec PyYAML et Node.js 24, pour les contrôles du contrat et de l'environnement (`tools/`).

## Commandes

| Commande | Effet |
| --- | --- |
| `cd infra && ./generer-env.sh && docker compose up -d` | Démarre PostgreSQL, Keycloak (realms importés) et Mailpit. Voir `infra/README.md`. |
| `mvn verify` | Construit, génère les interfaces depuis le contrat, lance les tests unitaires et d'intégration, mesure la couverture (80 %), produit la nomenclature CycloneDX. |
| `set -a; source infra/.env; set +a; mvn spring-boot:run -Dspring-boot.run.profiles=local` | Lance le back-end sur http://localhost:8086 (à partir du lot L2) ; l'application Angular (`npm start`) le joint depuis http://localhost:4220. |
| `npx --yes @redocly/cli@2.60.0 lint contracts/afrikcareunited-m0-openapi.yaml --config redocly.yaml` | Valide le contrat. |
| `python3 tools/check_contract.py contracts/afrikcareunited-m0-openapi.yaml` | Contrôles propres au projet sur le contrat. |
| `python3 tools/check_realms.py infra/keycloak/realms` | Vérifie les réglages exigés des deux realms et l'absence de secret. |
| `python3 tools/check_infra.py infra` | Vérifie l'environnement local : versions, ports, variables, secrets. |
| `python3 tools/realms/build_realms.py infra/keycloak/realms` | Régénère les deux realms (source unique des réglages communs). |

## Configuration et secrets

Aucun secret n'est versionné. En local, `infra/generer-env.sh` crée `infra/.env` (droits 600) avec des valeurs
aléatoires ; au déploiement, les mêmes variables viennent du coffre de l'hébergeur. `src/main/resources/application.yaml`
ne contient que des marqueurs `${VARIABLE}` et des valeurs locales sans risque.
