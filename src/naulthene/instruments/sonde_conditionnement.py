# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Adrien Nault — Naulthène AGI
"""Sonde de conditionnement perceptif — le signal « ressource en face » atteint-il les logits ?

Instrument **en lecture seule** (v41.33). Charge un `.brain`, capture des états RÉELS
vécus en jeu, les trie en deux classes — *face à une ressource* / *face à un mur* — et
mesure, **étage par étage**, si les activations internes distinguent les deux classes.

Ne sauvegarde jamais et ne fait tourner aucun apprentissage.

POURQUOI (campagne AB3, 26/08/2026)
------------------------------------
Neuf réfutations ont écarté le gradient comme cause du plafond au niveau 4. Ce que les
logs montrent est comportemental :

    Fourrage : 84 occasion(s) | 9 saisie(s) → taux 10,7 %
               faim moyenne aux occasions 0,963
               62 gestes `consommer`, dont 53 dans le vide

L'agent a faim à 96 %, il est FACE à de la nourriture, et il saisit une fois sur dix.
Distance des politiques mur/ressource : 0,2394. **L'hypothèse est que la décision n'est
pas conditionnée par ce que l'agent perçoit.** Cette sonde cherche l'étage où le signal
se dissipe.

LES SIX ÉTAGES DU CHEMIN C1 (lus dans `_executer_c1_reflexe` / `_tronc_cerebral`)
---------------------------------------------------------------------------------
    obs → porte_visuelle → bus_latent
        → hippocampe     → memoire_actuelle
        → analyseur      → pensee
        → fusion_memoire → pensee_enrichie      (contexte épisodique)
        → integrateur_bio→ pensee_bio           (⚠️ ici entrent les jauges)
        → tete_motrice   → logits_C1

L'étage `pensee_bio` est le suspect désigné : c'est le seul où la faim rejoint la
perception. S'il écrase le signal visuel, l'agent décide sur son ventre, pas sur ses yeux.

⚠️ TROIS PRÉCAUTIONS DE MESURE (leçons payées)
-----------------------------------------------
**(1) PLANCHER DE BRUIT OBLIGATOIRE.** Comparer deux centroïdes ne dit rien sans savoir ce
que vaut la distance entre deux moitiés du MÊME groupe. On mesure donc `d_intra` (mur vs
mur, ressource vs ressource, par bootstrap) à côté de `d_inter`. **Un `d_inter` inférieur
au p95 de `d_intra` n'existe pas** — c'est la règle du δ_A/A appliquée aux activations.

**(2) DEUX RÉGIMES BIO, ET C'EST VOULU.** *bio réel* = le vecteur bio effectivement vécu au
tick capturé (ce qui compte pour le comportement). *bio gelé* = un vecteur identique
imposé aux deux classes (isole le canal visuel pur). Si le signal existe en « bio gelé »
et disparaît en « bio réel », l'écrasement viscéral est démontré directement.

**(3) SÉPARABILITÉ, PAS SEULEMENT DISTANCE.** Une distance de centroïdes peut être grande
avec des nuages qui se recouvrent. On publie aussi le **d' (d-prime)** — écart des
centroïdes rapporté à la dispersion intra-classe — qui est la vraie mesure de « ces deux
états sont-ils distinguables ». d' < 1 : nuages confondus.

Usage :
    PYTHONPATH=src python -m naulthene.instruments.sonde_conditionnement <brain> \
        [--env ENV_ID] [--ticks N] [--graine G]
"""
import argparse
import numpy as np
import torch
import torch.nn.functional as F

from naulthene.cerveau.noyau import (
    AGI_Naulthene, DEVICE, creer_env, encoder, DIM_VECTEUR_BIO,
    DetecteurRessourcesBiologiques, NB_SOURCES_FOOD, NB_SOURCES_WATER,
)
from naulthene.cerveau.persistance import PersistanceAnatomique

ETAGES = ["bus_latent", "memoire_actuelle", "pensee", "pensee_enrichie",
          "pensee_bio", "logits_C1"]


