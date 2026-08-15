"""Analyse une campagne v41.4 : heritage de sevrage ON vs OFF, memes graines.

Ne decide rien : imprime les chiffres et les tests qui permettent de decider.
Lit les logs console (pas W&B) pour rester utilisable hors ligne.
"""
import re, sys, glob, os
from statistics import mean, median

RE_JOUR   = re.compile(r"^🌙 Jour (\d+)")
RE_NIVEAU = re.compile(r"Niveau (\d+)/(\d+)")
RE_PROMO  = re.compile(r"\[PROMOTION\]")
RE_MAT    = re.compile(r"Maturité v40\.2 : 🌡️ ([\d.]+)")
RE_MAITR  = re.compile(r"maîtrise (\d+)% \(n=")
# NB : la ligne de bilan finit par « autonomie 28% » SANS parenthèse fermante ; la ligne
# de promotion, elle, en a une. Exiger `%\)` ne captait donc que les promotions — et
# affichait « autonomie 0,0 % » sur des runs où elle valait 28 %.
RE_AUTO   = re.compile(r"autonomie (\d+)%")
RE_SEV    = re.compile(r"sevrage sur (\d+)%")
RE_HERIT  = re.compile(r"héritage ([+-]\d+)%")
RE_PARENT = re.compile(r"parenté carte (\d+)%")
RE_VICT   = re.compile(r"Victoires?\s*:?\s*(\d+)", re.I)

def lire(path):
    r = {"jours": 0, "niveau_max": 1, "niveau_fin": 1, "promotions": 0,
         "maturites": [], "maitrises": [], "autonomies": [], "heritages": [],
         "parentes": [], "jour_promo": [], "sevrages": []}
    jour = 0
    with open(path, errors="ignore") as f:
        for l in f:
            m = RE_JOUR.match(l)
            if m:
                jour = int(m.group(1)); r["jours"] = max(r["jours"], jour); continue
            if RE_PROMO.search(l):
                r["promotions"] += 1; r["jour_promo"].append(jour); continue
            m = RE_NIVEAU.search(l)
            if m:
                n = int(m.group(1))
                r["niveau_fin"] = n; r["niveau_max"] = max(r["niveau_max"], n)
            m = RE_MAT.search(l)
            if m: r["maturites"].append(float(m.group(1)))
            m = RE_MAITR.search(l)
            if m: r["maitrises"].append(int(m.group(1)))
            m = RE_AUTO.search(l)
            if m: r["autonomies"].append(int(m.group(1)))
            m = RE_SEV.search(l)
            if m: r["sevrages"].append(int(m.group(1)))
            m = RE_HERIT.search(l)
            if m: r["heritages"].append(int(m.group(1)))
            m = RE_PARENT.search(l)
            if m: r["parentes"].append(int(m.group(1)))
    return r

def resume(rs, nom):
    if not rs:
        print(f"  {nom}: aucun run"); return None
    nivmax = [r["niveau_max"] for r in rs]
    promo  = [r["promotions"] for r in rs]
    matmax = [max(r["maturites"]) if r["maturites"] else 0.0 for r in rs]
    automoy= [mean(r["autonomies"]) if r["autonomies"] else 0.0 for r in rs]
    her    = [mean([abs(x) for x in r["heritages"]]) if r["heritages"] else 0.0 for r in rs]
    print(f"  {nom:8s} n={len(rs):2d} | niveau max: moy {mean(nivmax):.2f} med {median(nivmax):.1f} "
          f"max {max(nivmax)} | promotions: tot {sum(promo)} moy {mean(promo):.2f} "
          f"| maturite max moy {mean(matmax):.3f} | autonomie moy {mean(automoy):.1f}% "
          f"| heritage moy {mean(her):.1f}pt")
    return {"nivmax": nivmax, "promo": promo, "matmax": matmax,
            "automoy": automoy, "heritage": her}

def main(pattern_dir):
    print("=" * 100)
    print("CAMPAGNE v41.4 — heritage de sevrage : ON (v414) vs OFF (temoin), MEMES graines")
    print("=" * 100)
    groupes = {}
    for f in sorted(glob.glob(os.path.join(pattern_dir, "c414_*.log"))):
        b = os.path.basename(f)
        m = re.match(r"c414_(v414|temoin)_g(\d+)\.log", b)
        if not m: continue
        var, g = m.group(1), int(m.group(2))
        r = lire(f); r["graine"] = g
        groupes.setdefault(var, []).append(r)

    print("\n--- PAR RUN ---")
    print(f"  {'variante':9s} {'graine':>6s} {'jours':>6s} {'niv.max':>8s} {'promo':>6s} "
          f"{'mat.max':>8s} {'auto.moy':>9s} {'herit.moy':>10s}")
    for var in ("v414", "temoin"):
        for r in sorted(groupes.get(var, []), key=lambda x: x["graine"]):
            mm = max(r["maturites"]) if r["maturites"] else 0.0
            am = mean(r["autonomies"]) if r["autonomies"] else 0.0
            hm = mean([abs(x) for x in r["heritages"]]) if r["heritages"] else 0.0
            print(f"  {var:9s} {r['graine']:6d} {r['jours']:6d} {r['niveau_max']:8d} "
                  f"{r['promotions']:6d} {mm:8.3f} {am:8.1f}% {hm:9.1f}pt")

    print("\n--- AGREGE ---")
    a = resume(groupes.get("v414", []), "v41.4")
    b = resume(groupes.get("temoin", []), "temoin")

    if a and b and len(a["nivmax"]) == len(b["nivmax"]) and a["nivmax"]:
        print("\n--- COMPARAISON APPARIEE (meme graine des deux cotes) ---")
        gs = sorted([r["graine"] for r in groupes["v414"]])
        va = {r["graine"]: r for r in groupes["v414"]}
        vb = {r["graine"]: r for r in groupes["temoin"]}
        mieux = pire = egal = 0
        deltas = []
        for g in gs:
            if g not in vb: continue
            d = va[g]["niveau_max"] - vb[g]["niveau_max"]
            deltas.append(d)
            mieux += d > 0; pire += d < 0; egal += d == 0
            print(f"  g{g:<4d} v41.4 niv {va[g]['niveau_max']} vs temoin {vb[g]['niveau_max']}"
                  f"   delta {d:+d}   (promo {va[g]['promotions']} vs {vb[g]['promotions']})")
        print(f"\n  BILAN : v41.4 meilleur sur {mieux} graine(s), pire sur {pire}, egal sur {egal}")
        if deltas:
            print(f"  delta niveau moyen : {mean(deltas):+.2f}")
        # test des signes, sans scipy
        n = mieux + pire
        if n:
            from math import comb
            k = max(mieux, pire)
            p = sum(comb(n, i) for i in range(k, n + 1)) / (2 ** n) * 2
            print(f"  test des signes bilateral : n={n} k={k}  p ≈ {min(1.0, p):.3f}"
                  f"  {'-> NON significatif' if p > 0.05 else '-> significatif a 5%'}")
        else:
            print("  test des signes : aucune paire discordante (tous egaux)")

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
