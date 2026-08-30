# Audit du génome — 30/08/2026

Mesures de l'[audit du génome](../../docs/etat_des_lieux/30082026_le_genome_audit_des_constantes.md).

## Protocole

Cerveau source : `brains/26082026_v4132_AB3_cursus/A_g11.brain` (campagne AB3, bras A,
graine 11), **copié** avant chaque usage — jamais lu en place (la sonde recharge et
pourrait écraser).

```bash
cp brains/26082026_v4132_AB3_cursus/A_g11.brain brains/30082026_audit_genome/s_nX.brain
WANDB_MODE=offline PYTHONPATH=src venv/bin/python \
    -m naulthene.instruments.sonde_recompense \
    --brain brains/30082026_audit_genome/s_nX.brain --jours 2 --niveau X
```

Niveaux mesurés : **0** (`Empty-5x5`), **3** (`SimpleCrossingS9N1` — le plafond),
**4** (`LavaGapS5`). 800 ticks chacun, 2 400 au total.

## Résultats

| Niveau | Récompense du monde | Total positif | Part du monde |
|---|---:|---:|---:|
| N0 | 1,0272 | 15,4523 | 6,65 % |
| N3 | **0,0000** | 14,5106 | **0,00 %** |
| N4 | 1,0382 | 17,0661 | 6,08 % |
| **Total** | **2,0654** | **47,0290** | **4,39 %** |

**95,61 % du signal d'apprentissage vient de constantes posées.**

## ⚠️ Bug d'instrument découvert pendant ces mesures

`sonde_recompense` **reconstruisait** `MALUS_DOULEUR` (supprimé du chemin en v41.27) au
lieu de le lire. Écart mesuré **−4,6200** contre un fantôme de **−4,6200** — le terme
inventé expliquait la totalité de l'écart et **retournait le signe** de la conclusion.
Corrigé le 30/08/2026 ; les chiffres ci-dessus sont **post-correctif**.

⚠️ **Toute mesure de `sonde_recompense` antérieure au 30/08/2026 est à refaire.**

## Limites

- **n = 1 cerveau.** Mesures **directes** (§4 de la règle de mesure : fiables comme
  lecture), pas une comparaison appariée. Aucune causalité établie avec le plafond.
- Le motif est reproduit sur 3 niveaux, ce qui est une cohérence interne, pas un `n`.
