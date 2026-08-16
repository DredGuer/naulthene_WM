# Bilan de la nuit du 15 au 16 août 2026

> **Pour le point de 7h30.** Trois questions posées, trois réponses mesurées, trois bugs
> trouvés — et une remise en cause du protocole de mesure lui-même.

---

## 1. Les trois réponses

### Q2 — Le métabolisme : **c'est l'agent, pas la nourriture**

Protocole : retirer l'agent de l'équation. Un **marcheur aléatoire** survit-il ?

| Niveau | Survie | Morts |
|---|---|---|
| `Empty-5x5` | **400/400 ticks** | **0 / 25** |
| `Empty-Random-6x6` | 400/400 | 0 / 25 |
| `Empty-8x8` | 400/400 | 0 / 25 |

**Le monde est vivable.** Et le chiffre qui tranche :

| | Nourriture/jour | Eau/jour |
|---|---|---|
| Marcheur **aléatoire** | 4,4 | 3,8 |
| Agent **après 1000 jours** | **4,0** | 3,9 |

> **Après mille jours d'entraînement, l'agent mange comme le hasard.**

### Q3 — L'apprentissage par victoire : **il apprend beaucoup, mais rien d'utile**

Les 4 graines jamais promues restent toute leur vie sur la même carte :

| | Début du run | Fin du run |
|---|---|---|
| Maîtrise moyenne | 24,7 % | **22,9 %** |

Autocorrélation d'un jour à l'autre : **−0,019** — une bonne journée n'annonce pas la
suivante.

**Mais le cerveau apprend physiquement** : cosinus de **0,238** sur `tete_motrice` entre
deux runs de même graine, déplacement de **112 %** de la norme.

### Q3-bis — Ce qu'il apprend à la place : **le métabolisme noie la victoire**

Amplitude cumulée sur 400 ticks — **personne ne l'avait jamais mesurée** :

| Niveau | `r_bio` | **La victoire** |
|---|---|---|
| `Empty-5x5` | **90,0 %** | 10,0 % |
| `Empty-8x8` | **98,5 %** | **1,5 %** |

Cause : `r_bio` est versé **à chaque tick** (400×/jour), la victoire **une fois par
épisode**. Rapport de fréquence **~300:1**.

### Q1 — La patience : **tu avais raison, et je m'étais trompé**

J'avais affirmé la veille que « la patience n'est plus un bloquant ». **Faux** : j'avais
comparé au budget d'`Empty-8x8` (256), pas à celui d'`Empty-5x5` — qui vaut **100**.

Et `max_steps` n'était **lu nulle part** dans le code (0 occurrence).

| Défaut | Constat |
|---|---|
| Patience calculée | 119 → 329 ticks |
| Budget réel du palier bloquant | **100** |
| Formule | `0,7 × taux_succès` → **à l'envers** |

Le débutant recevait **119** ticks, l'expert **329**.

---

## 2. Les trois bugs corrigés

| # | Bug | Mesure |
|---|---|---|
| **v41.7** | La nourriture n'avait **aucune valeur apprise** | `'FOOD' +0.000` sur **4004 repas** (contre `'goal' +0.515`) |
| **v41.8** | Patience **inversée** et hors budget | débutant 119 ticks / expert 329, sur une carte qui en alloue 100 |
| **v41.8-fix1** | Patience **écrasée** par l'ordre des opérations | 70 ticks au lieu de 100 ; 176 abandons au lieu de 61 |

Le troisième est un défaut de **ma propre correction** — trouvé par la campagne, pas par
la relecture.

---

## 3. ⚠️ Le résultat qui remet en cause la méthode

Trois campagnes, **mêmes 6 graines**, mêmes 1000 jours. Qui atteint le niveau 3 ?

| Graine | v41.6 | v41.7+v41.8 | fix1 |
|---|---|---|---|
| g44 | ✅ | ✅ | ❌ |
| g22 | ❌ | ❌ | ✅ *(j23 — record du projet)* |
| g55 | ✅ | ✅ | ✅ |
| g66 | ❌ | ✅ | ❌ |
| **Total** | **2/6** | **3/6** | **2/6** |

