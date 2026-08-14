# Campagne P17 & Ablation complète — 14 août 2026

> **Nature** : carnet de résultats. Non normatif. Consigne les mesures brutes, leurs biais
> connus, et ce qu'elles n'établissent pas.
>
> Deux campagnes indépendantes menées le même jour :
> **A.** la gaussienne d'apprentissage (P17) contre le cursus classique — 6 runs ;
> **B.** l'ablation complète du cerveau le plus avancé — 13 lésions × 3 niveaux.

---

## Ce qu'il faut retenir en trois lignes

1. La gaussienne produit **652 victoires contre 5** pour le cursus classique — mais la
   comparaison est **biaisée en sa faveur** sur deux points, et n'établit pas l'amplitude.
2. Couper C2 sur `DoorKey-5x5` **multiplie le taux de succès par 4,5**. Le même geste sur
   `6x6` et `8x8` le **divise**. Le verdict dépend du niveau.
3. `accord C1/C2 = 0,0 %` sur **les six runs**. Le chantier v37 n'a pas réglé ce point.

---

# A. La gaussienne d'apprentissage (P17)

## Le protocole

| | Témoin | Gaussienne |
|---|---|---|
| Régime | pointeur sur **un** niveau | **distribution** sur plusieurs |
| Répartition | 100 % sur le niveau courant | 13,2 % révision · 64,9 % socle · 17,4 % exploration · 4,5 % audace |
| Promotion | 2 victoires **ou** 35 % de maîtrise | **80 %** de maîtrise du niveau d'entrée |
| Graines | 11, 22, 33 | 11, 22, 33 |
| Jours | 2 000 | **4 590** ⚠️ |

## Les résultats bruts

| Graine | Témoin | Gaussienne | Palier atteint (témoin → gauss.) |
|---|---|---|---|
| g11 | **0** victoire | **199** | 1/6 → 2/6 |
| g22 | **1** victoire | **248** | 2/6 → 2/6 |
| g33 | **4** victoires | **205** | **5/6** → 1/6 |
| **Total** | **5** | **652** | |

Trois graines sur trois dans le même sens sur le nombre de victoires.

## ⚠️ Les deux biais, tous deux en faveur de la gaussienne

**1. Durée inégale — 4 590 jours contre 2 000.** Les cerveaux gaussiens sont *cumulatifs* :
2 590 jours d'une campagne antérieure (sans queue gauche) + 2 000 de celle-ci. Un `rm` est
passé avant que le run précédent ait fini d'écrire son `.brain` ; le log porte la trace
(`🧬 Résurrection du cerveau existant`). Les gaussiennes ont donc eu **2,3× plus de temps**.

**2. Distribution de cartes inégale.** Une gaussienne à 64,9 % sur le socle joue
majoritairement des cartes plus faciles que son niveau d'entrée. **Compter les victoires
brutes favorise mécaniquement le régime qui passe son temps sur du facile.** C'est le
défaut de mesure central de cette campagne.

### Ce que le chiffre établit malgré tout

Le témoin g11 est resté à **niveau 1/6 pendant 2 000 jours entiers, sans une seule
victoire**. Sur la même graine, la gaussienne en produit 199. Un facteur 2,3 en durée
n'explique pas un écart entre 0 et 199.

**La direction tient. L'amplitude ×130 ne veut rien dire.**

## Le résultat qui contredit le précédent

**Aucune gaussienne n'a dépassé le palier 2/6. Le témoin g33 est monté à 5/6.**

Ce n'est pas contradictoire, c'est mécanique : les deux régimes n'ont pas le même critère
de promotion. Le témoin promeut sur série de victoires ou 35 % de maîtrise ; la gaussienne
exige **80 %**.

> **Le témoin est promu sans avoir appris. La gaussienne apprend sans être promue.**

Lequel des deux est « meilleur » dépend entièrement de ce qu'on mesure — et c'est
précisément pourquoi cette campagne ne tranche pas.

## Le signal d'alerte : les victoires s'espacent

| Graine | Intervalle moyen entre victoires | Tendance |
|---|---|---|
| g11 | 29 j (n=69) | **3,01 ↗️ s'espacent** |
| g22 | 18 j (n=228) | **1,73 ↗️ s'espacent** |
| g33 | 22 j (n=178) | 0,50 ↘️ se rapprochent |

Les deux qui gagnent le plus voient leur cadence **ralentir**. L'agent ne consolide pas :
il atteint un plateau puis s'y installe.

## Ce que cette campagne ne permet PAS de conclure

