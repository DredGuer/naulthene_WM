# ÉTAPE 0 — Télémétrie de la cinétique motrice (lecture seule, instrument CORRIGÉ)

**Date** : 2026-09-01 · **Cerveau** : `A_g66` · **40 épisodes, 10 851 ticks** ·
`SimpleCrossingS9N1`, budget 324 ticks · **Sonde corrigée** (mémoire en `penser()[4]`).

## Les deux sondes demandées

| Sonde | Mesure |
|---|---|
| **Autocorrélation motrice lag-1** | `P(avancer_{t+1} \| avancer_t)` = **0,3743** |
| — à comparer à | `P(avancer)` = **0,3758** |
| — **ratio** | **0,9959** |
| **Gestes stériles purs** | **44,5 %** des ticks |

🔴 **Le ratio vaut 0,9959 — soit AUCUNE persistance motrice.** Avancer au tick *t* ne dit
**rigoureusement rien** sur ce que l'agent fera au tick *t+1*. La séquence d'actions est
**sans mémoire**.

⚠️ **Et c'est un PARADOXE avec la mesure du même jour** : les *logits* sont autocorrélés à
**0,69–0,85**, mais les *actions* ne le sont pas du tout. Des préférences stables produisent
des gestes sans mémoire — parce que l'échantillonnage multinomial d'une distribution
seulement *tiède* (`P(avancer) = 0,376`) détruit la structure temporelle des préférences.

`P(répéter la même action)` = **0,2157** contre 0,1429 pour l'uniforme : une persistance
résiduelle existe, mais elle est **1,5× l'uniforme**, pas 3× ou 5×.

## Décomposition complète du budget

| Famille | Ticks | Part | Sur 324 ticks |
|---|---|---|---|
| `AVANCER` **utile** (déplacement réel) | 1 894 | **17,5 %** | **56,6** |
| `AVANCER` **dans un mur** | 2 184 | 20,1 % | 65,2 |
| rotations (`gauche`/`droite`) | 1 944 | 17,9 % | 58,0 |
| **stériles** (`ramasser`/`poser`/`activer`/`fini`) | 4 829 | **44,5 %** | **144,2** |

### Les deux chiffres qui dominent

1. 🔴 **53,6 % des `AVANCER` se cognent dans un mur** (2 184 sur 4 078). L'agent choisit
   la bonne action et la joue contre une cloison.
2. 🔴 **17,5 % seulement des ticks produisent un déplacement.** Sur 324 ticks de budget,
   l'agent obtient **~57 ticks de mouvement réel** — pour un objectif à **12 cases**.

### Détail par action

| Action | Ticks | Part |
|---|---|---|
| `AVANCER` | 4 078 | 37,6 % |
| `activer` | 1 535 | 14,1 % |
| `fini` | 1 411 | 13,0 % |
| `poser` | 1 293 | 11,9 % |
| `droite` | 1 047 | 9,6 % |
| `gauche` | 897 | 8,3 % |
| `ramasser` | 590 | 5,4 % |

⚠️ `activer` + `fini` + `poser` = **39,0 %** du budget. Aucune de ces trois actions ne peut
produire le moindre effet sur `SimpleCrossing` (ni objet, ni porte).

## Ce que cela dit des trois briques proposées

| Brique | Prémisse | Verdict de l'Étape 0 |
|---|---|---|
| **B — inertie proprioceptive** | « le réseau ne sait pas s'il est en mouvement » | ✅ **CONFIRMÉE, et plus fortement qu'énoncé** : ratio 0,9959, persistance nulle. L'orientation (`cos`,`sin`) est déjà dans `DIM_TOUCHER`, mais c'est une **pose**, pas une **vitesse** |
| **C — avantage différentiel** | « 42 % des gestes sont stériles » | ✅ **CONFIRMÉE à 44,5 %** — et la brique couvre en réalité **64,6 %** du budget, car un `AVANCER` dans un mur est aussi un travail à rendement nul |
| **A — amortissement local** | « l'agent est payé pour piétiner près de la nourriture » | 🟡 **à mesurer** — la nourriture existe bien sur cette carte (semée par le cœur, respawn 80 % au nid), mais la part de `r_bio` dans le signal n'est pas établie ici |

## Limites

- **n = 1 cerveau** (`A_g66`, le meilleur de la cohorte). À porter à n=20 avant conclusion.
- Politique **figée** (`eval()`), aucun apprentissage : décrit ce que l'agent *fait*, pas ce
  qu'il *apprendrait*.
- `SimpleCrossing` rend 3 actions stériles **par construction** ; le chiffre ne se transporte
  pas tel quel sur un niveau à portes.

---

## Addendum — la brique A mesurée (et sa prémisse réfutée)

`sonde_recompense`, 800 ticks, niveau 4 (`SimpleCrossingS9N1`), deux cerveaux aux
extrémités de la cohorte.

| Terme | `A_g66` (fort, 40 % au banc) | `A_g144` (faible, 1,33 %) |
|---|---|---|
| `recompense_env` (le MONDE) | **39,8 %** | 10,9 % |
| `dopamine_curiosite` | 27,7 % | **40,1 %** |
| **`r_bio`** (faim/soif/stimulation) | **15,4 %** | **23,6 %** |
| `sous_objectif_intrinseque` | 11,7 % | 18,6 % |
| `micro_recompense_progres` | 5,4 % | 6,8 % |
| `penalite_stagnation` | 100 % du négatif | 100 % du négatif |

🔴 **La prémisse de la brique A est FAUSSE sur ce niveau.** `r_bio` — le terme que
l'amortissement local viserait — ne pèse que **15,4 %** du signal positif chez le cerveau
fort et **23,6 %** chez le faible. Il n'est **jamais dominant**. Ce qui domine est soit le
MONDE (39,8 % chez le fort), soit la CURIOSITÉ (40,1 % chez le faible).

Or **la curiosité a déjà été testée et réfutée** le 30/08 : rente confirmée à 40 % du
signal, mais maîtrise **15,0 % contre 15,0 %** entre curiosité faible et forte (n=40).
Amortir `r_bio`, plus petit encore, n'a aucune raison de faire mieux.

⚠️ **Nuance sur le chiffre « 86 % du signal est interne »** inscrit dans `CLAUDE.md` : il
a été mesuré sur un cerveau qui **ne gagnait jamais**. Chez un cerveau qui gagne 40 % du
temps, le monde verse **39,8 %** du signal positif. Le barème n'est pas creux *en soi* :
**il devient creux quand l'agent échoue**. C'est une boucle, pas une constante.

### Conséquence sur l'ordre des briques

| Brique | Statut après Étape 0 | Suite |
|---|---|---|
| **C — avantage différentiel** | ✅ prémisse confirmée, et **plus large qu'énoncé** (64,6 % du budget est un travail à rendement nul, pas 42 %) | à implémenter **en premier** |
| **B — inertie proprioceptive** | ✅ prémisse confirmée (ratio 0,9959) | à implémenter **en second** |
| **A — amortissement local** | ❌ **prémisse réfutée** : `r_bio` n'est jamais dominant (15–24 %), et son voisin plus gros (la curiosité) est déjà mesuré sans effet | **à ne pas implémenter** en l'état |
