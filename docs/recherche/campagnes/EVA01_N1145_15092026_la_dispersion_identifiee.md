# EVA-01 — la dispersion rendue identifiable : `n_final = 1 868` (max des cartes)

**Date** : 2026-09-15 · **Statut** : ✅ mesure réelle, non dégénérée, **condition de validité tenue**
**4 cerveaux × 2 cartes figées × 1 145 épisodes = 9 160 épisodes**, cohorte SCI-01 bras `K8_NU`,
**mêmes cerveaux et mêmes graines que les pilotes antérieurs**, lecture seule.

> Protocole et règle écrits AVANT le run
> ([`brains/EVA01_pilote_n1145_15092026/LISEZ_MOI.md`](../../../brains/EVA01_pilote_n1145_15092026/LISEZ_MOI.md),
> dossier créé à 09:46:49, mesure lancée à 09:48:01). Campagne **neuve** : celles des pilotes
> antérieurs (`EVA01_pilote_13092026`, `EVA01_pilote_n200_13092026`) restent archivées.

---

## 1. La question posée

> « À 200 épisodes par carte, l'IC95 de σ̂ touche 0 : la dispersion inter-cerveaux est-elle
> **identifiable** si l'on porte le budget à ~1 145 épisodes par carte (condition
> `σ²/v > χ²(0,975;3)/3 − 1 = 2,1161`) — et quel `n_final = max(n_carte3, n_carte4)` cette
> dispersion impose-t-elle ? »

À 200 épisodes, la dé-convolution était **mal conditionnée** : `σ̂² = s² − v` était une petite
différence de deux quantités comparables, et l'IC95 de σ̂ **touchait zéro** (carte 3 et poolé).
`n = 10 810` était donc un **point de plug-in**, pas un dimensionnement. La spec borne le pilote
à 4 cerveaux ; le seul remède accessible est de faire baisser `v` (`v ∝ 1/n_ep`), donc de jouer
plus d'épisodes par cerveau.

## 2. Protocole exact (seule variable changée : le budget d'épisodes)

| Élément | Valeur |
|---|---|
| Cohorte / bras | `brains/08092026_sci01_balayage_K`, **`K8_NU`**, voie explicite |
| Cerveaux | `K8_NU_g11`, `_g22`, `_g33`, `_g44` — **identiques aux pilotes antérieurs** |
| Cartes | **3** `SimpleCrossingS9N1` (budget 324), **4** `LavaGapS5` (budget 100) |
| Épisodes par carte | **1 145** (BUDGET DE MESURE, jamais le `n` du protocole) |
| Graines d'évaluation | **10000 … 11144** (pool dérivé : `range(base, base + episodes)`) |

```bash
NAULTHENE_DEVICE=cpu PYTHONPATH=src venv/bin/python -m naulthene.instruments.pilote_banc \
  --cohorte brains/08092026_sci01_balayage_K --bras K8_NU --cartes 3 4 \
  --graines-pilote 11 22 33 44 --episodes 1145 --graine-eval-base 10000 \
  --cohorte-explicite brains/EVA01_pilote_n1145_15092026/cohorte_explicite.json \
  --dossier-sortie brains/EVA01_pilote_n1145_15092026
```

Durée réelle **4 536,6 s (75 min 36 s)** — 09:48:01 → 11:03:41 — pour une estimation de ~76 min
dérivée du rythme mesuré. Cohorte complète (4/4), **0 épisode tronqué**, `.brain` inchangés.

## 3. Les chiffres bruts — avant toute interprétation

### 3.1 Taux de franchissement par cerveau et par carte (`gagnés/n`)

