-- Vérifie l'initialisation de PostgreSQL (rôles, bases, droits, extensions) ; échoue au premier écart.
-- Usage : psql -v ON_ERROR_STOP=1 -h localhost -U postgres -d afrikcareunited -f infra/postgres/verifier-initialisation.sql
DO $$
DECLARE
  r record;
BEGIN
  -- Rôles de connexion : ni superutilisateur, ni BYPASSRLS, ni création de bases ou de rôles.
  FOR r IN SELECT rolname, rolcanlogin, rolsuper, rolbypassrls, rolcreatedb, rolcreaterole
             FROM pg_roles WHERE rolname IN ('acu_owner', 'acu_app', 'acu_platform', 'acu_audit', 'keycloak') LOOP
    IF NOT r.rolcanlogin OR r.rolsuper OR r.rolbypassrls OR r.rolcreatedb OR r.rolcreaterole THEN
      RAISE EXCEPTION 'rôle % : attributs inattendus', r.rolname;
    END IF;
  END LOOP;
  IF (SELECT count(*) FROM pg_roles WHERE rolname IN ('acu_owner', 'acu_app', 'acu_platform', 'acu_audit', 'keycloak')) <> 5 THEN
    RAISE EXCEPTION 'il manque un rôle de connexion';
  END IF;

  -- acu_definer : sans connexion, seul à passer outre la Row-Level Security.
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'acu_definer' AND NOT rolcanlogin AND rolbypassrls AND NOT rolsuper) THEN
    RAISE EXCEPTION 'acu_definer doit être NOLOGIN BYPASSRLS';
  END IF;
  IF (SELECT count(*) FROM pg_roles WHERE rolbypassrls AND NOT rolsuper AND rolname LIKE 'acu%') <> 1 THEN
    RAISE EXCEPTION 'un seul rôle applicatif peut avoir BYPASSRLS';
  END IF;

  -- acu_owner peut prendre le rôle acu_definer sans en hériter.
  IF NOT EXISTS (
      SELECT 1 FROM pg_auth_members m
        JOIN pg_roles g ON g.oid = m.roleid AND g.rolname = 'acu_definer'
        JOIN pg_roles u ON u.oid = m.member AND u.rolname = 'acu_owner'
       WHERE NOT m.inherit_option AND m.set_option) THEN
    RAISE EXCEPTION 'acu_owner doit pouvoir prendre acu_definer (SET) sans héritage';
  END IF;
  IF EXISTS (SELECT 1 FROM pg_auth_members m JOIN pg_roles g ON g.oid = m.roleid
              JOIN pg_roles u ON u.oid = m.member
             WHERE u.rolname IN ('acu_app', 'acu_platform', 'acu_audit') ) THEN
    RAISE EXCEPTION 'les rôles de connexion de l''application ne changent jamais de rôle';
  END IF;

  -- Bases : propriétaires, encodage et droits de connexion.
  IF NOT EXISTS (SELECT 1 FROM pg_database d JOIN pg_roles o ON o.oid = d.datdba
                  WHERE d.datname = 'afrikcareunited' AND o.rolname = 'acu_owner' AND pg_encoding_to_char(d.encoding) = 'UTF8') THEN
    RAISE EXCEPTION 'base afrikcareunited : propriétaire ou encodage inattendu';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_database d JOIN pg_roles o ON o.oid = d.datdba
                  WHERE d.datname = 'keycloak' AND o.rolname = 'keycloak') THEN
    RAISE EXCEPTION 'base keycloak : propriétaire inattendu';
  END IF;
  IF has_database_privilege('keycloak', 'afrikcareunited', 'CONNECT') THEN
    RAISE EXCEPTION 'keycloak ne doit pas se connecter à la base de l''application';
  END IF;
  IF has_database_privilege('acu_app', 'keycloak', 'CONNECT') THEN
    RAISE EXCEPTION 'acu_app ne doit pas se connecter à la base de Keycloak';
  END IF;
  IF NOT has_database_privilege('acu_app', 'afrikcareunited', 'CONNECT') THEN
    RAISE EXCEPTION 'acu_app doit pouvoir se connecter à la base de l''application';
  END IF;

  -- Personne ne crée d'objet dans le schéma public.
  IF has_schema_privilege('acu_app', 'public', 'CREATE') OR has_schema_privilege('acu_owner', 'public', 'CREATE') THEN
    RAISE EXCEPTION 'création interdite dans le schéma public';
  END IF;

  -- Extensions du modèle de données.
  IF (SELECT count(*) FROM pg_extension WHERE extname IN ('btree_gist', 'pg_trgm', 'unaccent')) <> 3 THEN
    RAISE EXCEPTION 'extensions btree_gist, pg_trgm et unaccent attendues';
  END IF;

  RAISE NOTICE 'Initialisation de PostgreSQL conforme : 6 rôles, 2 bases, 3 extensions.';
END
$$;
