# L'agent apprend-il ? — la mesure contre la baseline aléatoire

**20/08/2026** — carnet de recherche, non normatif.
Question posée après trois nuits de travail sur la nociception : *« il faut trouver où ça
bloque »*.

---

## 1. La réponse en une ligne

> **OUI, l'agent apprend — sans ambiguïté et sur 10 graines sur 10.**
>
> 🔴 **RECTIFICATION (même jour).** Ce carnet affirmait ensuite qu'il « plafonne sous une
> politique aléatoire » (54,4 % contre 75,7 %). **C'était faux** : la baseline tirait parmi
> **3 actions**, l'agent en a **7**. À armes égales, le hasard fait **39,2 %** — l'agent le
> **bat de 15 points**. La conclusion est corrigée ici plutôt que supprimée.

Apprendre et être compétent sont deux choses différentes. Les données établissent la
première, réfutent la seconde.

---

## 2. Le test — `Empty-5x5`, aucun danger

Choisi pour éliminer toutes les variables : pas de lave, pas de clé, pas de porte. Une
pièce vide de 5×5, l'agent en haut à gauche, le but en bas à droite, **4 cases**.

**Baseline** (2000 épisodes, politique tirée au sort parmi gauche/droite/avancer) :

| baseline | `Empty-5x5` |
|---|---|
| hasard sur **3 actions** (biaisé — pas la même tâche) | 75,7 % |
| **hasard sur 7 actions** (équitable) | **39,2 %** |
| **Naulthène à 300 jours** | **54,4 %** |

Sur `LavaGapS5`, le hasard à 3 actions donne 10,3 % de réussite et 88,7 % de morts.

---

## 3. La preuve que l'agent apprend

### 3.1 La progression est monotone

10 runs × 300 jours, maîtrise moyenne par quart :

```
Q1 : 13,8 %  →  Q2 : 26,7 %  →  Q3 : 43,8 %  →  Q4 : 54,4 %
```

**+40,6 points, sans plateau.** La courbe monte encore à la fin du run.

### 3.2 Elle est vraie sur CHAQUE graine, pas seulement en moyenne

| graine | Q1 → Q4 | | graine | Q1 → Q4 |
|---|---|---|---|---|
| g1 | 5,6 % → 31,3 % | | g6 | 6,3 % → 42,7 % |
| g2 | 12,6 % → **83,0 %** | | g7 | 12,9 % → 70,0 % |
| g3 | 1,9 % → 7,6 % | | g8 | 4,7 % → **85,9 %** |
| g4 | 23,1 % → 47,1 % | | g9 | 20,8 % → 26,7 % |
| g5 | 26,2 % → 67,1 % | | g10 | 24,3 % → **82,3 %** |

**10/10 graines progressent.** Aucune ne régresse. Ce n'est pas une moyenne qui masque des
échecs.

### 3.3 L'agent devient plus EFFICACE, pas seulement plus chanceux

Intervalle moyen entre deux victoires (jours) :

| graine | début → fin |
|---|---|
| g1 | 5,4 j → **1,4 j** |
| g2 | 2,1 j → **1,0 j** |
| g4 | 1,5 j → **1,0 j** |
| g10 | 1,4 j → **1,0 j** |
| g3 | 10,8 j → 12,7 j ⚠️ |

Gagner plus souvent **et** plus vite : c'est la signature d'une politique qui s'améliore,
pas d'un tirage plus favorable.

### 3.4 Trois graines dépassent le hasard

**3/10 graines** terminent au-dessus de 75,7 % (g2 83,0 % · g8 85,9 % · g10 82,3 %). La
compétence est donc **atteignable par cette architecture** — elle n'est simplement pas
atteinte de façon fiable.

---

## 4. Ce que ça réfute — et c'est une erreur de ma part

Le 19/08 au soir, j'ai conclu : *« l'agent est 15× moins bon que le hasard, 5 % de
maîtrise »*. **C'était lu au jour 23 d'un run de 300.**

L'agent était en cours d'apprentissage ; j'ai pris un transitoire pour un plateau. C'est
exactement l'erreur que la règle de mesure interdit — et la deuxième de la même famille en
deux jours (après la douleur mesurée hors du tick réel).

