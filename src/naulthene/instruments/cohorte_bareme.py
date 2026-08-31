# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Adrien Nault — Naulthène AGI
"""LA COHORTE DU BARÈME — le ratio monde/interne prédit-il quoi que ce soit ? (v41.42)

Instrument de DIAGNOSTIC en lecture seule. Réplique sur N cerveaux la mesure que
l'audit du génome (30/08/2026) n'avait faite que sur UN.

    Un cerveau qui écoute un peu plus le monde s'en sort-il mieux qu'un cerveau
    enfermé dans son barème interne ?

---
POURQUOI CET INSTRUMENT

L'audit du 30/08 a mesuré que **95,6 % du signal d'apprentissage vient de constantes
posées** et **4,4 % du monde** — sur **un seul cerveau**. C'est une mesure directe
(§4 de la règle de mesure : fiable comme lecture), mais `n = 1` : elle décrit, elle
n'établit rien.

Seize hypothèses sont mortes exactement là où celle-ci se trouve : plausibles, non
mesurées. La règle du projet est de ne jamais conclure sous 20 graines.

⚠️ **Ce que cet instrument NE FAIT PAS** : couper la curiosité pour voir ce qui se
passe. Retirer 50 % du signal ferait s'effondrer l'agent à coup sûr — un effet énorme
et **ininterprétable** (« un cerveau privé de signal va moins bien » n'apprend rien).
C'est une ablation dont le résultat est connu d'avance, donc inutile.

Ici on ne coupe RIEN. On lit la **variation naturelle** entre 20 cerveaux qui ont
vécu, et on demande si elle corrèle avec la performance déjà journalisée.

---
CE QUE LA SONDE MESURE

Pour chaque cerveau de la cohorte, sur le niveau demandé :

  - `part_monde`  = Σ recompense_env / Σ (termes positifs)   ← l'écoute du monde
  - `part_curio`  = Σ dopamine_curiosite / Σ (termes positifs)
  - `part_stagn`  = Σ |penalite_stagnation| / Σ (termes négatifs)
  - `solde`       = Σ recompense_interne réellement versée

Puis la corrélation de ces parts avec la **maîtrise** et le **niveau atteint**, lus
dans le `.brain` lui-même — jamais recalculés.

---
LECTURE DU RÉSULTAT

| Ce qu'on observe | Verdict |
|---|---|
| `r(part_monde, maîtrise)` passe Bonferroni | 🔴 **premier suspect depuis une semaine** |
| `r` non significatif, dispersion faible | ✅ hypothèse **réfutée en une heure** |
| `part_monde` identique partout (σ ≈ 0) | ⚠️ mesure **VIDE** — pas de variation à corréler |

⚠️ Le troisième cas est le piège de l'ablation vide (bit de portage, 16 runs perdus) :
sans variation de la variable indépendante, aucune corrélation n'est calculable. Il est
testé explicitement et annoncé AVANT toute corrélation.

Aucune écriture : chaque cerveau est lu depuis une COPIE, jamais en place.

---
LANCEMENT

    PYTHONPATH=src python -m naulthene.instruments.cohorte_bareme \\
        --dossier brains/26082026_v4132_AB3_cursus --niveau 3 --jours 2
"""
from __future__ import annotations

import argparse
import glob
import json
import math
import os
import re
import shutil
import subprocess
import sys


# --- 1. LECTURE D'UN CERVEAU (sous-processus isolé) ---------------------------------
# Chaque cerveau est mesuré dans un processus SÉPARÉ : `sonde_recompense` installe un
# `sys.settrace` global et recharge des modules — mutualiser le processus ferait fuir
# l'état d'un cerveau sur le suivant, et cette fuite serait SILENCIEUSE.

_LIGNE = re.compile(r"^\s{2}(\w+)\s+(-?[\d.]+)\s+(-?[\d.]+)\s+(\d+)\s+([\d.]+)%")


def mesurer_un(chemin_brain: str, niveau: int, jours: int, scratch: str) -> dict | None:
    """Lance `sonde_recompense` sur une COPIE et parse sa sortie."""
    copie = os.path.join(scratch, "_lecture.brain")
    shutil.copy2(chemin_brain, copie)          # ⚠️ jamais lire un .brain en place

    env = dict(os.environ, WANDB_MODE="offline", PYTHONPATH="src")
    cmd = [sys.executable, "-m", "naulthene.instruments.sonde_recompense",
           "--brain", copie, "--jours", str(jours), "--niveau", str(niveau)]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True,
                             env=env, timeout=600).stdout
    except subprocess.TimeoutExpired:
        return None

    termes: dict[str, float] = {}
    for ligne in out.splitlines():
        m = _LIGNE.match(ligne)
        if m:
            termes[m.group(1)] = float(m.group(2))

    m_tot = re.search(r"RÉCOMPENSE TOTALE\s*:\s*([+-][\d.]+)", out)
    if not termes or m_tot is None:
        return None

    positifs = sum(v for v in termes.values() if v > 0)
    negatifs = sum(-v for v in termes.values() if v < 0)
    if positifs <= 0:
        return None

    return {
        "solde": float(m_tot.group(1)),
        "positifs": positifs,
        "negatifs": negatifs,
        "part_monde": termes.get("recompense_env", 0.0) / positifs,
        "part_curio": termes.get("dopamine_curiosite", 0.0) / positifs,
        "part_bio": termes.get("r_bio", 0.0) / positifs,
        "part_stagn": (-termes.get("penalite_stagnation", 0.0) / negatifs) if negatifs > 0 else 0.0,
        "termes": termes,
    }


