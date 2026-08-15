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
> [`CHANGELOG.md`](../fonctionnement/CHANGELOG.md) (historique des versions).

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
| **H16** | **La loterie d'amorçage** (un bon départ détermine le run) | ❌ **RÉFUTÉE** | À protocole identique, `niv_j200 → niv_j1200` : **rho = −0,003** |
| **H17** | **La mémoire spatiale sépare les runs** | 🟡 **CORRÉLATION RÉELLE, CAUSALITÉ INVERSÉE** | rho = **+0,77** (p = 0,006), mais **la promotion efface la mémoire** — c'est la stabilité de la carte qui fait la mémoire, pas l'inverse |
| **H18** | **La promotion efface l'abstraction avec les coordonnées** | ✅ **MÉCANISME CONFIRMÉ** | `reinitialiser_niveau()` vide **100 %** de la mémoire à chaque palier — journal à l'appui |

---

## H17 — Ce qui distingue g22 : il a mémorisé le but *(signal fort)*

> Analyse des `.brain` de la campagne 2a, coût de calcul **nul**.
> Proposition P2.b de [AVIS_ET_PROPOSITIONS_aout_2026.md](../ameliorations/AVIS_ET_PROPOSITIONS_aout_2026.md),
> devenue la seule piste ouverte sur la variance après la réfutation de H16.

### Le point de départ

g22 (continuité, **69 victoires**, cursus complet en 239 jours) est traité depuis le début
comme un outlier à neutraliser dans les moyennes. Question inverse : **que contient-il que
ses onze frères n'ont pas ?**

### Le cerveau de g22 est structurellement BANAL

Comparé à ses cinq frères de condition (mêmes protocoles, graines différentes) :

| Mesure | g22 | frères (moy.) | rapport |
|---|---|---|---|
| Victoires | 69 | 2,6 | **26,5×** |
| Norme synaptique totale | 48,32 | 47,39 | 1,02× |
| Myéline moyenne | 0,0015 | 0,0015 | 1,04× |
| `reference_choc_dopamine` | 0,608 | 0,611 | 1,00× |
| `dim_bus` | 96 | 96 | 1,00× |
| Couches au plancher vital | 1/12 | 1/12 | — |
| **Souvenirs spatiaux** | **241** | **52,6** | **4,58×** |

**Un agent 26 fois plus performant a exactement le même tissu synaptique.** Ni la
neurogenèse, ni la myélinisation, ni l'homéostasie dopaminergique ne le distinguent. Une
seule chose sort : **la mémoire**.

### La corrélation tient sans lui

Sur les 12 cerveaux, `souvenirs ↔ niveau atteint` :

| Population | n | rho | p (permutation, 50 000) |
|---|---|---|---|
| Tous | 12 | **+0,772** | **0,0055** |
| **Sans g22** | 11 | **+0,701** | **0,0199** |

Ce n'est donc pas un artefact de l'outlier : c'est un gradient qui traverse toute la
population.

### ⚠️ La contre-épreuve indispensable : cause ou conséquence ?

Un agent qui gagne beaucoup visite beaucoup, donc mémorise beaucoup. La corrélation
pourrait n'être qu'un compteur d'activité déguisé. **La structure des souvenirs tranche.**

| Cerveau | Souvenirs | dont `goal` | Victoires |
|---|---|---|---|
| **continu g22** | 241 | **21** | **69** |
| continu g11 | 14 | **0** | 1 |
| continu g33 | 75 | **0** | 3 |
| continu g44 | 72 | **0** | 4 |
| continu g55 | 54 | **0** | 3 |
| continu g66 | 48 | **0** | 2 |
| témoin g11 | 108 | **0** | 3 |
| témoin g22 | 45 | **0** | 1 |
| témoin g33 | 127 | **0** | 2 |
| témoin g44 | 50 | **0** | 1 |
| témoin g55 | 21 | **0** | 0 |
| témoin g66 | 35 | **0** | 2 |

> **g22 est le SEUL des douze cerveaux à posséder un seul repère de type `goal`. Il en a 21.
> Tous les autres en ont exactement zéro.**

Et le témoin g11 le confirme par l'absurde : **108 souvenirs, aucun `goal`, 3 victoires**.
Accumuler des repères ne suffit pas — il en avait sept fois plus que `continu g11` sans
faire mieux. Ce n'est pas la *quantité* de mémoire qui compte, c'est **ce qui est
mémorisé**.

### Ce que ça dit du mécanisme

La mémoire de g22 n'est pas un journal d'activité : c'est une **carte du but**. Les 21
repères `goal` (dédupliqués par `(pos, type)`, donc 21 *lieux* distincts) constituent
littéralement la connaissance « voilà où se trouvent les sorties ». Ses autres repères sont
d'ailleurs *moins* confirmés que ceux de ses frères (médiane 18 contre 55-114) : il n'a pas
ressassé quelques cases, il en a **cartographié beaucoup**.

Le mécanisme v36.0 (abstraction par récurrence) a donc fonctionné exactement comme prévu —
**sur un seul run sur douze**. Il n'est pas cassé : il n'est presque jamais **amorcé**.

### Pourquoi c'est cohérent avec tout le reste

Cela résout l'ambiguïté laissée par l'ablation mnésique (écarts 0, −3, +1, « non
concluant ») : couper la mémoire d'un agent **qui n'a mémorisé aucun but** ne pouvait rien
changer. On mesurait l'ablation d'un organe vide.

Et cela recoupe le critère déjà posé pour les sens :

> *Un sens n'est utile que s'il apporte une information qu'aucun autre canal ne donne.*

