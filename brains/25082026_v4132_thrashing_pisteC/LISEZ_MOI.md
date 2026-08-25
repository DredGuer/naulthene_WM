# Campagne 25/08/2026 — Piste C du thrashing : le conflit des organes

## Ce qu'on cherchait

Le gradient reçu par `integrateur_bio` (0,914) vaut **78×** celui de `porte_visuelle`
(0,012). Or les besoins corporels **alternent** : affamé un jour, assoiffé le lendemain.
**Hypothèse** : la politique subit cette alternance comme un pendule, d'où l'annulation.

**Prédiction** : geler un axe fait **remonter** l'alignement vers 1,0.

## Protocole

A/B apparié — même `.brain`, même graine (11), 12 jours. Le témoin est le bras A de la
campagne piste A (`brains/25082026_v4132_thrashing_pisteA/`).

⚠️ **`--soif-figee` a dû être créé** : aucun drapeau d'ablation métabolique n'existait.
Il **gèle** `hydratation` à 1.0 (donc `(1−hydratation)² = 0`) plutôt que de supprimer le
sens — l'agent garde tout, seul l'axe cesse de tirer. Avec **assertion runtime** que le
drapeau atteint le module (bug v41.4).

⚠️ Un agent qui n'a jamais soif ne cherche plus d'eau : la récolte hydrique s'effondre, et
c'est **attendu**. Ce bras mesure **uniquement l'alignement du gradient**, jamais une
performance.

## 🔴 Résultat : réfutée, effet nul

| BRAS | alignement | écart vs témoin |
|---|---|---|
| A — cursus libre (témoin) | 0,3428 | — |
| B — carte verrouillée | 0,2630 | −0,0798 |
| **C — soif figée** | **0,3389** | **−0,0039** |
| *repère 1/√12* | *0,2887* | |

Geler l'axe hydrique change l'alignement de **−0,0039** — **20× moins** que la piste A, qui
était déjà dans le mauvais sens. Le conflit des organes n'est pas la cause.

## 🟢 Le vrai résultat — le plafond est identique partout

| | A | B | C |
|---|---|---|---|
| `‖Σg‖` final | 0,8219 | 0,8329 | **0,8201** |

La direction utile sature au **même endroit** dans les trois bras. Le plafond ne dépend
d'aucune des causes testées.

**Explication : le clipping.** `clip_grad_norm_(…, max_norm=1.0)` et la norme globale
mesurée vaut **0,9315** — soit **93 % du plafond**, dont **98 % consommés par
`integrateur_bio`**. Le clipping ne crée pas le déséquilibre, il le **fige** : quand le corps
sature le budget, la vue ne peut pas grandir.

⚠️ **Hypothèse cohérente, pas encore une mesure** : il faudrait lire la norme globale
**avant** clipping et compter les nuits effectivement clippées.

## Fichiers

- `base.brain` — cerveau de départ (identique à celui de la piste A)
- `C_soif_figee.log` — le run complet, 12 jours
