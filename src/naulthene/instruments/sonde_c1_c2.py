"""Sonde C1/C2 — mesure le rapport de force entre le réflexe et le néo-cortex.

Instrument de diagnostic **en lecture seule** (v37.0) : charge un `.brain`, le fait
percevoir dans un environnement MiniGrid, et compare tick par tick les deux voix qui
composent la décision — `logits_instinct` produit par C1 (`_executer_c1_reflexe`) et
`valeurs_simulees` produit par C2 (`_solliciter_c2_neocortex`), avant leur fusion.

Ne sauvegarde JAMAIS le cerveau et ne fait jamais tourner d'apprentissage : le `.brain`
passé en argument ressort bit-identique. C'est la même discipline que `irm_cerveau.py`.

Trois chiffres à lire :

- **Ratio C2/C1** — rapport des amplitudes moyennes. Au-delà de ~3×, C2 domine la fusion
  quelle que soit la valeur de `force_planification` : l'arbitrage est alors décoratif.
- **Accord C1==C2** — part des ticks où les deux modules désignent la même action. Un
  accord nul signifie que le réflexe n'a aucune influence sur la décision finale ; un
  accord proche de 100 % signifie qu'ils sont devenus redondants. Les deux extrêmes sont
  pathologiques.
- **argmax C1 / argmax C2** — distribution des actions préférées. Une seule action sur
  tous les ticks révèle un module qui ne réagit plus à l'observation.

La politique jouée est **stochastique** (`multinomial` sur le softmax), jamais `argmax` :
l'agent est entraîné par REINFORCE et n'a donc jamais expérimenté son mode déterministe
— le forcer produit des boucles infinies et un diagnostic faux (leçon du banc d'ablation).

Diagnostic de référence, cerveau `070820261310_V36_600_RMD.brain` (600 jours, bus 64) :
ratio 9,9× à 22,1× selon l'environnement, accord **0 %** partout, argmax constant des
deux côtés. Voir `docs/ameliorations_appliquees/CHANTIER_v37_equilibre_c1_c2.md` §2.1.

Usage :
    PYTHONPATH=src python -m naulthene.instruments.sonde_c1_c2 <brain> <env_id> [ticks]

Exemple :
    PYTHONPATH=src python -m naulthene.instruments.sonde_c1_c2 \\
        brains/070820261310_V36_600_RMD.brain MiniGrid-SimpleCrossingS9N1-v0 400
"""

import argparse
import collections

import numpy as np
import torch

from naulthene.cerveau import noyau as N
from naulthene.cerveau.persistance import PersistanceAnatomique

GRAINE_ENV = 1234       # graine de l'environnement : deux sondes successives sont comparables
GRAINE_POLITIQUE = 7    # graine du tirage stochastique, pour la même raison
SEUIL_RATIO_SAIN = 3.0  # au-delà, C2 domine la fusion quel que soit force_planification


