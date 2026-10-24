/**
 * Journal d'audit en ajout seul et altération détectable (schéma audit) : écriture dans la transaction de
 * l'action, séquenceur unique, chaîne d'empreintes par organisation, points de contrôle signés toutes les
 * 15 minutes, détails personnels effaçables, consultation, vérification et export CSV (/audit-events,
 * /platform/audit-events). RG-10, RG-11.
 * <p>Lot : L4.
 */
@ApplicationModule(
    displayName = "Journal d'audit",
    allowedDependencies = {"shared", "contract"})
package com.afrikcareunited.audit;

import org.springframework.modulith.ApplicationModule;
