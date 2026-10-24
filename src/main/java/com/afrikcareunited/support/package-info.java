/**
 * Accès de support de l'équipe AfrikCareUnited, en lecture et pour le seul demandeur
 * (platform.support_access), et nomination d'un administrateur de secours approuvée par un second membre
 * (platform.admin_recovery) : /organization/support-access, /platform/support-access,
 * /platform/admin-recoveries.
 * <p>Lot : L9.
 */
@ApplicationModule(
    displayName = "Accès de support et administrateur de secours",
    allowedDependencies = {"shared", "contract", "organization", "membership", "identity", "audit", "notification"})
package com.afrikcareunited.support;

import org.springframework.modulith.ApplicationModule;
