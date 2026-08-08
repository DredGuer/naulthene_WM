# Diagnostic complet — Naulthène AGI, août 2026

> **Nature du document** : état des lieux factuel, arrêté au 8 août 2026. Chaque affirmation
> est adossée à une mesure sur un run réel, avec la source indiquée. Aucune modification de
> code n'accompagne ce diagnostic — c'est un instantané, pas un chantier.
>
> **Runs de référence**
>
> | Run | Cerveau | Durée | Ce qu'il établit |
> |---|---|---|---|
> | `58ssyw19` | V36 | 600 j | Base de comparaison pré-v37 |
> | `8wequiqg` | V37.1 | 600 j | Équilibre C1/C2 ; révèle le bug de la référence |
> | `ous47258` | **V37.1-fix1** | **1300 j** | **Run principal de ce diagnostic** |

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

**Ce n'est pas une panne cognitive.** Toutes les mécaniques que le projet a construites
fonctionnent et sont mesurables. Le blocage est **économique** : dans le barème actuel, tenter
de gagner coûte plus cher que renoncer.

---

## 2. Ce qui fonctionne — vérifié, chiffré

### 2.1 La santé synaptique — le chantier v37 a tenu

Sonde des poids sur le cerveau à 1300 jours :

| | Avant v37 (cerveau V36, 600 j) | Après v37 (1300 j) |
|---|---|---|
| Couches collées au plancher vital | **5 / 12** | **1 / 12** |
| `tete_motrice` | 10,00 % (plancher) | **40,78 %** |
| `cortex_prefrontal` | 10,00 % (plancher) | **87,96 %** |
| `porte_visuelle` | 16,18 % | **82,06 %** |
| `porte_auditive` | 21,75 % | **115,83 %** |
| Synapses mortes (cumul) | — | **0** |

Les trois correctifs de la v37.0 (plancher-plafond, timing de la myéline, échelle relative)
sont **validés sur le double de la durée** qui avait servi à les écrire. Le cerveau n'est plus
en voie d'extinction : il grossit.

Seule `tete_requete` reste au plancher — c'est **normal et attendu** : elle sert au routage
C3, aucun plug n'est branché, elle ne reçoit donc aucun gradient. Ce n'est pas une pathologie.

### 2.2 Le rêve — je m'étais trompé, il fonctionne

J'avais signalé « le rêve est quasi inexistant, 0,1 % ». **C'était une erreur de lecture de ma
part**, et elle a été répétée dans le CHANGELOG et le chantier v37.

`Pourcentage_Reve` est logué comme une **fraction** (`0,177`) mais affiché suivi d'un `%` — ce
qui donne « 0,177 % » à l'écran alors que la valeur réelle est **17,7 %**.

Vérification arithmétique :

```
Nb_Reves = 61,  Pourcentage_Reve = 0,153
61 / 0,153 = 398 ≈ len(memoire_moyen_terme) sur 400 ticks ✅
```

**Le rêve rejoue 15-18 % de la journée**, avec 70 souvenirs par nuit en fin de run. Il monte
même régulièrement (8 → 70 rêves/nuit sur 1300 jours). Les 110 nuits sans rêve des 200 premiers
jours sont réelles, mais s'expliquent : plasticité basse chez un cerveau neuf, elles disparaissent
totalement après le jour 400.

> ⚠️ **À corriger dans les documents** : `docs/CHANGELOG.md` (entrée v37.1-fix1) et
> `docs/CHANTIER_v37_equilibre_c1_c2.md` §6bis affirment tous deux que « le rêve est quasi
> inexistant ». C'est faux. L'affichage console mérite lui aussi d'être corrigé (`%` en trop).

### 2.3 L'équilibre C1/C2 — acquis

| Run | Ratio C2/C1 | Accord |
|---|---|---|
| Avant v37 | **9,9× à 22,1×** (dérivant selon la carte) | **0 %** partout |
| V37.1-fix1, 1300 j | **0,58 à 1,12** | **5,8 % à 85,3 %** |

Le ratio ne quitte jamais la plage saine sur 1300 jours. C1 et C2 sont enfin **deux voix
comparables**.

Mais l'accord **suit les victoires** au lieu de converger :

