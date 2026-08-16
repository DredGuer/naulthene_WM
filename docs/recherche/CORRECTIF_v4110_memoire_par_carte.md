# v41.10 — La mémoire par carte, et ce que la lave ne dit pas

**16/08/2026** — carnet de recherche, non normatif.
Fait suite au [scan des cerveaux](SCAN_CERVEAUX_16082026.md) du même jour.

---

## 1. Le défaut : une ardoise essuyée deux fois par jour

Le scan des 20 cerveaux de la campagne du 16/08 relevait ceci dans les logs :

```
🗺️ 5/200 souvenir(s) spatial(aux) — 51 715 doublon(s) évité(s)
```

**La mémoire spatiale tournait à 1 % de sa capacité** pendant que 51 715 expériences
étaient jetées comme redondantes.

### La cause

P17 (v41.6, livré la veille) tire le niveau de chaque épisode au sort autour du niveau de
référence. Chaque changement de carte appelait `_appliquer_niveau_episode`, qui appelait
`reinitialiser_niveau()` — **un effacement complet**.

| Grandeur | Mesure |
|---|---|
| Bascules de carte | ~1,5 par jour |
| Effacements sur un run de 2500 jours | **~3750** |
| Souvenirs vivants à l'instant du scan | 5 sur 200 |

### L'erreur de raisonnement

L'effacement confondait deux choses distinctes :

| | |
|---|---|
| changer de carte | les coordonnées **courantes** ne s'appliquent plus |
| ne plus jamais y aller | les coordonnées **ne valent plus rien** |

Le premier cas n'implique pas le second. Avant P17, il l'impliquait *en pratique* — un
pointeur qui ne recule jamais ne revient jamais sur ses pas, donc effacer était sans coût.
**P17 a invalidé cette hypothèse sans que l'effacement soit revu.** Sous P17, l'agent
revient sans cesse sur les mêmes cartes (révision, défi, incursion).

Conséquence directe : le mécanisme d'**abstraction par récurrence** (v36.0) — dont tout le
principe est que `confirmations` monte avec la répétition — ne pouvait
**structurellement** jamais accumuler. Il moyennait sur une ardoise remise à zéro.

> C'est une régression que j'ai introduite la veille avec P17, et que je n'avais pas vue.

---

## 2. Le correctif : archiver au lieu de détruire

`MemoireEpisodiqueSpatiale` gagne une **archive par carte**. `souvenirs` reste la vue de
la carte courante ; les autres dorment dans `archives_cartes`, indexées par une clé
opaque.

```python
def basculer_carte(self, cle_carte) -> bool:
    if cle_carte == self.carte_courante:
        return True
    if self.carte_courante is not None:
        self.archives_cartes[self.carte_courante] = self.souvenirs
    connue = cle_carte in self.archives_cartes
    self.souvenirs = self.archives_cartes.pop(cle_carte, [])
    self.carte_courante = cle_carte
    ...
```

### Les invariants préservés

| Invariant | État |
|---|---|
| **v39.0** — une coordonnée n'est jamais lue hors de sa carte | ✅ **renforcé** : seule la liste de la carte courante est exposée |
| **v39.0** — `empreinte_types` (le QUOI) reste transversale | ✅ inchangé |
| **v36.0** — rien n'est nommé | ✅ `cle_carte` est opaque, jamais interprétée |
| **v31.0** — éviction par le moins confirmé | ✅ inchangé, s'applique par carte |
| Greffe par recopie, jamais par exclusion | ✅ `.get()` défensif, un `.brain` v41.9 repart avec une seule carte |

`reinitialiser_niveau()` est **conservée** : elle reste la bonne opération pour un vrai
déménagement, et sert de témoin d'ablation.

### Vérification unitaire (9 invariants)

Test isolé de la classe, sans torch ni MiniGrid — dont le **test de fuite** :

