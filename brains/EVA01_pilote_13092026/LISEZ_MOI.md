# `EVA01_pilote_13092026` — le pilote qui DÉRIVE `n`

**Créé le 2026-09-13 à 00:29:56** (horodatage du système de fichiers du dossier, relevé par
`stat` ; `LISEZ_MOI.md` écrit à 00:30:41), **AVANT le premier run** (Règle de Trace : une
campagne s'archive avant de tourner). Ce dossier porte le **protocole**, puis les agrégats
machine.

## 1. La question posée, telle qu'elle a été formulée

> « Quelle est la dispersion inter-cerveaux du taux de franchissement sur les cartes
> figées 3 et 4 — et quel nombre d'épisodes `n` cette dispersion impose-t-elle au
> protocole du banc ? »

C'est la question de la spec §8bis : `n` **n'est pas une constante du protocole**, c'est un
**RÉSULTAT**. Le présent pilote est la première **mesure** du chantier EVA-01 ; les six
tâches précédentes ont construit l'instrument.

## 2. La règle (déclarée d'avance, spec §8bis)

```
p̄  = taux de franchissement POOLÉ du pilote (Σ gagnés / Σ épisodes, tous cerveaux,
     sur les deux cartes figées)
SE_binomiale(n) = sqrt( p̄ (1 − p̄) / n )              ← le bruit de mesure d'UN cerveau
contrainte      : SE_binomiale(n) <= sd_inter / 3,0   ← domination du bruit
n retenu        = le PLUS PETIT entier >= 1 qui la satisfait
```

`sd_inter` est l'écart-type **inter-cerveaux** (ddof = 1) des taux **par cerveau** — jamais
la dispersion des épisodes d'un même cerveau, qui mesure autre chose.

**Le seul paramètre posé est le facteur `3,0`.** Il est isolé (`FACTEUR_DOMINATION`) pour
pouvoir être contesté ; tout le reste est mesuré ici.

**L'intervalle de confiance de la SD estimée est publié** (`ic_sd`, loi du chi-deux sur la
variance, df = nombre de cerveaux − 1). Un pilote à 4 cerveaux donne une SD très mal
connue : publier sa seule valeur ponctuelle ferait passer une dispersion instable pour un
chiffre ferme.

## 3. Décision pré-enregistrée en cas de mesure dégénérée

Écrite **avant** toute mesure, pour qu'aucun `n` ne soit inventé après coup :

| Cas mesuré | Décision |
|---|---|
| `p̄ = 0` ou `p̄ = 1` (carte saturée) | `deriver_n` **refuse** (ValueError) : `n_derive = null` dans `pilote.json`, avec son motif. Aucun `n` de secours n'est calculé. |
| `sd_inter = 0` (cerveaux indiscernables) | idem : `n_derive = null`. Une dispersion nulle est un RÉSULTAT, pas une erreur à contourner. |
| un cerveau déclaré illisible | il est **remplacé**, et le remplacement est écrit et justifié ici — jamais comblé par une estimation. |

Un `n` dérivé d'une dispersion nulle serait un chiffre inventé : la contrainte
`0 <= 0` est vraie pour tout `n`, donc « le plus petit » vaudrait `1`, et rien dans la
mesure ne le soutiendrait.

## 4. Le dispositif (protocolé AVANT la mesure)

| Élément | Valeur | Pourquoi |
|---|---|---|
| Cohorte | `brains/08092026_sci01_balayage_K` | la campagne SCI-01, 6 bras × 20 graines |
| Bras | **`K8_NU`** seul | nommé par la spec du pilote |
| Cerveaux | **4** : graines d'entraînement **11, 22, 33, 44** | maximum de la fourchette « 2 à 4 » de la spec : c'est ce qui donne la meilleure estimation de dispersion à coût constant. Ce sont les **quatre premières graines déclarées** au manifeste de SCI-01, prises dans cet ordre et **avant toute mesure** — aucun cerveau n'est choisi sur son résultat. |
| Cartes | **3** (`SimpleCrossingS9N1`) et **4** (`LavaGapS5`) | les deux cartes gelées du protocole (§8) |
| Graines d'évaluation | **10000 … 10019** | pool dédié, disjoint de l'entraînement (5…199) |
| Épisodes par carte | **20** | ⚠️ **BUDGET DE MESURE DU PILOTE**, pas le `n` du protocole. Il doit être assez grand pour estimer la dispersion, assez petit pour que le pilote tienne en quelques minutes. Seul le `n` DÉRIVÉ entre au protocole (tâche 8). |
| `max_ticks` | budget natif du monde | jamais un plafond posé à la main |
| Métrique de la règle | `gagnes` (taux de franchissement) | la métrique PRIMAIRE de la famille gelée |

### Voie de résolution : EXPLICITE, et non par glob

`K8_NU` porte **2 surnuméraires** (`K8_NU_g122 2.brain`, `K8_NU_g122 3.brain`) : le glob
`lister_cerveaux` refuse alors **le bras entier** (`NomAmbigue`). La cohorte est donc
énumérée **un par un** dans `cohorte_explicite.json` (`{bras: {graine: chemin}}`), chaque
chemin canonique étant vérifié existant.

### Pré-vol (avant la mesure, jamais une estimation)

- les 4 `.brain` ont été **chargés** un par un : les quatre s'ouvrent (résurrection, aucun
  fichier iCloud non matérialisé, 0,0 à 0,6 s chacun) ;
