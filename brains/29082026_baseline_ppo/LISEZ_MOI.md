# Campagne 28-29/08/2026 — La ligne de base PPO (60 runs)

> **Le protocole complet est dans [`PROTOCOLE.md`](PROTOCOLE.md)**, écrit le 28/08 AVANT le
> premier run. Ce fichier n'existe que pour respecter la convention « un `LISEZ_MOI.md` par
> campagne » — il pointe, il ne duplique pas.

## Ce qu'on cherchait

Donner une **échelle externe** à quatre grandeurs mesurées sur Naulthène la semaine du
23-28/08 et qui n'en avaient aucune (dérive de l'axe informatif, d', plafond de probabilité
sur l'action favorisée, alignement W↔axe). Sans point de comparaison, aucune ne pouvait être
qualifiée de « normale » ou d'« anormale ».

## Ce qu'il y a dans ce dossier

| Fichiers | Contenu |
|---|---|
| `PROTOCOLE.md` | le protocole d'équité (même observation aplatie 7×7×3, `MlpPolicy`, 7 actions, 152 043 pas, récompense brute) |
| `lancer.sh` · `campagne.log` | la commande exacte et le journal de lancement |
| `aa_g11.json` / `.log` | **le test A/A** — δ_A/A = 0,000000 sur les 5 métriques |
| `ppo_a37_g*.json` / `.log` · `ppo_a69_g*` · `ppo_a107_g*` | les 3 bras (`[37,37]` 14 068 params · `[69,69]` 30 644 · `[107,107]` 55 648) × 20 graines |
| `resultats.json` | **l'agrégat machine** des 60 runs |

Instrument : [`src/naulthene/instruments/banc_ppo.py`](../../src/naulthene/instruments/banc_ppo.py).

## Le résultat, en une ligne

Un PPO **4× plus léger** que le cœur RL de Naulthène réussit **2,3× mieux** sur
`SimpleCrossingS9N1` (36,2 % / 39,8 % / 27,1 % selon le bras, contre ~16 %). Le mur
informationnel de MiniGrid **n'existe pas** — le plafond est une pathologie de l'architecture.

Dépouillement et limites : [`docs/recherche/campagnes/BASELINE_PPO_29082026_le_mur_n_existe_pas.md`](../../docs/recherche/campagnes/BASELINE_PPO_29082026_le_mur_n_existe_pas.md)
· CHANGELOG §[v41.38-baseline].
