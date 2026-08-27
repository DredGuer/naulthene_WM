# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Adrien Nault — Naulthène AGI
"""
Le Cerveau Bébé Développemental (V25.0, expérimental) — 4 ans (1440 jours × 3600
ticks) d'apprentissage 100% auto-supervisé avant tout signal de récompense externe.

Ce module ne vit que dans l'écosystème local de test (voir CLAUDE.md, section
"Variante Locale de Test"), pas encore porté sur `agi_google_colab.py`. Voir
`readme_fr.md` (section "Nouveautés v25.0 — Le Cerveau Bébé Développemental") pour le
contexte narratif complet et `CHANGELOG.md` pour le détail technique du commit.

Distinct du Cursus Développemental par Ères (v23.0, `cursus_developpemental.py`,
1000 jours / 3 ères / `naulthene_cursus.brain`) : les deux paradigmes ne partagent
JAMAIS le même cerveau — celui-ci vit dans son propre fichier `naulthene_bb.brain`
(FICHIER_BRAIN_BEBE). `cursus_developpemental.py` reste intact et utilisable tel quel.

Vision du paradigme (Piaget / Dehaene plutôt que RL classique) : au lieu de mesurer le
cursus en réussites de tâche, le bébé traverse 5 phases d'âge sur 1440 jours
subjectifs (agi_local_test.BORNES_PHASES_BEBE) :

  - Éveil des Sens    (jours   1- 90, ~0-3 mois)  : vision floue/réflexes, babil brut
                        (palier vocal 1, "Vocaliser"). 70% de dodo. Récompense externe
                        VERROUILLÉE à zéro (masquer_recompense_externe=True) — l'agent
                        n'a "aucune idée s'il fait bien ou mal", seuls JEPA +
                        homéostasie + curiosité pilotent l'apprentissage.
  - Exploration Motrice (jours  91-180, ~3-6 mois) : coordination œil-main, voyelles
                        a/e/i/o/u (paliers 2-6). 60% de dodo. Toujours masqué.
  - Locomotion & Concepts (jours 181-360, ~6-12 mois) : déplacements/objets, syllabes
                        ba/ma/pa (paliers 7-9). 50% de dodo. Le masquage lève à
                        JOUR_FIN_MASQUAGE_EXTERNE (240) — le Module "Parent" active
                        dès ce jour (voir agi_local_test._appliquer_feedback_parent_vocal).
  - Association Forte (jours 361-720, ~12-24 mois) : navigation ciblée, mots
                        papa/maman/porte (paliers 10-12). 40% de dodo. Parent actif,
                        récompense externe réelle.
  - Jeune Enfant      (jours 721-1440, ~24-48 mois) : planification complexe,
                        combinatoire Action+Objet (paliers 13+). 35% de dodo.

Chaque jour reste scindé matin (TICKS_MATIN_BEBE premiers ticks, focus MiniGrid) /
après-midi (focus vocal isolé) — même ratio 50/50 que TICKS_MATIN/ticks_par_jour du
Cursus par Ères, mais rapporté à TICKS_PAR_JOUR_BEBE (3600 ticks/jour, pas 400 —
constante dédiée, jamais mélangée avec celle du Cursus par Ères). Le
curriculum MiniGrid (`PROGRAMME`) et le curriculum vocal (`professeur_gemma.
CURRICULUM_VOCAL`) progressent en parallèle, comme dans le Cursus par Ères — seule la
DURÉE du cursus, le découpage en 5 phases (pas 3 ères) et les deux mécaniques nouvelles
(masquage + Parent + sommeil variable) changent.

Usage :
    WANDB_MODE=offline python cursus_bebe.py           # run complet (1440 jours)
    python cursus_bebe.py --jours 30                    # run court de test
"""

import argparse

import torch
import wandb

from naulthene.cerveau.noyau import (
    demarrer_journee, traiter_tick, executer_nuit,
    DEVICE, TICKS_PAR_JOUR_BEBE, TICKS_MATIN_BEBE,
    JOURS_TOTAUX_BEBE, JOUR_FIN_MASQUAGE_EXTERNE, BORNES_PHASES_BEBE,
    phase_bebe, plafond_reve_bebe, seuil_jour_vocal_reussi,
)
from naulthene.audio.lecons_vocales import CacheReferencesVocales
from naulthene.cerveau.persistance import PersistanceAnatomique
import naulthene.audio.professeur_gemma as pg

