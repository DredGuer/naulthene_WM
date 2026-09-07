#!/usr/bin/env python3
"""Depouillement de la campagne 06092026_epoques_nuit. Les juges sont dans LISEZ_MOI.md.

Bras : TEMOIN (reutilise 04092026_cursus_complet/LIBRE) vs K8_NU vs K8_CLIP.
"""
import re, os, json, math, statistics as st

D = os.path.dirname(os.path.abspath(__file__))
CURSUS = os.path.join(os.path.dirname(D), '04092026_cursus_complet')

P_JOUR = re.compile(r'^🌙 Jour (\d+) ')
P_CURS = re.compile(r'Niveau (\d+)/15 — maîtrise (\d+)%')
P_ARB  = re.compile(r'C1=([\d.]+) C2=([\d.]+).*?gain C1 ×([\d.]+)')
P_VICT = re.compile(r'🏆 (\d+) victoire\(s\)')
P_HC1  = re.compile(r'entropie des votes — C1 ([\d.]+)')

def lire(f):
    rows, cur = [], None
    for l in open(f, errors='ignore'):
        m = P_JOUR.match(l)
        if m:
            if cur: rows.append(cur)
            cur = {'j': int(m.group(1))}; continue
        if cur is None: continue
        m = P_ARB.search(l)
        if m: cur.update(c1=float(m.group(1)), c2=float(m.group(2)), gain=float(m.group(3)))
        m = P_VICT.search(l)
        if m: cur['vict'] = int(m.group(1))
        m = P_HC1.search(l)
        if m: cur['hc1'] = float(m.group(1))
        m = P_CURS.search(l)
        if m: cur.update(niv=int(m.group(1)), mait=int(m.group(2)))
    if cur: rows.append(cur)
    return [r for r in rows if 'niv' in r]

def med(rows, k, a, b):
    v = [r[k] for r in rows[a:b] if k in r]
    return st.median(v) if v else None

def tt(d):
    n = len(d)
    if n < 2: return 0.0, 0.0, n
    m, s = st.mean(d), st.stdev(d)
    return m, (0.0 if s == 0 else m/(s/math.sqrt(n))), n

GRAINES = [11,22,33,44,55,66,77,88,99,111,122,133,144,155,166,177,188,199,211,222]
BRAS = {'TEMOIN': (CURSUS, 'LIBRE'), 'K8_NU': (D, 'K8_NU'), 'K8_CLIP': (D, 'K8_CLIP')}

E, manquants = {}, []
for b, (dossier, prefixe) in BRAS.items():
    for g in GRAINES:
        f = os.path.join(dossier, f'{prefixe}_g{g}.log')
        if not os.path.exists(f): manquants.append(f'{b}_g{g}'); continue
        r = lire(f)
        if not r: manquants.append(f'{b}_g{g} (vide)'); continue
        # ⚠️ REGLE §6 — un `t` sur un run INACHEVE choisit implicitement sa fenetre.
        if r[-1]['j'] < 1500:
            manquants.append(f'{b}_g{g} (INACHEVE {r[-1]["j"]}/1500)'); continue
        E[f'{b}_g{g}'] = dict(niv=r[-1]['niv'], mait=med(r,'mait',-100,None),
                              gain=med(r,'gain',-100,None), c1=med(r,'c1',-100,None),
                              hc1=med(r,'hc1',-100,None),
                              vict=r[-1].get('vict', 0), nuits=len(r))

print(f"=== COUVERTURE === {len(E)}/60 runs" + (f"  MANQUANTS: {manquants}" if manquants else ""))

print("\n=== JUGE 4 (GARDE-FOU) — le regime est-il le meme partout ? ===")
ok = True
for b in BRAS:
    v = [E[f'{b}_g{g}']['gain'] for g in GRAINES if f'{b}_g{g}' in E]
    if not v: continue
    m = st.mean(v); bon = abs(m-1.0) < 0.02
    ok &= bon
    print(f"  {b:10} gain_c1 moyen {m:.4f}  (attendu 1,00 — voix libre)  {'OK' if bon else '!! ECHEC'}")
