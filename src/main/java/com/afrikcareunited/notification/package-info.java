/**
 * E-mails transactionnels en français et en anglais (invitations, confirmations, avis), envoyés par la
 * boîte d'envoi de Spring Modulith (ops.event_publication) avec nouveaux essais. SMTP paramétré par
 * environnement ; Mailpit en développement et en test, aucun envoi réel (D-12).
 * <p>Lot : L7.
 */
@ApplicationModule(
    displayName = "E-mails",
    allowedDependencies = {"shared"})
package com.afrikcareunited.notification;

import org.springframework.modulith.ApplicationModule;
