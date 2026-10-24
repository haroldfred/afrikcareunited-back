# ADR 0005 — Journal d'audit en ajout seul, chaîné, avec points de contrôle signés

- Statut : acceptée, 24 octobre 2026
- Origine : Règles RG-10 et RG-11 ; conception, « Journal d'audit : altération détectable ».

## Contexte

Le journal doit résister à une modification faite par quelqu'un qui contrôle la base, sans ralentir les actions.

## Décision

Les entrées sont écrites dans la transaction de l'action, puis chaînées par un séquenceur unique (rôle `acu_audit`) : empreinte SHA-256 de l'entrée et de la précédente, une chaîne par organisation et une pour la plateforme. Toutes les 15 minutes, un point de contrôle signé part hors de la base, en stockage non modifiable. Les détails personnels sont dans une table à part, effaçables sans casser la chaîne. Modification, suppression et vidage sont refusés par la base.

## Conséquences

Toute altération couverte par un point de contrôle est détectée ; une entrée plus récente reste exposée au plus 15 minutes, et son statut l'indique (« En attente du point de contrôle »).