```
jours  200-300 : accord 85,3 %   ← pendant le pic de 12 victoires
jours 1200-1300: accord  5,8 %   ← après 1000 jours sans victoire
```

**Ce n'est donc pas une propriété stable de l'architecture, c'est un indicateur** : quand
l'agent trouve quoi faire, ses deux systèmes s'accordent ; quand il ne trouve pas, ils divergent.
Traiter l'accord comme un levier serait confondre le thermomètre et la fièvre.

### 2.4 Le cliquet de la référence (v37.1-fix1) — correctif validé

| | Run 600 j (bug) | Run 1300 j (corrigé) |
|---|---|---|
| Dérive de `reference_choc_dopamine` | **−57 %** | **−7,4 %** (sur 2× plus long) |
| Crédit de distillation | 10 % → **69 %** | 12 % → **30 %** |

Et le comportement voulu apparaît : la référence **monte** pendant les 400 premiers jours
(0,2184 → 0,2332) — l'agent relève sa barre en découvrant qu'il peut vivre mieux — puis redescend
très lentement. C'est exactement le principe demandé : *un expert est plus difficile à
impressionner*.

### 2.5 Les cinq sens — tous actifs

| Sens | Mesure (200 derniers jours) |
|---|---|
| Bus sensoriel | **actif 100 %** des ticks |
| Toucher (contact) | 42,0 % des ticks |
| Toucher (portage) | 15,0 % |
| Odorat (ticks actifs) | **91,7 %**, intensité moyenne 0,225 |
| Odorat (taux d'approche) | **63,4 %** — mieux que le hasard (50 %) |
| Goût | 14,7 ticks/jour |

Le **taux d'approche olfactive à 63,4 %** est un résultat notable : la clinotaxie de la v32.0
fonctionne, l'agent remonte les gradients d'odeur mieux qu'au hasard.

### 2.6 La mémoire v36 — le mécanisme tourne à plein

| Métrique | Valeur (200 derniers jours) |
|---|---|
| Confirmations par repère | **108,4** (contre 1 avant la v36) |
| Types distincts | 5 |
| Ratio de rappel | **73,0 %** des ticks |
| Doublons convertis en abstraction | **11 228** |
| Saturation | 45 % |

L'abstraction par récurrence est le mécanisme le plus incontestablement fonctionnel du projet.

### 2.7 Le vocal — la seule progression continue

**Palier vocal 19** atteint, score moyen 0,466. C'est le seul cursus du projet qui **progresse
encore** en fin de run. À noter : `Score_Spectral_Moyen_Jour = 0,000` — seule la composante
formants contribue, la composante spectrale est morte ou jamais activée. À investiguer.

---

## 3. Le blocage — diagnostic

### 3.1 Ce qui se passe réellement sur `Empty-8x8`

Le niveau 2 du programme est `MiniGrid-Empty-8x8-v0` : **une pièce vide**. Pas d'obstacle, pas
d'objet, pas de clé. Il faut marcher d'un coin à l'autre.

Mesures sur les 100 derniers jours :

| Signal | Valeur | Lecture |
|---|---|---|
| Records de proximité au but | **8,9 / jour** | L'agent **avance vers le but** |
| Abandons par patience | **3,0 / jour** sur 4 épisodes | **75 % d'échec par épuisement** |
| Patience | 120 ticks | |
| Récompense moyenne | **0,0000** | |
| Pénalité de stagnation | **−6,54 / jour** | soit **−1,63 par épisode** |

**L'agent s'approche du but et n'y arrive pas avant l'épuisement de sa patience.** Il ne tourne
pas en rond : il progresse, puis le temps manque.

### 3.2 L'économie est structurellement perdante

```
Coût d'un épisode raté      : −1,63  (stagnation)  + coût métabolique
Gain d'une victoire          : +1,00  (et décroissant avec le nombre de pas)
Taux de réussite observé     : 25 %
```

**Espérance par épisode : 0,25 × (+1,00) + 0,75 × (−1,63) = −0,97.**

Dans ce barème, **la stratégie optimale est de ne pas s'épuiser à chercher**. C'est exactement
ce que l'agent a appris — et les 8,9 records de proximité montrent qu'il n'est pas passif : il
s'approche, puis renonce, parce que c'est rationnel.

> Ce déséquilibre avait déjà été mesuré par la sonde de récompense plusieurs versions avant la
> v37 (−5,23 par épisode contre +1,00 par victoire). **Il n'a jamais été corrigé.** Tous les
> chantiers depuis (v34 à v37) ont traité des mécaniques *en aval* de ce problème.

### 3.3 L'ère « Intégration » double la charge sans doubler l'apprentissage

`BORNES_ERES = (400, 600)` — au jour 600, l'ère `integration` remplace l'après-midi vocal par du
MiniGrid.

| Ère | Matin | Après-midi | Épisodes MiniGrid/jour |
|---|---|---|---|
| `alternance` (< 400) | MiniGrid | vocal isolé | 2,1 |
| `synesthesie` (400-599) | MiniGrid + audio | vocal isolé | 2,0 |
| `integration` (≥ 600) | MiniGrid | **MiniGrid** | **4,0** |

Bascule mesurée au jour exact :

```
jour 599 : 2 épisodes, 1 abandon, stagnation −3,0
jour 601 : 4 épisodes, 3 abandons, stagnation −7,2
```

**Le doublement de la pénalité de stagnation au jour 600 n'est pas une aggravation cognitive :
l'agent joue simplement deux fois plus.** La pénalité *par épisode* est stable depuis le jour
300 (−1,6).

Mais l'effet net est négatif : deux fois plus d'épisodes perdants dans une économie déjà
perdante, **sans contrepartie** — l'après-midi vocal, lui, produisait un apprentissage qui
progressait (palier 19).

### 3.4 Le guidage : une corrélation à vérifier

```
jours 200-300 : guidage ×1,00 → 12 victoires   (le pic du projet)
jours 400-600 : guidage ×3,00 →  0 victoire
```

Le filet de sécurité v35.1 amplifie les récompenses **de progression**. Hypothèse à tester :
en amplifiant l'approche, il rend *s'approcher* plus payant qu'*arriver*, et l'agent optimise
le sous-objectif au lieu de l'objectif.

**Ce n'est pas démontré** — la corrélation peut être inverse (le filet monte *parce que* l'agent
ne gagne plus). Un test d'ablation à graine fixée trancherait.

