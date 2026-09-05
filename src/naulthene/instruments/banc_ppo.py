# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Adrien Nault — Naulthène AGI
"""Banc PPO — la ligne de base qui manque au §3, et l'échelle des quatre grandeurs orphelines.

Entraîne un PPO `stable-baselines3` dans **exactement** les conditions de Naulthène, puis
mesure sur lui les **mêmes grandeurs, dans les mêmes unités** :

| Grandeur | Naulthène (mesuré) | Ce banc |
|---|---|---|
| proba de l'action favorisée face à un état informatif | **15,00 %** (plafond géométrique 18,00 %) | ← la question |
| entropie de la politique | 1,93 / max 1,946 | ← |
| d' `but visible / but absent` dans la dernière couche | 2,891 – 3,613 | ← |
| dérive de cette représentation | 0,42 °/nuit | ← |
| taux de réussite | ~16 % de maîtrise | ← |

⚠️ **ÉQUITÉ — ce qui est verrouillé** (voir `brains/29082026_baseline_ppo/PROTOCOLE.md`)
- observation **aplatie** 7×7×3 = 147 dims, `MlpPolicy` — jamais `CnnPolicy` :
  `porte_visuelle` est une couche **linéaire** sans convolution, donner un biais spatial à
  PPO fausserait tout ;
- **7 actions**, pas 8 — Naulthène masque `ACTION_DEMANDER` à `-inf` (invariant v30.0) ;
- **152 043 pas d'environnement** — 🔴 *mesuré* dans `tick_absolu` d'un cerveau réel après
  400 jours, jamais le nominal 400×400 = 160 000, qui est faux (journées écourtées) ;
- récompense **brute** MiniGrid, aucun shaping.

⚠️ **UN PPO BIEN RÉGLÉ N'EST PAS « LA NORMALE ».** C'est *une* référence. Un PPO mal réglé
plafonnerait aussi, et cette mesure ne dit rien de la vérité de la tâche — seulement d'un
point de comparaison qui n'existait pas.

⚠️ `stable-baselines3` est une dépendance **d'instrument**, jamais importée par le cœur.

Usage :
    PYTHONPATH=src python -m naulthene.instruments.banc_ppo --arch 69 --graine 11 \
        --pas 152043 --sortie resultat.json
    PYTHONPATH=src python -m naulthene.instruments.banc_ppo --aa      # contrôle A/A
"""
import argparse, json, warnings
import numpy as np
import gymnasium as gym
import torch

warnings.filterwarnings("ignore")

PAS_MESURES = 152_043          # tick_absolu réel, A_g11 à 400 jours — jamais estimé
ENV_ID = "MiniGrid-SimpleCrossingS9N1-v0"
N_ACTIONS = 7                  # Naulthène en joue 7 : ACTION_DEMANDER est masquée


class ObsAplatie(gym.ObservationWrapper):
    """7×7×3 → 147 dims, comme l'entrée de `porte_visuelle`. Aucun CNN."""
    def __init__(self, env):
        super().__init__(env)
        n = int(np.prod(env.observation_space["image"].shape))
        self.observation_space = gym.spaces.Box(0.0, 255.0, (n,), dtype=np.float32)

    def observation(self, obs):
        return obs["image"].astype(np.float32).ravel()


class SeptActions(gym.ActionWrapper):
    """Restreint à 7 actions — parité stricte avec le masque `-inf` de Naulthène."""
    def __init__(self, env):
        super().__init__(env)
        self.action_space = gym.spaces.Discrete(N_ACTIONS)

    def action(self, a):
        return int(a)


def faire_env(graine):
    import minigrid  # noqa: F401  (enregistre les environnements MiniGrid)
    e = gym.make(ENV_ID)
    e = ObsAplatie(SeptActions(e))
    e.reset(seed=graine)
    return e


def _capturer(env, modele, graine, n=3000, cap=150):
    """États réels triés en `but visible` / `but absent`, et latents de la politique."""
    obs, _ = env.reset(seed=graine)
    rng = np.random.RandomState(7)
    C = {"a": [], "b": []}
    for t in range(n):
        img = obs.reshape(7, 7, 3)
        k = "a" if (img[:, :, 0] == 8).any() else "b"
        if len(C[k]) < cap:
            C[k].append(obs.copy())
        obs, _, te, tr, _ = env.step(int(rng.randint(0, N_ACTIONS)))
        if te or tr:
            obs, _ = env.reset(seed=graine + t)
    return C


def _latents_et_probas(modele, lots):
    """Dernière couche cachée de la politique + distribution d'actions."""
    pol = modele.policy
    X = torch.as_tensor(np.array(lots), dtype=torch.float32, device=pol.device)
    with torch.no_grad():
        feats = pol.extract_features(X)
        if isinstance(feats, tuple):
            feats = feats[0]
        lat = pol.mlp_extractor.forward_actor(feats)
        dist = pol.get_distribution(X)
        p = dist.distribution.probs
    return lat.cpu().numpy(), p.cpu().numpy()


def _dprime(A, B):
    mu = A.mean(0) - B.mean(0)
    s = (np.sqrt(((A - A.mean(0)) ** 2).sum(1).mean())
         + np.sqrt(((B - B.mean(0)) ** 2).sum(1).mean())) / 2
    return float(np.linalg.norm(mu) / s) if s > 1e-12 else 0.0


