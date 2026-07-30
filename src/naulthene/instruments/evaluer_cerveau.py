"""
Le Contrôle de Connaissances (expérimental) — mesure de rétention par niveau.

Ce module ne vit que dans l'écosystème local de test (voir CLAUDE.md, section
"Variante Locale de Test"), pas encore porté sur `agi_google_colab.py`. Répond à un
besoin absent des instruments existants (`irm_cerveau.py`, `arene_visuelle.py`) : ils
observent un cerveau EN DIRECT sur le niveau où il en est dans son cursus, mais aucun
outil ne mesure "ce cerveau sait-il encore faire le Primaire, maintenant qu'il est
censé savoir faire l'Université ?" — la question de la rétention/l'oubli catalogique
(érosion nocturne insuffisamment cristallisée sur un vieux niveau, §8 de
docs/explications_readme.md).

Principe : charger un `.brain` en lecture seule, forcer temporairement son
environnement sur UN niveau donné du `PROGRAMME` (indépendamment du niveau réel où le
cursus l'a laissé), lui faire jouer N épisodes SEEDÉS (reproductibles d'un run à
l'autre) et compter le taux de victoire + la vitesse moyenne de résolution. Le
résultat est écrit dans un fichier JSON horodaté (`docs/notes/evals/`) — comparer deux
JSON (`--comparer`) montre si le cerveau a progressé, stagné ou régressé sur un niveau
qu'il ne pratique plus activement.

⚠️ Garantie de non-altération (même contrat que irm_cerveau.py/lancer_arene.py) :
`agent.eval()` + `torch.no_grad()` sur toute la boucle de jeu, aucun appel à
`apprendre_journee`/`executer_nuit`/`rever`/`declencher_neurogenese`, et surtout
AUCUN appel à `PersistanceAnatomique.sauvegarder()` — le `.brain` chargé n'est jamais
réécrit sur disque, quel que soit le nombre d'évaluations lancées dessus.

Usage :
    # Auto-détecte le niveau courant du cerveau et l'évalue seul
    python -m naulthene.instruments.evaluer_cerveau --brain brains/naulthene_parole.brain

    # Évalue explicitement le Primaire et le Collège, 20 épisodes chacun
    python -m naulthene.instruments.evaluer_cerveau --brain brains/naulthene_parole.brain \\
        --niveaux 0 1 --episodes 20

    # Évalue TOUS les niveaux du PROGRAMME (contrôle de connaissances complet)
    python -m naulthene.instruments.evaluer_cerveau --brain brains/naulthene_parole.brain --tous

    # Compare deux évaluations déjà enregistrées (avant/après)
    python -m naulthene.instruments.evaluer_cerveau --comparer eval_A.json eval_B.json
"""

import argparse
import json
import os
import time
from datetime import datetime, timezone

import numpy as np
import torch

from naulthene.cerveau.noyau import (
    demarrer_journee, traiter_tick, creer_env, encoder, DIM_VISUELLE, PROGRAMME, ticks_par_jour,
    DetecteurJalonsDoorKey, est_doorkey,
)
from naulthene.cerveau.persistance import PersistanceAnatomique

DOSSIER_EVALS_DEFAUT = "docs/notes/evals"