print(f"  => {'garde-fou PASSE' if ok else 'CAMPAGNE INVALIDE'}")

def apparie(a, b, var, label):
    d = [E[f'{a}_g{g}'][var] - E[f'{b}_g{g}'][var]
         for g in GRAINES if f'{a}_g{g}' in E and f'{b}_g{g}' in E]
    if not d: return
    m, t, n = tt(d)
    fav = sum(1 for x in d if x > 0)
    print(f"  {label:32} d = {m:+8.3f}  t = {t:+6.2f}  {'SIG' if abs(t)>2.86 else 'NS ':3}  ({fav}/{n})")
    d2 = sorted(d, key=abs)[:-4]
    if len(d2) >= 3:
        m2, t2, n2 = tt(d2)
        print(f"  {'  -> sans les 4 extremes':32} d = {m2:+8.3f}  t = {t2:+6.2f}  "
              f"{'SIG' if abs(t2)>2.86 else 'NS ':3}  (n={n2})")

print("\n=== JUGE 1 — MAITRISE ===")
apparie('K8_NU','TEMOIN','mait','K8_NU - TEMOIN')
apparie('K8_CLIP','TEMOIN','mait','K8_CLIP - TEMOIN')
apparie('K8_NU','K8_CLIP','mait','K8_NU - K8_CLIP')

print("\n=== JUGE 2 — NIVEAU (le mur) ===")
apparie('K8_NU','TEMOIN','niv','K8_NU - TEMOIN')
apparie('K8_CLIP','TEMOIN','niv','K8_CLIP - TEMOIN')

print("\n=== JUGE 3 — MECANISTE : l'entropie de C1 (la politique se decide-t-elle ?) ===")
apparie('K8_NU','TEMOIN','hc1','K8_NU - TEMOIN')
apparie('K8_CLIP','TEMOIN','hc1','K8_CLIP - TEMOIN')

print("\n=== TEST DE TAUTOLOGIE (les deux bras ont gagne au moins une fois) ===")
for b in ('K8_NU','K8_CLIP'):
    d = [E[f'{b}_g{g}']['mait'] - E[f'TEMOIN_g{g}']['mait'] for g in GRAINES
         if f'TEMOIN_g{g}' in E and f'{b}_g{g}' in E
         and E[f'TEMOIN_g{g}']['vict'] > 0 and E[f'{b}_g{g}']['vict'] > 0]
    if d:
        m, t, n = tt(d); print(f"  {b:10} maitrise conditionnee  d = {m:+.3f}  t = {t:+.2f}  (n={n})")

print("\n=== COMPTAGES ===")
for b in BRAS:
    ks = [f'{b}_g{g}' for g in GRAINES if f'{b}_g{g}' in E]
    if not ks: continue
    print(f"  {b:10} niv>=5: {sum(1 for k in ks if E[k]['niv']>=5):2}/{len(ks)} | "
          f"maitrise 0%: {sum(1 for k in ks if E[k]['mait']==0):2} | "
          f"maitrise moy {st.mean([E[k]['mait'] for k in ks]):5.2f}% | "
          f"victoires med {st.median([E[k]['vict'] for k in ks]):.0f} | "
          f"niv max {max(E[k]['niv'] for k in ks)}")

print("\n=== VERIF — maitrise a PALIER EGAL ===")
for b in BRAS:
    ks = [k for k in E if k.rsplit('_g',1)[0] == b]
    if not ks: continue
    par = {}
    for k in ks: par.setdefault(E[k]['niv'], []).append(E[k]['mait'])
    print(f"  {b:10} " + " | ".join(f"niv{n}: {st.median(v):5.1f}% (n={len(v)})"
                                   for n, v in sorted(par.items())))

json.dump(E, open(os.path.join(D,'agregat.json'),'w'), indent=1)
print(f"\nagregat.json ecrit ({len(E)} runs)")
