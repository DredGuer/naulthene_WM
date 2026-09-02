# LE REJEU À INSTRUMENT CORRIGÉ — la directivité survit, affaiblie

**Date** : 2026-09-02 · **n = 20/20** · **Lecture seule, aucun entraînement** ·
**Protocole écrit AVANT dépouillement** (`brains/02092026_rejeu_banc_corrige/LISEZ_MOI.md`)
· **Script d'analyse écrit avant la fin de la campagne** (`depouiller.py`, à n=15).

---

## 1. La question posée

Le 01/09, un défaut d'instrument a été trouvé : la sonde de banc lisait la mémoire de
travail en `penser()[1]` (la VALEUR, un scalaire) au lieu de `[4]`, et un garde-fou la
rejetait **en silence**. Tous les chiffres de banc des 30-31/08 décrivaient donc un agent
**sans mémoire de travail ni contexte épisodique**.

Deux questions, posées avant de mesurer :

1. `r(directivité, succès) = −0,8225` — **le seul prédicteur significatif jamais trouvé
   sur ce dépôt** — survit-il, recule-t-il, ou se renforce-t-il ?
2. La réintroduction du contexte mnésique suffit-elle, sur certaines graines, à structurer
   la persistance d'action **sans rien modifier au code** ?

## 2. Le protocole

| Élément | Valeur |
|---|---|
| Cohorte | les **20** cerveaux de `brains/30082026_plancher_n20/agregat.json`, fichiers identiques |
| Source | `brains/26082026_v4132_AB3_cursus/*.brain` |
| Environnement | `MiniGrid-SimpleCrossingS9N1-v0`, **300** épisodes, graines de carte appariées (`--graine 90210`) |
| Instrument | `sonde_plancher_geometrique` corrigé (`penser()[4]` + garde-fou **bruyant**) |
| Code | worktree figé à **`2d69b40`** (v41.47) : `DIM_VECTEUR_BIO = 42`, donc **aucune greffe** des cerveaux du 26/08 |
| Écriture | aucune — les `.brain` sont lus depuis une COPIE |

⚠️ **Une première passe a été JETÉE** (`_invalide_v4149/`, 14 fichiers) : elle tournait sur
v41.49 (`DIM_VECTEUR_BIO = 44`), donc greffait deux colonnes d'élan fraîchement initialisées
sur des cerveaux qui n'en avaient jamais eu. **Deux variables changeaient au lieu d'une.**

## 3. Les chiffres bruts

| cerveau | succ 30/08 | succ rejeu | δ | dir 30/08 | dir rejeu | δ | n victoires |
|---|---|---|---|---|---|---|---|
| A_g66 | 37,33 | **40,00** | +2,67 | 14,21 | 14,92 | +0,71 | 120 |
| A_g111 | 15,00 | **32,00** | **+17,00** | 14,83 | 14,50 | −0,33 | 96 |
| A_g133 | 29,00 | 23,67 | −5,33 | 13,83 | 15,67 | +1,83 | 71 |
| A_g122 | 27,33 | 22,67 | −4,66 | 16,33 | 16,46 | +0,13 | 68 |
| B_g144 | 28,67 | 22,00 | −6,67 | 14,67 | 16,96 | +2,29 | 66 |
| A_g166 | 31,00 | 20,33 | **−10,67** | 16,42 | 16,50 | +0,08 | 61 |
| B_g11 | 3,00 | 20,33 | **+17,33** | 22,17 | 16,83 | −5,33 | 61 |
| B_g211 | 15,33 | 16,33 | +1,00 | 18,04 | 18,67 | +0,63 | 49 |
| A_g188 | 20,67 | 14,33 | −6,34 | 13,92 | 17,08 | +3,17 | 43 |
| A_g222 | 7,33 | 13,67 | +6,34 | 16,79 | 18,75 | +1,96 | 41 |
| A_g33 | 11,00 | 13,67 | +2,67 | 19,17 | 18,00 | −1,17 | 41 |
| A_g77 | 9,33 | 9,33 | 0,00 | 18,54 | 19,29 | +0,75 | 28 |
| A_g155 | 7,67 | 8,00 | +0,33 | 18,08 | 20,92 | +2,84 | 24 |
| A_g177 | 3,33 | 6,67 | +3,34 | 19,21 | 16,00 | −3,21 | 20 |
| B_g188 | 13,00 | 6,33 | −6,67 | 15,67 | 16,83 | +1,17 | 19 |
| A_g44 | 1,33 | 3,67 | +2,34 | 22,75 | 22,08 | −0,67 | 11 |
| B_g44 | 2,33 | 2,00 | −0,33 | 22,83 | 23,58 | +0,75 | 6 |
| A_g144 | 1,33 | 1,33 | 0,00 | 22,25 | 16,83 | −5,42 | 4 |
| A_g11 | 1,00 | 1,00 | 0,00 | 20,50 | 18,67 | −1,83 | 3 |
| B_g122 | 0,00 | 0,33 | +0,33 | — | 26,25 | — | **1** |

### Les corrélations

| Prédicteur | `r` | `t` | `r²` | Verdict (Bonferroni 3 métriques, df=18 : **2,88**) |
|---|---:|---:|---:|---|
| **Directivité** | **−0,6794** | **−3,93** | **0,462** | ✅ **SIGNIFICATIF** |
| Maîtrise en run | +0,3721 | +1,70 | 0,138 | non significatif |
| `dim_bus` | −0,1766 | −0,76 | 0,031 | non significatif |

