# L'INERTIE MOTRICE — la prémisse était fausse : la décision est DÉJÀ lissée

**Date** : 2026-09-01 · **Statut** : ❌ **RÉFUTÉ** (sur la prémisse) · **n** : 1 cerveau ×
8 bras × 300 épisodes + simulation géométrique 200 graines · **Aucun code du noyau modifié.**

> 🔴 **AVERTISSEMENT AJOUTÉ LE MÊME JOUR, APRÈS COUP.** Le balayage de λ de la §3b a tourné
> avec un **défaut d'instrument** découvert quelques heures plus tard : la mémoire de travail
> était lue en `penser()[1]` (la VALEUR, un scalaire) au lieu de `[4]`, et un garde-fou la
> rejetait en silence — l'agent jouait **sans mémoire de travail ni contexte épisodique**.
> Voir `INSTRUMENT_01092026_la_memoire_du_banc.md`. Le tableau §3b est donc **non
> concluant** et rejoué.
>
> **Ce qui SURVIT intact** (aucun ne dépend de ce chemin) : le diagnostic d'autocorrélation
> §3c — mesuré sur les logits, pas sur la mémoire — la simulation géométrique §3d qui
> n'utilise aucun cerveau, et le mécanisme §4 qui est algébrique. **La réfutation de la
> prémisse tient donc entièrement** ; seule l'ampleur chiffrée du non-effet est à revoir.

---

## 1. La question posée

> « À chaque tick, la tête motrice tire une action dans une distribution multinomiale
> **indépendante**. Tirer des virages à gauche et à droite de façon stochastique à haute
> fréquence produit une annulation géométrique immédiate : l'agent oscille sur place.
> Donner une **masse cinématique** à la décision : `L_t = λ·L_{t-1} + (1−λ)·logits_t`.
> Vérifier si λ = 0,7 fait chuter la directivité de 18× vers 3×–5× l'optimal. »

Formulée par l'utilisateur, après la mesure du 31/08 : `r(directivité, succès) = −0,8225`
(`t = −5,96`, n=19), **68 % de la variance** du dépôt.

## 2. Le protocole exact

| Élément | Valeur |
|---|---|
| Cerveau | `A_g66` (le meilleur de la cohorte : 37,33 % au banc du 30/08) |
| Environnement | `MiniGrid-SimpleCrossingS9N1-v0`, budget 324 ticks |
| Épisodes | 300, **graines de carte appariées** (`--graine 90210`) |
| Bras | λ ∈ {0,0 ; 0,5 ; 0,7 ; 0,9} × {cerveau, aléatoire} |
| Régime | `eval()`, **lecture seule**, cerveau lu depuis une COPIE |
| Instrument | `src/naulthene/instruments/sonde_inertie_motrice.py` (neuf) |

**Le témoin critique** est un marcheur **aléatoire soumis à la même inertie** : si
l'inertie ne faisait que rectifier mécaniquement la trajectoire, il en profiterait autant
que le cerveau. Il garde la MÉCANIQUE et coupe la COGNITION.

## 3. Les chiffres bruts

### 3a. Le test A/A — l'instrument ne dérive pas

| Grandeur | Banc du 30/08 | Banc du 01/09 (λ=0) | δ |
|---|---|---|---|
| Succès `A_g66` | 37,33 % | **37,33 %** | **0,00** |
| Directivité | 14,21× | **14,21×** | **0,00** |
| Témoin aléatoire | 17/300 = 5,67 % | **17/300 = 5,67 %** | **0,00** |

**δ_A/A = 0,000000.** Tout écart A/B supérieur à zéro est donc mesurable.

### 3b. Le balayage de λ

| Politique | λ | Succès | IC95 | Directivité | Part `forward` |
|---|---|---|---|---|---|
| cerveau | **0,0** | **37,33 %** | [32,1 ; 42,9] | 14,21× | 41,0 % |
| cerveau | 0,5 | 36,67 % | — | 14,08× | 41,1 % |
| cerveau | 0,7 | **32,00 %** | — | 13,58× | 41,1 % |
| cerveau | 0,9 | 33,33 % | — | **13,04×** | 41,1 % |
| aléatoire | 0,0 | 5,67 % | [3,6 ; 8,9] | 21,42× | 14,4 % |
| aléatoire | 0,5 | 5,33 % | — | 22,79× | 14,2 % |
| aléatoire | 0,7 | 4,00 % | — | 21,17× | 14,2 % |
| aléatoire | 0,9 | 5,67 % | — | 19,83× | 14,2 % |