La position du but est **exactement** cette information : dans un monde continu, le but
déjà atteint n'est plus visible, et seule la mémoire peut le redonner. C'est aussi pourquoi
l'effet apparaît en condition **continuité** — la seule où un « T+n » existe.

### ⚠️ Ce que cette analyse ne démontre PAS

- **n = 12, et un seul cerveau porte le phénomène `goal`.** Une corrélation significative
  ne dit pas le sens de la flèche : mémoriser le but peut être la cause des victoires, ou
  la conséquence d'en avoir assez remporté pour que le repère se crée.
- **Aucune intervention n'a été testée.** Tout ce qui précède est de l'observation
  rétrospective.

### ⚠️ Correction : la piste de l'éviction ne tient pas

J'avais d'abord conclu qu'il fallait **protéger le repère `goal` de l'éviction précoce**
(un repère naît à 1 confirmation, donc part en premier). **Vérification faite dans le code,
cette piste vise un mécanisme qui ne tourne pas.**

| | Valeur |
|---|---|
| Capacité mnésique (plancher, `capacite_plancher`) | **200** minimum |
| Capacité à `dim_bus=96` | `96 × 12 × (1+déficit)` ≈ **1 152**, bornée par `cases × 3` |
| Souvenirs réellement stockés (12 cerveaux) | **14 à 241** |

**L'éviction ne se déclenche quasiment jamais** : la mémoire n'est jamais pleine. Aucun
repère `goal` n'a donc été « perdu » par oubli — il n'a **jamais été créé**.

La question se déplace donc en amont, sur `_memoriser_si_saillant` et
`SEUIL_SAILLANCE_MEMOIRE` : **pourquoi atteindre le but ne produit-il pas un repère chez
onze cerveaux sur douze ?**

> C'est la **quinzième erreur de diagnostic** du carnet, et elle a été évitée de justesse :
> j'allais proposer un correctif d'éviction pondérée par la valence, séduisant et
> parfaitement inutile. Vérifier qu'un mécanisme **tourne** avant de proposer de
> l'améliorer — le même défaut que `SEUIL_CRISTAL = 0,80`, jamais franchi, et que la
> Cristallisation Souple censée protéger des couches qu'elle n'a jamais protégées.

### Ce que la vérification en amont a donné

Trois hypothèses testées, deux éliminées **par la mesure directe** :

| Hypothèse | Test | Verdict |
|---|---|---|
| Le but n'est pas lisible au tick de victoire (l'agent est téléporté avant) | `grid.get(agent_pos)` au tick terminal, sur MiniGrid réel | ❌ **le but EST lisible** : `type = 'goal'`, récompense 0,955 |
| Le `reset()` efface la case avant la mémorisation | ordre dans `traiter_tick` | ❌ mémorisation ligne **5141**, `reset()` ligne **5221** — l'écriture précède |
| Le seuil de saillance rejette l'événement | reste la seule voie possible | 🔬 **piste ouverte** |

Le mécanisme n'est donc **pas cassé** : dans les deux modes (continu et témoin), un agent
qui touche le but se tient sur une case étiquetée `goal` au moment exact où
`_memoriser_si_saillant` est appelé.

### L'anomalie qui reste, et qui n'est pas expliquée

Si le seul facteur était la rareté des victoires, on attendrait une proportionnalité. Elle
n'existe pas :

| Cerveau | Victoires | Confirmations `goal` | Lieux `goal` distincts |
|---|---|---|---|
| **continu g22** | 69 | **155** | **21** |
| continu g44 | 4 | **0** | 0 |
| continu g33 / g55 / témoin g11 | 3 | **0** | 0 |
| continu g66 / témoin g33 / g66 | 2 | **0** | 0 |

Un agent à 4 victoires devrait avoir ~4 confirmations `goal`. Il en a **exactement zéro**,
et c'est vrai des onze. Inversement g22 en a **155 pour 69 victoires** — plus de deux par
victoire, ce qui est cohérent avec le réarmement continu (le but est **repositionné** et
retouché plusieurs fois au même endroit) mais pas avec un simple comptage.

**Le phénomène est donc discret, pas graduel : soit un agent cartographie le but, soit il
n'en garde aucune trace.**

### ✅ L'explication, trouvée — et elle dégonfle mon propre résultat

Le chemin de code a été **exécuté** (et non relu) sur MiniGrid réel, en pilotant un agent
jusqu'au but puis en appelant la vraie fonction du noyau :

```
victoire, recompense_env = 0.9550
agent_pos = (3,3), grid.get = goal
_memoriser_si_saillant -> True
repere ecrit : {'pos': (3,3), 'type': 'goal', 'confirmations': 1, 'valence': 0.955}
```

**Le mécanisme fonctionne parfaitement.** Une victoire écrit bien un repère `goal`. Ni le
seuil (0,05 contre une récompense de 0,955), ni la lisibilité de la case, ni l'ordre
mémorisation/`reset()` ne sont en cause.

Reste donc une seule explication compatible avec toutes les mesures, et elle est
arithmétique :

| | continu g22 | les onze autres |
|---|---|---|
| Env. final | `DoorKey-16x16` | `DoorKey-5x5` à `12x12` |
| Victoires en 600 jours | **69** | **0 à 4** |
| Repères `goal` | 21 lieux, 155 confirmations | **0** |
| Souvenirs stockés | **241** *(> capacité 200)* | 14 à 127 *(< 200)* |

Les onze autres ont gagné **1 à 4 fois sur ~240 000 ticks vécus**. Le repère `goal` de
chaque victoire a bien été écrit — mais il représente moins de 0,002 % de leur vécu, et il
disparaît du `.brain` final.

