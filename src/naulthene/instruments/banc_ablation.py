# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Adrien Nault — Naulthène AGI
"""LE BANC D'ABLATION — la lobotomie contrôlée (v33.1, expérimental)

Instrument de DIAGNOSTIC, pas d'entraînement. Prend un `.brain` entraîné, en fait une
copie par lésion, et mesure ce que chaque lésion coûte réellement.

    Une ablation qui ne dégrade rien signale un composant mort.

C'est la seule mesure qui répond en binaire, par composant, là où les courbes d'un run
long ne donnent que des impressions. Motivation directe : le run `az794yzw` (jours
5001→10000, 2026-08-05) a montré un agent CONVERGÉ — 0 victoire en 5000 jours, portes
0.77→0.81, JEPA plat à 0.0006, 0 neurogenèse, 0 sursaut. Le temps seul ne débloque plus
rien ; il faut savoir quelles pièces portent encore quelque chose.

---
PRINCIPES DE CONSTRUCTION (non négociables)

1. **Le cerveau de référence n'est JAMAIS touché.** Chaque cellule du banc travaille sur
   sa propre copie, dans un dossier dédié. Aucune ablation ne peut contaminer une autre,
   ni le `.brain` d'origine. La copie est vérifiée par MD5 avant usage.

2. **AUCUN apprentissage.** `torch.no_grad()` partout, jamais d'`apprendre_journee`,
   jamais d'`executer_nuit`, jamais de `sauvegarder`. On mesure un cerveau figé — s'il
   apprenait pendant le test, on mesurerait l'apprentissage, pas la lésion.

3. **Graine fixée, identique pour toutes les cellules.** Deux cellules qui ne diffèrent
   que par leur lésion doivent voir EXACTEMENT les mêmes cartes, dans le même ordre.
   Sans ça, l'écart mesuré mélange l'effet de la lésion et celui du tirage.

3bis. **La politique reste STOCHASTIQUE** (`multinomial`, comme `traiter_tick`), jamais
   gloutonne. Une première version du banc utilisait `argmax` pour « supprimer le
   hasard » : mesuré, l'agent joue alors l'action 0 en boucle infinie et échoue même sur
   Empty-8x8. Un agent REINFORCE apprend une politique stochastique — son mode
   déterministe est un régime qu'il n'a jamais connu. La reproductibilité vient de la
   graine, pas de la suppression du hasard.

4. **Les lésions sont des masques de PERCEPTION ou de DÉCISION, jamais des amputations
   de poids.** On neutralise un signal en entrée (mettre l'odorat à son neutre), on ne
   supprime pas une couche : supprimer changerait les dimensions et déclencherait des
   greffes, ce qui mesurerait la greffe plutôt que la lésion.

5. **Le neutre de chaque canal est celui du code**, pas zéro par défaut. La clinotaxie
   vaut 0.5 au neutre (invariant v32.0) — la mettre à 0.0 signifierait « éloignement
   maximal », soit une lésion DIFFÉRENTE de l'absence de signal, et le résultat serait
   ininterprétable.

---
LANCEMENT

    PYTHONPATH=src python -m naulthene.instruments.banc_ablation \\
        --brain brains/ablations/REFERENCE_5000j.brain --jours 30

    # Toutes les lésions × tous les niveaux, run complet (long)
    PYTHONPATH=src python -m naulthene.instruments.banc_ablation \\
        --brain brains/ablations/REFERENCE_5000j.brain --jours 50 --tous-niveaux

    # Une lésion précise, pour creuser
    PYTHONPATH=src python -m naulthene.instruments.banc_ablation \\
        --brain brains/ablations/REFERENCE_5000j.brain --lesions temoin,c2_coupe

Voir `docs/fonctionnement/LANCEMENT.md` pour le guide complet et `docs/ameliorations/les_sens_combinatoire.md` §7
pour les décisions que ce banc doit éclairer.
"""

import argparse
import copy
import json
import os
import random
import shutil
import time
from collections import defaultdict

import numpy as np
import torch

import naulthene.cerveau.noyau as nx
from naulthene.cerveau import bus_sensoriel as bs
from naulthene.cerveau.persistance import PersistanceAnatomique


# --- 1. LE CATALOGUE DES LÉSIONS ---
#
# Chaque lésion est (identifiant, libellé, famille). La famille sert au regroupement
# du rapport : une lésion sensorielle et une lésion cognitive ne se comparent pas.
#
# ⚠️ `temoin` DOIT rester en tête : c'est la référence à laquelle tout le reste est
# comparé. Sans témoin exécuté dans les mêmes conditions (même graine, même code
# d'instrumentation), les écarts mesurés n'ont aucun sens.