def evaluer_niveau(etat, index_niveau: int, nb_episodes: int, seed_base: int,
                    max_ticks_episode: int) -> dict:
    """Fait rejouer `nb_episodes` épisodes SEEDÉS (seed_base + i, une seed fixe par
    épisode pour que deux runs d'évaluation affrontent exactement les mêmes cartes) sur
    le niveau `PROGRAMME[index_niveau]`, en io remplaçant temporairement l'environnement
    de `etat` — `etat` lui-même n'est jamais sauvegardé, voir la garantie en tête de
    fichier. Retourne un résumé agrégé (taux de victoire, ticks moyens jusqu'à
    victoire, etc.), jamais les traces tick-par-tick (pas l'objet de cet outil, voir
    irm_cerveau.py pour l'observation fine)."""
    env_id, nom_classe = PROGRAMME[index_niveau]

    etat.env.close()
    etat.env = creer_env(env_id, DIM_VISUELLE)
    etat.env_id = env_id
    etat.nom_classe = nom_classe
    # Un cerveau qui a dépassé DoorKey depuis longtemps peut être réévalué dessus —
    # on repart d'un détecteur neuf à chaque niveau testé, jamais celui d'un autre
    # niveau resté accroché à etat.detecteur.
    etat.detecteur = None
    etat.palier_cible = 1

    victoires, ticks_jusqu_victoire, paliers_atteints = [], [], []

    for i in range(nb_episodes):
        seed = seed_base + i
        # `demarrer_journee` fait déjà `etat.env.reset()` en interne ET recalibre tous
        # les détecteurs (portes, progrès, cinétique, ressources bio, DoorKey) sur LA
        # carte tirée par ce reset. Refaire un second `env.reset(seed=...)` après coup
        # changerait la carte sous les pieds de ces détecteurs déjà calibrés sur
        # l'ancienne — bug constaté en test (0% de victoire sur Empty-8x8, y compris
        # à pleine durée, symptôme d'un détecteur désynchronisé plutôt qu'un vrai
        # oubli). On seed donc l'environnement AVANT d'appeler demarrer_journee, en
        # abaissant `Env.reset` au niveau de la seed du générateur NumPy sous-jacent
        # de Gymnasium via `etat.env.reset(seed=seed)` en PREMIER, sans second reset :
        # `demarrer_journee` ne passe pas de seed à son propre reset(), donc le
        # générateur pseudo-aléatoire de l'env garde la seed qu'on vient de lui donner
        # pour CE prochain reset (comportement documenté de Gymnasium : une seed posée
        # persiste jusqu'au reset suivant qui la consomme).
        etat.env.reset(seed=seed)
        demarrer_journee(etat)

        # ATTENTION (bug corrigé après un premier essai) : `traiter_tick` ne se contente
        # PAS de signaler la fin d'épisode — dès que `etat.fin_episode` devient True, il
        # enchaîne LUI-MÊME sur un nouvel épisode dans la foulée (`env.reset()`,
        # `ticks_episode_courant = 0`, voir noyau.py ~L3029-3055), exactement comme dans
        # une vraie journée d'entraînement où plusieurs épisodes MiniGrid se succèdent en
        # une seule "journée" de `ticks_par_jour`. Boucler jusqu'à `etat.fin_episode` et
        # lire `etat.victoire_aujourdhui`/`etat.ticks_episode_courant` APRÈS le tick qui a
        # déclenché ce chaînage lit donc déjà l'état du DEUXIÈME épisode (ticks remis à 0,
        # d'où le "ticks_moyen_si_victoire: 0.0" constaté en test). On capture donc la
        # victoire/les ticks au tick MÊME où `fin_episode` bascule, avant tout tick
        # suivant qui aurait déjà basculé sur le prochain épisode. `victoire_aujourdhui`
        # est également un flag de JOURNÉE (jamais remis à False tant que la journée
        # dure) — sans ce garde-fou, un cerveau qui gagne son 1er épisode puis en perd 5
        # autres dans la même journée compterait comme "journée gagnée", pas "épisode
        # gagné" : on isole donc explicitement un seul épisode réel par itération.
        a_gagne, ticks_episode = False, None
        with torch.no_grad():
            for _tick in range(max_ticks_episode):
                ticks_avant = etat.ticks_episode_courant
                traiter_tick(etat)
                if etat.fin_episode:
                    a_gagne = bool(etat.victoire_aujourdhui)
                    ticks_episode = ticks_avant + 1
                    break

        victoires.append(a_gagne)
        if a_gagne:
            ticks_jusqu_victoire.append(ticks_episode)
        if etat.doorkey_actif:
            paliers_atteints.append(etat.palier_cible)

    taux_victoire = float(np.mean(victoires)) if victoires else 0.0
    resultat = {
        "niveau_index": index_niveau,
        "env_id": env_id,
        "nom_classe": nom_classe,
        "episodes": nb_episodes,
        "seed_base": seed_base,
        "taux_victoire": taux_victoire,
        "victoires": int(sum(victoires)),
        "ticks_moyen_si_victoire": float(np.mean(ticks_jusqu_victoire)) if ticks_jusqu_victoire else None,
    }
    if paliers_atteints:
        resultat["palier_doorkey_moyen"] = float(np.mean(paliers_atteints))
        resultat["palier_doorkey_max"] = int(max(paliers_atteints))
    return resultat


