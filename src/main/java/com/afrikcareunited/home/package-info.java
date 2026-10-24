/**
 * Éléments « À traiter » de l'accueil (/home/tasks) : invitations qui expirent, comptes bloqués, affectations
 * qui se terminent, demandes d'accès de support. Lecture seule, au travers des interfaces des autres modules.
 * <p>Lot : L8.
 */
@ApplicationModule(
    displayName = "Accueil",
    allowedDependencies = {"shared", "contract", "membership", "access", "support", "identity"})
package com.afrikcareunited.home;

import org.springframework.modulith.ApplicationModule;
