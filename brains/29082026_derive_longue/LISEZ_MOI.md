# Mesures de dérive de représentation — 28-29/08/2026

Deux runs instrumentés sur **copies** de `brains/28082026_v4134_tronc/A_g11.brain`
(règle §8 : ne jamais reprendre un `.brain` sans le copier — il est écrasé à chaque nuit).

| Fichier | Run | Ce qu'il mesure |
|---|---|---|
| `derive_g11.{log,json}` | 300 nuits | rotation de l'axe informatif, **visuel vs complet** |
| `course_g11.{log,json}` | 200 nuits | les **deux** vitesses : l'axe et `W`, même protocole |

## Résultats

**Dérive (300 nuits)** — plancher de bruit de la sonde : **0,0198°**

- décroissance d'un facteur **7** jusqu'à la nuit ~100 (1,148° → 0,166°) ;
- puis **remontée** : pente **+0,00044 °/nuit** sur la seconde moitié, 0,409° au dernier bloc ;
- l'erreur JEPA converge proprement pendant ce temps (0,00735 → 0,00290, **monotone**) et
  `dim_bus` reste à 147 — ni le modèle du monde ni la neurogenèse n'expliquent la remontée ;
- ratio axe complet / axe visuel : **1,15 à 1,70**, sans tendance à la baisse.

**Course (200 nuits)**

- la proie (l'axe) : **0,4203 °/nuit** · le prédateur (`W`) : **0,0359 °/nuit** → **×11,7** ;
- alignement **0,1051 → 0,0917** : il **recule** (gain net −0,000069/nuit) ;
- **couplage** : quand `rot_axe` tombe à 0,101°, `rot_W` tombe à 0,012° en même temps.

## ⚠️ Portée

**Un seul cerveau, un seul environnement.** La règle des 20 graines s'applique : ce sont des
tendances fortes, pas des conclusions de population. Le lien avec le plafond au niveau 4
reste **non mesuré**.

Carnet complet : `docs/recherche/COURSE_29082026_le_predateur_recule.md`.

## Reproduction

```bash
cp brains/28082026_v4134_tronc/A_g11.brain brains/<campagne>/copie.brain
PYTHONPATH=src python -m naulthene.instruments.sonde_derive_longue     brains/<campagne>/copie.brain --jours 300 --sortie d.json
PYTHONPATH=src python -m naulthene.instruments.sonde_course_poursuite  brains/<campagne>/copie.brain --jours 200 --sortie c.json
```