def executer_evaluation(fichier_brain: str, indices_niveaux, nb_episodes: int,
                         seed_base: int, max_ticks_episode: int, dossier_sortie: str) -> str:
    persistance = PersistanceAnatomique(fichier=fichier_brain)
    etat = persistance.charger_ou_naitre()
    etat.agent.eval()  # même garantie que irm_cerveau.py/lancer_arene.py : jamais d'entraînement ici

    niveau_courant_detecte = etat.niveau_actuel
    print(f"🧠 Cerveau « {fichier_brain} » chargé — niveau actuel du cursus : "
          f"{PROGRAMME[niveau_courant_detecte][1]} (index {niveau_courant_detecte}), "
          f"jour={etat.jour}, dim_bus={etat.agent.dim_bus}.")

    if indices_niveaux is None:
        indices_niveaux = [niveau_courant_detecte]
    print(f"📋 Contrôle de connaissances sur {len(indices_niveaux)} niveau(x) : "
          f"{[PROGRAMME[i][1] for i in indices_niveaux]}, {nb_episodes} épisodes chacun "
          f"(seeds {seed_base}..{seed_base + nb_episodes - 1}).")

    resultats_par_niveau = []
    for index_niveau in indices_niveaux:
        t0 = time.time()
        resultat = evaluer_niveau(etat, index_niveau, nb_episodes, seed_base, max_ticks_episode)
        duree = time.time() - t0
        resultats_par_niveau.append(resultat)
        print(f"   ✅ {resultat['nom_classe']:35s} — taux de victoire "
              f"{resultat['taux_victoire']*100:5.1f}% ({resultat['victoires']}/{nb_episodes}), "
              f"ticks moy. si victoire: {resultat['ticks_moyen_si_victoire']}, "
              f"({duree:.1f}s)")

    etat.env.close()

    rapport = {
        "fichier_brain": fichier_brain,
        "date_evaluation": datetime.now(timezone.utc).isoformat(),
        "jour_cerveau_au_moment_du_test": etat.jour,
        "dim_bus_au_moment_du_test": etat.agent.dim_bus,
        "teneur_dopamine_au_moment_du_test": etat.teneur_dopamine,
        "niveau_actuel_cursus_au_moment_du_test": niveau_courant_detecte,
        "nb_episodes_par_niveau": nb_episodes,
        "seed_base": seed_base,
        "resultats": resultats_par_niveau,
    }

    os.makedirs(dossier_sortie, exist_ok=True)
    nom_brain = os.path.splitext(os.path.basename(fichier_brain))[0]
    horodatage = datetime.now().strftime("%Y%m%d_%H%M%S")
    chemin_sortie = os.path.join(dossier_sortie, f"{nom_brain}_{horodatage}.json")
    with open(chemin_sortie, "w", encoding="utf-8") as f:
        json.dump(rapport, f, ensure_ascii=False, indent=2)
    print(f"💾 Rapport écrit dans {chemin_sortie} (le .brain lui-même n'a pas été modifié).")
    return chemin_sortie


