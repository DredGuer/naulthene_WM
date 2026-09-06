import argparse,json,os,shutil,warnings
warnings.filterwarnings("ignore")
import numpy as np, torch
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--brain",required=True); ap.add_argument("--json")
    a=ap.parse_args()
    import naulthene.cerveau.noyau as N
    from naulthene.cerveau.persistance import PersistanceAnatomique
    c=os.path.join(os.path.dirname(a.brain) or ".",f".relu_{os.path.basename(a.brain)}")
    shutil.copy2(a.brain,c)
    try:
        agent=PersistanceAnatomique(c).charger_ou_naitre(N.DEVICE).agent; agent.eval()
        env=N.gym.make("MiniGrid-LavaGapS5-v0"); obs,_=env.reset(seed=7)
        mem=torch.zeros(1,agent.dim_bus,device=N.DEVICE); ctx=torch.zeros(1,agent.dim_bus,device=N.DEVICE)
        vb=torch.zeros(1,N.DIM_VECTEUR_BIO,device=N.DEVICE); rng=np.random.RandomState(7)
        P=[];B=[]
        with torch.no_grad():
            for _ in range(400):
                img=torch.tensor(obs["image"].reshape(1,-1),dtype=torch.float32,device=N.DEVICE)/10.0
                bl,mn,_,pb,_=agent._executer_c1_reflexe(img,mem,ctx,vb)
                P.append(pb); B.append(bl); mem=mn.detach()
                obs,_,te,tr,_=env.step(int(rng.randint(0,7)))
                if te or tr:
                    obs,_=env.reset(seed=int(rng.randint(0,10**6))); mem=torch.zeros(1,agent.dim_bus,device=N.DEVICE)
        env.close()
        P=torch.cat(P,0); B=torch.cat(B,0)
        r={"brain":os.path.basename(a.brain),"dim_bus":int(agent.dim_bus),
           "relu_mortes_pensee_bio":float((P.max(0).values<=1e-8).float().mean()),
           "taux_zeros_pensee_bio":float((P<=1e-8).float().mean()),
           "relu_mortes_bus_latent":float((B.max(0).values<=1e-8).float().mean()),
           "sd_dims_vivantes":float(P.std(0)[P.max(0).values>1e-8].mean()) if (P.max(0).values>1e-8).any() else 0.0}
        print(f"  {r['brain']:<26} bus {r['dim_bus']:>4} | relu mortes pensee_bio {100*r['relu_mortes_pensee_bio']:>5.1f} % | bus_latent {100*r['relu_mortes_bus_latent']:>5.1f} %")
        if a.json: json.dump(r,open(a.json,"w"),indent=1)
    finally:
        try: os.remove(c)
        except OSError: pass
main()
