# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Adrien Nault — Naulthène AGI
"""LE PLANCHER GÉOMÉTRIQUE — ces 15 % sont-ils une compétence ou un tirage ? (v41.45)

Instrument de DIAGNOSTIC en lecture seule.

    Dix-huit variables internes ne corrèlent avec la maîtrise. Avant d'échafauder une
    dix-neuvième théorie, tester si le nombre qu'on cherche à expliquer mesure quoi que
    ce soit.

---
L'HYPOTHÈSE TESTÉE

Si un cerveau entraîné 1440 jours, un cerveau NEUF (Xavier, jamais entraîné) et un
marcheur ALÉATOIRE uniforme obtiennent des scores voisins sur `SimpleCrossingS9N1`,
alors les ~15 % observés ne mesurent pas un apprentissage qui plafonne : ils mesurent
la part des cartes où la brèche tombe sur la trajectoire par défaut. Le « plafond »
serait le **plancher thermique de la carte**.

⚠️ CE QUE LA BASELINE PPO CONTRAINT DÉJÀ. Sur ce même niveau, avec le même budget de
pas, trois PPO atteignent **27,1 % à 39,8 %** (60 runs, δ_A/A = 0,000000). Si les 15 %
étaient un plancher purement géométrique, PPO y serait collé aussi. L'hypothèse du
plancher prédit donc `aléatoire ≈ Naulthène ≪ PPO` — et c'est exactement ce que ce
banc peut réfuter ou confirmer.

---
DEUX MESURES

1. **Le taux de succès** de trois politiques sur les mêmes cartes (graines appariées) :
   entraîné (`eval()`, aucun apprentissage), neuf (Xavier), aléatoire uniforme sur les
   7 actions réelles.

2. **La DIRECTIVITÉ des victoires** : longueur du chemin parcouru rapportée au plus
   court chemin réel (BFS sur la grille). Une politique qui a compris la tâche s'approche
   de 1,0× ; une victoire brownienne consomme presque tout le budget.

Aucune écriture : les cerveaux sont lus depuis une COPIE, jamais sauvegardés.

---
LANCEMENT

    PYTHONPATH=src python -m naulthene.instruments.sonde_plancher_geometrique \\
        --brain <cerveau>.brain --episodes 300
"""
from __future__ import annotations

import argparse
import collections
import math
import os
import random
import shutil

import numpy as np
import torch


ENV_DEFAUT = "MiniGrid-SimpleCrossingS9N1-v0"


# --- 1. LE PLUS COURT CHEMIN RÉEL (BFS sur la grille) --------------------------------
def plus_court_chemin(env) -> int | None:
    """Nombre de PAS D'AVANCE minimal entre l'agent et le but, murs contournés.

    ⚠️ Compte les cases, pas les actions : une rotation coûte un tick de plus dans le
    jeu. C'est donc une borne INFÉRIEURE du trajet optimal — elle ne peut que
    SURESTIMER la directivité, jamais la flatter à la baisse.
    """
    u = env.unwrapped
    grille = u.grid
    depart = tuple(u.agent_pos)
    but = None
    for x in range(grille.width):
        for y in range(grille.height):
            o = grille.get(x, y)
            if o is not None and getattr(o, "type", None) == "goal":
                but = (x, y)
    if but is None:
        return None
    vus = {depart}
    file = collections.deque([(depart, 0)])
    while file:
        (x, y), d = file.popleft()
        if (x, y) == but:
            return d
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if not (0 <= nx < grille.width and 0 <= ny < grille.height):
                continue
            if (nx, ny) in vus:
                continue
            o = grille.get(nx, ny)
            if o is not None and getattr(o, "type", None) in ("wall", "lava"):
                continue
            vus.add((nx, ny))
            file.append(((nx, ny), d + 1))
    return None