LESIONS = [
    ("temoin",          "Témoin (aucune lésion)",              "reference"),
    # --- Sens (masques de perception) ---
    ("vue_coupee",      "Vue neutralisée (obs à zéro)",        "sens"),
    ("ouie_coupee",     "Ouïe neutralisée",                    "sens"),
    ("toucher_coupe",   "Toucher neutralisé (4 dims)",         "sens"),
    ("odorat_coupe",    "Odorat neutralisé (+ clinotaxie)",    "sens"),
    ("gout_coupe",      "Goût neutralisé (2 dims)",            "sens"),
    ("exo_coupe",       "Exo-Sens neutralisé (8 dims)",        "sens"),
    ("bio_coupe",       "TOUT le vecteur bio neutralisé",      "sens"),
    # --- Cognition (masques de décision) ---
    ("c2_coupe",        "C2 coupé (force_planification=0)",    "cognition"),
    ("c2_horizon_court","C2 myope (horizon 1 seul)",           "cognition"),
    ("episodique_coupe","Mémoire épisodique de contexte à 0",  "cognition"),
    ("spatiale_coupee", "Mémoire spatiale vidée par épisode",  "cognition"),
    ("hippocampe_fige", "Mémoire de travail figée à 0",        "cognition"),
]

FAMILLES = ("reference", "sens", "cognition")


