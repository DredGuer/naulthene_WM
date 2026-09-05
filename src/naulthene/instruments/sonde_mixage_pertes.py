"""SONDE §7 — LA SECONDE TABLE DE MIXAGE : quel terme de perte SCULPTE le réseau ?

La table de mixage des RÉCOMPENSES a été mesurée (MIXAGE, 04/09 : `Bio` 57 %, `Env` 21,6 %).
Il en existe une SECONDE, jamais mesurée, un étage plus bas — `perte_totale` :

    JEPA + COEFF_PERTE_VOCALE*vocal + acteur + critique + entropie + TAUX_DISTILLATION_C1*distill

...sommée à poids 1 (aux deux coefficients près), puis UN SEUL `backward`, UN SEUL Adam,
UN SEUL `lr`. Six gradients d'organes différents dans le même pas.

Cette sonde rejoue une journée réelle, puis fait UN backward PAR TERME (jamais de `step`)
et relève la norme du gradient reçue par chaque couche. C'est la part de sculpture réelle,
pas la valeur de la perte — deux termes de même valeur peuvent avoir des gradients d'ordres
de grandeur différents.

⚠️ LECTURE SEULE : aucun `optimizer.step()`, le .brain est COPIÉ avant chargement.
⚠️ Le gradient est mesuré à l'état COURANT du cerveau (jour ~1500), pas moyenné sur la vie.

Usage :
    PYTHONPATH=src python -m naulthene.instruments.sonde_mixage_pertes \
        --brain brains/04092026_cursus_complet/LIBRE_g11.brain --ticks 300 --json s.json
"""
import argparse, json, os, shutil, warnings
warnings.filterwarnings("ignore")

import numpy as np
import torch
import torch.nn.functional as F

COUCHES = ("porte_visuelle", "hippocampe", "analyseur", "integrateur_bio",
           "tete_motrice", "cortex_prefrontal", "generateur_attente")


def _normes(agent):
    """Norme du gradient par couche, puis remise à zéro (jamais de step)."""
    out = {}
    for nom in COUCHES:
        c = getattr(agent, nom, None)
        if c is None:
            continue
        g = c.annexe_weight.grad
        out[nom] = 0.0 if g is None else float(g.norm())
    return out


def collecter(agent, N, n_ticks, graine):
    """Rejoue une journée réelle et retourne les tenseurs nécessaires aux pertes."""
    env = N.gym.make("MiniGrid-LavaGapS5-v0")
    obs, _ = env.reset(seed=graine)
    memoire = torch.zeros(1, agent.dim_bus, device=N.DEVICE)
    contexte = torch.zeros(1, agent.dim_bus, device=N.DEVICE)
    vbio = torch.zeros(1, N.DIM_VECTEUR_BIO, device=N.DEVICE)

    jepa, logps, ents, vals, rews, dones, bus_reels = [], [], [], [], [], [], []
    rng = np.random.RandomState(graine)
    for _ in range(n_ticks):
        img = torch.tensor(obs["image"].reshape(1, -1), dtype=torch.float32,
                           device=N.DEVICE) / 10.0
        # on passe par les VRAIES methodes du noyau : reconstruire la chaine a la main
        # ferait diverger la sonde du code mesure (piege de l'instrument, 01/09).
        (bus_latent, memoire_new, _pe, pensee_bio,
         logits) = agent._executer_c1_reflexe(img, memoire, contexte, vbio)
        valeur = agent.cortex_prefrontal(pensee_bio)

        d = torch.distributions.Categorical(logits=logits)
        a = d.sample()
        logps.append(d.log_prob(a).view(1))
        ents.append(d.entropy().view(1))
        vals.append(valeur.view(1, 1))

        obs, r, te, tr, _ = env.step(int(a.item()) % 7)
        rews.append(float(r) + rng.normal(0, .01))
        dones.append(bool(te or tr))

        # cible JEPA : le bus réel du tick suivant, reconstruit par le tronc
        img2 = torch.tensor(obs["image"].reshape(1, -1), dtype=torch.float32,
                            device=N.DEVICE) / 10.0
        with torch.no_grad():
            bus2, _, _ = agent._tronc_cerebral(img2, memoire_new.detach())
        onehot = agent.actions_eye[a.item() % agent.num_actions].unsqueeze(0)
        pred = agent._predire_bus(pensee_bio, onehot)
        jepa.append(F.mse_loss(pred, bus2.detach()))

        memoire = memoire_new.detach()
        if te or tr:
            obs, _ = env.reset(seed=int(rng.randint(0, 10**6)))
            memoire = torch.zeros(1, agent.dim_bus, device=N.DEVICE)
    env.close()
    return jepa, logps, ents, vals, rews, dones


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--brain", required=True)
    ap.add_argument("--ticks", type=int, default=300)
    ap.add_argument("--graine", type=int, default=7)
    ap.add_argument("--json", default=None)
    a = ap.parse_args()

    import naulthene.cerveau.noyau as N
    from naulthene.cerveau.persistance import PersistanceAnatomique

    copie = os.path.join(os.path.dirname(a.brain) or ".",
                         f".sonde_mix_{os.path.basename(a.brain)}")
    shutil.copy2(a.brain, copie)
    try:
        agent = PersistanceAnatomique(copie).charger_ou_naitre(N.DEVICE).agent
        agent.train()
        jepa, logps, ents, vals, rews, dones = collecter(agent, N, a.ticks, a.graine)

        # les retours Monte-Carlo, exactement comme apprendre_journee
        R, returns = 0.0, []
        for r, d in zip(reversed(rews), reversed(dones)):
            R = r + 0.95 * (0.0 if d else R)
            returns.insert(0, R)
        returns = torch.tensor(returns, dtype=torch.float32, device=N.DEVICE)
        if returns.numel() > 1 and returns.std() > 1e-6:
            returns = (returns - returns.mean()) / (returns.std() + 1e-8)
        v = torch.cat(vals).squeeze(-1)
        av = returns - v.detach()
        lp = torch.cat(logps).squeeze(-1)
        en = torch.cat(ents).squeeze(-1)

        termes = {
            "jepa":      torch.stack(jepa).mean(),
            "acteur":    -(lp * av).mean(),
            "critique":  F.mse_loss(v, returns),
            "entropie":  -0.02 * en.mean(),
        }

        res = {}
        for nom, perte in termes.items():
            agent.zero_grad(set_to_none=True)
            if not perte.requires_grad:
                res[nom] = {c: 0.0 for c in COUCHES}
                continue
            perte.backward(retain_graph=True)
            res[nom] = _normes(agent)
            res[nom]["_valeur_perte"] = float(perte.item())
        agent.zero_grad(set_to_none=True)

        r = {"brain": os.path.basename(a.brain), "ticks": a.ticks,
             "dim_bus": int(agent.dim_bus), "termes": res}
        print(f"\n  {r['brain']}  ({a.ticks} ticks, bus {agent.dim_bus})")
        print(f"  {'terme':<12}{'|perte|':>11}" + "".join(f"{c[:11]:>12}" for c in COUCHES))
        for nom, d in res.items():
            print(f"  {nom:<12}{abs(d.get('_valeur_perte',0)):>11.5f}"
                  + "".join(f"{d.get(c,0):>12.6f}" for c in COUCHES))
        if a.json:
            json.dump(r, open(a.json, "w"), indent=1)
    finally:
        try:
            os.remove(copie)
        except OSError:
            pass


if __name__ == "__main__":
    main()
