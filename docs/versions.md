# Versions retenues — back-end et environnement

Vérifiées le 24 octobre 2026 sur les sites officiels et les annonces de publication ; épinglées à la version exacte.
Aucune version préliminaire. À revérifier au lot L2, au premier accès au dépôt Maven central depuis le poste de construction.

| Composant | Version | Publication | Remarque |
| --- | --- | --- | --- |
| Java (Eclipse Temurin) | 25.0.5+8 | 22 octobre 2026 | Java 25, version à support long. |
| Maven | 3.9.11 ou plus récent | | Exigé par maven-enforcer-plugin. Le Maven Wrapper sera ajouté au L2 (téléchargement requis). |
| Spring Boot | 4.1.2 | 23 octobre 2026 | Démarreurs modulaires de Spring Boot 4 (webmvc, security-oauth2-client, flyway, jdbc, session-jdbc…). |
| Spring Modulith | 2.1.1 | | BOM `spring-modulith-bom`. |
| Testcontainers | géré par Spring Boot 4.1.2 (série 2.x) | | Artefacts `testcontainers-postgresql`, `testcontainers-junit-jupiter`. |
| testcontainers-keycloak | 4.4.0 | 1er octobre 2026 | Keycloak 26.8 par défaut. |
| ArchUnit | 1.5.0 | 4 août 2026 | `archunit-junit5`. |
| openapi-generator-maven-plugin | 7.26.0 | 6 octobre 2026 | Générateur `spring`, interfaces seules, option Spring Boot 4. |
| JaCoCo | 0.8.15 | 4 juin 2026 | Prise en charge officielle de Java 26 (donc 25). |
| PostgreSQL | 18.6 | 13 août 2026 | Image `postgres:18.6`. |
| Keycloak | 26.8.1 | 13 octobre 2026 | Image `quay.io/keycloak/keycloak:26.8.1`. |
| Mailpit | 1.32.0 | 23 octobre 2026 | Image `axllent/mailpit:v1.32.0` ; corrige les vulnérabilités de 2026 des versions ≤ 1.30.6. Développement et test uniquement. |
| Redocly CLI | 2.60.0 | | Validation du contrat (CI). |
| openapi-spec-validator | 0.8.4 | | Validation du contrat (CI). |

Gérés par le parent Spring Boot 4.1.2 (versions non répétées dans le pom.xml) : Flyway et son module PostgreSQL,
pilote PostgreSQL, Spring Security, Spring Session, JUnit, AssertJ, maven-enforcer-plugin, maven-failsafe-plugin,
cyclonedx-maven-plugin.

## Ce qui reste à faire au premier accès au dépôt Maven central

- Construire (`mvn verify`), ajouter le Maven Wrapper (`mvn wrapper:wrapper`) et épingler les empreintes (digest) des
  images Docker.
- Confirmer les noms des démarreurs modulaires de Spring Boot 4.1 et l'option `useSpringBoot4` du générateur
  (une option inconnue est ignorée par le générateur ; un démarreur absent fait échouer la construction).
