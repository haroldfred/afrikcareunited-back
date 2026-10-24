/**
 * Rôles système et personnalisés, catalogue des 12 permissions du M0, affectations datées (iam.role,
 * iam.permission, iam.role_permission, iam.assignment, iam.assignment_role) ; calcul des permissions
 * effectives du jour et de la portée de l'acteur (RG-01, RG-02, RG-04, RG-05, RG-08).
 * <p>Lot : L6.
 */
@ApplicationModule(
    displayName = "Rôles, permissions et affectations",
    allowedDependencies = {"shared", "contract", "organization", "audit"})
package com.afrikcareunited.access;

import org.springframework.modulith.ApplicationModule;
