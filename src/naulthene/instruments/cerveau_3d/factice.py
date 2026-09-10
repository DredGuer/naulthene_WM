# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Adrien Nault — Naulthène AGI
"""
VIS-01 — la source factice : un cerveau SYNTHÉTIQUE de même forme, sans aucun cerveau.

⚠️ FEUILLE, comme `telemetrie.py` : ce module n'importe NI `torch` NI `noyau` (numpy + la
télémétrie, rien d'autre). C'est la promesse de l'étape 0 du chantier : la démonstration
s'ouvre sur une machine qui n'a **pas** de cerveau, sans `.brain`, sans MiniGrid, sans GPU.
C'est aussi ce qui rend le mode factice utile au-delà de la démo (ruling du plan) : il est la
**FIXTURE** des tests du rendu, qui tournent donc sans `torch`.

⚠️ Ce que ce module NE fait pas, et ne fera jamais : lire un `.brain`, attacher des hooks à un
agent, écrire un fichier, entraîner quoi que ce soit. Il invente une structure de MÊME FORME
que la vraie (`definir_couches`, garde-fou du test d'anti-dérive
`test_forme_factice_egale_forme_reelle`) et la fait osciller. Le mouvement qu'on regarde est
donc **synthétique** : la page ne ment pas sur son origine, la bannière de la CLI l'écrit.

Voir `docs/ameliorations/CHANTIER_VIS-01_cerveau_3d_irm_vivante.md` §4 (les trois trames) et
`PLAN_VIS-01_cerveau_3d.md` (tâche 6).
"""
from __future__ import annotations

import math
import time

import numpy as np

from naulthene.cerveau.telemetrie import (
    DIM_AUDIO_ENTREE,
    DIM_VECTEUR_BIO,
    DIM_VISUELLE,
    NUM_ACTIONS,
    definir_couches,
    disposition,
    encoder_octets,
    quantifier_matrice,
    trame_activite,
    trame_evenement,
    trame_structure,
)

# La taille du cerveau FICTIF par défaut : celle du cerveau réel mesuré (`K4_NU_g11.brain`,
# 220 255 synapses, spec §4). Choisie identique pour que la démonstration juge la MÊME forme que
# l'étape 1 — une démonstration à `dim_bus = 16` ne dirait rien de ce que l'auteur va regarder.
DIM_BUS_FICTIF = 145

# Le nombre de rangs du flux (`RANGS` de `telemetrie`) : il règle le déphasage entre plaques.
NB_RANGS = 6

# Période de l'oscillation, en TRAMES (et non en secondes) : 60 trames ≈ 3 s à 20 Hz, ≈ 4 s à
# 15 Hz — un cycle lisible. ⚠️ La même formule exprimée en SECONDES ferait un cycle par minute :
# l'écran paraîtrait figé, et la seule chose que l'étape 0 doit montrer est justement le
# mouvement. « t » est donc le numéro de trame de la source, jamais un horodatage.
PERIODE_OSCILLATION = 60.0

# Un choc dopaminergique toutes les ~5 s : dans le vrai cerveau il marque la LTP (`fortifier_
# synapses`, noyau.py), ici il donne à la page un fait daté à afficher. Intensité 1,0 : un choc
# est un FAIT, pas une dose graduée — une source factice n'a aucun crédit à doser.
PERIODE_CHOC = 5.0


def bornes_factices(dim_bus: int) -> list[dict]:
    """Les bornes sensorielles et les têtes de la spec §5, pour un cerveau SYNTHÉTIQUE.

    ⚠️ Le rapporteur réel (tâche 7) LIT ces dimensions sur l'agent (`dim_visuelle`, `DIM_VOCALE`,
    `num_actions`) au lieu de les supposer : c'est cette table-ci qui est une convention figée,
    et elle n'est légitime que parce que la source factice n'a pas d'agent à interroger. Les
    valeurs sont celles de `telemetrie`, jamais des littéraux recopiés — une seule source.

    L'ORDRE des `rang_entree` est celui du `cat()` de `noyau.py` : le vecteur bio arrive APRÈS
    le bus (`189 = 145 + 44`), les actions AVANT (`153 = 8 + 145`). La page ne le suppose jamais,
    elle lit cette table (`planDesEntrees` dans `app.js`).
    """
    db = int(dim_bus)
    return [
        {"nom": "vision", "dim": DIM_VISUELLE, "couche": "porte_visuelle",
         "rang_entree": [0, DIM_VISUELLE]},
        {"nom": "audio", "dim": DIM_AUDIO_ENTREE, "couche": "porte_auditive",
         "rang_entree": [0, DIM_AUDIO_ENTREE]},
        {"nom": "vecteur_bio", "dim": DIM_VECTEUR_BIO, "couche": "integrateur_bio",
         "rang_entree": [db, db + DIM_VECTEUR_BIO]},
        {"nom": "actions", "dim": NUM_ACTIONS, "couche": "generateur_attente",
         "rang_entree": [0, NUM_ACTIONS]},
        {"nom": "actions", "dim": NUM_ACTIONS, "couche": "generateur_attente_audio",
         "rang_entree": [0, NUM_ACTIONS]},
    ]


