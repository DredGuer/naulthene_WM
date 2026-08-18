# Rapport de nuit — 18→19 août 2026

**Photo horodatée.** Travail mené pendant la nuit, sur consigne : laisser finir les runs,
mesurer, préparer la thermohoméostasie, mettre la doc à jour.

---

## ✅ 3 avancées

### 1. La cause du coût de la douleur est TROUVÉE — et ce n'est pas ce que j'avais dit

La v41.25 faisait chuter la survie (8,57 % → 6,71 %). J'avais d'abord conclu « c'est
métabolique ». **C'était faux** : `self.chaleur` ne touche ni l'énergie, ni la satiété, ni
la dépense — vérifié dans le code.

La cause est **comportementale**, et elle est chiffrée :

| ressources récoltées/jour | douleur ON | témoin | écart |
|---|---|---|---|
| `LavaGapS5` | 8,88 | 11,98 | **−26 %** |
| `LavaCrossingS9N1` | 10,24 | 13,73 | **−25 %** |

**Le même −25 % sur deux cartes sans rien de commun** (5×5 vs 9×9, 2 vs 6 cases de lave,
trajet 4 vs 12 cases). Sur ces cartes les ressources sont à **1,23 case** de la lave en
moyenne : **fuir la lave, c'est fuir le garde-manger**.

### 2. La v41.26 est implémentée, vérifiée au banc, et lancée

Les quatre paliers **émergent** de la formule, aucun n'est codé :

| distance | chaleur | douleur | palier |
|---|---|---|---|
| 0 | 1,0000 | **1,000000** | 4. intense (dégât) |
| 1 | 0,4573 | 0,112629 | 3. douloureux |
| 2 | 0,2091 | 0,002078 | 2. gênant |
| 3 | 0,0956 | **0,000000** | **1. ça va — ZÉRO EXACT** |

**La durée** (l'agent reste à distance 1) : 0,113 → 0,160 → 0,236 → **0,329** en 8 ticks.
**La dissipation** : 0,103 après 6 ticks hors du danger.

**Rien n'est empilé** — l'habituation est le *même* cliquet que `reference_choc_dopamine`
(v37.1). Aucune jauge « adrénaline » ou « endorphine » ajoutée.

### 3. Le banc `LavaCrossing` a bouclé et confirmé le diagnostic

10 paires complètes : survie ON 0,58 % [0,32–1,07] contre OFF 2,03 % [1,62–2,55],
`t = −4,32`. **La dégradation se reproduit sur une carte totalement différente** — ce
n'était donc pas une particularité de `LavaGap`.

---

## ⛔ 3 retards

### 1. Mon diagnostic « métabolique » était une corrélation prise pour une cause

J'ai vu l'énergie basse chez le bras ON (0,156 vs 0,259) et j'ai nommé la cause sans
vérifier le mécanisme. Le code montre que la chaleur **ne prélève rien**. La rectification
est portée dans le carnet, le CHANGELOG et les README — pas seulement dans le nouveau
document.

### 2. Le banc a réfuté ma première implémentation — deux fois

- **L'habituation montait trop vite.** J'avais repris le cliquet de
  `reference_choc_dopamine` tel quel (montée immédiate) : elle rattrapait la chaleur en
  **un tick**, l'excès tombait à zéro, et **la brûlure DÉCROISSAIT pendant que l'agent
  restait dans le feu** (0,0956 → 0,0307 en 8 ticks) — l'inverse exact du palier 3.
- **Le palier 1 n'avait pas de vrai zéro** : `T³` vaut `0,000084` à distance 4. Un epsilon
  n'est pas un lieu de repos.

Les deux sont corrigés **avant** le lancement de la campagne. C'est le banc qui les a
trouvés, pas moi — ce qui valide l'interdiction de recalculer une grandeur à la main.

### 3. Une hypothèse antérieure définitivement tombée

Le carnet de campagne avançait que « sur `LavaGap` le but est derrière la lave ». Vérifié :
le chemin sûr existe sur **10/10 graines** et le détour coûte **+0,0 case** dans les deux
environnements. **Éviter la lave n'a jamais rien coûté géométriquement.** Rétractation
portée partout où l'affirmation figurait.

---

## 💡 3 améliorations

### 1. ⚠️ Ne pas conclure la v41.26 sur `LavaGapS5` seul — priorité haute

Sur une carte 5×5, **aucune case n'est à distance ≥ 3 de la lave** (77 % à d=1, 23 % à
d=2). Le lieu de repos **n'existe pas géométriquement**.

```
cases INDOLORES — LavaGapS5        :  0 %
cases INDOLORES — LavaCrossingS9N1 : 11 %
```

La gradation divise la douleur moyenne par ~2 (0,16 → 0,087) mais **ne peut pas créer un
repos absent de la carte**. Si la campagne en cours donne un effet nul, il faudra la
rejouer sur `LavaCrossing` avant de conclure quoi que ce soit sur la formule.

### 2. Le critère de lecture est la RÉCOLTE, pas la survie

C'est le mécanisme causal identifié (−25 %, reproduit deux fois). Si la gradation ne fait
pas remonter la récolte, la piste est mauvaise — indépendamment de ce que dit la survie.
Ordre de lecture : **récolte → énergie → survie → valence**.

### 3. Décision en attente : que faire si la gradation ne suffit pas

Deux options, non arbitrées :
- **accepter le coût** — la douleur est biologiquement juste, elle coûte 3,1 points de
  survie sur ce banc, et c'est un résultat publiable tel quel ;
- **découpler la fuite de la faim** — piste ouverte, mais elle demande de repenser la
  structure de `D(t)`, pas d'ajouter un terme.

---

## 📊 État des campagnes au moment du rapport

| campagne | état |
|---|---|
| ROI v41.24 (n=20) | ✅ **terminée** — `r = +0,018`, la taille du bus n'explique rien |
| Nociception v41.25 (n=20) | ✅ **terminée** — valence −0,761 sur 20/20, survie −3,1 pts |
| `LavaCrossing` (n=10) | ✅ **terminée** — dégradation reproduite, `t = −4,32` |
| **Thermohoméostasie v41.26** | 🔄 **en cours** — 20 graines × 2 bras × 300 j |

## 🔧 Commits de la nuit

```
26473ac  merge: v41.26 thermohomeostasie — douleur graduee en 4 paliers
a8c49b7  feat(homeostasie): v41.26 thermohomeostasie
621044c  merge: diagnostic du cout de la douleur — metabolique, pas cognitif
789f070  merge: campagne nociception n=20
78bab95  merge: revue du dogme avant publication
```

Tous poussés sur `master`. Règle de miroir respectée (les deux README portent les mêmes
chiffres).
