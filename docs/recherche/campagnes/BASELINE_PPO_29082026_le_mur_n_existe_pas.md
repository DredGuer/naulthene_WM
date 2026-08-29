# 29/08/2026 — La ligne de base PPO : le mur informationnel n'existe pas

> Non normatif — carnet d'enquête. Remplit la ligne vide du §3 des README, ouverte depuis
> la création du dépôt.

## Pourquoi cette mesure était le trou le plus structurant

Quatre grandeurs mesurées avec soin cette semaine, **quatre sans échelle** :

| Mesure Naulthène | Anormal ? |
|---|---|
| dérive de l'axe : 0,42 °/nuit | inconnu |
| séparabilité `but visible` : d' = 3,0 | inconnu |
| plafond de probabilité : 18 % | inconnu |
| alignement W↔axe qui recule | inconnu |

Sans référence externe, aucune ne peut être qualifiée — le défaut exact que le projet
reproche à `SEUIL_CRISTAL = 0,80`.

## Protocole — équité verrouillée avant tout entraînement

| Point | Réglage | Pourquoi |
|---|---|---|
| Observation | 7×7×3 **aplatie** (147), `MlpPolicy` | `porte_visuelle` est **linéaire**, sans convolution : un CNN donnerait à PPO un biais spatial que Naulthène n'a pas |
| Actions | **7**, pas 8 | Naulthène masque `ACTION_DEMANDER` à `-inf` (invariant v30.0) |
| Budget | **152 043 pas** | 🔴 **mesuré** dans `tick_absolu` d'un cerveau à 400 jours — le nominal 400×400 = 160 000 est faux |
| Récompense | brute MiniGrid | aucun shaping |
| Env | `SimpleCrossingS9N1` | le niveau où l'agent plafonne |

**Trois architectures, pas une.** Égaliser au total de 55 616 aurait donné à PPO **1,8× le
budget décisionnel réel** : 45 % des paramètres de Naulthène achètent l'audio, le JEPA, le
bio et l'exocortex. Le cœur RL comparable fait **30 464**.

**δ_A/A = 0,000000** sur les 5 métriques (2 runs identiques, 152 043 pas). Le banc est
strictement déterministe : **tout écart mesuré est réel**, aucun plancher de bruit.

## Résultats — 60 runs (3 architectures × 20 graines)

| Architecture | Params | Réussite | Proba favorite | Entropie | d' |
|---|---|---|---|---|---|
| PPO `[37,37]` | 14 068 | **36,2 % ±13,3** | **35,45 % ±5,33** | 1,667 | 0,697 |
| PPO `[69,69]` | 30 644 | **39,8 % ±11,7** | **35,13 % ±5,08** | 1,681 | 0,647 |
| PPO `[107,107]` | 55 648 | **27,1 % ±10,8** | **34,73 % ±3,88** | 1,704 | 0,644 |
| **Naulthène** | 55 616 | **~16 %** | **15,00 %** | **1,930** | **2,891–3,613** |

*(plafond géométrique de Naulthène : 18,00 % · entropie max ln(7) = 1,9459)*

### [1] Le mur informationnel n'existe pas

PPO atteint **34,7–35,5 %** de probabilité sur l'action favorisée — **près du double du
plafond géométrique de 18,00 %** que la représentation de Naulthène autorise. Les trois
architectures tiennent dans un intervalle de **0,7 point** : c'est une propriété stable, pas
un réglage heureux.

**Le plafond est une pathologie de Naulthène**, pas une limite de MiniGrid. C'était l'issue
la moins confortable des deux prévues au protocole, et c'est celle qui sort.

### [2] La capacité n'est pas en cause

`r(params, réussite) = −0,1519` (`t = −1,17`, NS). Un PPO de **14 068 paramètres** — **4×
plus léger que le cœur RL de Naulthène** — réussit **2,3× mieux**. Le bras le plus gros est
même le moins bon (27,1 %). L'hypothèse « le cerveau est sous-dimensionné pour le niveau 4 »
est écartée.

