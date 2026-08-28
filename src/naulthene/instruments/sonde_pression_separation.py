# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Adrien Nault — Naulthène AGI
"""Sonde de pression — l'optimiseur PEUT-IL séparer deux états ?

Instrument **en lecture seule** (v41.35). Mesure `cos(∇_ressource, ∇_mur)` quand on
renforce la même action sur les deux classes d'états.

    +1 = l'optimiseur pousse les deux états DANS LA MÊME DIRECTION → aucune séparation
         ne peut émerger, quelle que soit la durée du run ou la fonction de récompense
     0 = directions indépendantes
    −1 = il les écarte activement

RÉSULTAT (28/08/2026, 3 cerveaux) : **+0,9857 / +0,9850 / +0,9865**. Les gradients sont
quasi colinéaires. Ce n'est pas « aucune pression à séparer », c'est une **impossibilité
mécanique** — voir `sonde_collapse.py` pour la cause et
`sonde_plafond_geometrique.py` pour ce qu'elle interdit.
"""
import numpy as np, torch, torch.nn.functional as F, sys
from naulthene.cerveau.noyau import DEVICE, DIM_VECTEUR_BIO, creer_env, encoder
from naulthene.cerveau.persistance import PersistanceAnatomique
from naulthene.cerveau.noyau import DetecteurRessourcesBiologiques, NB_SOURCES_FOOD, NB_SOURCES_WATER
B=sys.argv[1]; G=int(sys.argv[2]) if len(sys.argv)>2 else 11
rng=np.random.RandomState(G); torch.manual_seed(G)
e=PersistanceAnatomique(B).charger_ou_naitre(); ag=e.agent; ag.train(); db=ag.dim_bus
env=creer_env("MiniGrid-DoorKey-6x6-v0",147); obs,_=env.reset(seed=G)
det=DetecteurRessourcesBiologiques(nb_sources_food=NB_SOURCES_FOOD,nb_sources_water=NB_SOURCES_WATER)
det.reinitialiser_episode(env)
mem=torch.zeros(1,db,device=DEVICE); ctx=torch.zeros(1,db,device=DEVICE)
bio=torch.full((1,DIM_VECTEUR_BIO),0.5,device=DEVICE)
caps={"ressource":[],"mur":[]}
for t in range(3000):
    u=env.unwrapped; fx,fy=(int(v) for v in u.front_pos)
    ob=u.grid.get(fx,fy) if (0<=fx<u.grid.width and 0<=fy<u.grid.height) else None
    ram = ob is not None and getattr(ob,'can_pickup',lambda:False)()
    em = ob is not None and not ob.can_overlap() and not ram
    c="ressource" if ram else ("mur" if em else None)
    if c and len(caps[c])<120: caps[c].append(encoder(obs))
    obs,_,te,tr,_=env.step(int(rng.randint(0,7)))
    if te or tr: obs,_=env.reset(seed=G+t); det.reinitialiser_episode(env)
if len(caps["ressource"])<20 or len(caps["mur"])<20:
    print(f"echantillon insuffisant : {len(caps['ressource'])}/{len(caps['mur'])}"); sys.exit()
def grad_classe(lst, cible):
    """Gradient moyen sur integrateur_bio quand on RENFORCE l'action `cible` sur ces etats."""
    ag.zero_grad(set_to_none=True)
    perte=0.0
    for o in lst:
        _,_,_,pb,lg=ag._executer_c1_reflexe(o,mem,ctx,bio)
        lg=lg.clone(); lg[...,7]=float('-inf')
        perte = perte - F.log_softmax(lg,dim=-1)[0,cible]
    (perte/len(lst)).backward()
    return torch.cat([p.grad.flatten().clone() for p in ag.integrateur_bio.parameters()
                      if p.grad is not None])
# meme action renforcee sur les deux classes -> les gradients sont-ils alignes ?
gr=grad_classe(caps["ressource"],3)   # 3 = ramasser
gm=grad_classe(caps["mur"],3)
cos=float(F.cosine_similarity(gr.unsqueeze(0),gm.unsqueeze(0)).item())
print(f"\n=== {B.split('/')[-1]} — {len(caps['ressource'])} res / {len(caps['mur'])} mur ===")
print(f"cos(grad_ressource, grad_mur) en renforcant `ramasser` : {cos:+.4f}")
print(f"   +1 = l'optimiseur pousse les deux etats DANS LA MEME DIRECTION (aucune separation possible)")
print(f"    0 = directions independantes")
print(f"   -1 = il les ecarte activement")
# et l'ecart de logit que ca produirait
with torch.no_grad():
    lr=[];lm=[]
    for o in caps["ressource"]:
        _,_,_,_,lg=ag._executer_c1_reflexe(o,mem,ctx,bio); lr.append(lg.cpu().numpy().ravel())
    for o in caps["mur"]:
        _,_,_,_,lg=ag._executer_c1_reflexe(o,mem,ctx,bio); lm.append(lg.cpu().numpy().ravel())
lr=np.array(lr); lm=np.array(lm)
print(f"\nlogit `ramasser` : ressource {lr[:,3].mean():+.4f}  mur {lm[:,3].mean():+.4f}  ecart {lr[:,3].mean()-lm[:,3].mean():+.4f}")
print(f"norme des logits : {np.linalg.norm(lr.mean(0)):.4f}  (une politique nette ferait >>1)")
