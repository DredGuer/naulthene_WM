# Campagne 23/08/2026 — La table de mixage aux niveaux supérieurs (v41.32, étape 3)

## Ce qu'on cherchait

L'étape 1 avait mesuré la table de mixage au **niveau 1/15** (`Empty-5x5`), où **5 termes sur
11** affichaient `σ = 0,00000` — des ablations **vides** (pas de porte, pas de DoorKey, pas de
tuteur vocal). La table ne pouvait donc pas être arbitrée.

⚠️ **Piège évité** : le niveau 4 (`SimpleCrossingS9N1`) ne réveille **aucun** des 5 termes —
`est_doorkey() = False`, pas de porte, pas de tuteur. Vérifié en code **avant** de lancer.
Seul **`DoorKey-5x5`** réveille `Jalons` + `Guidage` + `Portes` simultanément.

**Deux runs, deux questions différentes :**

| Run | Question |
|---|---|
| `--env-force MiniGrid-SimpleCrossingS9N1-v0` | comment la table se comporte **là où l'agent est réellement bloqué** |
| `--env-force MiniGrid-DoorKey-5x5-v0` | la **dispersion des 5 termes** là où ils existent |

Graine 11, 80 jours chacun.

## Résultat 1 — Niveau 4 (`SimpleCrossingS9N1`), 80 nuits

| TERME | MOYENNE | σ | PART SIGNAL |
|---|---|---|---|
| **Bio** | +0,00362 | **0,04141** | **52,1 %** |
| Stagnation | −0,01383 | 0,01388 | 17,5 % |
| SousObjectif | +0,00437 | 0,01125 | 14,2 % |
| Curiosite | +0,01255 | 0,00856 | 10,8 % |
| Progres | +0,00065 | 0,00422 | 5,3 % |
| **Env** | **+0,00001** | **0,00009** | **0,1 %** |
| *5 muets* | 0,00000 | 0,00000 | 0,0 % |

## Résultat 2 — `DoorKey-5x5`, 80 nuits

| TERME | MOYENNE | σ | PART SIGNAL |
|---|---|---|---|
| **Bio** | +0,00248 | **0,03141** | **36,4 %** |
| **Jalons** | +0,00255 | **0,02926** | **33,9 %** |
| Stagnation | −0,01109 | 0,01221 | 14,1 % |
| SousObjectif | +0,00169 | 0,00556 | 6,4 % |
| Curiosite | +0,00727 | 0,00386 | 4,5 % |
| Guidage | +0,00017 | 0,00203 | 2,4 % |
| Portes | +0,00005 | 0,00113 | 1,3 % |
| Env | +0,00004 | 0,00084 | 1,0 % |
| Progres | +0,00000 | 0,00004 | 0,0 % |
| Vocal, CoutC3 | 0,00000 | 0,00000 | 0,0 % |

## 🔴 Le fait principal — `Env` s'effondre d'un facteur 240

`Env` **est la récompense de la tâche** (atteindre le but).

| Carte | σ de `Env` | Part du signal |
|---|---|---|
| `Empty-5x5` (niveau 1) | 0,02163 | **21,8 %** |
| **`SimpleCrossingS9N1` (niveau 4)** | **0,00009** | **0,1 %** |
| `DoorKey-5x5` | 0,00084 | 1,0 % |

**Sur la carte où l'agent est réellement bloqué, le but porte 0,1 % de la dispersion.**

Ce n'est **pas** une ablation vide : σ n'est pas nul, il est **écrasé**. L'agent atteint le
but, mais si rarement que le signal devient négligeable devant `Bio`. Recoupé par la maîtrise
finale : **15 % au niveau 1, 5 % au niveau 4**.

C'est un **cercle**, pas un bug : peu de victoires ⇒ signal faible ⇒ peu d'apprentissage de
la tâche ⇒ peu de victoires. Et pendant ce temps `Bio` monte de 44 % à **52,1 %** — le corps
occupe la place que le but laisse vide.

## Ce que ces tables établissent pour la table de mixage

1. **`Bio` domine partout** (52,1 % · 36,4 %), confirmant l'étape 1 — la voix vitale n'est
   jamais écrasée. La prémisse « amplifier le vital » reste réfutée.
2. **`Curiosite` et `Stagnation` restent des décalages d'origine** sur les trois cartes :
   forte moyenne, faible dispersion. C'est le vrai objet du chantier.
3. **`Jalons` est un vrai signal** quand il existe (33,9 %, σ = 0,029) — le second de la
   table. Il n'était pas « mort », il était absent.
4. **`Vocal` et `CoutC3` sont muets partout** : ablations vides **par configuration** (pas de
   tuteur, pas de plug), jamais par carte.

## ⚠️ Portée

**Bancs forcés** : le niveau reste à 1/15 par construction, donc « niveau atteint » y est
inopérant. Ces runs mesurent des **dispersions**, pas des performances.
**Une seule graine** (g11) : les chiffres exacts lui sont propres ; les faits qualitatifs
(domination de `Bio`, effondrement de `Env`, nature de `Curiosite`/`Stagnation`) sont nets.

## Fichiers

- `N4_g11.brain` / `.log` — niveau 4, 80 nuits
- `DK_g11.brain` / `.log` — DoorKey-5x5, 80 nuits
- `resultats_niveau4.json` — l'agrégat des deux tables
