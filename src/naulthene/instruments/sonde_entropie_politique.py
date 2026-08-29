# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Adrien Nault — Naulthène AGI
"""Sonde d'entropie — pourquoi la politique reste-t-elle plate, et QUELLE politique ?

Instrument (v41.39). Trois mesures sur un cerveau existant, sans campagne :

**[0] QUELLE POLITIQUE GOUVERNE.** ⚠️ La politique jouée est `voix_c1 + voix_c2`
(`penser()`, l. 1405), **pas** les logits bruts de `_executer_c1_reflexe`. Les 15 %
publiés le 27/08 venaient des logits **bruts** — mesure corrigée ici : la politique réelle
est à **23,9–26,2 %** et **1,83 d'entropie**, C2 apportant **+8 points de décision**.

**[1] ÉCRÊTAGE.** `gain_c1 = clamp(vigueur_min_c1(force) / amplitude_c1, 0,25 ; 4,0)`.
⚠️ Ce facteur n'est **pas produit par l'optimiseur** : il sature quand l'amplitude de C1 est
**faible**. La saturation est un *symptôme* de la faiblesse de C1, jamais une force
contrariée par une borne — distinguer les deux exige une **ablation**, pas une corrélation.

**[2] RÉPRESSION PAR L'ENTROPIE.** Norme du gradient de la perte d'entropie contre celle de
l'avantage, sur `tete_motrice`. RÉSULTAT : **0,4 % à 1,1 %**. `coeff_entropie` ne réprime
rien — hypothèse réfutée.
"""
import numpy as np, torch, torch.nn.functional as F, sys
import naulthene.cerveau.noyau as N
from naulthene.cerveau.noyau import (DEVICE, DIM_VECTEUR_BIO, creer_env, encoder,
                                      GAIN_C1_MIN, GAIN_C1_MAX)
from naulthene.cerveau.persistance import PersistanceAnatomique
B=sys.argv[1]; G=11; TICKS=400
rng=np.random.RandomState(G); torch.manual_seed(G)
etat=PersistanceAnatomique(B).charger_ou_naitre(); ag=etat.agent; db=ag.dim_bus
env=creer_env("MiniGrid-SimpleCrossingS9N1-v0",147); obs,_=env.reset(seed=G)
mem=torch.zeros(1,db,device=DEVICE); ctx=torch.zeros(1,db,device=DEVICE)

print(f"\n{'='*70}\n  {B.split('/')[-1]}\n{'='*70}")
# ---------- [0] + [1] : politique reelle vs logits bruts, et le gain ----------
gains=[]; ent_brut=[]; ent_jouee=[]; p_brut=[]; p_jouee=[]; ampl=[]
ag.eval()
for t in range(TICKS):
    vb=np.asarray(etat.moteur_bio.obtenir_vecteur_bio(),dtype=np.float32)
    bio=torch.tensor(vb,device=DEVICE).unsqueeze(0)
    with torch.no_grad():
        lg_f, val, _, pe, mn, bus, _, _ = ag.penser(encoder(obs), mem, ctx, bio,
                                                     force_planification=0.5)
        _,_,_,pb,lg_brut = ag._executer_c1_reflexe(encoder(obs),mem,ctx,bio)
    m=getattr(ag,"mesure_arbitrage",{})
    if m: gains.append(m.get("gain_c1",np.nan)); ampl.append(m.get("amplitude_c1",np.nan))
    for src,E,P in ((lg_brut,ent_brut,p_brut),(lg_f,ent_jouee,p_jouee)):
        x=src.clone(); x[...,7]=float('-inf')
        p=F.softmax(x,dim=-1).cpu().numpy().ravel()
        E.append(float(-(p*np.log(p+1e-12)).sum())); P.append(float(p.max()))
    mem=mn.detach()
    a=int(torch.distributions.Categorical(logits=lg_f.clone().index_fill_(-1,torch.tensor([7],device=DEVICE),float('-inf'))).sample().item())
    obs,r,te,tr,_=env.step(a)
    if te or tr: obs,_=env.reset(seed=G+t); mem=torch.zeros(1,db,device=DEVICE)
