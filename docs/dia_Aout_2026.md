# Diagnostic complet — Naulthène AGI, août 2026

> **Nature du document** : état des lieux factuel, arrêté au 8 août 2026. Chaque affirmation est
> adossée à une mesure sur un run réel ou à une lecture du code, avec sa source. Aucune
> modification de code n'accompagne ce diagnostic — c'est un instantané, pas un chantier.
>
> **Runs de référence**
>
> | Run | Cerveau | Durée | Ce qu'il établit |
> |---|---|---|---|
> | `58ssyw19` | V36 | 600 j | Base de comparaison pré-v37 |
> | `8wequiqg` | V37.1 | 600 j | Équilibre C1/C2 ; révèle le bug de la référence |
> | `ous47258` | **V37.1-fix1** | **1300 j** | **Run principal de ce diagnostic** |
>
> Cerveau analysé : `brains/080820260027_V371fix1_1300_RMD.brain` (bus 64, 1300 nuits).

---

## ⛔ NOTE DES BLOQUANTS — à lire avant toute reprise

État au moment du merge de la branche `feat/v37-equilibre-c1-c2` sur `master`.

### Ce qui bloque l'agent (mesuré, non corrigé)

| # | Bloquant | Mesure | Où |
|---|---|---|---|
| **B1** | **Patience deux fois trop courte** | 120 ticks contre **256** natifs MiniGrid → réussite atteignable **4,7 % vs 21,0 %** | `PATIENCE_MIN/MAX`, `EXTENSION_PATIENCE_SURSAUT` |
| **B2** | **Saut de difficulté ×10 au niveau 2** | réussite aléatoire **38,2 %** (`Empty-6x6`) → **3,8 %** (`Empty-8x8`) | `PROGRAMME` |
| **B3** | **Économie de récompense négative** | espérance **−1,06** par épisode (25 % × +0,67 + 75 % × −1,63) | `ThermostatCinetique`, `PENALITE_STAGNATION_BASE` |
| **B4** | **4 actions inutiles sur 7** | 3 actions utiles → réussite **×5** (4,7 % → 23,3 %) | `num_actions` |
| **B5** | **Ère Intégration** | ×2 d'épisodes perdants au jour 600, et suppression du seul cursus qui progressait (vocal) | `BORNES_ERES = (400, 600)` |

**Aucun de ces cinq bloquants n'est cognitif.** Toutes les mécaniques du cerveau fonctionnent
(§3) — c'est l'environnement d'exercice qui rend la réussite statistiquement inatteignable.

### Défauts connus, non corrigés

| # | Défaut | Impact |
|---|---|---|
| **D1** | **Affichage : `%` en trop sur `Pourcentage_Reve`** | La valeur est une fraction (`0,177`) affichée « 0,177 % ». **A déjà causé une erreur de diagnostic propagée dans deux documents.** Cosmétique mais piégeux |
| **D2** | `Score_Spectral_Moyen_Jour = 0,000` | La composante spectrale du score vocal est morte ou jamais branchée — non investigué |
| **D3** | `SEUIL_CRISTAL = 0.80` jamais franchi | Myéline réelle max **0,007**. La Cristallisation Souple v26.0 ne s'est enclenchée sur **aucun** cerveau du dépôt |
| **D4** | `EXTENSION_PATIENCE_SURSAUT = 50` | Constante en attente de calibrage **depuis la v30.1**, jamais tranchée |
| **D5** | Déficit métabolique permanent | Jauges à 0, **100 %** des ticks en zone critique, sur tous les runs. Toute mécanique de satiété/fatigue serait calibrée sur du vide |

### Questions ouvertes (à instrumenter, pas à supposer)

| # | Question | Test qui trancherait |
|---|---|---|
| **Q1** | Le guidage ×3,0 nuit-il aux victoires ? | Ablation à graine fixée, guidage figé à 1,0, 300 jours |
| **Q2** | L'erreur JEPA qui remonte : bénin ou dégradation ? | Comparer à dimension de bus constante |
| **Q3** | L'accord C1/C2 peut-il se stabiliser ? | Indissociable du blocage — c'est un thermomètre, pas un levier |

### Ce que je recommande comme prochain run

**Un seul changement à la fois.** Le mieux mesuré est **B1** : passer la patience de 120 à 256.
C'est une constante, aucune mécanique cognitive touchée, et un facteur **4,5** en jeu sur le taux
de réussite atteignable. Si ça débloque, B2 à B5 attendront.