**Le succès ne monte à aucun λ.** La directivité baisse de 8 % (14,21 → 13,04), très loin
de la cible 3×–5×, et **sans aucun gain de succès** — donc sans lever le goulot.

⚠️ **La part de `forward` est INVARIANTE** : 41,0 % → 41,1 % sur les trois λ. C'est la
preuve la plus directe que le filtre ne change pas le comportement.

### 3c. Pourquoi — les logits réels du cerveau (400 ticks)

| Grandeur | Valeur |
|---|---|
| **Autocorrélation lag-1, par action** | **0,685 · 0,733 · 0,772 · 0,748 · 0,715 · 0,847 · 0,748** |
| Écart-type ENTRE les 7 logits d'un même tick | 0,5674 |
| Écart-type TEMPOREL de chaque logit | 0,066 à 0,223 |
| `P(forward)` | **0,4092** (2,9× l'uniforme) |

🔴 **LA PRÉMISSE EST FAUSSE.** La décision n'est **pas** un tirage indépendant tick à tick :
elle est **déjà autocorrélée entre 0,69 et 0,85**. La mémoire de travail et le contexte
épisodique fournissent déjà le lissage temporel que λ devait apporter. La variation
temporelle (σ ≈ 0,07–0,22) est **2,5× à 8× plus petite** que l'écart entre actions au même
tick (σ = 0,567) : la politique est **stable dans le temps et tranchée dans l'espace**.

### 3d. La simulation géométrique (200 graines × 324 ticks, sans cerveau)

| Mode | k | Déplacement net | Cases distinctes | Taux de répétition |
|---|---|---|---|---|
| inertie **logits** | 0,0 | 8,65 | 33,9 | 0,1416 |
| inertie **logits** | 0,7 | 8,79 | 34,0 | 0,1564 |
| inertie **logits** | 0,9 | 8,68 | 34,1 | 0,1498 |
| inertie **probas** | 0,7 | 9,09 | 34,3 | 0,1563 |
| **bonus de répétition** | 2 | 11,59 | 36,6 | 0,4626 |
| **bonus de répétition** | 5 | **27,85** | 42,3 | **0,9105** |

Uniforme pur : `P(répéter) = 1/7 = 0,1429`.

## 4. Le mécanisme — pourquoi le filtre AR s'annule lui-même

Le filtre a **deux effets opposés** :

1. Il **corrèle** les vecteurs de logits successifs → devrait augmenter la persistance.
2. Il **divise leur variance** par `√((1−λ)/(1+λ))` → **aplatit le softmax vers l'uniforme**.

Mesuré : à λ = 0,9 l'écart-type des logits tombe à 0,159 et le taux de répétition revient à
**0,1481**, soit l'uniforme (0,1429). La persistance culmine à 0,1613 (λ=0,5) puis **décroît**.

> **Moyenner les ENTRÉES n'est pas biaiser vers la SORTIE.** Un vrai élan moteur exige un
> terme sur l'action **effectivement jouée** au tick précédent (mode `répétition` : 0,9105
> de persistance, déplacement ×3,2), pas une moyenne mobile des préférences.

## 5. Les vérifications passées

| Vérification | Résultat |
|---|---|
| **A/A (λ=0 vs banc 30/08)** | ✅ δ = 0,000000 sur les 3 grandeurs |
| **Témoin aléatoire sous inertie** | ✅ 5,67 % → 5,33 / 4,00 / 5,67 % — **aucun gain non plus** |
| **Inertie ≠ biais vers `forward`** | ✅ part invariante 41,0 → 41,1 % : le piège redouté ne s'est **pas** produit, mais parce que le filtre ne fait **rien** |
| **Formulation alternative (probas)** | ✅ testée, même résultat (9,09 vs 8,65 cases) |
| **Température** (trancher plus net) | ✅ testée, sans effet (8,45–8,96 cases de k=1 à k=8) |
| **Saturation du budget** | ✅ directivité max 22,79× < plafond 27,0× |

## 6. Les limites — écrites avant qu'on me les oppose

