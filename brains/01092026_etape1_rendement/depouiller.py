#!/usr/bin/env python3
"""Dépouillement STRICT de l'Étape 1 — protocole écrit AVANT le moindre résultat.

Juge de paix : la DIRECTIVITÉ au banc (< 6× succès, ≥ 12× échec), `LISEZ_MOI.md`.
Les runs d'entraînement produisent des `.brain` ; la directivité se mesure ensuite
au banc en lecture seule (`sonde_plancher_geometrique`, instrument corrigé le 01/09).

⚠️ Réécrit le 08/09/2026 au titre de **MES-01**. La version précédente sautait en
silence toute paire manquante (`except FileNotFoundError: continue`) et écrivait
`agregat.json` sans condition. La cohorte est désormais déclarée au manifeste et
exigée en entier.
⚠️ Aucune famille de tests n'ayant été pré-enregistrée ce jour-là, les seuils
affichés sont INDICATIFS — voir le commentaire du manifeste.

Usage : `venv/bin/python brains/01092026_etape1_rendement/depouiller.py`
Code de sortie **≠ 0** si la cohorte est incomplète.
"""
import json
import os
import statistics as st
import subprocess
import sys

D = os.path.dirname(os.path.abspath(__file__))
RACINE_DEPOT = os.path.dirname(os.path.dirname(D))
sys.path.insert(0, os.path.join(RACINE_DEPOT, "src"))

from naulthene.instruments.depouillement import Depouillement, Manifeste  # noqa: E402

GRAINES_DEFAUT = [11, 22, 33, 44, 55, 66, 77, 88, 99, 111,
                  122, 133, 144, 155, 166, 177, 188, 199, 211, 222]


def lancer_banc_si_absent(brain, sortie):
    """Produit la mesure de banc manquante ; ne juge rien, ne modifie aucun `.brain`."""
    if os.path.exists(sortie) or not os.path.exists(brain):
        return
    subprocess.run(
        [sys.executable, "-m", "naulthene.instruments.sonde_plancher_geometrique",
         "--brain", brain, "--episodes", "150", "--json", sortie],
        env={**os.environ, "PYTHONPATH": "src", "WANDB_MODE": "offline"},
        cwd=RACINE_DEPOT, capture_output=True)


def lire_banc(chemin):
    with open(chemin, encoding="utf-8") as fh:
        r = json.load(fh)["resultats"]["entraîné (eval)"]
    return {"succes": 100 * r["taux"], "directivite": r["directivite_mediane"],
            "n_victoires": r["n_victoires"]}


manifeste = Manifeste.depuis_fichier(os.path.join(D, "manifeste.json"))
for graine in manifeste.graines or GRAINES_DEFAUT:
    for bras in manifeste.bras:
        lancer_banc_si_absent(os.path.join(D, f"{bras}_g{graine}.brain"),
                              os.path.join(D, f"banc_{bras}_g{graine}.json"))

depouillement = Depouillement(manifeste, racine=D)
depouillement.collecter(lire_banc)
print(depouillement.rapport())

if not depouillement.valide():
    print("\n⛔ Aucun agrégat écrit, aucun juge prononcé — voir les violations ci-dessus.")
    sys.exit(depouillement.code_sortie())

E = depouillement.runs
GRAINES = manifeste.graines

print(f"\n{'graine':>7} {'ACTIF %':>9} {'TEM %':>8} {'ACTIF dir':>10} {'TEM dir':>9}")
for g in GRAINES:
    a, t = E[f"ACTIF_g{g}"], E[f"TEMOIN_g{g}"]
    fmt = lambda v, w: f"{v:>{w}.2f}" if v else f"{'-':>{w}}"  # noqa: E731
    print(f"{g:>7} {a['succes']:>9.2f} {t['succes']:>8.2f} "
          f"{fmt(a['directivite'], 10)} {fmt(t['directivite'], 9)}")

print("\n=== TESTS APPARIÉS (seuils INDICATIFS : aucune famille pré-enregistrée) ===")
print(depouillement.apparie("ACTIF", "TEMOIN", "succes", "δ succès (pt)").ligne())

# La directivité n'est DÉFINIE que pour un cerveau qui a gagné au moins une fois :
# les paires incomplètes sont un fait de la mesure, pas une exclusion — le n est affiché.
paires_dir = [g for g in GRAINES
              if E[f"ACTIF_g{g}"]["directivite"] and E[f"TEMOIN_g{g}"]["directivite"]]
print(f"  ⚠️ directivité définie sur {len(paires_dir)}/{len(GRAINES)} paires "
      "(un cerveau sans victoire n'a pas de trajet à mesurer)")
print(depouillement.resultat_de(
    [E[f"ACTIF_g{g}"]["directivite"] - E[f"TEMOIN_g{g}"]["directivite"]
     for g in paires_dir], "δ directivité (×)").ligne())

defini = [E[f"ACTIF_g{g}"]["directivite"] for g in GRAINES if E[f"ACTIF_g{g}"]["directivite"]]
print(f"\n=== JUGE DE PAIX (pré-enregistré) ===\n"
      f"  directivité ACTIF médiane = {st.median(defini):.2f}×  "
      f"(< 6,0 succès · ≥ 12,0 échec)  →  "
      f"{'SUCCÈS' if st.median(defini) < 6.0 else 'ÉCHEC' if st.median(defini) >= 12.0 else 'ZONE GRISE'}")

if depouillement.publier(os.path.join(D, "agregat.json")):
    print(f"\nagregat.json écrit ({len(E)} runs)")
sys.exit(depouillement.code_sortie())