def comparer_evaluations(chemins_json):
    """Affiche un tableau texte comparant N rapports JSON déjà produits par
    `executer_evaluation`, niveau par niveau (jointure sur `nom_classe`). Pense à
    passer des rapports produits avec le MÊME `--seed-base`/`--episodes` pour une
    comparaison vraiment à cartes égales."""
    rapports = []
    for chemin in chemins_json:
        with open(chemin, "r", encoding="utf-8") as f:
            rapports.append(json.load(f))

    niveaux_vus = []
    for rapport in rapports:
        for resultat in rapport["resultats"]:
            if resultat["nom_classe"] not in niveaux_vus:
                niveaux_vus.append(resultat["nom_classe"])

    entetes = [os.path.basename(c) for c in chemins_json]
    print("\n📊 Comparaison de rétention par niveau")
    print(f"{'Niveau':35s} | " + " | ".join(f"{e[:22]:22s}" for e in entetes))
    print("-" * (35 + 3 + len(entetes) * 25))
    for nom_classe in niveaux_vus:
        ligne = f"{nom_classe:35s} | "
        cellules = []
        for rapport in rapports:
            match = next((r for r in rapport["resultats"] if r["nom_classe"] == nom_classe), None)
            if match is None:
                cellules.append(f"{'—':22s}")
            else:
                cellules.append(f"{match['taux_victoire']*100:5.1f}% ({match['victoires']}/{match['episodes']})".ljust(22))
        print(ligne + " | ".join(cellules))
    print()
    for i, rapport in enumerate(rapports):
        print(f"  [{os.path.basename(chemins_json[i])}] jour={rapport['jour_cerveau_au_moment_du_test']}, "
              f"dim_bus={rapport['dim_bus_au_moment_du_test']}, "
              f"dopamine={rapport['teneur_dopamine_au_moment_du_test']:.3f}, "
              f"daté du {rapport['date_evaluation']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Le Contrôle de Connaissances — mesure de rétention par niveau (expérimental)")
    parser.add_argument("--brain", type=str, default="brains/naulthene_parole.brain",
                         help="Chemin du .brain à évaluer (jamais modifié)")
    parser.add_argument("--niveaux", type=int, nargs="+", default=None,
                         help="Indices PROGRAMME à tester (0=Primaire..4=Doctorat). "
                              "Défaut : uniquement le niveau actuel détecté dans le .brain")
    parser.add_argument("--tous", action="store_true",
                         help="Teste les 5 niveaux du PROGRAMME, ignore --niveaux")
    parser.add_argument("--episodes", type=int, default=10,
                         help="Nombre d'épisodes seedés par niveau (défaut 10)")
    parser.add_argument("--seed-base", type=int, default=0,
                         help="Seed du premier épisode (défaut 0) — garder la même valeur "
                              "entre deux évaluations pour comparer sur les MÊMES cartes")
    parser.add_argument("--max-ticks", type=int, default=ticks_par_jour,
                         help=f"Plafond de ticks par épisode (défaut {ticks_par_jour}, "
                              "comme une journée standard)")
    parser.add_argument("--dossier-sortie", type=str, default=DOSSIER_EVALS_DEFAUT,
                         help=f"Où écrire le rapport JSON (défaut {DOSSIER_EVALS_DEFAUT})")
    parser.add_argument("--comparer", type=str, nargs="+", default=None,
                         help="Au lieu d'évaluer, compare N rapports JSON déjà produits "
                              "(ex: --comparer eval_avant.json eval_apres.json)")
    args = parser.parse_args()

    if args.comparer:
        comparer_evaluations(args.comparer)
    else:
        indices = list(range(len(PROGRAMME))) if args.tous else args.niveaux
        executer_evaluation(
            fichier_brain=args.brain, indices_niveaux=indices, nb_episodes=args.episodes,
            seed_base=args.seed_base, max_ticks_episode=args.max_ticks,
            dossier_sortie=args.dossier_sortie,
        )
