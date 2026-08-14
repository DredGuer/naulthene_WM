# Dissection du cerveau g22 — 14 août 2026

> **Nature** : autopsie d'un `.brain`, lecture seule. Le cerveau le plus avancé produit par
> la campagne P17 (gaussienne d'apprentissage).
>
> Fichier : `brains/old_V39/p17_gauss_g22.brain` — 4 590 jours, 248 victoires.

---

## Pourquoi celui-là

| | g11 | **g22** | g33 |
|---|---|---|---|
| Victoires | 199 | **248** | — |
| Sommet atteint | 6×6 | **6×6** | 5×5 |
| Jours | 4 590 | 4 590 | 4 590 |

**248 victoires.** Le record précédent du projet était **69** (le fameux g22 de la campagne
v38) — et celui-là avait été obtenu sur un banc biaisé où jusqu'à la moitié des cartes
étaient gagnables sans la clé. Ici le banc est corrigé.

---

## 1. 🟢 L'empreinte de type — le résultat le plus intéressant

C'est le mécanisme v39.0 : la valence apprise par **type d'objet**, qui survit aux
changements de carte.

| Type | Valence apprise | Fois vécu |
|---|---|---|
| **`goal`** | **+1,1492** | 1 075 |
| `porte_key` | +0,1222 | 54 027 |
| `door` | +0,1157 | 3 659 |
| `sol` | +0,0949 | 49 425 |
| `porte_ball` | +0,0921 | 119 355 |
| `FOOD` | +0,0000 | 2 098 |
| `WATER` | +0,0000 | 926 |

### Ce que ça démontre

**Le but se détache d'un facteur 16,2×** de la moyenne de tout le reste.

Et c'est **entièrement appris** : nulle part dans le code il n'existe de table disant que
`goal` est bon. L'étiquette est une chaîne opaque tirée de l'API MiniGrid ; sa valeur est
la moyenne des chocs dopaminergiques réellement vécus à cet endroit.

> C'est la première fois que le projet peut montrer une **abstraction construite par
> l'expérience** plutôt que déclarée : le cerveau ne sait pas ce qu'est un but, il sait
> que « ce genre d'endroit » lui a valu 16 fois plus que les autres.

### Ce que ça ne démontre pas

Que cette abstraction **sert** à quelque chose. La campagne P12 a mesuré que l'utiliser
comme prior à la naissance des repères **n'améliore pas** la performance (2/5 graines
positives, p = 1,000). L'empreinte est **juste**, pas encore **utile**.

### Un détail qui interroge

`FOOD` et `WATER` sont à **exactement 0,0000** après 2 098 et 926 expériences. Manger ne
produit donc aucun choc dopaminergique net — le métabolisme est nourri, mais l'événement
n'est pas *marquant*. À creuser : c'est peut-être pourquoi l'odorat et le goût ne servent
à rien (mesuré en ablation).

---

## 2. 🟢 La santé synaptique — intacte après 4 590 jours

| Mesure | Valeur |
|---|---|
| Synapses mortes | **0** |
| Couches au plancher vital | **1 / 12** (`tete_requete`) |

À comparer aux 13 769 synapses mortes en médiane **avant** les correctifs v37, et aux
8 couches sur 11 à zéro absolu du cerveau v34. **La plomberie tient sur des durées longues.**

`tete_requete` au plancher est normal : c'est la tête du Port C3, dormante puisqu'aucun
plug n'est enregistré.

---

## 3. ⚠️ Les normes par couche — une hiérarchie qui interroge

Ratio à la norme de naissance :

| Couche | Ratio | Lecture |
|---|---|---|
| `porte_auditive` | **122,8 %** | a *grossi* |
| `tete_vocale` | 112,4 % | a grossi |
| `hippocampe` | 86,8 % | sain |
| `porte_visuelle` | 83,1 % | sain |
| `integrateur_bio` | 82,1 % | sain |
| `cortex_prefrontal` | 79,5 % | sain (C2) |
| `fusion_memoire` | 71,7 % | |
| `analyseur` | 59,2 % | |
| `generateur_attente_audio` | 49,2 % | |
| `generateur_attente` | 31,1 % | JEPA érodé |
| **`tete_motrice`** | **20,2 %** | ⚠️ **C1, la décision motrice** |
| `tete_requete` | 10,0 % | plancher (dormante) |

### Ce qui frappe

**Les deux couches audio sont les seules à avoir grossi**, dans un cursus qui ne contient
**aucune tâche vocale**. Pendant que `tete_motrice` — la couche qui *décide des actions* —
tombe à 20 %.

Deux lectures possibles, non tranchées :

1. **Bénigne** : la norme est un mauvais indicateur (invariant documenté en v37 —
   `tete_motrice` peut modifier 7,43 % de ses poids en 5 nuits à norme constante). La
   couche se *remodèle* sans grossir.
2. **Inquiétante** : le budget de plasticité part dans des couches inutilisées, pendant que
   la couche décisive s'érode.

⚠️ **Trancher exige une sonde de gradient**, pas une lecture de normes. Ne pas conclure ici.

---

## 4. La mémoire spatiale : vide

`souvenirs_spatiaux = 0` à l'arrêt — normal et attendu : la mémoire est vidée à chaque
changement de carte (le OÙ périme), et la gaussienne change de carte très souvent. C'est
précisément ce que la v39.0 corrige en faisant survivre le QUOI.

**C'est la meilleure illustration du correctif** : sans lui, ce cerveau n'aurait
strictement rien retenu de 4 590 jours. Avec lui, il garde 7 types et 230 000 expériences
accumulées.

---

## Ce que cette dissection change

| Question | Réponse |
|---|---|
| Le cerveau apprend-il quelque chose ? | ✅ **oui** — le but vaut 16× le reste, appris |
| La plomberie tient-elle sur 4 590 jours ? | ✅ **oui** — 0 synapse morte |
| Cet apprentissage sert-il à agir ? | ❓ **non démontré** (P12 dit non) |
| `tete_motrice` à 20 % est-il un problème ? | ❓ **à mesurer** par sonde de gradient |

---

*Dissection du 14 août 2026. Cerveau archivé dans `brains/old_V39/`, logs inclus.*
