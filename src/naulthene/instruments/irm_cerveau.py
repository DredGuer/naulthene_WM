# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Adrien Nault — Naulthène AGI
"""
L'IRM du Cerveau (V25.x, expérimental) — scanner d'activation en direct.

Ce module ne vit que dans l'écosystème local de test (voir CLAUDE.md, section
"Variante Locale de Test"), pas encore porté sur `agi_google_colab.py`. Écrit en
réponse au diagnostic de `docs/recherche/1440_JOURS_NAULTHENE_V1.md` (§3, "effondrement lent du
modèle du monde JEPA") : ce document décrivait par les CHIFFRES (Erreur_JEPA → 0.0000,
Pourcentage_Reve → 0.38%, Teneur_Dopamine → 2.4) un collapse de représentation, sans
jamais montrer VISUELLEMENT quelles dimensions du bus latent s'éteignent. Ce scanner
rend ce collapse observable en direct, dimension par dimension.

Charge un `.brain` existant (par défaut `naulthene_bb.brain`) et affiche une fenêtre
matplotlib à trois panneaux, mise à jour à chaque tick pendant que l'agent bouge
réellement dans MiniGrid :

  1. Activation du bus latent (32 dims sur ce run) à 3 étapes du tronc cérébral —
     `bus_latent` (sortie de `porte_visuelle`), `memoire_actuelle` (sortie de
     `hippocampe`), `pensee` (sortie de `analyseur`) — barres verticales, une couleur
     par étape. Une dimension plate à ~0 sur les trois étapes est une dimension "morte"
     au sens fonctionnel (jamais excitée par la perception), à ne pas confondre avec
     une synapse morte au sens structurel (panneau 2).
  2. Carte de myélinisation par couche plastique — heatmap de `myeline_M` (moyenne par
     neurone de sortie) pour les 9 couches motrices/visuelles/JEPA (les 2 couches audio
     sont exclues du scan visuel, elles répondent à un canal différent). Une ligne très
     sombre = neurone jamais fortement activé = candidat à l'élagage synaptique
     (`cycle_sommeil`, base_weight rasée sous 1e-4) — le contrepoint STRUCTUREL du
     panneau 1 (fonctionnel).
  3. Variance du bus latent au fil du temps (fenêtre glissante) — la mesure directe du
     "representation collapse" décrit par le rapport : si cette courbe tend vers 0 alors
     que l'agent continue de bouger dans des états visuellement différents, c'est la
     preuve empirique que `porte_visuelle` a cessé de distinguer les observations.

⚠️ Garantie explicite (même contrat que `lancer_arene.py`) : ce scanner n'entraîne
JAMAIS le cerveau qu'il observe. `etat.agent.eval()` est appelé après le chargement,
`executer_nuit`/`apprendre_journee` ne sont jamais invoqués — seul `traiter_tick`
tourne (pense/agit, ne modifie aucun poids hors d'un `backward()` explicite, jamais
appelé ici). Lancer ce scanner autant de fois que voulu ne modifie jamais le `.brain`.

Usage :
    python irm_cerveau.py                                # naulthene_bb.brain par défaut
    python irm_cerveau.py --brain naulthene_cursus.brain  # scanner un autre cerveau
    python irm_cerveau.py --intervalle-ms 200             # ralentit le rafraîchissement
"""

import argparse

import matplotlib.pyplot as plt
import numpy as np
import torch

from naulthene.cerveau.noyau import demarrer_journee, traiter_tick, creer_env, DIM_VISUELLE, ticks_par_jour
from naulthene.cerveau.persistance import PersistanceAnatomique

# Couches plastiques scannées pour la carte de myélinisation (panneau 2) — les 9 couches
# du circuit visuel/moteur/JEPA de base, dans l'ordre du tronc cérébral puis des têtes.
# Exclut délibérément porte_auditive/tete_vocale/generateur_attente_audio (canal séparé,
# un scan dédié à l'hémisphère audio serait un script distinct, pas ce scanner visuel).
COUCHES_SCANNEES = [
    "porte_visuelle", "hippocampe", "fusion_memoire", "analyseur", "integrateur_bio",
    "tete_motrice", "cortex_prefrontal", "generateur_attente",
]

TAILLE_FENETRE_VARIANCE = 200  # nombre de ticks gardés en mémoire pour la courbe du panneau 3


def _myeline_moyenne_par_neurone(agent, nom_couche: str) -> np.ndarray:
    """Moyenne de |myeline_M| sur la dimension d'entrée, un scalaire par neurone de
    sortie — réduit une matrice (out_features, in_features) à un vecteur (out_features,)
    affichable en heatmap 1D par couche. Miroir de la lecture faite par
    `cycle_sommeil`/`fortification_dopaminergique` (voir explications_readme.md §8),
    jamais une réécriture de cette logique — ici on ne fait que LIRE les buffers."""
    couche = getattr(agent, nom_couche)
    with torch.no_grad():
        return couche.myeline_M.abs().mean(dim=1).cpu().numpy()