```python
# INVARIANT v39.0 : (1,2) de A ne doit PAS être visible depuis B
assert (1, 2) not in {s['pos'] for s in m.souvenirs}

# LE POINT DU CORRECTIF : la récurrence s'accumule d'un passage à l'autre
m.enregistrer_evenement((1, 2), "goal", 300, intensite=1.0)
assert goal['confirmations'] == 2   # sans le correctif : restait à 1
```

✅ 9/9.

### Effet immédiat (run de 3 jours, graine 1)

| | Témoin (v41.9) | Variante (v41.10) |
|---|---|---|
| Cartes en mémoire | 1 | **4** |
| Repères au total | 16 | **33** |
| Cartes retrouvées | 0 | **3** |
| Confirmations / repère | — | **10,0** |

**3 retrouvailles sur 6 bascules en 3 jours** : la moitié des changements de carte
ramenait sur une carte connue dont les repères étaient détruits.

---

## 3. Ce que la lave ne dit pas

Le scan relevait une anomalie : `lava` porte une valence **positive** (+0,069) alors que
la lave tue.

### La mesure

```
300 épisodes MiniGrid-LavaGapS5, marcheur aléatoire :
  morts dans la lave : 206
  récompense associée — min/max/moyenne : (0, 0, 0.0)
```

**MiniGrid punit la mort par exactement `0.0`.** Le même `0` qu'un pas dans le vide.

### Ce que ça implique

Le canal n'est pas cassé. `_memoriser_si_saillant` reçoit `recompense_interne`, qui au
tick de la mort ne contient que le `r_bio` du moment — souvent légèrement positif.
L'agent enregistre fidèlement *« ici j'allais bien »*, puis l'épisode s'arrête sans que
rien ne lui dise pourquoi.

Comparaison éloquente :

| Événement | Coût pour l'agent |
|---|---|
| toucher un mur (`MALUS_DOULEUR`) | −0,01 |
| **mourir dans la lave** | **0,00** |

Toucher un mur coûte **infiniment plus cher que mourir**.

### La thèse de l'utilisateur (16/08)

> *« C'est peut-être lié au C1 qui doit faire la corrélation nouveau = prudence, et faire
> la liaison lave = danger. Mais doit être en plus dit par un adulte, car n'importe quel
> enfant (animal ou humain) ne distingue pas seul ce qui est dangereux, c'est l'expérience
> transmise. »*

La mesure appuie cette lecture. L'apprentissage par l'expérience suppose qu'il **y ait**
une expérience : un enfant qui touche le feu ressent la brûlure et corrige. Ici la lave ne
brûle pas — **elle éteint**. L'agent qui meurt n'apprend rien, il cesse d'exister, et le
tick suivant appartient à un autre épisode.

⚠️ **Aucun correctif n'est écrit à ce stade**, pour deux raisons :

1. **Ce n'est pas le blocage actuel.** `LavaGapS5` est le niveau 5 ; l'agent plafonne au
   niveau 3. Le `lava +0,069` provient des rares incursions P17 (×1 confirmation sur un
   run de 3 jours). Corriger ici serait optimiser un étage que l'agent n'habite pas.
2. **La forme du correctif est une décision de conception, pas une évidence.** Écrire
   `si mort → malus` serait un `if` en dur sur un type nommé, ce que le projet refuse
   (invariant v36.0 : aucune table `lava = danger`). Les pistes non arbitrées :
   - une **fin d'épisode sans récompense** perçue comme une saillance négative dérivée
     (l'absence de clôture positive **est** l'information) ;
   - un canal d'**accompagnement** — la thèse « dit par un adulte » — qui existe déjà en
     germe dans le module Parent (v25.0) et le Port C3 (v28.0) ;
   - une **prudence face au nouveau** côté C1, dérivée de l'erreur JEPA plutôt que du
     type rencontré.

### La réponse de l'utilisateur — et l'implémentation (v41.11)

> *« Peut-être que MiniGrid manque de gradation (2 cases de lave = chaud / 1 case =
> brûlant / sur la case = mort). Et quand on est mort = 0 XP = mort ! »*

