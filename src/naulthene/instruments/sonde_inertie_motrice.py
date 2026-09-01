# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Adrien Nault — Naulthène AGI
"""L'INERTIE MOTRICE — le trajet se tend-il si la décision a une masse ? (v41.47)

Instrument de DIAGNOSTIC en lecture seule. N'entraîne rien, n'écrit dans aucun `.brain`.

---
L'HYPOTHÈSE TESTÉE

Mesuré le 31/08 : `r(directivité, succès) = −0,8225` (`t = −5,96`, n=19) — 68 % de la
variance du dépôt. Les victoires sont BROWNIENNES (13,8× à 22,8× le plus court chemin,
optimal médian 12 pas, budget 324 ticks).

Cause proposée : à chaque tick la tête motrice tire dans une multinomiale INDÉPENDANTE.
`left` et `right` (actions 0 et 1) s'annulent géométriquement à haute fréquence, et
`forward` (action 2) — la seule qui déplace — n'est tirée qu'une fois sur sept en moyenne.

Correctif proposé : une MASSE CINÉMATIQUE sur la décision, du même genre que les inerties
déjà présentes dans le noyau (`INERTIE_FLOTTAISON`, `INERTIE_REFERENCE_CHOC`, les demi-vies
de la douleur) :

    L_t = λ · L_{t-1} + (1 − λ) · logits_t

λ = 0 restitue EXACTEMENT le comportement actuel : c'est le témoin A/A.

---
⚠️ LE PIÈGE QUE CE BANC DOIT ÉCARTER

Un filtre autorégressif sur les logits n'est PAS neutre : il renforce mécaniquement
l'action déjà dominante. Si `forward` est le mode de la politique, l'inertie produit
« avancer tout droit » — un trajet tendu SANS AUCUNE COGNITION.

D'où le témoin obligatoire : un MARCHEUR ALÉATOIRE soumis à la même inertie (logits
tirés uniformément puis lissés). S'il gagne autant que le cerveau entraîné, l'effet est
une rectification mécanique de la trajectoire, pas une amélioration de la décision.

C'est la même discipline que « le témoin garde le SENS et ne coupe que la MÉCANIQUE »
(règle de mesure §6) : ici le témoin garde la MÉCANIQUE et coupe la COGNITION.

---
LANCEMENT

    PYTHONPATH=src python -m naulthene.instruments.sonde_inertie_motrice \\
        --brain <cerveau>.brain --lambdas 0,0.5,0.7,0.9 --episodes 300
"""
from __future__ import annotations

import argparse
import collections
import math
import os
import shutil

import numpy as np
import torch


ENV_DEFAUT = "MiniGrid-SimpleCrossingS9N1-v0"

# Les 7 actions réelles de MiniGrid. L'ordre est celui de `unwrapped.actions` :
# left=0, right=1, forward=2, pickup=3, drop=4, toggle=5, done=6.
# ⚠️ Aucune table de coût ni de préférence ici : le banc ne connaît que le NOMBRE.
N_ACTIONS = 7


# --- 1. LE PLUS COURT CHEMIN (BFS) ----------------------------------------------------
def plus_court_chemin(env) -> int | None:
    """Distance en CASES entre l'agent et le but, obstacles contournés.

    ⚠️ Compte les cases, pas les actions : une rotation coûte un tick de plus dans le
    jeu réel. C'est donc une borne INFÉRIEURE du trajet optimal — la directivité
    mesurée est par construction un peu PESSIMISTE, jamais optimiste.
    """
    g = env.unwrapped.grid
    depart = tuple(env.unwrapped.agent_pos)
    but = None
    for x in range(g.width):
        for y in range(g.height):
            c = g.get(x, y)
            if c is not None and c.type == "goal":
                but = (x, y)
    if but is None:
        return None
    vus = {depart}
    file = collections.deque([(depart, 0)])
    while file:
        (x, y), d = file.popleft()
        if (x, y) == but:
            return d
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if not (0 <= nx < g.width and 0 <= ny < g.height) or (nx, ny) in vus:
                continue
            c = g.get(nx, ny)
            if c is not None and c.type in ("wall", "lava"):
                continue
            vus.add((nx, ny))
            file.append(((nx, ny), d + 1))
    return None


