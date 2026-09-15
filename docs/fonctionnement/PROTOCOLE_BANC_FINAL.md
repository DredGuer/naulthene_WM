# PROTOCOLE DU BANC FINAL — version 1 (gelée le 2026-09-15)

> **Document normatif.** Tout rapport produit par `banc_final.py` référence ce document et
> sa **version**. Toute modification du protocole **incrémente la version** et **invalide la
> comparabilité** des rapports antérieurs.
>
> **Ce que ce protocole fige** : les cartes, la règle qui dérive `n`, la valeur mesurée de
> `n`, le pool de graines d'évaluation, la famille de métriques et son seuil, et le coût
> déclaré de la campagne d'acceptation (tâche 9). **Ce qu'il ne certifie pas** : la justesse
> du banc (test d'acceptation D3, à part) et rien sur le cursus (interdit §8).

---

## 1. Les deux cartes — reportées SÉPARÉMENT, jamais poolées

| Index | Carte | Budget natif (`max_steps`) |
|---|---|---|
| **3** | `MiniGrid-SimpleCrossingS9N1-v0` — le mur réel du cursus | 324 |
| **4** | `MiniGrid-LavaGapS5-v0` — le palier suivant | 100 |

Les deux cartes sont **imposées** à tous les cerveaux (`--env-force`, niveau intact) et
**reportées séparément**. Le taux poolé des deux cartes **n'entre dans aucun dimensionnement**.

**Justification — la corrélation inter-cartes détruit la mesurabilité.** Mesurée sur le
pilote, la corrélation inter-cartes des taux par cerveau vaut

```
ρ = −0,8807  (à 200 épisodes/carte, cov = −0,00299375)   →   ρ = −0,8958  (à 1 145, cov = −0,00261049)
```

Les cerveaux **s'échangent** les cartes : `K8_NU_g11` est premier sur la carte 3 (0,477) et
dernier sur la carte 4 (0,053) ; `K8_NU_g44` est l'inverse (0,391 / 0,244). Le taux poolé
devient donc **presque indépendant du cerveau** (0,265 → 0,317), et la dispersion poolée
(σ̂ = 0,0221) tombe **sous** la dispersion de chaque carte (0,0343 et 0,0775). Pooler, c'est
**annuler le signal** qu'on cherche à mesurer. Chaque carte porte donc son propre `n`, et
chaque rapport publie les deux cartes côte à côte.

---

## 2. Le nombre d'épisodes `n` — DÉRIVÉ, gelé au maximum des cartes

`n` **n'est pas une constante** : c'est un **résultat** d'une mesure pilote. La règle
(spéc. §8bis) est la **domination du bruit de mesure** :

```
SE_binomiale(n) = sqrt( p̄ (1 − p̄) / n )   ≤   σ̂ / 3,0        n = le plus petit entier
```

où `p̄` est le taux de franchissement poolé de la carte et **σ̂** la dispersion inter-cerveaux
**dé-convoluée** (l'estimateur non biaisé : `σ̂² = max(0, s² − v)`, `s` = dispersion observée,
`v` = variance d'échantillonnage du pilote). Le seul paramètre **posé** est le facteur `3,0`.

La règle se réécrit `n = 9 · p̄(1−p̄) / σ̂²` : la variance est au **DÉNOMINATEUR**, donc la
carte qui **contraint** est celle de plus **petit** σ̂. Le protocole gèle donc le **maximum** :

```
n_final = max( n_carte3, n_carte4 )
```

### La mesure de sauvetage qui fonde ce `n` (2026-09-15)

À 200 épisodes par carte, l'IC95 de σ̂ **touchait zéro** (carte 3 et poolé) : la dispersion
n'était pas identifiable à 4 cerveaux. Le pilote a été re-mesuré à **1 145 épisodes par
cerveau et par carte** (condition `σ²/v > χ²(0,975;3)/3 − 1 = 2,1161`), mêmes cerveaux
(`K8_NU`, graines 11, 22, 33, 44), mêmes cartes, en lecture seule.

| Carte | `p̄` | σ̂ (dé-convoluée) | IC95 de σ̂ | `n` dérivé |
|---|---|---|---|---|
| 3 `SimpleCrossing` | 0,423799 (1941/4580) | 0,034303 | [0,015257 ; 0,138238] | **1 868** |
| 4 `LavaGap` | 0,142576 (653/4580) | 0,077477 | [0,043056 ; 0,291250] | **184** |

**`n_final = max(1 868, 184) = 1 868`**

Ligne de calcul (carte contraignante, la 3) :
`n = plus petit entier ≥ 1867,757392 tel que sqrt(0,423799 × (1 − 0,423799) / n) ≤ 0,034303 / 3 = 0,011434 ⇒ n = 1 868`.

⚠️ **L'IC95 de σ̂ exclut zéro sur les deux cartes** : c'est la **condition de validité** du
gel (pré-enregistrée avant la mesure). Sans elle, aucun `n` fini n'était autorisé.

---

## 3. Le pool de graines d'évaluation — `[10000, 10000 + n]`

Le pool est **dérivé** du `n` gelé :

```
graines d'évaluation = 10000 … 10000 + n_final − 1   (n_final graines)
```

(notation compacte `[10000, 10000 + n]` ; le code produit `range(10000, 10000 + n)`,
donc les `n` graines 10000…10000+n−1, borne haute exclue.)

- La **base** `10000` est une constante d'**isolation** : elle sépare hermétiquement
  l'évaluation du vécu d'entraînement (graines réelles 5…222).
- L'**étendue** suit `n` : **le code la dérive déjà** (`banc_final.py:758` —
  `range(graine_eval_base, graine_eval_base + episodes)`), aucune constante ne fige une borne
  haute. La spécification §8 (qui écrivait encore « 10000…10099 », héritée de l'ancien
  `n = 100`) est corrigée en conséquence.

---

## 4. La famille de métriques et le seuil

**Famille de 3 métriques** (convention MES-04, déclarée d'avance) :

| Rang | Métrique | Nature |
|---|---|---|
| **Primaire** | taux de franchissement (+ IC Wilson) | verdict |
| Secondaire | retour moyen | secondaire |
| Secondaire | longueur normalisée (médiane) | secondaire |

**Seuil** : `seuil_t(n, 3, 0.05)` — correction de Bonferroni sur la famille de 3.
À `n = 20` (cerveaux par bras, tâche 9) : **`t` = 2,6251**. Le nombre de métriques est
annoncé **avant** tout `t` ; le seuil est **recalculé** à chaque changement de `n`.

---

## 5. Le coût déclaré de la tâche 9

À `n_final = 1 868`, la campagne d'acceptation (2 bras × 20 cerveaux × 2 cartes)
évalue `2 × 20 × 2 × n_final = 149 440` épisodes. Sur la cadence **mesurée** du banc
(~0,5 s/épisode ; raffiné par carte : 0,63 s sur la carte 3, 0,32 s sur la carte 4) :

```
coût ≈ 80 × n_final × 0,5 s ≈ 20,8 h   (≈ 0,87 jours)
```

Ce coût est **déclaré** comme partie intégrante du protocole : un protocole qui cacherait son
coût cacherait sa portée. Il n'est **pas** une invitation à raboter `n` — la puissance
statistique n'est pas un paramètre d'ajustement (arbitrage de l'auteur, 13/09/2026).

---

## 6. Règles de clôture du registre

1. **Protocole standard versionné** : ce document, versionné ; tout rapport du banc le
   référence avec sa version.
2. **Banc final obligatoire** dans les nouvelles campagnes majeures.
3. **Séparation entraînement / évaluation** : un banc qui réutilise une graine
   d'entraînement est **invalide** (base d'évaluation ≥ 1000, en pratique 10000).

Règle de version : toute modification du protocole **incrémente sa version** et **invalide
la comparabilité** des rapports antérieurs.

---

## 7. L'interdit — le banc ne prouve rien sur le cursus

Le banc mesure une compétence **sur cartes imposées** (`--env-force`). Il **ne prouve rien**
sur le cursus (règle « un banc forcé ne prouve rien sur le cursus », CLAUDE.md §7) et **ne
remplace jamais** un run de cursus. Toute mécanique validée au banc **doit** repasser en
cursus complet. Le banc **dimensionne** l'instrument ; il ne le **certifie** pas (test
d'acceptation D3 séparé, qui doit reproduire l'ordre SCI-01 avant toute revendication).

---

## 8. Références aux mesures que ce protocole fige

- **Mesure de sauvetage** (le `n` gelé) :
  [`docs/recherche/campagnes/EVA01_N1145_15092026_la_dispersion_identifiee.md`](../recherche/campagnes/EVA01_N1145_15092026_la_dispersion_identifiee.md)
  et `brains/EVA01_pilote_n1145_15092026/pilote.json`.
- **Dé-convolution** (le `n = 10 810` rétracté comme point de plug-in, jamais dimensionnement) :
  [`docs/recherche/campagnes/EVA01_N200_13092026_la_dispersion_deconvoluee.md`](../recherche/campagnes/EVA01_N200_13092026_la_dispersion_deconvoluee.md).
- **Premier pilote** (`n = 333`, rétracté comme borne basse) :
  [`docs/recherche/campagnes/EVA01_13092026_la_derivation_de_n.md`](../recherche/campagnes/EVA01_13092026_la_derivation_de_n.md).
- Règle et cartes figées : spéc. `docs/ameliorations/CHANTIER_EVA-01_banc_final_standardise.md` §8.
