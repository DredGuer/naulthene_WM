# LE TROU NOIR DU RÉFLEXE — pourquoi C2 n'a jamais évalué huit plans

**Date** : 2026-09-06 · **Statut** : ✅ **MÉCANISME ÉTABLI**, une hypothèse intermédiaire
**réfutée par son propre témoin** · **40 cerveaux × 1500 jours** · coût : **zéro run**.

> Prérequis §6.a de [CONCEPTION_v42](../../ameliorations/CONCEPTION_v42_intention_c2.md).
> Mesuré **avant** d'écrire la moindre ligne de la tête d'intention.

---

## 1. La question

La tête d'intention devait lire la `pensee_branche` **finale** du rollout — l'argument étant
qu'elle voit les futurs, là où C1 ne voit que le présent. Avant de la coder :
**ces futurs sont-ils encore distincts à l'horizon 7 ?**

## 2. Le résultat — ils ne le sont pas

| Horizon | Séparation moyenne | Médiane |
|---|---|---|
| **h = 1** | 0,12328 | 0,10522 |
| h = 3 | 0,03052 | 0,01440 |
| **h = 7** | **0,01039** | **0,00368** |

**Ratio h7/h1 : médiane 0,0295** — les branches perdent **97 %** de leur séparation.
**33 cerveaux sur 40** sous 0,10. Identique dans les deux régimes (apparié, `t` = −1,09, NS).

> Une tête lisant la pensée finale recevrait **huit vecteurs quasi identiques**.

## 3. La cause n'est PAS le modèle du monde

Diagnostic pas à pas sur `LIBRE_g11`, deux rollouts comparés :

| Rollout | pas 1 | pas 3 | pas 7 | **h7/h1** |
|---|---|---|---|---|
| **Conduite par C1** (code actuel) | 0,199 | 0,025 | 0,009 | **0,043** |
| **Action répétée** par branche | 0,199 | 0,218 | **0,229** | **1,15** |

🔴 **JEPA maintient parfaitement la séparation** quand chaque branche garde son geste.
L'effondrement vient entièrement de `argmax(tete_motrice)` : dès que C1 reprend la conduite,
les huit futurs convergent **en trois pas**.

**La `pensee_branche` finale ne dit pas « où mène l'action a », elle dit « où C1 va de toute
façon ».**

## 4. Pourquoi C1 écrase les branches — et la nuance de la cohorte

Au pas 2 du rollout, combien d'actions **distinctes** C1 vote-t-il sur les huit branches ?

| | 40 cerveaux |
|---|---|
| Part des ticks à **vote unique** | **61,3 %** en moyenne (médiane 66,3 %) |
| Actions distinctes | **1,36 / 8** en moyenne |
| Cerveaux > 90 % de vote unique | **13 / 40** |
| Cerveaux < 50 % | **16 / 40** |

⚠️ **`LIBRE_g11` (95 %) n'est PAS représentatif** — la dispersion va de **2,5 % à 100 %**.
Sans la cohorte, j'aurais sur-généralisé depuis un seul cerveau : c'est exactement le biais
de sélection du 30/08 (`r = −0,89` sur 4 cerveaux → +0,3961 à n=20).

**Lien avec l'effondrement** : `r(vote unique, ratio h7/h1) = **−0,3257**` (`t` = −2,12,
n=40) — **sous le seuil de Bonferroni** (2,86). Le vote unique **contribue** à la
convergence, il ne l'explique **pas seul**.

## 5. 🔴 L'hypothèse « C1 est insensible » — testée, et son témoin la RÉFUTE

Hypothèse intermédiaire : si C1 vote pareil sur huit futurs distincts, c'est qu'il est
insensible à son entrée. **Témoin** : lui présenter du **bruit gaussien calibré à la même
séparation** que les vrais futurs.

| Entrée présentée à C1 | Séparation | Actions distinctes |
|---|---|---|
| Les 8 **futurs réels** | 0,2016 | **1,05** |
| **Bruit** calibré à la même séparation | 0,2013 | **1,02** |

**Aucune différence.** L'hypothèse « les futurs sont sémantiquement pauvres » est donc
**réfutée** : ce n'est pas la nature du signal qui est en cause, c'est son **amplitude**.

### La mesure qui l'explique : la politique de C1 est constante par larges morceaux

Quelle perturbation faut-il pour que C1 change d'avis ? (150 pensées réelles, `LIBRE_g11`)

| Bruit (% de la norme de `pensee_bio`) | Ticks où l'argmax change |
|---|---|
| 1 % | 0,0 % |
| 5 % | 0,3 % |
| 10 % | 0,0 % |
| 25 % | 2,5 % |
| 50 % | 5,2 % |
| **100 %** (norme doublée) | **13,2 %** |
| 200 % | 31,2 % |

⚠️ **La séparation des huit futurs vaut 0,2016 — soit 8,12 % de la norme.** Elle tombe donc
dans la zone où **C1 ne change jamais d'avis**.

> **Ce n'est pas que C1 ignore les futurs : c'est qu'aucune perturbation de cette taille,
> quelle qu'en soit la nature, ne déplace sa décision.** Sa politique est quasi constante
> par morceaux, et les morceaux sont très larges.

C'est la même famille de faits que les victoires browniennes (14–18× le plus court chemin)
et que « chaque voix vote une action constante » (v37) — mesurée ici sur le mécanisme.

## 6. Ce que ça ferme, ce que ça ouvre

**Fermé** :
- La tête d'intention **ne peut pas** lire la `pensee_branche` finale telle quelle.
- « Les futurs sont sémantiquement pauvres » : **réfuté par témoin**.
- « C2 évalue huit stratégies » : il évalue **une destination** vue de huit départs.

**Ouvert** :
1. 🟢 **Rendre les branches persistantes** restaure la séparation (1,15 mesuré), à
   complexité inchangée `O(A × H)`. ⚠️ Touche un invariant de CLAUDE.md — **levé
   explicitement par l'utilisateur le 06/09**, la raison étant mesurée.
2. ⚠️ **Mais cela ne corrige pas la cause profonde** : même avec des branches distinctes,
   C1 ne réagit pas à une perturbation de 8 % de la norme. Un rollout séparé alimenterait
   une tête d'intention neuve — pas C1.
3. 🔴 **Question neuve, non tranchée** : pourquoi la politique de C1 est-elle si plate ?
   Aucune mesure du dépôt ne l'explique. C'est peut-être le même fait que le plafond, vu
   sous un autre angle.

---

*Trois sondes en lecture seule : `sonde_horizon_branches.py`, `sonde_c1_branches.py`, plus
le témoin de bruit calibré. Agrégats dans `brains/06092026_sondes_zero_run/`.*
