"""Construit les deux realms Keycloak du M0 (fichiers d'import versionnés, sans secret).
Les secrets et adresses sont des marqueurs ${VARIABLE} remplacés par Keycloak à l'import (--import-realm).
Usage : python3 build_realms.py <dossier de sortie>
"""
import json
import sys
import uuid

out = sys.argv[1]

# Identifiants fixes : les liaisons de flux par client référencent un identifiant de flux.
NS = uuid.UUID('0192b1c4-7e3a-7c41-9f2d-5be0a8c3e000')


def fixed_id(name: str) -> str:
    return str(uuid.uuid5(NS, name))


EVENT_TYPES = [
    'LOGIN', 'LOGIN_ERROR', 'LOGOUT', 'LOGOUT_ERROR', 'CODE_TO_TOKEN', 'CODE_TO_TOKEN_ERROR',
    'UPDATE_PASSWORD', 'UPDATE_PASSWORD_ERROR', 'UPDATE_CREDENTIAL', 'UPDATE_CREDENTIAL_ERROR',
    'REMOVE_CREDENTIAL', 'REMOVE_CREDENTIAL_ERROR', 'UPDATE_TOTP', 'REMOVE_TOTP',
    'SEND_RESET_PASSWORD', 'SEND_RESET_PASSWORD_ERROR', 'RESET_PASSWORD', 'RESET_PASSWORD_ERROR',
    'EXECUTE_ACTIONS', 'EXECUTE_ACTIONS_ERROR', 'EXECUTE_ACTION_TOKEN', 'EXECUTE_ACTION_TOKEN_ERROR',
    'USER_DISABLED_BY_TEMPORARY_LOCKOUT', 'USER_DISABLED_BY_PERMANENT_LOCKOUT',
    'REFRESH_TOKEN_ERROR', 'INVALID_SIGNATURE', 'CLIENT_LOGIN_ERROR',
]

# Mots de passe : 12 caractères au moins, ni l'identifiant, ni l'e-mail, ni l'un des 3 précédents,
# ni un mot de passe courant (liste déployée avec Keycloak, data/password-blacklists).
PASSWORD_POLICY = ('length(12) and notUsername(undefined) and notEmail(undefined) and passwordHistory(3) '
                   'and passwordBlacklist(acu-mots-de-passe-courants.txt)')

AMR_PASSWORD = 'pwd'
AMR_OTP = 'otp'
AMR_RECOVERY = 'otp'  # code de secours : second facteur, au même titre que le code de l'application


def amr_config(alias: str, value: str) -> dict:
    """Valeur de référence de l'authentificateur, reprise par le mappeur AMR dans le jeton d'identité."""
    return {'id': fixed_id(alias), 'alias': alias, 'config': {'default.reference.value': value}}


def execution(authenticator: str, requirement: str, priority: int, config: str | None = None) -> dict:
    e = {
        'authenticator': authenticator,
        'authenticatorFlow': False,
        'requirement': requirement,
        'priority': priority,
        'autheticatorFlow': False,
        'userSetupAllowed': False,
    }
    if config:
        e['authenticatorConfig'] = config
    return e


def subflow(alias: str, requirement: str, priority: int) -> dict:
    return {
        'authenticatorFlow': True,
        'requirement': requirement,
        'priority': priority,
        'autheticatorFlow': True,
        'flowAlias': alias,
        'userSetupAllowed': False,
    }


def flow(alias: str, description: str, executions: list, top_level: bool = True) -> dict:
    return {
        'id': fixed_id(alias),
        'alias': alias,
        'description': description,
        'providerId': 'basic-flow',
        'topLevel': top_level,
        'builtIn': False,
        'authenticationExecutions': executions,
    }