⚠️ **Et ce n'est PAS l'éviction qui l'a retiré** : onze des douze cerveaux sont **sous la
capacité** (plancher 200), donc l'éviction n'a jamais tourné chez eux. Seul g22 la
déclenche (241 repères).

> **Je me suis trompé deux fois de suite au même endroit.** D'abord en proposant un
> correctif d'éviction (§ ci-dessus) alors que l'éviction ne tourne pas. Puis, en corrigeant,
> en réintroduisant **la même explication par l'éviction** sous une autre forme. La
> vérification numérique — « ces cerveaux ont-ils seulement atteint la capacité ? » — invalide
> les deux.

**Le devenir des 1 à 4 repères `goal` des onze autres cerveaux reste donc inexpliqué.**

### Les six vérifications faites, et ce qu'elles éliminent

Chaque voie a été testée **par exécution**, pas par lecture de code :

| # | Voie testée | Méthode | Résultat |
|---|---|---|---|
| 1 | Le but n'est pas lisible au tick terminal | agent piloté jusqu'au but, `Empty-5x5` | ❌ lisible (`type='goal'`, r=0,955) |
| 2 | Idem sur DoorKey (but derrière une porte) | clé ramassée, porte ouverte, but atteint | ❌ lisible (r=0,964) |
| 3 | Tenir la clé masque l'étiquette | `carrying=key` au tick de victoire | ❌ la case occupée **prime** sur le portage |
| 4 | Le seuil de saillance rejette l'événement | `SEUIL = 0,05` contre `r ≈ 0,96` | ❌ **19× au-dessus** du seuil |
| 5 | `reset()` efface la case avant l'écriture | ordre dans `traiter_tick` | ❌ écriture l.5141, `reset()` l.5221 |
| 6 | L'éviction / la troncature retire le repère | capacité 200-768 contre 14-127 stockés | ❌ **jamais atteinte** chez les onze |
| 7 | La déduplication au chargement le fusionne | `dedupliquer()` conserve un repère par `(pos,type)` | ❌ un `goal` unique survit |

Et la fonction réelle du noyau, appelée sur une vraie victoire DoorKey, écrit bien :

```
_memoriser_si_saillant -> True
{'pos': (3,3), 'type': 'goal', 'confirmations': 1, 'valence': 0.964}
```

**Le mécanisme est donc sain sur tous les chemins testés.** Un run instrumenté de 40 jours
(graine 22, témoin) a confirmé l'instrumentation elle-même — mais **0 victoire en 40 jours**,
donc aucune donnée sur le devenir du repère.

### ✅ LE MÉCANISME, TROUVÉ — la promotion efface la carte du but

Le run instrumenté a été lancé sur la **condition qui gagne** (2a continu + patience ∝
surface, graine 22). Le journal donne la réponse en trois lignes :

```
[ECRIT goal] tick=22091 pos=(1, 2) int=1.0035 taille 14->15
[ECRIT goal] tick=22142 pos=(1, 3) int=1.0119 taille 15->16

🎓 [PROMOTION] L'Agent passe en DoorKey 6×6 ! 🚀  (série de victoires)
```

Et le `.brain` sauvegardé juste après contient : `{'sol': 5, 'FOOD': 1, 'porte_key': 3,
'porte_ball': 1}` — **zéro repère `goal`**.

**Les repères sont bien écrits. Ils sont effacés par la promotion.**

```python
# noyau.py:5371, dans le bloc de promotion
etat.memoire_episodique_spatiale.reinitialiser_niveau()   # -> self.souvenirs = []
```