# --- 2. LE FILTRE D'INERTIE -----------------------------------------------------------
class Inertie:
    """`L_t = λ·L_{t-1} + (1−λ)·logits_t` — une masse cinématique sur la décision.

    λ = 0 ⇒ passe-plat EXACT (aucune opération flottante ajoutée sur le chemin, donc
    le témoin A/A est bit-identique au banc du 30/08).

    ⚠️ L'état est remis à zéro à CHAQUE épisode : l'agent est téléporté sur une carte
    neuve, son élan moteur ne survit pas au `reset()`. Même raison que `_odeurs_precedentes`
    (v32.0), `brulure` (v41.26) et la mémoire de travail du banc du plancher.
    """

    __slots__ = ("lam", "etat")

    def __init__(self, lam: float):
        self.lam = float(lam)
        self.etat = None

    def __call__(self, logits: np.ndarray) -> np.ndarray:
        if self.lam <= 0.0:
            return logits
        if self.etat is None:
            self.etat = logits.copy()
        else:
            self.etat = self.lam * self.etat + (1.0 - self.lam) * logits
        return self.etat

    def reset(self) -> None:
        self.etat = None


def echantillonner(logits: np.ndarray, rng) -> int:
    pr = np.exp(logits - logits.max())
    pr = pr / pr.sum()
    if not np.isfinite(pr).all() or pr.sum() <= 0:
        raise RuntimeError("politique dégénérée — le banc mesurerait du bruit")
    return int(rng.choices(range(N_ACTIONS), weights=pr.tolist())[0])


# --- 3. LA BOUCLE DE JEU --------------------------------------------------------------
def jouer(env_id, episodes, graine_base, decideur, inertie, patience=None):
    """Retourne (taux, [(ticks, optimal)], stats_actions)."""
    import random

    import gymnasium as gym
    import minigrid  # noqa: F401

    succes = 0
    trajets = []
    compte_actions = np.zeros(N_ACTIONS, dtype=np.int64)
    for i in range(episodes):
        env = gym.make(env_id)
        obs, _ = env.reset(seed=graine_base + i)
        inertie.reset()
        if hasattr(decideur, "reset"):
            decideur.reset()
        opt = plus_court_chemin(env)
        budget = min(env.unwrapped.max_steps, patience or env.unwrapped.max_steps)
        rng = random.Random(graine_base + i)
        ticks = 0
        gagne = False
        while ticks < budget:
            a = echantillonner(inertie(decideur(env, obs, rng)), rng)
            compte_actions[a] += 1
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
    return succes / episodes, trajets, compte_actions


def intervalle_wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    m = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - m), min(1.0, c + m))


