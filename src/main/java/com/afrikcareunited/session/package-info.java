/**
 * Session du navigateur, modèle BFF (RFC 10017) : connexion, réauthentification et déconnexion par Keycloak
 * (/auth), session courante, choix de l'établissement, signal d'activité, verrouillage après 15 minutes,
 * sessions actives (/session), configuration publique (/config). Sessions Spring Session JDBC, cookie HttpOnly
 * {@code __Host-acu_session}, CSRF {@code __Host-XSRF-TOKEN}.
 * <p>Lots : L2 (socle), L8 (session et Mon compte).
 */
@ApplicationModule(
    displayName = "Session et connexion",
    allowedDependencies = {"shared", "contract", "identity", "access", "organization", "membership", "support", "audit"})
package com.afrikcareunited.session;

import org.springframework.modulith.ApplicationModule;
