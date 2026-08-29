# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Adrien Nault — Naulthène AGI
"""Sonde de corrélation — l'écrêtage de `gain_c1` prédit-il la performance ?

Instrument (v41.39), même forme que `sonde_correlation_derive.py` : mesure sur une cohorte
appariée, corrélée à la performance **déjà enregistrée dans les logs**.

⚠️ `gain_c1` sature quand l'**amplitude de C1 est faible** — un `r` négatif signifie donc
« les cerveaux dont C1 est faible maîtrisent moins », **pas** « la borne nuit ». Les deux
lectures ne se distinguent que par une ablation. La sonde publie l'amplitude brute à côté,
pour rendre la confusion visible.

RÉSULTAT (29/08/2026, n=20) : r(écrêtage, maîtrise) = **−0,4519** (`t = −2,15`),
r(amplitude_C1, maîtrise) = **+0,4768** (`t = +2,30`) — le **même fait vu deux fois**, et
**aucun ne passe Bonferroni** (seuil 3,61 sur 5 corrélations). Deux résultats brisent la
chaîne causale : l'écrêtage **ne touche pas l'entropie** (`r = −0,0192`), et P(action
favorite) corrèle **négativement** avec la maîtrise (`r = −0,2868`).
"""
import numpy as np, torch, torch.nn.functional as F, json, re, math
from naulthene.cerveau.noyau import (DEVICE, DIM_VECTEUR_BIO, creer_env, encoder,
                                      GAIN_C1_MIN, GAIN_C1_MAX)
from naulthene.cerveau.persistance import PersistanceAnatomique
C="brains/28082026_v4134_tronc"
GR=[11,22,33,44,55,66,77,88,99,111,122,133,144,155,166,177,188,199,211,222]
TICKS=400
def mesurer(g):
    torch.manual_seed(g)
    etat=PersistanceAnatomique(f"{C}/A_g{g}.brain").charger_ou_naitre(); ag=etat.agent; ag.eval()
    db=ag.dim_bus
    env=creer_env("MiniGrid-SimpleCrossingS9N1-v0",147); obs,_=env.reset(seed=g)
    mem=torch.zeros(1,db,device=DEVICE); ctx=torch.zeros(1,db,device=DEVICE)
    gains=[];ampl=[];ent=[];pfav=[]
    for t in range(TICKS):
        vb=np.asarray(etat.moteur_bio.obtenir_vecteur_bio(),dtype=np.float32)
        with torch.no_grad():
            lg_f,_,_,_,mn,_,_,_ = ag.penser(encoder(obs),mem,ctx,
                                            torch.tensor(vb,device=DEVICE).unsqueeze(0),
                                            force_planification=0.5)
        m=getattr(ag,"mesure_arbitrage",{})
        if m: gains.append(m.get("gain_c1",np.nan)); ampl.append(m.get("amplitude_c1",np.nan))
        x=lg_f.clone(); x[...,7]=float('-inf'); p=F.softmax(x,dim=-1).cpu().numpy().ravel()
        ent.append(float(-(p*np.log(p+1e-12)).sum())); pfav.append(float(p.max()))
        a=int(torch.distributions.Categorical(logits=x).sample().item())
        mem=mn.detach(); obs,r,te,tr,_=env.step(a)
        if te or tr: obs,_=env.reset(seed=g+t); mem=torch.zeros(1,db,device=DEVICE)
    gg=np.array(gains)
    return dict(taux_ecretage=float((gg>=GAIN_C1_MAX-1e-6).mean()),
                gain_moyen=float(gg.mean()), amplitude_c1=float(np.nanmean(ampl)),
                entropie=float(np.mean(ent)), p_favorite=float(np.mean(pfav)))
def perf(g):
    t=open(f"{C}/A_g{g}.log",errors='ignore').read()
    nu=t.split("🌙 Jour ")[1:][-200:]
    m=[int(x.group(1)) for b in nu for x in [re.search(r'maîtrise (\d+)%',b)] if x]
    e=[float(x.group(1)) for b in nu for x in [re.search(r'⚡ moy ([\d.]+)',b)] if x]
    return (np.mean(m) if m else None, np.mean(e) if e else None)
R={}
for g in GR:
    d=mesurer(g); mm,ee=perf(g); d["maitrise"]=mm; d["energie"]=ee; R[g]=d
    print(f"g{g:<5} ecretage {100*d['taux_ecretage']:>5.1f}%  gain {d['gain_moyen']:.3f}  "
          f"ampl_C1 {d['amplitude_c1']:.4f}  ent {d['entropie']:.4f}  "
          f"P_fav {100*d['p_favorite']:>5.2f}%  maitrise {mm:.2f}%",flush=True)
json.dump({str(k):v for k,v in R.items()},open(f"{C}/correlation_ecretage.json","w"),indent=1)
def pe(x,y):
    x,y=np.array(x),np.array(y); n=len(x); r=float(np.corrcoef(x,y)[0,1])
    return r, r*math.sqrt((n-2)/max(1-r*r,1e-12)), n
print("\n"+"="*66)
E=[R[g]["taux_ecretage"] for g in GR]; A=[R[g]["amplitude_c1"] for g in GR]
M=[R[g]["maitrise"] for g in GR]; EN=[R[g]["entropie"] for g in GR]
P=[R[g]["p_favorite"] for g in GR]
for lbl,x,y in [("ecretage  -> maitrise",E,M),("amplitude_C1 -> maitrise",A,M),
                ("entropie  -> maitrise",EN,M),("P_favorite -> maitrise",P,M),
                ("ecretage  -> entropie",E,EN)]:
    r,t,n=pe(x,y); print(f"  r({lbl:<26}) = {r:+.4f}   t = {t:+.2f}")
print(f"\n  Bonferroni, 5 correlations, df=18 -> seuil |t| ~ 3,61")
print(f"\n  ecretage : min {100*min(E):.1f} %  max {100*max(E):.1f} %  moyenne {100*np.mean(E):.1f} %")
print(f"  entropie : min {min(EN):.4f}  max {max(EN):.4f}   (PPO : 1,667-1,704)")
print(f"  P_fav    : min {100*min(P):.2f} %  max {100*max(P):.2f} %  (PPO : 34,7-35,5 %)")
