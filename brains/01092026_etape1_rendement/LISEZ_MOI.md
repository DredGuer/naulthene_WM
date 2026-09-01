# ÉTAPE 1 — le rendement mécanique tend-il le trajet ? (brique C, v41.48)

**Date de lancement** : 2026-09-01 · **Protocole écrit AVANT dépouillement.**

## La question

La brique C pondère le gradient d'acteur par le rendement mécanique, de façon
**asymétrique** (le succès stérile n'ancre rien, l'échec stérile reste puni). L'Étape 0 a
établi que **64,6 % du budget** est un travail à rendement nul ou quasi nul.

**Le juge de paix est la DIRECTIVITÉ** (longueur du trajet victorieux / plus court chemin
réel), fixée par l'utilisateur :

| Résultat | Verdict |
|---|---|
| directivité **< 6×** | ✅ succès — le goulot moteur cède |
| directivité **≥ 12×** | ❌ échec — l'inertie n'est pas captée par C1 |
| entre les deux | 🟡 à interpréter, sans sur-lecture |

## Le protocole

| Élément | Valeur |
|---|---|
| Bras | **ACTIF** (v41.48) vs **TÉMOIN** (`--sans-rendement`) |
| Graines | **20**, appariées : 11 · 22 · … · 222 |
| Jours | 100 par run |
| Environnement | `--env-force MiniGrid-SimpleCrossingS9N1-v0` |
| Total | 40 runs |

**Appariement** : la graine `gN` du bras ACTIF voit **le même monde** que la `gN` du
TÉMOIN (déterminisme vérifié depuis la v41.9).

**Un seul bras par mécanique** : `--rendement-symetrique` n'est **pas** activé ici — ce
serait une ablation confondue. Il fera l'objet d'une campagne séparée si l'Étape 1 réussit.

## Les contrôles déjà passés (voir `brains/01092026_AA_rendement/`)

δ_A/A = 0 sur les deux bras · les bras diffèrent · drapeau vérifié dans le module ·
3 nuits complètes sans erreur · formule vérifiée au banc unitaire.

## ⚠️ Ce que cette campagne NE peut PAS établir

1. **Un banc forcé ne prouve rien sur le cursus** (règle de mesure §6). `--env-force`
   court-circuite la promotion : le niveau reste à 1/15 **par construction**, donc
   « niveau atteint » est inopérant comme juge. C'est l'Étape 2 qui tranchera.
2. `SimpleCrossing` **n'a ni porte ni clé** : trois des quatre actions y sont stériles par
   construction. Le gain, s'il existe, peut être surestimé pour cette raison — sur un
   niveau à portes, `toggle` cesse d'être stérile.
3. **100 jours** est court. Un effet qui n'apparaîtrait qu'à 1 500 jours serait invisible.

## Vérifications prévues au dépouillement

| Vérification | Pourquoi |
|---|---|
| **Tautologie** | la directivité n'est définie que sur les VICTOIRES : un bras qui gagne moins a moins de points. Rapporter n_victoires à côté de chaque directivité |
| **Saturation du budget** | plafond arithmétique 27,0× sur cette carte |
| **Bras à 0 victoire** | directivité indéfinie — compter les graines perdues par bras |
| **Signe du succès** | une directivité qui baisse pendant que le succès s'effondre est un ÉCHEC, pas un gain (leçon du 01/09 : à λ=0,9 la directivité était la meilleure et le succès le pire) |
