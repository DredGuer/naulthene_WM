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
import sys
from typing import Sequence

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
    if not graines:
        raise ValueError(f"{chemin} ne déclare aucune graine")
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


def resoudre_cohorte(cohorte: str, bras: Sequence[str],
                     graines: Sequence[int]) -> dict[str, dict[int, str]]:
    """Rend `{bras: {graine: chemin}}`. L'absence d'un cerveau n'est PAS traitée ici :
    c'est `Depouillement.collecter` qui refuse une cohorte incomplète (MES-01)."""
    return {b: lister_cerveaux(os.path.join(cohorte, b), b, graines) for b in bras}


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
    print(f"📋 {len(args.bras)} bras × {len(graines)} graines d'entraînement, "
          f"cartes {args.cartes}, {args.episodes} épisodes "
          f"(graines d'éval {args.graine_eval_base}…"
          f"{args.graine_eval_base + args.episodes - 1}).")
    print(f"   cerveaux résolus : "
          f"{ {b: len(v) for b, v in cohorte.items()} }")
    return 0


if __name__ == "__main__":
    sys.exit(main())
