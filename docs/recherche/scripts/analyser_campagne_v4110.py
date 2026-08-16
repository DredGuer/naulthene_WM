#!/usr/bin/env python3
"""Analyse la campagne A/B v41.10 (mémoire par carte) — avec intervalles de Wilson.

Règle de mesure du projet : jamais un taux sans son intervalle de confiance, jamais une
conclusion sous 20 graines. Ce script refuse donc de conclure si l'un des deux bras est
sous-échantillonné, et affiche systématiquement le recouvrement des intervalles.

    PYTHONPATH=src python docs/recherche/scripts/analyser_campagne_v4110.py [/tmp/campagne_v4110]
"""
from __future__ import annotations
import math
import re
import sys
from pathlib import Path

RE_JOUR = re.compile(r"🌙 Jour (\d+) \[([^\]]+)\]")
RE_CURSUS = re.compile(r"Cursus\s+:.*Niveau (\d+)/15 — maîtrise (\d+)%")
RE_CARTES = re.compile(r"Cartes v41\.10\s+:.*🗺️ (\d+) carte.*📍 (\d+) repère.*🔙 (\d+) retrouvée")
RE_CONF = re.compile(r"Mémoire v36\s+:.*🔁 ([\d.]+) confirmation")
RE_PROMO = re.compile(r"🎓 \[PROMOTION\]")


def wilson(succes: int, total: int, z: float = 1.96) -> tuple[float, float, float]:
    """Intervalle de Wilson à 95 % — jamais l'approximation normale (fausse aux extrêmes)."""
    if total == 0:
        return 0.0, 0.0, 1.0
    p = succes / total
    d = 1 + z * z / total
    centre = (p + z * z / (2 * total)) / d
    demi = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / d
    return p, max(0.0, centre - demi), min(1.0, centre + demi)


def lire(chemin: Path) -> dict | None:
    try:
        texte = chemin.read_text(errors="replace")
    except OSError:
        return None
    jours = RE_JOUR.findall(texte)
    if not jours:
        return None
    cursus = RE_CURSUS.findall(texte)
    cartes = RE_CARTES.findall(texte)
    confs = RE_CONF.findall(texte)
    niveaux = [int(n) for n, _ in cursus]
    return {
        "jours": int(jours[-1][0]),
        "niveau_final": niveaux[-1] if niveaux else 0,
        "niveau_max": max(niveaux) if niveaux else 0,
        "maitrise_finale": int(cursus[-1][1]) if cursus else 0,
        "promotions": len(RE_PROMO.findall(texte)),
        "cartes": int(cartes[-1][0]) if cartes else 0,
        "reperes": int(cartes[-1][1]) if cartes else 0,
        "retrouvees": int(cartes[-1][2]) if cartes else 0,
        "confirmations": float(confs[-1]) if confs else 0.0,
    }


def moyenne(valeurs):
    return sum(valeurs) / len(valeurs) if valeurs else 0.0


def main() -> int:
    racine = Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/campagne_v4110")
    logs = racine / "logs"
    if not logs.is_dir():
        print(f"introuvable : {logs}")
        return 1

    bras = {"temoin": [], "variante": []}
    for nom in bras:
        for f in sorted(logs.glob(f"{nom}_g*.log")):
            r = lire(f)
            if r:
                r["graine"] = f.stem.split("_g")[-1]
                bras[nom].append(r)

    print("=" * 78)
    print("CAMPAGNE v41.10 — la mémoire par carte sert-elle à quelque chose ?")
    print("  témoin   = --sans-memoire-cartes (la bascule EFFACE, v41.9)")
    print("  variante = par défaut            (la bascule ARCHIVE, v41.10)")
    print("=" * 78)

    for nom, runs in bras.items():
        if not runs:
            print(f"\n{nom.upper()} : aucun run terminé")
            continue
        n = len(runs)
        jours_moy = moyenne([r["jours"] for r in runs])
        print(f"\n{nom.upper()} — {n} run(s), {jours_moy:.0f} jours en moyenne")
        print(f"  niveau max atteint  : {moyenne([r['niveau_max'] for r in runs]):.2f} "
              f"(max absolu {max(r['niveau_max'] for r in runs)})")
        print(f"  maîtrise finale     : {moyenne([r['maitrise_finale'] for r in runs]):.1f} %")
        print(f"  promotions          : {moyenne([r['promotions'] for r in runs]):.2f}")
        print(f"  cartes en mémoire   : {moyenne([r['cartes'] for r in runs]):.1f}")
        print(f"  repères au total    : {moyenne([r['reperes'] for r in runs]):.1f}")
        print(f"  cartes retrouvées   : {moyenne([r['retrouvees'] for r in runs]):.0f}")
        print(f"  confirmations/repère: {moyenne([r['confirmations'] for r in runs]):.2f}")

    # --- Le critère principal, avec son intervalle ---
    print("\n" + "-" * 78)
    print("TAUX D'ATTEINTE PAR NIVEAU (Wilson 95 %)")
    print("-" * 78)
    niveau_ref = 3
    for seuil in (2, 3, 4):
        ligne = f"  niveau ≥ {seuil} : "
        bornes = {}
        for nom, runs in bras.items():
            if not runs:
                continue
            s = sum(1 for r in runs if r["niveau_max"] >= seuil)
            p, lo, hi = wilson(s, len(runs))
            bornes[nom] = (lo, hi)
            ligne += f"{nom} {p:5.0%} [{lo:.0%}–{hi:.0%}] (n={len(runs)})   "
        print(ligne)
        if len(bornes) == 2:
            a, b = bornes["temoin"], bornes["variante"]
            recouvre = not (a[1] < b[0] or b[1] < a[0])
            print(f"      → intervalles {'QUI SE RECOUVRENT — aucun effet démontré' if recouvre else 'DISJOINTS — effet réel'}")

    n_min = min((len(r) for r in bras.values() if r), default=0)
    print("\n" + "=" * 78)
    if n_min < 20:
        print(f"⚠️  {n_min} graine(s) par bras — INSUFFISANT pour conclure (minimum 20).")
        print("    Les chiffres ci-dessus sont descriptifs, pas concluants.")
    else:
        print("✅ 20 graines par bras : la comparaison est recevable.")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
