# Nuit du 15 au 16 août 2026 — trois questions posées, trois mesures

> **Nature** : carnet d'enquête. Non normatif. Consigne les mesures brutes et les
> erreurs de lecture, y compris les miennes de la veille au soir.
>
> **Questions posées par l'utilisateur** avant de se coucher :
> 1. La patience n'est **pas dérivée** comme le reste — la travailler et la muscler dès le
>    plus jeune âge.
> 2. Le problème métabolique : **agent ou nourriture** ? Ou les deux ?
> 3. **Mesurer l'apprentissage par victoire.**

---

## Q1 — La patience : ⚠️ JE ME SUIS TROMPÉ HIER SOIR

### Ce que j'ai affirmé (à tort)

> *« L'agent dispose de plus de temps que MiniGrid n'en alloue (256), et n'en utilise même
> pas la totalité — zéro abandon lucide. Le bloquant patience n'existe plus. »*

**C'est faux, et l'erreur vient d'avoir comparé à un seul chiffre (256) sans le vérifier
niveau par niveau.**

### Le budget réel de MiniGrid, mesuré

```python
env.unwrapped.max_steps
```

| Niveau | `max_steps` natif |
|---|---|
| `Empty-5x5` (**le palier où 4 graines sur 6 sont bloquées**) | **100** |
| `Empty-Random-6x6` | 144 |
| `Empty-8x8` | 256 |
| `SimpleCrossingS9N1` | 324 |
| `LavaGapS5` | 100 |
| `Fetch-5x5-N2` | 125 |

Le 256 que je citais est celui d'`Empty-8x8`, **pas** celui du palier bloquant.

### Ce que ça change

| Taux de succès | Patience calculée | / budget `Empty-5x5` |
|---|---|---|
| 0 % | 119 | **1,2×** |
| 30 % | 182 | 1,8× |
| 70 % | 266 | 2,7× |
| 100 % | 329 | 3,3× |
| *agent neuf* | *200* | *2,0×* |

> 🔴 **La patience du projet est TOUJOURS au-dessus du plafond natif sur `Empty-5x5`.**
> Elle n'a donc **aucun effet** à ce niveau : c'est `max_steps` qui coupe l'épisode, à 100
> ticks, quoi qu'il arrive.
>
> Les « 273 ticks / 0 abandon lucide » mesurés hier soir signifient donc **« l'agent
> n'atteint jamais SA patience »**, et non **« il a le temps qu'il faut »**. J'ai lu le
> second dans une donnée qui disait le premier.

**`max_steps` n'apparaît nulle part dans le code** (0 occurrence) : le projet n'a jamais lu
le budget que l'environnement lui accorde.

### Le second défaut — la patience est à l'envers

```python
potentiometre = 0.7 * taux_succes + 0.3 * facteur_vitesse
base_patience = patience_min + potentiometre * (patience_max - patience_min)
```

**Plus l'agent réussit, plus il a de temps. Plus il échoue, moins il en a.**

C'est l'inverse exact du principe demandé (*« la muscler dès le plus jeune âge pour qu'elle
permette en avançant de réussir »*) : un débutant qui échoue reçoit **119 ticks**, un expert
qui n'en a plus besoin en reçoit **329**.

Et `PATIENCE_MIN = 50` / `PATIENCE_MAX = 350` sont **posés en dur**, sans rapport avec le
budget réel de la carte — confirmant le diagnostic de l'utilisateur.

---

## Q2 — Le métabolisme : AGENT ou MONDE ? → **L'AGENT**

### Protocole

Retirer l'agent de l'équation : un **marcheur aléatoire** (actions tirées au hasard, qui
tente de consommer) survit-il sur la carte telle qu'elle est générée ? 400 ticks,
25 épisodes par cellule, moteur métabolique réel.

### Résultat