# --- 2. PERFORMANCE LUE DANS LE .brain ----------------------------------------------
def lire_performance(chemin_brain: str) -> dict:
    """Lit niveau et maîtrise DANS le cerveau — jamais recalculés."""
    import torch
    ck = torch.load(chemin_brain, map_location="cpu", weights_only=False)
    hist = ck.get("historique_episodes_niveau", []) or []
    reussites = [1.0 if r else 0.0 for r in hist]
    return {
        "niveau": ck.get("niveau_actuel", None),
        "maitrise": (100.0 * sum(reussites) / len(reussites)) if reussites else None,
        "n_episodes": len(reussites),
        "dim_bus": ck.get("dim_bus", None),
        "jour": ck.get("jour", None),
    }


# --- 3. STATISTIQUES ------------------------------------------------------------------
def pearson(xs: list[float], ys: list[float]) -> tuple[float, float, int]:
    """r de Pearson, son t de Student, et n. Retourne (nan, nan, n) si dégénéré."""
    paires = [(x, y) for x, y in zip(xs, ys)
              if x is not None and y is not None
              and not math.isnan(x) and not math.isnan(y)]
    n = len(paires)
    if n < 3:
        return float("nan"), float("nan"), n
    mx = sum(p[0] for p in paires) / n
    my = sum(p[1] for p in paires) / n
    sxy = sum((p[0] - mx) * (p[1] - my) for p in paires)
    sxx = sum((p[0] - mx) ** 2 for p in paires)
    syy = sum((p[1] - my) ** 2 for p in paires)
    if sxx <= 0 or syy <= 0:          # variable CONSTANTE : rien à corréler
        return float("nan"), float("nan"), n
    r = sxy / math.sqrt(sxx * syy)
    r = max(-0.999999, min(0.999999, r))
    t = r * math.sqrt((n - 2) / (1 - r * r))
    return r, t, n


def ecart_type(xs: list[float]) -> float:
    xs = [x for x in xs if x is not None and not math.isnan(x)]
    if len(xs) < 2:
        return float("nan")
    m = sum(xs) / len(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))


