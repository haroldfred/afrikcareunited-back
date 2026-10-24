"""Contrôles des realms Keycloak du M0 (conception détaillée, « Configuration Keycloak proposée »).
Vérifie les réglages exigés et l'absence de tout secret écrit en clair.
Usage : python3 tools/check_realms.py infra/keycloak/realms
Code de sortie 1 au premier écart (tous les écarts sont listés).
"""
import json
import re
import sys
from pathlib import Path

PLACEHOLDER = re.compile(r'^\$\{[A-Z0-9_]+(:[^}]*)?\}$')
problems: list[str] = []


def check(condition: bool, message: str) -> None:
    if not condition:
        problems.append(message)


def secrets_are_placeholders(node, path: str, realm: str) -> None:
    """Toute valeur de secret ou de mot de passe est vide ou un marqueur ${VARIABLE}."""
    if isinstance(node, dict):
        for key, value in node.items():
            here = f'{path}.{key}'
            if key.lower() in ('secret', 'password', 'value') and isinstance(value, str) and value:
                check(bool(PLACEHOLDER.match(value)), f'{realm} : valeur en clair pour {here}')
            if key == 'credentials':
                check(not value, f'{realm} : identifiants d’utilisateur dans le fichier ({here})')
            secrets_are_placeholders(value, here, realm)
    elif isinstance(node, list):
        for i, value in enumerate(node):
            secrets_are_placeholders(value, f'{path}[{i}]', realm)


def flows_by_alias(realm: dict) -> dict:
    return {f['alias']: f for f in realm.get('authenticationFlows', [])}


def authenticators(flows: dict, alias: str) -> list[tuple[str, str]]:
    """Authentificateurs d'un flux et de ses sous-flux, avec leur exigence."""
    found = []
    for e in flows.get(alias, {}).get('authenticationExecutions', []):
        if e.get('authenticatorFlow') or e.get('autheticatorFlow'):
            found.append((f"flow:{e['flowAlias']}", e['requirement']))
            found += authenticators(flows, e['flowAlias'])
        else:
            found.append((e['authenticator'], e['requirement']))
    return found


