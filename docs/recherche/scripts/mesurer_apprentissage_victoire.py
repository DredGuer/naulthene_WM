"""Q3 — Que change une victoire ? (nuit du 15/08/2026)

Le projet mesure des taux de réussite, jamais ce que l'agent RETIRE d'une victoire.
Trois mesures, de la plus directe à la plus profonde :

  A. COMPORTEMENT — l'agent réussit-il MIEUX juste après une victoire qu'après un échec ?
     (compare les N épisodes suivant une victoire à ceux suivant un échec)

  B. VITESSE — les victoires deviennent-elles plus rapides au fil du run ?
     Un agent qui apprend une carte doit la résoudre en moins de ticks.

  C. INDÉPENDANCE — la suite de victoires/échecs est-elle distinguable d'un tirage
     à pile ou face de même moyenne ? Si non, il n'y a AUCUNE mémoire d'un épisode
     à l'autre : chaque épisode est rejoué comme si c'était le premier.

Lit les logs console (`Cursus` + `Victoires`), pas les .brain : c'est le comportement
qui compte, pas les poids.
"""
import re, sys, glob, os
from statistics import mean, stdev

RE_JOUR = re.compile(r"^🌙 Jour (\d+)")
RE_MAITRISE = re.compile(r"maîtrise (\d+)% \(n=(\d+)\)")
RE_VICT = re.compile(r"(\d+) victoire", re.I)


def serie_maitrise(path):
    """Suite (jour, maîtrise) — la maîtrise EST la moyenne glissante des 20 derniers."""
    out = []
    jour = 0
    for l in open(path, errors="ignore"):
        m = RE_JOUR.match(l)
        if m:
            jour = int(m.group(1))
            continue
        m = RE_MAITRISE.search(l)
        if m:
            out.append((jour, int(m.group(1)) / 100.0, int(m.group(2))))
    return out


def analyser(path):
    nom = os.path.basename(path)[:-4]
    serie = serie_maitrise(path)
    if len(serie) < 50:
        print(f"  {nom}: trop court"); return

    taux = [t for _, t, _ in serie]

    # B. TENDANCE — la maîtrise progresse-t-elle sur la durée du run ?
    tiers = len(taux) // 3
    debut, fin = mean(taux[:tiers]), mean(taux[-tiers:])

    # C. AUTOCORRÉLATION à 1 pas sur la maîtrise différenciée.
    # Si l'agent apprend, une bonne journée en annonce une autre (corrélation > 0).
    # Sur du bruit pur, la différenciée est anticorrélée à ~-0.5.
    d = [taux[i+1] - taux[i] for i in range(len(taux)-1)]
    if len(d) > 10 and stdev(d) > 1e-9:
        md = mean(d)
        num = sum((d[i]-md)*(d[i+1]-md) for i in range(len(d)-1))
        den = sum((x-md)**2 for x in d)
        r1 = num/den if den else 0.0
    else:
        r1 = float("nan")

    print(f"  {nom:16s} maîtrise {debut:.0%} → {fin:.0%} ({fin-debut:+.0%})  "
          f"max {max(taux):.0%}  autocorr(Δ) {r1:+.3f}")
    return {"nom": nom, "debut": debut, "fin": fin, "max": max(taux), "r1": r1}


def main(rep):
    print("Q3 — QUE CHANGE UNE VICTOIRE ? Progression de la maîtrise sur le run\n")
    print("  Lecture : « maîtrise début → fin » sur les tiers extrêmes du run.")
    print("  autocorr(Δ) proche de -0.5 = bruit pur (aucune mémoire d'un jour à l'autre).\n")
    res = []
    for f in sorted(glob.glob(os.path.join(rep, "p17_g*.log"))):
        r = analyser(f)
        if r: res.append(r)
    if res:
        print(f"\n  MOYENNE : {mean(r['debut'] for r in res):.1%} → "
              f"{mean(r['fin'] for r in res):.1%} "
              f"({mean(r['fin']-r['debut'] for r in res):+.1%})")
        print(f"  autocorr moyenne : {mean(r['r1'] for r in res):+.3f}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
