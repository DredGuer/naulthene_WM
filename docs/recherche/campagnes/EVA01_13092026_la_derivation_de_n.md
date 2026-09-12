# EVA-01 — la dérivation de `n` par la mesure

**Date** : 2026-09-13 · **Statut** : ✅ **`n` est dérivé, et il vaut 333** ·
**4 cerveaux × 2 cartes figées × 20 épisodes = 160 épisodes**, cohorte SCI-01 bras `K8_NU`,
cohorte **EXPLICITE**, lecture seule.

> **Protocole et règle écrits AVANT le run** (`brains/EVA01_pilote_13092026/LISEZ_MOI.md`,
> dossier créé à 00:29:56, mesure lancée à 00:31:36). La règle, la cohorte, les 4 cerveaux
> et la décision à prendre en cas de mesure dégénérée y sont figés avant toute observation.
>
> **Ce carnet est la première MESURE du chantier EVA-01.** Les six tâches précédentes ont
> construit l'instrument ; celle-ci le **dimensionne**. `n` n'est pas une constante du
> protocole : c'est un **RÉSULTAT**.

---

## 1. La question posée, telle qu'elle a été formulée

> « Quelle est la dispersion inter-cerveaux du taux de franchissement sur les cartes
> figées 3 et 4 — et quel nombre d'épisodes `n` cette dispersion impose-t-elle au
> protocole du banc ? »

Règle déclarée d'avance (spec §8bis, le facteur `3,0` est **le seul paramètre posé**) :

```
SE_binomiale(n) = sqrt( p̄ (1 − p̄) / n )  <=  sd_inter / 3,0      n = le plus petit entier
```

## 2. Protocole exact

| Élément | Valeur |
|---|---|
| Cohorte | `brains/08092026_sci01_balayage_K` (SCI-01), bras **`K8_NU`**, voie **EXPLICITE** (`cohorte_explicite.json`) |
| Cerveaux | `K8_NU_g11`, `K8_NU_g22`, `K8_NU_g33`, `K8_NU_g44` — les **4 premières graines déclarées** au manifeste, choisies **avant toute mesure** |
| Cartes | **3** `MiniGrid-SimpleCrossingS9N1-v0` (budget 324), **4** `MiniGrid-LavaGapS5-v0` (budget 100) |
| Épisodes | **20 par carte** — ⚠️ **BUDGET DE MESURE DU PILOTE**, jamais le `n` du protocole |
| Graines d'évaluation | **10000 … 10019** (pool dédié, disjoint de l'entraînement 5…199) |
| `max_ticks` | budget natif du monde (aucun plafond posé) |

```bash
NAULTHENE_DEVICE=cpu PYTHONPATH=src venv/bin/python -m naulthene.instruments.pilote_banc \
  --cohorte brains/08092026_sci01_balayage_K --bras K8_NU --cartes 3 4 \
  --graines-pilote 11 22 33 44 --episodes 20 --graine-eval-base 10000 \
  --cohorte-explicite brains/EVA01_pilote_13092026/cohorte_explicite.json \
  --dossier-sortie brains/EVA01_pilote_13092026
```

Durée réelle **81 s** (00:31:36 → 00:32:57) pour une estimation de **~2 min** dérivée de la
sonde de cadence (0,63 s/épisode sur la carte 3, 0,32 sur la carte 4). Cohorte complète :
« couverture 4/4 runs », « tous les garde-fous passent », **0 épisode tronqué**.

⚠️ Le glob était **impossible** : `K8_NU` porte 2 surnuméraires (`K8_NU_g122 2.brain`,
`K8_NU_g122 3.brain`) et `lister_cerveaux` refuse alors le bras ENTIER.

## 3. Les chiffres bruts — avant toute interprétation

### 3.1 Taux de franchissement par cerveau et par carte (`gagnes/n`)

