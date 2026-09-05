# LE GRADIENT FANTÔME DE C2 — déforme-t-il le sol de C1 ?

**Protocole écrit AVANT le lancement** (05/09/2026). Campagne `05092026_detach_c2`.

## La question

L'[ablation propre de C2](../../docs/recherche/campagnes/ABLATION_C2_05092026_l_organe_muet.md)
a établi que **la VOIX de C2 est inerte** (δ maîtrise −1,375, `t` = −1,15, NS, n=20). Mais
elle a laissé une réserve explicite, écrite dans ses limites :

> ⚠️ **C2 tourne toujours** : seule sa *voix* est retirée de la fusion. Son gradient continue
> d'irriguer le tronc via `integrateur_bio`. Cette campagne ne dit **rien** de ce canal-là.

**Si ce gradient déforme la représentation, il agissait encore dans le bras ablaté** — et
« C2 est inerte » ne vaudrait que pour sa voix, pas pour l'organe entier.

## Pourquoi `--detach-c2` et NON `--sans-gradient-c2`

Le code l'écrit lui-même (`noyau.py` ~l. 5703) :

> *« Sans gradient, le critique cesse d'apprendre : ses estimations dérivent, donc les
> AVANTAGES qu'il fournit à l'acteur se dégradent. Ce bras mesure l'ALIGNEMENT du gradient,
> **JAMAIS la performance** — un score qui baisse ici ne prouve rien. »*

`--detach-c2` est la forme soignée : `_bio_pour_c2 = pensee_bio.detach()` (l. 1556). C2 **lit**
le corps pour évaluer et planifier, `cortex_prefrontal` **continue d'apprendre normalement**,
mais C2 ne **sculpte** plus `integrateur_bio` — la seule couche partagée. Seul C1 façonne
alors la représentation viscérale.

## ⚠️ Ce bras a DÉJÀ été mesuré, et il avait échoué

Campagne AB3 (26/08, n=20, **régime témoin**) : niveau `t` = **−0,70**, maîtrise
`t` = −1,93 ; son seul `t` significatif (ratio C2/C1) était une **tautologie**.

**Ce qui change ici** : le régime. AB3 tournait sous renormalisation (`gain_c1` clampé), dont
on sait depuis le 05/09 qu'elle **atrophie C1 chez 20 témoins sur 20** et masque cette
atrophie. Mesurer la collision C1/C2 sur un C1 qui s'atrophie n'isolait rien.
**Ce bras est le premier `--detach-c2` en régime libre.**

⚠️ **Prédiction honnête** : la probabilité que ce bras trouve un effet est **faible**. Il est
lancé parce que c'est la réserve que j'ai écrite moi-même dans le carnet précédent, pas parce
que j'attends un résultat.

## Le protocole

| Bras | `gain_c1` | Voix C2 | Gradient C2 → tronc | Runs |
|---|---|---|---|---|
| **LIBRE** (référence) | ≡ 1 | active | **actif** | **0** — réutilise `04092026_cursus_complet` |
| **LIBRE_DETACH** | ≡ 1 | active | **coupé** | 20 |

20 graines appariées (11 … 222) × 1500 jours · **20 runs neufs** · 6 en parallèle · ~4 h.

```bash
zsh brains/05092026_detach_c2/lancer.sh
```

## Les juges, posés d'avance

⚠️ **Bonferroni 3 métriques** ⇒ seuil `t` = **2,86**.

| Juge | Grandeur | Le gradient de C2 NUIT si | Il est NEUTRE si |
|---|---|---|---|
| **1. Maîtrise** | δ LIBRE_DETACH − LIBRE | δ > 0, `t` > 2,86 | δ ≈ 0 |
| **2. Niveau** | idem | δ > 0, `t` > 2,86 | δ ≈ 0 ⚠️ **probablement SATURÉ** |
| **3. Amplitude C1** | idem | δ > 0 significatif | δ ≈ 0 |
| **4. Garde-fou** | `gain_c1` | — | doit valoir **1,00** dans les deux bras |

⚠️ **Le juge 2 sera vraisemblablement saturé** : les 40 runs des campagnes libres précédentes
sont **tous au plafond du niveau 4**. Piège identifié le 05/09 sur l'ablation C2 — un `δ = 0`
y serait un **plafond**, pas une absence d'effet. **C'est le juge 1 qui portera la réponse**,
et le juge 3 qui dira si la représentation change.

## Interprétation prévue AVANT de voir les chiffres

| Résultat | Lecture |
|---|---|
| Juge 1 **positif** | le gradient de C2 **pollue** le tronc ⇒ « C2 est inerte » devient « C2 NUIT », et la refonte doit **d'abord** couper ce canal |
| Juge 1 **nul** | l'organe entier est neutre ⇒ la réserve du carnet précédent est **levée**, la refonte peut partir sur une base saine |
| Juge 1 **négatif** | le gradient de C2 **aide** malgré une voix inerte — le plus intéressant des trois, et le moins attendu |

## Pré-vol (fait avant lancement)

| Test | Résultat |
|---|---|
| Drapeau atteint (assertion runtime) | ✅ `[VARIANTE] detach asymétrique` |
| La lésion change le comportement | ✅ **4/5 grandeurs** divergent (H, JEPA, C1, C2) |
| `gain_c1` intact | ✅ **×1,00** |
| **A/A** (2 runs identiques, 40 j) | ✅ **BIT-IDENTIQUES** ⇒ **δ_A/A = 0,000000** |
| Harnais | ✅ `FLAGS` en **tableau zsh**, garde-fou `Jour 1500` (leçons du matin) |
