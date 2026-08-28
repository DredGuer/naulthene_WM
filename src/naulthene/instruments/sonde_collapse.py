# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Adrien Nault — Naulthène AGI
"""Sonde de collapse — à quel étage le réseau confond-il deux états distincts ?

Instrument **en lecture seule** (v41.35). Suit `cos(x_ressource, x_mur)` étage par étage.
Le gradient d'une couche linéaire vaut `δ ⊗ x` : si les entrées sont colinéaires, les
gradients le sont **aussi**, quelle que soit la récompense.

RÉSULTAT (28/08/2026) : l'observation brute **distingue** les deux états (cos = 0,610), et
le réseau les **confond progressivement** — `bus_latent` 0,959, `pensee_bio` **0,996**.
L'information entre et se perd. C'est ce qui explique la colinéarité des gradients mesurée
par `sonde_pression_separation.py`.
"""
import numpy as np, torch, torch.nn.functional as F, sys
from naulthene.cerveau.noyau import DEVICE, DIM_VECTEUR_BIO, creer_env, encoder
from naulthene.cerveau.persistance import PersistanceAnatomique
B=sys.argv[1]; G=11
rng=np.random.RandomState(G); torch.manual_seed(G)
e=PersistanceAnatomique(B).charger_ou_naitre(); ag=e.agent; ag.eval(); db=ag.dim_bus
env=creer_env("MiniGrid-DoorKey-6x6-v0",147); obs,_=env.reset(seed=G)
mem=torch.zeros(1,db,device=DEVICE); ctx=torch.zeros(1,db,device=DEVICE)
bio=torch.full((1,DIM_VECTEUR_BIO),0.5,device=DEVICE)
caps={"res":[],"mur":[]}
for t in range(3000):
    u=env.unwrapped; fx,fy=(int(v) for v in u.front_pos)
    ob=u.grid.get(fx,fy) if (0<=fx<u.grid.width and 0<=fy<u.grid.height) else None
    ram=ob is not None and getattr(ob,'can_pickup',lambda:False)()
    em=ob is not None and not ob.can_overlap() and not ram
    c="res" if ram else ("mur" if em else None)
    if c and len(caps[c])<120: caps[c].append(encoder(obs))
    obs,_,te,tr,_=env.step(int(rng.randint(0,7)))
    if te or tr: obs,_=env.reset(seed=G+t)
def etages(lst):
    o_=[];bl=[];pe=[];pb_=[]
    with torch.no_grad():
        for o in lst:
            bus,mn,_,pbio,_=ag._executer_c1_reflexe(o,mem,ctx,bio)
            o_.append(o.cpu().numpy().ravel()); bl.append(bus.cpu().numpy().ravel())
            pb_.append(pbio.cpu().numpy().ravel())
    return map(np.array,(o_,bl,pb_))
oR,bR,pR=etages(caps["res"]); oM,bM,pM=etages(caps["mur"])
def cos(a,b):
    a,b=a.mean(0),b.mean(0); return float(np.dot(a,b)/(np.linalg.norm(a)*np.linalg.norm(b)))
print(f"\n=== {B.split('/')[-1]} — COLINEARITE DES ENTREES, etage par etage ===")
print(f"  obs brute (147)         cos = {cos(oR,oM):.6f}")
print(f"  bus_latent (apres vue)  cos = {cos(bR,bM):.6f}")
print(f"  pensee_bio (entree tete) cos = {cos(pR,pM):.6f}")
print(f"\n  -> le gradient d'une couche lineaire vaut delta ⊗ x.")
print(f"     Si x_res et x_mur sont colineaires a {cos(pR,pM):.4f}, les gradients le sont AUSSI,")
print(f"     quelle que soit la recompense. La pression a separer ne PEUT PAS venir de la.")
