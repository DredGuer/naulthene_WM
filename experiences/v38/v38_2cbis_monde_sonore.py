"""v38 — ÉTAPE 2c-bis : LE MONDE SONORE (sans parent, sans assistance).

Pourquoi cette étape existe — le problème que 2c a créé.

2c a produit la première co-occurrence vue↔ouïe de l'histoire du projet (0 → 0,24), mais
**au prix de 1 à 2 paliers** :

    2c parent nourricier : 0/5 vs 2b, les SIX graines figees au palier 1
    2c-fix montrer seul  : 1/5 vs 2b, paliers medians 2,0 contre 3,0

Conséquence méthodologique : **2d (le liage) n'est pas interprétable sur cette pile.** Un
résultat nul ne permettrait pas de distinguer « le liage n'apporte rien » de « le parent a
annulé l'apport du liage ». On mesurerait deux effets de signe opposé avec un seul chiffre.

--- Le principe de cette étape ---

Le son ne vient plus d'un assistant, il vient **du monde lui-même** : un objet dans le champ
de vision de l'agent émet son propre timbre. Personne ne montre, personne ne nourrit,
personne ne décide à la place de l'agent.

C'est la traduction du fil conducteur mesuré sur trois jours :

    Ce qui REND POSSIBLE fait progresser  (la continuité : +1,5 palier)
    Ce qui FACILITE ne change rien        (la densité : effet nul)
    Ce qui FAIT A LA PLACE fait regresser (le parent : -2 paliers)

Un objet qui sonne rend possible l'association sans rien faciliter : l'agent doit toujours
chercher, sentir, mémoriser et atteindre le but par lui-même. Le son est une **propriété du
monde**, pas un service rendu.

--- ⚠️ Rien n'est expliqué en dur ---

Le timbre d'un type est ARBITRAIRE et OPAQUE (mêmes vecteurs formantiques qu'en 2c). Le
cerveau ne reçoit jamais « ceci est une clé » : il reçoit un MFCC qui co-occurre avec une
forme visuelle. Le lien reste à apprendre, jamais déclaré.

--- Ce qui est mesuré ---

  Cooc_Vue_Ouie   doit rester ~0,2-0,3 (le niveau atteint en 2c)
  paliers         doivent rester au niveau de 2b (3,0), pas retomber a 2,0

Si les deux tiennent, la co-occurrence est obtenue SANS son coût, et 2d devient mesurable.

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
def _charger(nom, fichier):
    s = _ilu.spec_from_file_location(nom, _os.path.join(_d, fichier))
    m = _ilu.module_from_spec(s); s.loader.exec_module(m); return m
_m2a = _charger("v38_2a", "v38_2a_continuite.py")
_m2b = _charger("v38_2b", "v38_2b_permanence.py")
_m2c = _charger("v38_2c", "v38_2c_parent.py")

_grille_de = _m2a._grille_de
installer_continuite = _m2a.installer_continuite
densite_pour = _m2b.densite_pour
VOCABULAIRE = _m2c.VOCABULAIRE          # mêmes timbres qu'en 2c, pour rester comparable

# Portée du son, en distance de Manhattan. Une BORNE, pas un seuil de décision : elle
# décrit une propriété physique du monde (le son s'atténue), au même titre que
# l'atténuation olfactive. Mesuré au smoke test : sans elle, 100 % des ticks sont
# sonores et le silence — donc l'information — disparaît.
PORTEE_SONORE = 2


class MondeSonore:
    """Chaque objet émet son timbre quand il est dans le champ de vision de l'agent.

    Différence essentielle avec le parent de 2c : cette entité **n'agit pas**. Elle ne se
    déplace pas, ne désigne rien, ne dépose rien. Elle ne fait qu'ajouter une propriété
    perceptible au monde — comme l'odeur, qui n'a jamais rien fait à la place de l'agent.
    """

    def __init__(self, rng):
        self.rng = rng
        self.synth = SynthetiseurFormants()
        self._mfcc = {}
        self.ticks_sonores = 0
        self.ticks_silence = 0

    def mfcc_de(self, type_objet):
        if type_objet not in self._mfcc:
            v = VOCABULAIRE.get(type_objet)
            if v is None:
                return None
            onde = self.synth.synthetiser(v)
            self._mfcc[type_objet] = np.asarray(
                extraire_mfcc(onde, SAMPLE_RATE), dtype=np.float32).reshape(-1)
        return self._mfcc[type_objet]

    def ecouter(self, e):
        """Le son du monde à ce tick, ou None (silence).

        L'objet le plus proche DANS LE CHAMP de vision émet. S'il n'y a rien à voir, il
        n'y a rien à entendre — et ce silence est informatif : c'est ce qui permet à la
        présence du son de prédire quelque chose.
        """
        ax, ay = int(e.agent_pos[0]), int(e.agent_pos[1])
        r = getattr(e, "agent_view_size", 7) // 2
        visibles = []
        for x in range(max(0, ax - r), min(e.grid.width, ax + r + 1)):
            for y in range(max(0, ay - r), min(e.grid.height, ay + r + 1)):
                t = type(e.grid.get(x, y)).__name__
                if t in VOCABULAIRE:
                    visibles.append((abs(x - ax) + abs(y - ay), t))
        # ⚠️ Corrigé au smoke test : sans la contrainte de PORTÉE ci-dessous, le son est
        # émis à 100 % des ticks (mesuré : 400 sonores / 0 silencieux) — une porte est
        # presque toujours dans le champ. Un signal permanent est un bruit de fond : il ne
        # peut rien prédire puisqu'il est toujours là. C'est exactement le piège rencontré
        # en 2c avec le parent, sous une autre forme.
        #
        # La portée est le pendant auditif de l'atténuation olfactive : un son proche
        # s'entend, un son lointain se perd. Le silence redevient donc informatif.
        visibles = [(d, t) for d, t in visibles if d <= PORTEE_SONORE]
        if not visibles:
            self.ticks_silence += 1
            return None
        visibles.sort()
        self.ticks_sonores += 1
        return self.mfcc_de(visibles[0][1])


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--jours", type=int, default=600)
    p.add_argument("--brain", type=str, required=True)
    p.add_argument("--graine", type=int, default=None)
    p.add_argument("--densite", type=float, default=3.0)
    p.add_argument("--monde-sonore", action="store_true",
                   help="les objets emettent ; sans ce flag = TEMOIN (= pile 2b)")
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

    nom = "2cbis_SONORE" if a.monde_sonore else "2cbis_TEMOIN"
    print(f"\n🔔 v38 ÉTAPE 2c-bis — {nom}   (graine {a.graine})\n", flush=True)
    print("   pile : continuité (2a) + densité (2b)"
          + (" + monde sonore (2c-bis)" if a.monde_sonore else ""))
    if a.monde_sonore:
        print("   le son vient du MONDE, pas d'un assistant :")
        print("   aucun geste, aucune aide — une propriété perceptible de plus")
    print(flush=True)

    from naulthene.audio.lecons_vocales import CacheReferencesVocales
    from naulthene.cerveau.persistance import PersistanceAnatomique
    from naulthene.salles_de_classe.cursus_developpemental import _perception_du_tick

    persistance = PersistanceAnatomique(a.brain)
    etat = persistance.charger_ou_naitre()
    cache = CacheReferencesVocales()
    rng = random.Random(7 if a.graine is None else 7 + a.graine)
    stats = {"continuations": 0, "resets_secours": 0}
    monde = MondeSonore(rng) if a.monde_sonore else None

    if not a.no_wandb:
        wandb.init(project="Naulthene-AGI", name=f"V38_{nom}_g{a.graine}_{a.jours}j",
                   config={"etape": "2cbis", "monde_sonore": a.monde_sonore,
                           "densite": a.densite, "graine": a.graine, "continu": True})

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

            cases, cooc = set(), 0
            ere = N.ere_courante(etat.jour)
            for tick in range(N.ticks_par_jour):
                moment = "matin" if tick < N.TICKS_MATIN else "apres_midi"
                mode, obs_aud, formants = _perception_du_tick(
                    etat, cache, ere, moment, derniere_action)

                if monde is not None and mode == "minigrid":
                    try:
                        e = _grille_de(etat.env)
                        m = monde.ecouter(e)
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
            log.update({"Etape": "2cbis", "Monde_Sonore": int(a.monde_sonore),
                        "Palier_Difficulte": etat.niveau_actuel,
                        "Reperes_N": len(sv), "Confirmations_Moyennes": conf,
                        "Continu_Cases_Distinctes_Jour": len(cases),
                        "Cooc_Vue_Ouie": cooc / max(1, N.TICKS_MATIN)})
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
                    "odorat_approche": log.get("Sens_Odorat_Taux_Approche"),
                    "ticks_critiques": log.get("Calibrage_Ticks_Critiques_Ratio"),
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

    extra = (f", {monde.ticks_sonores} ticks sonores / {monde.ticks_silence} silencieux"
             if monde else "")
    print(f"\n✅ {nom} g{a.graine} — palier {etat.niveau_actuel}/{len(N.PROGRAMME)-1}, "
          f"jour {etat.jour} (+{etat.jour-jour_depart} en {(time.time()-t0)/60:.0f} min), "
          f"{etat.victoires_totales} victoires{extra}", flush=True)


if __name__ == "__main__":
    main()
