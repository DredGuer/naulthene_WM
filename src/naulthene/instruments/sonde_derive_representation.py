# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Adrien Nault — Naulthène AGI
"""Sonde de dérive — l'axe informatif est-il STATIONNAIRE pendant que la tête apprend ?

Instrument (v41.36). Recalcule l'axe `mean(but vu) − mean(but absent)` **après chaque
nuit** et mesure sa rotation. `pensee_bio` dépend d'`integrateur_bio` et du tronc, tous
entraînés simultanément : la cible que poursuit `tete_motrice` peut donc bouger.

RÉSULTAT (28/08/2026) : l'axe tourne de **4,81°/nuit (g11)** et **3,35°/nuit (g22)**, soit
**35,2°** et **27,3°** sur 10 nuits. Rapporté à la vitesse de rapprochement de `W`
(0,106°/nuit et 0,245°/nuit), la cible fuit **14× à 46× plus vite** que le poursuivant.

C'est la conclusion de l'enquête d'août 2026 : la tête motrice avance dans la bonne
direction, en ligne presque droite, vers une cible qui se dérobe.
"""
import numpy as np, torch, sys
from naulthene.cerveau.noyau import DEVICE, DIM_VECTEUR_BIO, creer_env, encoder
from naulthene.cerveau.persistance import PersistanceAnatomique
B=sys.argv[1]; G=11; JOURS=10; TICKS=400
rng=np.random.RandomState(G); torch.manual_seed(G)
etat=PersistanceAnatomique(B).charger_ou_naitre(); ag=etat.agent; db=ag.dim_bus
env=creer_env("MiniGrid-SimpleCrossingS9N1-v0",147); obs,_=env.reset(seed=G)
mem=torch.zeros(1,db,device=DEVICE); ctx=torch.zeros(1,db,device=DEVICE)
bio=torch.full((1,DIM_VECTEUR_BIO),0.5,device=DEVICE)
env2=creer_env("MiniGrid-SimpleCrossingS9N1-v0",147)
def calc_axe():
    o2,_=env2.reset(seed=G); r2=np.random.RandomState(7); C={"a":[],"b":[]}
    for t in range(2500):
        img=o2["image"] if isinstance(o2,dict) else None
        if img is not None:
            k="a" if (img[:,:,0]==8).any() else "b"
            if len(C[k])<100: C[k].append(encoder(o2))
        o2,_,te,tr,_=env2.step(int(r2.randint(0,7)))
        if te or tr: o2,_=env2.reset(seed=G+t)
    def mo(l):
        v=[]
        with torch.no_grad():
            for o in l:
                _,_,_,p,_=ag._executer_c1_reflexe(o,mem,ctx,bio); v.append(p.cpu().numpy().ravel())
        return np.array(v).mean(0)
    a=mo(C["a"])-mo(C["b"]); return a/np.linalg.norm(a)
axes=[calc_axe()]
ag.train()
for jour in range(JOURS):
    lps=[];vals=[];ents=[];rws=[];dns=[];trs=[];jp=[]
    m=torch.zeros(1,db,device=DEVICE)
    for t in range(TICKS):
        u=env.unwrapped; pav,dav=tuple(u.agent_pos),int(u.agent_dir); po=u.carrying is not None
        bus,mn,_,pb,lg=ag._executer_c1_reflexe(encoder(obs),m,ctx,bio)
        lg2=lg.clone(); lg2[...,7]=float('-inf')
        d=torch.distributions.Categorical(logits=lg2); a=d.sample()
        lps.append(d.log_prob(a)); ents.append(d.entropy()); vals.append(ag.cortex_prefrontal(pb))
        act=torch.zeros(1,ag.actions_eye.shape[0],device=DEVICE); act[0,int(a.item())]=1.0
        jp.append(torch.nn.functional.mse_loss(ag._predire_bus(pb.detach(),act),bus.detach()))
        m=mn.detach(); obs,r,te,tr,_=env.step(int(a.item()))
        trs.append(bool(tuple(u.agent_pos)!=pav or int(u.agent_dir)!=dav or (u.carrying is not None)!=po))
        rws.append(float(r)); dns.append(bool(te or tr))
        if te or tr: obs,_=env.reset(seed=G+jour*1000+t)
    ag.apprendre_journee(jp,lps,ents,vals,rws,dns,coeff_entropie=0.01,transitions=trs)
    axes.append(calc_axe())
print(f"\n=== {B.split('/')[-1]} — L'AXE INFORMATIF BOUGE-T-IL ? ===")
der=[float(np.dot(axes[i],axes[i+1])) for i in range(JOURS)]
print(f"  cos(axe_nuit_n, axe_nuit_n+1) moyen : {np.mean(der):.4f}   (1,0 = axe fige)")
print(f"  cos(axe_debut, axe_fin)             : {float(np.dot(axes[0],axes[-1])):.4f}")
ang=np.degrees(np.arccos(np.clip(np.mean(der),-1,1)))
print(f"  rotation de l'axe PAR NUIT          : {ang:.2f}°")
angt=np.degrees(np.arccos(np.clip(float(np.dot(axes[0],axes[-1])),-1,1)))
print(f"  rotation totale sur {JOURS} nuits        : {angt:.2f}°")
print(f"\n  → si l'axe tourne plus vite que W ne le rattrape, l'alignement ne peut PAS monter.")
