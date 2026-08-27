# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Adrien Nault — Naulthène AGI
"""Sonde de perméabilité — à quel étage l'état cesse-t-il d'influencer la décision ?

Instrument de diagnostic **en lecture seule** (v41.32, Chantier 0) : charge un `.brain`,
lui présente des états délibérément CONTRASTÉS, et compare les vecteurs internes étage par
étage pour trouver où l'information se perd.

Ne sauvegarde JAMAIS le cerveau et ne fait tourner aucun apprentissage : le `.brain` passé
en argument ressort bit-identique. Même discipline que `irm_cerveau.py` et `sonde_c1_c2.py`.

POURQUOI CETTE SONDE (mesures du 23/08/2026)
--------------------------------------------
L'agent n'est **ni apathique ni aléatoire** — son entropie BAISSE (1,7695 → 1,7034) et il
est ~8700× plus décidé qu'un cerveau réellement éteint (écart au max ln(7) : 0,350 contre
0,00004 pour le cas v34.0-fix1). Il a donc des certitudes.

Mais sa réponse est **la même face à un mur et face à une pomme** : distance des politiques
0,194 contre un bruit d'échantillonnage de 0,213 (p95). **Ses certitudes ne dépendent pas de
ce qu'il perçoit.**

Cette sonde cherche l'étage où la transmission se rompt :

    bus_latent  →  pensee_bio  →  logits C1  /  valeur C2

| Signature | Verdict |
|---|---|
| `bus_latent` distinct, logits identiques | effondrement de représentation en profondeur |
| `bus_latent` déjà identique | portes sensorielles éteintes (cf. extinction v34.0) |
| tout distinct | la politique lit l'état, la cause est ailleurs |

⚠️ DEUX PROTOCOLES, ET C'EST VOULU
-----------------------------------
**(A) États FORGÉS** — jauges poussées aux extrêmes (satiété 0,0 contre 1,0…). Contraste
maximal, donc **borne SUPÉRIEURE** de la sensibilité du réseau. Mais ce sont des points
**hors distribution** : l'agent n'a peut-être jamais vécu une satiété à 1,0. Une réponse
plate sur un état jamais vu ne prouve pas grand-chose ; une réponse plate là **prouve
beaucoup**, car c'est le cas le plus favorable possible.

**(B) États RÉELS capturés en jeu** — deux ticks effectivement vécus, l'un face à une
ressource, l'autre face à un mur. C'est ce qui compte pour le comportement, mais le
contraste y est plus faible.

Lire les deux : (A) dit ce que le réseau PEUT distinguer, (B) ce qu'il distingue VRAIMENT.

MÉTRIQUE
--------
Distance cosinus (1 − cos) entre les deux vecteurs de chaque étage, dans [0, 2] :
**0 = identiques**, 1 = orthogonaux. Publiée à côté de la norme des deux vecteurs, parce
qu'une distance cosinus sur deux vecteurs quasi nuls n'a aucun sens — c'est le piège de la
v37.0 (« la norme est un mauvais indicateur d'apprentissage, vérifier la direction »),
appliqué en sens inverse : ici il faut vérifier la magnitude AVANT de lire la direction.

Usage :
    PYTHONPATH=src python -m naulthene.instruments.sonde_permeabilite <brain> [env_id] [ticks]
"""
import sys
import numpy as np
import torch

from naulthene.cerveau.noyau import (
    AGI_Naulthene, DEVICE, creer_env, encoder, DIM_VECTEUR_BIO,
    DetecteurRessourcesBiologiques, NB_SOURCES_FOOD, NB_SOURCES_WATER,
)
from naulthene.cerveau.persistance import PersistanceAnatomique


def _distance_cosinus(a: torch.Tensor, b: torch.Tensor) -> float:
    """1 − cos(a, b), dans [0, 2]. Retourne 0.0 si l'un des vecteurs est nul."""
    a, b = a.flatten().float(), b.flatten().float()
    na, nb = a.norm().item(), b.norm().item()
    if na < 1e-12 or nb < 1e-12:
        return 0.0
    return float(1.0 - torch.dot(a, b).item() / (na * nb))


def _etages(agent, obs, memoire, contexte, vecteur_bio):
    """Passe un état dans C1 et retourne les quatre vecteurs internes.

    Sous `torch.no_grad()` : aucun gradient, aucune modification du cerveau.
    """
    with torch.no_grad():
        bus, mem, pensee, pensee_bio, logits = agent._executer_c1_reflexe(
            obs, memoire, contexte, vecteur_bio)
        valeur_c2 = agent.cortex_prefrontal(pensee_bio)
    return {"bus_latent": bus, "pensee_bio": pensee_bio,
            "logits_C1": logits, "valeur_C2": valeur_c2}