| Cerveau | Carte 3 `SimpleCrossing` | Carte 4 `LavaGap` | **Poolé (2 cartes, n = 40)** |
|---|---|---|---|
| `K8_NU_g11` | **10/20 = 0,50** | 0/20 = 0,00 | 10/40 = **0,250** |
| `K8_NU_g22` | 5/20 = 0,25 | 2/20 = 0,10 | 7/40 = **0,175** |
| `K8_NU_g33` | 6/20 = 0,30 | **8/20 = 0,40** | 14/40 = **0,350** |
| `K8_NU_g44` | 7/20 = 0,35 | 3/20 = 0,15 | 10/40 = **0,250** |
| **Poolé carte** | **28/80 = 0,350** | **13/80 = 0,163** | **41/160 = 0,256** |
| SD inter-cerveaux (ddof = 1) | **0,108012** | **0,170171** | **0,071807** |
| IC95 de cette SD (χ², df = 3) | [0,061188 ; 0,402729] | [0,096400 ; 0,634492] | **[0,040678 ; 0,267736]** |

### 3.2 La dérivation

| Grandeur | Valeur |
|---|---|
| `p̄` poolé | **0,256250** (41/160) |
| `sd_inter` (4 cerveaux, ddof = 1) | **0,071807** |
| **`ic_sd` (IC95)** | **[0,040678 ; 0,267736]** |
| Seuil de domination `sd_inter / 3` | **0,023936** |
| Ligne de calcul | `n = plus petit entier >= 332,659091 tel que sqrt(0,256250 × 0,743750 / n) <= 0,023936 ⇒ n = 333` |
| **`n` DÉRIVÉ** | **333** |

### 3.3 Sensibilité : le même `n` sous trois lectures de la dispersion

| Formulation | `p̄` | `sd_inter` | `n` |
|---|---|---|---|
| **Poolé (retenu)** | 0,256250 | 0,071807 | **333** |
| Carte 3 seule | 0,350000 | 0,108012 | 176 |
| Carte 4 seule | 0,162500 | 0,170171 | 43 |
| Borne BASSE de l'IC95 de la SD | 0,256250 | 0,040678 | **1037** |
| Borne HAUTE de l'IC95 de la SD | 0,256250 | 0,267736 | **24** |

### 3.4 Vérifications passées

| Vérification | Résultat |
|---|---|
| **A/A** — protocole rejoué à l'identique (2ᵉ run, 81 s) | **160/160 épisodes identiques** (`gagne`, `ticks`, `retour`, `trajectoire`, `monde`) ; seuls les `duree_s` (temps mural) diffèrent. `p̄`, `sd_inter`, `ic_sd`, `n` : **identiques**. δ_A/A = **0** |
| **Dérivation rejouable** — `--depuis-rapport banc_final_*.json` | `p̄`, `sd_inter`, `ic_sd`, `n_derive`, `ligne_de_calcul`, `cerveaux`, `par_carte` : **8/8 champs identiques** |
| **« Plus petit » `n`** | `sqrt(p̄(1−p̄)/333) = 0,023922 <= 0,023936` ✅ · `n = 332` → 0,023958 > 0,023936 ❌ |
| **Lecture seule** | taille **et** mtime des 4 `.brain` identiques avant/après (`empreintes_avant.txt` / `empreintes_apres.txt`) ; aucun `.brain` dans `git status` |
| **Saturation** | `p̄ = 0,256` : ni 0 ni 1, **aucune cellule saturée** ; les 4 cerveaux ont un taux poolé non nul (0,175 à 0,350) |
| **Vacuïté des victoires** | 41/41 victoires : `retour > 0` ; `longueur_normalisee` calculée (jamais `None`) |
| **Troncature** | **0 épisode tronqué sur 160** — aucune mesure coupée par le budget du banc |
| **Carte tenue** | `env_id` et `budget` identiques pour les 160 épisodes de leur cellule (re-forçage tenu) |
| **Cohorte** | 4 cerveaux canoniques, **aucun surnuméraire** dans la mesure ; `duree_s` par cerveau 19-21 s |
| **Instrument** | `_exiger_instruments` n'a rien refusé : la sonde de mixage et le détecteur de ressources répondent |

### 3.5 Un fait NOUVEAU, trouvé en vérifiant : la `trajectoire` publiée perd le but sur 8 victoires

