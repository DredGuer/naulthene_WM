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
vocal, score de formants) à droite, et une bande mini-IRM sous l'image (activations du
bus latent à 3 étapes du tronc cérébral, v26.0-experimental — voir plus bas). Le babil
de l'agent est joué en temps réel dans les haut-parleurs (`hemisphere_audio`).

Mini-IRM en direct (v26.0-experimental) : à chaque tick, le tronc cérébral
(`etat.agent._tronc_cerebral`) est recalculé en lecture seule sous `torch.no_grad()`,
AVANT l'appel réel à `traiter_tick`, pour extraire `bus_latent`/`memoire_actuelle`/
`pensee` — même pattern que `irm_cerveau.py` (`_scanner_un_tick`), mais sur le MÊME
cerveau que celui qui joue dans MiniGrid (un seul `charger_ou_naitre()`, pas deux
copies divergentes), et rendu en pygame pur plutôt qu'en matplotlib (mélanger les deux
frameworks GUI dans un seul thread est fragile sur macOS). Pour un diagnostic complet
avec heatmap de myélinisation et courbe de variance, utiliser toujours
`irm_cerveau.py` séparément — ce mini-panneau ne couvre que le panneau 1 (activations).

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
    etat_mental_dopamine, etat_empreinte, DetecteurJalonsDoorKey, SUCCES_PAR_SOUS_SEUIL,
    DOPAMINE_MIN, DOPAMINE_NEUTRE, DOPAMINE_MAX,
)
from naulthene.cerveau.persistance import PersistanceAnatomique
from naulthene.instruments.arene_visuelle import FenetreArene
from naulthene.audio.hemisphere_audio import SynthetiseurFormants, jouer_son_temps_reel, recompense_formants, SAMPLE_RATE
from naulthene.audio.lecons_vocales import CacheReferencesVocales
import naulthene.audio.professeur_gemma as pg

TICKS_BANDEAU_EVENEMENT = 30  # ~3s à FPS_ARENE=10 (voir arene_visuelle.FPS_ARENE)

# v27.1 (correctif signalé par l'utilisateur, "micro-coupures permanentes") : jusqu'ici
# jouer_son_temps_reel était appelé à CHAQUE tick (10/s, FPS_ARENE) en mode non-bloquant
# — un son dure entre 0.1 et 0.6s (hemisphere_audio.BORNES_DUREE), donc un nouveau
# sd.play() coupait quasi systématiquement le son précédent en plein milieu, produisant
# un crépitement continu indépendant du niveau réel d'apprentissage du cerveau. On
# n'émet désormais qu'un son toutes les PERIODE_LECTURE_VOCALE ticks (5 × 100ms = 0.5s,
# légèrement au-dessus de la durée maximale d'un son) — largement suffisant pour que
# chaque vocalisation se termine avant la suivante. Le score de formants continue
# d'être recalculé à CHAQUE tick (pas de perte de réactivité sur la télémétrie/le
# bandeau), seule la LECTURE audio est espacée.
PERIODE_LECTURE_VOCALE = 5


