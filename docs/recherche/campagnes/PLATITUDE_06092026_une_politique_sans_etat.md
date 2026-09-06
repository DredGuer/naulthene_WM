# LA PLATITUDE DE C1 — une politique dictée par des biais, pas par l'état

**Date** : 2026-09-06 · **Statut** : ✅ **MÉCANISME ÉTABLI**, avec **témoin PPO** ·
**40 cerveaux × 1500 jours** · coût : **zéro run** (hors témoin PPO, ~10 min).

> Suite directe de [ROLLOUT_06092026](ROLLOUT_06092026_le_trou_noir_du_reflexe.md), qui avait
> mesuré qu'il faut **doubler la norme** de `pensee_bio` pour que C1 change d'avis dans 13 %
> des cas. Question posée par l'utilisateur : **qu'est-ce qui anesthésie C1 ?**

---

## 1. Le mécanisme — la variance est au mauvais endroit

La variance des logits se décompose en deux parts :

- **inter-actions** : variance des logits **moyens** entre les 7 actions → le **biais structurel**
- **intra-temps** : variance temporelle d'un logit donné → la **réponse à l'état courant**

| | Naulthène (40 cerveaux) | **PPO** (même carte, 97,27 %) |
|---|---|---|
| var inter-actions | 0,525 | 0,582 |
| var intra-temps | **0,104** | **9,578** |
| **ratio inter / intra** | **3,91** (médiane 2,71) | **0,06** |
| σ temporel d'un logit | **0,108** | **2,923** |
| marge des logits moyens | 0,148 | 0,012 |
| entropie | **1,930** (max 1,946) | **0,618** |
| argmax change d'un tick au suivant | 12,2 % | 21,6 % |
| actions distinctes jouées | **2,3 / 7** | 3 / 7 |

🔴 **Le ratio est inversé d'un facteur 60**, et le σ temporel d'un facteur **27**.

> **Chez PPO, la décision est dictée par l'état courant. Chez Naulthène, elle est dictée par
> des biais moyens que les fluctuations de l'état ne franchissent presque jamais.**
>
> **38 cerveaux sur 40** ont `inter > intra`.

### Le paradoxe apparent, et sa résolution

Naulthène a une entropie de **1,930 sur un maximum de 1,946** — sa politique est à **99 % de
l'uniforme** — et pourtant son argmax est figé sur **2 actions**.

Ce n'est pas contradictoire : les logits sont **proches en moyenne** (donc softmax plat, donc
entropie haute) mais leur **ordre** ne change pas, parce que chaque logit **bouge peu dans le
temps** (σ = 0,108) devant l'écart qui les sépare (0,148).

**Naulthène est indécis ET figé. PPO est décidé ET réactif.** L'entropie ne mesure pas ce
qu'on croyait : elle dit la platitude du softmax, jamais la réactivité de la politique.

### Pourquoi 8 % de perturbation ne suffit pas — le calcul

Sur `LIBRE_g11` : marge argmax/2ᵉ = **0,392** ; norme des lignes de `tete_motrice` = 0,648.

| Perturbation de `pensee_bio` | Variation d'un logit | Fraction de la marge |
|---|---|---|
| 5 % | 0,0069 | 1,8 % |
| **8,12 %** (la séparation des 8 futurs) | **0,0111** | **2,8 %** |
| 25 % | 0,0343 | 8,8 % |
| 100 % | 0,1373 | 35,0 % |

**Même en doublant la norme de la pensée, on n'atteint que 35 % de la marge.** La zone morte
est purement géométrique.

## 2. Les trois hypothèses mécaniques testées

| Hypothèse | Verdict |
|---|---|
| **Saturation des poids** de `tete_motrice` | ❌ **non** — \|W\| moyen 0,023, max 0,465, **0,00 %** de poids quasi nuls |
| **`tete_motrice` ignore les dims qui varient** | ❌ **non** — `r(variance de la dim, poids accordé)` = **+0,64** : elle les regarde bien |
| **Variance écrasée par la ReLU** | 🔴 **oui, mais sans lien avec la platitude** — voir §3 |

