# Environnement local (lot L1)

PostgreSQL 18.6, Keycloak 26.8.1 avec les realms `afrikcareunited` et `afrikcareunited-equipe`, Mailpit.
Données synthétiques uniquement ; aucun e-mail ne part (Mailpit les garde).

## Démarrer

```bash
cd infra
./generer-env.sh          # crée .env (secrets aléatoires, droits 600) ; ne remplace jamais un .env existant
docker compose up -d
docker compose ps         # postgres et keycloak passent à « healthy »
```

| Service | Adresse (poste local uniquement) | Accès |
| --- | --- | --- |
| PostgreSQL | localhost:5432, bases `afrikcareunited` et `keycloak` | rôles et mots de passe dans `.env` |
| Keycloak | http://localhost:8180 (console : /admin) | `ACU_KEYCLOAK_ADMIN_USER` / `ACU_KEYCLOAK_ADMIN_PASSWORD` |
| Mailpit | http://localhost:8025 (SMTP : localhost:1025) | aucun |

Hors de Docker, sur le poste (D-26) : le back-end (profil `local`) écoute sur http://localhost:8086 et l'application
Angular (`npm start`) sur http://localhost:4220, qui relaie `/api` vers le back-end. Keycloak renvoie le navigateur vers
cette adresse après la connexion (`ACU_PUBLIC_URL`) et signale les déconnexions au back-end
(`ACU_BACKEND_INTERNAL_URL`). Keycloak n'importe les realms qu'à son premier démarrage : après un changement de ces deux
adresses, `docker compose down -v` puis `docker compose up -d` (efface aussi les données locales).

Vérifier l'initialisation de PostgreSQL :

```bash
set -a; source .env; set +a
PGPASSWORD="$ACU_PG_SUPERUSER_PASSWORD" psql -h localhost -U postgres -d afrikcareunited \
  -v ON_ERROR_STOP=1 -f postgres/verifier-initialisation.sql
```

## Ce qui est en place

- **PostgreSQL** (`postgres/initdb/01-bases-et-roles.sh`, au premier démarrage) : bases `afrikcareunited` et
  `keycloak` séparées ; rôles `acu_owner` (migrations), `acu_app`, `acu_platform`, `acu_audit` (connexions de
  l'application, sans BYPASSRLS) et `acu_definer` (sans connexion, seul rôle BYPASSRLS, propriétaire des fonctions
  dédiées) ; schéma `public` fermé à la création ; extensions `btree_gist`, `pg_trgm`, `unaccent`.
- **Keycloak** (`keycloak/realms/`, importés au démarrage) : inscription libre désactivée, e-mails uniques,
  connexion par e-mail ou identifiant ; blocage 15 min après 5 échecs ; mots de passe de 12 caractères au moins,
  différents de l'identifiant, de l'e-mail et des 3 précédents, hors liste des mots de passe courants ; TOTP à
  6 chiffres et codes de secours ; mot de passe oublié qui demande le code à qui l'a activé et ne retire jamais
  l'application d'authentification ; sessions en filet (30 min, 12 h) ; liens de 30 min ; français par défaut et
  anglais ; événements conservés 7 jours, sans recopie dans le journal du serveur ; console de compte désactivée.
  Clients : `acu-bff` (confidentiel, PKCE, mappeur AMR, déconnexion signalée au back-end), `acu-confirm` (page de
  mot de passe seule), `acu-admin` (compte de service limité). Realm de l'équipe : double authentification toujours
  exigée, hors de portée du compte de service des organisations.
- **Mailpit** : SMTP local, interface web pour lire les e-mails envoyés par Keycloak et le back-end.

## À savoir

- `start-dev` est réservé au poste de développement (HTTP). La recette et la production démarrent Keycloak en mode
  `start` derrière TLS (lot L13).
- La liste `keycloak/password-blacklists/acu-mots-de-passe-courants.txt` est une **amorce** : elle est à remplacer,
  avant la recette, par une liste complète de mots de passe courants (par exemple les 100 000 plus fréquents).
- Les pages de connexion et e-mails de Keycloak gardent le thème par défaut jusqu'au thème AfrikCareUnited (lot L12).
- Réinitialiser l'environnement : `docker compose down -v` (efface les données locales), puis `docker compose up -d`.
