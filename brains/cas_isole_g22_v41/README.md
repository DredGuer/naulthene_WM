# Cas isolé — g22 v41, le premier franchissement de palier du projet

> **Ne jamais supprimer ni écraser.** Ces deux `.brain` sont les seuls témoins
> matériels du premier déblocage du cursus depuis l'origine du projet.

Sauvegardé le 14 août 2026, après le run v41 de 2000 jours (commit `04080c4`).

## Contenu

| Fichier | Ce que c'est |
|---|---|
| `140820261703_V41_2000_g22_RMD.brain` | **LE cas** — niveau 4/15, 1011 victoires |
| `140820261703_V41_2000_g11_RMD.brain` | Le contrôle — niveau 1/15, 1266 victoires |
| `run_g22_2000j.log` | Journal complet des 2000 nuits de g22 |
| `run_g11_2000j.log` | Journal complet des 2000 nuits de g11 |

## Pourquoi ces deux-là ensemble

g11 est le **contrôle idéal** : il gagne **plus** que g22 (1266 contre 1011) et reste
bloqué au niveau 1. La paire isole donc ce qui distingue « gagner » de « progresser ».

| | g11 | **g22** |
|---|---|---|
| Niveau | 1/15 | **4/15** |
| Victoires | **1266** | 1011 |
| force planif. | 0,383 | **0,724** |
| ratio C1/C2 | 1,58× | **4,59×** |
| `okay` / `danger` | 420 / 676 | **426 / 161** |

La seule différence structurelle : g22 est le seul dont le bilan s'est **inversé**
(`okay` = 2,6 × `danger`). Tous les autres accumulent plus de danger que de succès.

## Les promotions de g22

```
jour 770 → niveau 2
jour 775 → niveau 3
jour 778 → niveau 4     puis PLUS RIEN pendant 1223 jours
```

Trois paliers en **8 jours** après 769 jours de plateau.

## ⚠️ La divergence est native

Postulat strictement identique aux autres graines. Pourtant, dès la **nuit 1**, g22
affiche `danger = 0,00` (les autres : 1,00) et gagne au **jour 2** (les autres : 6–7).
Au jour 50, l'écart de `danger` est de **38×**.

Voir `docs/ameliorations/CORRECTIFS_v41_ligne_de_flottaison.md` §10.3.

## Comment relire ce cerveau

```bash
PYTHONPATH=src python -m naulthene.instruments.irm_cerveau \
    --brain brains/cas_isole_g22_v41/140820261703_V41_2000_g22_RMD.brain
PYTHONPATH=src python -m naulthene.instruments.sonde_c1_c2 \
    --brain brains/cas_isole_g22_v41/140820261703_V41_2000_g22_RMD.brain
```