| Cerveau | Carte 3 `SimpleCrossing` | Carte 4 `LavaGap` | **Poolé (2 cartes, n = 2 290)** |
|---|---|---|---|
| `K8_NU_g11` | **546/1145 = 0,476856** | 61/1145 = 0,053275 | 607/2290 = **0,265066** |
| `K8_NU_g22` | 481/1145 = 0,420087 | 163/1145 = 0,142358 | 644/2290 = **0,281223** |
| `K8_NU_g33` | 466/1145 = 0,406987 | 150/1145 = 0,131004 | 616/2290 = **0,268996** |
| `K8_NU_g44` | 448/1145 = 0,391266 | **279/1145 = 0,243668** | 727/2290 = **0,317467** |
| **Poolé carte** | **1941/4580 = 0,423799** | **653/4580 = 0,142576** | **2594/9160 = 0,283188** |
| SD observée `s` (ddof = 1) | 0,037282 | 0,078163 | **0,023866** |
| bruit du pilote `v` | 0,00021327 | 0,00010677 | **0,00008001** |
| part de `v` dans `s²` | **15,3 %** | **1,7 %** | **14,0 %** |
| **σ̂ = sqrt(s² − v)** | **0,034303** | **0,077477** | **0,022127** |
| IC95 de σ̂ | **[0,015257 ; 0,138238]** | **[0,043056 ; 0,291250]** | **[0,010138 ; 0,088535]** |
| IC95 de σ̂ **touche zéro** | ❌ **non** | ❌ **non** | ❌ **non** |

### 3.2 La corrélation inter-cartes — le poolage reste interdit

| Grandeur | n = 200 (tâche 7) | **n = 1 145 (cette campagne)** |
|---|---|---|
| cov inter-cartes des taux par cerveau (ddof = 1) | −0,00299375 | **−0,00261049** |
| **ρ (Pearson)** | **−0,8807** | **−0,8958** |

La corrélation reste **fortement négative** : les cerveaux s'échangent les cartes (`g11` premier
sur la carte 3 à 0,477 et dernier sur la 4 à 0,053 ; `g44` l'inverse, 0,391 / 0,244). Le taux
poolé est donc presque indépendant du cerveau (0,265 → 0,317), et la dispersion poolée
(σ̂ = 0,0221) tombe **sous** celle de chaque carte (0,0343 et 0,0775). **Pooler, c'est annuler
le signal.** Les cartes sont reportées **séparément**.

### 3.3 La dérivation — PAR CARTE, gelée au maximum

| Grandeur | Carte 3 | Carte 4 |
|---|---|---|
| `p̄` (taux poolé de la carte) | 0,423799 | 0,142576 |
| **σ̂ (dé-convoluée)** | **0,034303** | **0,077477** |
| seuil σ̂/3 | 0,011434 | 0,025826 |
| Ligne de calcul | `n = plus petit entier ≥ 1867,757392 tel que sqrt(0,423799 × 0,576201 / n) ≤ 0,011434 ⇒ n = 1 868` | `n = plus petit entier ≥ 183,3… tel que sqrt(0,142576 × 0,857424 / n) ≤ 0,025826 ⇒ n = 184` |
| **`n` dérivé** | **1 868** | **184** |

```
n_final = max( n_carte3, n_carte4 ) = max( 1 868, 184 ) = 1 868
```

La carte qui **contraint** est la 3, celle de plus **petit** σ̂ (la variance est au dénominateur).

**Lecture de la correction** : à 200 épisodes, `v` valait 71,6 % de `s²` sur la carte 3, ce qui
écrasait σ̂ (0,0220). À 1 145 épisodes, `v` tombe à 15,3 % de `s²` et **σ̂₃ remonte à 0,0343** :
la vraie dispersion entre cerveaux est plus grande que l'estimation à 200 épisodes, donc le `n`
requis est **plus petit** (1 868 contre la projection de 4 529 faite sur l'ancien point).

### 3.4 Coût de la tâche 9 à `n_final = 1 868`

| Grandeur | Valeur |
|---|---|
| Épisodes (2 bras × 20 cerveaux × 2 cartes × `n`) | **149 440** |
| Coût à ~0,5 s/épisode | **≈ 20,8 h (≈ 0,87 j)** |
| Coût raffiné par carte (0,63 s / 0,32 s) | **≈ 19,7 h (≈ 0,82 j)** |

## 4. Vérifications passées

| Vérification | Résultat |
|---|---|
| **Condition de validité pré-enregistrée** | IC95 de σ̂ **exclut zéro sur les deux cartes** (carte 3 : `[0,015257 ; 0,138238]` ; carte 4 : `[0,043056 ; 0,291250]`) — `touche_zero = False` partout, y compris poolé. La re-mesure **tient** la condition. |
| **Cohorte** | « couverture 4/4 runs », « tous les garde-fous passent », aucune exclusion |
| **Troncature** | **0 épisode tronqué sur 9 160** |
| **Lecture seule** | taille **et** mtime des 4 `.brain` identiques avant/après (`empreintes_avant.txt` / `empreintes_apres.txt`) |
| **Dérivation rejouable** | `--depuis-rapport` reproduit `pilote.json` à l'identique sur **11 champs** + les champs par carte |
| **A/A** | héritée de la tâche 7 (1 600/1 600 épisodes identiques, δ_A/A = 0) — **mécanisme inchangé** (graine torch + np + env par épisode), aucun rejeu complet re-lancé ici |
| **`n` = plus petit entier** | `deriver_n(0,423799, 0,034303, 3) = 1 868` et `1 867` échoue (contrainte non tenue) |

## 5. Les limites — écrites d'abord

1. **σ̂ est désormais identifiée, mais pas connue finement.** L'IC95 de σ̂ exclut zéro, donc
   `n` a une borne finie — mais l'intervalle reste large (carte 3 : un facteur ~9 entre les
   bornes 0,0153 et 0,1382). `s²` reste estimé sur **3 degrés de liberté** (4 cerveaux) :
   la condition « exclure zéro » est tenue, l'**instabilité** demeure. Monter à plus de
   cerveaux resserrerait l'IC, mais la spec borne le pilote à 4.
