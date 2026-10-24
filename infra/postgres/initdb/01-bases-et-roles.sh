#!/usr/bin/env bash
# Initialisation de PostgreSQL au premier démarrage (image officielle : /docker-entrypoint-initdb.d).
# Crée les bases et les rôles du M0 (conception détaillée, « Isolation des organisations ») :
#   acu_owner     propriétaire des tables, utilisé par les migrations Flyway uniquement
#   acu_app       requêtes des organisations, soumis à la Row-Level Security
#   acu_platform  requêtes de l'équipe AfrikCareUnited, pool distinct
#   acu_audit     séquenceur du journal d'audit, points de contrôle et vérification
#   acu_definer   sans connexion, propriétaire des fonctions SECURITY DEFINER (BYPASSRLS)
#   keycloak      base de Keycloak, séparée de celle de l'application
# Aucun mot de passe n'est écrit ici : ils viennent de l'environnement (infra/.env).
set -euo pipefail

for variable in ACU_DB_OWNER_PASSWORD ACU_DB_APP_PASSWORD ACU_DB_PLATFORM_PASSWORD ACU_DB_AUDIT_PASSWORD ACU_KEYCLOAK_DB_PASSWORD; do
  if [ -z "${!variable:-}" ]; then
    echo "Variable d'environnement manquante : ${variable} (voir infra/.env.example)" >&2
    exit 1
  fi
done

# Les mots de passe passent par des variables psql (:'nom'), jamais par une chaîne SQL construite à la main.
psql -v ON_ERROR_STOP=1 --username "${POSTGRES_USER:-postgres}" --dbname postgres \
  -v owner_password="${ACU_DB_OWNER_PASSWORD}" \
  -v app_password="${ACU_DB_APP_PASSWORD}" \
  -v platform_password="${ACU_DB_PLATFORM_PASSWORD}" \
  -v audit_password="${ACU_DB_AUDIT_PASSWORD}" \
  -v keycloak_password="${ACU_KEYCLOAK_DB_PASSWORD}" <<'EOSQL'
CREATE ROLE acu_owner    LOGIN   PASSWORD :'owner_password'    NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;
CREATE ROLE acu_app      LOGIN   PASSWORD :'app_password'      NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;
CREATE ROLE acu_platform LOGIN   PASSWORD :'platform_password' NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;
CREATE ROLE acu_audit    LOGIN   PASSWORD :'audit_password'    NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;
CREATE ROLE acu_definer  NOLOGIN                               NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION BYPASSRLS;
CREATE ROLE keycloak     LOGIN   PASSWORD :'keycloak_password' NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;

-- Les migrations (acu_owner) donnent les fonctions dédiées à acu_definer : il faut pouvoir prendre ce rôle
-- (SET), sans en hériter les droits (INHERIT FALSE).
GRANT acu_definer TO acu_owner WITH INHERIT FALSE, SET TRUE;

CREATE DATABASE afrikcareunited OWNER acu_owner ENCODING 'UTF8' TEMPLATE template0;
CREATE DATABASE keycloak OWNER keycloak ENCODING 'UTF8' TEMPLATE template0;

REVOKE ALL ON DATABASE afrikcareunited FROM PUBLIC;
REVOKE ALL ON DATABASE keycloak FROM PUBLIC;
GRANT CONNECT ON DATABASE afrikcareunited TO acu_app, acu_platform, acu_audit;

\connect afrikcareunited

-- Rien ne se crée dans le schéma public ; les schémas du M0 (org, iam, platform, audit, ops) viennent des migrations.
-- Depuis PostgreSQL 15, le propriétaire de la base possède aussi le schéma public : on le lui retire.
ALTER SCHEMA public OWNER TO CURRENT_USER;
REVOKE ALL ON SCHEMA public FROM PUBLIC;
GRANT USAGE ON SCHEMA public TO acu_owner, acu_app, acu_platform, acu_audit, acu_definer;

-- Extensions du modèle de données (installées ici : elles exigent un superutilisateur).
--   btree_gist : contrainte d'exclusion des périodes d'affectation
--   pg_trgm    : recherche par trigrammes sur le nom, l'e-mail et l'identifiant
--   unaccent   : recherche insensible aux accents (US-05)
CREATE EXTENSION IF NOT EXISTS btree_gist WITH SCHEMA public;
CREATE EXTENSION IF NOT EXISTS pg_trgm WITH SCHEMA public;
CREATE EXTENSION IF NOT EXISTS unaccent WITH SCHEMA public;
EOSQL

echo "Bases afrikcareunited et keycloak, rôles du M0 et extensions créés."