---

## 4. L'état biologique — un régime jamais quitté

| Jauge | Valeur (200 derniers jours) |
|---|---|
| Satiété | **0,005** |
| Hydratation | **0,014** |
| Stimulation | 1,000 |
| Déficit moyen | **1,97** |
| Ticks en zone critique | **100 %** |
| Autonomie des jauges | **0,0 %** |

**L'agent est en déficit métabolique maximal 100 % du temps, depuis toujours, sur tous les
runs.** Il consomme 0,27 nourriture et 0,19 eau par jour — très en dessous de ses besoins.

Conséquence pour la conception : la distinction **besoin / gourmandise** discutée précédemment
décrit un régime que cet agent **n'a jamais connu**. Calibrer une mécanique de satiété
aujourd'hui reviendrait à calibrer sur du vide.

---

## 5. Le modèle du monde (JEPA) — un signal contre-intuitif

```
jours    0-200 : 0,0402
jours  200-400 : 0,0153   ← minimum
jours  600-800 : 0,0168
jours 1200-1400: 0,0317   ← remonte
```

L'erreur JEPA **remonte** après le jour 800, alors que l'agent est immobile dans le cursus depuis
500 jours. Deux lectures possibles :

- **Bénigne** : le bus a grandi (16 → 64 dims), la cible est plus riche, l'erreur absolue monte
  sans que la compréhension baisse.
- **Préoccupante** : le modèle du monde se dégrade faute d'expérience nouvelle — l'agent rejoue
  les mêmes trajectoires ratées, et son JEPA se spécialise sur du bruit.

**Non tranché.** Le départager demanderait de comparer l'erreur JEPA à dimension de bus constante.

---

## 6. Récapitulatif : ce qui marche, ce qui bloque, ce qui est inconnu

### ✅ Fonctionne (mesuré)

