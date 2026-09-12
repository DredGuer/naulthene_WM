# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Adrien Nault — Naulthène AGI
"""Le banc final standardisé (chantier EVA-01) — juge à cartes figées.

Rejoue un ou plusieurs `.brain` sur des cartes et des graines IMPOSÉES à tous, en
lecture seule. Le banc ne s'entraîne jamais, ne promeut jamais un niveau, et n'écrit
jamais de `.brain`.

⚠️ Ce que ce banc ne prouve PAS : il mesure une compétence sur cartes imposées et ne dit
RIEN du cursus (règle « un banc forcé ne prouve rien sur le cursus », CLAUDE.md §7).

Protocole gelé : docs/fonctionnement/PROTOCOLE_BANC_FINAL.md
Conception : docs/ameliorations/CHANTIER_EVA-01_banc_final_standardise.md
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import statistics
import sys
import time
from datetime import datetime, timezone
from typing import Sequence

import numpy as np
import torch

from naulthene.cerveau.noyau import (
    DIM_VISUELLE,
    PROGRAMME,
    _budget_natif_carte,
    _graine_episode,
    creer_env,
    demarrer_journee,
    traiter_tick,
)
from naulthene.cerveau.persistance import PersistanceAnatomique
from naulthene.instruments.depouillement import Depouillement, Manifeste
from naulthene.instruments.primitives_banc import (
    longueur_normalisee,
    plus_court_chemin,
    taux_avec_ic,
)

CARTES_GELEES: tuple[int, int] = (3, 4)
GRAINE_EVAL_BASE_GELEE: int = 10000
GRAINE_EVAL_BASE_MINIMUM: int = 1000
DOSSIER_SORTIE_DEFAUT: str = "docs/recherche/evals/banc_final"

# Les 3 métriques de la famille pré-enregistrée (MES-04) : 1 primaire + 2 secondaires.
FAMILLE_METRIQUES: tuple[str, ...] = (
    "taux_franchissement",   # PRIMAIRE
    "retour_moyen",          # secondaire
    "longueur_normalisee",   # secondaire
)


class NomAmbigue(RuntimeError):
    """Plusieurs fichiers prétendent au même (bras, graine) — refus, jamais un choix."""


class GraineEvalRefusee(RuntimeError):
    """La base de graines d'évaluation empiéterait sur le pool d'entraînement."""


class EpisodesNonDerive(RuntimeError):
    """Le nombre d'épisodes doit venir du pilote : aucune valeur par défaut."""


class CarteInvalide(RuntimeError):
    """Index de carte hors du PROGRAMME."""


class BrasIntrouvable(RuntimeError):
    """Un bras déclaré ne résout AUCUN cerveau : faute de frappe, pas cohorte vide.

    Sans ce refus, `--bras K16_NU_TYPO` affichait `{'K16_NU_TYPO': 0}` et sortait en 0 —
    un succès silencieux, exactement ce que MES-01 interdit.
    """


class InstrumentIndisponible(RuntimeError):
    """Un instrument dont le banc dépend a disparu : on REFUSE de mesurer, jamais fausser.

    ⚠️ MESURÉ. Sans ce garde, un simple renommage dans `noyau.py` faisait tomber **tous** les
    `retour` à `0,0` (`etat.mix_somme.get("Env", 0.0)` → défaut silencieux) et **toutes** les
    empreintes de monde à vide (`getattr(detecteur, "positions_food", None)` → `[]`) : le banc
    aurait publié des métriques parfaitement fausses, sans une seule erreur — et `retour_moyen`
    appartient à la **famille de métriques gelée**. Un instrument absent doit EMPÊCHER la
    mesure, pas la dégrader en silence.
    """


def verifier_graine_eval_base(valeur: int) -> int:
    """Refuse une base de graines d'évaluation sous `GRAINE_EVAL_BASE_MINIMUM`.

    Le pool d'entraînement des campagnes réelles est 5…199 (multiples de 11). Une base
    à 0 — le défaut historique de `evaluer_cerveau.py` — collisionnait conceptuellement
    avec lui.
    """
    if int(valeur) < GRAINE_EVAL_BASE_MINIMUM:
        raise GraineEvalRefusee(
            f"--graine-eval-base {valeur} < {GRAINE_EVAL_BASE_MINIMUM} : risque de collision "
            f"avec le pool d'entraînement (5…199)")
    return int(valeur)


def exiger_episodes(valeur) -> int:
    """`n` est un RÉSULTAT du pilote (spec §8bis), jamais une constante de confort."""
    if valeur is None:
        raise EpisodesNonDerive(
            "--episodes est obligatoire : la valeur doit être DÉRIVÉE au pilote "
            "(spec §8bis), pas posée par défaut")
    valeur = int(valeur)
    if valeur < 1:
        raise EpisodesNonDerive(f"--episodes {valeur} invalide (minimum 1)")
    return valeur


def lire_graines_du_manifeste(cohorte: str) -> list[int]:
    """Lit `graines` dans `<cohorte>/manifeste.json` — la cohorte attendue est celle
    déclarée AVANT les runs (règle de Trace), jamais devinée après coup."""
    chemin = os.path.join(cohorte, "manifeste.json")
    with open(chemin, "r", encoding="utf-8") as f:
        donnees = json.load(f)

    graines = donnees.get("graines")
    if not graines and donnees.get("runs"):
        # Le manifeste du dépôt connaît DEUX formes (voir `depouillement.Manifeste`) :
        # `bras` × `graines`, ou une cohorte explicite `runs` — une LISTE de dicts
        # `{"nom": "A_g11", "fichier": "banc_A_g11.json"}`. N'en lire qu'une rendait un
        # diagnostic FAUX (« ne déclare aucune graine ») sur un manifeste parfaitement
        # valide (cas réel : brains/02092026_rejeu_banc_corrige, 20 runs).
        graines = sorted({int(m.group(1))
                          for entree in donnees["runs"]
                          for m in [re.search(r"_g(\d+)", str(entree.get("nom", "")))] if m})
    if not graines:
        raise ValueError(
            f"{chemin} : aucune graine lisible — formes reconnues : la clé `graines`, ou une "
            f"cohorte explicite `runs` dont les entrées portent « _g<graine> » dans `nom`")
    return [int(g) for g in graines]


def lister_cerveaux(dossier_bras: str, prefixe: str, graines: Sequence[int]) -> dict[int, str]:
    """Rend `{graine: chemin}` pour les noms CANONIQUES `{prefixe}_g{graine}.brain`.

    Refuse tout doublon `<...> N.brain` : ces fichiers portent une espace, existent
    réellement dans la campagne SCI-01, et leurs contenus DIFFÈRENT du canonique
    (mesuré le 12/09/2026). Choisir en silence fausserait l'appariement.
    """
    attendues = {int(g) for g in graines}
    canoniques: dict[int, str] = {}
    suspects: list[str] = []
    motif = re.compile(rf"^{re.escape(prefixe)}_g(\d+)(?: (\d+))?\.brain$")
    if not os.path.isdir(dossier_bras):
        return {}
    for nom in sorted(os.listdir(dossier_bras)):
        m = motif.match(nom)
        if m is None:
            continue
        graine, suffixe = int(m.group(1)), m.group(2)
        if suffixe is not None:
            if graine in attendues:
                suspects.append(nom)
            continue
        if graine in attendues:
            canoniques[graine] = os.path.join(dossier_bras, nom)
    if suspects:
        raise NomAmbigue(
            f"{dossier_bras} : {len(suspects)} fichier(s) surnuméraire(s) pour le même "
            f"(bras, graine) — refus, aucun choix silencieux : {', '.join(sorted(suspects))}")
    return canoniques


