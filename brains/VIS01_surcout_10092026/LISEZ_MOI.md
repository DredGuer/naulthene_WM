# `VIS01_surcout_10092026` — le surcoût du rapporteur (spec VIS-01 §10, tâche 10)

> **Dossier créé AVANT le premier run** (règle « une campagne s'archive avant de tourner »,
> CLAUDE.md §7.6) — **2026-09-10 19:06**. Ce `LISEZ_MOI.md` porte le **protocole** ; le
> calendrier (début, fin estimée, fin réelle) est dans
> `docs/fonctionnement/JOURNAL_DES_RUNS.md`, entrée écrite **avant** le premier lancement.
>
> ⚠️ **Les chiffres de la section 5 sont remplis APRÈS les runs**, et bruts — jamais une
> estimation, jamais un arrondi « arrangeant ». Un poste resté vide est un poste non mesuré.

---

## 1. La question posée (formulée AVANT la mesure)

Spec VIS-01 §10, ligne 3 du tableau des preuves :

> « **Surcoût du rapporteur — chiffré, jamais estimé** | ticks/s avec et sans hooks, même graine,
> même cerveau »

Question, telle qu'elle est posée : **un run qui vit est-il ralenti par les 12 forward hooks du
rapporteur, et de combien — en ticks par seconde ?**

