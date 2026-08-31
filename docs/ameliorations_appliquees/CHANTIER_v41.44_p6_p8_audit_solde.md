# Chantier v41.44 — P6 et P8 : l'audit du génome est soldé

**30/08/2026** · document `ameliorations_appliquees/` : ce qui est **livré**.

Clôture de l'[audit du génome](../etat_des_lieux/30082026_le_genome_audit_des_constantes.md),
après [P7 et P3](CHANTIER_v41.43_hygiene_du_genome.md).

⚠️ **Aucune mesure comportementale.** Ni niveau ni maîtrise. Ces chantiers alignent le code
sur le dogme ; ils ne prétendent rien sur le plafond.

---

## P6 — le seuil de cristallisation devient relatif ✅

### La mesure : une mécanique morte depuis la v26.0

Sur **10 cerveaux** de la cohorte AB3 :

| | Valeur |
|---|---:|
| Synapses cristallisées | **0 / 1 906 360** (0,0000 %) |
| `myeline_cumul` maximum observé | **0,01193434** |
| `SEUIL_CRISTAL` posé | **0,80** |
| Facteur manquant | **×67** |

La Cristallisation Souple ne s'est enclenchée sur **aucun** cerveau du dépôt, jamais. Ce
n'était pas une protection dormante : c'était du code mort **exécuté chaque nuit, sur
chaque synapse**, pour un résultat toujours nul.

### C'est le bug de la v37.0, resté quatre versions de plus

`q_ref = 1.0` supposait une myéline d'ordre 1 alors qu'elle vaut ~0,002 — échelle 500× trop
grande, `myeline_norm` collée à 0. Corrigé en v37.0 par `echelle_myeline`, un **quantile de
la couche**. `SEUIL_CRISTAL` est **le même bug, au même endroit** : une échelle absolue
posée a priori, jamais confrontée à une mesure.

### La correction

```python
seuil_cristal = echelle_myeline × FRACTION_SEUIL_CRISTAL      # au lieu de 0.80
```

`echelle_myeline` est déjà calculée deux lignes plus haut (quantile 0,75 de `myeline_M`,
monotone croissante) — elle est **réutilisée**, jamais recalculée, pour qu'il n'existe pas
deux échelles divergentes.

### Effet mesuré

| Cerveau | Cristallisées (avant) | Cristallisées (après) |
|---|---:|---:|
| Neuf, 3 nuits | 0 / 19 616 | **0 / 19 616** *(attendu : rien de myélinisé encore)* |
| Mature (26/08) | 0 / 219 965 | **3 071 / 219 965 (1,4 %)** |

La mécanique **fonctionne enfin**, et reste **rare** — c'est l'invariant recherché.

⚠️ **Ce que cela ne dit pas** : que c'est bénéfique. Figer une synapse est **irréversible**
(cliquet à sens unique). Deux témoins existent pour trancher un jour :
`--cristallisation-fossile` (seuil absolu 0,80, donc jamais) et `--sans-cristallisation`.

---

## P8 — le cœur ne nomme plus les couleurs ✅

### Ce qui a été déplacé

| Site | Avant | Après |
|---|---|---|
| `COULEUR_FOOD = "red"` | littéral dans `noyau.py` | **alias** de `bus_sensoriel.COULEUR_NOURRITURE` |
| `COULEUR_WATER = "blue"` | littéral dans `noyau.py` | **alias** de `bus_sensoriel.COULEUR_EAU` |
| `type == "ball"` | littéral dans `noyau.py` | `bus_sensoriel.TYPE_RESSOURCE` |

Les deux couleurs étaient une **duplication pure** : `bus_sensoriel` les exposait déjà, et
`noyau.py` les importait déjà. Il y avait donc deux sources pour la même vérité.

L'invariant v29.0 est préservé : `bus_sensoriel.py` reste **pur numpy** et n'importe
**jamais** `noyau.py` — la dépendance ne va que dans un sens (vérifié).

### ⚠️ Ce que P8 ne corrige PAS, et qu'il faut dire

Deux tables **restent** dans `noyau.py` :

```python
MOT_PAR_OBJET_MINIGRID  = {"wall": "mur", "door": "porte", "key": "clé", …}
MOT_PAR_COULEUR_MINIGRID = {"red": "rouge", "blue": "bleu", …}
```

Elles appartiennent au `LecteurCaseFrontale`, qui ne renvoie **aucune récompense** — il
renvoie un **mot**, pour l'apprentissage vocal. Nommer y est la **fonction même** : l'agent
doit apprendre à *dire* « mur ». Ce n'est pas un câblage de préférence.

Et surtout : **le cœur reste le jardinier du monde**. Il *sème* les ressources, donc il
dépend de la convention « une balle rouge est de la nourriture ». Le **nom** a quitté le
cœur ; la **dépendance** demeure. Dire l'inverse serait exactement le genre
d'enjolivement que ce dépôt s'interdit.

---

## Validation

| Test | Résultat |
|---|---|
| Seuil relatif s'enclenche (unitaire) | 1 synapse / 32, à la nuit 5 |
| Témoin `--cristallisation-fossile` | **0 cristallisée** — reproduit la v26.0 |
| Ablation `--sans-cristallisation` | 0 cristallisée |
| **Nuit complète** (3 nuits, run réel) | `exit=0`, 3 cristallisations, **aucun `NameError`** |
| **Test A/A** | **δ_A/A = 0** — banc déterministe |
| Rétrocompat `.brain` du 26/08 | 2 nuits, `exit=0` |
| Les 3 drapeaux CLI atteignent le module | assertion runtime OK |
| Alias P8 pointe la source unique | `COULEUR_FOOD == COULEUR_NOURRITURE` → `True` |
| Naissance | 7 760 paramètres, inchangé |

⚠️ **Non couvert** : effet sur le niveau et la maîtrise (exigent 20 graines × cursus
complet). `colab.py` non modifié.

---

## L'audit du génome est soldé

| # | Proposition | État |
|---|---|---|
| P1 | Corriger « 55 616 à la naissance » | ✅ v41.41 |
| P2 | Mesurer le barème | ✅ v41.42 — **réfuté (tautologie)** |
| P3 | Dériver la pénalité de stagnation | ✅ v41.43 — **reformulé** (pas un doublon) |
| P4 | Dériver `PLAFOND_ERREUR_DOPAMINE` | ⬜ **ouvert** |
| P5 | Dériver `BUS_REFERENCE_INITIAL` | ⬜ ouvert (cohérence, pas performance) |
| P6 | `SEUIL_CRISTAL` relatif | ✅ **v41.44** |
| P7 | Supprimer `MALUS_DOULEUR` | ✅ v41.43 |
| P8 | Déplacer les noms du monde | ✅ **v41.44** (partiel, cf. ci-dessus) |
| P9 | Isoler les vestiges DoorKey | ⬜ ouvert |

**Reste ouvert** : P4 (la curiosité, 40 % du signal pour un effet mesuré **nul**), P5, P9.