### [3] Le d' n'est ni dimensionnel, ni utile

`r(params, d') = −0,1097` (NS) : élargir de 37 à 107 dims ne change pas la séparabilité.
L'écart avec Naulthène est donc **architectural**, pas une affaire de largeur —
l'explication dimensionnelle envisagée est écartée.

Et surtout : **`r(d', réussite) = −0,0368`** (`t = −0,28`). Une meilleure séparation des
représentations n'achète **aucune** performance.

🔴 **Cela renverse la lecture de deux jours de mesures.** Le d' élevé de Naulthène
(2,891–3,613) avait été lu comme un signe de santé — « le tronc amplifie », « le JEPA fait
son travail ». PPO réussit **2,3× mieux avec un d' 4,5× plus faible**. Une représentation
géométriquement propre n'est pas le prérequis d'une bonne politique ; elle peut être
décorative.

### [4] La dérive ne prédit rien — sur une seconde architecture

`r(dérive, réussite) = −0,2066` (`t = −1,61`, NS) **chez PPO**. La quinzième réfutation
tient désormais sur **deux architectures indépendantes**.

PPO dérive par ailleurs **beaucoup** : ~31 °/jalon de 25 340 pas, contre 0,42 °/nuit de
380 pas chez Naulthène. ⚠️ Le rapport « ×10 par pas » qu'on peut en tirer est un **ordre de
grandeur, pas une mesure** : les unités de temps d'apprentissage diffèrent (PPO fait ~124
updates par jalon, Naulthène 1 par nuit). Le fait solide est que **PPO dérive massivement et
réussit mieux.**

### [5] Le nouveau suspect : l'entropie qui ne descend jamais

C'est la brèche la plus nette après la probabilité :

| | entropie | % du maximum ln(7) |
|---|---|---|
| PPO | 1,667 – 1,704 | 85,7 – 87,6 % |
| **Naulthène** | **1,930** | **99,2 %** |

PPO converge — ses logits s'écartent, l'incertitude tombe. Naulthène reste à **99,2 % du
bruit blanc** après 400 jours. Aucune expérience accumulée ne devient une certitude motrice.

## ⚠️ Réserves

1. **Un PPO bien réglé n'est pas « la normale »** — c'est *une* référence. Un PPO mal réglé
   plafonnerait aussi. Cette mesure situe Naulthène par rapport à un point de comparaison
   qui n'existait pas, elle ne dit pas la vérité de la tâche.
2. **Les architectures ne sont pas comparables terme à terme.** Naulthène a un cycle
   jour/nuit, une neurogenèse, un métabolisme qui le tue, cinq sens. PPO n'a rien de tout
   cela. La comparaison porte sur **des grandeurs**, pas sur les agents.
3. **Le taux de réussite de Naulthène (~16 %) n'est pas mesuré dans le même protocole** que
   celui de PPO (300 épisodes, politique stochastique). L'écart de réussite est donc
   indicatif ; **la probabilité de l'action favorisée et l'entropie, elles, sont mesurées à
   l'identique** et portent la conclusion.
4. `stable-baselines3` reste une dépendance **d'instrument**, jamais importée par le cœur.

## Ce que cela ouvre

Le chantier quitte la perception, la topologie, la mémoire et le gradient. La question
devient : **pourquoi la tête motrice maintient-elle une distribution à 99,2 % du maximum ?**

Trois candidats mesurables, aucun testé :
- le **coefficient d'entropie** (`coeff_entropie`) sur-pénalise-t-il la spécialisation ?
- le **gain de C1** (`GAIN_C1_MIN/MAX`) borne-t-il l'amplitude des logits ?
- la **formulation de la perte de l'acteur** empêche-t-elle les logits de diverger ?

⚠️ Le premier est une constante posée : le mesurer avant de le rendre adaptatif est la
méthode du projet (v30.1), pas l'inverse.

## Reproduction

```bash
brains/29082026_baseline_ppo/lancer.sh
PYTHONPATH=src python -m naulthene.instruments.banc_ppo --aa --arch 69 --graine 11
```
