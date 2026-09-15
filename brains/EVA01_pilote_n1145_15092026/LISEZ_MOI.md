# `EVA01_pilote_n1145_15092026` — la re-mesure de sauvetage (σ̂ rendue identifiable)

**Créé le 2026-09-15 à 09:46:49** (horodatage du système de fichiers, relevé par `date`),
**AVANT le premier run** (Règle de Trace). Campagne **NEUVE** : celles des pilotes antérieurs
(`brains/EVA01_pilote_13092026/`, `brains/EVA01_pilote_n200_13092026/`) restent archivées
telles quelles, jamais réécrites.

## 1. Pourquoi cette campagne existe — la dispersion n'était PAS identifiable à 200 épisodes

À 200 épisodes par carte, le pilote a publié **σ̂ = 0,012973 (poolé)** avec un **IC95 qui
touche zéro** (`[0 ; 0,090583]`) — et, par carte, la carte 3 touche aussi zéro
(`σ̂₃ = 0,022030`, IC95 `[0 ; 0,15]`). Conclusion de la tâche 7 : à **4 cerveaux**, la
dispersion inter-cerveaux n'est **pas distinguable du bruit d'échantillonnage** — `n` va de
**222 à l'infini** selon la borne lue, donc `n = 10 810` est un **point de plug-in**, pas un
dimensionnement.

La dé-convolution corrige le **biais** (`σ̂² = s² − v`), jamais l'**instabilité** : `s²` reste
estimé sur **3 degrés de liberté** (4 cerveaux). Le seul remède **accessible** (la spec borne
le pilote à 4 cerveaux) est de faire baisser `v`, donc de **jouer plus d'épisodes par
cerveau**.

```
condition d'exclusion de 0 :  σ² / v  >  χ²(0,975 ; df)/df − 1  =  2,1161   (df = 3)
                            v ∝ 1 / n_ep   ⇒   n_ep ≈ 1 145 épisodes par carte et par cerveau
```

⚠️ **Origine du budget « 1 145 »** : il se reproduit depuis le point **POOLÉ** du pilote à 200
épisodes (`σ²/v = 0,370` → ×5,72). L'exigence propre de la **carte 3** serait ≈ **1 065**
épisodes ; celle de la carte 4 est largement moindre. Le budget retenu est donc
**conservateur** (au-dessus de la carte la plus exigeante), pas un chiffre minimal.

**Condition de validité** : que le point `σ̂²` mesuré à 200 épisodes soit proche de la vérité —
sinon on ne précise qu'un intervalle autour d'un point faux. C'est précisément ce que cette
re-mesure **teste**, sans rien raboter.

## 2. La règle — inchangée, et le dimensionnement se fait PAR CARTE

```
SE_binomiale(n) = sqrt( p̄ (1 − p̄) / n )  <=  σ / 3,0        n = le plus petit entier
```

⚠️ **Le poolage est INTERDIT pour dimensionner.** Mesuré sur le pilote à 200 épisodes, la
corrélation inter-cartes des taux par cerveau vaut **ρ = −0,8807** (cov = −0,00299375) :
les cerveaux **s'échangent** les cartes (`g11` premier sur la carte 3 à 0,485 et dernier sur
la 4 à 0,040 ; `g44` l'inverse), donc le taux poolé est presque indépendant du cerveau
(0,2625 → 0,3175) et **détruit la mesurabilité**. Les deux cartes sont donc **reportées
séparément, jamais moyennées**.

La règle est `n = 9·p̄(1−p̄)/σ̂²` : la variance est au **DÉNOMINATEUR**, donc la carte qui
**contraint** est celle de plus **petit** σ̂. Le protocole gèle donc

```
n_final = max( n_carte3, n_carte4 )
```

(avec `n_carte = deriver_n(taux_poolé_carte, σ̂_carte, facteur = 3,0)`). Sur le pilote à 200
épisodes : `n_carte3 ≈ 4 529` (σ̂₃ = 0,0220), `n_carte4 ≈ 175` (σ̂₄ = 0,0786). La carte 3
**contraint**. Ces `n` sont **re-dérivés** sur les chiffres de CETTE campagne, jamais repris.

## 3. Le dispositif — identique aux pilotes antérieurs, sauf le budget d'épisodes

| Élément | Valeur | Changement |
|---|---|---|
| Cohorte | `brains/08092026_sci01_balayage_K`, bras `K8_NU` | identique |
| Cerveaux | graines d'entraînement **11, 22, 33, 44** (canoniques) | **IDENTIQUES** — c'est le budget qui change, pas l'échantillon |
| Cartes | **3** `SimpleCrossingS9N1` (budget 324), **4** `LavaGapS5` (budget 100) | identiques |
| Épisodes par carte | **1 145** | ⚠️ **200 → 1 145** (budget de MESURE, jamais le `n` du protocole) |
| Graines d'évaluation | **10000 … 11144** | ⚠️ 200 → 1 145 graines : le pool « 10000…10099 » de la spec §8 est **dépassé** (dimensionné pour l'ancien `n = 100`). Disjoint de l'entraînement (11…222) : aucun recouvrement. |
| `max_ticks` | budget natif du monde | identique |
| Voie de résolution | `cohorte_explicite.json` | **CHOIX, pas obligation** (le glob rend ces 4 graines sans lever ; le surnuméraire `K8_NU_g122` n'est pas demandé) |

## 4. Décision pré-enregistrée

| Cas | Décision |
|---|---|
| **IC95 de σ̂ de la carte 3 contient encore zéro** | **ARRÊT — on ne gèle rien.** Le chiffre (IC de σ̂) est rapporté au parent, la tâche 9 ne démarre pas sur un `n` non identifiable. |
| IC95 de σ̂ exclut zéro sur les **deux** cartes | `n_final = max(n_carte3, n_carte4)` est gelé avec sa ligne de calcul. |
| `σ̂ = 0` (`s² <= v`) sur une carte | `deriver_n` **refuse** (`n = null` + motif) — traité comme l'arrêt ci-dessus. |
| `p̄ ∈ {0, 1}` sur une carte | idem. |
| un cerveau illisible | remplacé et justifié ici, jamais estimé. |

## 5. Commande exacte

```bash
NAULTHENE_DEVICE=cpu PYTHONPATH=src venv/bin/python -m naulthene.instruments.pilote_banc \
  --cohorte brains/08092026_sci01_balayage_K --bras K8_NU --cartes 3 4 \
  --graines-pilote 11 22 33 44 --episodes 1145 --graine-eval-base 10000 \
  --cohorte-explicite brains/EVA01_pilote_n1145_15092026/cohorte_explicite.json \
  --dossier-sortie brains/EVA01_pilote_n1145_15092026
```

Fin estimée : **~11:05** — dérivée du rythme **MESURÉ** de la sonde de cadence du premier
pilote (0,63 s/épisode sur la carte 3, 0,32 sur la carte 4) :
`4 cerveaux × 1 145 × (0,63 + 0,32) ≈ 4 351 s ≈ 73 min`, plus 8 chargements de `.brain`
(0,43 s) — arrondi à **~76 min**.

## 6. Ce que cette campagne ne mesure pas

Rien du cursus (cartes imposées), rien sur la **justesse** du banc (il est dimensionné, pas
certifié), et la dispersion reste celle d'**un seul bras** (`K8_NU`). La dé-convolution
corrige le biais, pas l'instabilité : `s²` reste estimé sur **3 degrés de liberté**, et la
condition d'exclusion de zéro ne tient que si le point σ̂² de 200 épisodes était proche de la
vérité — c'est exactement l'hypothèse que cette re-mesure met à l'épreuve.