- ❌ Que la gaussienne est ×130 meilleure (durée + difficulté inégales).
- ❌ Que la gaussienne bloque la progression de palier (critère de promotion différent,
  pas capacité différente).
- ✅ Qu'un régime distributionnel produit des victoires là où le pointeur n'en produit
  aucune (g11 : 0 → 199).

**Pour trancher, il faut 3 gaussiennes partant réellement de zéro, à 2 000 jours,
comparées à taux de victoire par niveau — pas en victoires brutes.**

---

# B. L'ablation complète

## Le protocole

| | |
|---|---|
| Cerveau | `brains/old_V39/p17_gauss_g22.brain` — 4 590 jours, 248 victoires |
| Lésions | 13, une à la fois |
| Niveaux | 7 (`DoorKey-5x5`), 8 (`6x6`), 9 (`8x8`) — **le terrain réel de ce cerveau** |
| Épisodes | 60 par condition et par niveau |
| Apprentissage | **aucun** — le cerveau est figé, on ne mesure que le comportement |
| Graine | 1789 |

### ⚠️ Une première tentative a été jetée

Le banc prend « le dernier niveau du `PROGRAMME` » par défaut. Le premier lancement a donc
testé g22 sur `MultiRoom-N4-S5` — un niveau **qu'il n'a jamais vu**. Témoin à **0,0 %**,
et par conséquent les 13 lésions à « inerte ».

> **Leçon** : une ablation dont le témoin est à zéro ne mesure rien. Le résultat
> « tout est inerte » aurait été spectaculaire et entièrement faux. **Toujours vérifier
> que le témoin est au-dessus du plancher avant de lire une seule ligne du tableau.**

## Les résultats — trois niveaux, trois verdicts différents

### `DoorKey-5x5` (témoin 3,3 %)

| Lésion | Victoires | Écart | Marge 95 % |
|---|---|---|---|
| **c2_coupe** | **15,0 %** | **+11,7** | ±9,0 |
| episodique_coupe | 10,0 % | +6,7 | ±7,6 |
| *témoin* | *3,3 %* | — | ±4,5 |
| vue_coupee | 1,7 % | −1,7 | ±3,2 |
| bio_coupe | 0,0 % | −3,3 | — |

### `DoorKey-6x6` (témoin 11,7 %)

| Lésion | Victoires | Écart |
|---|---|---|
| *témoin* | *11,7 %* | — |
| c2_coupe | 6,7 % | **−5,0** |
| bio_coupe | 3,3 % | −8,3 |
| **vue_coupee** | **0,0 %** | **−11,7** |

### `DoorKey-8x8` (témoin 3,3 %)

| Lésion | Victoires | Écart |
|---|---|---|
| hippocampe_fige | 5,0 % | +1,7 |
| *témoin* | *3,3 %* | — |
| vue_coupee / bio_coupe / **c2_coupe** / episodique_coupe | 0,0 % | −3,3 |

## Lecture 1 — la vue est le seul organe systématiquement vital

Seul canal dont l'ablation dégrade sur **les trois niveaux**, jusqu'à annuler complètement
la performance sur `6x6` (11,7 % → 0 %). C'est aussi la seule lésion qui effondre l'accord
C1/C2 (0,311 → 0,042) : privé de vision, C2 délire.

## Lecture 2 — C2 : le verdict s'inverse avec la taille de la carte

| Niveau | Effet de couper C2 |
|---|---|
| `5x5` | **+11,7 pts** (×4,5) |
| `6x6` | −5,0 pts |
| `8x8` | −3,3 pts |

**Sur la carte la plus petite, la planification nuit ; dès qu'elle grandit, elle aide.**

Hypothèse la plus simple : sur `5x5`, l'optimum est à ~10 actions et la marge est de 25× —
l'exploration réflexe suffit largement, et un planificateur qui contredit systématiquement
le réflexe ne fait que réduire la couverture (0,0165 sans C2 contre 0,0121 avec). Sur les
cartes plus grandes, le réflexe seul ne porte plus.

⚠️ **Ce n'est pas ce que le README affirme.** Les deux README portent « couper C2 double le
taux de succès » — mesure faite sur un seul niveau. **La formulation est trop générale et
doit être corrigée** : l'effet dépend du niveau et change de signe.

## Lecture 3 — le piège de l'`accord = 1,000`

`c2_coupe` affiche un accord C1/C2 de **1,000 exactement** sur les trois niveaux.

Ce n'est **pas** un résultat : la lésion pose `force_planification = 0`, donc l'action
fusionnée *est* celle de C1 par construction. L'accord est trivialement parfait.
`banc_ablation.py:243-246`.

