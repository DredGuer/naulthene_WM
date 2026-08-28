# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Adrien Nault — Naulthène AGI
"""Sonde de collapse en NAVIGATION — le tronc encode-t-il l'espace là où l'agent bloque ?

Instrument **en lecture seule** (v41.35-fix1). Mesure la séparabilité de trois paires
d'états qui commandent des actions différentes en navigation, sur les niveaux 1-4 :

    A. mur en face      vs  case libre      → avancer ou tourner ?
    B. but VISIBLE      vs  but absent      → foncer ou explorer ?
    C. but DEVANT       vs  but sur le côté → avancer ou pivoter ?

⚠️ PUBLIE LE d-prime **ET** le cosinus, et c'est délibéré : le cosinus **sature** dans un
espace post-`relu` (voir `controle_saturation_cosinus.py`). Seul le d' est lisible ici — le
cosinus n'est conservé que pour rendre l'artefact visible.

RÉSULTAT (28/08/2026, 3 cerveaux, `SimpleCrossingS9N1`) : **l'agent n'est PAS
topologiquement aveugle.** Sur la paire décisive « but visible », le réseau AMPLIFIE la
séparation d'un facteur 3,5 à 4,4 (d' 0,824 → 2,891 / 3,613 / 3,017). Seule la paire
« mur / case libre » se dégrade (1,638 → 0,38–1,34).
"""
import numpy as np, torch, sys, json
from naulthene.cerveau.noyau import DEVICE, DIM_VECTEUR_BIO, creer_env, encoder
from naulthene.cerveau.persistance import PersistanceAnatomique
ENV=sys.argv[2] if len(sys.argv)>2 else "MiniGrid-SimpleCrossingS9N1-v0"
B=sys.argv[1]; G=11; N=6000; MAXC=150
rng=np.random.RandomState(G); torch.manual_seed(G)
e=PersistanceAnatomique(B).charger_ou_naitre(); ag=e.agent; ag.eval(); db=ag.dim_bus
env=creer_env(ENV,147); obs,_=env.reset(seed=G)
mem=torch.zeros(1,db,device=DEVICE); ctx=torch.zeros(1,db,device=DEVICE)
bio=torch.full((1,DIM_VECTEUR_BIO),0.5,device=DEVICE)
C={k:[] for k in ["mur","libre","but_vu","but_absent","but_devant","but_cote"]}
def ajoute(k,o):
    if len(C[k])<MAXC: C[k].append(o)
for t in range(N):
    u=env.unwrapped; o=encoder(obs)
    fx,fy=(int(v) for v in u.front_pos)
    dedans=0<=fx<u.grid.width and 0<=fy<u.grid.height
    ob=u.grid.get(fx,fy) if dedans else None
    if (not dedans) or (ob is not None and not ob.can_overlap()): ajoute("mur",o)
    elif ob is None: ajoute("libre",o)
    # le but est-il dans le champ visuel ? (obs 7x7x3, canal 0 = type d'objet ; 8 = goal)
    img=obs["image"] if isinstance(obs,dict) else None
    if img is not None:
        vus=np.argwhere(img[:,:,0]==8)
        if len(vus):
            ajoute("but_vu",o)
            # colonne 3 = axe central du champ (l'agent regarde droit devant)
            if np.abs(vus[:,0]-3).min()<=1: ajoute("but_devant",o)
            else: ajoute("but_cote",o)
        else: ajoute("but_absent",o)
    obs,_,te,tr,_=env.step(int(rng.randint(0,7)))
    if te or tr: obs,_=env.reset(seed=G+t); mem=torch.zeros(1,db,device=DEVICE)
def etages(lst):
    ob=[];bl=[];pb=[]
    with torch.no_grad():
        for o in lst:
            bus,_,_,p,_=ag._executer_c1_reflexe(o,mem,ctx,bio)
            ob.append(o.cpu().numpy().ravel()); bl.append(bus.cpu().numpy().ravel()); pb.append(p.cpu().numpy().ravel())
    return list(map(np.array,(ob,bl,pb)))
def cos(a,b):
    a,b=a.mean(0),b.mean(0)
    return float(np.dot(a,b)/(np.linalg.norm(a)*np.linalg.norm(b)+1e-12))
def plancher(X):
    """cos entre deux moities aleatoires de la MEME classe — le temoin."""
    v=[]
    for _ in range(60):
        i=rng.permutation(len(X)); h=len(X)//2
        v.append(cos(X[i[:h]],X[i[h:2*h]]))
    return float(np.mean(v))
print(f"\n{'='*82}")
print(f"  {B.split('/')[-1]}  sur  {ENV}")
print(f"{'='*82}")
print(f"  {'paire':<28}{'obs brute':>12}{'bus_latent':>12}{'pensee_bio':>12}{'plancher':>12}"
      f"{"d\' obs":>10}{"d\' bio":>10}")
print("  "+"-"*96)
for lbl,(k1,k2) in [("A. mur / case libre",("mur","libre")),
                    ("B. but vu / but absent",("but_vu","but_absent")),
                    ("C. but devant / but cote",("but_devant","but_cote"))]:
    if len(C[k1])<20 or len(C[k2])<20:
        print(f"  {lbl:<28}  echantillon insuffisant ({len(C[k1])}/{len(C[k2])})"); continue
    E1=etages(C[k1]); E2=etages(C[k2])
    pl=(plancher(E1[2])+plancher(E2[2]))/2
    # ⚠️ le cosinus SATURE dans un espace a activations positives (relu) : tout y est
    # proche de 1. Le d' (separabilite) ne sature pas — c'est lui qui tranche.
    def dprime(A,Bx):
        mu=A.mean(0)-Bx.mean(0); ec=np.linalg.norm(mu)
        s=(np.sqrt(((A-A.mean(0))**2).sum(1).mean())+np.sqrt(((Bx-Bx.mean(0))**2).sum(1).mean()))/2
        return float(ec/s) if s>1e-12 else 0.0
    dp_o=dprime(E1[0],E2[0]); dp_p=dprime(E1[2],E2[2])
    print(f"  {lbl:<28}{cos(E1[0],E2[0]):>12.4f}{cos(E1[1],E2[1]):>12.4f}{cos(E1[2],E2[2]):>12.4f}{pl:>12.4f}"
          f"{dp_o:>10.3f}{dp_p:>10.3f}")
print(f"\n  n : mur={len(C['mur'])} libre={len(C['libre'])} but_vu={len(C['but_vu'])} "
      f"but_absent={len(C['but_absent'])} devant={len(C['but_devant'])} cote={len(C['but_cote'])}")
