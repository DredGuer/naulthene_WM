#!/usr/bin/env python3
"""Depouillement de la campagne 07092026_branches_persistantes — les juges sont dans LISEZ_MOI.md.

Bras : **BP** (`--epoques-nuit 8 --branches-persistantes`, voix libre) vs **K8_NU**
(le meilleur régime connu du 06/09, réutilisé comme témoin — 0 run neuf).

Même méthode que `06092026_epoques_nuit/depouiller.py` (maîtrise = médiane des ~100
derniers jours du % affiché au bilan) + les juges spécifiques du LISEZ_MOI BP :
  J1 maîtrise appariée (+ retrait des 4 extrêmes)
  J2 niveau (apparié + Fisher sur le comptage ≥ 5)
  J3 ratio h7/h1 du rollout (mécaniste — mesure sur les 20 cerveaux BP, `rollout_h7h1/`,
     vs K8_NU mesuré le 07/09 dans `07092026_rollout_k8/`)
  J4 accord C1/C2 + ratio d'amplitude + garde-fou `gain_c1` (= 1,00 partout)
Seuil Bonferroni 3 métriques ⇒ t = 2,86 (pré-enregistré).
"""
import re, os, json, math, statistics as st
from math import comb

D = os.path.dirname(os.path.abspath(__file__))
K8_DIR = os.path.join(os.path.dirname(D), "06092026_epoques_nuit")
K8_ROLLOUT = os.path.join(os.path.dirname(D), "07092026_rollout_k8")
BP_ROLLOUT = os.path.join(D, "rollout_h7h1")

P_JOUR = re.compile(r'^🌙 Jour (\d+) ')
P_CURS = re.compile(r'Niveau (\d+)/15 — maîtrise (\d+)%')
P_ARB = re.compile(r'C1=([\d.]+) C2=([\d.]+).*?gain C1 ×([\d.]+)')
P_ACC = re.compile(r'accord ([\d.]+)%')
P_VICT = re.compile(r'🏆 (\d+) victoire\(s\)')
P_HC1 = re.compile(r'entropie des votes — C1 ([\d.]+)')


def lire(f):
    rows, cur = [], None
    for l in open(f, errors='ignore'):
        m = P_JOUR.match(l)
        if m:
            if cur:
                rows.append(cur)
            cur = {'j': int(m.group(1))}
            continue
        if cur is None:
            continue
        m = P_ARB.search(l)
        if m:
            cur.update(c1=float(m.group(1)), c2=float(m.group(2)), gain=float(m.group(3)))
        m = P_ACC.search(l)
        if m:
            cur['accord'] = float(m.group(1))
        m = P_VICT.search(l)
        if m:
            cur['vict'] = int(m.group(1))
        m = P_HC1.search(l)
        if m:
            cur['hc1'] = float(m.group(1))
        m = P_CURS.search(l)
        if m:
            cur.update(niv=int(m.group(1)), mait=int(m.group(2)))
    if cur:
        rows.append(cur)
    return [r for r in rows if 'niv' in r]


def med(rows, k, a, b):
    v = [r[k] for r in rows[a:b] if k in r]
    return st.median(v) if v else None


def tt(d):
    n = len(d)
    if n < 2:
        return 0.0, 0.0, n
    m, s = st.mean(d), st.stdev(d)
    return m, (0.0 if s == 0 else m / (s / math.sqrt(n))), n


def fisher_exact(a, b, c, d):
    """Test exact de Fisher bilatéral sur la table [[a, b], [c, d]]."""
    n = a + b + c + d
    def p_obs(x):
        return (comb(a + b, x) * comb(c + d, a + c - x)) / comb(n, a + c)
    lo, hi = max(0, a - d), min(a + b, a + c)
    p0 = p_obs(a)
    return sum(p_obs(x) for x in range(lo, hi + 1) if p_obs(x) <= p0 + 1e-15)


GRAINES = [11, 22, 33, 44, 55, 66, 77, 88, 99, 111, 122, 133,
           144, 155, 166, 177, 188, 199, 211, 222]
BRAS = {'BP': (D, 'BP'), 'K8_NU': (K8_DIR, 'K8_NU')}

