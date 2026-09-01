# La valence apprise atteint-elle la décision ? — 31/08/2026

Analyse : [VALENCE_31082026](../../docs/recherche/enquetes_closes/VALENCE_31082026_la_carte_est_vide_a_cet_endroit.md).

## Ce qu'on cherchait

La valence stockée dans `empreinte_types` (+0,84 pour les portes) influence-t-elle le
comportement, ou reste-t-elle décorative ?

**Réponse : elle n'atteint pas la décision** — `r(valence porte, directivité) = +0,0521`
(`t = +0,21`). Mais la cause n'est pas cybernétique : elle repose sur **2 à 36
confirmations** contre 8 621 pour la nourriture. **La carte est presque vide à cet endroit.**

## Protocole

**Aucun run lancé.** Lecture de 20 `.brain` (cohorte AB3 du 26/08) croisée avec le succès au
banc mesuré le 31/08 (`brains/30082026_plancher_n20/agregat.json`).

Pour chaque cerveau : valence apprise par type (`empreinte_types`), nombre de repères et
confirmations cumulées par type (`souvenirs_spatiaux` + `archives_cartes`), puis
corrélations avec succès au banc, maîtrise en run et directivité.

Seuil de Bonferroni (4 tests, n=20) : **|t| ≥ 2,50**.

## Résultats

| Corrélation | `r` | `t` |
|---|---:|---:|
| valence porte → succès | −0,2930 | −1,30 |
| valence porte → **directivité** | **+0,0521** | **+0,21** |
| confirmations portes → succès | +0,4455 | +2,11 |

## ⚠️ Artefact écarté

`r(valence, confirmations) = −0,63` (`t = −3,44`, significatif) est une **régression vers la
moyenne**, pas un fait cognitif : le même motif apparaît sur `sol` (−0,74), `FOOD` (−0,72)
et `WATER` (−0,53). Une valence calculée sur 2 événements est gonflée ; sur 36, elle
converge.

## Fichiers

- `agregat.json` — les 20 points (valences, confirmations, succès, directivité)

Les `.brain` sources restent dans `brains/26082026_v4132_AB3_cursus/`, **jamais modifiés**
(lecture seule, aucune copie nécessaire).