def _vecteur_bio_forge(dim, satiete, hydratation, energie, contact):
    """Construit un vecteur bio aux jauges imposées.

    ⚠️ HORS DISTRIBUTION par construction — voir la note (A) en tête de module. Les
    positions suivent l'ordre de `obtenir_vecteur_bio`, dont les 4 premières dims sont les
    jauges ; le reste est laissé neutre à 0.5 (le neutre du projet, jamais 0.0 — invariants
    v32.0 clinotaxie et v36.0 rappel marquant).
    """
    v = np.full(dim, 0.5, dtype=np.float32)
    v[0], v[1], v[2] = satiete, hydratation, energie
    if dim > 4:
        v[4] = contact
    return torch.tensor(v, dtype=torch.float32, device=DEVICE).unsqueeze(0)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    chemin = sys.argv[1]
    env_id = sys.argv[2] if len(sys.argv) > 2 else "MiniGrid-SimpleCrossingS9N1-v0"
    ticks = int(sys.argv[3]) if len(sys.argv) > 3 else 600

    env = creer_env(env_id, 147)
    obs, _ = env.reset(seed=11)
    persistance = PersistanceAnatomique(chemin)
    etat = persistance.charger_ou_naitre()
    agent = etat.agent
    agent.eval()
    dim_bus = agent.dim_bus
    print(f"Cerveau : {chemin}\n  dim_bus={dim_bus} | env={env_id}\n")

    memoire = torch.zeros(1, dim_bus, device=DEVICE)
    contexte = torch.zeros(1, dim_bus, device=DEVICE)

    # ================= PROTOCOLE A — ÉTATS FORGÉS =================
    print("=" * 68)
    print("A. ÉTATS FORGÉS (contraste maximal — borne SUPÉRIEURE de sensibilité)")
    print("=" * 68)
    obs_t = encoder(obs)
    survie = _etages(agent, obs_t, memoire, contexte,
                     _vecteur_bio_forge(DIM_VECTEUR_BIO, 0.0, 0.0, 0.0, 1.0))
    confort = _etages(agent, obs_t, memoire, contexte,
                      _vecteur_bio_forge(DIM_VECTEUR_BIO, 1.0, 1.0, 1.0, 0.0))
    print("  (même image, jauges opposées : satiété/hydratation/énergie 0,0 contre 1,0)\n")
    print(f"  {'ÉTAGE':<14}{'DIST. COS':>11}{'|survie|':>11}{'|confort|':>11}")
    print("  " + "-" * 47)
    for k in ("bus_latent", "pensee_bio", "logits_C1"):
        d = _distance_cosinus(survie[k], confort[k])
        print(f"  {k:<14}{d:>11.6f}{survie[k].norm().item():>11.4f}"
              f"{confort[k].norm().item():>11.4f}")
    # ⚠️ `valeur_C2` est un SCALAIRE (cortex_prefrontal.out_features == 1) : une distance
    # cosinus sur une seule dimension ne peut valoir que 0 (même signe) ou 2 (signes
    # opposés) — elle ne mesure donc RIEN d'autre que le signe. On publie les deux valeurs
    # brutes, seule lecture honnête pour un scalaire.
    print(f"  {'valeur_C2':<14}{'(scalaire)':>11}{survie['valeur_C2'].item():>11.4f}"
          f"{confort['valeur_C2'].item():>11.4f}")

    # ================= PROTOCOLE B — ÉTATS RÉELS =================
    print("\n" + "=" * 68)
    print("B. ÉTATS RÉELS capturés en jeu (ce que l'agent distingue VRAIMENT)")
    print("=" * 68)
    detecteur = DetecteurRessourcesBiologiques(nb_sources_food=NB_SOURCES_FOOD,
                                               nb_sources_water=NB_SOURCES_WATER)
    detecteur.reinitialiser_episode(env)
    captures = {"ressource": [], "mur": []}
    mem_courante = torch.zeros(1, dim_bus, device=DEVICE)
    for t in range(ticks):
        e = env.unwrapped
        fx, fy = (int(v) for v in e.front_pos)
        est_res = (fx, fy) in detecteur.positions_food or (fx, fy) in detecteur.positions_water
        dedans = 0 <= fx < e.grid.width and 0 <= fy < e.grid.height
        objet = e.grid.get(fx, fy) if dedans else None
        est_mur = (not dedans) or (objet is not None and not objet.can_overlap()
                                   and not est_res)
        cle = "ressource" if est_res else ("mur" if est_mur else None)
        if cle is not None and len(captures[cle]) < 40:
            captures[cle].append(encoder(obs))
        obs, _, term, trunc, _ = env.step(int(np.random.randint(0, 7)))
        if term or trunc:
            obs, _ = env.reset(seed=11 + t)
            detecteur.reinitialiser_episode(env)
    n_res, n_mur = len(captures["ressource"]), len(captures["mur"])
    print(f"  Captures : {n_res} face à une RESSOURCE | {n_mur} face à un MUR\n")
    if n_res == 0 or n_mur == 0:
        print("  ⚠️ Un des deux échantillons est VIDE — rien à comparer, on ne publie pas")
        print("     de zéro (règle de mesure : ablation vide ≠ ablation négative).")
        return
    bio_neutre = _vecteur_bio_forge(DIM_VECTEUR_BIO, 0.5, 0.5, 0.5, 0.5)
    moyennes = {}
    for cle in ("ressource", "mur"):
        acc = None
        for o in captures[cle]:
            et = _etages(agent, o, mem_courante, contexte, bio_neutre)
            acc = et if acc is None else {k: acc[k] + et[k] for k in acc}
        moyennes[cle] = {k: v / len(captures[cle]) for k, v in acc.items()}
    print(f"  {'ÉTAGE':<14}{'DIST. COS':>11}{'|ressource|':>13}{'|mur|':>11}")
    print("  " + "-" * 49)
    for k in ("bus_latent", "pensee_bio", "logits_C1"):
        d = _distance_cosinus(moyennes["ressource"][k], moyennes["mur"][k])
        print(f"  {k:<14}{d:>11.6f}{moyennes['ressource'][k].norm().item():>13.4f}"
              f"{moyennes['mur'][k].norm().item():>11.4f}")
    print(f"  {'valeur_C2':<14}{'(scalaire)':>11}"
          f"{moyennes['ressource']['valeur_C2'].item():>13.4f}"
          f"{moyennes['mur']['valeur_C2'].item():>11.4f}")
    print("\n  ⚠️ Une distance cosinus sur des vecteurs quasi nuls n'a aucun sens :")
    print("     lire les normes AVANT les distances.")


if __name__ == "__main__":
    main()