def _etages_complets(agent, obs, memoire, contexte, vecteur_bio):
    """Rejoue le chemin de C1 étage par étage — copie fidèle de _executer_c1_reflexe.

    On ne peut pas appeler la méthode telle quelle : elle ne retourne que 5 vecteurs et
    masque `memoire_actuelle`/`pensee`. On rejoue donc les MÊMES opérations, dans le même
    ordre, sous no_grad. Toute divergence ici invaliderait la mesure — d'où la vérification
    croisée `_verifier_fidelite()` lancée au démarrage.
    """
    with torch.no_grad():
        stimulus_visuel = F.relu(agent.porte_visuelle(obs))
        silence = torch.zeros(obs.shape[0], agent.porte_auditive.in_features,
                              device=obs.device, dtype=obs.dtype)
        bus_latent = stimulus_visuel + F.relu(agent.porte_auditive(silence))
        memoire_actuelle = F.relu(agent.hippocampe(
            torch.cat([bus_latent, memoire.detach()], dim=-1)))
        pensee = F.relu(agent.analyseur(memoire_actuelle))
        pensee_enrichie = agent.lecture_episodique(pensee, contexte)
        pensee_bio = agent.integrer_bio(pensee_enrichie.detach(), vecteur_bio)
        logits = agent.tete_motrice(pensee_bio)
    return {"bus_latent": bus_latent, "memoire_actuelle": memoire_actuelle,
            "pensee": pensee, "pensee_enrichie": pensee_enrichie,
            "pensee_bio": pensee_bio, "logits_C1": logits}


def _verifier_fidelite(agent, obs, memoire, contexte, bio):
    """Garde-fou : le rejeu manuel doit être BIT-IDENTIQUE à _executer_c1_reflexe."""
    with torch.no_grad():
        ref = agent._executer_c1_reflexe(obs, memoire, contexte, bio)
    mine = _etages_complets(agent, obs, memoire, contexte, bio)
    ecarts = {
        "bus_latent": (ref[0] - mine["bus_latent"]).abs().max().item(),
        "pensee_enrichie": (ref[2] - mine["pensee_enrichie"]).abs().max().item(),
        "pensee_bio": (ref[3] - mine["pensee_bio"]).abs().max().item(),
        "logits_C1": (ref[4] - mine["logits_C1"]).abs().max().item(),
    }
    pire = max(ecarts.values())
    statut = "✅ fidèle" if pire < 1e-6 else "🔴 DIVERGENT — mesure invalide"
    print(f"  Contrôle de fidélité du rejeu : écart max {pire:.3e}  {statut}")
    return pire < 1e-6


def _dprime(A, B):
    """Séparabilité des deux nuages : ‖μA−μB‖ / dispersion intra moyenne.

    d' < 1 = nuages confondus ; d' > 2 = classes nettement séparées.
    """
    muA, muB = A.mean(0), B.mean(0)
    ecart = np.linalg.norm(muA - muB)
    sA = np.sqrt(((A - muA) ** 2).sum(1).mean())
    sB = np.sqrt(((B - muB) ** 2).sum(1).mean())
    disp = (sA + sB) / 2.0
    return float(ecart / disp) if disp > 1e-12 else 0.0


def _cos(a, b):
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na < 1e-12 or nb < 1e-12:
        return 0.0
    return float(1.0 - np.dot(a, b) / (na * nb))


