/**
 * Identité unique d'une personne sur la plateforme (iam.user_account, Q1) : compte Keycloak, e-mail et
 * identifiant uniques, Mon compte (/me), événements de sécurité de l'identité, confirmations par e-mail
 * (/account-confirmations, iam.action_token), relais pseudonymisé des événements Keycloak
 * (ops.keycloak_event_cursor). Client d'administration Keycloak (acu-admin).
 * <p>Lots : L7, L8.
 */
@ApplicationModule(
    displayName = "Identités",
    allowedDependencies = {"shared", "contract", "audit", "notification"})
package com.afrikcareunited.identity;

import org.springframework.modulith.ApplicationModule;