def _axe(lat_a, lat_b):
    a = lat_a.mean(0) - lat_b.mean(0)
    n = np.linalg.norm(a)
    return a / n if n > 1e-12 else None


def _reussite(env, modele, graine, n_ep=300):
    ok = 0
    for i in range(n_ep):
        obs, _ = env.reset(seed=graine + 10_000 + i)
        for _ in range(400):
            a, _ = modele.predict(obs, deterministic=False)
            obs, r, te, tr, _ = env.step(int(a))
            if te or tr:
                ok += int(r > 0)
                break
    return ok / n_ep


def entrainer(arch, graine, pas, jalons=6):
    """Entraîne et mesure. `jalons` points intermédiaires → la dérive de représentation."""
    from stable_baselines3 import PPO
    env = faire_env(graine)
    modele = PPO("MlpPolicy", env, seed=graine, verbose=0,
                 policy_kwargs=dict(net_arch=dict(pi=[arch, arch], vf=[arch, arch])))
    n_par = sum(p.numel() for p in modele.policy.parameters())
    env_mes = faire_env(graine)
    C = _capturer(env_mes, modele, graine)
    axes = []
    par_jalon = max(1, pas // jalons)
    for j in range(jalons):
        modele.learn(total_timesteps=par_jalon, reset_num_timesteps=(j == 0),
                     progress_bar=False)
        la, _ = _latents_et_probas(modele, C["a"])
        lb, _ = _latents_et_probas(modele, C["b"])
        ax = _axe(la, lb)
        if ax is not None:
            axes.append(ax)
    la, pa = _latents_et_probas(modele, C["a"])
    lb, pb = _latents_et_probas(modele, C["b"])
    rot = [float(np.degrees(np.arccos(np.clip(float(np.dot(axes[i], axes[i + 1])), -1, 1))))
           for i in range(len(axes) - 1)] if len(axes) > 1 else []
    ent = float(-(pa.mean(0) * np.log(pa.mean(0) + 1e-12)).sum())
    return {
        "arch": arch, "graine": graine, "params": int(n_par), "pas": int(pas),
        "proba_favorite_but_vu": float(pa.mean(0).max()),
        "proba_favorite_but_absent": float(pb.mean(0).max()),
        "action_favorite_but_vu": int(pa.mean(0).argmax()),
        "action_favorite_but_absent": int(pb.mean(0).argmax()),
        "entropie": ent, "entropie_max": float(np.log(N_ACTIONS)),
        "dprime_latent": _dprime(la, lb),
        "derive_par_jalon_deg": float(np.mean(rot)) if rot else None,
        "reussite": _reussite(env_mes, modele, graine),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arch", type=int, default=69)
    ap.add_argument("--graine", type=int, default=11)
    ap.add_argument("--pas", type=int, default=PAS_MESURES)
    ap.add_argument("--sortie", default=None)
    ap.add_argument("--env", default=None,
                    help="surcharge ENV_ID (defaut : %s). Le defaut reste inchange pour "
                         "que l'A/A du 29/08 reste reproductible bit a bit." % ENV_ID)
    ap.add_argument("--aa", action="store_true",
                    help="contrôle A/A : deux runs identiques, avant tout A/B (règle §5)")
    a = ap.parse_args()

    if a.env:
        # v41.60 - le banc etait fige sur SimpleCrossingS9N1 (le niveau 3), donc la
        # baseline « le mur n'existe pas » n'avait JAMAIS ete mesuree au niveau du mur
        # (LavaGapS5, niveau 4, ou 40 runs sur 40 s'arretent). Surcharge explicite,
        # jamais implicite : sans ce drapeau le banc est bit-identique a la v41.38.
        globals()["ENV_ID"] = a.env
        print(f"[ENV] {ENV_ID}")

    if a.aa:
        print(f"CONTRÔLE A/A — arch [{a.arch},{a.arch}], graine {a.graine}, "
              f"{a.pas:,} pas, deux runs identiques\n")
        r1 = entrainer(a.arch, a.graine, a.pas)
        r2 = entrainer(a.arch, a.graine, a.pas)
        print(f"  {'métrique':<28}{'run 1':>12}{'run 2':>12}{'δ_A/A':>12}")
        print("  " + "-" * 64)
        for k in ("proba_favorite_but_vu", "entropie", "dprime_latent",
                  "derive_par_jalon_deg", "reussite"):
            v1, v2 = r1[k], r2[k]
            if v1 is None or v2 is None:
                continue
            print(f"  {k:<28}{v1:>12.4f}{v2:>12.4f}{abs(v1 - v2):>12.6f}")
        print(f"\n  ⚠️ δ_A/A est le VRAI plancher de détection : un effet A/B inférieur "
              f"n'existe pas,\n     quel que soit son `t` (règle de mesure §5).")
        if a.sortie:
            json.dump({"rep1": r1, "rep2": r2}, open(a.sortie, "w"), indent=1)
        return

    r = entrainer(a.arch, a.graine, a.pas)
    r["env_id"] = ENV_ID
    print(json.dumps(r, indent=1))
    if a.sortie:
        json.dump(r, open(a.sortie, "w"), indent=1)


if __name__ == "__main__":
    main()
