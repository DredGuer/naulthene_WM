# Le rollout survit-il au régime K8 ? — 07/09/2026

**Question** : les 8 époques par nuit (v41.62, +10,25 pt de maîtrise) ont-elles réparé
l'effondrement du rollout mesuré la veille sur le témoin ?

**Protocole** : `sonde_horizon_branches` sur les 20 `.brain` du bras `K8_NU`. Zéro run.

| | ratio h7/h1 médian |
|---|---|
| TÉMOIN (1 pas/nuit, 20 cerveaux) | 0,0293 |
| **K8_NU (8 pas/nuit, 20 cerveaux)** | **0,0118** |

🔴 **Non — le rollout reste effondré, et même un peu plus.** Les cerveaux ayant franchi le
niveau 5 ont un ratio **identique** aux autres (0,0129 contre 0,0117), et
`r(ratio, maîtrise) = **−0,08**`.

> **Les 8 époques ont amélioré le comportement sans rien réparer de la vision.** L'agent a
> été contraint à un réflexe plus efficace ; il n'a pas appris à mieux voir.

C'est ce résultat qui a décidé de coder **v41.63 (branches persistantes)** avant la tête
d'intention de C2 : la tête devait lire la `pensee_branche` finale, qui reste indistincte.