E, manquants = {}, []
for b, (dossier, prefixe) in BRAS.items():
    for g in GRAINES:
        f = os.path.join(dossier, f'{prefixe}_g{g}.log')
        if not os.path.exists(f):
            manquants.append(f'{b}_g{g}')
            continue
        r = lire(f)
        if not r:
            manquants.append(f'{b}_g{g} (vide)')
            continue
        if r[-1]['j'] < 1500:
            manquants.append(f'{b}_g{g} (INACHEVE {r[-1]["j"]}/1500)')
            continue
        E[f'{b}_g{g}'] = dict(niv=r[-1]['niv'], mait=med(r, 'mait', -100, None),
                              gain=med(r, 'gain', -100, None), c1=med(r, 'c1', -100, None),
                              c2=med(r, 'c2', -100, None),
                              accord=med(r, 'accord', -100, None),
                              hc1=med(r, 'hc1', -100, None),
                              vict=r[-1].get('vict', 0), nuits=len(r))

print(f"=== COUVERTURE === {len(E)}/40 runs"
      + (f"  MANQUANTS: {manquants}" if manquants else ""))

# Ratio h7/h1 du rollout — BP mesuré ici, K8_NU mesuré le 07/09.
ROLL = {}
for b, dossier in (('BP', BP_ROLLOUT), ('K8_NU', K8_ROLLOUT)):
    for g in GRAINES:
        f = os.path.join(dossier, f'{b}_g{g}.json' if b == 'BP'
                         else f'K8_NU_g{g}.json')
        if os.path.exists(f):
            ROLL[f'{b}_g{g}'] = json.load(open(f))['ratio_h7_sur_h1']
        else:
            manquants.append(f'rollout {b}_g{g}')

print("\n=== JUGE 4 (GARDE-FOU) — le régime est-il le même partout ? (gain_c1 ≈ 1,00) ===")
ok = True
for b in BRAS:
    v = [E[f'{b}_g{g}']['gain'] for g in GRAINES if f'{b}_g{g}' in E]
    if not v:
        continue
    m = st.mean(v)
    bon = abs(m - 1.0) < 0.02
    ok &= bon
    print(f"  {b:10} gain_c1 moyen {m:.4f}  (attendu 1,00 — voix libre)  {'OK' if bon else '!! ECHEC'}")
print(f"  => {'garde-fou PASSE' if ok else 'CAMPAGNE INVALIDE'}")


def apparie(a, b, var, label, sig=True):
    d = [E[f'{a}_g{g}'][var] - E[f'{b}_g{g}'][var]
         for g in GRAINES if f'{a}_g{g}' in E and f'{b}_g{g}' in E]
    if not d:
        return None
    m, t, n = tt(d)
    fav = sum(1 for x in d if x > 0)
    seuil = 2.86 if sig else 1.96
    print(f"  {label:34} d = {m:+8.3f}  t = {t:+6.2f}  "
          f"{'SIG' if abs(t) > seuil else 'NS':3}  ({fav}/{n})")
    d2 = sorted(d, key=abs)[:-4]
    if len(d2) >= 3:
        m2, t2, n2 = tt(d2)
        print(f"  {'  -> sans les 4 extremes':34} d = {m2:+8.3f}  t = {t2:+6.2f}  "
              f"{'SIG' if abs(t2) > seuil else 'NS':3}  (n={n2})")
    return d


print("\n=== JUGE 1 — MAITRISE (BP - K8_NU, apparié) ===")
d1 = apparie('BP', 'K8_NU', 'mait', 'maîtrise')

print("\n=== JUGE 2 — NIVEAU (BP - K8_NU) ===")
d2 = apparie('BP', 'K8_NU', 'niv', 'niveau (apparié)')
if d2 is not None:
    nplus = sum(1 for x in d2 if x > 0)
    nmoins = sum(1 for x in d2 if x < 0)
    print(f"  signe : {nplus} BP > K8_NU · {nmoins} BP < K8_NU · "
          f"{len(d2) - nplus - nmoins} égaux")
bp5 = sum(1 for g in GRAINES if E.get(f'BP_g{g}', {}).get('niv', 0) >= 5)
k85 = sum(1 for g in GRAINES if E.get(f'K8_NU_g{g}', {}).get('niv', 0) >= 5)
p = fisher_exact(bp5, 20 - bp5, k85, 20 - k85)
print(f"  Fisher (comptage ≥ 5) : BP {bp5}/20 vs K8_NU {k85}/20  p = {p:.4f}")

