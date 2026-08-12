"""v38 — ÉTAPE 2a : LA CONTINUITÉ PERMANENTE.

Exigence utilisateur : *« la continuité permanente »*.

Aujourd'hui, `noyau.py:5221` appelle `etat.env.reset()` à chaque fin d'épisode : l'agent est
téléporté, le monde régénéré, la mémoire tampon vidée. Avec une patience de ~120 ticks, cela
arrive 3 à 4 fois par journée de 400 ticks.

Conséquence mesurée par l'ablation du 12/08 : couper l'odorat ne change RIEN. Non pas parce
que le sens est mauvais — l'odorat topologique v32.0 calcule un signal correct — mais parce
que **le monde n'a pas de T+n**. L'agent sent une source hors de son champ de vision, puis
il est téléporté avant d'avoir pu y revenir. La redondance ne devient jamais prédiction.

    « Tu vois et tu sens une pomme → plus tard tu cherches de la nourriture, tu peux
      anticiper où est la pomme par son odeur. »

Ce « plus tard » n'existe pas dans le monde actuel. Cette étape le crée.

--- Ce qui change, et RIEN d'autre ---

Le `reset()` de fin d'épisode est remplacé par une **continuation** : le monde persiste,
l'agent reste où il est, et seul le BUT est repositionné ailleurs sur la carte. L'agent doit
donc aller le chercher depuis sa position courante, dans un monde qu'il a déjà exploré.

Ce qui est PRÉSERVÉ malgré la continuité (et pourquoi) :

  * `ticks_episode_courant` est remis à 0 — sinon la patience coupe l'agent définitivement
    après le premier « épisode ».
  * `_enregistrer_episode_niveau` continue d'être appelé — sans lui, plus AUCUNE promotion
    n'est possible (`historique_episodes_niveau` resterait vide). C'est le risque principal
    identifié au plan : un monde continu n'a pas d'épisodes, mais le cursus en a besoin.
    On garde donc la NOTION d'épisode (une tentative d'atteindre le but) tout en supprimant
    la DISCONTINUITÉ du monde.
  * Les détecteurs sont réinitialisés, car ils mesurent une tentative, pas un monde.

Ce qui n'est explicitement PAS réinitialisé — c'est tout l'objet de l'étape :

  * la grille et les ressources (le monde persiste)
  * la position de l'agent (pas de téléportation)
  * `memoire_tampon` et `vecteurs_episodiques` (le contexte survit)
  * `bus_sensoriel` (la trace de goût et `_odeurs_precedentes` survivent)

⚠️ INVARIANT v32.0 (4) — nuance importante : `_odeurs_precedentes` DOIT être remis à None
quand l'agent est téléporté, sinon la clinotaxie injecte un ΔS énorme et fictif. Ici l'agent
n'est PAS téléporté : le conserver est non seulement permis, c'est le but. La raison de
l'invariant (« au reset l'agent est téléporté et les sources régénérées ») ne s'applique
plus quand ni l'un ni l'autre n'a lieu.

Aucun fichier du projet n'est modifié : tout passe par surcharge en mémoire.
"""

import argparse
import json
import random
import time

import numpy as np
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


def _grille_de(env):
    """Remonte jusqu'à l'environnement MiniGrid sous les wrappers éventuels."""
    e = env
    while not hasattr(e, "grid") and hasattr(e, "env"):
        e = e.env
    return e


