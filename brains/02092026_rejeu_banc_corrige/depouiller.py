#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Adrien Nault — Naulthène AGI
"""Dépouillement du rejeu à instrument corrigé (02/09/2026).

Écrit AVANT que les 20 fichiers soient là (Règle de Trace §4) : les vérifications sont
donc fixées d'avance, et non choisies en regardant les chiffres.

    python3 brains/02092026_rejeu_banc_corrige/depouiller.py

Produit `agregat.json` dans le même dossier et un tableau markdown sur stdout.
"""
import glob
import json
import math
import os

RACINE = os.path.dirname(os.path.abspath(__file__))
ANCIEN = os.path.join(os.path.dirname(RACINE), "30082026_plancher_n20", "agregat.json")

# Plafond arithmétique de la carte : budget 324 ticks / plus court chemin médian 12 pas.
PLAFOND_DIRECTIVITE = 27.0
TEMOIN_ALEATOIRE_ATTENDU = 5.67   # 17/300, invariant : ne passe pas par le code corrigé


def corr(paires):
    """Pearson + t de Student. Retourne None si moins de 3 points."""
    n = len(paires)
    if n < 3:
        return None
    mx = sum(x for x, _ in paires) / n
    my = sum(y for _, y in paires) / n
    sxy = sum((x - mx) * (y - my) for x, y in paires)
    sxx = sum((x - mx) ** 2 for x, _ in paires)
    syy = sum((y - my) ** 2 for _, y in paires)
    if sxx <= 0 or syy <= 0:
        return None
    r = sxy / math.sqrt(sxx * syy)
    r = max(-0.999999, min(0.999999, r))
    return {"r": round(r, 4), "t": round(r * math.sqrt((n - 2) / (1 - r * r)), 2), "n": n}


def t_apparie(deltas):
    n = len(deltas)
    if n < 2:
        return None
    m = sum(deltas) / n
    sd = math.sqrt(sum((d - m) ** 2 for d in deltas) / (n - 1))
    if sd <= 0:
        return {"moy": round(m, 4), "t": None, "n": n, "favorables": sum(d > 0 for d in deltas)}
    return {"moy": round(m, 4), "t": round(m / (sd / math.sqrt(n)), 2), "n": n,
            "favorables": sum(d > 0 for d in deltas)}


