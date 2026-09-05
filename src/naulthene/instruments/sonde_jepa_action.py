"""SONDE §2.a — LE MODÈLE DU MONDE DISTINGUE-T-IL LES ACTIONS ?

C2 évalue ses 8 branches via `_predire_bus(pensee, action_onehot)` (noyau.py:1103), puis
`cortex_prefrontal` note chaque futur. Si `generateur_attente` produit quasiment le MÊME
bus futur quelle que soit l'action, alors `valeur_cumulee` est du bruit AVANT toute
normalisation — et aucune tête posée sur C2 ne pourra rien y changer.

    ratio = distance moyenne ENTRE ACTIONS  /  distance entre deux pensées successives

Le dénominateur est l'échelle du problème : « à quel point deux instants diffèrent ».
Un ratio proche de 0 signifie que choisir une action change moins l'avenir prédit que
laisser passer un tick — donc que le levier de l'agent est invisible à son modèle du monde.

⚠️ LECTURE SEULE. Aucune écriture, aucun pas d'optimiseur, le .brain est COPIÉ avant
chargement (règle de mesure §8 : un .brain est écrasé à chaque nuit).

Usage :
    PYTHONPATH=src python -m naulthene.instruments.sonde_jepa_action \
        --brain brains/04092026_cursus_complet/LIBRE_g11.brain --json sortie.json
"""
import argparse, json, os, shutil, warnings
warnings.filterwarnings("ignore")

import numpy as np
import torch


def mesurer(agent, n_etats=200, graine=7):
    """Retourne les distances inter-actions et inter-pensées, sur des pensées RÉELLES.

    Les pensées sont produites par le tronc à partir d'observations réelles (le monde
    de l'agent), jamais tirées au hasard dans l'espace latent : un vecteur gaussien
    n'est pas une pensée, et la sensibilité mesurée sur du bruit ne dit rien.
    """
    import naulthene.cerveau.noyau as N

    env = N.gym.make("MiniGrid-LavaGapS5-v0")
    obs, _ = env.reset(seed=graine)
    rng = np.random.RandomState(graine)

    memoire = torch.zeros(1, agent.dim_bus, device=N.DEVICE)
    A = agent.num_actions
    actions_1hot = agent.actions_eye                      # (A, A) identité

    pensees = []
    with torch.no_grad():
        for _ in range(n_etats):
            img = torch.tensor(obs["image"].reshape(1, -1), dtype=torch.float32,
                               device=N.DEVICE) / 10.0
            _, memoire, pensee = agent._tronc_cerebral(img, memoire)
            pensees.append(pensee)
            obs, _, te, tr, _ = env.step(int(rng.randint(0, 7)))
            if te or tr:
                obs, _ = env.reset(seed=int(rng.randint(0, 10**6)))
                memoire = torch.zeros(1, agent.dim_bus, device=N.DEVICE)
    env.close()

    d_actions, d_temps = [], []
    with torch.no_grad():
        for i, p in enumerate(pensees):
            # les A futurs prédits depuis CETTE pensée, un par action
            futurs = agent._predire_bus(p.expand(A, -1), actions_1hot)   # (A, dim_bus)
            # distance moyenne entre deux futurs d'actions DIFFÉRENTES
            m = torch.cdist(futurs, futurs)
            iu = torch.triu_indices(A, A, offset=1)
            d_actions.append(float(m[iu[0], iu[1]].mean()))
            # l'échelle : de combien la pensée bouge en un tick réel
            if i + 1 < len(pensees):
                d_temps.append(float(torch.norm(pensees[i + 1] - p)))

    return np.array(d_actions), np.array(d_temps)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--brain", required=True)
    ap.add_argument("--etats", type=int, default=200)
    ap.add_argument("--json", default=None)
    a = ap.parse_args()

    import naulthene.cerveau.noyau as N
    from naulthene.cerveau.persistance import PersistanceAnatomique

    copie = os.path.join(os.path.dirname(a.brain) or ".",
                         f".sonde_jepa_{os.path.basename(a.brain)}")
    shutil.copy2(a.brain, copie)
    try:
        etat = PersistanceAnatomique(copie).charger_ou_naitre(N.DEVICE)
        agent = etat.agent
        agent.eval()

        da, dt = mesurer(agent, n_etats=a.etats)
        ratio = float(da.mean() / (dt.mean() + 1e-12))

        r = {
            "brain": os.path.basename(a.brain),
            "dim_bus": int(agent.dim_bus),
            "num_actions": int(agent.num_actions),
            "d_inter_actions_moy": float(da.mean()),
            "d_inter_actions_med": float(np.median(da)),
            "d_temps_moy": float(dt.mean()),
            "ratio_action_sur_temps": ratio,
            "n_etats": int(a.etats),
        }
        print(f"  {r['brain']:<28} bus {r['dim_bus']:>4}  "
              f"δ_action {da.mean():>9.5f}  δ_temps {dt.mean():>9.5f}  "
              f"ratio {ratio:>8.4f}")
        if a.json:
            json.dump(r, open(a.json, "w"), indent=1)
    finally:
        try:
            os.remove(copie)
        except OSError:
            pass


if __name__ == "__main__":
    main()
