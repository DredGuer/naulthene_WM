# `VIS01_preuve` — la preuve A/A de la passerelle `--telemetrie-3d` (chantier VIS-01, tâche 9)

> **Nature** : dossier de campagne **régularisé le 10/09/2026 à 19:06** (tâche 10).
> Les runs qu'il contient ont été lancés et terminés le **10/09/2026 entre 18:47:45 et
> 18:48:03** (tâche 9). Le `LISEZ_MOI.md` et la ligne de `JOURNAL_DES_RUNS.md` sont donc
> **POSTÉRIEURS aux runs** — voir « Écart de trace » ci-dessous, consigné et non masqué.

---

## 1. La question posée (telle qu'elle a été formulée)

Spec VIS-01 §10, ligne « Étape 2 : run bit-identique sans drapeau » :

> « **Étape 2 : run bit-identique sans drapeau** — deux runs même graine (5 jours) avec et sans
> télémétrie active, `diff` des niveaux promus — **le test qui compte** »

Autrement dit : **le drapeau `--telemetrie-3d` change-t-il quelque chose au cerveau ?** Ce n'est
pas une mesure d'effet, c'est une preuve de **non-effet** : elle doit être vidée (aucune
différence) pour que les campagnes observées restent interprétables.

## 2. Protocole exact

