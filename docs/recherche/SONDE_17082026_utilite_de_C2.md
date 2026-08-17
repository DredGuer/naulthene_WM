# C2 devient-il utile ? — la mesure qui manquait

**17/08/2026** — carnet de recherche, non normatif.
Question de l'utilisateur : *« Je veux tester si C2 à terme devient utile ou non. Prouve-moi
pourquoi et comment C1 et C2 travaillent ensemble. »*

---

## 1. Pourquoi toutes les mesures précédentes étaient aveugles

Le projet mesurait C2 de trois façons, toutes indirectes :

| Métrique | Ce qu'elle dit | Pourquoi c'est insuffisant |
|---|---|---|
| `Arbitrage_Ratio_C2C1` | l'AMPLITUDE de C2 | un module fort peut ne rien changer |
| `Arbitrage_Accord` | les deux argmax coïncident | **cassé** : deux voix figées → 100 % (v41.14) |
| ablation « couper C2 » | l'effet sur le score | 0,0 pt, mais sans dire **pourquoi** |

Aucune ne répond à : **C2 change-t-il la décision, et dit-il autre chose que C1 ?**

---

## 2. Deux erreurs de sonde, corrigées avant conclusion

⚠️ Consignées parce qu'elles auraient produit un résultat faux et crédible.

**(a) La sonde jouait l'`argmax`.** L'agent réel **échantillonne**
(`Categorical.sample()` dans `traiter_tick`). En jouant le mode, l'agent tournait sur
place, revoyait la même observation, et **les deux voix affichaient une entropie de
0.000**. J'ai failli conclure « C1 et C2 sont morts » — alors qu'un run réel mesure C1
entre 0,17 et 0,77.

**(b) Le remappage de niveau.** `persistance` ramène un `.brain` à l'index de son `env_id`.
Le cerveau sondé revenait au niveau 0 sans que la sonde le signale. D'où l'option
`--niveau`.

Règle vérifiée à chaque fois : **comparer la sonde à un run vivant** avant de croire ses
chiffres.

---

## 3. Le résultat : C2 n'est pas éteint, il est REDONDANT

Mesure directe des 7 logits de chaque voix, tick par tick, sur un cerveau de 1 M de ticks :

```
corrélation C1/C2 des 7 logits : +0,962   (min +0,933, max +0,980)
ticks où corrélation > 0,9     : 100 %
amplitude C1 : 2,80     amplitude C2 : 3,24
```

**C2 a une amplitude comparable à C1** (3,24 contre 2,80 — il est même légèrement plus
fort) et **dit exactement la même chose**. Il n'est ni faible ni muet : il est *superflu*.

C'est pourquoi l'ablation donne 0,0 point sur six niveaux. On ne retire pas un organe
inerte — on retire un **doublon**. Le score ne bouge pas parce que C1 porte déjà
l'information.

---

## 4. La population complète — mon hypothèse partiellement RÉFUTÉE

Le §3 reposait sur **un** cerveau. Passé aux **30 cerveaux mûrs** disponibles (~1 M ticks
chacun), la « redondance » ne tient plus comme règle générale :

| Groupe | n | corr. moyenne | médiane | étendue |
|---|---|---|---|---|
| v41.10 témoin | 9 | **+0,647** | +0,850 | −0,45 → +0,96 |
| v41.10 variante | 9 | +0,352 | +0,699 | −0,91 → +0,96 |
| v41.13 témoin | 6 | **−0,147** | −0,024 | −0,88 → +0,22 |
| v41.13 variante | 6 | +0,574 | +0,665 | −0,15 → +0,97 |
| **TOUS** | **30** | **+0,385** | **+0,504** | **−0,91 → +0,97** |

Répartition :

| Régime | Part |
|---|---|
| **copie** (corr > +0,7) | **43 %** |
| indépendant (\|corr\| < 0,3) | 20 % |
| **opposé** (corr < −0,3) | **17 %** |

