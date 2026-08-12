"""v38 — ÉTAPE 2b : LA PERMANENCE DES 5 SENS.

Exigence utilisateur : *« la superposition possible (association des 5 sens en permanence et
en tout lieu et temps) »*.

Cette étape s'empile sur 2a : elle GARDE la continuité et ajoute une seule chose — de quoi
sentir et goûter partout, tout le temps.

--- Le problème mesuré ---

Une association ne peut pas se former sur un canal muet. Or trois des cinq sens se taisent
la plupart du temps (mesuré sur les runs de 1300 jours) :

    Vue      100 %  des ticks
    Toucher   42-58 %
    Odorat    91,7 % ... mais 0,0 % au Doctorat (aucune ressource sur MultiRoom)
    Goût      ~4 %   (14,7 ticks sur 400)
    Ouïe      jamais en même temps que la vue   → traité en 2c

Le goût est le cas extrême : il ne porte un signal que sur 4 % des ticks. `odorat ↔ goût`
est pourtant la paire pronostiquée « très forte » dans `les_sens_combinatoire.md` §6.3 —
c'est la chaîne de survie (sentir avant de goûter, c'est ce qui évite l'empoisonnement).
Elle est aujourd'hui **strictement inobservable**.

--- Ce qui change, et rien d'autre ---

`NB_SOURCES_FOOD` et `NB_SOURCES_WATER` passent de 2+2 à une densité PROPORTIONNELLE à la
surface de la carte. Deux sources sur un 5×5 (9 cases utiles) et deux sur un 16×16
(196 cases) ne produisent pas du tout la même disponibilité olfactive : c'est la même erreur
d'échelle que la patience corrigée en A3.

    densite = DENSITE_RESSOURCES  (sources pour 20 cases utiles)
    nb_food = nb_water = max(2, round(cases_utiles / 20 * densite))

--- ⚠️ Le risque, posé d'avance ---

Un monde saturé de ressources supprime la rareté, donc l'enjeu. Le déficit métabolique est
aujourd'hui à **100 % des ticks en zone critique** sur tous les runs
(`dia_Aout_2026.md` §5) : passer brutalement à 0 % supprimerait toute pression de survie et
rendrait le métabolisme décoratif.

C'est pourquoi la densité est **instrumentée puis mesurée**, jamais posée définitivement :
la métrique `Calibrage_Ticks_Critiques_Ratio` doit rester **strictement entre 0 et 1**. Si
elle tombe à 0, la densité est trop forte et le test est invalide — on aurait remplacé un
monde impossible par un monde sans enjeu.

Doctrine du projet (v30.1) : instrumenter d'abord, calibrer ensuite. Cette étape MESURE
l'effet de la densité, elle ne prétend pas avoir trouvé la bonne valeur.

Aucun fichier du projet n'est modifié : tout passe par surcharge en mémoire.
"""

import argparse
import json
import random
import time

import torch
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

# On réutilise le réarmement de tâche de 2a — même code, même invariants.
import importlib.util as _ilu
import os as _os
_spec = _ilu.spec_from_file_location(
    "v38_2a", _os.path.join(_os.path.dirname(_os.path.abspath(__file__)),
                            "v38_2a_continuite.py"))
_m2a = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(_m2a)
_grille_de = _m2a._grille_de
_rearmer_tache = _m2a._rearmer_tache
installer_continuite = _m2a.installer_continuite