def main():
    ancien = {p["nom"]: p for p in json.load(open(ANCIEN, encoding="utf-8"))["points"]}
    points, aleatoires = [], set()
    for f in sorted(glob.glob(os.path.join(RACINE, "banc_*.json"))):
        d = json.load(open(f, encoding="utf-8"))
        r = d["resultats"]["entraîné (eval)"]
        o = ancien.get(d["cerveau"], {})
        aleatoires.add(round(d["resultats"]["aléatoire (7 actions)"]["taux"] * 100, 2))
        points.append({
            "nom": d["cerveau"], "dim_bus": d.get("dim_bus"), "jour": d.get("jour"),
            "maitrise_run": d.get("maitrise_run"),
            "succes_3008": o.get("banc"), "succes_rejeu": round(r["taux"] * 100, 2),
            "directivite_3008": o.get("directivite"),
            "directivite_rejeu": r["directivite_mediane"],
            "n_victoires": r["n_victoires"],
            "entropie_jouee": r.get("entropie_jouee"),
        })
    points.sort(key=lambda p: -p["succes_rejeu"])

    avec_vic = [p for p in points if p["n_victoires"] >= 1 and p["directivite_rejeu"]]
    apparies = [p for p in points if p["succes_3008"] is not None]
    ap_dir = [p for p in apparies if p["directivite_3008"] and p["directivite_rejeu"]]

    res = {
        "date": "2026-09-02",
        "question": "r(directivité, succès) survit-il à la correction d'instrument du 01/09 ?",
        "n": len(points),
        "protocole": "identique au 30/08 à l'unique exception de l'index de la mémoire de "
                     "travail (penser()[4]) ; worktree figé à 2d69b40 (v41.47), "
                     "DIM_VECTEUR_BIO=42, aucune greffe ; --force non passé (défaut du banc "
                     "à l'époque du rejeu : 0.5 figée)",
        "seuil_bonferroni_3_metriques_df18": 2.88,
        "points": points,
        "correlations_rejeu": {
            "directivite_vs_succes": corr([(p["directivite_rejeu"], p["succes_rejeu"]) for p in avec_vic]),
            "maitrise_vs_succes": corr([(p["maitrise_run"], p["succes_rejeu"])
                                        for p in points if p["maitrise_run"] is not None]),
            "dim_bus_vs_succes": corr([(p["dim_bus"], p["succes_rejeu"])
                                       for p in points if p["dim_bus"]]),
        },
        "correlation_3008_memes_cerveaux": corr(
            [(p["directivite_3008"], p["succes_3008"]) for p in apparies if p["directivite_3008"]]),
        "delta_apparie": {
            "succes": t_apparie([p["succes_rejeu"] - p["succes_3008"] for p in apparies]),
            "directivite": t_apparie([p["directivite_rejeu"] - p["directivite_3008"] for p in ap_dir]),
        },
        "verifications": {
            "temoin_aleatoire_valeurs": sorted(aleatoires),
            "temoin_aleatoire_conforme": aleatoires == {TEMOIN_ALEATOIRE_ATTENDU},
            "saturation_budget": {
                "plafond": PLAFOND_DIRECTIVITE,
                "pire": max((p["directivite_rejeu"] for p in avec_vic), default=None),
                "au_plafond": sum(1 for p in avec_vic
                                  if p["directivite_rejeu"] and p["directivite_rejeu"] >= PLAFOND_DIRECTIVITE),
            },
            "tautologie_cerveaux_sans_victoire": [p["nom"] for p in points if p["n_victoires"] == 0],
            "n_directivite_definie": len(avec_vic),
        },
    }

    # Robustesse : la corrélation survit-elle au retrait des 4 extrêmes de directivité ?
    tries = sorted(avec_vic, key=lambda p: p["directivite_rejeu"])
    if len(tries) >= 7:
        coeur = tries[2:-2]
        res["correlations_rejeu"]["directivite_vs_succes_sans_4_extremes"] = corr(
            [(p["directivite_rejeu"], p["succes_rejeu"]) for p in coeur])

    json.dump(res, open(os.path.join(RACINE, "agregat.json"), "w", encoding="utf-8"),
              indent=1, ensure_ascii=False)

    print(f"\nREJEU À INSTRUMENT CORRIGÉ — n = {res['n']}/20\n")
    print(f"{'cerveau':<9}{'succ_3008':>10}{'succ_rejeu':>11}{'δ':>8}"
          f"{'dir_3008':>10}{'dir_rejeu':>10}{'δ':>8}{'n_vic':>7}{'H_jouée':>9}")
    for p in points:
        f = lambda v, w=9: f"{v:>{w}.2f}" if isinstance(v, (int, float)) else f"{'-':>{w}}"
        ds = (p["succes_rejeu"] - p["succes_3008"]) if p["succes_3008"] is not None else None
        dd = (p["directivite_rejeu"] - p["directivite_3008"]
              if p["directivite_3008"] and p["directivite_rejeu"] else None)
        print(f"{p['nom']:<9}{f(p['succes_3008'],10)}{f(p['succes_rejeu'],11)}{f(ds,8)}"
              f"{f(p['directivite_3008'],10)}{f(p['directivite_rejeu'],10)}{f(dd,8)}"
              f"{p['n_victoires']:>7}{f(p['entropie_jouee'],9)}")
    print()
    for k, v in res["correlations_rejeu"].items():
        print(f"  r({k}) = {v}")
    print(f"  [30/08, mêmes cerveaux] {res['correlation_3008_memes_cerveaux']}")
    print(f"  δ apparié succès      : {res['delta_apparie']['succes']}")
    print(f"  δ apparié directivité : {res['delta_apparie']['directivite']}")
    print(f"  vérifications         : {res['verifications']}")
    print(f"\n  Seuil Bonferroni (3 métriques, df=18) : 2,88")
    print(f"  📄 {os.path.join(RACINE, 'agregat.json')}\n")


if __name__ == "__main__":
    main()
