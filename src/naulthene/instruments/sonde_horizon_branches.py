"""§6.a — les branches du rollout divergent-elles A L'HORIZON 7 ?

La sonde jepa_action mesure la separation au tick immediat (ratio 0,48). Ici on mesure la
separation des `pensee_branche` A CHAQUE HORIZON du rollout reel, en reutilisant le code du
noyau (jamais une reimplementation : le piege de l'instrument, 01/09).

Si les branches convergent a h=7, une tete d'intention lisant la pensee finale filtrerait
du bruit.
"""
import argparse, json, os, shutil, warnings
warnings.filterwarnings("ignore")
import numpy as np, torch, torch.nn.functional as F

def separation_par_horizon(agent, N, n_etats=80, graine=7, horizons=(1,3,7)):
    env = N.gym.make("MiniGrid-LavaGapS5-v0")
    obs,_ = env.reset(seed=graine)
    memoire = torch.zeros(1, agent.dim_bus, device=N.DEVICE)
    contexte = torch.zeros(1, agent.dim_bus, device=N.DEVICE)
    vbio = torch.zeros(1, N.DIM_VECTEUR_BIO, device=N.DEVICE)
    rng = np.random.RandomState(graine)
    A = agent.num_actions
    sep = {h: [] for h in horizons}
    with torch.no_grad():
        for _ in range(n_etats):
            img = torch.tensor(obs["image"].reshape(1,-1), dtype=torch.float32,
                               device=N.DEVICE)/10.0
            (_, mem_new, _pe, pensee_bio, _lg) = agent._executer_c1_reflexe(
                img, memoire, contexte, vbio)
            # --- rollout REEL, recopie fidele de simuler_futur_et_planifier ---
            pb = pensee_bio.expand(A,-1); mb = mem_new.expand(A,-1)
            pas_prec = 0
            for i,h in enumerate(sorted(horizons)):
                for saut in range(h - pas_prec):
                    if i==0 and saut==0:
                        ap = agent.actions_eye
                    else:
                        ch = torch.argmax(agent.tete_motrice(pb), dim=-1)
                        ap = agent.actions_eye[ch]
                    fb = F.relu(agent._predire_bus(pb, ap))
                    fm = F.relu(agent.hippocampe(torch.cat([fb, mb], dim=-1)))
                    fp = F.relu(agent.analyseur(fm))
                    fp = F.relu(agent.integrateur_bio(
                        torch.cat([fp, vbio.expand(fp.shape[0],-1)], dim=-1)))
                    pb, mb = fp, fm
                pas_prec = h
                m = torch.cdist(pb, pb)
                iu = torch.triu_indices(A, A, offset=1)
                sep[h].append(float(m[iu[0],iu[1]].mean()))
            memoire = mem_new.detach()
            obs,_,te,tr,_ = env.step(int(rng.randint(0,7)))
            if te or tr:
                obs,_ = env.reset(seed=int(rng.randint(0,10**6)))
                memoire = torch.zeros(1, agent.dim_bus, device=N.DEVICE)
    env.close()
    return {h: float(np.mean(v)) for h,v in sep.items()}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--brain", required=True); ap.add_argument("--json", default=None)
    a = ap.parse_args()
    import naulthene.cerveau.noyau as N
    from naulthene.cerveau.persistance import PersistanceAnatomique
    copie = os.path.join(os.path.dirname(a.brain) or ".", f".h7_{os.path.basename(a.brain)}")
    shutil.copy2(a.brain, copie)
    try:
        agent = PersistanceAnatomique(copie).charger_ou_naitre(N.DEVICE).agent; agent.eval()
        s = separation_par_horizon(agent, N)
        r = {"brain": os.path.basename(a.brain), "separation": s,
             "ratio_h7_sur_h1": s[7]/(s[1]+1e-12)}
        print(f"  {r['brain']:<26} h1 {s[1]:.5f}  h3 {s[3]:.5f}  h7 {s[7]:.5f}   "
              f"h7/h1 {r['ratio_h7_sur_h1']:.4f}")
        if a.json: json.dump(r, open(a.json,"w"), indent=1)
    finally:
        try: os.remove(copie)
        except OSError: pass

if __name__ == "__main__": main()
