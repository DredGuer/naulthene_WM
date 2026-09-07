# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Adrien Nault — Naulthène AGI
"""Banc PPO — capture des fenêtres du barème du cursus (protocole A, 07/09/2026).

Réutilise les conditions **verrouillées** de `banc_ppo` (v41.38, A/A δ = 0.000000) :
- `SimpleCrossingS9N1` (la vraie carte du mur « Niveau 4/15 », off-by-one corrigé le 07/09),
- observation **aplatie** 7×7×3 = 147 dims, `MlpPolicy` (jamais `CnnPolicy`),
- **7 actions** (parité avec le masque `-inf` de Naulthène),
- budget **152 043 pas** d'environnement (le `tick_absolu` réel d'un cerveau à 400 jours),
- récompense **brute** MiniGrid, aucun shaping.

En plus du banc d'origine, ce script capture le **vecteur binaire victoire/défaite épisode
par épisode PENDANT l'entraînement**, pour appliquer le barème exact de `noyau.py`
(`TAUX_PROMOTION` = 0.60 sur `FENETRE_PROMOTION` = 20 épisodes glissants, victoire =
`récompense > 0` et jamais `termine` seul) à la vie réellement vécue de PPO. C'est la
question du protocole A : *un PPO placé dans la règle du cursus resterait-il au niveau 4 ?*

⚠️ La capture se fait par `Monitor` (info `"episode"`), donc seuls les épisodes **terminés**
sont comptés — l'épisode coupé par la fin du budget est exclu (idem pour Naulthène : un
épisode en cours au coucher du soleil ne compte pas dans sa fenêtre).

Usage :
    PYTHONPATH=src python -m naulthene.instruments.banc_ppo_fenetres --graine 11 \
        --sortie resultat.json
    PYTHONPATH=src python -m naulthene.instruments.banc_ppo_fenetres --pas 20000 --aa
        # pré-vol A/A : deux runs identiques — le vecteur de victoires doit être bit-identique
"""
import argparse, json, warnings

warnings.filterwarnings("ignore")

from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.monitor import Monitor

from naulthene.instruments.banc_ppo import PAS_MESURES, faire_env


class _CapteurEpisodes(BaseCallback):
    """Copie le geste d'EpisodeInfoCallback : lit `infos[i]["episode"]` produit par Monitor."""

    def __init__(self):
        super().__init__()
        self.victoires = []

    def _on_step(self):
        for info in self.locals.get("infos", []):
            ep = info.get("episode")
            if ep is not None:
                self.victoires.append(1.0 if ep["r"] > 0 else 0.0)
        return True


def entrainer_avec_capture(arch, graine, pas):
    """Entraîne PPO dans les conditions de banc_ppo et rend le vecteur binaire des victoires."""
    env = Monitor(faire_env(graine))
    modele = PPO("MlpPolicy", env, seed=graine, verbose=0,
                 policy_kwargs=dict(net_arch=dict(pi=[arch, arch], vf=[arch, arch])))
    capteur = _CapteurEpisodes()
    modele.learn(total_timesteps=pas, reset_num_timesteps=True,
                 progress_bar=False, callback=capteur)
    wins = capteur.victoires
    return {
        "arch": arch,
        "graine": graine,
        "pas": int(pas),
        "env_id": "MiniGrid-SimpleCrossingS9N1-v0",
        "n_episodes": len(wins),
        "taux_victoire": (sum(wins) / len(wins)) if wins else None,
        "victoires": wins,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arch", type=int, default=69)
    ap.add_argument("--graine", type=int, default=11)
    ap.add_argument("--pas", type=int, default=PAS_MESURES)
    ap.add_argument("--sortie", default=None)
    ap.add_argument("--aa", action="store_true",
                    help="pré-vol A/A : deux runs identiques — les vecteurs de victoires "
                         "doivent être bit-identiques, sinon la capture est invalide")
    a = ap.parse_args()

    if a.aa:
        print(f"PRÉ-VOL A/A — arch [{a.arch},{a.arch}], graine {a.graine}, {a.pas:,} pas\n")
        r1 = entrainer_avec_capture(a.arch, a.graine, a.pas)
        r2 = entrainer_avec_capture(a.arch, a.graine, a.pas)
        identique = (r1["victoires"] == r2["victoires"])
        print(f"  n_épisodes run 1 : {r1['n_episodes']}")
        print(f"  n_épisodes run 2 : {r2['n_episodes']}")
        print(f"  vecteur bit-identique : {identique}")
        print(f"  ⚠️ Si faux, la capture est invalide — ne pas lancer la campagne.")
        if a.sortie:
            json.dump({"rep1": r1, "rep2": r2, "bit_identique": bool(identique)},
                      open(a.sortie, "w"), indent=1)
        return

    r = entrainer_avec_capture(a.arch, a.graine, a.pas)
    print(json.dumps({k: v for k, v in r.items() if k != "victoires"}, indent=1))
    print(f"  (vecteur de {r['n_episodes']} victoires non affiché — dans {a.sortie})")
    if a.sortie:
        json.dump(r, open(a.sortie, "w"), indent=1)


if __name__ == "__main__":
    main()