`reinitialiser_niveau()` **vide la mémoire spatiale entière** à chaque changement de
niveau. Son intention est raisonnable et documentée (*« les souvenirs d'un niveau précédent
n'ont plus de sens spatial une fois la carte changée »*), mais elle produit un effet de
bord que personne n'avait mesuré :

> **Un agent qui progresse perd toute sa mémoire spatiale à l'instant précis où il vient de
> prouver qu'il savait quelque chose.** Et il la perd au pire moment : le repère `goal`
> naît *au tick de la victoire*, donc quelques ticks avant la promotion qu'il déclenche.

Ce n'est **pas** une explication par la rareté ni par l'oubli : c'est un effacement
programmé, systématique, à 100 % des promotions.

### Pourquoi g22 est le seul à en garder

g22 a atteint le **dernier palier** (`DoorKey-16x16`) au jour 239, puis y est resté 361
jours en gagnant 65 fois. **Après la dernière promotion, plus rien n'efface sa mémoire** :
ses 21 repères `goal` sont ceux accumulés sur cette unique carte finale.

Les onze autres sont morts en cours de cursus (niveaux 0 à 4) : chacun a été **remis à zéro
à chaque palier franchi**, et leur dernier `goal` a été effacé par leur dernière promotion.

**La corrélation `souvenirs ↔ niveau` (rho = +0,77) s'explique donc en grande partie par un
artefact** : plus un agent est resté longtemps sans être promu sur sa carte finale, plus il
a de souvenirs. Ce n'est pas la mémoire qui produit la performance — c'est la **stabilité de
la carte** qui produit la mémoire.

### Ce que ça vaut comme piste

L'effacement pose une vraie question de conception, indépendante de tout ce qui précède :

| | |
|---|---|
| **L'argument pour** | une position `(1,2)` n'a pas le même sens sur une autre carte — garder les coordonnées serait trompeur |
| **L'argument contre** | on efface aussi **la valence apprise par type** (`goal` = 1,00 ; `sol` = 0,07), qui n'a rien de spatial et qui est exactement ce que la v36.0 cherchait à construire |

Autrement dit : le mécanisme jette **l'abstraction avec les coordonnées**. Or l'abstraction
par récurrence (v36.0) était précisément censée survivre au particulier — c'est sa raison
d'être. Un agent qui a appris « atteindre un `goal` est ce qui m'arrive de mieux »
(valence 1,00 contre 0,07) redécouvre cette leçon **à chaque palier**, de zéro.

**La proposition compatible avec la règle « rien en dur »** : à la promotion, effacer les
`pos` (qui n'ont effectivement plus de sens) mais **conserver la statistique par type**
(`valence`, `confirmations`) — qui n'est ni spatiale, ni nommée, ni déclarée. Le cerveau
garderait « ce genre d'endroit vaut ça » en perdant « c'était là ».

⚠️ **À tester, pas à croire.** Ce carnet vient de montrer que trois de mes explications
successives sur ce sujet étaient fausses. Celle-ci est **mesurée** (le journal ci-dessus),
mais son *effet* sur la performance ne l'est pas.

### Ce qui reste vrai, et ce qui tombe

| Affirmation | Statut |
|---|---|
| `souvenirs ↔ niveau`, rho = +0,77 (p = 0,006), sans g22 rho = +0,70 | ✅ **tient** |
| g22 est le seul à cartographier le but | ✅ **tient** (mesuré) |
| Le cerveau de g22 est structurellement banal (norme 1,02×, myéline 1,04×) | ✅ **tient** |
| « Mémoriser le but **cause** la performance » | ❌ **non démontré** — la causalité inverse suffit à tout expliquer |

**La flèche va très probablement dans l'autre sens** : g22 cartographie le but *parce
qu'*il gagne souvent, et non l'inverse. C'est exactement la contre-épreuve que j'avais
annoncée comme indispensable — et elle est défavorable à mon hypothèse.

### Ce qui subsiste comme piste réelle

Le mécanisme d'abstraction v36.0 a un **point de fragilité mesuré** : un repère rare et
précieux (le but, atteint 1 à 4 fois) est traité exactement comme un repère banal et
massif (`sol`, vu des milliers de fois). L'éviction retire le **moins confirmé** — donc
systématiquement l'événement rare, quelle que soit son importance.

La `valence` est déjà calculée, déjà stockée, et vaut **0,955 pour un but contre ~0,07 pour
le reste** (mesuré sur les 12 cerveaux : valence médiane 0,068-0,132). Elle distingue donc
déjà l'événement marquant du bruit — **sans qu'aucun type ne soit nommé**, exactement comme
la règle l'exige.

C'est la seule proposition qui survit à cette analyse, et elle est modeste : faire entrer
la valence dans le critère d'éviction, à côté des confirmations. Elle reste **à tester**,
et le résultat ci-dessus impose de la tester **contre** l'hypothèse nulle « la mémoire du
but n'est qu'un symptôme » — pas de la supposer acquise.

---

## H16 — La loterie d'amorçage *(RÉFUTÉE — et c'était mon hypothèse)*

> Analyse rétrospective sur les **142 runs W&B existants**, coût de calcul **nul**.
> Proposition P2.a de [AVIS_ET_PROPOSITIONS_aout_2026.md](../ameliorations/AVIS_ET_PROPOSITIONS_aout_2026.md).

### L'hypothèse

J'avais proposé que la variance ×69 entre graines ne soit pas du bruit mais un **effet
d'amorçage** : une victoire précoce lancerait le cercle vertueux (dopamine → myéline →
consolidation), son absence laissant le cerveau au plancher. Si c'était vrai, le levier
n'était plus statistique mais développemental.

### Le premier signal, séduisant et trompeur

Sur les 94 runs exploitables, le jour de la première victoire corrèle négativement avec le
nombre total de victoires : **rho = −0,533**. Une victoire précoce annonce un meilleur run.

**Ce chiffre ne vaut rien**, pour une raison mécanique : une première victoire au jour 704
laisse 496 jours pour en accumuler d'autres, contre 1199 pour une victoire au jour 1. La
corrélation mesure la durée restante, pas l'amorçage. À durée constante, le signe s'inverse
même sur un sous-groupe (400 j : **+0,457**).

### Le test qui tranche

Question reformulée pour échapper à l'artefact : **le niveau atteint au jour 200 prédit-il
le niveau final ?** Le niveau, contrairement au cumul de victoires, ne croît pas
mécaniquement avec le temps restant.

| Population | n | rho | p (permutation, 20 000) |
|---|---|---|---|
| Tous les runs de 1200 j | 33 | **+0,596** | **0,0004** |
| **Groupe TÉMOIN seul** *(protocole identique, graines différentes)* | 10 | **−0,003** | **1,0000** |

**Tout l'effet disparaît dès qu'on compare des runs qui ne diffèrent que par leur graine.**

### Les dix trajectoires témoins, brutes

```
niv_j200 = 0  ->  niv_j1200 = 5      niv_j200 = 2  ->  niv_j1200 = 2
niv_j200 = 0  ->  niv_j1200 = 2      niv_j200 = 2  ->  niv_j1200 = 5
niv_j200 = 1  ->  niv_j1200 = 5      niv_j200 = 2  ->  niv_j1200 = 5
niv_j200 = 1  ->  niv_j1200 = 5      niv_j200 = 3  ->  niv_j1200 = 4
niv_j200 = 1  ->  niv_j1200 = 4
niv_j200 = 1  ->  niv_j1200 = 4
```

| Départ à j.200 | n | Niveau final médian |
|---|---|---|
| Niveau 0-1 *(démarrage lent)* | 6 | **4,5** |
| Niveau 2-3 *(démarrage rapide)* | 4 | **4,5** |

**Exactement la même médiane.** Le meilleur run final (niveau 5) est parti de **zéro** à
j.200 ; l'un des pires (niveau 2) était **le plus avancé** de tous à j.200 (niveau 3, trois
victoires précoces).