> ⚠️ **Rappel structurel** : tout le code des v34 à v37 vit dans
> `src/naulthene/cerveau/noyau.py`, qui est **gitignoré** (terrain d'essai local). Ce merge
> apporte la documentation, `persistance.py` et les instruments — **pas les mécaniques
> elles-mêmes**. Un clone du dépôt n'aura pas la v37.

---

## Sommaire

1. [Le résultat en une page](#1-le-résultat-en-une-page)
2. [Le blocage — anatomie complète](#2-le-blocage--anatomie-complète)
3. [Ce qui fonctionne — vérifié, chiffré](#3-ce-qui-fonctionne--vérifié-chiffré)
4. [Les formules du système](#4-les-formules-du-système)
5. [L'état biologique](#5-létat-biologique--un-régime-jamais-quitté)
6. [Le modèle du monde (JEPA)](#6-le-modèle-du-monde-jepa)
7. [Récapitulatif](#7-récapitulatif--ce-qui-marche-ce-qui-bloque-ce-qui-est-inconnu)
8. [Recommandations](#8-recommandations--par-ordre-de-retour-attendu)
9. [Erreurs de diagnostic commises et corrigées](#9-erreurs-de-diagnostic-commises-et-corrigées)

---

## 1. Le résultat en une page

L'agent **ne franchit pas le niveau 2 sur 15**, et n'a plus gagné depuis **678 jours**.

```
jour    1 → niveau 0   (Empty-5x5)
jour  272 → niveau 1   (Empty-Random-6x6)
jour  274 → niveau 2   (Empty-8x8)          ← deux paliers en deux jours
jour  275 … 1300       aucune promotion, 1 victoire en 1025 jours
```

22 victoires au total, **taux de vie 1,69 %**. Le pic (12 victoires entre les jours 200 et 300)
est le meilleur du projet ; il ne s'est jamais reproduit.

**Ce n'est pas une panne cognitive.** Toutes les mécaniques construites depuis la v18 fonctionnent
et sont mesurables. Le blocage tient à **trois facteurs qui se composent**, et le principal n'est
ni la mémoire, ni C1/C2, ni la distillation :

| # | Facteur | Chiffre |
|---|---|---|
| 1 | **Le saut de difficulté `Empty-6x6` → `Empty-8x8`** | une politique aléatoire réussit **38,2 %** puis **3,8 %** — un facteur **×10** |
| 2 | **La patience (120) est < la moitié du budget natif MiniGrid (256)** | à 256 ticks, le taux aléatoire passe de 4,7 % à **21,0 %** |
| 3 | **L'économie de récompense est perdante** | espérance **−0,97** par épisode |

---

## 2. Le blocage — anatomie complète

### 2.1 Le niveau 2 n'est pas « une pièce vide facile »

`MiniGrid-Empty-8x8-v0` : grille 8×8, **intérieur 6×6**. Agent en (1,1), but en (6,6).

Coût optimal mesuré par **BFS sur l'espace `(x, y, direction)`** — donc en comptant les rotations,
pas seulement les déplacements :

| Niveau | Optimal BFS | Patience 120 | Marge |
|---|---|---|---|
| `Empty-5x5` | **5** actions | 120 | ×24,0 |
| `Empty-Random-6x6` | **4,8** en moyenne (2 à 8) | 120 | ×24,8 |
| `Empty-8x8` | **11** actions | 120 | ×10,9 |

**La marge reste confortable (×10,9).** La patience n'est donc *pas* le facteur limitant en
théorie — ce point invalide une affirmation faite plus tôt (voir §9).

### 2.2 Mais le taux de réussite atteignable s'effondre

Mesure directe : politique **uniformément aléatoire** sur les 7 actions, 400 épisodes par niveau,
120 ticks de patience.

| Niveau | Réussite aléatoire | Pas moyens quand ça réussit |
|---|---|---|
| `Empty-5x5` | **42,8 %** | 57 |
| `Empty-Random-6x6` | **38,2 %** | 58 |
| `Empty-8x8` | **3,8 %** | 95 |

**Le taux chute d'un facteur 10 entre le niveau 1 et le niveau 2.** C'est le vrai saut de
difficulté, et il est invisible dans l'énoncé du programme : les trois niveaux s'appellent tous
« Empty ».

Le principe posé dans `CLAUDE.md` — *« une seule compétence change entre deux paliers voisins »* —
est respecté sur le papier (c'est la même tâche à trois échelles), mais **la difficulté effective
n'est pas linéaire dans la taille de la grille** : elle explose parce que la marche aléatoire
diffuse en √t alors que la distance croît en t.

### 2.3 La patience est le levier le plus direct

Toujours en politique aléatoire sur `Empty-8x8` :

| Patience | Réussite aléatoire |
|---|---|
| **120** (valeur du projet) | 4,7 % |
| 180 | 12,3 % |
| **256** (`max_steps` natif MiniGrid) | **21,0 %** |
| 400 | 28,7 % |
| 600 | 22,0 % (redescend — l'épisode est tronqué par MiniGrid à 256) |

**La patience du projet (120) est moins de la moitié du budget que MiniGrid accorde lui-même
(256).** L'agent est coupé avant d'avoir eu l'occasion statistique de réussir.

> Constantes concernées : `PATIENCE_MIN = 50`, `PATIENCE_MAX`, `EXTENSION_PATIENCE_SURSAUT = 50`.
> Cette dernière est d'ailleurs listée dans `CLAUDE.md` comme **la constante en attente de
> calibrage** depuis la v30.1.

### 2.4 L'espace d'action contient 4 actions inutiles

`Empty-8x8` n'a ni objet, ni porte, ni clé. Sur les **8 actions** exposées (7 MiniGrid +
`ACTION_DEMANDER` masquée), **4 sont sans effet** : `pickup`, `drop`, `toggle`, `done`.

Mesure : politique aléatoire limitée aux **3 actions utiles** (gauche, droite, avancer), patience
120 :

```
7 actions  →  4,7 % de réussite
3 actions  → 23,3 % de réussite     ← ×5
```

L'agent doit donc apprendre, en plus de naviguer, à **ne pas gaspiller 4/7 de ses ticks**. C'est
un coût d'apprentissage réel qui n'apparaît nulle part dans le cursus.

### 2.5 L'économie de récompense

**Formule de la pénalité de stagnation** (`ThermostatCinetique.evaluer_tick`, `noyau.py:1535`) :

```python
if pos_actuelle == historique[-1]:          penalite = base * 2.0
elif pos_actuelle in historique:            penalite = base * (1.5 ** occurrences)
penalite *= facteur_contexte
```

avec `PENALITE_STAGNATION_BASE = 0.015`, un historique borné à **6 positions**, et trois facteurs
de contexte :

| Contexte | Facteur |
|---|---|
| interaction (`pickup`/`toggle`, ou face à `Key`/`Door`/`Goal`) | ×0,05 |
| manipulation (porte un objet) | ×0,30 |
| **libre** (le cas d'`Empty-8x8`) | **×1,00** |

Barème par tick, en mode libre :

| Situation | Pénalité |
|---|---|
| Immobile (même case qu'au tick précédent) | −0,0300 |
| Case revue 1 fois dans les 6 dernières | −0,0225 |
| Case revue 3 fois | −0,0506 |
| Case revue 6 fois (maximum) | **−0,1709** |

**Récompense d'une victoire** (formule native MiniGrid) :

```
reward = 1 − 0.9 × (step_count / max_steps)     avec max_steps = 256
```

| Victoire en… | Récompense |
|---|---|
| 14 pas | +0,951 |
| 60 pas | +0,789 |
| 120 pas | +0,578 |

**Bilan mesuré** (100 derniers jours du run de 1300 j) :

```
pénalité de stagnation :  −6,54 / jour  sur 4 épisodes  =  −1,63 / épisode
                       :  soit −0,0136 par tick  →  8 % du pire cas théorique
taux de réussite       :  25 %
gain moyen d'une victoire (≈95 pas) : +0,67

Espérance = 0,25 × (+0,67) + 0,75 × (−1,63) = −1,06
```

**Un épisode a une espérance négative.** Dans ce barème, ne pas s'épuiser à chercher est la
stratégie rationnelle — et c'est exactement ce que l'agent a appris.

> **Nuance importante** : la pénalité mesurée est à **8 % du maximum théorique**. L'agent **ne
> piétine pas**. Il fait 8,9 nouveaux records de proximité au but par jour : il *avance*, il
> n'arrive simplement pas à temps. Le problème n'est pas un agent bloqué contre un mur, c'est un
> agent qui progresse trop lentement pour le budget qu'on lui laisse.

### 2.6 L'ère « Intégration » double la charge sans contrepartie

`BORNES_ERES = (400, 600)` (`noyau.py:3370`) — au jour 600, l'après-midi vocal devient du MiniGrid.

| Ère | Matin (200 ticks) | Après-midi (200 ticks) | Épisodes MiniGrid/jour mesurés |
|---|---|---|---|
| `alternance` (< 400) | MiniGrid | vocal isolé | 2,1 |
| `synesthesie` (400-599) | MiniGrid + audio | vocal isolé | 2,0 |
| `integration` (≥ 600) | MiniGrid | **MiniGrid** | **4,0** |

Bascule mesurée au jour exact :

```
jour 599 : 2 épisodes, 1 abandon, stagnation −3,0
jour 601 : 4 épisodes, 3 abandons, stagnation −7,2
```

**Le doublement de la pénalité au jour 600 n'est pas une aggravation cognitive** : l'agent joue
simplement deux fois plus. La pénalité *par épisode* est stable depuis le jour 300 (≈ −1,6).

Mais l'effet net est négatif : deux fois plus d'épisodes à espérance négative, et **le sacrifice
du seul cursus qui progressait encore** (le vocal, palier 19).

### 2.7 Le guidage — corrélation non démontrée

```
jours 200-300 : guidage ×1,00 → 12 victoires   (le pic du projet)
jours 400-600 : guidage ×3,00 →  0 victoire
```

Le filet v35.1 amplifie `recompense_continue`, `micro_recompense_progres` et `poids_progres` —
donc les récompenses **de progression**. Hypothèse : en amplifiant l'approche, il rend
*s'approcher* plus payant qu'*arriver*.

**Non démontré.** La causalité peut être inverse : le filet monte *parce que* l'agent ne gagne
plus (`JOURS_AVANT_RENFORT = 30`, montée jusqu'à `RENFORT_AIDE_MAX = 3.0`). Un test d'ablation à
graine fixée, guidage figé à 1,0, trancherait en un run.

---

## 3. Ce qui fonctionne — vérifié, chiffré

### 3.1 La santé synaptique — le chantier v37 a tenu

Sonde des poids (`sonde_poids.py`) sur le cerveau à 1300 jours, ratio = `‖base‖ / norme_naissance` :

| Couche | Avant v37 (V36, 600 j) | Après v37 (1300 j) |
|---|---|---|
| `porte_visuelle` | 16,18 % | **82,06 %** |
| `hippocampe` | 25,03 % | **67,60 %** |
| `fusion_memoire` | 22,88 % | **74,37 %** |
| `analyseur` | 21,07 % | **61,88 %** |
| `integrateur_bio` | 13,25 % | **101,35 %** |
| `tete_motrice` | **10,00 %** (plancher) | **40,78 %** |
| `cortex_prefrontal` | **10,00 %** (plancher) | **87,96 %** |
| `generateur_attente` | **10,00 %** (plancher) | **48,83 %** |
| `tete_requete` | **10,00 %** (plancher) | **10,00 %** (plancher) |
| `porte_auditive` | 21,75 % | **115,83 %** |
| `tete_vocale` | **10,00 %** (plancher) | **90,32 %** |
| `generateur_attente_audio` | 12,59 % | **73,69 %** |
| **Couches au plancher** | **5 / 12** | **1 / 12** |
| **Synapses mortes (cumul)** | — | **0** |

Les trois correctifs de la v37.0 sont **validés sur le double de la durée** qui a servi à les
écrire. Le cerveau n'est plus en voie d'extinction : il grossit (`integrateur_bio` et
`porte_auditive` dépassent leur norme de naissance).

`tete_requete` reste au plancher — **normal et attendu** : elle sert au routage C3, aucun plug
n'est branché, elle ne reçoit aucun gradient. Ce n'est pas une pathologie.

Myéline mesurée : **0,0032 à 0,0070** selon les couches. Rappel : `SEUIL_CRISTAL = 0.80` n'a
**jamais** été franchi sur aucun cerveau du dépôt — la Cristallisation Souple v26.0 ne s'est
enclenchée nulle part.

### 3.2 Le rêve — fonctionne (correction d'une erreur de diagnostic)

`Pourcentage_Reve` est logué comme une **fraction** (`0,177`) mais affiché suivi d'un `%` — ce qui
donne « 0,177 % » à l'écran alors que la valeur réelle est **17,7 %**.

Vérification arithmétique :

```
Nb_Reves = 61,  Pourcentage_Reve = 0,153
61 / 0,153 = 398 ≈ len(memoire_moyen_terme) sur 400 ticks ✅
```

| Tranche | % rejoué | Rêves/nuit | Nuits sans rêve |
|---|---|---|---|
| 0-200 | 4,7 % | 8,4 | **110 / 200** |
| 200-400 | 8,2 % | 16,3 | 14 / 200 |
| 400-600 | 15,3 % | 30,6 | **0** |
| 800-1000 | 11,9 % | 47,5 | **0** |
| 1200-1300 | **17,7 %** | **70,5** | **0** |

**Le rêve monte régulièrement** (8 → 70 rêves/nuit). Les nuits sans rêve du début sont réelles
(plasticité basse chez un cerveau neuf) et **disparaissent totalement après le jour 400**.

> 🐛 **Défaut d'affichage à corriger** : le `%` en trop dans le bilan console de `executer_nuit`.
> Il a provoqué une erreur de diagnostic propagée dans deux documents (voir §9).

### 3.3 L'équilibre C1/C2 — acquis, mais l'accord est un thermomètre

| Run | Ratio C2/C1 | Accord |
|---|---|---|
| Avant v37 | **9,9× à 22,1×** (dérivant selon la carte) | **0 %** partout |
| V37.1-fix1, 1300 j | **0,58 à 1,12** | **5,8 % à 85,3 %** |

Trajectoire complète de l'accord :

| Tranche | Accord | Ratio | Contexte |
|---|---|---|---|
| 0-100 | 44,6 % | 0,90 | |
| 200-300 | **85,3 %** | 0,58 | ← **pic de 12 victoires** |
| 400-500 | 84,1 % | 0,61 | |
| 800-900 | 63,5 % | 1,00 | |
| 1100-1200 | 24,4 % | 0,95 | |
| 1200-1300 | **5,8 %** | 1,12 | ← après 1000 j sans victoire |

**L'accord suit les victoires au lieu de converger.** Ce n'est pas une propriété stable de
l'architecture, c'est un **indicateur** : quand l'agent trouve quoi faire, ses deux systèmes
s'accordent. Traiter l'accord comme un levier serait confondre le thermomètre et la fièvre.

### 3.4 Le cliquet de la référence (v37.1-fix1) — correctif validé

| | Run 600 j (bug) | Run 1300 j (corrigé) |
|---|---|---|
| Dérive de `reference_choc_dopamine` | **−57 %** | **−7,4 %** (sur 2× plus long) |
| Crédit de distillation | 10 % → **69 %** | 12 % → **30 %** |

Et le comportement voulu apparaît :

```
jours   0-100 : référence 0,2184
jours 300-400 : référence 0,2332   ← elle MONTE
jours 1200-1300: référence 0,2022
```

La référence **monte** pendant 400 jours — l'agent relève sa barre en découvrant qu'il peut vivre
mieux — puis redescend très lentement. C'est exactement le principe visé : *un expert est plus
difficile à impressionner*.

### 3.5 Les cinq sens — tous actifs

| Sens | Mesure (200 derniers jours) |
|---|---|
| Bus sensoriel | **actif 100 %** des ticks |
| Toucher (contact) | 42,0 % des ticks |
| Toucher (portage) | 15,0 % |
| Odorat (ticks actifs) | **91,7 %**, intensité moyenne 0,225 |
| **Odorat (taux d'approche)** | **63,4 %** — contre 50 % au hasard |
| Goût | 14,7 ticks/jour |

Le **taux d'approche olfactive à 63,4 %** est un résultat notable : la clinotaxie v32.0 fonctionne,
l'agent remonte les gradients d'odeur mieux qu'au hasard. C'est une preuve directe que les sens
faibles influencent réellement le comportement via `integrateur_bio`.

### 3.6 La mémoire v36 — le mécanisme tourne à plein

| Métrique | Valeur (200 derniers jours) |
|---|---|
| **Confirmations par repère** | **108,4** (contre 1 avant la v36) |
| Types distincts | 5 |
| **Ratio de rappel** | **73,0 %** des ticks |
| Valence moyenne | 0,083 |
| Taille de la mémoire spatiale | 90 repères |
| Doublons convertis en abstraction | **11 228** |
| Saturation | 45 % |

L'abstraction par récurrence est le mécanisme **le plus incontestablement fonctionnel** du projet.

### 3.7 Le vocal — la seule progression continue

**Palier vocal 19**, score moyen 0,466. Seul cursus du projet encore en progression en fin de run.

⚠️ `Score_Spectral_Moyen_Jour = 0,000` sur les 200 derniers jours, alors que
`Score_Formants_Moyen_Jour = 0,466`. La composante spectrale du score vocal est **morte ou jamais
branchée** — à investiguer.

### 3.8 Neurogenèse

```
bus : 16 → 64 dims        empreinte_enfance : 1,000 → 0,250
```

Deux neurogenèses sur le run. Le thermostat d'erreur JEPA fonctionne.

---

## 4. Les formules du système

Référence rapide des mécaniques centrales, telles qu'elles sont écrites dans le code.

### 4.1 Érosion nocturne (`NaultheneLinearSynaptique.cycle_sommeil`)

```python
# Étape 0 (v37.0-fix) : la myéline voit l'apprentissage du jour
myeline_M = max(myeline_M, |annexe_weight|)

# Étape 1 : consolidation
base_weight += annexe_weight

# Étape 2-3 : érosion géométrique, protégée par la myéline
echelle    = max(echelle_myeline, quantile(myeline_M, 0.75))    # v37.0-fix : RELATIVE
myeline_n  = clamp(myeline_M / echelle, 0, 1)
facteur    = 1 − λ × (1 − myeline_n)
facteur    = 1.0 where |base_weight| < PLANCHER_POIDS_VITAL      # v34.0-fix1
base_weight *= facteur

# Plancher de couche (v37.0-fix : cliquet, jamais un plafond)
base_weight *= clamp(norme_naissance × FRACTION_NORME_MIN_COUCHE / ‖base‖, min=1.0)
```

| Constante | Valeur | Rôle |
|---|---|---|
| `λ` (`lambda_erosion`) | `0.05 × plasticité` | taux d'érosion nocturne |
| `FRACTION_NORME_MIN_COUCHE` | `0.10` | une couche garde ≥ 10 % de sa norme de naissance |
| `PLANCHER_POIDS_VITAL` | `1e-3` | sous ce seuil, une synapse n'est plus érodée |
| `QUANTILE_ECHELLE_MYELINE` | `0.75` | échelle de myéline relative à la couche |
| `SEUIL_CRISTAL` | `0.80` | **jamais franchi** (myéline réelle max : 0,007) |

### 4.2 Arbitrage C1 / C2 (`penser`)

```python
amplitude_c1 = max(logits_instinct) − min(logits_instinct)
gain_c1      = clamp(VIGUEUR_MIN_C1 / amplitude_c1, GAIN_C1_MIN, GAIN_C1_MAX)   # double sens
logits_finaux = (logits_instinct × gain_c1) + (valeurs_simulees × force_planification)
```

`VIGUEUR_MIN_C1` est **dérivée, jamais posée** :

```
VIGUEUR_MIN_C1 = (AMPLITUDE_C2_NORMALISEE × FORCE_PLANIFICATION_LIBRE) / RATIO_C1C2_VISE
               = (2,1 × 0,85) / 2,0  ≈  0,89
```

| Constante | Valeur |
|---|---|
| `AMPLITUDE_C2_NORMALISEE` | `2.1` (amplitude d'un z-score sur 7 actions, **mesurée**) |
| `RATIO_C1C2_VISE` | `2.0` (C2 reste prépondérant, sans écraser) |
| `GAIN_C1_MIN` / `GAIN_C1_MAX` | `0.25` / `4.0` |
| `FORCE_PLANIFICATION_GUIDE` / `LIBRE` | `0.5` / `0.85` |

### 4.3 Rollout mental (`simuler_futur_et_planifier`)

Complexité **linéaire**, jamais `7^horizon` : le premier pas branche sur les 7 actions réelles,
les suivants suivent l'argmax glouton.

```
valeur_cumulee = Σ_h  γ^h × cortex_prefrontal(état_simulé_à_h)      h ∈ HORIZONS = (1, 3, 7)
valeur_cumulee = (valeur_cumulee − moyenne) / (écart-type + 1e−8)   # INCONDITIONNELLE (v37.0-fix)
```

### 4.4 Distillation sélective (v37.1 + fix1)

```python
# Crédit rétrograde, borné aux épisodes
credit *= DECROISSANCE_CREDIT_DISTILLATION
if done[i]:      credit = 0
if choc[i] > 0:  credit = max(credit, min(choc[i] / reference, 1.0))

# Perte : moyenne PONDÉRÉE (journée stérile ⇒ rien n'est distillé)
perte = Σ(pertes × poids) / Σ(poids)

# Le cliquet (v37.1-fix1) : montée rapide, descente ~50× plus lente
inertie = INERTIE_REFERENCE_CHOC if monte else INERTIE_OUBLI_REFERENCE_CHOC
reference += (moyenne_jour − reference) × (1 − inertie)
```

| Constante | Valeur |
|---|---|
| `TAUX_DISTILLATION_C1` | `0.05` (0 = mécanique désactivée) |
| `DECROISSANCE_CREDIT_DISTILLATION` | `0.92` (≈44 % de crédit 10 ticks avant le choc) |
| `INERTIE_REFERENCE_CHOC` (montée) | `0.99` |
| `INERTIE_OUBLI_REFERENCE_CHOC` (descente) | `0.9998` |

### 4.5 Réservoir dopaminergique

```python
si événement : D += (DOPAMINE_MAX − D) × TAUX_CHOC_BASE × poids_evenement
si abandon   : D += (DOPAMINE_MIN − D) × TAUX_FRICTION_DOUCE_ABANDON
sinon        : D += (DOPAMINE_MIN − D) × TAUX_FRICTION
D = clip(D, DOPAMINE_MIN, DOPAMINE_MAX)
```

Le poids d'événement est un **OU doux** (borné dans [0,1] par construction, jamais une somme) :

```
poids_evenement = 1 − (1 − w_vis × p_vis)(1 − w_voc × p_voc)(1 − w_c3 × p_c3)
```

| Constante | Valeur |
|---|---|
| `DOPAMINE_MIN` / `NEUTRE` / `MAX` | `0.001` / `5.0` / `10.0` |
| `TAUX_CHOC_BASE` | `0.9` |
| `TAUX_FRICTION` | `0.01` |
| `TAUX_FRICTION_DOUCE_ABANDON` | `0.05` |
| `POIDS_DOPAMINE_VISUEL` / `VOCAL` / `C3` | `1.0` / `0.7` / `0.5` |

### 4.6 Rêve adaptatif

```
pourcentage_reve = POURCENTAGE_REVE_MIN
                 + (PLAGE_REVE_MAX − POURCENTAGE_REVE_MIN) × plasticite_base × facteur_richesse
taille_lot       = round(pourcentage_reve × len(memoire_moyen_terme))
```

| Constante | Valeur |
|---|---|
| `POURCENTAGE_REVE_MIN` | `0.0001` (0,01 %) |
| `PLAGE_REVE_MAX` | `0.60` (60 %) |
| Plafond effectif mesuré | `0.600` |
| Valeur atteinte en fin de run | **0,177 (17,7 %)** |

### 4.7 Promotion du cursus (v35.0)

Deux voies en **OU**, jamais l'une sans l'autre :

```
promu  ⟺  victoires_consécutives ≥ VICTOIRES_REQUISES
       OU  taux_maîtrise(fenêtre 20) ≥ TAUX_PROMOTION  (avec ≥ MIN_EPISODES_PROMOTION)
```

| Constante | Valeur |
|---|---|
| `VICTOIRES_REQUISES` | `2` |
| `FENETRE_PROMOTION` | `20` épisodes |
| `TAUX_PROMOTION` | `0.60` |
| `MIN_EPISODES_PROMOTION` | `10` |

> La réussite se juge sur `recompense_env > 0`, **jamais sur `termine` seul** — `termine` vaut
> aussi `True` quand l'agent meurt dans la lave.

---

## 5. L'état biologique — un régime jamais quitté

| Jauge | Valeur (200 derniers jours) |
|---|---|
| Satiété | **0,005** |
| Hydratation | **0,014** |
| Stimulation | 1,000 |
| Déficit moyen | **1,97** (max 2,0) |
| **Ticks en zone critique** | **100 %** |
| **Autonomie des jauges** | **0,0 %** |
| Nourriture consommée | 0,27 / jour |
| Eau consommée | 0,19 / jour |
| `r_bio` cumulé | **−0,30 / jour** |
| Effort métabolique moyen | 0,468 |

**L'agent est en déficit métabolique maximal 100 % du temps, depuis toujours, sur tous les runs.**

Conséquences pour la conception :

1. La distinction **besoin / gourmandise** (discutée en conception) décrit un régime que cet
   agent **n'a jamais connu**. Calibrer une mécanique de satiété aujourd'hui reviendrait à
   calibrer sur du vide.
2. `r_bio = −0,30/jour` s'ajoute à la pénalité de stagnation dans l'économie négative du §2.5.
3. Le mécanisme de **fatigue/mortalité** envisagé en v34 s'appliquerait à un agent déjà au fond
   de ses jauges — il mourrait immédiatement.

---

## 6. Le modèle du monde (JEPA)

```
jours    0-200 : 0,0402
jours  200-400 : 0,0153   ← minimum
jours  400-600 : 0,0155
jours  600-800 : 0,0168
jours  800-1000: 0,0255
jours 1000-1200: 0,0290
jours 1200-1400: 0,0317   ← remonte
```

L'erreur JEPA **remonte** après le jour 800, alors que l'agent est immobile dans le cursus depuis
500 jours. Deux lectures :

- **Bénigne** : le bus a grandi (16 → 64 dims), la cible `porte_visuelle(obs)` est plus riche,
  l'erreur absolue monte sans que la compréhension baisse.
- **Préoccupante** : le modèle du monde se dégrade faute d'expérience nouvelle — l'agent rejoue
  les mêmes trajectoires ratées et son JEPA se spécialise sur du bruit.

**Non tranché.** Départager demanderait de comparer l'erreur JEPA à dimension de bus constante,
ou de normaliser par la norme du bus cible.

---

## 7. Récapitulatif — ce qui marche, ce qui bloque, ce qui est inconnu

### ✅ Fonctionne (mesuré)

| Mécanique | Version | Preuve |
|---|---|---|
| Plasticité structurelle | v37.0 | 1 couche au plancher contre 5 ; **0 synapse morte** sur 1300 j |
| Rêve adaptatif | v13+ | **15-18 %** de la journée rejouée, 70 rêves/nuit |
| Équilibre C1/C2 | v37.0 | ratio **0,58-1,12** contre 9,9-22,1× |
| Cliquet de la référence | v37.1-fix1 | dérive **−7,4 %** sur 1300 j contre −57 % sur 600 j |
| Abstraction mnésique | v36.0 | **108** confirmations/repère, **73 %** de rappel |
| Odorat topologique & clinotaxie | v32.0 | **63,4 %** de taux d'approche (vs 50 % au hasard) |
| Les 5 sens | v29/v30 | bus actif **100 %** des ticks |
| Neurogenèse | v13+ | bus **16 → 64** |
| Cursus vocal | v27.x | **palier 19**, seul cursus encore en progression |
| Rétrocompatibilité `.brain` | v24+ | aucune fausse greffe sur 1300 nuits |

### 🔴 Bloque (mesuré)

| Problème | Chiffre | Racine |
|---|---|---|
| **Saut de difficulté 6x6 → 8x8** | réussite aléatoire **38,2 % → 3,8 %** (×10) | `PROGRAMME` |
| **Patience < budget natif** | 120 contre 256 → **4,7 % vs 21,0 %** | `PATIENCE_*` |
| **Économie perdante** | espérance **−1,06** par épisode | `ThermostatCinetique` |
| **4 actions inutiles sur 7** | 3 actions → réussite **×5** | `num_actions` |
| Ère Intégration | ×2 d'épisodes perdants, vocal sacrifié | `BORNES_ERES` |
| Progression du cursus | **niveau 2/15**, 678 j sans victoire | conséquence |

### ❓ Inconnu (à instrumenter)

| Question | Comment trancher |
|---|---|
| Le guidage ×3,0 nuit-il aux victoires ? | ablation à graine fixée, guidage figé à 1,0, 300 j |
| L'erreur JEPA qui remonte : bénin ou dégradation ? | comparer à dimension de bus constante |
| `Score_Spectral_Moyen_Jour = 0,000` | vérifier si la composante est branchée |
| `EXTENSION_PATIENCE_SURSAUT = 50` | constante en attente de calibrage depuis la v30.1 |
| L'accord C1/C2 peut-il se stabiliser ? | indissociable du blocage — c'est un thermomètre |

---

## 8. Recommandations — par ordre de retour attendu

> Aucune n'est implémentée. Classées par rapport (impact attendu / risque de casser l'existant).

**1. Aligner la patience sur le budget natif de MiniGrid.** C'est le levier le plus direct et le
mieux mesuré : passer de 120 à 256 ticks fait passer le taux de réussite atteignable de **4,7 %
à 21,0 %**, sans toucher à une seule mécanique cognitive. `max_steps = 256` n'est pas un chiffre
arbitraire — c'est ce que l'environnement lui-même considère comme raisonnable.

**2. Rééquilibrer l'économie de récompense.** Espérance **−1,06** par épisode : l'échec est
rationnel. Attention à ne pas seulement baisser la pénalité — la mesure montre que l'agent est à
8 % du pire cas, donc le problème vient autant du **numérateur** (une victoire à +0,67 en moyenne)
que du dénominateur.

**3. Insérer un palier entre `Empty-6x6` et `Empty-8x8`.** Le saut ×10 en difficulté effective
contredit le principe « une seule compétence change entre deux paliers ». Un `Empty-7x7` ou un
`Empty-Random-8x8` (départ variable, donc parfois proche) lisserait la marche.

**4. Mesurer avant de toucher au guidage.** Une ablation à graine fixée coûte un run et lève une
ambiguïté qui pollue trois diagnostics.

**5. Reconsidérer l'ère Intégration.** Doubler les épisodes MiniGrid dans une économie perdante
aggrave mécaniquement le bilan et sacrifie le seul cursus qui progressait.

**6. Ne pas toucher à C1/C2, à la mémoire, ni à la distillation.** Les trois fonctionnent. Le pic
de 12 victoires (jours 200-300) prouve que l'architecture *peut* apprendre quand les conditions
le permettent.

---

## 9. Erreurs de diagnostic commises et corrigées

Traçabilité — ces affirmations ont été faites en cours de route puis invalidées par la mesure.

| Affirmation | Statut | Ce que dit la mesure |
|---|---|---|
| « Le rêve est quasi inexistant (0,1 %) » | ❌ **FAUX** | Fraction lue comme un pourcentage : c'est **17,7 %**. Propagé dans `CHANGELOG.md` et `CHANTIER_v37` — **corrigé dans les deux** |
| « La patience de 120 ticks est insuffisante en soi » | ❌ **IMPRÉCIS** | La marge est de **×10,9** sur l'optimal BFS (11 actions). Le problème n'est pas la marge théorique mais le **taux de réussite atteignable** (4,7 % contre 21,0 % à 256 ticks) |
| « L'accord C1/C2 a convergé à 100 % » (mi-run, 600 j) | ❌ **FAUX** | Oscillation lue comme une tendance ; l'accord **suit les victoires** |
| « `SimpleCrossing` est mal placé dans le cursus » | ❌ **ÉCARTÉ** | Le déséquilibre C1/C2 existait aussi sur les niveaux **maîtrisés** |
| « L'économie s'aggrave après le jour 600 » | ❌ **IMPRÉCIS** | La pénalité *par épisode* est stable (−1,6) ; c'est le **nombre d'épisodes** qui double |
| « Le Doctorat est infaisable » | ❌ **FAUX** | BFS mesuré : **33,7** actions optimales pour 120 disponibles |

**Leçon récurrente** : lire une tranche isolée d'un run conduit à des conclusions inverses de
celles du run complet. Quatre fois sur six, l'erreur venait d'une extrapolation sur moins de
100 jours ou d'une unité mal lue.

**Méthode qui a fonctionné** : reproduire le phénomène en simulation isolée (le cliquet, les taux
de réussite aléatoires, le BFS) plutôt que d'interpréter une courbe. Une mesure directe sur
400 épisodes tranche en secondes ce qu'un run de 600 jours laisse ambigu.

---

*Document arrêté au 8 août 2026 — run `ous47258` (1300 jours), cerveau
`080820260027_V371fix1_1300_RMD.brain`. Toutes les valeurs de code sont relevées dans
`src/naulthene/cerveau/noyau.py` à cette date.*
