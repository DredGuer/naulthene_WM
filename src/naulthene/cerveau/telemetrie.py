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
import socket
import threading
from collections import deque

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

    ⚠️ Cas NON FINI (ruling de revue) : un poids `NaN`/`inf` — cerveau dans un état inattendu —
    est traité **comme absent**, pas comme un pic. Sans le garde `np.isfinite(pic)`, `pic` vaut
    `nan` ou `inf`, `echelle` aussi, et la trame `structure` part avec un `NaN` que `JSON.parse`
    rejette : le navigateur n'affiche plus rien au lieu d'afficher un cerveau cassé (spec §9 —
    « cerveau dans un état inattendu : affiché comme tel, jamais corrigé »). On préfère donc des
    octets nuls et `1.0`, c'est-à-dire une plaque morte mais VALIDE.
    """
    a = np.asarray(m, dtype=np.float32)
    pic = float(np.max(np.abs(a))) if a.size else 0.0
    if not np.isfinite(pic) or pic <= 0.0:
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


# --- 2. La forme du cerveau et sa disposition (CONVENTION DE LECTURE, spec §5) ---

# L'ordre est celui du FLUX DE DONNÉES, pas une anatomie : Naulthène n'a ni cortex ni lobe.
# Il est déclaré ici une fois pour toutes et identique pour tous les cerveaux — c'est ce qui
# rend deux cerveaux comparables à l'écran.
RANGS = {
    "porte_visuelle": 0, "porte_auditive": 0,
    "hippocampe": 1, "analyseur": 2, "fusion_memoire": 2,
    "integrateur_bio": 3,
    "tete_motrice": 4, "cortex_prefrontal": 4, "tete_vocale": 4, "tete_requete": 4,
    "generateur_attente": 5, "generateur_attente_audio": 5,
}

# L'activation que `penser()` applique APRÈS la couche linéaire (relevé dans noyau.py, voir le
# plan) : le rapporteur applique exactement celle-ci, et rien d'autre. Un hook capture la sortie
# LINÉAIRE ; reproduire l'activation ici est un miroir, pas une réinterprétation.
ACTIVATION_PAR_COUCHE = {
    "porte_visuelle": "relu", "porte_auditive": "relu", "hippocampe": "relu",
    "analyseur": "relu", "fusion_memoire": "relu", "integrateur_bio": "relu",
    "tete_vocale": "sigmoide",
    "tete_motrice": "aucune", "cortex_prefrontal": "aucune", "tete_requete": "aucune",
    "generateur_attente": "aucune", "generateur_attente_audio": "aucune",
}

# Bornes sensorielles et têtes à sortie fixe — valeurs MESURÉES le 10/09/2026 sur un cerveau de
# 1500 jours (K4_NU_g11) ; le rapporteur, lui, les LIT sur l'agent au lieu de les supposer.
DIM_VISUELLE = 147
DIM_AUDIO_ENTREE = 130
DIM_VECTEUR_BIO = 44
NUM_ACTIONS = 8
DIM_ROUTAGE_C3 = 5

ECART_PLAQUES = 1.6    # distance entre deux rangs, sur l'axe Z
PAS_NEURONE = 0.09     # distance entre deux neurones voisins dans une plaque


def definir_couches(dim_bus: int) -> list[dict]:
    """Les 12 couches du cerveau, dans l'ordre de lecture — `(entree, sortie)` par couche.

    ⚠️ Sert de FIXTURE (source factice, tests). Le rapporteur réel ne l'utilise pas : il lit
    `in_features`/`out_features` sur l'agent, ce qui le rend insensible à une erreur ici.
    Un test compare d'ailleurs cette table à un agent neuf (`test_forme_factice_egale_forme_reelle`).
    """
    db = int(dim_bus)
    return [
        {"nom": "porte_visuelle", "rang": 0, "entree": DIM_VISUELLE, "sortie": db},
        {"nom": "porte_auditive", "rang": 0, "entree": DIM_AUDIO_ENTREE, "sortie": db},
        {"nom": "hippocampe", "rang": 1, "entree": 2 * db, "sortie": db},
        {"nom": "analyseur", "rang": 2, "entree": db, "sortie": db},
        {"nom": "fusion_memoire", "rang": 2, "entree": 2 * db, "sortie": db},
        {"nom": "integrateur_bio", "rang": 3, "entree": db + DIM_VECTEUR_BIO, "sortie": db},
        {"nom": "tete_motrice", "rang": 4, "entree": db, "sortie": NUM_ACTIONS},
        {"nom": "cortex_prefrontal", "rang": 4, "entree": db, "sortie": 1},
        {"nom": "tete_vocale", "rang": 4, "entree": db, "sortie": 8},
        {"nom": "tete_requete", "rang": 4, "entree": db, "sortie": DIM_ROUTAGE_C3},
        {"nom": "generateur_attente", "rang": 5, "entree": NUM_ACTIONS + db, "sortie": db},
        {"nom": "generateur_attente_audio", "rang": 5, "entree": NUM_ACTIONS + db, "sortie": db},
    ]


def disposition(couches: list[dict]) -> dict:
    """Positions `(n, 3)` de chaque neurone de SORTIE : une plaque par couche, sur un plan XY,
    empilée sur Z selon le rang. Grille régulière ⇒ **déterministe** (mêmes entrées, mêmes
    positions à l'octet), donc deux cerveaux se superposent exactement.
    """
    positions = {}
    for couche in couches:
        n = int(couche["sortie"])
        colonnes = max(1, int(np.ceil(np.sqrt(n))))
        lignes = int(np.ceil(n / colonnes))
        pts = np.zeros((n, 3), dtype=np.float32)
        for i in range(n):
            col, lig = i % colonnes, i // colonnes
            pts[i, 0] = (col - (colonnes - 1) / 2.0) * PAS_NEURONE
            pts[i, 1] = (lig - (lignes - 1) / 2.0) * PAS_NEURONE
            pts[i, 2] = float(couche["rang"]) * ECART_PLAQUES
        positions[couche["nom"]] = pts
    return positions


# --- 3. Les trois trames ---

def trame_structure(couches: list[dict], bornes: list[dict], meta: dict) -> dict:
    """`couches` : `{nom, rang, entree, sortie, echelle, poids_i8, positions}` — les matrices
    DÉJÀ quantifiées, et les positions DÉJÀ calculées par `disposition()` (`float16` n×3 encodé
    base64) : c'est le serveur qui calcule la géométrie, jamais le navigateur, pour que la
    disposition reste **une seule fois** définie (Python) et identique partout ·
    `bornes` : `{nom, dim, couche, rang_entree}` (vision, audio, vecteur bio, actions) ·
    `meta` : `{jour, tick_absolu, dim_bus, niveau}`."""
    return {"type": "structure", "version": VERSION_TRAME,
            "couches": couches, "bornes": bornes, **meta}


def trame_activite(neurones: dict, scalaires: dict, meta: dict) -> dict:
    """`neurones` : `{nom_couche: octets float16 encodés base64}` (déjà encodés, cf. tâche 7) ·
    `scalaires` : dopamine, faim, force_planification, action… · `meta` : `{jour, tick_absolu}`."""
    return {"type": "activite", "version": VERSION_TRAME,
            "neurones": neurones, "scalaires": scalaires, **meta}


def trame_evenement(genre: str, meta: dict | None = None, **champs) -> dict:
    """Un fait daté, pas une mesure continue : choc dopaminergique, victoire, neurogenèse."""
    return {"type": "evenement", "version": VERSION_TRAME, "genre": genre,
            **(meta or {}), **champs}


def serialiser(trame: dict) -> bytes:
    """JSON compact — la trame d'activité part 15 fois par seconde, chaque octet compte.

    ⚠️ `allow_nan=False` (ruling de revue) : `json.dumps` écrit `NaN`/`Infinity` par défaut —
    des littéraux que `JSON.parse` REJETTE. Un `NaN` qui s'échappe ferait tomber la page entière
    au lieu de laisser voir un cerveau cassé. Ici l'appelant perd la trame (`ValueError`) : un
    échec visible, jamais un datagramme invalide sur le réseau.
    """
    return json.dumps(trame, separators=(",", ":"), allow_nan=False).encode("utf-8")


def deserialiser(octets: bytes) -> dict | None:
    """`None` sur tout ce qui n'est pas une trame exploitable — jamais une exception : un
    datagramme tronqué ne doit pas tuer la boucle d'écoute (spec §9)."""
    try:
        trame = json.loads(octets.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(trame, dict) or "type" not in trame:
        return None
    return trame


# --- 4. Le bus borné (le présent, jamais du retard) et l'émetteur non bloquant ---

TAILLE_FILE_EVENEMENTS = 32


class BusTrames:
    """Le point de rendez-vous entre qui produit les trames et qui les sert.

    Choix assumé (spec §9) : l'activité n'est PAS une file — seule la DERNIÈRE trame est gardée.
    Si le serveur ou le navigateur prend du retard, on saute des images plutôt que d'accumuler
    du passé : on regarde un cerveau vivant, pas un enregistrement.
    """

    def __init__(self, taille_evenements: int = TAILLE_FILE_EVENEMENTS):
        self._verrou = threading.Lock()
        self._structure = None
        self._activite = None
        self._evenements = deque(maxlen=int(taille_evenements))
        self._sequence = 0
        self._sequence_structure = 0
        self._evenements_total = 0

    def publier_structure(self, trame: dict) -> None:
        with self._verrou:
            self._structure = trame
            self._sequence_structure += 1

    def publier_activite(self, trame: dict) -> None:
        with self._verrou:
            self._activite = trame
            self._sequence += 1

    def publier_evenement(self, trame: dict) -> None:
        with self._verrou:
            self._evenements.append(trame)
            self._evenements_total += 1

    @property
    def sequence(self) -> int:
        with self._verrou:
            return self._sequence

    @property
    def sequence_structure(self) -> int:
        """Nombre de structures publiées depuis la naissance du bus.

        ⚠️ Ruling de revue (tâche 4 — extension MINIMALE, la seule autorisée à ce module) :
        `structure()` rend la même chose avant et après une neurogenèse. Sans ce compteur, un
        abonné (le flux SSE) ne peut pas savoir que le cerveau a GRANDI, alors que la spec §9
        exige que le client reconstruise alors la scène. Comparer `sequence_structure` d'un tour
        à l'autre est la seule façon de détecter le CHANGEMENT, puisque les trames de structure
        ne portent ni compteur ni horodatage.
        """
        with self._verrou:
            return self._sequence_structure

    def structure(self):
        with self._verrou:
            return self._structure

    def activite(self):
        with self._verrou:
            return self._activite

    def evenements_depuis(self, index: int) -> tuple[list, int]:
        """`index` = valeur précédente de `compteurs()["evenements_total"]`. Renvoie les
        événements encore en file après cet index, et le nouveau total."""
        with self._verrou:
            total = self._evenements_total
            en_file = list(self._evenements)
        manquants = total - len(en_file)
        return en_file[max(0, index - manquants):], total

    def compteurs(self) -> dict:
        with self._verrou:
            return {"sequence": self._sequence,
                    "sequence_structure": self._sequence_structure,
                    "evenements_total": self._evenements_total,
                    "evenements_en_file": len(self._evenements)}


def analyser_cible_udp(cible: str) -> tuple:
    """`"udp:hote:port"` → `(hote, port)`. Une cible mal formée est une ERREUR DE CONFIGURATION :
    elle doit planter au démarrage, pas produire un silence qu'on prendrait pour un cerveau lent.
    """
    morceaux = str(cible).split(":")
    if len(morceaux) != 3 or morceaux[0] != "udp":
        raise ValueError(f"cible de télémétrie invalide : {cible!r} (attendu « udp:hote:port »)")
    return morceaux[1], int(morceaux[2])


# 🔴 MESURÉ le 10/09/2026, et c'est la raison d'être de cette constante : le `SO_SNDBUF` par
# défaut de macOS vaut **9 216 octets**, et le noyau refuse alors en `OSError [Errno 40]
# « Message too long »` tout datagramme plus gros — SANS que l'appelant puisse distinguer cette
# perte d'un cerveau lent. Or la trame d'activité grossit avec le bus (`≈ (8·dim_bus + 22) × 2,67`
# octets) : mesuré, 9 198 octets passent à `dim_bus = 408` et 9 230 ÉCHOUENT à `dim_bus = 409`.
# Les trames d'activité disparaissaient donc EN SILENCE dès que le cerveau grandissait.
#
# 1 Mio couvre le plafond DUR d'un datagramme UDP (65 507 octets) avec une marge confortable, pour
# une mémoire négligeable (un tampon par socket). Au-delà de 65 507, aucune valeur de `SO_SNDBUF`
# ne sauve la trame : c'est le protocole qui l'interdit, et `envoyer` la compte alors comme perdue.
TAMPON_ENVOI_UDP = 1 << 20


class EmetteurUDP:
    """Envoie une trame sans jamais attendre. Toute erreur ⇒ trame PERDUE, comptée, jamais une
    exception qui remonterait dans la boucle du cerveau."""

    def __init__(self, cible: str):
        self._adresse = analyser_cible_udp(cible)
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # ⚠️ RELEVER `SO_SNDBUF` AVANT `setblocking(False)` : sans cela, les trames d'activité
        # meurent en silence dès `dim_bus ≈ 409` (cf. `TAMPON_ENVOI_UDP`). `tampon_envoi` retient
        # la valeur EFFECTIVEMENT accordée par le noyau — qui peut être plus basse que celle
        # demandée (plafond système) ; c'est elle qui est vérifiée par `getsockopt` dans les tests,
        # et c'est elle qui décide si une trame passe.
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, TAMPON_ENVOI_UDP)
        self.tampon_envoi = int(self._socket.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF))
        self._socket.setblocking(False)
        self._envoyees, self._perdues = 0, 0

    def envoyer(self, trame: dict) -> bool:
        try:
            self._socket.sendto(serialiser(trame), self._adresse)
        except (OSError, ValueError, TypeError):
            # TypeError : un scalaire numpy (`variance du bus`, `logits C1/C2` — spec §4) n'est
            # pas sérialisable JSON. Sans lui, l'exception remonterait dans la boucle du cerveau.
            self._perdues += 1
            return False
        self._envoyees += 1
        return True

    def fermer(self) -> None:
        try:
            self._socket.close()
        except OSError:
            pass

    def compteurs(self) -> dict:
        return {"envoyees": self._envoyees, "perdues": self._perdues,
                "cible": f"{self._adresse[0]}:{self._adresse[1]}"}
