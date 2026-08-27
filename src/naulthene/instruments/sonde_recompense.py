# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Adrien Nault — Naulthène AGI
"""LA SONDE DE RÉCOMPENSE — qui tire la récompense vers le bas ? (v33.1, expérimental)

Instrument de DIAGNOSTIC en lecture seule. Décompose, terme par terme, la récompense
réellement reçue à chaque tick.

    Un agent optimise ce qu'on lui donne. Si la somme est négative, il apprend à ne rien
    faire — et il a raison.

Motivation (sonde de gradient, 2026-08-05) : le gradient atteint bien `tete_motrice`
(0,05 → 0,16), donc l'apprentissage a démarré. Mais la récompense du jour est
**NÉGATIVE** (Σr = −9,12 / −6,92 / −6,68 sur 3 jours, 400 ticks sur 400 en reçoivent une).

L'agent n'a pas échoué à apprendre : il a **correctement appris** que bouger coûte et que
rien ne rapporte. Le profil mesuré par le banc d'ablation le confirme — `forward` joué
5,5 % du temps, 53,8 % d'actions stériles, 96 % de ticks sur place. C'est la politique
optimale d'un agent qui ne peut que perdre.

Reste à savoir **quel terme domine ce déficit**. `recompense_interne` est la somme de
dix contributions (voir `traiter_tick`) ; sans les séparer, toute correction serait un
réglage à l'aveugle — et remplacer un chiffre arbitraire par un autre chiffre arbitraire
ne vaut pas mieux (doctrine v30.1 : instrumenter d'abord, calibrer ensuite).

---
CE QUE LA SONDE MESURE

Pour chacun des dix termes : la somme sur le jour, la moyenne par tick, le nombre de ticks
où il est non nul, et son signe dominant. Plus la part de chaque terme dans le total
POSITIF et dans le total NÉGATIF — c'est ce rapport qui dit si le déséquilibre vient d'un
coût trop lourd ou d'un gain absent.

Aucune écriture : le cerveau est chargé depuis une COPIE, jamais sauvegardé.

---
LANCEMENT

    PYTHONPATH=src python -m naulthene.instruments.sonde_recompense \\
        --brain brains/ablations/REFERENCE_5000j.brain --jours 2 --niveau 0

    # Comparer un niveau peuplé de ressources et un niveau nu
    PYTHONPATH=src python -m naulthene.instruments.sonde_recompense \\
        --brain brains/ablations/REFERENCE_5000j.brain --jours 2 --niveau 4
"""

import argparse
import os
import shutil
from collections import defaultdict

import numpy as np
import torch

import naulthene.cerveau.noyau as nx
from naulthene.cerveau.persistance import PersistanceAnatomique


# Les dix contributions de `recompense_interne`, dans l'ordre du code (`traiter_tick`).
# Le libellé dit ce que le terme RÉCOMPENSE, pas seulement son nom de variable.
TERMES = [
    ("recompense_env",           "victoire de l'environnement"),
    ("dopamine_curiosite",       "curiosité (erreur JEPA × dopamine)"),
    ("micro_recompense",         "micro-récompense (jalon DoorKey)"),
    ("micro_recompense_porte",   "franchissement de porte"),
    ("micro_recompense_progres",  "record de proximité au But"),
    ("penalite_stagnation",      "pénalité de stagnation"),
    ("sous_objectif_intrinseque", "sous-objectif intrinsèque"),
    ("r_bio",                    "métabolisme (faim/soif/stimulation)"),
    ("micro_recompense_vocale",  "production vocale"),
    ("cout_requete_c3",          "coût d'une requête C3 (soustrait)"),
    ("recompense_continue",      "guidage vers le But (hors Mode Libre)"),
    ("MALUS_DOULEUR",            "choc contre un mur"),
]


def instrumenter(journal):
    """Enveloppe `traiter_tick` pour capturer les variables locales du tick.

    On ne modifie PAS `noyau.py`. On installe un `sys.settrace` limité à la seule
    fonction `traiter_tick` : au moment où elle rend la main, ses variables locales sont
    encore accessibles et contiennent tous les termes de la somme. C'est plus intrusif
    qu'un simple wrapper, mais c'est la seule façon de lire une décomposition qui n'est
    jamais retournée ni stockée.

    ⚠️ Le traçage ralentit fortement l'exécution (~×3). Acceptable pour 2-3 jours de
    diagnostic, jamais pour un run.
    """
    import sys

    def tracer(frame, evenement, arg):
        if evenement != "call":
            return None
        if frame.f_code.co_name != "traiter_tick":
            return None

        def au_retour(frame, evenement, arg):
            if evenement != "return":
                return
            loc = frame.f_locals
            ligne = {}
            for nom, _ in TERMES:
                if nom == "MALUS_DOULEUR":
                    ligne[nom] = (nx.MALUS_DOULEUR if loc.get("mur_touche") else 0.0)
                elif nom == "recompense_continue":
                    # N'entre dans la somme QUE hors Mode Libre.
                    v = loc.get("recompense_continue", 0.0)
                    etat = loc.get("etat")
                    actif = etat is not None and not getattr(etat, "mode_libre", False)
                    ligne[nom] = float(v) if actif else 0.0
                else:
                    v = loc.get(nom, 0.0)
                    ligne[nom] = float(v) if v is not None else 0.0
            ligne["_total"] = float(loc.get("recompense_interne", 0.0))
            ligne["_mur"] = bool(loc.get("mur_touche", False))
            ligne["_action"] = loc.get("action_item", -1)
            journal.append(ligne)

        return au_retour

    sys.settrace(tracer)
    return sys.settrace


