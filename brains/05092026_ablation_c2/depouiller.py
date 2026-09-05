#!/usr/bin/env python3
"""Depouillement de la campagne 05092026_ablation_c2. Les juges sont dans LISEZ_MOI.md."""
import re, glob, os, json, math, statistics as st

D = os.path.dirname(os.path.abspath(__file__))
CURSUS = os.path.join(os.path.dirname(D), '04092026_cursus_complet')

P_JOUR = re.compile(r'^🌙 Jour (\d+) ')
P_CURS = re.compile(r'Niveau (\d+)/15 — maîtrise (\d+)%')
P_ARB  = re.compile(r'C1=([\d.]+) C2=([\d.]+).*?gain C1 ×([\d.]+)')
P_VICT = re.compile(r'🏆 (\d+) victoire\(s\)')

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
BRAS = {'LIBRE': CURSUS, 'LIBRE_SANS_C2': D, 'TEMOIN_SANS_C2': D}

# --- Etat final par run ---
E, manquants = {}, []
for b, dossier in BRAS.items():
    for g in GRAINES:
        f = os.path.join(dossier, f'{b}_g{g}.log')
        if not os.path.exists(f): manquants.append(f'{b}_g{g}'); continue
        r = lire(f)
        if not r: manquants.append(f'{b}_g{g} (vide)'); continue
        # ⚠️ REGLE DE MESURE §6 — un `t` sur un run INACHEVE choisit implicitement sa
        # fenetre (leçon du 20/08 : t=+3,68 a mi-parcours -> +1,93 a la fin). Un run qui
        # n'a pas atteint 1500 nuits est EXCLU, jamais compte comme termine.
        if r[-1]['j'] < 1500:
            manquants.append(f'{b}_g{g} (INACHEVE {r[-1]["j"]}/1500)'); continue
        E[f'{b}_g{g}'] = dict(niv=r[-1]['niv'], mait=med(r,'mait',-100,None),
                              gain=med(r,'gain',-100,None), c1=med(r,'c1',-100,None),
                              vict=r[-1].get('vict', 0), nuits=len(r))

print(f"=== COUVERTURE === {len(E)}/60 runs" + (f"  MANQUANTS: {manquants}" if manquants else ""))

# --- Juge 4 : garde-fou, le gain est-il intact ? ---
print("\n=== JUGE 4 (GARDE-FOU) — le gain de C1 est-il intact ? ===")
ok4 = True
for b in BRAS:
    v = [E[f'{b}_g{g}']['gain'] for g in GRAINES if f'{b}_g{g}' in E]
    if not v: continue
    m = st.mean(v)
    att = "≈1,00" if b.startswith('LIBRE') else "≫0,25"
    bon = (abs(m-1.0) < 0.02) if b.startswith('LIBRE') else (m > 0.5)
    ok4 &= bon
    print(f"  {b:15} gain moyen {m:.4f}  (attendu {att})  {'OK' if bon else '!! ECHEC'}")
print(f"  => {'garde-fou PASSE' if ok4 else 'CAMPAGNE INVALIDE'}")

# --- Juges 1/2/3 : comparaisons appariees ---
def apparie(a, b, var, label):
    d = [E[f'{a}_g{g}'][var] - E[f'{b}_g{g}'][var]
         for g in GRAINES if f'{a}_g{g}' in E and f'{b}_g{g}' in E]
    if not d: return
    m, t, n = tt(d)
    fav = sum(1 for x in d if x > 0)
    sig = "SIG" if abs(t) > 2.86 else "NS"
    print(f"  {label:34} δ = {m:+7.3f}  t = {t:+6.2f}  {sig:3}  ({fav}/{n} favorables)")
    # test des extremes : retrait des 4 plus grands |ecarts|
    d2 = sorted(d, key=abs)[:-4]
    if len(d2) >= 3:
        m2, t2, n2 = tt(d2)
        print(f"  {'  ↳ sans les 4 extremes':34} δ = {m2:+7.3f}  t = {t2:+6.2f}  "
              f"{'SIG' if abs(t2)>2.86 else 'NS':3}  (n={n2})")

print("\n=== JUGE 1 — MAITRISE : C2 sert-il ? (LIBRE vs LIBRE_SANS_C2) ===")
apparie('LIBRE','LIBRE_SANS_C2','mait','maitrise')
print("\n=== JUGE 2 — NIVEAU : C2 sert-il ? ===")
apparie('LIBRE','LIBRE_SANS_C2','niv','niveau')
print("\n=== JUGE 3 — LA CONFUSION HISTORIQUE (LIBRE_SANS_C2 vs TEMOIN_SANS_C2) ===")
apparie('LIBRE_SANS_C2','TEMOIN_SANS_C2','mait','maitrise')
apparie('LIBRE_SANS_C2','TEMOIN_SANS_C2','niv','niveau')
apparie('LIBRE_SANS_C2','TEMOIN_SANS_C2','c1','amplitude C1')

# --- Tautologie ---
print("\n=== TEST DE TAUTOLOGIE (les deux bras ont gagne au moins une fois) ===")
d = [E[f'LIBRE_g{g}']['mait'] - E[f'LIBRE_SANS_C2_g{g}']['mait'] for g in GRAINES
     if f'LIBRE_g{g}' in E and f'LIBRE_SANS_C2_g{g}' in E
     and E[f'LIBRE_g{g}']['vict'] > 0 and E[f'LIBRE_SANS_C2_g{g}']['vict'] > 0]
if d:
    m, t, n = tt(d); print(f"  maitrise conditionnee  δ = {m:+.3f}  t = {t:+.2f}  (n={n})")

# --- Comptages ---
print("\n=== COMPTAGES ===")
for b in BRAS:
    ks = [f'{b}_g{g}' for g in GRAINES if f'{b}_g{g}' in E]
    if not ks: continue
    print(f"  {b:15} niv4: {sum(1 for k in ks if E[k]['niv']>=4):2}/{len(ks)} | "
          f"maitrise 0%: {sum(1 for k in ks if E[k]['mait']==0):2} | "
          f"niveau 1: {sum(1 for k in ks if E[k]['niv']<=1):2} | "
          f"niv max {max(E[k]['niv'] for k in ks)}")


# --- L'inversion du juge 3 est-elle un artefact de palier ? ---
# Comparer la maitrise de deux cerveaux qui jouent des NIVEAUX DIFFERENTS n'a pas de sens :
# un palier plus facile donne mecaniquement une maitrise plus haute. Ce bloc compare a
# palier EGAL.
print("\n=== VERIF — maitrise a PALIER EGAL (l'inversion du juge 3) ===")
for b in BRAS:
    ks = [k for k in E if k.rsplit('_g',1)[0] == b]
    if not ks: continue
    par = {}
    for k in ks: par.setdefault(E[k]['niv'], []).append(E[k]['mait'])
    print(f"  {b:16} " + " | ".join(f"niv{n}: {st.median(v):5.1f}% (n={len(v)})"
                                   for n, v in sorted(par.items())))
print("  => si l'ecart disparait a niveau egal, le delta de maitrise est un ARTEFACT de palier")

json.dump(E, open(os.path.join(D,'agregat.json'),'w'), indent=1)
print(f"\nagregat.json ecrit ({len(E)} runs)")