### Ce que ça veut dire

Le rho = +0,596 sur la population mélangée n'était **pas** de l'amorçage : c'était un effet
de **condition expérimentale**. Certains protocoles vont mieux du début à la fin, ce qui
crée une corrélation début↔fin qui n'a rien d'individuel. La confondre avec de l'amorçage,
c'est attribuer à la trajectoire d'un agent ce qui appartient à son protocole.

**Trois conséquences :**

1. **Un mauvais départ n'est pas rattrapable — il n'a jamais été un handicap.** Il n'y a
   donc rien à « sauver » par une intervention précoce, et toute mécanique de type
   « garantir une première victoire tôt » viserait un problème inexistant.
2. **La variance ×69 reste inexpliquée.** Elle ne vient pas de l'amorçage. La piste
   suivante est [P2.b](../ameliorations/AVIS_ET_PROPOSITIONS_aout_2026.md#p2--dompter-la-variance-sans-la-tuer)
   (l'étude de g22), désormais la seule ouverte.
3. **Mesurer tôt ne sert à rien.** Un run évalué à j.200 n'annonce pas son résultat à
   j.1200 — l'espoir d'écourter les campagnes en jugeant sur les 200 premiers jours est mort
   avec cette hypothèse.

### La leçon de méthode

C'est la **quatorzième erreur de diagnostic** consignée, et elle appartient à la même
famille que les cinq précédentes : *une corrélation lue sur une population hétérogène*.
La correction n'a pas demandé un seul run — seulement de poser la question à l'intérieur
d'un groupe où une seule chose varie.

> **Un chiffre significatif (p = 0,0004) peut mesurer exactement le contraire de ce qu'on
> croit.** Ici, il mesurait la différence entre protocoles pendant que je lui faisais dire
> la trajectoire d'un individu.

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
| ~~**Patience ∝ √surface**~~ | ~~4/4~~ | ⛔ **réfuté le soir même** (+2/−1/+1 en apparié) |
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

### ⛔ Verrouillage de la patience — le dernier levier tombe aussi

Patience ∝ √surface sur 3 nouvelles graines (404, 505, 606) **contre 3 runs sans patience
sur les mêmes graines**.

| Graine | Avec patience | Sans patience | Écart apparié |
|---|---|---|---|
| 404 | 4 vict. / pal. 4 | 2 / 2 | **+2** |
| 505 | 4 / 4 | 5 / 5 | **−1** |
| 606 | 5 / 5 | 4 / 4 | **+1** |
| **Moyenne** | **4,33** (σ 0,47) | **3,67** (σ 1,25) | +0,67 |

**+2, −1, +1** : le levier gagne une fois, perd une fois. L'écart moyen est très en-dessous
du seuil de significativité du carnet.

Le point décisif est ailleurs — **la même condition ne se reproduit pas elle-même** :

| 6 runs, réglages *strictement identiques* | Victoires |
|---|---|
| témoins de l'après-midi (g101, 202, 303) | 5, 5, 5 |
| verrouillage (g404, 505, 606) | 4, 4, 5 |

L'écart-type nul des trois premiers (5/5/5), que j'avais présenté le matin même comme
**la marque d'un effet robuste**, était un **accident de trois graines**.

**Aucun des cinq leviers testés le 12/08 ne produit d'effet reproductible.**

---

## 🔬 La variance elle-même — la vraie découverte de la journée

> **Bémol de l'utilisateur (12/08, soir)** : *« ça ne peut pas être reproductible, car
> l'agent ne reproduit pas à l'identique sur tous les runs exactement le même comportement
> de départ, qui s'amplifie avec le temps ? »*

Le bémol contient **deux affirmations distinctes**. Mesurées séparément sur les 6 runs à
réglages identiques, **la première est vraie, la seconde est fausse** — et c'est l'inverse
qui se produit.

### ✅ « Le comportement de départ n'est pas reproductible » — CONFIRMÉ

Victoires cumulées, 6 runs strictement identiques, seule la graine change :

| Graine | j.50 | j.100 | j.200 | j.400 | j.800 | j.1200 |
|---|---|---|---|---|---|---|
| 101 | **2** | 2 | 2 | 2 | 5 | 5 |
| 202 | 0 | 1 | 1 | 3 | 4 | 5 |
| 303 | 1 | 1 | 1 | 1 | 3 | 5 |
| 404 | 0 | 0 | 1 | 3 | 3 | 4 |
| 505 | 0 | 1 | 1 | 1 | 4 | 4 |
| 606 | 0 | 0 | 0 | 0 | 3 | 5 |

À 50 jours : **0, 0, 0, 1, 2, 2**. Les trajectoires divergent dès le départ.

### ❌ « Ça s'amplifie avec le temps » — RÉFUTÉ, c'est l'inverse

| Jour | Valeurs | σ | Étendue |
|---|---|---|---|
| 50 | 2,0,1,0,0,0 | 0,76 | 2 |
| 200 | 2,1,1,1,1,0 | 0,58 | 2 |
| **400** | 2,3,1,3,1,0 | **1,11** | **3** |
| **600** | 4,3,1,3,2,1 | **1,11** | **3** |
| 800 | 5,4,3,3,4,3 | 0,75 | 2 |
| **1200** | 5,5,5,4,4,5 | **0,47** | **1** |

La dispersion **monte** jusqu'au jour 400-600 puis **redescend**. À 1200 jours, les six runs
tiennent dans un intervalle de **1 victoire**. Le run parti à 0 (g606) finit à 5 ; celui
parti à 2 (g101) finit à 5 aussi.

**Les trajectoires divergent, l'état final converge.**

### Ce que ça change

1. **Le résultat final EST reproductible** (4-5 victoires, 6 runs sur 6) ; c'est le
   **chemin** qui ne l'est pas. La conclusion du bémol (« donc rien n'est reproductible »)
   ne suit donc pas — mais sa prémisse était juste, et elle explique tous les faux positifs
   de la journée.

2. **C'est un bon signe pour l'architecture** : un agent dont les trajectoires divergent
   mais dont l'état final converge **apprend** quelque chose de stable, au lieu de subir son
   tirage initial. Une divergence qui s'amplifierait (l'hypothèse du bémol) signalerait au
   contraire un système chaotique, où le hasard initial déciderait de tout.

