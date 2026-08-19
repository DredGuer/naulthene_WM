# La douleur unique — une seule douleur, deux signatures

**19/08/2026** — carnet de recherche, non normatif.
Refonte demandée par l'utilisateur : *« le seul élément à gérer dans la gestion du corps,
c'est la douleur, avec ses facteurs de points de douleur, de temps, et sa dégradation
proportionnelle au pic de douleur et au type »*.

---

## 1. Ce qui était faux — deux douleurs sans rapport

| source | où | forme |
|---|---|---|
| mur | `recompense_interne += MALUS_DOULEUR` | **−0,01**, constante, sans mémoire |
| chaleur | `D(t) += chaleur²` puis `instant + brulure` | graduée, avec accumulation |

**Deux canaux, deux échelles, deux traitements.** L'empilement que le projet refuse — et
`MALUS_DOULEUR` était l'une des 4 récompenses en dur signalées par l'audit du dogme, celle
même qui produisait l'inversion *« mourir coûte moins cher que se cogner »*.

---

## 2. La forme retenue

```
douleur(t) = douleur(t−1) × (1 − dégradation(t)) + pic(t)
```

**Un seul état corporel.** Le « type » n'est pas un canal : c'est le couple
**(pic, demi-vie de récupération)** que l'organe sensoriel fournit.

| événement | pic | demi-vie |
|---|---|---|
| **brûlure** | ∝ excès thermique | **60 ticks** — ça s'installe |
| **choc mural** | ∝ vitesse d'impact | **5 ticks** — ça passe |

Les deux signatures vivent dans `bus_sensoriel.py` (la frontière corps/monde, où `lava` a
le droit d'exister) ; **`noyau.py` ne reçoit que deux nombres** et ignore ce qui l'a blessé.

### L'indexation exponentielle, dans les deux sens

**(1) Le pic sature** — `douleur += pic × (1 − douleur)`. Un corps déjà au maximum ne peut
pas avoir « deux fois plus mal ». Borné dans [0,1] par construction, sans `clip`.

**(2) La récupération ralentit** avec l'exposition ET l'intensité :

```
dégradation = (1 / demi_vie) × exp(−(exposition + douleur))
```

⚠️ **Correction utilisateur, et c'est le cœur du modèle** : le temps n'augmente **pas** la
douleur aiguë — il **allonge la récupération**. Mesuré :

| exposition | douleur pendant | après 50 ticks de repos |
|---|---|---|
| 1 tick | 0,1973 | **0,0955** |
| 50 ticks | 0,9744 | **0,6925** |
| 200 ticks | 0,9749 | **0,6943** |

Le pic sature au même niveau ; c'est la **descente** qui change du tout au tout.

---

## 3. La chaleur est un état MAINTENU par la source

Première implémentation : la chaleur infligeait un pic **à chaque tick**. Résultat en
régime permanent — **douleur 0,898**, pire que la v41.26 (0,432). Le pic arrivait sans
cesse pendant que la récupération ralentissait : les deux effets se cumulaient.

Correction utilisateur : *« selon la distance, la chauffe est un état maintenu, lié au feu
ou à la lave, pas qu'au cerveau »*.

**La physique juste** : un corps **évacue** la chaleur. Il ne se lèse que si l'apport
dépasse sa capacité d'évacuation.

```
apport net = max(0, chaleur − CAPACITE_EVACUATION_THERMIQUE)
```

⚠️ **Évacuer ≠ percevoir.** Le seuil de perception (0,12) et la capacité d'évacuation
(0,40) sont deux capacités distinctes : on sent la chaleur bien avant de brûler. Les
confondre faisait brûler l'agent partout où il sentait quelque chose — le défaut de fond
des v41.25 et v41.26.

**La distance module le PALIER D'ÉQUILIBRE**, pas seulement la vitesse d'y arriver
(400 ticks, chemin réel) :

| distance | chaleur | douleur permanente |
|---|---|---|
| d≥3 | 0,096 | **0,0000** |
| d=2 | 0,209 | **0,0000** |
| d=1 (longer) | 0,457 | **0,1664** |
| d=0 (dedans) | 1,000 | **0,8057** |

L'agent peut **longer** la lave sans se consumer ; y entrer brûle à fond.

---

## 4. La vitesse d'impact

MiniGrid n'a pas de vitesse continue. La vitesse est l'**inverse du nombre de ticks depuis
le dernier déplacement réussi** : avancer à chaque tick donne 1,0, piétiner s'effondre.

| vitesse | douleur du choc |
|---|---|
| 1,00 (pleine course) | **0,9300** |
| 0,33 (au ralenti) | 0,2833 |
| 0,10 (à l'arrêt) | 0,0820 |

---

## 5. L'option (b) — mourir coûte la journée

Décision utilisateur : mourir arrête la **journée** (l'agent perd ses ticks restants, la
nuit tombe, il repart le lendemain). L'utilisateur assume la convention : *« même si c'est
tricher »* — une vraie mort terminerait le run, mais aucun cerveau ne dépasserait le
jour 2 (206 morts sur 300 épisodes mesurées).

⚠️ **Le coût est bien plus lourd que prévu.** Smoke test, 8 jours :

```
ticks perdus/jour : 290, 396, 396, 384, 399, 286, 364, 374
moyenne : 361/400 = 90 % de la journée perdue
```

L'agent ne vit plus que **~39 ticks par jour** au lieu de 400. Et `chaleur à la mort =
0,457`, pas 1,0 : **il ne meurt pas dans la lave, il meurt à côté** — de faim, faute de
temps pour manger.

---

## 6. La campagne — trois bras, et pourquoi

Deux changements simultanés (douleur unifiée **+** option b) seraient **confondus**. D'où
trois bras sur les **mêmes 20 graines** :

| bras | douleur unifiée | option (b) |
|---|---|---|
| **A** | ✅ | ✅ |
| **B** | ✅ | ❌ |
| **C** | ❌ | ❌ |

- **B vs C** → la douleur unifiée aide-t-elle ou nuit-elle ?
- **A vs B** → combien coûte l'option (b) ?
- **A vs C** → le bilan global.

Vérifié avant lancement : les trois bras produisent des déficits distincts
(**1,641 / 2,758 / 2,009**) et les deux ablations impriment leur avertissement.

Critères de lecture, dans l'ordre : **récolte** (le mécanisme causal identifié cette nuit,
−25 % sur deux cartes) → énergie → survie → valence de la lave.
