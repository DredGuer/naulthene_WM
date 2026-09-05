# PPO AU NIVEAU DU MUR — le mur n'est pas la carte

**Date** : 2026-09-06 · **Statut** : ❌ **HYPOTHÈSE RÉFUTÉE** (§4 du plan) ·
**n = 5 graines · δ_A/A = 0,000000** · coût : ~40 min.

> **Protocole écrit AVANT le lancement** : `brains/06092026_ppo_lavagap/LISEZ_MOI.md`.

---

## 1. La question posée

*« Le mur n'existe pas »* ([BASELINE_PPO](BASELINE_PPO_29082026_le_mur_n_existe_pas.md),
29/08) a été mesuré sur **`SimpleCrossingS9N1`** — le **niveau 3**, que Naulthène
**franchit** (20/20 en régime libre). Le mur, lui, est au **niveau 4** : **`LavaGapS5`**,
où **40 runs sur 40** s'arrêtent.

La conclusion « le plafond est une pathologie de cette architecture » reposait donc sur une
**extrapolation d'un niveau à l'autre**, jamais mesurée là où ça bloque. D'où :
**PPO franchit-il `LavaGapS5` ?**

L'hypothèse testée était favorable à Naulthène : *si PPO plafonne aussi, le mur est la carte*
— `LavaGapS5` a la mort qui paie `0.0` quand un mur coûte `−0,01`, aucune case indolore
(77 % à distance 1 de la lave), et un agent dont `Bio` pèse 57 % du gradient y a une raison
mécanique de ne pas bouger.

## 2. Le résultat

| Graine | Réussite PPO |
|---|---|
| g11 (contrôle A/A) | **98,00 %** |
| g22 | **100,00 %** |
| g33 | 97,67 % |
| g44 | **100,00 %** |
| g55 | 90,67 % |
| **Moyenne (n=5)** | **97,27 %** |

| Comparaison, même carte, même budget | Taux |
|---|---|
| **PPO** (69×69, 152 043 pas) | **97,27 %** |
| Marcheur aléatoire (600 épisodes) | **6,67 %** — IC95 [4,67 ; 8,66] |
| **Naulthène** (40 runs × 1500 jours) | **0 franchissement** |

**PPO fait 14,6× le témoin aléatoire. Naulthène n'y arrive jamais.**

## 3. Les vérifications

| Vérification | Résultat |
|---|---|
| **A/A** (deux runs identiques) | **δ = 0,000000** sur les 5 métriques — banc déterministe |
| **Le drapeau atteint-il le module ?** | ✅ testé avant lancement : `faire_env` construit bien `LavaGapS5` (`max_steps` 324 → **100**) |
| **Réussite = `r > 0` ?** | ✅ `_reussite` compte `int(r > 0)` — mourir dans la lave donne `r = 0`, donc échec (invariant v35.0-4) |
| **Témoin sur la même carte ?** | ✅ 6,67 % sur 600 épisodes, même budget de 400 pas |
| **Résultat trop propre ?** | ⚠️ 100,00 % sur 2 graines — vérifié : c'est `300/300` épisodes, pas un canal débranché ; la dispersion existe (min 90,67 %) |

## 4. Ce que ça ferme

🔴 **L'hypothèse §4 est réfutée. Le mur n'est pas `LavaGapS5`.**

Et le constat le plus dur du dépôt **s'aggrave** :

| Niveau | PPO | Naulthène |
|---|---|---|
| 3 — `SimpleCrossingS9N1` | ~40 % | 25,83 % (franchi) |
| **4 — `LavaGapS5`** | **97,27 %** | **0 / 40 runs** |

Au niveau 3, PPO faisait **2,3×** mieux. Au niveau 4, il fait **essentiellement tout** là où
Naulthène ne passe jamais. `LavaGapS5` est, pour un RL standard, **plus facile** que le
niveau précédent (`max_steps` 100, carte 5×5, chemin court) — c'est précisément là que
Naulthène s'arrête.

> **Le plafond n'est pas une propriété du monde. Il est dans l'architecture, et l'écart
> se creuse avec la facilité de la tâche.**

## 5. Ce que ça laisse ouvert

- **La permutation du cursus (§4.2) perd sa justification** : déplacer `LavaGapS5` ne
  contournerait pas un obstacle du monde, il n'y en a pas.
- Reste entière la question de **pourquoi** un agent qui gagne 860 fois dans sa vie ne
  convertit jamais ces victoires en promotion sur cette carte.
- ⚠️ **n = 5, sous le seuil des 20 graines.** Le contraste (97,27 % contre 6,67 %) est
  d'un ordre de grandeur au-dessus de tout ce que n=5 pourrait confondre avec du bruit,
  mais aucune comparaison **fine** ne doit être tirée de ces cinq points.

---

*Outil : `banc_ppo.py` + `--env` (v41.60, le défaut reste `SimpleCrossingS9N1` pour que
l'A/A du 29/08 reste reproductible bit à bit). Agrégat : `brains/06092026_ppo_lavagap/agregat.json`.*
