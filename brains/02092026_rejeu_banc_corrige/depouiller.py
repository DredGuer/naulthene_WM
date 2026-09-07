#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Adrien Nault — Naulthène AGI
"""Dépouillement STRICT du rejeu à instrument corrigé (02/09/2026).

Écrit AVANT que les 20 fichiers soient là (Règle de Trace §4) : les vérifications
sont fixées d'avance, et non choisies en regardant les chiffres.

    venv/bin/python brains/02092026_rejeu_banc_corrige/depouiller.py

⚠️ Réécrit le 08/09/2026 au titre de **MES-01**. Trois changements de fond :
  1. la cohorte des 20 cerveaux est DÉCLARÉE au manifeste et exigée en entier —
     le script d'origine partait d'un `glob("banc_*.json")`, donc sa couverture
     était définie par ce qui traînait sur le disque ;
  2. les deux vérifications pré-enregistrées (témoin aléatoire invariant à 5,67 % ;
     aucun cerveau au plafond de budget 27,0×) étaient CALCULÉES ET IGNORÉES —
     elles bloquent désormais la publication ;
  3. le seuil n'est plus la constante 2,88 : il est dérivé de `n` et de la famille
     de 3 métriques, avec `df = n − 2` pour une corrélation.

Produit `agregat.json` dans le même dossier — et ne le produit PAS si une
vérification échoue. Code de sortie **≠ 0** dans ce cas.
"""
import json
import math
import os
import sys

RACINE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(RACINE)), "src"))

from naulthene.instruments.depouillement import Depouillement, Manifeste, seuil_t  # noqa: E402

ANCIEN = os.path.join(os.path.dirname(RACINE), "30082026_plancher_n20", "agregat.json")

# Plafond arithmétique de la carte : budget 324 ticks / plus court chemin médian 12 pas.
PLAFOND_DIRECTIVITE = 27.0
TEMOIN_ALEATOIRE_ATTENDU = 5.67   # 17/300, invariant : ne passe pas par le code corrigé


def corr(paires, comparaisons, alpha):
    """Pearson + `t` de Student, avec le seuil DÉRIVÉ (df = n − 2)."""
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
    r = max(-0.999999, min(0.999999, sxy / math.sqrt(sxx * syy)))
    t = r * math.sqrt((n - 2) / (1 - r * r))
    seuil = seuil_t(n - 1, comparaisons, alpha)  # df = n − 2
    return {"r": round(r, 4), "t": round(t, 2), "n": n,
            "seuil": round(seuil, 3), "significatif": abs(t) > seuil}


def lire_banc(chemin):
    with open(chemin, encoding="utf-8") as fh:
        d = json.load(fh)
    r = d["resultats"]["entraîné (eval)"]
    return {
        "nom": d["cerveau"], "dim_bus": d.get("dim_bus"), "jour": d.get("jour"),
        "maitrise_run": d.get("maitrise_run"),
        "succes_rejeu": round(r["taux"] * 100, 2),
        "directivite_rejeu": r["directivite_mediane"],
        "n_victoires": r["n_victoires"],
        "entropie_jouee": r.get("entropie_jouee"),
        "temoin_aleatoire": round(
            d["resultats"]["aléatoire (7 actions)"]["taux"] * 100, 2),
    }


manifeste = Manifeste.depuis_fichier(os.path.join(RACINE, "manifeste.json"))
depouillement = Depouillement(manifeste, racine=RACINE)
depouillement.collecter(lire_banc)

with open(ANCIEN, encoding="utf-8") as fh:
    ancien = {p["nom"]: p for p in json.load(fh)["points"]}
for cle, point in depouillement.runs.items():
    o = ancien.get(point["nom"], {})
    point["succes_3008"] = o.get("banc")
    point["directivite_3008"] = o.get("directivite")

# --- Les deux vérifications pré-enregistrées, désormais BLOQUANTES ---------------
aleatoires = sorted({p["temoin_aleatoire"] for p in depouillement.runs.values()})
depouillement.exiger(
    aleatoires == [TEMOIN_ALEATOIRE_ATTENDU],
    f"témoin aléatoire non invariant : {aleatoires} (attendu [{TEMOIN_ALEATOIRE_ATTENDU}])")
au_plafond = [p["nom"] for p in depouillement.runs.values()
              if p["directivite_rejeu"] and p["directivite_rejeu"] >= PLAFOND_DIRECTIVITE]
depouillement.exiger(
    not au_plafond,
    f"directivité censurée par le budget ({PLAFOND_DIRECTIVITE}×) : {au_plafond}")