- ⚠️ **fait mesuré au chargement, à publier** : pour `K8_NU_g11`, le `env_id` enregistré
  (`MiniGrid-Empty-5x5-v0`) diverge de son `niveau_actuel` enregistré (4), et
  `persistance` remappe donc son niveau **4 → 0** au chargement. Le banc **force** la carte
  de travail (`_forcer_carte`) et ne lit `niveau_actuel` que pour la télémétrie et le
  tirage du cursus, jamais dans la décision intra-épisode : la mesure n'est donc pas
  confondue. Le fait est publié parce qu'il décrit l'état RÉEL du cerveau comparé ;
- lecture seule : les `.brain` ne sont ni copiés ni modifiés
  (`empreintes_avant.txt` porte taille + mtime avant le run, à comparer après).

### Sonde de cadence (exécutée AVANT la mesure officielle, chiffres publiés)

Le rythme du banc n'était pas connu (aucun run de `banc_final` n'avait chronométré plus de
3 épisodes à ce jour). Une sonde a donc mesuré le **coût** d'un cerveau — `K8_NU_g11` — aux
graines d'évaluation **1000-1001** (pool dédié, disjoint des 10000+ de la mesure officielle) :

| Carte | Budget | 2 épisodes | s/épisode | ms/tick | gagnés (sonde) |
|---|---|---|---|---|---|
| 3 — `SimpleCrossingS9N1` | 324 | 1,27 s | 0,63 | 1,96 | **2 / 2** |
| 4 — `LavaGapS5` | 100 | 0,64 s | 0,32 | 3,21 | 0 / 2 |

Chargement d'un `.brain` : 0,43 s. D'où l'estimation de la mesure officielle :
4 cerveaux × (20 × 0,63 + 20 × 0,32) s + 8 chargements ≈ **80 s de calcul**.

⚠️ **Cette sonde n'entre dans AUCUN calcul de `n`** : elle sert à estimer une durée (règle du
journal des runs), et ses chiffres sont écrits ici pour qu'aucun nombre produit pendant la
campagne ne reste hors trace — y compris ceux qui ne comptent pas. Qu'elle ne soit pas
saturée à 0 est une information de **faisabilité**, jamais un résultat : la mesure
officielle porte sur d'autres graines, sur 20 épisodes, et sur 4 cerveaux.

## 5. La commande exacte

```bash
NAULTHENE_DEVICE=cpu PYTHONPATH=src venv/bin/python -m naulthene.instruments.pilote_banc \
  --cohorte brains/08092026_sci01_balayage_K --bras K8_NU --cartes 3 4 \
  --graines-pilote 11 22 33 44 --episodes 20 --graine-eval-base 10000 \
  --cohorte-explicite brains/EVA01_pilote_13092026/cohorte_explicite.json \
  --dossier-sortie brains/EVA01_pilote_13092026 2>&1 | tee brains/EVA01_pilote_13092026/pilote.log
```

`pilote_banc` appelle `banc_final.executer_banc` (donc `evaluer_cerveau_sur_carte`) : la
reproductibilité, l'état frais par (bras, carte) et le re-forçage de carte par épisode
sont ceux de l'instrument déjà vérifié — aucune mécanique du banc n'est réimplémentée.

### Sorties attendues

| Fichier | Contenu |
|---|---|
| `banc_final_<horodatage>.json` | le rapport BRUT du banc : taux par cerveau et par carte, épisodes (monde, trajectoire, budget) |
| `pilote.json` | `p_barre`, `sd_inter`, `ic_sd`, `n_derive`, la ligne de calcul, les dispersions par carte |
| `pilote.log` | la sortie console complète |
| `empreintes_apres.txt` | taille + mtime des `.brain` après le run (preuve de lecture seule) |

## 6. Ce que ce pilote NE mesure PAS

- Il ne dit **rien du cursus** : le banc force des cartes imposées (règle « un banc forcé ne
  prouve rien sur le cursus », CLAUDE.md §7).
- Il ne **certifie pas** que le banc juge juste : il le **dimensionne**. Le test
  d'acceptation D3 est une autre étape.
- Une dispersion à 4 cerveaux est **mal connue** : c'est pourquoi `ic_sd` est publiée et
  pourquoi `n` doit être relu à la lumière de cet intervalle.
- Les 4 cerveaux appartiennent au **même bras** : la dispersion mesurée est celle du bras
  `K8_NU`, pas celle qui séparerait deux bras différents.

## 7. Résultat (mesuré le 2026-09-13, 00:31:36 → 00:32:57, 81 s)

Le détail, les vérifications et les limites sont dans le carnet
[`docs/recherche/campagnes/EVA01_13092026_la_derivation_de_n.md`](../../docs/recherche/campagnes/EVA01_13092026_la_derivation_de_n.md).
En quatre lignes :

| Grandeur | Valeur |
|---|---|
| `p_barre` (poolé, 2 cartes, 4 cerveaux) | **0,256250** (41/160) |
| `sd_inter` (inter-cerveaux, ddof = 1) | **0,071807** |
| `ic_sd` (IC95, chi-deux, df = 3) | **[0,040678 ; 0,267736]** |
| **`n_derive`** | **333** |

Le `20` de ce pilote est resté ce qu'il était : un **budget de mesure**. Le `n` du protocole
(tâche 8) est le **333**, avec sa ligne de calcul écrite dans `pilote.json`. La mesure n'est
pas dégénérée : aucune cellule saturée, aucun épisode tronqué, A/A à **160/160 épisodes
identiques**. ⚠️ Deux faits sont publiés ici **sans être corrigés** (hors périmètre de la
tâche 7) : la `trajectoire` du banc perd le but sur **8 victoires sur 41**, et `K8_NU_g11`
porte un état incohérent (`env_id` contre `niveau_actuel`).
