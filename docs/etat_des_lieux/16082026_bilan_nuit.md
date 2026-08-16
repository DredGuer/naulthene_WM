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