class Lesion:
    """Un masque appliqué au vol pendant le tick. Ne modifie JAMAIS les poids.

    Le masque agit à trois endroits possibles, tous en amont de la décision :
      - `masquer_obs` : la vision, avant `porte_visuelle` ;
      - `masquer_bio` : le vecteur bio, avant `integrateur_bio` ;
      - `force_planification` / `horizons` : l'arbitrage C1/C2 dans `penser`.

    Une lésion inconnue lève immédiatement : mieux vaut un crash au démarrage qu'un
    run de plusieurs heures qui mesure un témoin en croyant mesurer une lésion.
    """

    def __init__(self, identifiant):
        connus = {ident for ident, _, _ in LESIONS}
        if identifiant not in connus:
            raise ValueError(f"Lésion inconnue : {identifiant!r}. Connues : {sorted(connus)}")
        self.id = identifiant
        self.libelle = next(lib for i, lib, _ in LESIONS if i == identifiant)
        self.famille = next(f for i, _, f in LESIONS if i == identifiant)

    # --- Les bornes des sens faibles dans le vecteur bio ---
    #
    # Le vecteur bio se termine par la queue posée par `BusSensoriel.interpreter`, dans
    # cet ordre EXACT (contrat append-only, voir bus_sensoriel.interpreter) :
    #   [toucher ×4][chimie ×4][exo ×8][clinotaxie ×2]
    # Les indices sont donc comptés DEPUIS LA FIN — jamais depuis le début, car la tête
    # du vecteur bio (jauges, quête, rappel spatial) a une longueur qui a varié selon
    # les versions.
    @staticmethod
    def _bornes_queue(n):
        """Retourne les tranches (début, fin) de chaque sens, en index ABSOLUS.

        --- v39-fix (R1) : ANCRAGE PAR LE DÉBUT, JAMAIS PAR LA FIN ---

        🔴 CE QUE ÇA CORRIGE. L'ancienne version calculait `d = n - q`, c'est-à-dire
        qu'elle partait de la FIN du vecteur en supposant la clinotaxie dernière. C'était
        vrai en v32.0 ; ça ne l'est plus depuis que le contrat append-only a fait son
        travail :

            v36.0  +2 dims (rappel marquant)   -> décalage +2
            v39.2  +1 dim  (présence auditive) -> décalage +3

        Conséquence mesurée sur le layout réel (v39.2) :

            tranche      index RÉELS   index CALCULÉS (ancienne version)
            toucher      16:20         19:23      (+3)
            odorat       20:22         23:25      (+3)
            goût         22:24         25:27      (+3)
            exo          24:32         27:35      (+3)
            clinotaxie   32:34         35:37      (+3)

        Donc `toucher_coupe` neutralisait en réalité 2 dims de toucher ET 2 d'odorat, en
        laissant 2 dims de toucher intactes — et `clinotaxie` écrasait le rappel marquant
        (dont le neutre est [0.5, 0.0], pas 0.5). **Le tableau d'ablation publié dans les
        deux README a été produit avec ce découpage faux et doit être refait.**

        Les 16 premières dims du vecteur bio sont STABLES depuis la v22.1 (3 jauges +
        3 quête + 2 rappel spatial + 8 quête vocale) : c'est le seul ancrage fiable, parce
        que le contrat du projet garantit que tout ajout se fait EN QUEUE.
        """
        t0 = 16                                       # fin du bloc stable v22.1
        c0 = t0 + bs.DIM_TOUCHER
        e0 = c0 + bs.DIM_CHIMIE
        k0 = e0 + bs.DIM_EXO
        r0 = k0 + bs.DIM_ODORAT_DELTA                 # rappel marquant (v36.0)

        # Garde-fou : le contrat est append-only, donc toute dimension ajoutée en queue
        # DOIT faire crier cette assertion plutôt que décaler silencieusement les lésions.
        # C'est la leçon des trois défauts R1/R4/R5 — un invariant qu'on peut tester
        # mécaniquement et qu'on laisse en commentaire finit par être violé sans bruit.
        attendu = r0 + nx.DIM_RAPPEL_MARQUANT + getattr(nx, "DIM_PRESENCE_AUDITIVE", 0)
        assert attendu == n, (
            f"Layout du vecteur bio inattendu : {n} dims reçues, {attendu} calculées. "
            "Une dimension a été ajoutée sans mettre à jour _bornes_queue — les lésions "
            "porteraient sur les mauvaises tranches (défaut R1, v39)."
        )

        return {
            "queue":      (t0, k0 + bs.DIM_ODORAT_DELTA),
            "toucher":    (t0, c0),
            "chimie":     (c0, e0),
            "odorat":     (c0, c0 + 2),               # odeur_food, odeur_water
            "gout":       (c0 + 2, e0),               # gout_food, gout_water
            "exo":        (e0, k0),
            "clinotaxie": (k0, r0),
        }

    def masquer_obs(self, obs):
        if self.id == "vue_coupee":
            return torch.zeros_like(obs)
        return obs

    def masquer_audio(self, obs_auditive):
        if self.id == "ouie_coupee":
            return None                                # None = silence, chemin natif
        return obs_auditive

    def masquer_bio(self, vecteur_bio):
        """Neutralise une tranche du vecteur bio. Le neutre est celui du code :
        0.0 pour toucher/chimie/exo, 0.5 pour la clinotaxie (invariant v32.0)."""
        if self.id not in ("toucher_coupe", "odorat_coupe", "gout_coupe",
                           "exo_coupe", "bio_coupe"):
            return vecteur_bio

        v = vecteur_bio.clone()
        n = v.shape[-1]
        b = self._bornes_queue(n)

        if self.id == "bio_coupe":
            v[..., :] = 0.0
            d, f = b["clinotaxie"]
            v[..., d:f] = 0.5                          # neutre v32.0, jamais 0.0
            # v39-fix (R1) : le rappel marquant a pour neutre [0.5, 0.0] — sa valence
            # remise à 0.0 signifierait « le pire souvenir possible » et rendrait l'agent
            # craintif partout, ce qui n'est pas une ABLATION mais une lésion active.
            # L'ancien découpage écrasait cette tranche sans le savoir (décalage +3).
            r0 = b["clinotaxie"][1]
            v[..., r0] = 0.5                           # valence neutre
            v[..., r0 + 1] = 0.0                       # confiance nulle
        elif self.id == "toucher_coupe":
            d, f = b["toucher"]; v[..., d:f] = 0.0
        elif self.id == "gout_coupe":
            d, f = b["gout"]; v[..., d:f] = 0.0
        elif self.id == "exo_coupe":
            d, f = b["exo"]; v[..., d:f] = 0.0
        elif self.id == "odorat_coupe":
            # L'odorat, c'est l'intensité ET sa dérivée : couper l'une sans l'autre
            # laisserait un gradient encore exploitable, donc une lésion incomplète.
            d, f = b["odorat"]; v[..., d:f] = 0.0
            d, f = b["clinotaxie"]; v[..., d:f] = 0.5
        return v

    def force_planification(self, valeur_nominale):
        if self.id == "c2_coupe":
            return 0.0                                 # C2 tourne mais n'influence plus
        return valeur_nominale

    def horizons(self, nominal):
        if self.id == "c2_horizon_court":
            return (1,)                                # myopie : plus de vision longue
        return nominal

    def masquer_contexte(self, contexte):
        if self.id == "episodique_coupe":
            return torch.zeros_like(contexte)
        return contexte

    def masquer_memoire(self, memoire):
        if self.id == "hippocampe_fige":
            return torch.zeros_like(memoire)
        return memoire

    @property
    def vide_spatiale_par_episode(self):
        return self.id == "spatiale_coupee"


# --- 2. LA SALLE DE TEST — un épisode, sans aucun apprentissage ---

