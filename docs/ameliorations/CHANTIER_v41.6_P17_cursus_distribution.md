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

## 7. Résultats — point d'étape à j468 (run en cours)

### 7.1 La comparaison directe : g44, même graine, avec et sans P17

| g44 | 1ʳᵉ promotion | 2ᵉ promotion |
|---|---|---|
| **Sans P17** (v41.4, 2000 j) | jour **477** | jour **493** |
| **Avec P17** | jour **243** | jour **332** |

**Les deux paliers sont franchis presque 2× plus tôt.**

⚠️ **Deux correctifs ont changé en même temps** — la maturité synchrone (v41.5) et P17
(v41.6). Cette accélération ne peut pas être attribuée à P17 seul : la maturité synchrone
supprime à elle seule des refus mesurés (7 sur le corpus précédent). L'attribution exigera
une ablation séparée.

### 7.2 État des 6 graines à j468

| Graine | Niveau | Promotions | Maîtrise max | Maturité max |
|---|---|---|---|---|
| g11 | 1/15 | 0 | 50 % | 0,278 |
| g22 | 1/15 | 0 | 55 % | 0,336 |
| g33 | 1/15 | 0 | 45 % | 0,225 |
| **g44** | **3/15** | **2** (j243, j332) | — | 0,400 |
| **g55** | **3/15** | **2** (j300, j361) | — | 0,400 |
| g66 | 1/15 | 0 | 55 % | 0,336 |

**2 graines sur 6 franchissent deux paliers** (contre 1 sur 4 en v41.4). Les 4 autres
plafonnent entre 45 % et 55 % de maîtrise — sous le seuil de 60 %, donc **un mur réel**,
pas un défaut de mesure : leur maturité maximale (0,225 → 0,336) reste loin de 0,400.

### 7.3 La distribution s'adapte réellement à l'échec

Sur g44 bloqué au niveau 3, la ligne de bilan montre le couplage attendu :

```
🎲 2 révision(s) · 0 incursion(s) — défi visé 33% | hors palier 0/2 réussis
```

Le **défi visé est tombé à 33 %** (contre 78-95 % au niveau 1 en début de run) : la
distribution a détecté l'échec et bascule vers la révision, **sans aucun `if`**. C'est
exactement le comportement recherché — et c'est la preuve que `P17_Poids_Defi` est bien
couplé à la maîtrise, donc que la distribution est dérivée et non figée.

### 7.4 L'incursion produit des victoires

**839 victoires sur 3179 épisodes hors palier — 26,4 %.**

L'agent réussit régulièrement sur des niveaux où il n'est **pas encore promu**. Sous
l'ancien pointeur, ces épisodes n'auraient jamais existé.

### 7.5 ❌ Ce que P17 ne corrige pas (à ce stade)

g44 au niveau 3 reste à **10 % de maîtrise** malgré la révision active. La révision
entretient les acquis, elle n'enseigne pas le palier courant. **Le mur d'`Empty-8x8`
tient.**

*Section à compléter à la fin du run (1000 j).*


---

## 8. Point d'étape à j932 — ce que P17 change, et ce qu'il ne change pas

### 8.1 ✅ L'effondrement au niveau 3 est enrayé

C'est le résultat le plus net, et il est directement comparable à v41.4 (même graine) :

| g44 au niveau 3 (`Empty-8x8`) | Sans P17 | **Avec P17** |
|---|---|---|
| Maîtrise maximale atteinte | **2 %** | **30 %** |
| Jours passés au palier | 1500 | 603 (run plus court) |

**L'agent n'est plus effondré** — il tient 30 % là où il était à 2 %. La révision entretient
réellement quelque chose. g55 donne le même chiffre (30 %), sur une graine indépendante.

**Mais 30 % reste sous le seuil de 60 %** : aucune 3ᵉ promotion, ni sur g44 ni sur g55, en
~600 jours au palier. **Le mur d'`Empty-8x8` tient.**

### 8.2 L'incursion travaille — 32 % de réussite hors palier

Sur g44 : **524 victoires sur 1649 épisodes hors palier**. Un tiers des incursions réussit.
Sous l'ancien pointeur, aucun de ces épisodes n'aurait existé.

### 8.3 🔴 Un bloquant documenté du projet a DISPARU — la patience

Le dépôt documente depuis des semaines *« le bloquant le mieux mesuré du projet : la
patience plafonne à 120 ticks contre 256 pour MiniGrid lui-même — réussite atteignable
4,7 % contre 21,0 % »*.

**Mesuré sur ce run :**

```
⏳ Patience de base du jour: 273 ticks/épisode (0 abandon(s) lucide(s), patience_min: 220)
```

| | Valeur documentée | **Mesurée ce soir** |
|---|---|---|
| Patience | 120 ticks | **258 → 273 ticks** |
| Abandons lucides | — | **0** |

> ⚠️ **L'agent dispose de plus de temps que MiniGrid n'en alloue (256), et n'en utilise même
> pas la totalité — zéro abandon lucide.** Le bloquant « patience » de l'étape 4a de la
> feuille de route **n'existe plus** : il a été résorbé par la patience adaptative sans que
> la documentation soit mise à jour.
>
> **Conséquence** : l'agent a le temps qu'il faut. S'il échoue sur `Empty-8x8`, ce n'est pas
> faute de pas disponibles. L'étape 4a est **sans objet**, et il faut corriger le §2.4e de
> l'état des lieux et le §3.7 qui l'annoncent encore comme le bloquant principal.

### 8.4 Le métabolisme reste déficitaire

```
r_bio cumulé -2,745 — 4 Nourriture(s), 4 Eau(x) consommée(s)
r_bio cumulé -3,778 — 3 Nourriture(s), 2 Eau(x) consommée(s)
```

L'agent **mange et boit** (3 à 5 unités par jour, la boucle corporelle fonctionne), mais
`r_bio` cumulé reste **négatif** : le déficit structurel identifié en v41.2 (§2.6) n'est pas
résorbé. C'est cohérent avec le diagnostic d'alors — la trouvabilité, pas le barème.
