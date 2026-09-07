#!/usr/bin/env python3
"""Dépouillement STRICT de la campagne 05092026_detach_c2.

Protocole et juges : `LISEZ_MOI.md` — transcrits dans `manifeste.json`.
Bras : LIBRE (référence, réutilise 04092026_cursus_complet) vs LIBRE_DETACH (20 runs neufs).
Convention : `d = LIBRE_DETACH − LIBRE`. `d > 0` ⇒ couper le gradient de C2 AIDE,
donc ce gradient NUISAIT (juge 1 « positif » du LISEZ_MOI).

⚠️ Réécrit le 08/09/2026 au titre de **MES-01** : couverture, garde-fous et seuils
sont désormais portés par `naulthene.instruments.depouillement`, qui bloque la
publication sur campagne invalide et dérive le seuil de `n`.

Usage : `venv/bin/python brains/05092026_detach_c2/depouiller.py`
Code de sortie **≠ 0** si la campagne est invalide.
"""
import os
import statistics as st
import sys

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(D)), "src"))

from naulthene.instruments.depouillement import Depouillement, Manifeste  # noqa: E402
from naulthene.instruments.journal_cursus import lire_journal, resumer_journal  # noqa: E402

depouillement = Depouillement(
    Manifeste.depuis_fichier(os.path.join(D, "manifeste.json")), racine=D)
depouillement.collecter(lambda chemin: resumer_journal(lire_journal(chemin)))
depouillement.verifier_gardes()
print(depouillement.rapport())

if not depouillement.valide():
    print("\n⛔ Aucun agrégat écrit, aucun juge prononcé — voir les violations ci-dessus.")
    sys.exit(depouillement.code_sortie())

E = depouillement.runs
GRAINES = depouillement.manifeste.graines
BRAS = list(depouillement.manifeste.bras)


def juger(a, b, var, label):
    res = depouillement.apparie(a, b, var, label, retirer_extremes=4)
    print(res.ligne())
    if res.reduit:
        print(res.reduit.ligne())


print("\n=== JUGE 1 — MAÎTRISE (LIBRE_DETACH - LIBRE) ===")
juger("LIBRE_DETACH", "LIBRE", "mait", "maîtrise")

print("\n=== JUGE 2 — NIVEAU (attention : probablement SATURÉ) ===")
juger("LIBRE_DETACH", "LIBRE", "niv", "niveau")

print("\n=== JUGE 3 — AMPLITUDE C1 (la représentation change-t-elle ?) ===")
juger("LIBRE_DETACH", "LIBRE", "c1", "amplitude C1")

print("\n=== TEST DE TAUTOLOGIE (les deux bras ont gagné au moins une fois) ===")
print("  ⚠️ conditionnement DÉLIBÉRÉ, pas une exclusion : le n retenu est affiché.")
deltas = [E[f"LIBRE_DETACH_g{g}"]["mait"] - E[f"LIBRE_g{g}"]["mait"] for g in GRAINES
          if E[f"LIBRE_g{g}"]["vict"] > 0 and E[f"LIBRE_DETACH_g{g}"]["vict"] > 0]
print(depouillement.resultat_de(deltas, "maîtrise conditionnée").ligne())

print("\n=== COMPTAGES ===")
for b in BRAS:
    ks = [f"{b}_g{g}" for g in GRAINES]
    print(f"  {b:15} niv4: {sum(1 for k in ks if E[k]['niv'] >= 4):2}/{len(ks)} | "
          f"maîtrise 0%: {sum(1 for k in ks if E[k]['mait'] == 0):2} | "
          f"niveau 1: {sum(1 for k in ks if E[k]['niv'] <= 1):2} | "
          f"niv max {max(E[k]['niv'] for k in ks)}")

print("\n=== VÉRIF — le juge NIVEAU est-il SATURÉ ? ===")
for b in BRAS:
    ks = [f"{b}_g{g}" for g in GRAINES]
    print(f"  {b:15} {sum(1 for k in ks if E[k]['niv'] >= 4)}/{len(ks)} "
          "au plafond du niveau 4")
print("  => si les DEUX bras sont au plafond, un d=0 est un PLAFOND, "
      "pas une absence d'effet")

print("\n=== VÉRIF — maîtrise à PALIER ÉGAL ===")
for b in BRAS:
    par = {}
    for g in GRAINES:
        par.setdefault(E[f"{b}_g{g}"]["niv"], []).append(E[f"{b}_g{g}"]["mait"])
    print(f"  {b:16} " + " | ".join(f"niv{n}: {st.median(v):5.1f}% (n={len(v)})"
                                    for n, v in sorted(par.items())))

if depouillement.publier(os.path.join(D, "agregat.json")):
    print(f"\nagregat.json écrit ({len(E)} runs)")
sys.exit(depouillement.code_sortie())
