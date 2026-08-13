"""
Le Cursus de la Parole (V27.0, expérimental, "École de la Parole & Synesthésie") — 900
jours × 800 ticks d'acquisition du langage ancré dans la vision (grounding).

Ce module ne vit que dans l'écosystème local de test (voir CLAUDE.md, section
"Variante Locale de Test"), pas encore porté sur `agi_google_colab.py`. Voir
`docs/fonctionnement/CHANGELOG.md` (entrée v27.0) et `readme_fr.md` pour le contexte narratif complet.

Distinct du Cursus par Ères (v23.0, `cursus_developpemental.py`) et du Cerveau Bébé
(v25.0, `cursus_bebe.py`) : les trois paradigmes ne partagent JAMAIS le même cerveau —
celui-ci vit dans son propre fichier `naulthene_parole.brain` (FICHIER_BRAIN_PAROLE).

Ce que ce cursus ajoute par rapport aux deux précédents :
  1. La voix de l'utilisateur (banque vocale disque, voir
     instruments/enregistreur_voix.py) comme référence — remplace `say` quand des
     prises existent, avec formants RÉELS estimés par analyse LPC.
  2. Une récompense/apprentissage MIXTE formants+spectral (voir
     hemisphere_audio.recompense_vocale_mixte) — l'agent est noté ET entraîné sur le
     son réellement synthétisé, pas seulement sur deux nombres.
  3. La synesthésie RÉELLE (noyau.LecteurCaseFrontale) : à partir de la phase 1, le mot
     à nommer n'est plus tiré d'un curriculum abstrait mais LU dans la case juste
     devant l'agent — ce qu'il voit devient ce qu'il doit dire.

Trois phases pédagogiques sur 900 jours subjectifs (noyau.BORNES_PHASES_PAROLE) :

  - Imprégnation totale (jours   1-299) : le professeur nomme systématiquement le mot
    du curriculum courant, matin ET après-midi (guidage=1.0 constant). Il corrige MÊME
    quand l'agent a bon — c'est de l'exposition, pas de l'évaluation.
  - Autonomie guidée   (jours 300-599) : le matin bascule sur la synesthésie (mot lu
    dans la case frontale, agent en mouvement réel) ; l'après-midi reste sur le
    curriculum. Le guidage décroît de 1.0 vers ~0.4 (noyau.taux_guidage_parole) — une
    fraction croissante des ticks laisse l'agent vocaliser SANS cible ni note.
  - Émancipation        (jours 600-899) : synesthésie toute la journée, avec syntagmes
    couleur+objet (LecteurCaseFrontale.lire_syntagme). Guidage ~0.4 → 0.1 : le
    professeur ne intervient plus que sur une minorité de ticks.

Point structurel important : la synesthésie ne peut fonctionner qu'en mode
mode_perception="minigrid" — LecteurCaseFrontale a besoin que l'agent BOUGE (env.step
réellement appelé) pour que la case devant lui change. En "vocal_isole", l'environnement
est en pause (voir noyau._traiter_tick_vocal_isole) et la case resterait figée toute
l'après-midi. C'est la raison du découpage matin(synesthésie)/après-midi(curriculum) des
phases 1-2, symétrique à l'inverse du Cursus par Ères (matin=MiniGrid, après-midi=vocal).

v27.4 (correctif utilisateur, "l'agent a l'air de progresser trop vite") : la cible
synesthésique utilise désormais LecteurCaseFrontale.lire_stable plutôt que lire/
lire_syntagme bruts — sans lissage, le mot cible changeait à CHAQUE tick où l'agent
tournait la tête ou avançait, ne laissant jamais le temps à l'agent de vraiment associer
un mot à l'objet qu'il regarde. lire_stable n'accepte une nouvelle cible qu'après
noyau.SEUIL_STABILITE_SYNESTHESIE (20) ticks CONSÉCUTIFS passés devant le même objet ;
tant qu'aucune cible n'a jamais été stabilisée (début de journée/épisode), aucune
correction n'est appliquée ce tick-là (formants_cibles=None) plutôt que de risquer une
fausse association.

Usage :
    WANDB_MODE=offline python cursus_parole.py           # run complet (900 jours)
    python cursus_parole.py --jours 30                    # run court de test
"""