def flows(otp_always: bool) -> tuple[list, list]:
    """Flux de connexion, de mot de passe oublié et de confirmation par le mot de passe."""
    second_factor_requirement = 'REQUIRED' if otp_always else 'CONDITIONAL'
    second_factor = [
        execution('auth-otp-form', 'ALTERNATIVE', 10, 'acu-amr-otp'),
        execution('auth-recovery-authn-code-form', 'ALTERNATIVE', 20, 'acu-amr-recovery'),
    ]
    if not otp_always:
        second_factor.insert(0, execution('conditional-user-configured', 'REQUIRED', 0))
    browser = [
        flow('acu navigateur', 'Connexion : mot de passe, puis code de double authentification ou code de secours', [
            execution('auth-cookie', 'ALTERNATIVE', 10),
            subflow('acu navigateur formulaires', 'ALTERNATIVE', 20),
        ]),
        flow('acu navigateur formulaires', 'Formulaires de connexion', [
            execution('auth-username-password-form', 'REQUIRED', 10, 'acu-amr-password'),
            subflow('acu navigateur second facteur', second_factor_requirement, 20),
        ], top_level=False),
        flow('acu navigateur second facteur', 'Second facteur', second_factor, top_level=False),
    ]
    # Mot de passe oublié : le code reste exigé de qui l'a activé, et aucune application d'authentification
    # n'est supprimée (pas d'étape « Reset OTP »).
    reset = [
        flow('acu mot de passe oublie', 'Mot de passe oublié : e-mail, code exigé si activé, nouveau mot de passe', [
            execution('reset-credentials-choose-user', 'REQUIRED', 10),
            execution('reset-credential-email', 'REQUIRED', 20),
            subflow('acu mot de passe oublie second facteur', 'CONDITIONAL', 30),
            execution('reset-password', 'REQUIRED', 40),
        ]),
        flow('acu mot de passe oublie second facteur', 'Code de double authentification ou code de secours', [
            execution('conditional-user-configured', 'REQUIRED', 0),
            execution('auth-otp-form', 'ALTERNATIVE', 10),
            execution('auth-recovery-authn-code-form', 'ALTERNATIVE', 20),
        ], top_level=False),
    ]
    # Confirmation par le mot de passe (client acu-confirm) : page de mot de passe seule, sans cookie de session.
    confirm = [
        flow('acu confirmation mot de passe', 'Confirmation d’une demande sensible par le mot de passe', [
            execution('auth-username-password-form', 'REQUIRED', 10, 'acu-amr-password'),
        ]),
    ]
    configs = [amr_config('acu-amr-password', AMR_PASSWORD), amr_config('acu-amr-otp', AMR_OTP),
               amr_config('acu-amr-recovery', AMR_RECOVERY)]
    return browser + reset + confirm + builtin_flows(), configs


def builtin_flows() -> list:
    """Flux standard de Keycloak, repris tels quels : un fichier d'import qui définit des flux doit les définir tous."""
    def builtin(alias, description, executions, provider='basic-flow', top_level=True):
        f = flow(alias, description, executions, top_level)
        f['providerId'] = provider
        f['builtIn'] = True
        return f
    registration_page = subflow('registration form', 'REQUIRED', 10)
    registration_page['authenticator'] = 'registration-page-form'
    return [
        builtin('registration', 'Registration flow (inscription désactivée)', [registration_page]),
        builtin('registration form', 'Registration form', [
            execution('registration-user-creation', 'REQUIRED', 20),
            execution('registration-password-action', 'REQUIRED', 50),
            execution('registration-recaptcha-action', 'DISABLED', 60),
            execution('registration-terms-and-conditions', 'DISABLED', 70),
        ], provider='form-flow', top_level=False),
        builtin('direct grant', 'OpenID Connect Resource Owner Grant (désactivé sur les clients)', [
            execution('direct-grant-validate-username', 'REQUIRED', 10),
            execution('direct-grant-validate-password', 'REQUIRED', 20),
            subflow('Direct Grant - Conditional OTP', 'CONDITIONAL', 30),
        ]),
        builtin('Direct Grant - Conditional OTP', 'Flow to determine if the OTP is required for the authentication', [
            execution('conditional-user-configured', 'REQUIRED', 10),
            execution('direct-grant-validate-otp', 'REQUIRED', 20),
        ], top_level=False),
        builtin('clients', 'Base authentication for clients', [
            execution('client-secret', 'ALTERNATIVE', 10),
            execution('client-jwt', 'ALTERNATIVE', 20),
            execution('client-secret-jwt', 'ALTERNATIVE', 30),
            execution('client-x509', 'ALTERNATIVE', 40),
        ], provider='client-flow'),
    ]


def amr_mapper() -> dict:
    return {
        'name': 'amr',
        'protocol': 'openid-connect',
        'protocolMapper': 'oidc-amr-mapper',
        'consentRequired': False,
        'config': {'id.token.claim': 'true', 'access.token.claim': 'true', 'introspection.token.claim': 'true'},
    }


