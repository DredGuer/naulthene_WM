"""v38 — ÉTAPE 2c : LE PARENT PHYSIQUE.

Exigence utilisateur : *« il faudrait de la vie dans le monde et quelqu'un qui guide
l'agent (un parent physique) »*.

S'empile sur 2a (continuité) et 2b (permanence des sens), et ajoute une seule chose : une
entité qui montre, nomme et nourrit.

--- Pourquoi c'est la vraie pièce manquante ---

`Cooc_Vue_Ouie = 0` aujourd'hui. Le professeur parle OU l'agent regarde, jamais les deux au
même tick (`les_sens_combinatoire.md` §9). Tant que c'est le cas, **aucune association
vue↔son ne peut se former**, quel que soit le monde. Une perte de liage n'aurait rien à
mordre — c'est exactement l'erreur de la v33 (concevoir sur une prémisse non mesurée).

Le parent résout la synchronisation PAR CONSTRUCTION : il est *dans* la grille, donc ce
qu'il nomme est visible au moment où il le nomme.

--- La remarque de l'utilisateur, qui cadre cette étape ---

    « L'ouïe est peut-être le plus difficile à exploiter, par sa nature dans MiniGrid où il
      y a tout à créer comme son. »

C'est exact et ça distingue 2c des étapes précédentes. Vue, toucher, odorat et goût DÉRIVENT
d'un état de la grille (une case occupée, un contact, une distance topologique). L'ouïe ne
dérive de rien : MiniGrid est muet. Il n'y a pas de son à capter, il y a un son à FABRIQUER.

Vérifié avant d'écrire cette étape — la machinerie existe déjà et n'a rien de spécifique à
la voix humaine :

    SynthetiseurFormants  vecteur 8 dims -> onde     (pur numpy)
    extraire_mfcc         onde -> 130 dims           (l'entrée qu'attend porte_auditive)

Un « nom d'objet » est donc simplement un vecteur de 8 paramètres formantiques. Quatre noms
synthétiques produisent des MFCC dont les distances valent 2,59 à 5,66 : distinguables, donc
apprenables. Aucune brique nouvelle n'est nécessaire.

--- ⚠️ Rien n'est expliqué en dur ---

Le son associé à un type d'objet est ARBITRAIRE et OPAQUE. Le cerveau ne reçoit jamais
« ceci est une clé » : il reçoit un MFCC qui co-occurre avec une forme visuelle. Le lien est
à apprendre, jamais déclaré — même discipline que la mémoire v36.0, où la valence d'un type
est apprise et jamais tabulée.

--- ⚠️ Le sevrage est MÉRITÉ, jamais daté ---

`empreinte_enfance` (1,0 à la naissance → 0,25 mesuré aujourd'hui) est déjà une mesure
continue de maturité, sérialisée dans le `.brain`. Elle sert de curseur d'intervention :
aucun compteur de jours n'est introduit, conformément au cadrage v34 §3.3.

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
from naulthene.audio.hemisphere_audio import (SynthetiseurFormants, extraire_mfcc,
                                              SAMPLE_RATE)

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
_spec = _ilu.spec_from_file_location("v38_2a", _os.path.join(_d, "v38_2a_continuite.py"))
_m2a = _ilu.module_from_spec(_spec); _spec.loader.exec_module(_m2a)
_spec2 = _ilu.spec_from_file_location("v38_2b", _os.path.join(_d, "v38_2b_permanence.py"))
_m2b = _ilu.module_from_spec(_spec2); _spec2.loader.exec_module(_m2b)

_grille_de = _m2a._grille_de
installer_continuite = _m2a.installer_continuite
densite_pour = _m2b.densite_pour


# --- Le vocabulaire du parent -------------------------------------------------------
# 8 paramètres formantiques par type, ARBITRAIRES et OPAQUES. Le cerveau n'apprend jamais
# que ces chiffres signifient « clé » : il apprend qu'un certain MFCC accompagne une
# certaine forme visuelle. Les valeurs sont choisies pour être bien séparées en MFCC
# (distances mesurées : 2,59 à 5,66), pas pour ressembler à un mot français.
VOCABULAIRE = {
    "Key":   [0.50, 0.15, 0.85, 0.50, 0.30, 0.30, 0.40, 0.70],
    "Door":  [0.50, 0.75, 0.25, 0.50, 0.30, 0.30, 0.40, 0.70],
    "Goal":  [0.50, 0.45, 0.55, 0.50, 0.30, 0.30, 0.40, 0.70],
    "Ball":  [0.50, 0.25, 0.35, 0.50, 0.30, 0.30, 0.40, 0.70],
}

# Borne haute de la fréquence de parole du parent (une BORNE, pas un seuil de décision —
# la fréquence réelle reste dérivée de `empreinte_enfance`). Mesuré au smoke test : sans
# elle, le parent parle 100 % des ticks et le son cesse d'être informatif.
PLAFOND_PAROLE = 0.35


class ParentPhysique:
    """Une entité qui MONTRE, NOMME et NOURRIT — et qui se retire en grandissant.

    Le parent n'occupe pas de case (il ne bloque jamais l'agent) : il est un point de
    référence mobile qui désigne. Ce choix évite d'ajouter un obstacle dans un monde déjà
    contraint, et rend le geste « montrer » lisible : le parent va se placer SUR l'objet
    qu'il désigne, à la vue de l'agent.
    """

    def __init__(self, rng):
        self.rng = rng
        self.synth = SynthetiseurFormants()
        self.pos = None
        self.cible = None          # (x, y, type) de l'objet montré
        self._mfcc = {}            # cache : un MFCC par type, calculé une seule fois
        self.gestes_montrer = 0
        self.gestes_nourrir = 0
        self.ticks_nomme = 0
        self.ticks_vu = 0          # co-occurrence VUE + OUÏE : la métrique de l'étape

    def mfcc_de(self, type_objet):
        if type_objet not in self._mfcc:
            v = VOCABULAIRE.get(type_objet)
            if v is None:
                return None
            onde = self.synth.synthetiser(v)
            self._mfcc[type_objet] = np.asarray(
                extraire_mfcc(onde, SAMPLE_RATE), dtype=np.float32).reshape(-1)
        return self._mfcc[type_objet]

    def _objets_saillants(self, e):
        out = []
        for x in range(e.grid.width):
            for y in range(e.grid.height):
                o = e.grid.get(x, y)
                t = type(o).__name__
                if t in VOCABULAIRE:
                    out.append((x, y, t))
        return out

    def _dans_le_champ(self, e, x, y):
        """L'objet est-il dans le cône de vision 7×7 de l'agent ?

        C'est la condition SINE QUA NON de l'étape : nommer un objet que l'agent ne voit
        pas n'associerait rien — pire, cela apprendrait au cerveau que le son ne prédit
        aucune forme. On approxime le cône par la distance de Chebyshev au rayon de vue,
        ce qui suffit ici (l'exactitude du cône importe moins que le fait de ne jamais
        nommer un objet lointain).
        """
        ax, ay = int(e.agent_pos[0]), int(e.agent_pos[1])
        r = getattr(e, "agent_view_size", 7) // 2
        return max(abs(x - ax), abs(y - ay)) <= r

    def agir(self, etat, e, force):
        """Un tick de parentage. `force` ∈ [0,1] dérivée de `empreinte_enfance`.

        Retourne le MFCC à injecter comme observation auditive, ou None (silence).
        """
        if self.rng.random() > force:      # le parent n'intervient pas à chaque tick
            return None

        objets = self._objets_saillants(e)
        if not objets:
            return None

        ax, ay = int(e.agent_pos[0]), int(e.agent_pos[1])

        # NOURRIR : si les jauges sont basses, déposer une ressource près de l'agent.
        moteur = getattr(etat, "moteur_bio", None)
        if moteur is not None and min(getattr(moteur, "satiete", 1.0),
                                      getattr(moteur, "hydratation", 1.0)) < 0.2:
            from minigrid.core.world_object import Ball
            libres = [(x, y) for x in range(max(1, ax - 2), min(e.grid.width - 1, ax + 3))
                      for y in range(max(1, ay - 2), min(e.grid.height - 1, ay + 3))
                      if e.grid.get(x, y) is None and (x, y) != (ax, ay)]
            if libres:
                x, y = libres[self.rng.randrange(len(libres))]
                coul = getattr(etat.detecteur_ressources_bio, "COULEUR_FOOD", "red")
                e.grid.set(x, y, Ball(color=coul))
                self.gestes_nourrir += 1

        # MONTRER : se placer sur l'objet saillant le plus proche de l'agent.
        objets.sort(key=lambda o: abs(o[0] - ax) + abs(o[1] - ay))
        x, y, t = objets[0]
        self.pos, self.cible = (x, y), (x, y, t)
        self.gestes_montrer += 1

        # NOMMER : le son n'est émis QUE si l'objet montré est dans le champ de vision.
        if not self._dans_le_champ(e, x, y):
            return None
        self.ticks_nomme += 1
        self.ticks_vu += 1
        return self.mfcc_de(t)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--jours", type=int, default=600)
    p.add_argument("--brain", type=str, required=True)
    p.add_argument("--graine", type=int, default=None)
    p.add_argument("--densite", type=float, default=3.0)
    p.add_argument("--parent", action="store_true",
                   help="active le parent ; sans ce flag = TÉMOIN (= pile 2b)")
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

    nom = "2c_PARENT" if a.parent else "2c_TEMOIN"
    print(f"\n👪 v38 ÉTAPE 2c — {nom}   (graine {a.graine})\n", flush=True)
    print("   pile : continuité (2a) + densité (2b)" + (" + parent (2c)" if a.parent else ""))
    if a.parent:
        print(f"   vocabulaire : {', '.join(VOCABULAIRE)} — sons arbitraires et opaques")
        print("   sevrage     : force ∝ empreinte_enfance (mérité, jamais daté)")
    print(flush=True)

    from naulthene.audio.lecons_vocales import CacheReferencesVocales
    from naulthene.cerveau.persistance import PersistanceAnatomique
    from naulthene.salles_de_classe.cursus_developpemental import _perception_du_tick

    persistance = PersistanceAnatomique(a.brain)
    etat = persistance.charger_ou_naitre()
    cache = CacheReferencesVocales()
    rng = random.Random(7 if a.graine is None else 7 + a.graine)
    stats = {"continuations": 0, "resets_secours": 0}
    parent = ParentPhysique(rng) if a.parent else None

    if not a.no_wandb:
        wandb.init(project="Naulthene-AGI", name=f"V38_{nom}_g{a.graine}_{a.jours}j",
                   config={"etape": "2c", "parent": a.parent, "densite": a.densite,
                           "graine": a.graine, "continu": True})

    journal = open(a.journal, "a", buffering=1) if a.journal else None
    derniere_action, niveau_prec = 0, etat.niveau_actuel
    env_installe = None
    jour_depart, t0 = etat.jour, time.time()

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

            # Le sevrage : le parent intervient d'autant plus que le cerveau est jeune.
            # `empreinte_enfance` vaut 1,0 à la naissance et décroît avec la neurogenèse.
            #
            # ⚠️ Corrigé au smoke test : `empreinte_enfance` seule donne force = 1,0 sur un
            # cerveau neuf, donc Cooc_Vue_Ouie = 1,000 — le parent parle à CHAQUE tick.
            # Un signal permanent est un bruit de fond : il ne peut rien prédire, puisqu'il
            # est toujours là. L'association a besoin que le son soit parfois absent pour
            # que sa présence porte de l'information.
            #
            # `PLAFOND_PAROLE` borne donc la fréquence d'intervention. Ce n'est PAS un
            # seuil de décision (il n'y a aucun « si X alors parler ») : c'est une borne
            # sur une variable continue, exactement le rôle que CLAUDE.md assigne aux
            # constantes — « les constantes sont des bornes, les valeurs sont dérivées ».
            force = (PLAFOND_PAROLE * float(getattr(etat, "empreinte_enfance", 1.0))
                     if a.parent else 0.0)
            cases, cooc = set(), 0

            ere = N.ere_courante(etat.jour)
            for tick in range(N.ticks_par_jour):
                moment = "matin" if tick < N.TICKS_MATIN else "apres_midi"
                mode, obs_aud, formants = _perception_du_tick(
                    etat, cache, ere, moment, derniere_action)

                # --- 2c : le parent parle PENDANT que l'agent regarde ---
                # C'est tout l'objet de l'étape. On n'écrase le canal auditif que
                # pendant la phase MiniGrid : l'après-midi vocal garde ses leçons.
                if parent is not None and mode == "minigrid":
                    try:
                        e = _grille_de(etat.env)
                        m = parent.agir(etat, e, force)
                        if m is not None:
                            obs_aud = torch.tensor([m], dtype=torch.float32,
                                                   device=N.DEVICE)
                            cooc += 1
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

            log = N.executer_nuit(etat)
            sv = etat.memoire_episodique_spatiale.souvenirs
            conf = (sum(s.get('confirmations', 1) for s in sv) / len(sv)) if sv else 0.0
            log.update({"Etape": "2c", "Parent": int(a.parent),
                        "Palier_Difficulte": etat.niveau_actuel,
                        "Reperes_N": len(sv), "Confirmations_Moyennes": conf,
                        "Continu_Cases_Distinctes_Jour": len(cases),
                        "Cooc_Vue_Ouie": cooc / max(1, N.TICKS_MATIN),
                        "Parent_Gestes_Montrer": parent.gestes_montrer if parent else 0,
                        "Parent_Gestes_Nourrir": parent.gestes_nourrir if parent else 0,
                        "Parent_Force": force})
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
                    "cooc_vue_ouie": round(cooc / max(1, N.TICKS_MATIN), 3),
                    "parent_force": round(force, 3),
                    "parent_montrer": parent.gestes_montrer if parent else 0,
                    "parent_nourrir": parent.gestes_nourrir if parent else 0,
                    "odorat_approche": log.get("Sens_Odorat_Taux_Approche"),
                    "ticks_critiques": log.get("Calibrage_Ticks_Critiques_Ratio"),
                    "autonomie": log.get("Calibrage_Autonomie_Jauges"),
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

    extra = (f", {parent.gestes_montrer} gestes montrer, "
             f"{parent.gestes_nourrir} nourrir") if parent else ""
    print(f"\n✅ {nom} g{a.graine} — palier {etat.niveau_actuel}/{len(N.PROGRAMME)-1}, "
          f"jour {etat.jour} (+{etat.jour-jour_depart} en {(time.time()-t0)/60:.0f} min), "
          f"{etat.victoires_totales} victoires{extra}", flush=True)


if __name__ == "__main__":
    main()