**Accord moyen entre campagnes : 4,0/6** — contre 6/6 si le succès tenait à la graine, et
~3,6/6 au hasard pur.

> 🔴 **Sur 6 graines, aucun effet plus petit que ±1 graine n'est mesurable.** Toutes mes
> comparaisons de la nuit sont donc **non concluantes**, y compris celles qui
> m'arrangeaient.

**Décision** : une campagne de **population (20 graines × 600 jours)** tourne depuis 02h05.
Elle établira le **taux de franchissement de référence** du code courant — ce qu'aucune
campagne du projet n'a jamais mesuré sur un échantillon suffisant.

---

## 4. Ce qui reste à arbitrer (pour toi)

Le déséquilibre 300:1 entre métabolisme et victoire est **mesuré** mais **non corrigé** —
volontairement, car les trois options se contredisent :

| Option | Principe | Risque |
|---|---|---|
| Pondérer `r_bio` | le faire taire | il faudrait le diviser par **62** sur `Empty-8x8` : l'agent deviendrait indifférent à sa survie |
| **Espacer `r_bio`** (par épisode, pas par tick) | corriger la **fréquence**, pas l'amplitude | change la granularité du signal corporel — **jamais testé** |
| Enrichir le monde | supprimer le déficit à la source | le monde est déjà vivable (marcheur aléatoire : 0 mort) |

> 💡 **La deuxième est la seule qui ne contredise aucun principe du projet** : elle ne
> touche ni à l'amplitude du corps, ni au monde. Elle attend ton arbitrage.

---

## 5. ⚠️ J'ai simulé ma propre recommandation — elle est plus faible que je ne l'ai dit

Avant de te la proposer, j'ai calculé ce que donnerait « `r_bio` versé par épisode » à
partir des amplitudes déjà mesurées. **Aucune modification du code.**

| Niveau | `r_bio` avant | **après** | Victoire avant | **après** |
|---|---|---|---|---|
| `Empty-5x5` | 89,9 % | **75,8 %** | 10,1 % | **24,2 %** |
| `Empty-Random-6x6` | 87,8 % | **71,5 %** | 12,2 % | **28,5 %** |
| `Empty-8x8` | 98,4 % | **95,6 %** | 1,6 % | **4,4 %** |

L'amplitude **totale** de `r_bio` ne change pas — le corps pousse autant. Ce qui change est
le nombre d'**événements** : de 400 par jour à ~1,5-4.

### Ce que la simulation corrige dans mon propos

> Je t'ai présenté cette option comme « la seule qui ne contredise aucun principe ».
> C'est toujours vrai, **mais son effet est modeste là où le problème est le pire** :
> sur `Empty-8x8` — le palier bloquant — la victoire passerait de 1,6 % à **4,4 %**.
> Elle resterait noyée.

### Et un risque que je n'avais pas vu

Un `r_bio` versé en fin d'épisode **n'indique plus quel tick a soulagé**. L'agent perdrait
l'association « ce geste-ci m'a nourri » — exactement ce que la **v41.2-fix7** avait établi
et vérifié (contraste 15× entre manger affamé et manger repu).

> **La piste demande donc un crédit rétrograde, pas un simple déplacement du versement.**
> C'est un chantier, pas un réglage — et il faut le dire avant de s'y engager.

### Ce que je recommande à la place, pour le point de 7h30

**Ne rien décider sur le déséquilibre tant que la campagne de population n'a pas parlé.**
Elle dira si le code courant franchit des paliers à un taux stable ; si oui, le
déséquilibre 300:1 n'est peut-être pas le bloquant principal, et le corriger serait
optimiser la mauvaise chose.

---

## 6. 🔴 DÉCOUVERTE FINALE — les runs ne sont PAS reproductibles à graine fixée

En cherchant pourquoi les mêmes graines donnaient des résultats opposés entre deux
campagnes, j'ai testé le cas le plus simple possible : **deux runs lancés l'un après
l'autre, même graine, même code, même machine, 3 jours.**

