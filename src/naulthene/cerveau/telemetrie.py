# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Adrien Nault — Naulthène AGI
"""
VIS-01 — la télémétrie du cerveau 3D : le format des trames, et rien d'autre.

⚠️ FEUILLE : ce module n'importe NI `torch` NI `noyau` (numpy seul). C'est ce qui permet à
`noyau.py` de l'importer à l'étape 2 sans créer de cycle d'import — même motif que
`bus_sensoriel.py`. Il ne connaît ni l'agent ni ses couches : il reçoit des tableaux et des
dictionnaires DÉJÀ extraits, et les met en forme.

Voir `docs/ameliorations/CHANTIER_VIS-01_cerveau_3d_irm_vivante.md` §4 pour le contrat des
trois trames, et `docs/ameliorations/PLAN_VIS-01_cerveau_3d.md` pour l'ordre de livraison.
"""
from __future__ import annotations

import base64
import json

import numpy as np

VERSION_TRAME = 1


def quantifier_matrice(m) -> tuple[bytes, float]:
    """Compresse une matrice de poids en `int8` + une échelle scalaire.

    `echelle = max(|m|) / 127` : la quantification est donc TOUJOURS relative au poids le plus
    fort de la couche, jamais à une constante posée — une couche faible et une couche forte sont
    décrites avec la même résolution relative. L'erreur commise est bornée par `echelle / 2`,
    soit `max(|m|) / 254`.

    Cas dégénéré : une matrice entièrement nulle n'a pas d'échelle définissable — on renvoie des
    octets nuls et `1.0` (et non `0.0`, qui produirait des NaN à la déquantification).
    """
    a = np.asarray(m, dtype=np.float32)
    pic = float(np.max(np.abs(a))) if a.size else 0.0
    if pic <= 0.0:
        return bytes(int(a.size)), 1.0
    echelle = pic / 127.0
    quantifie = np.clip(np.rint(a / echelle), -127.0, 127.0).astype(np.int8)
    return quantifie.tobytes(), echelle


def dequantifier_matrice(octets: bytes, echelle: float, forme) -> np.ndarray:
    """Inverse de `quantifier_matrice` — la seule perte est l'arrondi `int8`."""
    quantifie = np.frombuffer(octets, dtype=np.int8).astype(np.float32)
    return (quantifie * float(echelle)).reshape(tuple(forme))


def encoder_octets(octets: bytes) -> str:
    """Encodes binaires → texte, pour tenir dans un flux JSON (SSE)."""
    return base64.b64encode(octets).decode("ascii")


def decoder_octets(texte: str) -> bytes:
    """Inverse de `encoder_octets` ; `validate=True` refuse un texte corrompu plutôt que de
    rendre des octets silencieusement tronqués."""
    return base64.b64decode(texte.encode("ascii"), validate=True)
