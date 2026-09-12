# `EVA01_pilote_n200_13092026` — le pilote re-mesuré à 200 épisodes par cerveau

**Créé le 2026-09-13 à 00:55:36** (horodatage du système de fichiers, relevé par `stat`),
**AVANT le premier run** (Règle de Trace). Campagne **NEUVE** : celle du premier pilote
(`brains/EVA01_pilote_13092026/`) reste archivée telle quelle, jamais réécrite.

## 1. Pourquoi cette campagne existe — ce que le tour 1 a corrigé

Le premier pilote a publié `sd_inter = 0,071807` et `n = 333`. Une revue indépendante a
montré, et le calcul ci-dessous le confirme, que **cette dispersion est gonflée par le
pilote lui-même** :

```
E[s²] = σ² + v        σ = dispersion RÉELLE entre cerveaux
                      v = variance d'ÉCHANTILLONNAGE du taux de chaque cerveau
```

Mesuré sur le premier pilote : `s² = 0,00515625`, dont **88,1 %** est de la variance
d'échantillonnage (`v = 0,00454492`). Le bruit de mesure ne dominait donc **pas** la
dispersion réelle — contrairement à l'intention écrite du §8bis (« bruit < ~10 % de la
variance »). Conséquence : **`333` est une BORNE BASSE, pas une estimation.**

⚠️ **Ce biais ne se corrige PAS en ajoutant des cerveaux.** `E[s²] = σ² + v` quel que soit
leur nombre : c'est `v` qu'il faut faire baisser, et `v ≈ p(1−p)/n` ne dépend que du
nombre d'ÉPISODES PAR CERVEAU. D'où cette campagne : **mêmes cerveaux, mêmes graines,
budget d'épisodes porté de 20 à 200** (`v` divisé par 10).

## 2. La règle — inchangée, mais appliquée au bon estimateur

```
SE_binomiale(n) = sqrt( p̄ (1 − p̄) / n )  <=  σ / 3,0        n = le plus petit entier
```

Le §8bis nomme « l'écart-type **inter-cerveaux** de ce même taux » : c'est **σ**. Or `s`
observé en est un estimateur **biaisé vers le haut**. L'estimateur correct est
`σ̂ = sqrt(max(0, s² − v))`, avec

```
v = Σ_cartes (n_c · p_c · (1 − p_c)) / N²          N = Σ_cartes n_c
```

⚠️ `v` se calcule sur les taux **par carte** : les deux cartes n'ont pas le même taux
(0,35 contre 0,16 au premier pilote), et les traiter comme un seul binôme de 400 épisodes
serait faux (`p̄(1−p̄)/N` majore `v` — donc minore σ̂, donc minore `n`).

**Ce n'est PAS changer la règle** : c'est mesurer la grandeur que la règle nomme, au lieu
de son estimateur biaisé. Le facteur `3,0` reste le seul paramètre posé.

## 3. Le dispositif — identique au premier pilote, sauf le budget d'épisodes

| Élément | Valeur | Changement |
|---|---|---|
| Cohorte | `brains/08092026_sci01_balayage_K`, bras `K8_NU` | identique |
| Cerveaux | graines d'entraînement **11, 22, 33, 44** (canoniques) | **IDENTIQUES** — c'est le budget qui change, pas l'échantillon |
| Cartes | **3** `SimpleCrossingS9N1` (budget 324), **4** `LavaGapS5` (budget 100) | identiques |
| Épisodes par carte | **200** | ⚠️ **20 → 200** (budget de MESURE, jamais le `n` du protocole) |
| Graines d'évaluation | **10000 … 10199** | ⚠️ 20 → 200 graines : le pool « 10000…10099 » de la spec §8 est **dépassé** (il avait été dimensionné pour l'ancien `n = 100`). Disjoint de l'entraînement (5…199) : aucun recouvrement. |
| `max_ticks` | budget natif du monde | identique |
| Voie de résolution | `cohorte_explicite.json` | **CHOIX, pas obligation** : `lister_cerveaux('K8_NU', [11,22,33,44])` rend les 4 sans lever (mesuré — le surnuméraire `K8_NU_g122` n'est pas demandé). Le glob ne refuse le bras que pour les **20 graines du manifeste**. |

## 4. Décision pré-enregistrée

| Cas | Décision |
|---|---|
| `σ̂ = 0` (`s² <= v`) | `deriver_n` **refuse** : `n_derive = null` + motif. Une dispersion indiscernable du bruit n'autorise aucun `n` fini. |
| `p̄ ∈ {0, 1}` | idem. |
| un cerveau illisible | remplacé et justifié ici, jamais estimé. |

**Ce qui est publié dans les deux cas** : `s` ET σ̂, leurs deux IC, `v` et la part de
variance qu'il représente, les deux `n` (`n_derive` de σ̂, `n_derive_sd_observee` de `s`).

## 5. Commande exacte

```bash
NAULTHENE_DEVICE=cpu PYTHONPATH=src venv/bin/python -m naulthene.instruments.pilote_banc \
  --cohorte brains/08092026_sci01_balayage_K --bras K8_NU --cartes 3 4 \
  --graines-pilote 11 22 33 44 --episodes 200 --graine-eval-base 10000 \
  --cohorte-explicite brains/EVA01_pilote_n200_13092026/cohorte_explicite.json \
  --dossier-sortie brains/EVA01_pilote_n200_13092026
```

Fin estimée : **~01:09** — dérivée du rythme MESURÉ de la sonde de cadence du premier
pilote (0,63 s/épisode sur la carte 3, 0,32 sur la carte 4) : `4 × 200 × (0,63 + 0,32)` ≈
**760 s ≈ 13 min**, plus 8 chargements de `.brain` (0,43 s).

## 6. Ce que cette campagne ne mesure pas

Identique au premier pilote : rien du cursus (cartes imposées), rien sur la **justesse** du
banc (il est dimensionné, pas certifié), et la dispersion reste celle d'**un seul bras**.
⚠️ S'y ajoute une limite propre à la dé-convolution : elle corrige le **biais**, pas
l'**instabilité** — `s²` reste estimé sur 3 degrés de liberté (4 cerveaux), et l'IC de σ̂
le dit.

## 7. Résultat (mesuré le 2026-09-13, 00:55:59 → 01:08:45, 766 s)

Détail, vérifications et limites :
[`docs/recherche/campagnes/EVA01_N200_13092026_la_dispersion_deconvoluee.md`](../../docs/recherche/campagnes/EVA01_N200_13092026_la_dispersion_deconvoluee.md).

| Grandeur | Valeur |
|---|---|
| `p_barre` (poolé, 2 cartes, 4 cerveaux) | **0,281250** (450/1 600) |
| `sd_inter` **observée** (gonflée par le pilote) | 0,024958 — dont **73,0 %** de bruit |
| **`sd_inter_deconvoluee` σ̂** | **0,012973** (IC95 **[0 ; 0,090583]**, touche 0) |
| **`n_derive` (de σ̂)** | **10 810** |
| `n_derive_sd_observee` (borne basse) | 2 921 |

⚠️ **Le `n` a changé d'ordre de grandeur** : 333 → **10 810**, soit ≈ **342 h ≈ 14 jours**
pour la campagne de la tâche 9 (6 bras × 20 graines × 2 cartes). Ce n'est pas à cette
campagne de trancher : c'est l'arbitrage de la tâche 8 (moins de cartes ou de bras, facteur
`3,0` révisé par écrit, ou plus de cerveaux au pilote pour resserrer σ̂) — **jamais** raboter
`n` en silence. A/A rejoué : **1 600/1 600 épisodes identiques**, δ = 0.
