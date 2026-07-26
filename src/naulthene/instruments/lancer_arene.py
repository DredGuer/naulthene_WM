"""
L'Arène & Démo Live (V24.0, expérimental) — observer un cerveau entraîné en action.

Ce module ne vit que dans l'écosystème local de test (voir CLAUDE.md, section
"Variante Locale de Test"), pas encore porté sur `agi_google_colab.py`. Voir le plan
v24.0 et `readme.md` (section "L'Arène & Démo Live") pour le contexte narratif complet.

Charge un `.brain` existant (par défaut `naulthene_cursus.brain`, produit par
`cursus_developpemental.py` — mais n'importe quel `.brain`, y compris
`naulthene_v21.brain` de la Cuve, convient) et affiche une fenêtre pygame unique
(`arene_visuelle.FenetreArene`) : l'image MiniGrid rendue en direct à gauche, un
panneau de télémétrie (dopamine, jauges biologiques, curriculum MiniGrid, curriculum
vocal, score de formants) à droite. Le babil de l'agent est joué en temps réel dans les
haut-parleurs (`hemisphere_audio`).

Bug corrigé (v24.0-fix5, signalé par l'utilisateur) : jusqu'ici `traiter_tick(etat)`
était appelé SANS `obs_auditive` ni `formants_cibles` — le score de formants restait
donc toujours `None` par construction, quel que soit le niveau réel de l'agent (déjà
capable de dire "maman" à ~0.5 dans le cursus). Ce n'était pas un seuil de décodage mal
calibré, c'est que l'Arène ne présentait JAMAIS de mot à répéter. Corrigé : l'Arène
injecte désormais la référence audio (MFCC + formants cibles) du palier vocal courant
à chaque tick, via `lecons_vocales.CacheReferencesVocales` — le même mécanisme déjà
utilisé par `cursus_developpemental.py`, cohérent avec "Palier vocal : Mot 'maman'"
déjà affiché dans le panneau.

⚠️ Garantie explicite : cette Arène n'entraîne JAMAIS le cerveau qu'elle observe.
`etat.agent.eval()` est appelé après le chargement, et `executer_nuit`/
`apprendre_journee` ne sont jamais invoqués dans la boucle — seul `traiter_tick`
tourne, qui pense/agit mais ne modifie aucun poids en dehors d'un `backward()` explicite
(jamais appelé ici). Observer l'agent ne l'altère jamais, tu peux lancer l'Arène autant
de fois que tu veux sans risque pour le `.brain`.

Usage :
    python lancer_arene.py                              # naulthene_cursus.brain par défaut
    python lancer_arene.py --brain naulthene_v21.brain   # visualiser le cerveau de la Cuve
"""

import argparse

import torch

from naulthene.cerveau.noyau import (
    demarrer_journee, traiter_tick, ere_courante, creer_env, DIM_VISUELLE, ticks_par_jour, DEVICE,
)
from naulthene.cerveau.persistance import PersistanceAnatomique
from naulthene.instruments.arene_visuelle import FenetreArene
from naulthene.audio.hemisphere_audio import SynthetiseurFormants, jouer_son_temps_reel, recompense_formants, SAMPLE_RATE
from naulthene.audio.lecons_vocales import CacheReferencesVocales
import naulthene.audio.professeur_gemma as pg


def _construire_telemetrie(etat, score_vocal) -> dict:
    """Rassemble les infos affichables depuis `EtatCognitif` (objet accessible sans
    encapsulation, voir exploration du plan v24.0) — aucune de ces infos n'est
    retournée par `traiter_tick` lui-même, donc on les lit directement sur `etat`
    après chaque tick."""
    palier_dk = etat.palier_cible if etat.doorkey_actif else None
    nom_palier_vocal = pg.CURRICULUM_VOCAL[etat.palier_vocal - 1]["nom"] \
        if 0 < etat.palier_vocal <= len(pg.CURRICULUM_VOCAL) else "—"
    return {
        "dopamine": etat.teneur_dopamine,
        "satiete": etat.moteur_bio.satiete,
        "hydratation": etat.moteur_bio.hydratation,
        "stimulation": etat.moteur_bio.stimulation,
        "niveau_minigrid": etat.nom_classe,
        "palier_doorkey": palier_dk,
        "ere": ere_courante(etat.jour) if etat.jour > 0 else "—",
        "palier_vocal_nom": nom_palier_vocal,
        "score_vocal": score_vocal,
        "jour": etat.jour,
        "tick_absolu": etat.tick_absolu,
    }


