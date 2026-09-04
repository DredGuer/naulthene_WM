# LE REBOND D'ENTROPIE N'EST PAS CAUSÉ PAR LE CHANGEMENT DE CARTE

**Date** : 2026-09-04 · **Statut** : ❌ **RÉFUTÉE** · **Coût : 0 run** (réanalyse de la
campagne `04092026_cursus_complet` en cours, 30 logs terminés).

---

## 1. L'hypothèse, telle qu'elle a été formulée

Le juge 0 de la campagne du 04/09 avait mesuré que **20/20 cerveaux LIBRE** passent par un
minimum d'entropie puis **remontent** (+0,26 à +1,22). L'explication proposée était
séduisante et mécaniquement plausible :

> *« Dans le cursus, le changement d'environnement agit comme un régulateur : dès que la
> politique devient trop nette sur la carte A, elle se heurte aux murs de la carte B qui la
> sanctionnent et forcent le réseau à ré-explorer. Le monde lui-même empêche la politique de
> converger. »*

**Prédiction testable** : le rebond d'entropie doit être **synchronisé** avec les
changements de niveau. Si c'est vrai, la flexibilité de l'agent n'est pas un choix interne
mais une **fracture imposée par le monde**.

## 2. Le protocole

Réanalyse pure, sur données déjà acquises. Pour chaque log terminé (30 runs, deux bras) :

- repérage des nuits où `Niveau N/15` **change** ;
- fenêtre de ±5 nuits autour de chaque changement, Δ entropie = moyenne(après) − moyenne(avant) ;
- **témoin apparié** : mêmes fenêtres, mêmes runs, sur des nuits **sans** changement et
  distantes d'au moins 10 nuits de toute promotion, tirées à graine fixée (42).

## 3. Les chiffres

| | Δ entropie | n |
|---|---|---|
| Autour d'un **changement de carte** | **+0,0160** ± 0,1154 | 61 |
| Nuits **ordinaires** (témoin) | **+0,0152** ± 0,0850 | 61 |
| **Écart** | **+0,0008** | — |
| **`t` (Welch)** | **+0,045** | seuil 2,0 |

**Il n'y a rigoureusement aucune différence.** Les hausses après changement représentent
**32/61 (52 %)** — soit exactement le hasard.

### Le test d'amplitude, encore plus net

| | valeur |
|---|---|
| Rebond mesuré par promotion | **+0,0160** |
| Promotions par run (moyenne) | **2,0** |
| **Effet cumulé maximal** | **+0,0325** |
| **Rebond réellement observé (juge 0)** | **+0,26 à +1,22** |

Même en attribuant aux promotions **100 %** de leur effet, elles expliquent au mieux
**3 % du rebond**. L'ordre de grandeur est absent.

### Le rebond existe là où il n'y a AUCUN changement de carte

C'est la vérification qui clôt le dossier :

| Régime | Rebond médian (fin − minimum) |
|---|---|
| Cursus complet (15 niveaux, promotions) | **+1,100** (n=15) |
| **Banc forcé** (`--env-force`, **une seule carte, 0 promotion**) | **+0,693** (n=20) |

Le rebond est **présent, massif, dans un régime où la carte ne change jamais**. Une cause
qui n'a pas besoin d'être là pour que l'effet se produise n'est pas la cause.

### Et les minima ne sont pas là où il faudrait

| Cerveau | Nuit du minimum | Nuits de promotion | Distance |
|---|---|---|---|
| LIBRE_g11 | 1019 | 11, 26, 433 | **586** |
| LIBRE_g111 | 104 | 59, 207, 414 | 45 |
| LIBRE_g122 | 156 | 93, 100, 287 | 56 |
| LIBRE_g133 | 165 | 90, 97, 103 | 62 |

Les minima tombent des **dizaines à des centaines de nuits** après la promotion la plus
proche. Aucune synchronisation.

## 4. Ce que ça ferme, ce que ça laisse ouvert

**Fermé** : le rebond d'entropie **n'est pas** une fracture imposée par le changement
d'environnement. Quatre convergences indépendantes le disent : pas d'écart au test apparié
(`t` = +0,045), un ordre de grandeur manquant (3 %), la présence du rebond **sans aucune
promotion**, et des minima désynchronisés.

**Ouvert, et c'est le point qui compte** : le rebond est donc **endogène**. Il vient de la
dynamique interne du réseau — plasticité nocturne, érosion, cliquets de référence — et pas
du monde. Cela le rend **plus** intéressant, pas moins : c'est une propriété de
l'architecture, mesurable sans changer l'environnement.

Hypothèses non testées, par ordre de coût :
1. **L'érosion nocturne** : chaque nuit rogne les poids ; une politique nette non renforcée se dé-durcit mécaniquement. Testable en lisant la myéline aux nuits du rebond.
2. **Le cliquet de `reference_choc_dopamine`** : si la référence monte, le crédit de distillation baisse, donc C1 automatise moins — la politique se relâche.
3. **Le régime métabolique** : `Bio` pèse 62,1 % du gradient (mesuré le 04/09) ; un corps qui se dégrade pourrait dominer la politique et la brouiller.

⚠️ **Aucune de ces trois n'est mesurée.** Elles sont écrites ici pour ne pas être
redécouvertes, pas pour être crues.

## 5. Note de méthode — une erreur de lecture, corrigée en séance

Le premier passage du script affichait un témoin à **−0,0223** (contre +0,0160 pour les
promotions), ce qui suggérait un effet net. C'était **faux** : le tirage du témoin était mal
apparié (fenêtre `H[i-5:i]` calculée sur un index non filtré). Corrigé, le témoin vaut
**+0,0152** — et l'effet disparaît.

> **Un résultat favorable se vérifie deux fois plus qu'un défavorable** (règle de mesure §3).
> Ici, la vérification a retiré le résultat.

---

*22ᵉ explication mesurée puis réfutée. Coût : zéro run.*
