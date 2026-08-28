"""TEST DE FALSIFICATION v41.34 : le bruit perceptif a-t-il baisse ?

Hypothese : un signal de valeur atteignant porte_visuelle apprend a taire ce qui ne vaut
rien, donc |V(t+1)-V(t)| doit BAISSER au profit du signal utile.
Reference (cerveaux v41.33, tronc detache) : 0,0899 (g11) et 0,1085 (g44).

⚠️ Un bruit qui baisse ne suffit PAS : il pourrait baisser parce que V s'est APLATI
(collapse). On mesure donc aussi l'etendue de V et le RAPPORT SIGNAL/BRUIT — l'effet
causal du bit de portage rapporte au bruit. C'est le rapport qui compte, pas le bruit seul.
"""
import numpy as np, torch, sys, json, math
from naulthene.cerveau.noyau import DEVICE, DIM_VECTEUR_BIO, creer_env, encoder
from naulthene.cerveau.persistance import PersistanceAnatomique
C="brains/28082026_v4134_tronc"
GR=[11,22,33,44,55,66,77,88,99,111,122,133,144,155,166,177,188,199,211,222]
def mesurer(brain, G, n=1500):
    rng=np.random.RandomState(G); torch.manual_seed(G)
    e=PersistanceAnatomique(brain).charger_ou_naitre(); ag=e.agent; ag.eval(); db=ag.dim_bus
    env=creer_env("MiniGrid-DoorKey-6x6-v0",147); obs,_=env.reset(seed=G)
    mem=torch.zeros(1,db,device=DEVICE); ctx=torch.zeros(1,db,device=DEVICE)
    V=[]; ecarts_bit=[]
    for t in range(n):
        u=env.unwrapped; pa=u.carrying is not None; o=encoder(obs)
        vals={}
        for bit in (0.0,1.0):
            vb=np.full(DIM_VECTEUR_BIO,0.5,dtype=np.float32); vb[-1]=bit
            with torch.no_grad():
                _,mn,_,pb,lg=ag._executer_c1_reflexe(o,mem,ctx,torch.tensor(vb,device=DEVICE).unsqueeze(0))
                vals[bit]=float(ag.cortex_prefrontal(pb).item())
        ecarts_bit.append(vals[1.0]-vals[0.0]); V.append(vals[1.0 if pa else 0.0])
        vb=np.full(DIM_VECTEUR_BIO,0.5,dtype=np.float32); vb[-1]=1.0 if pa else 0.0
        with torch.no_grad():
            _,mn,_,_,lg=ag._executer_c1_reflexe(o,mem,ctx,torch.tensor(vb,device=DEVICE).unsqueeze(0))
        lg=lg.clone(); lg[...,7]=float('-inf')
        a=int(torch.distributions.Categorical(logits=lg).sample().item()); mem=mn.detach()
        obs,r,te,tr,_=env.step(a)
        if te or tr: obs,_=env.reset(seed=G+t); mem=torch.zeros(1,db,device=DEVICE)
    V=np.array(V); eb=np.array(ecarts_bit)
    bruit=float(np.abs(V[1:]-V[:-1]).mean())
    signal=float(abs(eb.mean()))
    return dict(bruit=bruit, signal=signal, snr=(signal/bruit if bruit>1e-12 else 0.0),
                etendue=float(V.max()-V.min()), std_V=float(V.std()))
res={}
for g in GR:
    res[str(g)]={b:mesurer(f"{C}/{b}_g{g}.brain",g) for b in "AB"}
    print(f"g{g} fait",flush=True)
json.dump(res,open(f"{C}/bruit_perceptif.json","w"),indent=1)
print("OK")
