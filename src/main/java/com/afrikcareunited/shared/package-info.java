/**
 * Noyau partagé, ouvert à tous les modules : erreurs RFC 9457 et leurs 36 codes, identifiants UUIDv7,
 * horloge injectée, contexte de la requête (organisation, établissement, acteur), idempotence, ETag,
 * en-têtes de sécurité et limites de débit. Ne dépend d'aucun autre module.
 * <p>Lots : L2 (socle back-end), L3 (exploitation).
 */
@ApplicationModule(
    displayName = "Noyau partagé",
    type = ApplicationModule.Type.OPEN)
package com.afrikcareunited.shared;

import org.springframework.modulith.ApplicationModule;
