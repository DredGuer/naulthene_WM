# 29/08/2026 — L'agent n'est pas paralysé par le doute. Il est confiant dans l'erreur.

> Non normatif — carnet d'enquête. Ferme le chapitre « mécanique de décision »
> (entropie, logits, bornes), comme `CORRELATION_29082026_*` a fermé celui de la perception.

## [0] Une correction : je mesurais la mauvaise politique

La politique **jouée** est `voix_c1 + voix_c2` (`penser()`, l. 1405). Les 15 % publiés le
27/08 venaient des logits **bruts** de `_executer_c1_reflexe` — C1 seul, avant l'arbitrage.

| | entropie | P(action favorite) |
|---|---|---|
| logits **bruts** (C1 seul) — *ce qui avait été mesuré* | 1,9417 | **16,05 %** |
| **politique jouée** (C1+C2) — *ce que l'agent fait* | **1,8631** | **23,89 %** |
| PPO (60 runs) | 1,667–1,704 | 34,7–35,5 % |

**L'agent est nettement moins apathique que je ne l'ai écrit.** C2 apporte **+8 points de
décision**. Et le « plafond géométrique à 18 % » du 28/08 portait sur les logits bruts :
**la politique réelle le dépasse déjà** (23,9 %), parce qu'elle additionne une seconde voix.
Le plafond existe pour C1 seul, jamais pour l'agent.

## [1] Le `coeff_entropie` est acquitté

Norme du gradient sur `tete_motrice` :

| Cerveau | ‖grad avantage‖ | ‖grad entropie‖ | ratio |
|---|---|---|---|
| A_g11 | 0,170474 | 0,000751 | **0,44 %** |
| A_g44 | 0,025278 | 0,000266 | **1,05 %** |

Le terme d'entropie pèse **moins de 1 %** de l'incitation à agir. Il ne réprime aucune
spécialisation. Hypothèse réfutée.

## [2] L'écrêtage : un signal, sous le seuil, et une chaîne causale brisée

`gain_c1 = clamp(vigueur_min_c1(force) / amplitude_c1, 0,25 ; 4,0)` sature sur certains
cerveaux — **99,8 % des ticks sur g44**, 0 % sur onze autres.

| Corrélation (n=20) | `r` | `t` | seuil Bonferroni (5 corr., df=18) |
|---|---|---|---|
| écrêtage → maîtrise | **−0,4519** | −2,15 | 3,61 |
| **amplitude C1 → maîtrise** | **+0,4768** | **+2,30** | 3,61 |
| entropie → maîtrise | +0,2342 | +1,02 | 3,61 |
| **P(favorite) → maîtrise** | **−0,2868** | −1,27 | 3,61 |
| écrêtage → entropie | −0,0192 | −0,08 | 3,61 |

**Aucune ne passe.** Après quinze réfutations toutes sous `|r| < 0,21`, ces deux-là à ~0,46
sortent du lot — mais `t = 2,30` contre 3,61 reste **non significatif**, et rien ne sera
revendiqué là-dessus.

⚠️ **Les deux premières lignes sont le MÊME FAIT vu deux fois.** `écrêtage` et
`amplitude_C1` sont liés mécaniquement (`gain = vigueur / amplitude`, saturé à 4,0). C'est
**une** observation, pas deux indices convergents.

⚠️ **Et son sens n'est pas celui qu'on suppose.** `gain_c1` n'est pas produit par
l'optimiseur : il sature parce que **l'amplitude de C1 est faible**. Le résultat dit donc
« les cerveaux dont C1 est faible maîtrisent moins », **pas** « la borne nuit ». Une
corrélation ne peut pas distinguer les deux — **seule une ablation le pourrait**.

## [3] Ce qui brise la chaîne causale

Deux mesures contredisent le raisonnement qui avait mené jusqu'ici :

**L'écrêtage ne touche pas l'entropie** — `r = −0,0192` (`t = −0,08`). Or l'hypothèse était
« la borne ampute la certitude ». Elle ne l'ampute pas : elle limite l'amplitude interne de
C1, pas la distribution finale.

**Et P(action favorite) corrèle NÉGATIVEMENT avec la maîtrise** — `r = −0,2868`. Lisible
dans le tableau : g177 est le plus décidé (33,18 %) pour 18,23 % de maîtrise ; g133 est à
25,40 % pour **26,57 %**.

🔴 **L'agent n'est pas paralysé par le doute. Quand il se décide, il se décide souvent pour
la mauvaise action.** Être plus décidé n'aide pas — ce qui ruine l'idée que le manque de
décision est le problème.

## Ce que cela ferme

Le fossé avec PPO ne s'explique **pas** par la forme de la distribution : Naulthène joue à
1,83 d'entropie et 25 % de P(favorite), PPO à 1,68 et 35 %. Proches. Et pourtant 16 % contre
40 % de réussite.

**PPO ne réussit pas parce qu'il crie plus fort — il réussit parce qu'il pointe dans la
bonne direction.** L'échec est **qualitatif, pas quantitatif**.

Le chapitre « mécanique de décision » (entropie, amplitude des logits, bornes de gain) se
referme comme s'est refermé celui de la perception.

## Ce que cela n'autorise pas

**Aucune ablation de `GAIN_C1_MAX` sur ce seul critère.** Deux raisons : le signal ne passe
pas Bonferroni, et la borne haute est un correctif documenté — sans elle, la distillation
renforce C1 plus vite que C2 et le ratio **s'inverse à 0,21×** (mesuré sur 30 jours,
chantier v37.0). Retirer un garde-fou pour un `t = 2,30` réintroduirait un défaut connu.

Ce qu'il faudrait : **n ≥ 40 graines** pour trancher un `r` de cette taille, ou une ablation
directe qui, elle, distinguerait la cause de la conséquence.

## Reproduction

```bash
PYTHONPATH=src python -m naulthene.instruments.sonde_entropie_politique <brain>
PYTHONPATH=src python -m naulthene.instruments.sonde_ecretage_c1
```

Données : `brains/28082026_v4134_tronc/correlation_ecretage.json`.