def afficher(journal, nom_cerveau, niveau, jours):
    print("\n" + "=" * 100)
    print(f"  SONDE DE RÉCOMPENSE — {os.path.basename(nom_cerveau)} — {niveau}")
    print(f"  {len(journal)} ticks sur {jours} jour(s)")
    print("=" * 100)

    total = sum(l["_total"] for l in journal)
    n = max(1, len(journal))
    print(f"\n  RÉCOMPENSE TOTALE : {total:+.4f}   (moyenne par tick : {total/n:+.6f})")
    if total < 0:
        print("  ⚠️  NÉGATIVE — l'agent ne peut que perdre en agissant.")

    print(f"\n  {'terme':<28} {'somme':>11} {'moy/tick':>11} {'ticks≠0':>9} "
          f"{'%ticks':>7}  {'rôle'}")
    print("  " + "-" * 96)

    sommes = {}
    for nom, libelle in TERMES:
        vals = [l[nom] for l in journal]
        s = sum(vals)
        nz = sum(1 for v in vals if v != 0.0)
        sommes[nom] = s
        signe = "🔴 COÛT" if s < -1e-9 else ("🟢 gain" if s > 1e-9 else "—")
        print(f"  {nom:<28} {s:>11.4f} {s/n:>11.6f} {nz:>9} {100*nz/n:>6.1f}%  "
              f"{signe}  {libelle}")

    pos = sum(v for v in sommes.values() if v > 0)
    neg = sum(v for v in sommes.values() if v < 0)
    print("  " + "-" * 96)
    print(f"  {'TOTAL POSITIF':<28} {pos:>11.4f}")
    print(f"  {'TOTAL NÉGATIF':<28} {neg:>11.4f}")
    print(f"  {'SOLDE':<28} {pos+neg:>11.4f}")

    print("\n  RÉPARTITION DU DÉFICIT")
    print("  " + "-" * 96)
    for nom, libelle in sorted(TERMES, key=lambda t: sommes[t[0]]):
        s = sommes[nom]
        if s >= -1e-9:
            continue
        print(f"    {nom:<28} {100*s/neg:>6.1f} % du total négatif   ({libelle})")
    print()
    for nom, libelle in sorted(TERMES, key=lambda t: -sommes[t[0]]):
        s = sommes[nom]
        if s <= 1e-9:
            continue
        print(f"    {nom:<28} {100*s/pos:>6.1f} % du total positif   ({libelle})")

    # --- Verdict ---
    print("\n" + "=" * 100)
    pire = min(TERMES, key=lambda t: sommes[t[0]])
    meilleur = max(TERMES, key=lambda t: sommes[t[0]])
    print(f"  Terme le plus COÛTEUX : {pire[0]} ({sommes[pire[0]]:+.4f}) — {pire[1]}")
    print(f"  Terme le plus PAYANT  : {meilleur[0]} ({sommes[meilleur[0]]:+.4f}) — {meilleur[1]}")
    print()
    if total < 0 and abs(neg) > 3 * pos:
        print("  🔴 DÉSÉQUILIBRE MAJEUR : les coûts dépassent les gains d'un facteur > 3.")
        print("     L'immobilité est mathématiquement la meilleure stratégie disponible.")
        print("     → C'est un problème d'ÉQUILIBRAGE, pas d'architecture.")
    elif total < 0:
        print("  🟠 DÉFICIT MODÉRÉ : la somme penche du mauvais côté, mais pas massivement.")
    else:
        print("  🟢 SOLDE POSITIF sur ce niveau — chercher le déficit ailleurs.")
    print("=" * 100)


def main():
    p = argparse.ArgumentParser(description="Sonde de récompense — décomposition terme à terme")
    p.add_argument("--brain", required=True)
    p.add_argument("--jours", type=int, default=2)
    p.add_argument("--niveau", type=int, default=None)
    p.add_argument("--graine", type=int, default=1789)
    args = p.parse_args()

    if not os.path.exists(args.brain):
        raise SystemExit(f"❌ Cerveau introuvable : {args.brain}")

    dossier = os.path.join(os.path.dirname(args.brain) or ".", "_sonde_r")
    os.makedirs(dossier, exist_ok=True)
    copie = os.path.join(dossier, "sonde.brain")
    shutil.copy2(args.brain, copie)

    torch.manual_seed(args.graine)
    np.random.seed(args.graine)

    etat = PersistanceAnatomique(copie).charger_ou_naitre()
    if args.niveau is not None:
        env_id, nom = nx.PROGRAMME[args.niveau]
        etat.env.close()
        etat.env = nx.creer_env(env_id, nx.DIM_VISUELLE)
        etat.env_id, etat.nom_classe = env_id, nom

    journal = []
    print(f"\n🔬 SONDE DE RÉCOMPENSE — {args.jours} jour(s) sur {etat.nom_classe}")
    print("   (traçage actif : l'exécution est ~3× plus lente que la normale)")

    settrace = instrumenter(journal)
    try:
        for j in range(args.jours):
            nx.demarrer_journee(etat)
            for _ in range(nx.ticks_par_jour):
                nx.traiter_tick(etat)
            nx.executer_nuit(etat)
    finally:
        settrace(None)

    etat.env.close()
    if not journal:
        raise SystemExit("❌ Aucun tick capturé — le traçage n'a rien intercepté.")
    afficher(journal, args.brain, etat.nom_classe, args.jours)

    try:
        shutil.rmtree(dossier)
    except OSError:
        pass


if __name__ == "__main__":
    main()
