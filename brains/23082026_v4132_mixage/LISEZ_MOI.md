# Campagne 23/08/2026 — La sonde de mixage (v41.32, étape 1)

## Ce qu'on cherchait

Mesurer, pour chacun des **11 termes** sommés à poids 1 au point d'assemblage unique de la
récompense (`noyau.py`, `recompense_interne`), sa **moyenne** et surtout son **écart-type**
— avant de toucher à la moindre pondération.

Question de fond : le soulagement de l'eau est-il **noyé** sous le bruit de fond, comme le
supposait la proposition « table de mixage / Maslow émergent » ?

## Protocole

Test **A/A** (deux runs rigoureusement identiques), conformément à `CLAUDE.md` §5 :

```bash
mkdir -p brains/23082026_v4132_mixage        # AVANT le lancement
for rep in 1 2; do
  WANDB_MODE=offline PYTHONPATH=src python -m naulthene.cerveau.noyau \
      --graine 11 --jours 40 \
      --brain "brains/23082026_v4132_mixage/AA_g11_rep${rep}.brain" \
      > "brains/23082026_v4132_mixage/AA_g11_rep${rep}.log" 2>&1 &
done
```

- **Graine** : 11 · **Jours** : 40 · **Cursus complet** (pas de `--env-force`)
- **Version** : v41.32-étape1, sonde de mixage (télémétrie pure)

## Résultat A/A

**δ_A/A = 0 — les deux runs sont bit-identiques** sur les 40 nuits (lignes de mixage et
niveaux atteints). Le banc est déterministe : un futur A/B pourra attribuer son effet.

## Résultat principal

| TERME | MOYENNE | σ | PART DU SIGNAL |
|---|---|---|---|
| **Bio** | +0,00346 | **0,04357** | **44,0 %** |
| **Env** | +0,00136 | 0,02163 | 21,8 % |
| Stagnation | −0,01611 | 0,01359 | 13,7 % |
| Curiosite | +0,02091 | 0,00889 | 9,0 % |
| SousObjectif | +0,00171 | 0,00679 | 6,8 % |
| Progres | +0,00090 | 0,00462 | 4,7 % |
| Jalons | 0,00000 | **0,00000** | 0,0 % |
| Portes | 0,00000 | **0,00000** | 0,0 % |
| Vocal | 0,00000 | **0,00000** | 0,0 % |
| CoutC3 | 0,00000 | **0,00000** | 0,0 % |
| Guidage | 0,00000 | **0,00000** | 0,0 % |
| *TOTAL assemblé* | *+0,01223* | *0,05955* | — |

**5 termes sur 11 sont rigoureusement MUETS** (σ = 0,00000 exact sur 40 nuits × 400 ticks).

⚠️ **Ce sont des ablations VIDES, pas négatives.** L'agent est resté au **niveau 1/15**
(`Empty-5x5`) : pas de porte, pas de DoorKey — donc `Jalons`, `Portes` et `Guidage` n'ont
aucun support sur cette carte ; pas de tuteur vocal ni de plug C3 pour les deux autres.
Ces cinq termes devront être remesurés sur une carte où ils existent (niveau 4).

## Empreinte de type (vérification 1.e, canal WATER)

Lecture directe du `.brain` :

| TYPE | VALENCE | VÉCU |
|---|---|---|
| `goal` | **+0,65143** | 36 |
| `FOOD` | **+0,57497** | 67 |
| `sol` | +0,11984 | 884 |
| `WATER` | **+0,11673** | 60 |

Le correctif v41.7 **fonctionne** : `FOOD` n'est plus à 0,000 (il était à `+0.000 ×4004`),
il est à **+0,575**, comparable à `goal`. Mais `WATER` reste à **+0,117** — exactement le
niveau du **sol nu**, pour un nombre d'expériences comparable à `FOOD` (60 contre 67).

## Fichiers

- `AA_g11_rep{1,2}.brain` — les deux cerveaux A/A
- `AA_g11_rep{1,2}.log` — bilans de nuit complets (40 nuits chacun)
- `resultats_mixage.json` — l'agrégat, écrit à côté des sources (règle `CLAUDE.md` §7)
