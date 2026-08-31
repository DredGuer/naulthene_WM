# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Adrien Nault — Naulthène AGI
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

# --- v41.11 : LA THERMOCEPTION — le danger comme CHAMP CONTINU, jamais comme étiquette ---
#
# Idée de l'utilisateur (16/08) : *« peut-être que MiniGrid manque de gradation
# (2 cases de lave = chaud / 1 case = brûlant / sur la case = mort). Et quand on est
# mort = 0 XP = mort ! »*
#
# 🔴 CE QUE ÇA CORRIGE (mesuré le 16/08) :
#
#   (a) MiniGrid punit la mort par EXACTEMENT 0.0 — 206 morts sur 300 épisodes, toutes à
#       récompense nulle. Toucher un mur coûte MALUS_DOULEUR = -0.01 ; mourir coûte ZÉRO.
#       Toucher un mur coûte donc infiniment plus cher que mourir.
#
#   (b) Le vecteur bio est RIGOUREUSEMENT IDENTIQUE sur la case adjacente à la lave et à
#       trois cases de distance :
#
#           juste à côté de la lave : [0. 0. 1. 0. ... 0.5 0.5]
#           à trois cases           : [1. 0. 1. 0. ... 0.5 0.5]   (le 1.0 est un MUR)
#
#   (c) La lave était traitée UNIQUEMENT comme un obstacle : elle figure dans
#       `TYPES_BLOQUANTS_ODORAT` au même titre qu'un mur, donc elle arrête l'odeur — mais
#       n'en émet AUCUNE. Elle était une cloison, jamais une source.
#
#   (d) La vue la voit (indice 9 dans le canal des types) mais comme un SYMBOLE parmi
#       d'autres : `9` ne se distingue de `1` (sol) ou `8` (but) par rien de continu.
#
# Bilan : l'agent ne pouvait apprendre le danger ni par l'expérience (il meurt, donc
# n'apprend rien — le tick suivant appartient à un autre épisode), ni par les sens (aucun
# gradient ne monte quand il s'approche). D'où la valence POSITIVE mesurée sur `lava`
# (+0,069) : l'agent enregistre « ici j'allais bien », puis l'épisode s'arrête sans que
# rien ne lui dise pourquoi.
#
# LA FORME — pourquoi un champ et pas un malus. Un `if mort: récompense -= X` serait un
# seuil en dur sur un type nommé, exactement ce que le projet refuse (invariant v36.0 :
# aucune table `lava = danger`). Un CHAMP continu, lui, est un sens de plus : il monte à
# mesure qu'on approche, exactement comme l'odorat de la nourriture monte — et l'agent en
# apprend la signification par ce qui lui arrive ensuite, jamais par déclaration.
#
# La chaleur réutilise DONC la machinerie olfactive à l'identique (BFS topologique,
# même atténuation) : le danger est « une odeur de plus », dont la seule particularité est
# d'être émise par les cases qui bloquent le passage. Rien de neuf n'est inventé.
#
# ⚠️ RIEN N'EST NOMMÉ DANS LE CERVEAU. `noyau.py` ne teste jamais « est-ce de la lave » :
# il reçoit deux scalaires de plus dans son vecteur bio et doit découvrir seul ce qu'ils
# valent. Le nom `lava` n'apparaît QUE dans ce fichier de traduction sensorielle, au même
# titre que `red`/`blue` désignent déjà nourriture et eau depuis la v29.0 — c'est
# l'équivalent d'un récepteur thermique, pas d'une connaissance.
#
# Ajoutées EN QUEUE (contrat append-only, invariant v29.0), donc hors cible JEPA.
DIM_THERMOCEPTION = 2   # chaleur perçue (proximité du danger) + sa variation (clinotaxie)

