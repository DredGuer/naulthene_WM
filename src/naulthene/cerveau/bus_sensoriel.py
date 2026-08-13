"""
Le Bus Sensoriel Multimodal (v29.0, expérimental) — l'Interpréteur des 5 Sens.

Ce module ne contient AUCUN réseau de neurones et n'importe jamais `naulthene.cerveau.noyau`
(même discipline que `naulthene.exocortex.port_c3` : pas de cycle d'import, pas de
dépendance au cerveau). Il ne fait qu'une chose : lire le monde MiniGrid et le traduire
en signaux normalisés, prêts à être consommés par le cerveau.

Motivation (voir docs/ameliorations_appliquees/Maj_V29_readme.md) : jusqu'en v28.0, l'agent avait deux sens
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
| **Exo-Sens**  | *Externe*   | 8 dims dans `vecteur_bio` (v30.0, voir ci-dessous)       |

v30.0 — **le 6ème sens (l'Exo-Sens)**. L'Exocortex C3 cesse d'être un « 3ème cerveau »
qu'on interroge via une action apprise pour devenir un **canal perceptif exogène** : le
monde numérique (LLM/RAG, bases vectorielles, APIs, capteurs IoT) est *senti* en continu,
exactement comme le toucher. L'agent n'a plus à décider de demander ; c'est
`integrateur_bio` qui apprend seul, par myélinisation, quelle attention accorder à ces
dimensions — du bruit verra ses poids tomber vers 0, une information utile les verra se
renforcer. Aucun `if` de déclenchement n'existe dans le chemin de décision, cohérent avec
les refus posés en v28 (seuil pour C3) et v29 (court-circuit C1→C2). Sans plug branché,
le vecteur est nul et le comportement est strictement celui de la v29.1.

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
DIM_EXO = 8       # v30.0 — le 6ème sens, l'Exo-Sens (vecteur perceptif exogène)

# v32.0 — LA CLINOTAXIE : la VARIATION de l'odeur entre deux ticks (food, eau).
#
# Jusqu'ici `integrateur_bio` ne recevait que l'intensité instantanée S_t, sans aucun
# état interne lui permettant d'en dériver quoi que ce soit : le réseau était donc
# structurellement AVEUGLE AU MOUVEMENT. Il ne pouvait pas savoir si le dernier pas
# l'avait rapproché ou éloigné d'une ressource — une information que même un ver
# nématode exploite (la clinotaxie : comparer la concentration courante à la précédente
# et virer en conséquence).
#
# C'est particulièrement décisif sur les petites cartes, là où le diagnostic v29.1 avait
# montré que l'odorat ne servait à rien : sur `DoorKey-6x6`, S_t reste dans une plage
# étroite d'une case à l'autre, mais le SIGNE de ΔS bascule proprement à chaque pas.
# Le gradient existe dans le monde depuis la v30.0 ; ce sont ces 2 dims qui le rendent
# enfin LISIBLE par le cerveau.
#
# Ajoutées EN QUEUE du vecteur bio (contrat append-only), donc hors cible JEPA : la
# variation olfactive nourrit C1 (`integrateur_bio`), jamais le modèle du monde de C2.
DIM_ODORAT_DELTA = 2

# --- ODORAT : atténuation exponentielle de proximité (v30.0) ---
#
# En v29.x, l'odorat décroissait LINÉAIREMENT sur une portée fixe de 4 cases
# (`PORTEE_ODORAT = 4.0`). La télémétrie v29.1 a montré que ce réglage saturait : 97,6 %
# de couverture sur Empty-8x8 et 100 % sur DoorKey-6x6 — un signal presque toujours actif
# porte très peu d'information, et l'agent ne pouvait pas s'en servir pour s'orienter.
#
# Une portée relative à la géométrie de la carte (min(W,H)/3) a été envisagée puis écartée :
# elle ne corrigeait PAS les cartes 4×4 (DoorKey/Unlock restaient à 95 % de couverture) et
# AGGRAVAIT le Doctorat en augmentant la portée de 4 à 5. Le problème n'était pas la portée,
# c'était la FORME de la décroissance : une coupure linéaire franche laisse un plateau de
# signal fort sur presque toute une petite carte.
#
# En biologie, une odeur n'est pas un cercle à bord net : c'est un gradient de diffusion
# chimique qui chute très vite près de la source. D'où l'atténuation exponentielle :
#
#     S(d) = exp(-LAMBDA_ODORAT * d)      avec LAMBDA_ODORAT = 0.8
#
#     d=0 → 1.000 (contact)   d=1 → 0.449   d=2 → 0.202
#     d=3 → 0.091             d=4 → 0.041   d≥5 → négligeable
#
# Ce qui compte n'est pas la « couverture » mais le GRADIENT (l'écart de signal entre deux
# cases voisines) : c'est lui qui permet à l'agent de savoir dans quelle direction aller.
# Mesuré sur 600 placements aléatoires de 4 sources, gradient moyen entre cases voisines :
#
#     Carte          | linéaire portée 4 | exponentiel λ=0.8
#     Empty-8x8      |       0.208       |       0.221
#     DoorKey-6x6    |       0.196       |       0.305   (+56 %)
#     MemoryS7       |       0.207       |       0.259
#     MultiRoom      |       0.118       |       0.084   (voir ci-dessous)
#
# DoorKey — la carte où le problème avait été diagnostiqué — gagne 56 % de gradient : c'est
# exactement le rôle de « boussole de proximité » recherché. En contrepartie assumée,
# MultiRoom (Doctorat, 13×13) perd un peu de gradient : l'exponentielle porte moins loin
# qu'une rampe linéaire à 4 cases. C'est cohérent avec le rôle voulu du sens (proximité,
# pas cartographie longue distance — celle-ci reste le travail de la vue et de
# MemoireEpisodiqueSpatiale), mais à surveiller via `Sens_Odorat_*` sur un run au Doctorat.
LAMBDA_ODORAT = 0.8

# Sous ce seuil, le signal est coupé net à 0.0 plutôt que de traîner une valeur infinitésimale
# (à d=6, exp(-4.8) ≈ 0.008). Évite qu'une source à l'autre bout de la carte maintienne
# `Sens_Odorat_Ticks_Actifs_Ratio` artificiellement à 100 % avec un signal inexploitable.
SEUIL_COUPURE_ODORAT = 0.02

# --- ODORAT TOPOLOGIQUE : la distance de CHEMINEMENT, pas le vol d'oiseau (v32.0) ---
#
# Jusqu'en v31.1, `lire_chimie` calculait une distance de Manhattan pure
# (|dx| + |dy|), sans jamais consulter la grille entre l'agent et la source. Une odeur
# traversait donc les murs : sur `DoorKey-6x6`, une ressource située dans la pièce
# verrouillée émettait exactement le même signal que si la cloison n'existait pas.
#
# Conséquence, plus grave qu'une simple imprécision : le gradient devenait TROMPEUR.
# L'agent qui suit une odeur à travers un mur s'englue contre la paroi — le sens le
# guide vers un point qu'il ne peut pas atteindre. Un gradient faux est pire que pas de
# gradient du tout, puisque `integrateur_bio` ne peut pas apprendre à ignorer un signal
# qui n'est faux qu'une partie du temps.
#
# La distance est donc désormais celle d'un parcours en largeur (BFS) MULTI-SOURCES : on
# part de toutes les sources d'un même type à la fois et on propage sur les cases
# franchissables. Le coût est en O(V+E) sur une grille de 36 à 169 cases, soit MOINS que
# la double boucle de scan qu'il remplace (laquelle balayait déjà toute la grille).
#
# Les portes fermées ne bloquent PAS : elles « fuient ». Une porte close arrête l'air,
# pas les molécules — et surtout, la bloquer rendrait l'odorat inutile précisément quand
# l'agent cherche la clé de cette porte (le signal n'apparaîtrait qu'une fois la porte
# déjà ouverte, donc le problème déjà résolu). Elle ajoute à la place un SURCOÛT de
# distance : l'odeur passe dessous, atténuée, et le gradient se renforce brutalement dès
# l'ouverture. Un mur, lui, reste infranchissable.
SURCOUT_PORTE_FERMEE = 4

# Types d'objets MiniGrid qui arrêtent totalement la diffusion. `wall` et `lava` bloquent ;
# une `door` est traitée à part (voir SURCOUT_PORTE_FERMEE) ; tout le reste (`ball`, `key`,
# `box`, `goal`, case vide) laisse passer l'odeur — un objet posé au sol n'est pas une
# cloison.
TYPES_BLOQUANTS_ODORAT = ("wall", "lava")

# Conservée pour la rétrocompatibilité documentaire (v29.x) — n'est plus utilisée par le
# calcul depuis la v30.0, l'atténuation exponentielle n'ayant pas de portée franche.
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
        # v30.0 — avertissement distinct pour l'Exo-Sens : un plug qui renvoie un vecteur
        # malformé ne doit jamais désactiver les 5 sens physiques (voir _avertir_exo).
        self._avertissement_exo_donne = False
        # Trace de goût : [nourriture, eau], décroît à chaque tick.
        self._gout_courant = np.zeros(2, dtype=np.float32)
        # v32.0 — mémoire d'un tick pour la clinotaxie (ΔS). `None` = pas de tick
        # précédent comparable (début d'épisode) ⇒ ΔS neutre, voir lire_chimie.
        self._odeurs_precedentes = None

    def _avertir(self, exception):
        if not self._avertissement_donne:
            print(f"⚠️  Bus sensoriel (toucher/odorat/goût) désactivé "
                  f"(API minigrid incompatible : {exception})")
            self._avertissement_donne = True
        self.actif = False

    def reinitialiser_episode(self, env=None):
        """Le goût ne traverse PAS les épisodes (contrairement aux jauges du
        BiologicalHomeostasisEngine, qui sont un métabolisme continu) : c'est une
        sensation immédiate liée à une bouchée précise, pas un état vital.

        v32.0 — la mémoire olfactive du tick précédent est effacée pour la même raison,
        mais avec un enjeu plus vif : au `reset()`, l'agent est TÉLÉPORTÉ et les sources
        sont régénérées ailleurs. Comparer la première odeur du nouvel épisode à la
        dernière de l'ancien produirait un ΔS énorme et purement fictif, que C1
        interpréterait comme un violent rapprochement. Le premier tick d'un épisode n'a
        donc pas de variation — il n'a rien à quoi se comparer."""
        self._gout_courant[:] = 0.0
        self._odeurs_precedentes = None

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
          proche du type correspondant. v30.0 — décroissance **exponentielle**
          `exp(-LAMBDA_ODORAT * d)` (distance de Manhattan, cohérente avec la métrique déjà
          utilisée par `DetecteurJalonsDoorKey._distance` et `MemoireEpisodiqueSpatiale`),
          coupée à 0.0 sous `SEUIL_COUPURE_ODORAT`. Remplace la rampe linéaire de la v29.x,
          qui saturait les petites cartes — voir le commentaire de `LAMBDA_ODORAT` en tête
          de module pour le diagnostic et les mesures de gradient.
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

                # v32.0 — distance de CHEMINEMENT (BFS multi-sources), plus le vol
                # d'oiseau : l'odeur ne traverse plus les murs. Voir SURCOUT_PORTE_FERMEE.
                distances = self._distances_topologiques(grille, pos_agent)

                for i, couleur in enumerate((COULEUR_NOURRITURE, COULEUR_EAU)):
                    d = distances[couleur]
                    if d is None:
                        continue  # aucune source, ou aucune ATTEIGNABLE (mur infranchissable)
                    # v30.0 — gradient de diffusion chimique plutôt qu'un cercle à bord net.
                    intensite = float(np.exp(-LAMBDA_ODORAT * d))
                    odeurs[i] = intensite if intensite >= SEUIL_COUPURE_ODORAT else 0.0
            except Exception as e:
                self._avertir(e)
                odeurs = [0.0, 0.0]

        deltas = self._calculer_deltas_odorat(odeurs)
        return (odeurs + [float(self._gout_courant[0]), float(self._gout_courant[1])]
                + deltas)

    def _calculer_deltas_odorat(self, odeurs) -> list:
        """v32.0 — la clinotaxie : ΔS = S_t − S_{t−1} par type de ressource, normalisé
        dans [0, 1] par `(ΔS + 1) / 2`.

        La normalisation est impérative et non cosmétique : toutes les autres dims du bus
        sont bornées dans [0, 1] (voir la discipline en tête de module), et une dim
        signée dans [−1, 1] pèserait deux fois plus lourd à l'entrée de `integrateur_bio`
        par simple effet d'échelle. Le point neutre est donc **0.5** — « je ne me
        rapproche ni ne m'éloigne » — au-dessus je me rapproche, en dessous je m'éloigne.

        Sans tick précédent (premier tick d'un épisode, voir `reinitialiser_episode`), la
        valeur retournée est exactement 0.5 : neutre, jamais un faux pic directionnel.
        """
        if self._odeurs_precedentes is None:
            deltas = [0.5, 0.5]
        else:
            deltas = [
                float(np.clip((odeurs[i] - self._odeurs_precedentes[i] + 1.0) / 2.0, 0.0, 1.0))
                for i in range(2)
            ]
        self._odeurs_precedentes = list(odeurs)
        return deltas

    def _distances_topologiques(self, grille, pos_agent) -> dict:
        """Distance de cheminement (BFS multi-sources) de l'agent à la source la plus
        proche de chaque type — v32.0. Retourne `{couleur: distance ou None}`.

        Un seul parcours par type de ressource, propagé DEPUIS les sources vers l'agent :
        on s'arrête dès que la case de l'agent est atteinte. Partir des sources plutôt que
        de l'agent permet de traiter d'un coup toutes les sources d'un même type — c'est
        le « champ de diffusion » du document de conception, et ça donne directement le
        minimum recherché sans comparer source par source.

        Le coût de traversée d'une case n'est pas uniforme : une porte fermée coûte
        `1 + SURCOUT_PORTE_FERMEE` au lieu de 1 (elle « fuit » — voir le commentaire de
        cette constante). Une file de priorité serait donc formellement requise ; on
        garde une BFS à seaux (`buckets`), suffisante et plus simple ici puisque les
        coûts sont de petits entiers bornés.

        `None` signifie « aucune source de ce type, ou aucune atteignable » — un mur
        infranchissable rend une ressource littéralement inodore, ce qui est le
        comportement voulu.
        """
        resultat = {COULEUR_NOURRITURE: None, COULEUR_EAU: None}
        largeur, hauteur = grille.width, grille.height

        # Coût d'entrée de chaque case : None = infranchissable. Calculé une fois pour
        # les deux parcours (la topologie ne dépend pas du type de ressource).
        cout = [[1] * hauteur for _ in range(largeur)]
        sources = {COULEUR_NOURRITURE: [], COULEUR_EAU: []}
        for x in range(largeur):
            for y in range(hauteur):
                objet = grille.get(x, y)
                if objet is None:
                    continue
                type_objet = getattr(objet, "type", None)
                if type_objet in TYPES_BLOQUANTS_ODORAT:
                    cout[x][y] = None
                elif type_objet == "door" and not getattr(objet, "is_open", True):
                    cout[x][y] = 1 + SURCOUT_PORTE_FERMEE
                elif type_objet == "ball":
                    couleur = getattr(objet, "color", None)
                    if couleur in sources:
                        sources[couleur].append((x, y))

        for couleur, positions in sources.items():
            if positions:
                resultat[couleur] = self._bfs_vers_agent(cout, positions, pos_agent,
                                                         largeur, hauteur)
        return resultat

    @staticmethod
    def _bfs_vers_agent(cout, sources, pos_agent, largeur, hauteur):
        """Propagation à seaux depuis `sources` jusqu'à `pos_agent`. Retourne la distance
        pondérée, ou None si l'agent n'est pas atteignable.

        Les seaux (`dict[distance] -> cases`) tiennent lieu de file de priorité : les
        coûts étant de petits entiers (1, ou 1+SURCOUT_PORTE_FERMEE), traiter les
        distances dans l'ordre croissant garantit qu'une case est finalisée à sa distance
        minimale — un Dijkstra dégénéré, sans le coût d'un tas."""
        INFINI = float("inf")
        meilleure = [[INFINI] * hauteur for _ in range(largeur)]
        seaux = {0: []}
        for (x, y) in sources:
            # Une source posée sur une case franchissable est le point de départ à
            # distance 0 : c'est l'odeur AU contact de la ressource.
            if meilleure[x][y] > 0:
                meilleure[x][y] = 0
                seaux[0].append((x, y))

        distance_courante = 0
        distance_max = largeur * hauteur * (1 + SURCOUT_PORTE_FERMEE)
        while distance_courante <= distance_max:
            lot = seaux.pop(distance_courante, None)
            if lot is None:
                if not seaux:
                    break
                distance_courante += 1
                continue
            for (x, y) in lot:
                if meilleure[x][y] < distance_courante:
                    continue  # entrée périmée, une meilleure distance a été trouvée depuis
                if (x, y) == pos_agent:
                    return distance_courante
                for (vx, vy) in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                    if not (0 <= vx < largeur and 0 <= vy < hauteur):
                        continue
                    cout_case = cout[vx][vy]
                    if cout_case is None:
                        continue  # mur : la diffusion s'arrête net
                    candidate = distance_courante + cout_case
                    if candidate < meilleure[vx][vy]:
                        meilleure[vx][vy] = candidate
                        seaux.setdefault(candidate, []).append((vx, vy))
            distance_courante += 1

        return None

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

    # --- 3. L'EXO-SENS — LE 6ème SENS (v30.0) ---

    def percevoir_exogene(self, reponse_c3=None) -> list:
        """Transducteur du 6ème sens : traduit une `ReponseC3` en DIM_EXO=8 dims
        normalisées, perçues **en continu** au même titre que le toucher ou l'odorat.

        C'est le pivot conceptuel de la v30.0 : C3 n'est plus un « 3ème cerveau » qu'on
        interroge par une action apprise, mais un **canal perceptif exogène**. L'agent ne
        décide pas de « demander » — il *sent* le monde numérique en permanence, et c'est
        `integrateur_bio` qui apprend seul, par myélinisation, à quel point ces dimensions
        méritent son attention. Si le plug envoie du bruit, les poids correspondants
        tomberont naturellement vers 0 ; s'il envoie de l'information utile, ils se
        renforceront. **Aucun `if` de déclenchement dans le chemin de décision** — c'est
        ce qui rend cette option cohérente avec les refus posés en v28 (seuil pour C3) et
        v29 (court-circuit C1→C2).

        `reponse_c3=None` (aucun plug branché, ou aucun n'a répondu) ⇒ vecteur nul : le
        comportement redevient **strictement identique à la v29.1**. C'est l'invariant de
        frugalité du projet — sans greffon, l'organisme est inchangé, et le coût se réduit
        à des multiplications par zéro déjà vectorisées.

        Les valeurs sont **clippées dans [0, 1]** ici plutôt que de faire confiance au
        plug : un service externe est par nature non maîtrisé, et une dimension à 10^6
        écraserait `integrateur_bio` par simple échelle (les 5 sens physiques sont tous
        bornés — voir la discipline de normalisation en tête de module). Un vecteur de
        mauvaise taille est ignoré (vecteur nul) plutôt que tronqué au hasard.
        """
        neutre = [0.0] * DIM_EXO
        if reponse_c3 is None:
            return neutre
        perception = getattr(reponse_c3, "perception", None)
        if perception is None:
            return neutre  # plug purement décisionnel (v28) : rien à percevoir
        try:
            vecteur = np.asarray(perception, dtype=np.float32).flatten()
            if vecteur.shape[0] != DIM_EXO:
                self._avertir_exo(
                    f"vecteur de perception de taille {vecteur.shape[0]}, {DIM_EXO} attendues"
                )
                return neutre
            if not np.all(np.isfinite(vecteur)):
                self._avertir_exo("vecteur de perception contenant NaN/inf")
                return neutre
            return [float(v) for v in np.clip(vecteur, 0.0, 1.0)]
        except Exception as e:
            self._avertir_exo(f"vecteur de perception illisible ({e})")
            return neutre

    def _avertir_exo(self, motif: str):
        """Avertissement UNE SEULE FOIS sur un Exo-Sens malformé — même discipline que
        `_avertir` pour les sens physiques. Contrairement à lui, ne désactive PAS le bus :
        un plug qui renvoie un vecteur invalide ne doit pas rendre l'agent aveugle,
        sourd et insensible ; seul l'Exo-Sens retombe à neutre pour ce tick."""
        if not self._avertissement_exo_donne:
            print(f"⚠️  Exo-Sens ignoré ce tick ({motif}) — vecteur neutre utilisé. "
                  f"Les 5 sens physiques ne sont pas affectés.")
            self._avertissement_exo_donne = True

    # --- 4. L'INTERPRÉTEUR UNIFIÉ ---

    def interpreter(self, env, action_item=None, reponse_c3=None) -> list:
        """Point d'entrée unique : renvoie les DIM_TOUCHER + DIM_CHIMIE + DIM_EXO +
        DIM_ODORAT_DELTA = 18 dims des sens faibles à moyens ET du 6ème sens, dans
        l'ordre exact attendu par la queue du `vecteur_bio` (voir
        `BiologicalHomeostasisEngine.obtenir_vecteur_bio`) :

            [contact, objet_en_main, orient_cos, orient_sin,        ← toucher (v29.0)
             odeur_food, odeur_water, gout_food, gout_water,        ← chimie  (v29.0)
             exo_0 .. exo_7,                                        ← Exo-Sens (v30.0)
             delta_odeur_food, delta_odeur_water]                   ← clinotaxie (v32.0)

        ⚠️ Les 2 dims de clinotaxie sont en QUEUE, donc APRÈS l'Exo-Sens — et non
        accolées à l'odorat dont elles dérivent, ce qui serait plus lisible mais
        décalerait les 8 dims exogènes d'un `.brain` v30/v31 déjà entraîné. Le contrat
        append-only prime sur la lisibilité du regroupement.

        L'ordre de cette concaténation est un CONTRAT : il doit rester synchronisé avec
        `obtenir_vecteur_bio` et avec la greffe de rétrocompatibilité de
        `persistance._greffer_vecteur_bio_etendu` (qui recopie les N premières dims d'un
        ancien `.brain` et laisse les nouvelles à leur initialisation). Ne jamais insérer
        une dimension au milieu — **toujours ajouter en queue**.

        `reponse_c3=None` (défaut) ⇒ les 8 dims de l'Exo-Sens sont nulles, comportement
        strictement identique à la v29.1.
        """
        self.decroitre_gout()
        # `lire_chimie` renvoie DIM_CHIMIE + DIM_ODORAT_DELTA valeurs : les 4 dims
        # chimiques historiques PUIS les 2 deltas, qu'on ré-ordonne ici pour respecter le
        # contrat append-only (les deltas partent en toute fin, après l'Exo-Sens).
        chimie_et_deltas = self.lire_chimie(env)
        chimie = chimie_et_deltas[:DIM_CHIMIE]
        deltas_odorat = chimie_et_deltas[DIM_CHIMIE:]
        return (self.lire_toucher(env, action_item)
                + chimie
                + self.percevoir_exogene(reponse_c3)
                + deltas_odorat)

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
            # v32.0 — 2 dims d'intensité (S_t) + 2 dims de variation (ΔS, clinotaxie).
            # La distance est topologique (BFS) depuis cette version : l'odeur ne
            # traverse plus les murs, une porte fermée la laisse « fuir » avec surcoût.
            "odorat": {"gourmandise": "faible", "dims": 2 + DIM_ODORAT_DELTA,
                       "chemin": "vecteur_bio → integrateur_bio", "jepa": False,
                       "topologique": True, "clinotaxie": True},
            "gout": {"gourmandise": "faible", "dims": 2,
                     "chemin": "vecteur_bio → integrateur_bio", "jepa": False},
            # v30.0 — le 6ème sens. "gourmandise" externe : le coût n'est pas dans le
            # cerveau (8 dims, négligeable) mais chez le plug (réseau, LLM, base
            # vectorielle) — d'où une catégorie à part plutôt qu'un rang dans l'échelle
            # physique. "exogene": True le distingue des 5 sens du monde physique.
            "exo_sens": {"gourmandise": "externe", "dims": DIM_EXO,
                         "chemin": "PortC3 → vecteur_bio → integrateur_bio",
                         "jepa": False, "exogene": True},
        }
