# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Adrien Nault — Naulthène AGI
"""
Le Cursus Développemental par Ères (V23.0/V24.0, expérimental) — 1000 jours
d'apprentissage autonome, MiniGrid + parole.

Ce module ne vit que dans l'écosystème local de test (voir CLAUDE.md, section
"Variante Locale de Test"), pas encore porté sur `agi_google_colab.py`. Voir les plans
v23.0/v24.0 et `readme_fr.md` (section "Le Cursus Développemental par Ères") pour le
contexte narratif complet.

v24.0 — persistance (préalable à la Phase 2 "Arène & Démo Live") : jusqu'ici ce script
faisait TOUJOURS naître un cerveau neuf via `initialiser_etat_cognitif()` et ne
sauvegardait jamais rien — un cursus de 1000 jours disparaissait intégralement à la fin
du process, sans rien à observer ensuite. Le cursus reprend désormais un cerveau
existant via `PersistanceAnatomique` (fichier dédié `naulthene_cursus.brain`, distinct
de `naulthene_v21.brain` utilisé par la Cuve/daemon — les deux écosystèmes ne se
mélangent jamais) et sauvegarde après CHAQUE nuit (donc chaque jour subjectif).

Jusqu'à la v22.1, l'apprentissage vocal ne se déclenchait que via une leçon manuelle
(`client_professeur.py --palier N`, un humain choisit le palier). Ce script fait
tourner l'agent SEUL, sans client réseau, à travers un programme de 1000 jours
subjectifs organisé en 3 ères de difficulté croissante — exactement comme un enfant qui
passe de la crèche à l'école primaire :

  - Ère Alternance (jours 1-399) : chaque journée se scinde en un MATIN (MiniGrid pur,
    `mode_perception="minigrid"`) et un APRÈS-MIDI (parole isolée, l'agent "au calme,
    écran noir", `mode_perception="vocal_isole"` — voir `agi_local_test.traiter_tick`).
  - Ère Synesthésie (jours 400-599) : le matin devient multimodal (MiniGrid ET audio
    simultanés, le cerveau unifié gère les deux à la fois) ; l'après-midi étend le
    vocabulaire aux syllabes/mots (paliers 7+ du curriculum vocal).
  - Ère Intégration (jours 600-999) : toute la journée est multimodale — l'agent
    verbalise une cible vocale liée à l'action MiniGrid qu'il vient de jouer (mapping
    action→voyelle, v1 volontairement minimale — voir Question ouverte B du plan v23.0).

Le curriculum MiniGrid (`PROGRAMME`, Primaire→Doctorat) et le curriculum vocal
(`professeur_gemma.CURRICULUM_VOCAL`, voyelles→syllabes→mots) progressent en PARALLÈLE,
chacun par son propre mécanisme de promotion — les ères ne remplacent ni l'un ni
l'autre, elles orchestrent QUAND chacun est actif dans la journée (décision
utilisateur).

Usage :
    WANDB_MODE=offline python cursus_developpemental.py          # run complet (1000 jours)
    python cursus_developpemental.py --jours 30                   # run court de test
"""

import argparse

import torch
import wandb

from naulthene.cerveau.noyau import (
    demarrer_journee, traiter_tick, executer_nuit,
    ere_courante, DEVICE, DIM_MFCC, ticks_par_jour, TICKS_MATIN, DUREE_ERE,
    seuil_jour_vocal_reussi,
)
from naulthene.audio.lecons_vocales import CacheReferencesVocales
from naulthene.cerveau.persistance import PersistanceAnatomique
import naulthene.audio.professeur_gemma as pg

FICHIER_BRAIN_CURSUS = "brains/naulthene_cursus.brain"  # dédié, distinct de naulthene_v21.brain
                                                    # (Cuve/daemon) — les deux écosystèmes
                                                    # (cursus autonome vs client-serveur)
                                                    # ne partagent jamais le même cerveau

# Garde-fou "École de Rattrapage Vocal" (v24.0-fix2, corrigé v24.0-fix3) : sur le run
# réel de 1000 jours qui a révélé le blocage du seuil de promotion (voir
# agi_local_test.py, correctif v24.0-fix1), aucun signal ne prévenait qu'un cursus
# entier tournait dans le vide côté vocal — il a fallu inspecter le .brain à la main
# après coup pour s'en apercevoir. Si après JOURS_MAX_SANS_PREMIERE_LETTRE jours
# subjectifs ÉCOULÉS DANS CETTE SESSION (pas etat.jour cumulatif depuis la naissance
# du cerveau — voir bug v24.0-fix2 : un vieux cerveau repris après 970 jours vécus AVANT
# le correctif de seuil se voyait couper la parole dès le 1er jour de la nouvelle
# tentative, sans laisser de vraie chance au nouveau seuil de prouver qu'il fonctionne)
# le palier vocal n'a JAMAIS quitté le palier 1 (aucune voyelle validée), le cursus
# s'arrête proprement — sauvegarde incluse, comme une interruption Ctrl+C — plutôt que
# de tourner à vide jusqu'au bout des jours_totaux demandés. Ne se déclenche qu'UNE
# fois avant la toute première promotion : passé ce cap, palier_vocal > 1 pour de bon
# (aucun mécanisme de rétrogradation dans GestionnaireCursusAbnegation), donc le
# garde-fou ne peut plus jamais se redéclencher plus tard dans le curriculum.
JOURS_MAX_SANS_PREMIERE_LETTRE = 100