```
run 1 : JEPA 0.0841 → maîtrise 45 %  |  JEPA 0.0825 → 43 %  |  JEPA 0.0420
run 2 : JEPA 0.0841 → maîtrise 50 %  |  JEPA 0.0884 → 42 %  |  JEPA 0.0418
        ↑ identique                    ↑ DIVERGENCE dès le jour 1
```

**Le jour 1 commence identique (JEPA 0,0841) et se termine différemment (45 % contre
50 %).** La divergence naît à l'intérieur de la première journée.

### Ce que ce n'est pas

| Hypothèse testée | Résultat |
|---|---|
| `mps` non déterministe | ❌ **réfutée** — 3 essais identiques au 10ᵉ chiffre, sur `cpu` comme sur `mps` |
| `--jours` influence un calcul | ❌ **réfutée** — il n'entre dans aucune formule |
| Code différent entre campagnes | ❌ **réfutée** — `git diff` vide |

La cause reste à isoler (ordre d'appels au générateur dépendant du timing, opérations
asynchrones GPU, ou état partagé non réamorcé).

### ⚠️ Ce que cela invalide

> **Toute comparaison de ce projet reposant sur « même graine, donc même trajectoire » est
> caduque.** Cela inclut :
>
> - les comparaisons appariées de la nuit (v41.6 vs v41.7+v41.8 vs fix1)
> - la comparaison appariée v41.4 « héritage ON vs OFF » du 15/08, dont la conclusion
>   « 3 graines bit-identiques » ne peut plus s'expliquer par la seule ablation
> - toute conclusion du type « cette graine réussit, celle-là non »
>
> Cela **explique aussi** l'accord de 4,0/6 mesuré entre campagnes : ce n'était pas une
> propriété des graines, c'était **du bruit d'exécution**.

### Ce que cela n'invalide pas

Les résultats obtenus par **mesure directe**, qui ne dépendent d'aucune comparaison entre
runs :

| Résultat | Méthode |
|---|---|
| `'FOOD' +0.000` sur 4004 repas | lecture d'un `.brain` |
| Le monde est vivable (marcheur aléatoire) | 25 épisodes, statistique interne |
| `r_bio` = 90-98 % du signal | amplitudes cumulées, 20 épisodes |
| La maîtrise ne progresse pas (24,7 → 22,9 %) | série temporelle **intra**-run |
| Patience inversée / hors budget | lecture du code + `max_steps` |

### 📌 Priorité n°1 pour la suite

**Rendre les runs reproductibles** avant toute nouvelle campagne comparative. Sans cela,
le projet ne peut mesurer aucun effet plus petit que son bruit d'exécution — ce qui est
précisément ce qui s'est passé cette nuit, et vraisemblablement depuis longtemps.

### 6.1 ✅ CAUSE ISOLÉE — `env.reset()` n'est jamais appelé avec une graine

```bash
grep -c "env.reset()"    →  3    # tous les resets du projet
grep -c "reset(seed="    →  0    # aucun n'est seedé
```

**Preuve directe** — même processus, `torch.manual_seed(11)` + `np.random.seed(11)` +
`random.seed(11)` appliqués avant chaque essai :

| | Position de l'agent au reset |
|---|---|
| `reset()` — **comme le projet** | (1,2) dir 0 · (2,4) dir 3 · (2,2) dir 2 → **3 cartes différentes** |
| `reset(seed=11)` | (4,2) dir 2 · (4,2) dir 2 · (4,2) dir 2 → **identique** |

> 🎯 **MiniGrid possède son propre générateur, initialisé sur l'entropie système.**
> `torch.manual_seed` et `np.random.seed` n'ont **aucun effet** dessus. Chaque run tire
> donc une suite de cartes différente, quelle que soit la graine passée en `--graine`.
>
> C'est la cause exacte de la divergence observée au jour 1 : les deux runs voient des
> mondes différents dès le premier épisode.