FICHIER_BRAIN_BEBE = "brains/naulthene_bb.brain"  # dédié, distinct de naulthene_cursus.brain
                                             # (Cursus par Ères) et naulthene_v21.brain
                                             # (Cuve/daemon) — les trois écosystèmes ne
                                             # partagent jamais le même cerveau

# Garde-fou "École de Rattrapage Vocal" (repris à l'identique de
# cursus_developpemental.py — même diagnostic possible : un seuil de promotion trop
# ambitieux, ou une érosion nocturne trop agressive, peut bloquer tout apprentissage
# vocal indéfiniment sans qu'aucun signal ne le signale). Compteur LOCAL à cette
# session (jours_ecoules_session), pas etat.jour cumulatif — voir cursus_developpemental.py
# pour la justification complète du bug évité.
JOURS_MAX_SANS_PREMIERE_LETTRE = 100

# Nombre de paliers vocaux consommés par phase avant l'ère "combinatoire" (phase 4) où
# la cible suit l'action jouée, comme dans l'Ère Intégration du Cursus par Ères — v1
# volontairement minimale, un vrai vocabulaire sémantique riche reste hors de portée de
# cette itération (voir cursus_developpemental.VOYELLE_PAR_ACTION pour le précédent).
VOYELLE_PAR_ACTION = {
    0: "i",  # left
    1: "o",  # right
    2: "a",  # forward — l'action la plus fréquente, la voyelle la plus simple
    3: "u",  # pickup
    4: "u",  # drop
    5: "e",  # toggle (ouvrir/porte)
    6: "a",  # done
}


def _perception_du_tick_bebe(etat, cache: CacheReferencesVocales, phase: int, moment: str,
                               derniere_action: int):
    """Détermine (mode_perception, obs_auditive, formants_cibles) pour CE tick, selon
    la phase d'âge et le moment de la journée. Retourne toujours un triplet.

    Phases 0-1 (Éveil des Sens, Exploration Motrice) : matin MiniGrid pur (silence),
    après-midi vocal isolé — le bébé le plus jeune ne fait jamais les deux à la fois.
    Phase 2 (Locomotion & Concepts) : matin devient multimodal (MiniGrid ET audio en
    même temps), après-midi vocal isolé sur les paliers plus avancés. Phases 3-4
    (Association Forte, Jeune Enfant) : toute la journée multimodale, cible vocale
    dérivée de la dernière action jouée (verbalisation de l'action, comme l'Ère
    Intégration du Cursus par Ères)."""
    if phase <= 1:
        if moment == "matin":
            return "minigrid", None, None
        else:
            mfcc, formants = cache.obtenir_pour_palier(etat.palier_vocal)
            obs_auditive = torch.tensor([mfcc], dtype=torch.float32, device=DEVICE)
            return "vocal_isole", obs_auditive, formants

    elif phase == 2:
        mfcc, formants = cache.obtenir_pour_palier(etat.palier_vocal)
        obs_auditive = torch.tensor([mfcc], dtype=torch.float32, device=DEVICE)
        if moment == "matin":
            return "minigrid", obs_auditive, formants
        else:
            return "vocal_isole", obs_auditive, formants

    else:  # phase 3 ou 4 — toute la journée multimodale, cible = dernière action jouée
        voyelle = VOYELLE_PAR_ACTION.get(derniere_action, "a")
        from naulthene.audio.hemisphere_audio import VOYELLES_CIBLES
        mfcc, _ = cache.obtenir_pour_palier(2)  # palier 2 = "a", juste un MFCC de référence stable
        formants = VOYELLES_CIBLES[voyelle]
        obs_auditive = torch.tensor([mfcc], dtype=torch.float32, device=DEVICE)
        return "minigrid", obs_auditive, formants


