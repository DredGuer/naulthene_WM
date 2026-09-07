#!/usr/bin/env python3
"""Dépouillement STRICT de la campagne 07092026_branches_persistantes.

Protocole et juges : `LISEZ_MOI.md` — transcrits dans `manifeste.json`.
Bras : **BP** (`--epoques-nuit 8 --branches-persistantes`, voix libre) vs **K8_NU**
(le meilleur régime connu du 06/09, réutilisé comme témoin — 0 run neuf).

Juges pré-enregistrés :
  J1 maîtrise appariée (+ retrait des 4 extrêmes)
  J2 niveau (apparié + Fisher sur le comptage ≥ 5)
  J3 ratio h7/h1 du rollout (mécaniste — `rollout_h7h1/` pour BP,
     `../07092026_rollout_k8/` pour le témoin)
  J4 accord C1/C2 + ratio d'amplitude + garde-fou `gain_c1`

⚠️ Réécrit le 08/09/2026 au titre de **MES-01** : couverture, garde-fous et seuils
sont portés par `naulthene.instruments.depouillement`. Deux changements de fond par
rapport à la version d'origine :
  1. les 40 JSON de rollout sont EXIGÉS — leur absence bloque la publication, là où
     la version précédente se contentait de les ajouter à une liste affichée ;
  2. le seuil n'est plus la constante 2,86 mais la valeur dérivée de `n` et de la
     famille de 3 métriques. Le juge 4 (accord), descriptif à l'origine (seuil 1,96),
     est désormais jugé au seuil de la famille — plus sévère, verdict inchangé.

Usage : `venv/bin/python brains/07092026_branches_persistantes/depouiller_BP.py`
Code de sortie **≠ 0** si la campagne est invalide.
"""
import json
import math
import os
import statistics as st
import sys
from math import comb

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(D)), "src"))

from naulthene.instruments.depouillement import Depouillement, Manifeste  # noqa: E402
from naulthene.instruments.journal_cursus import lire_journal, resumer_journal  # noqa: E402

BP_ROLLOUT = os.path.join(D, "rollout_h7h1")
K8_ROLLOUT = os.path.join(os.path.dirname(D), "07092026_rollout_k8")


def fisher_exact(a, b, c, d):
    """Test exact de Fisher bilatéral sur la table [[a, b], [c, d]]."""
    n = a + b + c + d

    def p_obs(x):
        return (comb(a + b, x) * comb(c + d, a + c - x)) / comb(n, a + c)

    lo, hi = max(0, a - d), min(a + b, a + c)
    p0 = p_obs(a)
    return sum(p_obs(x) for x in range(lo, hi + 1) if p_obs(x) <= p0 + 1e-15)


depouillement = Depouillement(
    Manifeste.depuis_fichier(os.path.join(D, "manifeste.json")), racine=D)
depouillement.collecter(lambda chemin: resumer_journal(lire_journal(chemin)))
depouillement.verifier_gardes()

GRAINES = depouillement.manifeste.graines

# --- Données annexes : le ratio h7/h1 du rollout, EXIGÉ graine par graine ---------
ROLL = {}
for bras, dossier in (("BP", BP_ROLLOUT), ("K8_NU", K8_ROLLOUT)):
    for g in GRAINES:
        chemin = os.path.join(dossier, f"{bras}_g{g}.json")
        if depouillement.exiger(os.path.exists(chemin),
                                f"rollout {bras}_g{g} : fichier absent ({chemin})"):
            with open(chemin, encoding="utf-8") as fh:
                ROLL[f"{bras}_g{g}"] = json.load(fh)["ratio_h7_sur_h1"]

print(depouillement.rapport())
print(f"rollout h7/h1 : {len(ROLL)}/{2 * len(GRAINES)} mesures présentes")

if not depouillement.valide():
    print("\n⛔ Aucun agrégat écrit, aucun juge prononcé — voir les violations ci-dessus.")
    sys.exit(depouillement.code_sortie())

E = depouillement.runs
BRAS = list(depouillement.manifeste.bras)


def juger(a, b, var, label):
    res = depouillement.apparie(a, b, var, label, retirer_extremes=4)
    print(res.ligne())
    if res.reduit:
        print(res.reduit.ligne())
    return depouillement.deltas(a, b, var)


