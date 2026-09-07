# PPO SUR `LavaGapS5` — 🔴 CARNET RÉTRACTÉ : ce n'était PAS le niveau du mur

> # 🔴 RÉTRACTATION DU 07/09/2026
>
> **Ce carnet a testé PPO sur une carte qui n'est pas celle du blocage.** Sa conclusion
> principale est **fausse** et a été publiée dans les deux README, au CHANGELOG v41.60, au
> journal des runs et dans le PLAN §4.
>
> **La cause** : un décalage de numérotation. Le log affiche `niveau_actuel + 1`
> (`noyau.py:11344`), donc **« Niveau 4/15 » est l'index 3 = `SimpleCrossingS9N1`**, pas
> `LavaGapS5`. Vérifié indépendamment sur les logs, qui nomment la carte jouée :
>
> ```
> TEMOIN bloqué   : 🌙 Jour 1500 [Primaire 1 (Contourner)]   ← SimpleCrossingS9N1
>                   🎓 Niveau 4/15 — maîtrise 10%
> K8 « niveau 5 » : 🌙 Jour 1500 [Primaire 2 (Éviter le danger)] ← LavaGapS5
> ```
>
> **Le mur est donc `SimpleCrossingS9N1`**, et les cerveaux K8 qui « franchissent le niveau
> 5 » viennent en réalité **d'entrer dans `LavaGapS5`** — ils ont franchi le vrai mur.
>
> | Affirmation publiée | Ce qui est vrai |
> |---|---|
> | « PPO résout le niveau du mur à **97,27 %** quand Naulthène ne passe jamais » | mesuré sur `LavaGapS5`, **une carte plus loin** que le blocage |
> | « L'écart se creuse : **14,6×** » | sur la **vraie** carte du mur, PPO fait **36–40 %** contre **25,83 %** pour Naulthène — **~1,5×** |
> | « Le mur est une pathologie de cette architecture » | **partiellement une règle du cursus** : `TAUX_PROMOTION = 0,60` exige 60 % de réussite, quand **PPO lui-même plafonne à 40 %** sur cette carte |
>
> **Ce qui SURVIT de ce carnet** : la mesure elle-même est juste — PPO résout bien
> `LavaGapS5` à 97,27 % (n=5, δ_A/A = 0). C'est son **interprétation** qui est fausse. Et le
> fait est même plus intéressant retourné : `LavaGapS5` est, pour un RL standard, **plus
> facile** que la carte qui bloque Naulthène.
>
> ⚠️ **Conséquence collatérale** : cinq versions de mécaniques « lave » (v41.11 → v41.27) ont
> été construites pour une carte **hors du chemin du blocage**.
>
> Voir [le point général du 07/09](../../etat_des_lieux/07092026_point_general_et_direction.md).

---

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
