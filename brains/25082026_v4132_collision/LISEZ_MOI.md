# Campagne 25-26/08/2026 — La collision C1/C2 : trois ablations du gradient (AB1 · AB2 · AB3)

> Compte rendu : [`docs/recherche/enquetes_closes/REFUTATIONS_23082026_trois_chantiers_avant_la_premiere_ligne.md`](../../docs/recherche/enquetes_closes/REFUTATIONS_23082026_trois_chantiers_avant_la_premiere_ligne.md)
> §4quindecies (« le thrashing est expliqué — la collision C1/C2 dans `integrateur_bio` »)
> et suivants. LISEZ_MOI écrit **a posteriori** le 02/09/2026, à partir de ce document et des
> logs — pas un protocole écrit avant le run.

## Ce qu'on cherchait

Le thrashing du gradient d'acteur (alignement 0,3966 contre 0,3536 pour une marche
aléatoire) venait-il de la **collision** entre le gradient de C1 et celui de C2 sur les poids
partagés ? Trois ablations sur banc de sonde, **une seule graine (g11), 12 jours**, cerveau
de départ `base.brain` (niveau 4).

| Bras | Drapeau | Ce qui est coupé |
|---|---|---|
| **AB1** — gradient de C2 coupé | `--sans-gradient-c2` | `valeurs_tensor` détaché avant la perte critique ; **forward de C2 intact** (il pèse toujours dans l'arbitrage) |
| **AB2** — sans masquage causal | — | le masquage causal du gradient d'acteur (v41.31) |
| **AB3** — detach asymétrique | — | seule la rétropropagation de C2 vers le **tronc partagé** ; C2 continue d'apprendre |

Chaque drapeau relu par assertion dans le module nommé (sortie
`🔬 [ABLATION] gradient de C2 COUPÉ — forward intact`) — règle §6.4.

## Ce qu'il y a dans ce dossier

| Fichier | Contenu |
|---|---|
| `base.brain` | point de départ commun — **bit-identique** à `../23082026_v4132_discrimination/N4_g11.brain` et à `../25082026_v4132_thrashing_pisteC/base.brain` (vérifié `cmp`, 02/09) |
| `AB1_sans_gradient_c2.log` | bras AB1 |
| `AB2_sans_masquage.log` | bras AB2 |
| `AB3_detach_asymetrique.log` | bras AB3 |

⚠️ Pas de `.brain` d'arrivée, pas de JSON d'agrégat : les chiffres ne sont que dans les logs
et dans le document. Antérieur à la Règle de Trace (31/08).

## Le résultat, en une ligne

| Bras | alignement final | `‖Σg‖` final | grad/jour sur `tete_motrice` |
|---|---|---|---|
| Témoin | 0,3428 | 0,8219 | 0,1998 |
| **AB1** | **0,6751** (+0,3323) | 3,8388 (×4,7) | 0,4739 (×2,37) |
| AB2 | 0,5879 | 0,5571 | 0,0790 |
| AB3 | 0,4298 (+25 %) | 1,8674 | 0,3621 |

AB1 double l'alignement mais tue C2 ; AB2 réfute la piste B (le masquage **concentre**, il
ne perturbe pas) ; AB3 est « à moitié concluant » et devient la mécanique **v41.32**, portée
au cursus complet dans `../26082026_v4132_AB3_cursus/` — où elle ne change **rien**
(niveau −0,10, `t = −0,70`, n=20). Dixième réfutation.
