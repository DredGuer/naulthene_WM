# La thermohoméostasie — de la douleur chronique à la douleur graduée

**18/08/2026, nuit** — carnet de recherche, non normatif.
Gradation posée par l'utilisateur ; décision : **la douleur est conservée**.

---

## 1. Le défaut de la v41.25 : une douleur sans zéro

`douleur = T²` est **continue et jamais nulle**. Mesuré sur les cartes du banc :

| | LavaGapS5 | LavaCrossingS9N1 |
|---|---|---|
| Distance moyenne case libre → lave | **1,23 case** | 2,51 cases |
| Cases à chaleur > 0,10 | **100 %** | 98 % |
| Cases à chaleur > 0,25 | **77 %** | **77 %** |

> **L'agent n'avait aucun lieu de repos.** Son déficit restait creusé partout, `r_bio`
> négatif en permanence, et il fuyait sans jamais pouvoir cesser de fuir.

### La cause n'était PAS métabolique

Vérification du code : `self.chaleur` ne touche **ni** `energie`, **ni** `satiete`, **ni**
`hydratation`, **ni** la dépense. Aucun gage métabolique n'est prélevé.

La chaîne réelle est **comportementale** :

```
douleur permanente → évitement permanent → moins de nourriture atteinte
                   → énergie basse → vigueur au plancher → C2 éteint
```

| (dernier quart) | ON | OFF | écart |
|---|---|---|---|
| Ressources récoltées/j — **LavaGap** | 8,88 | 11,98 | **−26 %** |
| Ressources récoltées/j — **LavaCrossing** | 10,24 | 13,73 | **−25 %** |

**Le même −25 % sur deux cartes sans rien de commun.** Sur ces cartes les ressources sont
à ~1,2 case de la lave : **fuir la lave, c'est fuir le garde-manger**.

⚠️ *Correction d'un diagnostic antérieur* : j'avais d'abord conclu « c'est métabolique ».
C'était une corrélation (énergie basse chez ON) prise pour une cause. Le mécanisme est
comportemental — la douleur ne consomme rien, elle **éloigne**.

---

## 2. La gradation — les quatre paliers

Formulation utilisateur :

| Palier | Description | Propriété mathématique requise |
|---|---|---|
| 1 | « ça va, c'est chaud » | douleur **rigoureusement nulle** |
| 2 | « gênant mais supportable » | croissance très lente |
| 3 | « douloureux, tenable quelques secondes » | croissance rapide **+ cumul temporel** |
| 4 | « intense, recul réflexe, dégât » | explosif |

Deux éléments manquaient à la v41.25 : **un seuil de perception** (palier 1) et **la
durée** (palier 3 — « quelques secondes » implique que rester coûte).

### La forme retenue

```
seuil    = max(FRACTION × habituation, plancher)        ← le palier 1, DÉRIVÉ du vécu
instant  = ((T − seuil) / (1 − seuil))³                 ← les paliers 2/3/4
brûlure  = brûlure × (1 − dissipation) + instant        ← la durée
douleur  = min(1, instant + brûlure)
```

**Rien de neuf n'est empilé** : `habituation` est le **même cliquet** que
`reference_choc_dopamine` (v37.1), déjà validé. Aucune jauge « adrénaline » ou
« endorphine » n'est ajoutée — la structure produit ces effets d'elle-même.

### Vérification au banc (`banc_gradation_douleur.py`)

```
dist  chaleur   douleur    palier
   0   1.0000  1.000000    4. intense (dégât)
   1   0.4573  0.112629    3. douloureux
   2   0.2091  0.002078    2. gênant
   3   0.0956  0.000000    1. ça va — ZÉRO EXACT
   4   0.0437  0.000000    1. ça va — ZÉRO EXACT
```

**La durée** (distance 1, l'agent reste) :

```
tick 1 : 0.113    tick 2 : 0.160    tick 4 : 0.236    tick 8 : 0.329
```

Supportable un instant, insupportable si l'on s'attarde — exactement le palier 3.
**Dissipation** : après 6 ticks hors du danger, 0,103 (la brûlure s'apaise).

---

## 3. Deux défauts trouvés par le banc, et corrigés

Le banc a fait son travail : il a réfuté la première implémentation.

**(a) L'habituation montait trop vite.** J'avais repris le cliquet de
`reference_choc_dopamine` tel quel — montée **immédiate**. Conséquence : l'habituation
rattrapait la chaleur en **un tick**, l'excès tombait à zéro, et la brûlure **DÉCROISSAIT
pendant que l'agent restait dans le feu** (0,0956 → 0,0307 en 8 ticks). L'inverse exact du
palier 3 — une brûlure ne s'apaise pas parce qu'on reste dedans.

Correctif : montée **lente** (`0,02/tick`), descente 10× plus lente encore. L'habituation
est une adaptation de **centaines de ticks**, pas une réaction du tick.

**(b) Le palier 1 n'avait pas de vrai zéro.** `T³` sans seuil vaut `0,000084` à distance 4
— un epsilon, pas un zéro. Un nocicepteur réel a une **intensité minimale d'activation**.
Correctif : seuil de perception **relatif à l'habituation**, donc dérivé du vécu (deux
agents d'histoires différentes n'ont pas le même palier 1).

---

## 4. ⚠️ Une limite que la gradation ne peut pas lever

```
cases INDOLORES — LavaGapS5        :  0 %
cases INDOLORES — LavaCrossingS9N1 : 11 %
```

Sur `LavaGapS5`, **aucune case n'est à distance ≥ 3 de la lave** : 77 % sont à d=1, 23 % à
d=2. Le lieu de repos n'existe **pas géométriquement** sur une carte 5×5.

La gradation **divise la douleur moyenne par ~2** (0,16 → 0,087) mais ne peut pas créer un
repos absent de la carte. **C'est une limite du banc, pas du mécanisme** — et il faut
l'énoncer avant de lire les résultats, sinon un effet nul serait attribué à la formule
alors qu'il viendrait de la géométrie.

---

## 5. Campagne en cours

**20 graines × 2 bras × 300 jours** sur `LavaGapS5` (lancée à 23h50).

- bras **GRAD** : douleur graduée v41.26
- bras **OFF** : `--sans-douleur` (témoin)

Critères, dans l'ordre d'importance :

1. **La récolte de nourriture remonte-t-elle ?** C'est le mécanisme causal identifié
   (−25 % en v41.25, reproduit sur deux cartes). Si la gradation ne le corrige pas, la
   piste est mauvaise.
2. La survie rejoint-elle celle du témoin ?
3. La valence de la lave reste-t-elle négative ? (elle doit — sinon la gradation a tué
   l'apprentissage en même temps que la douleur chronique)

⚠️ Aucune conclusion ne sera tirée sous 20 graines, chaque taux sera donné avec son
intervalle de Wilson, et le point §4 devra être rappelé à la lecture.