C'est le bon angle, et il déplace le problème : **le manque n'est pas la punition, c'est le
gradient.** Deux mesures supplémentaires l'ont confirmé avant d'écrire une ligne :

```
vecteur bio, juste à côté de la lave : [0. 0. 1. 0. ... 0.5 0.5]
vecteur bio, à trois cases           : [1. 0. 1. 0. ... 0.5 0.5]   (le 1.0 est un MUR)
```

**Identiques.** Et la lave figurait dans `TYPES_BLOQUANTS_ODORAT` : elle *arrêtait* l'odeur
sans jamais en *émettre* — une cloison, jamais une source. La vue, elle, la code en `9`,
un symbole discret que rien ne distingue de `1` (sol) ou `8` (but).

L'agent était donc **aveugle au danger dans tous ses sens**, et incapable d'apprendre par
l'expérience puisqu'il n'y a pas d'expérience : celui qui meurt n'apprend rien.

**Le correctif : `DIM_THERMOCEPTION = 2`, en queue du vecteur bio (37 → 39).** La chaleur
réutilise la machinerie olfactive à l'identique — le danger devient « une odeur de plus ».

| Distance à la lave | Chaleur perçue |
|---|---|
| **sur la case** | **1,000** *(mort)* |
| **adjacent** | **0,449** *(brûlant)* |
| **2 cases** | **0,202** *(chaud)* |
| carte sans lave | **0,000** *(exact)* |

Exactement la gradation demandée. Détail notable : sur `LavaGapS5` le **but est à 0,202** —
il jouxte le danger, et l'agent le sentira.

**Pourquoi un champ et pas un malus.** `si mort → récompense −= X` serait un seuil en dur
sur un type nommé, ce que l'invariant v36.0 interdit. Un champ est un **sens** : sa
signification s'apprend, elle ne se déclare pas. Le nom `lava` n'apparaît que dans
`bus_sensoriel.py` — au même titre que `red`/`blue` désignent nourriture et eau depuis la
v29.0. `noyau.py` ne reçoit que deux nombres.

**Vérifications** : clinotaxie thermique correcte dans les deux sens (approche 0,624 /
recul 0,376) ; non-régression **exacte** `(0.0, 0.5)` sur Empty-5x5, DoorKey-6x6,
Empty-8x8 ; greffe `.brain` **101 → 103 dims sans exclusion**, validée sur deux nuits
complètes.

**Première mesure, ligne de base** : l'agent **approche du danger 69–80 % des ticks de
variation**. Il ne le fuit pas du tout — ce qui est attendu, le sens vient de naître.
`Thermo_Taux_Approche` doit décroître si l'agent apprend ; stable, le sens sera perçu mais
inexploité.

⚠️ **Ce que ça ne règle PAS** : la mort reste à `0.0`. La thermoception donne à l'agent de
quoi *anticiper* le danger, pas de quoi *savoir* que mourir est mauvais. La question du
« 0 XP = mort » reste entière et non arbitrée.

---

## 4. Campagne A/B en cours

**Protocole conforme à la règle de mesure** (`CLAUDE.md`) :

| | |
|---|---|
| Test A/A préalable | ✅ deux runs graine 7 → empreinte **bit-identique** (md5 égal) |
| Ablation vérifiée | ✅ 1 carte vs 4, 0 retrouvaille vs 3 — le témoin diffère réellement |
| Graines | **20 par bras** (jamais de conclusion sous 20) |
| Mondes | identiques des deux côtés (reproductibilité v41.9) |
| Durée | 2500 jours |
| Intervalles de confiance | Wilson, obligatoires à côté de chaque taux |

Le drapeau `--sans-memoire-cartes` suit le motif d'écriture-dans-le-module-nommé + assertion
runtime posé après le bug v41.4 (où une ablation muette avait produit une campagne entière
de résultats faux).

**Résultats à venir.** Aucune conclusion ne sera tirée avant la fin des 40 runs et le
calcul des intervalles.
