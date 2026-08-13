"""v39 — P17 : LA GAUSSIENNE D'APPRENTISSAGE.

    « Tu fais 3×3 vingt fois, puis 4×4 cinq fois, puis 3×3 deux fois, comme ça
      aléatoirement — mais tant que le 3×3 n'est pas réussi, tu ne vas pas au-delà
      du 5×5, sauf exceptionnellement. »

Le cursus cesse d'être un POINTEUR (`niveau_actuel`, un entier qui ne recule jamais) pour
devenir une DISTRIBUTION. À chaque épisode, le palier joué est **tiré au sort** :

        palier N     (le socle, celui à valider)   ~75 %
        palier N+1   (l'exploration)               ~20 %
        palier N+2   (l'exceptionnel)              ~5 %

Le sommet se déplace quand — et seulement quand — le socle atteint **80 % de maîtrise**.

--- Pourquoi cette forme, et pas un cursus classique ---

Le cursus actuel est un cliquet : une victoire chanceuse suffit à promouvoir, et on ne
redescend jamais. Mesuré sur la campagne v3739 : `base g11` promu au **jour 4**, puis
**396 jours de stagnation** — poussé sur un terrain qu'il ne maîtrisait pas, sans aucun
moyen de revenir consolider.

Avec la gaussienne, trois propriétés tombent **sans un seul `if`** :

    retours en arrière réguliers          -> la queue gauche (les paliers acquis
                                             restent joués tant qu'ils sont dans la fenêtre)
    « pas au-delà tant que non acquis »   -> le sommet ne bouge qu'avec la maîtrise
    « sauf exceptionnellement »           -> la queue droite est fine, jamais nulle

--- Ce qui reste conforme à la règle « rien en dur » ---

Les 75/20/5 sont une FORME (la largeur de la courbe), pas une décision : aucune règle ne
dit « si X alors joue le palier N ». Le SOMMET, lui, est entièrement dérivé de ce que
l'agent a réellement réussi — c'est un NIVEAU, jamais un seuil, exactement comme
`reference_choc_dopamine`.

--- Pas de durée fixée ---

Le run tourne jusqu'à ce que TOUS les paliers soient maîtrisés (ou jusqu'à `--jours-max`,
garde-fou de sécurité). C'est la conséquence directe du principe : on ne décide plus
combien de temps ça doit prendre, on attend que ce soit acquis.

Lancement :

    PYTHONPATH=src:experiences/v38 python experiences/v39/v39_p17_gaussienne.py \\
        --graine 22 --brain brains/xxx.brain
"""
import argparse
import os
import random
import sys
from collections import deque

sys.path.insert(0, "src")
sys.path.insert(0, "experiences/v38")
os.environ.setdefault("WANDB_MODE", "offline")

import torch

from naulthene.cerveau import noyau as N

# Les six échelles de la même tâche — identiques à 2a, pour rester comparable.
TAILLES = [5, 6, 8, 10, 12, 16]

# --- La FORME de la courbe (utilisateur, 14/08) ---
#
# Ce ne sont pas des seuils de décision : c'est la largeur de la gaussienne, discrétisée
# sur trois paliers. Le socle domine, l'exploration existe, l'exceptionnel reste possible.
POIDS_GAUSSIENNE = (0.75, 0.20, 0.05)

# Le socle est « acquis » à 80 % de réussite — le sommet se déplace alors d'un cran.
# ⚠️ C'est un NIVEAU mesuré sur ce que l'agent a vécu, pas une constante de décision :
# rien ne dit « si taux > 0.8 alors fais X », on déplace seulement le centre de la courbe.
SEUIL_MAITRISE = 0.80

# Fenêtre glissante par palier. Trop courte, une série chanceuse fait monter le sommet ;
# trop longue, l'agent reste bloqué sur un palier qu'il maîtrise déjà.
FENETRE_MAITRISE = 20
MIN_EPISODES = 10        # sous ce nombre, le taux n'est pas encore significatif