print("\n=== JUGE 3 — MECANISTE : ratio h7/h1 du rollout (séparation des branches) ===")
if ROLL:
    rbp = [ROLL[f'BP_g{g}'] for g in GRAINES if f'BP_g{g}' in ROLL]
    rk8 = [ROLL[f'K8_NU_g{g}'] for g in GRAINES if f'K8_NU_g{g}' in ROLL]
    print(f"  médiane BP : {st.median(rbp):.4f}   médiane K8_NU : {st.median(rk8):.4f}")
    # apparié sur log10 (ratios très asymétriques)
    d = [math.log10(ROLL[f'BP_g{g}'] + 1e-12) - math.log10(ROLL[f'K8_NU_g{g}'] + 1e-12)
         for g in GRAINES if f'BP_g{g}' in ROLL and f'K8_NU_g{g}' in ROLL]
    m, t, n = tt(d)
    print(f"  log10(ratio) BP - K8_NU : d = {m:+8.3f}  t = {t:+6.2f}  "
          f"{'SIG' if abs(t) > 2.86 else 'NS'}  ({sum(1 for x in d if x > 0)}/{n})")
    d2 = sorted(d, key=abs)[:-4]
    if len(d2) >= 3:
        m2, t2, n2 = tt(d2)
        print(f"  {'  -> sans les 4 extremes':34} d = {m2:+8.3f}  t = {t2:+6.2f}  "
              f"{'SIG' if abs(t2) > 2.86 else 'NS':3}  (n={n2})")
    # Le mécanisme a-t-il mordu ? (référence banc : 0,78 ; témoin effondré ~0,012)
    n_bp_01 = sum(1 for x in rbp if x > 0.05)
    n_k8_01 = sum(1 for x in rk8 if x > 0.05)
    print(f"  cerveaux à ratio > 0,05 : BP {n_bp_01}/20 · K8_NU {n_k8_01}/20")

print("\n=== JUGE 4 — ACCORD C1/C2 et ratio d'amplitude ===")
apparie('BP', 'K8_NU', 'accord', 'accord C1/C2 % (apparié)', sig=False)
d_rat = [E[f'BP_g{g}']['c2'] / E[f'BP_g{g}']['c1'] if E[f'BP_g{g}']['c1'] else float('nan')
         for g in GRAINES if f'BP_g{g}' in E]
d_rat_k = [E[f'K8_NU_g{g}']['c2'] / E[f'K8_NU_g{g}']['c1'] if E[f'K8_NU_g{g}']['c1']
           else float('nan') for g in GRAINES if f'K8_NU_g{g}' in E]
d_rat = [x for x in d_rat if x == x]
d_rat_k = [x for x in d_rat_k if x == x]
print(f"  ratio C2/C1 médian : BP {st.median(d_rat):.3f} · K8_NU {st.median(d_rat_k):.3f}")

print("\n=== COMPTAGES ===")
for b in BRAS:
    ks = [f'{b}_g{g}' for g in GRAINES if f'{b}_g{g}' in E]
    if not ks:
        continue
    print(f"  {b:10} niv>=5: {sum(1 for k in ks if E[k]['niv'] >= 5):2}/{len(ks)} | "
          f"maîtrise 0%: {sum(1 for k in ks if E[k]['mait'] == 0):2} | "
          f"maîtrise moy {st.mean([E[k]['mait'] for k in ks]):5.2f}% | "
          f"victoires med {st.median([E[k]['vict'] for k in ks]):.0f} | "
          f"niv max {max(E[k]['niv'] for k in ks)}")

print("\n=== VERIF — maîtrise à PALIER ÉGAL ===")
for b in BRAS:
    ks = [k for k in E if k.rsplit('_g', 1)[0] == b]
    par = {}
    for k in ks:
        par.setdefault(E[k]['niv'], []).append(E[k]['mait'])
    print(f"  {b:10} " + " | ".join(f"niv{n}: {st.median(v):5.1f}% (n={len(v)})"
                                    for n, v in sorted(par.items())))

json.dump(E, open(os.path.join(D, 'agregat_BP.json'), 'w'), indent=1)
print(f"\nagregat_BP.json écrit ({len(E)} runs)")