| Niveau | Politique | Survie | Morts | Nourriture | Eau |
|---|---|---|---|---|---|
| `Empty-5x5` | **aléatoire** | **400/400** | **0/25** | 4,4 | 3,8 |
| `Empty-Random-6x6` | **aléatoire** | **400/400** | **0/25** | 4,1 | 5,2 |
| `Empty-8x8` | **aléatoire** | **400/400** | **0/25** | 1,6 | 1,4 |

> ✅ **Le monde est vivable.** Un marcheur au hasard ne meurt **jamais**, sur les trois
> niveaux. Le déficit métabolique n'est **pas** un problème de trouvabilité.

*(L'oracle « va vers la ressource la plus proche » fait pire que le hasard — ma
heuristique de navigation est fausse. Sans effet sur la conclusion : si le hasard survit,
le monde suffit.)*

### 🔴 Le résultat qui fait mal

Comparaison de la consommation **par jour**, agent entraîné 1000 jours contre marcheur
aléatoire :

| | Nourriture | Eau |
|---|---|---|
| **Marcheur aléatoire** | **4,4** | **3,8** |
| **Agent réel, après 1000 jours** | **4,0** | **3,9** |

> 🔴 **L'agent mange exactement comme le hasard.** Après mille jours d'entraînement, sa
> consommation est indiscernable de celle d'un marcheur aléatoire — légèrement inférieure
> pour la nourriture.
>
> **Il n'a rien appris sur l'alimentation.** Le geste de manger existe (fix5), le
> soulagement lui est bien crédité (fix7), le contraste mesuré est de 15× entre affamé et
> repu — et pourtant le comportement ne se distingue pas du hasard.

**Réponse à la question : c'est l'agent, pas la nourriture.** Et ce n'est pas un problème
de motivation mal câblée : c'est un problème d'apprentissage — ce qui renvoie directement
à la question Q3.

---

## Q3 — Que change une victoire ? → **RIEN DE MESURABLE**

### A. La maîtrise ne progresse pas, sur la même carte, en 1000 jours

Les quatre graines jamais promues restent **toute leur vie sur `Empty-5x5`** : leur
maîtrise est donc directement comparable d'un bout à l'autre du run, sans biais de
changement de carte.

| Graine | Premier 10 % du run | Milieu | Dernier 10 % | Évolution |
|---|---|---|---|---|
| g11 | 21,6 % | 23,3 % | 23,4 % | +1,8 % |
| g22 | 28,5 % | 24,3 % | 24,3 % | −4,2 % |
| g33 | 23,2 % | 18,2 % | 21,5 % | −1,7 % |
| g66 | 25,6 % | 26,2 % | 22,5 % | −3,1 % |
| **Moyenne** | **24,7 %** | — | **22,9 %** | **−1,8 %** |

> 🔴 **Sur ~1000 jours et plusieurs milliers d'épisodes joués sur LA MÊME CARTE, la
> maîtrise ne progresse pas — elle baisse légèrement.**

### B. Une bonne journée n'annonce pas la suivante

Autocorrélation à 1 pas de la maîtrise différenciée, moyenne sur les 6 runs : **−0,019**.

Sur une série où l'apprentissage s'accumule, une bonne journée en annonce une autre
(corrélation positive). Ici, la valeur est **indistinguable de zéro** : chaque journée est
tirée indépendamment de la précédente.

### C. ⚠️ Mais le cerveau APPREND PHYSIQUEMENT — et beaucoup

C'est ce qui rend le résultat intéressant plutôt que trivial. Comparaison des poids de deux
cerveaux issus de la **même graine** (g11) sur deux runs distincts :

| Couche | Cosinus | Déplacement / norme |
|---|---|---|
| `tete_motrice` | **0,238** | **112 %** |
| `porte_visuelle` | 0,388 | 103 % |
| `analyseur` | 0,497 | 109 % |
| `hippocampe` | 0,541 | 95 % |
| `integrateur_bio` | 0,787 | 63 % |
| `cortex_prefrontal` | 0,882 | 48 % |