print(depouillement.rapport())
if not depouillement.valide():
    print("\n⛔ Aucun agrégat écrit, aucune corrélation prononcée.")
    sys.exit(depouillement.code_sortie())

points = sorted(depouillement.runs.values(), key=lambda p: -p["succes_rejeu"])
k, alpha = manifeste.comparaisons_prevues, manifeste.alpha
avec_vic = [p for p in points if p["n_victoires"] >= 1 and p["directivite_rejeu"]]
apparies = [p for p in points if p["succes_3008"] is not None]
ap_dir = [p for p in apparies if p["directivite_3008"] and p["directivite_rejeu"]]

correlations = {
    "directivite_vs_succes": corr(
        [(p["directivite_rejeu"], p["succes_rejeu"]) for p in avec_vic], k, alpha),
    "maitrise_vs_succes": corr(
        [(p["maitrise_run"], p["succes_rejeu"]) for p in points
         if p["maitrise_run"] is not None], k, alpha),
    "dim_bus_vs_succes": corr(
        [(p["dim_bus"], p["succes_rejeu"]) for p in points if p["dim_bus"]], k, alpha),
}
# Robustesse : la corrélation survit-elle au retrait des 4 extrêmes de directivité ?
tries = sorted(avec_vic, key=lambda p: p["directivite_rejeu"])
if len(tries) >= 7:
    correlations["directivite_vs_succes_sans_4_extremes"] = corr(
        [(p["directivite_rejeu"], p["succes_rejeu"]) for p in tries[2:-2]], k, alpha)

print(f"\nREJEU À INSTRUMENT CORRIGÉ — n = {len(points)}/{manifeste.runs_attendus}\n")
print(f"{'cerveau':<9}{'succ_3008':>10}{'succ_rejeu':>11}{'δ':>8}"
      f"{'dir_3008':>10}{'dir_rejeu':>10}{'δ':>8}{'n_vic':>7}{'H_jouée':>9}")
for p in points:
    f = lambda v, w=9: f"{v:>{w}.2f}" if isinstance(v, (int, float)) else f"{'-':>{w}}"  # noqa: E731
    ds = (p["succes_rejeu"] - p["succes_3008"]) if p["succes_3008"] is not None else None
    dd = (p["directivite_rejeu"] - p["directivite_3008"]
          if p["directivite_3008"] and p["directivite_rejeu"] else None)
    print(f"{p['nom']:<9}{f(p['succes_3008'], 10)}{f(p['succes_rejeu'], 11)}{f(ds, 8)}"
          f"{f(p['directivite_3008'], 10)}{f(p['directivite_rejeu'], 10)}{f(dd, 8)}"
          f"{p['n_victoires']:>7}{f(p['entropie_jouee'], 9)}")

print("\n=== CORRÉLATIONS (seuil dérivé, Bonferroni 3 métriques, df = n − 2) ===")
for nom, v in correlations.items():
    print(f"  r({nom}) = {v}")
print(f"  [30/08, mêmes cerveaux] {corr([(p['directivite_3008'], p['succes_3008']) for p in apparies if p['directivite_3008']], k, alpha)}")

print("\n=== DELTAS APPARIÉS (rejeu − 30/08) ===")
print("  ⚠️ paires DÉCLARÉES : un cerveau absent de l'agrégat du 30/08 n'a pas de "
      "contrepartie — le n est affiché.")
print(f"  succès      : {len(apparies)}/{len(points)} paires")
print(depouillement.resultat_de(
    [p["succes_rejeu"] - p["succes_3008"] for p in apparies], "δ succès").ligne())
print(f"  directivité : {len(ap_dir)}/{len(points)} paires")
print(depouillement.resultat_de(
    [p["directivite_rejeu"] - p["directivite_3008"] for p in ap_dir],
    "δ directivité").ligne())

print("\n=== VÉRIFICATIONS PRÉ-ENREGISTRÉES (bloquantes) ===")
print(f"  témoin aléatoire      : {aleatoires} — attendu [{TEMOIN_ALEATOIRE_ATTENDU}]  ✅")
print(f"  saturation du budget  : pire {max(p['directivite_rejeu'] for p in avec_vic):.2f}× "
      f"< plafond {PLAFOND_DIRECTIVITE}×  ✅")
print(f"  cerveaux sans victoire: {[p['nom'] for p in points if p['n_victoires'] == 0] or 'aucun'}")
print(f"  directivité définie   : {len(avec_vic)}/{len(points)}")

if depouillement.publier(os.path.join(RACINE, "agregat.json")):
    print(f"\nagregat.json écrit ({len(points)} runs)")
sys.exit(depouillement.code_sortie())
