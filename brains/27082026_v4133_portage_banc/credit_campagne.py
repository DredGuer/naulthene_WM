"""Ventilation du credit sur les cerveaux finaux — bras A vs bras B, apparie."""
import numpy as np, torch, torch.nn.functional as F, json, sys
from naulthene.cerveau import noyau as N
from naulthene.cerveau.noyau import DEVICE, DIM_VECTEUR_BIO, creer_env, encoder
from naulthene.cerveau.persistance import PersistanceAnatomique
C="brains/27082026_v4133_portage_banc"
GR=[11,22,33,44,55,66,77,88,99,111,122,133,144,155,166,177,188,199,211,222]
JOURS=4; TICKS=400
def mesurer(brain, graine, portage_actif):
    rng=np.random.RandomState(graine); torch.manual_seed(graine)
    etat=PersistanceAnatomique(brain).charger_ou_naitre(); ag=etat.agent; ag.train()
    db=ag.dim_bus
    env=creer_env("MiniGrid-DoorKey-6x6-v0",147); obs,_=env.reset(seed=graine)
    cum={c:{"n":0,"A":[]} for c in ("sterile","neutre","utile")}
    Vp=[]; Vv=[]
    for jour in range(JOURS):
        mem=torch.zeros(1,db,device=DEVICE); ctx=torch.zeros(1,db,device=DEVICE)
        lps=[]; vals=[]; rws=[]; dns=[]; cls=[]
        for t in range(TICKS):
            u=env.unwrapped
            pav,dav=tuple(u.agent_pos),int(u.agent_dir); port_av=u.carrying is not None
            vb=np.full(DIM_VECTEUR_BIO,0.5,dtype=np.float32)
            vb[-1]= (1.0 if port_av else 0.0) if portage_actif else 0.0
            bio=torch.tensor(vb,device=DEVICE).unsqueeze(0)
            _,mn,_,pb,lg=ag._executer_c1_reflexe(encoder(obs),mem,ctx,bio)
            v=ag.cortex_prefrontal(pb)
            (Vp if port_av else Vv).append(float(v.detach().item()))
            lg=lg.clone(); lg[...,7]=float('-inf')
            d=torch.distributions.Categorical(logits=lg); act=d.sample()
            lps.append(d.log_prob(act)); vals.append(v); mem=mn.detach()
            obs,r,te,tr,_=env.step(int(act.item()))
            ab=tuple(u.agent_pos)!=pav; at=int(u.agent_dir)!=dav
            am=(u.carrying is not None)!=port_av
            cls.append("utile" if am else ("neutre" if (ab or at) else "sterile"))
            rws.append(float(r)); dns.append(bool(te or tr))
            if te or tr: obs,_=env.reset(seed=graine+jour*1000+t)
        rets=[]; R=0.0
        for rw,dn in zip(reversed(rws),reversed(dns)):
            R=rw+0.99*R*(0.0 if dn else 1.0); rets.insert(0,R)
        rets=torch.tensor(rets,dtype=torch.float32,device=DEVICE)
        if rets.numel()>1 and rets.std()>1e-6: rets=(rets-rets.mean())/(rets.std()+1e-8)
        vt=torch.cat(vals).squeeze(-1); adv=(rets-vt.detach()).cpu().numpy()
        for i,c in enumerate(cls):
            cum[c]["n"]+=1; cum[c]["A"].append(float(adv[i]))
    Au=np.abs(cum["utile"]["A"]); An=np.abs(cum["neutre"]["A"])
    ratio=Au.mean()/An.mean() if len(Au)>2 and An.mean()>1e-12 else None
    Vp=np.array(Vp); Vv=np.array(Vv)
    d=None
    if len(Vp)>10 and len(Vv)>10:
        s=np.sqrt((Vp.var()+Vv.var())/2); d=(Vp.mean()-Vv.mean())/s if s>1e-12 else 0.0
    return dict(ratio=ratio, n_utile=len(Au), n_neutre=len(An), dcohen=d,
                n_porte=len(Vp), n_vide=len(Vv))
res={}
for g in GR:
    res[str(g)]={}
    for bras,pa in (("A",True),("B",False)):
        res[str(g)][bras]=mesurer(f"{C}/{bras}_g{g}.brain", g, pa)
    print(f"g{g} fait", flush=True)
json.dump(res,open(f"{C}/credit_final.json","w"),indent=1)
print("OK")
