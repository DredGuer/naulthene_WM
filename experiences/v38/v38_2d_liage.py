"""v38 — ÉTAPE 2d : LE LIAGE MULTIMODAL.

Objectif : qu'un objet perçu SIMULTANÉMENT par deux sens finisse, par répétition, par former
une représentation unique — au point que la réactivation d'une modalité rappelle l'autre.

    « Tu vois et tu sens une pomme -> plus tard tu cherches de la nourriture, tu peux
      anticiper où est la pomme par son odeur. »

--- Sur quelle base cette étape est construite, et pourquoi ---

Le chantier a produit six conditions. Une seule tient statistiquement :

    2b (continuité + densité) : 5 positifs sur 5, AUCUNE régression, p = 0,062
    2a                        : 4/5, p = 0,375, une graine en recul
    2c, 2c-fix, 2c-ter        : p = 1,000 / 1,000 / 0,688

**2d s'empile donc sur 2b**, pas sur la pile complète. Empiler sur 2c-ter reviendrait à
construire sur une brique dont l'apport n'est pas démontré : un résultat nul serait
ininterprétable (« le liage n'apporte rien » vs « la brique du dessous l'a annulé »).

Le son de 2c-ter est CONSERVÉ — il est le seul moyen d'obtenir la co-occurrence vue<->ouïe,
et c'est sa version corrigée (parcimonie, variance, vrai silence) qui a cessé de coûter des
paliers. Ce qui est écarté, c'est le parent (2c), pas le son.

--- Le mécanisme ---

Un terme de perte qui RAPPROCHE les modalités co-occurrentes et ÉLOIGNE celles qui ne
co-occurrent pas. Formulation InfoNCE symétrique sur les deux sorties de porte :

    positif : (vision_t, audio_t)          -- le même tick, donc le même objet
    négatifs: (vision_t, audio_t') t'!=t   -- des ticks différents du même lot

--- ⚠️ Le mode d'échec silencieux, et sa parade ---

Sans négatifs, la solution triviale est l'EFFONDREMENT : toutes les représentations au même
point, perte nulle, plus rien de distingué. La courbe descend magnifiquement pendant que la
représentation meurt.

C'est pourquoi :
  (a) les négatifs sont obligatoires (in-batch, jamais de perte purement attractive) ;
  (b) la VARIANCE des embeddings est instrumentée AVANT d'activer la perte, pas après —
      `Liage_Variance_Vision` et `Liage_Variance_Audio` doivent rester non nulles ;
  (c) un tick de quasi-silence est EXCLU des paires : rapprocher une forme visuelle du
      silence apprendrait au silence à être prédictif, l'inverse du but. Le silence est un
      signal (v38-2c-ter) mais ce n'est pas un NOM.

--- ⚠️ Rien n'est expliqué en dur ---

Aucune table objet->son. Le seul signal est la SIMULTANÉITÉ : deux canaux actifs au même
tick. Le cerveau n'apprend jamais « ce MFCC est une clé », il apprend « ces deux signaux
arrivent ensemble ».

Aucun fichier du projet n'est modifié : tout passe par surcharge en mémoire.
"""

import argparse
import json
import random
import time

import numpy as np
import torch
import torch.nn.functional as F
import wandb
from gymnasium.envs.registration import register

import naulthene.cerveau.noyau as N

for _t in (10, 12):
    try:
        register(id=f"MiniGrid-DoorKey-{_t}x{_t}-v0",
                 entry_point="minigrid.envs:DoorKeyEnv", kwargs={"size": _t})
    except Exception:
        pass

PALIERS = [
    ("MiniGrid-DoorKey-5x5-v0", "DoorKey 5×5   (9 cases)"),
    ("MiniGrid-DoorKey-6x6-v0", "DoorKey 6×6   (16 cases)"),
    ("MiniGrid-DoorKey-8x8-v0", "DoorKey 8×8   (36 cases)"),
    ("MiniGrid-DoorKey-10x10-v0", "DoorKey 10×10 (64 cases)"),
    ("MiniGrid-DoorKey-12x12-v0", "DoorKey 12×12 (100 cases)"),
    ("MiniGrid-DoorKey-16x16-v0", "DoorKey 16×16 (196 cases)"),
]
SURFACE = {"5x5": 9, "6x6": 16, "8x8": 36, "10x10": 64, "12x12": 100, "16x16": 196}

