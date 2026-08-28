# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Adrien Nault — Naulthène AGI
"""Sonde du gradient reçu — que touche RÉELLEMENT `tete_motrice`, et que fait Adam ?

Instrument (v41.36) : joue des journées réelles et intercepte le clipping **à la source**
(la valeur retournée par `clip_grad_norm_`), jamais en relisant les `.grad` après coup —
c'est le bug « lecture après modification » qui avait produit une tautologie le 25/08.

⚠️ **Adam NORMALISE le pas** : `|ΔW| ≈ lr·√n`, indépendamment de `|∇W|`. Le ratio
`|∇W|/|W|` n'est donc PAS l'indicateur du déplacement — il faut mesurer `ΔW` directement.

RÉSULTAT (28/08/2026) : gradient brut 0,234 / 0,056 ; **g22 n'est clippé 0 nuit sur 5**
(norme globale 0,26 contre un plafond de 1,0) et ne progresse pas mieux pour autant — le
clipping n'est pas le coupable. Le pas réel vaut **0,93 % / 0,84 % de |W| par 5 nuits**,
conforme au pas théorique d'Adam (0,034 contre 0,031 mesuré).
"""
import numpy as np, torch, sys, copy
import naulthene.cerveau.noyau as N
from naulthene.cerveau.noyau import DEVICE, DIM_VECTEUR_BIO, creer_env, encoder
from naulthene.cerveau.persistance import PersistanceAnatomique
B=sys.argv[1]; G=11; JOURS=5; TICKS=400
rng=np.random.RandomState(G); torch.manual_seed(G)
etat=PersistanceAnatomique(B).charger_ou_naitre(); ag=etat.agent; db=ag.dim_bus
env=creer_env("MiniGrid-SimpleCrossingS9N1-v0",147); obs,_=env.reset(seed=G)
# espion sur le clip : on capture la valeur RETOURNEE, jamais relue apres coup
_vrai_clip=torch.nn.utils.clip_grad_norm_
_journal=[]
def _espion(params, maxn, *a, **k):
    params=list(params)
    brut_tm=sum(float(p.grad.norm()**2) for p in ag.tete_motrice.parameters() if p.grad is not None)**0.5
    tot=_vrai_clip(params,maxn,*a,**k)
    tot=float(tot)
    fac=min(1.0, maxn/(tot+1e-12))
    _journal.append((brut_tm, tot, fac))
    return tot
torch.nn.utils.clip_grad_norm_=_espion
W0=(ag.tete_motrice.base_weight.detach()+ag.tete_motrice.annexe_weight.detach()).cpu().numpy().copy()
mem=torch.zeros(1,db,device=DEVICE); ctx=torch.zeros(1,db,device=DEVICE)
bio=torch.full((1,DIM_VECTEUR_BIO),0.5,device=DEVICE)
ag.train()
for jour in range(JOURS):
    lps=[];vals=[];ents=[];rws=[];dns=[];trs=[];jp=[]
    mem=torch.zeros(1,db,device=DEVICE)
    for t in range(TICKS):
        u=env.unwrapped; pav,dav=tuple(u.agent_pos),int(u.agent_dir); po=u.carrying is not None
        bus,mn,_,pb,lg=ag._executer_c1_reflexe(encoder(obs),mem,ctx,bio)
        lg2=lg.clone(); lg2[...,7]=float('-inf')
        d=torch.distributions.Categorical(logits=lg2); a=d.sample()
        lps.append(d.log_prob(a)); ents.append(d.entropy()); vals.append(ag.cortex_prefrontal(pb))
        act=torch.zeros(1,ag.actions_eye.shape[0],device=DEVICE); act[0,int(a.item())]=1.0
        jp.append(torch.nn.functional.mse_loss(ag._predire_bus(pb.detach(),act), bus.detach()))
        mem=mn.detach()
        obs,r,te,tr,_=env.step(int(a.item()))
        trs.append(bool(tuple(u.agent_pos)!=pav or int(u.agent_dir)!=dav or (u.carrying is not None)!=po))
        rws.append(float(r)); dns.append(bool(te or tr))
        if te or tr: obs,_=env.reset(seed=G+jour*1000+t)
    ag.apprendre_journee(jp,lps,ents,vals,rws,dns,coeff_entropie=0.01,transitions=trs)
