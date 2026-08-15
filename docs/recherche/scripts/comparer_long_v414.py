"""Comparaison APPARIEE des runs longs (2000 jours) : heritage ON vs OFF, memes graines.

Les runs `long414_g<N>.log`      portent l'heritage ACTIF.
Les runs `long414_temoin_g<N>.log` portent l'ablation `--sans-heritage`.

Meme graine, meme duree, meme code a un drapeau pres : c'est la seule
comparaison qui puisse trancher.
"""
import re, sys, glob, os
from statistics import mean

RE_JOUR = re.compile(r"^🌙 Jour (\d+)")
RE_NIV  = re.compile(r"Niveau (\d+)/(\d+)")
RE_PROM = re.compile(r"\[PROMOTION\]")
RE_MAT  = re.compile(r"🌡️ ([\d.]+)")
RE_MTR  = re.compile(r"maîtrise (\d+)%")
RE_AUTO = re.compile(r"autonomie (\d+)%")
RE_SEV  = re.compile(r"sevrage (\d+)%")
RE_HER  = re.compile(r"héritage ([+-]\d+)%")

def lire(p):
    d = {"jours":0,"niv_max":1,"promo":0,"jours_promo":[],
         "mat":[], "mtr":[], "auto":[], "sev":[], "her":[]}
    jour = 0
    with open(p, errors="ignore") as f:
        for l in f:
            m = RE_JOUR.match(l)
            if m: jour = int(m.group(1)); d["jours"] = max(d["jours"], jour); continue
            if RE_PROM.search(l): d["promo"] += 1; d["jours_promo"].append(jour); continue
            m = RE_NIV.search(l)
            if m: d["niv_max"] = max(d["niv_max"], int(m.group(1)))
            for rx, k in ((RE_MAT,"mat"),(RE_MTR,"mtr"),(RE_AUTO,"auto"),
                          (RE_SEV,"sev"),(RE_HER,"her")):
                m = rx.search(l)
                if m: d[k].append(float(m.group(1)))
    return d

def main(rep):
    print("=" * 96)
    print("RUNS LONGS 2000 JOURS — heritage ON vs OFF, MEMES graines")
    print("=" * 96)
    on, off = {}, {}
    for f in glob.glob(os.path.join(rep, "long414_g*.log")):
        g = int(re.search(r"long414_g(\d+)\.log", os.path.basename(f)).group(1))
        on[g] = lire(f)
    for f in glob.glob(os.path.join(rep, "long414_temoin_g*.log")):
        g = int(re.search(r"long414_temoin_g(\d+)\.log", os.path.basename(f)).group(1))
        off[g] = lire(f)

    graines = sorted(set(on) & set(off))
    if not graines:
        print("  (pas encore de paire complete)"); return

    print(f"\n{'graine':>6s} {'variante':>9s} {'jours':>6s} {'niv':>4s} {'promo':>6s} "
          f"{'j.promo':>12s} {'mat.max':>8s} {'mtr.max':>8s} {'auto.moy':>9s} {'sev.moy':>8s} {'her.moy':>8s}")
    for g in graines:
        for nom, d in (("HERITAGE", on[g]), ("temoin", off[g])):
            jp = ",".join(str(x) for x in d["jours_promo"][:3]) or "-"
            print(f"{g:6d} {nom:>9s} {d['jours']:6d} {d['niv_max']:4d} {d['promo']:6d} "
                  f"{jp:>12s} {(max(d['mat']) if d['mat'] else 0):8.3f} "
                  f"{(max(d['mtr']) if d['mtr'] else 0):7.0f}% "
                  f"{(mean(d['auto']) if d['auto'] else 0):8.1f}% "
                  f"{(mean(d['sev']) if d['sev'] else 0):7.1f}% "
                  f"{(mean([abs(x) for x in d['her']]) if d['her'] else 0):7.1f}pt")
        print()

    print("--- DELTA (heritage - temoin) ---")
    mieux = pire = egal = 0
    dn, dp = [], []
    for g in graines:
        a, b = on[g], off[g]
        d_niv = a["niv_max"] - b["niv_max"]
        d_pro = a["promo"] - b["promo"]
        dn.append(d_niv); dp.append(d_pro)
        mieux += d_niv > 0; pire += d_niv < 0; egal += d_niv == 0
        flag = "  <-- HERITAGE MIEUX" if d_niv > 0 else ("  <-- TEMOIN MIEUX" if d_niv < 0 else "")
        print(f"  g{g:<4d} delta niveau {d_niv:+d}   delta promotions {d_pro:+d}{flag}")
    print(f"\n  BILAN : heritage meilleur sur {mieux}, pire sur {pire}, egal sur {egal}")
    if dn: print(f"  delta niveau moyen : {mean(dn):+.2f}   delta promotions moyen : {mean(dp):+.2f}")
    n = mieux + pire
    if n:
        from math import comb
        k = max(mieux, pire)
        p = min(1.0, sum(comb(n,i) for i in range(k,n+1)) / (2**n) * 2)
        print(f"  test des signes : n={n} k={k}  p ≈ {p:.3f}"
              f"  {'-> NON significatif' if p > 0.05 else '-> significatif a 5%'}")
    else:
        print("  test des signes : aucune paire discordante")
        print("  ⚠️ verifier que l'heritage s'est REELLEMENT active (her.moy > 0 cote HERITAGE)")

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