def jouer_episode(etat, lesion, patience, rng_env, generateur):
    """Joue UN épisode complet et retourne ses mesures. Aucun gradient, aucun buffer,
    aucune dopamine : `torch.no_grad()` couvre tout, et rien n'est écrit dans `etat`
    hors des structures d'épisode qui sont réinitialisées juste après.

    Retourne un dict de mesures brutes — l'agrégation est faite par l'appelant.
    """
    env = etat.env
    graine = int(rng_env.integers(0, 2**31 - 1))
    obs_brute, _ = env.reset(seed=graine)

    agent = etat.agent
    memoire = torch.zeros(1, agent.dim_bus, device=nx.DEVICE)
    contexte = torch.zeros(1, agent.dim_bus, device=nx.DEVICE)
    latents = []

    etat.bus_sensoriel.reinitialiser_episode()
    if lesion.vide_spatiale_par_episode:
        etat.memoire_episodique_spatiale.souvenirs.clear()

    portes = set()
    dist_min = None
    records = 0
    reussi = False
    ticks = 0
    recompense = 0.0
    but = _position_but(env.unwrapped)

    # --- Mesures de DIAGNOSTIC (v33.1) : elles ne disent pas seulement « ça marche ou
    # non », mais POURQUOI — ce qui distingue un composant à jeter d'un composant à
    # rectifier. Aucune n'influence la décision : lecture pure.
    compte_actions = [0] * 7          # quelles actions l'agent utilise réellement
    cases_visitees = set()            # couverture spatiale = exploration réelle
    positions = []                    # trace, pour détecter les boucles
    somme_entropie = 0.0              # 0 = politique figée, ln(7)=1.946 = hasard pur
    accord_c1_c2 = 0                  # C1 et C2 veulent-ils la même chose ?
    somme_ecart_c2 = 0.0              # amplitude de l'influence de C2 sur l'arbitrage
    ticks_sur_place = 0               # agent qui ne bouge pas d'une case

    for t in range(patience):
        ticks = t + 1
        obs = lesion.masquer_obs(nx.encoder(obs_brute))

        # Les 18 dims des sens faibles, telles que le tick réel les construit.
        signaux = etat.bus_sensoriel.interpreter(env, None, None)

        # Rappel spatial : même condition que `traiter_tick` — il n'a de sens que si une
        # quête de survie est active, sinon `type_recherche` n'existe pas.
        rappel = None
        if etat.moteur_bio.quete_active is not None:
            rappel = etat.memoire_episodique_spatiale.recuperer_contexte(
                tuple(int(v) for v in env.unwrapped.agent_pos),
                etat.moteur_bio.quete_active["type"].replace("SURVIVAL_", ""),
                etat.tick_absolu,
            )

        bio_liste = etat.moteur_bio.obtenir_vecteur_bio(
            rappel_spatial=rappel, cible_vocale=None, signaux_sensoriels=signaux
        )
        vecteur_bio = torch.tensor(bio_liste, dtype=torch.float32,
                                    device=nx.DEVICE).unsqueeze(0)
        vecteur_bio = lesion.masquer_bio(vecteur_bio)

        # --- Sonde C1 vs C2 (diagnostic, hors chemin de décision) ---
        #
        # `penser` ne retourne que l'arbitrage final. Pour savoir QUI décide, on rejoue
        # C1 seul puis C2 seul. C'est un surcoût réel (≈ +40 % de temps de tick) mais
        # c'est la seule façon de distinguer « C2 est inutile » de « C2 écrase C1 ».
        # Aucun de ces tenseurs n'est réinjecté dans la boucle : lecture pure.
        c1_sortie = agent._executer_c1_reflexe(
            obs, lesion.masquer_memoire(memoire), lesion.masquer_contexte(contexte),
            vecteur_bio, obs_auditive=lesion.masquer_audio(None)
        )
        logits_c1 = c1_sortie[4]
        valeurs_c2, _ = agent._solliciter_c2_neocortex(
            c1_sortie[3], c1_sortie[1],
            horizons_planification=lesion.horizons(nx.HORIZONS_PLANIFICATION),
        )
        force = lesion.force_planification(etat.force_planification_jour)
        if int(torch.argmax(logits_c1[0, :7])) == \
           int(torch.argmax((logits_c1 + valeurs_c2 * force)[0, :7])):
            accord_c1_c2 += 1
        somme_ecart_c2 += float((valeurs_c2[0, :7] * force).abs().mean())

        (logits, _valeur, _vocaux, pensee_enrichie,
         memoire, _bus, _routage, _indecision) = agent.penser(
            obs, lesion.masquer_memoire(memoire), lesion.masquer_contexte(contexte),
            vecteur_bio,
            force_planification=force,
            horizons_planification=lesion.horizons(nx.HORIZONS_PLANIFICATION),
            obs_auditive=lesion.masquer_audio(None),
            plugs_c3_disponibles=None,
        )
        latents.append(pensee_enrichie.detach())

        # ÉCHANTILLONNAGE, exactement comme `traiter_tick` (`dist.sample()`), jamais
        # d'argmax.
        #
        # ⚠️ Le banc a d'abord été écrit en politique gloutonne, au motif de « mesurer ce
        # que le cerveau sait, pas ce que le hasard lui fait tenter ». C'était une erreur,
        # mesurée : en argmax, l'agent joue l'action 0 (tourner à gauche) en BOUCLE
        # INFINIE et n'atteint jamais le But, même sur Empty-8x8 qu'il a franchi au jour
        # 66. Un agent entraîné par REINFORCE apprend une politique STOCHASTIQUE ; son
        # mode déterministe n'est pas « sa meilleure version », c'est un régime qu'il n'a
        # jamais connu. Mesurer l'argmax, c'est mesurer un agent qui n'existe pas.
        #
        # La reproductibilité est assurée par `generateur` (une graine par cellule),
        # pas en supprimant le hasard.
        probabilites = torch.softmax(logits[0, :7], dim=-1).cpu()
        action = int(torch.multinomial(probabilites, 1, generator=generateur).item())

        # Entropie de la politique EFFECTIVE (celle qui a produit l'action), en nats.
        # 0 = l'agent joue toujours la même chose ; ln(7) ≈ 1.946 = tirage uniforme.
        p = probabilites.clamp_min(1e-12)
        somme_entropie += float(-(p * p.log()).sum())
        compte_actions[action] += 1

        pos_avant = tuple(int(v) for v in env.unwrapped.agent_pos)
        obs_brute, recompense, termine, tronque, _ = env.step(action)

        noyau_env = env.unwrapped
        pos = tuple(int(v) for v in noyau_env.agent_pos)
        cases_visitees.add(pos)
        positions.append(pos)
        if pos == pos_avant:
            ticks_sur_place += 1
        objet = noyau_env.grid.get(*pos)
        if objet is not None and getattr(objet, "type", None) == "door" \
           and getattr(objet, "is_open", False):
            portes.add(pos)
        if but is not None:
            d = abs(pos[0] - but[0]) + abs(pos[1] - but[1])
            if dist_min is None or d < dist_min:
                dist_min = d
                records += 1

        contexte = torch.stack(latents[-20:]).mean(dim=0).detach()

        if termine or tronque:
            reussi = bool(recompense > 0)
            break

    n = max(1, ticks)
    return {
        "reussi": reussi, "ticks": ticks, "portes": len(portes),
        "records": records, "dist_min": dist_min if dist_min is not None else -1,
        "recompense": float(recompense),
        # --- Diagnostic ---
        "entropie": somme_entropie / n,
        "cases": len(cases_visitees),
        # Taux de couverture : cases distinctes / ticks. Proche de 1 = l'agent avance
        # toujours vers du neuf ; proche de 0 = il repasse sans cesse au même endroit.
        "couverture": len(cases_visitees) / n,
        "sur_place": ticks_sur_place / n,
        "accord_c1_c2": accord_c1_c2 / n,
        "ecart_c2": somme_ecart_c2 / n,
        # Diversité d'actions : combien des 7 actions ont été jouées au moins une fois.
        "actions_utilisees": sum(1 for c in compte_actions if c > 0),
        "repartition_actions": compte_actions,
    }


