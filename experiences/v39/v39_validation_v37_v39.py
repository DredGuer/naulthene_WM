"""Validation v37 → v39 : chaque condition dans sa propre graine, en PARALLÈLE.

Objectif : vérifier que les mécaniques livrées entre la v37 et la v39 font
ce qu'elles annoncent — et, quand c'est possible, qu'elles APPORTENT
quelque chose. Chaque condition est isolée (une seule chose change), et
tous les runs tournent dans des processus séparés.

⚠️ TOUS les runs utilisent le réarmement CORRIGÉ (R5) : le but reste
derrière la porte. Les résultats ne sont donc PAS comparables aux
chiffres v38 publiés, qui ont été produits avec le biais.

CONDITIONS
    base        v39 complet (référence de cette campagne)
    sans_v39    empreinte de type neutralisée (= comportement v38)
    sans_prior  empreinte conservée mais prior débranché (isole P12)
    sans_v37    distillation C2→C1 coupée (isole v37.1)
    sans_c2     C2 n'influence plus la décision (contrôle historique)

Chaque condition × 6 graines = 30 runs, lancés par vagues parallèles.
"""
import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

RACINE = Path("/Users/dredguer/Documents/1. Dossier personnel important/1. Adrien/21. AGI")
SCRATCH = Path(__file__).parent

GABARIT = '''
import sys, os, json
sys.path.insert(0, "src"); sys.path.insert(0, "experiences/v38")
os.environ.setdefault("WANDB_MODE", "offline")
import torch
from naulthene.cerveau import noyau as N

COND = "{cond}"

# --- neutralisations, une seule par condition ---
if COND == "sans_v39":
    # l'empreinte de type ne survit plus aux promotions (comportement v38)
    def _reinit_v38(self):
        self.souvenirs = []
        self.empreinte_types = {{}}
    N.MemoireEpisodiqueSpatiale.reinitialiser_niveau = _reinit_v38

elif COND == "sans_prior":
    # l'empreinte SURVIT mais n'informe plus la naissance des repères :
    # isole l'apport du PRIOR (P12) de celui de la simple conservation (P11).
    _vrai_enr = N.MemoireEpisodiqueSpatiale.enregistrer_evenement
    def _enr_sans_prior(self, position, type_evenement, tick_absolu, intensite=0.0, **kw):
        avant = dict(self.empreinte_types)
        self.empreinte_types = {{}}          # prior indisponible à l'écriture
        try:
            return _vrai_enr(self, position, type_evenement, tick_absolu,
                             intensite=intensite, **kw)
        finally:
            # on restaure et on ré-applique la mise à jour manquée
            fusion = dict(avant)
            for k, v in self.empreinte_types.items():
                if k not in fusion:
                    fusion[k] = v
            self.empreinte_types = fusion
            self._nourrir_empreinte(type_evenement, intensite)
    N.MemoireEpisodiqueSpatiale.enregistrer_evenement = _enr_sans_prior

elif COND == "sans_v37":
    N.TAUX_DISTILLATION_C1 = 0.0          # l'auto-distillation C2->C1 est coupée

elif COND == "sans_c2":
    # ⚠️ NE PAS toucher FORCE_PLANIFICATION_LIBRE : elle sert AUSSI à dériver
    # VIGUEUR_MIN_C1 au moment de l'import (noyau.py:3146). La mettre à 0 corromprait
    # le gain de C1 en plus de couper C2 — deux changements au lieu d'un.
    # On neutralise donc la valeur du JOUR, après qu'elle a été calculée.
    _vraie_nuit_fp = N.executer_nuit
    def _forcer_zero(etat, *a, **k):
        r = _vraie_nuit_fp(etat, *a, **k)
        etat.force_planification_jour = 0.0
        return r
    N.executer_nuit = _forcer_zero
    _vrai_demarrer = N.demarrer_journee
    def _demarrer_zero(etat, *a, **k):
        r = _vrai_demarrer(etat, *a, **k)
        etat.force_planification_jour = 0.0
        return r
    N.demarrer_journee = _demarrer_zero

# --- traçage commun ---
journal = {{"jours": [], "victoires": []}}
_vraie_nuit = N.executer_nuit
def _nuit(etat, *a, **k):
    r = _vraie_nuit(etat, *a, **k)
    journal["jours"].append((etat.jour, etat.niveau_actuel))
    if etat.victoire_aujourdhui:
        journal["victoires"].append(etat.jour)
    return r
N.executer_nuit = _nuit

import v38_2a_continuite as X
sys.argv = ["x", "--jours", "{jours}", "--graine", "{graine}",
            "--continu", "--patience-surface", "--brain", r"{brain}"]
try:
    X.main()
except SystemExit:
    pass

niveau_joue, prec = {{}}, 0
for j, niv in journal["jours"]:
    niveau_joue[j] = prec
    prec = niv
arrivee, prem = {{}}, {{}}
for j in sorted(niveau_joue):
    arrivee.setdefault(niveau_joue[j], j)
for j in journal["victoires"]:
    n = niveau_joue.get(j)
    if n is not None:
        prem.setdefault(n, j)
delais = {{n: prem[n] - arrivee[n] for n in arrivee if n in prem and prem[n] >= arrivee[n]}}

# santé synaptique : la promesse centrale de la v37
import glob
sante = {{}}
try:
    d = torch.load(r"{brain}", map_location="cpu", weights_only=False)
    sd = d["state_dict"]
    base = {{k.replace(".base_weight",""): t for k, t in sd.items()
             if k.endswith("base_weight")}}
    nn = {{k.replace(".norme_naissance",""): float(t) for k, t in sd.items()
           if k.endswith("norme_naissance")}}
    morts = sum(int((t.abs() < 1e-8).sum()) for t in base.values())
    plancher = sum(1 for k, t in base.items()
                   if k in nn and nn[k] > 0 and float(t.norm())/nn[k] < 0.105)
    sante = {{"synapses_mortes": morts, "couches_au_plancher": plancher,
              "n_couches": len(base),
              "empreinte_types": len(d.get("empreinte_types", {{}}) or {{}}),
              "souvenirs": len(d.get("souvenirs_spatiaux", []) or []),
              "reperes_goal": sum(1 for s in (d.get("souvenirs_spatiaux") or [])
                                  if s.get("type") == "goal")}}
except Exception as e:
    sante = {{"erreur": str(e)}}

json.dump({{"condition": COND, "graine": {graine},
           "niveau_final": max((n for _, n in journal["jours"]), default=0),
           "victoires": len(journal["victoires"]),
           "delais": delais,
           "delai_median": sorted(delais.values())[len(delais)//2] if delais else None,
           **sante}}, open(r"{sortie}", "w"), indent=1)
'''