2. **La dispersion reste celle d'un seul bras** (`K8_NU`) : elle décrit l'hétérogénéité
   intra-bras, jamais l'écart entre deux bras.
3. **σ̂ suppose le taux par cerveau approximativement normal** et `v` **identique pour tous
   les cerveaux** (hypothèse de la dé-convolution), ni testé ici.
4. **Rien de tout ceci ne dit du cursus** ni de la justesse du banc : le pilote **dimensionne**
   l'instrument, il ne le **certifie** pas (test d'acceptation D3 toujours à faire).

## 6. Ce que cette campagne FERME

1. **`n` est identifiable : `n_final = 1 868`**, gelé au maximum des cartes (la carte 3
   contraint). C'est le remplacement **mesuré** du `10 810` (point de plug-in, tâche 7) et de
   la projection `4 529` (faite sur un σ̂₃ sous-estimé par le bruit).
2. **Le poolage est définitivement interdit** : ρ = −0,8958 (confirmant le −0,8807 de la tâche
   7) — le taux poolé est presque indépendant du cerveau.
3. **La prédiction du remède est vérifiée** : à 1 145 épisodes, `v` tombe de 71,6 % à **15,3 %**
   de `s²` sur la carte 3, et σ̂₃ se stabilise autour de 0,034 (au lieu de l'ancien 0,022
   écrasé par le bruit).
4. **Le pool d'évaluation `[10000, 10000 + n]` tient** : 1 868 graines (10000…11867), disjoint
   de l'entraînement, dérivé par le code (`banc_final.py:758`).

## 7. Ce que cette campagne LAISSE OUVERT

1. **Le test d'acceptation D3** (reproduire l'ordre SCI-01) : le banc est dimensionné, pas
   certifié — la tâche 9 doit encore le faire réussir.
2. **L'artefact de `trajectoire`** (8 victoires sur 41 sans le but, tâche 7) : toujours
   non corrigé, tâche d'instrument à part.
3. **L'IC de σ̂ reste large** : la valeur ponctuelle σ̂₃ = 0,0343 porte `n = 1 868`, mais la
   borne basse de l'IC (0,0153) porterait `n` ≈ 9 400, la borne haute (0,1382) `n` ≈ 115.
   Le `n` gelé est le **point**, pas une garantie — c'est écrit, pas tu.

---

**Artefacts** : `brains/EVA01_pilote_n1145_15092026/` — `LISEZ_MOI.md` (protocole écrit avant le
run), `cohorte_explicite.json`, `empreintes_avant.txt` / `empreintes_apres.txt`, `pilote.json`,
`banc_final_20260915_110341.json` (rapport brut : 9 160 épisodes), `pilote.log`,
`reproduction/pilote.json` (dérivation rejouée). Précédents :
[`EVA01_N200_13092026`](EVA01_N200_13092026_la_dispersion_deconvoluee.md) ·
[`EVA01_13092026`](EVA01_13092026_la_derivation_de_n.md).
