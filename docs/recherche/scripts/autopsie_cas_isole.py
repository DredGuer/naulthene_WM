#!/usr/bin/env python3
"""AUTOPSIE D'UN CAS ISOLÉ — comprendre ce qui s'est passé dans UN cerveau (17/08/2026).

Écrit pour `esprit_g7`, le premier cerveau du projet à franchir le niveau 5 (LavaGap) et à
y vivre 151 jours. Le scanner de population (`scanner_cerveaux.py`) ne sait pas traiter un
cerveau unique ; celui-ci compare un sujet à ses **témoins appariés** (mêmes graine, mêmes
mondes, seules les lois A/B diffèrent) — la seule comparaison qui isole une cause.

Sept volets :
  1. ANATOMIE      — normes, myéline, plancher vital, neurogenèse par couche
  2. MÉTABOLISME   — énergie, vigueur, repas, zone critique (lu dans le log)
  3. CURSUS        — trajectoire de paliers, jours passés, maîtrise
  4. MÉMOIRE       — repères par carte, confirmations, empreinte de type apprise
  5. DANGER        — ce que l'agent a appris de la lave (valence, morts, thermoception)
  6. ARBITRAGE     — C1/C2 : amplitudes, entropies, accord, ratio
  7. DIFFÉRENTIEL  — sujet vs témoins, colonne par colonne

⚠️ Un cerveau isolé est une ANECDOTE (§4 de la règle de mesure). Ce script ne peut donc
établir aucun taux. Son rôle est de produire des HYPOTHÈSES falsifiables sur le mécanisme,
que seule une campagne à n ≥ 20 pourra confirmer.

Usage :
    PYTHONPATH=src python docs/recherche/scripts/autopsie_cas_isole.py \
        --sujet <brain> --sujet-log <log> [--temoin nom=<brain>:<log> ...]
"""
from __future__ import annotations
import argparse
import re
from collections import Counter
from pathlib import Path

import numpy as np
import torch

# --- Motifs de lecture des logs de nuit (format `executer_nuit`) ----------------------
P = {
    "niveau":    re.compile(r"Niveau (\d+)/15 — maîtrise (\d+)%"),
    "jour":      re.compile(r"^🌙 Jour (\d+) \[([^\]]+)\]", re.M),
    "energie":   re.compile(r"⚡ moy ([\d.]+) \(min ([\d.]+)\) \| 💪 vigueur moy ([\d.]+)"),
    "critique":  re.compile(r"ticks en zone critique : (\d+)/(\d+)"),
    "manger":    re.compile(r"🍽️ (\d+)/(\d+) ticks \([\d.]+%\) \| efficacité ([\d.]+)% \| récolté (\d+)"),
    "arbitrage": re.compile(r"C1=([\d.]+) C2=([\d.]+) \(ratio ([\d.]+)x\)[^|]*\| accord ([\d.]+)%"),
    "votes":     re.compile(r"entropie des votes — C1 ([\d.]+) \| C2 ([\d.]+)[^:]*: C1 (\d+), C2 (\d+)"),
    "cartes":    re.compile(r"🗺️ (\d+) carte\(s\) en mémoire \| 📍 (\d+) repère"),
    "empreinte": re.compile(r"🧬 (\d+) type\(s\) appris sur (\d+) expérience"),
    "victoire":  re.compile(r"🏆 (\d+) victoire\(s\) en (\d+) jour"),
    "jepa":      re.compile(r"Erreur JEPA moy: ([\d.]+)"),
    "thermo":    re.compile(r"🌡️ chaleur moy ([\d.]+)"),
    "haut":      re.compile(r"↑ '(\w+)' ([+-][\d.]+) \(×(\d+)\)"),
    "bas":       re.compile(r"↓ '(\w+)' ([+-][\d.]+) \(×(\d+)\)"),
}