# Mapping action MiniGrid -> voyelle verbalisée, Ère Intégration UNIQUEMENT (v1
# minimale assumée, voir plan v23.0 Question ouverte B — pas un vrai vocabulaire
# sémantique riche, juste de quoi "verbaliser en bougeant" dans l'espace déjà appris
# par le curriculum vocal existant). Actions MiniGrid : left=0, right=1, forward=2,
# pickup=3, drop=4, toggle=5, done=6 (voir CLAUDE.md, COUT_CORPOREL_PAR_ACTION).
VOYELLE_PAR_ACTION = {
    0: "i",  # left  — voyelle aiguë/fermée, mnémonique arbitraire mais stable
    1: "o",  # right
    2: "a",  # forward — l'action la plus fréquente, la voyelle la plus simple (palier 2)
    3: "u",  # pickup
    4: "u",  # drop
    5: "e",  # toggle (ouvrir/porte)
    6: "a",  # done
}


def _perception_du_tick(etat, cache: CacheReferencesVocales, ere: str, moment: str,
                          derniere_action: int):
    """Détermine (mode_perception, obs_auditive, formants_cibles) pour CE tick, selon
    l'ère et le moment de la journée — voir le docstring de ce module pour la
    description narrative des 3 ères. Retourne toujours un triplet, y compris pour le
    matin de l'Ère Alternance (mode "minigrid", silence pur — identique au comportement
    pré-v23.0)."""
    if ere == "alternance":
        if moment == "matin":
            return "minigrid", None, None
        else:
            mfcc, formants = cache.obtenir_pour_palier(etat.palier_vocal)
            obs_auditive = torch.tensor([mfcc], dtype=torch.float32, device=DEVICE)
            return "vocal_isole", obs_auditive, formants

    elif ere == "synesthesie":
        # Matin : MiniGrid ET audio EN MÊME TEMPS (mode "minigrid" avec obs_auditive
        # fourni — traiter_tick gère déjà la fusion multimodale, voir agi_local_test.py
        # _tronc_cerebral). Après-midi : même mécanique que l'Alternance, mais le
        # palier vocal a eu le temps de progresser vers les syllabes/mots (paliers 7+).
        mfcc, formants = cache.obtenir_pour_palier(etat.palier_vocal)
        obs_auditive = torch.tensor([mfcc], dtype=torch.float32, device=DEVICE)
        if moment == "matin":
            return "minigrid", obs_auditive, formants
        else:
            return "vocal_isole", obs_auditive, formants

    else:  # "integration"
        # Toute la journée multimodale, cible vocale dérivée de la DERNIÈRE action
        # jouée (verbalisation de l'action, v1 minimale — voir VOYELLE_PAR_ACTION).
        voyelle = VOYELLE_PAR_ACTION.get(derniere_action, "a")
        from naulthene.audio.hemisphere_audio import VOYELLES_CIBLES
        mfcc, _ = cache.obtenir_pour_palier(2)  # palier 2 = "a", juste pour un MFCC de référence stable
        # La cible vocale suit l'action, indépendamment du palier vocal atteint —
        # cohérent avec "verbaliser ce qu'il fait", pas "réciter le curriculum".
        formants = VOYELLES_CIBLES[voyelle]
        obs_auditive = torch.tensor([mfcc], dtype=torch.float32, device=DEVICE)
        return "minigrid", obs_auditive, formants


def _promouvoir_palier_vocal_si_merite(etat):
    """Décide, en fin de journée, si le score de formants moyen du jour justifie une
    promotion du palier vocal — réutilise GestionnaireCursusAbnegation (mécanisme 2+2
    succès déjà utilisé pour les 7 paliers DoorKey, voir agi_local_test.py) via
    l'instance SÉPARÉE etat.gestionnaire_cursus_vocal.

    École de Rattrapage Vocal (v24.0-fix1) : le seuil n'est plus une constante fixe —
    `seuil_jour_vocal_reussi(etat.palier_vocal)` le fait progresser de 0.15 (débutant)
    à 0.45 (avancé) à mesure que le palier vocal monte. Diagnostiqué sur un run réel de
    1000 jours : un seuil fixe à 0.5 avait laissé gestionnaire_cursus_vocal_succes_courant
    bloqué à 0 du premier au dernier jour — aucune promotion, aucun apprentissage
    vocal viable (porte_auditive restée à norme exactement zéro)."""
    ticks_vocaux = getattr(etat, "ticks_vocaux_jour", 0)
    if ticks_vocaux == 0:
        return  # aucun tick vocal ce jour (ne devrait pas arriver dans ce cursus, garde-fou)

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


