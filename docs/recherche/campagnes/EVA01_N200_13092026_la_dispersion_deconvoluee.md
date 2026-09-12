# EVA-01 — la dispersion DÉ-CONVOLUÉE : `n` passe de 333 à 10 810

**Date** : 2026-09-13 (tour de correction 1) · **Statut** : ✅ mesure réelle, non dégénérée
**4 cerveaux × 2 cartes figées × 200 épisodes = 1 600 épisodes**, cohorte SCI-01 bras `K8_NU`,
**mêmes cerveaux et mêmes graines que le premier pilote**, lecture seule.

> Protocole et règle écrits AVANT le run
> ([`brains/EVA01_pilote_n200_13092026/LISEZ_MOI.md`](../../../brains/EVA01_pilote_n200_13092026/LISEZ_MOI.md),
> dossier créé à 00:55:36, mesure lancée à 00:55:59). Campagne **neuve** : celle du premier
> pilote (`EVA01_pilote_13092026`) reste archivée, jamais réécrite.

---

## 1. La question posée

> « La dispersion inter-cerveaux publiée est-elle celle des **cerveaux**, ou celle du
> **pilote** ? »

Le premier pilote publiait `s = 0,071807` ⇒ `n = 333`. Une revue indépendante a montré que
`s` **majore** la dispersion réelle : le taux d'un cerveau est une moyenne de `n` tirages, donc
bruité, et

```
E[s²] = σ² + v        σ = dispersion RÉELLE entre cerveaux
                      v = variance d'ÉCHANTILLONNAGE du taux de chaque cerveau
```

Au premier pilote, `v = 0,00454492` pour `s² = 0,00515625` : **88 % de la dispersion publiée
était le bruit du pilote**. `333` était donc une **borne basse**, et à `n = 333` le bruit de
mesure (`SE = 0,023923`) valait **1,21 σ̂** — l'inverse exact de l'intention du §8bis.

⚠️ **Ce biais ne se corrige PAS en ajoutant des cerveaux** : `E[s²] = σ² + v` quel que soit
leur nombre. Il se corrige en jouant plus d'**épisodes par cerveau** (`v ≈ p(1−p)/n`). D'où
cette campagne : **mêmes 4 cerveaux, mêmes 4 graines, 200 épisodes par carte au lieu de 20**.

## 2. Protocole exact (seule variable changée : le budget d'épisodes)

| Élément | Valeur |
|---|---|
| Cohorte / bras | `brains/08092026_sci01_balayage_K`, **`K8_NU`**, voie explicite |
| Cerveaux | `K8_NU_g11`, `_g22`, `_g33`, `_g44` — **identiques au premier pilote** |
| Cartes | **3** `SimpleCrossingS9N1` (budget 324), **4** `LavaGapS5` (budget 100) |
| Épisodes par carte | **200** (BUDGET DE MESURE, jamais le `n` du protocole) |
| Graines d'évaluation | **10000 … 10199** (⚠️ pool « 10000…10099 » de la spec §8 **dépassé** : il avait été dimensionné pour l'ancien `n = 100` ; disjoint de l'entraînement 5…199) |

```bash
NAULTHENE_DEVICE=cpu PYTHONPATH=src venv/bin/python -m naulthene.instruments.pilote_banc \
  --cohorte brains/08092026_sci01_balayage_K --bras K8_NU --cartes 3 4 \
  --graines-pilote 11 22 33 44 --episodes 200 --graine-eval-base 10000 \
  --cohorte-explicite brains/EVA01_pilote_n200_13092026/cohorte_explicite.json \
  --dossier-sortie brains/EVA01_pilote_n200_13092026
```

Durée réelle **766 s (12 min 46)** — 00:55:59 → 01:08:45 — pour une estimation de ~13 min
dérivée du rythme mesuré. Cohorte complète (4/4), **0 épisode tronqué**, `.brain` inchangés.

## 3. Les chiffres bruts — avant toute interprétation

### 3.1 Taux de franchissement par cerveau et par carte (`gagnes/n`)

| Cerveau | Carte 3 `SimpleCrossing` | Carte 4 `LavaGap` | **Poolé (2 cartes, n = 400)** |
|---|---|---|---|
| `K8_NU_g11` | **97/200 = 0,485** | 8/200 = 0,040 | 105/400 = **0,2625** |
| `K8_NU_g22` | 82/200 = 0,410 | 25/200 = 0,125 | 107/400 = **0,2675** |
| `K8_NU_g33` | 81/200 = 0,405 | 30/200 = 0,150 | 111/400 = **0,2775** |
| `K8_NU_g44` | 79/200 = 0,395 | **48/200 = 0,240** | 127/400 = **0,3175** |
| **Poolé carte** | **339/800 = 0,42375** | **111/800 = 0,13875** | **450/1 600 = 0,28125** |
| SD observée `s` (ddof = 1) | 0,041307 | 0,082298 | **0,024958** |
| IC95 de `s` (χ², df = 3) | [0,023400 ; 0,154014] | [0,046621 ; 0,306851] | **[0,014139 ; 0,093058]** |
| bruit du pilote `v` | 0,00122093 | 0,00059749 | **0,00045461** |
| part de `v` dans `s²` | 71,6 % | 8,8 % | **73,0 %** |
| **σ̂ = sqrt(s² − v)** | 0,022030 | **0,078584** | **0,012973** |
| IC95 de σ̂ | [0 ; 0,150000] **touche 0** | [0,039699 ; 0,305876] | **[0 ; 0,090583] touche 0** |

