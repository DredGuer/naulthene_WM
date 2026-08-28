# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Adrien Nault — Naulthène AGI
"""Sonde de corrélation — la dérive de représentation prédit-elle la performance ?

Instrument (v41.37). Mesure la vitesse de dérive sur chaque cerveau d'une cohorte appariée,
puis la corrèle à la performance **déjà enregistrée dans les logs** — jamais recalculée,
sinon on corrélerait un état avec la performance d'un autre état.

**POURQUOI CETTE FORME.** Deux alternatives avaient été envisagées : passer la sonde de
dérive à 20 graines, ou enrichir la mesure avec d'autres axes informatifs. Les deux
décrivent le phénomène **plus finement sans jamais tester s'il cause quoi que ce soit** —
c'est le piège que le projet a déjà payé (une mécanique mesurée là où elle est active prouve
qu'elle marche, jamais qu'elle explique autre chose). Une corrélation, elle, est falsifiable
dans les deux sens.

Le précédent du dépôt : `maîtrise ~ énergie moyenne` donne **r = +0,710** (`t = +2,85`).
C'est cette forme de mesure qui a désigné le métabolisme comme suspect.

RÉSULTAT (29/08/2026, n=20, cohorte v41.34) : **r(dérive, maîtrise) = +0,1386**
(`t = +0,59`), r(dérive, énergie) = −0,1059, r(dérive, niveau) = −0,0506. **Aucune
n'approche le seuil de Bonferroni (3,38 sur 3 métriques, df=18)**, et le signe de la
première est *positif* — l'inverse de la prédiction. La dérive existe mais n'explique pas le
plafond. Quinzième réfutation.
"""
import numpy as np, torch, json, re, math, sys, copy
from naulthene.cerveau.noyau import DEVICE, DIM_VECTEUR_BIO, creer_env, encoder
from naulthene.cerveau.persistance import PersistanceAnatomique
C="brains/28082026_v4134_tronc"
GR=[11,22,33,44,55,66,77,88,99,111,122,133,144,155,166,177,188,199,211,222]
NUITS=12; TICKS=400
def axe(ag,env,mem,ctx,bio,g,n=1200,cap=100):
    o,_=env.reset(seed=g); r=np.random.RandomState(7); K={"a":[],"b":[]}
    for t in range(n):
        img=o["image"] if isinstance(o,dict) else None
        if img is not None:
            k="a" if (img[:,:,0]==8).any() else "b"
            if len(K[k])<cap: K[k].append(encoder(o))
        o,_,te,tr,_=env.step(int(r.randint(0,7)))
        if te or tr: o,_=env.reset(seed=g+t)
    if len(K["a"])<20 or len(K["b"])<20: return None
    def mo(l):
        v=[]
        with torch.no_grad():
            for x in l:
                _,_,_,p,_=ag._executer_c1_reflexe(x,mem,ctx,bio); v.append(p.cpu().numpy().ravel())
        return np.array(v).mean(0)
    a=mo(K["a"])-mo(K["b"]); nn=np.linalg.norm(a)
    return a/nn if nn>1e-12 else None
def rot(u,v):
    if u is None or v is None or len(u)!=len(v): return None
    return float(np.degrees(np.arccos(np.clip(float(np.dot(u,v)),-1,1))))
def mesurer(g):
    torch.manual_seed(g)
    etat=PersistanceAnatomique(f"{C}/A_g{g}.brain").charger_ou_naitre()
    ag=etat.agent; db=ag.dim_bus
    env=creer_env("MiniGrid-SimpleCrossingS9N1-v0",147); obs,_=env.reset(seed=g)
    envm=creer_env("MiniGrid-SimpleCrossingS9N1-v0",147)
    mem0=torch.zeros(1,db,device=DEVICE); ctx=torch.zeros(1,db,device=DEVICE)
    biog=torch.full((1,DIM_VECTEUR_BIO),0.5,device=DEVICE)
    a0=axe(ag,envm,mem0,ctx,biog,g); rots=[]
    ag.train()
    for j in range(NUITS):
        lps=[];vals=[];ents=[];rws=[];dns=[];trs=[];jp=[]
        mem=torch.zeros(1,db,device=DEVICE)
        for t in range(TICKS):
            u=env.unwrapped; pav,dav=tuple(u.agent_pos),int(u.agent_dir); po=u.carrying is not None
            vb=np.asarray(etat.moteur_bio.obtenir_vecteur_bio(),dtype=np.float32)
            bus,mn,_,pb,lg=ag._executer_c1_reflexe(encoder(obs),mem,ctx,
                                                    torch.tensor(vb,device=DEVICE).unsqueeze(0))
            lg2=lg.clone(); lg2[...,7]=float('-inf')
            d=torch.distributions.Categorical(logits=lg2); a=d.sample()
            lps.append(d.log_prob(a)); ents.append(d.entropy()); vals.append(ag.cortex_prefrontal(pb))
            oh=torch.zeros(1,ag.actions_eye.shape[0],device=DEVICE); oh[0,int(a.item())]=1.0
            jp.append(torch.nn.functional.mse_loss(ag._predire_bus(pb.detach(),oh),bus.detach()))
            mem=mn.detach(); obs,r,te,tr,_=env.step(int(a.item()))
            trs.append(bool(tuple(u.agent_pos)!=pav or int(u.agent_dir)!=dav or (u.carrying is not None)!=po))
            rws.append(float(r)); dns.append(bool(te or tr))
            if te or tr: obs,_=env.reset(seed=g+j*1000+t)
        ag.apprendre_journee(jp,lps,ents,vals,rws,dns,coeff_entropie=0.01,transitions=trs)
        a1=axe(ag,envm,mem0,ctx,biog,g); rr=rot(a0,a1)
        if rr is not None: rots.append(rr)
        a0=a1
    return float(np.mean(rots)) if rots else None
def perf(g):
    t=open(f"{C}/A_g{g}.log",errors='ignore').read()
    nu=t.split("🌙 Jour ")[1:][-200:]
    m=[int(x.group(1)) for b in nu for x in [re.search(r'maîtrise (\d+)%',b)] if x]
    e=[float(x.group(1)) for b in nu for x in [re.search(r'⚡ moy ([\d.]+)',b)] if x]
    lv=[int(x) for x in re.findall(r'Niveau (\d+)/15',t)]
    return (np.mean(m) if m else None, np.mean(e) if e else None, max(lv) if lv else None)
R={}
for g in GR:
    d=mesurer(g); mm,ee,lv=perf(g)
    R[g]={"derive":d,"maitrise":mm,"energie":ee,"niveau":lv}
    print(f"g{g:<5} derive {d:.4f}°/nuit  maitrise {mm:.2f}%  energie {ee:.4f}  niveau {lv}",flush=True)
json.dump(R,open(f"{C}/correlation_derive.json","w"),indent=1)
def pearson(x,y):
    x,y=np.array(x),np.array(y); n=len(x)
    r=float(np.corrcoef(x,y)[0,1]); t=r*math.sqrt((n-2)/max(1-r*r,1e-12))
    return r,t,n
print("\n"+"="*58)
D=[R[g]["derive"] for g in GR]
for k in ("maitrise","energie","niveau"):
    Y=[R[g][k] for g in GR]
    r,t,n=pearson(D,Y)
    print(f"  r(derive, {k:<9}) = {r:+.4f}   t = {t:+.2f}   n={n}")
print("\n  Bonferroni, 3 metriques, df=18 -> seuil |t| ~ 3,38")