import importlib.util as _ilu
import os as _os
_d = _os.path.dirname(_os.path.abspath(__file__))
def _charger(nom, fichier):
    s = _ilu.spec_from_file_location(nom, _os.path.join(_d, fichier))
    m = _ilu.module_from_spec(s); s.loader.exec_module(m); return m
_m2a = _charger("v38_2a", "v38_2a_continuite.py")
_m2b = _charger("v38_2b", "v38_2b_permanence.py")
_m2t = _charger("v38_2cter", "v38_2cter_parcimonie.py")

_grille_de = _m2a._grille_de
installer_continuite = _m2a.installer_continuite
densite_pour = _m2b.densite_pour
MondeSonore = _m2t.MondeSonore

# Poids du terme de liage dans la perte totale. Une BORNE : à 0.0 la mécanique est
# entièrement désactivée et le comportement est bit-identique à 2b + son.
POIDS_LIAGE = 0.05
# Température de l'InfoNCE. Plus elle est basse, plus la perte est exigeante sur la
# séparation des négatifs.
TEMPERATURE_LIAGE = 0.1
# Nombre minimal de paires dans un lot pour que la perte ait un sens : avec moins de 4
# négatifs, l'InfoNCE dégénère en simple attraction — donc en effondrement.
PAIRES_MIN_LIAGE = 8