def _construire_telemetrie(etat, score_vocal) -> dict:
    """Rassemble les infos affichables depuis `EtatCognitif` (objet accessible sans
    encapsulation, voir exploration du plan v24.0) — aucune de ces infos n'est
    retournée par `traiter_tick` lui-même, donc on les lit directement sur `etat`
    après chaque tick.

    v26.0-experimental — parité avec le bilan de nuit console (`noyau.py`,
    `executer_nuit`, bloc `🌙 Jour N [...]`) : la plupart des valeurs ci-dessous sont
    DÉJÀ des attributs accumulés en continu sur `etat` pendant la journée (identiques à
    ce que lirait `executer_nuit` au même instant). Trois valeurs n'existent QUE après
    un vrai `executer_nuit` (jamais appelé ici, garantie de non-altération) et sont donc
    des PROXYS recalculés ici avec la même formule, sans attendre la nuit :
    - `plasticite_base_estimee` : même formule que noyau.py:2624-2627, appliquée à
      `etat.teneur_dopamine` courant au lieu d'une valeur figée en fin de nuit.
    - `erreur_jepa_proxy`/`recompense_proxy` : moyennes sur les buffers déjà accumulés
      ce jour (`etat.erreur_journee`/`etat.recompenses_journee` divisés par
      `len(etat.jepa_losses)`, le nombre de ticks écoulés) — identiques en valeur à ce
      que calculerait `executer_nuit` à cet instant précis (mêmes formules, noyau.py
      lignes 2620-2721), juste lus avant que la nuit ne les remette à zéro.
    - `thermostat_estime` : comparaison simplifiée erreur/seuil, ne peut jamais afficher
      "MUTATION !" (qui exige un vrai appel à `declencher_neurogenese`, jamais fait ici).
    - "souvenirs_en_attente" : PAS un proxy du pourcentage de rêve (qui n'a pas
      d'équivalent continu, dépend de `agent.rever()`) — juste la taille du buffer de
      mémoire moyen-terme accumulé, pour indiquer qu'il y a de la matière en attente."""
    palier_dk = etat.palier_cible if etat.doorkey_actif else None
    nom_palier_vocal = pg.CURRICULUM_VOCAL[etat.palier_vocal - 1]["nom"] \
        if 0 < etat.palier_vocal <= len(pg.CURRICULUM_VOCAL) else "—"

    etat_mental, pct_dopamine = etat_mental_dopamine(etat.teneur_dopamine, DOPAMINE_MIN, DOPAMINE_NEUTRE, DOPAMINE_MAX)
    if etat.teneur_dopamine >= DOPAMINE_NEUTRE:
        plasticite_base_estimee = 1.0
    else:
        plasticite_base_estimee = max(0.0, (etat.teneur_dopamine - DOPAMINE_MIN) / (DOPAMINE_NEUTRE - DOPAMINE_MIN))

    ticks_du_jour = len(etat.jepa_losses) or 1  # évite une division par zéro tout début de journée
    erreur_jepa_proxy = etat.erreur_journee / ticks_du_jour
    recompense_proxy = sum(etat.recompenses_journee) / ticks_du_jour if etat.recompenses_journee else 0.0
    if erreur_jepa_proxy > etat.seuil_actuel:
        thermostat_estime = "Au-dessus du seuil (nuit requise pour mutation)"
    else:
        thermostat_estime = "Sous le seuil"

    taux_maitrise_txt = "N/A"
    nom_palier_doorkey = None
    sous_seuil_nom = None
    mode_decision_txt = None
    if palier_dk is not None:
        nom_palier_doorkey = DetecteurJalonsDoorKey.NOMS[palier_dk - 1]
        if etat.episodes_jour > 0:
            taux_maitrise_txt = f"{100.0 * etat.succes_palier_cible_jour / etat.episodes_jour:.0f}%"
        sous_seuil_nom = "Amorçage" if etat.gestionnaire_cursus.sous_seuil_actuel == 1 else "Abnégation"
        mode_decision_txt = "🕊️ Libre (aucune récompense de guidage)" if etat.mode_libre else "🧭 Guidé (béquille active)"

    quete_bio = etat.moteur_bio.quete_active["type"] if etat.moteur_bio.quete_active else "Aucune"

    return {
        "dopamine": etat.teneur_dopamine,
        "etat_mental": etat_mental,
        "pct_dopamine": pct_dopamine,
        "dim_bus": etat.agent.dim_bus,
        "empreinte_enfance": etat.empreinte_enfance,
        "etat_plasticite": etat_empreinte(etat.empreinte_enfance),
        "plasticite_base_estimee": plasticite_base_estimee,
        "palier_doorkey": palier_dk,
        "nom_palier_doorkey": nom_palier_doorkey,
        "succes_palier_jour": etat.succes_palier_cible_jour,
        "episodes_jour": etat.episodes_jour,
        "taux_maitrise_txt": taux_maitrise_txt,
        "sous_seuil_actuel": etat.gestionnaire_cursus.sous_seuil_actuel if palier_dk is not None else None,
        "sous_seuil_nom": sous_seuil_nom,
        "succes_sous_seuil": etat.gestionnaire_cursus.succes_sous_seuil_courant if palier_dk is not None else 0,
        "succes_par_sous_seuil": SUCCES_PAR_SOUS_SEUIL,
        "facteur_complexite_jour": etat.facteur_complexite_jour,
        "mode_decision_txt": mode_decision_txt,
        "force_planification": etat.force_planification_jour,
        "coeff_entropie": etat.coeff_entropie_jour,
        "portes_franchies_jour": etat.portes_franchies_jour,
        "progres_personnel_jour": etat.progres_personnel_jour if not etat.doorkey_actif else 0,
        "souvenirs_en_attente": len(etat.memoire_moyen_terme),
        "patience_base_jour": etat.patience_base_jour,
        "abandons_patience_jour": etat.abandons_patience_jour,
        "sursauts_jour": etat.sursauts_jour,
        "patience_min": etat.module_acceptation.patience_min,
        "sous_objectifs_curiosite_jour": etat.sous_objectifs_curiosite_jour if etat.mode_libre else 0,
        "satiete": etat.moteur_bio.satiete,
        "hydratation": etat.moteur_bio.hydratation,
        "stimulation": etat.moteur_bio.stimulation,
        "quete_bio": quete_bio,
        "r_bio_jour": etat.r_bio_jour,
        "food_consommes_jour": etat.food_consommes_jour,
        "water_consommes_jour": etat.water_consommes_jour,
        "effort_moyen_jour": etat.effort_metabolique_jour / ticks_du_jour,
        "souvenirs_spatiaux": len(etat.memoire_episodique_spatiale.souvenirs),
        "erreur_jepa_proxy": erreur_jepa_proxy,
        "recompense_proxy": recompense_proxy,
        "thermostat_estime": thermostat_estime,
        "niveau_minigrid": etat.nom_classe,
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
    print("ℹ️  La promotion de NIVEAU MiniGrid (changement de carte) ne peut pas se produire "
          "dans l'Arène — elle est décidée uniquement pendant une vraie nuit (executer_nuit), "
          "jamais appelée ici pour garantir que l'observation n'altère jamais le cerveau. "
          "Relance le cursus/la Cuve pour voir une promotion de niveau. Le changement de "
          "PALIER DoorKey, lui, s'observe normalement (bandeau d'événement ci-dessous).")

    fenetre = FenetreArene()
    synth = SynthetiseurFormants()
    cache_vocal = CacheReferencesVocales()
    print("🔥 Préchauffage de la référence vocale du palier courant...")
    cache_vocal.obtenir_pour_palier(etat.palier_vocal)
    interrompu = False
    palier_precedent = etat.palier_cible if etat.doorkey_actif else None
    ticks_restants_bandeau = 0
    texte_bandeau = None
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

            # Mini-IRM (v26.0-experimental) : recalcul en lecture seule du tronc cérébral
            # sur l'observation du tick COURANT — même pattern que irm_cerveau.py
            # (_scanner_un_tick), appelé AVANT traiter_tick pour lire etat.etat_courant/
            # etat.memoire_tampon avant que penser() (dans traiter_tick) ne les réécrive.
            # torch.no_grad() : aucune conséquence sur l'apprentissage, une lecture pure.
            with torch.no_grad():
                bus_latent_irm, memoire_actuelle_irm, pensee_irm = etat.agent._tronc_cerebral(
                    etat.etat_courant, etat.memoire_tampon.detach(), obs_auditive=obs_auditive
                )
            activations = {
                "bus_latent": bus_latent_irm.cpu().numpy().flatten(),
                "memoire_actuelle": memoire_actuelle_irm.cpu().numpy().flatten(),
                "pensee": pensee_irm.cpu().numpy().flatten(),
            }

            infos = traiter_tick(etat, obs_auditive=obs_auditive, formants_cibles=formants_cibles)
            image = etat.env.render()
            ticks_journee_observation += 1

            vecteur_vocal = infos["infos_internes"]["parametres_vocaux"]
            score_vocal = None
            if vecteur_vocal:
                # v27.1 : lecture espacée (voir PERIODE_LECTURE_VOCALE) — évite de
                # lancer un nouveau sd.play() par-dessus un son encore en train de
                # jouer, cause des micro-coupures rapportées à chaque tick.
                if ticks_journee_observation % PERIODE_LECTURE_VOCALE == 0:
                    onde = synth.synthetiser(vecteur_vocal)
                    jouer_son_temps_reel(onde, sample_rate=SAMPLE_RATE, bloquant=False)
                formants_produits = synth.parametres_depuis_vecteur(vecteur_vocal)
                score_vocal = recompense_formants(formants_cibles, formants_produits)

            # Bandeau d'événement (v26.0-experimental) : détecte un changement de palier
            # DoorKey par diff entre deux ticks — palier_cible EST mis à jour en continu
            # dans traiter_tick (noyau.py:2523-2525), contrairement à la promotion de
            # NIVEAU MiniGrid (voir note affichée au démarrage). Même formulation que le
            # print console existant.
            palier_courant = etat.palier_cible if etat.doorkey_actif else None
            if palier_courant is not None and palier_precedent is not None and palier_courant != palier_precedent:
                nom_nouveau_palier = DetecteurJalonsDoorKey.NOMS[palier_courant - 1]
                texte_bandeau = f"🎓 Palier {palier_courant} visé : {nom_nouveau_palier}"
                ticks_restants_bandeau = TICKS_BANDEAU_EVENEMENT
            palier_precedent = palier_courant

            telemetrie = _construire_telemetrie(etat, score_vocal)
            evenement_a_afficher = texte_bandeau if ticks_restants_bandeau > 0 else None
            fenetre.dessiner_frame(image, telemetrie, activations=activations, evenement=evenement_a_afficher)
            if ticks_restants_bandeau > 0:
                ticks_restants_bandeau -= 1

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
