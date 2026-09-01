# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Adrien Nault — Naulthène AGI
"""LES GESTES STÉRILES — quelle part du budget part en actions impossibles ? (v41.47)

Instrument de DIAGNOSTIC en lecture seule.

Mesuré le 26/08 (v41.28) : **57,2 %** des ticks en gestes stériles sur `Empty-5x5`,
`poser`/`activer`/`parler` stériles à **100 %**. Le correctif a rendu le geste stérile
plus CHER (travail tenté), pas moins FRÉQUENT. `CLAUDE.md` avait alors inscrit :

    « Si le gaspillage persiste après ce correctif, le levier suivant est le BÉNÉFICE
      (un geste qui ne change rien devrait n'apprendre rien), PAS un durcissement du coût. »

Ce banc mesure si le gaspillage a persisté, sur la cohorte entière.

⚠️ Sur `SimpleCrossingS9N1`, `pickup`/`drop`/`toggle` sont stériles PAR CONSTRUCTION
(aucun objet, aucune porte). `done` ne termine rien. Ces quatre actions ne peuvent
strictement rien changer au monde — la stérilité est ici une propriété de la CARTE,
lue sur l'API, jamais une table posée.

LANCEMENT
    PYTHONPATH=src python -m naulthene.instruments.sonde_gestes_steriles \\
        --brain <cerveau>.brain --episodes 60 --json <sortie>.json
"""
from __future__ import annotations

import argparse
import os
import random
import shutil

import numpy as np
import torch


ENV_DEFAUT = "MiniGrid-SimpleCrossingS9N1-v0"
N_ACTIONS = 7


def main() -> None:
    p = argparse.ArgumentParser(description="Quelle part du budget part en gestes stériles ?")
    p.add_argument("--brain", required=True)
    p.add_argument("--env", default=ENV_DEFAUT)
    p.add_argument("--episodes", type=int, default=60)
    p.add_argument("--graine", type=int, default=90210)
    p.add_argument("--json", default=None)
    a = p.parse_args()

    import gymnasium as gym
    import minigrid  # noqa: F401

    import naulthene.cerveau.noyau as N
    from naulthene.cerveau.persistance import PersistanceAnatomique

    copie = os.path.join(os.path.dirname(a.brain) or ".",
                         f"_steriles_{os.getpid()}.brain")
    shutil.copy2(a.brain, copie)
    etat = PersistanceAnatomique(copie).charger_ou_naitre(N.DEVICE)
    ag = etat.agent
    ag.eval()
    moteur = N.BiologicalHomeostasisEngine()

    # La stérilité est lue sur la CARTE, jamais déclarée : une action est stérile si
    # le monde ne peut pas y répondre. Ici : aucun objet ramassable, aucune porte.
    grille_a_objets = False
    e0 = gym.make(a.env)
    e0.reset(seed=a.graine)
    g = e0.unwrapped.grid
    for x in range(g.width):
        for y in range(g.height):
            c = g.get(x, y)
            if c is not None and c.type in ("key", "ball", "box", "door"):
                grille_a_objets = True
    e0.close()

    compte = np.zeros(N_ACTIONS, dtype=np.int64)
    inutiles = 0          # gestes n'ayant produit AUCUN changement d'état du monde
    total = 0
    succes = 0
    rng = random.Random(a.graine)
    with torch.no_grad():
        for ep in range(a.episodes):
            env = gym.make(a.env)
            obs, _ = env.reset(seed=a.graine + ep)
            mem, epis = None, []
            for _ in range(env.unwrapped.max_steps):
                v = torch.tensor(obs["image"].flatten(), dtype=torch.float32,
                                 device=N.DEVICE).unsqueeze(0) / 10.0
                bio = torch.tensor(moteur.obtenir_vecteur_bio(), dtype=torch.float32,
                                   device=N.DEVICE).unsqueeze(0)
                if mem is None:
                    mem = torch.zeros(1, ag.dim_bus, device=N.DEVICE)
                ctx = (torch.stack(epis).mean(dim=0) if epis else ag.contexte_vide())
                o = ag.penser(v, mem, ctx, bio, force_planification=0.5,
                              horizons_planification=(1, 3, 7), gamma_planif=0.9)
                L = o[0].squeeze(0)[:N_ACTIONS].cpu().numpy().astype(np.float64)
                # ⚠️ `penser()` retourne 8 valeurs : [0] logits, [1] VALEUR (scalaire),
                # [2] vocaux, [3] pensee_enrichie, [4] MEMOIRE_ACTUELLE, [5] bus_latent,
                # [6] routage, [7] indecision. La mémoire de travail est en **[4]**.
                # Lire [1] renvoie un tenseur (1,1) qu'un garde-fou sur `dim_bus` rejette
                # SILENCIEUSEMENT : l'agent tourne alors à mémoire NULLE. Défaut trouvé
                # le 01/09/2026 dans les trois sondes de banc — voir
                # docs/recherche/enquetes_closes/INSTRUMENT_01092026_la_memoire_du_banc.md
                mem = o[4]
                if mem.shape[-1] != ag.dim_bus:
                    raise RuntimeError(
                        f"mémoire de travail de forme {tuple(mem.shape)} au lieu de "
                        f"(1, {ag.dim_bus}) — le banc mesurerait un agent amputé")
                epis.append(mem.detach())
                pr = np.exp(L - L.max())
                pr /= pr.sum()
                act = int(rng.choices(range(N_ACTIONS), weights=pr.tolist())[0])
                avant = (tuple(env.unwrapped.agent_pos), env.unwrapped.agent_dir,
                         env.unwrapped.carrying)
                obs, r, te, tr, _ = env.step(act)
                apres = (tuple(env.unwrapped.agent_pos), env.unwrapped.agent_dir,
                         env.unwrapped.carrying)
                compte[act] += 1
                total += 1
                if avant == apres:
                    inutiles += 1
                if te or tr:
                    succes += 1 if r > 0 else 0
                    break
            env.close()

    part_st = float(compte[3:].sum() / max(total, 1))
    part_inutile = float(inutiles / max(total, 1))
    print(f"{os.path.basename(a.brain):<16} ticks={total:6d} "
          f"stériles={100*part_st:5.1f} % sans_effet={100*part_inutile:5.1f} % "
          f"succès={100*succes/a.episodes:5.1f} %")

    if a.json:
        import json as _json
        ck = torch.load(a.brain, map_location="cpu", weights_only=False)
        h = ck.get("historique_episodes_niveau", []) or []
        with open(a.json, "w", encoding="utf-8") as f:
            _json.dump({"cerveau": os.path.basename(a.brain).replace(".brain", ""),
                        "env": a.env, "episodes": a.episodes, "ticks": total,
                        "carte_a_objets": grille_a_objets,
                        "distribution_actions": compte.tolist(),
                        "part_steriles": part_st,
                        "part_sans_effet": part_inutile,
                        "succes": succes / a.episodes,
                        "dim_bus": ag.dim_bus,
                        "maitrise_run": ((100.0 * sum(1 for x in h if x) / len(h))
                                         if h else None)},
                       f, ensure_ascii=False, indent=2)
    try:
        os.remove(copie)
    except OSError:
        pass


if __name__ == "__main__":
    main()