# --- 4. PROGRAMME ---------------------------------------------------------------------
def main() -> None:
    p = argparse.ArgumentParser(description="Le ratio monde/interne prédit-il la performance ?")
    p.add_argument("--dossier", required=True, help="dossier de la cohorte (.brain)")
    p.add_argument("--niveau", type=int, default=3, help="niveau forcé (3 = le plafond)")
    p.add_argument("--jours", type=int, default=2)
    p.add_argument("--bras", default="A_", help="préfixe du bras à lire (A_ ou B_)")
    p.add_argument("--sortie", default=None, help="chemin du JSON de résultats")
    a = p.parse_args()

    # Doublons de copie Finder (« X 2.brain ») exclus : ce sont les MÊMES runs.
    cerveaux = sorted(c for c in glob.glob(os.path.join(a.dossier, f"{a.bras}*.brain"))
                      if not re.search(r" \d+\.brain$", c))
    if not cerveaux:
        print(f"❌ aucun cerveau '{a.bras}*.brain' dans {a.dossier}")
        sys.exit(1)

    scratch = os.path.join(a.dossier if os.path.isdir(a.dossier) else ".", "_scratch_cohorte")
    os.makedirs(scratch, exist_ok=True)

    print("=" * 100)
    print(f"  COHORTE DU BARÈME — {len(cerveaux)} cerveaux, bras '{a.bras}', "
          f"niveau {a.niveau}, {a.jours} jour(s)")
    print("=" * 100)
    print(f"\n  {'cerveau':16s} {'niv':>4s} {'maîtrise':>9s} "
          f"{'part_monde':>11s} {'part_curio':>11s} {'part_stagn':>11s} {'solde':>9s}")
    print("  " + "-" * 84)

    lignes = []
    for chemin in cerveaux:
        nom = os.path.basename(chemin).replace(".brain", "")
        try:
            perf = lire_performance(chemin)
        except Exception as exc:
            print(f"  {nom:16s}  ❌ lecture impossible : {type(exc).__name__}")
            continue
        mes = mesurer_un(chemin, a.niveau, a.jours, scratch)
        if mes is None:
            print(f"  {nom:16s}  ❌ sonde muette")
            continue
        rec = {"nom": nom, **perf, **{k: v for k, v in mes.items() if k != "termes"}}
        lignes.append(rec)
        mtr = f"{perf['maitrise']:8.2f}%" if perf["maitrise"] is not None else "      n/a"
        print(f"  {nom:16s} {str(perf['niveau']):>4s} {mtr} "
              f"{100*mes['part_monde']:10.2f}% {100*mes['part_curio']:10.2f}% "
              f"{100*mes['part_stagn']:10.2f}% {mes['solde']:9.4f}")

    if len(lignes) < 3:
        print("\n❌ trop peu de cerveaux lus — aucune statistique possible.")
        sys.exit(1)

    # --- LE TEST PRÉALABLE : la variable indépendante VARIE-T-ELLE ? ---
    # Sans variation, aucune corrélation n'existe. C'est le piège de l'ablation vide
    # (bit de portage v41.33, 16 runs perdus) : vérifier AVANT de corréler.
    pm = [l["part_monde"] for l in lignes]
    sd = ecart_type(pm)
    print("\n" + "=" * 100)
    print("  TEST PRÉALABLE — la part du monde varie-t-elle entre cerveaux ?")
    print("=" * 100)
    print(f"  moyenne {100*sum(pm)/len(pm):.3f}%   écart-type {100*sd:.3f} pt   "
          f"min {100*min(pm):.3f}%   max {100*max(pm):.3f}%")
    if sd < 1e-9:
        print("\n  ⚠️  MESURE VIDE : la part du monde est CONSTANTE sur toute la cohorte.")
        print("      Aucune corrélation n'est calculable — ce n'est PAS un résultat négatif.")
    else:
        print(f"  ✅ la variable varie (étendue {100*(max(pm)-min(pm)):.3f} pt) — "
              f"la corrélation a un sens.")

    # --- LES CORRÉLATIONS ---
    metriques = [("maitrise", "maîtrise (%)"), ("niveau", "niveau atteint")]
    predicteurs = [("part_monde", "part du MONDE"), ("part_curio", "part CURIOSITÉ"),
                   ("part_stagn", "part STAGNATION"), ("solde", "solde net")]
    n_tests = len(metriques) * len(predicteurs)
    df = len(lignes) - 2
    # Bonferroni bilatéral, p = 0,05 / n_tests — approximation normale (df ≥ 18).
    from statistics import NormalDist
    seuil = NormalDist().inv_cdf(1 - 0.05 / (2 * n_tests))

    print("\n" + "=" * 100)
    print(f"  CORRÉLATIONS — {n_tests} tests, seuil de Bonferroni |t| ≥ {seuil:.2f} (df={df})")
    print("=" * 100)
    print(f"  {'prédicteur':20s} {'métrique':16s} {'r':>9s} {'t':>8s} {'n':>4s}  verdict")
    print("  " + "-" * 84)

    resultats = []
    for pk, plab in predicteurs:
        for mk, mlab in metriques:
            xs = [l.get(pk) for l in lignes]
            ys = [float(l[mk]) if l.get(mk) is not None else None for l in lignes]
            r, t, n = pearson(xs, ys)
            if math.isnan(r):
                verdict = "⚠️  dégénéré (variable constante)"
            elif abs(t) >= seuil:
                verdict = "🔴 SIGNIFICATIF (Bonferroni)"
            elif abs(t) >= 2.0:
                verdict = "🟠 |t|≥2 mais ÉCHOUE Bonferroni"
            else:
                verdict = "✅ non significatif"
            print(f"  {plab:20s} {mlab:16s} {r:9.4f} {t:8.2f} {n:4d}  {verdict}")
            resultats.append({"predicteur": pk, "metrique": mk,
                              "r": None if math.isnan(r) else r,
                              "t": None if math.isnan(t) else t, "n": n})

    sortie = a.sortie or os.path.join(a.dossier, f"cohorte_bareme_niv{a.niveau}_{a.bras.strip('_')}.json")
    with open(sortie, "w", encoding="utf-8") as f:
        json.dump({"cerveaux": lignes, "correlations": resultats,
                   "seuil_bonferroni": seuil, "n_tests": n_tests,
                   "ecart_type_part_monde": sd,
                   "niveau": a.niveau, "jours": a.jours, "bras": a.bras}, f,
                  ensure_ascii=False, indent=2)
    print(f"\n  📄 résultats : {sortie}")
    shutil.rmtree(scratch, ignore_errors=True)
    print("=" * 100)


if __name__ == "__main__":
    main()
