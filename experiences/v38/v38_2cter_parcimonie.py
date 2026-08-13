"""v38 — ÉTAPE 2c-ter : LE SON PARCIMONIEUX, VARIABLE, ET LE VRAI SILENCE.

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

--- Les trois corrections de cette étape (remarques utilisateur) ---

2c-bis a échoué : 120 200 ticks sonores / 0 silencieux. Le son était permanent, donc
inutile. Trois causes distinctes, trois corrections.

  (1) LA SATURATION PAR LA DENSITÉ. `Ball` était dans le vocabulaire, et l'étape 2b en
      sème des dizaines (29 par carte en 16×16) : il y avait TOUJOURS une ressource à
      portée. Mes deux étapes se contredisaient. Seuls les objets RARES et STRUCTURANTS
      (clé, porte, but) sonnent désormais ; la nourriture omniprésente reste muette — ce
      qui est d'ailleurs plus juste, elle a déjà l'odorat pour elle.

  (2) LE TIMBRE FIGÉ.

          « Il y a autant de variations, de possibilités et d'états pour le dire. Chaque
            variation nourrit les précédentes. Je pense que c'est ce qui permet
            d'appréhender un nouveau son qui ressemble. »

      4 timbres strictement identiques ne permettent AUCUNE généralisation : la même clé
      produisait exactement le même MFCC, pour toujours. Un agent ne peut alors construire
      qu'une table de correspondance — et rien ne permettrait de la distinguer d'un
      concept. C'est exactement la limite que `les_sens_combinatoire.md` §7.6 pose pour la
      VISION dans MiniGrid... que j'avais reproduite dans le canal auditif alors que rien
      ne m'y obligeait : le son, contrairement aux pixels, je le fabrique.

      Chaque émission varie donc autour de son prototype. Vérifié : variance intra-type
      2,909 contre distance inter-type 6,201, soit un ratio de 2,1× — les types restent
      distinguables MALGRÉ la variance, ce qui est la condition pour qu'il y ait quelque
      chose à généraliser.

  (3) LA PARCIMONIE, ET LE VRAI SILENCE.

          « Le cerveau est fait pour être stimulé, mais finit par perdre de l'information
            s'il l'est trop, surtout dans ses débuts. Trop de son, rien ne passe ; pas
            assez, rien ne s'établit. »
          « Le silence n'est pas 0, le silence est quand il y a presque plus rien à
            établir. »

      ⚠️ Cette dernière remarque corrige un défaut RÉEL du code, pas seulement de mon
      banc d'essai. Dans `noyau.py:548-552`, `obs_auditive=None` ne produit pas un
      silence : le terme DISPARAÎT de la somme du bus latent. La norme du bus change,
      donc l'échelle d'activation de tout l'aval (hippocampe, analyseur, tête motrice).
      Le cerveau ne perçoit pas le calme — il perd le canal, silencieusement.

      C'est le défaut annoncé dans `les_sens_combinatoire.md` §4.3 : « absent » et « nul »
      sont indistinguables. Ici le silence devient donc un son de très faible amplitude,
      PERÇU (distance mesurée au timbre plein : 3,71, non nulle) plutôt qu'absent.

      La parcimonie, elle, est obtenue par une période de rafraîchissement : un objet ne
      re-sonne pas à chaque tick. Entre deux émissions, le monde est calme — et c'est ce
      calme qui rend l'émission suivante informative.

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
# Seuls les objets RARES et STRUCTURANTS sonnent. `Ball` (la nourriture) est
# délibérément ABSENT : l'étape 2b en sème des dizaines, il saturait le canal.
VOCABULAIRE = {k: v for k, v in _m2c.VOCABULAIRE.items() if k != "Ball"}

# Écart-type de la variation d'un timbre autour de son prototype. Une BORNE : la valeur
# réelle est tirée à chaque émission. Mesuré : ratio inter/intra = 2,1x, donc les types
# restent distinguables malgré la variance.
VARIANCE_TIMBRE = 0.04

# Nombre de ticks pendant lesquels un objet déjà entendu se tait. C'est la parcimonie :
# sans elle, 100 % des ticks sont sonores et plus rien ne passe.
PERIODE_SILENCE = 6

# Amplitude du quasi-silence. JAMAIS 0, et surtout jamais `None` : voir la docstring (3).
AMPLITUDE_SILENCE = 0.05

# Portée du son, en distance de Manhattan. Une BORNE, pas un seuil de décision : elle
# décrit une propriété physique du monde (le son s'atténue), au même titre que
# l'atténuation olfactive. Mesuré au smoke test : sans elle, 100 % des ticks sont
# sonores et le silence — donc l'information — disparaît.
PORTEE_SONORE = 2          # portée plancher, sur la plus petite carte (5×5)
DIVISEUR_PORTEE = 1.5      # portée = côté / 1.5 — calibré par mesure, voir portee_pour()

def portee_pour(e):
    """Portée du son, PROPORTIONNELLE à la carte — jamais fixe.

    ⚠️ Mesuré : une portée fixe de 2 donne 34 % de son sur 5×5 mais **0 %** sur 8×8 et
    16×16. L'agent n'approche presque jamais la clé ou la porte à moins de 2 cases sur
    une grande carte, donc le canal se tait entièrement — l'excès inverse de 2c-bis.

    C'est la même erreur d'échelle que la patience (corrigée en A3) et que la densité de
    ressources (corrigée en 2b) : une constante calibrée sur la plus petite carte ne
    transpose pas. La portée suit donc le côté de la grille.

    Le diviseur a été CALIBRÉ PAR MESURE, jamais posé — balayage sur 4 tailles de carte
    x 4 diviseurs, 400 ticks chacun, à densité 2b réelle. Taux de ticks sonores :

        diviseur    5x5    8x8   12x12  16x16
           /3       33 %    8 %    0 %    3 %     trop rare, le canal se tait
           /2       33 %    4 %    3 %   18 %     idem
        >> /1.5     38 %   27 %   30 %   25 %     équilibré partout
           /1       36 %   50 %   40 %   48 %     trop dense, retour au bruit de fond
    """
    cote = max(getattr(e.grid, "width", 8), getattr(e.grid, "height", 8))
    return max(PORTEE_SONORE, round(cote / DIVISEUR_PORTEE))


class MondeSonore:
    """Chaque objet émet son timbre quand il est dans le champ de vision de l'agent.

    Différence essentielle avec le parent de 2c : cette entité **n'agit pas**. Elle ne se
    déplace pas, ne désigne rien, ne dépose rien. Elle ne fait qu'ajouter une propriété
    perceptible au monde — comme l'odeur, qui n'a jamais rien fait à la place de l'agent.
    """

    def __init__(self, rng):
        self.rng = rng
        self.synth = SynthetiseurFormants()
        self._mfcc_silence = None
        self._derniere_emission = {}
        self._tick = 0
        self.ticks_sonores = 0
        self.ticks_silence = 0

    def mfcc_de(self, type_objet):
        """Une PRISE du timbre de ce type — jamais deux fois la même.

        Le prototype est fixe, la réalisation varie. C'est ce qui donne à l'agent quelque
        chose à généraliser : reconnaître un son « qui ressemble » suppose d'en avoir
        entendu plusieurs versions différentes.
        """
        v = VOCABULAIRE.get(type_objet)
        if v is None:
            return None
        bruit = self.rng.gauss
        vec = [min(0.98, max(0.02, x + bruit(0.0, VARIANCE_TIMBRE))) for x in v]
        return np.asarray(extraire_mfcc(self.synth.synthetiser(vec), SAMPLE_RATE),
                          dtype=np.float32).reshape(-1)

    def _quasi_silence(self):
        """Le silence PERÇU : un son de très faible amplitude, jamais `None`.

        ⚠️ Point corrigé ici, et c'est un défaut du noyau autant que du banc d'essai :
        `obs_auditive=None` fait DISPARAÎTRE le terme auditif de la somme du bus
        (`noyau.py:548-552`). La norme du bus change, donc l'échelle de tout l'aval. Le
        cerveau ne perçoit alors pas le calme — il perd le canal.

        « Le silence n'est pas 0, le silence est quand il y a presque plus rien à
          établir. » Le silence est donc ici un signal de faible intensité, mis en cache
        une fois pour toutes (il ne varie pas : c'est le fond, pas un événement).
        """
        if self._mfcc_silence is None:
            v = list(next(iter(VOCABULAIRE.values())))
            v[7] = AMPLITUDE_SILENCE
            self._mfcc_silence = np.asarray(
                extraire_mfcc(self.synth.synthetiser(v), SAMPLE_RATE),
                dtype=np.float32).reshape(-1)
        return self._mfcc_silence

    def ecouter(self, e):
        """Le son du monde à ce tick : une émission, ou le quasi-silence.

        Trois filtres successifs, chacun corrigeant un mode de saturation mesuré :
          - la PORTÉE   : un objet lointain ne s'entend pas
          - le VOCABULAIRE : la nourriture omniprésente est muette (2b la sème par
                             dizaines et saturait le canal)
          - la PARCIMONIE : un objet déjà entendu se tait `PERIODE_SILENCE` ticks
        """
        self._tick += 1
        ax, ay = int(e.agent_pos[0]), int(e.agent_pos[1])
        portee = portee_pour(e)
        proches = []
        for x in range(max(0, ax - portee), min(e.grid.width, ax + portee + 1)):
            for y in range(max(0, ay - portee), min(e.grid.height, ay + portee + 1)):
                t = type(e.grid.get(x, y)).__name__
                if t in VOCABULAIRE and abs(x - ax) + abs(y - ay) <= portee:
                    proches.append((abs(x - ax) + abs(y - ay), x, y, t))
        proches.sort()

        for _d, x, y, t in proches:
            dernier = self._derniere_emission.get((x, y))
            if dernier is not None and self._tick - dernier < PERIODE_SILENCE:
                continue                      # cet objet vient de sonner : il se tait
            self._derniere_emission[(x, y)] = self._tick
            self.ticks_sonores += 1
            return self.mfcc_de(t)

        self.ticks_silence += 1
        return self._quasi_silence()


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

    nom = "2cter_PARCIMONIE" if a.monde_sonore else "2cter_TEMOIN"
    print(f"\n🔔 v38 ÉTAPE 2c-ter — {nom}   (graine {a.graine})\n", flush=True)
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
                   config={"etape": "2cter", "monde_sonore": a.monde_sonore,
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
                        avant = monde.ticks_sonores
                        m = monde.ecouter(e)
                        if m is not None:
                            obs_aud = torch.tensor([m], dtype=torch.float32,
                                                   device=N.DEVICE)
                            # ⚠️ Depuis que le silence est un SIGNAL (et non `None`), le
                            # test « m is not None » est toujours vrai : il ne mesurerait
                            # plus que la présence du canal. On ne compte donc que les
                            # vraies ÉMISSIONS, celles qui portent le timbre d'un objet.
                            if monde.ticks_sonores > avant:
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
            log.update({"Etape": "2cter", "Monde_Sonore": int(a.monde_sonore),
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
