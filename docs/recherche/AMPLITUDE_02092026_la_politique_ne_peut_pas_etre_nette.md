# L'AMPLITUDE — la politique ne peut pas être nette, par construction

**Date** : 2026-09-02 · **Nature** : lecture de code + réanalyse de données existantes
(**aucun run lancé**) · **n = 20 cerveaux** (cohorte AB3 du 26/08) + rejeu partiel (13/20).

> Consigné AVANT d'être discuté (Règle de Trace §4). Ce document pose une **hypothèse
> mécanique** et le test qui la tranche ; il ne prétend pas l'avoir démontrée.
> Agrégat machine : `brains/02092026_amplitude_politique/agregat.json`.

---

## 1. La question posée

L'utilisateur, le 02/09 : *« comment rendre enfin vraiment intelligents mes nouveaux
cerveaux ? »* — après 21 réfutations qui convergent toutes sur la même phrase :
**l'information est là, le réseau ne s'en sert pas** (v41.48, v41.49).

Question reformulée : **où, dans le chemin qui va des logits appris à l'action jouée, une
politique nette pourrait-elle être empêchée d'exister ?** Les 21 réfutations ont toutes
manipulé ce qui ENTRE (signal, information, crédit). Aucune n'a regardé ce qui SORT.

## 2. Ce que le code fait — lecture de `penser()` et `apprendre_journee()`

Trois faits, lisibles à [noyau.py:1416-1463](../../src/naulthene/cerveau/noyau.py#L1416-L1463)
et [noyau.py:1770-1937](../../src/naulthene/cerveau/noyau.py#L1770-L1937) :

**(F1) L'amplitude de C1 est ASSERVIE.** `gain_c1 = clamp(2,1 × f / amplitude_c1, 0,25, 4)`
puis `voix_c1 = logits × gain_c1`. Quoi que la tête motrice apprenne, sa voix est ramenée
à `2,1 × force_planification` **dans les deux sens** (v37.0-fix, v40.0 parité). Le clip
sature 99,8 % des ticks (v41.39).

**(F2) L'amplitude de C2 est FIXE.** `valeurs_simulees` est z-scoré inconditionnellement
(invariant v37.0 n°3) : amplitude ≈ 2,1 quelle que soit l'information que C2 porte, × `f`.

**(F3) La politique jouée est `voix_c1 + voix_c2`.** Son amplitude maximale est donc
`≈ 4,2 × f` si les deux voix s'accordent, moins sinon (accord mesuré : 2 à 34 %).

Conséquence arithmétique : `softmax` est invariante par translation mais pas par échelle.
Une plage de logits bornée à ~2,5-3 sur 7 actions borne `P(action favorite)` — c'est le
« plafond géométrique » de v41.35, mais il ne vient pas de `‖W‖` : **il vient du gain qui
renormalise `W` à chaque tick.** Aucun apprentissage ne peut le franchir.

**(F4) Une seule descente de gradient par nuit.** `apprendre_journee` calcule la perte
sur les ~400 ticks de la journée et fait **un** `optimizer.step()` ; `rever` en fait un
second (JEPA seul). Sur un run de 400 jours (152 043 pas d'environnement, le budget de la
ligne de base PPO), la tête motrice reçoit **400 pas d'optimiseur**. PPO (`n_steps=2048`,
`batch=64`, `n_epochs=10`) en reçoit **≈ 23 757** sur le même budget : **59×**. Le gradient
est de plus clippé à norme 1 **globalement**, JEPA compris.

## 3. Les chiffres bruts

### 3a. Amplitudes des 100 dernières nuits, 20 cerveaux, contre le banc du 30/08

| cerveau | C1 amp | C2 amp | gain C1 | accord | banc 30/08 | directivité |
|---|---|---|---|---|---|---|
| A_g66 | **0,799** | 1,600 | 1,55 | 33,9 % | **37,33** | 14,2 |
| A_g166 | 0,782 | 1,744 | 1,59 | 26,3 % | 31,00 | 16,4 |
| A_g133 | 0,472 | 1,588 | 2,57 | 23,9 % | 29,00 | 13,8 |
| B_g144 | 0,462 | 1,784 | 2,87 | 9,4 % | 28,67 | 14,7 |
| A_g122 | 0,515 | 1,547 | 2,27 | 16,2 % | 27,33 | 16,3 |
| A_g188 | 0,671 | 2,068 | 2,23 | 2,1 % | 20,67 | 13,9 |
| B_g211 | 0,501 | 2,462 | 3,31 | 13,1 % | 15,33 | 18,0 |
| A_g111 | 0,520 | 1,637 | 2,35 | 15,3 % | 15,00 | 14,8 |
| B_g188 | 0,474 | 2,298 | 3,19 | 16,6 % | 13,00 | 15,7 |
| A_g33 | 0,554 | 1,634 | 2,30 | 23,0 % | 11,00 | 19,2 |
| A_g77 | 0,664 | 1,667 | 1,89 | 7,5 % | 9,33 | 18,5 |
| A_g155 | 0,908 | 1,682 | 1,48 | 3,9 % | 7,67 | 18,1 |
| A_g222 | 0,335 | 1,776 | 3,31 | 27,7 % | 7,33 | 16,8 |
| A_g177 | 0,749 | 1,781 | 1,85 | 11,5 % | 3,33 | 19,2 |
| B_g11 | 0,325 | 1,708 | 3,51 | 12,2 % | 3,00 | 22,2 |
| B_g44 | 0,488 | 2,036 | 2,93 | 3,6 % | 2,33 | 22,8 |
| A_g144 | 0,437 | 1,832 | 2,99 | 12,5 % | 1,33 | 22,2 |
| A_g44 | 0,377 | 1,826 | 3,22 | 11,9 % | 1,33 | 22,8 |
| A_g11 | 0,431 | 1,797 | 2,92 | 4,7 % | 1,00 | 20,5 |
| B_g122 | 0,474 | 1,649 | 2,66 | 23,4 % | 0,00 | — |

| Prédicteur | `r` vs banc | `t` | `r` vs directivité | `t` |
|---|---|---|---|---|
| amplitude C1 | **+0,3715** | +1,70 | −0,3365 | −1,47 |
| amplitude C2 | −0,1569 | −0,67 | +0,0935 | +0,39 |
| gain C1 | **−0,4369** | −2,06 | +0,3939 | +1,77 |
| accord C1/C2 | **+0,4459** | +2,11 | −0,3939 | −1,77 |

Seuil Bonferroni (4 métriques, df = 18) : **2,88**. ❌ **Aucune ne passe.** Les signes sont
tous dans le sens de l'hypothèse (plus C1 est ample et moins il est amplifié
artificiellement, mieux le cerveau réussit), mais **ce n'est pas une preuve** — voir §4.