def bff_client(secret_variable: str, callback: str) -> dict:
    return {
        'clientId': 'acu-bff',
        'name': 'AfrikCareUnited — back-end (BFF)',
        'description': 'Client confidentiel du back-end : code d’autorisation avec PKCE, déconnexion signalée au back-end',
        'enabled': True,
        'protocol': 'openid-connect',
        'publicClient': False,
        'clientAuthenticatorType': 'client-secret',
        'secret': '${' + secret_variable + '}',
        'standardFlowEnabled': True,
        'implicitFlowEnabled': False,
        'directAccessGrantsEnabled': False,
        'serviceAccountsEnabled': False,
        'frontchannelLogout': False,
        'consentRequired': False,
        'fullScopeAllowed': False,
        'redirectUris': ['${ACU_PUBLIC_URL}/api/v1/auth/callback/' + callback],
        'webOrigins': [],
        'rootUrl': '${ACU_PUBLIC_URL}',
        'attributes': {
            'pkce.code.challenge.method': 'S256',
            'post.logout.redirect.uris': '${ACU_PUBLIC_URL}/login',
            'backchannel.logout.url': '${ACU_BACKEND_INTERNAL_URL}/api/v1/auth/backchannel-logout',
            'backchannel.logout.session.required': 'true',
            'backchannel.logout.revoke.offline.tokens': 'false',
            'use.refresh.tokens': 'true',
            'client_credentials.use_refresh_token': 'false',
            'oauth2.device.authorization.grant.enabled': 'false',
            'oidc.ciba.grant.enabled': 'false',
        },
        'protocolMappers': [amr_mapper()],
        'defaultClientScopes': ['acr', 'basic', 'profile', 'email'],
        'optionalClientScopes': [],
    }


def disabled_builtin(client_id: str) -> dict:
    return {'clientId': client_id, 'enabled': False, 'publicClient': True, 'protocol': 'openid-connect'}


USER_PROFILE = {
    'attributes': [
        {
            'name': 'username', 'displayName': '${username}',
            'validations': {'length': {'min': 3, 'max': 255}, 'username-prohibited-characters': {}, 'up-username-not-idn-homograph': {}},
            'permissions': {'view': ['admin', 'user'], 'edit': ['admin']}, 'multivalued': False,
        },
        {
            'name': 'email', 'displayName': '${email}',
            'validations': {'email': {}, 'length': {'max': 255}},
            'permissions': {'view': ['admin', 'user'], 'edit': ['admin']}, 'multivalued': False,
        },
        {
            'name': 'firstName', 'displayName': '${firstName}',
            'validations': {'length': {'max': 255}, 'person-name-prohibited-characters': {}},
            'permissions': {'view': ['admin', 'user'], 'edit': ['admin']}, 'multivalued': False,
        },
        {
            'name': 'lastName', 'displayName': '${lastName}',
            'validations': {'length': {'max': 255}, 'person-name-prohibited-characters': {}},
            'permissions': {'view': ['admin', 'user'], 'edit': ['admin']}, 'multivalued': False,
        },
    ],
    'groups': [{'name': 'user-metadata', 'displayHeader': 'User metadata', 'displayDescription': 'Attributes, which refer to user metadata'}],
    'unmanagedAttributePolicy': 'ADMIN_VIEW',
}