def lancer_cursus(jours_totaux: int = DUREE_ERE, activer_wandb: bool = True,
                    fichier_brain: str = FICHIER_BRAIN_CURSUS):
    """Boucle principale du cursus : `jours_totaux` jours subjectifs SUPPLÉMENTAIRES à
    partir de l'état repris (ou d'un cerveau neuf si aucun `.brain` n'existe encore),
    chaque jour scindé en matin/après-midi selon l'ère courante (voir ere_courante).
    Réutilise EXACTEMENT les mêmes helpers que le mode standalone classique
    (demarrer_journee, traiter_tick, executer_nuit) — seule la logique de CE QUI est
    passé à traiter_tick change selon le moment de la journée.

    v24.0 : sauvegarde après CHAQUE nuit (persistance.py, fichier_brain dédié) — un
    cursus interrompu (Ctrl+C, panne) ne perd au plus que la journée en cours, jamais
    les précédentes. `ere_courante` reste dérivée de `etat.jour`, qui continue de
    s'incrémenter depuis la valeur reprise (pas remis à 1) — reprendre un cursus au
    jour 450 reste bien en Ère Synesthésie, pas de retour en arrière artificiel."""
    if activer_wandb:
        wandb.init(project="Naulthene-AGI", name="Run_23_Cursus_Developpemental_Eres")

    persistance = PersistanceAnatomique(fichier=fichier_brain)
    etat = persistance.charger_ou_naitre()
    cache = CacheReferencesVocales()
    print("🔥 Préchauffage des références vocales (say → MFCC, une seule fois)...")
    cache.prechauffer()
    print(f"   {cache._nb_appels_say} référence(s) audio générée(s) et mises en cache.")

    derniere_action = 2  # "forward" par défaut avant le tout premier tick
    interrompu = False
    arret_garde_fou = False  # v24.0-fix2 — distinct de interrompu (Ctrl+C) pour un
                               # message de fin honnête (voir bloc final)
    jours_ecoules_session = 0  # v24.0-fix3 — compteur LOCAL à cette exécution du
                                 # script (par opposition à etat.jour, cumulatif depuis
                                 # la naissance du cerveau) : le garde-fou juge le
                                 # seuil ACTUEL sur une vraie fenêtre de
                                 # JOURS_MAX_SANS_PREMIERE_LETTRE jours à partir de
                                 # CETTE tentative, pas depuis toute la vie du cerveau

    try:
        for _ in range(jours_totaux):
            demarrer_journee(etat)
            jours_ecoules_session += 1
            jour = etat.jour  # incrémenté par demarrer_journee — reprend depuis l'état chargé
            ere = ere_courante(jour)
            if jour == 1 or ere_courante(jour - 1) != ere:
                print(f"\n🌅 [NOUVELLE ÈRE] Jour {jour} — entrée dans l'ère « {ere} ».")

            for tick in range(ticks_par_jour):
                moment = "matin" if tick < TICKS_MATIN else "apres_midi"
                mode_perception, obs_auditive, formants_cibles = _perception_du_tick(
                    etat, cache, ere, moment, derniere_action
                )
                infos = traiter_tick(
                    etat, obs_auditive=obs_auditive, formants_cibles=formants_cibles,
                    mode_perception=mode_perception,
                )
                if infos["action"] is not None:
                    derniere_action = infos["action"]

            log = executer_nuit(etat)
            _promouvoir_palier_vocal_si_merite(etat)
            log["Ere"] = ere
            log["Palier_Vocal"] = etat.palier_vocal
            if activer_wandb:
                wandb.log(log)

            persistance.sauvegarder(etat)

            # Garde-fou École de Rattrapage Vocal (v24.0-fix2, compteur corrigé en
            # fix3) — voir constante JOURS_MAX_SANS_PREMIERE_LETTRE en tête de fichier.
            # jours_ecoules_session, pas etat.jour : un vieux cerveau qui a déjà vécu
            # des centaines de jours avant un changement de seuil mérite une vraie
            # nouvelle fenêtre de jugement, pas un verdict basé sur son passé.
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
    parser = argparse.ArgumentParser(description="Cursus Développemental par Ères — Naulthène AGI (v23.0)")
    parser.add_argument("--jours", type=int, default=DUREE_ERE, help="Nombre de jours subjectifs du cursus")
    parser.add_argument("--no-wandb", action="store_true", help="Désactive le logging Weights & Biases")
    # v30.0 — `--brain` expose en CLI le paramètre `fichier_brain` que `lancer_cursus`
    # acceptait déjà : indispensable pour la convention de nommage des cerveaux
    # (voir CLAUDE.md, « Convention de nommage des cerveaux »), qui demande un fichier
    # horodaté par run plutôt qu'un chemin unique réutilisé. Sans ce flag, il fallait
    # renommer/archiver le fichier à la main entre deux runs.
    parser.add_argument("--brain", type=str, default=FICHIER_BRAIN_CURSUS,
                        help=f"Fichier .brain à charger/sauvegarder (défaut : {FICHIER_BRAIN_CURSUS})")
    args = parser.parse_args()

    lancer_cursus(jours_totaux=args.jours, activer_wandb=not args.no_wandb,
                  fichier_brain=args.brain)