import argparse

import torch
import wandb

from naulthene.cerveau.noyau import (
    demarrer_journee, traiter_tick, executer_nuit, promouvoir_palier_vocal_si_merite,
    DEVICE, LecteurCaseFrontale,
    TICKS_PAR_JOUR_PAROLE, TICKS_MATIN_PAROLE, JOURS_TOTAUX_PAROLE,
    BORNES_PHASES_PAROLE, phase_parole, taux_guidage_parole,
)
from naulthene.audio.lecons_vocales import CacheReferencesVocales
from naulthene.cerveau.persistance import PersistanceAnatomique
import naulthene.audio.professeur_gemma as pg
import numpy as np

FICHIER_BRAIN_PAROLE = "brains/naulthene_parole.brain"  # dédié, distinct de
                                             # naulthene_cursus.brain (Cursus par Ères),
                                             # naulthene_bb.brain (Cerveau Bébé) et
                                             # naulthene_v21.brain (Cuve/daemon) — les
                                             # quatre écosystèmes ne partagent jamais le
                                             # même cerveau

# Garde-fou "École de Rattrapage Vocal" (repris à l'identique de cursus_bebe.py /
# cursus_developpemental.py) : compteur LOCAL à cette session, pas etat.jour cumulatif.
JOURS_MAX_SANS_PREMIERE_LETTRE = 100

_NOMS_PHASES = (
    "Imprégnation totale",
    "Autonomie guidée",
    "Émancipation",
)


def _cible_synesthesique(etat, cache: CacheReferencesVocales, lecteur: LecteurCaseFrontale,
                          syntagme: bool):
    """(mot, mfcc, formants, notable) déduits de la case DEVANT l'agent, LISSÉS par
    LecteurCaseFrontale.lire_stable (v27.4) — c'est ici que la synesthésie devient
    réelle : l'oreille reçoit le son du mot que l'agent est en train de VOIR, et la
    quête vocale porte la cible F1/F2 mesurée sur la vraie voix de l'utilisateur
    prononçant ce mot précis (si la banque en contient une référence).

    `notable` (nouveau, v27.4) : False tant qu'AUCUNE cible n'a encore été stabilisée
    (début d'épisode, ou l'agent vient de changer ce qu'il regarde) — l'appelant doit
    alors traiter ce tick comme "pas de correction", même si le tirage de guidage
    l'aurait normalement autorisée, pour ne jamais associer un mot à un objet que
    l'agent n'a pas encore regardé assez longtemps. `mfcc`/`formants` restent ceux du
    palier vocal COURANT dans ce cas (l'oreille continue d'entendre un son de fond,
    simplement non corrigé), pour ne jamais laisser obs_auditive à None en synesthésie.

    Si le mot stabilisé n'est dans AUCUN palier du curriculum vocal, on retombe sur le
    palier vocal courant — on ne demande jamais à l'agent de nommer quelque chose dont
    on n'a aucune référence audio à lui faire entendre."""
    mot, _type_objet, _couleur, _stable_ce_tick = lecteur.lire_stable(etat.env, syntagme=syntagme)
    if mot is None:
        mfcc, formants = cache.obtenir_pour_palier(etat.palier_vocal)
        return None, mfcc, formants, False
    palier_du_mot = next((l["palier"] for l in pg.CURRICULUM_VOCAL if l["cible"] == mot), None)
    palier = palier_du_mot if palier_du_mot is not None else etat.palier_vocal
    mfcc, formants = cache.obtenir_pour_palier(palier)
    return mot, mfcc, formants, True


