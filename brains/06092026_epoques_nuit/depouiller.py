#!/usr/bin/env python3
"""Dépouillement STRICT de la campagne 06092026_epoques_nuit.

Protocole et juges : `LISEZ_MOI.md` — transcrits dans `manifeste.json`.
Bras : TEMOIN (réutilise 04092026_cursus_complet/LIBRE) vs K8_NU vs K8_CLIP.

⚠️ Réécrit le 08/09/2026 au titre de **MES-01** (registre des problèmes à corriger).
La version précédente affichait « CAMPAGNE INVALIDE » sans s'arrêter, écartait
silencieusement toute graine absente (`for g in GRAINES if ... in E`) et comparait
`t` à la constante **2,86** y compris après retrait de quatre observations. Toute
cette logique vit désormais dans `naulthene.instruments.depouillement`, qui refuse
d'écrire un agrégat sur une campagne invalide et **dérive** le seuil de `n`.

Usage : `venv/bin/python brains/06092026_epoques_nuit/depouiller.py`
Code de sortie **≠ 0** si la campagne est invalide.
"""
import os
import statistics as st
import sys

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(D)), "src"))
sys.path.insert(0, os.path.join(D, "..", "..", "src"))

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


print("\n=== JUGE 1 — MAÎTRISE ===")
juger("K8_NU", "TEMOIN", "mait", "K8_NU - TEMOIN")
juger("K8_CLIP", "TEMOIN", "mait", "K8_CLIP - TEMOIN")
juger("K8_NU", "K8_CLIP", "mait", "K8_NU - K8_CLIP")

print("\n=== JUGE 2 — NIVEAU (le mur) ===")
juger("K8_NU", "TEMOIN", "niv", "K8_NU - TEMOIN")
juger("K8_CLIP", "TEMOIN", "niv", "K8_CLIP - TEMOIN")

print("\n=== JUGE 3 — MÉCANISTE : entropie de C1 (la politique se décide-t-elle ?) ===")
juger("K8_NU", "TEMOIN", "hc1", "K8_NU - TEMOIN")
juger("K8_CLIP", "TEMOIN", "hc1", "K8_CLIP - TEMOIN")

print("\n=== TEST DE TAUTOLOGIE (les deux bras ont gagné au moins une fois) ===")
print("  ⚠️ conditionnement DÉLIBÉRÉ, pas une exclusion : le n retenu est affiché.")
for b in ("K8_NU", "K8_CLIP"):
    deltas = [E[f"{b}_g{g}"]["mait"] - E[f"TEMOIN_g{g}"]["mait"] for g in GRAINES
              if E[f"TEMOIN_g{g}"]["vict"] > 0 and E[f"{b}_g{g}"]["vict"] > 0]
    print(depouillement.resultat_de(deltas, f"{b} maîtrise conditionnée").ligne())

print("\n=== COMPTAGES ===")
for b in BRAS:
    ks = [f"{b}_g{g}" for g in GRAINES]
    print(f"  {b:10} niv>=5: {sum(1 for k in ks if E[k]['niv'] >= 5):2}/{len(ks)} | "
          f"maîtrise 0%: {sum(1 for k in ks if E[k]['mait'] == 0):2} | "
          f"maîtrise moy {st.mean([E[k]['mait'] for k in ks]):5.2f}% | "
          f"victoires méd {st.median([E[k]['vict'] for k in ks]):.0f} | "
          f"niv max {max(E[k]['niv'] for k in ks)}")

print("\n=== VÉRIF — maîtrise à PALIER ÉGAL ===")
for b in BRAS:
    par = {}
    for g in GRAINES:
        par.setdefault(E[f"{b}_g{g}"]["niv"], []).append(E[f"{b}_g{g}"]["mait"])
    print(f"  {b:10} " + " | ".join(f"niv{n}: {st.median(v):5.1f}% (n={len(v)})"
                                    for n, v in sorted(par.items())))

if depouillement.publier(os.path.join(D, "agregat.json")):
    print(f"\nagregat.json écrit ({len(E)} runs)")
sys.exit(depouillement.code_sortie())
