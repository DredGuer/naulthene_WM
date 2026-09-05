# PPO AU NIVEAU DU MUR — `LavaGapS5`

**Date** : 2026-09-06 · **Statut** : 🟡 protocole écrit **AVANT** le lancement ·
Piste §4.1 de [PLAN_05092026](../../docs/ameliorations/PLAN_05092026_toutes_les_pistes_classees.md).

## La question posée

> *« Le mur n'existe pas »* (BASELINE_PPO, 29/08) a été mesuré sur
> **`SimpleCrossingS9N1`** — le **niveau 3**, que Naulthène **franchit** (20/20 en régime
> libre). Le mur, lui, est au **niveau 4** : **`LavaGapS5`**, où **40 runs sur 40**
> s'arrêtent. La conclusion « le plafond est une pathologie de cette architecture » est
> donc une **extrapolation d'un niveau à l'autre**, jamais mesurée là où ça bloque.

**PPO franchit-il `LavaGapS5` ?**

## Ce que chaque issue signifie

| Issue | Lecture | Conséquence sur le plan |
|---|---|---|
| **PPO réussit bien** (≫ témoin aléatoire) | le mur est **architectural** | le plan §20 tient : §3 (pas d'optimiseur) et §6 (échelle Bio) passent devant |
| **PPO plafonne aussi** | le mur est **la carte** | §4.2 (permuter `LavaGapS5` dans le cursus) passe **devant tout**, et « le mur n'existe pas » doit être **nuancé publiquement** (README FR+EN, règle de miroir) |

## Protocole

```bash
PYTHONPATH=src python -m naulthene.instruments.banc_ppo \
    --env MiniGrid-LavaGapS5-v0 --graine <g> --pas 152043 \
    --sortie brains/06092026_ppo_lavagap/ppo_lavagap_g<g>.json
```

- **A/A d'abord** (règle §5) : deux runs identiques, graine 11. `δ_A/A` = plancher de détection.
- **n = 5 graines** (11, 22, 33, 44, 55) — ⚠️ **sous le seuil des 20** : ce banc ne peut
  donner qu'un **ordre de grandeur**, jamais un `t`. Le contraste attendu (PPO 2,3× le
  témoin au niveau 3) est massif ; s'il faut n=20 pour le voir, c'est déjà une réponse.
- **Témoin** : le marcheur aléatoire sur la même carte, même budget.
- `--pas 152043` : le tick_absolu réel de A_g11 à 400 jours, **jamais estimé** (v41.38).

## ⚠️ Ce que ce banc ne dira PAS

1. **Il ne mesure pas Naulthène.** Il mesure si la carte est solvable par un RL standard
   au même budget. Un PPO qui échoue ne prouve pas que Naulthène est sain.
2. **`max_steps` = 100 sur `LavaGapS5`** contre **324** sur `SimpleCrossingS9N1` — budget
   par épisode **3,2× plus court**. Un taux de réussite plus bas est donc attendu même
   sans difficulté supplémentaire : comparer à **son propre témoin aléatoire**, jamais au
   25,83 % du niveau 3.
3. **Mourir dans la lave termine l'épisode avec `recompense_env = 0`** : la réussite se
   juge sur `recompense_env > 0`, jamais sur `termine` (invariant v35.0-4).

## Résultats

*(rempli au fil de l'eau — agrégat machine : `agregat.json`)*