def _position_but(noyau_env):
    """Position du But sur la grille, ou None s'il n'y en a pas (certains niveaux)."""
    g = noyau_env.grid
    for x in range(g.width):
        for y in range(g.height):
            o = g.get(x, y)
            if o is not None and o.type == "goal":
                return (x, y)
    return None


# --- 3. LE BANC — une cellule = une lésion × un niveau ---

def executer_cellule(chemin_brain, lesion_id, niveau_idx, jours, episodes_par_jour,
                     graine, dossier_travail):
    """Une cellule complète du banc, sur sa PROPRE copie du cerveau.

    La copie est refaite pour chaque cellule et supprimée après : deux cellules ne
    partagent jamais un fichier, donc aucune ne peut contaminer l'autre.
    """
    lesion = Lesion(lesion_id)
    env_id, nom_niveau = nx.PROGRAMME[niveau_idx]

    copie = os.path.join(dossier_travail, f"{lesion_id}__niv{niveau_idx}.brain")
    shutil.copy2(chemin_brain, copie)

    # Graine identique pour toutes les cellules d'un même niveau : c'est ce qui rend
    # les lésions comparables entre elles (principe 3).
    torch.manual_seed(graine)
    np.random.seed(graine)
    random.seed(graine)
    rng_env = np.random.default_rng(graine)
    # Générateur DÉDIÉ au choix d'action, sur CPU (torch.multinomial n'accepte pas de
    # generator MPS). Séparé de `rng_env` pour que la suite des cartes et la suite des
    # tirages d'action soient indépendantes : deux lésions voient ainsi les mêmes cartes
    # même si elles consomment le hasard d'action à des rythmes différents.
    generateur = torch.Generator(device="cpu").manual_seed(graine)

    persistance = PersistanceAnatomique(copie)
    etat = persistance.charger_ou_naitre()
    etat.agent.eval()

    if etat.env_id != env_id:
        etat.env.close()
        etat.env = nx.creer_env(env_id, nx.DIM_VISUELLE)
        etat.env_id, etat.nom_classe = env_id, nom_niveau

    patience = getattr(etat, "patience_max", None) or nx.PATIENCE_MAX
    mesures = []
    t0 = time.time()

    with torch.no_grad():
        for _ in range(jours):
            for _ in range(episodes_par_jour):
                mesures.append(jouer_episode(etat, lesion, patience, rng_env, generateur))

    etat.env.close()
    try:
        os.remove(copie)
    except OSError:
        pass

    n = len(mesures)
    victoires = sum(1 for m in mesures if m["reussi"])
    dmins = [m["dist_min"] for m in mesures if m["dist_min"] >= 0]
    moy = lambda cle: sum(m[cle] for m in mesures) / n if n else 0.0

    # Intervalle de confiance à 95 % sur le taux de victoire (Wald). Publié pour que
    # « +3 pp » ne soit jamais lu comme significatif quand il ne l'est pas : avec 180
    # épisodes, la marge est d'environ ±7 pp autour de 50 %.
    taux = victoires / n if n else 0.0
    marge = 1.96 * ((taux * (1 - taux) / n) ** 0.5) if n else 0.0

    repartition = [0] * 7
    for m in mesures:
        for i, c in enumerate(m["repartition_actions"]):
            repartition[i] += c
    total_actions = max(1, sum(repartition))

    return {
        "lesion": lesion_id, "libelle": lesion.libelle, "famille": lesion.famille,
        "niveau_idx": niveau_idx, "niveau": nom_niveau, "env_id": env_id,
        "episodes": n,
        "taux_victoire": taux, "victoires": victoires, "marge_95": marge,
        "ticks_moy": moy("ticks"),
        "portes_moy": moy("portes"),
        "records_moy": moy("records"),
        "dist_min_moy": sum(dmins) / len(dmins) if dmins else -1,
        # --- Diagnostic ---
        "entropie_moy": moy("entropie"),
        "cases_moy": moy("cases"),
        "couverture_moy": moy("couverture"),
        "sur_place_moy": moy("sur_place"),
        "accord_c1_c2_moy": moy("accord_c1_c2"),
        "ecart_c2_moy": moy("ecart_c2"),
        "actions_utilisees_moy": moy("actions_utilisees"),
        "repartition_actions": [c / total_actions for c in repartition],
        "duree_s": time.time() - t0,
    }