### Les écarts appariés (rejeu − 30/08)

| Grandeur | δ moyen | `t` | favorables |
|---|---:|---:|---|
| Succès | **+0,63 pt** | +0,40 | 10/20 |
| Directivité | −0,09× | −0,16 | 12/19 |

## 4. Ce que ça établit

**(1) La directivité SURVIT — c'est toujours le seul prédicteur significatif du dépôt.**
`r = −0,68`, `t = −3,93`, au-dessus du seuil de Bonferroni. Elle reste, et de loin, le
meilleur prédicteur : **46 % de la variance** contre 14 % pour la maîtrise en run.

**(2) 🔴 MAIS ELLE EST AFFAIBLIE, ET SA ROBUSTESSE A CHANGÉ DE NATURE.**

| Test | 30/08 (amputé) | 02/09 (corrigé) |
|---|---|---|
| global | −0,8225 (`t` = −5,96) | **−0,6794** (`t` = −3,93) |
| **sans les 4 extrêmes** | **−0,789** (`t` = −4,63) ✅ | **−0,478** (`t` = −2,04) ❌ **NS** |
| variance expliquée | 68 % | **46 %** |

Le 31/08, la survie au retrait des 4 extrêmes était **l'une des trois vérifications
avancées pour établir le résultat**. Elle ne passe plus. La corrélation est donc
**davantage portée par ses extrêmes** qu'on ne le croyait : elle sépare bien les cerveaux
très directifs des cerveaux très browniens, mais elle discrimine mal **au milieu de la
distribution**, là où vivent la plupart des cerveaux.

⚠️ Ce point a été **consigné à n=15, avant la fin de la campagne** (voir `LISEZ_MOI.md`),
précisément pour qu'il ne puisse pas être découvert après coup puis minimisé.

**(3) La mémoire de travail n'est pas un levier — c'est une source de VARIANCE.**
δ moyen **+0,63 pt** (`t` = +0,40, 10/20 favorables) : rien. Mais individuellement,
**A_g111 gagne 17,0 points**, **B_g11 en gagne 17,3**, et **A_g166 en perd 10,7**. Rendre
sa mémoire à l'agent le déplace fortement — dans les deux sens, sans direction moyenne.

**(4) L'ordre des cerveaux est bouleversé.** B_g11 passe de 3,00 % (19ᵉ) à 20,33 % (7ᵉ) ;
A_g166 passe de 31,00 % (3ᵉ) à 20,33 %. **Tout classement de cerveaux établi sur les
chiffres du 30-31/08 est caduc.**

## 5. Les vérifications

| Vérification | Résultat |
|---|---|
| **Témoin aléatoire** | **5,67 %** (17/300) sur les **20** runs — invariant strict, il ne passe pas par le code corrigé. L'instrument est sain |
| **Saturation du budget** | plafond arithmétique 27,0× ; pire cerveau **26,25×** (B_g122) ; **0 sur 20** au plafond |
| **Tautologie** | **aucun** cerveau à zéro victoire cette fois (le 30/08, B_g122 en avait zéro) — la directivité est définie partout |
| **B_g122 : 1 seule victoire** | sa directivité (26,25×) repose sur **un** épisode et frôle le plafond. En retirant les cerveaux à moins de 3 victoires : `r = −0,6676` (`t` = −3,70, n=19) — **le résultat ne dépend pas de ce point** |
| **Retrait des 4 extrêmes** | 🔴 **ne survit plus** (voir §4.2) |
| **Une seule variable a changé** | oui — worktree figé v41.47, aucune greffe. La passe qui greffait a été jetée |

## 6. Les limites

1. **Banc forcé** : ne prouve rien sur le cursus (règle §6). Le niveau reste à 1/15 par
   construction.
2. **Corrélationnel.** Aucune causalité n'est établie — et v41.47 a montré que la seule
   intervention jamais tentée sur cette variable (l'inertie, λ=0,9) donnait la **meilleure**
   directivité de la campagne avec le **pire** succès. La directivité pourrait rester un
   **symptôme** de la compétence, non son levier.
3. Politique **figée** (`eval()`) : on mesure ce que ces cerveaux savent déjà faire.
4. Ces cerveaux datent du 26/08 (v41.32) : ni rendement (v41.48), ni élan (v41.49). C'est
   **voulu** — on fige la référence historique.
5. `--force` n'a pas été passé : le banc a tourné à `force_planification = 0,5` figée,
   comme au 30/08. Le défaut `acceptation()` introduit en v41.50 n'est **pas** dans ces
   chiffres — c'est ce qui les garde comparables au 30/08.

## 7. Ce que ça ferme, ce que ça laisse ouvert

**Fermé** : la réserve d'instrument du 01/09. Les chiffres de banc sont de nouveau
utilisables, et le **sens** des conclusions du 30-31/08 tient (la compétence est réelle,
l'aléatoire reste à 5,67 %, la directivité prédit toujours). Les **valeurs**, elles, sont
remplacées par celles de ce document.

**Requalifié** : `r(directivité, succès)` passe de « premier prédicteur significatif,
68 % de la variance, survit au retrait des extrêmes » à **« prédicteur significatif,
46 % de la variance, porté par ses extrêmes »**. Les README et `CLAUDE.md` doivent le dire.

**Ouvert** : la directivité est-elle une **cause** ou un **symptôme** ? Le bras A
(`--gain-c1-libre`, v41.50) n'en dépend pas : son juge n°1 est l'**entropie jouée**, une
grandeur que ce document ne touche pas.