| Champ | Valeur |
|---|---|
| Graine | `11` (`--graine 11`), **la même dans les deux bras** |
| Durée | `--jours 5` — 5 journées × 400 ticks = **2 000 ticks par run** |
| Bras témoin | `aa_temoin.brain` — **aucun** drapeau |
| Bras observé | `aa_telemetrie.brain` — `--telemetrie-3d udp:127.0.0.1:9998` (**aucun serveur** en écoute : les trames `activite`/`evenement` partent et sont perdues, cas « serveur absent » de la spec §9) |
| Cerveaux | **neufs** (`🐣 Naissance d'un nouveau cerveau (Bus=16)`), nés de la même graine, même code |
| Device / W&B | `NAULTHENE_DEVICE=cpu` · `WANDB_MODE=offline` |
| Répertoire | `brains/VIS01_preuve/` (créé pour l'occasion) · `PYTHONPATH=../../src` |

Commande réellement lancée (telle que reproduite par le rapport de la tâche 9) :

```bash
cd "…/21. AGI/brains/VIS01_preuve"
for bras in temoin telemetrie; do
  NAULTHENE_DEVICE=cpu WANDB_MODE=offline PYTHONPATH=../../src ../../venv/bin/python3 \
      -m naulthene.cerveau.noyau --graine 11 --jours 5 --brain "aa_${bras}.brain" \
      $([ "$bras" = telemetrie ] && echo "--telemetrie-3d udp:127.0.0.1:9998") \
      > "aa_${bras}.log" 2>&1
done
diff <(grep -o 'Niveau [0-9]*' aa_temoin.log) <(grep -o 'Niveau [0-9]*' aa_telemetrie.log)
```

## 3. Résultat brut

| Observation | Témoin (`aa_temoin`) | Observé (`aa_telemetrie`) |
|---|---|---|
| Jours simulés | `Jour 001 → 005` | `Jour 001 → 005` |
| `tick_absolu` final | 2 000 | 2 000 |
| Lignes `Niveau N` (celle que compare le `diff`) | 5 × `Niveau 1` | 5 × `Niveau 1` |
| Lignes propres à la télémétrie | 0 | **1** (l'annonce d'activation) |
| Taille du `.brain` sur le disque | 601 623 o | 602 143 o |
| `torch.equal` sur les 97 tenseurs | — | **identiques** ; `optimizer_state_dict` identique |
| Croissance pendant le run | — | **neurogenèse réelle** (`Thermostat: MUTATION +16 !`), structure finale à `dim_bus = 32` |

**`diff` des niveaux promus : VIDE.** Le témoin est **atteint** (5 lignes de chaque côté, ce n'est
pas une comparaison vide), et l'écart de taille des deux `.brain` (520 o) a été **rétracté** comme
artefact : c'est la **longueur du nom de fichier** (`aa_telemetrie.brain`, 4 caractères de plus que
`aa_temoin.brain`, × 130 entrées d'archive) qui change la compression zlib du `data.pkl` — le
contenu décompressé est identique (576 153 o) et les 130 entrées d'archive portent le **même
SHA-256**. Voir l'entrée `[v41.76]` du CHANGELOG.

## 4. Preuve complémentaire bout en bout (`e2e/`)

Un listener UDP réel (socket liée sur `127.0.0.1:0`) a écouté pendant un run `--jours 1` lancé avec
`--telemetrie-3d udp:127.0.0.1:<port>` : **16 trames `evenement` + 11 trames `activite` reçues**,
plus grosse trame 1 100 o (`dim_bus = 16`), fichier de structure de 13 603 o. Le canal ne fait donc
pas que se brancher : il **livre**.

Fichiers conservés : `e2e/e2e.brain` et `e2e/e2e.brain.vis01_structure.json`.
⚠️ **Le log console de ce run n'a pas été conservé** (le `.log` compte autant que le `.brain` pour
la télémétrie console — c'est une trace manquante, elle est écrite ici plutôt que tue).

## 5. 🔴 Écart de trace — l'entrée de journal est POSTÉRIEURE aux runs

Le dogme « rien sans écrit » (CLAUDE.md §6) exige, pour **tout run lancé**, une entrée
`docs/fonctionnement/JOURNAL_DES_RUNS.md` écrite **AU LANCEMENT**, et un `LISEZ_MOI.md` par dossier
de campagne. **Ni l'une ni l'autre n'existait au lancement des runs de ce dossier** :

| Fait | Horodatage |
|---|---|
| Lancement du bras témoin | 2026-09-10 ~18:47:45 |
| Fin du bras observé | 2026-09-10 18:48:03 |
| Run bout en bout `e2e` | 2026-09-10 18:49:21 |
| Ligne `JOURNAL_DES_RUNS.md` + ce `LISEZ_MOI.md` | 2026-09-10 19:06 (tâche 10) |

**Raison exacte** : la liste des fichiers autorisés du brief de la tâche 9 était **close** (quatre
fichiers : `noyau.py`, `telemetrie.py`, `tests/test_cerveau_3d.py`, `CHANGELOG.md`) et le commit
ciblé devait ne rien contenir d'autre — le rapport de la tâche 9 l'a écrit comme préoccupation n°4
plutôt que de la masquer. La tâche 10 régularise : l'entrée existe désormais, **datée du jour réel
des runs** avec l'écart consigné.

**Ce que cela change, et ce que cela ne change pas** : les horodatages réels sont reconstruits
depuis le **journal du système de fichiers** (`mtime` de `aa_temoin.brain` = 18:47:54,
`aa_telemetrie.brain` = 18:48:03, `e2e/` = 18:49:21) et la première ligne horodatée de chaque log
`wandb` (18:47:47) — jamais depuis une estimation de mémoire. Le verdict (`diff` vide) et les
chiffres ne dépendent pas de cette écriture tardive ; c'est **la règle de trace** qui était violée,
et c'est elle qui est réparée.

## 6. Limites (écrites ici, avant d'être opposées)

1. **n = 1 graine, 5 jours.** Très en deçà de la règle « n ≥ 20 graines » du dépôt — mais c'est
   exactement le protocole de la spec §10, et c'est une preuve de **non-effet** (2 000 ticks
   appariés, cerveaux identiques au bit), pas une mesure d'effet. Aucune conclusion
   comportementale n'en est tirée.
2. **Cerveaux neufs `bus = 16 → 32`**, donc bien plus petits que le `dim_bus = 145` de la spec :
   l'A/A prouve la neutralité du chemin de code, pas celle d'un cerveau mature.
3. **Aucun serveur en écoute** pendant l'A/A : le cas testé est celui (nominal) où la trame est
   perdue, pas celui où elle est consommée. Le run `e2e` couvre ce second cas séparément.
4. Ces artefacts (`*.log`, `*.vis01_structure.json`) sont **locaux** : `brains/**/*.log` est
   gitignoré et `*.brain` aussi. Seul ce `LISEZ_MOI.md` est versionné.

## 7. Ce que cela ferme, ce que cela laisse ouvert

- **Ferme** : « le drapeau `--telemetrie-3d` modifie le cerveau » — non mesuré sur 5 jours et
  2 000 ticks appariés, à une graine.
- **Laisse ouvert** : (a) la neutralité au-delà de quelques centaines de ticks et sur un cerveau
  mature ; (b) le **surcoût** du rapporteur — mesuré dans `brains/VIS01_surcout_10092026/` (tâche
  10), jamais estimé.