### 6.2 ⚠️ Le correctif n'est PAS trivial — ne pas l'appliquer à la légère

Ajouter `seed=` à `reset()` est une ligne, mais le choix de la graine est un **arbitrage de
conception**, pas un détail :

| Option | Effet | Risque |
|---|---|---|
| `reset(seed=graine)` fixe | toujours **la même carte** | l'agent apprendrait **une** carte par cœur, plus la tâche — désastreux |
| `reset(seed=graine + n_episode)` | suite reproductible **et** variée | ✅ la bonne forme, mais change la distribution des cartes vues |
| Ne rien faire | statu quo | aucune comparaison n'est fiable |

> La deuxième option est la seule viable, mais **elle modifie ce que l'agent voit** : les
> cartes ne seront plus les mêmes qu'aujourd'hui. Tous les chiffres du projet
> deviendraient non comparables aux précédents — ce qui est acceptable **une fois**, à
> condition d'être annoncé.

**Je ne l'ai pas appliqué** : c'est un changement de nature du banc d'essai, il te revient.

### 6.3 Ce que cette découverte réhabilite

Le dépôt documente que **« 9 mécaniques cognitives sur 9 testées n'ont produit aucun
effet »**. Cette conclusion supposait que deux runs comparés ne différaient que par la
mécanique testée.

> **Ils différaient aussi par les cartes tirées.** Le « bruit natal » que le projet
> attribue depuis des semaines aux graines est, au moins en partie, un **bruit de banc
> d'essai**.
>
> Cela ne prouve pas que les 9 mécaniques fonctionnaient — mais cela signifie que
> **le test qui les a écartées ne pouvait pas les départager**.

---

## 7. 📊 Le taux de référence — première mesure du projet sur un échantillon suffisant

**20 graines × 600 jours**, code `v41.8-fix1` — campagne complète.

| Résultat | Graines | Taux | IC 95 % |
|---|---|---|---|
| Au moins 1 promotion | **8/20** | **40 %** | [22 % ; 61 %] |
| 2 promotions (niveau 3) | **5/20** | **25 %** | [11 % ; 47 %] |
| Aucune promotion | 12/20 | 60 % | — |

**13 promotions au total.** Répartition : 12 graines restent au niveau 1, 3 atteignent le
niveau 2, 5 atteignent le niveau 3.

### La conclusion qui clôt la nuit

Les trois campagnes de la nuit donnaient **2/6, 3/6, 2/6** — soit **33 %, 50 %, 33 %**.

> 🔴 **Les trois tombent dans l'intervalle de confiance du taux de base [20 % ; 61 %].**
> Aucune d'elles ne mesurait autre chose que ce taux. Les écarts que j'ai passé la nuit à
> interpréter — « une graine de plus », « fix1 restaure la vitesse », « g22 promue au
> jour 23 » — sont **entièrement contenus dans le bruit**.

### Ce que cela établit pour la suite

| Constat | Conséquence pratique |
|---|---|
| Le taux de base est **39 %** [20-61] | un correctif doit dépasser ~60 % pour être détectable à n=18 |
| L'intervalle reste **large même à 18 graines** | conséquence directe des cartes non seedées (§6.1) |
| 6 graines ⇒ IC de ±30 points | **aucune campagne à 6 graines n'a jamais rien pu prouver sur ce projet** |

> **L'ordre des priorités est donc inversé par rapport à ce que je croyais en début de
> nuit** : rendre le banc reproductible (§6.2) n'est pas une amélioration de confort,
> c'est le **préalable** à toute mesure d'effet. Tant qu'il n'est pas fait, chaque
> campagne coûte des heures pour produire un chiffre indistinguable de 39 %.

### Note positive

Le taux de base **n'est pas nul** : 39 % des graines franchissent un palier, 22 % en
franchissent deux, en 600 jours. Le cursus n'est donc pas totalement bloqué — il l'était
dans la lecture historique parce que les campagnes précédentes tournaient sur des codes
antérieurs aux correctifs de promotion (v41.3, v41.5) et sur des échantillons trop petits.
