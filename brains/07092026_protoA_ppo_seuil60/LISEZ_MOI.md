# PROTOCLE A — PPO face à la règle 60 % du cursus

**Date** : 2026-09-07 · **Statut** : 📋 **préparé — AUCUN run lancé** · **Nature** : banc
PPO (zéro ligne de `noyau.py` touchée). Protocole écrit **avant** lancement (règle du dépôt).

> Source : [protocoles en réserve §1](../../docs/ameliorations/07092026_protocoles_en_reserve.md)
> et point général du 07/09 §2.3.2 / §5.2
> ([lien](../../docs/etat_des_lieux/07092026_point_general_et_direction.md)).

## La question

**Le mur « Niveau 4/15 » (`SimpleCrossingS9N1`, off-by-one corrigé le 07/09) est-il en
partie une RÈGLE DU CURSUS ?** Le seuil de promotion (`TAUX_PROMOTION` = 60 % sur
`FENETRE_PROMOTION` = 20 épisodes) est **au-dessus de ce que PPO atteint sur cette carte à
ce budget** : PPO réussit 36-40 % à 152 k pas (baseline du 29/08). Si un PPO — qui
converge, lui — ne valide **jamais** une fenêtre de 20 à 12 victoires, alors la phrase
« le plafond est une pathologie de cette architecture » est fausse en l'état : le mur est
**verrouillé par le barème**, et le débat sur `TAUX_PROMOTION` s'ouvre sur preuve.

## Ce qui est mesuré — et comment

- **Banc** : `src/naulthene/instruments/banc_ppo_fenetres.py` — réutilise les conditions
  verrouillées de `banc_ppo` (v41.38, A/A δ = 0.000000) : `SimpleCrossingS9N1`,
  observation aplatie 7×7×3, `MlpPolicy`, **7 actions**, récompense brute, **152 043 pas**.
- **Capture** : vecteur binaire victoire/défaite **épisode par épisode pendant
  l'entraînement** (Monitor, victoire = `r > 0`, jamais `termine` seul — même règle que
  `noyau.py` §v35.0 invariant 4).
- **Analyse** : `src/naulthene/instruments/analyser_fenetres_60.py` — applique la règle
  exacte (fenêtre glissante de 20, passage ≥ 12/20) **et** mesure l'autre branche du OU
  (série de **2 victoires consécutives**) : la promotion réelle est un OU, la porte 60 %
  n'est pas le seul chemin.

## Les bras

| Bras | Contenu | Runs |
|---|---|---|
| **PPO** | `--arch 69` (le bras à 39,8 % du 29/08 — le meilleur), graines **11, 22, 33, 44, 55**, 152 043 pas | 5 |
| **A/A pré-vol** | `--pas 20000 --aa` à la graine 11 | 2 courts |

## Les juges, posés d'avance

| Juge | Grandeur | Verdict qui s'ensuit |
|---|---|---|
| **1. Porte 60 %** | ≥ 1 fenêtre ≥ 12/20, par graine | **0/5** → le barème verrouille à lui seul le niveau 4 (mur barémique) : ouvrir le débat `TAUX_PROMOTION` **sur preuve**, en rappelant qu'il dérive `SEUIL_MATURITE` et le sevrage (ne pas le toucher isolément). **≥ 1/5** → le seuil n'est pas le mur : le goulot est l'apprenant, ne pas baisser le seuil. |
| **2. Fidélité** | taux de victoire global 36-40 % | vérifie que le banc reproduit la baseline du 29/08 (sinon l'écart vient du script, pas du monde) |
| **3. Route série** | occurrences de 2 victoires consécutives | si la série de 2 passe massivement, la voie rapide du OU aurait promu PPO dans le cursus → la porte 60 % n'explique pas seule un blocage éventuel |

## Prédiction écrite d'avance

**Je ne sais pas — et le signe importe.** À p ≈ 0,4 et des centaines de fenêtres, un
passage ≥ 12/20 est **plausible** sous l'hypothèse d'indépendance ; mais les victoires ne
sont pas indépendantes (politique qui s'améliore, épisodes courts, corrélations), donc
« jamais » reste possible. La réponse est la mesure, pas l'intuition.

## ⚠️ Limites, écrites d'avance

1. `--arch 69` seul : on donne à PPO son **meilleur** bras connu — pas de balayage
   d'architecture ici (ce n'est pas la question).
2. 152 043 pas = le budget de référence du banc. Si le juge 1 est ambigu (passages rares),
   l'extension **600 k pas** (une vie entière, point général §5.2) tranchera.
3. PPO dans le vrai cursus jouerait aussi les niveaux précédents ; ici on isole la carte
   du mur — c'est le point du protocole.
4. L'épisode coupé par la fin du budget est exclu de la fenêtre (comme une journée qui se
   termine chez Naulthène).

## Pré-vol obligatoire avant lancement

```bash
PYTHONPATH=src python -m naulthene.instruments.banc_ppo_fenetres --pas 20000 --aa
```

Le vecteur de victoires des deux runs doit être **bit-identique** (leçon v41.62 : un
drapeau qui marche malgré tout, seul le δ sur deux runs le prouve). Si faux : la capture
est invalide, corriger avant tout run.

## Lancement

```bash
for g in 11 22 33 44 55; do
  PYTHONPATH=src python -m naulthene.instruments.banc_ppo_fenetres \
    --graine $g --sortie "07092026_protoA_ppo_seuil60/ppo_g${g}.json" &
done
wait
PYTHONPATH=src python -m naulthene.instruments.analyser_fenetres_60 \
  07092026_protoA_ppo_seuil60/ppo_g*.json
```

**Coût** : ~50-60 min (5 runs). **À lancer après la fin de la campagne
`branches_persistantes` (~15:15), ou sur décision explicite** — ne pas concurrencer la
vague 2 sans accord. Ligne au [journal des runs](../../docs/fonctionnement/JOURNAL_DES_RUNS.md)
**au lancement** (règle formelle), pas avant.