def _promouvoir_palier_vocal_si_merite(etat):
    """Décide, en fin de journée, si le score de formants moyen du jour justifie une
    promotion du palier vocal — identique à cursus_developpemental.py (même
    mécanisme GestionnaireCursusAbnegation via l'instance séparée
    etat.gestionnaire_cursus_vocal, même seuil progressif seuil_jour_vocal_reussi)."""
    ticks_vocaux = getattr(etat, "ticks_vocaux_jour", 0)
    if ticks_vocaux == 0:
        return

    seuil_du_jour = seuil_jour_vocal_reussi(etat.palier_vocal)
    score_moyen_jour = getattr(etat, "score_vocal_jour", 0.0) / ticks_vocaux
    jour_reussi = score_moyen_jour >= seuil_du_jour

    promu, message = etat.gestionnaire_cursus_vocal.enregistrer_resultat_episode(jour_reussi)
    if message:
        print(f"   🗣️ {message} (score vocal moyen du jour: {score_moyen_jour:.3f}, "
              f"seuil École de Rattrapage: {seuil_du_jour:.3f})")
    if promu and etat.palier_vocal < len(pg.CURRICULUM_VOCAL):
        etat.palier_vocal += 1
        nom_palier = pg.CURRICULUM_VOCAL[etat.palier_vocal - 1]["nom"]
        print(f"   🎓 [PROMOTION VOCALE] Palier {etat.palier_vocal} visé : {nom_palier}")


_NOMS_PHASES = (
    "Éveil des Sens (0-3 mois)",
    "Exploration Motrice (3-6 mois)",
    "Locomotion & Concepts (6-12 mois)",
    "Association Forte (12-24 mois)",
    "Jeune Enfant (24-48 mois)",
)