### 3.2 La dérivation (règle du §8bis, appliquée à σ̂)

| Grandeur | Valeur |
|---|---|
| `p̄` poolé | **0,281250** (450/1 600) |
| `v` (variance d'échantillonnage) | **0,00045461** — 73,0 % de la variance observée |
| `sd_inter` **observée** (gonflée) | 0,024958 |
| **σ̂ dé-convoluée** | **0,012973** |
| seuil σ̂/3 | **0,004324** |
| Ligne de calcul | `n = plus petit entier >= 10 809,357666 tel que sqrt(0,281250 × 0,718750 / n) <= 0,012973 / 3 = 0,004324 ⇒ n = 10 810` |
| **`n` DÉRIVÉ (de σ̂)** | **10 810** |
| borne basse (de `s` observée) | **2 921** |

### 3.3 Sensibilité — un `n` qui va de 222 à l'infini

| Formulation | dispersion lue | `n` | coût tâche 9 (6 bras × 20 graines × 2 cartes) |
|---|---|---|---|
| **σ̂ poolé (retenu)** | 0,012973 | **10 810** | **≈ 342 h (14 jours)** |
| `s` poolée (borne basse) | 0,024958 | 2 921 | ≈ 93 h |
| σ̂ poolé, convention « un seul binôme » pour `v` | 0,010842 | 15 478 | ≈ 490 h |
| σ̂ de la carte 3 seule | 0,022030 | 4 529 | ≈ 143 h |
| σ̂ de la carte 4 seule | 0,078584 | 175 | ≈ 15 h |
| **borne HAUTE de l'IC95 de σ̂** | 0,090583 | **222** | ≈ 7 h |
| **borne BASSE de l'IC95 de σ̂** | **0,000000** | **INDÉFINI** | — |

⚠️ **La dé-convolution est mal conditionnée à 4 cerveaux** : σ̂² = s² − v est une différence
de deux quantités comparables (0,000623 − 0,000455). C'est ce qui produit l'IC qui touche 0,
et c'est aussi pourquoi la convention de `v` déplace encore `n` d'un facteur 1,43 (10 810
contre 15 478) même à 200 épisodes par cerveau.

### 3.4 Vérifications passées

| Vérification | Résultat |
|---|---|
| **A/A** — protocole rejoué à l'identique (`replicat_AA/`) | **1 600/1 600 épisodes identiques** (`gagne`, `ticks`, `retour`, `trajectoire`, `monde`), seuls les `duree_s` diffèrent ; `p̄`, `s`, σ̂, les deux `n` : **identiques** ⇒ **δ_A/A = 0** |
| **Cohorte** | « couverture 4/4 runs », « tous les garde-fous passent », aucune exclusion |
| **Troncature** | **0 épisode tronqué sur 1 600** |
| **Lecture seule** | taille **et** mtime des 4 `.brain` identiques avant/après (`empreintes_avant.txt` / `empreintes_apres.txt`) |
| **Contrôle interne du biais** | le prix du biais est VISIBLE : à 20 épisodes les taux poolés s'étalaient de 0,175 à 0,350 (amplitude **0,175**) ; à 200, de 0,2625 à 0,3175 (amplitude **0,055**). L'étalement du premier pilote était majoritairement du tirage, exactement ce que `E[s²] = σ² + v` prédit |
| **Carte tenue** | `env_id` et `budget` constants par cellule sur les 1 600 épisodes |
| **Dérivation rejouable** | `--depuis-rapport` reproduit `pilote.json` (mêmes champs, mêmes `n`) |

## 4. Les limites — écrites d'abord

1. 🔴 **L'IC95 de σ̂ touche ZÉRO.** Sur données poolées, la dispersion réelle n'est **pas
   distinguable du bruit** à 4 cerveaux : `n` peut valoir 10 810, 222, ou n'avoir aucune borne
   finie. Le `10 810` est une **estimation ponctuelle**, pas un dimensionnement garanti.
2. **La dé-convolution corrige le BIAIS, jamais l'INSTABILITÉ.** `s²` reste estimé sur **3
   degrés de liberté** (4 cerveaux) : corriger le biais ne resserre pas l'intervalle, et
   l'intervalle est devenu plus gênant à mesure que le biais disparaissait.
3. **σ̂² est une petite différence de deux grandes quantités** : à 4 cerveaux, la convention
   de `v` déplace `n` d'un facteur 1,43. Ce n'est pas un détail d'implémentation, c'est une
   fragilité de la méthode à cet effectif.
4. **La dispersion reste celle d'un seul bras** (`K8_NU`) : elle décrit l'hétérogénéité
   intra-bras, jamais l'écart entre deux bras.
5. **σ̂ suppose le taux par cerveau approximativement normal** et `v` **identique pour tous
   les cerveaux** (hypothèse de la dé-convolution). Ni l'une ni l'autre n'est testée ici.
6. **Rien de tout ceci ne dit du cursus** ni de la justesse du banc : le pilote **dimensionne**
   l'instrument, il ne le **certifie** pas (test d'acceptation D3 toujours à faire).