def lancer_arene(fichier_brain: str = "brains/naulthene_cursus.brain"):
    persistance = PersistanceAnatomique(fichier=fichier_brain)
    etat = persistance.charger_ou_naitre()

    # Recrée l'environnement avec le rendu activé (le .brain restaure un env sans
    # render_mode, voir persistance.py charger_ou_naitre) — même env_id/niveau, juste
    # le canal visuel en plus.
    etat.env.close()
    etat.env = creer_env(etat.env_id, DIM_VISUELLE, render_mode="rgb_array")

    demarrer_journee(etat)
    etat.agent.eval()  # APRÈS demarrer_journee (qui appelle agent.train() en son sein)
    print("👁️  Mode observation : le cerveau n'apprend pas pendant cette démo (agent.eval()).")

    fenetre = FenetreArene()
    synth = SynthetiseurFormants()
    cache_vocal = CacheReferencesVocales()
    print("🔥 Préchauffage de la référence vocale du palier courant...")
    cache_vocal.obtenir_pour_palier(etat.palier_vocal)
    interrompu = False
    ticks_journee_observation = 0  # compteur LOCAL à l'Arène, indépendant de
                                     # etat.tick_absolu/ticks_episode_courant (gérés par
                                     # traiter_tick lui-même pour les fins d'épisode) —
                                     # ne pilote qu'un simple "rappel de journée" pour
                                     # vider les buffers de temps en temps (voir ci-dessous)

    try:
        while True:
            if fenetre.evenements_fermeture_demandee():
                print("\n🖱️  Fermeture de la fenêtre demandée.")
                break

            # v24.0-fix5 : injecte la référence audio (MFCC + formants cibles) du
            # palier vocal COURANT à chaque tick — même mécanisme que
            # cursus_developpemental.py (CacheReferencesVocales), pour que l'Arène
            # présente réellement un mot à répéter au lieu de laisser l'agent
            # vocaliser dans le vide (mode "minigrid" reste actif par ailleurs :
            # l'agent voit et bouge normalement, il entend et parle en plus).
            mfcc, formants_cibles = cache_vocal.obtenir_pour_palier(etat.palier_vocal)
            obs_auditive = torch.tensor([mfcc], dtype=torch.float32, device=DEVICE)
            infos = traiter_tick(etat, obs_auditive=obs_auditive, formants_cibles=formants_cibles)
            image = etat.env.render()
            ticks_journee_observation += 1

            vecteur_vocal = infos["infos_internes"]["parametres_vocaux"]
            score_vocal = None
            if vecteur_vocal:
                onde = synth.synthetiser(vecteur_vocal)
                jouer_son_temps_reel(onde, sample_rate=SAMPLE_RATE, bloquant=False)
                formants_produits = synth.parametres_depuis_vecteur(vecteur_vocal)
                score_vocal = recompense_formants(formants_cibles, formants_produits)

            telemetrie = _construire_telemetrie(etat, score_vocal)
            fenetre.dessiner_frame(image, telemetrie)

            # traiter_tick gère déjà lui-même la fin d'épisode MiniGrid (env.reset()
            # automatique, voir agi_local_test.py ligne ~2243) — inutile de la
            # dupliquer ici. On rappelle juste demarrer_journee() périodiquement pour
            # vider les buffers de journée (jepa_losses, log_probs_journee...) qui,
            # sans nuit ni apprentissage, grandiraient indéfiniment sur une démo
            # longue. Aucun apprentissage n'a lieu (pas d'executer_nuit) — c'est un
            # simple "ménage mémoire", pas une clôture pédagogique.
            if ticks_journee_observation >= ticks_par_jour:
                demarrer_journee(etat)
                etat.agent.eval()
                ticks_journee_observation = 0

    except KeyboardInterrupt:
        interrompu = True
        print("\n🛑 Arrêt demandé (Ctrl+C).")

    finally:
        fenetre.fermer()
        etat.env.close()

    print(f"✅ Arène fermée{' (interrompue)' if interrompu else ''}. "
          f"Le cerveau observé n'a pas été modifié (aucune sauvegarde nécessaire).")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="L'Arène & Démo Live — Naulthène AGI (v24.0)")
    parser.add_argument("--brain", type=str, default="brains/naulthene_cursus.brain",
                         help="Fichier .brain à observer (défaut : brains/naulthene_cursus.brain, produit par cursus_developpemental.py)")
    args = parser.parse_args()

    lancer_arene(fichier_brain=args.brain)