def refuser_bras_vides(resolue: dict[str, dict[int, str]]) -> dict[str, dict[int, str]]:
    """Refuse tout bras qui ne résout AUCUN cerveau : faute de frappe, pas cohorte vide.

    Appelé par `resoudre_cohorte` (chemin GLOB) **et** par `main()` APRÈS les deux branches —
    car la voie EXPLICITE ne passe pas par `resoudre_cohorte`, et c'est pourtant le chemin
    OBLIGATOIRE de la tâche 9 (5 bras sur 6 sont refusés par le glob). Un garde posé sur le
    seul chemin glob laissait donc le succès silencieux intact précisément là où il compte.
    """
    vides = sorted(b for b, v in resolue.items() if not v)
    if vides:
        raise BrasIntrouvable(
            f"aucun cerveau résolu pour {len(vides)} bras : {', '.join(vides)} — "
            f"vérifie l'orthographe du bras et la présence des fichiers canoniques "
            f"`<bras>_g<graine>.brain`")
    return resolue


def resoudre_cohorte(cohorte: str, bras: Sequence[str],
                     graines: Sequence[int]) -> dict[str, dict[int, str]]:
    """Rend `{bras: {graine: chemin}}`. L'absence d'un cerveau DANS une cohorte résolue
    n'est PAS traitée ici : c'est `Depouillement.collecter` qui refuse une cohorte
    incomplète (MES-01).

    En revanche un bras qui ne résout RIEN est refusé ici : c'est une faute de frappe, pas
    une cohorte vide. Sans ce garde, `--bras K16_NU_TYPO` affichait `0` cerveau et sortait
    en 0 — un succès silencieux.
    """
    return refuser_bras_vides(
        {b: lister_cerveaux(os.path.join(cohorte, b), b, graines) for b in bras})


def lire_cohorte_explicite(chemin: str) -> dict[str, dict[int, str]]:
    """Enumere la cohorte UN PAR UN : `{bras: {graine: chemin de .brain}}`.

    La spec exige cette voie quand un bras contient des surnumeraires — le glob refuse
    alors le bras entier (K8_NU en porte 2, mesures). Le glob reste le chemin par defaut
    avec son refus d'ambiguite ; ici rien n'est devine, et CHAQUE chemin declare doit
    exister, sinon le refus nomme les absents.
    """
    with open(chemin, "r", encoding="utf-8") as f:
        donnees = json.load(f)
    cohorte: dict[str, dict[int, str]] = {}
    absents: list[str] = []
    for nom_bras, par_graine in donnees.items():
        cohorte[nom_bras] = {}
        for graine, chemin_brain in par_graine.items():
            if not os.path.exists(chemin_brain):
                absents.append(chemin_brain)
                continue
            cohorte[nom_bras][int(graine)] = chemin_brain
    if absents:
        raise ValueError(
            f"cohorte explicite : {len(absents)} chemin(s) declare(s) mais absent(s) — "
            f"{', '.join(sorted(absents))}")
    return cohorte


def _recompense_env_cumulee(etat) -> float:
    """Σ des récompenses d'ENVIRONNEMENT depuis le début de la journée courante.

    ⚠️ `noyau.py` n'expose PAS `etat.recompense_env` : la récompense rendue par
    `env.step` n'y vit que le temps du tick (variable locale de `traiter_tick`) et
    n'est portée par AUCUN champ de l'état (vérifié : `vars(etat)` ne contient que
    `recompenses_journee`, qui cumule la récompense INTERNE, pas celle du monde). La
    seule lecture possible sans modifier `noyau.py` (ARC-01) est celle de la sonde de
    mixage, qui la CUMULE tick par tick dans `etat.mix_somme["Env"]` — et que
    `demarrer_journee` réarme (via `_reinitialiser_buffers_journee`). Le retour d'un
    épisode est donc la DIFFÉRENCE de cette accumulation sur la fenêtre de l'épisode.

    ⚠️ Lecture seule : le banc n'ajoute rien à la sonde, ne la réarme pas, et ne
    dépend d'aucune mécanique de `noyau.py` pour la mesurer.

    ⚠️ Le `0,0` de repli n'est PAS un silence : `_exiger_instruments` passe avant **et** après
    les ticks de chaque épisode, et refuse la mesure si la sonde a disparu ou s'est tue. Ici,
    un accumulateur vide est l'état LÉGITIME du début d'épisode (`demarrer_journee` vient de
    le réarmer).
    """
    return float(etat.mix_somme.get("Env", 0.0))


def _canonique(valeur, vus: set, profondeur_objet: int = 1):
    """Réduction DÉTERMINISTE et JSON-compatible d'une valeur quelconque, pour hachage.

    Les tenseurs et les tableaux entrent par leur empreinte (jamais par leur `repr`, qui est
    tronqué), les conteneurs récursivement, et les objets par le NOM DE LEUR TYPE **et** le
    contenu de leur `vars()` — jamais une adresse mémoire, qui rendrait l'empreinte différente
    d'un processus à l'autre sans qu'une seule grandeur ait bougé.

    ⚠️ `profondeur_objet=1` N'EST PAS UN DÉTAIL : à 0, 17 des 209 champs de `vars(etat)` se
    réduisaient à leur nom de type, et parmi eux `memoire_episodique_spatiale` — c'est-à-dire la
    MÉMOIRE, l'un des trois états que le brief nomme comme persistant avec la dopamine et la
    patience. Mesuré : à 0, un champ sur 12 était aveugle ; à 1, la mémoire rentre dans
    l'empreinte. La profondeur est BORNÉE à 1 pour ne pas descendre dans l'arbre des modules de
    l'agent (ses paramètres sont déjà hachés par le `state_dict`, et son optimiseur — inerte en
    évaluation — ne fait pas partie de l'état depuis lequel la mesure PART).

    Aucune troncature silencieuse : les séquences sont parcourues EN ENTIER (un plafond de
    longueur cacherait un changement de mémoire au-delà de la coupe, exactement le défaut que
    MES-01 interdit). Le seul garde est un anti-cycle par identité.
    """
    if isinstance(valeur, torch.Tensor):
        tenseur = valeur.detach().to("cpu").contiguous()
        try:
            octets = tenseur.numpy().tobytes()
        except TypeError:  # dtype sans vue numpy (bfloat16)
            octets = tenseur.float().numpy().tobytes()
        return ["tensor", list(tenseur.shape), str(tenseur.dtype),
                hashlib.sha256(octets).hexdigest()]
    if isinstance(valeur, np.ndarray):
        return ["array", list(valeur.shape), str(valeur.dtype),
                hashlib.sha256(np.ascontiguousarray(valeur).tobytes()).hexdigest()]
    if valeur is None or isinstance(valeur, (bool, int, float, str)):
        return valeur
    if isinstance(valeur, np.generic):
        return valeur.item()
    if isinstance(valeur, dict):
        if id(valeur) in vus:
            return ["cycle"]
        vus.add(id(valeur))
        reduit = ["dict", [[str(cle), _canonique(valeur[cle], vus, profondeur_objet)]
                           for cle in sorted(valeur, key=str)]]
        vus.discard(id(valeur))
        return reduit
    if isinstance(valeur, (list, tuple)):
        if id(valeur) in vus:
            return ["cycle"]
        vus.add(id(valeur))
        reduit = ["seq", [_canonique(element, vus, profondeur_objet) for element in valeur]]
        vus.discard(id(valeur))
        return reduit
    if isinstance(valeur, (set, frozenset)):
        # Trié par la forme CANONIQUE de chaque élément : l'ordre d'itération d'un `set` de
        # chaînes dépend du hachage du processus (PYTHONHASHSEED) et n'est pas reproductible.
        return ["set", sorted(repr(_canonique(element, vus, profondeur_objet))
                              for element in valeur)]
    attributs = vars(valeur) if profondeur_objet > 0 else None
    if isinstance(attributs, dict):
        if id(valeur) in vus:
            return ["cycle"]
        vus.add(id(valeur))
        # Un objet dont `vars()` n'est pas un dict (slots, C-extension) garde son seul type.
        reduit = ["objet", type(valeur).__name__,
                  {str(cle): _canonique(attributs[cle], vus, profondeur_objet - 1)
                   for cle in sorted(attributs, key=str)}]
        vus.discard(id(valeur))
        return reduit
    return ["objet", type(valeur).__name__]