def _scanner_un_tick(etat, obs_auditive=None, formants_cibles=None):
    """Un tick d'observation qui fait réellement avancer l'agent dans l'environnement
    (réutilise `traiter_tick`, donc action échantillonnée + apprentissage JEPA/dopamine
    inchangés) ET recalcule séparément les 3 activations du tronc cérébral pour le scan.

    Pourquoi recalculer plutôt que lire le retour de `traiter_tick` : `traiter_tick` ne
    retourne que `{'action', 'infos_internes'}` (voir agi_local_test.py) — bus_latent/
    memoire_actuelle/pensee n'en sortent jamais. On rejoue donc `_tronc_cerebral` sur la
    MÊME observation courante juste avant le tick réel (`etat.etat_courant`,
    `etat.memoire_tampon`), en `torch.no_grad()` — aucune conséquence sur
    l'apprentissage, c'est une lecture, pas un second forward entraînant."""
    with torch.no_grad():
        bus_latent, memoire_actuelle, pensee = etat.agent._tronc_cerebral(
            etat.etat_courant, etat.memoire_tampon.detach(), obs_auditive=obs_auditive
        )

    infos = traiter_tick(etat, obs_auditive=obs_auditive, formants_cibles=formants_cibles)
    return bus_latent.cpu().numpy().flatten(), memoire_actuelle.cpu().numpy().flatten(), \
        pensee.cpu().numpy().flatten(), infos