torch.nn.utils.clip_grad_norm_=_vrai_clip
W1=(ag.tete_motrice.base_weight.detach()+ag.tete_motrice.annexe_weight.detach()).cpu().numpy()
br=np.array([x[0] for x in _journal]); tot=np.array([x[1] for x in _journal]); fac=np.array([x[2] for x in _journal])
nW=np.linalg.norm(W0)
print(f"\n{'='*66}\n  {B.split('/')[-1]} — {JOURS} nuits reelles\n{'='*66}")
print(f"[1] gradient BRUT sur tete_motrice   : {br.mean():.6f}   (min {br.min():.6f} max {br.max():.6f})")
print(f"[2] norme globale AVANT clip         : {tot.mean():.6f}   (plafond 1.0)")
print(f"    nuits clippees                   : {int((tot>1.0).sum())}/{len(tot)}")
print(f"    facteur de reduction moyen       : x{fac.mean():.4f}")
print(f"[3] gradient EFFECTIF (post-clip)    : {(br*fac).mean():.6f}")
print(f"    ratio |grad_eff| / |W|           : {(br*fac).mean()/nW:.8f}")
print(f"\n[4] PAS REEL D'ADAM (ce qui compte vraiment)")
dW=W1-W0
print(f"    |W| avant                        : {nW:.6f}")
print(f"    |Delta W| sur {JOURS} nuits            : {np.linalg.norm(dW):.6f}")
print(f"    soit                             : {100*np.linalg.norm(dW)/nW:.4f} % de |W| par {JOURS} nuits")
print(f"    ⚠️ Adam NORMALISE le pas : |dW| ~ lr*sqrt(n_params), pas ~ |grad|")
print(f"    pas theorique d'Adam (lr={ag.lr}) : {ag.lr*np.sqrt(W0.size):.6f}")
# --- pivot angulaire ---
env2=creer_env("MiniGrid-SimpleCrossingS9N1-v0",147); o2,_=env2.reset(seed=G)
Ca={"a":[],"b":[]}
for t in range(3000):
    img=o2["image"] if isinstance(o2,dict) else None
    if img is not None:
        k="a" if (img[:,:,0]==8).any() else "b"
        if len(Ca[k])<120: Ca[k].append(encoder(o2))
    o2,_,te,tr,_=env2.step(int(rng.randint(0,7)))
    if te or tr: o2,_=env2.reset(seed=G+t)
def mo(l):
    v=[]
    with torch.no_grad():
        for o in l:
            _,_,_,p,_=ag._executer_c1_reflexe(o,mem,ctx,bio); v.append(p.cpu().numpy().ravel())
    return np.array(v).mean(0)
axe=mo(Ca["a"])-mo(Ca["b"]); axe/=np.linalg.norm(axe)
def al(Wx): return float(np.mean([abs(np.dot(w,axe)/np.linalg.norm(w)) for w in Wx[:7]]))
a0,a1=al(W0),al(W1)
print(f"\n[5] PIVOT VERS L'AXE INFORMATIF")
print(f"    alignement moyen avant           : {a0:.6f}")
print(f"    alignement moyen apres {JOURS} nuits  : {a1:.6f}")
print(f"    gain par nuit                    : {(a1-a0)/JOURS:+.8f}")
cible=1/np.sqrt(W0.shape[1])*3
if a1>a0 and (a1-a0)>0:
    print(f"    nuits pour atteindre 3x le hasard ({cible:.3f}) : {(cible-a1)/((a1-a0)/JOURS):.0f}")
else:
    print(f"    -> l'alignement N'AUGMENTE PAS : la couche ne pivote pas vers l'axe")
