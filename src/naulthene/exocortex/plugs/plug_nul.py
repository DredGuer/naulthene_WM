# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Adrien Nault — Naulthène AGI
"""Plug Nul (v28.0, expérimental) — le plug par défaut, toujours indisponible.

C'est le mode nominal : un `AGI_Naulthene` sans aucun plug enregistré (ou seulement
avec `PlugNul`) doit se comporter EXACTEMENT comme la v27.6 — action 7 ("DEMANDER")
masquée à `-inf`, jamais échantillonnée. Utile pour tester explicitement le chemin
"C3 absent" sans avoir à omettre l'enregistrement d'un plug.
"""

from naulthene.exocortex.port_c3 import PlugC3, RequeteC3, ReponseC3


class PlugNul(PlugC3):
    nom = "plug_nul"

    def est_disponible(self) -> bool:
        return False

    def interroger(self, requete: RequeteC3) -> ReponseC3 | None:
        return None
