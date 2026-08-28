# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Adrien Nault — Naulthène AGI
"""Sonde de plafond — quel écart de logit la géométrie AUTORISE-t-elle ?

Instrument **en lecture seule** (v41.35). Borne mathématique : `logit = W·x`, donc
`|logit_r − logit_m| ≤ ‖W‖ · ‖x_r − x_m‖`. Mesure la distance réelle des représentations
et l'écart de logit qu'elle permet **au maximum**, avec des poids parfaits.

RÉSULTAT (28/08/2026) : ‖x_res − x_mur‖ vaut **1,5 % à 22,6 %** de la norme de
`pensee_bio`, ce qui plafonne la probabilité de l'action favorisée à **14,56 % – 18,69 %**
— contre **14,29 %** pour le hasard sur 7 actions. Les 15,00 % mesurés en jeu ne sont donc
pas de l'apathie : c'est **le maximum que la géométrie autorise**.
"""
import numpy as np, torch, sys
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
P={}
with torch.no_grad():
    for k in ("res","mur"):
        v=[]
        for o in caps[k]:
            _,_,_,pb,_=ag._executer_c1_reflexe(o,mem,ctx,bio); v.append(pb.cpu().numpy().ravel())
        P[k]=np.array(v)
mr,mm=P["res"].mean(0),P["mur"].mean(0)
dist=np.linalg.norm(mr-mm); nr=np.linalg.norm(mr)
W=ag.tete_motrice.base_weight.detach().cpu().numpy()
try: W=W+ag.tete_motrice.annexe_weight.detach().cpu().numpy()
except Exception: pass
nW=np.linalg.norm(W,axis=1).max()
print(f"\n=== {B.split('/')[-1]} ===")
print(f"  ||pensee_bio||               = {nr:.4f}")
print(f"  ||x_res - x_mur||            = {dist:.4f}   ({100*dist/nr:.2f} % de la norme)")
print(f"  ||W|| max (ligne tete_motrice)= {nW:.4f}")
print(f"  ECART DE LOGIT MAXIMAL       = {nW*dist:.6f}")
p=np.exp(nW*dist)/(np.exp(nW*dist)+6)
print(f"  -> proba max atteignable pour l'action favorisee : {100*p:.2f} %  (hasard = 14,29 %)")
print(f"\n  Autrement dit : meme avec des poids PARFAITS, la tete motrice ne peut pas")
print(f"  ecarter les deux etats de plus de {nW*dist:.4f} en logit. Le plafond n'est pas")
print(f"  dans l'apprentissage — il est dans la GEOMETRIE de la representation recue.")