def _plancher_bruit(X, rng, n_boot=200):
    """p95 de la distance cosinus entre deux moitiés ALÉATOIRES du même groupe.

    C'est le δ_A/A des activations : en dessous, une distance inter-classes ne veut
    rien dire.
    """
    n = len(X)
    if n < 4:
        return None
    ds = []
    for _ in range(n_boot):
        idx = rng.permutation(n)
        h = n // 2
        ds.append(_cos(X[idx[:h]].mean(0), X[idx[h:2 * h]].mean(0)))
    return float(np.percentile(ds, 95))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("brain")
    ap.add_argument("--env", default="MiniGrid-Empty-8x8-v0")
    ap.add_argument("--ticks", type=int, default=4000)
    ap.add_argument("--graine", type=int, default=11)
    ap.add_argument("--max-captures", type=int, default=300)
    a = ap.parse_args()

    rng = np.random.RandomState(a.graine)
    torch.manual_seed(a.graine)

    env = creer_env(a.env, 147)
    obs, _ = env.reset(seed=a.graine)
    etat = PersistanceAnatomique(a.brain).charger_ou_naitre()
    agent = etat.agent
    agent.eval()
    dim_bus = agent.dim_bus

    print(f"Cerveau : {a.brain}")
    print(f"  dim_bus={dim_bus} | env={a.env} | graine={a.graine} | ticks={a.ticks}\n")

    memoire = torch.zeros(1, dim_bus, device=DEVICE)
    contexte = torch.zeros(1, dim_bus, device=DEVICE)
    bio_gele = torch.tensor(np.full(DIM_VECTEUR_BIO, 0.5, dtype=np.float32),
                            device=DEVICE).unsqueeze(0)

    if not _verifier_fidelite(agent, encoder(obs), memoire, contexte, bio_gele):
        return

    # ---------- CAPTURE : conjonction (obs, vecteur_bio) face à ressource / mur ----------
    detecteur = DetecteurRessourcesBiologiques(nb_sources_food=NB_SOURCES_FOOD,
                                               nb_sources_water=NB_SOURCES_WATER)
    detecteur.reinitialiser_episode(env)
    caps = {"ressource": [], "mur": []}
    mem_courante = memoire.clone()
    for t in range(a.ticks):
        e = env.unwrapped
        fx, fy = (int(v) for v in e.front_pos)
        est_res = ((fx, fy) in detecteur.positions_food
                   or (fx, fy) in detecteur.positions_water)
        dedans = 0 <= fx < e.grid.width and 0 <= fy < e.grid.height
        objet = e.grid.get(fx, fy) if dedans else None
        est_mur = (not dedans) or (objet is not None and not objet.can_overlap()
                                   and not est_res)
        cle = "ressource" if est_res else ("mur" if est_mur else None)
        if cle is not None and len(caps[cle]) < a.max_captures:
            # le vecteur bio RÉEL du tick : on prend l'état viscéral courant du moteur
            # ⚠️ AUCUN try/except ici : un vecteur bio de secours à 0.5 rendrait les
            # deux classes identiques par construction et ferait conclure « noyé » à
            # tort. Si l'API bouge, la sonde DOIT casser bruyamment.
            vb = np.asarray(etat.moteur_bio.obtenir_vecteur_bio(), dtype=np.float32)
            assert vb.shape[0] == DIM_VECTEUR_BIO, (
                f"vecteur bio de taille {vb.shape[0]}, attendu {DIM_VECTEUR_BIO}")
            caps[cle].append((encoder(obs), vb))
        obs, _, term, trunc, _ = env.step(int(rng.randint(0, 7)))
        if term or trunc:
            obs, _ = env.reset(seed=a.graine + t)
            detecteur.reinitialiser_episode(env)

    n_r, n_m = len(caps["ressource"]), len(caps["mur"])
    print(f"\n  Captures : {n_r} face à une RESSOURCE | {n_m} face à un MUR")
    if n_r < 10 or n_m < 10:
        print("  ⚠️ Échantillon INSUFFISANT — on ne publie pas de zéro.")
        print("     (règle de mesure : une ablation vide n'est pas une ablation négative)")
        return

    # ---------- MESURE, deux régimes bio ----------
    for regime in ("bio gelé (canal visuel isolé)", "bio réel (ce qui pilote le geste)"):
        gele = regime.startswith("bio gelé")
        act = {c: {k: [] for k in ETAGES} for c in ("ressource", "mur")}
        for c in ("ressource", "mur"):
            for o, vb in caps[c]:
                bio = (bio_gele if gele else
                       torch.tensor(vb, device=DEVICE).unsqueeze(0))
                et = _etages_complets(agent, o, mem_courante, contexte, bio)
                for k in ETAGES:
                    act[c][k].append(et[k].cpu().numpy().ravel())
        print(f"\n{'=' * 84}")
        print(f"  {regime.upper()}")
        print(f"{'=' * 84}")
        print(f"  {'ÉTAGE':<18}{'d_inter':>10}{'plancher':>10}{'verdict':>12}"
              f"{'d-prime':>10}{'|res|':>9}{'|mur|':>9}")
        print("  " + "-" * 80)
        for k in ETAGES:
            R = np.array(act["ressource"][k])
            M = np.array(act["mur"][k])
            d = _cos(R.mean(0), M.mean(0))
            pl = max(x for x in (_plancher_bruit(R, rng), _plancher_bruit(M, rng))
                     if x is not None)
            dp = _dprime(R, M)
            verdict = "SIGNAL" if d > pl else "noyé"
            print(f"  {k:<18}{d:>10.6f}{pl:>10.6f}{verdict:>12}{dp:>10.3f}"
                  f"{np.linalg.norm(R.mean(0)):>9.3f}{np.linalg.norm(M.mean(0)):>9.3f}")
    print("\n  Lecture : `d_inter` doit DÉPASSER le plancher (p95 intra-classe) pour")
    print("  exister. `d-prime` < 1 = nuages confondus même si la distance est non nulle.")


if __name__ == "__main__":
    main()
