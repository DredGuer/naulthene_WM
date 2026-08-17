# Pourquoi C2 est étouffé — ce n'est pas la pondération, c'est la faim

**17/08/2026** — carnet de recherche, non normatif.
Demande de l'utilisateur : *« Essaye de régler ce problème de pondération, voir si ce qu'il
a à dire est intéressant. Fais quelques tests avant et après chaque modification. »*

**Résultat : la pondération n'est pas le problème. Aucune ligne de `src/` n'a été modifiée
au terme de ce diagnostic — le correctif que j'avais écrit s'est révélé inopérant et a été
retiré.**

---

## 1. La chaîne de pondération, mesurée étage par étage

Sur deux cerveaux mûrs (~1 M ticks), en instrumentant chaque étape :

| Étape | variante v41.13 | témoin v41.10 |
|---|---|---|
| C2 amplitude **brute** (sortie rollout) | 0,0022 | 0,0014 |
| C2 après **normalisation** (z-score) | **3,127** | **3,081** |
| `acceptation` | 0,215 | 0,729 |
| **`vigueur`** | **0,150** | **0,150** |
| `force = acceptation × vigueur` | 0,032 | 0,109 |
| C2 **pondéré** (entre en fusion) | 0,101 | 0,337 |
| C1 final | 0,090 | 0,149 |
| **ratio réel C2/C1** | **1,12×** | **2,26×** |

### Deux corrections à ce que j'affirmais ce matin

**(a) Le ratio n'est pas 0,03×, il est de 1,12× à 2,26×.** C2 pèse autant, voire deux fois
plus, que C1 dans la fusion. Le `0,03–0,10×` lu dans les logs est la métrique
`Arbitrage_Ratio_C2C1`, qui compare des grandeurs mesurées à des étapes différentes.

**(b) La normalisation ne « écrase » pas C2 — elle l'AMPLIFIE.** Elle prend une amplitude
brute de 0,002 et la porte à 3,1, soit **×1400**. Sans elle, C2 serait littéralement
invisible.

> **La pondération fonctionne comme prévu. Il n'y a rien à y corriger.**

---

## 2. Le vrai goulot : `vigueur = 0,150` exactement

Une seule valeur est identique sur les deux cerveaux, au millième près : **la vigueur, à
`VIGUEUR_PLANCHER = 0.15`**. C'est le plancher, pas une mesure.

Vérifié sur les runs longs :

```
temoin_g1   : vigueur moy 0.150 (min 0.150) | énergie moy 0.041
variante_g3 : vigueur moy 0.150 (min 0.150) | énergie moy 0.034
temoin_g2   : vigueur moy 0.150 (min 0.150) | énergie moy 0.063
```

Et sur un run neuf, **dès le premier jour** : `400/400 ticks en basse énergie`.

**L'agent vit à 4 % d'énergie, en épuisement permanent, toute sa vie.**

Or `force_planification = acceptation × vigueur`, et la vigueur **multiplie aussi** le gain
de C1. C2 la subit donc deux fois. Au plancher, la force de planification vaut **~7× moins**
qu'à pleine énergie.

> **C2 n'est pas étouffé par son architecture ni par sa normalisation. Il est étouffé par
> la faim.** Un organisme à 4 % d'énergie ne planifie pas — et c'est biologiquement juste.
> Le défaut n'est pas la règle : c'est que cet état soit devenu permanent.

---

## 3. Une falaise entre 2 et 3 repas par jour

Régime stationnaire simulé sur 20 jours, métabolisme continu :

| repas/jour | énergie moyenne | vigueur | régime |
|---|---|---|---|
| **2** | **0,131** | **0,150** | **plancher** |
| **3** | **0,893** | **0,750** | plein régime |
| 4 | 0,972 | 1,000 | plein régime |
| 6 | 0,968 | 1,000 | plein régime |

**Ce n'est pas une pente, c'est une falaise** : entre 2 et 3 repas, l'énergie passe de 0,13
à 0,89 (×6,8).

