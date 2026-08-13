"""Analyse de la campagne v37→v39 : test des signes sur graines appariées."""
import glob
import json
import statistics
from collections import defaultdict
from itertools import combinations
from math import comb

REF = "base"


def charger():
    d = defaultdict(dict)
    for f in glob.glob("v3739_*.json"):
        if "TOUS" in f:
            continue
        try:
            r = json.loads(open(f).read())
            d[r["condition"]][r["graine"]] = r
        except Exception:
            pass
    return d


def p_signes(deltas):
    """Test des signes bilatéral, en ignorant les ex aequo."""
    pos = sum(1 for x in deltas if x > 0)
    neg = sum(1 for x in deltas if x < 0)
    n = pos + neg
    if n == 0:
        return 1.0, pos, neg
    k = min(pos, neg)
    p = sum(comb(n, i) for i in range(k + 1)) / (2 ** n) * 2
    return min(1.0, p), pos, neg


def main():
    d = charger()
    if REF not in d:
        print("pas encore de runs `base`")
        return

    print("=" * 78)
    print("VALIDATION v37 → v39   (réarmement CORRIGÉ — non comparable aux chiffres v38)")
    print("=" * 78)

    # --- 1. Santé : la promesse centrale de la v37 ---
    print("\n1. SANTÉ SYNAPTIQUE  (promesse v37 : 0 synapse morte)")
    print(f"   {'condition':12s} {'runs':>5s} {'morts max':>10s} {'plancher méd.':>14s}")
    for c in sorted(d):
        rs = list(d[c].values())
        morts = [r.get("synapses_mortes", 0) for r in rs]
        plan = [r.get("couches_au_plancher", 0) for r in rs]
        n_c = rs[0].get("n_couches", "?")
        print(f"   {c:12s} {len(rs):5d} {max(morts):10d} "
              f"{statistics.median(plan):9.1f}/{n_c}")

    # --- 2. Mémoire : la promesse v39 ---
    print("\n2. MÉMOIRE  (promesse v39 : l'empreinte survit, les repères `goal` aussi)")
    print(f"   {'condition':12s} {'empreinte':>10s} {'souvenirs':>10s} {'goal':>6s}")
    for c in sorted(d):
        rs = list(d[c].values())
        print(f"   {c:12s} "
              f"{statistics.median([r.get('empreinte_types',0) for r in rs]):10.1f} "
              f"{statistics.median([r.get('souvenirs',0) for r in rs]):10.1f} "
              f"{statistics.median([r.get('reperes_goal',0) for r in rs]):6.1f}")

    # --- 3. Performance appariée ---
    print("\n3. PERFORMANCE  (chaque condition contre `base`, graines appariées)")
    print(f"   {'condition':12s} {'paliers méd.':>13s} {'vict. méd.':>11s} "
          f"{'écarts paliers':>22s} {'p':>7s}")
    base = d[REF]
    for c in sorted(d):
        rs = d[c]
        communes = sorted(set(rs) & set(base))
        if not communes:
            continue
        niv = [rs[g]["niveau_final"] for g in communes]
        vic = [rs[g]["victoires"] for g in communes]
        if c == REF:
            print(f"   {c:12s} {statistics.median(niv):13.1f} "
                  f"{statistics.median(vic):11.1f} {'(référence)':>22s} {'—':>7s}")
            continue
        deltas = [rs[g]["niveau_final"] - base[g]["niveau_final"] for g in communes]
        p, pos, neg = p_signes(deltas)
        txt = ",".join(f"{x:+d}" for x in deltas)
        print(f"   {c:12s} {statistics.median(niv):13.1f} "
              f"{statistics.median(vic):11.1f} {txt:>22s} {p:7.3f}")

    # --- 4. Vitesse post-promotion ---
    print("\n4. VITESSE POST-PROMOTION  (jours avant la 1re victoire sur un palier neuf)")
    print(f"   {'condition':12s} {'délai médian':>13s}   (plus bas = mieux)")
    for c in sorted(d):
        vals = [r["delai_median"] for r in d[c].values() if r.get("delai_median") is not None]
        if vals:
            print(f"   {c:12s} {statistics.median(vals):13.1f}   (n={len(vals)})")
        else:
            print(f"   {c:12s} {'—':>13s}   (aucune promotion suivie de victoire)")

    print("\n" + "=" * 78)
    print("LECTURE : `sans_X` MOINS bon que `base` ⇒ la mécanique X APPORTE quelque chose.")
    print("          `sans_X` égal ou meilleur   ⇒ elle ne se justifie pas (encore).")
    print("=" * 78)


if __name__ == "__main__":
    main()
