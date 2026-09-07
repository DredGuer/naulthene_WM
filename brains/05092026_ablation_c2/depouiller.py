#!/usr/bin/env python3
"""Dépouillement STRICT de la campagne 05092026_ablation_c2.

Protocole et juges : `LISEZ_MOI.md` — transcrits dans `manifeste.json`.
Bras : LIBRE (réutilise 04092026_cursus_complet) vs LIBRE_SANS_C2 vs TEMOIN_SANS_C2.

⚠️ Réécrit le 08/09/2026 au titre de **MES-01** : couverture, garde-fous et seuils
sont désormais portés par `naulthene.instruments.depouillement`. Le garde-fou du
bras témoin est un **plancher** (`gain > 0,5`), pas une cible — il est déclaré comme
tel au manifeste, et il est BLOQUANT comme les autres.

Usage : `venv/bin/python brains/05092026_ablation_c2/depouiller.py`
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


print("\n=== JUGE 1 — MAÎTRISE : C2 sert-il ? (LIBRE vs LIBRE_SANS_C2) ===")
juger("LIBRE", "LIBRE_SANS_C2", "mait", "maîtrise")

print("\n=== JUGE 2 — NIVEAU : C2 sert-il ? ===")
juger("LIBRE", "LIBRE_SANS_C2", "niv", "niveau")

print("\n=== JUGE 3 — LA CONFUSION HISTORIQUE (LIBRE_SANS_C2 vs TEMOIN_SANS_C2) ===")
juger("LIBRE_SANS_C2", "TEMOIN_SANS_C2", "mait", "maîtrise")
juger("LIBRE_SANS_C2", "TEMOIN_SANS_C2", "niv", "niveau")
juger("LIBRE_SANS_C2", "TEMOIN_SANS_C2", "c1", "amplitude C1")

print("\n=== TEST DE TAUTOLOGIE (les deux bras ont gagné au moins une fois) ===")
print("  ⚠️ conditionnement DÉLIBÉRÉ, pas une exclusion : le n retenu est affiché.")
deltas = [E[f"LIBRE_g{g}"]["mait"] - E[f"LIBRE_SANS_C2_g{g}"]["mait"] for g in GRAINES
          if E[f"LIBRE_g{g}"]["vict"] > 0 and E[f"LIBRE_SANS_C2_g{g}"]["vict"] > 0]
print(depouillement.resultat_de(deltas, "maîtrise conditionnée").ligne())

print("\n=== COMPTAGES ===")
for b in BRAS:
    ks = [f"{b}_g{g}" for g in GRAINES]
    print(f"  {b:15} niv4: {sum(1 for k in ks if E[k]['niv'] >= 4):2}/{len(ks)} | "
          f"maîtrise 0%: {sum(1 for k in ks if E[k]['mait'] == 0):2} | "
          f"niveau 1: {sum(1 for k in ks if E[k]['niv'] <= 1):2} | "
          f"niv max {max(E[k]['niv'] for k in ks)}")

# Comparer la maîtrise de deux cerveaux qui jouent des NIVEAUX DIFFÉRENTS n'a pas de
# sens : un palier plus facile donne mécaniquement une maîtrise plus haute.
print("\n=== VÉRIF — maîtrise à PALIER ÉGAL (l'inversion du juge 3) ===")
for b in BRAS:
    par = {}
    for g in GRAINES:
        par.setdefault(E[f"{b}_g{g}"]["niv"], []).append(E[f"{b}_g{g}"]["mait"])
    print(f"  {b:16} " + " | ".join(f"niv{n}: {st.median(v):5.1f}% (n={len(v)})"
                                    for n, v in sorted(par.items())))
print("  => si l'écart disparaît à niveau égal, le delta de maîtrise est un "
      "ARTEFACT de palier")

if depouillement.publier(os.path.join(D, "agregat.json")):
    print(f"\nagregat.json écrit ({len(E)} runs)")
sys.exit(depouillement.code_sortie())
