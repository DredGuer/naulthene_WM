# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Adrien Nault — Naulthène AGI
"""Sonde d'état synaptique — la nuit écrase-t-elle `tete_motrice`, ou regarde-t-elle ailleurs ?

Instrument **en lecture seule** (v41.36). Deux mesures : la norme rapportée à
`norme_naissance` (le plancher vital vaut 10 %), et l'alignement des 7 lignes de `W` sur
l'axe informatif `mean(but vu) − mean(but absent)`.

⚠️ **Le plancher du hasard est publié**, et il est indispensable : en dimension d, deux
vecteurs aléatoires ont |cos| ≈ 1/√d — soit 0,083 en dim 147. Un alignement de 0,09 n'est
donc PAS de l'orthogonalité « active », c'est le bruit. Un contrôle empirique sur 2000
vecteurs aléatoires accompagne chaque mesure.

RÉSULTAT (28/08/2026) : norme à **90–98 %** de la naissance (aucun écrasement nocturne),
alignement à **1× le plancher** sauf une ligne sur 21.
"""
import numpy as np, torch, sys
from naulthene.cerveau.noyau import DEVICE, DIM_VECTEUR_BIO, creer_env, encoder
from naulthene.cerveau.persistance import PersistanceAnatomique
B=sys.argv[1]; ENV=sys.argv[2] if len(sys.argv)>2 else "MiniGrid-SimpleCrossingS9N1-v0"; G=11
rng=np.random.RandomState(G); torch.manual_seed(G)
e=PersistanceAnatomique(B).charger_ou_naitre(); ag=e.agent; ag.eval(); db=ag.dim_bus
tm=ag.tete_motrice
W=tm.base_weight.detach().cpu().numpy().copy()
try: W=W+tm.annexe_weight.detach().cpu().numpy()
except Exception: pass
nb=tm.norme_naissance.item() if hasattr(tm,"norme_naissance") else None
nW=np.linalg.norm(W)
print(f"\n{'='*72}\n  {B.split('/')[-1]}  ({ENV})\n{'='*72}")
print("[1] NORME — la nuit ecrase-t-elle la tete motrice ?")
if nb:
    print(f"    norme actuelle   {nW:.6f}")
    print(f"    norme naissance  {nb:.6f}")
    print(f"    ratio            {100*nW/nb:.2f} %   (plancher vital = 10,00 %)")
    print(f"    -> {'🔴 COLLEE AU PLANCHER' if abs(100*nW/nb-10.0)<0.5 else '✅ au-dessus du plancher'}")
else: print(f"    norme actuelle {nW:.6f} (norme_naissance absente)")
print(f"    norme par ligne (7 actions jouables) :")
for i,n in enumerate(["gauche","droite","avancer","ramasser","poser","activer","parler"]):
    print(f"      {n:<10}{np.linalg.norm(W[i]):.6f}")
# ---------- l'axe informatif ----------
env=creer_env(ENV,147); obs,_=env.reset(seed=G)
mem=torch.zeros(1,db,device=DEVICE); ctx=torch.zeros(1,db,device=DEVICE)
bio=torch.full((1,DIM_VECTEUR_BIO),0.5,device=DEVICE)
C={"a":[],"b":[]}
for t in range(4000):
    u=env.unwrapped; o=encoder(obs)
    img=obs["image"] if isinstance(obs,dict) else None
    if img is not None:
        vu=(img[:,:,0]==8).any()
        k="a" if vu else "b"
        if len(C[k])<150: C[k].append(o)
    obs,_,te,tr,_=env.step(int(rng.randint(0,7)))
    if te or tr: obs,_=env.reset(seed=G+t)
def moy(lst):
    v=[]
    with torch.no_grad():
        for o in lst:
            _,_,_,p,_=ag._executer_c1_reflexe(o,mem,ctx,bio); v.append(p.cpu().numpy().ravel())
    return np.array(v)
A=moy(C["a"]); Bx=moy(C["b"])
axe=A.mean(0)-Bx.mean(0); axe_n=axe/np.linalg.norm(axe)
d=W.shape[1]
print(f"\n[2] ALIGNEMENT — W regarde-t-elle dans la direction de l'information ?")
print(f"    axe informatif = mean(but VU) - mean(but ABSENT), dim {d}")
print(f"    plancher du hasard en dim {d} : |cos| ~ {1/np.sqrt(d):.4f}")
print(f"    {'action':<12}{'|cos(W_i, axe)|':>18}{'x plancher':>12}")
for i,n in enumerate(["gauche","droite","avancer","ramasser","poser","activer","parler"]):
    w=W[i]; c=abs(float(np.dot(w,axe_n)/(np.linalg.norm(w)+1e-12)))
    print(f"    {n:<12}{c:>18.4f}{c*np.sqrt(d):>12.2f}")
# controle empirique du plancher
alea=[abs(float(np.dot(r,axe_n)/np.linalg.norm(r))) for r in rng.randn(2000,d)]
print(f"    ---")
print(f"    controle : 2000 vecteurs ALEATOIRES -> |cos| moyen {np.mean(alea):.4f}  p95 {np.percentile(alea,95):.4f}")