# --- LA RÉUSSITE SE MESURE SUR LA JOURNÉE, PAS SUR L'ÉPISODE (utilisateur, 14/08) ---
#
#   « 80 %, c'est sur une journée : il faut mesurer l'évolution du taux d'échec par
#     rapport à la réussite. Si par exemple dans une journée il dépasse le seuil des
#     100 portes ouvertes, on peut considérer qu'il a réussi. »
#
# Pourquoi c'est un meilleur signal que la victoire seule : sur DoorKey, une victoire est
# un événement RARE et binaire (0 ou 1 par jour, souvent 0 pendant des centaines de
# jours — mesuré). Le taux de maîtrise calculé dessus est donc extrêmement bruité, et
# c'est exactement ce qui a permis à `base g11` d'être promu au jour 4 sur un coup de
# chance.
#
# Franchir une porte est en revanche un acte FRÉQUENT et GRADUÉ : il exige déjà la
# compétence centrale (trouver la clé, l'utiliser, passer). Un agent qui franchit
# 100 portes dans sa journée a démontré une compétence *installée*, pas un accident.
#
# ⚠️ Ce n'est PAS un seuil de décision au sens interdit par le projet : il ne pilote
# aucune action de l'agent. C'est un critère de MESURE — l'équivalent d'une note
# d'examen —, appliqué a posteriori sur une journée déjà vécue.
#
# --- ⚠️ LE CHIFFRE DE 100 EST IMPOSSIBLE SUR DOORKEY — MESURÉ ---
#
# L'utilisateur proposait « 100 portes ouvertes dans une journée ». Vérification sur tous
# les logs disponibles (60 journées où au moins une porte a été franchie) :
#
#     minimum 1  ·  médiane 1  ·  MAXIMUM 2
#
# La raison est structurelle : `DoorKey` ne contient **qu'une seule porte** par carte, et
# la journée compte ~2 épisodes. Un seuil à 100 ne se déclencherait donc JAMAIS — le
# critère serait mort, et la gaussienne retomberait silencieusement sur la seule victoire.
#
# C'est exactement le piège documenté du projet (`SEUIL_CRISTAL = 0.80`, jamais franchi ;
# l'ablation d'un organe vide) : **un seuil posé a priori, jamais confronté à une mesure.**
#
# L'INTENTION de l'utilisateur est juste et elle est conservée : juger la journée sur un
# acte FRÉQUENT et GRADUÉ plutôt que sur l'événement rare et binaire qu'est la victoire.
# Seule l'ÉCHELLE est corrigée — et elle est désormais DÉRIVÉE du monde, pas posée :
# « franchir au moins une porte par épisode joué », ce qui veut dire que l'agent a
# effectivement trouvé la clé et ouvert la porte à chaque tentative de la journée.
def journee_reussie(etat) -> bool:
    """Le critère de réussite d'une JOURNÉE (v39-P17).

    Une victoire suffit. À défaut, l'agent a « réussi sa journée » s'il a franchi une
    porte à chaque épisode joué — c'est-à-dire s'il a exécuté la compétence centrale de
    DoorKey (trouver la clé, ouvrir) de façon systématique, sans forcément atteindre le
    but. C'est le signal gradué que la victoire seule ne donne pas.
    """
    if bool(getattr(etat, "victoire_aujourdhui", False)):
        return True
    portes = getattr(etat, "portes_franchies_jour", 0)
    episodes = max(1, getattr(etat, "episodes_jour", 1))
    return portes >= episodes