1. **n = 1 cerveau.** Le balayage n'a tourné que sur `A_g66`. La règle des 20 graines
   interdit d'affirmer un effet ; ici on constate une **absence** d'effet, doublée d'une
   explication mécanique (§4) et d'une simulation indépendante du cerveau — mais un λ
   utile sur un *autre* profil de cerveau n'est pas exclu.
2. **Politique FIGÉE.** Un agent qui *apprendrait* sous inertie verrait d'autres données.
3. `SimpleCrossingS9N1` **n'a ni porte ni clé** : rien ici ne prédit les niveaux 7+.
4. **Seul l'axe 1 est testé.** Les axes 2 (intention persistante de C2) et 3 (saturation de
   la curiosité) touchent la boucle d'apprentissage et ne sont **pas** mesurables en
   lecture seule — ils restent ouverts.

## 7. Ce que cela ferme, ce que cela laisse ouvert

**Fermé** — l'inertie sur les logits, dans les deux formulations, comme correctif de la
directivité. Et, plus important, **la prémisse** : la tête motrice n'est pas myope tick à
tick, elle est déjà lissée à 0,69–0,85.

**Ouvert** — la directivité reste le premier prédicteur du dépôt (`r = −0,8225`). Le
brownien ne vient donc **pas** d'une décision qui oscille : elle est stable et tranchée
(`P(forward) = 0,41`). Il vient d'ailleurs — hypothèse à tester : **le cap n'est pas
maintenu à travers les ROTATIONS**. L'agent avance droit, mais quand il tourne, rien ne
mémorise la direction qu'il visait.

⚠️ **Une 19ᵉ réfutation, mais la première qui tue une PRÉMISSE plutôt qu'un remède.**

---

## 8. Addendum du même jour — l'hypothèse successeur est réfutée à son tour, et ce qu'on
trouve à la place est plus gros

§7 proposait : « le cap n'est pas maintenu à travers les ROTATIONS ». **Faux.** Mesuré sur
60 épisodes du même cerveau (15 738 ticks) :

| Grandeur | Valeur |
|---|---|
| Rotations (actions 0/1) | 2 672 — **17,0 %** des ticks |
| Paires de rotations qui **s'annulent** | 223 — **8,3 %** des rotations |
| Longueur moyenne d'une salve de rotations | **1,20** (médiane **1**) |
| Salves de longueur ≥ 3 (≥ 3/4 de tour) | 63 sur 2 235 — **2,8 %** |

L'agent ne tourne pas en rond : il tourne **une fois**, puis fait autre chose. L'annulation
géométrique redoutée représente **8,3 % des rotations, soit 1,4 % des ticks**.

### Ce qui occupe réellement le budget

| Famille | Ticks | Part |
|---|---|---|
| `forward` | 6 452 | 41,0 % |
| rotations | 2 672 | 17,0 % |
| **stériles** (`pickup`/`drop`/`toggle`/`done`) | **6 614** | **42,0 %** |

🔴 **42 % du budget part en gestes qui ne peuvent RIEN faire.** `SimpleCrossingS9N1` ne
contient ni objet à ramasser, ni porte à activer : ces quatre actions y sont **stériles par
construction**, à 100 %, sur toutes les cartes du niveau.

Sur les 324 ticks de budget : **136 sont jetés**, 188 seulement sont moteurs. Rapporté au
trajet réel (14,21× × 12 cases ≈ 171 ticks), **~72 ticks stériles par victoire**.

⚠️ **Ce n'est pas neuf, et c'est le point important** : la v41.28 (26/08) avait mesuré
**57,2 %** de gestes stériles sur `Empty-5x5` et corrigé le *coût* (le travail tenté). Le
taux est passé à 42,0 % — **réduit d'un quart, toujours énorme**. Le correctif a rendu le
geste stérile plus **cher**, il ne l'a pas rendu moins **fréquent**.

Or l'avertissement inscrit dans `CLAUDE.md` à l'époque disait exactement ceci :

> « Si le gaspillage persiste après ce correctif, le levier suivant est le **BÉNÉFICE**
> (un geste qui ne change rien devrait n'apprendre rien), **pas** un durcissement du coût. »

**Le gaspillage a persisté.** La condition posée il y a six jours est remplie.

### Statut

🟡 **Mesure directe, n = 1 cerveau, non conclusive au sens de la règle des 20 graines.**
Elle décrit `A_g66` — le **meilleur** cerveau de la cohorte (37,33 %). À vérifier sur la
cohorte avant toute conclusion, et **avant toute modification du noyau**.