def _perception_du_tick_parole(etat, cache: CacheReferencesVocales, lecteur: LecteurCaseFrontale,
                                phase: int, moment: str, taux_guidage: float):
    """Détermine (mode_perception, obs_auditive, formants_cibles, mfcc_references) pour
    CE tick, selon la phase pédagogique et le moment de la journée.

    Phase 0 (Imprégnation) : curriculum toute la journée, guidage=1.0 constant — voir
    taux_guidage_parole, qui reste à TAUX_GUIDAGE_INITIAL tant que jour < BORNES_PHASES_PAROLE[0].
    Phase 1 (Autonomie guidée) : matin = synesthésie (mode "minigrid", l'agent bouge et
    la case frontale change réellement) ; après-midi = curriculum, mode "vocal_isole"
    (comme les cursus précédents). Phase 2 (Émancipation) : synesthésie toute la
    journée, avec syntagmes couleur+objet.

    Le tirage de guidage (np.random.random() >= taux_guidage → formants_cibles=None)
    laisse l'agent vocaliser SANS être noté sur une fraction croissante des ticks —
    penser() produit parametres_vocaux de toute façon (l'agent "parle" toujours), mais
    personne ne le corrige ce tick-là."""
    guide = np.random.random() < taux_guidage

    if phase == 0:
        mfcc, formants = cache.obtenir_pour_palier(etat.palier_vocal)
        obs_auditive = torch.tensor([mfcc], dtype=torch.float32, device=DEVICE)
        formants_cibles = formants if guide else None
        mfcc_references = cache.obtenir_mfcc_prises(etat.palier_vocal) if guide else None
        return "minigrid", obs_auditive, formants_cibles, mfcc_references

    elif phase == 1:
        if moment == "matin":
            mot, mfcc, formants, notable = _cible_synesthesique(etat, cache, lecteur, syntagme=False)
            obs_auditive = torch.tensor([mfcc], dtype=torch.float32, device=DEVICE)
            formants_cibles = formants if (guide and notable) else None
            palier_mot = next((l["palier"] for l in pg.CURRICULUM_VOCAL if l["cible"] == mot), etat.palier_vocal)
            mfcc_references = cache.obtenir_mfcc_prises(palier_mot) if (guide and notable) else None
            return "minigrid", obs_auditive, formants_cibles, mfcc_references
        else:
            mfcc, formants = cache.obtenir_pour_palier(etat.palier_vocal)
            obs_auditive = torch.tensor([mfcc], dtype=torch.float32, device=DEVICE)
            formants_cibles = formants if guide else None
            mfcc_references = cache.obtenir_mfcc_prises(etat.palier_vocal) if guide else None
            return "vocal_isole", obs_auditive, formants_cibles, mfcc_references

    else:  # phase 2 — synesthésie toute la journée, syntagmes couleur+objet
        mot, mfcc, formants, notable = _cible_synesthesique(etat, cache, lecteur, syntagme=True)
        obs_auditive = torch.tensor([mfcc], dtype=torch.float32, device=DEVICE)
        formants_cibles = formants if (guide and notable) else None
        palier_mot = next((l["palier"] for l in pg.CURRICULUM_VOCAL if l["cible"] == mot), etat.palier_vocal)
        mfcc_references = cache.obtenir_mfcc_prises(palier_mot) if (guide and notable) else None
        return "minigrid", obs_auditive, formants_cibles, mfcc_references