> Un cosinus de **0,24** sur la tête motrice signifie que les deux cerveaux ont des
> politiques **presque orthogonales**. Le gradient agit, massivement.

### 🎯 La conclusion des trois mesures

| Hypothèse | Statut |
|---|---|
| « Le cerveau n'apprend pas » (plasticité morte) | ❌ **réfutée** — les poids se déplacent de 100 % de leur norme |
| « L'agent n'est pas motivé » (récompense mal câblée) | ❌ **réfutée** — contraste affamé/repu de 15×, soulagement crédité |
| « Le monde est trop pauvre » | ❌ **réfutée** — un marcheur aléatoire survit 400/400 |
| **« L'agent apprend beaucoup, mais rien d'UTILE »** | ✅ **c'est ce que les mesures décrivent** |

**L'agent modifie massivement ses poids, sans que son comportement s'améliore.** Il
consomme comme le hasard (Q2), sa maîtrise stagne à ~23 % sur mille jours (Q3-A), et ses
journées sont indépendantes les unes des autres (Q3-B).

### Ce que cela oriente

La question n'est plus *« pourquoi n'apprend-il pas ? »* mais **« qu'apprend-il à la
place ? »**. Deux pistes, non testées à cette heure :

1. **Le signal d'apprentissage est dominé par le métabolique.** `r_bio` est versé à chaque
   tick (négatif en permanence, −2,7 à −3,8 par jour), la victoire une fois par épisode.
   Si le gradient est saturé par la survie, la victoire ne pèse rien — et l'agent apprend
   effectivement quelque chose : à gérer un déficit qu'il ne peut pas résoudre.
2. **Le crédit temporel ne remonte pas jusqu'à la cause.** Une victoire sur `Empty-5x5`
   demande ~10 pas ; si l'avantage n'est pas propagé, seul le dernier pas est renforcé.

---

## Les deux correctifs livrés cette nuit

### v41.7 — la nourriture n'avait aucune valeur apprise

**Le bug** : `enregistrer_evenement` était appelé pour `"FOOD"`/`"WATER"` **sans le
paramètre `intensite`**, donc avec sa valeur par défaut de `0.0` — alors que le seul autre
appelant transmet bien la sienne.

```
↑ 'goal' +0.515 (×1037)    ← appris
↓ 'FOOD' +0.000 (×4004)    ← 4004 repas, valence rigoureusement nulle
```

Même motif sur les 4 graines mesurées. L'abstraction par récurrence (v36.0) et l'empreinte
de type (v39.0) **moyennaient des zéros**, des milliers de fois.

> 🎯 **C'est l'explication mécanique du résultat Q2** : l'agent ne pouvait pas apprendre
> que la nourriture vaut quelque chose — le seul canal qui aurait pu porter cette
> information ne transportait que des zéros. D'où une consommation indiscernable du hasard
> après 1000 jours.

**Le correctif** transmet le soulagement réel, déjà calculé quinze lignes plus bas pour
`r_bio`. Rien de nouveau n'entre dans le système. **Rien n'est déclaré non plus** :
l'intensité est *mesurée* — manger rassasié écrit une intensité quasi nulle, manger affamé
une intensité forte.

**Vérifié** : `WATER` passe de `+0.000` figé à `+0.052 → +0.090 → +0.096`.

### v41.8 — la patience dérivée du budget de la carte

```
patience = max_steps × (0,45 + 0,55 × (1 − maîtrise))
```

