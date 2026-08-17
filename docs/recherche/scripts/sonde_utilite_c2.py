#!/usr/bin/env python3
"""Sonde d'UTILITÉ CAUSALE de C2 — répond à « C2 devient-il utile ? » (17/08/2026).

Toutes les mesures existantes portent sur l'AMPLITUDE de C2 (ratio C2/C1) ou sur son
ACCORD avec C1. Aucune ne répond à la seule question qui compte :

    **Est-ce que C2 change la décision, et quand il la change, est-ce pour le mieux ?**

Cette sonde mesure quatre choses, tick par tick, sur un cerveau réel dans son monde :

  1. TAUX DE VETO      — combien de fois l'action finale diffère de celle que C1 aurait
                         jouée seul. C'est l'influence causale de C2, indépendamment de
                         son amplitude : un C2 minuscule qui fait basculer un tick décisif
                         est plus utile qu'un C2 énorme qui ne change jamais rien.
  2. QUALITÉ DU VETO   — quand C2 impose son choix, l'agent s'en sort-il mieux ? Comparé
                         par la valeur estimée de l'état atteint (`cortex_prefrontal`).
  3. ENTROPIE DES VOTES— C1 et C2 proposent-ils des actions VARIÉES, ou chacun répète-t-il
                         la même ? (0 = voix figée ⇒ tout « accord » est un artefact.)
  4. INFORMATION MUTUELLE — les deux voix sont-elles corrélées ? Une IM nulle signifie que
                         C2 n'apporte rien que C1 ne dise déjà, OU qu'il parle d'autre
                         chose entièrement. Croisée avec le veto, ça tranche.

Usage :
    PYTHONPATH=src python docs/recherche/scripts/sonde_utilite_c2.py <brain> [--ticks 2000]
"""
from __future__ import annotations
import argparse
import math
import sys
from collections import Counter

import numpy as np
import torch


def entropie(hist: Counter, n_actions: int = 7) -> float:
    """Entropie normalisée dans [0,1]. 0 = toujours la même action."""
    total = sum(hist.values())
    if total <= 0 or len(hist) <= 1:
        return 0.0
    h = -sum((n / total) * math.log(n / total) for n in hist.values() if n > 0)
    return h / math.log(n_actions)