3. **⚠️ Je mesurais la mauvaise variable.** Comparer des *totaux de victoires* entre
   conditions, sur des courbes qui divergent puis reconvergent, revient à comparer les
   points d'arrivée d'un processus qui les égalise — donc à **jeter précisément
   l'information qui distinguerait les conditions**. Les 4,33 vs 3,67 mesuraient surtout du
   bruit de milieu de course.

   Ce qu'il faudrait comparer : des **vitesses** — jour de la première promotion, pente de
   progression, aire sous la courbe — et non des états finaux.

4. **La fenêtre de mesure utile se situe autour du jour 400-600**, là où σ est maximal.
   C'est là qu'un effet réel serait visible ; à 1200 jours, la convergence l'a effacé.

### Conséquence sur la puissance statistique

Avec σ ≈ 1,1 au point le plus dispersé, détecter un écart d'une victoire exige **8 à 10
graines par condition** (~12 h de calcul par condition sur cette machine). **3 graines ne
suffisent pas** — c'était encore trop optimiste, malgré la règle posée le matin même.

> **Règle définitive du carnet** : sur ce système, un effet ne s'établit ni sur un run
> (erreur du matin), ni sur trois (erreur du soir), mais sur **≥8 graines appariées, mesuré
> sur une vitesse et non sur un total, dans la fenêtre où la variance est maximale**.

### Ce qui reste debout, et ce n'est pas rien

**L'agent franchit le cursus de 6 paliers dans 11 runs sur 12**, toutes conditions
confondues (paliers atteints : 2 à 5, moyenne ≈ 4).

Le blocage historique — *« niveau 2 sur 15 depuis 678 jours »* — **n'apparaît dans aucun de
ces runs**. Ce qui a changé n'est aucun des cinq leviers testés, mais ce qui leur est
**commun** :

- les correctifs **v37** (érosion géométrique, myéline rafraîchie en tête de
  `cycle_sommeil`, échelle de myéline relative, plancher vital qui n'est plus un plafond) ;
- un cursus **DoorKey progressif à 6 paliers** (une seule compétence change entre deux
  paliers voisins) au lieu du `PROGRAMME` à 15 niveaux hétérogènes.

C'est-à-dire : **la réparation du cerveau et la cohérence du cursus** — pas les
raffinements d'apprentissage testés ensuite.

### À méditer plus tard *(idées utilisateur, non testées)*

- **Les siestes** : un cycle de consolidation *intra*-journée, en plus du sommeil nocturne.
- **Corréler l'énergie et la capacité d'apprentissage** : manger plus ⇒ apprendre plus. Le
  socle existe déjà (satiété, hydratation, `deficit_bio`) et module déjà la capacité
  mnésique — mais **pas** le taux d'apprentissage lui-même. Piste cohérente avec le coût
  énergétique réel du cerveau (50 % de l'énergie de l'enfant à 5 ans).

---

## H15 — Les sens sont-ils utilisés ? *(campagne d'ablation, 12/08 soir)*

### Ce que 77 runs W&B ont montré

Analyse de l'historique complet (197 Mo, runs ≥ 300 jours ; 53 stubs écartés, ~25 des 135
métriques réellement creusées — le vocal, le Port C3 et le calibrage métabolique restent
inexplorés).

**1. ✅ La v37 a réparé le cerveau — le seul effet massif de toute l'histoire du projet**

| Synapses mortes (max/run) | Médiane | Max |
|---|---|---|
| Avant les correctifs (n=30) | **13 769** | 77 169 |
| Après (n=47) | **0** | 77 729 |

**2. 🔴 Les sens sont branchés, mais inertes dans la décision**

Taux d'approche olfactive (0,50 = pile ou face), 17 runs de 1200 jours :

| Fenêtre | Taux |
|---|---|
| j.1-100 | 0,54 |
| j.500-600 | 0,57 |
| j.1100-1200 | 0,55 |

**Évolution médiane sur 1200 jours : +0,013.** Un apprentissage réel donnerait +0,10 à
+0,30. Corrélations avec les victoires : odorat **+0,13**, toucher **+0,32**, rappel
mnésique **−0,09** (négatif). La mémoire retrouve ses souvenirs (97-99 % de rappel réussi,
proximité 0,79) — ils n'influencent pas les décisions.

L'odorat topologique v32 (BFS, portes qui fuient, clinotaxie) est calculé *correctement* :
le signal est propre et injecté. L'hypothèse est que `integrateur_bio` n'apprend jamais à
le **lire**, parce que dans MiniGrid l'agent **voit déjà ce qu'il sent** — sentir une clé
qu'on voit n'apporte aucune information. Le sens serait **inutile, pas cassé**.

