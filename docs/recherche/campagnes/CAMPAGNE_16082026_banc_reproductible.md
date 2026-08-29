# Campagne du 16 août 2026 — 20 graines × 2500 jours, banc reproductible

> **La première campagne du projet dont les résultats sont reproductibles.** Le correctif
> v41.9 (cartes seedées) a été validé par un témoin A/A tournant en parallèle : deux runs
> de graine identique sont restés **identiques sur les 2500 jours**.
>
> ⚠️ Les chiffres antérieurs à la v41.9 ne sont **pas comparables** à ceux-ci : les cartes
> tirées ont changé.

---

## 1. Le protocole

| | |
|---|---|
| Graines | 20 (11 → 222) |
| Durée | 2500 jours chacune |
| Code | v41.9 |
| Témoin | 1 run A/A (graine 11 dupliquée), **OK sur 2500 jours** |
| Total simulé | 50 000 jours, ~350 000 épisodes |

## 2. Les résultats

| Palier | Graines | Taux | IC 95 % |
|---|---|---|---|
| ≥ 1 promotion (niveau 2+) | **17/20** | **85 %** | [64 % ; 95 %] |
| ≥ 2 promotions (niveau 3+) | **17/20** | **85 %** | [64 % ; 95 %] |
| ≥ 3 promotions (niveau 4+) | **0/20** | **0 %** | [0 % ; 16 %] |

**34 promotions au total.** Médiane : 1ʳᵉ au jour **781**, 2ᵉ au jour **978**.

### Le détail

| Graine | Niveau | Jours de promotion |
|---|---|---|
| g66 | 3 | 129, 210 |
| g77 | 3 | 282, 319 |
| g177 | 3 | 361, 394 |
| g22 | 3 | 484, 581 |
| g55 | 3 | 491, 609 |
| g199 | 3 | 606, 639 |
| g211 | 3 | 698, 978 |
| g122 | 3 | 781, 817 |
| g11 | 3 | 823, 966 |
| g88 | 3 | 852, 1196 |
| g144 | 3 | 1006, 1046 |
| g99 | 3 | 1056, 1078 |
| g133 | 3 | 1123, 1158 |
| g111 | 3 | 1307, 1336 |
| g44 | 3 | 1587, 1621 |
| g155 | 3 | 1874, 2136 |
| g166 | 3 | **36, 2410** ⚠️ |
| g33, g188, g222 | 1 | — |

## 3. 🔴 Le mur est au niveau 3, et il est absolu

**0 graine sur 20 n'atteint le niveau 4**, malgré 2500 jours chacune — soit 50 000 jours
cumulés. L'intervalle de confiance est [0 % ; 16 %] : même dans le pire cas, moins d'une
graine sur six franchirait ce palier.

Le niveau 3 est `Empty-8x8` — une pièce vide, plus grande. Le niveau 4 est
`SimpleCrossingS9N1` : **le premier niveau où il faut contourner un mur**.

> C'est la première fois que le blocage du projet est localisé avec cette précision :
> ce n'est ni le départ, ni la distance, c'est **l'apparition d'un obstacle à contourner**.

## 4. 🎯 Les deux premiers paliers forment UN SEUL obstacle

Écart entre 1ʳᵉ et 2ᵉ promotion, sur les 17 graines promues :

```
22, 29, 33, 33, 34, 35, 36, 37, 40, 81, 97, 118, 143, 262, 280, 344, 2374
     └──────────── médiane : 40 jours ────────────┘
```

**11 graines sur 17 (65 %) enchaînent en moins de 100 jours.** Une fois le premier palier
franchi, le second suit presque aussitôt.

Conséquence pratique : `Empty-5x5` → `Empty-Random-6x6` → `Empty-8x8` ne sont **pas trois
apprentissages**, mais un seul. Le cursus gagnerait à les traiter comme un palier unique et
à consacrer sa granularité là où le mur se trouve.

### L'exception g166 — une promotion prématurée

g166 est promue au **jour 36** (record de la campagne) puis reste bloquée **2374 jours**.
C'est la seule graine promue très tôt *et* bloquée très longtemps.

Lecture probable : promotion sur un coup de chance, l'agent arrivant au niveau 2 **sans
avoir réellement acquis le niveau 1**. C'est exactement ce que le critère de maturité
v40.2 (un produit de trois facteurs) devait empêcher — il reste donc une porte de sortie
par la chance, à n = 1 sur 20.

## 5. Ce que l'échantillon permet — et ce qu'il ne permet pas

**Permet** : affirmer que le taux de franchissement des deux premiers paliers est de
**85 % [64-95]** à 2500 jours, et que le niveau 4 n'est **pas atteint** (0/20).

**Ne permet pas** : détecter un correctif qui déplacerait le taux de moins de **31 points**.
À n = 20, tout effet plus petit est indistinguable du bruit.

> Pour comparer deux versions sur le niveau 4 (taux actuel : 0 %), n = 20 suffit — toute
> graine qui le franchirait serait un signal. Pour comparer sur les paliers 1-2 (85 %), il
> faudrait **n ≥ 60**, le taux étant déjà proche du plafond.