7. **Le budget d'évaluation dépasse le pool gelé** : 200 épisodes ⇒ graines 10000…10199, au
   delà des « 10000…10099 » du §8. Le pool est resté disjoint de l'entraînement, mais c'est
   une constante gelée de plus que l'ancien `n = 100` avait dimensionnée.

## 5. Ce que cette campagne FERME

1. **Le premier `n` était faux, et il est remplacé** : `333` était une borne basse gonflée par
   le bruit du pilote ; la valeur dérivée est **10 810**, avec sa ligne de calcul.
2. **La prédiction du biais est VÉRIFIÉE sur ses propres données** : en jouant 10× plus
   d'épisodes, l'étalement inter-cerveaux tombe de 0,175 à 0,055 et `s` de 0,0718 à 0,0250 —
   c'est-à-dire exactement ce que `E[s²] = σ² + v` annonçait. Le biais n'est pas une subtilité
   théorique : il a été mesuré deux fois.
3. **La reproductibilité tient à 1 600 épisodes** : A/A à δ = 0, trajectoires comprises.
4. **Le débat « plus de cerveaux » est tranché** : il n'aurait pas corrigé ce biais (il n'en
   corrige que l'instabilité), et il aurait coûté 4 cerveaux de plus à chaque run.

## 6. Ce que cette campagne LAISSE OUVERT — l'arbitrage de la tâche 8

1. 🔴 **Le coût de la tâche 9 est passé de l'ordre de l'heure à l'ordre de la SEMAINE.**
   À `n = 10 810` : **≈ 342 h ≈ 14 jours** pour 6 bras × 20 graines × 2 cartes (≈ 143 h si
   l'on ne garde que la carte 3, qui est celle du test apparié ; ≈ 7 h si l'on retenait la
   borne haute de l'IC de σ̂). **Ce n'est pas à la tâche 7 de trancher** : le protocole
   (tâche 8) doit choisir **par écrit** entre réduire le nombre de cartes, réduire le nombre
   de bras, réviser le facteur `3,0` (seul paramètre posé), ou augmenter le nombre de cerveaux
   du pilote pour resserrer σ̂. **Raboter `n` en silence est exclu.**
2. **L'alternative que la mesure désigne** : la carte 4 porte une dispersion **réelle et
   mesurable** (σ̂ = 0,0786, IC qui **ne touche pas 0**, `n` = 175) là où le poolé est noyé
   dans le bruit (73 % de `v`). Une famille de métriques réduite à la carte 4 serait
   dimensionnable ; l'arbitrage doit dire si c'est encore le banc voulu.
3. **Le nombre de cerveaux du pilote** (4, borne de la spec) est désormais le facteur
   limitant : c'est lui qui fixe `df = 3` et l'IC qui touche 0.
4. **Le pool de graines d'évaluation** (10000…10099) est trop court pour tout `n > 100` :
   à réviser en même temps que le protocole.
5. **L'artefact de `trajectoire`** (8 victoires sur 41 dont le but est absent, cf. carnet du
   premier pilote §3.5) reste entier : seule son **explication** a été corrigée.

---

**Artefacts** : `brains/EVA01_pilote_n200_13092026/` — `LISEZ_MOI.md` (protocole écrit avant
le run), `cohorte_explicite.json`, `pilote.json`, `banc_final_20260913_010845.json` (rapport
brut : 1 600 épisodes avec monde, trajectoire et budget), `pilote.log`, `replicat_AA/` (l'A/A),
`empreintes_avant.txt` / `empreintes_apres.txt`. Code :
`src/naulthene/instruments/pilote_banc.py` (`variance_echantillonnage`,
`dispersion_inter_cerveaux(v=…)`, `deriver_n` borné), `tests/test_pilote_banc.py` (29 tests).
Précédent : [`EVA01_13092026`](EVA01_13092026_la_derivation_de_n.md) (le pilote à 20 épisodes,
avec son erratum).