## 3. 🔴 LA DÉCOUVERTE COLLATÉRALE — 55 % des neurones sont MORTS

| Couche | Neurones **toujours à zéro** sur 400 ticks |
|---|---|
| **`pensee_bio`** (l'entrée de la décision) | **56,1 %** — médiane 57,4 %, min 37,0 %, max 78,7 % |
| **`bus_latent`** (la sortie du tronc) | **62,8 %** |

**40 cerveaux sur 40 dépassent 30 % de neurones morts.** Plus de la moitié de la capacité
allouée par la neurogenèse (bus 16 → 145) est **structurellement éteinte**.

⚠️ **MAIS CE N'EST PAS LA CAUSE DE LA PLATITUDE** :
`r(ReLU mortes, ratio inter/intra) = **+0,1314**` (`t` = +0,82, n=40, NS).

**Deux pathologies distinctes**, pas une cause et son effet. C'est le genre de raccourci que
la mesure a évité ici — l'enchaînement « neurones morts ⇒ moins de variance ⇒ politique
plate » est séduisant et **faux**.

⚠️ Cela recoupe, par un chemin indépendant,
[NEUROSCIENCES §1](../../ameliorations/NEUROSCIENCES_05092026_developpement_et_heredite.md) :
**0 synapse morte sur 259 329**, mais **56 % de neurones morts**. Les *poids* survivent (le
plancher vital les protège) ; ce sont les *activations* qui s'éteignent. Le dépôt mesurait la
mauvaise grandeur.

## 4. Ce que ça explique

Ce mécanisme rend compte, d'un seul coup, de faits jusqu'ici séparés :

| Fait déjà mesuré | Explication |
|---|---|
| Victoires **browniennes** (14–18× le plus court chemin) | une politique qui ne dépend pas de l'état produit une marche quasi aléatoire |
| **2 actions distinctes** jouées sur 7 | le classement est figé par les biais |
| C1 vote la même action sur les 8 branches du rollout | la séparation (8,12 %) est sous la marge (0,392) |
| L'effondrement du rollout à h=7 | conséquence directe du point précédent |
| `r(succès, directivité) = −0,92` | la directivité **est** le symptôme de cette platitude |

## 5. ⚠️ Ce que ça n'établit PAS

1. **Aucun lien causal avec le plafond n'est démontré.** C'est une **description** du
   mécanisme, pas une cause mesurée. 26 hypothèses ont déjà été réfutées sur ce dépôt.
2. **Le témoin PPO est à n=1** (une graine, une architecture). Le contraste est d'un ordre de
   grandeur, mais aucune comparaison fine n'en découle.
3. **On ne sait pas POURQUOI la variance temporelle est si faible.** Trois candidats non
   départagés : (a) `pensee_bio` varie peu parce que 56 % de ses dims sont mortes — mais la
   non-corrélation du §3 l'affaiblit ; (b) un seul pas de gradient par jour ne suffit pas à
   creuser des différences entre actions ; (c) le tronc détaché fait que la perception n'est
   jamais sculptée par la décision.
4. **Aucun de ces trois candidats n'est testé.**

## 6. Ce que ça ouvre

🟢 **La piste §3 du plan (un seul pas de gradient par journée) gagne un mécanisme.** Une
politique mise à jour **1 500 fois** dans sa vie, contre 23 680 pour PPO, a peu d'occasions
de creuser une dépendance à l'état. Le lien reste **à mesurer** : c'est une hypothèse, pas
une conclusion.

🟡 **Les ReLU mortes sont un chantier à part**, et probablement plus grave que la platitude
pour l'avenir du projet : la neurogenèse alloue de la capacité qui s'éteint à 56 %.

---

*Sondes créées : `sonde_platitude_c1.py`, `sonde_relu_mortes.py` (lecture seule).
Agrégat : `brains/06092026_sondes_zero_run/agregat_platitude.json`.*