**Ce qui est constant, lui, est éloquent** : sur 20 cerveaux, **aucun** n'a une amplitude
C1 > 0,91 ni une amplitude C2 hors de [1,55 ; 2,46]. Tous vivent dans la même boîte.

### 3b. Le rejeu à instrument corrigé (13/20 au moment de l'écriture — INCOMPLET)

| Grandeur | Valeur |
|---|---|
| δ succès apparié (corrigé − 30/08) | **+0,59 pt**, `t = +0,31`, 7/13 favorables |
| δ directivité apparié | −0,15, `t = −0,22` |
| `r(directivité, succès)` rejeu | **−0,6792**, `t = −3,07`, n = 13 |
| même corrélation, mêmes 13 cerveaux, chiffres du 30/08 | −0,8096, `t = −4,57` |
| écarts individuels | A_g111 **+17,0 pt** · A_g166 **−10,7** · A_g188 −6,3 · A_g133 −5,3 |
| témoin aléatoire | **5,67 %** sur les 13 (invariant, comme prévu) |

Lecture provisoire : réintroduire la mémoire de travail ne change **rien en moyenne** mais
déplace des cerveaux individuels de ±10-17 points. La mémoire de travail n'est pas un
levier de compétence, c'est une **source de variance**. ⚠️ Ne pas conclure avant 20/20.

## 4. Les vérifications