> **À ne pas citer comme « couper C2 réconcilie les deux systèmes ».** C'est une
> tautologie de la mesure.

## Lecture 4 — cinq canaux identiques au témoin à la 7ᵉ décimale

`ouie_coupee`, `odorat_coupe`, `gout_coupe`, `exo_coupe`, `spatiale_coupee` rendent des
valeurs **rigoureusement identiques** au témoin — jusqu'à `couverture = 0.012144507493088898`
et `accord = 0.2567137785537611`.

Ce n'est pas « ça ne change presque rien » : c'est **le même calcul, bit pour bit**. Ces
canaux portent déjà des zéros sur DoorKey (pas de son, pas de nourriture, aucun plug C3
enregistré). Les couper revient à mettre des zéros là où il y avait des zéros.

> **On n'a pas mesuré leur inutilité — on a mesuré leur absence de stimulus.**
> Un verdict « inerte » sur ces cinq lignes est **vide**, pas négatif.

---

# C. Le fil qui relie les deux campagnes

Les six runs, gaussiens comme témoins, affichent la même ligne :

```
Arbitrage C1/C2 : C1=0.469  C2=2.743  (ratio 5.85x) | accord 0.0%
```

| Run | C1 | C2 | Ratio | Accord |
|---|---|---|---|---|
| témoin g11 | 0,469 | 2,743 | 5,85× | **0,0 %** |
| témoin g22 | 0,315 | 2,751 | 8,74× | **0,0 %** |
| témoin g33 | 0,378 | 2,513 | 6,64× | **0,0 %** |

### 🐛 Mais ce 0,0 % est un BUG DE MESURE (trouvé le 14/08)

`noyau.py:868` :

```python
"accord": int((logits_instinct.argmax(dim=-1)
               == valeurs_simulees.argmax(dim=-1)).all().item()),
```

Le `.all()` exige que **toutes** les lignes du batch soient d'accord pour compter 1. Sur
400 ticks, une seule divergence écrit 0. **Le résultat est quasiment garanti à 0 % par
construction**, quel que soit l'état réel du cerveau.

Le banc d'ablation, qui mesure **tick par tick**, trouve **0,26 à 0,31** sur le même cerveau.

| Source | Accord mesuré |
|---|---|
| Log de nuit (`.all()` sur le batch) | **0,0 %** |
| Banc d'ablation (par tick) | **26 à 31 %** |

> **Le désaccord réel est de ~70 %, pas de 100 %.** Le chiffre de 0 % circule dans le projet
> depuis le chantier v37 et a orienté le diagnostic vers un problème plus grave qu'il ne
> l'est. **Correctif à faire** : remplacer `.all()` par une moyenne sur le batch, comme le
> fait déjà `banc_ablation.py`.

Le ratio, lui, n'est pas affecté par ce bug :

C'est exactement le défaut que le chantier v37 devait corriger
([CHANTIER_v37](../ameliorations_appliquees/CHANTIER_v37_equilibre_c1_c2.md), qui mesurait
0 % d'accord et un ratio de 9,9× à 22,1×). Le ratio a baissé, l'accord **pas du tout**.

Et ça rejoint la [dissection de g22](DISSECTION_g22_aout_2026.md) : le cerveau *sait* que
le but vaut **16,2×** le reste — appris, jamais déclaré — mais
[P12](../ameliorations/AVIS_ET_PROPOSITIONS_aout_2026.md) a mesuré que s'en servir
n'améliore rien (2 graines positives sur 5, p = 1,000).

> **L'agent a une bonne carte et un mauvais volant.** La représentation est juste ; la voie
> qui va de la représentation à l'action est monopolisée par une couche qui contredit
> systématiquement le réflexe.

## Ce qu'il faudrait mesurer ensuite

1. **La gaussienne, proprement** : 3 runs de zéro à 2 000 jours, comparés en **taux de
   victoire par niveau**, pas en victoires brutes.
2. **L'accord C1/C2** : pourquoi reste-t-il à 0,0 % après le chantier v37 ? Une sonde de
   gradient sur `tete_motrice` (à 20,2 % de sa norme de naissance) et `cortex_prefrontal`
   dirait si la voie motrice apprend encore quelque chose.
3. **L'ablation sur un cerveau qui a des stimuli** : les cinq canaux muets ne pourront être
   jugés que sur un environnement où ils portent un signal non nul.

---

*Campagne du 14 août 2026. Logs et `.brain` archivés dans `brains/old_V39/`.
Résultats bruts : `brains/ablations/g22_doorkey.json`.*
