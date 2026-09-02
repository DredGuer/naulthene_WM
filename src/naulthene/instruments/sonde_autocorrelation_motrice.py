# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Adrien Nault — Naulthène AGI
"""L'AUTOCORRÉLATION MOTRICE — le geste a-t-il enfin une mémoire ? (v41.49)

JUGE N°1 de la brique B, en lecture seule.

Mesuré à l'Étape 0 (01/09/2026, `A_g66`, 10 851 ticks) :

    P(avancer_{t+1} | avancer_t) = 0,3743
    P(avancer)                   = 0,3758
    ratio                        = 0,9959      ← AUCUNE persistance motrice

⚠️ C'EST LE JUGE QUI PASSE EN PREMIER. Si le ratio ne décolle pas, l'information
cinématique n'a pas été captée par C1 — et la directivité n'est alors **pas
interprétable** : on serait devant une ablation VIDE, pas négative (règle de mesure §4).
C'est exactement ce qui manquait à la brique C, dont l'échec ne permettait pas de
distinguer « le mécanisme n'a pas mordu » de « il a mordu sans effet ».

LANCEMENT
    PYTHONPATH=src python -m naulthene.instruments.sonde_autocorrelation_motrice \\
        --brain <cerveau>.brain --episodes 40 --json <sortie>.json
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
ACTION_AVANCER = 2


def main() -> None:
    p = argparse.ArgumentParser(description="Le geste a-t-il une mémoire ?")
    p.add_argument("--brain", required=True)
    p.add_argument("--env", default=ENV_DEFAUT)
    p.add_argument("--episodes", type=int, default=40)
    p.add_argument("--graine", type=int, default=90210)
    p.add_argument("--json", default=None)
    a = p.parse_args()

    import gymnasium as gym
    import minigrid  # noqa: F401

    import naulthene.cerveau.noyau as N
    from naulthene.cerveau.persistance import PersistanceAnatomique

    copie = os.path.join(os.path.dirname(a.brain) or ".", f"_autocorr_{os.getpid()}.brain")
    shutil.copy2(a.brain, copie)
    etat = PersistanceAnatomique(copie).charger_ou_naitre(N.DEVICE)
    ag = etat.agent
    ag.eval()
    moteur = N.BiologicalHomeostasisEngine()
    elan = N.MoteurElan()

    seqs = []
    rng = random.Random(a.graine)
    with torch.no_grad():
        for ep in range(a.episodes):
            env = gym.make(a.env)
            obs, _ = env.reset(seed=a.graine + ep)
            elan.reinitialiser_episode(env)
            mem = torch.zeros(1, ag.dim_bus, device=N.DEVICE)
            epis, acts = [], []
            for _ in range(env.unwrapped.max_steps):
                v = torch.tensor(obs["image"].flatten(), dtype=torch.float32,
                                 device=N.DEVICE).unsqueeze(0) / 10.0
                # ⚠️ L'élan est FOURNI au vecteur bio, exactement comme en run — sinon le
                # banc mesurerait un agent privé du sens qu'on cherche à évaluer.
                bio = torch.tensor(moteur.obtenir_vecteur_bio(elan=elan.etat_courant()),
                                   dtype=torch.float32, device=N.DEVICE).unsqueeze(0)
                ctx = (torch.stack(epis).mean(dim=0) if epis else ag.contexte_vide())
                o = ag.penser(v, mem, ctx, bio, force_planification=0.5,
                              horizons_planification=(1, 3, 7), gamma_planif=0.9)
                mem = o[4]
                if mem.shape[-1] != ag.dim_bus:
                    raise RuntimeError("mémoire de travail de forme inattendue — banc amputé")
                epis.append(mem.detach())
                pr = torch.softmax(o[0].squeeze(0)[:N_ACTIONS], dim=-1).cpu().numpy()
                act = int(rng.choices(range(N_ACTIONS), weights=pr.tolist())[0])
                acts.append(act)
                obs, r, te, tr, _ = env.step(act)
                elan.observer(env)
                if te or tr:
                    break
            seqs.append(acts)
            env.close()

    plat = [x for s in seqs for x in s]
    n = len(plat)
    p_av = plat.count(ACTION_AVANCER) / max(n, 1)
    num = den = 0
    for s in seqs:
        for i in range(len(s) - 1):
            if s[i] == ACTION_AVANCER:
                den += 1
                num += int(s[i + 1] == ACTION_AVANCER)
    p_cond = num / max(den, 1)
    ratio = p_cond / p_av if p_av > 0 else float("nan")
    # Persistance toutes actions confondues, à comparer à l'uniforme 1/7.
    n2 = d2 = 0
    for s in seqs:
        for i in range(len(s) - 1):
            d2 += 1
            n2 += int(s[i + 1] == s[i])
    p_rep = n2 / max(d2, 1)
    steriles = sum(1 for x in plat if x >= 3) / max(n, 1)

    print(f"{os.path.basename(a.brain):<18} ticks={n:6d}  P(av)={p_av:.4f}  "
          f"P(av|av)={p_cond:.4f}  ratio={ratio:.4f}  "
          f"P(rep)={p_rep:.4f}  stériles={100*steriles:.1f} %")

    if a.json:
        import json as _json
        with open(a.json, "w", encoding="utf-8") as f:
            _json.dump({"cerveau": os.path.basename(a.brain).replace(".brain", ""),
                        "env": a.env, "episodes": a.episodes, "ticks": n,
                        "P_avancer": p_av, "P_avancer_sachant_avancer": p_cond,
                        "ratio_autocorrelation": ratio,
                        "P_repeter": p_rep, "part_steriles": steriles,
                        "reference_etape0": 0.9959},
                       f, ensure_ascii=False, indent=2)
    try:
        os.remove(copie)
    except OSError:
        pass


if __name__ == "__main__":
    main()
