/**
 * Appartenances et invitations (iam.membership, iam.invitation) : liste et fiche des utilisateurs, invitation
 * par lien ou mot de passe provisoire, renvoi et annulation, suspension, réactivation, fin d'appartenance,
 * déblocage, réinitialisation de la double authentification, affichage du téléphone (/users,
 * /invitations, /me/memberships/{organizationId}/leave). RG-03, RG-06, RG-09, RG-12.
 * <p>Lot : L7.
 */
@ApplicationModule(
    displayName = "Utilisateurs et invitations",
    allowedDependencies = {"shared", "contract", "identity", "access", "organization", "audit", "notification"})
package com.afrikcareunited.membership;

import org.springframework.modulith.ApplicationModule;