def lancer_cursus_bebe(jours_totaux: int = JOURS_TOTAUX_BEBE, activer_wandb: bool = True,
                         fichier_brain: str = FICHIER_BRAIN_BEBE):
    """Boucle principale du Cerveau Bébé : `jours_totaux` jours subjectifs
    SUPPLÉMENTAIRES à partir de l'état repris (ou d'un cerveau neuf si aucun `.brain`
    n'existe encore), chaque jour scindé en matin/après-midi selon la phase d'âge
    courante (voir phase_bebe). Réutilise EXACTEMENT les mêmes helpers que le Cursus
    par Ères et le mode standalone (demarrer_journee, traiter_tick, executer_nuit) —
    seuls CE QUI est passé à traiter_tick/executer_nuit change (masquage de récompense,
    Module Parent, plafond de rêve variable).

    Sauvegarde après CHAQUE nuit (même garantie de reprise que le Cursus par Ères) —
    un run interrompu (Ctrl+C, panne) ne perd au plus que la journée en cours."""
    if activer_wandb:
        wandb.init(project="Naulthene-AGI", name="Run_25_Bebe_Developpemental_4ans")

    persistance = PersistanceAnatomique(fichier=fichier_brain)
    etat = persistance.charger_ou_naitre()
    cache = CacheReferencesVocales()
    print("🔥 Préchauffage des références vocales (say → MFCC, une seule fois)...")
    cache.prechauffer()
    print(f"   {cache._nb_appels_say} référence(s) audio générée(s) et mises en cache.")

    derniere_action = 2  # "forward" par défaut avant le tout premier tick
    interrompu = False
    arret_garde_fou = False
    jours_ecoules_session = 0  # compteur LOCAL à cette exécution (voir garde-fou plus bas)

    try:
        for _ in range(jours_totaux):
            demarrer_journee(etat)
            jours_ecoules_session += 1
            jour = etat.jour
            phase = phase_bebe(jour)
            if jour == 1 or phase_bebe(jour - 1) != phase:
                print(f"\n👶 [NOUVELLE PHASE] Jour {jour} — entrée dans « {_NOMS_PHASES[phase]} ».")

            masquer_recompense_externe = jour < JOUR_FIN_MASQUAGE_EXTERNE
            parent_actif = not masquer_recompense_externe
            if jour == JOUR_FIN_MASQUAGE_EXTERNE:
                print(f"\n👨‍👩‍👦 [MODULE PARENT] Jour {jour} — fin du masquage de récompense "
                      f"externe, le feedback social vocal (\"Oui !\"/\"Non !\") s'active.")

            for tick in range(TICKS_PAR_JOUR_BEBE):
                moment = "matin" if tick < TICKS_MATIN_BEBE else "apres_midi"
                mode_perception, obs_auditive, formants_cibles = _perception_du_tick_bebe(
                    etat, cache, phase, moment, derniere_action
                )
                infos = traiter_tick(
                    etat, obs_auditive=obs_auditive, formants_cibles=formants_cibles,
                    mode_perception=mode_perception,
                    masquer_recompense_externe=masquer_recompense_externe,
                    parent_actif=parent_actif,
                )
                if infos["action"] is not None:
                    derniere_action = infos["action"]

            log = executer_nuit(etat, plafond_reve=plafond_reve_bebe(jour))
            _promouvoir_palier_vocal_si_merite(etat)
            log["Phase_Bebe"] = phase
            log["Palier_Vocal"] = etat.palier_vocal
            log["Masquage_Recompense_Externe"] = int(masquer_recompense_externe)
            log["Parent_Actif"] = int(parent_actif)
            if activer_wandb:
                wandb.log(log)

            persistance.sauvegarder(etat)

            if etat.palier_vocal == 1 and jours_ecoules_session >= JOURS_MAX_SANS_PREMIERE_LETTRE:
                arret_garde_fou = True
                print(f"\n🚨 [ÉCOLE DE RATTRAPAGE] Aucune voyelle validée après "
                      f"{jours_ecoules_session} jours de cette session (jour absolu du "
                      f"cerveau : {etat.jour} ; seuil : {JOURS_MAX_SANS_PREMIERE_LETTRE}) "
                      f"— arrêt du cursus. Le cerveau reste sauvegardé (palier_vocal=1) ; "
                      f"vérifie le seuil/l'atténuation d'érosion avant de relancer.")
                break

    except KeyboardInterrupt:
        interrompu = True
        print("\n🛑 Arrêt demandé (Ctrl+C) — sauvegarde d'urgence de la journée déjà"
              " consolidée (la journée en cours, elle, est perdue)...")
        persistance.sauvegarder(etat)

    finally:
        etat.env.close()

    if arret_garde_fou:
        print(f"\n🚨 Cursus arrêté par l'École de Rattrapage après "
              f"{jours_ecoules_session} jours de cette session (jour absolu du cerveau "
              f": {etat.jour}) — aucune voyelle validée en "
              f"{JOURS_MAX_SANS_PREMIERE_LETTRE} jours. Ajuste SEUIL_VOCAL_PALIER_DEBUTANT "
              f"/ ATTENUATION_EROSION_AUDIO_DEBUT (agi_local_test.py) avant de relancer "
              f"({fichier_brain}).")
    elif interrompu:
        print(f"\n⏸️  Cursus interrompu au jour {etat.jour} — reprendra à ce point"
              f" au prochain lancement ({fichier_brain}).")
    else:
        print(f"\n✅ Cursus terminé après {jours_totaux} jours subjectifs "
              f"(jour absolu atteint : {etat.jour}).")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Le Cerveau Bébé Développemental — Naulthène AGI (v25.0)")
    parser.add_argument("--jours", type=int, default=JOURS_TOTAUX_BEBE, help="Nombre de jours subjectifs du cursus")
    parser.add_argument("--no-wandb", action="store_true", help="Désactive le logging Weights & Biases")
    # v30.0 — voir cursus_developpemental.py : expose en CLI le `fichier_brain` déjà
    # accepté par la fonction, pour la convention de nommage horodatée (CLAUDE.md).
    parser.add_argument("--brain", type=str, default=FICHIER_BRAIN_BEBE,
                        help=f"Fichier .brain à charger/sauvegarder (défaut : {FICHIER_BRAIN_BEBE})")
    args = parser.parse_args()

    lancer_cursus_bebe(jours_totaux=args.jours, activer_wandb=not args.no_wandb,
                       fichier_brain=args.brain)