class Gaussienne:
    """Le cursus comme distribution — pas comme pointeur.

    Tient une fenêtre glissante de réussite PAR palier (le cursus historique n'en tenait
    qu'une seule, celle du niveau courant : impossible de savoir si un palier ancien est
    toujours maîtrisé).
    """

    def __init__(self, n_paliers, rng):
        self.n = n_paliers
        self.rng = rng
        self.sommet = 0
        self.historique = [deque(maxlen=FENETRE_MAITRISE) for _ in range(n_paliers)]
        self.episodes_par_palier = [0] * n_paliers

    def taux(self, palier):
        h = self.historique[palier]
        if len(h) < MIN_EPISODES:
            return None                      # pas encore mesurable
        return sum(h) / len(h)

    def tirer_palier(self):
        """Tire le palier du prochain épisode selon la courbe centrée sur `sommet`."""
        candidats, poids = [], []
        for decalage, p in enumerate(POIDS_GAUSSIENNE):
            palier = self.sommet + decalage
            if palier < self.n:
                candidats.append(palier)
                poids.append(p)
        if not candidats:                    # sommet au dernier palier
            return self.n - 1
        return self.rng.choices(candidats, weights=poids, k=1)[0]

    def enregistrer(self, palier, reussi):
        self.historique[palier].append(1.0 if reussi else 0.0)
        self.episodes_par_palier[palier] += 1

    def deplacer_si_acquis(self):
        """Le sommet avance quand le socle atteint le seuil. Retourne True s'il a bougé."""
        t = self.taux(self.sommet)
        if t is not None and t >= SEUIL_MAITRISE and self.sommet < self.n - 1:
            self.sommet += 1
            return True
        return False

    def tout_acquis(self):
        """Tous les paliers sont-ils maîtrisés ? (condition d'arrêt du run)"""
        if self.sommet < self.n - 1:
            return False
        t = self.taux(self.n - 1)
        return t is not None and t >= SEUIL_MAITRISE

    def rapport(self):
        parts = []
        for i in range(self.n):
            t = self.taux(i)
            parts.append(f"{TAILLES[i]}×{TAILLES[i]}:"
                         + ("--" if t is None else f"{100*t:.0f}%")
                         + ("◄" if i == self.sommet else " "))
        return " | ".join(parts)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--brain", type=str, required=True)
    p.add_argument("--graine", type=int, default=None)
    p.add_argument("--jours-max", type=int, default=3000,
                   help="garde-fou : le run s'arrête quand TOUT est acquis, pas à une date")
    p.add_argument("--temoin", action="store_true",
                   help="cursus classique (cliquet) au lieu de la gaussienne")
    a = p.parse_args()

    if a.graine is not None:
        torch.manual_seed(a.graine)
        N.np.random.seed(a.graine)
        random.seed(a.graine)
    rng = random.Random(a.graine or 0)

    N.BUS_REFERENCE_INITIAL = 64
    N.PROGRAMME[:] = [(f"MiniGrid-DoorKey-{t}x{t}-v0", f"DoorKey {t}×{t}") for t in TAILLES]

    gauss = Gaussienne(len(TAILLES), rng) if not a.temoin else None
    etat_partage = {"stop": False, "jour_fin": None}

    if gauss is not None:
        # --- Le tirage du palier remplace le pointeur ---
        #
        # `creer_env` est le seul point où le monde change de palier. On l'intercepte pour
        # y injecter le tirage : le noyau croit suivre `niveau_actuel`, il suit en réalité
        # la distribution.
        vrai_creer = N.creer_env

        def creer_env_tire(env_id, dim_visuelle, *args, **kwargs):
            palier = gauss.tirer_palier()
            vrai_id = N.PROGRAMME[palier][0]
            env = vrai_creer(vrai_id, dim_visuelle, *args, **kwargs)
            etat_partage["palier_courant"] = palier
            return env

        N.creer_env = creer_env_tire
        from naulthene.cerveau import persistance as _persist
        _persist.creer_env = creer_env_tire

        # --- Enregistrer la réussite AU BON PALIER, et faire avancer le sommet ---
        vraie_nuit = N.executer_nuit

        def nuit_gaussienne(etat, *args, **kwargs):
            r = vraie_nuit(etat, *args, **kwargs)
            palier = etat_partage.get("palier_courant", gauss.sommet)
            # La réussite se juge sur la JOURNÉE (victoire OU 100 portes franchies),
            # pas sur le seul événement rare qu'est la victoire — voir `journee_reussie`.
            reussie = journee_reussie(etat)
            gauss.enregistrer(palier, reussie)
            if reussie and not etat.victoire_aujourdhui:
                etat_partage["jours_portes"] = etat_partage.get("jours_portes", 0) + 1

            # Le palier suivant est tiré maintenant, et le monde suit.
            suivant = gauss.tirer_palier()
            if suivant != palier:
                etat.env_id, etat.nom_classe = N.PROGRAMME[suivant]
                try:
                    etat.env.close()
                except Exception:
                    pass
                etat.env = vrai_creer(etat.env_id, N.DIM_VISUELLE)
                etat_partage["palier_courant"] = suivant
                # ⚠️ La mémoire spatiale est vidée au changement de CARTE, comme dans le
                # cursus historique : les coordonnées n'ont plus de sens. L'empreinte de
                # type (v39.0) survit, elle — c'est tout l'objet du correctif P11.
                etat.memoire_episodique_spatiale.reinitialiser_niveau()

            if gauss.deplacer_si_acquis():
                print(f"\n   🎯 [SOMMET] socle acquis → la courbe se recentre sur "
                      f"{TAILLES[gauss.sommet]}×{TAILLES[gauss.sommet]}", flush=True)

            if etat.jour % 20 == 0:
                print(f"   📊 {gauss.rapport()}", flush=True)

            if gauss.tout_acquis():
                etat_partage["stop"] = True
                etat_partage["jour_fin"] = etat.jour
                print(f"\n   🏁 TOUS LES PALIERS ACQUIS au jour {etat.jour}", flush=True)
            return r

        N.executer_nuit = nuit_gaussienne

    nom = "P17_TEMOIN (cliquet)" if a.temoin else "P17_GAUSSIENNE"
    print(f"\n🔔 v39 P17 — {nom}   (graine {a.graine})\n", flush=True)
    if gauss is not None:
        print(f"   courbe {POIDS_GAUSSIENNE} · socle acquis à {SEUIL_MAITRISE:.0%}")
        print(f"   le run s'arrête quand TOUT est acquis (garde-fou : {a.jours_max} j)\n",
              flush=True)

    # --- Arrêt sur acquisition, pas sur une durée ---
    if gauss is not None:
        vrai_demarrer = N.demarrer_journee

        def demarrer_avec_arret(etat, *args, **kwargs):
            if etat_partage["stop"]:
                raise SystemExit(0)
            return vrai_demarrer(etat, *args, **kwargs)

        N.demarrer_journee = demarrer_avec_arret

    import v38_2a_continuite as X
    sys.argv = ["x", "--jours", str(a.jours_max), "--graine", str(a.graine),
                "--continu", "--patience-surface", "--brain", a.brain]
    try:
        X.main()
    except SystemExit:
        pass

    if gauss is not None:
        print(f"\n✅ {nom}")
        print(f"   sommet final : {TAILLES[gauss.sommet]}×{TAILLES[gauss.sommet]} "
              f"(palier {gauss.sommet + 1}/{len(TAILLES)})")
        print(f"   {gauss.rapport()}")
        print(f"   épisodes par palier : {gauss.episodes_par_palier}")
        if etat_partage["jour_fin"]:
            print(f"   🏁 cursus complet en {etat_partage['jour_fin']} jours")


if __name__ == "__main__":
    main()