| Mécanique | Preuve |
|---|---|
| Plasticité structurelle (v37) | 1 couche au plancher contre 5 ; 0 synapse morte sur 1300 j |
| Rêve adaptatif | 15-18 % de la journée rejouée, 70 rêves/nuit |
| Équilibre C1/C2 (v37.0) | ratio 0,58-1,12 contre 9,9-22,1× |
| Cliquet de la référence (v37.1-fix1) | dérive −7,4 % sur 1300 j contre −57 % sur 600 j |
| Abstraction mnésique (v36) | 108 confirmations/repère, 73 % de rappel |
| Odorat topologique & clinotaxie (v32) | 63,4 % de taux d'approche |
| Les 5 sens | bus actif 100 % des ticks |
| Neurogenèse | bus 16 → 64 |
| Cursus vocal | palier 19, seul cursus encore en progression |

### 🔴 Bloque (mesuré)

| Problème | Chiffre |
|---|---|
| **Économie de récompense perdante** | espérance **−0,97** par épisode |
| Patience insuffisante pour `Empty-8x8` | **75 %** d'abandons, 8,9 records de proximité/jour |
| Ère Intégration | ×2 d'épisodes perdants sans contrepartie |
| Progression du cursus | **niveau 2/15**, 678 jours sans victoire |

### ❓ Inconnu (à instrumenter)

| Question | Comment trancher |
|---|---|
| Le guidage ×3,0 nuit-il aux victoires ? | ablation à graine fixée, guidage figé à 1,0 |
| L'erreur JEPA qui remonte : bénin ou dégradation ? | comparer à dimension de bus constante |
| `Score_Spectral_Moyen_Jour = 0,000` | vérifier si la composante est branchée |
| L'accord C1/C2 peut-il se stabiliser ? | dépend des victoires — indissociable du blocage |

---

## 7. Ce que je recommanderais — par ordre de retour attendu

> Aucune de ces pistes n'est implémentée. Elles sont classées par rapport
> (impact attendu / risque de casser l'existant).

**1. Rééquilibrer l'économie de récompense.** C'est le seul problème dont on peut démontrer
qu'il rend l'échec rationnel. Le diagnostic existe depuis plusieurs versions, il n'a jamais été
traité. Tout le reste est en aval.

**2. Mesurer avant de toucher au guidage.** L'ablation à graine fixée (guidage figé à 1,0 sur
300 jours) coûte un run et lève une ambiguïté qui pollue trois diagnostics.

**3. Reconsidérer l'ère Intégration.** Doubler les épisodes MiniGrid dans une économie perdante
aggrave mécaniquement le bilan, et sacrifie le seul cursus qui progressait encore.

**4. Ne pas toucher à C1/C2, à la mémoire, ni à la distillation.** Les trois fonctionnent. Le
pic de 12 victoires (jours 200-300) prouve que l'architecture *peut* apprendre quand l'économie
le permet.

---

## 8. Erreurs de diagnostic commises, et corrigées ici

Traçabilité — ces affirmations ont été faites en cours de route puis invalidées par la mesure.

| Affirmation | Statut | Correction |
|---|---|---|
| « Le rêve est quasi inexistant (0,1 %) » | ❌ **FAUX** | Fraction lue comme un pourcentage : c'est **17,7 %**. Présent dans le CHANGELOG et le chantier v37, **à corriger** |
| « L'accord C1/C2 a convergé à 100 % » (mi-run, 600 j) | ❌ **FAUX** | Oscillation lue comme une tendance ; il suit les victoires |
| « `SimpleCrossing` est mal placé dans le cursus » | ❌ **ÉCARTÉ** | Le déséquilibre C1/C2 existait aussi sur les niveaux maîtrisés |
| « L'économie s'aggrave après le jour 600 » | ❌ **IMPRÉCIS** | La pénalité *par épisode* est stable ; c'est le nombre d'épisodes qui double |
| « Le Doctorat est infaisable » | ❌ **FAUX** | BFS mesuré : 33,7 actions optimales pour 120 disponibles |

**Leçon récurrente** : lire une tranche isolée d'un run conduit à des conclusions inverses de
celles du run complet. Trois fois sur quatre, l'erreur venait d'une extrapolation sur moins de
100 jours.

---

*Document arrêté au 8 août 2026, run `ous47258` (1300 jours), cerveau
`080820260027_V371fix1_1300_RMD.brain`.*
