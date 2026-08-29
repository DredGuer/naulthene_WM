# 29/08/2026 — La dérive de représentation ne prédit pas la performance

> Quinzième réfutation. Non normatif — carnet d'enquête.
> Clôt la série `CIBLE_MOBILE_28082026_*` → `COURSE_29082026_*`.

## Pourquoi cette mesure plutôt qu'une autre

Deux suites étaient possibles après la mesure de la dérive : passer la sonde à 20 graines
pour obtenir un intervalle de confiance propre, ou enrichir la mesure avec d'autres axes
informatifs (`mur/libre`, `but devant/côté`).

**Les deux décrivent le phénomène plus finement sans tester s'il cause quoi que ce soit.**
C'est le piège que le projet a déjà payé plusieurs fois : mesurer une mécanique là où elle
est active prouve qu'elle marche, jamais qu'elle explique le blocage.

La corrélation, elle, est **falsifiable dans les deux sens** — et le dépôt a le précédent
qui valide la méthode : `maîtrise ~ énergie moyenne` donne **r = +0,710** (`t = +2,85`).
Quand un lien existe dans ces données, cette forme de mesure le voit.

## Protocole

Cohorte **v41.34, 20 cerveaux appariés** (n=20 immédiat, aucune campagne à lancer).
Chaque cerveau est vieilli de **12 nuits** uniquement pour mesurer sa vitesse de dérive ; la
performance corrélée est celle **déjà enregistrée dans son log de 400 jours**, jamais
recalculée — sinon on corrélerait un état avec la performance d'un autre état.

## Résultat

| Corrélation | `r` | `t` | seuil Bonferroni (3 métriques, df=18) |
|---|---|---|---|
| dérive ↔ **maîtrise** | **+0,1386** | +0,59 | 3,38 |
| dérive ↔ énergie | −0,1059 | −0,45 | 3,38 |
| dérive ↔ niveau atteint | −0,0506 | −0,21 | 3,38 |

**Aucune n'approche le seuil.** Et le signe de la première est **positif** : les graines qui
dérivent le plus maîtrisent légèrement *mieux*, l'inverse de la prédiction.

### Deux cas lisibles à l'œil nu

| Graine | dérive | maîtrise |
|---|---|---|
| **g111** | **2,87 °/nuit** (la pire) | **22,75 %** (parmi les meilleures) |
| **g211** | **0,62 °/nuit** (la plus stable) | **7,30 %** (parmi les pires) |

Le cerveau qui dérive **4,6× plus** maîtrise **3,1× mieux**. Si la dérive causait le
plafond, ces deux-là seraient inversés.

## Ce que cela ferme

La dérive **existe** — 0,42 °/nuit, alignement qui recule de 0,1051 à 0,0917, couplage
proie/prédateur : tout cela reste mesuré et documenté dans `COURSE_29082026_*.md`. Mais
elle **n'explique pas le blocage au niveau 4**.

C'était le maillon manquant, refusé comme supposition pendant deux jours. Il ne tient pas.

## Ce que cela ne dit pas

1. **Que la dérive est inoffensive.** Une corrélation nulle sur 20 graines n'exclut pas un
   effet non linéaire, ou un effet qui n'apparaîtrait qu'au-delà d'un seuil de dérive
   jamais atteint ici (l'étendue observée est 0,60–2,87 °/nuit).
2. **Que l'intervention architecturale serait inutile.** Elle n'est simplement **plus
   justifiée par cette mesure** — il faudrait une autre raison de la tenter.
3. **Que la corrélation implique la causalité**, dans un sens comme dans l'autre. Un `r`
   nul est un argument plus faible qu'un `r` fort, et il est ici cohérent avec l'absence de
   lien, pas une preuve d'absence.

## Ce qui reste

Le plafond au niveau 4 reste inexpliqué après **quinze réfutations**. Le seul prédicteur
mesuré à ce jour est **l'énergie** (`r = +0,710`, `t = +2,85`), et il pointe vers le
métabolisme — pas vers la géométrie, pas vers le gradient, pas vers la perception.

## Reproduction

```bash
PYTHONPATH=src python -m naulthene.instruments.sonde_correlation_derive
```

Données brutes : `brains/28082026_v4134_tronc/correlation_derive.json`.