# --- 4. RAPPORT & W&B ---

def publier_wandb(resultats, nom_run, graine, jours, episodes_par_jour):
    """Publie le banc dans W&B : une table complète + des barres par lésion.

    Import local : le banc doit rester utilisable sans W&B installé/connecté
    (`--sans-wandb`), c'est un instrument de diagnostic, pas un run d'entraînement.
    """
    import wandb

    wandb.init(project="Naulthene-AGI", name=nom_run, job_type="ablation",
               config={"graine": graine, "jours": jours,
                       "episodes_par_jour": episodes_par_jour,
                       "lesions": [l[0] for l in LESIONS]})

    colonnes = ["lesion", "libelle", "famille", "niveau", "episodes", "taux_victoire",
                "marge_95", "delta_pp", "significatif", "verdict",
                "ticks_moy", "portes_moy", "records_moy", "dist_min_moy",
                "entropie", "couverture", "sur_place", "accord_c1_c2", "ecart_c2",
                "actions_utilisees"]
    table = wandb.Table(columns=colonnes)

    temoins = {r["niveau_idx"]: r for r in resultats if r["lesion"] == "temoin"}
    for r in resultats:
        t = temoins.get(r["niveau_idx"])
        delta = (r["taux_victoire"] - t["taux_victoire"]) * 100 if t else 0.0
        seuil = max(((r["marge_95"] + t["marge_95"]) * 100) if t else 3.0, 2.0)
        significatif = abs(delta) >= seuil
        if r["lesion"] == "temoin":
            verdict = "temoin"
        elif delta <= -seuil * 2:
            verdict = "VITAL"
        elif delta <= -seuil:
            verdict = "contribue"
        elif delta >= seuil:
            verdict = "NUISIBLE"
        else:
            verdict = "inerte"

        table.add_data(r["lesion"], r["libelle"], r["famille"], r["niveau"],
                       r["episodes"], r["taux_victoire"], r["marge_95"], delta,
                       significatif, verdict,
                       r["ticks_moy"], r["portes_moy"], r["records_moy"],
                       r["dist_min_moy"], r["entropie_moy"], r["couverture_moy"],
                       r["sur_place_moy"], r["accord_c1_c2_moy"], r["ecart_c2_moy"],
                       r["actions_utilisees_moy"])

        prefixe = f"Ablation/{r['niveau']}/{r['lesion']}"
        wandb.log({f"{prefixe}/taux_victoire": r["taux_victoire"],
                   f"{prefixe}/delta_pp": delta,
                   f"{prefixe}/portes_moy": r["portes_moy"],
                   f"{prefixe}/records_moy": r["records_moy"],
                   f"{prefixe}/dist_min_moy": r["dist_min_moy"],
                   f"{prefixe}/entropie": r["entropie_moy"],
                   f"{prefixe}/couverture": r["couverture_moy"],
                   f"{prefixe}/sur_place": r["sur_place_moy"],
                   f"{prefixe}/accord_c1_c2": r["accord_c1_c2_moy"],
                   f"{prefixe}/ecart_c2": r["ecart_c2_moy"]})

    wandb.log({"Ablation/table": table})
    wandb.finish()