def realm(name: str, display: str, operators: bool) -> dict:
    flow_list, configs = flows(otp_always=operators)
    clients = [bff_client('ACU_KEYCLOAK_EQUIPE_BFF_SECRET' if operators else 'ACU_KEYCLOAK_BFF_SECRET',
                          'keycloak-equipe' if operators else 'keycloak')]
    users = []
    if not operators:
        clients.append({
            'clientId': 'acu-confirm',
            'name': 'AfrikCareUnited — confirmations',
            'description': 'Confirmation des demandes sensibles par le mot de passe, saisie toujours exigée (prompt=login, max_age=0)',
            'enabled': True,
            'protocol': 'openid-connect',
            'publicClient': False,
            'clientAuthenticatorType': 'client-secret',
            'secret': '${ACU_KEYCLOAK_CONFIRM_SECRET}',
            'standardFlowEnabled': True,
            'implicitFlowEnabled': False,
            'directAccessGrantsEnabled': False,
            'serviceAccountsEnabled': False,
            'frontchannelLogout': False,
            'consentRequired': False,
            'fullScopeAllowed': False,
            'redirectUris': ['${ACU_PUBLIC_URL}/api/v1/account-confirmations/callback'],
            'webOrigins': [],
            'rootUrl': '${ACU_PUBLIC_URL}',
            'attributes': {'pkce.code.challenge.method': 'S256', 'use.refresh.tokens': 'false'},
            'authenticationFlowBindingOverrides': {'browser': fixed_id('acu confirmation mot de passe')},
            'protocolMappers': [amr_mapper()],
            'defaultClientScopes': ['acr', 'basic'],
            'optionalClientScopes': [],
        })
        clients.append({
            'clientId': 'acu-admin',
            'name': 'AfrikCareUnited — administration des utilisateurs',
            'description': 'Compte de service du back-end : gestion des utilisateurs de ce realm et lecture de ses événements',
            'enabled': True,
            'protocol': 'openid-connect',
            'publicClient': False,
            'clientAuthenticatorType': 'client-secret',
            'secret': '${ACU_KEYCLOAK_ADMIN_SECRET}',
            'standardFlowEnabled': False,
            'implicitFlowEnabled': False,
            'directAccessGrantsEnabled': False,
            'serviceAccountsEnabled': True,
            'fullScopeAllowed': False,
            'attributes': {'use.refresh.tokens': 'false', 'client_credentials.use_refresh_token': 'false'},
            'defaultClientScopes': ['basic'],
            'optionalClientScopes': [],
        })
        users.append({
            'username': 'service-account-acu-admin',
            'enabled': True,
            'serviceAccountClientId': 'acu-admin',
            'realmRoles': [],
            'clientRoles': {'realm-management': ['manage-users', 'view-users', 'query-users', 'view-events']},
        })
    # Console de compte désactivée : tout passe par Mon compte et le back-end. Le client « account » reste
    # créé par Keycloak, mais le rôle manage-account n'est plus donné par défaut (defaultRole ci-dessous).
    clients += [disabled_builtin('account-console')]

    required_actions = [
        {'alias': 'CONFIGURE_TOTP', 'name': 'Configure OTP', 'providerId': 'CONFIGURE_TOTP', 'enabled': True,
         'defaultAction': operators, 'priority': 10, 'config': {}},
        {'alias': 'UPDATE_PASSWORD', 'name': 'Update Password', 'providerId': 'UPDATE_PASSWORD', 'enabled': True,
         'defaultAction': False, 'priority': 30, 'config': {}},
        {'alias': 'CONFIGURE_RECOVERY_AUTHN_CODES', 'name': 'Recovery Authentication Codes',
         'providerId': 'CONFIGURE_RECOVERY_AUTHN_CODES', 'enabled': True, 'defaultAction': False, 'priority': 20,
         'config': {}},
        {'alias': 'VERIFY_EMAIL', 'name': 'Verify Email', 'providerId': 'VERIFY_EMAIL', 'enabled': True,
         'defaultAction': False, 'priority': 50, 'config': {}},
        {'alias': 'delete_credential', 'name': 'Delete Credential', 'providerId': 'delete_credential', 'enabled': True,
         'defaultAction': False, 'priority': 60, 'config': {}},
    ]

    return {
        'realm': name,
        'displayName': display,
        'enabled': True,
        'sslRequired': 'external',
        'registrationAllowed': False,
        'registrationEmailAsUsername': False,
        'rememberMe': False,
        'verifyEmail': False,
        'loginWithEmailAllowed': True,
        'duplicateEmailsAllowed': False,
        'resetPasswordAllowed': True,
        'editUsernameAllowed': False,
        'organizationsEnabled': False,
        # Force brute : 5 échecs, blocage de 15 min, compteur remis à zéro après 15 min sans échec.
        'bruteForceProtected': True,
        'permanentLockout': False,
        'maxTemporaryLockouts': 0,
        'bruteForceStrategy': 'MULTIPLE',
        'failureFactor': 5,
        'waitIncrementSeconds': 900,
        'maxFailureWaitSeconds': 900,
        'maxDeltaTimeSeconds': 900,
        'minimumQuickLoginWaitSeconds': 60,
        'quickLoginCheckMilliSeconds': 1000,
        'passwordPolicy': PASSWORD_POLICY,
        # Double authentification : TOTP à 6 chiffres, toutes les 30 s.
        'otpPolicyType': 'totp',
        'otpPolicyAlgorithm': 'HmacSHA1',
        'otpPolicyDigits': 6,
        'otpPolicyPeriod': 30,
        'otpPolicyLookAheadWindow': 1,
        'otpPolicyCodeReusable': False,
        'otpSupportedApplications': ['totpAppFreeOTPName', 'totpAppGoogleName', 'totpAppMicrosoftAuthenticatorName'],
        # Sessions Keycloak : en filet ; le back-end tient lui-même 15 min, 2 h et 12 h.
        'ssoSessionIdleTimeout': 1800,
        'ssoSessionMaxLifespan': 43200,
        'ssoSessionIdleTimeoutRememberMe': 0,
        'ssoSessionMaxLifespanRememberMe': 0,
        'offlineSessionIdleTimeout': 0,
        'accessTokenLifespan': 300,
        'accessCodeLifespan': 60,
        'accessCodeLifespanLogin': 1800,
        'accessCodeLifespanUserAction': 1800,
        # Liens envoyés par Keycloak (création du mot de passe, mot de passe oublié) : 30 min.
        'actionTokenGeneratedByAdminLifespan': 1800,
        'actionTokenGeneratedByUserLifespan': 1800,
        'internationalizationEnabled': True,
        'supportedLocales': ['fr', 'en'],
        'defaultLocale': 'fr',
        # Événements : connexions et actions d'administration, conservés 7 jours ;
        # l'écouteur qui les recopie dans le journal du serveur (jboss-logging) est retiré.
        'eventsEnabled': True,
        'eventsExpiration': 604800,
        'eventsListeners': [],
        'enabledEventTypes': EVENT_TYPES,
        'adminEventsEnabled': True,
        'adminEventsDetailsEnabled': False,
        'browserFlow': 'acu navigateur',
        'resetCredentialsFlow': 'acu mot de passe oublie',
        'registrationFlow': 'registration',
        'directGrantFlow': 'direct grant',
        'clientAuthenticationFlow': 'clients',
        'dockerAuthenticationFlow': 'docker auth',
        'firstBrokerLoginFlow': 'first broker login',
        'authenticationFlows': flow_list,
        'authenticatorConfig': configs,
        'requiredActions': required_actions,
        'defaultRole': {
            'name': f'default-roles-{name}',
            'description': '${role_default-roles}',
            'composite': True,
            'composites': {'realm': []},
            'clientRole': False,
        },
        'clients': clients,
        'users': users,
        'smtpServer': {
            'host': '${ACU_SMTP_HOST}',
            'port': '${ACU_SMTP_PORT}',
            'from': '${ACU_SMTP_FROM}',
            'fromDisplayName': 'AfrikCareUnited',
            'replyTo': '',
            'ssl': '${ACU_SMTP_SSL:false}',
            'starttls': '${ACU_SMTP_STARTTLS:false}',
            'auth': '${ACU_SMTP_AUTH:false}',
            'user': '${ACU_SMTP_USER:}',
            'password': '${ACU_SMTP_PASSWORD:}',
        },
        'components': {
            'org.keycloak.userprofile.UserProfileProvider': [{
                'providerId': 'declarative-user-profile',
                'subComponents': {},
                'config': {'kc.user.profile.config': [json.dumps(USER_PROFILE, ensure_ascii=False)]},
            }],
        },
        'attributes': {
            'frontendUrl': '',
            'acr.loa.map': '{}',
            'firstBrokerLoginFlow': 'first broker login',
            'organizationsEnabled': 'false',
        },
        'browserSecurityHeaders': {
            'contentSecurityPolicyReportOnly': '',
            'xContentTypeOptions': 'nosniff',
            'referrerPolicy': 'no-referrer',
            'xRobotsTag': 'none',
            'xFrameOptions': 'DENY',
            'contentSecurityPolicy': "frame-src 'self'; frame-ancestors 'none'; object-src 'none';",
            'strictTransportSecurity': 'max-age=31536000; includeSubDomains',
        },
    }


for file_name, realm_name, display, operators in [
    ('afrikcareunited-realm.json', 'afrikcareunited', 'AfrikCareUnited', False),
    ('afrikcareunited-equipe-realm.json', 'afrikcareunited-equipe', 'AfrikCareUnited — équipe', True),
]:
    with open(f'{out}/{file_name}', 'w', encoding='utf-8') as f:
        json.dump(realm(realm_name, display, operators), f, ensure_ascii=False, indent=2)
        f.write('\n')
    print('écrit', file_name)
