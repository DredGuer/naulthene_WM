# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Adrien Nault — Naulthène AGI
"""Plug Simulé (v28.0, expérimental) — greffon déterministe pour les crash-tests.

Ne fait aucun appel réseau. `preferences_fixes` (optionnel) permet de forcer un avis
donné pour vérifier l'assimilation (Test 3 du plan v28.0) ; par défaut une préférence
légère et déterministe sur l'action 0. Le flag `panne` peut être basculé en cours de
run pour simuler une déconnexion brutale en plein épisode (Test 2, "Déconnexion en
Vol") — `interroger` lève alors une exception, exactement ce que `PortC3.canal_emission`
est censé capturer et mettre en cooldown, sans jamais remonter au noyau.

Note de conception : `panne` n'affecte QUE `interroger`, pas `est_disponible`. Un vrai
service qui tombe en marche ne se déclare généralement pas indisponible avant d'avoir
essayé de répondre — c'est `interroger` qui échoue en vol. Un plug annoncé disponible
mais qui lève est exactement le scénario que `PortC3.canal_emission` doit absorber."""

import numpy as np

from naulthene.exocortex.port_c3 import PlugC3, RequeteC3, ReponseC3


class PlugSimule(PlugC3):
    nom = "plug_simule"

    def __init__(self, preferences_fixes: np.ndarray | None = None, confiance: float = 0.5):
        self.preferences_fixes = preferences_fixes
        self.confiance = confiance
        self.panne = False  # basculé à True en vol pour le crash-test de déconnexion

    def est_disponible(self) -> bool:
        return True

    def interroger(self, requete: RequeteC3) -> ReponseC3 | None:
        if self.panne:
            raise RuntimeError("PlugSimule en panne simulée (crash-test)")
        if self.preferences_fixes is not None:
            preferences = self.preferences_fixes.astype(np.float32)
        else:
            preferences = np.zeros(requete.num_actions, dtype=np.float32)
            preferences[0] = 1.0
        return ReponseC3(preferences=preferences, confiance=self.confiance, origine=self.nom)
