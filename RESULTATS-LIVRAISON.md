# Résultats de la livraison du 24 octobre 2026 — afrikcareunited-back

Lots livrés : **L0** (projet Maven, paquets, CI, décisions d'architecture) et **L1** (environnement local).

## Ce qui n'a pas pu être exécuté

Le dépôt Maven central, Docker Hub, quay.io et GitHub n'étaient pas joignables depuis l'environnement de travail
(refus du proxy réseau), et Docker n'y est pas installé. En conséquence :

- **`mvn verify` n'a pas été lancé** : le projet n'a été ni compilé ni testé ; `ModularityTests` et
  `ArchitectureTests` n'ont pas tourné ; aucune couverture JaCoCo.
- **`docker compose up` n'a pas été lancé** : l'import des deux realms par Keycloak 26.8.1 n'a pas été essayé.

Ces deux vérifications sont les premières du lot L2, dès que l'accès au réseau est ouvert ; le workflow
`.github/workflows/back-ci.yml` les fait aussi (construction, démarrage de la pile, découverte OIDC des deux realms).

## Ce qui a été exécuté (24 octobre 2026), avec les résultats obtenus

| Contrôle | Commande | Résultat |
| --- | --- | --- |
| Syntaxe Java | `javac -proc:none` (JDK 21) sur les 14 fichiers Java | aucune erreur de syntaxe ; seules restent les erreurs de dépendances absentes (Spring, ArchUnit, JUnit), attendues sans Maven |
| pom.xml, YAML | analyse XML et YAML | pom.xml bien formé ; application.yaml, application-local.yaml, docker-compose.yml, workflow et redocly.yaml valides |
| Contrat d'API | `npx @redocly/cli@2.60.0 lint …` | valide ; 2 contrôles ignorés et justifiés (/auth/login et /auth/reauth répondent par une redirection) |
| Contrat d'API | `openapi-spec-validator` 0.8.4 | OK |
| Contrat d'API | `python3 tools/check_contract.py …` | 64 chemins, 75 opérations, 99 schémas, 12 permissions, 58 actions de journal, 36 codes d'erreur ; tous les contrôles passent |
| Realms Keycloak | `python3 tools/check_realms.py infra/keycloak/realms` | conformes, aucun secret en clair |
| Contre-épreuve des realms | 4 écarts introduits volontairement (secret en clair, étape « Reset OTP », 30 échecs autorisés, écouteur jboss-logging) | les 4 détectés |
| Realms et générateur | `tools/realms/build_realms.py` puis comparaison | fichiers identiques |
| Environnement local | `python3 tools/check_infra.py infra` | 3 services aux versions épinglées, ports sur 127.0.0.1, 15 variables déclarées, aucun secret écrit |
| Génération de infra/.env | `infra/generer-env.sh` | 11 secrets aléatoires de 32 caractères, droits 600, aucun « a-generer » restant ; second lancement sans effet |
| Initialisation de PostgreSQL | `01-bases-et-roles.sh` puis `verifier-initialisation.sql` sur un serveur **PostgreSQL 18.4 réel** | conforme : 6 rôles, 2 bases, 3 extensions ; refus sans variables d'environnement ; mot de passe contenant des guillemets accepté sans injection |
| Modèle d'isolation (essai) | table en FORCE ROW LEVEL SECURITY, fonction SECURITY DEFINER possédée par acu_definer | sans organisation fixée : 0 ligne ; dans l'organisation : 1 ligne ; fonction dédiée : 2 lignes ; propriétaire soumis à la RLS ; acu_app ne crée pas de schéma et ne prend pas acu_definer |
| Workflow de CI | `actionlint` 1.7.12 | aucune erreur |
| Secrets | `detect-secrets` (Yelp) sur tout le dossier | 3 signalements, tous des faux positifs examinés : le mot « password » dans la politique de mots de passe des deux realms et la constante AMR « pwd » ; aucun secret |

PostgreSQL 18.4 provient du paquet npm `@embedded-postgres/linux-x64` 18.4.0-beta.17 (le suffixe « beta » est celui
de l'emballage npm ; le serveur est la version 18.4 publiée). Il n'a servi qu'à cette vérification et n'est pas une
dépendance du projet, qui utilise l'image `postgres:18.6`.

## Défauts trouvés par ces vérifications et corrigés

- Le propriétaire de la base possédait le schéma `public` (comportement de PostgreSQL ≥ 15) et pouvait y créer des
  objets : l'initialisation rend ce schéma au superutilisateur.
- `generer-env.sh` s'arrêtait au premier secret (SIGPIPE de `tr` avec `pipefail`) et laissait un `.env` incomplet :
  corrigé et vérifié.
- Trois règles pour les migrations du lot L2 (propriété et droits des fonctions dédiées) : notées dans
  `docs/architecture.md`.

Empreinte SHA-256 du contrat : `35367923ec987ef034bcdef3de9d59b879ff8f4aac69faf617035b5e3adeed8f`
(identique dans afrikcareunited-front).