print("\n=== JUGE 1 — MAÎTRISE (BP - K8_NU, apparié) ===")
juger("BP", "K8_NU", "mait", "maîtrise")

print("\n=== JUGE 2 — NIVEAU (BP - K8_NU) ===")
d_niv = juger("BP", "K8_NU", "niv", "niveau (apparié)")
nplus = sum(1 for x in d_niv if x > 0)
nmoins = sum(1 for x in d_niv if x < 0)
print(f"  signe : {nplus} BP > K8_NU · {nmoins} BP < K8_NU · "
      f"{len(d_niv) - nplus - nmoins} égaux")
bp5 = sum(1 for g in GRAINES if E[f"BP_g{g}"]["niv"] >= 5)
k85 = sum(1 for g in GRAINES if E[f"K8_NU_g{g}"]["niv"] >= 5)
n = len(GRAINES)
print(f"  Fisher (comptage ≥ 5) : BP {bp5}/{n} vs K8_NU {k85}/{n}  "
      f"p = {fisher_exact(bp5, n - bp5, k85, n - k85):.4f}")

print("\n=== JUGE 3 — MÉCANISTE : ratio h7/h1 du rollout (séparation des branches) ===")
rbp = [ROLL[f"BP_g{g}"] for g in GRAINES]
rk8 = [ROLL[f"K8_NU_g{g}"] for g in GRAINES]
print(f"  médiane BP : {st.median(rbp):.4f}   médiane K8_NU : {st.median(rk8):.4f}")
# apparié sur log10 (ratios très asymétriques)
d_log = [math.log10(ROLL[f"BP_g{g}"] + 1e-12) - math.log10(ROLL[f"K8_NU_g{g}"] + 1e-12)
         for g in GRAINES]
res = depouillement.resultat_de(d_log, "log10(ratio) BP - K8_NU", retirer_extremes=4)
print(res.ligne())
if res.reduit:
    print(res.reduit.ligne())
print(f"  cerveaux à ratio > 0,05 : BP {sum(1 for x in rbp if x > 0.05)}/{n} · "
      f"K8_NU {sum(1 for x in rk8 if x > 0.05)}/{n}")

print("\n=== JUGE 4 — ACCORD C1/C2 et ratio d'amplitude ===")
print("  ⚠️ juge DESCRIPTIF à l'origine (seuil 1,96) ; jugé ici au seuil de la famille.")
juger("BP", "K8_NU", "accord", "accord C1/C2 % (apparié)")
for bras in BRAS:
    ratios = [E[f"{bras}_g{g}"]["c2"] / E[f"{bras}_g{g}"]["c1"]
              for g in GRAINES if E[f"{bras}_g{g}"]["c1"]]
    print(f"  ratio C2/C1 médian {bras:8} {st.median(ratios):.3f}  (n={len(ratios)})")

print("\n=== COMPTAGES ===")
for bras in BRAS:
    ks = [f"{bras}_g{g}" for g in GRAINES]
    print(f"  {bras:10} niv>=5: {sum(1 for k in ks if E[k]['niv'] >= 5):2}/{len(ks)} | "
          f"maîtrise 0%: {sum(1 for k in ks if E[k]['mait'] == 0):2} | "
          f"maîtrise moy {st.mean([E[k]['mait'] for k in ks]):5.2f}% | "
          f"victoires méd {st.median([E[k]['vict'] for k in ks]):.0f} | "
          f"niv max {max(E[k]['niv'] for k in ks)}")

print("\n=== VÉRIF — maîtrise à PALIER ÉGAL ===")
for bras in BRAS:
    par = {}
    for g in GRAINES:
        par.setdefault(E[f"{bras}_g{g}"]["niv"], []).append(E[f"{bras}_g{g}"]["mait"])
    print(f"  {bras:10} " + " | ".join(f"niv{k}: {st.median(v):5.1f}% (n={len(v)})"
                                       for k, v in sorted(par.items())))

for cle, valeur in ROLL.items():
    E[cle]["ratio_h7_sur_h1"] = valeur
if depouillement.publier(os.path.join(D, "agregat_BP.json")):
    print(f"\nagregat_BP.json écrit ({len(E)} runs)")
sys.exit(depouillement.code_sortie())
