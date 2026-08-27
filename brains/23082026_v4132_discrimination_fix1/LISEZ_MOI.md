# Campagne 23/08/2026 — La sonde de discrimination (v41.32, étape 4)

## Ce qu'on cherchait

`contact_frontal` est **un seul bit** dérivé de `can_overlap()`. Or `Ball.can_overlap()` et
`Wall.can_overlap()` valent **tous deux False** : le même bit vaut 1.0 pour un mur et pour
une ressource (mesuré : **81,5 % mur / 18,5 % ressource**).

**Hypothèse** : l'agent serait aveuglé par ce capteur fusionné — le bit crierait
« obstacle, contourne ! » devant une pomme, ce qui expliquerait l'anti-corrélation du
fourrage (ratio observé/attendu 0,67).

**Test** : comparer la distribution des 7 actions quand `contact_frontal = 1`, selon que la
case frontale porte un **mur** ou une **ressource**. Distance de variation totale
(½·Σ|p−q|), sans hypothèse de forme ni seuil posé.

## 🔴 Un premier run était un ARTEFACT — corrigé

Le run initial donnait `consommer sur ressource = 0,0 %` sur **60/60 nuits**, alors que le
même run enregistrait **295 saisies réelles**. Incompatible ⇒ artefact.

**Cause** : `env.step` s'exécute ~370 lignes avant la sonde. MiniGrid a déjà exécuté
`pickup`, la Ball est dans `carrying`, la case est vide — `can_overlap()` ne voyait plus
rien. Même défaut temporel qu'en v41.25-fix1 (chaleur) et v41.5 (maturité).

**Correctif (fix1)** : tester `positions_food`/`positions_water` — les ensembles du
détecteur, vidés seulement à `evaluer_tick`, donc **après** la sonde. C'est pourquoi la
sonde de fourrage, qui les utilisait déjà, n'avait pas ce biais.

## Résultats corrigés (graine 11, 60 jours, 2 cartes)

### `Empty-5x5` — distance 0,1943

| ACTION | % MUR | % RESSOURCE | ÉCART |
|---|---|---|---|
| gauche | 7,9 % | 9,6 % | +1,7 |
| droite | 6,4 % | 9,3 % | +2,9 |
| avancer | 23,3 % | 24,7 % | +1,4 |
| **consommer** | **12,1 %** | **9,8 %** | **−2,3** |
| poser | 16,6 % | 14,9 % | −1,7 |
| activer | 16,0 % | 12,3 % | −3,8 |
| parler | 17,7 % | 19,5 % | +1,8 |

### `SimpleCrossingS9N1` (niveau 4) — distance 0,2640

| ACTION | % MUR | % RESSOURCE | ÉCART |
|---|---|---|---|
| gauche | 8,4 % | 11,3 % | +2,9 |
| droite | 4,9 % | 10,3 % | +5,5 |
| avancer | 21,1 % | 21,9 % | +0,7 |
| **consommer** | **16,0 %** | **16,0 %** | **+0,0** |
| poser | 7,2 % | 6,5 % | −0,8 |
| activer | 35,5 % | 25,3 % | −10,2 |
| parler | 6,7 % | 8,8 % | +2,1 |

## Le témoin de bruit — indispensable pour lire ces chiffres

Deux échantillons tirés de la **même** distribution (donc aucune discrimination réelle), aux
mêmes tailles que les mesures, 4000 tirages :

| Carte | Mesure | Bruit p50 | Bruit p95 | Verdict |
|---|---|---|---|---|
| `Empty-5x5` | **0,194** | 0,127 | **0,213** | **sous le p95 — indistinguable du bruit** |
| Niveau 4 | **0,264** | 0,150 | **0,249** | à peine au-dessus du p95 |

## Verdict

🟢 **L'hypothèse « les distributions sont identiques » est CONFIRMÉE** : la distance mesurée
est au niveau du bruit d'échantillonnage. L'agent **ne discrimine pas** une ressource d'un
mur, ou à peine.

🔴 **Mais le mécanisme proposé est réfuté.** L'hypothèse prédisait que l'agent **se
détourne** devant une ressource (plus de rotations, moins de `consommer`). Les écarts vont
dans ce sens mais **restent dans le bruit**, et sur le niveau 4 `consommer` est
**rigoureusement identique** (16,0 / 16,0).

Ce n'est donc pas que l'agent **fuit** la ressource. C'est qu'il fait **exactement la même
chose** dans les deux cas : il ne voit pas la différence, et il ne l'exploite pas non plus.

## Le fait le plus net — la distance DÉCROÎT

| Carte | 1er tiers | 2ᵉ tiers | 3ᵉ tiers |
|---|---|---|---|
| `Empty-5x5` | 0,253 | 0,186 | **0,144** |
| Niveau 4 | 0,255 | 0,263 | 0,274 |

Sur `Empty-5x5`, l'agent devient **avec le temps moins discriminant**. Il n'apprend pas à
distinguer : il apprend à **uniformiser** sa réponse.

## ⚠️ Portée

Bancs forcés (niveau bloqué à 1/15), **une seule graine**. Le témoin de bruit rend la lecture
honnête mais ne remplace pas n ≥ 20. Ces runs mesurent une **distance de distributions**,
jamais une performance.

## Fichiers

- `E5_g11.brain` / `.log` — `Empty-5x5`, 60 nuits
- `N4_g11.brain` / `.log` — niveau 4, 60 nuits
