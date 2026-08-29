# Ligne de base PPO — protocole d'équité

**Objectif** : donner une échelle aux quatre grandeurs mesurées cette semaine et qui n'en
ont aucune.

| Mesure Naulthène | Anormal ? |
|---|---|
| dérive de l'axe informatif : **0,42 °/nuit** | inconnu |
| séparabilité `but visible` : **d' = 3,0** | inconnu |
| plafond de probabilité sur l'action favorisée : **18 %** | inconnu |
| alignement W↔axe qui **recule** | inconnu |

Sans point de comparaison externe, aucune de ces valeurs ne peut être qualifiée. C'est le
défaut que le projet reproche à `SEUIL_CRISTAL = 0,80` — une valeur posée *a priori*,
jamais confrontée à une mesure.

## Les deux issues, toutes deux informatives

| Résultat | Lecture |
|---|---|
| **PPO monte à ~80 %** sur l'action utile | le plafond à 18 % est une **pathologie de Naulthène** — et on a enfin une cible chiffrée |
| **PPO plafonne aussi vers ~20 %** | c'est une **propriété de MiniGrid** (observation 7×7 aplatie, récompense creuse), et les quinze réfutations changent de sens : elles ne cherchaient pas un défaut au bon endroit |

## Équité — ce qui est verrouillé

| Point | Réglage | Pourquoi |
|---|---|---|
| **Observation** | tenseur 7×7×3 **aplati** (147 dims), `MlpPolicy` | `porte_visuelle` est une couche **linéaire 147→64**, sans aucune convolution. Un `CnnPolicy` donnerait à PPO un biais spatial que Naulthène n'a pas |
| **Actions** | **7**, pas 8 | Naulthène masque `ACTION_DEMANDER` à `-inf` en permanence (invariant v30.0) : il en joue réellement 7. Lui en donner 8 dont une inerte handicaperait PPO là où Naulthène ne l'est pas |
| **Budget** | **152 043 pas d'environnement** | 🔴 **mesuré**, pas estimé : `tick_absolu` du cerveau A_g11 après 400 jours. Le nominal 400×400 = 160 000 est **faux** (journées écourtées) |
| **Récompense** | brute MiniGrid, **aucun shaping** | Naulthène a ses propres signaux internes, mais aucun ne vient de l'environnement |
| **Environnement** | `MiniGrid-SimpleCrossingS9N1-v0` | le niveau 4, celui où l'agent plafonne |
| **Graines** | les mêmes que la cohorte v41.34 | appariement |

## ⚠️ Le dimensionnement : pourquoi PAS un seul PPO à 55 616 paramètres

Égaliser au total de Naulthène serait **faux dans l'autre sens**. Le README l'établit déjà :
**25 088 paramètres (45 %) achètent des facultés qu'aucune baseline n'a** — hémisphère audio
(13 440), JEPA (4 608), intégrateur biologique (6 720), port exocortex (320). Le **cœur RL
strictement comparable fait 30 464 paramètres**.

Donner 55 616 paramètres à PPO lui offrirait **1,8× le budget décisionnel réel**.

**Trois bras, donc, pas un :**

| Bras | Réseau | Params visés | Question |
|---|---|---|---|
| **PPO-mince** | `[64, 64]` | ~14 k | un réseau *plus petit* que le cœur RL y arrive-t-il ? |
| **PPO-apparié** | dimensionné | ~30 k | à **budget décisionnel égal** (30 464) |
| **PPO-total** | dimensionné | ~55 k | à **budget total égal** — la lecture la plus favorable à PPO |

Si les trois plafonnent à 20 %, c'est la tâche. Si les trois montent à 80 %, c'est
l'architecture. Si seul le plus gros y arrive, c'est une question de capacité — **et aucun
bras unique ne peut distinguer ces trois cas.**

## Ce qui sera mesuré, dans les mêmes unités

1. **Taux de réussite** sur `SimpleCrossing` (comparable à la « maîtrise » de Naulthène)
2. **Probabilité de l'action favorisée** face à un état informatif — la grandeur du plafond à 18 %
3. **Entropie de la politique** (Naulthène : 1,93 sur un max de 1,946)
4. **d' de séparabilité** `but visible / but absent` dans la dernière couche cachée
5. **Dérive de cette représentation**, nuit après nuit — pour situer les 0,42 °/nuit

## Règles de mesure appliquées

- **A/A avant tout A/B** : deux PPO identiques, même graine, avant toute comparaison
- **n ≥ 20 graines**, ou le résultat est une tendance et sera annoncé comme telle
- **Bonferroni** sur les 5 métriques ⇒ seuil `t ≈ 3,5` (df=19)
- **Aucun `t` avant la fin** des runs
- Écriture directe dans `brains/29082026_baseline_ppo/`, jamais dans un scratchpad (§7)

## ⚠️ Réserves posées d'avance

1. **Un PPO bien réglé n'est pas « la normale ».** C'est *une* référence, pas la vérité de
   la tâche. Un PPO mal réglé plafonnerait aussi.
2. **Les architectures diffèrent trop pour une comparaison stricte.** Naulthène a un cycle
   jour/nuit, une neurogenèse, un métabolisme qui le tue. PPO n'a rien de tout ça. La
   comparaison porte sur **une grandeur** (le plafond de politique), pas sur les agents.
3. **`stable-baselines3` est une dépendance nouvelle**, hors du `pip install` documenté.
   Elle reste **cantonnée aux instruments**, jamais importée par le cœur.
