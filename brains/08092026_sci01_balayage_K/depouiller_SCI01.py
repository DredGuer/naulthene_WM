#!/usr/bin/env python3
"""Dépouillement STRICT de la campagne 08092026_sci01_balayage_K (SCI-01).

Protocole et juges pré-enregistrés : `LISEZ_MOI.md` (08/09/2026, code v41.68) —
transcrits dans les manifestes. Bras : K1_TEMOIN · K2_NU · K4_NU · K8_NU ·
K16_NU · K8_CLIP_e02, tous sur socle réparé (voix libre + --detach-c2 constants).

⚠️ Deux manifestes : `manifeste.json` (parent, 20 graines = Waves 1+2) et
`manifeste_wave1.json` (10 graines 11→111 = Wave 1 seule). Usage :
`venv/bin/python depouiller_SCI01.py [manifeste_wave1.json|manifeste.json]` —
défaut `manifeste_wave1.json` (Wave 1 terminée) ; passer `manifeste.json`
seulement quand Waves 1+2 complètes (n=20).

Règles MES-01/MES-04 appliquées par `naulthene.instruments.depouillement` :
refuse d'écrire un agrégat sur une campagne incomplète, vérifie les gardes
(voix libre ≡ 1,00), dérive le seuil de `n` × `comparaisons_prevues` (5).

Juges pré-enregistrés (LISEZ_MOI §3) :
  1. Maîtrise  : δ apparié vs K1_TEMOIN (et CLIP vs K8_NU) — t > seuil, survit aux extrêmes.
  2. Niveau    : franchissement du mur (`niv >= 5` = entré dans LavaGapS5).
  3. FORME de K : maîtrise(K) vs K — monotone ? saturée ? en cloche ? (lecture + δ par palier).
  4. Mécaniste ε : distribution du ratio + fraction clippée — télémétrie `Rejouer`
     (v41.68), présente UNIQUEMENT sur K8_CLIP_e02 (bras NU : pas de ratio logué,
     réserve consignée au journal des runs).

Code de sortie ≠ 0 si la campagne est invalide ou un juge ne peut pas être prononcé.
"""
import json
import os
import re
import statistics as st
import sys

D = os.path.dirname(os.path.abspath(__file__))
for p in (os.path.join(D, "..", "..", "src"), os.path.join(D, "..", "..", "..", "src")):
    if os.path.isdir(p):
        sys.path.insert(0, p)
        break

from naulthene.instruments.depouillement import Depouillement, Manifeste  # noqa: E402
from naulthene.instruments.journal_cursus import lire_journal, resumer_journal  # noqa: E402

_nom_manifeste = sys.argv[1] if len(sys.argv) > 1 else "manifeste_wave1.json"
_mf = json.load(open(os.path.join(D, _nom_manifeste), encoding="utf-8"))
print(f"📋 Manifeste : {_nom_manifeste} — {len(_mf['graines'])} graines × "
      f"{len(_mf['bras'])} bras = {len(_mf['graines']) * len(_mf['bras'])} runs attendus")

depouillement = Depouillement(
    Manifeste.depuis_fichier(os.path.join(D, _nom_manifeste)), racine=D)
depouillement.collecter(lambda chemin: resumer_journal(lire_journal(chemin)))
depouillement.verifier_gardes()
print(depouillement.rapport())

if not depouillement.valide():
    print("\n⛔ Aucun agrégat écrit, aucun juge prononcé — voir les violations ci-dessus.")
    sys.exit(depouillement.code_sortie())

E = depouillement.runs
GRAINES = depouillement.manifeste.graines
BRAS = list(depouillement.manifeste.bras)


def juger(a, b, var, label, retirer=4):
    res = depouillement.apparie(a, b, var, label, retirer_extremes=retirer)
    print(res.ligne())
    if res.reduit:
        print(res.reduit.ligne())


print("\n=== JUGE 1 — MAÎTRISE (δ apparié vs K1_TEMOIN ; CLIP vs K8_NU) ===")
for b in ("K2_NU", "K4_NU", "K8_NU", "K16_NU"):
    juger(b, "K1_TEMOIN", "mait", f"{b} - K1_TEMOIN")
juger("K8_CLIP_e02", "K8_NU", "mait", "K8_CLIP_e02 - K8_NU (effet du clip à K=8)")

print("\n=== JUGE 2 — NIVEAU (franchissement du mur, comptage par bras) ===")
for b in BRAS:
    ks = [f"{b}_g{g}" for g in GRAINES]
    print(f"  {b:12} niv>=5 : {sum(1 for k in ks if E[k]['niv'] >= 5):2}/{len(ks)}"
          f"  | maîtrise 0% : {sum(1 for k in ks if E[k]['mait'] == 0):2}"
          f"  | maîtrise moy {st.mean([E[k]['mait'] for k in ks]):5.2f}%")