def afficher_rapport(resultats):
    """Rapport console, groupé par niveau, trié par dégradation décroissante."""
    print("\n" + "=" * 100)
    print("  RAPPORT D'ABLATION — écart au témoin, par niveau")
    print("=" * 100)

    par_niveau = defaultdict(list)
    for r in resultats:
        par_niveau[r["niveau_idx"]].append(r)

    for niveau_idx in sorted(par_niveau):
        cellules = par_niveau[niveau_idx]
        temoin = next((c for c in cellules if c["lesion"] == "temoin"), None)
        nom = cellules[0]["niveau"]
        print(f"\n▶ {nom}  ({cellules[0]['env_id']})")
        if temoin:
            print(f"   témoin : {temoin['taux_victoire']:.1%} de victoires "
                  f"sur {temoin['episodes']} épisodes, "
                  f"{temoin['portes_moy']:.2f} portes/ép, "
                  f"dist_min moy {temoin['dist_min_moy']:.1f}")
        print(f"   {'lésion':<20} {'victoire':>9} {'Δ pp':>8} {'portes':>8} "
              f"{'records':>8} {'dist_min':>9}  verdict")
        print("   " + "-" * 92)

        lesions = [c for c in cellules if c["lesion"] != "temoin"]
        lesions.sort(key=lambda c: c["taux_victoire"] - (temoin["taux_victoire"] if temoin else 0))
        for c in lesions:
            delta = (c["taux_victoire"] - temoin["taux_victoire"]) * 100 if temoin else 0.0
            # Seuil de significativité : la somme des deux marges d'erreur. Un écart
            # inférieur n'est PAS distinguable du bruit d'échantillonnage, même s'il
            # dépasse 3 points — c'est ce qui évite de conclure sur du vent.
            seuil = ((c["marge_95"] + temoin["marge_95"]) * 100) if temoin else 3.0
            seuil = max(seuil, 2.0)
            if delta <= -seuil * 2:
                verdict = "🔴 VITAL"
            elif delta <= -seuil:
                verdict = "🟠 contribue"
            elif delta >= seuil:
                verdict = "🔵 NUISIBLE (!)"
            else:
                verdict = "⚪ inerte"
            print(f"   {c['lesion']:<20} {c['taux_victoire']:>8.1%} {delta:>+8.1f} "
                  f"{c['portes_moy']:>8.2f} {c['records_moy']:>8.2f} "
                  f"{c['dist_min_moy']:>9.1f}  {verdict}")

        # --- Le tableau de diagnostic : POURQUOI, pas seulement combien ---
        print(f"\n   {'—— diagnostic ——':<20} {'entropie':>9} {'couvert.':>9} "
              f"{'surplace':>9} {'accordC1C2':>11} {'|C2|':>8} {'act/7':>6}")
        print("   " + "-" * 92)
        for c in [temoin] + lesions if temoin else lesions:
            if c is None:
                continue
            print(f"   {c['lesion']:<20} {c['entropie_moy']:>9.3f} "
                  f"{c['couverture_moy']:>9.3f} {c['sur_place_moy']:>9.3f} "
                  f"{c['accord_c1_c2_moy']:>11.3f} {c['ecart_c2_moy']:>8.3f} "
                  f"{c['actions_utilisees_moy']:>6.1f}")

    print("\n" + "=" * 100)
    print("  VERDICTS — le seuil est l'intervalle de confiance à 95 %, pas un chiffre fixe.")
    print("   🔴 VITAL      : le couper casse l'agent → à conserver tel quel")
    print("   🟠 contribue  : apport réel mais modeste")
    print("   ⚪ inerte     : ne change rien → ne porte AUCUN signal utile ICI")
    print("   🔵 NUISIBLE   : l'agent fait MIEUX sans → à RECTIFIER, pas à jeter")
    print()
    print("  LIRE LE DIAGNOSTIC (colonnes ci-dessus) :")
    print("   entropie   : 0 = politique figée | ln(7)=1.946 = hasard pur")
    print("   couverture : cases distinctes / tick — proche de 0 = tourne en rond")
    print("   surplace   : fraction de ticks sans changer de case (rotations, murs)")
    print("   accordC1C2 : fraction de ticks où C1 et C2 veulent la MÊME action")
    print("                → proche de 0 = C2 contredit systématiquement le réflexe")
    print("   |C2|       : amplitude moyenne de l'influence de C2 sur l'arbitrage")
    print("   act/7      : combien des 7 actions sont réellement utilisées")
    print()
    print("  ⚠️ « inerte » ≠ « cassé ». Un composant peut être inerte faute de STIMULUS :")
    print("     l'odorat est mesuré à 0,0 % des ticks au Doctorat (cartes sans nourriture).")
    print("     Toujours croiser avec la ligne « Les 5 Sens » des logs avant de conclure.")
    print("=" * 100)