class CollecteurPaires:
    """Accumule les paires (vision, audio) co-occurrentes de la journée.

    On stocke les sorties de PORTE (`porte_visuelle`, `porte_auditive`), pas les
    observations brutes : c'est là que les deux modalités vivent déjà dans le même espace,
    et c'est ce que le bus somme aujourd'hui sans jamais les lier.
    """

    def __init__(self):
        self.vision, self.audio = [], []

    def ajouter(self, obs_v, obs_a):
        # Les OBSERVATIONS sont stockées (détachées : elles ne portent pas de gradient),
        # les projections seront recalculées dans `perte()` pour que le gradient
        # atteigne bien les deux portes.
        self.vision.append(obs_v.detach().reshape(1, -1))
        self.audio.append(obs_a.detach().reshape(1, -1))

    def vider(self):
        self.vision, self.audio = [], []

    def perte(self, agent):
        """InfoNCE symétrique. Retourne (perte, variance_vision, variance_audio).

        La variance est retournée pour être LOGUÉE : c'est le détecteur d'effondrement.
        Si elle s'effondre vers 0, la perte « réussit » en détruisant la représentation.
        """
        if len(self.vision) < PAIRES_MIN_LIAGE:
            return None, 0.0, 0.0
        V = F.relu(agent.porte_visuelle(torch.cat(self.vision, dim=0)))
        A = F.relu(agent.porte_auditive(torch.cat(self.audio, dim=0)))
        Vn = F.normalize(V, dim=-1)
        An = F.normalize(A, dim=-1)
        logits = (Vn @ An.T) / TEMPERATURE_LIAGE
        cible = torch.arange(len(Vn), device=Vn.device)
        # Symétrique : vision->audio ET audio->vision. Une seule direction laisserait une
        # modalité libre de s'effondrer.
        perte = 0.5 * (F.cross_entropy(logits, cible) +
                       F.cross_entropy(logits.T, cible))
        return perte, float(V.var(dim=0).mean()), float(A.var(dim=0).mean())


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--jours", type=int, default=600)
    p.add_argument("--brain", type=str, required=True)
    p.add_argument("--graine", type=int, default=None)
    p.add_argument("--densite", type=float, default=3.0)
    p.add_argument("--liage", action="store_true",
                   help="active la perte de liage ; sans ce flag = TEMOIN (2b + son)")
    p.add_argument("--patience-surface", action="store_true")
    p.add_argument("--journal", type=str, default=None)
    p.add_argument("--no-wandb", action="store_true")
    a = p.parse_args()

    if a.graine is not None:
        torch.manual_seed(a.graine)
        N.np.random.seed(a.graine)
        random.seed(a.graine)

    N.BUS_REFERENCE_INITIAL = 64
    N.PROGRAMME[:] = PALIERS
    N.TAUX_PROMOTION = 0.35
    N.VICTOIRES_REQUISES = 1

    nom = "2d_LIAGE" if a.liage else "2d_TEMOIN"
    print(f"\n🔗 v38 ÉTAPE 2d — {nom}   (graine {a.graine})\n", flush=True)
    print("   base : 2b (continuité + densité) — la seule condition qui tient (p=0,062)")
    print("   son  : 2c-ter (parcimonie, variance, vrai silence)")
    print(f"   liage: {'InfoNCE symétrique, poids ' + str(POIDS_LIAGE) if a.liage else 'DÉSACTIVÉ'}")
    print(flush=True)

    from naulthene.audio.lecons_vocales import CacheReferencesVocales
    from naulthene.cerveau.persistance import PersistanceAnatomique
    from naulthene.salles_de_classe.cursus_developpemental import _perception_du_tick

    persistance = PersistanceAnatomique(a.brain)
    etat = persistance.charger_ou_naitre()
    cache = CacheReferencesVocales()
    rng = random.Random(7 if a.graine is None else 7 + a.graine)
    stats = {"continuations": 0, "resets_secours": 0}
    monde = MondeSonore(rng)
    collecteur = CollecteurPaires() if a.liage else None

    if not a.no_wandb:
        wandb.init(project="Naulthene-AGI", name=f"V38_{nom}_g{a.graine}_{a.jours}j",
                   config={"etape": "2d", "liage": a.liage, "poids": POIDS_LIAGE,
                           "graine": a.graine})

    journal = open(a.journal, "a", buffering=1) if a.journal else None
    derniere_action, niveau_prec = 0, etat.niveau_actuel
    env_installe = None
    jour_depart, t0 = etat.jour, time.time()
    liage_cumul, var_v, var_a = 0.0, 0.0, 0.0

    try:
        for _ in range(a.jours):
            n_src = densite_pour(PALIERS[etat.niveau_actuel][0], a.densite)
            N.NB_SOURCES_FOOD = N.NB_SOURCES_WATER = n_src
            d = getattr(etat, "detecteur_ressources_bio", None)
            if d is not None:
                d.nb_sources_food = d.nb_sources_water = n_src

            N.demarrer_journee(etat)
            if etat.env is not env_installe:
                installer_continuite(etat, rng, stats)
                env_installe = etat.env

            if a.patience_surface:
                cle = etat.env_id.replace("MiniGrid-DoorKey-", "").replace("-v0", "")
                f = (SURFACE.get(cle, 9) / 9) ** 0.5
                etat.patience_jour = int(etat.patience_jour * f)
                etat.patience_base_jour = etat.patience_jour

            if collecteur is not None:
                collecteur.vider()
            cases, cooc = set(), 0

            ere = N.ere_courante(etat.jour)
            for tick in range(N.ticks_par_jour):
                moment = "matin" if tick < N.TICKS_MATIN else "apres_midi"
                mode, obs_aud, formants = _perception_du_tick(
                    etat, cache, ere, moment, derniere_action)

                emission = False
                if mode == "minigrid":
                    try:
                        e = _grille_de(etat.env)
                        avant = monde.ticks_sonores
                        m = monde.ecouter(e)
                        if m is not None:
                            obs_aud = torch.tensor([m], dtype=torch.float32,
                                                   device=N.DEVICE)
                            emission = monde.ticks_sonores > avant
                            if emission:
                                cooc += 1
                    except Exception:
                        pass

                # --- 2d : collecte des paires co-occurrentes ---
                # ⚠️ Seules les vraies ÉMISSIONS sont appariées. Un tick de quasi-silence
                # est exclu : rapprocher une forme visuelle du silence apprendrait au
                # silence à être prédictif — exactement l'inverse du but.
                if collecteur is not None and emission and obs_aud is not None:
                    try:
                        # On mémorise les ENTRÉES, pas les sorties de porte : le
                        # gradient du liage doit traverser `porte_visuelle` et
                        # `porte_auditive`, donc les projections sont recalculées au
                        # moment du backward. Stocker des tenseurs `.detach()`és ici
                        # rendrait la perte inopérante sur les poids.
                        collecteur.ajouter(etat.etat_courant, obs_aud)
                    except Exception:
                        pass

                infos = N.traiter_tick(etat, obs_auditive=obs_aud,
                                       formants_cibles=formants, mode_perception=mode)
                if infos["action"] is not None:
                    derniere_action = infos["action"]
                if mode == "minigrid":
                    try:
                        e = _grille_de(etat.env)
                        cases.add((int(e.agent_pos[0]), int(e.agent_pos[1])))
                    except Exception:
                        pass

            # --- 2d : un pas de gradient de liage, APRÈS la journée ---
            # Placé ici et non dans `traiter_tick` : le liage est un apprentissage de
            # structure, pas une décision. Il ne doit jamais influencer l'action du tick.
            if collecteur is not None:
                perte, var_v, var_a = collecteur.perte(etat.agent)
                if perte is not None:
                    # ⚠️ Pas de `except` silencieux ici. La première version appelait
                    # `optimiseur` (au lieu de `optimizer`, noyau.py:533) : l'exception
                    # aurait été avalée, le liage n'aurait JAMAIS appris, et le run
                    # aurait produit un « effet nul » parfaitement crédible. Un banc
                    # d'essai qui masque ses propres pannes mesure du vide.
                    etat.agent.optimizer.zero_grad()
                    (POIDS_LIAGE * perte).backward()
                    etat.agent.optimizer.step()
                    liage_cumul = float(perte)

            log = N.executer_nuit(etat)
            sv_mem = etat.memoire_episodique_spatiale.souvenirs
            conf = (sum(s.get('confirmations', 1) for s in sv_mem) / len(sv_mem)) if sv_mem else 0.0
            log.update({"Etape": "2d", "Liage": int(a.liage),
                        "Palier_Difficulte": etat.niveau_actuel,
                        "Reperes_N": len(sv_mem), "Confirmations_Moyennes": conf,
                        "Cooc_Vue_Ouie": cooc / max(1, N.TICKS_MATIN),
                        "Liage_Perte": liage_cumul,
                        "Liage_Variance_Vision": var_v,
                        "Liage_Variance_Audio": var_a})
            if not a.no_wandb:
                wandb.log(log)
            persistance.sauvegarder(etat)

            if journal:
                journal.write(json.dumps({
                    "nom": nom, "graine": a.graine, "jour": etat.jour,
                    "niveau": etat.niveau_actuel, "victoire": log.get("Victoire", 0),
                    "victoires_total": etat.victoires_totales,
                    "reperes": len(sv_mem), "confirmations": round(conf, 2),
                    "cooc_vue_ouie": round(cooc / max(1, N.TICKS_MATIN), 3),
                    "liage_perte": round(liage_cumul, 4),
                    "var_vision": round(var_v, 6), "var_audio": round(var_a, 6),
                    "odorat_approche": log.get("Sens_Odorat_Taux_Approche"),
                }) + "\n")

            if etat.niveau_actuel != niveau_prec:
                print(f"   📈 Jour {etat.jour} — {N.PROGRAMME[etat.niveau_actuel][1]}",
                      flush=True)
                niveau_prec = etat.niveau_actuel
    except KeyboardInterrupt:
        print("\n⏹️  Interrompu — cerveau sauvegardé.")
    finally:
        if journal:
            journal.close()
        if not a.no_wandb:
            wandb.finish()

    print(f"\n✅ {nom} g{a.graine} — palier {etat.niveau_actuel}/{len(N.PROGRAMME)-1}, "
          f"jour {etat.jour} (+{etat.jour-jour_depart} en {(time.time()-t0)/60:.0f} min), "
          f"{etat.victoires_totales} victoires, "
          f"variance finale vision {var_v:.4f} / audio {var_a:.4f}", flush=True)


if __name__ == "__main__":
    main()