# --- 2. LES TROIS POLITIQUES ----------------------------------------------------------
def jouer(politique, env_id, episodes, graine_base, agent=None, etat_fab=None,
          patience=None):
    """Retourne (taux_succes, [(ticks, optimal)] des victoires)."""
    import gymnasium as gym
    import minigrid  # noqa: F401

    succes = 0
    trajets = []
    for i in range(episodes):
        env = gym.make(env_id)
        obs, _ = env.reset(seed=graine_base + i)
        # ⚠️ La mémoire de travail DOIT repartir à chaque épisode : l'agent est
        # téléporté sur une carte neuve. Sans ce reset elle fuit d'un épisode au
        # suivant — bug de la première version de ce banc, corrigé avant publication.
        if agent is not None and hasattr(agent, "reset"):
            agent.reset()
        opt = plus_court_chemin(env)
        # ⚠️ En run l'agent ABANDONNE volontairement (abnégation, ~258 ticks mesurés)
        # avant `max_steps`. Le banc doit pouvoir mesurer les DEUX régimes : sans
        # patience il accorde plus de temps qu'en jeu, ce qui l'avantage.
        budget = min(env.unwrapped.max_steps, patience or env.unwrapped.max_steps)
        rng = random.Random(graine_base + i)
        ticks = 0
        gagne = False
        while ticks < budget:
            if politique == "aleatoire":
                a = rng.randrange(7)
            else:
                a = agent(env, obs, rng)
            obs, r, termine, tronque, _ = env.step(a)
            ticks += 1
            if termine or tronque:
                gagne = r > 0
                break
        if gagne:
            succes += 1
            if opt:
                trajets.append((ticks, opt))
        env.close()
    return succes / episodes, trajets


def intervalle_wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    m = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - m), min(1.0, c + m))


