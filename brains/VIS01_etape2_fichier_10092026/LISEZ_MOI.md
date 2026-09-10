# `VIS01_etape2_fichier_10092026` — l'étape 2 de bout en bout, après la tâche 11

**Protocole écrit AVANT le premier lancement** (2026-09-10 19:28), dossier créé **avant** le premier
run. Campagne d'**instrument** (VIS-01, tâche 11), pas de mesure cognitive : elle prouve qu'un run
EN COURS alimente réellement la page 3D.

## 1. La question, telle qu'elle a été posée

Le 10/09/2026, l'e2e de la tâche 10 a mesuré, serveur en `--serveur-seul --udp 9998` et run vivant
(`brains/VIS01_surcout_10092026/LISEZ_MOI.md` §8) :

| Observation | Valeur mesurée par la tâche 10 |
|---|---|
| `/sante` après le run | `sequence = 13`, `evenements_total = 68`, **`sequence_structure = 0`** |
| `/structure` après le run | **`{}`** |

Cause écrite depuis : la trame `structure` (305 086 o) ne peut pas passer par UDP (plafond dur de
65 507 o) ; le run l'écrit dans `<brain>.vis01_structure.json`, et **personne ne relisait ce
fichier**. Question de cette campagne : *avec le veilleur de la tâche 11, un serveur
`--serveur-seul --structure-fichier` voit-il enfin la structure d'un run en cours — et la voit-il
CHANGER (neurogenèse) sans redémarrer ?*

## 2. Protocole exact

| Champ | Valeur |
|---|---|
| Serveur | `python -m naulthene.instruments.cerveau_3d --serveur-seul --udp 9998 --port 8771 --structure-fichier brains/VIS01_etape2_fichier_10092026/etape2.brain.vis01_structure.json` — lancé **AVANT** le run, donc fichier **absent** au démarrage |
| Run | `python -m naulthene.cerveau.noyau --graine 11 --jours 60 --no-wandb --brain brains/VIS01_etape2_fichier_10092026/etape2.brain --telemetrie-3d udp:127.0.0.1:9998` (`NAULTHENE_DEVICE=cpu`, `WANDB_MODE=offline`) — **cerveau NEUF** (naissance, `dim_bus = 16`), donc rien d'existant n'est écrasé |
| Sonde | une interrogation de `GET /structure` + `GET /sante` **par seconde** pendant le run (`poll_structure.txt`) — c'est le témoin du CHANGEMENT en direct |
| Flux | un extrait SSE (`sse_extrait.txt`) pris pendant le run : la page reçoit-elle `structure` **et** `activite` sur le même flux ? |
| Réponses brutes | `structure_avant.json`, `structure_apres_run.json`, `sante_avant.json`, `sante_apres_run.json` |
| Témoin du producteur | le bilan du run (`run1.log` : « N structure(s) écrite(s) ») et les compteurs de la veille dans `/sante` |

⚠️ **Aucun fichier de `brains/08092026_sci01_balayage_K/` n'est lu ni écrit** (campagne historique) ;
aucun `.brain` préexistant n'est écrasé (le cerveau `etape2.brain` **naît** ici) ; aucun dossier
temporaire hors du dépôt.

## 3. Fichiers

| Fichier | Ce qu'il porte |
|---|---|
| `etape2.brain` | le cerveau neuf du run (gitignoré, comme tout `.brain`) |
| `etape2.brain.vis01_structure.json` | la trame `structure` écrite par le run (305 Ko à terme) |
| `run1.log` | la console du run (bilan de télémétrie en fin de run) |
| `serveur.log` | la bannière du serveur et son bilan de veille |
| `poll_structure.txt` | `dim_bus` / `sequence_structure` / compteurs de veille, **une ligne par seconde** |
| `sse_extrait.txt` | l'extrait brut du flux SSE pendant le run |
| `*_avant.json` / `*_apres_run.json` | les réponses HTTP brutes, avant et après |
| `chrono.txt` | la chronologie horodatée, commande par commande |

**Versionnés** (comme le `chrono.txt` de `VIS01_surcout_10092026`) : `LISEZ_MOI.md`, `chrono.txt`,
`poll_structure.txt` — les trois traces qui ne se régénèrent pas. **Laissés sur le disque, non
versionnés** : `etape2.brain` (1,8 Mo, gitignoré), `run1.log` (353 Ko, gitignoré),
`sse_extrait.txt` (1 Mo, regénérable en reconnectant un client), les réponses HTTP brutes et
`cli_duree.txt`.

## 4. Limites, écrites d'avance

1. **Un seul run, une seule graine** : cette campagne ne mesure aucun effet cognitif (c'est un
   instrument) ; elle ne dit rien de plus que « la chaîne serveur → navigateur est branchée ».
2. **La neurogenèse n'est pas forcée** : si `dim_bus` ne bouge pas pendant 60 jours, le témoin du
   CHANGEMENT en direct manquera, et il faudra le dire — les tests unitaires, eux, la provoquent.