def moy(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else 0.0


def lire_log(p: Path) -> dict:
    t = p.read_text(errors="replace")
    d = {"txt": t}
    niv = [(int(a), int(b)) for a, b in P["niveau"].findall(t)]
    jours = P["jour"].findall(t)
    d["n_nuits"] = len(jours)
    d["paliers"] = Counter(nom for _, nom in jours)
    d["niv_max"] = max((n for n, _ in niv), default=0)
    d["maitrise_fin"] = niv[-1][1] if niv else 0
    # trajectoire : premier jour de chaque palier
    d["premiere"] = {}
    for i, (n, _) in enumerate(niv):
        j = int(jours[i][0]) if i < len(jours) else i + 1
        d["premiere"].setdefault(n, j)
    en = P["energie"].findall(t)
    q = len(en) // 4 * 3            # dernier quart
    d["energie"] = moy([float(a) for a, _, _ in en[q:]])
    d["vigueur"] = moy([float(c) for _, _, c in en[q:]])
    cr = P["critique"].findall(t)
    d["critique"] = moy([int(a) / max(1, int(b)) for a, b in cr[q:]])
    mg = P["manger"].findall(t)
    d["recolte"] = moy([int(r) for _, _, _, r in mg[q:]])
    d["effic_manger"] = moy([float(e) for _, _, e, _ in mg[q:]])
    ar = P["arbitrage"].findall(t)
    d["c1"] = moy([float(a) for a, _, _, _ in ar[q:]])
    d["c2"] = moy([float(b) for _, b, _, _ in ar[q:]])
    d["ratio"] = moy([float(r) for _, _, r, _ in ar[q:]])
    d["accord"] = moy([float(x) for _, _, _, x in ar[q:]])
    vo = P["votes"].findall(t)
    d["ent_c1"] = moy([float(a) for a, _, _, _ in vo[q:]])
    d["ent_c2"] = moy([float(b) for _, b, _, _ in vo[q:]])
    d["nact_c1"] = moy([int(a) for _, _, a, _ in vo[q:]])
    d["nact_c2"] = moy([int(b) for _, _, _, b in vo[q:]])
    ca = P["cartes"].findall(t)
    d["cartes"] = moy([int(a) for a, _ in ca[q:]])
    d["reperes"] = moy([int(b) for _, b in ca[q:]])
    em = P["empreinte"].findall(t)
    d["types"] = moy([int(a) for a, _ in em[q:]])
    d["experiences"] = moy([int(b) for _, b in em[q:]])
    vi = P["victoire"].findall(t)
    d["victoires"] = int(vi[-1][0]) if vi else 0
    d["jepa"] = moy([float(x) for x in P["jepa"].findall(t)[q:]])
    d["valences"] = {n: (float(v), int(c)) for n, v, c in
                     P["haut"].findall(t)[-6:] + P["bas"].findall(t)[-6:]}
    return d


def anatomie(brain: Path) -> dict:
    from naulthene.cerveau.persistance import PersistanceAnatomique
    etat = PersistanceAnatomique(str(brain)).charger_ou_naitre()
    ag = etat.agent
    out = {"dim_bus": ag.dim_bus, "tick": etat.tick_absolu, "couches": {},
           "params": sum(p.numel() for p in ag.parameters()),
           "niveau": etat.niveau_actuel, "classe": etat.nom_classe,
           "dopamine": float(getattr(etat, "teneur_dopamine", 0.0)),
           "etat": etat, "agent": ag}
    for nom, m in ag.named_modules():
        if not hasattr(m, "annexe_weight"):
            continue
        b = m.base_weight.detach()
        my = m.myeline_M.detach()
        n = my.numel()
        out["couches"][nom] = {
            "forme": tuple(b.shape),
            "norme": float(b.norm()),
            "naissance": float(m.norme_naissance),
            # 10 % = PLANCHER_POIDS_VITAL : une couche collée là est morte cliniquement
            "ratio_naissance": float(b.norm() / max(1e-9, float(m.norme_naissance))),
            "myeline_max": float(my.max()),
            "myeline_p75": float(my.flatten().kthvalue(max(1, int(.75 * n))).values),
            "cristal": int(m.cristallisee.sum()) if hasattr(m, "cristallisee") else 0,
        }
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sujet", required=True)
    ap.add_argument("--sujet-log", required=True)
    ap.add_argument("--temoin", action="append", default=[],
                    help="nom=chemin.brain:chemin.log")
    args = ap.parse_args()

    suj_b, suj_l = Path(args.sujet), Path(args.sujet_log)
    tem = {}
    for spec in args.temoin:
        nom, chemins = spec.split("=", 1)
        b, l = chemins.split(":", 1)
        tem[nom] = (Path(b), Path(l))

    print("=" * 88)
    print(f"AUTOPSIE — {suj_b.name}")
    print("=" * 88)

    A = anatomie(suj_b)
    L = lire_log(suj_l)

    # ---------- 1. IDENTITÉ ----------
    print(f"\n{'─'*88}\n1. IDENTITÉ\n{'─'*88}")
    print(f"  bus {A['dim_bus']} dims | {A['params']:,} paramètres | tick absolu {A['tick']:,}")
    print(f"  niveau à la sauvegarde : {A['niveau']} ({A['classe']})")
    print(f"  dopamine : {A['dopamine']:.3f}/10 | nuits vécues : {L['n_nuits']}")

    # ---------- 2. CURSUS ----------
    print(f"\n{'─'*88}\n2. CURSUS — la trajectoire\n{'─'*88}")
    print(f"  niveau MAX atteint : {L['niv_max']}   maîtrise finale : {L['maitrise_fin']}%")
    print(f"  victoires cumulées : {L['victoires']}")
    print(f"\n  {'palier':<34}{'nuits':>8}{'part':>8}   premier jour")
    tot = sum(L["paliers"].values())
    for nom, n in L["paliers"].items():
        print(f"  {nom:<34}{n:>8}{n/max(1,tot):>7.0%}")
    print(f"\n  premier jour par niveau : " +
          "  ".join(f"n{k}→j{v}" for k, v in sorted(L["premiere"].items())))

    # ---------- 3. ANATOMIE ----------
    print(f"\n{'─'*88}\n3. ANATOMIE — état des couches")
    print(f"   ⚠️ ratio 0.10 = PLANCHER VITAL : la couche y est cliniquement morte.")
    print(f"   La myéline est le seul indicateur d'apprentissage (l'annexe est remise à 0")
    print(f"   chaque nuit par cycle_sommeil — un 0.000000 n'y prouve RIEN).\n{'─'*88}")
    print(f"  {'couche':<26}{'forme':>14}{'norme':>9}{'/naiss.':>9}"
          f"{'myél.max':>10}{'myél.p75':>10}{'cristal':>8}")
    for nom, c in A["couches"].items():
        alerte = " ⚠️" if c["ratio_naissance"] <= 0.105 else ""
        print(f"  {nom:<26}{str(c['forme']):>14}{c['norme']:>9.3f}"
              f"{c['ratio_naissance']:>9.3f}{c['myeline_max']:>10.6f}"
              f"{c['myeline_p75']:>10.6f}{c['cristal']:>8}{alerte}")
    au_plancher = [n for n, c in A["couches"].items() if c["ratio_naissance"] <= 0.105]
    print(f"\n  couches AU PLANCHER VITAL : {len(au_plancher)}/{len(A['couches'])}"
          + (f" → {', '.join(au_plancher)}" if au_plancher else ""))
    best = max(A["couches"].items(), key=lambda kv: kv[1]["myeline_max"])
    print(f"  couche la MIEUX myélinisée : {best[0]} ({best[1]['myeline_max']:.6f})")

    # ---------- 4. MÉTABOLISME ----------
    print(f"\n{'─'*88}\n4. MÉTABOLISME (moyennes du dernier quart)\n{'─'*88}")
    print(f"  énergie {L['energie']:.3f} | vigueur {L['vigueur']:.3f} | "
          f"zone critique {L['critique']:.0%} des ticks")
    print(f"  récolte {L['recolte']:.1f} ressource(s)/jour | "
          f"efficacité du geste manger {L['effic_manger']:.1f}%")

    # ---------- 5. MÉMOIRE & ABSTRACTION ----------
    print(f"\n{'─'*88}\n5. MÉMOIRE & ABSTRACTION\n{'─'*88}")
    print(f"  {L['cartes']:.1f} carte(s) en mémoire | {L['reperes']:.0f} repère(s) au total")
    print(f"  {L['types']:.0f} type(s) appris sur {L['experiences']:,.0f} expérience(s)")
    print(f"  erreur JEPA {L['jepa']:.4f}")
    if L["valences"]:
        print(f"\n  VALENCES APPRISES (aucune n'est déclarée — moyenne des chocs vécus) :")
        for n, (v, c) in sorted(L["valences"].items(), key=lambda kv: -kv[1][0]):
            print(f"    {n:<12} {v:+.3f}  (×{c:,})")

    # ---------- 6. ARBITRAGE ----------
    print(f"\n{'─'*88}\n6. ARBITRAGE C1/C2\n{'─'*88}")
    print(f"  C1 {L['c1']:.3f} | C2 {L['c2']:.3f} | ratio C2/C1 {L['ratio']:.3f}× | "
          f"accord {L['accord']:.1f}%")
    print(f"  entropie votes : C1 {L['ent_c1']:.3f} ({L['nact_c1']:.1f} actions) | "
          f"C2 {L['ent_c2']:.3f} ({L['nact_c2']:.1f} actions)")
    if L["ent_c1"] < 0.05 or L["ent_c2"] < 0.05:
        print(f"  ⚠️ une voix est FIGÉE — tout « accord » mesuré est un artefact (v41.14)")

    # ---------- 7. DIFFÉRENTIEL ----------
    if tem:
        print(f"\n{'─'*88}\n7. DIFFÉRENTIEL — sujet contre témoins appariés (même graine)\n{'─'*88}")
        lus = {n: lire_log(l) for n, (b, l) in tem.items()}
        ana = {n: anatomie(b) for n, (b, l) in tem.items()}
        cles = [("niveau max", "niv_max", "{:.0f}"), ("maîtrise fin %", "maitrise_fin", "{:.0f}"),
                ("victoires", "victoires", "{:.0f}"), ("énergie", "energie", "{:.3f}"),
                ("vigueur", "vigueur", "{:.3f}"), ("zone critique", "critique", "{:.0%}"),
                ("récolte/jour", "recolte", "{:.1f}"), ("ratio C2/C1", "ratio", "{:.3f}"),
                ("entropie C1", "ent_c1", "{:.3f}"), ("actions C1", "nact_c1", "{:.1f}"),
                ("repères mém.", "reperes", "{:.0f}"), ("types appris", "types", "{:.1f}"),
                ("erreur JEPA", "jepa", "{:.4f}")]
        noms = list(lus)
        print(f"  {'grandeur':<18}{'SUJET':>12}" + "".join(f"{n:>14}" for n in noms))
        for lbl, k, f in cles:
            ligne = f"  {lbl:<18}{f.format(L[k]):>12}"
            for n in noms:
                ligne += f"{f.format(lus[n][k]):>14}"
            print(ligne)
        print(f"\n  {'paramètres':<18}{A['params']:>12,}"
              + "".join(f"{ana[n]['params']:>14,}" for n in noms))
        print(f"  {'couches plancher':<18}"
              f"{sum(1 for c in A['couches'].values() if c['ratio_naissance']<=0.105):>12}"
              + "".join(f"{sum(1 for c in ana[n]['couches'].values() if c['ratio_naissance']<=0.105):>14}"
                        for n in noms))
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