def lancer_cursus_parole(jours_totaux: int = JOURS_TOTAUX_PAROLE, activer_wandb: bool = True,
                          fichier_brain: str = FICHIER_BRAIN_PAROLE):
    """Boucle principale du Cursus de la Parole : `jours_totaux` jours subjectifs
    SUPPLÉMENTAIRES à partir de l'état repris (ou d'un cerveau neuf si aucun `.brain`
    n'existe encore), chaque jour scindé matin/après-midi selon la phase courante (voir
    phase_parole). Réutilise EXACTEMENT les mêmes helpers que les deux autres cursus
    (demarrer_journee, traiter_tick, executer_nuit) — seul ce qui est passé à
    traiter_tick change (mode_perception, formants_cibles, mfcc_references).

    Sauvegarde après CHAQUE nuit (même garantie de reprise que les cursus précédents) —
    un run interrompu (Ctrl+C, panne) ne perd au plus que la journée en cours."""
    if activer_wandb:
        wandb.init(project="Naulthene-AGI", name="Run_27_Ecole_Parole_Synesthesie")

    persistance = PersistanceAnatomique(fichier=fichier_brain)
    etat = persistance.charger_ou_naitre()
    cache = CacheReferencesVocales()
    print("🔥 Préchauffage des références vocales (banque disque → say en repli)...")
    cache.prechauffer()
    print(f"   {cache.resume_banque()}.")

    lecteur = etat.lecteur_case_frontale
    interrompu = False
    arret_garde_fou = False
    jours_ecoules_session = 0  # compteur LOCAL à cette exécution

    try:
        for _ in range(jours_totaux):
            demarrer_journee(etat)
            jours_ecoules_session += 1
            jour = etat.jour
            phase = phase_parole(jour)
            taux_guidage = taux_guidage_parole(jour)
            if jour == 1 or phase_parole(jour - 1) != phase:
                print(f"\n🗣️  [NOUVELLE PHASE] Jour {jour} — entrée dans « {_NOMS_PHASES[phase]} » "
                      f"(taux de guidage : {taux_guidage:.2f}).")

            for tick in range(TICKS_PAR_JOUR_PAROLE):
                moment = "matin" if tick < TICKS_MATIN_PAROLE else "apres_midi"
                mode_perception, obs_auditive, formants_cibles, mfcc_references = (
                    _perception_du_tick_parole(etat, cache, lecteur, phase, moment, taux_guidage)
                )
                traiter_tick(
                    etat, obs_auditive=obs_auditive, formants_cibles=formants_cibles,
                    mode_perception=mode_perception, parent_actif=(phase >= 1),
                    mfcc_references=mfcc_references,
                )

            log = executer_nuit(etat)
            promouvoir_palier_vocal_si_merite(etat)
            log["Phase_Parole"] = phase
            log["Taux_Guidage"] = taux_guidage
            log["Palier_Vocal"] = etat.palier_vocal
            log["Mot_Frontal_Dernier"] = lecteur.dernier_mot
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
              f"/ ATTENUATION_EROSION_AUDIO_DEBUT (noyau.py) avant de relancer "
              f"({fichier_brain}).")
    elif interrompu:
        print(f"\n⏸️  Cursus interrompu au jour {etat.jour} — reprendra à ce point"
              f" au prochain lancement ({fichier_brain}).")
    else:
        print(f"\n✅ Cursus terminé après {jours_totaux} jours subjectifs "
              f"(jour absolu atteint : {etat.jour}).")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Le Cursus de la Parole — Naulthène AGI (v27.0)")
    parser.add_argument("--jours", type=int, default=JOURS_TOTAUX_PAROLE, help="Nombre de jours subjectifs du cursus")
    parser.add_argument("--no-wandb", action="store_true", help="Désactive le logging Weights & Biases")
    # v30.0 — voir cursus_developpemental.py : expose en CLI le `fichier_brain` déjà
    # accepté par la fonction, pour la convention de nommage horodatée (CLAUDE.md).
    parser.add_argument("--brain", type=str, default=FICHIER_BRAIN_PAROLE,
                        help=f"Fichier .brain à charger/sauvegarder (défaut : {FICHIER_BRAIN_PAROLE})")
    args = parser.parse_args()

    lancer_cursus_parole(jours_totaux=args.jours, activer_wandb=not args.no_wandb,
                         fichier_brain=args.brain)