def densite_pour(env_id, densite):
    """Nombre de sources de chaque type, proportionnel à la surface utile de la carte.

    Deux sources fixes sur un 5×5 et sur un 16×16 ne donnent pas la même disponibilité
    olfactive — c'est la même erreur d'échelle que la patience, corrigée en A3.
    """
    cle = env_id.replace("MiniGrid-DoorKey-", "").replace("-v0", "")
    cases = SURFACE.get(cle, 9)
    return max(2, round(cases / 20.0 * densite))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--jours", type=int, default=600)
    p.add_argument("--brain", type=str, required=True)
    p.add_argument("--graine", type=int, default=None)
    p.add_argument("--densite", type=float, default=0.0,
                   help="sources pour 20 cases utiles ; 0 = TÉMOIN (2+2 fixes, comme 2a)")
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

    nom = f"2b_DENSITE{a.densite:g}" if a.densite > 0 else "2b_TEMOIN"
    print(f"\n🌾 v38 ÉTAPE 2b — {nom}   (graine {a.graine})\n", flush=True)
    print("   continuité 2a : ACTIVE (le monde persiste, la tâche se réarme)")
    if a.densite > 0:
        for e, _l in PALIERS:
            print(f"      {e.replace('MiniGrid-DoorKey-','').replace('-v0',''):>6} → "
                  f"{densite_pour(e, a.densite)} food + {densite_pour(e, a.densite)} water")
    else:
        print("   densité      : 2 food + 2 water (fixe) — référence")
    print(flush=True)

    from naulthene.audio.lecons_vocales import CacheReferencesVocales
    from naulthene.cerveau.persistance import PersistanceAnatomique
    from naulthene.salles_de_classe.cursus_developpemental import _perception_du_tick

    persistance = PersistanceAnatomique(a.brain)
    etat = persistance.charger_ou_naitre()
    cache = CacheReferencesVocales()
    rng = random.Random(7 if a.graine is None else 7 + a.graine)
    stats = {"continuations": 0, "resets_secours": 0}

    if not a.no_wandb:
        wandb.init(project="Naulthene-AGI", name=f"V38_{nom}_g{a.graine}_{a.jours}j",
                   config={"etape": "2b", "densite": a.densite, "graine": a.graine,
                           "continu": True})

    journal = open(a.journal, "a", buffering=1) if a.journal else None
    derniere_action, niveau_prec = 0, etat.niveau_actuel
    env_installe = None
    jour_depart, t0 = etat.jour, time.time()

    try:
        for _ in range(a.jours):
            # La densité doit être appliquée AVANT `demarrer_journee`, qui construit
            # l'environnement du jour et place les ressources.
            if a.densite > 0:
                n = densite_pour(PALIERS[etat.niveau_actuel][0], a.densite)
                N.NB_SOURCES_FOOD = n
                N.NB_SOURCES_WATER = n
                d = getattr(etat, "detecteur_ressources_bio", None)
                if d is not None:
                    d.nb_sources_food = n
                    d.nb_sources_water = n

            N.demarrer_journee(etat)

            if etat.env is not env_installe:          # continuité 2a, toujours active
                installer_continuite(etat, rng, stats)
                env_installe = etat.env

            if a.patience_surface:
                cle = etat.env_id.replace("MiniGrid-DoorKey-", "").replace("-v0", "")
                f = (SURFACE.get(cle, 9) / 9) ** 0.5
                etat.patience_jour = int(etat.patience_jour * f)
                etat.patience_base_jour = etat.patience_jour

            cases, n_canaux = set(), []
            ere = N.ere_courante(etat.jour)
            for tick in range(N.ticks_par_jour):
                moment = "matin" if tick < N.TICKS_MATIN else "apres_midi"
                mode, obs_aud, formants = _perception_du_tick(
                    etat, cache, ere, moment, derniere_action)
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

            log = N.executer_nuit(etat)
            sv = etat.memoire_episodique_spatiale.souvenirs
            conf = (sum(s.get('confirmations', 1) for s in sv) / len(sv)) if sv else 0.0

            # 2b.1 — combien de canaux portent réellement un signal ?
            presents = 1  # la vue est toujours là
            for cle_m, seuil in (("Sens_Toucher_Contact_Ratio", 0.05),
                                 ("Sens_Odorat_Ticks_Actifs_Ratio", 0.05)):
                if (log.get(cle_m) or 0) > seuil:
                    presents += 1
            if (log.get("Sens_Gout_Ticks_Actifs") or 0) > 0:
                presents += 1

            log.update({"Etape": "2b", "Densite": a.densite, "Continu": 1,
                        "Palier_Difficulte": etat.niveau_actuel,
                        "Reperes_N": len(sv), "Confirmations_Moyennes": conf,
                        "Continu_Cases_Distinctes_Jour": len(cases),
                        "Cooc_N_Canaux": presents})
            if not a.no_wandb:
                wandb.log(log)
            persistance.sauvegarder(etat)

            if journal:
                journal.write(json.dumps({
                    "nom": nom, "graine": a.graine, "jour": etat.jour,
                    "niveau": etat.niveau_actuel, "victoire": log.get("Victoire", 0),
                    "victoires_total": etat.victoires_totales,
                    "reperes": len(sv), "confirmations": round(conf, 2),
                    "cases_distinctes": len(cases), "n_canaux": presents,
                    "odorat_actif": log.get("Sens_Odorat_Ticks_Actifs_Ratio"),
                    "odorat_approche": log.get("Sens_Odorat_Taux_Approche"),
                    "gout_ticks": log.get("Sens_Gout_Ticks_Actifs"),
                    "toucher": log.get("Sens_Toucher_Contact_Ratio"),
                    # garde-fou : si ce ratio tombe a 0, la densite a tue la rarete
                    "ticks_critiques": log.get("Calibrage_Ticks_Critiques_Ratio"),
                    "autonomie": log.get("Calibrage_Autonomie_Jauges"),
                    "food": log.get("Bio_Food_Consommes_Jour"),
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
          f"{etat.victoires_totales} victoires, {stats['continuations']} continuations",
          flush=True)


if __name__ == "__main__":
    main()