print("\n=== JUGE 3 — FORME de K (maîtrise par palier de K — lecture, pas de test) ===")
for b in BRAS:
    vals = [E[f"{b}_g{g}"]["mait"] for g in GRAINES]
    print(f"  {b:12} maîtrise moy {st.mean(vals):5.2f}% · méd {st.median(vals):5.1f}%"
          f" · min {min(vals):3.0f} · max {max(vals):3.0f}")

print("\n  δ maîtrise par palier de K (chaque bras vs K1_TEMOIN, détail du juge 1) :")
for b in ("K2_NU", "K4_NU", "K8_NU", "K16_NU", "K8_CLIP_e02"):
    deltas = [E[f"{b}_g{g}"]["mait"] - E[f"K1_TEMOIN_g{g}"]["mait"] for g in GRAINES]
    print(f"  {b:12} δ moy {st.mean(deltas):+6.2f} pt · {sum(1 for d in deltas if d > 0)}/20 favorables")

print("\n=== JUGE 4 — MÉCANISTE ε (ratio + fraction clippée, télémétrie Rejouer) ===")
# La ligne Rejouer (v41.68) ne porte ratio/p90/clippés QUE sur K8_CLIP_e02
# (RATIO_CLIPPE_ACTIF) — réserve consignée au journal des runs (bras NU sans télémétrie).
_REJOUER = re.compile(
    r"Rejouer \(v41\.68\).*?ratio moy ([0-9.]+) · p90 ([0-9.]+) · clippés ([0-9.]+)%")

def dernieres_stats_rejouer(chemin: str) -> dict | None:
    """Dernières stats Rejouer d'un log (moyenne des 200 dernières nuits)."""
    ratios, clippes = [], []
    with open(chemin, errors="ignore", encoding="utf-8") as fh:
        for ligne in fh:
            m = _REJOUER.search(ligne)
            if m:
                ratios.append(float(m.group(1)))
                clippes.append(float(m.group(3)))
    if not ratios:
        return None
    r = ratios[-200:]
    c = clippes[-200:]
    return {"ratio_moy": st.mean(r), "ratio_p90": sorted(r)[int(len(r) * 0.9) - 1],
            "frac_clippee": st.mean(c)}

print("  ⚠️ Bras NU (K1→K16) : ratio non logué (hors RATIO_CLIPPE_ACTIF) — télémétrie absente,")
print("     réserve consignée au journal des runs (09/08). Seul K8_CLIP_e02 est lisible ici.")
for g in GRAINES:
    chemin = os.path.join(D, "K8_CLIP_e02", f"K8_CLIP_e02_g{g}.log")
    s = dernieres_stats_rejouer(chemin)
    if s:
        print(f"  K8_CLIP_e02_g{g}: ratio moy {s['ratio_moy']:.4f}"
              f" · p90 {s['ratio_p90']:.4f} · fraction clippée {s['frac_clippee']:.1f}%")

print("\n=== TEST DE TAUTOLOGIE (maîtrise conditionnée aux victoires > 0) ===")
for b in ("K4_NU", "K8_NU", "K16_NU", "K8_CLIP_e02"):
    deltas = [E[f"{b}_g{g}"]["mait"] - E[f"K1_TEMOIN_g{g}"]["mait"] for g in GRAINES
              if E[f"K1_TEMOIN_g{g}"].get("vict", 0) > 0
              and E[f"{b}_g{g}"].get("vict", 0) > 0]
    if len(deltas) >= 2:
        print(depouillement.resultat_de(
            deltas, f"{b} maîtrise conditionnée (n={len(deltas)})").ligne())
    else:
        print(f"  {b}: pas assez de paires victorieuses pour conditionner (n={len(deltas)})")

print("\n=== VÉRIF — maîtrise à PALIER ÉGAL (niveau 4 uniquement, hors franchisseurs) ===")
for b in BRAS:
    par = {}
    for g in GRAINES:
        par.setdefault(E[f"{b}_g{g}"]["niv"], []).append(E[f"{b}_g{g}"]["mait"])
    print(f"  {b:12} " + " | ".join(f"niv{n}: {st.median(v):5.1f}% (n={len(v)})"
                                    for n, v in sorted(par.items())))

_sortie_agregat = os.path.join(
    D, "agregat_wave1.json" if _nom_manifeste == "manifeste_wave1.json" else "agregat.json")
if depouillement.publier(_sortie_agregat):
    print(f"\n✅ {os.path.basename(_sortie_agregat)} écrit ({len(E)} runs)")
sys.exit(depouillement.code_sortie())