g=np.array(gains); mx=float(np.log(7))
print(f"[0] QUELLE POLITIQUE GOUVERNE ?   (entropie max = {mx:.4f})")
print(f"    logits BRUTS (C1 seul)  : entropie {np.mean(ent_brut):.4f}  P(favorite) {100*np.mean(p_brut):.2f} %")
print(f"    politique JOUEE (C1+C2) : entropie {np.mean(ent_jouee):.4f}  P(favorite) {100*np.mean(p_jouee):.2f} %")
print(f"    PPO (reference, 60 runs): entropie 1.667-1.704   P(favorite) 34,7-35,5 %")
print(f"\n[1] ECRETAGE DU GAIN C1   bornes [{GAIN_C1_MIN} ; {GAIN_C1_MAX}]")
print(f"    gain moyen        : {g.mean():.4f}   (min {g.min():.4f}  max {g.max():.4f})")
print(f"    ticks a la borne HAUTE ({GAIN_C1_MAX}) : {int((g>=GAIN_C1_MAX-1e-6).sum())}/{len(g)}  ({100*(g>=GAIN_C1_MAX-1e-6).mean():.1f} %)")
print(f"    ticks a la borne BASSE ({GAIN_C1_MIN}) : {int((g<=GAIN_C1_MIN+1e-6).sum())}/{len(g)}  ({100*(g<=GAIN_C1_MIN+1e-6).mean():.1f} %)")
print(f"    amplitude C1 brute : {np.nanmean(ampl):.4f}")

# ---------- [2] : la repression par l'entropie ----------
print(f"\n[2] LE GRADIENT : AVANTAGE contre ENTROPIE, sur tete_motrice")
ag.train()
lps=[];ents=[];vals=[];rws=[];dns=[];trs=[];jp=[]
mem=torch.zeros(1,db,device=DEVICE); obs,_=env.reset(seed=G)
for t in range(TICKS):
    u=env.unwrapped; pav,dav=tuple(u.agent_pos),int(u.agent_dir); po=u.carrying is not None
    vb=np.asarray(etat.moteur_bio.obtenir_vecteur_bio(),dtype=np.float32)
    bus,mn,_,pb,lg=ag._executer_c1_reflexe(encoder(obs),mem,ctx,torch.tensor(vb,device=DEVICE).unsqueeze(0))
    lg2=lg.clone(); lg2[...,7]=float('-inf')
    d=torch.distributions.Categorical(logits=lg2); a=d.sample()
    lps.append(d.log_prob(a)); ents.append(d.entropy()); vals.append(ag.cortex_prefrontal(pb))
    oh=torch.zeros(1,ag.actions_eye.shape[0],device=DEVICE); oh[0,int(a.item())]=1.0
    jp.append(F.mse_loss(ag._predire_bus(pb.detach(),oh),bus.detach()))
    mem=mn.detach(); obs,r,te,tr,_=env.step(int(a.item()))
    trs.append(bool(tuple(u.agent_pos)!=pav or int(u.agent_dir)!=dav or (u.carrying is not None)!=po))
    rws.append(float(r)); dns.append(bool(te or tr))
    if te or tr: obs,_=env.reset(seed=G+t)
rets=[];R=0.0
for rw,dn in zip(reversed(rws),reversed(dns)):
    R=rw+0.99*R*(0.0 if dn else 1.0); rets.insert(0,R)
rets=torch.tensor(rets,dtype=torch.float32,device=DEVICE)
if rets.std()>1e-6: rets=(rets-rets.mean())/(rets.std()+1e-8)
vt=torch.cat(vals).squeeze(-1); adv=rets-vt.detach()
lpt=torch.cat(lps).squeeze(-1); ent_t=torch.cat(ents).squeeze(-1)
msk=torch.tensor([1.0 if x else 0.0 for x in trs],device=DEVICE)
def norme(perte):
    ag.zero_grad(set_to_none=True); perte.backward(retain_graph=True)
    return sum(float(p.grad.norm()**2) for p in ag.tete_motrice.parameters() if p.grad is not None)**0.5
p_act=-((lpt*adv*msk).sum()/torch.clamp(msk.sum(),min=1.0))
COEF=getattr(etat,"coeff_entropie_jour",0.01)
p_ent=-COEF*ent_t.mean()
na,ne=norme(p_act),norme(p_ent)
ag.zero_grad(set_to_none=True)
print(f"    coeff_entropie utilise : {COEF}")
print(f"    ||grad AVANTAGE||  : {na:.6f}")
print(f"    ||grad ENTROPIE||  : {ne:.6f}")
print(f"    RATIO entropie/avantage : {ne/max(na,1e-12):.4f}")
print(f"    -> {'🔴 L ENTROPIE DOMINE' if ne>na else 'l avantage domine'}")
