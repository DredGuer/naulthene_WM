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