def lancer_irm(fichier_brain: str = "brains/naulthene_bb.brain", intervalle_ms: int = 100):
    persistance = PersistanceAnatomique(fichier=fichier_brain)
    etat = persistance.charger_ou_naitre()

    etat.env.close()
    etat.env = creer_env(etat.env_id, DIM_VISUELLE)

    demarrer_journee(etat)
    etat.agent.eval()  # même garantie que lancer_arene.py : jamais d'entraînement ici
    print(f"🧲 IRM du cerveau « {fichier_brain} » — dim_bus={etat.agent.dim_bus}, "
          f"jour={etat.jour}, niveau={etat.nom_classe}.")
    print("👁️  Mode observation : le cerveau n'apprend pas pendant ce scan (agent.eval()).")

    dim_bus = etat.agent.dim_bus
    historique_variance = []

    fig, (ax_bus, ax_myeline, ax_variance) = plt.subplots(3, 1, figsize=(11, 10))
    fig.suptitle(f"IRM Naulthène — {fichier_brain} (dim_bus={dim_bus}, jour={etat.jour})")

    # --- Panneau 1 : activation du bus latent aux 3 étapes du tronc cérébral ---
    indices = np.arange(dim_bus)
    largeur = 0.25
    barres_bus_latent = ax_bus.bar(indices - largeur, np.zeros(dim_bus), largeur,
                                     label="bus_latent (porte_visuelle)", color="#4C72B0")
    barres_memoire = ax_bus.bar(indices, np.zeros(dim_bus), largeur,
                                  label="memoire_actuelle (hippocampe)", color="#DD8452")
    barres_pensee = ax_bus.bar(indices + largeur, np.zeros(dim_bus), largeur,
                                 label="pensee (analyseur)", color="#55A868")
    ax_bus.set_xlim(-1, dim_bus)
    ax_bus.set_ylim(0, 3.0)
    ax_bus.set_xlabel("Dimension du bus latent")
    ax_bus.set_ylabel("Activation (post-ReLU)")
    ax_bus.set_title("Panneau 1 — Activation par dimension (une dimension plate = neurone fonctionnellement mort)")
    ax_bus.legend(loc="upper right", fontsize=8)

    # --- Panneau 2 : carte de myélinisation par couche ---
    donnees_myeline = [_myeline_moyenne_par_neurone(etat.agent, c) for c in COUCHES_SCANNEES]
    taille_max = max(len(d) for d in donnees_myeline)
    grille_myeline = np.zeros((len(COUCHES_SCANNEES), taille_max))
    for i, d in enumerate(donnees_myeline):
        grille_myeline[i, :len(d)] = d
    im_myeline = ax_myeline.imshow(grille_myeline, aspect="auto", cmap="inferno", interpolation="nearest")
    ax_myeline.set_yticks(range(len(COUCHES_SCANNEES)))
    ax_myeline.set_yticklabels(COUCHES_SCANNEES, fontsize=8)
    ax_myeline.set_xlabel("Neurone de sortie de la couche")
    ax_myeline.set_title("Panneau 2 — Myélinisation par couche (sombre = synapses jamais fortifiées, candidates à l'élagage nocturne)")
    fig.colorbar(im_myeline, ax=ax_myeline, label="|myeline_M| moyenne", fraction=0.03)

    # --- Panneau 3 : variance du bus latent dans le temps (detection de collapse) ---
    ligne_variance, = ax_variance.plot([], [], color="#C44E52", linewidth=1.5)
    ax_variance.set_xlim(0, TAILLE_FENETRE_VARIANCE)
    ax_variance.set_ylim(0, 1.0)
    ax_variance.set_xlabel(f"Tick (fenêtre glissante des {TAILLE_FENETRE_VARIANCE} derniers)")
    ax_variance.set_ylabel("Variance(bus_latent)")
    ax_variance.set_title("Panneau 3 — Variance du bus latent (tend vers 0 = representation collapse, voir explications_readme.md §2.2)")
    ax_variance.axhline(0.02, color="gray", linestyle="--", linewidth=1, label="seuil indicatif de collapse")
    ax_variance.legend(loc="upper right", fontsize=8)
    texte_alerte_collapse = ax_bus.text(
        0.5, 0.5, "", transform=ax_bus.transAxes, ha="center", va="center",
        fontsize=13, color="#C44E52", fontweight="bold",
    )

    fig.tight_layout(rect=(0, 0, 1, 0.96))
    plt.ion()
    plt.show()

    ticks_journee_observation = 0
    tick_global = 0
    try:
        while plt.fignum_exists(fig.number):
            bus_latent, memoire_actuelle, pensee, infos = _scanner_un_tick(etat)
            ticks_journee_observation += 1
            tick_global += 1

            for barre, valeur in zip(barres_bus_latent, bus_latent):
                barre.set_height(valeur)
            for barre, valeur in zip(barres_memoire, memoire_actuelle):
                barre.set_height(valeur)
            for barre, valeur in zip(barres_pensee, pensee):
                barre.set_height(valeur)
            pic = max(bus_latent.max(initial=0), memoire_actuelle.max(initial=0), pensee.max(initial=0), 1e-6)
            ax_bus.set_ylim(0, pic * 1.15)
            texte_alerte_collapse.set_text(
                "⚠ Bus latent totalement plat (0 partout) — representation collapse, voir §3 du rapport"
                if pic <= 1e-6 else ""
            )

            variance_du_tick = float(np.var(bus_latent))
            historique_variance.append(variance_du_tick)
            if len(historique_variance) > TAILLE_FENETRE_VARIANCE:
                historique_variance.pop(0)
            ligne_variance.set_data(range(len(historique_variance)), historique_variance)
            pic_variance = max(historique_variance, default=1e-6)
            ax_variance.set_ylim(0, max(pic_variance * 1.2, 0.05))

            if tick_global % 20 == 0:  # la myéline évolue lentement (seulement au sommeil) —
                donnees_myeline = [_myeline_moyenne_par_neurone(etat.agent, c) for c in COUCHES_SCANNEES]
                grille_myeline = np.zeros((len(COUCHES_SCANNEES), taille_max))
                for i, d in enumerate(donnees_myeline):
                    grille_myeline[i, :len(d)] = d
                im_myeline.set_data(grille_myeline)
                im_myeline.set_clim(0, max(grille_myeline.max(), 1e-6))

            fig.suptitle(f"IRM Naulthène — {fichier_brain} (dim_bus={dim_bus}, jour={etat.jour}, "
                         f"tick={etat.tick_absolu}, variance bus={variance_du_tick:.4f})")
            fig.canvas.draw_idle()
            plt.pause(intervalle_ms / 1000.0)

            if ticks_journee_observation >= ticks_par_jour:
                demarrer_journee(etat)
                etat.agent.eval()
                ticks_journee_observation = 0

    except KeyboardInterrupt:
        print("\n🛑 Arrêt demandé (Ctrl+C).")
    finally:
        plt.close(fig)
        etat.env.close()

    print("✅ Scan terminé. Le cerveau observé n'a pas été modifié (aucune sauvegarde nécessaire).")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="L'IRM du Cerveau — Naulthène AGI (scanner d'activation, expérimental)")
    parser.add_argument("--brain", type=str, default="brains/naulthene_bb.brain",
                         help="Fichier .brain à scanner (défaut : brains/naulthene_bb.brain)")
    parser.add_argument("--intervalle-ms", type=int, default=100,
                         help="Pause entre deux ticks affichés, en millisecondes (défaut : 100)")
    args = parser.parse_args()

    lancer_irm(fichier_brain=args.brain, intervalle_ms=args.intervalle_ms)
