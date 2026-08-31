# La curiosité est une rente permanente — et elle ne prédit rien

**30/08/2026** · `recherche/enquetes_closes/` : **non normatif**, à lire avant de rouvrir.

## La question posée

Après le constat que **86 % du signal est dense et hors-sujet** ([CREUX_30082026](CREUX_30082026_la_recompense_n_est_pas_creuse.md)) :

> *« Comment la tâche peut-elle piloter la politique si elle ne pèse que 14 % de la
> fonction de valeur ? Faut-il mesurer l'impact d'une diète sévère sur les termes internes,
> ou d'abord disséquer les 86 % ? »*

**La dissection est le test préalable de la diète** — c'est elle qui dit si l'ablation
mesurerait quelque chose. Elle a été faite en premier, et elle **répond déjà**.

---

## Verdict en une phrase

> La curiosité **est** bien une rente permanente (l'erreur JEPA ne décroît pas sur
> 1440 jours, ratio médian **1,11×**), elle **pèse 40,4 %** du signal positif — et elle
> **ne prédit rien** : les cerveaux qui en reçoivent le moins et ceux qui en reçoivent le
> plus maîtrisent **15,0 % contre 15,0 %**. **Dix-huitième réfutation.**

---

## 1. La dissection des 86 %

Mesuré sur **40 cerveaux** (cohorte AB3, niveau 3, 800 ticks) :

| Composante | Part du signal positif |
|---|---:|
| **Curiosité** (`dopamine_normalisée × erreur_JEPA`) | **40,4 %** |
| Sous-objectifs + records de proximité | 26,6 % |
| `r_bio` (métabolisme) | 20,0 % |
| **Monde** (la tâche) | **13,0 %** |

**Ce que la diète promettait, arithmétiquement** : couper la curiosité ferait passer la
tâche de **13,0 % à 21,8 %** du signal — un **doublement du poids relatif**, sans rien
ajouter. Le levier est réel.

---

## 2. La curiosité EST une rente permanente ✅ confirmé

`dopamine_curiosite = dopamine_normalisée × min(erreur_JEPA, PLAFOND)`. Elle paie la
**surprise**. Si l'agent comprenait son monde, elle s'éteindrait d'elle-même.

Erreur JEPA, premier cinquième contre dernier cinquième du run (1440 jours) :

| | Valeur |
|---|---:|
| Ratio médian fin/début | **1,11×** |
| Cerveaux dont l'erreur **décroît** (<1) | **19 / 40** |

**L'erreur JEPA ne décroît pas** — elle augmente légèrement, et le sens de variation est un
tirage à pile ou face. L'agent est payé en continu pour une surprise qui ne s'épuise
jamais : c'est bien une **rente**, exactement comme la question le supposait.

---

## 3. 🔴 Mais la rente ne prédit RIEN — et le test est sans appel

### 3.1 La curiosité qui s'éteint ne prédit pas la maîtrise

| Corrélation | r | t | n |
|---|---:|---:|---:|
| `ratio_JEPA(fin/début)` ~ maîtrise | **+0,0116** | **+0,07** | 40 |

Un cerveau dont le modèle du monde s'améliore ne maîtrise **pas** mieux.

### 3.2 La part de curiosité ne prédit pas la maîtrise

| Corrélation | r | t | n |
|---|---:|---:|---:|
| `part_curiosité` ~ maîtrise | **−0,0173** | **−0,11** | 40 |

Et le **signe s'inverse entre les deux bras** (A : +0,2277 · B : −0,2623) — signature du
bruit, déjà relevée dans la [cohorte du barème](../campagnes/COHORTE_30082026_le_bareme_ne_predit_rien.md).

### 3.3 Le test direct, en deux groupes

| Groupe | Maîtrise moyenne | n |
|---|---:|---:|
| Curiosité **faible** (< 35 % du signal) | **15,0 %** | 14 |
| Curiosité **forte** (> 45 % du signal) | **15,0 %** | 14 |

**Identiques au dixième de point.** Il n'existe pas de variation naturelle de la curiosité
qui s'accompagne d'une variation de performance.

---

## 4. Pourquoi la diète n'est pas justifiée — et ce que ça ne dit pas

La cohorte offre une **variation naturelle large** de la part de curiosité (20,0 % à
64,6 %, soit un facteur **3,2×**). Sur cette étendue, la performance est **plate**.

> Un facteur 3,2× de variation naturelle produit **0,0 point** d'écart de maîtrise.
> Une ablation qui diviserait la curiosité par ~1,7 (40 % → 0) explorerait une plage
> **plus étroite** que celle déjà observée sans effet.

⚠️ **Ce n'est PAS une preuve que la diète serait sans effet.** Deux limites qui comptent :

1. **Observationnel ≠ interventionnel.** La variation naturelle entre cerveaux n'est pas
   une manipulation contrôlée : la part de curiosité est ici une *conséquence* du vécu
   autant qu'une cause. Une ablation forcée pourrait sortir du régime observé.
2. **La corrélation nulle porte sur les PARTS, pas sur la présence.** Couper entièrement la
   curiosité change la nature du signal (0 %), pas seulement sa proportion — un régime
   qu'aucun cerveau n'a exploré.

Ce que la mesure établit, c'est que **rien dans les données existantes ne justifie de
dépenser une campagne de 40 runs** sur cette hypothèse. Ce n'est pas la même chose que de
la réfuter définitivement.

---

## 5. Ce que cela ferme, ce que cela laisse

**Fermé** : *« la curiosité écrase la tâche, donc la couper libérera l'apprentissage »* —
sous sa forme prédictive, la plus testable. Trois tests indépendants, tous nuls.

**Toujours vrai, et non expliqué** : la tâche ne pèse que **13 %** du signal, et la
curiosité **40 %**. Le déséquilibre est réel, il est simplement **sans corrélat mesurable**
avec la performance.

**Ce qui reste ouvert, et qui n'est pas une question de barème** : la cohorte montre que ni
la représentation (`d' ≈ 3`), ni la formule du crédit (MC/TD/GAE), ni la densité du signal,
ni sa composition ne prédisent la maîtrise. **Dix-huit hypothèses, dix-huit réfutations.**
Le tableau des suspects reste **vide**.

⚠️ Toutes les mesures de ce document sont des **lectures directes** (§4 de la règle de
mesure) sur 40 cerveaux — fiables comme lectures, mais **aucune comparaison appariée**, donc
aucune causalité établie dans un sens ni dans l'autre.