def _empreinte_etat(etat) -> dict:
    """Empreinte sha256 de l'état de DÉPART du cerveau : poids/buffers **et** état volatil.

    Publiée par (bras, carte) dans le rapport : c'est l'artefact qui rend AUDITABLE la promesse
    « un état FRAIS par (bras, carte) ». Sans elle, la seule preuve de cette promesse était une
    sonde externe — et un artefact qui ne montre pas ce qu'il a mesuré ne peut pas être audité.

    ⚠️ POURQUOI L'ÉTAT VOLATIL EST INCLUS, ET PAS SEULEMENT LE `state_dict`. Mesuré sur un
    cerveau réel de la campagne SCI-01 (`K8_NU_g11.brain`, carte 0, graines 10000-10002) : une
    évaluation laisse le `state_dict` **BIT-IDENTIQUE** (`de0884ff9a9acbcc` avant ET après — en
    `eval()` et sous `torch.no_grad()`, poids et buffers ne bougent pas), alors qu'elle fait
    bouger l'état qui, LUI, persiste d'un appel à l'autre : dopamine `7,006 → 9,991`,
    `tick_absolu` `541824 → 541845`, plus la mémoire et les compteurs de journée. Un hachage du
    seul `state_dict` aurait donc été **AVEUGLE au défaut que la tâche 5 ferme** : avec un état
    PARTAGÉ entre deux cartes, les deux empreintes seraient restées ÉGALES et le mutant aurait
    survécu. `sha256_state_dict` est publié à côté pour que cette invariance se LISE.

    ⚠️ Déterminisme : deux `charger_ou_naitre()` du même `.brain` rendent la MÊME empreinte
    (`515d863f33f7545e`, mesuré) — sans quoi ce verrou échouerait au hasard au lieu de garder.

    Lecture seule : on lit `vars(etat)` et le `state_dict`, on ne modifie rien.
    """
    volatil = {cle: _canonique(valeur, set()) for cle, valeur in sorted(vars(etat).items())}
    poids = _canonique(etat.agent.state_dict(), set())

    def _sha(charge) -> str:
        return hashlib.sha256(json.dumps(
            charge, sort_keys=True, ensure_ascii=False, default=repr).encode("utf-8")).hexdigest()

    return {"sha256": _sha([volatil, poids]), "sha256_state_dict": _sha(poids)}


def _exiger_instruments(etat, ticks_joues: bool = False) -> None:
    """CRIE si un instrument dont le banc dépend a disparu ou s'est tu (voir la classe).

    Appelé DEUX fois par épisode :
      - AVANT la journée : l'accumulateur porte encore les canaux de l'épisode précédent, ce
        qui permet de voir un canal DISPARU sous un buffer non vide ;
      - APRÈS les ticks : la sonde doit avoir accumulé, sinon elle est morte et tous les
        retours seraient publiés à `0,0`.

    Ce qu'il exige, et pourquoi chacun :
      - `etat.mix_somme` est un dict — sans lui, `retour` tombe à `0,0` en silence ;
      - il n'a pas PERDU le canal `"Env"` — un buffer non vide qui ne le porte plus signale
        une sonde changée sous nos pieds ;
      - après ≥ 1 tick, il PORTE `"Env"` — une sonde muette rendrait tous les retours nuls ;
      - `detecteur_ressources_bio` expose `positions_food`/`positions_water` — sans eux,
        l'empreinte du monde serait publiée VIDE et un tirage de ressources différent
        redeviendrait invisible (c'est par ce champ que M1 est tué).

    Doctrine : une mesure REFUSÉE bruyamment vaut mieux qu'une mesure fausse et silencieuse.
    """
    accumulateur = getattr(etat, "mix_somme", None)
    if not isinstance(accumulateur, dict):
        raise InstrumentIndisponible(
            "etat.mix_somme a disparu (ou n'est plus un dict) : la sonde de mixage de "
            "`noyau.py` (v41.32) n'alimente plus le retour d'épisode, qui serait publié à "
            "0,0 SANS erreur. Vérifier `_sonder_mixage` et son réarmement dans "
            "`_reinitialiser_buffers_journee`.")
    if accumulateur and "Env" not in accumulateur:
        raise InstrumentIndisponible(
            f"etat.mix_somme cumule {len(accumulateur)} canal(aux) mais plus « Env » : la "
            f"récompense d'environnement n'est plus cumulée par la sonde de mixage de "
            f"`noyau.py`. Or `retour_moyen` appartient à la famille de métriques gelée — "
            f"vérifier `_sonder_mixage(etat, Env=…)` dans `traiter_tick`.")
    if ticks_joues and "Env" not in accumulateur:
        raise InstrumentIndisponible(
            "aucune récompense d'environnement accumulée alors que des ticks ont été joués : "
            "la sonde de mixage est MUETTE. Tous les retours seraient mesurés à 0,0 sans "
            "erreur — vérifier `_sonder_mixage(etat, Env=…)` dans `traiter_tick`.")
    detecteur = getattr(etat, "detecteur_ressources_bio", None)
    for attribut in ("positions_food", "positions_water"):
        if not hasattr(detecteur, attribut):
            raise InstrumentIndisponible(
                f"etat.detecteur_ressources_bio.{attribut} a disparu : l'empreinte du monde "
                f"serait publiée VIDE, et un tirage de ressources différent redeviendrait "
                f"invisible. Vérifier "
                f"`DetecteurRessourcesBiologiques.reinitialiser_episode`.")


