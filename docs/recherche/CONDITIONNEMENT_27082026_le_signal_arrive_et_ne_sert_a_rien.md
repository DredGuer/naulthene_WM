# 27/08/2026 — Le signal perceptif ARRIVE aux logits. Ce n'est pas un défaut de câblage.

> Dixième réfutation. Non normatif — carnet d'enquête.
> Fait suite à la campagne AB3 (`brains/26082026_v4132_AB3_cursus/RESULTATS.md`).

## L'hypothèse testée

Après AB3, j'avais proposé que le plafond vienne d'un **défaut de conditionnement** :
l'agent déciderait sur son état interne sans que la perception atteigne la tête motrice.
Preuve invoquée : taux de saisie 10,7 % à faim 0,963, et 53 gestes `consommer` sur 62
joués dans le vide.

**Cette hypothèse est fausse.** Le signal arrive.

## Instrument

`src/naulthene/instruments/sonde_conditionnement.py` (lecture seule) — rejoue le chemin
de C1 étage par étage sur des états réels triés en deux classes (*face à une ressource* /
*face à un mur*), avec **plancher de bruit** (p95 de la distance entre deux moitiés du
même groupe) et **d-prime**.

Contrôle de fidélité du rejeu manuel contre `_executer_c1_reflexe` : **écart max
0.000e+00**, bit-identique.

## Résultat — 6 étages, 300 captures par classe (A_g11)

| Étage | d_inter | plancher | verdict | d-prime |
|---|---|---|---|---|
| `bus_latent` | 0,010972 | 0,001332 | **SIGNAL** | 0,607 |
| `memoire_actuelle` | 0,010927 | 0,002014 | **SIGNAL** | 0,568 |
| `pensee` | 0,009335 | 0,001287 | **SIGNAL** | 0,568 |
| `pensee_enrichie` | 0,004961 | 0,000776 | **SIGNAL** | 0,529 |
| `pensee_bio` | 0,023511 | 0,002598 | **SIGNAL** | 0,568 |
| `logits_C1` | 0,020617 | 0,005024 | **SIGNAL** | 0,424 |

**Aucun étage n'éteint le signal.** Il n'y a pas de rupture de transmission — donc pas de
« porte sensorielle éteinte », pas d'« écrasement par la faim dans `integrateur_bio` ».
`pensee_bio` **amplifie** même le contraste (0,0050 → 0,0235).

## Confirmation au niveau du GESTE — 5 cerveaux

Distance des politiques (variation totale sur les 7 actions jouables), avec plancher :

| Cerveau | d_politique | plancher | rapport | action préférée res / mur |
|---|---|---|---|---|
| A_g11 | 0,0117 | 0,0060 | **1,96×** | droite / droite |
| A_g22 | 0,0691 | 0,0169 | **4,09×** | ramasser / ramasser |
| A_g44 | 0,0080 | 0,0023 | **3,53×** | avancer / avancer |
| A_g111 | 0,0104 | 0,0025 | **4,08×** | ramasser / ramasser |
| A_g144 | 0,0271 | 0,0059 | **4,58×** | ramasser / ramasser |

**5 cerveaux sur 5 : le signal dépasse le plancher.** La politique DIFFÈRE selon ce que
l'agent a en face.

## Le vrai défaut : le signal est RÉEL mais NÉGLIGEABLE

Le problème n'est pas l'existence du signal, c'est son **amplitude**.

- `d-prime` de **0,42 à 0,61** à tous les étages. **d' < 1 = nuages confondus.** Les deux
  classes se distinguent en moyenne mais se recouvrent presque entièrement tick par tick.
- L'écart le plus fort sur une action vaut **±0,0058** de probabilité (A_g11). Autrement
  dit : voir une pomme plutôt qu'un mur change la probabilité de `ramasser` de
  **14,44 % à 15,00 %**.
- **L'action préférée est LA MÊME dans les deux cas sur 5/5 cerveaux.** Le signal ne
  franchit jamais le seuil de l'argmax.

C'est cohérent avec le taux de saisie mesuré en jeu : à 15 % de probabilité par tick,
face à une ressource, on saisit ~10 % des occasions. **Le comportement observé est
exactement ce que prédit cette politique.** Il n'y a rien d'inexpliqué.

### Le cas A_g22 est l'exception qui éclaire

`ramasser` à **64,5 % / 71,4 %** — une politique dégénérée qui joue une action à
deux tiers du temps, et dont l'écart va dans le **mauvais sens** (moins de `ramasser`
face à une ressource que face à un mur). Entropie 1,10 contre 1,94 au maximum. Cet agent
n'explore plus ; il n'a pas appris à saisir, il a appris à marteler.

## Deux erreurs de mesure commises et corrigées

1. **Le régime « bio réel » était un leurre.** Vérifié après coup : **0 dimension sur 41
   ne variait** entre captures (`std < 1e-6` partout, satiété constante à 0,1667). La
   sonde ne fait tourner ni `step_metabolisme` ni les sens, donc le moteur bio est gelé.
   Les colonnes « bio réel » du premier tableau ne mesuraient rien de plus que « bio
   gelé ». **Seul le régime gelé est valide** — il isole le canal visuel, ce qui reste
   la question posée.
2. **Softmax sur 8 logits au lieu de 7.** `ACTION_DEMANDER` (indice 7) est masquée à
   `-inf` en jeu (invariant v30.0) ; la softmaxer produisait une entropie de **2,07**,
   au-dessus du maximum théorique `ln(7) = 1,9459` — impossible, et c'est ce qui a
   révélé l'erreur. Toutes les valeurs de ce document sont post-correction.

## Ce que cela ferme et ce que cela ouvre

**Fermé** : le câblage perceptif. Il n'y a pas d'étage à réparer, pas de porte éteinte,
pas d'écrasement viscéral. Toute piste « le signal n'arrive pas » est réfutée.

**Ouvert** : pourquoi un signal qui arrive ne devient-il jamais décisif ? L'écart
perceptif existe mais reste **deux ordres de grandeur sous ce qu'il faudrait** pour
changer l'action choisie. La question n'est plus « où le signal se perd » mais **« qu'est-ce
qui empêche un écart de 0,006 de croître »**.

Trois suspects, non testés :

1. **Le crédit d'apprentissage.** `Gradient causal v41.31 : 176/400 ticks crédités (44 %)`.
   Un tick où l'agent saisit une ressource est-il crédité davantage qu'un tick neutre ?
2. **La saturation de `ramasser`.** Le cas A_g22 suggère qu'une action peut se figer sans
   jamais être conditionnée. Mécanisme : distillation C2→C1 sur un crédit non conditionnel ?
3. **Le bénéfice différentiel.** Piste déjà nommée en v41.28 : *« si le gaspillage persiste,
   le levier suivant est le BÉNÉFICE — un geste qui ne change rien devrait n'apprendre
   rien »*. Jamais implémentée, jamais mesurée.

## Reproduction

```bash
PYTHONPATH=src python -m naulthene.instruments.sonde_conditionnement \
    brains/26082026_v4132_AB3_cursus/A_g11.brain --env MiniGrid-Empty-8x8-v0 --ticks 3000
PYTHONPATH=src python brains/26082026_v4132_AB3_cursus/sonde_politique.py \
    brains/26082026_v4132_AB3_cursus/A_g11.brain
```