**La redondance est le régime le plus fréquent, pas le régime universel.** Un cerveau sur
six voit ses deux voix systématiquement *opposées* (jusqu'à −0,911). Le cerveau du §3
(+0,962) était le cas le plus extrême, pas le cas typique.

⚠️ **C'est exactement ce que la règle de mesure prédit** : j'avais tiré une conclusion
générale d'une observation unique, parce qu'elle expliquait élégamment l'ablation à 0,0 pt.
Trente cerveaux la ramènent à « 43 % des cas ».

### Ce qui, en revanche, tient sur les 30

**C2 est SYSTÉMATIQUEMENT plus fort que C1** — dans les trois groupes, sans exception :

| Groupe | amplitude C1 | amplitude C2 | ratio |
|---|---|---|---|
| v41.10 témoin | 2,24 | 2,81 | **1,25×** |
| v41.13 témoin | 1,68 | 2,48 | **1,47×** |
| v41.13 variante | 1,61 | 2,80 | **1,74×** |

Cela contredit frontalement la lecture historique du projet (« C2 est éteint, ratio
0,03–0,10× »). Ce ratio-là est mesuré **après** normalisation et pondération par
`force_planification` ; sur les logits **bruts**, C2 parle plus fort que C1.

⚠️ La contradiction n'est qu'apparente, et elle est instructive : `Arbitrage_Ratio_C2C1`
mesure ce qui **arrive dans la fusion**, la sonde mesure ce que C2 **produit**. C2 a donc
bien un avis marqué — c'est la chaîne de pondération qui l'atténue avant l'arbitrage.

---

## 5. Réponse à la question posée

> **C2 devient-il utile à terme ?**

**Non, et pour deux raisons distinctes selon les cerveaux :**

- dans **43 %** des cas, il converge vers C1 (corr > +0,7) : un second avis identique
  n'ajoute rien, quel que soit son poids ;
- dans les autres, il a un avis **différent** mais qui n'atteint pas la décision — le
  ratio effectif dans la fusion tombe à 0,03–0,10×.

Dans les deux régimes, l'ablation donne 0,0 point. **Mais pour des raisons opposées** —
redondant ici, étouffé là. C'est la première fois que le projet distingue les deux.

> **Comment C1 et C2 travaillent-ils ensemble ?**

Le seul canal qui les relie est **unidirectionnel** : l'auto-distillation C2 → C1 (v37.0)
tire C1 vers C2 à chaque tick. Rien, nulle part, ne pousse C2 à se **différencier** de C1,
et rien ne fait remonter l'information dans l'autre sens.

À la naissance les deux voix sont indépendantes (corr −0,003, mesuré). Ce qui suit dépend
entièrement de la trajectoire : convergence dans 43 % des cas, divergence stérile ailleurs.

Coût de l'opération : **C2 consomme 42 % du temps de calcul** par tick, contre 6 % pour C1.

---

## 6. Ce que ça ouvre — non tranché

1. **Le canal de pondération, pas C2 lui-même.** C2 produit un avis d'amplitude 2,5–2,8
   qui arrive à 0,03–0,10× dans la fusion. Le goulot est identifié et mesurable : il est
   dans la chaîne `normalisation → force_planification → vigueur`, pas dans le module.
2. **Couper la distillation.** Si C1 cesse d'imiter C2, les 43 % de copies disparaissent-
   elles ? A/B propre sur `TAUX_DISTILLATION_C1`.
3. **Donner à C2 ce que C1 n'a pas.** Il ne reçoit que `pensee_bio`, l'état déjà compressé
   par C1 : par construction il ne peut rien voir de plus. La v41.13 est un premier pas
   (écart +0,721 sur la corrélation, mais **n=6, non concluant**).

⚠️ Aucune de ces trois pistes n'est validée. La seule chose solide de cette page est la
mesure de population : **43 % de copies, 17 % d'opposés, C2 systématiquement plus fort que
C1 en amplitude brute.**
