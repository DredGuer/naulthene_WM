# Pourquoi l'agent joue des gestes inutiles — il optimise exactement ce qu'on lui demande

**20/08/2026** — carnet de recherche, non normatif.
Question utilisateur : *« il faut comprendre pourquoi »*.

---

## 1. Le constat

Sur `Empty-5x5` (pièce vide, but à 4 cases), part des ticks par action — dernier quart de
10 runs × 300 jours :

| action | part des ticks | stérile |
|---|---|---|
| tourner G | 9,9 % | 0 % |
| tourner D | 12,3 % | 0 % |
| **AVANCER** | **20,6 %** | 52 % |
| ramasser | 21,4 % | **86 %** |
| poser | 8,6 % | **100 %** |
| activer | 14,9 % | **100 %** |
| parler | 9,8 % | **100 %** |

**57,2 % des ticks** partent dans des gestes qui ne changent rien à cette carte.

---

## 2. La cause — une inversion d'incitation, mesurée

`calculer_effort_metabolique` (v41.20, le travail physique) facture :

| geste | effort |
|---|---|
| **AVANCER** (déplacement réel) | **4,0000** |
| tourner (rotation) | 1,4545 |
| **STÉRILE** (poser / activer / parler) | **1,0909** |

> **Le seul geste qui rapproche du but coûte 3,7× plus cher que ne rien faire.**

`r_bio` étant la dérivée du déficit, chaque tick facture cet effort en énergie. Donc :

- **avancer** → punition immédiate, forte, à chaque tick ;
- **parler** → punition minimale, aucun risque ;
- **la récompense du but** → +1, **rare et lointaine**.

**L'agent n'est pas irrationnel : il joue optimalement sous la fonction de coût qu'on lui
donne.** Économiser en jouant des gestes stériles est la meilleure stratégie disponible.
Le comportement est une **conséquence**, pas un défaut d'apprentissage.

---

## 3. Ce que ça réfute

Trois hypothèses testées, deux écartées :

| hypothèse | verdict |
|---|---|
| **H-a** — les gestes stériles ne coûtent rien, donc rien ne les décourage | ✅ **confirmée** (1,09 contre 4,00) |
| **H-b** — l'entropie d'exploration force ces actions | ❌ écartée : entropie C1 **0,499**, 4 actions distinctes sur 7 — l'agent a de vraies préférences, il n'explore pas au hasard |
| **H-c** — la tête motrice n'apprend pas | ❌ écartée : la maîtrise monte de 13,8 % à 54,4 % sur 10/10 graines |

**La politique fonctionne. C'est l'objectif qu'elle poursuit qui est mal posé.**

---

## 4. Le lien avec la v41.20

Le correctif v41.20 avait remplacé une table de 7 constantes par un **travail physique**
dérivé (masse × distance). C'était juste sur le plan du dogme, et il a corrigé une
sur-facturation réelle (×4,73).

Mais il a produit un effet de bord non anticipé : **la physique rend le déplacement
intrinsèquement plus cher que l'immobilité**, ce qui est vrai dans le monde réel — sauf
qu'un organisme vivant qui ne bouge pas *meurt*, alors qu'ici il économise.

Chez le vivant, le coût de l'immobilité est payé par la **faim qui monte pendant ce
temps**. Ici, `taux_satiete` est bien prélevé à chaque tick… mais il est **identique quel
que soit le geste**, donc il ne pénalise pas l'inaction *relativement* à l'action.

---

## 5. Ce que cela n'est pas

⚠️ **Ce n'est pas un argument pour re-poser une table de coûts.** Le dogme tient : le
problème n'est pas que l'effort soit dérivé, c'est que **le bénéfice ne l'est pas
symétriquement**. Un geste qui ne change rien au monde devrait rapporter zéro *et* coûter
quelque chose ; aujourd'hui il coûte le minimum et rapporte zéro — donc il gagne.

⚠️ **Ce n'est pas la douleur.** Trois nuits de travail sur la nociception ont mesuré
`t = −1,51` (non significatif) sur le comportement. Le blocage était ailleurs.

---

## 6. Pistes, non arbitrées

1. **Le geste stérile doit coûter ce qu'il prétend faire.** L'agent qui joue `poser` sans
   rien porter dépense l'intention d'un `poser` — pas le minimum du barème. Le signal
   existe déjà (`sterile` est mesuré depuis la sonde v41.19) mais n'entre nulle part.
2. **Le temps doit coûter plus que le mouvement.** Si rester immobile creusait le déficit
   plus vite qu'un pas ne le creuse, l'immobilité cesserait d'être rentable — c'est ce que
   fait la faim chez le vivant.
3. **Ne rien changer et l'assumer** : sur une carte à ressources, économiser *est* adaptatif.
   Le comportement n'est aberrant que parce que `Empty-5x5` n'a rien à manger.

⚠️ Aucune de ces pistes n'est testée. La mesure établit **la cause**, pas le remède.
