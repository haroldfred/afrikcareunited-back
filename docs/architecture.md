# Architecture du back-end

Référence : conception détaillée du M0 v0.1, validée le 24 octobre 2026 (modèle de données, contrats d'API, flux,
plan de tests et plan d'implémentation). Décisions : `docs/adr/`.

## Vue d'ensemble

```
Navigateur ── nginx (application Angular, servie à part) ── /api/v1 ── back-end (BFF + API, ce dossier)
                                                                          ├── PostgreSQL 18 : base afrikcareunited (RLS forcée)
                                                                          ├── Keycloak 26.8 : realms afrikcareunited et afrikcareunited-equipe
                                                                          └── SMTP (Mailpit en local)
```

- **BFF (RFC 10017)** : le back-end parle à Keycloak (code d'autorisation avec PKCE), garde les jetons dans la
  session serveur (Spring Session JDBC) et ne donne au navigateur qu'un cookie HttpOnly `__Host-acu_session`.
- **Contrat d'abord** : `contracts/afrikcareunited-m0-openapi.yaml` génère à la construction les interfaces Spring du
  paquet `contract` ; les contrôleurs les implémentent, toute divergence casse la compilation.
- **Monolithe modulaire** : un seul projet Maven, un paquet par fonctionnalité, frontières vérifiées par Spring Modulith.

## Modules et dépendances permises

| Module | Contenu | Peut dépendre de | Lots |
| --- | --- | --- | --- |
| shared | erreurs RFC 9457, UUIDv7, horloge, contexte de requête, idempotence, ETag | — (ouvert à tous) | L2, L3 |
| contract | code généré depuis le contrat | — (ouvert à tous) | L2 |
| audit | journal chaîné, séquenceur, points de contrôle, export | shared, contract | L4 |
| notification | e-mails FR/EN par la boîte d'envoi | shared | L7 |
| organization | organisations, établissements | shared, contract, audit | L5 |
| access | rôles, permissions, affectations, calcul des droits | + organization, audit | L6 |
| identity | identité unique, Mon compte, confirmations, événements Keycloak | + audit, notification | L7, L8 |
| membership | appartenances, invitations, fiche utilisateur | + identity, access, organization, audit, notification | L7 |
| support | accès de support, administrateur de secours | + organization, membership, identity, audit, notification | L9 |
| home | éléments « À traiter » | + membership, access, support, identity | L8 |
| session | connexion, session, verrouillage, contexte | + identity, access, organization, membership, support, audit | L2, L8 |

Le graphe est sans cycle : `audit` et `notification` ne dépendent d'aucun module métier ; un module ne s'adresse
à un autre que par les classes publiques de premier niveau de celui-ci (ou ses événements).

## Données et isolation

Cinq schémas (org, iam, platform, audit, ops), vingt-deux tables, toutes celles d'une organisation en
`FORCE ROW LEVEL SECURITY`. Rôles PostgreSQL : voir `infra/README.md`. Le serveur fixe l'organisation au début de
chaque transaction ; chaque chemin qui traverse les organisations passe par une fonction `SECURITY DEFINER` dédiée,
possédée par `acu_definer`.

### Constats de la vérification sur PostgreSQL 18.4 (lot L1), à appliquer aux migrations du lot L2

Essai réel des rôles sur une instance PostgreSQL 18.4 : la RLS forcée renvoie 0 ligne sans organisation fixée,
1 ligne dans l'organisation fixée ; une fonction dédiée possédée par `acu_definer` voit les 2 lignes ; le
propriétaire `acu_owner` est lui aussi soumis à la RLS forcée. L'essai a aussi montré trois règles à respecter :

1. Donner une fonction à `acu_definer` exige que ce rôle ait `CREATE` sur le schéma au moment du changement de
   propriétaire : `GRANT CREATE ON SCHEMA … TO acu_definer`, `ALTER FUNCTION … OWNER TO acu_definer`, puis
   `REVOKE CREATE`.
2. Les droits d'exécution d'une fonction dédiée (`REVOKE … FROM PUBLIC`, `GRANT EXECUTE` au seul rôle qui en a
   besoin) se posent **avant** le changement de propriétaire : après, `acu_owner` ne peut plus les modifier.
3. La première migration retire le droit d'exécution par défaut :
   `ALTER DEFAULT PRIVILEGES FOR ROLE acu_owner REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC`.

Depuis PostgreSQL 15, le propriétaire d'une base possède aussi le schéma `public` : l'initialisation le rend au
superutilisateur pour que personne n'y crée d'objet (écart trouvé et corrigé par `verifier-initialisation.sql`).

## Configuration

`src/main/resources/application.yaml` : uniquement des marqueurs `${VARIABLE}` et des valeurs locales sans risque.
Durées du M0 paramétrables (`acu.session`, `acu.invitation`, `acu.keycloak`) : les tests les raccourcissent.
Sondes de santé sur le port d'administration 8081, jamais exposé ; journaux JSON (format ECS) sans données personnelles.

## Retour de la fenêtre de déverrouillage

Après la réauthentification (`GET /api/v1/auth/reauth?popup=true`), le back-end redirige la fenêtre vers
`/session/reauth-complete?outcome=unlocked` (même personne, session reprise) ou `?outcome=ended` (session fermée).
Cette page de l'application prévient l'onglet par `BroadcastChannel` puis se ferme (front-end, lot L10).
