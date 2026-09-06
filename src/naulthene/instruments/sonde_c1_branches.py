"""SONDE — C1 DISTINGUE-T-IL LES FUTURS QU'ON LUI MONTRE ?

Dans `simuler_futur_et_planifier`, apres le premier pas, chaque branche est poursuivie par
`argmax(tete_motrice(pensee_branche))`. La question n'est pas « C1 conduit-il ? » mais
« C1 conduit-il DIFFEREMMENT selon la branche ? ».

Si C1 vote la MEME action sur les A branches, alors les A futurs convergent — non parce que
le rollout les ecrase, mais parce que C1 est INSENSIBLE a ce qu'on lui montre.

⚠️ LECTURE SEULE, le .brain est COPIE avant chargement (regle de mesure §8).
"""
import argparse, json, os, shutil, warnings
warnings.filterwarnings("ignore")
import numpy as np, torch, torch.nn.functional as F


def mesurer(agent, N, n_ticks=120, graine=7):
    env = N.gym.make("MiniGrid-LavaGapS5-v0")
    obs, _ = env.reset(seed=graine)
    mem = torch.zeros(1, agent.dim_bus, device=N.DEVICE)
    ctx = torch.zeros(1, agent.dim_bus, device=N.DEVICE)
    vb = torch.zeros(1, N.DIM_VECTEUR_BIO, device=N.DEVICE)
    rng = np.random.RandomState(graine)
    A = agent.num_actions
    distincts = []
    with torch.no_grad():
        for _ in range(n_ticks):
            img = torch.tensor(obs["image"].reshape(1, -1), dtype=torch.float32,
                               device=N.DEVICE) / 10.0
            _, mn, _, pbio, _ = agent._executer_c1_reflexe(img, mem, ctx, vb)
            pb, mb = pbio.expand(A, -1), mn.expand(A, -1)
            fb = F.relu(agent._predire_bus(pb, agent.actions_eye))
            fm = F.relu(agent.hippocampe(torch.cat([fb, mb], dim=-1)))
            fp = F.relu(agent.analyseur(fm))
            fp = F.relu(agent.integrateur_bio(
                torch.cat([fp, vb.expand(A, -1)], dim=-1)))
            ch = torch.argmax(agent.tete_motrice(fp), dim=-1)
            distincts.append(len(set(ch.tolist())))
            mem = mn.detach()
            obs, _, te, tr, _ = env.step(int(rng.randint(0, 7)))
            if te or tr:
                obs, _ = env.reset(seed=int(rng.randint(0, 10**6)))
                mem = torch.zeros(1, agent.dim_bus, device=N.DEVICE)
    env.close()
    d = np.array(distincts)
    return {"actions_distinctes_med": float(np.median(d)),
            "actions_distinctes_moy": float(d.mean()),
            "part_ticks_vote_unique": float((d == 1).mean()),
            "num_actions": int(A), "n_ticks": int(n_ticks)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--brain", required=True); ap.add_argument("--json", default=None)
    a = ap.parse_args()
    import naulthene.cerveau.noyau as N
    from naulthene.cerveau.persistance import PersistanceAnatomique
    copie = os.path.join(os.path.dirname(a.brain) or ".",
                         f".c1br_{os.path.basename(a.brain)}")
    shutil.copy2(a.brain, copie)
    try:
        agent = PersistanceAnatomique(copie).charger_ou_naitre(N.DEVICE).agent
        agent.eval()
        r = mesurer(agent, N); r["brain"] = os.path.basename(a.brain)
        print(f"  {r['brain']:<26} vote unique {100*r['part_ticks_vote_unique']:>5.1f} % "
              f"| actions distinctes med {r['actions_distinctes_med']:.1f}/{r['num_actions']}")
        if a.json: json.dump(r, open(a.json, "w"), indent=1)
    finally:
        try: os.remove(copie)
        except OSError: pass


if __name__ == "__main__":
    main()