Et l'agent réel mange **3,2 fois par jour en moyenne** — exactement sur l'arête. Séquence
mesurée sur cinq jours consécutifs :

```
6 repas | 1 repas | 5 repas | 0 repas | 4 repas
```

Simulé avec **cette séquence réelle** : énergie moyenne **0,22**, vigueur au plancher.
Un seul jour à zéro fait tomber l'énergie de 1,000 à 0,206.

Bonne nouvelle : **la récupération est rapide** — un seul jour à 4 repas restaure la
vigueur à 1,000. Le système n'est pas cassé, il est *instable au point de fonctionnement*.

---

## 4. Pourquoi l'agent ne mange que 3 fois

Le monde offre **~20 ressources par jour**. Ce n'est pas la disponibilité qui limite.

Pour manger, il faut réunir trois conditions :

| Condition | Probabilité |
|---|---|
| être sur une case adjacente à la ressource | 4/35 |
| être **orienté** vers elle | 1/4 |
| jouer `ACTION_CONSOMMER` à ce tick | 1/7 |

Soit **1 tick sur 245** au hasard pur, c'est-à-dire 1,6 repas/jour.

L'agent réel obtient **7 à 10 % d'efficacité** sur 68 gestes/jour — donc **4× mieux que le
hasard**. Il a appris quelque chose. Mais 68 gestes × 10 % = 6,8 repas, et il en récolte
2 à 6 selon les jours.

> **L'agent n'est pas incompétent : le barème est calibré pour un monde où manger est
> facile, dans un monde où c'est difficile.**

---

## 5. Le correctif que j'ai écrit, puis RETIRÉ

J'ai d'abord identifié que la digestion coûte plus cher que la faim elle-même :

```
faim pure (taux_satiete) .... 0,00700/tick  ->  2,80/jour  (46 %)
DIGESTION (débit/rendement) . 0,00833/tick  ->  3,33/jour  (54 %)
```

La digestion tournait au **débit maximal en permanence**, même quand l'énergie était déjà
excédentaire. J'ai écrit une digestion « à la demande » :

```python
besoin = max(0.0, depense + (ENERGIE_MAX - self.energie))
conversion = min(self.debit_digestif, self.reserve_mobilisable(), besoin)
```

**Test avant/après, même graine, 60 jours :**

| | énergie moy | vigueur | ratio C2/C1 |
|---|---|---|---|
| avant | 0,044 | 0,150 | 0,26× |
| après | 0,043 | 0,150 | 0,33× |

**Aucun effet.** Et la raison est arithmétique : à énergie 0,04, `besoin` vaut 0,96 tandis
que `debit_digestif` vaut 0,0075. Le `min()` retient **toujours** le débit. Le correctif ne
mordrait que si l'agent atteignait une énergie proche de 1,0 — c'est-à-dire uniquement dans
le cas où le problème est déjà résolu.

**Correctif retiré.** Il aurait ajouté une branche, un drapeau d'ablation et une complexité
pour un effet nul.

---

## 6. Ce que ça change pour la suite

La cible est déplacée, et elle est mesurable :

1. **Faire passer l'agent de 3,2 à 4 repas/jour** suffit à restaurer la vigueur à 1,000, et
   donc à multiplier par ~7 la force de planification de C2. C'est le levier le plus court
   vers « C2 devient audible ».
2. **Trois voies possibles**, aucune testée :
   - rendre le geste moins exigeant (consommer la case **sous** l'agent en plus de la case
     frontale) ;
   - augmenter la densité de ressources (`NB_SOURCES_FOOD`, actuellement 2) ;
   - abaisser `taux_satiete` pour éloigner le point de fonctionnement de la falaise.
3. **Puis re-mesurer C2** avec la même sonde. Si à vigueur 1,000 C2 reste inerte, alors le
   problème est bien architectural — et cette fois on le saura pour de bon.

⚠️ **Ce document ne prouve pas que C2 deviendra utile une fois nourri.** Il prouve que la
mesure actuelle de C2 est faite sur un agent en épuisement permanent, donc dans le seul
régime où le projet a explicitement décidé que la délibération devait s'éteindre.