3. **Le navigateur n'est pas ouvert** : le flux est lu par `curl`/urllib, pas par three.js. Ce qui
   est prouvé est le transport, pas le rendu.

---

## 5. Chiffres bruts (mesurés le 10/09/2026, 19:28:48 → 19:31:00)

### 5.1 La chaîne, avant / pendant / après

| Instant | `GET /structure` | `sequence_structure` | Compteurs de la veille (`/sante`) |
|---|---|---|---|
| 19:28:51 (serveur seul, **fichier absent**) | **`{}`** | **0** | `publications 0`, `absences 12` |
| 19:28:57 (run lancé à 19:28:53, fichier écrit au montage) | **12 couches, `dim_bus` 16** | **1** | `publications 1`, `absences 17` |
| 19:29:00 | `dim_bus` 32 | 2 | `publications 2` |
| 19:29:04 | `dim_bus` 48 | 3 | `publications 3` |
| 19:29:10 | `dim_bus` 51 | 4 | `publications 4` |
| 19:29:31 | `dim_bus` 67 | 5 | `publications 5` |
| 19:29:45 → 19:30:14 (run terminé à 19:30:08) | `dim_bus` 68 | 6 | `publications 6`, `illisibles 0`, `invalides 0` |

Les `dim_bus` **distincts vus par le SERVEUR**, dans l'ordre, sur une ligne par seconde
(`poll_structure.txt`) : `(absent) ×5 → 16 ×2 → 32 ×3 → 48 ×5 → 51 ×16 → 67 ×11 → 68 ×24`.

⚠️ **6 publications pour 11 structures écrites** par le run (`run1.log` : « 11 structure(s)
écrite(s), 0 ratée(s) ») : la veille relit la SIGNATURE, pas l'historique. Deux neurogenèses dans
la même seconde donnent une seule publication — celle du **dernier** état. C'est sans conséquence
ici (le bus ne garde que la dernière structure, et `dim_bus` ne décroît jamais), et c'est écrit
pour ne pas être découvert plus tard.

### 5.2 Le flux SSE (client connecté 19:29:01 → 19:29:31, `sse_extrait.txt`)

| Canal | Reçu |
|---|---|
| `structure` | **4 trames** — `dim_bus` **16, 32, 48, 51**, toutes avec **12 couches** |
| `activite` | 252 |
| `evenement` | 1 404 |
| Premier événement du flux | `event: structure` (la structure passe AVANT toute activité) |

### 5.3 Les deux transports, côte à côte

| | |
|---|---|
| Trame `structure` finale | **88 488 octets** (`dim_bus = 68`) — **au-dessus du plafond dur de 65 507 o** d'un datagramme UDP : le fichier n'est pas un confort, c'est la seule voie |
| Activité / événements | **4 463 datagrammes envoyés, 0 perdu** (`run1.log`) — l'UDP fait le travail pour lequel il passe |
| Run | 60 jours en **75 s** (19:28:53 → 19:30:08) ⇒ **1,25 s/jour**, cohérent avec le rythme dérivé par `VIS01_surcout_10092026` (~1,16 s/jour + démarrage) : le serveur en veille ne ralentit pas le run |

### 5.4 La CLI, seule, sur le fichier que le run a laissé (`cli_duree.txt`)

```
   structure  : brains/VIS01_etape2_fichier_10092026/etape2.brain.vis01_structure.json — structure
                chargée : 12 couche(s), dim_bus = 68 (relue à chaque changement, 1 publication(s))
📡 structure : 1 publication(s) depuis … — 0 absence(s), 0 illisible(s), 0 invalide(s).
```

**Avant / après, même protocole** (l'e2e de la tâche 10 vs cette campagne, serveur `--serveur-seul`
et run vivant) :

| Observation | Tâche 10 (10/09, 19:15) | Tâche 11 (10/09, 19:29) |
|---|---|---|
| `/structure` | **`{}`** | **12 couches, `dim_bus` 68** |
| `sequence_structure` | **0** | **6** |
| Page 3D | « en attente de la structure… » | scène construite, puis **reconstruite 5 fois** (croissance du cerveau) |

## 6. Ce que cela ferme, ce que cela laisse ouvert

- **Ferme** : la « 🔴 Limite connue de l'étape 2 » écrite dans `docs/fonctionnement/LANCEMENT.md`
  (« la lecture de ce fichier par le serveur du spectateur n'est PAS encore implémentée ») et
  l'écart constaté par la tâche 10 (`/structure` = `{}`, `sequence_structure` = 0). L'étape 2 est
  branchée de bout en bout : un run en cours alimente la 3D, structure comprise.
- **Laisse ouvert** : (a) le rendu three.js réel (un navigateur n'a pas été ouvert — le transport
  est prouvé, pas l'image) ; (b) les neurogenèses multiples dans une même seconde (seule la
  dernière est publiée) ; (c) le coût de la veille sur un serveur qui porte déjà plusieurs
  navigateurs (non mesuré : un seul client SSE ici).