# --- 5. POINT D'ENTRÉE ---

def main():
    p = argparse.ArgumentParser(description="Banc d'ablation — lobotomie contrôlée")
    p.add_argument("--brain", required=True, help="cerveau de référence (jamais modifié)")
    p.add_argument("--jours", type=int, default=30, help="jours simulés par cellule")
    p.add_argument("--episodes", type=int, default=2, help="épisodes par jour")
    p.add_argument("--graine", type=int, default=1789)
    p.add_argument("--lesions", default=None,
                   help="liste séparée par des virgules (défaut : toutes)")
    p.add_argument("--niveaux", default=None,
                   help="indices séparés par des virgules (défaut : le dernier)")
    p.add_argument("--tous-niveaux", action="store_true")
    p.add_argument("--sans-wandb", action="store_true")
    p.add_argument("--sortie", default="brains/ablations/resultats.json")
    args = p.parse_args()

    if not os.path.exists(args.brain):
        raise SystemExit(f"❌ Cerveau introuvable : {args.brain}")

    lesions = ([s.strip() for s in args.lesions.split(",")] if args.lesions
               else [l[0] for l in LESIONS])
    if "temoin" not in lesions:
        lesions.insert(0, "temoin")          # sans témoin, aucun écart n'est calculable

    if args.tous_niveaux:
        niveaux = list(range(len(nx.PROGRAMME)))
    elif args.niveaux:
        niveaux = [int(s) for s in args.niveaux.split(",")]
    else:
        niveaux = [len(nx.PROGRAMME) - 1]

    dossier = os.path.join(os.path.dirname(args.brain) or ".", "_travail")
    os.makedirs(dossier, exist_ok=True)

    total = len(lesions) * len(niveaux)
    print(f"\n🔬 BANC D'ABLATION")
    print(f"   cerveau  : {args.brain}")
    print(f"   cellules : {total} ({len(lesions)} lésions × {len(niveaux)} niveaux)")
    print(f"   volume   : {args.jours} jours × {args.episodes} ép. = "
          f"{args.jours * args.episodes} épisodes/cellule")
    print(f"   graine   : {args.graine} (identique pour toutes les cellules)\n")

    resultats = []
    fait = 0
    for niveau_idx in niveaux:
        for lesion_id in lesions:
            fait += 1
            nom = nx.PROGRAMME[niveau_idx][1]
            print(f"   [{fait:>3}/{total}] {nom:<38} {lesion_id:<18} ", end="", flush=True)
            try:
                r = executer_cellule(args.brain, lesion_id, niveau_idx, args.jours,
                                     args.episodes, args.graine, dossier)
                resultats.append(r)
                print(f"✓ {r['taux_victoire']:>6.1%}  ({r['duree_s']:.0f}s)")
            except Exception as e:
                print(f"❌ {type(e).__name__}: {e}")

    if not resultats:
        raise SystemExit("❌ Aucune cellule n'a abouti.")

    os.makedirs(os.path.dirname(args.sortie) or ".", exist_ok=True)
    with open(args.sortie, "w") as f:
        json.dump({"brain": args.brain, "graine": args.graine, "jours": args.jours,
                   "episodes_par_jour": args.episodes, "resultats": resultats}, f, indent=2)
    print(f"\n💾 Résultats bruts : {args.sortie}")

    afficher_rapport(resultats)

    if not args.sans_wandb:
        try:
            nom_run = f"Ablation_{os.path.basename(args.brain).replace('.brain','')}"
            publier_wandb(resultats, nom_run, args.graine, args.jours, args.episodes)
            print("📊 Publié sur W&B.")
        except Exception as e:
            print(f"⚠️  W&B indisponible ({type(e).__name__}: {e}) — résultats JSON intacts.")

    try:
        shutil.rmtree(dossier)
    except OSError:
        pass


if __name__ == "__main__":
    main()
