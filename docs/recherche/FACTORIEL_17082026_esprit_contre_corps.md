# Plan factoriel — c'est l'esprit qui débloque, pas le corps

**17/08/2026** — carnet de recherche, non normatif.
Point 2 de la feuille de route utilisateur : *« L'ablation croisée (Brain-Sparing seul vs
Corps-Seul) : isoler la contribution respective de la suppression du diviseur sur les logits
et du transfert du coût sur l'effort moteur. »*

---

## 1. Le protocole

Deux lois, croisées en 2×2, **10 graines par cellule**, 600 jours, CPU 1 thread.

| Cellule | loi A (brain-sparing) | loi B (économie d'action) |
|---|---|---|
| `v4115` | ✗ | ✗ |
| `esprit` | ✅ | ✗ |
| `corps` | ✗ | ✅ |
| `v4116` | ✅ | ✅ |

- **loi A** : `vigueur` retirée du produit sur les logits — elle ne peut plus écraser une
  préférence de C1 (`softmax` n'est pas invariant par échelle).
- **loi B** : `vigueur` déplacée sur le **coût de l'action** — un agent épuisé bouge moins
  cher, au lieu de décider moins bien.

Contrôles : 40 logs à 600/600 jours, **aucun crash**, campagne terminée à 16h08.

---

## 2. Le résultat : la loi A fait tout, la loi B ne fait rien

| Cellule | niveau 4 atteint (Wilson 95 %) | niveau max |
|---|---|---|
| témoin (A off, B off) | 0/10 · **0 %** [0–28] | 3 |
| **brain-sparing SEUL (A)** | 8/10 · **80 %** [49–94] | **5** |
| économie d'action SEULE (B) | 0/10 · **0 %** [0–28] | 3 |
| les deux (A+B) | 6/10 · **60 %** [31–83] | 4 |

**La loi B seule ne franchit aucun palier de plus que le témoin** — 0/10 des deux côtés,
niveau max 3 des deux côtés.

Tests des signes appariés (mêmes graines) :

```
esprit vs corps  : gagne 9 perd 1 nul 0  → p = 0,0215   ✅
v4116  vs corps  : gagne 8 perd 0 nul 2  → p = 0,0078   ✅
corps  vs v4115  : gagne 1 perd 1 nul 8  → p = 1,0000   ✗ aucun effet
esprit vs v4116  : gagne 3 perd 1 nul 6  → p = 0,6250   ✗ indistinguables
```

> **La totalité de l'effet mesuré en campagne n=20 vient de la loi A.** La loi B est
> indistinguable du témoin sur le franchissement de paliers (p = 1,0000, 8 nuls sur 10).

---

## 3. Pourquoi c'est contre-intuitif, et ce que ça dit du corps

La loi B **fonctionne** pourtant, au sens métabolique — elle est la seule à améliorer
franchement l'état du corps :

| Cellule | énergie | vigueur | entropie C1 | ratio C2/C1 |
|---|---|---|---|---|
| témoin | 0,202 | 0,196 | **0,029** | 0,155 |
| brain-sparing seul (A) | 0,251 | 0,216 | **0,565** | 2,841 |
| économie d'action seule (B) | **0,393** | **0,313** | **0,061** | 0,315 |
| les deux (A+B) | **0,561** | **0,439** | **0,601** | 3,093 |

La loi B **double presque l'énergie** (0,202 → 0,393) et la vigueur (0,196 → 0,313). Le
métabolisme va mieux. **Et l'agent n'apprend pas plus pour autant.**

La raison se lit dans la colonne « entropie C1 » : sous la loi B seule elle reste à
**0,061** — C1 est toujours une voix quasi muette. Nourrir un agent qui décide au hasard
lui donne un hasard mieux nourri.

> **Un corps en meilleur état ne suffit pas si la décision reste écrasée.** L'énergie n'est
> pas le goulot : c'est ce que l'agent en fait. Le diagnostic
> [`DIAGNOSTIC_17082026_pourquoi_C2_est_etouffe.md`](DIAGNOSTIC_17082026_pourquoi_C2_est_etouffe.md)
> concluait que « C2 est étouffé par la faim » — cette campagne le **corrige** : C2 était
> étouffé par une multiplication, et la faim n'en était que le déclencheur visible.

⚠️ La loi B reste défendable pour une autre raison : elle est la seule des deux à rendre
`vigueur` fonctionnelle. Sans elle, le brain-sparing laisse `vigueur` ne moduler **rien**
que de la télémétrie — c'est le défaut que l'audit du dogme avait relevé. Le combiné A+B
est donc le seul état cohérent du code, même si son gain sur les paliers est porté par A.

---

## 4. Le premier niveau 5 du projet

`esprit_g7` atteint le **niveau 5 — « Primaire 2 (Éviter le danger) »**, c'est-à-dire
`LavaGap`. Et il n'y passe pas en coup de vent :

```
148 jours  Nourrisson (Premiers pas)
 18 jours  Éveil (Départ aléatoire)
270 jours  Maternelle (Longue distance)
 13 jours  Primaire 1 (Contourner)
151 jours  Primaire 2 (Éviter le danger)   ← 25 % de sa vie
```

**151 jours au niveau 5** — un quart de son existence. Ce n'est pas un franchissement
accidentel suivi d'une rechute.

⚠️ **C'est UNE graine sur 40.** Selon le §4 de la règle de mesure, c'est une **anecdote**,
la catégorie explicitement marquée « ❌ jamais fiable ». Elle ne prouve rien sur le taux
d'atteinte du niveau 5. Ce qu'elle établit, en revanche, est plus modeste et solide : le
palier 5 **n'est pas un mur infranchissable** — au moins un cerveau y vit durablement. Avant
aujourd'hui, 0 cerveau sur les 60 de la campagne n=20 y était parvenu.

Et le paradoxe à ne pas manquer : la cellule `esprit` a la **maîtrise finale la plus basse**
(8,0 % contre 18,5 %). Normal — elle est la seule à passer sa vie sur les paliers durs. Le
même piège que le compteur de victoires du carnet n=20 : **une métrique de score récompense
la stagnation** quand les bras ne vivent pas dans les mêmes mondes.

---

## 5. Ce que ça change pour la suite

**Tranché :**

- l'effet du correctif est **entièrement attribuable à la loi A** ;
- la loi B améliore le corps sans améliorer l'apprentissage — elle est *nécessaire à la
  cohérence du code*, pas à la performance ;
- le mur du niveau 4 est levé (0 % → 80 %), et le niveau 5 est franchissable au moins une
  fois.

**Ouvert :**

- le mur s'est-il simplement déplacé au niveau 5 ? 1 cerveau sur 40 y arrive — il faut une
  campagne dédiée sur `esprit` seul, à n ≥ 20, pour le savoir ;
- pourquoi `esprit` (A seul) fait-il *aussi bien ou mieux* que A+B (3-1-6, p = 0,62) alors
  que A+B a une bien meilleure énergie ? Les deux cellules sont statistiquement
  indistinguables, mais si A seul dominait vraiment, cela signifierait que **plus d'énergie
  nuit** — une piste à ne pas écarter sans mesure ;
- le test de falsification P17 (`--defi-force`) devient moins urgent : le mur du niveau 4
  n'était pas le curriculum, il était dans la décision. Il reste pertinent pour le niveau 5.