def _forcer_carte(etat, index_carte: int) -> tuple[str, str]:
    """Remplace l'environnement de `etat` par `PROGRAMME[index_carte]` ; rend `(env_id, nom_classe)`.

    ⚠️ Ne touche PAS `etat.niveau_actuel` : le niveau du cursus reste une mesure de
    développement (exigence 5 du registre) — le banc n'impose qu'une carte de travail.

    ⚠️ Appelé aussi À CHAQUE ÉPISODE, et c'est nécessaire : dès que `fin_episode` bascule,
    `traiter_tick` rebascule lui-même sur une carte TIRÉE DU CURSUS
    (`_appliquer_niveau_episode(_tirer_niveau_episode(etat))`). Sans ce rappel, les épisodes
    suivants n'étaient plus joués sur la carte imposée — le rapport aurait décrit une carte
    jamais mesurée.

    Un détecteur neuf par carte : celui d'un autre niveau resterait accroché (leçon
    d'evaluer_cerveau.py l.77-81).
    """
    env_id, nom_classe = PROGRAMME[index_carte]
    etat.env.close()
    etat.env = creer_env(env_id, DIM_VISUELLE)
    etat.env_id = env_id
    etat.nom_classe = nom_classe
    etat.detecteur = None
    etat.palier_cible = 1
    return env_id, nom_classe


def _empreinte_monde(etat, graine_monde: int) -> dict:
    """Empreinte LISIBLE du monde réellement semé pour l'épisode en cours.

    ⚠️ POURQUOI ELLE EXISTE. Sans elle, le rapport ne disait RIEN de la carte jouée ni du
    tirage : deux évaluations pouvaient diverger (mondes différents) en publiant un résultat
    identique, et la dérive de carte était **invisible dans l'artefact** — il fallait muter
    le code pour la voir. Mesuré : les trois leviers de graine retirés, les positions de
    ressources différaient d'une passe à l'autre (`((3,1),(1,2))` contre `((2,1),(1,2))`)
    pendant que le rapport, lui, restait identique.

    Ce qu'elle porte, et pourquoi chaque champ :
      - `graine` : la graine que le monde VA consommer (`_graine_episode(etat)` au moment du
        reset). C'est le seul moyen de rendre lisible une carte dont le contenu ne dépend pas
        du tirage — `MiniGrid-Empty-5x5-v0` a un but et un départ FIXES, donc son contenu ne
        varie jamais avec la graine, alors que des cartes à disposition aléatoire, si ;
      - `but`, `depart`, `direction` : la disposition engendrée par cette graine ;
      - `food`, `water`, `nid` : les sources SEMÉES par `DetecteurRessourcesBiologiques`, qui
        dépendent du `np.random` GLOBAL, pas de la graine d'environnement.

    Tout est rendu en listes (jamais un `set` de tuples, qui ne se sérialise pas en JSON) et
    TRIÉ, pour que deux mondes identiques donnent une empreinte identique au bit près.

    ⚠️ Lecture seule : on lit la grille et les positions semées, on n'écrit rien. Le balayage
    du but est local parce que `plus_court_chemin` rend la DISTANCE au but, pas sa position.
    """
    u = etat.env.unwrapped
    but = None
    for x in range(u.grid.width):
        for y in range(u.grid.height):
            objet = u.grid.get(x, y)
            if objet is not None and getattr(objet, "type", None) == "goal":
                but = [int(x), int(y)]
    detecteur = getattr(etat, "detecteur_ressources_bio", None)

    def _cases(positions):
        return sorted([int(x), int(y)] for x, y in (positions or ()))

    nid = getattr(detecteur, "nid_position", None)
    return {
        "graine": int(graine_monde),
        "but": but,
        "depart": [int(u.agent_pos[0]), int(u.agent_pos[1])],
        "direction": int(u.agent_dir),
        "food": _cases(getattr(detecteur, "positions_food", None)),
        "water": _cases(getattr(detecteur, "positions_water", None)),
        "nid": [int(nid[0]), int(nid[1])] if nid is not None else None,
    }


