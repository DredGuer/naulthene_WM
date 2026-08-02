"""
Le Bus Sensoriel Multimodal (v29.0, expérimental) — l'Interpréteur des 5 Sens.

Ce module ne contient AUCUN réseau de neurones et n'importe jamais `naulthene.cerveau.noyau`
(même discipline que `naulthene.exocortex.port_c3` : pas de cycle d'import, pas de
dépendance au cerveau). Il ne fait qu'une chose : lire le monde MiniGrid et le traduire
en signaux normalisés, prêts à être consommés par le cerveau.

Motivation (voir docs/Maj_V29_readme.md) : jusqu'en v28.0, l'agent avait deux sens
« gourmands » (la vue via `porte_visuelle`, l'ouïe via `porte_auditive`) qui possédaient
chacun leur propre couche synaptique, et rien d'autre. Les trois sens restants de la
hiérarchie biologique — toucher, odorat, goût — n'existaient nulle part, alors qu'ils
sont justement les moins coûteux à calculer et les plus directement liés à la survie.

La hiérarchie de gourmandise énergétique implémentée ici suit exactement celle du
document de conception :

| Sens          | Gourmandise | Chemin dans le cerveau                                  |
|---------------|-------------|---------------------------------------------------------|
| Vue           | Extrême     | `porte_visuelle` (147 dims → bus latent), cible JEPA     |
| Ouïe          | Élevée      | `porte_auditive` (130 dims MFCC → bus latent), JEPA audio |
| Toucher       | Moyenne     | 4 dims dans `vecteur_bio` → `integrateur_bio`            |
| Odorat        | Faible      | 2 dims chimiques dans `vecteur_bio`                      |
| Goût          | Faible      | 2 dims chimiques dans `vecteur_bio`                      |

Décision structurante (utilisateur, v29.0) : le toucher et la chimie N'ONT PAS de porte
synaptique dédiée sommée dans le bus latent. Ils entrent par la QUEUE du `vecteur_bio`
(DIM_VECTEUR_BIO passe de 16 à 24), donc par `integrateur_bio`, juste avant la décision.
C'est le choix le moins intrusif pour un cerveau déjà entraîné : les sens faibles ne
polluent jamais la cible JEPA visuelle (`perte_jepa` compare toujours le bus prédit au
bus réel de la vision seule), et un `.brain` existant se greffe par recopie plutôt que de
perdre sa couche (voir `persistance._greffer_vecteur_bio_etendu`).

Dégradation identique aux détecteurs génériques de `noyau.py` §3b : si `_MINIGRID_OK`
est faux ou si l'API MiniGrid change, l'interpréteur se désactive définitivement après UN
avertissement et renvoie des signaux neutres (des zéros) — jamais de crash de
l'entraînement, jamais de changement du chemin de gradient.
"""

import numpy as np

try:
    from minigrid.core.actions import Actions
    _MINIGRID_OK = True
except Exception:
    _MINIGRID_OK = False


# --- Dimensions des sens faibles (FIXES, comme DIM_VOCALE/DIM_ROUTAGE_C3) ---
# Elles ne grandissent JAMAIS avec la neurogenèse : `declencher_neurogenese` les inclut
# dans le segment non-extensible `DIM_VECTEUR_BIO` de `integrateur_bio`.
DIM_TOUCHER = 4   # contact frontal, objet en main, orientation (cos, sin)
DIM_CHIMIE = 4    # odorat (nourriture, eau) + goût (dernière ressource consommée)

# Portée de l'odorat, en cases de la grille (distance de Manhattan). L'odorat est le seul
# sens « à distance » des deux sens chimiques : il décroît linéairement avec la distance
# à la source la plus proche, et vaut 0 au-delà. Volontairement court (4 cases) — c'est
# un signal de survie grossier qui oriente, pas une carte : la cartographie précise reste
# le travail de la vue et de MemoireEpisodiqueSpatiale.
PORTEE_ODORAT = 4.0

# Objets MiniGrid qui « sentent » quelque chose. Réutilise la convention déjà posée par
# DetecteurRessourcesBiologiques (noyau.py §3e) : Ball rouge = Nourriture, Ball bleue =
# Eau. Aucune position ni aucun niveau codé en dur — l'odorat est générique au sens de
# CLAUDE.md §3b, il fonctionne sur n'importe quelle carte du PROGRAMME.
COULEUR_NOURRITURE = "red"
COULEUR_EAU = "blue"


