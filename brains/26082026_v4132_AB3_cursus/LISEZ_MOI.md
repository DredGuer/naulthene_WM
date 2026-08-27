# Campagne 26/08/2026 — AB3 (detach asymétrique C2) sur cursus complet

## L'hypothèse testée

Le thrashing du gradient vient de la **collision C1/C2 dans `integrateur_bio`** — la seule
couche où les deux têtes rétropropagent (6,127 et 4,907), le tronc perceptif étant coupé des
deux par le `.detach()` de la l. 1149.

**AB3** (`--detach-c2`) donne à C2 un **droit de lecture seule** sur la représentation
viscérale : il lit `pensee_bio` pour évaluer et planifier, `cortex_prefrontal` continue
d'apprendre, mais il ne rétropropage plus dans `integrateur_bio`. Seul C1 sculpte le corps.

## Ce que le banc a déjà donné (12 jours, 1 graine)

| | témoin | AB3 |
|---|---|---|
| alignement du gradient | 0,3428 | **0,4298** (+25 %) |
| `‖Σg‖` final | 0,8219 | **1,8674** (×2,3 — saturation levée) |
| gradient/jour `tete_motrice` | 0,1998 | **0,3621** (×1,8) |
| `cortex_prefrontal` apprend | oui | **oui** (0,638/jour) |

⚠️ **AB3 n'est PAS validé** : +25 % contre +97 % pour AB1 (qui coupe tout le gradient de C2
mais n'est pas viable — sa ligne de base dérive), et la trajectoire **chute au jour 9**
(0,723 → 0,430). Une seule graine, 12 jours, sur banc de sonde.

## Protocole

| | |
|---|---|
| **Bras A** (témoin) | nominal, `DETACH_C2_ASYMETRIQUE = False` |
| **Bras B** | `--detach-c2` |
| Graines | **20, appariées** (mêmes graines dans les deux bras) |
| Durée | **1440 jours** |
| Environnement | **cursus complet** (15 niveaux, pas de `--env-force`) |
| Total | **40 runs** |

**Pourquoi 1440 jours** : la neurogenèse est éteinte depuis **882 jours** en moyenne — au-delà
de ~1500 jours le réseau ne change plus structurellement. La campagne de référence du 22/08
tournait à 1500 jours et a suffi à établir le plafond (niveau 4,10 vs 4,05).

**Pourquoi pas de A/A** : il a été fait deux fois cette semaine, **δ = 0** (bit-identique) sur
`Empty-5x5` et sur le cursus. Le déterminisme du banc est établi ; le relancer coûterait
20 runs pour reconfirmer un acquis. L'**appariement strict** est conservé — c'est lui qui fait
la puissance du test.

## Métriques

- **niveau atteint** (le juge principal — plafond mesuré à 4/15 sur 40 cerveaux)
- maîtrise sur les 100 dernières nuits
- énergie moyenne, satiété minimale
- alignement du gradient et `‖Σg‖` si lisibles

## ⚠️ Règles appliquées

- **Aucun `t` avant la fin des 40 runs.** Leçon du 20/08 (`t=+3,68` à mi-parcours → `+1,93` à
  la fin) et du 22/08 (maîtrise +4,95 à n=5 → +1,09 à n=20).
- **Correction de Bonferroni** si plusieurs métriques sont testées.
- Un banc forcé ne prouve rien sur le cursus : c'est précisément pourquoi cette campagne
  tourne en **cursus libre**.

## Commandes

```bash
C=brains/26082026_v4132_AB3_cursus
for g in <20 graines>; do
  # bras A (témoin)
  WANDB_MODE=offline PYTHONPATH=src python -m naulthene.cerveau.noyau \
      --graine $g --jours 1440 --brain "$C/A_temoin_g$g.brain" > "$C/A_temoin_g$g.log" 2>&1
  # bras B (AB3)
  WANDB_MODE=offline PYTHONPATH=src python -m naulthene.cerveau.noyau \
      --graine $g --jours 1440 --detach-c2 --brain "$C/B_detach_g$g.brain" > "$C/B_detach_g$g.log" 2>&1
done
```

## Durée estimée

Mesuré : **396 s pour 50 jours** → ~3 h 10 par run de 1440 jours. **40 runs en 8 parallèle :
~16 heures.**