def _rearmer_tache(env, rng):
    """Redonne un objectif à résoudre SANS régénérer le monde ni déplacer l'agent.

    --- Le piège trouvé au smoke test, et la distinction qu'il impose ---

    Une continuité naïve (« ne jamais rien réinitialiser ») rend la tâche TRIVIALE dès la
    première réussite, parce que trois états de la tâche sont absorbants :

        carrying   : la clé n'est jamais relâchée      → Portage 100 % (mesuré)
        la porte   : une fois ouverte, elle le reste   → plus aucun obstacle
        souvenirs  : plus rien de neuf à mémoriser     → figés à 1 (mesuré)

    Le témoin donne Portage 39-77 % et 4 souvenirs ; la version naïve donnait 100 % et
    1 souvenir figé. L'agent ne résolvait plus rien — il traversait une porte déjà ouverte,
    clé en main. On aurait mesuré une « progression » qui n'aurait rien voulu dire.

    D'où la distinction, qui est le vrai contenu de l'étape 2a :

        PERSISTE (c'est le but)          | SE RÉARME (sinon plus de tâche)
        ---------------------------------|--------------------------------
        la grille et sa topologie        | la position du but
        la position de l'agent           | la clé, reposée au sol
        memoire_tampon, épisodiques      | la porte, refermée et verrouillée
        trace de goût, odeurs précédentes|

    C'est aussi ce que fait le vivant : le monde persiste, mais on ne garde pas la pomme
    dans la main pour l'éternité — on la mange, et il faut en retrouver une autre.
    """
    from minigrid.core.world_object import Goal, Key

    e = _grille_de(env)
    ax, ay = int(e.agent_pos[0]), int(e.agent_pos[1])

    def _cases_libres(exclure_agent=True):
        return [(x, y) for x in range(1, e.grid.width - 1)
                for y in range(1, e.grid.height - 1)
                if e.grid.get(x, y) is None and not (exclure_agent and (x, y) == (ax, ay))]

    # 1. Le but : on retire l'ancien, on en repose un LOIN de l'agent. Un but qui
    #    apparaîtrait sous ses pieds ne demanderait aucun déplacement, et le cursus se
    #    validerait sur du vide.
    for x in range(e.grid.width):
        for y in range(e.grid.height):
            if type(e.grid.get(x, y)).__name__ == "Goal":
                e.grid.set(x, y, None)

    libres = _cases_libres()
    if not libres:
        return False
    dmax = max(abs(x - ax) + abs(y - ay) for x, y in libres)
    lointaines = [p for p in libres if abs(p[0] - ax) + abs(p[1] - ay) >= dmax * 0.5]
    gx, gy = lointaines[rng.randrange(len(lointaines))]
    e.grid.set(gx, gy, Goal())

    # 2. La porte : refermée et reverrouillée. Sans cela, la compétence centrale de
    #    DoorKey (trouver la clé, ouvrir) n'est exercée qu'une seule fois par journée.
    portes = [(x, y) for x in range(e.grid.width) for y in range(e.grid.height)
              if type(e.grid.get(x, y)).__name__ == "Door"]
    for px, py in portes:
        d = e.grid.get(px, py)
        d.is_open, d.is_locked = False, True

    # 3. La clé : si l'agent la porte encore, on la lui retire et on la repose au sol.
    #    `carrying` est un état absorbant — rien dans MiniGrid ne le vide jamais.
    if e.carrying is not None:
        if type(e.carrying).__name__ == "Key" and portes:
            libres2 = _cases_libres()
            if libres2:
                kx, ky = libres2[rng.randrange(len(libres2))]
                e.grid.set(kx, ky, e.carrying)
        e.carrying = None
    elif portes and not any(type(e.grid.get(x, y)).__name__ == "Key"
                            for x in range(e.grid.width) for y in range(e.grid.height)):
        # Filet : la carte a une porte mais plus aucune clé (elle a pu être écrasée).
        libres2 = _cases_libres()
        if libres2:
            kx, ky = libres2[rng.randrange(len(libres2))]
            e.grid.set(kx, ky, Key("yellow"))

    return True


