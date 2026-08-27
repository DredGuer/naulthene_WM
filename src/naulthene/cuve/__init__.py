# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Adrien Nault — Naulthène AGI
"""
La Cuve — cerveau persistant en client-serveur (V21.0, expérimental).

- `daemon_cerveau` : le serveur (la Cuve elle-même), héberge un cerveau
  persistant en cryostase entre les connexions.
- `client_corps` : client jetable pilotant la Cuve via MiniGrid.
- `client_professeur` : client jetable pour les leçons de parole ponctuelles.

Voir docs/fonctionnement/LANCEMENT.md pour le guide de lancement complet.
"""