| Vérification | Résultat |
|---|---|
| **Tautologie** — l'amplitude est-elle une mesure de victoire déguisée ? | Non : `gain_c1` et `amplitude_c1` sont lus dans les logs du **run** (v41.32, 1440 j), le succès au **banc** forcé du 30/08. Deux instruments, deux mondes |
| **Le banc du 30/08 est amputé** (v41.47) | Oui — les corrélations §3a sont contre un banc à mémoire nulle. À refaire contre le rejeu quand il sera complet |
| **Plage tronquée** | Oui, et c'est **le point** : amplitude C1 ∈ [0,33 ; 0,91] sur 20 cerveaux. Une corrélation sur une plage que le code interdit d'élargir ne peut pas être significative — c'est l'intervention qui tranchera, pas la corrélation |
| **L'ablation « C2 coupé = 0,0 pt » est-elle propre ?** | 🔴 **NON.** `c2_coupe` pose `force_planification = 0` ([banc_ablation.py:245-247](../../src/naulthene/instruments/banc_ablation.py#L245-L247)), donc `vigueur_min_c1(0) = 0`, donc `gain_c1 = 0,25` (borne basse). **Couper C2 divise aussi la voix de C1 par 6 à 14** (gain témoin 1,5-3,5 → 0,25). Les deux bras sont quasi uniformes ; leur égalité ne dit **rien** sur C2. L'ablation est **confondue par la parité v40.0**, introduite le 14/08, avant la campagne des 78 cellules |
| **v41.39 « P(favorite) corrèle négativement avec la maîtrise »** | Mesuré sur des cerveaux dont P(favorite) est bornée dans [15 ; 25] % par F1-F3. Même piège de plage tronquée que `maîtrise ~ énergie` à n=10 |
| **Le contrôle v41.31 (`GAIN_ACTEUR_CONTROLE = 2,6`)** teste-t-il F4 ? | Non — le code le dit lui-même : « Adam absorbe un facteur constant ». Multiplier la perte n'est pas multiplier le nombre de pas |

## 5. Les limites

1. **Tout est corrélationnel ou lu dans le code.** Rien ici n'est une mesure d'intervention.
2. Le banc de référence est celui du 30/08, amputé ; le rejeu est à 13/20.
3. Les invariants v37.0 (gain double sens, C2 normalisé inconditionnellement) ont été posés
   contre un bug réel — C2 écrasant C1 de 9,9 à 22× à cause de l'érosion. **Ce bug a été
   corrigé ailleurs** (myéline rafraîchie, plancher non-plafond, échelle relative — v37.0-fix
   3/4/5). Le gain peut être un correctif devenu orphelin, mais ça reste à montrer.
4. « C2 = 0,0 pt » n'est pas réfuté ici : il est **non établi**. C2 peut très bien être
   inutile ; le banc ne l'a simplement jamais mesuré proprement.

## 6. Ce que cela ferme, ce que cela laisse ouvert

**Fermé** : l'idée que le plafond géométrique vient de `‖W‖` (v41.35). Il vient du gain.

**Ouvert, et c'est le test à faire** — un banc forcé `SimpleCrossingS9N1`, 20 graines
appariées, 100 jours, **critères fixés avant le run** (entropie de la politique jouée
< 1,75 ; succès moyen > 25 % ; directivité médiane < 10×) :

| Bras | Ce qui change | Ce que ça teste |
|---|---|---|
| TÉMOIN | rien | — |
| **A — voix libre** | `gain_c1 ≡ 1,0` : C1 parle à l'amplitude qu'il a **apprise** ; C2 inchangé | F1 — le gain est-il ce qui empêche la netteté ? |
| **B — budget** | K passes de minibatch par nuit sur la journée (avec ratio d'importance clippé, sinon c'est du off-policy nu), K dérivé du nombre d'épisodes clos dans la journée — jamais posé | F4 — 59× moins de pas d'optimiseur est-il le goulot ? |
| **C — C2 coupé, C1 intact** | `force = 0` **et** `gain_c1 ≡ 1,0` | refaire l'ablation de C2 sans confondre |

Trois bras, une mécanique par bras (règle §6.2), un témoin qui garde le sens et ne coupe
que la mécanique (§6.3). Le drapeau doit être relu **dans** `penser()` par assertion (§6.4).

**Mise à jour du 02/09, soir** : le bras A est **codé** (`--gain-c1-libre`, v41.50), A/A passé
(témoin bit-identique au code d'avant), protocole écrit dans
`brains/02092026_brasA_voix_libre/LISEZ_MOI.md`. Deux corrections d'instrument au passage :
`entropie_jouee` dans le JSON du banc, et la force de planification du banc — **figée à 0,5
jusqu'ici**, donc le témoin y était renormalisé à 1,05 d'amplitude quelle que soit sa force
vécue — lue désormais dans `acceptation()` du cerveau (`--force 0.5` = protocole historique).
Observation sur un nouveau-né : témoin à `gain ×0,25-0,45` — à `f ≈ 0`, le gain **étouffe**
C1 dès le premier jour, il ne l'amplifie pas.

⚠️ Le bras A retire un mécanisme, il n'en ajoute aucun : il est conforme au dogme. Le bras
B ajoute un nombre — il n'est acceptable que si K est **dérivé** (épisodes clos, ou arrêt
quand la perte cesse de baisser), et il doit être instrumenté (`Apprentissage_Pas_Nuit`).