# --- 4. EXÉCUTION ---------------------------------------------------------------------
def main() -> None:
    p = argparse.ArgumentParser(description="L'inertie motrice tend-elle le trajet ?")
    p.add_argument("--brain", required=True)
    p.add_argument("--env", default=ENV_DEFAUT)
    p.add_argument("--episodes", type=int, default=300)
    p.add_argument("--graine", type=int, default=90210)
    p.add_argument("--lambdas", default="0,0.5,0.7,0.9")
    p.add_argument("--patience", type=int, default=None)
    p.add_argument("--json", default=None)
    a = p.parse_args()

    lambdas = [float(x) for x in a.lambdas.split(",")]

    import naulthene.cerveau.noyau as N
    from naulthene.cerveau.persistance import PersistanceAnatomique

    copie = os.path.join(os.path.dirname(a.brain) or ".",
                         f"_inertie_lecture_{os.getpid()}.brain")
    shutil.copy2(a.brain, copie)

    print("=" * 96)
    print(f"  L'INERTIE MOTRICE — {a.env}, {a.episodes} épisodes, graines appariées")
    print(f"  cerveau : {os.path.basename(a.brain)}")
    print("=" * 96)

    etat = PersistanceAnatomique(copie).charger_ou_naitre(N.DEVICE)
    agent = etat.agent
    agent.eval()
    moteur = N.BiologicalHomeostasisEngine()

    def decideur_cerveau():
        """Reproduit la politique RÉELLEMENT jouée : `penser()` complet (voix C1 + C2),
        vecteur bio du VRAI moteur (plusieurs neutres sont à 0,5, jamais 0), contexte
        épisodique = moyenne courante des latents de l'épisode."""
        memoire = None
        episodiques = []

        def un(env, obs, rng):
            nonlocal memoire, episodiques
            with torch.no_grad():
                v = torch.tensor(obs["image"].flatten(), dtype=torch.float32,
                                 device=N.DEVICE).unsqueeze(0) / 10.0
                bio = torch.tensor(moteur.obtenir_vecteur_bio(), dtype=torch.float32,
                                   device=N.DEVICE).unsqueeze(0)
                if memoire is None:
                    memoire = torch.zeros(1, agent.dim_bus, device=N.DEVICE)
                contexte = (torch.stack(episodiques).mean(dim=0)
                            if episodiques else agent.contexte_vide())
                sortie = agent.penser(v, memoire, contexte, bio,
                                      force_planification=0.5,
                                      horizons_planification=(1, 3, 7),
                                      gamma_planif=0.9)
                logits = sortie[0]
                # ⚠️ La mémoire de travail est en **[4]** (`memoire_actuelle`), pas en
                # [1] qui est la VALEUR d'état, un scalaire. Voir le commentaire complet
                # dans `sonde_gestes_steriles.py`.
                memoire = sortie[4]
                if memoire.shape[-1] != agent.dim_bus:
                    raise RuntimeError(
                        f"mémoire de travail de forme {tuple(memoire.shape)} au lieu de "
                        f"(1, {agent.dim_bus}) — le banc mesurerait un agent amputé")
                episodiques.append(memoire.detach())
                return logits.squeeze(0)[:N_ACTIONS].cpu().numpy().astype(np.float64)

        def reset():
            nonlocal memoire, episodiques
            memoire = None
            episodiques = []
        un.reset = reset
        return un

    def decideur_aleatoire():
        """LE TÉMOIN CRITIQUE — logits uniformes, donc AUCUNE cognition, mais soumis à
        la MÊME inertie. Sépare la rectification mécanique de la trajectoire d'une
        amélioration réelle de la décision.

        ⚠️ Les logits sont tirés au hasard à chaque tick (et non figés à zéro) : sinon
        l'inertie n'aurait rien à lisser et le témoin serait vide, pas négatif."""
        def un(env, obs, rng):
            return np.array([rng.gauss(0.0, 1.0) for _ in range(N_ACTIONS)])
        return un

    charge = {"cerveau": os.path.basename(a.brain).replace(".brain", ""),
              "env": a.env, "episodes": a.episodes, "graine": a.graine,
              "dim_bus": agent.dim_bus, "bras": {}}

    for etiquette, fab in (("cerveau", decideur_cerveau), ("aleatoire", decideur_aleatoire)):
        print(f"\n  ── {etiquette.upper()} " + "─" * (88 - len(etiquette)))
        for lam in lambdas:
            taux, trajets, actions = jouer(a.env, a.episodes, a.graine, fab(),
                                           Inertie(lam), patience=a.patience)
            k = round(taux * a.episodes)
            lo, hi = intervalle_wilson(k, a.episodes)
            ratios = [t / o for t, o in trajets]
            direct = float(np.median(ratios)) if ratios else None
            part_av = float(actions[2] / max(actions.sum(), 1))
            print(f"  λ={lam:<4} succès {100*taux:6.2f} % IC95 [{100*lo:4.1f} ; {100*hi:4.1f}]"
                  f"  ({k:3d}/{a.episodes})  directivité "
                  f"{('%6.2f×' % direct) if direct else '   n/a '}"
                  f"  part `forward` {100*part_av:5.1f} %")
            charge["bras"][f"{etiquette}_lam{lam}"] = {
                "lambda": lam, "politique": etiquette, "taux": taux,
                "lo": lo, "hi": hi, "n_victoires": len(trajets),
                "directivite_mediane": direct,
                "part_forward": part_av,
                "distribution_actions": actions.tolist(),
            }

    if a.json:
        import json as _json
        ck = torch.load(a.brain, map_location="cpu", weights_only=False)
        h = ck.get("historique_episodes_niveau", []) or []
        charge["maitrise_run"] = (100.0 * sum(1 for x in h if x) / len(h)) if h else None
        charge["jour"] = ck.get("jour")
        charge["niveau"] = ck.get("niveau_actuel")
        with open(a.json, "w", encoding="utf-8") as f:
            _json.dump(charge, f, ensure_ascii=False, indent=2)
        print(f"\n  📄 {a.json}")

    try:
        os.remove(copie)
    except OSError:
        pass
    print("=" * 96)


if __name__ == "__main__":
    main()