C'est la dernière preuve de la spec qui n'avait jamais été faite (elle est rappelée comme telle
dans la spec §13 : « ⚠️ **Aucune mesure de performance n'a été faite** »).

## 2. Protocole exact

| Champ | Valeur |
|---|---|
| Cerveau de départ | **copie** de `brains/VIS01_preuve/aa_temoin.brain` (`bus = 32`, né le 10/09/2026 avec le code de `3281f3e`), recopiée **avant CHAQUE run** sous `<BRAS>_rep<k>.brain` |
| Graine | `11`, identique dans les 6 runs |
| Bras SANS | aucun drapeau (le chemin actuel, sans aucun objet de télémétrie) |
| Bras AVEC | `--telemetrie-3d udp:127.0.0.1:9998` — **aucun serveur en écoute** (cas nominal de la spec §9 : la trame est perdue, le tick n'est jamais retardé). Un serveur en écoute ajouterait un **second processus qui vole du CPU au run**, donc confondrait la mesure |
| Durée par run | `--jours 50` = **20 000 ticks** (durée choisie pour que le démarrage de ~3,5 s ne pèse que ~5 % du temps mesuré) |
| Répétitions | **3 par bras, entrelacées** (`SANS, AVEC, SANS, AVEC, SANS, AVEC`) : une dérive thermique de la machine frappe alors les deux bras également |
| Démarrage mesuré à part | 1 run `--jours 0` par bras sur une copie (`t0`), pour soustraire l'import `torch` + la résurrection du `.brain` + le montage |
| Device / W&B | `NAULTHENE_DEVICE=cpu` · `--no-wandb` (le logging W&B coûte du temps et n'a rien à voir avec le rapporteur) |
| Ne mesure PAS | un navigateur connecté ; un serveur en écoute ; un cerveau à `dim_bus = 145` |

Commande, telle qu'elle sera lancée :

```bash
cd "…/21. AGI"
for rep in 1 2 3; do
  for BRAS in SANS AVEC; do
    cp brains/VIS01_preuve/aa_temoin.brain "brains/VIS01_surcout_10092026/surcout_${BRAS}_rep${rep}.brain"
    /usr/bin/time -p env NAULTHENE_DEVICE=cpu PYTHONPATH=src venv/bin/python3 \
        -m naulthene.cerveau.noyau --graine 11 --jours 50 --no-wandb \
        --brain "brains/VIS01_surcout_10092026/surcout_${BRAS}_rep${rep}.brain" \
        $([ "$BRAS" = AVEC ] && echo "--telemetrie-3d udp:127.0.0.1:9998") \
        > "brains/VIS01_surcout_10092026/surcout_${BRAS}_rep${rep}.log" 2>&1
  done
done
```

**Métrique** : `ticks/s = 20 000 / (temps mural du run − temps mural du run --jours 0 du même bras)`.
Les 6 valeurs brutes sont reportées, plus la **médiane** de chaque bras, et l'écart des médianes
en % — jamais l'écart d'une seule paire.

**Témoin de validité** : les deux bras doivent promouvoir les **mêmes niveaux** (le drapeau est
bit-identique, prouvé par l'A/A de `brains/VIS01_preuve/`) ; un écart de niveaux signalerait que la
mesure de temps compare deux choses différentes.

**Ce que la mesure ne peut pas trancher, écrit d'avance** : sous ~2 %, l'écart entre deux runs
d'une machine non dédiée est du même ordre que le bruit de mesure. Si c'est le cas, ce sera **dit**
(« non séparable du bruit à 3 répétitions »), jamais maquillé en « coût négligeable ».

## 3. Pourquoi ce cerveau-là, et pas un autre

- `brains/08092026_sci01_balayage_K/` est une **campagne historique** : interdite d'usage ici.
- `aa_temoin.brain` a été **produit par le code même de cette version** (`3281f3e`), donc aucun
  risque de greffe, de remap de niveau ou de comportement de compatibilité — un `.brain` plus
  ancien (v41.32) aurait mélangé le surcoût cherché avec une migration.
- Sa taille (`bus = 32`, croissant par neurogenèse pendant 50 jours) est **plus petite** que le
  `dim_bus = 145` de la spec : c'est une **limite assumée** du protocole, écrite ici avant la
  mesure. Le coût des hooks ne dépend pas de la largeur des couches (une capture par appel de
  couche, à une ligne), mais l'encodage des trames, lui, grossit avec le bus — c'est dit dans la
  section des limites.

## 4. Vérifications passées au dépouillement

| Vérification | Résultat |
|---|---|
| Les 6 runs vont au bout | ✅ **6/6, `exit 0`**, 50 bilans `🌙 Jour` par run (20 000 ticks chacun) — `chrono.txt` |
| **Niveaux promus identiques entre les deux bras** | ✅ `diff` **VIDE** pour chacune des 3 paires ; séquence identique partout : **8 × Niveau 1, 9 × Niveau 2, 33 × Niveau 3** (50 journées) — le drapeau n'a donc rien changé au comportement, ce qui est la condition pour que les deux temps mesurent la même chose |
| `dim_bus` final identique | ✅ **`Bus: 71 dims`** au dernier bilan des **6** runs (départ 32, donc 10 neurogenèses : le cerveau a plus que doublé pendant la mesure, et il a doublé **pareil** dans les deux bras) |
| Le bilan de fin de run affiche les compteurs (bras AVEC) | ✅ les 3 runs AVEC impriment la ligne : **11 structure(s) écrite(s), 0 ratée(s), 0 erreur(s)** — **3 762 / 3 764 / 3 759** datagrammes envoyés, **0 perdu** |
| Le bras SANS n'imprime **aucune** ligne de télémétrie | ✅ **0** occurrence de `TÉLÉMÉTRIE` dans les 3 journaux SANS (le run témoin reste celui d'avant VIS-01) |
| Témoin « la mesure n'est pas vide » | ✅ un rapporteur jamais attaché aurait rendu les deux bras identiques ; ici ~3 760 datagrammes par run AVEC prouvent que le chemin chaud a bien travaillé (et le run `e2e`, avec un serveur réel, les a comptés : **13 trames d'activité + 68 événements reçus pour 1 journée**) |

## 5. Chiffres bruts

### 5.1 Temps muraux (mesurés par `date +%s.%N` autour de chaque commande, `chrono.txt`)

| Run | Jours | Début (local) | Secondes | Exit |
|---|---:|---|---:|---:|
| `demarrage_SANS` (`--jours 0`) | 0 | 19:09:14 | 3,37 | 0 |
| `demarrage_AVEC` (`--jours 0`) | 0 | 19:09:18 | 2,81 | 0 |
| `prevol_SANS` | 5 | 19:09:20 | 8,08 | 0 |
| `prevol_AVEC` | 5 | 19:09:28 | 8,33 | 0 |
| `surcout_SANS_rep1` | 50 | 19:09:37 | **58,86** | 0 |
| `surcout_AVEC_rep1` | 50 | 19:10:36 | **62,16** | 0 |
| `surcout_SANS_rep2` | 50 | 19:11:38 | **58,05** | 0 |
| `surcout_AVEC_rep2` | 50 | 19:12:36 | **62,14** | 0 |
| `surcout_SANS_rep3` | 50 | 19:13:38 | **57,96** | 0 |
| `surcout_AVEC_rep3` | 50 | 19:14:36 | **61,87** | 0 |
| `demarrage_SANS_bis1/2/3` | 0 | 19:15→19:16 | 3,63 · 2,84 · 2,75 | 0 |
| `demarrage_AVEC_bis1/2/3` | 0 | 19:15→19:16 | 2,84 · 2,90 · 3,02 | 0 |

*Fin des mesures : 19:15:38* (les 3 démarrages supplémentaires ont été faits **après**, pour resserrer
le coût fixe — c'est écrit ici parce que c'est un ajout au protocole annoncé, pas une mesure
d'origine).

### 5.2 Coût fixe (import de `torch` + résurrection du `.brain` + montage), 4 mesures par bras

| Bras | Mesures (s) | Médiane |
|---|---|---:|
| SANS | 3,37 · 3,63 · 2,84 · 2,75 | **3,10** |
| AVEC | 2,81 · 2,84 · 2,90 · 3,02 | **2,87** |

⚠️ **Le montage de la télémétrie ne coûte rien de mesurable ici** : les deux médianes diffèrent de
0,23 s **dans le sens d'un AVEC plus rapide**, soit moins que la dispersion des mesures (0,88 s
d'amplitude côté SANS). Le coût de l'instrument est donc **par tick**, pas au démarrage.

### 5.3 Le surcoût, en ticks/s (20 000 ticks par run)

| Bras | Temps mural médian | Démarrage médian | **Boucle** (mur − démarrage) | **ticks/s** (boucle seule) |
|---|---:|---:|---:|---:|
| SANS | 58,05 s | 3,10 s | **54,95 s** | **364,0** |
| AVEC | 62,14 s | 2,87 s | **59,27 s** | **337,4** |

**Écart : +7,87 % de temps de boucle, soit −7,30 % de débit (ticks/s).**

**Sensibilité à la convention de soustraction du démarrage** (parce que le chiffre ne doit pas
dépendre d'un choix caché) :

| Convention | Écart de temps |
|---|---:|
| Aucune soustraction (temps mural brut, ce que l'utilisateur voit) | **+7,05 %** |
| Démarrage commun soustrait (médiane des 8 mesures) | **+7,41 %** |
| Démarrage propre à chaque bras soustrait (retenu) | **+7,87 %** |

→ **Le surcoût est de ≈ +7,5 % (± 0,5 point)**, quelle que soit la convention.

**Il est très au-dessus du bruit** : la dispersion entre les 3 répétitions d'un même bras est de
**1,55 %** (SANS : 57,96–58,86) et **0,47 %** (AVEC : 61,87–62,16), soit **5 à 15 fois moins** que
l'effet mesuré. Les 3 paires vont toutes dans le même sens, avec un écart de 3,3 à 4,2 s.

**Ce que le surcoût contient, exactement** : les 12 forward hooks (capture par tick), l'encodage
des trames d'activité à 15 Hz, l'envoi UDP (non bloquant), le fichier de structure au montage puis
après chaque neurogenèse (**11 écritures** ici), et les compteurs. C'est le coût **complet du
drapeau**, pas celui des seuls hooks — les séparer demanderait un banc dédié (hors des fichiers
autorisés par cette tâche).

## 6. Limites (écrites par moi d'abord)

1. **3 répétitions par bras, une seule graine (11), un seul cerveau de départ, une seule machine.**
   Ce n'est pas un intervalle de confiance : c'est un écart reproductible sur 3 paires, dont la
   dispersion interne est 5 à 15 fois plus petite que l'effet.
2. **Le cerveau mesuré est petit** (`bus = 32 → 71`) et **grossit pendant la mesure** : les 3 760
   datagrammes par run sont encodés sur un bus de 32 à 71, pas sur le `dim_bus = 145` de la spec
   (trame `structure` de 305 Ko / activité d'environ 3,6 Ko). Or **le coût qui grossit avec le bus
   est justement l'encodage des trames** : à `dim_bus = 145`, le surcoût mesuré ici est donc un
   **minorant** du surcoût réel. Ce point est la limite la plus importante de cette mesure.
3. **Aucun serveur en écoute** dans les 6 runs mesurés (décision du protocole) : on mesure le coût
   côté cerveau, pas celui d'un consommateur. Un serveur qui tourne sur la même machine volerait du
   CPU au run, donc confondrait la mesure (le run `e2e` montre séparément que les trames arrivent).
4. **Aucun navigateur connecté** : le coût des connexions SSE n'est pas dans ces chiffres (elles
   ne coûtent rien au cerveau, qui n'envoie qu'en UDP).
5. **La soustraction du démarrage est un choix** : il est explicité, chiffré sous trois
   conventions, et l'écart ne change pas de signe ni d'ordre de grandeur. Mais la mesure **ne
   dispose pas d'une horloge interne au run** (aucun point de repère temporel dans le journal
   console) : c'est la faiblesse de méthode assumée de ce protocole.
6. **Un seul état de machine** : pas de mesure sous charge (une campagne en parallèle), pas de
   mesure thermique longue. Les 6 runs ont tourné seule sur la machine, dans la même fenêtre de
   6 minutes.

## 7. Ce que cela ferme, ce que cela laisse ouvert

- **Ferme** : la dernière preuve manquante de la spec §10 (« Surcoût du rapporteur — chiffré,
  jamais estimé ») et l'avertissement de la spec §13 (« aucune mesure de performance n'a été
  faite »). Le surcoût du drapeau `--telemetrie-3d` est de **≈ +7,5 % de temps de run, soit
  −7,3 % de ticks/s** (364,0 → 337,4 ticks/s), mesuré sur 3 paires de 20 000 ticks partant du même
  cerveau à la même graine.
- **Précise une garantie de la spec §8** : « un run n'est jamais ralenti » est **vrai au sens du
  réseau** (UDP non bloquant, file bornée : un consommateur absent, lent ou saturé ne retarde
  jamais un tick — c'est ce que la mesure confirme, 0 perdu) et **faux au sens du calcul** :
  l'instrument lui-même coûte ≈ 7,5 %, et c'est désormais chiffré au lieu d'être supposé.
- **Laisse ouvert** : (a) le même chiffre à `dim_bus = 145` (le coût d'encodage y est plus grand —
  à mesurer sur un vrai cerveau mature, hors du périmètre de cette tâche) ; (b) la séparation
  hooks / encodage / écriture du fichier ; (c) le comportement sous charge machine ; (d) le coût
  des connexions SSE avec un navigateur réellement ouvert.

## 8. Preuve bout en bout avec un serveur RÉEL (étape 2) — et l'écart constaté

Après les mesures de temps (pour ne pas voler de CPU au run mesuré), la chaîne de l'étape 2 a été
montée pour de vrai, dans ce dossier :

```bash
# terminal 1 — le spectateur, en écoute UDP
PYTHONPATH=src venv/bin/python3 -m naulthene.instruments.cerveau_3d --serveur-seul --udp 9998 --port 8770
# terminal 2 — un run observé, sur une copie neuve du même cerveau
PYTHONPATH=src venv/bin/python3 -m naulthene.cerveau.noyau --graine 11 --jours 1 --no-wandb \
    --brain brains/VIS01_surcout_10092026/e2e_run.brain --telemetrie-3d udp:127.0.0.1:9998
```

| Observation | Valeur mesurée |
|---|---|
| Page servie | **HTTP 200** (`e2e_page.html`, 1 702 octets) |
| `/sante` **avant** le run | `{"bus":{"sequence":0,"sequence_structure":0,"evenements_total":0,…}}` |
| `/sante` **après** le run | `{"bus":{"sequence":13,"sequence_structure":0,"evenements_total":68,"evenements_en_file":32},…}` |
| Bilan du run | **81 datagrammes envoyés, 0 perdu** — **13 trames d'activité** (15 Hz tenu : 400 ticks en ~1 s) **+ 68 événements** = 81 : **tout ce qui est parti est arrivé** |
| `/structure` **après** le run | **`{}`** — et `sequence_structure` reste **0** |

🔴 **Écart constaté, mesuré ici et écrit ici** : la trame `structure` n'arrive **jamais** au
serveur en `--serveur-seul`. Ce n'est pas un hasard : elle n'est **pas envoyée en UDP**
(305 Ko ≫ le plafond dur de 65 507 o par datagramme, avenant du 10/09) — le run l'écrit dans
`<brain>.vis01_structure.json` (ici `e2e_run.brain.vis01_structure.json`, 30 517 octets), et
**aucun code ne relit ce fichier** : `cerveau_3d/serveur.py` et `cerveau_3d/__main__.py` ne
connaissent que la structure de leur source locale (`grep -rn "vis01_structure" src/` ne rend que
`noyau.py`). Conséquence : la page reste sur « en attente de la structure… », alors que les trames
d'activité et d'événement, elles, **arrivent** (13 + 68 reçues).

**Ce que cela signifie, exactement** : l'étape 2 est **livrée en partie** — le run s'observe sans
être modifié (preuve A/A), il dépose sa structure sur le disque et émet ses trames ; la moitié
« **lue par le serveur** » de l'avenant n'est pas implémentée. C'est enregistré au registre
(**VIS-01**, « livré en partie ») et dans `LANCEMENT.md` §7bis, jamais caché derrière un « ça
marche ».