# --- 3. PROGRAMME ---------------------------------------------------------------------
def main() -> None:
    p = argparse.ArgumentParser(description="Les 15 % sont-ils une compétence ou un tirage ?")
    p.add_argument("--brain", required=True, help="cerveau entraîné (lu depuis une COPIE)")
    p.add_argument("--env", default=ENV_DEFAUT)
    p.add_argument("--episodes", type=int, default=300)
    p.add_argument("--graine", type=int, default=90210)
    p.add_argument("--patience", type=int, default=None,
                   help="troncature volontaire (défaut : max_steps de la carte). "
                        "La patience réelle mesurée en run est de ~258 ticks.")
    a = p.parse_args()

    import naulthene.cerveau.noyau as N
    from naulthene.cerveau.persistance import PersistanceAnatomique

    # ⚠️ jamais lire un .brain en place : `sauvegarder()` l'écraserait
    copie = os.path.join(os.path.dirname(a.brain) or ".", "_plancher_lecture.brain")
    shutil.copy2(a.brain, copie)

    print("=" * 96)
    print(f"  LE PLANCHER GÉOMÉTRIQUE — {a.env}, {a.episodes} épisodes, graines appariées")
    print("=" * 96)

    # ⚠️ `charger_ou_naitre` retourne un EtatCognitif, pas un modèle nu.
    etat = PersistanceAnatomique(copie).charger_ou_naitre(N.DEVICE)
    agent_e = etat.agent
    agent_e.eval()
    neuf = N.AGI_Naulthene(dim_visuelle=N.DIM_VISUELLE,
                           dim_bus=agent_e.dim_bus).to(N.DEVICE)
    neuf.eval()
    print(f"  cerveau : dim_bus={agent_e.dim_bus} · "
          f"{sum(q.numel() for q in agent_e.parameters())} paramètres")

    # Le moteur biologique fournit le vecteur bio dans son régime NEUTRE de départ
    # (jauges pleines), plutôt qu'un vecteur nul qui n'existe dans aucun run réel.
    moteur = N.BiologicalHomeostasisEngine()

    def fabrique(modele):
        """Reproduit la politique RÉELLEMENT jouée : `penser()` complet, donc
        `voix_c1 + voix_c2` — jamais les logits bruts de C1 seuls (erreur du 27/08,
        15,00 % publié pour C1 quand la politique jouée est à 23,89 %)."""
        memoire = None
        episodiques = []          # comme `etat.vecteurs_episodiques` en run

        def jouer_un(env, obs, rng):
            nonlocal memoire, episodiques
            with torch.no_grad():
                v = torch.tensor(obs["image"].flatten(), dtype=torch.float32,
                                 device=N.DEVICE).unsqueeze(0) / 10.0
                # ⚠️ JAMAIS un vecteur bio NUL. Plusieurs dimensions ont un neutre à
                # **0,5** et non 0 (clinotaxie v32.0, variation thermique v41.11, rappel
                # marquant v36.0 = [0.5, 0.0]) : des zéros feraient croire à l'agent qu'il
                # est affamé, en fuite olfactive permanente et entouré de mauvais
                # souvenirs — un régime qu'il n'a jamais appris. On demande donc le
                # vecteur au VRAI moteur biologique, exactement comme la boucle de jeu.
                bio_np = moteur.obtenir_vecteur_bio()
                bio = torch.tensor(bio_np, dtype=torch.float32,
                                   device=N.DEVICE).unsqueeze(0)
                if memoire is None:
                    memoire = torch.zeros(1, modele.dim_bus, device=N.DEVICE)
                # ⚠️ Le contexte épisodique n'est PAS un vecteur nul en run : c'est
                # `contexte_vide()` au premier tick, puis la MOYENNE des états latents
                # de l'épisode (noyau.py l.8590). Le banc doit reproduire les deux,
                # sinon il mesure un agent privé de sa mémoire de contexte.
                contexte = (torch.stack(episodiques).mean(dim=0)
                            if episodiques else modele.contexte_vide())
                sortie = modele.penser(v, memoire, contexte, bio,
                                       force_planification=0.5,
                                       horizons_planification=(1, 3, 7),
                                       gamma_planif=0.9)
                logits = sortie[0]
                memoire = sortie[1] if torch.is_tensor(sortie[1]) and \
                    sortie[1].shape[-1] == modele.dim_bus else memoire
                if torch.is_tensor(memoire) and memoire.shape[-1] == modele.dim_bus:
                    episodiques.append(memoire.detach())
                pr = torch.softmax(logits.squeeze(0)[:7], dim=-1).cpu().numpy()
                if not np.isfinite(pr).all() or pr.sum() <= 0:
                    raise RuntimeError("politique dégénérée — le banc mesurerait du bruit")
                return int(rng.choices(range(7), weights=(pr / pr.sum()).tolist())[0])

        def reset():
            nonlocal memoire, episodiques
            memoire = None
            episodiques = []      # vidé à chaque épisode, comme l.8289 en run
        jouer_un.reset = reset
        return jouer_un

    resultats = {}
    for label, pol, ag in (("entraîné (eval)", "modele", fabrique(agent_e)),
                           ("neuf (Xavier)", "modele", fabrique(neuf)),
                           ("aléatoire (7 actions)", "aleatoire", None)):
        taux, trajets = jouer(pol, a.env, a.episodes, a.graine, agent=ag,
                              patience=a.patience)
        k = round(taux * a.episodes)
        lo, hi = intervalle_wilson(k, a.episodes)
        resultats[label] = (taux, trajets, lo, hi)
        print(f"\n  {label:24s} succès {100*taux:5.2f} %  IC95 [{100*lo:4.1f} ; {100*hi:4.1f}]  "
              f"({k}/{a.episodes})")
        if trajets:
            ratios = [t / o for t, o in trajets]
            print(f"  {'':24s} directivité : {np.median(ratios):5.2f}× le plus court chemin "
                  f"(médiane sur {len(trajets)} victoires)")

    print("\n" + "=" * 96)
    print("  LECTURE")
    print("=" * 96)
    te = resultats["entraîné (eval)"][0]
    tn = resultats["neuf (Xavier)"][0]
    ta = resultats["aléatoire (7 actions)"][0]
    _, lo_e, hi_e = resultats["entraîné (eval)"][0], resultats["entraîné (eval)"][2], resultats["entraîné (eval)"][3]
    lo_a, hi_a = resultats["aléatoire (7 actions)"][2], resultats["aléatoire (7 actions)"][3]
    chevauche = not (lo_e > hi_a or lo_a > hi_e)
    print(f"  entraîné {100*te:.2f} %  ·  neuf {100*tn:.2f} %  ·  aléatoire {100*ta:.2f} %")
    if chevauche:
        print("  🔴 les intervalles de l'entraîné et de l'aléatoire SE CHEVAUCHENT :")
        print("     rien ne distingue la politique apprise d'un tirage — le score mesuré")
        print("     est le PLANCHER GÉOMÉTRIQUE de la carte, pas un apprentissage.")
    else:
        print("  ✅ les intervalles sont DISJOINTS : la politique apprise fait mieux qu'un")
        print("     tirage. Le score mesure une compétence réelle, si faible soit-elle.")
    print("\n  ⚠️ Référence : sur ce même niveau et ce même budget, PPO atteint 27,1–39,8 %")
    print("     (60 runs, δ_A/A = 0,000000).")
    try:
        os.remove(copie)
    except OSError:
        pass
    print("=" * 96)


if __name__ == "__main__":
    main()