| Contrôle sur les 41 victoires | Résultat |
|---|---|
| Position finale publiée = but | **33/41** |
| **But ABSENT de la trajectoire publiée** | **8/41 (19,5 %)** |
| dont le dernier point publié = le **départ** | 4/8 |

Le mécanisme est lisible dans `banc_final.evaluer_cerveau_sur_carte` : la position est lue
**après** `traiter_tick`, qui enchaîne LUI-MÊME sur l'épisode suivant dès que `fin_episode`
bascule. Sur l'épisode gagnant, la lecture attrape donc parfois la position de l'épisode
**suivant** (`[1, 1]`), et le pas qui atteint le but n'est jamais publié. Exemple mesuré :
`K8_NU_g22`, carte 3, graine 10018 — 33 ticks, `retour = 0,908`, `longueur_normalisee = 2,75`
(victoire authentique), trajectoire publiée
`[[2,1], …, [6,7], [1,1]]` : le but `[7,7]` n'y figure pas.

⚠️ **Cette anomalie ne touche AUCUN chiffre de ce pilote** : `p̄`, `sd_inter` et `n` viennent
du compteur `gagnes` et de `ticks`, jamais de la trajectoire ; l'A/A est identique *y
compris* sur les trajectoires (l'artefact est déterministe, ce n'est pas du bruit).
`banc_final.py` n'est pas modifié ici (hors périmètre de la tâche 7) : le fait est
**consigné** pour la tâche qui traitera l'instrument.

## 4. Les limites — écrites d'abord

1. **4 cerveaux, c'est peu, et l'intervalle le dit** : `IC95(sd_inter) = [0,041 ; 0,268]`.
   Reporté sur `n`, cet intervalle implique **de 24 à 1037 épisodes** — un facteur **43**.
   Le `333` est une estimation, pas une borne : sa propre incertitude est publiée à côté de
   lui précisément pour qu'il ne soit pas lu comme un chiffre ferme.
2. **La dispersion est mesurée sur un seul bras** (`K8_NU`). Elle décrit l'hétérogénéité
   *intra-bras* — ce qui est la grandeur pertinente pour dimensionner un test apparié par
   graine — mais elle ne dit rien de l'écart entre deux bras.
3. **Les deux cartes ne classent pas les cerveaux pareil** : `K8_NU_g11` est le meilleur sur
   la carte 3 (50 %) et le dernier sur la carte 4 (0 %) ; `K8_NU_g33` fait l'inverse
   (30 % / 40 %). Corrélation inter-cartes des taux par cerveau mesurée : **ρ = −0,54**.
   Conséquence arithmétique : la dispersion **poolée** (0,072) est plus PETITE que chacune
   des dispersions par carte (0,108 et 0,170), donc le `n` poolé (333) est le plus GRAND des
   trois. Sur ces données, le choix poolé est le plus conservateur — **ce n'est pas une
   garantie générale** : avec des cartes positivement corrélées, la dispersion poolée serait
   plus grande et le `n` plus petit. À 4 cerveaux, ce ρ n'a évidemment aucune valeur
   statistique : il explique une arithmétique, il n'établit rien.
4. **L'IC de la SD suppose la normalité** des taux par cerveau — approximation assumée à 4
   valeurs, pas un résultat.
5. **Un état de cerveau est incohérent dans le fichier** : pour `K8_NU_g11`, l'`env_id`
   enregistré (`Empty-5x5`) diverge de son `niveau_actuel` enregistré (4), et `persistance`
   remappe le niveau **4 → 0** au chargement. Le banc **force** la carte et ne lit
   `niveau_actuel` que pour la télémétrie et le tirage du cursus, jamais dans la décision
   intra-épisode : la mesure n'est pas confondue, et le cerveau concerné est justement
   celui qui réussit le mieux la carte 3 — un cerveau « cassé » n'aurait pas fait 50 %.
   Reste que **l'archive SCI-01 contient un état incohérent**, ce qui est un fait à part
   entière (audit d'intégrité de `brains/`, hors périmètre d'EVA-01).
6. **Le facteur 3,0 n'est pas mesuré** : il est posé (spec §8bis). C'est le seul paramètre
   de la règle qui ne vient pas des données.
