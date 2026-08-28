# 28/08/2026 — Le plafond est GÉOMÉTRIQUE. Le réseau détruit l'information qu'il reçoit.

> Non normatif — carnet d'enquête. Ce n'est pas une réfutation de plus : c'est le
> diagnostic vers lequel les quatorze précédentes convergent.

## La question restée ouverte après 14 réfutations

Le signal perceptif arrive aux logits (mesuré). Le crédit d'un geste stérile est nul depuis
la v41.31 (vérifié dans le code). La carte perceptive est protégée et la connecter empire
tout (v41.34, bruit +48 %). Isoler l'action dans l'avantage ne contraste rien (TD 1,125× ·
GAE 1,161× contre MC 1,275×).

Et pourtant la politique reste plate : entropie **1,93** sur un maximum de 1,946, action
préférée **identique** face à un mur et une ressource sur 5/5 cerveaux.

**Pourquoi ?**

## [1] L'optimiseur ne PEUT PAS séparer les deux états

`cos(∇_ressource, ∇_mur)` en renforçant `ramasser` sur les deux classes :

| Cerveau | cosinus |
|---|---|
| A_g11 | **+0,9857** |
| A_g22 | **+0,9850** |
| A_g44 | **+0,9865** |

Les gradients sont **quasi colinéaires**. Renforcer `ramasser` face à une ressource le
renforce presque identiquement face à un mur.

Ce n'est pas « aucune pression à séparer » — c'est une **impossibilité mécanique**. Aucune
fonction de récompense, aucune durée de run ne peut y changer quoi que ce soit.

## [2] La cause : le réseau confond progressivement ce que l'œil distingue

`cos(x_ressource, x_mur)` étage par étage :

| Étage | A_g11 | A_g44 |
|---|---|---|
| **Observation brute** (147 dims) | **0,610** | **0,610** |
| `bus_latent` (après `porte_visuelle`) | 0,959 | 0,897 |
| **`pensee_bio`** (entrée de la tête motrice) | **0,996** | **0,9999** |

**L'information est dans l'entrée. Le réseau la détruit.**

Le gradient d'une couche linéaire vaut `δ ⊗ x`. Si `x_res` et `x_mur` sont colinéaires à
0,996, les gradients le sont **aussi**, quelle que soit `δ` — donc quelle que soit la
récompense. La colinéarité de [1] est la **conséquence arithmétique** de celle-ci.

## [3] Ce que la géométrie interdit

Borne : `|logit_r − logit_m| ≤ ‖W‖ · ‖x_r − x_m‖`.

| Cerveau | ‖x_res − x_mur‖ | écart de logit **maximal** | proba max de l'action favorisée |
|---|---|---|---|
| A_g11 | 0,2127 (14,5 % de la norme) | **0,2752** | **18,00 %** |
| A_g22 | 0,2550 (22,6 %) | 0,3212 | 18,69 % |
| A_g44 | **0,0187 (1,5 %)** | **0,0221** | **14,56 %** |

Hasard sur 7 actions : **14,29 %**.

**Même avec des poids parfaits**, la tête motrice de g44 ne peut pas dépasser 14,56 %.
Les **15,00 %** mesurés en jeu le 27/08 (contre 14,44 % face à un mur) ne sont donc pas de
l'apathie, ni un défaut d'incitation : **c'est le maximum que la géométrie autorise.**

## Ce que cela réorganise

Quatorze réfutations avaient éliminé, une par une, les explications du plafond :

| Piste | Verdict | Pourquoi elle ne pouvait pas marcher |
|---|---|---|
| Thrashing du gradient | réfutée (AB3) | un gradient propre sur des entrées colinéaires reste colinéaire |
| Crédit temporel (TD/GAE) | réfutée | `δ` change, `x` ne change pas |
| Agnosie proprioceptive | levée (d +1,43) — **sans effet** | le critique lit un scalaire, l'acteur lit un vecteur écrasé |
| Attention descendante | réfutée (bruit +48 %) | agite le tronc au lieu de l'orienter |

Toutes agissaient sur `δ` — le signal d'erreur. **Aucune ne pouvait agir sur `x`.**

## ⚠️ Ce que cette mesure n'établit PAS

1. **Que c'est LA cause du plafond au niveau 4.** Elle établit un plafond mécanique sur la
   discrimination *ressource/mur*. Le lien avec la promotion du cursus est **plausible mais
   non mesuré** — les niveaux 1 à 4 ne contiennent d'ailleurs aucun objet à ramasser.
2. **Que le collapse est pathologique.** Une représentation compressée *doit* rapprocher
   des états ; la question est de savoir si 0,996 est trop. Aucune référence externe n'a été
   mesurée (un PPO CNN sur la même tâche donnerait le point de comparaison — **non fait**).
3. **Que c'est corrigible.** Aucune correction n'a été testée.

Le chiffre le plus solide reste **0,610 → 0,996** : l'information entre, elle se perd.

## Pistes ouvertes, aucune testée

- **Un biais spatial.** `porte_visuelle` est une couche **linéaire 147→64** sur une
  observation aplatie — aucune convolution, donc aucune notion de voisinage. Le réseau doit
  déduire la topologie de la co-occurrence statistique seule.
- **Une perte contrastive sur le tronc.** Elle agirait sur `x`, pas sur `δ` — la première
  famille d'intervention que ce diagnostic désigne. ⚠️ Ce serait un objectif **posé**, à
  confronter au dogme avant d'être écrit.
- **La largeur du bus.** 64 dims pour compresser 147 dims de vision + 42 de corps.

## Instruments (lecture seule, versionnés)

```bash
PYTHONPATH=src python -m naulthene.instruments.sonde_pression_separation <brain> [graine]
PYTHONPATH=src python -m naulthene.instruments.sonde_collapse <brain>
PYTHONPATH=src python -m naulthene.instruments.sonde_plafond_geometrique <brain>
```
