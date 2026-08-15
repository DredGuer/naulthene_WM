# Chantier v41.6 — P17 : le cursus comme distribution

> **Statut** : implémenté, run de validation en cours (6 graines × 1000 j, 15/08/2026 soir).
> **Fichier** : `src/naulthene/cerveau/noyau.py` (expérimental — pas dans `colab.py`).
> **Origine** : [P17](AVIS_ET_PROPOSITIONS_aout_2026.md), formulé par l'utilisateur le 14/08.

---

## 1. Ce que ça remplace

`niveau_actuel` était un **pointeur** : on jouait ce niveau et rien d'autre.

**Mesuré sur les runs de 2000 jours (v41.4)** : g44, promu au niveau 3 (`Empty-8x8`), s'y
effondre à **2 % de maîtrise** et y reste **1500 jours** — sans jamais rejouer les deux
paliers qu'il maîtrisait. *Un pointeur qui ne recule jamais transforme le moindre mur en
cul-de-sac définitif.*

La formulation d'origine :

> *« Tu fais 3×3 vingt fois, puis 4×4 cinq fois, puis 3×3 deux fois, comme ça
> aléatoirement — mais tant que le 3×3 n'est pas réussi, tu ne vas pas au-delà du 5×5,
> sauf exceptionnellement. »*

## 2. La forme — trois propriétés sans un seul `if`

Le niveau joué est **tiré au sort** à chaque épisode, autour du niveau de référence :

| Propriété voulue | Comment elle émerge |
|---|---|
| Retours en arrière réguliers | la **queue gauche** de la distribution |
| « Pas au-delà tant que ce n'est pas acquis » | le sommet ne bouge qu'avec la **maîtrise** |
| « Sauf exceptionnellement » | la **queue droite** est fine, **jamais nulle** |

## 3. ⚠️ Les proportions sont DÉRIVÉES, jamais posées

La formulation initiale proposait **65 % / 15 % / 20 %** en dur. Trois constantes auraient
remplacé un pointeur rigide par trois chiffres arbitraires — exactement ce que la méthode
v30.1 interdit : *« remplacer un chiffre arbitraire par une formule arbitraire ne vaut pas
mieux, elle est juste plus difficile à remettre en cause »*.

Ces valeurs sont donc devenues le **point de passage** de la courbe à `TAUX_PROMOTION` :

| Maîtrise | Révision | Défi | Incursion |
|---|---|---|---|
| 0 % | 66 % | 33 % | 2 % |
| 20 % | 61 % | 33 % | 6 % |
| 40 % | 43 % | 44 % | 13 % |
| **60 %** | **15 %** | **65 %** | **20 %** ← *le point P17, au millième* |
| 80 % | 15 % | 63 % | 22 % |
| 100 % | 15 % | 60 % | 25 % |

Deux grandeurs mesurées gouvernent tout : l'**avancement** (`maîtrise / TAUX_PROMOTION`) et
l'**étalement** (`1 − maîtrise`) — un agent qui maîtrise reste concentré, un agent qui
échoue s'étale vers ce qu'il sait faire. Même doctrine que le rêve adaptatif.

## 4. 🔍 Deux défauts trouvés par la mesure, AVANT tout run

Le test unitaire de la distribution les a rattrapés — ils auraient tous deux produit
l'inverse de l'effet recherché.

### 4.1 Le défi tombait à 2 % chez un agent qui échoue

En laissant la gaussienne porter directement la masse par palier, la masse totale d'un côté
dépendait du **nombre de paliers disponibles**, pas de l'intention. Résultat mesuré à 0 %
de maîtrise : révision 98 %, **défi 2 %**.

> 🔴 L'agent ne jouait quasiment plus son propre palier — il ne pouvait donc **plus jamais
> y progresser**. P17 l'aurait **enfermé** dans la révision au lieu de l'en sortir.

**Correctif** : chaque côté est distribué en **forme** (gaussienne) puis remis à l'échelle
de la **masse** voulue. La forme décide de la répartition, les poids décident du volume.
Plus un **plancher de défi** (`défi_référence × 0,5`), lui-même dérivé du point P17.

### 4.2 L'incursion tombait à 0 % chez un agent qui maîtrise

L'étalement s'annulant avec la maîtrise, la queue droite était écrasée : **0 % d'incursion à
80 %** de maîtrise — l'inverse exact de l'intention, un agent qui s'ennuie devant rester
enfermé.

**Correctif** : `sigma_droite = max(0,4 ; étalement × 0,6)` et un facteur de croissance
normalisé pour valoir exactement 1 au point de référence.

## 5. Les invariants

| # | Invariant | Vérification |
|---|---|---|
| 1 | Tirage borné à `[0, len(PROGRAMME)-1]` | **assertion** + 5000 tirages testés |
| 2 | Seuls les épisodes du **niveau de référence** comptent pour la promotion | garde dans `_enregistrer_episode_niveau` |
| 3 | Le défi ne descend jamais sous la moitié de sa référence | testé sur toute la plage 0→100 % |
| 4 | L'incursion n'est **jamais nulle** | testé sur toute la plage |
| 5 | Le tirage utilise `np.random` (celui que `--graine` réamorce) | reproductibilité à graine fixée |

### 5.1 ⚠️ L'invariant de mesure (n°2) est le plus important

Créditer une révision réussie sur `Empty-5x5` au compte du niveau 3 gonflerait la maîtrise
et promouvrait un agent qui **n'a rien montré là où il fallait**. C'est précisément ce que
l'invariant « vider la fenêtre à chaque promotion » (v35.0) existe pour empêcher — et P17
l'aurait réintroduit **par une autre porte**.

La maîtrise **générale** (v41.4), elle, prend tout : c'est son rôle de traverser les cartes.

### 5.2 Piège corrigé — `doorkey_actif` était fixé une fois par jour

Juste tant qu'une journée ne voyait qu'une seule carte. **P17 change de carte en cours de
journée** : sans réévaluation, les détecteurs de jalons DoorKey tourneraient sur une grille
sans clé ni porte (ou l'inverse).

## 6. Instrumentation (même commit)

Ligne `Cursus P17` au bilan de nuit + 6 clés W&B. La plus importante est
**`P17_Poids_Defi`** : elle doit **monter quand la maîtrise monte**. C'est ce couplage qui
distingue une distribution *dérivée* de trois constantes en dur — si elle reste plate, la
mécanique est un pointeur déguisé.

## 7. Résultats

*(en attente — cette section sera remplie par la mesure)*

**Comparaison de référence** (v41.4, sans P17, 2000 j) :

| | Résultat |
|---|---|
| Graines bloquées au niveau 1 | **3 sur 4** |
| g44 au niveau 3 | **1500 jours à 2 % de maîtrise** |
