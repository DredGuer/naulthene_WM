# P3 — l'échelle de stagnation dérivée (30/08/2026)

Mesures du [chantier v41.43](../../docs/ameliorations_appliquees/CHANTIER_v41.43_hygiene_du_genome.md).

## A/B sur la même graine

Cerveau `A_g11` (copié depuis `brains/26082026_v4132_AB3_cursus/`), niveau 3, 800 ticks,
**un seul facteur changé** :

| | FOSSILE (`0.015` posé) | DÉRIVÉ (`0.1/max_steps`) | Facteur |
|---|---:|---:|---:|
| Stagnation | −14,0527 | **−0,4156** | **÷33,8** |
| Total positif | 14,5106 | 15,9185 | ×1,10 |
| **Solde net** | **+0,4579** | **+15,5029** | **×33,9** |

Le témoin restitue **exactement** les chiffres d'origine, au dix-millième — le A/B est propre.

## Commandes

```bash
# bras dérivé (défaut depuis v41.43)
WANDB_MODE=offline PYTHONPATH=src venv/bin/python \
    -m naulthene.instruments.sonde_recompense \
    --brain <copie>.brain --jours 2 --niveau 3

# bras témoin : forcer STAGNATION_DERIVEE_ACTIVE = False au niveau module
# (le drapeau --stagnation-fossile appartient au cursus, pas à la sonde)
```

## ⚠️ Limites

- **n = 1 cerveau**, aucun run lancé. Mesure d'**échelle**, pas de performance.
- **Ni le niveau ni la maîtrise** n'ont été mesurés sous échelle dérivée.
- Rien n'autorise à présenter ce correctif comme une piste sur le plafond.

Les `.brain` de travail ont été supprimés après mesure ; les sources restent intacts dans
`brains/26082026_v4132_AB3_cursus/`.