**3. ⚠️ Le cursus est plat — agrandir la carte ne rend pas la tâche plus difficile**

19 runs, délai médian pour franchir chaque palier :

| Transition | Surface départ | Délai médian |
|---|---|---|
| 5×5 → 6×6 | 9 cases | 91 j |
| 6×6 → 8×8 | 16 | **58 j** |
| 8×8 → 10×10 | 36 | 109 j |
| 10×10 → 12×12 | 64 | 85 j |
| 12×12 → 16×16 | 100 | 130 j |

**La surface est multipliée par 11, le délai par 1,4** — et le 6×6 → 8×8 est le plus
*rapide* de tous. L'échelle spatiale n'est donc pas un axe de difficulté pour cet agent :
il fait la même chose partout. Cela explique pourquoi les cinq leviers du 12/08 n'ont rien
produit — ils réglaient la difficulté d'un axe qui n'en est pas un.

⚠️ Corollaire : **une victoire n'est pas comparable d'un run à l'autre.** Les runs les plus
« rapides » (27 j/victoire) sont ceux qui restent sur les niveaux faciles.

### Bilan d'étape *(formulé par l'utilisateur)*

> - **Sous-exploitation de la multimodalité** : les sens sont actuellement inactifs dans la
>   prise de décision, alors que leur couplage est censé consolider l'apprentissage et
>   l'abstraction de l'environnement.
> - **Inadéquation de MiniGrid** : les règles discrètes ne fournissent pas des signaux
>   physiques suffisamment riches pour orienter naturellement les déplacements de l'agent.
> - **Perspectives** : enrichir l'environnement avec des contraintes physiques et
>   sensorielles réelles (odeurs, bruits, obstacles) ; réintroduire une **présence parentale
>   durable** pour étayer l'apprentissage à long terme.

Ce bilan est cohérent avec les trois mesures ci-dessus. Il reste une **hypothèse** tant que
l'ablation ne l'a pas confirmée : une corrélation faible peut aussi signifier un canal utile
mais redondant. Seule la coupure tranche.

### Protocole d'ablation

4 conditions × 3 graines (11, 22, 33) × 600 jours, **témoins appariés sur les mêmes
graines** — le protocole imposé par la leçon de variance de la journée.

| Condition | Tranches neutralisées |
|---|---|
| **TÉMOIN** | aucune (référence) |
| **chimie** | odorat + goût + clinotaxie |
| **toucher** | contact, portage, orientation |
| **mémoire** | rappel marquant + rappel spatial |

La coupure agit sur `vecteur_bio` (36 dims, disposition append-only stable depuis la v29.0,
`noyau.py:367`), en forçant chaque tranche à sa **valeur NEUTRE, jamais à zéro** :