def evaluer_cerveau_sur_carte(etat, index_carte: int, graines: Sequence[int],
                              max_ticks: int = 0) -> dict:
    """Rejoue `graines` épisodes SEEDÉS sur `PROGRAMME[index_carte]`, en lecture seule.

    Reproductibilité (décision D1) : pour un épisode d'identité `s`, on pose la graine de
    l'ENVIRONNEMENT (`env.reset(seed=s)`) **et** celle du RNG torch (`torch.manual_seed(s)`).
    La seconde est l'apport d'EVA-01 : sans elle, `Categorical(...).sample()` dans
    `noyau.py` tire une suite d'actions différente à chaque exécution.

    ⚠️ La première ne suffit PAS seule : depuis la v41.9, `demarrer_journee` réamorce
    l'environnement avec une graine DÉRIVÉE (`_graine_episode`), ce qui rend
    `env.reset(seed=s)` inopérant. Le banc fixe donc aussi les deux termes de cette
    dérivation (`graine_run`, `episodes_vecus`) — voir le commentaire de la boucle, qui
    porte la mesure du défaut.

    ⚠️ Le forçage remplace `etat.env` mais ne touche PAS `etat.niveau_actuel` : le niveau du
    cursus reste une mesure de développement (exigence 5 du registre).

    ⚠️ CE QUE CHAQUE ÉPISODE PUBLIE, EN PLUS DE SES MÉTRIQUES. La mesure ne suffit pas : il
    faut pouvoir AUDITER le monde qui l'a produite **et le comportement qu'elle a suivi**.
    Chaque entrée d'`episodes` porte donc `env_id` (la carte réellement jouée), `budget` (les
    ticks réellement reçus), `monde` (empreinte du tirage : graine consommée, but, départ,
    ressources semées) et `trajectoire` (positions occupées, distinctes, dans l'ordre de
    première visite). Sans `monde`, un épisode joué dans un AUTRE monde restait invisible ;
    sans `trajectoire`, deux politiques différentes produisaient le MÊME rapport — mesuré par
    la revue indépendante : **176 ticks divergents sur 972 avec un dict publié identique**.
    Le `budget` de tête est celui de la carte imposée ; les `budget` par épisode doivent lui
    être égaux (re-forçage oblige), et une divergence se lit désormais au lieu d'être tue.

    ⚠️ AUCUN INSTRUMENT MANQUANT NE DÉGRADE LA MESURE EN SILENCE : `_exiger_instruments`
    passe avant chaque épisode **et** après ses ticks, et lève `InstrumentIndisponible`
    plutôt que de publier des retours à `0,0` ou une empreinte vide.

    ⚠️ LES TROIS LEVIERS DE GRAINE SONT L'ENSEMBLE DU DISPOSITIF (voir le commentaire de la
    boucle) — un quatrième a été cherché et **écarté par la mesure**. Hypothèse testée : la
    NAISSANCE d'un cerveau tirerait elle aussi du `np.random` GLOBAL, ce qui exigerait un `np.random.seed(...)` avant
    `charger_ou_naitre()`. Mesuré : faux, et de trois façons — `np.random.get_state()[2]` vaut
    **624 avant et après** une naissance complète (zéro tirage consommé) ; deux naissances
    seedées en torch donnent le même `state_dict` (`sha256 = 134895af4844680b`) que
    `np.random` soit seedé ou non ; leur empreinte LARGE (`4817393f8d31475d`) reste identique
    quand les deux naissances partent d'états `np.random` DIFFÉRENTS. La naissance est tirée
    par `nn.init.xavier_uniform_` sur `base_weight`, donc par torch seul.
    """
    if not 0 <= index_carte < len(PROGRAMME):
        raise CarteInvalide(f"index de carte {index_carte} hors PROGRAMME (0…{len(PROGRAMME) - 1})")

    env_id, nom_classe = _forcer_carte(etat, index_carte)

    budget = int(max_ticks) if max_ticks > 0 else _budget_natif_carte(etat.env)
    episodes = []
    for graine in graines:
        graine = int(graine)
        # AVANT la journée : l'accumulateur de la sonde porte encore l'épisode précédent, donc
        # un canal disparu s'y voit. Un instrument manquant REFUSE la mesure (voir la classe).
        _exiger_instruments(etat)
        if etat.env_id != env_id:
            # ⚠️ LA CARTE DÉRIVE EN COURS D'ÉVALUATION. `traiter_tick` appelle, à la bascule
            # de `fin_episode`, `_appliquer_niveau_episode(_tirer_niveau_episode(etat))` :
            # l'épisode suivant partait alors sur la carte du CURSUS, plus sur la carte
            # imposée. Mesuré sur la carte 3 (`SimpleCrossingS9N1`, budget 324) : premier
            # épisode à 324 ticks, second à **100** — le budget de `Empty-5x5`, avec
            # `env_id` final `MiniGrid-Empty-5x5-v0`. Le rapport aurait donc attribué à la
            # carte 3 des épisodes joués ailleurs. On re-force à CHAQUE épisode.
            _forcer_carte(etat, index_carte)
        # --- L'IDENTITÉ D'ÉPISODE EST `graine` : LES TROIS GÉNÉRATEURS QUI EN DÉCIDENT ---
        #
        # 1. LE MONDE. `demarrer_journee` ne consomme PAS la graine posée par
        #    `env.reset(seed=…)` : il appelle `_reset_seede`, qui réamorce l'environnement
        #    avec `_graine_episode(etat)` = `etat.graine_run × GRAINE_ECART_ENTRE_RUNS +
        #    etat.episodes_vecus` (v41.9). Un `env.reset(seed=graine)` seul est donc un
        #    NO-OP — mesuré : deux passes du même cerveau gagnaient l'épisode 10001 en
        #    **64** puis en **82** ticks. Le banc fixe les DEUX termes de cette dérivation,
        #    sans quoi la carte d'un épisode dépend du nombre d'épisodes déjà vécus dans le
        #    processus : deux bras n'affronteraient plus le même monde pour la même graine.
        #    (`episodes_vecus` n'a qu'un rôle mécanique dans tout `noyau.py` — vérifié.)
        # 2. LES RESSOURCES SEMÉES dans le monde et le TIRAGE DU CURSUS passent, eux, par le
        #    `np.random` GLOBAL (`DetecteurRessourcesBiologiques`, `_tirer_niveau_episode`) —
        #    que ni la graine d'environnement ni `torch.manual_seed` ne contrôlent. Mesuré :
        #    sans ce seed, deux passes identiques divergeaient (graine 10000 gagnée en 75
        #    ticks d'un côté, perdue de l'autre) ; avec lui, elles sont bit-identiques.
        # 3. L'ACTION est échantillonnée par `torch` (`Categorical(...).sample()` dans
        #    `noyau.py`) — c'est l'apport D1 d'EVA-01, sans lequel la suite d'actions
        #    change à chaque exécution.
        #
        # On seede AVANT `demarrer_journee` : c'est là que le monde est semé, et un second
        # reset après coup désynchroniserait les détecteurs déjà calibrés sur la carte tirée.
        etat.graine_run = 0
        etat.episodes_vecus = graine
        etat.env.reset(seed=graine)
        np.random.seed(graine)
        # La graine que `_reset_seede` va consommer DANS `demarrer_journee` : lue ici, avant
        # l'incrément du compteur, c'est exactement celle du monde de CET épisode. Elle entre
        # dans l'empreinte publiée, sinon une carte à disposition FIXE (`Empty-5x5` : but et
        # départ constants) ne laisserait aucune trace d'un changement de graine.
        graine_monde = _graine_episode(etat)
        demarrer_journee(etat)
        torch.manual_seed(graine)  # D1 — reproductibilité de l'échantillonnage d'action

        # --- CE QUE L'ÉPISODE A RÉELLEMENT JOUÉ, PUBLIÉ DANS LE RÉSULTAT ---
        # La carte est lue ICI, après le forçage et le reset : c'est celle dans laquelle les
        # ticks vont se dérouler. Le budget est celui de CETTE carte (borné par `max_ticks`
        # s'il est posé) — avec le re-forçage il vaut le budget annoncé ; s'il en divergeait,
        # l'artefact le DIRAIT au lieu de le taire.
        carte_jouee = etat.env_id
        budget_episode = int(max_ticks) if max_ticks > 0 else _budget_natif_carte(etat.env)
        empreinte = _empreinte_monde(etat, graine_monde)

        optimal = plus_court_chemin(etat.env)
        recompense_avant = _recompense_env_cumulee(etat)
        gagne, ticks, tronque, recompense = False, None, True, 0.0
        # --- LA TRAJECTOIRE, SANS LAQUELLE L'ARTEFACT EST AVEUGLE AU COMPORTEMENT ---
        # Mesuré par la revue indépendante : sur la carte 3, 176 ticks sur 972 divergeaient
        # entre deux passes ALORS QUE le rapport publié était identique — les 3 épisodes
        # donnent `gagne=False`, `ticks=324` (le budget entier), `retour=0.0`, et le monde
        # semé est constant. Tout ce qui était publié était donc aveugle à la trajectoire.
        # On publie les positions OCCUPÉES, distinctes, dans l'ordre de première visite :
        # compact (une carte 9×9 en compte quelques dizaines) et fidèle à ce qui a été joué.
        #
        # ⚠️ Lues dans `environnement_episode`, JAMAIS dans `etat.env` : au tick de bascule,
        # `traiter_tick` peut avoir remplacé `etat.env` par une carte du CURSUS — la position
        # lue serait alors celle d'un autre monde.
        environnement_episode = etat.env
        positions_vues: list[list[int]] = []
        vues = set()
        with torch.no_grad():
            for _tick in range(budget_episode):
                ticks_avant = etat.ticks_episode_courant
                traiter_tick(etat)
                position = environnement_episode.unwrapped.agent_pos
                cle = (int(position[0]), int(position[1]))
                if cle not in vues:
                    vues.add(cle)
                    positions_vues.append([cle[0], cle[1]])
                # `traiter_tick` enchaîne LUI-MÊME sur un nouvel épisode dès que
                # `fin_episode` bascule : on lit la victoire au tick MÊME de la bascule.
                if etat.fin_episode:
                    _exiger_instruments(etat, ticks_joues=True)
                    gagne = bool(etat.victoire_aujourdhui)
                    ticks = ticks_avant + 1
                    tronque = False
                    recompense = _recompense_env_cumulee(etat) - recompense_avant
                    break
            if tronque:
                # Un épisode tronqué n'a pas de victoire, mais sa récompense partielle
                # reste une information MESURÉE : on la calcule, on ne la laisse pas à 0,0.
                _exiger_instruments(etat, ticks_joues=True)
                recompense = _recompense_env_cumulee(etat) - recompense_avant
        episodes.append({
            "graine": graine,
            "gagne": gagne,
            "tronque": tronque,
            "ticks": ticks,
            "retour": recompense,
            # --- Ce que l'épisode a RÉELLEMENT joué (audit du JSON, sans muter le code) ---
            # `env_id` : la carte des ticks. Un épisode joué ailleurs qu'annoncé se lit ici,
            # au lieu d'être invisible dans l'artefact.
            "env_id": carte_jouee,
            # `budget` : le nombre de ticks que CET épisode a reçus. Avec le re-forçage il
            # vaut le budget annoncé en tête de résultat ; une divergence signalerait que la
            # carte n'a pas été tenue.
            "budget": budget_episode,
            # `monde` : empreinte du monde semé (graine consommée, but, départ, ressources).
            "monde": empreinte,
            # `trajectoire` : les positions occupées, distinctes, dans l'ordre de première
            # visite. C'est le seul champ SENSIBLE AU COMPORTEMENT — sans lui, deux
            # trajectoires différentes (donc deux politiques) produisent le MÊME rapport :
            # mesuré, 176 ticks divergents sur 972 avec un dict publié identique.
            "trajectoire": positions_vues,
            # La longueur n'a de sens que sur un épisode GAGNÉ : sur un échec, le
            # « trajet » est la durée du budget et le rapport ne mesurerait rien.
            "longueur_normalisee": longueur_normalisee(ticks, optimal) if gagne else None,
        })

    gagnes = sum(1 for e in episodes if e["gagne"])
    longueurs = [e["longueur_normalisee"] for e in episodes
                 if e["longueur_normalisee"] is not None]
    return {
        "index_carte": index_carte,
        "env_id": env_id,
        "nom_classe": nom_classe,
        "optimal": optimal,
        "budget": budget,
        "episodes": episodes,
        "gagnes": gagnes,
        "tronques": sum(1 for e in episodes if e["tronque"]),
        "taux": taux_avec_ic(gagnes, len(episodes)),
        "retour_moyen": float(statistics.mean([e["retour"] for e in episodes])) if episodes else 0.0,
        "longueur_mediane": (float(statistics.median(longueurs)) if longueurs else None),
    }


