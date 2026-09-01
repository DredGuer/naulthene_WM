# A/A + validation d'implémentation — brique C (rendement mécanique asymétrique, v41.48)

**Date** : 2026-09-01 · **Avant toute campagne** (règle de mesure §1 et §5).

## Ce qui est validé ici

| Contrôle | Commande | Résultat |
|---|---|---|
| **A/A témoin** (`--sans-rendement`, 2 réplicats) | `--graine 11 --jours 3` | ✅ **δ = 0** |
| **A/A bras actif** (2 réplicats) | `--graine 11 --jours 3` | ✅ **δ = 0** |
| **Les deux bras DIFFÈRENT** | diff actif vs témoin | ✅ **différents** |
| **Le drapeau atteint le module** | assertion runtime | ✅ (message d'ablation imprimé 1×) |
| **Nuit complète** (v32.0) | 3 nuits par run | ✅ 0 erreur, 0 traceback |
| **Télémétrie conditionnelle** (v29.1) | ligne console + clés W&B | ✅ absente quand la mécanique dort |
| **Formule asymétrique** | test unitaire | ✅ échec stérile **puni** (−3,0), succès stérile **nul** |
| **Passe-plat exact** | rendement = 1 partout | ✅ identique à l'original |

## 🔴 Le défaut trouvé et corrigé AVANT la campagne

**Première écriture : les deux bras étaient IDENTIQUES** — exactement le bug v41.4.

Cause : le rendement avait été calqué sur `transition_tick`, or le masque v41.31
(`GRADIENT_CAUSAL_ACTIF`, actif) **annule déjà** tous les ticks sans transition. Le
rendement était donc un **doublon exact du masque** : il ne pouvait rien ajouter.

**Correction** : le rendement mesure le **travail mécanique LIVRÉ / travail ENGAGÉ**, ce
que le masque ne distingue pas. Il départage ce que le masque confond :

| Geste | Masque v41.31 | Rendement v41.48 |
|---|---|---|
| pas qui déplace | 1 | **1,000** |
| rotation (pivote la vue, ne déplace rien) | 1 | **0,125** |
| `forward` dans un mur | 0 | 0,000 |
| `toggle` dans le vide | 0 | 0,000 |

Le **0,125** n'est pas réglé : c'est `(½ M r²) / (M · PAS_GRILLE)` avec `r = PAS_GRILLE/2`,
soit le rapport géométrique **1/8** déjà inscrit dans les invariants v41.28 (« le ratio
locomotion/manipulation est GÉOMÉTRIQUE, pas un réglage »). **La masse se simplifie** dans
le rapport — le rendement est donc invariant à la croissance du corps.

⚠️ **La rotation n'est PAS punie** : elle reste la brique de base de l'exploration
(invariant v41.31). Elle est créditée **à la hauteur de ce qu'elle déplace**.

## L'asymétrie, mesurée sur le banc unitaire

|  | avantage | rendement | asymétrique (retenu) | symétrique (témoin) |
|---|---|---|---|---|
| succès, geste utile | +2,0 | 1,0 | **+2,0** | +2,0 |
| succès, geste stérile | +2,0 | 0,0 | **0,0** (n'ancre rien) | 0,0 |
| échec, geste utile | −3,0 | 1,0 | **−3,0** | −3,0 |
| **échec, geste stérile** | −3,0 | 0,0 | **−3,0 (PUNI)** | **0,0 (invisible)** |

C'est la ligne en gras qui justifie l'asymétrie : pondérer les deux signes rendrait le
geste stérile **invisible** au lieu d'indésirable — la faute symétrique de celle que la
v41.28 a corrigée côté coût.

## Le rendement observé en run (3 jours, graine 11)

`0,124 → 0,081 → 0,077` de moyenne, **233 → 272 gestes à rendement nul** par jour.
L'agent livre **moins de 12 %** du travail mécanique qu'il engage — cohérent avec l'Étape 0
mesurée indépendamment au banc (17,5 % de ticks avec déplacement).

## ⚠️ Ce qui n'est PAS démontré ici

Ces contrôles établissent que la mécanique **fonctionne et agit**. Ils ne disent
**rien** de son utilité : ni la directivité, ni la maîtrise, ni le niveau n'ont été
mesurés. C'est l'objet de l'Étape 1 (banc, n=20, directivité en juge de paix, cible < 6×).
