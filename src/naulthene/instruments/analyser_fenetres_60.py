# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Adrien Nault — Naulthène AGI
"""Analyse les fenêtres glissantes du barème du cursus (protocole A, 07/09/2026).

Applique la règle de promotion de `noyau.py` à un vecteur binaire victoire/défaite
produit par `banc_ppo_fenetres.py` (ou par n'importe quelle source : le script ne
connaît que le JSON) :

- **voie maîtrise** : fenêtre glissante de `FENETRE` = 20 épisodes, victoire = `r > 0`,
  passage si ≥ `SEUIL` = 12 victoires sur 20 (60 %), après `MIN_EPISODES` = 10 épisodes ;
- **voie série** (l'autre branche du OU) : 2 victoires consécutives — mesurée aussi,
  parce que la promotion réelle est un OU : si la série de 2 passe souvent, la porte
  60 % n'est pas le seul chemin et « rester au niveau 4 » ne s'explique pas par elle.

Usage :
    PYTHONPATH=src python -m naulthene.instruments.analyser_fenetres_60 \
        resultat_g11.json resultat_g22.json ...
"""
import argparse, json, sys

import numpy as np

FENETRE = 20
SEUIL = 12          # 60 % de 20 — TAUX_PROMOTION de noyau.py
MIN_EPISODES = 10   # sous ce nombre d'épisodes, le taux n'est pas significatif


def analyser(wins):
    """Rend les statistiques du barème pour un vecteur binaire de victoires."""
    w = np.asarray(wins, dtype=int)
    n = len(w)
    if n == 0:
        return None
    taux = float(w.mean())
    # Fenêtres glissantes de FENETRE : w[i] compte les victoires des épisodes i..i+19.
    if n >= FENETRE:
        fenetres = np.convolve(w, np.ones(FENETRE, dtype=int), mode="valid")
        depassent = int((fenetres >= SEUIL).sum())
        n_fenetres = int(len(fenetres))
        prem_passage = int(np.argmax(fenetres >= SEUIL)) + 1 if depassent else None
        max_fenetre = int(fenetres.max())
    else:
        depassent = n_fenetres = prem_passage = 0
        max_fenetre = int(w.sum())
    # Route série : 2 victoires consécutives (l'autre branche du OU de promotion).
    doubles = int((w[:-1] & w[1:]).sum()) if n >= 2 else 0
    # Plus longue série de victoires.
    meilleure_serie = int(0)
    courante = 0
    for x in w:
        courante = courante + 1 if x else 0
        meilleure_serie = max(meilleure_serie, courante)
    return {
        "n_episodes": n,
        "taux_victoire": taux,
        "fenetres_20": n_fenetres,
        "max_victoires_sur_20": max_fenetre,
        "fenetres_ge_12": depassent,
        "fraction_fenetres_ge_12": depassent / n_fenetres if n_fenetres else None,
        "episode_premier_passage": prem_passage,
        "passages_2_consecutives": int(doubles),
        "meilleure_serie": meilleure_serie,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("fichiers", nargs="+", help="JSON de sortie de banc_ppo_fenetres")
    a = ap.parse_args()

    lignes = []
    for f in a.fichiers:
        try:
            data = json.load(open(f))
        except Exception as e:
            print(f"❌ {f} : {e}", file=sys.stderr)
            continue
        wins = data.get("victoires")
        if wins is None:
            print(f"❌ {f} : pas de clé 'victoires'", file=sys.stderr)
            continue
        s = analyser(wins)
        lignes.append((f, data, s))
        if s is None:
            print(f"⚠️ {f} : vecteur vide", file=sys.stderr)
            continue
        print(f"== {f}  (arch {data.get('arch')}, graine {data.get('graine')}, "
              f"{data.get('pas'):,} pas)")
        print(f"   épisodes : {s['n_episodes']} · taux victoire : {s['taux_victoire']*100:.1f} %")
        print(f"   fenêtres de {FENETRE} : {s['fenetres_20']} · "
              f"MAX victoires sur 20 : {s['max_victoires_sur_20']}/{FENETRE}")
        print(f"   fenêtres ≥ {SEUIL}/20 : {s['fenetres_ge_12']} "
              f"({s['fraction_fenetres_ge_12']*100:.1f} % des fenêtres)"
              + (f" · premier passage épisode {s['episode_premier_passage']}"
                 if s["prem_passage"] else ""))
        print(f"   route série (2 victoires consécutives) : {s['passages_2_consecutives']} "
              f"occurrence(s) · meilleure série : {s['meilleure_serie']}")

    # Verdict agrégé : combien de graines passent au moins une fois la porte 60 % ?
    if lignes:
        passes = [1 for _, _, s in lignes if s and s["fenetres_ge_12"] > 0]
        n = len([1 for _, _, s in lignes if s])
        print("\n" + "=" * 60)
        print(f"VERDICT — graines avec ≥ 1 fenêtre ≥ {SEUIL}/{FENETRE} : "
              f"{sum(passes)}/{n}")
        if sum(passes) == 0 and n:
            print(f"→ 0/{n} : à {n} graines, la porte 60 % × {FENETRE} n'est jamais passée "
                  f"→ mur barémique (candidat), à confronter à la route série ci-dessus.")
        else:
            print("→ la porte 60 % est passée au moins une fois : le seuil n'est pas "
                  "à lui seul le mur — le goulot est l'apprenant.")


if __name__ == "__main__":
    main()
