# Campagne 25/08/2026 — Le clipping se déclenche-t-il ?

## Ce qu'on cherchait

Le plafond de `‖Σg‖` (~0,82) est identique dans les trois bras du thrashing. Hypothèse :
`clip_grad_norm_(…, max_norm=1.0)` sature à chaque nuit.

## 🔴 La mesure précédente était une tautologie

J'avais lu « norme globale 0,9315, soit 93 % du plafond ». **Sans valeur** : l'ordre est
`backward()` → `clip` → `step()`, et la sonde lit les `.grad` **après**. La valeur était
déjà écrasée, **bornée à 1,0 par construction**.

**Correctif** : `clip_grad_norm_` **retourne** la norme avant écrêtage. On l'intercepte le
temps de l'appel (restauration en `finally`).

## Résultat — 12 jours, graine 11

| | |
|---|---|
| **Nuits clippées** | **12 / 12 (100 %)** |
| Norme brute moyenne | **2,8193** (×2,8 le plafond) |
| Norme brute maximale | **6,6533** (×6,7) |
| Facteur de division moyen | **0,4435** (tout ÷ ~2,3) |

| Part du budget BRUT | moyenne | min | max |
|---|---|---|---|
| corps (`integrateur_bio`) | **40,1 %** | 13,8 % | 66,1 % |
| décision (`tete_motrice`) | 10,0 % | 1,4 % | 31,4 % |
| **vue** (`porte_visuelle`) | **0,67 %** | 0,1 % | 1,8 % |

## ⚠️ La nuance décisive

`clip_grad_norm_` divise **toutes** les composantes par le même facteur — il ne change
**pas** les parts relatives.

| Le clipping explique | Il n'explique PAS |
|---|---|
| la faible **amplitude** des logits (÷2,3 par nuit) | le **déséquilibre** corps/vue (parts intactes) |
| le plafond de `‖Σg‖` identique dans les 3 bras | le **thrashing** (une division ne renverse aucune direction) |

**Le déséquilibre 60× est antérieur au clip** : il vient de la structure du signal
(`Bio` = 52,1 % de la dispersion), pas de l'optimiseur.

⚠️ **Ne pas relever `max_norm`** sans A/B : la norme brute atteint 6,65 certains jours.

## Fichiers

- `base.brain` — cerveau de départ
- `clipping.log` — le run complet, 12 jours