def construire_depouillement(cohorte: str, bras: Sequence[str], graines: Sequence[int],
                             metriques_par_chemin: dict) -> Depouillement:
    """Déclare la cohorte puis la collecte, en déléguant à MES-01.

    Le `lecteur` rend les métriques DÉJÀ calculées, indexées par chemin de `.brain` ; un
    cerveau absent ou non évalué rend `None`, ce que `collecter` transforme en violation
    — c'est ainsi que la cohorte incomplète devient structurellement impossible.

    ⚠️ `extension_log=".brain"` N'EST PAS COSMÉTIQUE : sans lui, le banc ne publie JAMAIS rien.
    `Manifeste.cohorte` compose ses chemins en `<cohorte>/<bras>/<bras>_g<graine>` +
    `extension_log`, dont le défaut est `.log`. Or `collecter` exige d'abord
    `os.path.exists(chemin)`, et le `lecteur` cherche ensuite ce chemin dans
    `metriques_par_chemin`, INDEXÉ PAR CHEMIN DE `.brain` (la seule grandeur que le banc
    mesure). Mesuré : `Manifeste(...).cohorte` rend
    `[('A_g11', '/cohorte/A/A_g11.log'), ('A_g22', '/cohorte/A/A_g22.log')]` par défaut, et
    `[… '/cohorte/A/A_g11.brain']` avec `.brain`. Avec le défaut, les 4 (bras, graine) seraient
    donc exclus pour « fichier absent », `dp.runs` resterait VIDE, et une campagne pourtant
    complète serait déclarée invalide à chacune de ses exécutions.

    Aucune statistique n'est recodée ici : appariement par graine d'entraînement, seuil de
    Bonferroni (`seuil_t(n, comparaisons_prevues, alpha)`) et refus de publier viennent tous de
    `depouillement.py` (MES-01).

    ⚠️ `dossier` EST LE NOM DU BRAS, JAMAIS `os.path.join(cohorte, b)` — ET CE DÉFAUT RENDAIT LE BANC
    INUTILISABLE SUR SON PROPRE CHEMIN DOCUMENTÉ. `Manifeste.cohorte` compose
    `<dossier>/<prefixe>_g<graine>.brain`, et `Depouillement.chemin_run` RE-préfixe ce chemin par sa
    `racine` (posée à `cohorte` ici). Un `dossier` déjà préfixé DOUBLAIT donc tout : mesuré sur la
    cohorte réelle (`--cohorte brains/08092026_sci01_balayage_K`, invocation du plan, 40 `.brain`),
    le manifeste réclamait `brains/08092026_sci01_balayage_K/brains/08092026_sci01_balayage_K/
    K16_NU/K16_NU_g11.brain` → **0 run collecté, 40 violations « fichier absent », aucun agrégat,
    dossier de sortie non créé**. Avec une cohorte ABSOLUE, `os.path.join(racine, chemin_absolu)`
    rend le chemin absolu : le doublage disparaissait **par accident**, et TOUS les tests, qui
    passent par `tempfile` donc par des chemins absolus, étaient aveugles à ce défaut.

    ⚠️ LA RENCONTRE ENTRE LE MANIFESTE ET LES MÉTRIQUES EST CANONICALISÉE (`os.path.abspath`), ET NE
    DOIT PAS ÊTRE UNE COÏNCIDENCE TEXTUELLE. Le manifeste recompose ses chemins, et les clés de
    `metriques_par_chemin` viennent de la résolution (`resoudre_cohorte`) ou, en voie EXPLICITE,
    d'un inventaire JSON écrit à la main : rien ne garantit la même écriture des deux côtés
    (`./brains/…` contre `brains/…`, relatif contre absolu). Mesuré : des clés relatives face à une
    racine absolue suffisaient à tout exclure en « source illisible ou vide ». On compare donc les
    chemins canoniques, jamais leur orthographe.
    """
    manifeste = Manifeste(
        campagne=os.path.basename(os.path.normpath(cohorte)),
        mode="confirmatoire",
        graines=[int(g) for g in graines],
        bras={b: {"dossier": b, "prefixe": b} for b in bras},
        alpha=0.05,
        comparaisons_prevues=len(FAMILLE_METRIQUES),
        extension_log=".brain",
    )
    dp = Depouillement(manifeste, racine=cohorte)
    metriques_canoniques = {os.path.abspath(chemin): metriques
                            for chemin, metriques in metriques_par_chemin.items()}
    dp.collecter(lambda chemin: metriques_canoniques.get(os.path.abspath(chemin)))
    return dp