class BusSensoriel:
    """Interpréteur universel des 5 sens : traduit l'état brut de l'environnement en un
    jeu de signaux normalisés dans [0, 1] (ou [-1, 1] pour l'orientation).

    Sans état inter-tick, à une exception près : la trace de goût (`_gout_courant`), qui
    décroît sur quelques ticks après une consommation — un goût est par nature une
    rémanence, pas un instantané. `reinitialiser_episode` la remet à zéro.

    Ne calcule JAMAIS la vue ni l'ouïe : ces deux sens gourmands ont leur propre porte
    synaptique dans `AGI_Naulthene` (`porte_visuelle`, `porte_auditive`) et leurs propres
    encodeurs (`noyau.encoder`, `hemisphere_audio`). Ce bus ne s'occupe que des trois
    sens faibles à moyens, plus la description déclarative de la hiérarchie complète
    (voir `hierarchie_sensorielle`) utilisée par la documentation et la télémétrie.
    """

    # Décroissance de la trace de goût par tick. 0.85 ⇒ un goût reste perceptible ~10
    # ticks après la bouchée, cohérent avec l'ordre de grandeur des jauges du
    # BiologicalHomeostasisEngine (taux_satiete=0.008/tick).
    DECROISSANCE_GOUT = 0.85

    def __init__(self):
        self.actif = _MINIGRID_OK
        self._avertissement_donne = False
        # Trace de goût : [nourriture, eau], décroît à chaque tick.
        self._gout_courant = np.zeros(2, dtype=np.float32)

    def _avertir(self, exception):
        if not self._avertissement_donne:
            print(f"⚠️  Bus sensoriel (toucher/odorat/goût) désactivé "
                  f"(API minigrid incompatible : {exception})")
            self._avertissement_donne = True
        self.actif = False

    def reinitialiser_episode(self, env=None):
        """Le goût ne traverse PAS les épisodes (contrairement aux jauges du
        BiologicalHomeostasisEngine, qui sont un métabolisme continu) : c'est une
        sensation immédiate liée à une bouchée précise, pas un état vital."""
        self._gout_courant[:] = 0.0

    # --- 1. LE TOUCHER (gourmandise moyenne) ---

    def lire_toucher(self, env, action_item=None) -> list:
        """Proprioception + contact, en DIM_TOUCHER=4 dims normalisées :

        - `contact_frontal` : 1.0 si la case devant l'agent est bloquante (mur, ou porte
          fermée/verrouillée), 0.0 sinon. C'est le « je touche quelque chose » brut —
          l'agent sait qu'il est au contact SANS avoir à l'inférer de sa vue.
        - `objet_en_main` : 1.0 si l'agent porte un objet (`carrying`), 0.0 sinon. C'est
          la proprioception de la main : en v28.0, l'agent ne savait qu'il tenait la clé
          qu'indirectement, via le canal visuel.
        - `orientation_cos`, `orientation_sin` : l'orientation de l'agent encodée sur le
          cercle plutôt qu'en entier 0-3. Un encodage circulaire évite la discontinuité
          artificielle entre la direction 3 et la direction 0, qui sont voisines dans le
          monde réel mais distantes de 3 unités en encodage brut.

        Renvoie DIM_TOUCHER zéros si le bus est inactif — signal neutre, jamais d'erreur.
        """
        if not self.actif:
            return [0.0] * DIM_TOUCHER
        try:
            noyau_env = env.unwrapped

            contact_frontal = 0.0
            fx, fy = (int(v) for v in noyau_env.front_pos)
            grille = noyau_env.grid
            if not (0 <= fx < grille.width and 0 <= fy < grille.height):
                contact_frontal = 1.0  # le bord de la grille est toujours un mur
            else:
                objet = grille.get(fx, fy)
                if objet is not None:
                    # `can_overlap()` est l'API MiniGrid native qui dit si l'agent peut
                    # entrer sur la case — vraie pour le sol/but/lave, fausse pour un mur
                    # ou une porte fermée. Plus fiable qu'une liste de types codée en dur.
                    contact_frontal = 0.0 if objet.can_overlap() else 1.0

            objet_en_main = 1.0 if getattr(noyau_env, "carrying", None) is not None else 0.0

            direction = int(noyau_env.agent_dir)
            angle = (np.pi / 2.0) * direction
            return [contact_frontal, objet_en_main,
                    float(np.cos(angle)), float(np.sin(angle))]
        except Exception as e:
            self._avertir(e)
            return [0.0] * DIM_TOUCHER

    # --- 2. L'ODORAT & LE GOÛT (gourmandise faible, signaux chimiques) ---

    def lire_chimie(self, env) -> list:
        """Odorat (à distance) + goût (au contact), en DIM_CHIMIE=4 dims :

        - `odeur_nourriture`, `odeur_eau` : intensité dans [0, 1] de la source la plus
          proche du type correspondant, décroissant linéairement sur PORTEE_ODORAT cases
          (distance de Manhattan, cohérente avec la métrique déjà utilisée par
          `DetecteurJalonsDoorKey._distance` et `MemoireEpisodiqueSpatiale`). 0.0 si
          aucune source à portée.
        - `gout_nourriture`, `gout_eau` : la trace rémanente de la dernière ressource
          effectivement consommée, décroissant à DECROISSANCE_GOUT par tick (voir
          `signaler_consommation`, appelée par la boucle principale au moment exact où
          `BiologicalHomeostasisEngine.consommer_ressource` l'est).

        C'est le canal « signal de survie direct » du document de conception : l'odorat
        oriente vers la ressource avant même de la voir, le goût confirme après coup
        qu'elle a bien été ingérée. Ni l'un ni l'autre n'entre dans la cible JEPA.
        """
        odeurs = [0.0, 0.0]
        if self.actif:
            try:
                noyau_env = env.unwrapped
                grille = noyau_env.grid
                pos_agent = tuple(int(v) for v in noyau_env.agent_pos)
                distances = {COULEUR_NOURRITURE: None, COULEUR_EAU: None}

                for x in range(grille.width):
                    for y in range(grille.height):
                        objet = grille.get(x, y)
                        if objet is None or objet.type != "ball":
                            continue
                        couleur = getattr(objet, "color", None)
                        if couleur not in distances:
                            continue
                        d = abs(x - pos_agent[0]) + abs(y - pos_agent[1])
                        if distances[couleur] is None or d < distances[couleur]:
                            distances[couleur] = d

                for i, couleur in enumerate((COULEUR_NOURRITURE, COULEUR_EAU)):
                    d = distances[couleur]
                    if d is not None and d <= PORTEE_ODORAT:
                        odeurs[i] = float(1.0 - (d / PORTEE_ODORAT))
            except Exception as e:
                self._avertir(e)
                odeurs = [0.0, 0.0]

        return odeurs + [float(self._gout_courant[0]), float(self._gout_courant[1])]

    def signaler_consommation(self, type_ressource: str):
        """Appelée par la boucle principale au moment où l'agent consomme réellement une
        ressource (voir `BiologicalHomeostasisEngine.consommer_ressource`). Met la trace
        de goût correspondante à 1.0 ; elle décroîtra ensuite d'elle-même à chaque appel
        de `decroitre_gout`. Un type inconnu (ex. "STIM", qui ne se goûte pas) est
        silencieusement ignoré."""
        if type_ressource == "FOOD":
            self._gout_courant[0] = 1.0
        elif type_ressource == "WATER":
            self._gout_courant[1] = 1.0

    def decroitre_gout(self):
        """Décroissance de la rémanence gustative, appelée une fois par tick."""
        self._gout_courant *= self.DECROISSANCE_GOUT
        self._gout_courant[self._gout_courant < 1e-3] = 0.0

    # --- 3. L'INTERPRÉTEUR UNIFIÉ ---

    def interpreter(self, env, action_item=None) -> list:
        """Point d'entrée unique : renvoie les DIM_TOUCHER + DIM_CHIMIE = 8 dims des
        sens faibles à moyens, dans l'ordre exact attendu par la queue du `vecteur_bio`
        (voir `BiologicalHomeostasisEngine.obtenir_vecteur_bio`) :

            [contact, objet_en_main, orient_cos, orient_sin,
             odeur_food, odeur_water, gout_food, gout_water]

        L'ordre de cette concaténation est un CONTRAT : il doit rester synchronisé avec
        `obtenir_vecteur_bio` et avec la greffe de rétrocompatibilité de
        `persistance._greffer_vecteur_bio_etendu` (qui recopie les 16 premières dims d'un
        ancien `.brain` et laisse ces 8 nouvelles à leur initialisation). Ne jamais
        insérer une dimension au milieu — toujours ajouter en queue.
        """
        self.decroitre_gout()
        return self.lire_toucher(env, action_item) + self.lire_chimie(env)

    @staticmethod
    def hierarchie_sensorielle() -> dict:
        """Description déclarative de la hiérarchie des 5 sens (coût énergétique relatif
        et chemin d'entrée dans le cerveau). Lecture seule, sans effet de bord : sert la
        documentation, la télémétrie W&B et l'IRM (`instruments/irm_cerveau.py`), jamais
        le chemin de décision — aucune de ces valeurs n'est consommée par `penser()`."""
        return {
            "vue": {"gourmandise": "extreme", "dims": 147,
                    "chemin": "porte_visuelle → bus_latent", "jepa": True},
            "ouie": {"gourmandise": "elevee", "dims": 130,
                     "chemin": "porte_auditive → bus_latent", "jepa": True},
            "toucher": {"gourmandise": "moyenne", "dims": DIM_TOUCHER,
                        "chemin": "vecteur_bio → integrateur_bio", "jepa": False},
            "odorat": {"gourmandise": "faible", "dims": 2,
                       "chemin": "vecteur_bio → integrateur_bio", "jepa": False},
            "gout": {"gourmandise": "faible", "dims": 2,
                     "chemin": "vecteur_bio → integrateur_bio", "jepa": False},
        }
