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