def sonder(chemin_brain: str, env_id: str, ticks: int = 400) -> dict:
    """Sonde un cerveau sur un environnement. Retourne le dict des mesures."""
    etat = PersistanceAnatomique(chemin_brain).charger_ou_naitre()
    cerveau = etat.agent
    cerveau.eval()

    env = N.creer_env(env_id, N.DIM_VISUELLE)
    obs, _ = env.reset(seed=GRAINE_ENV)

    memoire = torch.zeros(1, cerveau.dim_bus, device=N.DEVICE)
    contexte = torch.zeros(1, cerveau.dim_bus, device=N.DEVICE)

    mesures = collections.defaultdict(list)
    generateur = torch.Generator().manual_seed(GRAINE_POLITIQUE)

    for _ in range(ticks):
        vue = torch.tensor(obs["image"], dtype=torch.float32,
                           device=N.DEVICE).flatten().unsqueeze(0) / 10.0
        # Vecteur bio neutre : on isole le rapport de force C1/C2 des fluctuations
        # viscérales (faim, soif) qui varieraient d'une sonde à l'autre.
        vecteur_bio = torch.zeros(1, N.DIM_VECTEUR_BIO, device=N.DEVICE)

        with torch.no_grad():
            _, memoire_actuelle, _, pensee_bio, logits_instinct = cerveau._executer_c1_reflexe(
                vue, memoire, contexte, vecteur_bio
            )
            valeurs_simulees, _ = cerveau._solliciter_c2_neocortex(
                pensee_bio, memoire_actuelle,
                horizons_planification=N.HORIZONS_PLANIFICATION, gamma_planif=0.9
            )

        # On compare les deux voix telles qu'elles entrent DANS la fusion, et non telles
        # qu'elles sortent de leur module : C2 est donc pondéré par force_planification,
        # et C1 reçoit le gain de réamplification de la v37.0 (Mesure 2). Sonder les
        # logits bruts de C1 mesurerait un déséquilibre que l'arbitrage ne voit plus.
        # v40.0 — la force de planification n'est plus une constante : on lit celle que le
        # cerveau sondé a réellement GAGNÉE par son vécu. Sonder avec l'ancienne valeur fixe
        # (0.85) mesurerait un rapport de force que cet agent n'a jamais connu.
        force = agent.force_planification_vecue()
        amplitude_brute = (logits_instinct.max(dim=-1, keepdim=True).values
                           - logits_instinct.min(dim=-1, keepdim=True).values)
        gain = torch.clamp(N.vigueur_min_c1(force) / (amplitude_brute + 1e-8),
                           min=N.GAIN_C1_MIN, max=N.GAIN_C1_MAX)
        voix_c1 = (logits_instinct * gain)[0, :7].cpu().numpy()
        voix_c2 = (valeurs_simulees[0, :7] * force).cpu().numpy()
        mesures["gain_c1"].append(float(gain.mean().item()))

        mesures["amplitude_c1"].append(float(voix_c1.max() - voix_c1.min()))
        mesures["amplitude_c2"].append(float(voix_c2.max() - voix_c2.min()))
        mesures["accord"].append(1.0 if voix_c1.argmax() == voix_c2.argmax() else 0.0)
        mesures["argmax_c1"].append(int(voix_c1.argmax()))
        mesures["argmax_c2"].append(int(voix_c2.argmax()))

        logits_finaux = (torch.tensor(voix_c1)
                         + valeurs_simulees[0, :7].cpu() * force)
        action = int(torch.multinomial(torch.softmax(logits_finaux, 0), 1,
                                       generator=generateur).item())
        mesures["action_jouee"].append(action)

        memoire = memoire_actuelle.detach()
        obs, recompense, termine, tronque, _ = env.step(action)
        if termine or tronque:
            # v35.0 : la réussite se juge sur la récompense, jamais sur `termine` seul
            # (mourir dans la lave termine aussi l'épisode).
            mesures["issue"].append(1.0 if recompense > 0 else 0.0)
            obs, _ = env.reset()

    moyenne_c1 = float(np.mean(mesures["amplitude_c1"]))
    moyenne_c2 = float(np.mean(mesures["amplitude_c2"]))
    return {
        "env_id": env_id,
        "ticks": ticks,
        "amplitude_c1": moyenne_c1,
        "amplitude_c2": moyenne_c2,
        "ratio": moyenne_c2 / max(1e-9, moyenne_c1),
        "gain_c1": float(np.mean(mesures["gain_c1"])),
        "accord": float(np.mean(mesures["accord"])),
        "argmax_c1": dict(collections.Counter(mesures["argmax_c1"])),
        "argmax_c2": dict(collections.Counter(mesures["argmax_c2"])),
        "actions_jouees": dict(collections.Counter(mesures["action_jouee"])),
        "episodes": len(mesures["issue"]),
        "victoires": int(sum(mesures["issue"])),
    }


def afficher(r: dict) -> None:
    print(f"\n--- {r['env_id']} / {r['ticks']} ticks ---")
    print(f"  Amplitude C1 (instinct) : {r['amplitude_c1']:.4f}  (gain v37 ×{r['gain_c1']:.2f})")
    print(f"  Amplitude C2 (planif)   : {r['amplitude_c2']:.4f}")
    alerte = "  ⚠️  C2 DOMINE LA FUSION" if r["ratio"] > SEUIL_RATIO_SAIN else "  ✅"
    print(f"  Ratio C2/C1             : {r['ratio']:.2f}x{alerte}")
    alerte_accord = "  ⚠️  C1 sans influence" if r["accord"] == 0.0 else ""
    print(f"  Accord C1==C2           : {r['accord'] * 100:.1f}%{alerte_accord}")
    print(f"  argmax C1               : {r['argmax_c1']}")
    print(f"  argmax C2               : {r['argmax_c2']}")
    print(f"  actions jouées          : {r['actions_jouees']}")
    print(f"  épisodes / victoires    : {r['episodes']} / {r['victoires']}")


def main() -> None:
    p = argparse.ArgumentParser(description="Sonde le rapport de force C1/C2 (lecture seule).")
    p.add_argument("brain", help="chemin du .brain à sonder")
    p.add_argument("env", nargs="?", default="MiniGrid-SimpleCrossingS9N1-v0",
                   help="env_id MiniGrid (défaut : le niveau bloquant SimpleCrossingS9N1)")
    p.add_argument("ticks", nargs="?", type=int, default=400)
    a = p.parse_args()
    afficher(sonder(a.brain, a.env, a.ticks))


if __name__ == "__main__":
    main()
