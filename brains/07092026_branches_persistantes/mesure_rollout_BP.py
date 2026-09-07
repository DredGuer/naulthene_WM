#!/usr/bin/env python3
"""Mesure le ratio h7/h1 du rollout sur un cerveau BP — régime BRANCHES PERSISTANTES.

Copie fidèle du geste de `sonde_horizon_branches.py` (lecture seule : copie du .brain,
jamais l'original), MAIS force le drapeau v41.63 dans le module importé : lancé via
`python -m naulthene.instruments.sonde_horizon_branches`, le parse d'arguments de noyau
n'est jamais exécuté et `BRANCHES_PERSISTANTES` resterait False — la sonde mesurerait
l'ANCIEN rollout sur des cerveaux BP. C'est le piège de l'instrument du 01/09.

Usage :
    python3 mesure_rollout_BP.py <chemin_du_brain> [chemin_du_brain ...]
"""
import json, os, shutil, sys

import naulthene.cerveau.noyau as N

# v41.63 — les DEUX copies du module, même discipline que la campagne (l.12551 noyau).
N.BRANCHES_PERSISTANTES = True
try:
    N._module_reel.BRANCHES_PERSISTANTES = True
except AttributeError:
    pass

from naulthene.cerveau.persistance import PersistanceAnatomique
from naulthene.instruments.sonde_horizon_branches import separation_par_horizon

ICI = os.path.dirname(os.path.abspath(__file__))
SORTIE = os.path.join(ICI, "rollout_h7h1")
os.makedirs(SORTIE, exist_ok=True)


def mesurer(brain_path):
    copie = brain_path + ".h7tmp"
    shutil.copy2(brain_path, copie)
    try:
        agent = PersistanceAnatomique(copie).charger_ou_naitre(N.DEVICE).agent
        agent.eval()
        s = separation_par_horizon(agent, N)
        return {"brain": os.path.basename(brain_path), "separation": s,
                "ratio_h7_sur_h1": s[7] / (s[1] + 1e-12)}
    finally:
        try:
            os.remove(copie)
        except OSError:
            pass


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("usage: mesure_rollout_BP.py <brain> [brain ...]")
    for b in sys.argv[1:]:
        r = mesurer(b)
        nom = os.path.basename(b).replace(".brain", ".json")
        out = os.path.join(SORTIE, nom)
        json.dump(r, open(out, "w"), indent=1)
        print(f"  {r['brain']:<26} h1 {r['separation'][1]:.5f}  "
              f"h3 {r['separation'][3]:.5f}  h7 {r['separation'][7]:.5f}   "
              f"h7/h1 {r['ratio_h7_sur_h1']:.4f}  -> {out}")