| Maîtrise | `Empty-5x5` (budget 100) | `Empty-8x8` (budget 256) |
|---|---|---|
| 0 % | **100** (l'épisode entier) | **256** |
| 60 % | 67 | 172 |
| 100 % | 50 | 115 |

Le débutant reçoit tout, l'expert ~45 %. Même doctrine que le sevrage de l'aide (v41.3).

### Contrôle à j11 — les correctifs ne dégradent pas

| Graine | Maîtrise moy. j1-11, **v41.8** | v41.6 (sans correctifs) |
|---|---|---|
| g11 | **31 %** | 24 % |
| g22 | **36 %** | 34 % |
| g33 | **33 %** | 19 % |

Et **4 abandons lucides** seulement : la patience réduite ne tronque pas d'épisodes utiles.

⚠️ 11 jours ne prouvent rien — c'est un contrôle de non-régression, pas un résultat.

---

## Q3-suite — « Qu'apprend-il à la place ? » : le métabolique noie la victoire

La question laissée ouverte au §Q3 était : *si l'agent apprend massivement (cosinus 0,24)
mais ne s'améliore pas, qu'apprend-il ?* La récompense somme huit termes ; **personne n'en
avait jamais mesuré le poids relatif**.

Mesure de l'amplitude cumulée sur 400 ticks (ce qui compte pour le gradient est
l'amplitude, pas le signe), 20 épisodes par niveau :

| Niveau | `r_bio` (métabolique) | `recompense_env` (**la victoire**) |
|---|---|---|
| `Empty-5x5` | 5,36 — **90,0 %** | 0,60 — **10,0 %** |
| `Empty-Random-6x6` | 5,88 — **87,8 %** | 0,82 — 12,2 % |
| `Empty-8x8` | 4,92 — **98,5 %** | 0,08 — **1,5 %** |

> 🔴 **Le signal métabolique représente 88 à 98,5 % de ce que l'agent reçoit.** La victoire
> — le seul objectif du cursus — pèse **1,5 %** sur le palier où deux graines stagnent.
>
> La raison est structurelle : `r_bio` est versé **à chaque tick** (400 fois par journée),
> la victoire **une fois par épisode** (1,4 fois par 400 ticks au mieux, 0,1 sur
> `Empty-8x8`). Même à amplitude unitaire comparable, le rapport de fréquence est de
> **~300:1**.

### Ce que cela résout

Les trois mesures de la nuit forment maintenant une chaîne cohérente :

1. L'agent **apprend massivement** (poids déplacés de 100 % de leur norme).
2. Ce qu'il apprend est **à 90-98 % du métabolisme**, pas la tâche.
3. Et jusqu'à cette nuit, il ne pouvait **même pas** apprendre le métabolisme utilement,
   la valence de la nourriture étant figée à zéro (v41.7).

> **Il passait son temps à apprendre un déficit qu'il n'avait aucun moyen de résoudre.**

C'est la formulation mécanique de ce que le §2.6 du chantier v41.2 avait pressenti sans le
mesurer : *« un agent en famine permanente n'a rien à planifier, il n'a qu'une urgence »*.

### ⚠️ Ce que cela ne dit PAS

Ce n'est **pas** une preuve qu'il faut baisser `r_bio`. Deux lectures restent ouvertes :

| Lecture | Conséquence |
|---|---|
| Le métabolisme est **trop bruyant** | il faudrait réduire son amplitude par tick |
| Le métabolisme est **insoluble** | il faudrait le rendre satisfiable, et il cesserait de crier |

La v41.7 vient précisément de rendre la nourriture apprenable. **La campagne en cours
tranche entre les deux** : si la valence devient positive et que le déficit se résorbe, la
seconde lecture est la bonne et aucun réglage d'amplitude n'est nécessaire.

Aucune modification de `r_bio` n'a donc été faite cette nuit — mesurer d'abord.

---

## ⚠️ Contrôle à mi-campagne (j475) — le correctif v41.7 ne suffit pas

Le §Q3-suite laissait deux lectures ouvertes et annonçait que la campagne trancherait.
**Point d'étape à mi-parcours, et il est défavorable au correctif.**

### Ce qui a changé

| | Avant (v41.6) | **Après (v41.7)** |
|---|---|---|
| Valence `WATER` | **+0,000** figé | **+0,052 → +0,134** (elle vit) |

Le canal fonctionne : la valence est apprise, et `rappel marquant` est actif **98 à 100 %
des ticks** — l'information atteint bien le vecteur bio.

### Ce qui n'a PAS changé

| Mesure | v41.6 | **v41.7** | Marcheur aléatoire |
|---|---|---|---|
| Nourriture / jour | 4,0 | **4,0** | 4,4 |
| Eau / jour | 4,0 | **4,0** | 3,8 |
| Efficacité du geste | ~10 % | **~10 %** | — |
| `r_bio` moyen (début → fin) | −2,26 → −2,05 | **−2,07 → −1,99** | — |

> 🔴 **La valence est désormais apprise, et le comportement n'a pas bougé d'un pouce.**
> L'agent consomme toujours exactement comme un marcheur aléatoire, et le déficit
> métabolique reste stationnaire.

### Ce que cela apprend

Le correctif v41.7 était **nécessaire** (une valence figée à zéro sur 4004 expériences est
un bug, quoi qu'il arrive) mais **pas suffisant**. Savoir que la nourriture est bonne ne
suffit pas à aller la chercher.

Cela **renforce** la lecture « le métabolisme est trop bruyant » plutôt que « il est
insoluble » : rendre la nourriture apprenable n'a pas résorbé le déficit. À 90-98 % du
signal, `r_bio` reste vraisemblablement dominant au point que l'information de valence,
bien que présente, ne pèse rien dans la décision.

⚠️ **Aucune conclusion ferme à ce stade** : c'est un point d'étape à j475 sur 1000, et les
niveaux atteints ne sont pas encore comparables (g44/g55 étaient au niveau 3 en v41.6, donc
mesurés sur une carte plus difficile). Le bilan final départagera.

---

## 🏁 Bilan de la campagne de nuit (v41.7 + v41.8) — et le défaut qu'elle a révélé

⚠️ *Chiffres corrigés après achèvement des 1000 jours — une première lecture faite à
j965 donnait g55 au niveau 2, elle était prématurée.*

| Graine | v41.6 (P17 seul) | **v41.7 + v41.8** |
|---|---|---|
| g11 | niveau 1 | niveau 1 |
| g22 | niveau 1 | niveau 1 |
| g33 | niveau 1 | niveau 1 |
| **g44** | niveau 3 — **j243, j332** | niveau 3 — **j534, j587** ⚠️ |
| **g55** | niveau 3 — j300, j361 | niveau 3 — **j869, j989** ⚠️ |
| **g66** | niveau 1 | **niveau 3 — j305, j388** ✅ |

**Population : 3 graines sur 6 au niveau 3, contre 2 sur 6 en v41.6.**

Mais **le délai se dégrade sur les deux graines communes** (g44 : j243 → j534 ; g55 :
j300 → j869), et l'amélioration ne tient qu'à g66. Verdict **ambigu et globalement
défavorable sur la vitesse** — et la cause est un défaut de **ma** v41.8, pas des
correctifs eux-mêmes.

### La cause, mesurée sur g44

| | v41.6 | **v41.8** |
|---|---|---|
| Patience moyenne | 117 ticks | **70** ⚠️ |
| Abandons lucides | 107 | **161** ⚠️ |

> 🔴 **La v41.8 retirait du temps là où elle devait en donner** — exactement le défaut
> qu'elle prétendait corriger.

**Deux erreurs cumulées dans mon implémentation :**

1. **Mauvais ordre.** `_patience_budget` était appelé **avant** la modulation par l'envie,
   dont le facteur `(0,5 + 0,5 × envie)` divise ensuite jusqu'à 2. Un débutant censé
   recevoir l'épisode entier (100 ticks) n'en recevait que 50 à 70.
2. **Substitution au lieu de borne.** La cible *remplaçait* la valeur, effaçant la
   modulation par l'envie et par le thermostat.

**Correctif `v41.8-fix1`** : le budget s'applique **en dernier** et agit comme **plancher**.
Vérifié — à 0 % de maîtrise, une patience entrante de 50, 100 ou 140 donne toujours **100**
(le budget) ; à 100 % de maîtrise elle retombe à 50.

### ⚠️ Leçon de méthode

C'est la **deuxième fois en deux jours** qu'un correctif de ma main produit l'inverse de
son intention et n'est rattrapé que par la mesure appariée :

| Correctif | Intention | Effet réel avant correction |
|---|---|---|
| P17 (v41.6) | sortir l'agent de la révision | l'y **enfermait** (défi à 2 %) — rattrapé avant run |
| Patience (v41.8) | donner du temps au débutant | lui en **retirait** (70 vs 117 ticks) — rattrapé après run |

La différence entre les deux : P17 a été testé **avant** lancement, la patience seulement
**après**. Une distribution se teste en trois lignes ; un effet de composition entre deux
modulations ne se voit qu'en conditions réelles — ou en lisant l'ordre des opérations.

---

## Le métabolique : ce qu'il faudrait pour rééquilibrer (aucune modification faite)

`r_bio` entre dans `recompense_interne` **sans aucun coefficient** — d'où sa domination
mesurée à 90-98 %. Calcul du facteur qui égaliserait les deux signaux :

| Niveau | `r_bio` | Victoire | Ratio | Coefficient nécessaire |
|---|---|---|---|---|
| `Empty-5x5` | 5,36 | 0,60 | **9×** | 0,112 |
| `Empty-Random-6x6` | 5,88 | 0,82 | 7× | 0,139 |
| `Empty-8x8` | 4,92 | 0,08 | **62×** | **0,016** |

> Il faudrait **diviser `r_bio` par 62** sur `Empty-8x8` pour que la victoire pèse autant.
> Ce n'est pas un réglage de coefficient — c'est un problème de structure.

### ⚠️ Pourquoi je n'ai rien modifié

1. **Baisser `r_bio` rendrait l'agent indifférent à sa survie** — le projet pose que le
   corps DOIT pousser (« c'est le corps qui pousse à manger pour vivre »). Un coefficient
   à 0,016 est un débranchement déguisé.
2. **Le coefficient dépendrait du niveau** (9× ici, 62× là) : une constante unique serait
   fausse partout, et une formule par niveau serait un chiffre en dur de plus.
3. **La piste « rendre le déficit soluble » a été tentée cette nuit et n'a pas suffi** :
   la v41.7 rend la valence apprenable, la consommation reste à 4,0/4,0 — identique au
   marcheur aléatoire.

**Trois options pour la suite, aucune neutre, toutes à arbitrer :**

| Option | Principe | Risque |
|---|---|---|
| Pondérer `r_bio` | le faire taire | l'agent cesse de se soucier de survivre |
| Espacer `r_bio` (verser par épisode, pas par tick) | corriger le **rapport de fréquence 300:1**, pas l'amplitude | change la granularité du signal corporel |
| Rendre le monde plus nourrissant | supprimer le déficit à la source | le monde est déjà vivable (un marcheur aléatoire survit) |

> 💡 **La deuxième option est la seule qui ne contredise aucun principe du projet** : elle
> ne touche ni à l'amplitude du corps ni au monde, seulement à la **fréquence** de versement
> — qui est la vraie cause du 300:1. Elle n'a jamais été testée.

---

## Campagne `v41.8-fix1` — point à mi-parcours (j478)

### Le fix de patience fonctionne

Distribution des patiences appliquées sur g44 : **366 jours à exactement 100** (le budget
entier d'`Empty-5x5`), 71 jours à 144 (`Empty-Random-6x6` en incursion P17), et des
valeurs jusqu'à 306 sur les cartes plus grandes. **La patience suit désormais le budget de
la carte jouée**, ce qu'elle ne faisait pas avant.

| g44 | v41.6 | v41.8 (bug) | **v41.8-fix1** |
|---|---|---|---|
| Abandons lucides (à j478) | — | 161 *(sur 1000 j)* | **40** |

⚠️ *Une moyenne brute des patiences donne 59 ticks, plus basse qu'attendu : elle est tirée
par les journées sans ligne de patience (485 lignes vides sur g44). Ce n'est pas un
symptôme — la distribution des valeurs réelles est correcte.*

### 🎯 Un résultat inédit : g22 promue au jour 23

| Graine | v41.6 | v41.7+v41.8 | **fix1 (à j478)** |
|---|---|---|---|
| **g22** | jamais | jamais | **j23, j128** → niveau 3 |
| g55 | j300, j361 | j869, j989 | **j336, j347** |
| g44 | j243, j332 | j534, j587 | *(pas encore)* |

**g22 n'avait jamais franchi un seul palier dans aucune campagne.** Sa promotion au
**jour 23** est la plus précoce jamais observée sur ce projet — le précédent record était
le jour 74 (v41.3, graine 42).

⚠️ **À ne pas surinterpréter** : c'est une graine, à mi-parcours, et le projet a déjà été
trompé exactement ainsi (g22 v41, niveau 4 en solo, invalidée par la population). Le bilan
final départagera.

---

## 🎲 Le résultat le plus dérangeant de la nuit — qui réussit change à chaque campagne

Trois campagnes, **mêmes six graines**, mêmes 1000 jours. Qui atteint le niveau 3 ?

| Graine | v41.6 | v41.7+v41.8 | fix1 *(j747)* | Total |
|---|---|---|---|---|
| g11 | — | — | — | **0/3** |
| g22 | — | — | ✅ | 1/3 |
| g33 | — | — | — | **0/3** |
| g44 | ✅ | ✅ | — | 2/3 |
| g55 | ✅ | ✅ | ✅ | **3/3** |
| g66 | — | ✅ | — | 1/3 |
| **Total** | **2/6** | **3/6** | **2/6** | |

### L'accord entre campagnes

| Paire | Accord |
|---|---|
| v41.6 vs v41.7+v41.8 | 5/6 |
| v41.6 vs fix1 | 4/6 |
| v41.7+v41.8 vs fix1 | **3/6** |
| **Moyenne** | **4,0 / 6** |

| Hypothèse | Accord attendu |
|---|---|
| Le succès est une propriété de la **graine** | **6/6** |
| Le succès est **pur hasard** (taux ~2,3/6) | ~3,6/6 |
| **Mesuré** | **4,0/6** |

> 🔴 **L'accord observé est à peine au-dessus du hasard pur.** g44 réussissait deux fois
> puis échoue ; g22 n'avait jamais rien franchi et devient la plus précoce du projet
> (jour 23). Seule g55 est stable sur les trois.
>
> **La réussite d'une graine n'est donc pas une propriété robuste** — ni de la graine, ni
> du correctif. Elle est dominée par le bruit.

### ⚠️ Ce que cela implique pour toutes les conclusions du projet

**Comparer deux campagnes sur 6 graines ne permet de distinguer aucun effet plus petit que
le bruit** — et le bruit vaut ici ±1 graine sur 6.

Cela vaut rétroactivement pour les lectures de cette nuit :

| Ce que j'ai écrit | Ce que le bruit permet d'affirmer |
|---|---|
| « v41.7+v41.8 : 3/6 contre 2/6, une graine de plus » | **rien** — dans le bruit |
| « fix1 restaure la vitesse (g55 : j869 → j336) » | plausible mais **non établi** sur une graine |
| « g22 promue au jour 23, record du projet » | **un fait**, mais pas la preuve d'un effet |

> **Conséquence de méthode** : toute campagne future visant à départager deux versions doit
> tourner sur **≥ 20 graines**, pas 6. En dessous, on mesure la loterie natale — exactement
> ce que la campagne v41 avait déjà démontré, et que je viens de re-démontrer sans le
> vouloir.

Le seul résultat de la nuit qui ne dépende pas de la population reste **les trois bugs
trouvés et corrigés** (valence nulle, patience inversée, patience écrasée), chacun établi
par une mesure directe et non par une comparaison de graines.