# --- v41.12 : LE TOUCHER EST UN ENSEMBLE DE CAPTEURS, ET IL PORTE LOIN ---
#
# Décision utilisateur (16/08) : *« Il faut que les sens, autant l'odeur que le toucher,
# permettent plus de potentiel (sentir de loin et ressentir par le toucher de loin) ! Le
# toucher est un ensemble de capteurs (pression, thermoception, etc.) »*
#
# 🔴 CE QUE ÇA CORRIGE. Le toucher v29.0 était un interrupteur à portée ZÉRO :
# `contact_frontal` vaut 1.0 si la case devant est bloquante, 0.0 sinon. Trois
# conséquences mesurables :
#
#   (a) Aucune anticipation. L'agent apprend qu'il y a un mur EN LE PERCUTANT — le signal
#       arrive au tick où il est déjà trop tard, et l'action qui l'a produit est déjà jouée.
#   (b) Aucune gradation. Un couloir d'une case de large et une plaine ouverte donnent
#       exactement le même 0.0 tant que rien n'est pile devant : l'agent ne peut pas
#       distinguer « je suis à l'étroit » de « je suis au large », alors que c'est
#       précisément l'information qui permet de longer un mur ou de trouver une ouverture.
#   (c) Aucune direction. Un scalaire frontal ne dit pas de quel CÔTÉ ça se resserre.
#
# LA FORME — la proprioception d'encombrement. Deux capteurs de plus, dérivés de la MÊME
# machinerie que l'odorat et la chaleur (rien de neuf n'est inventé) :
#
#   `pression`  : à quel point l'espace se referme autour de l'agent, dans [0,1]. C'est la
#                 fraction pondérée de directions bloquées dans un voisinage, atténuée par
#                 la distance — un mur collé pèse plus qu'un mur à trois cases. 0.0 en
#                 pleine plaine, ~1.0 dans un cul-de-sac.
#   `asymetrie` : de quel côté ça se resserre, dans [0,1] avec 0.5 = équilibré. C'est ce
#                 qui rend le longement de mur apprenable : < 0.5 ça pousse à gauche,
#                 > 0.5 à droite. Même neutre à 0.5 que la clinotaxie (v32.0) et le rappel
#                 marquant (v36.0) — 0.0 signifierait « bloqué à gauche au maximum ».
#
# ⚠️ CE N'EST PAS DE LA VUE. La pression ne dit RIEN de ce qu'il y a : ni type, ni couleur,
# ni objet. Elle ne dit que « ça se referme, et plutôt par là » — exactement ce qu'un
# vibrisse ou une main tendue dans le noir rapportent. La vue reste le seul sens qui
# identifie ; le toucher étendu ne fait que palper une forme.
#
# ⚠️ Rien n'est nommé : le calcul teste `can_overlap()` (l'API MiniGrid qui dit si on peut
# entrer), jamais un type d'objet. Un mur, une porte fermée et le bord de la grille
# produisent le même signal parce qu'ils font la même chose : ils arrêtent.
#
# Ajoutées EN QUEUE (contrat append-only), donc hors cible JEPA.
DIM_PRESSION = 2   # encombrement perçu + son asymétrie gauche/droite

# Portée du palper. Au-delà, l'agent ne « sent » plus la forme de l'espace — il faudrait
# la voir. 3 cases couvre le voisinage utile sur les cartes 5x5 à 8x8 du PROGRAMME sans
# saturer (mesuré : une portée de 1 reproduit le toucher binaire, une portée de 6 sature
# les petites cartes à ~1.0 partout, exactement le défaut qui a tué l'odorat v29.x).
PORTEE_PRESSION = 3

# Types qui ÉMETTENT de la chaleur. Distinct de TYPES_BLOQUANTS_ODORAT : un mur bloque
# sans brûler, la lave fait les deux. La liste reste ouverte — tout type ajouté ici
# devient une source de chaleur sans qu'aucune autre ligne ne change.
TYPES_BRULANTS = ("lava",)