def _poids_factices(couche: dict, rng: np.random.Generator) -> np.ndarray:
    """Des poids tirés de la MÊME loi que le vrai cerveau : `xavier_uniform_` (noyau.py).

    `nn.init.xavier_uniform_(base_weight)` pose `borne = sqrt(6 / (fan_in + fan_out))` et tire
    uniformément dans `[-borne, borne]`. On ne choisit donc pas une échelle « qui a l'air bien » :
    une couche large (`porte_visuelle`, 147×145) est plus faible qu'une tête étroite
    (`tete_motrice`, 145×8), exactement comme dans un cerveau neuf — sans quoi le seuil
    d'affichage des synapses ne se comporterait pas comme à l'étape 1.

    L'ORDRE des tirages suit celui de `definir_couches` : la graine suffit à rejouer la même
    structure à l'octet, ce qui rend la démonstration reproductible d'une session à l'autre.
    """
    borne = math.sqrt(6.0 / float(couche["entree"] + couche["sortie"]))
    return rng.uniform(-borne, borne,
                       size=(int(couche["sortie"]), int(couche["entree"]))).astype(np.float32)


def structure_factice(dim_bus: int, graine: int = 11) -> dict:
    """Une trame `structure` complète : 12 couches de même forme qu'un vrai cerveau, poids
    quantifiés `int8` + échelle, positions calculées par `disposition`, bornes sensorielles.

    ⚠️ `jour = 0` et `niveau = None` : la source factice n'a vécu aucune journée et ne joue
    aucun niveau. Le `null` est un AVEU, pas un oubli — écrire « niveau 1/15 » ferait afficher
    au panneau une information fausse (la page teste `trame.niveau.affiche` et se tait sinon).

    Déterministe : même `dim_bus`, même `graine` ⇒ même trame, à l'octet.
    """
    couches = definir_couches(int(dim_bus))
    geometrie = disposition(couches)
    rng = np.random.default_rng(int(graine))
    encodees = []
    for couche in couches:
        octets, echelle = quantifier_matrice(_poids_factices(couche, rng))
        positions = geometrie[couche["nom"]].astype(np.float16).tobytes()
        encodees.append({**couche, "echelle": echelle, "poids_i8": encoder_octets(octets),
                         "positions": encoder_octets(positions)})
    return trame_structure(encodees, bornes_factices(dim_bus),
                           {"jour": 0, "tick_absolu": 0, "dim_bus": int(dim_bus),
                            "niveau": None})


def _phases(couche: dict) -> np.ndarray:
    """Le déphasage de chaque neurone d'une plaque : celui du RANG, plus un décalage par neurone.

    - `2π · rang / 6` : l'onde parcourt les rangs dans l'ordre du FLUX DE DONNÉES (portes → têtes
      JEPA). C'est la seule lecture que ce choix affirme — pas une anatomie (spec §5).
    - `2π · i / n` : un cycle complet réparti sur la plaque. ⚠️ Sans ce second terme, les 145
      neurones d'une plaque s'allument et s'éteignent D'UN BLOC : le critère « les neurones
      s'allument » ne serait alors vrai qu'à l'échelle de la plaque, et la démonstration
      montrerait 12 aplats clignotants au lieu d'une onde. Le décalage est déterministe (aucun
      tirage) : la forme du mouvement est la même à chaque lancement.
    """
    n = max(1, int(couche["sortie"]))
    return (2.0 * math.pi * float(couche["rang"]) / float(NB_RANGS)
            + 2.0 * math.pi * np.arange(n, dtype=np.float64) / float(n))


