"""Le signal survit-il jusqu'au GESTE ? Distance des politiques + separabilite par action."""
import numpy as np, torch, torch.nn.functional as F
from naulthene.cerveau.noyau import (creer_env, encoder, DIM_VECTEUR_BIO, DEVICE,
    DetecteurRessourcesBiologiques, NB_SOURCES_FOOD, NB_SOURCES_WATER)
from naulthene.cerveau.persistance import PersistanceAnatomique
import sys
BRAIN=sys.argv[1]; ENV=sys.argv[2] if len(sys.argv)>2 else "MiniGrid-Empty-8x8-v0"
rng=np.random.RandomState(11); torch.manual_seed(11)
env=creer_env(ENV,147); obs,_=env.reset(seed=11)
etat=PersistanceAnatomique(BRAIN).charger_ou_naitre(); agent=etat.agent; agent.eval()
db=agent.dim_bus
mem=torch.zeros(1,db,device=DEVICE); ctx=torch.zeros(1,db,device=DEVICE)
bio=torch.tensor(np.full(DIM_VECTEUR_BIO,0.5,dtype=np.float32),device=DEVICE).unsqueeze(0)
det=DetecteurRessourcesBiologiques(nb_sources_food=NB_SOURCES_FOOD,nb_sources_water=NB_SOURCES_WATER)
det.reinitialiser_episode(env)
caps={"ressource":[], "mur":[]}
for t in range(4000):
    e=env.unwrapped; fx,fy=(int(v) for v in e.front_pos)
    er=(fx,fy) in det.positions_food or (fx,fy) in det.positions_water
    dd=0<=fx<e.grid.width and 0<=fy<e.grid.height
    ob=e.grid.get(fx,fy) if dd else None
    em=(not dd) or (ob is not None and not ob.can_overlap() and not er)
    c="ressource" if er else ("mur" if em else None)
    if c and len(caps[c])<400: caps[c].append(encoder(obs))
    obs,_,te,tr,_=env.step(int(rng.randint(0,7)))
    if te or tr: obs,_=env.reset(seed=11+t); det.reinitialiser_episode(env)
def probs(lst):
    P=[]
    with torch.no_grad():
        for o in lst:
            _,_,_,pb,lg=agent._executer_c1_reflexe(o,mem,ctx,bio)
            # ⚠️ ACTION_DEMANDER (indice 7) est masquée à -inf en jeu tant qu'aucun plug
            # C3 n'est enregistré (invariant v30.0). Softmaxer les 8 logits bruts mesure
            # une politique QUI N'EXISTE PAS : l'entropie dépassait ln(7).
            lg = lg.clone(); lg[..., 7] = float('-inf')
            P.append(F.softmax(lg,dim=-1).cpu().numpy().ravel())
    return np.array(P)
R=probs(caps["ressource"]); M=probs(caps["mur"])
print(f"\ncaptures : {len(R)} res / {len(M)} mur")
tv=0.5*np.abs(R.mean(0)-M.mean(0)).sum()
# plancher de bruit : deux moities du meme groupe
def plancher(X,nb=400):
    ds=[]
    for _ in range(nb):
        i=rng.permutation(len(X)); h=len(X)//2
        ds.append(0.5*np.abs(X[i[:h]].mean(0)-X[i[h:2*h]].mean(0)).sum())
    return np.percentile(ds,95)
pl=max(plancher(R),plancher(M))
print(f"\nDISTANCE DES POLITIQUES (variation totale) : {tv:.6f}")
print(f"plancher de bruit (p95 intra)              : {pl:.6f}")
print(f"VERDICT : {'SIGNAL' if tv>pl else 'NOYE'}   (rapport {tv/pl:.2f}x)")
NOMS=["gauche","droite","avancer","ramasser","poser","activer","parler"]
print(f"\n{'action':<10}{'P(res)':>9}{'P(mur)':>9}{'ecart':>9}")
print("-"*37)
for i,n in enumerate(NOMS):
    if i<R.shape[1]:
        print(f"{n:<10}{R[:,i].mean():>9.4f}{M[:,i].mean():>9.4f}{R[:,i].mean()-M[:,i].mean():>+9.4f}")
print(f"\naction preferee  res : {NOMS[int(R.mean(0).argmax())]}   mur : {NOMS[int(M.mean(0).argmax())]}")
print(f"entropie         res : {-(R.mean(0)*np.log(R.mean(0)+1e-12)).sum():.4f}   mur : {-(M.mean(0)*np.log(M.mean(0)+1e-12)).sum():.4f}   (max={np.log(7):.4f})")