def info_mutuelle(paires, n_actions: int = 7) -> float:
    """I(C1;C2) normalisée par min(H(C1), H(C2)) — dans [0,1].

    0 = les deux voix sont indépendantes (C2 n'exprime rien de ce que C1 exprime).
    1 = connaître l'une donne l'autre (C2 est redondant avec C1).
    Une valeur intermédiaire est le signe d'une vraie complémentarité.
    """
    if not paires:
        return 0.0
    n = len(paires)
    c1 = Counter(a for a, _ in paires)
    c2 = Counter(b for _, b in paires)
    joint = Counter(paires)
    h1 = -sum((v / n) * math.log(v / n) for v in c1.values())
    h2 = -sum((v / n) * math.log(v / n) for v in c2.values())
    if h1 <= 1e-12 or h2 <= 1e-12:
        return 0.0   # une voix figée : l'IM est nulle par construction, pas par mesure
    im = 0.0
    for (a, b), v in joint.items():
        p_ab = v / n
        im += p_ab * math.log(p_ab / ((c1[a] / n) * (c2[b] / n)))
    return im / min(h1, h2)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("brain")
    ap.add_argument("--ticks", type=int, default=2000)
    ap.add_argument("--graine", type=int, default=7)
    ap.add_argument("--niveau", type=int, default=None,
                    help="force le palier du PROGRAMME sur lequel sonder")
    args = ap.parse_args()

    from naulthene.cerveau import noyau as N
    from naulthene.cerveau.persistance import PersistanceAnatomique

    torch.manual_seed(args.graine)
    np.random.seed(args.graine)

    pers = PersistanceAnatomique(args.brain)
    etat = pers.charger_ou_naitre()
    agent = etat.agent
    agent.eval()

    print(f"\n{'=' * 74}")
    print(f"SONDE D'UTILITÉ CAUSALE DE C2 — {args.brain.split('/')[-1]}")
    print(f"  niveau {etat.niveau_actuel} ({etat.nom_classe}) | bus {agent.dim_bus} dims "
          f"| tick absolu {etat.tick_absolu}")
    print(f"{'=' * 74}")

    # Le remappage de `persistance` peut ramener le cerveau au niveau de son env_id
    # d'origine ; `--niveau` force le palier sur lequel on veut sonder (c'est tout
    # l'objet du test DoorKey : mesurer C2 là où une causalité existe).
    if args.niveau is not None:
        etat.niveau_actuel = int(args.niveau)
        etat.env_id, etat.nom_classe = N.PROGRAMME[etat.niveau_actuel]
        etat.env.close()
        etat.env = N.creer_env(etat.env_id, N.DIM_VISUELLE)
        etat.doorkey_actif = N.est_doorkey(etat.env_id)
        if etat.doorkey_actif and etat.detecteur is None:
            etat.detecteur = N.DetecteurJalonsDoorKey()
        print(f"  → sondé sur : {etat.nom_classe} ({etat.env_id})")

    def _nouvel_episode():
        obs, _ = N._reset_seede(etat)
        etat.etat_courant = N.encoder(obs)
        etat.memoire_tampon = torch.zeros(1, agent.dim_bus, device=N.DEVICE)
        etat.vecteurs_episodiques = []
        etat.detecteur_ressources_bio.reinitialiser_episode(etat.env)
        etat.bus_sensoriel.reinitialiser_episode(etat.env)
        etat.positions_visitees_episode = set()

    _nouvel_episode()

    votes_c1, votes_c2, votes_fin = Counter(), Counter(), Counter()
    paires = []
    vetos = 0
    gain_veto, gain_sans_veto = [], []
    n_mesures = 0

    with torch.no_grad():
        for _ in range(args.ticks):
            obs = N.encoder(etat.env.unwrapped.gen_obs())
            if etat.etat_courant is None:
                etat.etat_courant = obs
            memoire = (etat.memoire_tampon if etat.memoire_tampon is not None
                       else torch.zeros(1, agent.dim_bus, device=N.DEVICE))
            contexte = (torch.stack(etat.vecteurs_episodiques).mean(dim=0)
                        if etat.vecteurs_episodiques
                        else torch.zeros(1, agent.dim_bus, device=N.DEVICE))
            vbio = torch.tensor(
                [etat.moteur_bio.obtenir_vecteur_bio(
                    signaux_sensoriels=etat.bus_sensoriel.interpreter(etat.env))],
                dtype=torch.float32, device=N.DEVICE)

            # Les deux voix, séparément — exactement comme `penser` les produit.
            (_bus, mem_act, _pe, pensee_bio,
             logits_c1) = agent._executer_c1_reflexe(obs, memoire, contexte, vbio)
            valeurs_c2, _ind = agent._solliciter_c2_neocortex(
                pensee_bio, mem_act, vecteur_bio=vbio)

            a_c1 = int(logits_c1.argmax(dim=-1).view(-1)[0].item())
            a_c2 = int(valeurs_c2.argmax(dim=-1).view(-1)[0].item())

            # La fusion réelle, avec la force de planification du jour.
            force = float(getattr(etat, "force_planification_jour", 0.5))
            fusion = logits_c1 + valeurs_c2 * force
            fusion = fusion.view(-1)[:N.NUM_ACTIONS_BASE]
            a_fin = int(fusion.argmax().item())

            votes_c1[a_c1] += 1
            votes_c2[a_c2] += 1
            votes_fin[a_fin] += 1
            paires.append((a_c1, a_c2))
            n_mesures += 1

            # LE VETO : C2 a-t-il détourné la décision de C1 ?
            veto = (a_fin != a_c1)
            if veto:
                vetos += 1

            # Qualité : valeur estimée de l'état atteint après l'action jouée.
            # `cortex_prefrontal` est le juge interne de l'agent — le seul disponible
            # sans dérouler l'environnement en double.
            v_etat = float(agent.cortex_prefrontal(pensee_bio).mean().item())
            (gain_veto if veto else gain_sans_veto).append(v_etat)

            # ⚠️ L'AGENT ÉCHANTILLONNE, IL NE PREND PAS L'ARGMAX (`Categorical.sample()`
            # dans `traiter_tick`). Une première version de cette sonde jouait l'argmax :
            # l'agent tournait alors en boucle sur place, revoyait la même observation, et
            # les DEUX voix affichaient une entropie de 0.000 — un artefact complet.
            # Mesuré contre un run réel : C1 y est à 0,17–0,77, pas à 0.
            _a_joue = int(torch.distributions.Categorical(logits=fusion).sample().item())
            obs_s, _r, term, trunc, _ = etat.env.step(_a_joue if _a_joue < 7 else 6)
            etat.etat_courant = N.encoder(obs_s)
            etat.memoire_tampon = mem_act
            if term or trunc:
                _nouvel_episode()

    e1, e2 = entropie(votes_c1), entropie(votes_c2)
    im = info_mutuelle(paires)
    taux_veto = vetos / max(1, n_mesures)
    accord = sum(1 for a, b in paires if a == b) / max(1, len(paires))

    print(f"\n1. INFLUENCE CAUSALE — C2 change-t-il la décision ?")
    print(f"   taux de VETO ........... {taux_veto:6.1%}  "
          f"({vetos} tick(s) sur {n_mesures})")
    if taux_veto < 0.01:
        print(f"   → C2 est CAUSALEMENT MUET : il ne détourne quasiment jamais C1.")
    elif taux_veto > 0.5:
        print(f"   → C2 DOMINE : c'est lui qui décide, C1 propose.")
    else:
        print(f"   → C2 pèse réellement sur une fraction des décisions.")

    print(f"\n2. QUALITÉ DU VETO — quand il s'impose, est-ce mieux ?")
    if gain_veto and gain_sans_veto:
        mv, ms = float(np.mean(gain_veto)), float(np.mean(gain_sans_veto))
        print(f"   valeur estimée avec veto ... {mv:+.4f}")
        print(f"   valeur estimée sans veto ... {ms:+.4f}")
        print(f"   écart ...................... {mv - ms:+.4f}")
    else:
        print(f"   (pas assez de veto pour comparer)")

    print(f"\n3. LES VOIX SONT-ELLES VIVANTES ?")
    print(f"   entropie C1 ............ {e1:6.3f}  ({len(votes_c1)} action(s) distinctes)")
    print(f"   entropie C2 ............ {e2:6.3f}  ({len(votes_c2)} action(s) distinctes)")
    if e2 < 0.05:
        print(f"   → ⚠️ C2 est FIGÉ. Tout « accord » mesuré contre lui est un artefact.")

    print(f"\n4. COMPLÉMENTARITÉ")
    print(f"   accord brut (argmax) ... {accord:6.1%}")
    print(f"   info mutuelle I(C1;C2) . {im:6.3f}  (0 = indépendants, 1 = redondants)")

    print(f"\n{'-' * 74}")
    if e2 < 0.05 and taux_veto < 0.01:
        print("VERDICT : C2 est inerte — figé ET sans influence causale.")
    elif e2 < 0.05:
        print("VERDICT : C2 influence la décision mais vote toujours pareil —\n"
              "          il agit comme un BIAIS CONSTANT, pas comme une délibération.")
    elif taux_veto < 0.01:
        print("VERDICT : C2 a des avis variés mais aucun poids — voix étouffée.")
    else:
        print("VERDICT : C2 délibère ET pèse. Reste à savoir s'il a raison (§2).")
    print(f"{'-' * 74}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
