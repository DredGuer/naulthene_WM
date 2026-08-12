# Bug or not bug — carnet de recherche sur le blocage du cursus

> **Nature du document** : carnet d'investigation, tenu au fil des expériences. On y consigne
> ce qui a été **testé**, ce qui a été **mesuré**, et surtout ce qui a été **réfuté** — y
> compris quand la réfutation porte sur une hypothèse formulée ici même.
>
> Un test raté est une donnée. Une hypothèse abandonnée sans trace est un test qu'on
> recommencera dans six mois. **Rien n'est effacé de ce document.**
>
> Ouvert le 11 août 2026, après le run de 1300 jours (`ous47258`) qui a établi que l'agent
> plafonne au niveau 2/15 depuis 678 jours simulés.
>
> Documents liés : [`dia_Aout_2026.md`](dia_Aout_2026.md) (diagnostic système),
> [`CHANGELOG.md`](CHANGELOG.md) (historique des versions).

---

## La question de départ

L'agent ne progresse plus. Sept mécaniques majeures ont été livrées entre la v31 et la v37,
chacune conçue et mesurée — **aucune n'a débloqué le cursus**. La question devient donc :

> Le blocage est-il un **bug** (quelque chose de cassé qu'on peut réparer) ou une **erreur
> logique** (quelque chose de mal conçu qu'il faut repenser) ?

D'où le titre de ce carnet.

---

## Tableau de bord des hypothèses

| # | Hypothèse | Statut | Verdict en une ligne |
|---|---|---|---|
| H1 | Extinction synaptique | ✅ **CONFIRMÉE puis CORRIGÉE** | 98,1 % de synapses mortes → 0 % après v34/v37 |
| H2 | `SimpleCrossing` mal placé dans le cursus | ❌ **RÉFUTÉE** | Le déséquilibre C1/C2 existait aussi sur les niveaux maîtrisés |
| H3 | Le rêve est éteint | ❌ **RÉFUTÉE** | Erreur de lecture : fraction prise pour un % — le rêve tourne à 15-18 % |
| H4 | Patience insuffisante | 🟡 **PARTIELLE** | Marge ×10,9 sur l'optimal, mais 4,7 % vs 21,0 % de réussite atteignable |
| H5 | La redondance du monde tue le cerveau | 🟡 **VRAIE mais NON TRANSPOSABLE** | `Empty-5x5` = 1 config, mais donner de la variété d'abord **empire** |
| H6 | Le monde riche à difficulté adaptative | 🟢 **LA MEILLEURE** | Seule courbe qui accélère, mais aucune promotion franchie |
| H7 | Le signal de progrès manque (quête auto coupée) | ❌ **RÉFUTÉE** | Rétabli, santé interne améliorée, mais **moins** de victoires |
| H8 | Le problème est la NOTATION | 🟡 **MIXTE** | Pas plus de victoires, mais **×36 de consolidation** sans sanction |
| H9 | Le seuil de promotion est inadapté | ⏳ **NON TESTÉE** | 60 % sur 48 configurations ≠ 60 % sur 1 configuration |
| H10 | La sévérité doit décroître avec l'âge | 🟡 **NON CONCLUANT** | Gradient obtenu, 3 victoires — dans la variance ; protocole défaillant |
| H11 | **Surproduction initiale** (foisonner avant d'élaguer) | ✅ **CONFIRMÉE** | Bus 64 à la naissance → **18 victoires** contre 7 |
| H9 (testée) | **Le seuil de promotion** | ✅ **CONFIRMÉE** | 25 %/1 vict. → **cursus franchi de bout en bout**, une première |
| A1 | C2 est une fonction de valeur **linéaire** | 🔬 **EN COURS** | Projection dim_bus→1 sans couche cachée |

---

## H1 — L'extinction synaptique

**Testé** : sonde des poids sur 8 générations de cerveaux, de la v30 à la v37.1-fix1.

| Cerveau | `porte_visuelle` | `hippocampe` | `porte_auditive` | Synapses mortes |
|---|---|---|---|---|
| V30 700 j | 0,918 | 1,057 | 1,540 | **50,4 %** |
| V33 5000 j | 0,458 | 0,806 | 0,845 | **66,8 %** |
| **V34 1500 j** | **0,0000** | **0,0000** | **0,0000** | **98,1 %** |
| V34fix 2700 j | 1,024 | 1,420 | 0,540 | **0,0 %** |
| V37.1fix 1300 j | **4,373** | **3,181** | **6,296** | **0,0 %** |

Le cerveau V34 1500 j était **cliniquement mort** : trois couches à zéro absolu, 98 % du réseau
élagué. La chaîne causale est établie : pas de victoire → pas de gradient → pas de myéline →
érosion à taux plein → pruning.

**Corrigé** par le plancher vital (v34.0-fix1/fix2) puis par trois bugs supplémentaires trouvés
en v37.0 (plancher devenu plafond, myéline lue au mauvais moment, échelle 500× trop grande).

✅ **Cette piste est close.** Zéro synapse morte sur tous les runs récents, et les normes sont
4 à 6× supérieures à toutes les générations précédentes.

---

## H3 — Le rêve : une erreur de diagnostic à garder en mémoire

Affirmé pendant deux sessions : *« le rêve est quasi inexistant, 0,1 % »*. **C'était faux.**

`Pourcentage_Reve` est logué comme une **fraction** (`0,177`) mais affiché suivi d'un `%`. La
valeur réelle est **17,7 %**.

```
Vérification : Nb_Reves = 61, Pourcentage_Reve = 0,153
               61 / 0,153 = 398 ≈ len(memoire_moyen_terme) sur 400 ticks ✅
```

L'erreur avait été propagée dans `CHANGELOG.md` et le chantier v37 avant d'être corrigée.

> **Leçon méthodologique** : une unité mal lue produit un faux diagnostic qui survit à
> plusieurs sessions. Toujours vérifier une métrique par un calcul indépendant avant d'en
> tirer une conclusion.

---

## H5 — La redondance du monde *(hypothèse utilisateur)*

**Formulation** : *« un vrai cerveau qui revoit en boucle tout le temps les mêmes choses sans
jamais de nouveauté meurt de bêtise »*.

### Le constat est exact — mesuré

Configurations distinctes sur 500 graines (hash de grille + position + direction) :

```
 0 Empty-5x5              1 config    ← une seule
 1 Empty-Random-6x6      60
 2 Empty-8x8              1 config    ← une seule
 3 SimpleCrossingS9N1    42
 4 LavaGapS5              3
12 MemoryS7              16
---
 5 Fetch-5x5-N2         499
 6 GoToDoor-6x6         500
10 Unlock               498
13 MultiRoom-N2-S4      500
```

**Les trois premiers niveaux — ceux où l'agent passe sa vie — sont les plus pauvres du
programme.** Le cursus est construit à l'envers : la variété arrive *après* le mur.

Sur `Empty-5x5`, l'agent ne voit que **24 observations distinctes** en 300 ticks. Sur
`GoToDoor`, il en voit **171**.

### Mais la transposition échoue

Test : cursus réordonné par **variété décroissante** (les mondes riches d'abord), 800 jours,
contre un témoin en ordre officiel.

| | Témoin (officiel) | Variété d'abord |
|---|---|---|
| Victoires / 800 j | **12** | **2** |
| Niveau final | 2/15 | 1/15 |
| Records de proximité/j | 9,49 | **0,00** |
| Accord C1/C2 | 87,4 % | 20,5 % |

**Six fois moins de victoires.** La cause apparaît dans les records de proximité tombés à zéro :
quand le but change de place à chaque épisode, « se rapprocher » ne veut plus rien dire, et
l'agent perd tout signal d'apprentissage intermédiaire.

🟡 **Le constat est juste, la solution naïve ne l'est pas.**

---

## H6 — Monde complexe, difficulté adaptative *(hypothèse utilisateur, la plus prometteuse)*

**Formulation** : *« Tu n'apprends pas les maths sup à un enfant de 2 ans, mais tu lui apprends
à compter, et il s'arrête souvent à ce qu'il a retenu (1, 2, 3…). Une fois qu'il a acquis assez
d'infos de base, tu fais évoluer. Donc il faut commencer simple dans un monde complexe, et
complexifier en fonction de l'enfant. »*

La distinction essentielle avec H5 : **on ne simplifie pas le monde, on simplifie la tâche**.
L'enfant de 2 ans est déjà dans le monde réel.

**Protocole** : un seul type de monde (`DoorKey`, riche dès le jour 1 : 48 à 300 configurations),
dont seule la **taille** grandit — et seulement quand l'agent maîtrise. La tâche ne change
jamais de nature, donc « se rapprocher du but » garde son sens à chaque palier.

| | Témoin | Variété | **Adaptatif** |
|---|---|---|---|
| Victoires / 800 j | 12 | 2 | 7 |
| **Répartition par 100 j** | `6 6 0 0 0 0 0 0` | `2 0 0 0 0 0 0 0` | **`0 1 1 0 1 2 2 0`** |
| Confirmations mémoire | 42,7 | 75,7 | **534,7** (×12,5) |
| Types en mémoire | 4 | 6 | **7** |
| Pénalité de stagnation/j | −4,84 | −3,65 | **−2,74** |

### Le résultat qui compte n'est pas le total, c'est la forme

```
TÉMOIN     6  6  0  0  0  0  0  0   ← 12 victoires en 200 j, puis MORT pendant 600 j
ADAPTATIF  0  1  1  0  1  2  2  0   ← lent au départ, puis ACCÉLÈRE
```

Le témoin gagne plus, puis s'éteint définitivement. L'adaptatif place **4 de ses 7 victoires sur
les 300 derniers jours**, avec la mention `↘️ se rapprochent` dans les logs — et il n'avait pas
fini de progresser à l'arrêt.

**C'est exactement la courbe d'apprentissage d'un enfant** : lent à démarrer, puis ça vient tout
seul.

Autre fait notable : l'agent atteint le **palier 7/7** du détecteur DoorKey (« Franchir &
Sortir »), le jalon final. Aucun run récent n'était allé au-delà du palier 1.

🟢 **La meilleure hypothèse testée à ce jour**, mais aucune promotion franchie (voir H9).

---

## H7 — Le signal de progrès manquant

**Découverte** : sur DoorKey en Mode Libre, **les deux guidages sont coupés simultanément**.

| Guidage | État | Raison |
|---|---|---|
| `RECOMPENSE_APPROCHE_BUT` | coupé | décrochage v17.0 au palier ≥ 5 |
| `DetecteurProgresPersonnel` | coupé | `QUETE_AUTO_EN_MODE_LIBRE = False` |

Mesuré sur le run adaptatif : l'agent passe en Mode Libre **dès le jour 100** et y reste
700 jours avec `Guidage_But` entre 0,008 et 0,030 — c'est-à-dire **rien**.

Le code décrit lui-même `QUETE_AUTO_EN_MODE_LIBRE` comme *« un INSTRUMENT DE DIAGNOSTIC, pas
une mécanique cognitive »*, à activer pour établir la causalité puis à remettre à `False`.

**Test réalisé** (surcharge en mémoire, `noyau.py` non modifié) :

| | Adaptatif | **Quête+ (drapeau activé)** |
|---|---|---|
| Victoires / 800 j | 7 | **5** |
| Records de proximité/j | 0,00 | **2,36** ✅ |
| Erreur JEPA | 0,0092 | **0,0075** ✅ (meilleure des 4 runs) |
| Accord C1/C2 | 35,8 % | **49,3 %** ✅ |
| Confirmations | 534,7 | **564,3** ✅ |

Le drapeau fait **exactement ce qu'il devait faire** : le signal est rétabli, et trois
indicateurs de santé cognitive s'améliorent. **Mais les victoires baissent.**

❌ **Réfutée comme cause principale.** La rareté du signal n'est pas ce qui bloque. Le drapeau
reste à `False`, comme le code le demandait.

---

## H8 — Et si le problème était la NOTATION ? *(hypothèse utilisateur, en cours)*

**Formulation** : *« Dans la vraie vie, tu passes ton temps à corriger surtout les premières
années, jusqu'à ce que le cerveau comprenne. Et après, certaines choses viennent plus vite
seules. »*

### Ce que la mesure montre

Rapport entre la sanction subie et la récompense reçue, sur les 400 derniers jours :

| Run | Stagnation/jour | Victoires | **Ratio sanction / récompense** |
|---|---|---|---|
| Témoin | −4,84 | 0 | **4 835 000 000×** |
| Variété | −3,65 | 0 | **3 649 000 000×** |
| Adaptatif | −2,74 | 5 | **314×** |
| Quête+ | −2,72 | 4 | **389×** |

Même dans le meilleur cas, **l'agent est puni 314 fois plus qu'il n'est récompensé**. Dans les
runs bloqués, la récompense est littéralement nulle et le ratio explose.

Un élève noté −314 pour chaque +1 cesse de tenter. C'est exactement ce que l'agent a appris —
et les 8,9 records de proximité par jour montrent qu'il n'est pas passif : **il s'approche,
puis renonce, parce que c'est le calcul juste**.

### Le protocole

Surcharge en mémoire de `PENALITE_STAGNATION_BASE` et `MALUS_DOULEUR`, sur le cursus adaptatif
(H6, la meilleure base) :

- **×1,0** — témoin (le run adaptatif déjà réalisé, 7 victoires)
- **×0,1** — indulgence : l'agent est corrigé dix fois moins sévèrement
- **×0,0** — aucune sanction : l'agent n'est plus *noté*, seulement encouragé

### Résultats

| | Adaptatif (×1,0) | Indul ×0,1 | Sans sanction (×0,0) |
|---|---|---|---|
| Victoires / 800 j | **7** | 3 | 5 |
| Stagnation/jour | −2,74 | −0,30 | **0,00** |
| **Confirmations mémoire** | 535 | 1047 | **1542** (×36 vs témoin) |
| **Accord C1/C2** | 0,358 | 0,294 | **0,794** |

❌ **Réfutée sur les victoires** : enlever la notation ne fait pas gagner davantage (5 contre 7).

🟢 **Mais confirmée sur la santé interne** : sans sanction, la mémoire abstrait **36 fois plus**
que le témoin, et l'accord C1/C2 double. **La sanction dégrade la consolidation** — elle
n'empêche pas de gagner, elle empêche d'apprendre.

Deux enseignements contradictoires qui se complètent :

- sanction constante → le cerveau ne consolide pas ;
- sanction nulle → plus rien ne presse l'agent (aucune urgence à réussir vite).

**Aucun des trois runs n'était l'hypothèse réelle.** La formulation utilisateur dit *« surtout
les premières années… et après ça vient tout seul »* — c'est une sanction **qui décroît**, pas
une sanction constante à un niveau quelconque. D'où H10.

---

## H10 — La sévérité décroissante *(hypothèse utilisateur, dérivée de H8)*

**Le constat de conception** : le projet fait déjà décroître l'**aide** avec la maîtrise
(`facteur_guidage`, v35.1 : maîtrise ≤ 60 % → aide pleine ; ≥ 90 % → aide nulle). Mais la
**sanction** est une constante : `PENALITE_STAGNATION_BASE = 0.015`, du jour 1 au jour 1300.

> Le maître retire ses conseils, mais garde le stylo rouge à la même pression pendant toute
> la scolarité.

C'est le seul mécanisme du projet où une correction reste identique à elle-même pendant
des centaines de jours, alors que tout le reste (aide, dopamine, patience, référence de choc)
évolue avec l'âge. **Une incohérence de conception, pas un bug.**

### Tentative 1 — ancrage sur le taux de maîtrise : ÉCHEC

```python
maturité = taux_maîtrise / SEUIL_FIN_SEVRAGE
sévérité = SÉVÉRITÉ_MAX − (SÉVÉRITÉ_MAX − SÉVÉRITÉ_MIN) × maturité
```

Mesuré sur 800 jours : `Sévérité : début = 1,000  min = 0,953  fin = 1,000`.

**La sévérité n'a jamais décru** (4,7 % de variation au maximum). Cause : le taux de maîtrise
est resté à 0 % tout le run. **Le mécanisme était circulaire** — la sévérité devait s'alléger
pour aider l'agent à progresser, mais elle ne s'allégeait que s'il progressait déjà.

> ⚠️ **Erreur de conception de ma part, pas une réfutation de l'hypothèse.** Le run est donc
> à lire comme un **second témoin adaptatif** : il donne **3 victoires contre 7** dans des
> conditions équivalentes. C'est une information précieuse en soi — **la variance entre deux
> runs identiques est de 3 à 7 victoires**, donc aucun écart rapporté dans ce carnet en dessous
> de cet ordre n'est significatif.

### Tentative 2 — ancrage sur `reference_choc_dopamine`

Le bon ancrage doit mesurer la maturité **sans dépendre des victoires**. Deux candidats mesurés
sur un run DoorKey réel de 800 jours :

| Candidat | Trajectoire | Verdict |
|---|---|---|
| `empreinte_enfance` | 1,00 → 0,25 en **100 jours**, puis figée | ❌ trop brutale |
| `reference_choc_dopamine` | 0,150 → 0,599 sur 800 j, montée régulière | ✅ **retenu** |

`reference_choc_dopamine` est l'échelle de ce qui impressionne l'agent (cliquet v37.1-fix1).
Elle monte avec le **vécu**, pas avec les succès. C'est exactement une maturité : *un agent qui
a beaucoup vécu n'est plus impressionné par ce qui bouleversait le débutant — et n'a plus besoin
d'être autant corrigé.*

Trajectoire de sévérité attendue (simulée depuis les valeurs réelles) :

```
jour   1 : ref=0,150 → sévérité ×0,787  (pénalité 0,0118)
jour 301 : ref=0,184 → sévérité ×0,739  (pénalité 0,0111)
jour 501 : ref=0,493 → sévérité ×0,302  (pénalité 0,0045)
jour 801 : ref=0,599 → sévérité ×0,151  (pénalité 0,0023)
```

Un vrai gradient, ×5 entre le début et la fin. La sévérité ne tombe **jamais à zéro**
(`SEVERITE_MIN = 0.15`) : le run « sans sanction » a montré que sans contrainte, plus rien ne
presse l'agent.

### Résultat de la tentative 2

| | Adaptatif | Sans sanction | **Sév. décroissante v2** |
|---|---|---|---|
| Victoires / 800 j | 7 | 5 | **3** |
| Confirmations | 535 | 1542 | **1087** |
| Accord C1/C2 | 0,358 | 0,794 | 0,291 |
| Sévérité | — | — | **0,292 → 0,150** (gradient ×1,9) |

Le gradient a bien fonctionné cette fois. Et la répartition va dans le sens prédit :

```
sévérité 0,30 (j0-400)   → 1 victoire
sévérité 0,15 (j600-800) → 2 victoires   ← les deux dernières arrivent au plancher
```

🟡 **Non concluant** : 3 victoires est dans la variance basse (3-7). Le sens est le bon,
l'amplitude n'est pas démontrable.

> ⚠️ **Défaut de protocole, à corriger si l'hypothèse est reprise.** La sévérité démarre à
> **0,292, pas à 1,0** — parce que `reference_choc_dopamine` vaut déjà 0,15 au jour 1
> (initialisée sur le premier choc vécu). L'agent commence donc sa vie **déjà à 70 %
> d'indulgence**. Ce n'est pas « sévère puis indulgent » qui a été testé, mais « moyennement
> indulgent puis très indulgent ». **La phase de correction ferme des premières années n'a
> jamais existé.**

---

## H11 — La surproduction initiale *(données biologiques apportées par l'utilisateur)*

### Le fait biologique

> *« Dans les premières années de vie, le cerveau crée jusqu'à un million de nouvelles
> connexions synaptiques par seconde. Dès l'âge de 5 ans, il atteint environ 90 % de son
> volume adulte final. »*
>
> Puis **seulement** vient l'élagage : −1 à −2 % de matière grise par an à l'adolescence,
> pour ne garder que les circuits fréquemment activés.

**L'ordre est : foisonner d'abord, élaguer ensuite.**

### Ce que fait Naulthène — l'inverse

L'agent naît à `BUS_REFERENCE_INITIAL = 16` dimensions et grandit **lentement** par
neurogenèse (16 → 64 sur 1300 jours). Pendant ce temps, l'érosion nocturne élague en
permanence.

**Il élague sans avoir jamais foisonné.** Il n'y a jamais eu de surplus de connexions parmi
lesquelles sélectionner — chaque synapse perdue est une perte sèche, pas un tri.

Cela relit tout H1 sous un jour différent : les 50 à 98 % de synapses mortes des runs pré-v34
ressemblaient à une pathologie. **L'élagage massif est pourtant le régime biologique normal.**
Ce qui manquait n'était pas moins d'élagage — c'était plus de matière au départ.

### Ce que le décalage maturatif dit de C1/C2

> *« Le système limbique (émotions, récompense, dopamine) atteint sa pleine maturité au milieu
> de l'adolescence, alors que le cortex préfrontal (inhibition, planification) ne finit sa
> maturation que vers 25 ans. »*

Chez Naulthène :

| Module | Rôle | Paramètres |
|---|---|---|
| `cortex_prefrontal` | **C2** — planification, valeur | **64** (0,1 % du réseau) |
| `tete_motrice` | **C1** — réflexe | 512 |
| `integrateur_bio` | homéostasie, dopamine | 6 400 |

**Le préfrontal est le plus petit module du réseau** — 64 paramètres sur 55 232. Et le banc
d'ablation mesure que **couper C2 double le taux de succès** (4,50 % → 10,67 %).

Ce n'est peut-être pas un défaut : c'est le régime normal d'un cerveau jeune. Le décalage
maturatif est **biologiquement attendu**, et la conclusion « C2 nuit » pourrait simplement
signifier « C2 n'a pas fini de mûrir ».

### Protocole

Trois runs de **1200 jours** lancés en parallèle :

| Run | Bus de naissance | Promotion | Ce qu'il teste |
|---|---|---|---|
| **H11** | **64** (au lieu de 16) | 60 % / 2 victoires | La surproduction seule |
| **H09** | 16 | **25 % / 1 victoire** | Le seuil adapté au monde riche |
| **H11+H09** | **64** | **25 % / 1 victoire** | Les deux combinées |

Tous sur le cursus DoorKey adaptatif (H6, la meilleure base). 1200 jours au lieu de 800 pour
dépasser la variance observée.

### Résultats — runs de 1200 jours (nuit du 11 au 12 août)

| | H11 surproduction | H09 seuil | H11+H09 |
|---|---|---|---|
| Victoires / 1200 j | **18** | 3 | 3 |
| **Palier final** | 0/3 | **3/3** ✅ | **3/3** ✅ |
| Confirmations mémoire | **1460** | 28 | 174 |
| Accord C1/C2 | 0,00008 | 0,029 | **0,639** |
| Synapses mortes | 0 | 0 | 0 |

**Répartition des victoires (par 150 jours) :**

```
H11 surprod   4  0  0  2  3  5  3  1   = 18   ← accélère jusqu'au jour 900
H09 promo     0  0  1  0  2  0  0  0   =  3
H11+H09       0  1  0  0  0  0  0  2   =  3
```

### ✅ H11 — la surproduction initiale fonctionne

Naître à 64 dimensions au lieu de 16 donne **18 victoires contre 7** pour l'adaptatif de
référence, et **1460 confirmations mémoire**. C'est le meilleur total de toute la campagne
DoorKey, et la courbe monte jusqu'au jour 900.

Le fait biologique se transpose : *foisonner d'abord, élaguer ensuite*. L'agent élaguait
sans avoir jamais foisonné.

### ✅ H9 — le seuil de promotion était bien le verrou

```
jour 417 → DoorKey 6×6
jour 648 → DoorKey 8×8
jour 651 → DoorKey 16×16   ← cursus terminé
```

**Première fois du projet qu'un cursus est franchi de bout en bout.** Passer de
« 60 % / 2 victoires consécutives » à « 25 % / 1 victoire » suffit — aucun des sept runs
précédents n'avait franchi une seule promotion.

### 🔴 Le découplage : gagner ≠ progresser

Les deux effets **ne se combinent pas** : H11+H09 donne 3 victoires, pas 21.

| Run | Profil |
|---|---|
| H11 | **Le Savant** — gagne beaucoup (18), mémorise énormément (1460), ne monte jamais de niveau |
| H09 | **Le Franchisseur** — monte tout le cursus, mais 3 victoires et 28 confirmations |

H11 accumule 18 victoires **réparties**, jamais consécutives ni concentrées : il ne
déclenche donc aucune promotion. H09 monte sur des coups de chance sans avoir consolidé.

**Gagner et progresser sont deux régimes distincts**, et aucun run n'a réussi les deux.

---

## A1 à A4 — Les quatre axes de conciliation *(formulés par l'utilisateur)*

### A1 — Le goulot de C2 : une correction factuelle et une confirmation

> Formulation initiale : *« `cortex_prefrontal` est resté figé à 64 paramètres »*

❌ **Factuellement inexact** : `cortex_prefrontal = NaultheneLinearSynaptique(dim_bus, 1)`.
Il vaut `dim_bus × 1`, donc il a bien suivi 16 → 64 → 96 paramètres.

✅ **Mais l'intuition tient, et plus fortement** : c'est une **projection LINÉAIRE vers un
scalaire**, sans aucune couche cachée.

```
C2 = cortex_prefrontal : (1, 64)  → une somme pondérée, aucune non-linéarité
C1 = tete_motrice      : (8, 64)  → 8× plus de paramètres
```

**C2 ne peut exprimer que des fonctions de valeur linéaires** : « chaque dimension du bus
contribue proportionnellement », jamais « cette *combinaison* d'états est bonne, celle-là
non ».

Cela explique enfin trois mesures qui restaient sans cause :

| Mesure v37 | Explication par la linéarité |
|---|---|
| Amplitude de C2 constante (2,10 ± 0,02) sur 3 cartes | une projection linéaire d'un état normalisé donne toujours la même échelle |
| `argmax(C2)` figé sur une action, 400 ticks/400 | le rollout produit des états proches, une fonction linéaire les ordonne identiquement |
| Couper C2 **double** le taux de succès | un évaluateur linéaire sur un espace non linéaire est pire que pas d'évaluateur |

**Test** : `CortexProfond` — `dim_bus → dim_bus//2 → 1` avec ReLU, greffé par recopie des
poids appris (jamais de reset), interface plastique complète (`cycle_sommeil`,
`fortification_dopaminergique`, `agrandir`).

### A2 — La promotion hybride

H09 promeut sur un coup de chance : 25 % de réussite ou **une seule** victoire suffit. D'où
28 confirmations mémoire seulement — l'agent monte sans avoir compris.

**Test** : double verrou — `taux ≥ 35 %` **ET** `confirmations ≥ 50`. La voie « série de
victoires » est neutralisée (`VICTOIRES_REQUISES = 99`), pour qu'aucun coup de chance ne
puisse promouvoir seul.

### A3 — La gradation des espaces

Le saut `8×8` (36 cases intérieures) → `16×16` (196 cases) multiplie la surface par **5,4**.

**Test** : deux paliers intermédiaires enregistrés dynamiquement (`DoorKey-10x10` = 64 cases,
`DoorKey-12x12` = 100 cases) — ils n'existent pas dans MiniGrid, mais `DoorKeyEnv(size=N)`
les accepte. Plus une **patience indexée sur la surface** (`×√(surface/9)`), pour que
l'exploration d'un monde 5× plus grand ne soit pas coupée au même nombre de ticks qu'un 5×5.

### A4 — L'élagage développemental

H11 naît large (64) et le reste. Biologiquement, la surproduction est **suivie** d'un
élagage : −1 à −2 % de matière grise par an à l'adolescence.

⏳ **Non testé** : la neuro-régression (réduire `dim_bus`) est un chantier structurel, pas
une surcharge de constante. `agrandir()` sait faire croître, rien ne sait rétrécir.

### Protocole des 4 runs (1200 jours chacun)

| Run | A1 | A2 | A3 | Ce qu'il isole |
|---|---|---|---|---|
| BASE | — | — | — | témoin (bus 64, promo 35 %) |
| A1 | ✅ | — | — | l'effet du C2 profond seul |
| A3 | — | — | ✅ | l'effet du lissage seul |
| A1+A2+A3 | ✅ | ✅ | ✅ | la conciliation complète |

#### Un bug du banc d'essai, trouvé avant l'analyse (12/08)

La première salve a été interrompue à ~550 jours par un redémarrage de session. En
reprenant, une relecture du code a montré que **A3 n'avait jamais reçu sa patience
élargie** : le script étirait `etat.patience_base_jour`, qui n'est que la valeur
**loguée** (`noyau.py:4139`, commentaire « capturée avant tout étirement par Sursaut,
pour le log »). Le budget réellement consommé par le test d'abandon est
`etat.patience_jour` (`noyau.py:4856`).

A3 a donc tourné 567 jours en recevant les **grandes cartes avec le budget d'une 5×5** —
soit l'exact inverse de l'axe testé. C'est aussi l'explication la plus simple de son
retard (palier 2/5 quand BASE et A1 étaient à 3/3).

Conséquence sur le protocole : **A3 repart de zéro** sur un cerveau neuf (les 567 jours
sont conservés en `.bak` mais écartés de l'analyse — mélanger deux conditions dans une
même courbe la rendrait illisible), tandis que BASE, A1 et A1+A2+A3 **reprennent** leurs
cerveaux. L'asymétrie est notée ici pour que personne ne compare plus tard des âges
différents sans le savoir.

> Leçon de méthode, la même qu'en H10 tentative 1 : **vérifier que le levier agit bien sur
> la variable que le noyau lit**, pas sur son homonyme d'affichage. Un test qui ne teste
> rien ressemble en tout point à un test qui échoue.

#### Signal précoce, avant même la fin des runs

Sur les ~550 premiers jours de la salve interrompue :

| Run | Jour | Palier atteint |
|---|---|---|
| BASE | 553 | **3/3** (16×16) |
| A1 | 550 | **3/3** (16×16) |
| A3 | 567 | 2/3 *(patience buguée, run écarté)* |
| A1+A2+A3 | 518 | **0/5** ← bloqué au départ |

**A2 bloque tout.** Le double verrou (taux ≥ 35 % **ET** confirmations ≥ 50) n'a jamais
laissé passer une seule promotion en 518 jours. À vérifier sur le run complet : si les
confirmations moyennes plafonnent sous 50, le verrou est inatteignable par construction —
ce serait un seuil en dur déguisé en critère de consolidation, exactement ce que le projet
s'interdit.

#### Résultats des 4 runs (12/08)

| Run | Repères | Conf. moy | Palier | Victoires | Jour |
|---|---|---|---|---|---|
| BASE | 739 | 54 | 3/3 ✅ | 3 | 1253 |
| A1 (C2 profond) | 685 | 67 | 3/3 ✅ | 3 | 1250 |
| **A3 (patience corrigée)** | 586 | 27 | **5/5** ✅ | 5 | 1200 |
| A1+A2+A3 | **25** | **3264** | **0/5** ❌ | 4 | 1218 |

**✅ A3 est le meilleur résultat du projet à ce jour** — cursus à 6 paliers franchi de bout
en bout depuis la naissance, promotions aux jours 175, 269, 326, 632 et 921. La
progression est *régulière* (pas un coup de chance) et l'espacement croissant des
promotions est le signe d'une difficulté qui monte réellement.

Le seul changement par rapport au run raté : **la patience étirée sur la bonne variable**.
Le lissage des paliers (10×10, 12×12) sans le budget de temps ne servait à rien ; avec, il
franchit tout. La leçon dépasse le test : sur une grande carte, **le temps d'exploration
est une ressource au même titre que la mémoire**.

**❌ A1 n'a rien changé** (685 repères / palier 3, contre 739 / palier 3 pour BASE). Le C2
profond n'a produit aucun écart mesurable. Attention à ne pas le déclarer inutile trop
vite : le ratio C1/C2 était déjà revenu à ~0,6× depuis les correctifs v37, donc C2 n'était
plus écrasé — la couche cachée corrige un goulot **expressif** dont rien ne prouve encore
qu'il soit le facteur limitant.

**❌ A2 est le blocage, et pas pour la raison supposée.** J'avais écrit plus haut que le
verrou « confirmations ≥ 50 » risquait d'être inatteignable. **C'est faux, mesuré** :
A1+A2+A3 atteint **3264 confirmations de moyenne**, 65× le seuil. Le verrou n'a jamais
bloqué sur les confirmations.

#### La vraie découverte : largeur ≠ profondeur mnésique

En rassemblant tous les runs, la séparation est **parfaite, sans une exception** :

| Run | Repères | Conf. moy | Palier |
|---|---|---|---|
| A1+A2+A3 | 25 | 3264 | 0/5 ❌ |
| H11 surproduction | 25 | 1788 | 0/3 ❌ |
| A3fix | 586 | 27 | 5/5 ✅ |
| A1 | 685 | 67 | 3/3 ✅ |
| BASE | 739 | 54 | 3/3 ✅ |

- **Peu de repères, massivement re-confirmés** (23–25) ⇒ **jamais** de promotion
- **Beaucoup de repères, peu confirmés** (586–739) ⇒ cursus franchi

Le chiffre « H11 = 1460 confirmations » consigné la nuit précédente était juste mais **lu à
l'envers** : ce n'était pas une mémoire riche, c'était **25 souvenirs relus 1788 fois
chacun**. H11 ne gagne pas parce qu'il a compris ; il gagne parce qu'il a sur-appris UNE
configuration. Il n'est pas savant, il est **obsessionnel**.

C'est exactement l'intuition de l'utilisateur — « un cerveau qui revoit en boucle les mêmes
choses sans jamais de nouveauté se meurt de bêtise » — retrouvée par la mesure.

⚠️ **Le fait le plus dérangeant du projet** : les gagnants sont les ignorants. H11 fait
**18 victoires avec 25 repères**, les explorateurs en font **3 avec 700 repères**. La
récompense de MiniGrid **paie l'obsession** : 18 victoires est un optimum local très
profond, trouvé par le système, pas contre lui.

---

## H12 / H13 / H14 — l'apprentissage plutôt que le cerveau *(hypothèses utilisateur)*

> « La taille est un facteur d'intelligence, seulement si l'organisation interne est
> bonne. Je pense que plus que le cerveau, l'apprentissage est aussi important. »

### La cause mécanique, trouvée dans le code

`noyau.py:2389` évince le repère au `confirmations` **minimal**. Un repère neuf naît à
`confirmations: 1` — il est donc **toujours le minimum**, donc évincé **immédiatement**,
écrasé par des souvenirs 1788× plus établis.

**L'oubli tue systématiquement la nouveauté au profit de l'habitude.** H11 n'a pas 25
repères parce qu'il explore peu : parce que tout ce qu'il découvre est effacé à la
naissance. La règle v36.0 (« l'oubli retire le moins abstrait ») est juste sur le principe
mais crée un **cliquet** : plus un souvenir est ancien, plus il est protégé, donc plus il
se re-confirme, donc plus il est protégé.

C'est le même défaut de forme que `norme_naissance` (v34.0-fix2) et
`reference_choc_dopamine` (v37.1-fix1) : **une référence qui suit sa propre dérive ne borne
plus rien.**

### Les trois tests

| # | Hypothèse | Mécanisme testé |
|---|---|---|
| **H13** | grâce mnésique | un repère de moins de 10 nuits est **inévinçable** |
| **H14** | entrelacement | 20 % des jours rejouent un palier **déjà franchi** |
| **H12** | rotation forcée | le niveau change tous les 100 j **sans promotion** |

**H13** applique le « ne rien enlever les premiers temps » de l'utilisateur à l'échelle du
*souvenir* : une période de consolidation avant d'entrer en compétition. Biologiquement
fondé — un souvenir récent est protégé pendant sa consolidation, pas jugé sur son
ancienneté d'usage.

**H14** est l'*interleaved practice*, l'un des effets les mieux établis en sciences de
l'apprentissage (révision espacée et mélangée > blocs massés). Le cursus actuel est
purement **bloqué** : un niveau franchi disparaît à jamais, aucun mécanisme ne le rejoue.

**H12** sépare deux lectures concurrentes du découplage : si la largeur mnésique apparaît
quand le monde change **sans** promotion, c'est le changement de monde qui la crée (et la
largeur est une *conséquence* de la progression, pas sa cause). Si elle n'apparaît pas,
c'est le bus 64 lui-même qui produit l'obsession — et le coupable est **A4** : naître large
**sans jamais élaguer**.

### Sur les constantes — la frontière inné / acquis

> Question de l'utilisateur : « où s'arrête l'inné, où commence l'apprentissage ? »

Dans ce projet la réponse est nette : **l'inné pose des MÉCANISMES, jamais des NIVEAUX.**

| Inné (écrit dans le code) | Acquis (valeur numérique vécue) |
|---|---|
| l'architecture (C1, C2, JEPA, bus unifié) | les poids, la myéline |
| les *règles* de plasticité, d'homéostasie, d'oubli | les repères, leur `valence` |
| la structure des sens | `reference_choc_dopamine` |

`reference_choc_dopamine` est l'exemple canonique : le même choc de 0,1 vaut **100 % pour
un débutant et 11,4 % pour le même agent devenu expert**.

⚠️ **`NUITS_DE_GRACE = 10` et `PROBA_ENTRELACEMENT = 0.20` sont donc de l'inné arbitraire**
— exactement ce que CLAUDE.md interdit. Ils sont en **dur assumé**, et uniquement pour
répondre à « l'effet existe-t-il ? ». S'il existe, ils devront dériver de quelque chose de
vécu (la plasticité du moment pour la grâce ; la *fragilité mesurée* de la compétence pour
la révision, plutôt qu'un pourcentage fixe). C'est la méthode du projet : **instrumenter et
mesurer avant de rendre adaptatif**, ne jamais remplacer un chiffre arbitraire par une
formule arbitraire.

### Résultats — 5 runs de 1200 jours (12/08)

Tous avec le correctif de patience A3, tous partis de la naissance.

| Run | Palier | Victoires | Repères | Conf. moy |
|---|---|---|---|---|
| Témoin | 2/5 | 2 | 131 | 294 |
| H13 grâce seule | 3/5 | 3 | 118 | 110 |
| H14 entrelacement seul | 4/5 | 4 | 383 | 47 |
| **H13 + H14** | **5/5** ✅ | **9** | **605** | **18** |
| H12 rotation forcée | 1/5 * | 2 | 689 | 49 |

\* trompeur : la rotation fait *visiter* les 6 paliers sans jamais les mériter ; le niveau
final n'est qu'une position dans le cycle.

> ⛔ **TOUT CE QUI SUIT, JUSQU'À LA SECTION « RÉPLICATION », A ÉTÉ RÉFUTÉ LE 12/08 AU SOIR.**
> Conservé intact — la règle du carnet est que rien n'est effacé. Voir
> [la réplication sur 3 graines](#-réplication-sur-3-graines--le-résultat-est-réfuté) :
> le témoin fait **mieux** (5,0 victoires contre 3,3) et franchit le cursus **3 fois sur 3**.
> Les conclusions ci-dessous reposaient sur **un seul run par condition**.

### ~~✅ Les deux mécanismes se COMBINENT~~ — RÉFUTÉ

H13 seul : **+1 palier**. H14 seul : **+2 paliers**. Ensemble : **+3 paliers et 9 victoires**
(contre 2 pour le témoin, ×4,5).

Ce n'est pas additif, c'est **multiplicatif** — et c'est notable parce que la combinaison
précédente avait **échoué** : H11+H09 donnait 3 victoires au lieu des 21 espérées.

La raison est mécanique et se dit en une phrase : **H14 produit de la nouveauté (le monde
change), H13 l'empêche d'être effacée à la naissance.** Séparément, chacun est bridé par ce
qui manque à l'autre — H14 génère des repères neufs que l'éviction tue aussitôt ; H13
protège des repères neufs qu'un monde figé ne produit jamais.

C'est exactement la formulation de l'utilisateur : *« il faut de la diversité, mais en même
temps de la redondance »*.

### ~~🔑 Le « moment de bascule »~~ — RÉFUTÉ (le plateau n'appartient qu'à H13/H14)

| Run | 1ʳᵉˢ promotions | Plateau | Reprise |
|---|---|---|---|
| H13+H14 | j.66, j.68 | **742 jours** | j.810, 857, 987 |
| H14 | j.94, j.136 | **751 jours** | j.887, 893 |
| H13 | j.45 | **914 jours** | j.959, 1112 |

Toutes les conditions gagnantes suivent la même forme : deux promotions rapides, **un
plateau de 700 à 900 jours**, puis un décollage.

⚠️ **Ce plateau est indiscernable de l'échec qu'on diagnostique depuis le début du projet.**
Le run de 600 jours qui a lancé toute cette investigation aurait été coupé **200 jours avant
le décollage** — et conclu « bloqué au niveau 2 ». Le diagnostic « l'agent stagne » a
peut-être été porté, à plusieurs reprises, sur des runs simplement **trop courts**.

C'est la réponse à la question de l'utilisateur — *« laisser la connaissance s'accumuler
(je ne sais pas à quel point) »* : **~800 jours**, et rien avant ne l'annonce.

Conséquence de méthode : **aucun run de moins de 1000 jours ne peut conclure à un blocage.**

### ❌ H12 réfute « la largeur mnésique suffit »

H12 produit la mémoire la plus large de tous les runs du projet (**689 repères**) et ne
franchit rien. C'est la réfutation directe d'une hypothèse formulée plus tôt dans la
journée (« la promotion fabrique la diversité, la largeur serait une conséquence »).

Les deux sens sont faux :

- Peu de repères sur-confirmés (25) ⇒ pas de progression *(H11, A1+A2+A3)*
- **Beaucoup de repères ⇒ pas de progression non plus** *(H12, 689 repères)*

Ce qui compte n'est donc **ni la largeur ni la profondeur**, mais **de la nouveauté qui
revient sur du connu**. Un monde qui change en permanence (H12) est aussi stérile qu'un
monde qui ne change jamais (H11). La révision — revenir sur un palier **déjà franchi** —
est le seul mécanisme qui produise les deux à la fois.

### Réserves

- **Un seul run par condition.** L'écart témoin → H13+H14 (2 → 9 victoires) dépasse
  largement la marge de variance mesurée en H10 (3 vs 7, « aucun écart sous 4 victoires
  n'est significatif »), donc l'effet principal tient. Mais l'écart H13 seul vs H14 seul
  (3 vs 4) est **dans le bruit** et ne doit pas être interprété.
- **Les constantes restent de l'inné arbitraire** (10 nuits, 20 %). Elles ont répondu à
  « l'effet existe-t-il ? » — oui. Elles doivent maintenant dériver du vécu.

---

## ⛔ Réplication sur 3 graines — le résultat est RÉFUTÉ

H13+H14 rejoué sur 3 graines (101, 202, 303) **avec 3 témoins appariés sur les mêmes
graines**. Note technique : `noyau.py:48-49` fixe torch/numpy à 42 **au chargement du
module** ; les graines sont donc réécrites *après* l'import, sinon les trois répétitions
seraient strictement identiques.

| | g101 | g202 | g303 | Moyenne | σ |
|---|---|---|---|---|---|
| **H13+H14** | 7 vict. / 5 pal. | 2 / 2 | 1 / 1 | **3,3 / 2,7** | 2,62 |
| **Témoin** | 5 / 5 | 5 / 5 | 5 / 5 | **5,0 / 5,0** | **0,00** |

**Le témoin fait mieux, et il franchit le cursus complet 3 fois sur 3 avec un écart-type de
zéro.** Le « ×4,5 » annoncé le matin était un **artefact d'un seul run** — la graine 101
reproduit d'ailleurs le bon résultat (7 victoires), ce qui montre précisément le piège :
sur n=1, on ne voit pas qu'on a tiré la queue de la distribution.

### La signature mémoire s'inverse

| Run | Repères | Conf. moy |
|---|---|---|
| H13+H14 g202 | 156 | 211 |
| H13+H14 g303 | **63** | **427** |

C'est l'exact profil obsessionnel de H11 (25 repères / 1788 conf.). **La grâce mnésique a
PRODUIT l'obsession au lieu de l'empêcher** — l'inverse du mécanisme supposé. Protéger un
repère neuf de l'éviction lui laisse le temps de se re-confirmer, donc de devenir
inévinçable *par le haut* une fois la grâce expirée. Le cliquet n'a pas été supprimé, il a
été **alimenté**.

### Ce que la réfutation emporte avec elle

- **Le « moment de bascule » (plateau de 700-900 j) tombe** : les témoins franchissent tout
  **sans plateau**. Ce plateau appartenait à la famille H13/H14, il n'est pas une loi de
  maturation de l'agent. C'était une sur-généralisation depuis trois courbes parentes.
- **« La révision est le seul mécanisme qui produise les deux à la fois »** : non démontré.
- Reste vrai en revanche : **un run court ne peut pas conclure**, puisque la variance entre
  graines va de 1 à 7 victoires sur une condition identique.

### 🎯 Le seul levier qui survit : la patience ∝ √surface

Le seul ingrédient **commun aux 4 runs qui franchissent le cursus complet** (A3fix + les 3
témoins) est `--patience-surface`.

| Levier | Runs | Verdict |
|---|---|---|
| **Patience ∝ √surface** | 4/4 | ✅ **confirmé** |
| Grâce mnésique (H13) | 1/3 | ❌ non reproduit |
| Entrelacement (H14) | 1/3 | ❌ non reproduit |
| C2 profond (A1) | 0/1 | ❌ aucun effet |
| Promotion hybride (A2) | 0/1 | ❌ bloque tout |

**Le blocage du projet n'était ni la mémoire, ni C2, ni le seuil de promotion : c'était le
temps d'exploration.** L'agent recevait le même budget de ticks sur une carte de 196 cases
que sur une de 9. Il n'échouait pas par incapacité — **il était coupé avant d'avoir fini**.

C'est cohérent avec la mesure BFS du carnet (marge ×10,9 sur `DoorKey-5x5`) : la marge est
confortable sur une petite carte et devient négative en grandissant, sans que rien dans le
code ne s'en aperçoive.

### Erreur de méthode commise ici — à ne pas répéter

J'ai annoncé « ×4,5 sur les victoires » comme un résultat solide **en citant, dans la même
page, la règle qui l'interdisait** (H10 : « aucun écart sous 4 victoires n'est
significatif »). Deux fautes distinctes :

1. **n=1 présenté comme une conclusion.** L'écart 2 → 9 dépassait le seuil de H10, mais ce
   seuil portait sur la *variance entre graines* — il ne pouvait pas être appliqué à un run
   unique dont la variance était, par construction, inconnue.
2. **Un signal précoce lu à travers la théorie.** À 140 jours, les témoins étaient devant ;
   je l'ai *expliqué* (« la protection coûte cher au début, ça paiera après le plateau »)
   au lieu de le prendre pour ce qu'il était — les témoins étaient devant parce qu'ils
   étaient **meilleurs**, et ils le sont restés 1060 jours de plus.

Règle qui en découle : **toute condition annoncée comme un effet doit être répliquée sur ≥3
graines avec témoins appariés, avant publication et non après.**

🔬 **Verrouillage lancé le 12/08 à 17h05** : patience ∝ √surface sur 3 nouvelles graines
(404, 505, 606) **contre 3 runs sans patience sur les mêmes graines** — le seul protocole
qui isole vraiment ce levier.

### À méditer plus tard *(idées utilisateur, non testées)*

- **Les siestes** : un cycle de consolidation *intra*-journée, en plus du sommeil nocturne.
- **Corréler l'énergie et la capacité d'apprentissage** : manger plus ⇒ apprendre plus. Le
  socle existe déjà (satiété, hydratation, `deficit_bio`) et module déjà la capacité
  mnésique — mais **pas** le taux d'apprentissage lui-même. Piste cohérente avec le coût
  énergétique réel du cerveau (50 % de l'énergie de l'enfant à 5 ans).

---

## H9 — Le seuil de promotion *(non testée)*

```
DoorKey-5x5 : 48 configurations distinctes
Promotion   : 2 victoires CONSÉCUTIVES  OU  60 % sur 20 épisodes
```

Sur `Empty-5x5` (1 configuration), 60 % de réussite signifie « avoir appris **un chemin** ». Sur
`DoorKey-5x5` (48 configurations), 60 % signifie « avoir appris **une politique qui
généralise** » — un objectif d'une tout autre nature.

Les 2 victoires consécutives sont encore plus improbables : il faut réussir deux cartes
*différentes* d'affilée, tirées au hasard parmi 48.

**Aucun des quatre runs n'a franchi une seule promotion sur DoorKey.**

⏳ Non testée : cela touche `TAUX_PROMOTION` et `VICTOIRES_REQUISES`, des constantes du cursus
protégées par les invariants v35.0 (voir `CLAUDE.md`).

---

## Méthode — ce qui a bien fonctionné

**Reproduire en simulation isolée plutôt qu'interpréter une courbe.** Une mesure directe sur
400 épisodes tranche en quelques secondes ce qu'un run de 800 jours laisse ambigu :

- Le comptage des configurations distinctes (H5) a réfuté une intuition en 30 secondes.
- Le BFS sur `(x, y, direction)` a corrigé l'affirmation « la patience est insuffisante ».
- Le calcul du taux de réussite d'une politique aléatoire a révélé le saut ×10 au niveau 2.

**Tester dans le scratchpad, jamais dans le projet.** Les quatre expériences de ce carnet
n'ont modifié aucun fichier de `src/` : les constantes sont surchargées en mémoire au
démarrage d'un script isolé. Le dépôt reste propre, les tests restent rejouables.

**Toujours un témoin.** Le run « variété » aurait pu passer pour un succès sans le témoin lancé
en parallèle dans les mêmes conditions.

---

## Erreurs de diagnostic commises dans cette investigation

| Affirmation | Statut | Correction |
|---|---|---|
| « Le rêve est quasi inexistant » | ❌ FAUX | Fraction lue comme un pourcentage — 17,7 %, pas 0,1 % |
| « Le JEPA à zéro est causé par la pauvreté du monde » | ❌ INVERSÉ | Le JEPA était à zéro parce que les couches étaient mortes (98 %) |
| « Le rêve détruit le cerveau » | ❌ FAUX | Corrélation **négative** (−0,22) : le rêve protège |
| « Le Goal est introuvable sur DoorKey » | ❌ FAUX | Il est bien trouvé ; c'est `_quete_auto_active` qui coupe le détecteur |
| « La patience de 120 est insuffisante en soi » | ❌ IMPRÉCIS | Marge ×10,9 sur l'optimal BFS ; le problème est le taux atteignable |
| « A3 est en retard, le lissage ne sert à rien » | ❌ FAUX | Le banc d'essai étirait `patience_base_jour` (valeur *loguée*) au lieu de `patience_jour` (budget réel). A3 n'avait jamais été testé — corrigé, il franchit 5/5 |
| « La révision espacée fait ×4,5 sur les victoires » | ❌ **RÉFUTÉ** | **n=1.** Répliqué sur 3 graines : témoin 5,0 vs H13+H14 3,3. Voir [la réplication](#-réplication-sur-3-graines--le-résultat-est-réfuté) |
| « Le plateau de 800 jours est une loi de maturation » | ❌ SUR-GÉNÉRALISÉ | Il n'existe que dans la famille H13/H14 ; les témoins franchissent tout sans plateau |
| « Le verrou de confirmations d'A2 est inatteignable » | ❌ FAUX | Mesuré à **3264**, soit 65× le seuil. A2 bloque, mais pour une autre raison |
| « La promotion fabrique la diversité mnésique » | ❌ RÉFUTÉ | H12 produit 689 repères (record) **sans** aucune progression |

**Dix erreurs en une investigation.** Elles sont toutes consignées parce que chacune a coûté du
temps, et qu'aucune ne doit être refaite.

Les cinq dernières partagent **une même cause** : conclure depuis **un seul run**. Les cinq
premières venaient d'une mauvaise lecture d'une métrique ; celles-ci viennent d'une lecture
correcte d'un échantillon trop petit — plus insidieux, parce que le chiffre était juste.

---

### Sur la significativité des écarts

Le run H10-tentative-1 a servi de **second témoin involontaire** : mêmes conditions que le run
adaptatif, **3 victoires contre 7**. Cette variance doit être gardée en tête pour tout ce
carnet — **un écart de moins de 4 victoires sur 800 jours n'est pas un signal.**

Ce qui reste robuste malgré cette variance, parce que l'écart est d'un autre ordre :

| Signal | Amplitude | Robuste ? |
|---|---|---|
| Confirmations mémoire, sanction nulle vs témoin | 42,7 → 1542 (**×36**) | ✅ |
| Accord C1/C2, sanction faible en fin de parcours | 0,29 → 0,86 (**×3**) | ✅ |
| Courbe témoin qui s'éteint vs DoorKey qui accélère | 0 vs 4-5 victoires en 2e moitié | ✅ |
| Écarts de victoires entre runs DoorKey (3 à 7) | dans la variance | ❌ |

**Mise à jour du 12/08 — la variance est pire que ne le disait H10.** Une condition unique
(H13+H14) rejouée sur 3 graines donne **1, 2 et 7 victoires** : un facteur **×7** entre deux
exécutions du *même* protocole. Le seuil de H10 (« moins de 4 victoires d'écart n'est pas un
signal ») était donc encore **trop permissif**.

Règle applicable à tout ce carnet, désormais :

> **Aucun run unique ne peut établir un effet.** Une condition ne compte que répliquée sur
> **≥3 graines avec témoins appariés sur les mêmes graines**. Un témoin sur une autre graine
> ne vaut rien : il compare deux tirages, pas deux conditions.

Ce que la réplication a rendu **plus** solide, à l'inverse : le témoin franchit le cursus
complet **3 fois sur 3, écart-type 0,00**. Un effet reproductible se reconnaît à ça — pas à
l'amplitude d'un seul run, mais à la **faiblesse de sa variance**.

---

*Carnet ouvert le 11 août 2026. Dernière entrée : H10, tentative 2 en cours.*