def _trame_activite_factice(couches: list[dict], t: int) -> dict:
    """L'activité synthétique de la trame n° `t` : chaque neurone oscille dans `[0, 1]`.

    `valeur = 0,5 · (1 + sin(2π·t/60 + φ))` — normalisée dans `[0, 1]` comme une activation
    post-ReLU (la page colore `valeur / maximum` de la trame), puis encodée `float16` → base64
    exactement comme le fera le rapporteur réel : la page ne connaît qu'UN format.

    Les scalaires bougent aussi, à des périodes DIFFÉRENTES les unes des autres (240, 180, 120
    trames) : à période commune, tout l'écran monterait et descendrait ensemble et la ligne
    d'infos paraîtrait figée.
    """
    neurones = {}
    for couche in couches:
        angle = 2.0 * math.pi * float(t) / PERIODE_OSCILLATION + _phases(couche)
        valeurs = 0.5 * (1.0 + np.sin(angle))
        neurones[couche["nom"]] = encoder_octets(valeurs.astype(np.float16).tobytes())
    scalaires = {
        "dopamine": float(0.5 * (1.0 + math.sin(2.0 * math.pi * t / 240.0))),
        "faim": float(0.5 * (1.0 + math.sin(2.0 * math.pi * t / 180.0))),
        "force_planification": float(0.5 * (1.0 + math.sin(2.0 * math.pi * t / 120.0))),
        # L'action change ~1 fois par seconde : `int(t)` puisqu'un tick est un pas de temps, et
        # modulo le nombre d'actions réelles — jamais un 8 écrit en dur.
        "action": int(t // 15) % NUM_ACTIONS,
    }
    return trame_activite(neurones, scalaires, {"jour": 0, "tick": int(t)})


def boucle_factice(bus, hz: float = 15.0, dim_bus: int = DIM_BUS_FICTIF, arret=None,
                   duree: float | None = None, graine: int = 11) -> None:
    """Publie une structure puis une trame d'activité par période `1/hz`, jusqu'à `duree` ou
    jusqu'à ce que `arret` soit armé. Bloque l'appelant : elle est faite pour tourner dans un
    fil (la CLI l'y met).

    - `bus` : un `BusTrames` (`telemetrie`) — la source ne connaît rien d'autre.
    - `arret` : un objet à `is_set()` (`threading.Event`), ou `None` pour ne jamais s'arrêter
      autrement que par `duree`. Le test d'arrêt est fait EN TÊTE de tour : un arrêt demandé
      pendant le sommeil de la période ne publie pas une trame de plus.
    - `duree` : durée d'ÉMISSION en secondes (`None` = sans fin). À 20 Hz, `duree=1.0` publie
      les trames 0 à 19 — soit 20 trames, le plancher de 10 du critère n°1 étant très en dessous.
    - `graine` : graine de la structure (l'activité, elle, est entièrement déterministe).

    ⚠️ L'échéancier est ABSOLU (`debut + t·période`) et non « dors une période à chaque tour » :
    un `sleep(1/15)` qui dérive de 2 % ferait 12,5 Hz réels au bout de dix minutes. Ici une
    période en retard est rattrapée sans dormir, et l'horloge ne se décale jamais.
    """
    periode = 1.0 / float(hz)
    if periode <= 0.0:
        raise ValueError(f"cadence invalide : hz={hz!r} (attendu > 0)")
    couches = definir_couches(int(dim_bus))
    bus.publier_structure(structure_factice(dim_bus, graine))

    debut = time.monotonic()
    t = 0
    prochain_choc = PERIODE_CHOC
    while True:
        if arret is not None and arret.is_set():
            return
        ecoule = time.monotonic() - debut
        if duree is not None and ecoule >= float(duree):
            return
        bus.publier_activite(_trame_activite_factice(couches, t))
        if ecoule >= prochain_choc:
            bus.publier_evenement(trame_evenement("choc_dopamine", {"jour": 0, "tick": t},
                                                  intensite=1.0))
            prochain_choc += PERIODE_CHOC
        t += 1
        attente = (debut + t * periode) - time.monotonic()
        if attente > 0.0:
            time.sleep(attente)
