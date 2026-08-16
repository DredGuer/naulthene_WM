"""Analyse d'une campagne longue : taux de franchissement + intervalles de confiance.

Applique la Regle de Mesure (CLAUDE.md) : jamais un taux sans son intervalle,
et distinction explicite entre ce que l'echantillon permet d'affirmer ou non.
"""
import re, sys, glob, os
from statistics import mean, median

RE_JOUR = re.compile(r"^🌙 Jour (\d+)")
RE_NIV = re.compile(r"Niveau (\d+)/15")
RE_PROMO = re.compile(r"\[PROMOTION\]")
RE_MAITRISE = re.compile(r"maîtrise (\d+)%")


def wilson(k, n, z=1.96):
    """Intervalle de confiance de Wilson — correct meme sur petits echantillons."""
    if n == 0:
        return 0.0, 0.0, 0.0
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / d
    return p, max(0.0, c - h), min(1.0, c + h)


def lire(path):
    jour = 0
    niv_max = 1
    promos = []
    maitrises = []
    for l in open(path, errors="ignore"):
        m = RE_JOUR.match(l)
        if m:
            jour = int(m.group(1))
            continue
        if RE_PROMO.search(l):
            promos.append(jour)
            continue
        m = RE_NIV.search(l)
        if m:
            niv_max = max(niv_max, int(m.group(1)))
        m = RE_MAITRISE.search(l)
        if m:
            maitrises.append(int(m.group(1)))
    return {"jours": jour, "niveau_max": niv_max, "promotions": promos,
            "maitrise_max": max(maitrises) if maitrises else 0}


def main(rep, motif="j16_g*.log"):
    runs = {}
    for f in sorted(glob.glob(os.path.join(rep, motif))):
        g = re.search(r"_g(\d+)\.log", os.path.basename(f))
        if g:
            runs[int(g.group(1))] = lire(f)
    if not runs:
        print("aucun run"); return

    print("=" * 78)
    print(f" CAMPAGNE — {len(runs)} graines")
    print("=" * 78)
    print(f"\n  {'graine':>7s} {'jours':>7s} {'niv':>4s} {'promos':>7s} {'jours de promotion':>26s}")
    for g in sorted(runs):
        r = runs[g]
        jp = ", ".join(str(x) for x in r["promotions"][:4]) or "—"
        print(f"  g{g:<6d} {r['jours']:7d} {r['niveau_max']:4d} {len(r['promotions']):7d} {jp:>26s}")

    n = len(runs)
    k1 = sum(1 for r in runs.values() if r["niveau_max"] >= 2)
    k2 = sum(1 for r in runs.values() if r["niveau_max"] >= 3)
    k3 = sum(1 for r in runs.values() if r["niveau_max"] >= 4)

    print(f"\n  --- TAUX (intervalle de Wilson a 95 %) ---")
    for lab, k in (("≥ 1 promotion (niveau 2+)", k1),
                   ("≥ 2 promotions (niveau 3+)", k2),
                   ("≥ 3 promotions (niveau 4+)", k3)):
        p, lo, hi = wilson(k, n)
        print(f"  {lab:28s} {k:2d}/{n} = {p:5.0%}   IC95 [{lo:.0%} ; {hi:.0%}]")

    tous = [j for r in runs.values() for j in r["promotions"]]
    if tous:
        print(f"\n  --- QUAND ---")
        print(f"  {len(tous)} promotions au total")
        print(f"  1re promotion : mediane j{median([r['promotions'][0] for r in runs.values() if r['promotions']]):.0f}")
        p2 = [r['promotions'][1] for r in runs.values() if len(r['promotions']) > 1]
        if p2:
            print(f"  2e promotion  : mediane j{median(p2):.0f}")

    print(f"\n  --- CE QUE L'ECHANTILLON PERMET ---")
    p, lo, hi = wilson(k2, n)
    largeur = hi - lo
    print(f"  Largeur de l'IC sur le niveau 3+ : ±{largeur/2:.0%}")
    print(f"  => un correctif doit deplacer le taux de plus de {largeur:.0%} pour etre")
    print(f"     detectable a n={n}. En dessous, il est indistinguable du bruit.")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".",
         sys.argv[2] if len(sys.argv) > 2 else "j16_g*.log")
