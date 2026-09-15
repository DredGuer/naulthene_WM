# EVA-01 — la dérivation de `n` par la mesure

**Date** : 2026-09-13 · **Statut** : ✅ mesure réelle, non dégénérée ·
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

## 0. 🔴 ERRATUM DU 13/09/2026 (tour de correction 1) — `333` est une BORNE BASSE

**Ce carnet n'est pas réécrit** : ses chiffres sont ceux du 20-épisodes, tels qu'ils ont été
mesurés. Mais **la valeur de `n` qu'il publiait était biaisée**, et l'ancien chiffre doit
rester lisible à côté du nouveau (Règle de Trace : une rétractation montre l'ancien chiffre
en regard).

| Grandeur | Publié le 13/09 (20 épisodes) — **inchangé, archivé** | Après dé-convolution du MÊME run | Après re-mesure à 200 épisodes |
|---|---|---|---|
| dispersion | `s = 0,071807` (observée, gonflée) | σ̂ = **0,024725** (v par carte) · **0,019790** (v « un seul binôme ») | `s = 0,024958`, **σ̂ = 0,012973** |
| `n` | **333** (borne basse) | **2806** · **4380** | **10 810** (borne basse : 2921) |

⚠️ **Les deux σ̂ de la colonne 3 diffèrent par la convention retenue pour `v`** : par carte
(`Σ_c n_c·p_c(1−p_c)/N²`, la seule exacte quand les deux cartes n'ont pas le même taux) ou
« un seul binôme pour les 40 épisodes » (`p̄(1−p̄)/N`, qui **majore** `v`). Le code publie la
première ; la seconde est reportée parce que la revue l'avait employée. ⚠️ **L'écart NE se
referme PAS en jouant plus d'épisodes** : à 200 épisodes il vaut encore un facteur **1,43**
sur `n` (10 810 contre 15 478) — parce que σ̂² = `s² − v` est une **différence de deux
quantités comparables**, donc mal conditionnée à 4 cerveaux. C'est écrit dans les limites du
carnet de re-mesure.

**La re-mesure confirme le diagnostic et déplace `n` de 333 à 10 810** — voir
[`EVA01_N200_13092026`](EVA01_N200_13092026_la_dispersion_deconvoluee.md) : mêmes cerveaux,
mêmes graines, 200 épisodes par carte (1 600 épisodes). L'étalement des taux poolés tombe de
0,175 (20 épisodes) à **0,055** (200 épisodes) : le premier `s` était majoritairement du
tirage, exactement ce que `E[s²] = σ² + v` annonce.

**Pourquoi.** Le taux d'un cerveau est une MOYENNE de 20 épisodes, donc bruité. La
dispersion observée entre cerveaux contient ce bruit en plus de la dispersion réelle :

```
E[s²] = σ² + v      σ = dispersion RÉELLE entre cerveaux
                    v = variance d'ÉCHANTILLONNAGE du taux de chaque cerveau
```

Mesuré ici : `s² = 0,00515625`, dont **88,1 %** (`v = 0,00454492`) est de la variance
d'échantillonnage. Le bruit de mesure ne dominait donc **pas** la dispersion réelle,
contrairement à l'intention écrite du §8bis (« bruit < ~10 % de la variance ») : à `n = 333`,
`SE = 0,023923` vaut **1,21 × σ̂**. Le `333` publié était donc une **borne basse**.

⚠️ **Ce biais ne se corrige PAS en ajoutant des cerveaux** (`E[s²] = σ² + v` quel que soit
leur nombre) : il se corrige en jouant plus **d'épisodes par cerveau**. D'où la campagne
[`EVA01_pilote_n200_13092026`](../../../brains/EVA01_pilote_n200_13092026/LISEZ_MOI.md),
mêmes cerveaux, mêmes graines, **200 épisodes par carte** (`v` divisé par 10).

⚠️ **Conséquence de coût, à trancher en tâche 8 et pas ici** : σ̂ implique un `n` de l'ordre
de **2 800 à 4 400** épisodes sur ce run, et la re-mesure à 200 épisodes le porte à
**10 810** — soit ≈ **342 h ≈ 14 jours** pour la campagne de tâche 9 (6 bras × 20 graines ×
2 cartes), un passage de l'ordre de l'heure à l'ordre de la **semaine**. Raboter `n` n'est pas
une option ; réduire le nombre de cartes ou de bras, réviser le facteur `3,0`, ou augmenter
le nombre de cerveaux du pilote sont des décisions à écrire.

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

⚠️ **CORRECTION MESURÉE (tour de correction 1) — la voie explicite n'était PAS obligatoire
ici.** Ce carnet écrivait que le glob rendait la mesure « impossible » : c'est **faux pour
ces quatre graines**. Mesuré : `lister_cerveaux('K8_NU', [11, 22, 33, 44])` rend les 4
cerveaux **sans lever**, et `resoudre_cohorte` non plus — le surnuméraire est
`K8_NU_g122`, une graine **non demandée**. Le glob ne refuse `K8_NU` que si l'on demande les
**20 graines du manifeste** (`NomAmbigue`, mesuré). La voie explicite a donc été un
**CHOIX** — énumérer les cerveaux un par un, avec un chemin vérifié existant pour chacun —
et non une nécessité. Aucun chiffre de ce carnet n'en dépend.

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

> ⚠️ **Nomenclature révisée le 15/09/2026 (tâche 8, tour de correction 1, commit `1c3ca60`)** — la
> mesure ci-dessus est datée et **n'est pas réécrite**, mais la clé qu'elle nomme a changé de nom : la
> clé racine `n_derive` **n'existe plus**. Ce qu'elle contenait (le `n` dérivé de la dispersion
> **poolée**) s'appelle désormais `n_derive_poole`, et le `n` **gelé** publié à la racine est
> `n_final` (le **maximum des `n` par carte**, sous `par_carte[*].n_derive`). Un lecteur qui
> `grep n_derive` sur `pilote.json` trouverait donc la grandeur **interdite pour dimensionner** :
> lire `n_final`.
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
| dont le dernier point publié = la case **d'avant le but** | 4/8 |

⚠️ **MÉCANISME CORRIGÉ (tour de correction 1).** Ce carnet écrivait d'abord que la position
est lue « après que `traiter_tick` a réenchaîné l'épisode suivant », et `banc_final.py`
écrivait que `traiter_tick` « peut avoir **remplacé** `etat.env` par une carte du CURSUS ».
**Les deux diagnostics étaient faux, et un correctif parti de là n'aurait rien corrigé.**

Mesuré en rejouant une cellule ENTIÈRE (`K8_NU_g22`, carte 3, graines 10000-10019), mon
propre replay reproduisant **20/20 trajectoires publiées à l'identique** :

- **19 fois sur 20**, au tick de bascule, `etat.env` est un **NOUVEL objet** — et c'est
  alors `environnement_episode` (l'ancien objet, resté sur le but) qui porte la **bonne**
  position. Le « remplacement » décrit donc le cas où le rapport est **juste** ;
- **1 fois sur 20** (graine 10018), `etat.env` n'est **pas** remplacé : le **MÊME objet** est
  remis à zéro **en place** (`id(env)` constant sur toute la cellule, `agent_pos` passant de
  `(6,7)` à `(1,1)`, `fin_episode=True`). La lecture d'après-bascule rend alors le **départ
  de l'épisode suivant**, jamais le but.

D'où les deux formes publiées : quand le départ `[1,1]` n'avait pas encore été vu, il est
ajouté **en dernier** (4 cas) ; quand il l'avait déjà été, il est **dédupliqué** et le
dernier point publié reste la **case d'avant le but** (4 cas). Exemple du premier type :
`K8_NU_g22`, carte 3, graine 10018 — 33 ticks, `retour = 0,908`,
`longueur_normalisee = 2,75` (victoire authentique), trajectoire publiée
`[[2,1], …, [6,7], [1,1]]` : le but `[7,7]` n'y figure pas.

⚠️ **Cette anomalie ne touche AUCUN chiffre de ce pilote** : `p̄`, `sd_inter` et `n` viennent
du compteur `gagnes` et de `ticks`, jamais de la trajectoire ; l'A/A est identique *y
compris* sur les trajectoires (l'artefact est déterministe, ce n'est pas du bruit).
Le **commentaire** de `banc_final.py` a été corrigé (tour de correction 1 — seule exception
au gel de ce fichier, vérifiée par comparaison d'AST : **aucune ligne exécutable ne
change**) ; le **comportement**, lui, n'est pas corrigé : c'est une tâche d'instrument, avec
son propre test.

## 4. Les limites — écrites d'abord

1. 🔴 **`sd_inter` EST GONFLÉ PAR LE BRUIT DU PILOTE, ET `333` EST UNE BORNE BASSE**
   (ajouté au tour de correction 1). La dispersion observée `s = 0,071807` mélange la
   dispersion réelle entre cerveaux et la variance d'échantillonnage du pilote :
   `E[s²] = σ² + v`, avec ici `s² = 0,00515625` et `v = 0,00454492` — **88,1 % de bruit**.
   Dé-convoluée : **σ̂ = 0,024725** (convention de `v` par carte, la seule exacte ici) ou
   σ̂ = 0,019790 (convention « un seul binôme sur 40 épisodes », qui majore `v`), soit
   **`n` = 2806 à 4380** — jamais 333. À `n = 333`, `SE = 0,023923` vaut **1,21 × σ̂** : le
   bruit de mesure **ne dominait pas** la dispersion réelle, contrairement à l'intention du
   §8bis. Voir l'erratum (§0) et la re-mesure à 200 épisodes par cerveau.
2. **4 cerveaux, c'est peu, et l'intervalle le dit** : `IC95(sd_inter) = [0,041 ; 0,268]`.
   Reporté sur `n`, cet intervalle implique **de 24 à 1037 épisodes** — un facteur **43**.
   Le `333` est une estimation, pas une borne : sa propre incertitude est publiée à côté de
   lui précisément pour qu'il ne soit pas lu comme un chiffre ferme.
3. **La dispersion est mesurée sur un seul bras** (`K8_NU`). Elle décrit l'hétérogénéité
   *intra-bras* — ce qui est la grandeur pertinente pour dimensionner un test apparié par
   graine — mais elle ne dit rien de l'écart entre deux bras.
4. **Les deux cartes ne classent pas les cerveaux pareil** : `K8_NU_g11` est le meilleur sur
   la carte 3 (50 %) et le dernier sur la carte 4 (0 %) ; `K8_NU_g33` fait l'inverse
   (30 % / 40 %). Corrélation inter-cartes des taux par cerveau mesurée : **ρ = −0,54**.
   Conséquence arithmétique : la dispersion **poolée** (0,072) est plus PETITE que chacune
   des dispersions par carte (0,108 et 0,170), donc le `n` poolé (333) est le plus GRAND des
   trois. Sur ces données, le choix poolé est le plus conservateur — **ce n'est pas une
   garantie générale** : avec des cartes positivement corrélées, la dispersion poolée serait
   plus grande et le `n` plus petit. À 4 cerveaux, ce ρ n'a évidemment aucune valeur
   statistique : il explique une arithmétique, il n'établit rien.
5. **L'IC de la SD suppose la normalité** des taux par cerveau — approximation assumée à 4
   valeurs, pas un résultat. La dé-convolution hérite de la même hypothèse.
6. **Un état de cerveau est incohérent dans le fichier** : pour `K8_NU_g11`, l'`env_id`
   enregistré (`Empty-5x5`) diverge de son `niveau_actuel` enregistré (4), et `persistance`
   remappe le niveau **4 → 0** au chargement. Le banc **force** la carte et ne lit
   `niveau_actuel` que pour la télémétrie et le tirage du cursus, jamais dans la décision
   intra-épisode : la mesure n'est pas confondue, et le cerveau concerné est justement
   celui qui réussit le mieux la carte 3 — un cerveau « cassé » n'aurait pas fait 50 %.
   Reste que **l'archive SCI-01 contient un état incohérent**, ce qui est un fait à part
   entière (audit d'intégrité de `brains/`, hors périmètre d'EVA-01).
7. **Le facteur 3,0 n'est pas mesuré** : il est posé (spec §8bis). C'est le seul paramètre
   de la règle qui ne vient pas des données.
8. **Rien ici ne dit du cursus** : cartes imposées, règle « un banc forcé ne prouve rien sur
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
5. **La voie `--cohorte-explicite` fonctionne de bout en bout** — mais ⚠️ **elle n'était pas
   obligatoire** (voir la correction du §2 : le glob rend ces 4 graines sans lever ; il ne
   refuse `K8_NU` que pour les 20 graines du manifeste). Ce qui est fermé, c'est que la voie
   explicite **marche** ; ce qui est corrigé, c'est qu'elle fût *nécessaire*.

## 6. Ce que ce pilote LAISSE OUVERT

1. 🔴 **La faisabilité de la tâche 9 change d'ordre de grandeur.** À `n = 333` (borne basse),
   chaque (bras, graine) coûte `333 × 0,63 + 333 × 0,32 ≈ 316 s`, soit **≈ 10,5 h** pour
   6 bras × 20 graines × 2 cartes. Mais `333` est un plancher : avec σ̂ ≈ 0,020-0,025, le
   même calcul donne **des jours** (≈ 88 h à `n = 2806`, ≈ 137 h à `n = 4380`). Ce n'est
   **pas à la tâche 7 de trancher** : c'est un arbitrage de la tâche 8 — réduire les cartes
   ou les bras, ou contester le facteur `3,0` **par écrit** — **jamais** raboter `n` en
   silence.
2. **Le choix « poolé » plutôt que « par carte »** — la spec dit « cartes figées » au pluriel
   sans trancher. Ici les trois lectures donnent 333 / 176 / 43 ; le protocole devra écrire
   **laquelle il retient** (le présent carnet retient le poolé, le plus conservateur).
3. **La convention de `v`** (par carte, ou « un seul binôme pour N épisodes ») déplace σ̂ de
   0,0198 à 0,0247 sur ces données, donc `n` de 4380 à 2806 : à 20 épisodes par cerveau, le
   choix n'est pas neutre. À 200 épisodes, il le devient (voir la campagne de re-mesure).
4. **L'IC de la SD à 4 cerveaux** est trop large pour fixer `n` à mieux qu'un facteur 43.
   Le seul moyen de resserrer l'**instabilité** — la dé-convolution, elle, ne corrige que le
   **biais** — serait d'**augmenter le nombre de cerveaux du pilote** (8 ou 12 au lieu de
   4) ; la spec borne à 4, donc c'est une décision à prendre.
5. **L'artefact de `trajectoire`** (§3.5, 8 victoires sur 41) : l'artefact qui doit rendre le
   comportement auditable est muet sur le pas décisif — et son mécanisme est désormais
   correctement diagnostiqué (reset EN PLACE du même objet, pas remplacement). À corriger
   dans une tâche d'instrument, avec son propre test.
6. **L'état incohérent de `K8_NU_g11`** (limite 6) : à verser à l'audit d'intégrité de
   `brains/`, ouvert au registre.
7. **Rien sur la justesse du banc** : le pilote dimensionne, il ne certifie pas. Tant que le
   test d'acceptation D3 n'a pas reproduit l'ordre SCI-01, **aucune supériorité n'est
   revendiquée**.

---

**Artefacts** : `brains/EVA01_pilote_13092026/` — `LISEZ_MOI.md` (protocole écrit avant le
run), `cohorte_explicite.json`, `pilote.json`, `banc_final_20260913_003257.json` (rapport
brut : 160 épisodes avec monde, trajectoire et budget), `pilote.log`, `sonde_cadence.txt`,
`empreintes_avant.txt` / `empreintes_apres.txt`, `replicat_AA/` (l'A/A), `reproduction/`
(la dérivation rejouée depuis le rapport). **Suite de la mesure** :
[`EVA01_N200_13092026`](EVA01_N200_13092026_la_dispersion_deconvoluee.md) et
`brains/EVA01_pilote_n200_13092026/`. Code : `src/naulthene/instruments/pilote_banc.py`,
`tests/test_pilote_banc.py` (29 tests au tour de correction 1).