- clinotaxie → **0.5** (invariant v32.0 (3) : 0.0 signifie « éloignement maximal »)
- rappel marquant → **[0.5, 0.0]** (invariant v36.0 (5) : une valence à 0.0 signifie « le
  pire souvenir possible » et rendrait l'agent craintif partout)

Mettre zéro mesurerait un effet qui n'existe pas — l'agent deviendrait *fuyant*, pas
*indifférent*. Le sens reste **calculé** (la télémétrie `Sens_*` demeure comparable entre
conditions), mais sa valeur n'atteint jamais `integrateur_bio`.

⚠️ **L'Exo-Sens n'est PAS amputé** (décision utilisateur explicite, conforme à l'invariant
v30.0 (2)) : `num_actions` reste à 8, `ACTION_DEMANDER` reste masquée à `-inf`, et 4 `.brain`
du dépôt sont déjà à 8 actions. Aucune ligne de `src/naulthene/` n'est modifiée — tout passe
par surcharge en mémoire.

**Prédiction à falsifier** : si couper la chimie ne change rien (écart < 1 victoire, mêmes
paliers), l'odorat et le goût sont démontrés **inutiles dans MiniGrid** — et le chantier
suivant porte sur le **monde**, pas sur le sens.

### Résultats — 12 runs de 600 jours (12/08, 20h05 → 21h15)

| Condition | g11 | g22 | g33 | Moyenne | σ | Écarts appariés |
|---|---|---|---|---|---|---|
| **TÉMOIN** | 2 | 3 | 3 | **2,67** | 0,47 | — |
| chimie coupée | 5 | 1 | 1 | 2,33 | 1,89 | +3, −2, −2 |
| **toucher coupé** | 0 | 1 | 1 | **0,67** | 0,47 | **−2, −2, −2** |
| mémoire coupée | 2 | 0 | 4 | 2,00 | 1,63 | 0, −3, +1 |

### 🔴 Le toucher est le seul sens démontré nécessaire

**−2 victoires sur les 3 graines, sans une exception.** C'est le **premier effet de toute
cette investigation qui va dans le même sens sur toutes les graines**, avec un écart-type
identique à celui du témoin (0,47) — donc sans l'explosion de variance qui a invalidé tous
les résultats précédents.

Couper le toucher fait chuter l'agent de 2,67 à 0,67 victoire : **−75 % de performance**.
Cohérent avec la corrélation W&B qui plaçait déjà le toucher en tête (+0,32 contre +0,13
pour l'odorat).

L'explication est mécanique : le toucher porte `contact_frontal` et surtout
**`objet_en_main`**. Sur DoorKey, *savoir qu'on tient la clé* est l'information la plus
décisive de la tâche. Ce n'est pas un sens exotique — c'est de la **proprioception**, et
c'est la seule modalité qui renseigne sur un **état interne que la vue ne montre pas**.

### ✅ La chimie (odorat + goût) ne sert à rien — hypothèse utilisateur confirmée

**2,33 contre 2,67**, écart de 0,33 victoire, très en-dessous du bruit. Les écarts appariés
sont incohérents (+3, −2, −2) et σ explose à 1,89. Le run le plus performant de toute la
campagne (5 victoires, g11) est même un run **sans odorat**.

C'est la confirmation directe du bilan d'étape : *les règles discrètes de MiniGrid ne
fournissent pas des signaux physiques suffisamment riches*. **L'agent voit déjà ce qu'il
sent** — l'odorat ne fait que redire ce que l'œil montre, et un canal redondant n'a aucune
raison d'être appris.

⚠️ Le sens n'est **pas cassé** : l'odorat topologique v32.0 calcule un signal correct
(BFS, portes qui fuient, clinotaxie). Il est **inutile dans ce monde**. La distinction est
capitale pour la suite : le chantier porte sur **l'environnement**, pas sur le capteur.

### ⚠️ La mémoire — non concluant

Écarts appariés 0, −3, +1 : le **signe change selon la graine**. Moyenne 2,00 contre 2,67,
mais σ = 1,63. Aucune conclusion possible sur 3 graines — et il ne faut pas répéter
l'erreur du matin en appelant cela un effet.

### Le critère qui en ressort pour la conception

Ce qui distingue le toucher des deux autres canaux tient en une phrase :

> **Un sens n'est utile que s'il apporte une information qu'aucun autre canal ne donne.**

- Le toucher renseigne sur un **état interne** (je porte / je ne porte pas) → utilisé.
- L'odorat renseigne sur une **position** que la vue donne déjà → ignoré.
- La mémoire spatiale renseigne sur des **lieux** que la vue redonne à chaque tick → ambigu.

Conséquence pour l'étape suivante : un monde qui exige l'odorat doit rendre la source
**invisible**, pas seulement odorante. Rendre un sens obligatoire ne se décrète pas dans le
capteur — cela se construit dans le monde, en **retirant à la vue** ce qu'on veut confier à
l'odorat.

### Ce que cette campagne ne dit pas

- **600 jours, pas 1200.** Les runs de la veille ont montré que certaines conditions ne se
  séparent qu'après le jour 800 ; un effet tardif de la chimie resterait invisible ici.
- **3 graines.** La règle posée le matin même exige ≥ 8 graines pour un écart d'une
  victoire. L'effet du toucher (−2 sur 3/3, σ nul) dépasse ce seuil ; ceux de la chimie et
  de la mémoire, non.
- **Aucune interaction testée.** Couper deux sens ensemble pourrait révéler une redondance
  (l'agent compense l'odorat par la vue, mais peut-être pas s'il perd les deux).

### ✅ Réponse définitive — campagne v41, 78 cellules (15/08)

→ [CAMPAGNE_v41_population_et_ablation_aout_2026.md](CAMPAGNE_v41_population_et_ablation_aout_2026.md)

Les trois réserves ci-dessus sont levées sur le volume : **78 cellules** (13 lésions × 3
niveaux × 2 cerveaux), 300 épisodes chacune, sur deux cerveaux v41 à 2000 jours, avec un
**témoin non nul** (8,7 % à 46,7 %) — le défaut qui avait invalidé le banc du 14/08.

**La réponse à H15 est : non, quatre sens sur six ne sont pas utilisés.**

| Lésion | Effet sur les 6 niveaux |
|---|---|
| Ouïe, Goût, Exo-Sens | **+0,0 × 6** |
| Odorat | +0,0 × 5, −0,7 × 1 |
| **C2 coupé** et **C2 myope** | **+0,0 × 6** ← le résultat qui domine la campagne |
| Toucher | **−4,4 / −5,4 / −6,7** (g11) — le seul sens qui coûte partout |
| Vecteur bio | −4,4 / −3,4 / **−8,0** — coût croissant avec la difficulté |
| Vue | instable : aide sur 3 niveaux, nuit sur 3 |

Cela **confirme et généralise** le constat de H15 (« les sens sont branchés, mais inertes
dans la décision ») : l'inertie ne concerne pas que la chimie, elle touche aussi **le
système délibératif entier**. Un C2 qu'on débranche sans que le score bouge d'un dixième de
point sur 6 niveaux ne participe pas à la décision.

Et un résultat que H15 n'anticipait pas : **les trois mémoires sont plutôt nuisibles** —
figer la mémoire de travail *améliore* le score sur 4 niveaux sur 6 (jusqu'à **+4,7**).

> **La conséquence de conception reste celle de H15, renforcée.** « Rendre un sens
> obligatoire ne se décrète pas dans le capteur — cela se construit dans le monde, en
> retirant à la vue ce qu'on veut confier à l'odorat. » Neuf mécaniques cognitives testées,
> neuf sans apport démontré ; les deux seuls leviers qui ont marché sont des propriétés du
> **monde**.

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
| « La patience ∝ √surface est le levier confirmé 4/4 » | ❌ **RÉFUTÉ le soir même** | Apparié sur 3 graines : +2, −1, +1. Le 4/4 était 4 tirages favorables |
| « σ = 0,00 sur 3 témoins prouve un effet robuste » | ❌ FAUX | Accident de 3 graines : les 3 suivantes, réglages identiques, donnent 4, 4, 5 |
| « La divergence entre runs s'amplifie avec le temps » | ❌ INVERSÉ | σ culmine à j.400-600 (1,11) puis **retombe** à 0,47 — les runs convergent |

**Treize erreurs en une investigation.** Elles sont toutes consignées parce que chacune a coûté du
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