CONDITIONS = ["base", "sans_v39", "sans_prior", "sans_v37", "sans_c2"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jours", type=int, default=400)
    ap.add_argument("--graines", type=int, nargs="+", default=[11, 22, 33, 44, 55, 66])
    ap.add_argument("--conditions", nargs="+", default=CONDITIONS)
    ap.add_argument("--parallele", type=int, default=5,
                    help="runs simultanés (12 cœurs disponibles)")
    a = ap.parse_args()

    taches = [(c, g) for g in a.graines for c in a.conditions]
    print(f"{len(taches)} runs — {a.parallele} en parallèle, {a.jours} jours\n", flush=True)

    en_cours, faits = [], 0
    t0 = time.time()
    while taches or en_cours:
        while taches and len(en_cours) < a.parallele:
            cond, g = taches.pop(0)
            sortie = SCRATCH / f"v3739_{cond}_g{g}.json"
            script = SCRATCH / f"_v3739_{cond}_{g}.py"
            script.write_text(GABARIT.format(
                cond=cond, graine=g, jours=a.jours, sortie=str(sortie),
                brain=f"/tmp/v3739_{cond}_g{g}.brain"))
            log = open(SCRATCH / f"v3739_{cond}_g{g}.log", "w")
            p = subprocess.Popen([sys.executable, str(script)], cwd=str(RACINE),
                                 env=dict(os.environ, WANDB_MODE="offline"),
                                 stdout=log, stderr=subprocess.STDOUT)
            en_cours.append((p, cond, g, sortie, log))
            print(f"  ▶ {cond:11s} g{g}", flush=True)

        time.sleep(5)
        for item in list(en_cours):
            p, cond, g, sortie, log = item
            if p.poll() is not None:
                log.close()
                en_cours.remove(item)
                faits += 1
                ok = "✓" if sortie.exists() else "✗"
                print(f"  {ok} {cond:11s} g{g}   [{faits}/{faits+len(taches)+len(en_cours)}]"
                      f"  {(time.time()-t0)/60:.0f} min", flush=True)

    resultats = []
    for f in sorted(SCRATCH.glob("v3739_*.json")):
        try:
            resultats.append(json.loads(f.read_text()))
        except Exception:
            pass
    json.dump(resultats, open(SCRATCH / "v3739_TOUS.json", "w"), indent=1)
    print(f"\n→ v3739_TOUS.json ({len(resultats)} runs)")


if __name__ == "__main__":
    main()
