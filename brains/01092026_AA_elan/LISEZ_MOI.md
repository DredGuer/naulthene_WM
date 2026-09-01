# A/A + validation d'implémentation — brique B (ancrage cinématique, v41.49)

**Date** : 2026-09-01 · **Avant toute campagne.**

## Ce qui est validé

| Contrôle | Résultat |
|---|---|
| **A/A témoin** (`--sans-elan`, 2 réplicats) | ✅ **δ = 0** |
| **A/A bras actif** (2 réplicats) | ✅ **δ = 0** |
| **Les deux bras DIFFÈRENT** | ✅ (le test qui avait démasqué le doublon de la brique C) |
| **Drapeau atteint le module** | ✅ assertion runtime, message imprimé 1× |
| **Cerveau NEUF** — 3 nuits | ✅ 0 erreur |
| **GREFFE d'un `.brain` v41.33** (42 → 44 dims) | ✅ `199 → 202` dims, **acquis préservés**, 2 nuits complètes, 0 erreur |
| **Le signal PORTE de l'information** | ✅ amplitude **0,167–0,211** (pas une dimension morte) |

⚠️ La greffe a été validée sur une **nuit complète**, pas seulement sur des ticks : c'est
l'exigence posée après le bug v32.0, où le crash ne survenait ni au chargement ni pendant
la journée, mais à la première `executer_nuit`.

## La demi-vie, dérivée du monde (arbitrage utilisateur)

MiniGrid impose `max_steps = 4·n²` sur ces grilles, donc `√(max_steps)/2` restitue le
**côté** de la carte. Vérifié sur quatre environnements :

| Environnement | `max_steps` | grille | demi-vie dérivée |
|---|---|---|---|
| `Empty-5x5` | 100 | 5×5 | **5,00** |
| `SimpleCrossingS9N1` | 324 | 9×9 | **9,00** |
| `Empty-16x16` | 1024 | 16×16 | **16,00** |
| `DoorKey-6x6` | 360 | 6×6 | 9,49 |

La demi-vie est donc littéralement **la longueur d'une traversée**. Aucun chiffre posé —
même précédent que la patience (v41.30) et la stagnation (v41.43).

## Le référentiel : ÉGOCENTRIQUE (arbitrage utilisateur)

`avance` = projection du déplacement sur l'axe du regard · `dérive` = projection sur la
normale. Cohérent avec `DIM_PRESSION` (v41.12 : « les directions tournent avec l'agent,
jamais absolues »). Un Δ absolu aurait obligé le réseau à apprendre **quatre** règles au
lieu d'une, « je viens d'avancer » s'encodant différemment selon la direction cardinale.

**Neutre à 0,5 sur les deux dims**, jamais 0,0 — 0,0 signifierait « je recule à pleine
vitesse ». Même piège que la clinotaxie (v32.0), la thermoception (v41.11) et le rappel
marquant (v36.0).

## Le décalage d'un tick est VOULU

`etat_courant()` est lu **avant** la décision, `observer()` appelé **après** `env.step`.
L'agent décide donc en connaissant le mouvement du tick **précédent** — ce qui est
exactement l'information utile : « je VIENS d'avancer » doit être su AVANT de choisir.
C'est l'inverse de la nociception (v41.25), où la chaleur devait être relue APRÈS le pas
parce qu'elle facture là où le corps est ARRIVÉ.

`etat_courant()` est **séparé** de `observer()` et sans effet de bord : la v41.25 a payé
cher la confusion inverse (`lire_thermoception` écrivait son état, donc un second appel
divisait par deux la clinotaxie du tick suivant).

## Mesure en run (3 jours, graine 11, `Empty-5x5`)

avance moyenne **0,538 · 0,533 · 0,532** (neutre 0,5), amplitude **0,185 · 0,167 · 0,180**.
Le signal est légèrement en avant du neutre et **varie** — ce n'est pas une dimension morte.

## ⚠️ Ce qui n'est PAS démontré

Aucune utilité. Ni directivité, ni maîtrise, ni autocorrélation motrice **après**
apprentissage. La cible reste `P(avancer|avancer)/P(avancer)`, mesurée à **0,9959** avant.