7. **Rien ici ne dit du cursus** : cartes imposées, règle « un banc forcé ne prouve rien sur
   le cursus ». Et rien ne dit que le banc **juge juste** — il est dimensionné, pas certifié
   (le test d'acceptation D3 reste à faire).

## 5. Ce que ce pilote FERME

1. **La constante `n` est morte.** Le `100` posé, le « 20 de confort », tous les `n` devinés :
   la valeur du protocole est **dérivée d'une mesure**, avec sa ligne de calcul visible
   (`√(0,256250 × 0,743750 / 333) = 0,023922 <= 0,023936`).
2. **L'objection « dimensionner avec la variance de SCI-01 »** est définitivement tranchée :
   la variance pertinente n'existait pas avant le banc, elle est maintenant mesurée
   (0,0718 poolé, 0,108 et 0,170 par carte) — c'est exactement la circularité que la tâche 7
   devait rompre.
3. **La reproductibilité du banc est confirmée sur une mesure réelle** : A/A à 160/160
   épisodes identiques, δ = 0 — le δ_A/A que la règle de mesure exige à côté de tout résultat.
4. **La carte n'est pas un mur infranchissable** : 41 victoires sur 160 épisodes, aucun
   épisode tronqué. L'instrument a de quoi mesurer (aucune saturation à 0).
5. **La voie `--cohorte-explicite` est validée en conditions réelles** : elle était
   *obligatoire* (le glob refusait le bras) et elle a fonctionné de bout en bout.

## 6. Ce que ce pilote LAISSE OUVERT

1. **La faisabilité de la campagne de la tâche 9**. À `n = 333`, chaque (bras, graine) coûte
   `333 × 0,63 + 333 × 0,32 ≈ 316 s` : **≈ 10,5 h** pour 6 bras × 20 graines × 2 cartes
   (**≈ 7,0 h** si l'on ne garde que la carte 3, qui est celle du test apparié). C'est un
   facteur **3,3** au-dessus de l'ancien `n = 100` abandonné. Si ce budget est trop lourd, la
   décision ne peut PAS être de raboter `n` en silence : elle doit être rédigée (facteur
   autre que 3, ou famille de métriques réduite, ou moins de bras).
2. **Le choix « poolé » plutôt que « par carte »** — la spec dit « cartes figées » au pluriel
   sans trancher. Ici les trois lectures donnent 333 / 176 / 43 ; le protocole devra écrire
   **laquelle il retient** (le présent carnet retient le poolé, le plus conservateur).
3. **L'IC de la SD à 4 cerveaux** est trop large pour fixer `n` à mieux qu'un facteur 43.
   Le seul moyen de resserrer serait d'**augmenter le nombre de cerveaux du pilote** (8 ou 12
   au lieu de 4) — la spec borne à 4, donc c'est une décision à prendre.
4. **L'artefact de `trajectoire`** (§3.5, 8 victoires sur 41) : l'artefact qui doit rendre le
   comportement auditable est muet sur le pas décisif. À corriger dans une tâche
   d'instrument, avec son propre test.
5. **L'état incohérent de `K8_NU_g11`** (limite 5) : à verser à l'audit d'intégrité de
   `brains/`, ouvert au registre.
6. **Rien sur la justesse du banc** : le pilote dimensionne, il ne certifie pas. Tant que le
   test d'acceptation D3 n'a pas reproduit l'ordre SCI-01, **aucune supériorité n'est
   revendiquée**.

---

**Artefacts** : `brains/EVA01_pilote_13092026/` — `LISEZ_MOI.md` (protocole écrit avant le
run), `cohorte_explicite.json`, `pilote.json`, `banc_final_20260913_003257.json` (rapport
brut : 160 épisodes avec monde, trajectoire et budget), `pilote.log`, `sonde_cadence.txt`,
`empreintes_avant.txt` / `empreintes_apres.txt`, `replicat_AA/` (l'A/A), `reproduction/`
(la dérivation rejouée depuis le rapport). Code : `src/naulthene/instruments/pilote_banc.py`,
`tests/test_pilote_banc.py` (16 tests).