def check_realm(path: Path, operators: bool) -> None:
    realm = json.loads(path.read_text(encoding='utf-8'))
    name = realm['realm']
    secrets_are_placeholders(realm, name, name)

    # Comptes : pas d'inscription libre, e-mails uniques, connexion par e-mail ou identifiant.
    for key, expected in [('registrationAllowed', False), ('rememberMe', False), ('duplicateEmailsAllowed', False),
                          ('loginWithEmailAllowed', True), ('editUsernameAllowed', False), ('resetPasswordAllowed', True)]:
        check(realm.get(key) is expected, f'{name} : {key} doit valoir {expected}')

    # Force brute : 5 échecs, 15 minutes, jamais de blocage définitif.
    check(realm.get('bruteForceProtected') is True, f'{name} : protection contre la force brute absente')
    check(realm.get('permanentLockout') is False, f'{name} : blocage définitif interdit')
    for key, expected in [('failureFactor', 5), ('waitIncrementSeconds', 900), ('maxFailureWaitSeconds', 900),
                          ('maxDeltaTimeSeconds', 900)]:
        check(realm.get(key) == expected, f'{name} : {key} doit valoir {expected}')

    policy = realm.get('passwordPolicy', '')
    for rule in ('length(12)', 'notUsername', 'notEmail', 'passwordHistory(3)', 'passwordBlacklist('):
        check(rule in policy, f'{name} : politique de mot de passe sans {rule}')

    # Double authentification : TOTP 6 chiffres, 30 s, codes de secours.
    check(realm.get('otpPolicyType') == 'totp' and realm.get('otpPolicyDigits') == 6 and realm.get('otpPolicyPeriod') == 30,
          f'{name} : TOTP à 6 chiffres et 30 s attendu')
    check({'totpAppFreeOTPName', 'totpAppGoogleName', 'totpAppMicrosoftAuthenticatorName'} <= set(realm.get('otpSupportedApplications', [])),
          f'{name} : applications FreeOTP, Google et Microsoft Authenticator attendues')
    actions = {a['alias']: a for a in realm.get('requiredActions', [])}
    check(actions.get('CONFIGURE_RECOVERY_AUTHN_CODES', {}).get('enabled') is True, f'{name} : codes de secours non activés')
    check(actions.get('CONFIGURE_TOTP', {}).get('defaultAction') is operators,
          f'{name} : CONFIGURE_TOTP par défaut {"obligatoire pour l’équipe" if operators else "non imposé aux organisations"}')

    # Sessions en filet, liens de 30 minutes, langues.
    for key, expected in [('ssoSessionIdleTimeout', 1800), ('ssoSessionMaxLifespan', 43200),
                          ('actionTokenGeneratedByUserLifespan', 1800), ('actionTokenGeneratedByAdminLifespan', 1800)]:
        check(realm.get(key) == expected, f'{name} : {key} doit valoir {expected}')
    check(realm.get('internationalizationEnabled') is True and realm.get('defaultLocale') == 'fr'
          and set(realm.get('supportedLocales', [])) == {'fr', 'en'}, f'{name} : français par défaut et anglais attendus')

    # Événements : 7 jours, aucun écouteur vers le journal du serveur.
    check(realm.get('eventsEnabled') is True and realm.get('eventsExpiration') == 604800, f'{name} : événements sur 7 jours attendus')
    check('jboss-logging' not in realm.get('eventsListeners', ['jboss-logging']), f'{name} : écouteur jboss-logging à retirer')
    check(realm.get('adminEventsEnabled') is True, f'{name} : événements d’administration attendus')
    for event in ('LOGIN', 'LOGIN_ERROR', 'USER_DISABLED_BY_TEMPORARY_LOCKOUT', 'UPDATE_CREDENTIAL', 'REMOVE_CREDENTIAL'):
        check(event in realm.get('enabledEventTypes', []), f'{name} : événement {event} non enregistré')

    # Flux : liaisons existantes, sous-flux et configurations référencés existants.
    flows = flows_by_alias(realm)
    for binding in ('browserFlow', 'resetCredentialsFlow', 'registrationFlow', 'directGrantFlow', 'clientAuthenticationFlow'):
        check(realm.get(binding) in flows, f'{name} : flux {binding} « {realm.get(binding)} » absent du fichier')
    configs = {c['alias'] for c in realm.get('authenticatorConfig', [])}
    for flow in flows.values():
        for e in flow.get('authenticationExecutions', []):
            if e.get('authenticatorFlow') or e.get('autheticatorFlow'):
                check(e.get('flowAlias') in flows, f'{name} : sous-flux « {e.get("flowAlias")} » absent')
            if 'authenticatorConfig' in e:
                check(e['authenticatorConfig'] in configs, f'{name} : configuration « {e["authenticatorConfig"]} » absente')

    browser = authenticators(flows, realm['browserFlow'])
    names = [a for a, _ in browser]
    check('auth-otp-form' in names and 'auth-recovery-authn-code-form' in names, f'{name} : connexion sans code ni code de secours')
    second = next((req for a, req in browser if a.startswith('flow:') and 'second facteur' in a), None)
    check(second == ('REQUIRED' if operators else 'CONDITIONAL'),
          f'{name} : second facteur {"toujours exigé pour l’équipe" if operators else "exigé de qui l’a activé"}')

    reset = [a for a, _ in authenticators(flows, realm['resetCredentialsFlow'])]
    check('reset-otp' not in reset, f'{name} : le mot de passe oublié ne doit jamais retirer l’application d’authentification')
    check('auth-otp-form' in reset and 'conditional-user-configured' in reset,
          f'{name} : le mot de passe oublié doit demander le code à qui l’a activé')

    # Clients.
    clients = {c['clientId']: c for c in realm.get('clients', [])}
    bff = clients.get('acu-bff', {})
    check(bff.get('publicClient') is False and bff.get('standardFlowEnabled') is True, f'{name} : acu-bff confidentiel, code d’autorisation')
    check(bff.get('directAccessGrantsEnabled') is False and bff.get('implicitFlowEnabled') is False,
          f'{name} : acu-bff sans mot de passe direct ni flux implicite')
    check(bff.get('attributes', {}).get('pkce.code.challenge.method') == 'S256', f'{name} : PKCE S256 attendu sur acu-bff')
    check(bool(bff.get('attributes', {}).get('backchannel.logout.url')), f'{name} : déconnexion signalée au back-end absente')
    check(any(m.get('protocolMapper') == 'oidc-amr-mapper' for m in bff.get('protocolMappers', [])), f'{name} : mappeur AMR absent')
    check(clients.get('account-console', {}).get('enabled') is False, f'{name} : console de compte à désactiver')
    default_role = realm.get('defaultRole', {}).get('composites', {})
    check('account' not in default_role.get('client', {}), f'{name} : rôles du compte Keycloak donnés par défaut')

    if operators:
        check('acu-admin' not in clients, f'{name} : hors de portée du compte de service des organisations')
    else:
        confirm = clients.get('acu-confirm', {})
        override = confirm.get('authenticationFlowBindingOverrides', {}).get('browser')
        target = next((f for f in flows.values() if f.get('id') == override), None)
        check(target is not None and [a for a, _ in authenticators(flows, target['alias'])] == ['auth-username-password-form'],
              f'{name} : acu-confirm doit n’afficher que la page de mot de passe')
        admin = clients.get('acu-admin', {})
        check(admin.get('serviceAccountsEnabled') is True and admin.get('standardFlowEnabled') is False,
              f'{name} : acu-admin doit être un compte de service seul')
        account = next((u for u in realm.get('users', []) if u.get('serviceAccountClientId') == 'acu-admin'), {})
        check(account.get('clientRoles', {}).get('realm-management') == ['manage-users', 'view-users', 'query-users', 'view-events'],
              f'{name} : acu-admin limité à la gestion des utilisateurs et à la lecture des événements')
        check(not account.get('realmRoles'), f'{name} : aucun rôle de realm pour acu-admin')

    smtp = realm.get('smtpServer', {})
    check(all(PLACEHOLDER.match(str(smtp.get(k, ''))) for k in ('host', 'port', 'from')), f'{name} : SMTP paramétré par environnement')


folder = Path(sys.argv[1] if len(sys.argv) > 1 else 'infra/keycloak/realms')
check_realm(folder / 'afrikcareunited-realm.json', operators=False)
check_realm(folder / 'afrikcareunited-equipe-realm.json', operators=True)
blacklist = Path(folder.parent, 'password-blacklists', 'acu-mots-de-passe-courants.txt')
check(blacklist.is_file() and blacklist.read_text(encoding='utf-8').strip() != '', 'liste des mots de passe courants absente')

if problems:
    print(f'{len(problems)} écart(s) :')
    for p in problems:
        print(' -', p)
    sys.exit(1)
print('Realms Keycloak : afrikcareunited et afrikcareunited-equipe conformes, aucun secret en clair.')
