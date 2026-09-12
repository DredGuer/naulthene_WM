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
import json
import os
import re
import statistics
import sys
import time
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
    """
    return float(etat.mix_somme.get("Env", 0.0))


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
    faut pouvoir AUDITER le monde qui l'a produite. Chaque entrée d'`episodes` porte donc
    `env_id` (la carte réellement jouée), `budget` (les ticks réellement reçus) et `monde`
    (empreinte du tirage : graine consommée, but, départ, ressources semées). Sans cela, un
    épisode joué sur une AUTRE carte ou dans un AUTRE monde restait invisible dans le
    résultat — mesuré : les trois leviers de graine retirés, les mondes différaient pendant
    que le rapport, lui, restait identique. Le `budget` de tête est celui de la carte
    imposée ; les `budget` par épisode doivent lui être égaux (re-forçage oblige), et une
    divergence se lit désormais au lieu d'être tue.
    """
    if not 0 <= index_carte < len(PROGRAMME):
        raise CarteInvalide(f"index de carte {index_carte} hors PROGRAMME (0…{len(PROGRAMME) - 1})")

    env_id, nom_classe = _forcer_carte(etat, index_carte)

    budget = int(max_ticks) if max_ticks > 0 else _budget_natif_carte(etat.env)
    episodes = []
    for graine in graines:
        graine = int(graine)
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
        with torch.no_grad():
            for _tick in range(budget_episode):
                ticks_avant = etat.ticks_episode_courant
                traiter_tick(etat)
                # `traiter_tick` enchaîne LUI-MÊME sur un nouvel épisode dès que
                # `fin_episode` bascule : on lit la victoire au tick MÊME de la bascule.
                if etat.fin_episode:
                    gagne = bool(etat.victoire_aujourdhui)
                    ticks = ticks_avant + 1
                    tronque = False
                    recompense = _recompense_env_cumulee(etat) - recompense_avant
                    break
            if tronque:
                # Un épisode tronqué n'a pas de victoire, mais sa récompense partielle
                # reste une information MESURÉE : on la calcule, on ne la laisse pas à 0,0.
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
    return 0


if __name__ == "__main__":
    sys.exit(main())
