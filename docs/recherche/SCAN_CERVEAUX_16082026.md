# Scan comparatif des cerveaux — 16 août 2026

> **Question posée par l'utilisateur** : *« la clé de beaucoup de problèmes est liée à la
> gestion entre C1 et C2, la mémorisation de tout et la compression des éléments
> abstraits. Il faudrait scanner les cerveaux, les meilleurs comme les pires. »*
>
> **Corpus** : les 20 cerveaux de la campagne du 16/08 (2500 jours chacun, banc
> reproductible). **16 promus** au niveau 3 contre **3 bloqués** au niveau 1.
> Lecture seule, aucun run supplémentaire.

---

## 1. 🔴 C2 est PLUS GROS chez les cerveaux qui échouent

| | Promus (niv. 3) | Bloqués (niv. 1) |
|---|---|---|
| Norme **C1** (`tete_motrice`) | **2,00** | 1,72 |
| Norme **C2** (`cortex_prefrontal`) | **0,98** | **1,33** |
| **Ratio C1/C2** | **2,11** | **1,30** |

> **Le cerveau qui délibère le plus est celui qui réussit le moins.** Ce n'est pas que C2
> soit atrophié chez les bons : il est **plus lourd chez les mauvais**, de 36 %.

Ce résultat ferme une hypothèse tenace du projet — « C2 ne sert à rien parce qu'il n'a pas
assez de poids ». **Lui en donner davantage est corrélé à l'échec, pas à la réussite.**

Il est cohérent avec le verdict d'ablation d'août (`c2_coupe` = +0,0 sur 6 niveaux) tout en
l'expliquant : un C2 qui grossit sans piloter est un C2 qui **capte du gradient sans rendre
de service** — au détriment des couches qui, elles, agissent.

## 2. 🔴 La mémoire est utilisée à 1 % de sa capacité — et c'est un effet de bord de P17

```
🗺️ 5/200 souvenir(s) spatial(aux) — 51 715 doublon(s) évité(s)
```

| | Promus | Bloqués |
|---|---|---|
| Repères stockés | **10,4** | 7,0 |
| Confirmations moyennes | 1,72 | **4,95** |
| Confirmation maximale | 5,3 | **16,0** |

La capacité est de ~200 à 1000 repères selon `dim_bus`. **Elle est remplie à 1 %.**

### La cause

`_appliquer_niveau_episode` (P17, livré hier) appelle `reinitialiser_niveau()` à **chaque
changement de carte** — ce qui est juste en soi (les coordonnées d'une carte n'ont aucun
sens sur une autre). Mais P17 change de carte **1,5 fois par jour** en moyenne :

> **~3750 effacements de mémoire sur un run de 2500 jours.**
>
> La mémoire spatiale n'a jamais le temps d'accumuler quoi que ce soit. Le mécanisme
> d'abstraction par récurrence (v36.0) — *« un doublon n'est jamais jeté, il confirme »* —
> tourne sur une ardoise essuyée deux fois par jour.

⚠️ **C'est une régression que j'ai introduite hier en livrant P17**, et que la campagne
d'hier ne pouvait pas révéler (banc non reproductible).

### Le détail qui trahit le gaspillage

**51 715 doublons évités** pour 5 repères conservés. L'agent revoit constamment les mêmes
lieux ; l'information existe, elle est simplement jetée à chaque bascule de carte.

## 3. ✅ L'abstraction par TYPE fonctionne — c'est la seule chose qui survit

L'`empreinte_types` (v39.0) n'est **pas** effacée aux changements de carte (elle porte le
QUOI, pas le OÙ), et elle est la seule mémoire réellement remplie :

| Type | Valence apprise | Confirmations |
|---|---|---|
| `goal` | **+0,570** | 2 323 |
| `porte_ball` | +0,832 | 2 |
| `porte_key` | +0,767 | 2 |
| `FOOD` | **+0,306** | 11 442 |
| `WATER` | +0,125 | 10 536 |
| `sol` | +0,083 | 73 485 |
| `lava` | **+0,069** ⚠️ | 12 |

**Le correctif v41.7 fonctionne** : `FOOD` est passé de `+0.000` (figé sur 4004 repas) à
**+0,306** sur 11 442 confirmations. L'agent apprend enfin que la nourriture a de la valeur.

Et la hiérarchie apprise est **juste** : le but (+0,570) vaut plus que la nourriture
(+0,306), qui vaut plus que l'eau (+0,125), qui vaut plus que le sol (+0,083). **Rien de
tout cela n'est déclaré** — c'est appris par accumulation de chocs.

### ⚠️ Sauf `lava`

`lava` a une valence **positive** (+0,069) sur 12 confirmations. La lave tue. Elle devrait
être la valence la plus négative du répertoire.

Douze rencontres seulement : l'agent meurt trop vite pour accumuler l'expérience, et le
choc de la mort n'est visiblement pas crédité à l'étiquette. **À vérifier** — c'est un
canal d'apprentissage potentiellement inversé.

## 4. Ce que le scan dit des autres couches

| Couche | Promus vs bloqués |
|---|---|
| `generateur_attente` (**JEPA**) | **+59 %** |
| `fusion_memoire` | +46 % |
| `porte_visuelle` | +44 % |
| `hippocampe` | +37 % |
| `analyseur` | +31 % |
| `tete_motrice` (C1) | +16 % |
| `integrateur_bio` | +1 % |
| `porte_auditive` | −1 % |
| `cortex_prefrontal` (**C2**) | **−26 %** |

> **Le modèle du monde (JEPA) est ce qui distingue le plus un bon cerveau d'un mauvais**
> (+59 %), et **C2 est la seule couche plus développée chez les mauvais**.
>
> Le `dim_bus` suit : **74 dims** chez les promus contre **53** chez les bloqués (+39 %) —
> les bons cerveaux ont fait plus de neurogenèse, donc ont rencontré plus d'erreur de
> prédiction à résoudre.

## 5. Synthèse — trois pistes, par ordre de ce que la mesure justifie

| # | Piste | Fondement mesuré |
|---|---|---|
| **1** | **Ne plus effacer la mémoire spatiale à chaque bascule P17** — la garder par carte plutôt que la détruire | 1 % de capacité utilisée, 3750 effacements/run, 51 715 doublons jetés |
| **2** | **Vérifier le crédit de `lava`** — une valence positive sur ce qui tue est un canal inversé | +0,069 au lieu d'être le minimum du répertoire |
| **3** | **Cesser de chercher à renforcer C2** | il est déjà 36 % plus gros chez ceux qui échouent |

La piste 1 est la plus directe : elle restaure un mécanisme qui existe déjà et que
j'ai neutralisé hier sans le voir. Elle ne demande aucune nouvelle mécanique.
