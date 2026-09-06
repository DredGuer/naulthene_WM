"""SONDE — POURQUOI LA POLITIQUE DE C1 EST-ELLE PLATE ?

Mesure du 06/09 : il faut DOUBLER la norme de `pensee_bio` pour que C1 change d'avis dans
13 % des cas, alors que les 8 futurs du rollout ne different que de 8,12 % de cette norme.

Cette sonde decompose la variance des logits en deux parts :

    - INTER-ACTIONS  : var des logits MOYENS entre les 7 actions -> le biais structurel
    - INTRA-TEMPS    : var temporelle d'un logit donne          -> la reponse a l'etat

Si inter >> intra, le classement des actions est fixe par des BIAIS, et l'etat courant ne
peut pas le renverser : la politique est constante par morceaux.

⚠️ LECTURE SEULE, le .brain est COPIE avant chargement (regle de mesure §8).
"""
import argparse, json, os, shutil, warnings
warnings.filterwarnings("ignore")
import numpy as np, torch, torch.nn.functional as F


def mesurer(agent, N, n_ticks=400, graine=7, env_id="MiniGrid-LavaGapS5-v0"):
    env = N.gym.make(env_id)
    obs, _ = env.reset(seed=graine)
    mem = torch.zeros(1, agent.dim_bus, device=N.DEVICE)
    ctx = torch.zeros(1, agent.dim_bus, device=N.DEVICE)
    vb = torch.zeros(1, N.DIM_VECTEUR_BIO, device=N.DEVICE)
    rng = np.random.RandomState(graine)
    L, P = [], []
    with torch.no_grad():
        for _ in range(n_ticks):
            img = torch.tensor(obs["image"].reshape(1, -1), dtype=torch.float32,
                               device=N.DEVICE) / 10.0
            _, mn, _, pb, lg = agent._executer_c1_reflexe(img, mem, ctx, vb)
            L.append(lg[:, :N.NUM_ACTIONS_BASE]); P.append(pb)
            mem = mn.detach()
            obs, _, te, tr, _ = env.step(int(rng.randint(0, 7)))
            if te or tr:
                obs, _ = env.reset(seed=int(rng.randint(0, 10**6)))
                mem = torch.zeros(1, agent.dim_bus, device=N.DEVICE)
    env.close()
    L = torch.cat(L, 0); P = torch.cat(P, 0)
    mu = L.mean(0)
    s = mu.sort(descending=True).values
    pr = F.softmax(L, dim=-1)
    arg = L.argmax(-1)
    return {
        "var_inter_actions": float(mu.var()),
        "var_intra_temps": float(L.var(0).mean()),
        "ratio_inter_sur_intra": float(mu.var() / (L.var(0).mean() + 1e-12)),
        "marge_logits_moyens": float(s[0] - s[1]),
        "sd_temporel_logit": float(L.std(0).mean()),
        "entropie": float(-(pr * pr.clamp_min(1e-9).log()).sum(-1).mean()),
        "p_favorite": float(pr.max(dim=-1).values.mean()),
        "part_ticks_argmax_change": float((arg[1:] != arg[:-1]).float().mean()),
        "actions_distinctes_jouees": int(len(torch.unique(arg))),
        "norme_pensee": float(P.norm(dim=-1).mean()),
        "n_ticks": int(n_ticks),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--brain", required=True)
    ap.add_argument("--ticks", type=int, default=400)
    ap.add_argument("--json", default=None)
    a = ap.parse_args()
    import naulthene.cerveau.noyau as N
    from naulthene.cerveau.persistance import PersistanceAnatomique
    copie = os.path.join(os.path.dirname(a.brain) or ".",
                         f".plat_{os.path.basename(a.brain)}")
    shutil.copy2(a.brain, copie)
    try:
        agent = PersistanceAnatomique(copie).charger_ou_naitre(N.DEVICE).agent
        agent.eval()
        r = mesurer(agent, N, n_ticks=a.ticks); r["brain"] = os.path.basename(a.brain)
        print(f"  {r['brain']:<26} inter/intra {r['ratio_inter_sur_intra']:>6.2f} | "
              f"marge {r['marge_logits_moyens']:.3f} vs sd {r['sd_temporel_logit']:.3f} | "
              f"H {r['entropie']:.3f} | argmax change {100*r['part_ticks_argmax_change']:.1f} % | "
              f"{r['actions_distinctes_jouees']} actions")
        if a.json: json.dump(r, open(a.json, "w"), indent=1)
    finally:
        try: os.remove(copie)
        except OSError: pass


if __name__ == "__main__":
    main()
