# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Adrien Nault — Naulthène AGI
"""Sonde d'avantage — quelle formule contraste réellement le geste utile ?

Instrument **en lecture seule** (v41.33). Rejoue des trajectoires sur un cerveau chargé et
compare trois formes d'avantage sur LES MÊMES ticks :

    MC   = returns normalisés − V(s)      ← ce que le code fait aujourd'hui
    TD   = r + γ·V(s') − V(s)             ← le « Clic! » immédiat
    GAE  = Σ (γλ)^k · δ_{t+k}             ← le Clic! lissé (λ = 0,95)

Ne sauvegarde jamais et n'entraîne rien : le `.brain` ressort inchangé.

RÉSULTAT (8 cerveaux × 2000 ticks, 27/08/2026) : **aucune ne contraste**. MC 1,275× ·
TD(0) 1,125× · GAE 1,161× — et le code actuel est le moins mauvais des trois. TD(0) est en
outre très instable (0,351× à 2,953× selon la graine). Voir
`docs/recherche/CLIC_27082026_le_td_error_ne_sauve_rien.md`.

⚠️ Le masque `ACTION_DEMANDER` (indice 7, `-inf`) est appliqué : softmaxer les 8 logits
bruts mesurerait une politique qui n'existe pas — l'entropie dépassait alors ln(7).
"""
import numpy as np, torch, sys
from naulthene.cerveau.noyau import DEVICE, DIM_VECTEUR_BIO, creer_env, encoder
from naulthene.cerveau.persistance import PersistanceAnatomique
GAMMA=0.99; LAM=0.95
def run(B,G,n=2000):
    rng=np.random.RandomState(G); torch.manual_seed(G)
    e=PersistanceAnatomique(B).charger_ou_naitre(); ag=e.agent; ag.eval(); db=ag.dim_bus
    env=creer_env("MiniGrid-DoorKey-6x6-v0",147); obs,_=env.reset(seed=G)
    mem=torch.zeros(1,db,device=DEVICE); ctx=torch.zeros(1,db,device=DEVICE)
    V=[];rw=[];dn=[];cls=[]
    for t in range(n):
        u=env.unwrapped; pav,dav=tuple(u.agent_pos),int(u.agent_dir); pa=u.carrying is not None
        vb=np.full(DIM_VECTEUR_BIO,0.5,dtype=np.float32); vb[-1]=1.0 if pa else 0.0
        with torch.no_grad():
            _,mn,_,pb,lg=ag._executer_c1_reflexe(encoder(obs),mem,ctx,torch.tensor(vb,device=DEVICE).unsqueeze(0))
            V.append(float(ag.cortex_prefrontal(pb).item()))
        lg=lg.clone(); lg[...,7]=float('-inf')
        a=int(torch.distributions.Categorical(logits=lg).sample().item()); mem=mn.detach()
        obs,r,te,tr,_=env.step(a)
        am=(u.carrying is not None)!=pa; ab=tuple(u.agent_pos)!=pav; at=int(u.agent_dir)!=dav
        cls.append("utile" if am else ("neutre" if (ab or at) else "sterile"))
        rw.append(float(r)); dn.append(bool(te or tr))
        if te or tr: obs,_=env.reset(seed=G+t); mem=torch.zeros(1,db,device=DEVICE)
    return map(np.array,(V,rw,dn,np.array(cls,dtype=object)))
def ratios(A,cls):
    u=np.abs(A[cls=="utile"]); n=np.abs(A[cls=="neutre"])
    return (u.mean()/n.mean() if len(u)>4 and n.mean()>1e-12 else None), len(u)
print(f"{'graine':<8}{'MC (actuel)':>14}{'TD(0)':>10}{'GAE(.95)':>11}{'n utile':>9}")
print("-"*54)
res={'MC':[],'TD':[],'GAE':[]}
for G in [11,22,33,44,55,66,77,88]:
    V,rw,dn,cls=run(f"brains/27082026_v4133_portage_banc/A_g{G}.brain",G)
    ret=np.zeros(len(rw)); R=0.0
    for i in range(len(rw)-1,-1,-1): R=rw[i]+GAMMA*(0.0 if dn[i] else R); ret[i]=R
    ret_n=(ret-ret.mean())/(ret.std()+1e-8) if ret.std()>1e-6 else ret
    A_mc=ret_n-V
    Vs=np.where(dn,0.0,np.append(V[1:],0.0)); delta=rw+GAMMA*Vs-V
    A_gae=np.zeros(len(delta)); acc=0.0
    for i in range(len(delta)-1,-1,-1):
        acc = delta[i] + GAMMA*LAM*(0.0 if dn[i] else acc); A_gae[i]=acc
    r1,nu=ratios(A_mc,cls); r2,_=ratios(delta,cls); r3,_=ratios(A_gae,cls)
    for k,v in (('MC',r1),('TD',r2),('GAE',r3)):
        if v: res[k].append(v)
    f=lambda x: f"{x:.3f}x" if x else "  —  "
    print(f"g{G:<7}{f(r1):>14}{f(r2):>10}{f(r3):>11}{nu:>9}")
print("-"*54)
print(f"{'moyenne':<8}{np.mean(res['MC']):>13.3f}x{np.mean(res['TD']):>9.3f}x{np.mean(res['GAE']):>10.3f}x")