# --- v41.27 : LES SIGNATURES NOCICEPTIVES ---
#
# Le « type » d'une douleur n'est PAS un canal séparé dans le cerveau : c'est un couple
# (pic, demi-vie de récupération) que l'organe sensoriel fournit. C'est ici, dans le bus —
# la frontière corps/monde, où `lava` a le droit d'exister au même titre que `red`/`blue`
# pour la nourriture — et NULLE PART ailleurs. `noyau.py` ne reçoit que deux nombres et ne
# sait pas ce qui l'a blessé.
#
# Formulation utilisateur (19/08) : *« le chaud ça brûle, mais se taper contre un mur est
# aussi une douleur. Brûlure = douleur vive avec dégradation lente, alors que se cogner
# est une douleur proportionnelle à la vitesse de percussion avec une dégradation
# proportionnellement rapide. »*
#
# Les deux demi-vies sont en TICKS. Leur RAPPORT (~12×) est ce qui porte le sens : une
# brûlure s'installe, un choc passe. Les valeurs absolues sont un ordre de grandeur, pas
# un réglage fin — c'est le rapport qui doit être préservé si on les révise.
DEMI_VIE_BRULURE = 60.0   # la chaleur marque : des dizaines de ticks pour redescendre
DEMI_VIE_CHOC = 5.0       # le choc mécanique passe vite

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

# --- v41.12 : LA PORTÉE SUIT LA TAILLE DU MONDE (décision utilisateur : « sentir de loin ») ---
#
# 🔴 CE QUE ÇA CORRIGE (mesuré). Avec λ = 0.8 fixe et une coupure à 0.02, l'odorat
# s'ÉTEINT À 5 CASES, quelle que soit la carte :
#
#     d=4 → 0.0408 (perçu)      d=5 → 0.0183 (COUPÉ)
#
# Sur `Empty-8x8` (6×6 utile, diagonale ~10 cases) l'agent est donc olfactivement aveugle
# sur la moitié de son monde ; sur MultiRoom (13×13) sur les trois quarts. Le commentaire
# ci-dessus l'anticipait déjà (« l'exponentielle porte moins loin qu'une rampe linéaire,
# à surveiller ») et le renvoyait à une surveillance — c'est ce que cette version règle.
#
# LA FORME — dérivée, jamais posée. λ est calibré pour que le signal atteigne encore le
# seuil de coupure à une DEMI-TRAVERSÉE de la carte courante :
#
#     portée_utile = (largeur + hauteur) / 2 × FRACTION_PORTEE_CARTE
#     λ(carte)     = -ln(SEUIL_COUPURE_ODORAT) / portée_utile
#
# Une petite carte garde donc un gradient serré (l'agent doit s'approcher pour distinguer),
# une grande carte laisse l'odeur porter — exactement le comportement d'une diffusion
# réelle dans un volume plus grand. Aucune portée n'est écrite en dur : elle tombe de la
# géométrie du monde, comme la capacité mnésique tombe de `dim_bus` (v31.0).
#
# ⚠️ LA FRACTION EST MESURÉE, PAS CHOISIE — et la première valeur essayée était mauvaise.
# Le critère n'est pas la couverture (un signal partout ne porte aucune information : c'est
# le défaut qui a tué l'odorat v29.x, 97,6 % de couverture sur Empty-8x8) mais le GRADIENT
# entre cases voisines, seul support de l'orientation. Mesuré sur 200 à 300 placements
# aléatoires de source, gradient moyen :
#
#     Empty-8x8, λ = 0.800 (v30.0) → 0.0860   portée  4   ← LE PIRE des sept testés
#     Empty-8x8, λ = 0.500         → 0.0970   portée  7
#     Empty-8x8, λ = 0.408         → 0.1000   portée  9   ← optimum (+16 %)
#     Empty-8x8, λ = 0.200         → 0.0851   portée 19   ← trop plat, ça resature
#
# La courbe a bien un maximum : trop net on ne sent rien de loin, trop plat on ne distingue
# plus rien de près. L'optimum tombe autour d'une **traversée complète** de la carte —
# mesuré indépendamment sur quatre cartes (fraction optimale 0.8 / 1.2 / 1.2 / 1.5).
#
# ⚠️ Une première version de ce correctif bornait λ à `LAMBDA_ODORAT` « par prudence ».
# C'était une erreur : la borne rendait le correctif INOPÉRANT sur Empty-8x8 — le niveau
# du blocage — en y préservant précisément le réglage le plus mauvais. Prudence et inertie
# se ressemblent beaucoup ; seule la mesure les distingue.
FRACTION_PORTEE_CARTE = 1.0

