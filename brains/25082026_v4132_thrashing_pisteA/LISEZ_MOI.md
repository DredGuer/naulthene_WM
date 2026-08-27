# Campagne 25/08/2026 — Piste A du thrashing : l'instabilité du monde

## Ce qu'on cherchait

Le thrashing du gradient est confirmé (alignement 0,40 contre un hasard à 0,35). **Piste A** :
le cursus change de carte d'un jour à l'autre (P17), donc la politique optimale change —
d'où des gradients contradictoires.

**Prédiction** : verrouiller la carte **réduit** le thrashing (alignement **monte**).

## Protocole

A/B **apparié** — même `.brain` de départ, même graine (11), 12 jours, seul le verrou change.

```bash
cp .../N4_g11.brain brains/25082026_v4132_thrashing_pisteA/base.brain
# A (témoin)   : cursus libre
PYTHONPATH=src python -m naulthene.instruments.sonde_gradient --brain base.brain --jours 12 --graine 11
# B (ablation) : carte verrouillée
PYTHONPATH=src python -m naulthene.instruments.sonde_gradient --brain base.brain --jours 12 --graine 11 \
    --env-force MiniGrid-SimpleCrossingS9N1-v0
```

⚠️ `--env-force` a dû être **ajouté à la sonde** : `--niveau` ne suffit pas, il fixe l'env au
démarrage mais `demarrer_journee` change ensuite de carte via P17.

## 🔴 Résultat : réfutée, et dans le mauvais sens

| BRAS | alignement final | repère 1/√12 |
|---|---|---|
| **A — cursus libre** (témoin) | **0,3428** | 0,2887 |
| **B — carte verrouillée** | **0,2630** | 0,2887 |

**Verrouiller le monde AGGRAVE le thrashing de 23 %.** L'instabilité du cursus n'est pas la
cause — elle serait plutôt un facteur **stabilisant**.

Et le bras B passe **sous** le repère du hasard (0,2630 < 0,2887) : ce n'est plus seulement
des pas indépendants, c'est une **annulation active**.

## Trajectoires complètes

| jour | A ‖Σg‖ | A align. | B ‖Σg‖ | B align. |
|---|---|---|---|---|
| 4 | 0,4845 | 0,7298 | 0,7132 | 0,6034 |
| 8 | 0,5204 | 0,3966 | 0,9669 | 0,4986 |
| 10 | 0,8116 | 0,4295 | 0,7976 | 0,2937 |
| 12 | 0,8219 | **0,3428** | 0,8329 | **0,2630** |

⚠️ Fait notable : `‖Σg‖` **plafonne** dans les deux bras (~0,82) pendant que `Σ‖g‖` continue
de croître (2,40 et 3,17). La direction utile sature ; tout le gradient supplémentaire est
dépensé en allers-retours.

## ⚠️ Réserve majeure — l'ablation est PARTIELLE

| | révisions P17 |
|---|---|
| Bras A | 1 à 3 par jour, sur 12 jours |
| Bras B | 0 sur 3 jours, **1 sur 9 jours** |

`--env-force` fixe l'`env_id` mais **P17 révise encore à l'intérieur de la carte**. Le
contraste entre les deux bras est donc **faible**, et l'écart mesuré est un **minorant**.

⚠️ **Une seule graine, 12 jours.** Le sens de l'effet (B pire que A) est net, mais il faudrait
n ≥ 20 graines pour en faire une mesure plutôt qu'un indice.

## Ce que cela laisse

| Piste | État |
|---|---|
| **A — instabilité du monde** | 🔴 **réfutée** (effet inverse) |
| B — masquage causal (~38 % des ticks) | ⬜ non testée |
| C — alternance des besoins (faim/soif) | ⬜ non testée |

La piste C gagne en plausibilité : le gradient est dominé par `integrateur_bio` (0,914,
soit **78×** la vue), et les besoins corporels **alternent** par construction.

## Fichiers

- `base.brain` — le cerveau de départ, commun aux deux bras
- `A_cursus_libre.log` / `B_carte_fixe.log` — les deux runs complets
