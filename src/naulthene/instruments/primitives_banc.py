# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Adrien Nault — Naulthène AGI
"""Primitives partagées du banc standardisé (chantier EVA-01).

Foyer UNIQUE de quatre primitives auparavant dupliquées ou absentes. Pur stdlib :
ce module n'importe JAMAIS `noyau` (même règle d'absence de cycle que
`bus_sensoriel.py`).

Historique : `plus_court_chemin` et `intervalle_wilson` existaient en DEUX copies
corps-identiques (`sonde_inertie_motrice.py`, `sonde_plancher_geometrique.py`), sans
aucun test, et les deux copies affirmaient des conclusions OPPOSÉES de la même
prémisse. Voir CHANTIER_EVA-01 §3.4.
"""
from __future__ import annotations

import collections
import math


def plus_court_chemin(env) -> int | None:
    """Nombre de CASES du trajet minimal entre l'agent et le but, obstacles contournés.

    ⚠️ Compte les cases, pas les actions : une rotation coûte un tick de plus dans le jeu
    réel (et `N_ACTIONS` vaut 7). C'est donc une borne INFÉRIEURE du nombre de pas.

    Conséquence de lecture, et c'est le point qui avait été écrit à l'envers dans
    `sonde_inertie_motrice.py` : le rapport `trajet / plus_court_chemin` ne peut que
    SURESTIMER la directivité, jamais la sous-estimer.
    """
    u = env.unwrapped
    grille = u.grid
    depart = tuple(u.agent_pos)
    but = None
    for x in range(grille.width):
        for y in range(grille.height):
            o = grille.get(x, y)
            if o is not None and getattr(o, "type", None) == "goal":
                but = (x, y)
    if but is None:
        return None
    vus = {depart}
    file = collections.deque([(depart, 0)])
    while file:
        (x, y), d = file.popleft()
        if (x, y) == but:
            return d
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if not (0 <= nx < grille.width and 0 <= ny < grille.height):
                continue
            if (nx, ny) in vus:
                continue
            o = grille.get(nx, ny)
            if o is not None and getattr(o, "type", None) in ("wall", "lava"):
                continue
            vus.add((nx, ny))
            file.append(((nx, ny), d + 1))
    return None


def intervalle_wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Intervalle de confiance de Wilson pour `k` succès sur `n` essais.

    Wilson plutôt que l'intervalle normal : il reste valide aux taux extrêmes (0 %,
    100 %) là où l'approximation normale sort de [0, 1].
    """
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    m = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - m), min(1.0, c + m))


def longueur_normalisee(trajet: int, optimal: int | None) -> float | None:
    """`trajet / plus_court_chemin` — la convention est NOMMÉE ici, pas implicite.

    Le rapport est >= 1 par construction (le trajet réel ne peut pas être plus court que
    la borne inférieure `optimal`). Un `optimal` inconnu rend `None`, JAMAIS `0.0` :
    une métrique absente doit être absente, pas nulle.
    """
    if optimal is None or optimal <= 0:
        return None
    return trajet / optimal


def taux_avec_ic(k: int, n: int) -> dict:
    """Forme UNIQUE d'un taux et de son intervalle, pour que tous les rapports du banc
    soient comparables entre eux (mêmes clés, mêmes types)."""
    bas, haut = intervalle_wilson(k, n)
    return {
        "k": int(k),
        "n": int(n),
        "taux": (k / n) if n else 0.0,
        "ic_bas": bas,
        "ic_haut": haut,
    }