# Bornes de sécurité sur λ, pas de préférence. La borne HAUTE empêche un monde minuscule
# de produire un sens à portée nulle ; la borne BASSE empêche un monde immense de saturer
# partout. Aucune des deux ne mord sur les 15 cartes du PROGRAMME (λ y va de 0.10 à 0.98) :
# ce sont des garde-fous pour un berceau futur, pas un réglage.
LAMBDA_MIN, LAMBDA_MAX = 0.05, 1.5

# Sous ce seuil, le signal est coupé net à 0.0 plutôt que de traîner une valeur infinitésimale
# (à d=6, exp(-4.8) ≈ 0.008). Évite qu'une source à l'autre bout de la carte maintienne
# `Sens_Odorat_Ticks_Actifs_Ratio` artificiellement à 100 % avec un signal inexploitable.
SEUIL_COUPURE_ODORAT = 0.02


def lambda_diffusion_carte(largeur, hauteur) -> float:
    """v41.12 — λ adapté à la taille du monde : la portée émerge, elle n'est pas posée.

    Calibré pour que le signal atteigne encore le seuil de coupure à une **traversée
    complète** de la carte — fraction validée par mesure de gradient sur quatre cartes
    (voir FRACTION_PORTEE_CARTE). Un petit monde garde donc un gradient serré, un grand
    monde laisse l'odeur porter : la portée émerge de la géométrie, elle n'est pas posée.

    Sert à l'odorat ET à la thermoception : les deux sont des champs de diffusion, et un
    danger doit se sentir d'aussi loin qu'une ressource — sans quoi l'agent flairerait sa
    nourriture à l'autre bout d'une grande carte tout en découvrant la lave au contact.
    """
    try:
        portee = max(1.0, (float(largeur) + float(hauteur)) / 2.0 * FRACTION_PORTEE_CARTE)
        lam = -float(np.log(SEUIL_COUPURE_ODORAT)) / portee
        return float(np.clip(lam, LAMBDA_MIN, LAMBDA_MAX))
    except Exception:
        return LAMBDA_ODORAT

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
# v41.44 — P8 de l'audit du génome : le TYPE d'objet porteur de ressource rejoint les
# deux couleurs, au même endroit et pour la même raison. Un `type == "ball"` restait
# écrit en dur dans `noyau.py` pour compter les ressources — un nom du monde dans le
# cœur cognitif. Sa place est ici, à la frontière corps/monde : c'est l'organe sensoriel
# qui sait à quoi ressemble une ressource, comme il sait déjà que `lava` brûle.
TYPE_RESSOURCE = "ball"


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
        # v41.11 — même rôle pour la chaleur (voir lire_thermoception). `None` = premier
        # tick de l'épisode ⇒ variation neutre à 0.5, jamais un faux refroidissement.
        self._chaleur_precedente = None

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
        # v41.11 — idem pour la chaleur : au reset l'agent est téléporté, comparer à la
        # dernière chaleur de l'épisode précédent produirait un Δ fictif et violent.
        self._chaleur_precedente = None

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
                # v41.12 — la portée suit la taille du monde. Sur une petite carte,
                # `lambda_diffusion_carte` retourne exactement LAMBDA_ODORAT : le
                # comportement v30.0 est préservé là où il avait été calibré.
                lam = lambda_diffusion_carte(grille.width, grille.height)

                for i, couleur in enumerate((COULEUR_NOURRITURE, COULEUR_EAU)):
                    d = distances[couleur]
                    if d is None:
                        continue  # aucune source, ou aucune ATTEIGNABLE (mur infranchissable)
                    # v30.0 — gradient de diffusion chimique plutôt qu'un cercle à bord net.
                    intensite = float(np.exp(-lam * d))
                    odeurs[i] = intensite if intensite >= SEUIL_COUPURE_ODORAT else 0.0
            except Exception as e:
                self._avertir(e)
                odeurs = [0.0, 0.0]

        deltas = self._calculer_deltas_odorat(odeurs)
        return (odeurs + [float(self._gout_courant[0]), float(self._gout_courant[1])]
                + deltas)

    def lire_pression(self, env) -> list:
        """v41.12 — LE TOUCHER À DISTANCE : encombrement + asymétrie (DIM_PRESSION=2).

        Palpe l'espace sur `PORTEE_PRESSION` cases dans les quatre directions RELATIVES à
        l'agent (devant, derrière, gauche, droite). Chaque direction rend la distance au
        premier obstacle ; une distance courte pèse lourd, une direction dégagée ne pèse
        rien.

        - `pression` : moyenne des contributions `1 - d/portée`, dans [0, 1].
          0.0 = plaine ouverte, ~1.0 = cul-de-sac. C'est la GRADATION qui manquait : le
          toucher v29.0 ne distinguait pas un couloir d'une plaine tant que rien n'était
          pile devant.
        - `asymetrie` : `(gauche - droite + 1) / 2`, dans [0, 1], **neutre à 0.5**.
          C'est ce qui rend le longement de mur apprenable — un scalaire frontal ne dit
          jamais de quel côté ça se resserre.

        ⚠️ Ce sens ne DÉCRIT rien : ni type, ni couleur, ni objet. Il rapporte une forme,
        comme une vibrisse ou une main tendue dans le noir. `can_overlap()` est le seul
        test — un mur, une porte fermée et le bord de la grille sont indiscernables ici,
        parce qu'ils font la même chose : ils arrêtent.

        ⚠️ Les directions sont RELATIVES (elles tournent avec l'agent), jamais absolues :
        « ça se resserre à ma gauche » garde son sens quand l'agent pivote, alors que
        « ça se resserre au nord » obligerait C1 à recomposer l'information avec
        l'orientation à chaque tick.
        """
        if not self.actif:
            return [0.0, 0.5]
        try:
            noyau_env = env.unwrapped
            grille = noyau_env.grid
            x0, y0 = (int(v) for v in noyau_env.agent_pos)
            direction = int(noyau_env.agent_dir)

            # Vecteurs unitaires MiniGrid : 0=droite(+x), 1=bas(+y), 2=gauche, 3=haut.
            # On tourne le repère avec l'agent pour obtenir devant/droite/derrière/gauche.
            base = [(1, 0), (0, 1), (-1, 0), (0, -1)]
            devant = base[direction % 4]
            droite = base[(direction + 1) % 4]
            derriere = base[(direction + 2) % 4]
            gauche = base[(direction + 3) % 4]

            def distance_obstacle(dx, dy):
                """Nombre de cases libres avant le premier obstacle, borné à la portée."""
                for pas in range(1, PORTEE_PRESSION + 1):
                    x, y = x0 + dx * pas, y0 + dy * pas
                    if not (0 <= x < grille.width and 0 <= y < grille.height):
                        return pas - 1          # le bord de la grille arrête aussi
                    objet = grille.get(x, y)
                    if objet is not None and not objet.can_overlap():
                        return pas - 1
                return PORTEE_PRESSION          # dégagé sur toute la portée

            # Contribution d'une direction : 1.0 collé à l'obstacle, 0.0 si dégagé.
            def serrage(v):
                return 1.0 - distance_obstacle(*v) / PORTEE_PRESSION

            s_devant, s_droite = serrage(devant), serrage(droite)
            s_derriere, s_gauche = serrage(derriere), serrage(gauche)

            pression = (s_devant + s_droite + s_derriere + s_gauche) / 4.0
            # Neutre à 0.5 : ni plus serré à gauche, ni à droite (même discipline que la
            # clinotaxie v32.0 — 0.0 signifierait « bloqué à gauche au maximum »).
            asymetrie = (s_gauche - s_droite + 1.0) / 2.0
            return [float(np.clip(pression, 0.0, 1.0)),
                    float(np.clip(asymetrie, 0.0, 1.0))]
        except Exception as e:
            self._avertir(e)
            return [0.0, 0.5]

    def _champ_thermique(self, env) -> float:
        """v41.25 — le CHAMP de rayonnement seul (BFS topologique), sans mémoire ni delta.

        Extrait de `lire_thermoception` pour être partagé avec `chaleur_seule` : un seul
        calcul, deux lectures. Dupliquer le BFS aurait ouvert la porte à ce que les deux
        versions divergent au premier correctif.
        """
        chaleur = 0.0
        if self.actif:
            try:
                noyau_env = env.unwrapped
                grille = noyau_env.grid
                pos_agent = tuple(int(v) for v in noyau_env.agent_pos)
                largeur, hauteur = grille.width, grille.height

                # Topologie propre à la chaleur : les murs arrêtent, les cases brûlantes
                # rayonnent (donc franchissables ici, contrairement au calcul olfactif).
                cout = [[1] * hauteur for _ in range(largeur)]
                sources = []
                for x in range(largeur):
                    for y in range(hauteur):
                        objet = grille.get(x, y)
                        if objet is None:
                            continue
                        type_objet = getattr(objet, "type", None)
                        if type_objet in TYPES_BRULANTS:
                            sources.append((x, y))
                        elif type_objet in TYPES_BLOQUANTS_ODORAT:
                            cout[x][y] = None      # un mur fait de l'ombre thermique
                        elif type_objet == "door" and not getattr(objet, "is_open", True):
                            cout[x][y] = 1 + SURCOUT_PORTE_FERMEE

                if sources:
                    d = self._bfs_vers_agent(cout, sources, pos_agent, largeur, hauteur)
                    if d is not None:
                        # v41.12 — même portée adaptative que l'odorat : un danger doit se
                        # sentir d'aussi loin qu'une ressource, sinon l'agent flairerait sa
                        # nourriture à l'autre bout de la carte tout en découvrant la lave
                        # au contact.
                        intensite = float(np.exp(-lambda_diffusion_carte(largeur, hauteur) * d))
                        chaleur = intensite if intensite >= SEUIL_COUPURE_ODORAT else 0.0
            except Exception as e:
                self._avertir(e)
                chaleur = 0.0
        return chaleur

    def lire_thermoception(self, env) -> list:
        """v41.11 — LA CHALEUR : le danger perçu comme un champ continu (DIM_THERMOCEPTION=2).

        - `chaleur` : intensité dans [0, 1] de la source brûlante la plus proche, par la
          MÊME loi que l'odorat (`exp(-LAMBDA_ODORAT * d)` sur la distance de cheminement).
          C'est la gradation demandée : loin = 0, à quelques cases = tiède, adjacent =
          brûlant, dessus = maximum.
        - `delta_chaleur` : sa variation depuis le tick précédent, normalisée dans [0, 1]
          avec un neutre à **0.5** — même contrat que la clinotaxie olfactive (v32.0), et
          même piège évité : 0.0 signifierait « refroidissement maximal », ce qui ferait
          croire à l'agent qu'il fuit un danger inexistant à chaque premier tick.

        ⚠️ LA DIFFÉRENCE AVEC L'ODORAT, ET POURQUOI ELLE EST NÉCESSAIRE. Une source
        brûlante est aussi un obstacle (`lava` est dans `TYPES_BLOQUANTS_ODORAT`) : si on
        la traitait comme une source olfactive ordinaire, le BFS partirait d'une case
        marquée infranchissable et ne propagerait rien du tout. La chaleur se propage donc
        sur une topologie où les cases brûlantes sont FRANCHISSABLES en tant que points de
        départ — ce qui est physiquement juste : la chaleur rayonne depuis le feu, elle
        n'est pas arrêtée par lui.

        Les murs, eux, arrêtent bien la chaleur — un agent séparé de la lave par une
        cloison n'est pas en danger, et lui envoyer un signal serait exactement le défaut
        que la v32.0 a corrigé pour l'odorat (un gradient qui traverse un mur est PIRE que
        pas de gradient, car il est faux une partie du temps seulement).

        ⚠️ Le cerveau ne reçoit que deux nombres. Il n'apprendra ce qu'ils signifient que
        par ce qui lui arrive quand ils montent — jamais par une déclaration.
        """
        chaleur = self._champ_thermique(env)

        # Même neutre à 0.5 et même normalisation que la clinotaxie olfactive.
        if self._chaleur_precedente is None:
            delta = 0.5
        else:
            delta = float(np.clip((chaleur - self._chaleur_precedente + 1.0) / 2.0, 0.0, 1.0))
        self._chaleur_precedente = chaleur
        return [float(np.clip(chaleur, 0.0, 1.0)), delta]

    def chaleur_seule(self, env) -> float:
        """v41.25 — la chaleur INSTANTANÉE, sans effet de bord.

        Même champ de rayonnement que `lire_thermoception`, mais SANS toucher à
        `_chaleur_precedente` et sans produire de delta. Existe pour un seul usage : la
        facturation nociceptive doit relire la température APRÈS `env.step` (la case où
        l'agent est arrivé), alors que la perception, elle, reste celle du début de tick.

        ⚠️ Appeler `lire_thermoception` une seconde fois dans le même tick serait un
        BUG : il écraserait `_chaleur_precedente` avec la valeur post-step, si bien que
        la clinotaxie du tick suivant comparerait deux mesures séparées par un demi-tick
        et rapporterait une variation deux fois trop petite. Le signal d'approche — la
        seule chose qui permet d'apprendre à FUIR — serait silencieusement faussé.
        """
        return float(self._champ_thermique(env))

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
        DIM_ODORAT_DELTA + DIM_THERMOCEPTION = 20 dims des sens faibles à moyens ET du
        6ème sens, dans l'ordre exact attendu par la queue du `vecteur_bio` (voir
        `BiologicalHomeostasisEngine.obtenir_vecteur_bio`) :

            [contact, objet_en_main, orient_cos, orient_sin,        ← toucher (v29.0)
             odeur_food, odeur_water, gout_food, gout_water,        ← chimie  (v29.0)
             exo_0 .. exo_7,                                        ← Exo-Sens (v30.0)
             delta_odeur_food, delta_odeur_water,                   ← clinotaxie (v32.0)
             chaleur, delta_chaleur,                                ← thermoception (v41.11)
             pression, asymetrie]                                   ← toucher à distance (v41.12)

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
                + deltas_odorat
                # v41.11 — la thermoception ferme la queue : ajoutée APRÈS la clinotaxie,
                # jamais accolée à l'odorat dont elle réutilise la machinerie. Même
                # arbitrage qu'en v32.0 : le contrat append-only prime sur la lisibilité
                # du regroupement, sans quoi tous les `.brain` v32→v41 se décaleraient.
                + self.lire_thermoception(env)
                # v41.12 — le toucher à distance ferme la queue. Il est placé ICI et non
                # accolé à `lire_toucher` dont il fait pourtant partie conceptuellement :
                # l'insérer au milieu décalerait toutes les dims des `.brain` v29→v41.
                # Le contrat append-only prime sur le regroupement logique — même
                # arbitrage qu'en v32.0 pour la clinotaxie.
                + self.lire_pression(env))

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