> **Leçon** : une mesure prise avant la fin du run ne mesure pas le run. Le seul chiffre
> lisible en cours de route est une **tendance**, jamais un niveau.

---

## 5. Le vrai blocage

L'agent apprend **et** bat le hasard équitable (54,4 % contre 39,2 %). Le blocage n'est
donc pas la politique elle-même, mais **ce qu'elle est incitée à faire** : **57,2 % des
ticks** partent en gestes stériles, parce qu'ils coûtent **1,09** quand avancer coûte
**4,00**. Voir [`POURQUOI_20082026_l_agent_economise.md`](POURQUOI_20082026_l_agent_economise.md).

Cela converge avec tout ce que le projet a mesuré par ailleurs :

- couper C2 ne change le score de **0,0 point** sur 6 niveaux (78 cellules) ;
- grossir le cerveau n'apporte **rien** (`r = +0,018`, IC95 [−0,45 ; +0,48], n=18) ;
- **1 mécanique cognitive sur 14** testées a amélioré une métrique de tâche.

**Un système qui apprend mais plafonne sous le hasard a une politique qui se dégrade
quelque part entre le signal et l'action.** C'est là qu'il faut chercher — pas dans les
mécaniques qu'on empile au-dessus.

---

## 6. Ce que la nuit sur la nociception a réellement produit

Le défaut corrigé était **réel** : la lave portait la valence de l'eau (+0,06) sur tous les
cerveaux depuis l'origine, parce que MiniGrid punit la mort par exactement `0.0`. C'est
réparé — valence **−0,761 sur 20/20 graines**, `t = −1066`.

Mais **ce n'était pas le blocage**. Trois versions de douleur ont été construites et
mesurées ; aucune ne change le comportement (voir §7). Le travail n'est pas perdu — il
ferme définitivement une piste et supprime une des 4 récompenses en dur du dogme
(`MALUS_DOULEUR`) — mais il traitait un symptôme.

---

## 7. Campagne v41.27 — résultats finaux (n=20, 3 bras)

| bras | approche du danger | récolte | survie |
|---|---|---|---|
| **A** (douleur + mort coûteuse) | **36,0 %** | 2,67 | 5,89 % [4,8–7,2] |
| **B** (douleur seule) | 62,5 % | 11,56 | 8,98 % [8,5–9,4] |
| **C** (témoin) | 63,0 % | 12,19 | 9,79 % [9,4–10,2] |

```
B vs C — LA DOULEUR SEULE
  approche : −0,48 pt   t = −1,51   NON significatif
  récolte  : −0,63      t = −1,17   NON significatif

A vs B — LE COÛT DE LA MORT
  approche : −26,54 pts t = −15,21  SIGNIFICATIF
  récolte  :  −8,89     t = −15,94  SIGNIFICATIF
```

**La douleur informe ; la conséquence enseigne.** Ce qui fait éviter la lave, ce n'est pas
qu'elle fasse mal — c'est que mourir coûte cher.

⚠️ Mais l'option (b) est **inutilisable telle quelle** : 275 ticks perdus par jour, récolte
divisée par 4, et la **survie la plus basse des trois bras**. L'agent évite parce qu'il n'a
plus le temps de faire autre chose — il meurt de faim au lieu de brûler.

---

## 8. Ce qui reste ouvert

1. **Pourquoi la politique plafonne-t-elle sous le hasard ?** C'est LA question. Trois
   pistes mesurables : la distribution des actions jouées (l'agent joue-t-il 7 actions ou
   une seule en boucle ?), la patience par épisode (100 ticks pour un but à 4 cases), et
   le gradient qui atteint réellement `tete_motrice`.
2. **Un coût de mort intermédiaire.** A évite mais meurt de faim, B mange mais ne
   comprend rien. L'optimum est entre les deux.
3. **La baseline aléatoire devient un témoin permanent.** Elle coûte 30 secondes et c'est
   elle qui a révélé le vrai problème — après trois nuits passées ailleurs.
