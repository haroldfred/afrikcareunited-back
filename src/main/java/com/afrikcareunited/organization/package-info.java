/**
 * Organisations clientes et leurs établissements (org.organization, org.establishment) : lecture et
 * modification côté client (/organization) et ouverture, suspension et réactivation côté plateforme
 * (/platform/organizations). Copie des rôles système à l'ouverture d'une organisation.
 * <p>Lot : L5.
 */
@ApplicationModule(
    displayName = "Organisations et établissements",
    allowedDependencies = {"shared", "contract", "audit"})
package com.afrikcareunited.organization;

import org.springframework.modulith.ApplicationModule;