def installer_continuite(etat, rng, stats):
    """Remplace le `reset()` de fin d'épisode par une continuation du monde.

    On enveloppe `env.reset` : le premier appel (celui de `demarrer_journee`) est laissé
    intact — il faut bien créer le monde une fois. Les suivants sont détournés vers un
    simple repositionnement du but.
    """
    env = etat.env
    reset_original = env.reset
    e = _grille_de(env)

    # Budget de pas illimité : sinon MiniGrid tronque l'épisode lui-même (`max_steps`),
    # ce qui réintroduirait exactement la discontinuité qu'on supprime.
    e.max_steps = 10 ** 9

    def reset_continu(*a, **kw):
        stats["continuations"] += 1
        ok = _rearmer_tache(env, rng)
        if not ok:                      # cas dégénéré : plus une seule case libre
            stats["resets_secours"] += 1
            return reset_original(*a, **kw)
        # On renvoie l'observation COURANTE (l'agent n'a pas bougé) au lieu d'une
        # observation d'un monde neuf. C'est littéralement « rien ne s'est passé, sauf
        # que l'objectif a changé de place ».
        e.step_count = 0                # la patience redémarre, le monde non
        return e.gen_obs(), {}

    env.reset = reset_continu
    return reset_original


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--jours", type=int, default=600)
    p.add_argument("--brain", type=str, required=True)
    p.add_argument("--graine", type=int, default=None)
    p.add_argument("--continu", action="store_true",
                   help="active la continuité (sans ce flag = TÉMOIN identique à l'ablation)")
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

    nom = "2a_CONTINU" if a.continu else "2a_TEMOIN"
    print(f"\n🌍 v38 ÉTAPE 2a — {nom}   (graine {a.graine})\n", flush=True)
    print("   monde persistant : le reset() est remplacé par un repositionnement du but"
          if a.continu else "   monde discontinu : reset() classique (référence)")
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
                   config={"etape": "2a", "continu": a.continu, "graine": a.graine})

    journal = open(a.journal, "a", buffering=1) if a.journal else None
    derniere_action, niveau_prec = 0, etat.niveau_actuel
    env_installe = None
    jour_depart, t0 = etat.jour, time.time()

    try:
        for _ in range(a.jours):
            N.demarrer_journee(etat)

            # La continuité s'installe APRÈS `demarrer_journee` : c'est lui qui crée
            # l'environnement du jour (et appelle le premier reset, légitime).
            if a.continu and etat.env is not env_installe:
                installer_continuite(etat, rng, stats)
                env_installe = etat.env

            if a.patience_surface:
                cle = etat.env_id.replace("MiniGrid-DoorKey-", "").replace("-v0", "")
                f = (SURFACE.get(cle, 9) / 9) ** 0.5
                etat.patience_jour = int(etat.patience_jour * f)
                etat.patience_base_jour = etat.patience_jour

            cases = set()
            ere = N.ere_courante(etat.jour)
            for tick in range(N.ticks_par_jour):
                moment = "matin" if tick < N.TICKS_MATIN else "apres_midi"
                mode, obs_aud, formants = _perception_du_tick(
                    etat, cache, ere, moment, derniere_action)
                infos = N.traiter_tick(etat, obs_auditive=obs_aud,
                                       formants_cibles=formants, mode_perception=mode)
                if infos["action"] is not None:
                    derniere_action = infos["action"]
                try:                      # 2a.4 — l'agent explore-t-il, ou tourne-t-il ?
                    e = _grille_de(etat.env)
                    cases.add((int(e.agent_pos[0]), int(e.agent_pos[1])))
                except Exception:
                    pass

            log = N.executer_nuit(etat)
            sv = etat.memoire_episodique_spatiale.souvenirs
            conf = (sum(s.get('confirmations', 1) for s in sv) / len(sv)) if sv else 0.0
            log.update({"Etape": "2a", "Continu": int(a.continu),
                        "Palier_Difficulte": etat.niveau_actuel,
                        "Reperes_N": len(sv), "Confirmations_Moyennes": conf,
                        "Continu_Cases_Distinctes_Jour": len(cases),
                        "Continu_Continuations": stats["continuations"],
                        "Continu_Resets_Secours": stats["resets_secours"]})
            if not a.no_wandb:
                wandb.log(log)
            persistance.sauvegarder(etat)

            if journal:
                journal.write(json.dumps({
                    "nom": nom, "graine": a.graine, "jour": etat.jour,
                    "niveau": etat.niveau_actuel, "victoire": log.get("Victoire", 0),
                    "victoires_total": etat.victoires_totales,
                    "reperes": len(sv), "confirmations": round(conf, 2),
                    "cases_distinctes": len(cases),
                    "odorat_approche": log.get("Sens_Odorat_Taux_Approche"),
                    "gout_ticks": log.get("Sens_Gout_Ticks_Actifs"),
                    "toucher": log.get("Sens_Toucher_Contact_Ratio"),
                    "rappel": log.get("Memoire_Taux_Rappel_Reussi"),
                    "jepa": log.get("Erreur_JEPA"),
                    "continuations": stats["continuations"],
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
          f"{stats['continuations']} continuations, "
          f"{stats['resets_secours']} resets de secours", flush=True)


if __name__ == "__main__":
    main()
