# Campagne v41.34 — LE TRONC PERCEPTIF CONNECTÉ

**Lancée le 28/08/2026.** 20 graines appariées × 400 jours × 2 bras = **40 runs**,
**cursus complet** (pas de `--env-force`).

## La question

`_executer_c1_reflexe` contient `pensee_enrichie.detach()`. Cette ligne est présente dans
`colab.py` **depuis l'origine du projet** — jamais commentée, jamais justifiée, jamais
mesurée. C'est le dernier choix structurel du cœur dont personne ne connaît la raison.

Mesuré (3 pertes injectées séparément) :

| Couche | JEPA | ACTEUR | CRITIQUE |
|---|---|---|---|
| `porte_visuelle` | 0,033868 | **0,000000** | **0,000000** |
| `hippocampe` | 0,042690 | **0,000000** | **0,000000** |
| `analyseur` | 0,105406 | **0,000000** | **0,000000** |
| `integrateur_bio` | 0,000000 | 3,370580 | 4,332367 |

**Seul le JEPA sculpte la perception.** L'acteur et le critique travaillent sur une
représentation optimisée pour *prédire la dynamique*, jamais pour distinguer ce qui a de
la valeur.

## Pourquoi ça pourrait compter

Le bit de portage vaut **+0,325 de valeur** en contrefactuel pur (361 % du mouvement
typique de `V`), et pourtant le saut **réel** au moment d'une saisie ne vaut que
**+0,006**, contre +0,015 sur un tick banal. Le signal est noyé par le bruit de la vue
(±0,090/tick, non orienté) — parce que la perception n'a aucune raison d'apprendre à
taire ce qui ne vaut rien. C'est ce qui a réfuté le TD(0) (13ᵉ réfutation).

**Hypothèse à tester** : un signal de valeur atteignant `porte_visuelle` réduirait ce
bruit au profit du signal utile.

## Protocole

| | |
|---|---|
| **Bras A** | nominal — `.detach()` en place (comportement historique) |
| **Bras B** | `--tronc-connecte` — l'acteur et le critique rétropropagent jusqu'à la vue |
| Env | **cursus complet**, 15 niveaux |
| Graines | 11 → 222 (20, appariées) · 400 jours |

## Validations AVANT lancement

| Test | Résultat |
|---|---|
| Le gradient atteint la vue | `porte_visuelle` **0,000000 → 2,831270** |
| Rien d'autre ne bouge | `integrateur_bio` 5,244813 · `tete_motrice` 1,792821 · `cortex_prefrontal` 2,885004 — **identiques à la 6ᵉ décimale** dans les deux bras |
| A/A du bras nominal | **bit-identique**, δ = 0 |
| La variante atteint le module | `🔬 [VARIANTE] tronc perceptif CONNECTÉ` + assertion runtime |
| Pas d'ablation vide | la variable agit à **chaque tick de chaque niveau** — contrairement au bit de portage (§4), aucun prérequis de niveau |

## ⚠️ CE BRAS PEUT ÊTRE NUISIBLE, ET C'EST VOULU

Ce n'est **pas une correction, c'est une question**. Le `.detach()` protège peut-être
quelque chose de réel : sans lui, le gradient de l'acteur remonte dans un tronc
**récurrent** (`hippocampe` lit `memoire_precedente`), et les deux têtes se
rétropropagent dans les **mêmes** couches perceptives — c'est exactement la collision
C1/C2 mesurée en v41.32 sur `integrateur_bio`, étendue à quatre couches de plus. L'A/B
doit pouvoir dire que la variante est pire.

## Ce qu'on lira, dans l'ordre

1. **Le bruit perceptif** — `|V(t+1) − V(t)|` moyen doit BAISSER si l'hypothèse tient
   (référence : **0,0899** g11 · **0,1085** g44).
2. **Le contraste du crédit** — `|A| utile / |A| neutre` (référence : **1,275×**).
3. **Le d de Cohen du portage** — la perception aide-t-elle le critique ? (réf. **+1,43**).
4. **Le comportement** — niveau, maîtrise, énergie. Sur cursus complet, cette fois, donc
   le niveau *peut* juger.

⚠️ **AUCUN `t` AVANT LA FIN DES 40 RUNS.** Bonferroni obligatoire.

## Reproduction

```bash
brains/28082026_v4134_tronc/lancer.sh
```