def executer_banc(cohorte: str, bras: Sequence[str], cartes: Sequence[int],
                  graines: Sequence[int], episodes: int, graine_eval_base: int,
                  dossier_sortie: str, max_ticks: int = 0,
                  cohorte_resolue: dict | None = None) -> dict:
    """Évalue toute la cohorte, puis publie le rapport et l'agrégat JSON.

    ⚠️ `cohorte_resolue` est le SEUL moyen de faire entrer la voie EXPLICITE jusqu'ici :
    `resoudre_cohorte` passe par le glob, qui REFUSE 5 des 6 bras de la campagne SCI-01
    (mesuré : 113 surnuméraires). Sans ce paramètre, `--cohorte-explicite` serait perdu au
    moment de l'évaluation et la tâche 9 échouerait à la résolution — après dix tâches.
    """
    cartes = [int(c) for c in cartes]
    graines_eval = list(range(int(graine_eval_base), int(graine_eval_base) + int(episodes)))
    if cohorte_resolue is None:
        cohorte_resolue = resoudre_cohorte(cohorte, bras, graines)

    par_cerveau, metriques_par_chemin = {}, {}
    for nom_bras, cerveaux in cohorte_resolue.items():
        for graine, chemin in sorted(cerveaux.items()):
            cle = f"{nom_bras}_g{graine}"
            par_carte = {}
            # L'empreinte de l'état de DÉPART de chaque carte : publiée plus bas à côté de
            # `cartes`, elle est la seule pièce qui rend la fraîcheur de l'état AUDITABLE.
            empreintes_etat_initial = {}
            t0 = time.time()
            for index_carte in cartes:
                # ⚠️ L'ÉTAT EST RECHARGÉ ICI, DONC PAR (bras, carte) — ET C'EST STRUCTURANT.
                # `evaluer_cerveau_sur_carte` n'est PAS une fonction pure de
                # (fichier .brain, carte, graines) : le cerveau GARDE son état d'un appel à
                # l'autre (mémoire, dopamine, patience), si bien que le MÊME épisode ne rend
                # plus le même résultat selon ce qui a été joué avant lui. Mesuré par la revue
                # indépendante de la tâche 4 : carte 0 → victoires **1, 2, 2** ; carte 4 (une
                # carte GELÉE du plan) → **0, 0, 1** ; et une autre carte intercalée déplace un
                # même épisode de 61 à **88** ticks, soit **+44 %** sur `longueur_normalisee`,
                # une métrique de la FAMILLE. Ce n'est PAS un défaut de seeding : deux cerveaux
                # nés sous la même graine, évalués UNE fois chacun, donnent des trajectoires
                # identiques — c'est bien l'état du cerveau qui survit.
                # Conséquence : recharger le `.brain` avant CHAQUE (bras, carte), pour que le
                # chiffre d'une carte ne dépende pas de l'ORDRE d'évaluation dans le processus.
                # Sans cela, deux bras évalués dans un ordre différent ne sont plus comparables
                # et l'appariement par graine (tâche 9) perd son sens.
                # Parade VÉRIFIÉE : deux `charger_ou_naitre()` du même `.brain` rendent un
                # `state_dict` BIT-IDENTIQUE. Coût : une relecture de fichier par (bras, carte),
                # négligeable devant les épisodes joués. Le flux aléatoire, lui, n'est pas
                # décalé par cette relecture : `evaluer_cerveau_sur_carte` réamorce torch ET
                # `np.random` à chaque épisode.
                # REPRODUIT ET CHIFFRÉ ICI, sur un cerveau RÉEL de la campagne SCI-01
                # (`brains/08092026_sci01_balayage_K/K8_NU/K8_NU_g11.brain`), carte 0, graines
                # 10000-10002, MÊME carte évaluée 3 fois de suite — l'état partagé dérive,
                # l'état frais non :
                #   état PARTAGÉ : ticks de la graine 10000 = **10, 44, 25** et
                #                 `longueur_normalisee` = **2,5 → 11,0 → 6,25** (+340 % du 1er
                #                 au 2e appel) ;
                #   état FRAIS   : les trois appels rendent le MÊME triplet `[10, 6, 5]`.
                # (Sur la carte 4 du même cerveau l'effet n'est pas visible : il perd les trois
                # épisodes au budget entier — l'effet dépend donc de la carte, ce qui est une
                # raison de plus pour ne pas s'en remettre à l'ordre.)
                # ⚠️ La parade suppose que le `.brain` EXISTE : les deux voies de résolution le
                # garantissent (`lister_cerveaux` ne rend que des noms présents,
                # `lire_cohorte_explicite` refuse un chemin absent) — sinon `charger_ou_naitre`
                # ferait NAÎTRE un cerveau différent à chaque carte, ce qui serait pire.
                etat = PersistanceAnatomique(fichier=chemin).charger_ou_naitre()
                etat.agent.eval()  # jamais d'entraînement, jamais de sauvegarde
                # ⚠️ L'EMPREINTE DE L'ÉTAT DE DÉPART, CALCULÉE JUSTE APRÈS LE CHARGEMENT ET
                # PUBLIÉE PAR (bras, carte). C'est l'artefact qui rend la promesse ci-dessus
                # AUDITABLE : les deux cartes d'un même cerveau doivent porter la MÊME empreinte,
                # et une divergence se LIT dans le rapport au lieu d'exiger une sonde externe.
                # Elle est prise AVANT `evaluer_cerveau_sur_carte` : elle décrit l'état depuis
                # lequel la mesure PART, pas celui qu'elle laisse derrière elle.
                # ⚠️ ELLE DOIT RESTER ICI, DANS LA BOUCLE DES CARTES, ET PAS SEULEMENT PARCE QU'ELLE
                # Y TROUVE SON SENS : hissée à côté du chargement, elle publierait DEUX FOIS la
                # même empreinte alors que l'état serait partagé — l'artefact CERTIFIERAIT une
                # fraîcheur qu'il n'aurait pas vérifiée (mesuré : la variante « squelette du plan »
                # laisse le verrou d'empreinte VERT). La propriété qui garde réellement ce banc est
                # l'INDÉPENDANCE À L'ORDRE, tenue par le test `TestIndependanceALOrdre`.
                empreinte_etat = _empreinte_etat(etat)
                try:
                    resultat = evaluer_cerveau_sur_carte(etat, index_carte, graines_eval,
                                                         max_ticks)
                finally:
                    # `_forcer_carte` a ouvert un monde : on le referme même si la mesure est
                    # refusée (`InstrumentIndisponible`), sinon l'évaluation suivante hériterait
                    # d'un environnement resté ouvert.
                    etat.env.close()
                par_carte[resultat["nom_classe"]] = resultat
                empreintes_etat_initial[resultat["nom_classe"]] = empreinte_etat
                print(f"   ✅ {cle:22s} {resultat['nom_classe']:32s} "
                      f"{resultat['taux']['taux'] * 100:5.1f}% "
                      f"({resultat['gagnes']}/{resultat['taux']['n']}), "
                      f"tronqués {resultat['tronques']}")
            par_cerveau[cle] = {"chemin": chemin, "cartes": par_carte,
                                "empreinte_etat_initial": empreintes_etat_initial,
                                "duree_s": time.time() - t0}
            # Vue plate pour le test apparié MES-01 (une valeur scalaire par métrique).
            premiere = par_carte[PROGRAMME[cartes[0]][1]]
            metriques_par_chemin[chemin] = {
                "taux_franchissement": premiere["taux"]["taux"],
                "retour_moyen": premiere["retour_moyen"],
                # None (jamais NaN, qui empoisonnerait le t, ni 0.0, qui serait un mensonge)
                "longueur_normalisee": premiere["longueur_mediane"],
                "jours_final": 0,  # le banc n'a pas de notion de jours
            }

    dp = construire_depouillement(cohorte, bras, graines, metriques_par_chemin)
    print("\n" + dp.rapport())

    comparaisons, ignorees = [], []
    for i, bras_a in enumerate(bras):
        for bras_b in list(bras)[i + 1:]:
            for metrique in FAMILLE_METRIQUES:
                manquants = [f"{b}_g{g}" for b in (bras_a, bras_b)
                             for g in dp.manifeste.graines
                             if dp.runs.get(f"{b}_g{g}", {}).get(metrique) is None]
                if manquants:
                    # Une métrique absente n'est PAS zéro : on refuse de la tester et on
                    # DIT pourquoi, plutôt que de moyenner un NaN ou un faux 0,0.
                    ignorees.append(
                        f"{metrique} — {bras_a} vs {bras_b} : indisponible pour "
                        f"{len(manquants)} cerveau(x) ({', '.join(manquants[:5])}"
                        + ("…" if len(manquants) > 5 else "") + ")")
                    continue
                comparaisons.append(dp.apparie(bras_a, bras_b, metrique,
                                               f"{metrique} — {bras_a} vs {bras_b}"))
    print("\n=== TESTS APPARIÉS (famille de "
          f"{len(FAMILLE_METRIQUES)} métriques, seuil Bonferroni) ===")
    for resultat in comparaisons:
        print("  " + resultat.ligne())
    if ignorees:
        print(f"\n⚠️  {len(ignorees)} comparaison(s) IGNORÉE(S) — métrique absente, jamais zéro :")
        for motif in ignorees:
            print("   - " + motif)

    rapport = {
        "campagne": os.path.basename(os.path.normpath(cohorte)),
        "date_evaluation": datetime.now(timezone.utc).isoformat(),
        "protocole": "PROTOCOLE_BANC_FINAL v1",
        "cartes": cartes,
        "episodes_par_carte": int(episodes),
        "graine_eval_base": int(graine_eval_base),
        "graines_entrainement": [int(g) for g in graines],
        "bras": list(bras),
        "cerveaux": par_cerveau,
        "couverture": {"obtenus": len(dp.runs), "attendus": len(bras) * len(graines)},
        "exclusions": dp.exclusions,
        "violations": dp.violations,
        "seuil_bonferroni": (comparaisons[0].seuil if comparaisons else None),
        "comparaisons_ignorees": ignorees,
        "comparaisons": [
            {"label": r.label, "delta": r.delta, "t": r.t, "n": r.n,
             "favorables": r.favorables, "seuil": r.seuil,
             "significatif": r.significatif} for r in comparaisons],
    }
    if dp.violations:
        # ⚠️ AUCUN AGRÉGAT N'EST PUBLIÉ SUR UNE CAMPAGNE INVALIDE — critère de succès de la
        # tâche, et doctrine de `Depouillement.publier` (MES-01 : « à la moindre violation :
        # aucun agrégat écrit et code de sortie non nul »). Le garde est nécessaire ICI, et pas
        # seulement dans `apparie` : quand un cerveau manque, TOUTES les métriques des paires
        # concernées sont absentes, donc aucune comparaison n'est tentée, donc rien ne lève —
        # et le fichier s'écrirait sans une erreur. Il serait pourtant parfaitement lisible :
        # `couverture` inférieure à `attendus`, `comparaisons` vide — un lecteur pressé y
        # verrait un résultat. `main()` sort en 1, et le rapport ci-dessus nomme les exclusions.
        print(f"\n⛔ Agrégat NON publié : campagne INVALIDE ({len(dp.violations)} violation(s), "
              f"voir le rapport ci-dessus) — règle MES-01. Rien n'a été écrit dans "
              f"{dossier_sortie}.")
        return rapport
    os.makedirs(dossier_sortie, exist_ok=True)
    horodatage = datetime.now().strftime("%Y%m%d_%H%M%S")
    chemin = os.path.join(dossier_sortie, f"banc_final_{horodatage}.json")
    with open(chemin, "w", encoding="utf-8") as f:
        json.dump(rapport, f, ensure_ascii=False, indent=2)
    print(f"\n💾 Agrégat écrit dans {chemin} (aucun .brain n'a été modifié).")
    return rapport


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Le banc final standardisé (EVA-01) — cartes figées, graines d'éval dédiées")
    parser.add_argument("--cohorte", type=str, required=True,
                        help="Dossier de campagne (contient manifeste.json et un dossier par bras)")
    parser.add_argument("--bras", type=str, nargs="+", required=True,
                        help="Noms des bras à comparer (ex. K8_NU K16_NU)")
    parser.add_argument("--cohorte-explicite", type=str, default=None,
                        help="JSON {bras: {graine: chemin}} enumerant les cerveaux UN PAR UN. "
                             "Contourne volontairement le glob, qui refuse un bras portant des "
                             "surnumeraires (K8_NU en a 2). Chaque chemin doit exister.")
    parser.add_argument("--cartes", type=int, nargs="+", default=list(CARTES_GELEES),
                        help=f"Indices PROGRAMME (défaut gelé : {list(CARTES_GELEES)})")
    parser.add_argument("--episodes", type=int, default=None,
                        help="Nombre d'épisodes par carte. OBLIGATOIRE : vient du pilote (§8bis)")
    parser.add_argument("--graine-eval-base", type=int, default=GRAINE_EVAL_BASE_GELEE,
                        help=f"Première graine d'évaluation (défaut {GRAINE_EVAL_BASE_GELEE})")
    parser.add_argument("--max-ticks", type=int, default=0,
                        help="0 = budget natif du monde (max_steps). Jamais un plafond posé.")
    parser.add_argument("--dossier-sortie", type=str, default=DOSSIER_SORTIE_DEFAUT)
    args = parser.parse_args()

    verifier_graine_eval_base(args.graine_eval_base)
    exiger_episodes(args.episodes)
    graines = lire_graines_du_manifeste(args.cohorte)
    if args.cohorte_explicite:
        cohorte = lire_cohorte_explicite(args.cohorte_explicite)
    else:
        cohorte = resoudre_cohorte(args.cohorte, args.bras, graines)
    # APRÈS les deux branches : la voie explicite ne passe pas par `resoudre_cohorte`.
    cohorte = refuser_bras_vides(cohorte)
    print(f"📋 {len(args.bras)} bras × {len(graines)} graines d'entraînement, "
          f"cartes {args.cartes}, {args.episodes} épisodes "
          f"(graines d'éval {args.graine_eval_base}…"
          f"{args.graine_eval_base + args.episodes - 1}).")
    print(f"   cerveaux résolus : "
          f"{ {b: len(v) for b, v in cohorte.items()} }")
    # Cohérence --bras / inventaire (Minor différé de la tâche 3) : un bras déclaré dans --bras
    # mais ABSENT de l'inventaire n'est pas dans le dict résolu, donc `refuser_bras_vides` ne peut
    # pas le voir — `--bras K8_NU K2_NU` avec un inventaire sans K2_NU sortait en 0 en affichant
    # `{'K8_NU': 1}`. Même classe de défaut que I-3 : succès silencieux.
    absents = sorted(set(args.bras) - set(cohorte))
    if absents:
        raise BrasIntrouvable(
            f"bras déclarés dans --bras mais ABSENTS de l'inventaire : {', '.join(absents)}")
    rapport = executer_banc(
        cohorte=args.cohorte, bras=args.bras, cartes=args.cartes, graines=graines,
        episodes=args.episodes, graine_eval_base=args.graine_eval_base,
        dossier_sortie=args.dossier_sortie, max_ticks=args.max_ticks,
        cohorte_resolue=cohorte)  # la voie explicite doit SURVIVRE jusqu'ici
    return 0 if not rapport["violations"] else 1


if __name__ == "__main__":
    sys.exit(main())
