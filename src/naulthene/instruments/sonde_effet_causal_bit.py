# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Adrien Nault — Naulthène AGI
"""Sonde d'effet causal — combien vaut UNE dimension du vecteur bio pour le critique ?

Instrument **en lecture seule** (v41.33). Au même tick, sur le même état et la même
mémoire, bascule une seule dimension du vecteur bio de 0 à 1 et lit l'écart sur `V`.
C'est un **contrefactuel pur** : tout le reste est tenu constant, donc l'écart mesuré est
causal, contrairement à un saut `V(s')−V(s)` observé en jeu où la vue a changé aussi.

RÉSULTAT sur le bit de portage (27/08/2026) : **+0,325 (g11) et +0,437 (g44)**, soit
**361 % à 403 %** du mouvement typique de `V` d'un tick à l'autre — et pourtant le saut
RÉELLEMENT observé au moment d'une saisie ne vaut que +0,006. Le signal existe et se fait
noyer par le bruit perceptif (±0,090/tick, non orienté). C'est ce qui a réfuté le passage
en TD(0) **avant** de lancer la moindre campagne.

Ne sauvegarde jamais et n'entraîne rien.
"""
import numpy as np, torch, sys
from naulthene.cerveau.noyau import DEVICE, DIM_VECTEUR_BIO, creer_env, encoder
from naulthene.cerveau.persistance import PersistanceAnatomique
B=sys.argv[1]; G=11
rng=np.random.RandomState(G); torch.manual_seed(G)
etat=PersistanceAnatomique(B).charger_ou_naitre(); ag=etat.agent; ag.eval(); db=ag.dim_bus
env=creer_env("MiniGrid-DoorKey-6x6-v0",147); obs,_=env.reset(seed=G)
mem=torch.zeros(1,db,device=DEVICE); ctx=torch.zeros(1,db,device=DEVICE)
# CONTREFACTUEL : au meme tick, meme obs, meme memoire — on ne change QUE le bit
ecarts=[]; V_reels=[]
for t in range(1200):
    u=env.unwrapped; pa=u.carrying is not None
    o=encoder(obs)
    vals={}
    for bit in (0.0,1.0):
        vb=np.full(DIM_VECTEUR_BIO,0.5,dtype=np.float32); vb[-1]=bit
        with torch.no_grad():
            _,mn,_,pb,lg=ag._executer_c1_reflexe(o,mem,ctx,torch.tensor(vb,device=DEVICE).unsqueeze(0))
            vals[bit]=float(ag.cortex_prefrontal(pb).item())
    ecarts.append(vals[1.0]-vals[0.0]); V_reels.append(vals[1.0 if pa else 0.0])
    vb=np.full(DIM_VECTEUR_BIO,0.5,dtype=np.float32); vb[-1]=1.0 if pa else 0.0
    with torch.no_grad():
        _,mn,_,_,lg=ag._executer_c1_reflexe(o,mem,ctx,torch.tensor(vb,device=DEVICE).unsqueeze(0))
    lg=lg.clone(); lg[...,7]=float('-inf')
    a=int(torch.distributions.Categorical(logits=lg).sample().item()); mem=mn.detach()
    obs,r,te,tr,_=env.step(a)
    if te or tr: obs,_=env.reset(seed=G+t); mem=torch.zeros(1,db,device=DEVICE)
e=np.array(ecarts); v=np.array(V_reels)
print(f"\n=== {B.split('/')[-1]} — 1200 ticks ===")
print(f"EFFET CAUSAL PUR du bit (meme etat, on bascule 0->1) :")
print(f"   V(bit=1) - V(bit=0) = {e.mean():+.6f}  +-{e.std():.6f}   [{e.min():+.4f}, {e.max():+.4f}]")
print(f"\nVARIATION TOTALE de V d'un tick a l'autre (tout confondu) :")
d=np.abs(v[1:]-v[:-1])
print(f"   |V(t+1)-V(t)| moyen = {d.mean():.6f}")
print(f"\nPART du bit dans le mouvement de V : {100*abs(e.mean())/d.mean():.1f} %")
print(f"   -> le reste vient de la VUE, qui change a chaque tick")
