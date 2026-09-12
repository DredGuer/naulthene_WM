# Journal des runs — une ligne par campagne, écrite AU LANCEMENT

> **Règle de trace, quatrième volet** (posée le 07/09/2026, demande utilisateur).
> Le `LISEZ_MOI.md` de campagne porte le **protocole** ; ce journal porte le **calendrier**.
> Les deux sont obligatoires, et tous deux s'écrivent **avant** que le premier run démarre.
>
> ⚠️ **Pourquoi ce fichier existe** : le 07/09, la campagne des branches persistantes avait
> son protocole complet mais **aucun horodatage versionné** — début, fin estimée et fin
> réelle n'existaient que dans les métadonnées du système de fichiers, qui ne survivent ni à
> un `git clone` ni à une copie. Et l'estimation annoncée à l'oral (« ~2 h ») s'est révélée
> fausse d'un facteur 3 : la mesure du rythme réel donnait **~6 h**. Un écart de cette taille
> est invisible sans trace écrite.

## Comment remplir une ligne

| Champ | Règle |
|---|---|
| **Titre** | le nom de la campagne, pas la conclusion espérée |
| **Début** | `date "+%Y-%m-%d %H:%M"` au moment du lancement, jamais reconstruit après coup |
| **Fin estimée** | dérivée du **rythme mesuré** après ~30 min, jamais devinée à l'avance |
| **Fin réelle** | remplie à la fin ; l'écart avec l'estimation est une information |
| **Pourquoi** | la question posée, en une phrase, telle qu'elle a été formulée |
| **Statut** | 🟡 en cours · ✅ terminée · ❌ échouée/annulée |

⚠️ **Une campagne annulée reste au journal**, avec la raison. Le 05/09, une campagne audio de
8 h a été annulée par son propre pré-vol : c'est ce genre d'entrée qui évite de la relancer.

---

## Runs

### ✅ `VIS01_etape2_fichier_10092026` — la structure relue par le serveur (tâche 11)

| | |
|---|---|
| **Début** | 2026-09-10 19:29 *(entrée écrite à 19:28, AVANT le premier lancement ; `date "+%Y-%m-%d %H:%M"`)* |
| **Fin estimée** | **~19:32** (≈ 3 min) — dérivée du rythme **MESURÉ** par `VIS01_surcout_10092026` (50 jours ≈ 58 s de temps mural, démarrage ≈ 3,4 s inclus ⇒ ≈ 3,6 j/s, soit ~0,3 s/jour) : 1 à 2 runs de 60 jours (≈ 20 s chacun) + les observations HTTP/SSE, qui ne coûtent rien au run |
| **Fin réelle** | **2026-09-10 19:31** — **écart ≈ −1 min sur l'estimation (~2 min au lieu de ~3 min)** : le run a tenu 60 jours en **75 s** (1,25 s/jour — le rythme de `VIS01_surcout` est confirmé), et **un seul run a suffi** (la neurogenèse a eu lieu : `dim_bus` 16 → 68) |
| **Coût** | 1 run de 60 jours sur un cerveau **NEUF** (`etape2.brain`, naissance, `dim_bus = 16`), graine 11, `NAULTHENE_DEVICE=cpu`, `--no-wandb`, `--telemetrie-3d udp:127.0.0.1:9998`, observé par un serveur `--serveur-seul --structure-fichier` **lancé avant le run** (fichier absent au démarrage) |
| **Statut** | ✅ terminée — **`/structure` rend 12 couches, `sequence_structure` passe de 0 à 6 PENDANT le run** |

**Pourquoi** : la tâche 11 répare la moitié « lue par le serveur » de l'avenant de protocole du
10/09 (la trame `structure` voyage par FICHIER, trop grosse pour un datagramme UDP). L'e2e de la
tâche 10 avait mesuré l'état d'avant, serveur vivant et run vivant : `/structure` = `{}` et
`sequence_structure = 0` pendant que 81 trames d'activité/événements arrivaient par UDP. Question
posée : *un serveur `--serveur-seul --structure-fichier` voit-il enfin la structure d'un run en
cours, et la voit-il CHANGER (neurogenèse) sans redémarrer ?*

**Résultat** : oui, et sans redémarrage. Au démarrage (fichier absent) `/structure` rend `{}` et la
veille compte ses absences ; **4 s après le lancement du run** la page a **12 couches à
`dim_bus = 16`**, puis le serveur republie **5 fois pendant le run** (32 → 48 → 51 → 67 → 68) à
mesure des neurogenèses. Un client SSE connecté pendant le run a reçu **4 trames `structure`**
(`dim_bus` 16, 32, 48, 51) **+ 252 `activite` + 1 404 `evenement`**, la structure toujours en tête
de flux. La trame finale pèse **88 488 o**, au-dessus du plafond dur de 65 507 o d'un datagramme :
le fichier était bien la seule voie. Le run, lui, n'a pas été ralenti (60 jours en 75 s).

Protocole complet et chiffres bruts : [`brains/VIS01_etape2_fichier_10092026/LISEZ_MOI.md`](../../brains/VIS01_etape2_fichier_10092026/LISEZ_MOI.md).
⚠️ Aucun fichier de `brains/08092026_sci01_balayage_K/` (campagne historique) n'est lu ni écrit ;
aucun `.brain` préexistant n'est écrasé — le cerveau de cette campagne **naît** dans son dossier.

### 🟡 `VIS01_surcout_10092026` — le surcoût du rapporteur (spec VIS-01 §10)

| | |
|---|---|
| **Début** | 2026-09-10 19:08 *(entrée écrite à 19:07, AVANT le premier lancement — l'horodatage de chaque run est aussi enregistré dans `chrono.txt`, dans le dossier de campagne)* |
| **Fin estimée** | **~19:16** (≈ 8 min) — dérivée du rythme **MESURÉ** de la preuve A/A de la tâche 9 (5 jours en ≈ 9 s de temps mural, démarrage de ≈ 3,5 s inclus ⇒ ≈ 3,6 j/s ⇒ 50 jours ≈ 58 s par run) : 2 pré-vols (5 jours) + 2 runs `--jours 0` + 6 runs de 50 jours + marges |
| **Fin réelle** | **2026-09-10 19:15:38** — **écart ≈ −1 min sur l'estimation (~7 min 30 au lieu de ~8 min)**, soit **−6 %** : le rythme dérivé de la preuve A/A était bon à ~2 % près (58 s prévus, 58–62 s mesurés par run). Les **3 démarrages supplémentaires** (19:15→19:16) ont été ajoutés **après** la mesure pour resserrer le coût fixe : c'est un ajout au protocole, consigné comme tel |
| **Coût** | 6 runs × 50 jours (20 000 ticks) sur le **même cerveau copié** 6 fois (`aa_temoin.brain`, `bus = 32`, graine 11) : 3 répétitions par bras, entrelacées · plus 2 pré-vols de 5 jours, 4 mesures de démarrage `--jours 0` par bras, et un run de 1 jour observé par un vrai serveur (`e2e`) |
| **Statut** | ✅ terminée et **dépouillée** — **≈ +7,5 % de temps de run, soit −7,3 % de ticks/s (364,0 → 337,4)** |

**Pourquoi** : la spec VIS-01 §10 exige une preuve « **surcoût du rapporteur — chiffré, jamais
estimé** : ticks/s avec et sans hooks, même graine, même cerveau ». C'est la **seule preuve du
chantier qui n'avait jamais été faite** (la spec §13 le dit noir sur blanc : « Aucune mesure de
performance n'a été faite »). Question posée : *un run qui vit est-il ralenti par les 12 forward
hooks du rapporteur, et de combien, en ticks/s ?*

**Résultat** : temps mural médian **58,05 s (SANS) vs 62,14 s (AVEC)** sur 20 000 ticks, démarrage
soustrait : **364,0 vs 337,4 ticks/s**, soit **+7,87 % de temps de boucle / −7,30 % de débit**
(l'écart vaut +7,05 % à +7,87 % selon la convention de soustraction du démarrage — la dispersion
entre répétitions d'un même bras est de 0,47 à 1,55 %, donc **5 à 15 fois plus petite que
l'effet**). Les deux bras ont promu les **mêmes niveaux** (`diff` vide sur les 3 paires) et fini au
**même `dim_bus` (71)** : la mesure compare bien la même chose. ⚠️ **Minorant** : mesuré à
`bus = 32 → 71`, pas au `dim_bus = 145` de la spec, et c'est l'encodage des trames qui grossit avec
le bus.

Protocole complet et chiffres bruts : [`brains/VIS01_surcout_10092026/LISEZ_MOI.md`](../../brains/VIS01_surcout_10092026/LISEZ_MOI.md).
⚠️ Le dossier de campagne a été créé **avant** le premier run, et aucun `.brain` existant n'est
écrasé : chaque run part d'une **copie fraîche** du même cerveau (celle de
`brains/VIS01_preuve/`), sous un nom propre.

🔴 **RÉTRACTATION DU 10/09/2026 (vague finale, constat I5) — CE QUE DISAIT CE PARAGRAPHE (ancien
énoncé en regard, dogme « rien sans écrit ») :**

> « **Découverte annexe (mesurée pendant la clôture, et écrite ici parce qu'elle a coûté un run)** :
> en `--serveur-seul`, la **structure n'arrive pas** — le run écrit bien
> `<brain>.vis01_structure.json`, mais **aucun code ne relit ce fichier** (l'étape 2 est donc livrée
> **en partie** ; les trames d'activité et d'événement, elles, arrivent : 13 + 68 pour le run `e2e`). »

**Deux choses y étaient fausses, et la seconde contredisait une entrée située soixante lignes plus
haut dans CE MÊME fichier :**

1. « en `--serveur-seul`, la structure n'arrive pas » — **vrai seulement SANS `--structure-fichier`**.
   Avec l'option (tâche 11), la structure arrive : l'entrée `VIS01_etape2_fichier_10092026` de ce
   fichier a mesuré `/structure` passant de `{}` à **12 couches**, `dim_bus` **16 → 68**,
   `sequence_structure` **0 → 6**.
2. « **aucun code ne relit ce fichier** » — **faux depuis la tâche 11** (`2fad056`) :
   `VeilleurStructureFichier` (`cerveau_3d/serveur.py`) le relit au démarrage puis à chaque
   changement, et `__main__.py` l'expose par `--structure-fichier`. C'est l'énoncé du BAS qui était
   périmé, pas celui du haut.

**Ce qui reste vrai, et qui a bien coûté un run** : la découverte de clôture n'était pas fausse sur
le FOND — le run écrivait un fichier que personne ne lisait —, elle l'est devenue le lendemain. Le
run `e2e` reste donc la mesure de référence pour la version d'AVANT la tâche 11 (13 trames
d'activité + 68 événements, **aucune** structure reçue) : **datée, elle ne périme pas**. Détail et
preuves : section 8 du `LISEZ_MOI` de la campagne `VIS01_surcout_10092026`.

---

### ✅ `VIS01_preuve` — la preuve A/A de `--telemetrie-3d` (tâche 9) — **entrée écrite APRÈS les runs**

| | |
|---|---|
| **Début** | 2026-09-10 18:47:45 |
| **Fin estimée** | *(aucune — voir l'écart de trace ci-dessous : l'entrée n'existait pas au lancement)* |
| **Fin réelle** | 2026-09-10 18:48:03 — **18 s pour les deux runs** (bien plus court que les « plusieurs minutes » annoncées : cerveau neuf `bus = 16`, CPU, 2 000 ticks par run) |
| **Coût** | 2 runs × 5 jours, graine 11, même code : `aa_temoin.brain` (aucun drapeau) vs `aa_telemetrie.brain` (`--telemetrie-3d udp:127.0.0.1:9998`) · + un run bout en bout `--jours 1` avec un listener UDP réel (`e2e/`, 18:49:21) |
| **Statut** | ✅ terminée et **dépouillée** — `diff` des niveaux promus **VIDE** |

**Pourquoi** : la spec VIS-01 §10 exige que le drapeau `--telemetrie-3d` (étape 2, la seule qui
touche `noyau.py`) laisse le run **bit-identique** sans lui. Preuve de non-effet, pas mesure
d'effet.

**Résultat** : `diff` des niveaux promus **vide** (5 × `Niveau 1` de chaque côté — témoin ATTEINT),
`tick_absolu = 2 000` des deux côtés, `.brain` **identiques au contenu** (97 tenseurs
`torch.equal`, 130 entrées d'archive au même SHA-256 ; l'écart brut de 520 o est la longueur du nom
de fichier × 130 entrées, rétracté dans le CHANGELOG `[v41.76]`). Une **vraie neurogenèse** a eu
lieu dans le bras observé (`Thermostat: MUTATION +16 !`), donc le point d'appel « après
neurogenèse » a bien été traversé.

🔴 **Écart de trace, consigné et non masqué** : ces runs ont été lancés **sans** entrée de journal
au lancement et **sans** `LISEZ_MOI.md` de campagne — la liste des fichiers autorisés du brief de la
tâche 9 était close et le commit ciblé devait ne rien contenir d'autre (le rapport de la tâche 9
l'a écrit comme préoccupation, pas caché). La présente ligne et le `LISEZ_MOI.md` ont été écrits le
**10/09/2026 à 19:06**, soit **~18 min après la fin des runs**. Les horodatages ci-dessus sont
reconstruits depuis le journal du système de fichiers (`mtime` des `.brain` : 18:47:54 et 18:48:03)
et la première ligne horodatée des logs `wandb` (18:47:47) — jamais depuis une estimation de
mémoire. Le verdict et les chiffres n'en dépendent pas : c'est **la règle de trace** qui était
violée, et c'est elle qui est réparée.

Protocole complet : [`brains/VIS01_preuve/LISEZ_MOI.md`](../../brains/VIS01_preuve/LISEZ_MOI.md).

---

### ✅ `08092026_sci01_balayage_K` — Wave 1 : balayage K/ε sur l'apprenant réparé

| | |
|---|---|
| **Début** | 2026-09-08 (v41.68) |
| **Fin estimée** | ~18-22 h *(Wave 1 : 60 runs × 1500 j, 6 en parallèle — rythme mesuré sur le pré-vol 2 nuits)* |
| **Fin réelle** | 2026-09-09 ~18:55 — **60/60 runs, 0 échec** (écart ~×2 sur l'estimation : les bras lourds K16/K8_CLIP sont ~2× plus lents que K1-K8, rythme mesuré ~2,7 j/min K16 · ~5,8 j/min K8_CLIP) |
| **Coût** | Wave 1 : 6 bras × 10 graines × 1500 jours · Wave 2 (différée) : n=20 ciblé (graines 122→222) |
| **Statut** | ✅ Wave 1 terminée et **dépouillée** (09/09) — verdict final en attente de la Wave 2 (n=20) |

**Pourquoi** : le point K=8 du 07/09 a été mesuré avec le **rejeu faussé** (APP-01) — il
n'est plus un témoin valide. Le balayage re-mesure la **forme** de l'effet de K (2/4/8/16)
et le signe du clip (ε = 0,2 à K=8) sur le socle sain (voix libre + `--detach-c2` constants
sur tous les bras, témoin K=1 inclus). Indicateurs clés extractibles des logs : maîtrise,
niveau, **distribution du ratio `exp(lp − lp_old)` et fraction clippée** (ligne console
`Rejouer (v41.68)`, v41.64/68).

**Pré-vol (08/09)** : manifeste validé (format strict MES-01) · 2 nuits réelles K8_NU :
exit 0, 2 bilans, **0 violation** du garde de parité de forme, 2 lignes `Rejouer` ;
drapeau `[VARIANTE] 8 epoques` présent.

**Résultat Wave 1 (dépouillement strict 09/09, n=10 par bras — voir le
[carnet](../recherche/campagnes/SCI01_WAVE1_09092026_la_forme_en_cloche.md))** :
franchissements du mur `SimpleCrossingS9N1` → `LavaGapS5` : **0/10 · 0/10 · 8/10 · 10/10 ·
3/10** pour K = 1, 2, 4, 8, 16 — **forme en cloche, optimum K=8**. Le clip ε=0,2 **ne nuit
plus** (K8_CLIP_e02 = 10/10 ; fraction clippée ~8 % — clip quasi inerte car le ratio est
déjà sain). ⚠️ Aucun `t` ne passe Bonferroni à n=10 ; le juge maîtrise est confondu par le
palier — le niveau porte la réponse. Wave 2 (graines 122→222) requise pour le verdict final.

[Protocole](../../brains/08092026_sci01_balayage_K/LISEZ_MOI.md) ·
[Dépouillement Wave 1](../../brains/08092026_sci01_balayage_K/depouillement_wave1.txt)

### ✅ `08092026_sci01_balayage_K` — Wave 2 : n=20 ciblé (graines 122→222)

| | |
|---|---|
| **Début** | 2026-09-09 23:11 |
| **Fin estimée** | ~40-45 h *(dérivée du rythme mesuré Wave 1 : ~43 h pour 60 runs, bras lourds dominants)* |
| **Fin réelle** | **2026-09-11 23:15** — **60/60 runs, 0 échec** · écart ≈ **−2 h sur l'estimation haute** (~48 h réelles) |
| **Coût** | 6 bras × 10 graines (122, 133, 144, 155, 166, 177, 188, 199, 211, 222) × 1500 jours |
| **Statut** | ✅ terminée et **dépouillée à n=20** (12/09) |

**Pourquoi** : compléter la cohorte à **n=20 par bras** (règle cardinale : aucun test formel
sous 20 graines). La Wave 1 (n=10) a montré une **cloche 0/0/8/10/3** (optimum K=8) et un
**clip inerte** (~8 % de fraction clippée) — la Wave 2 absorbe la variance inter-individuelle
et tranche si K=8 est le socle moteur, au dépouillement final sur `manifeste.json` (20 graines).

**Pré-vol** : aucun nouveau nécessaire — pré-vol Wave 1 (manifeste validé, 2 nuits K8_NU
exit 0, garde de parité 0 violation) couvrait la vague.

⚠️ **Hétérogénéité de code pendant la vague — mesurée et requalifiée.** 4 commits **VIS-01**
(10/09 16:03 → 20:12) ont modifié `noyau.py` (+352 lignes, en-tête → v41.75/41.76) alors que la
vague tournait : K1→K8 sous **v41.68**, K16 à cheval, K8_CLIP sous **v41.76**. **Vérification
A/A du 12/09** (graine 11, 10 jours, 8 époques/nuit, sans `--telemetrie-3d`, worktree `44a45a7`
vs HEAD) : 9 lignes clés **identiques**, logs complets **identiques** (505 lignes), séquence de
jours identique, **payload sémantique des `.brain` identique** (47 tenseurs/scalaires, aucune
différence). Les changements sont de la **télémétrie opt-in** : la cohorte est
**fonctionnellement homogène**. Réserve consignée : la règle « même code » n'est pas respectée
*littéralement*, elle l'est *sur preuve mesurée*.

**Résultat n=20 (dépouillement strict, seuil Bonferroni 2,86)** :

| Bras | Franchissements | Maîtrise moy. |
|---|---|---|
| K1_TEMOIN | 0/20 | 14,0 % |
| K2_NU | 1/20 | 20,0 % |
| K4_NU | **13/20** | 16,1 % |
| K8_NU | **18/20** | 12,0 % |
| K16_NU | 4/20 | 9,5 % |
| **K8_CLIP_e02** | **20/20** | 12,5 % |

**Cloche confirmée** (0 · 1 · 13 · **18** · 4) avec **optimum à K=8** ; à palier égal, la
maîtrise monte avec K jusqu'à 8 (15 → 20 → 25 → 27,5 %) puis K16 s'effondre (7,5 %). **Le clip
ε=0,2 est INERTE** (fraction clippée ~8 %, K8_CLIP vs K8_NU `p` = 0,49) — le « clipping nuit »
du 07/09 est **requalifié** (artefact du rejeu faussé APP-01). ⚠️ Aucun `t` de maîtrise n'est
interprétable (confusion de palier) : **la cloche repose sur des comptages, pas sur un test**.

⚠️ **Faux refus MES-01 corrigé au passage** : `K8_NU_g144` (promu au jour 1500) était déclaré
« INACHEVÉ 1499/1500 » parce que le motif du lecteur exigeait `maîtrise <nombre>%` et **jetait
les nuits de promotion** (`maîtrise —`). `journal_cursus.py` corrigé (le niveau suffit à valider
une nuit) ; re-dépouillement des **6 campagnes publiées : 0 verdict changé** (5 strictement
identiques, BP marginalement déplacé mais NS→NS).

[Protocole](../../brains/08092026_sci01_balayage_K/LISEZ_MOI.md) ·
[Verdict n=20](../recherche/campagnes/SCI01_N20_12092026_le_verdict.md)

#### 🗒️ Point d'étape — 08/09/2026 09:37 (24 runs terminés / 60)

**Avancement** : K1_TEMOIN **10/10** · K2_NU **10/10** · K4_NU **4/10** (g11, g22, g33, g44) ·
K8_NU / K16_NU / K8_CLIP_e02 non lancés. 0 échec sur les 24 runs terminés.

**Premières mesures directes (fin de run, aucun `t` — cohorte incomplète, pas de verdict)** :

- **K1_TEMOIN** : maîtrise finale moyenne **11,5 %** (médiane 12,5, min 5, max 20) · niveau
  4/15 partout · **0/10** franchissements.
- **K2_NU** : maîtrise finale moyenne **13,0 %** (médiane 15,0, min 5, max 20) · niveau 4/15
  partout · **0/10** franchissements.
- **K4_NU** (4 terminés) : **3/4** au niveau 5/15 (`LavaGapS5`, l'étage au-delà du mur
  `SimpleCrossingS9N1` — g11, g33, g44) · g22 reste en 4/15 (maîtrise 30 %). Signal précoce
  cohérent avec l'effet seuil de K=8 du 07/09, mais **n=4 = anecdote statistique** : rien ne
  sera calculé avant les 10 runs du bras.

**⚠️ Réserve méthodologique — Juge 4 (mécaniste, ratio/clippés) sur les bras NU** : dans
`noyau.py`, `ratios_epochs` n'est rempli que si `RATIO_CLIPPE_ACTIF` (`~2224`) — les bras NU
(K1→K16) ne loguent donc que `parité max · entropie moy` en console, et W&B étant offline,
la distribution du ratio n'est **pas** consignée sur disque pour eux. Seul K8_CLIP_e02 (non
lancé) portera la télémétrie ratio/p90/fraction clippée dans cette Wave 1. Acté : pas de
modification de code pendant que la campagne tourne ; correction prévue pour la Wave 2
(observation pure du ratio sur tous les bras, `RATIO_CLIPPE_ACTIF` inactif compris).

#### 🗒️ Point d'étape — 09/09/2026 15:42 (55 runs terminés / 60 — bras K16 et K8_CLIP en cours de bouclage)

**Avancement** : K1_TEMOIN 10/10 · K2_NU 10/10 · K4_NU 10/10 · K8_NU 10/10 · **K16_NU 10/10**
(terminé ~15:20) · **K8_CLIP_e02 5/10** terminés + 5 en cours (g66 ~1457 j, g77 ~682, g88 ~211,
g99 ~197, g111 ~92). 0 échec sur les 55 runs terminés.

**Forme provisoire des franchissements du mur `SimpleCrossingS9N1` → `LavaGapS5` (comptage
sur bras complets — AUCUN test, le dépouillement MES-01 attendra `WAVE 1 TERMINEE`) :**

| K | Franchissements / 10 | Lecture |
|---|---|---|
| K=1 | 0/10 | sous le seuil |
| K=2 | 0/10 | sous le seuil |
| K=4 | 8/10 | saut de phase |
| K=8 (nu) | 10/10 | maximum apparent |
| K=16 | **3/10** | retombée — **forme en cloche, optimum ~K=8** |
| K=8 + clip ε=0,2 | **5/5 sur terminés** | ⚠️ signal **renversé** vs 07/09 (où le clip « nuisait ») — maîtrises 15-35 %, plus saines que K8_NU pur (souvent 0-10 %) |

⚠️ **K8_CLIP inverse la conclusion du 07/09** (le « clipping nuit » avait été mesuré nuisible à
−1,00 pt sur le rejeu faussé) : sur le socle réparé, 5/5 des terminés franchissent avec des
maîtrises finales élevées. **n=5, pas de verdict** — mais c'est le fil le plus chaud du
dépouillement à venir. L'estimation de lancement (~18-22 h) est **dépassée d'un facteur ~2**
(rythme réel des bras lourds : ~2,7 j/min K16 · ~5,8 j/min K8_CLIP) — écart consigné, la fin
réelle sera reportée dans l'en-tête de campagne.

---

### ✅ `07092026_protoA_ppo_seuil60` — PPO face à la règle 60 % du cursus

| | |
|---|---|
| **Début** | 2026-09-07 18:13 |
| **Fin estimée** | ~18:50 *(dérivée du pré-vol A/A : 2 × 20 k pas en ~1 min, dont import torch)* |
| **Fin réelle** | 2026-09-07 ~18:15 — 5/5 runs terminés, **0 échec** |
| **Coût** | 5 runs PPO × 152 043 pas (arch [69,69]) · **banc** — zéro ligne de `noyau.py` |
| **Statut** | ✅ terminée |

**Écart estimé / réel** : ~35 min d'avance — l'estimation dérivée du pré-vol sur-comptait
l'import torch ; 5 runs PPO en parallèle sur `mps` ≈ 2 min de calcul réel.

**Pourquoi** : le seuil de promotion (`TAUX_PROMOTION` = 60 % × 20 épisodes) est au-dessus de
ce que PPO atteint (36-40 %) sur `SimpleCrossingS9N1` — le mur du niveau 4 est-il en partie
une **règle du cursus** ? Le banc capture le vecteur binaire victoire/défaite épisode par
épisode pendant l'entraînement → fenêtres glissantes ≥ 12/20 **et** route série (2 victoires
consécutives, l'autre branche du OU).

**Pré-vol (18:13)** : A/A 2 × 20 k pas — **vecteurs bit-identiques** (64 épisodes ×2) :
la capture est valide.

**Résultat ([carnet](../recherche/campagnes/PPO_AU_SEUIL_07092026_la_porte_60_n_est_pas_le_mur.md))** :
**2/5 graines** passent au moins une fenêtre ≥ 12/20 (g11, g33 — celles qui convergent à
~45-50 %) → verdict pré-enregistré : **le seuil 60 % n'est pas à lui seul le mur, le goulot
est l'apprenant**. Route série : **4/5 graines** déclenchent la voie des 2 victoires
consécutives (jusqu'à 47 occurrences) → un PPO dans le cursus (OU) ne resterait pas bloqué
par la porte 60 %. ⚠️ n = 5, arch 69 seul, deux graines (g22, g44) convergent mal —
instabilité de PPO lui-même, pas du script.

[Protocole complet](../../brains/07092026_protoA_ppo_seuil60/LISEZ_MOI.md)

---

### ✅ `07092026_branches_persistantes` — les branches persistantes du rollout

| | |
|---|---|
| **Début** | 2026-09-07 09:03 |
| **Fin estimée** | 2026-09-07 ~15:15 *(mesurée sur le rythme réel à 09:35 : 8,7 % en 32 min)* |
| **Fin réelle** | 2026-09-07 ~16:05 — 20/20, « CAMPAGNE TERMINEE », **0 échec** |
| **Coût** | 20 runs × 1500 jours, 6 en parallèle |
| **Statut** | ✅ terminée |

**Écart estimé / réel** : ~50 min de retard — le rythme **ralentit** en fin de course (les
cerveaux grossissent) : c'est exactement l'information que la règle « fin estimée mesurée »
voulait capturer.

**Pourquoi** : les 8 branches du rollout mental perdent **97 % de leur séparation** avant
l'horizon 7 — C2 n'évalue pas 8 plans, il évalue **une destination** vue de 8 départs. La
cause est `argmax(tete_motrice)`, pas JEPA (h7/h1 = 1,15 à action répétée contre 0,043).
Cette campagne teste si rendre les branches persistantes change quelque chose au
comportement — c'est le **prérequis** de la tête d'intention de C2 (v42).

**Prédiction écrite d'avance** : effet comportemental **peu probable**. C2 est mesuré inerte
et son gradient nuisait ; `r(ratio rollout, maîtrise) = −0,08`. Un juge 3 qui passe avec un
juge 1 nul serait **acceptable** — la mécanique marcherait sans que C2 sache s'en servir.

**Résultat (dépouillé le 07/09 soir — [carnet](../recherche/campagnes/BRANCHES_PERSISTANTES_07092026_la_mecanique_marche_la_voix_reste_inerte.md))** :
conforme à la prédiction. Juge 3 (mécaniste) **passe massivement** — h7/h1 médian
**0,0073 → 1,01**, log10 apparié `t` = **+18,76** (20/20, survit aux extrêmes à +19,31 ;
🔴 requalifié le 08/09 par la sonde MES-02, contexte et corps réels — CHANGELOG [v41.66]) ;
juges 1 (maîtrise δ **−2,10 pt**, NS), 2 (niveau 7/20 vs 5/20, Fisher `p` = 0,73) et 4 (accord,
NS) **nuls**. Sortie brute : `depouillement_BP.txt` · agrégat : `agregat_BP.json`.

[Protocole complet](../../brains/07092026_branches_persistantes/LISEZ_MOI.md)

---

### ✅ `06092026_epoques_nuit` — les époques de la nuit

| | |
|---|---|
| **Début** | 2026-09-06 ~22:00 |
| **Fin réelle** | 2026-09-07 ~00:30 *(~2 h 30, 3 bras)* |
| **Coût** | 40 runs neufs × 1500 jours, 6 en parallèle · **0 échec** |
| **Statut** | ✅ terminée |

**Pourquoi** : la politique ne recevait qu'**un seul pas de gradient par journée** de
400 ticks, contre 23 680 pour PPO sur le même banc. Un pas déplace les logits de 0,0107 pour
une marge de 0,392 : il en faudrait **~37** pour changer une décision.

**Résultat** : maîtrise **8,75 % → 19,00 %** (δ +10,25 pt, `t` = +4,81, 15/20, survit aux
extrêmes) et **5 cerveaux sur 20 franchissent le niveau 5**. 🔴 Le clipping de PPO **nuit**,
à l'inverse de l'attente théorique. [Carnet](../recherche/campagnes/EPOQUES_07092026_le_mur_du_niveau_4_est_franchi.md)

---

### ✅ `05092026_detach_c2` — le gradient fantôme de C2

| | |
|---|---|
| **Début** | 2026-09-05 23:09 |
| **Fin réelle** | 2026-09-06 ~07:00 *(~8 h)* |
| **Coût** | 20 runs neufs × 1500 jours, 6 en parallèle · **0 échec** |
| **Statut** | ✅ terminée |

**Pourquoi** : lever la réserve écrite dans le carnet de l'ablation C2 — sa *voix* est inerte,
mais son *gradient* irrigue encore `integrateur_bio`, la couche partagée.

**Résultat** : **+5,25 pt** de maîtrise (`t` = +4,97, 16/20, survit aux extrêmes). Prédiction
« probablement rien » **réfutée**. [Carnet](../recherche/campagnes/DETACH_C2_06092026_le_gradient_fantome_nuisait.md)

---

### ✅ `06092026_ppo_lavagap` — PPO au niveau du mur

| | |
|---|---|
| **Début** | 2026-09-06 ~00:30 · **Fin** ~01:10 *(~40 min)* |
| **Coût** | 5 graines + A/A + témoin aléatoire |
| **Statut** | ✅ terminée |

**Pourquoi** : la baseline « le mur n'existe pas » avait été mesurée au niveau **3**, que
Naulthène franchit — jamais au niveau **4**, où 40 runs sur 40 s'arrêtent.

**Résultat** : PPO résout `LavaGapS5` à **97,27 %** contre 6,67 % pour un marcheur aléatoire.
🔴 **RECTIFIÉ le 07/09 — mauvaise carte** : « Niveau 4/15 » est `SimpleCrossingS9N1`, pas
`LavaGapS5` (le log affiche `niveau_actuel + 1`). Ce banc a testé **une carte plus loin**
que le blocage. Sur la vraie carte du mur : PPO **36–40 %** contre **25,83 %** — ~1,5×. [Carnet](../recherche/campagnes/PPO_LAVAGAP_06092026_le_mur_n_est_pas_la_carte.md)

---

### ❌ `05092026_audio` — l'ablation de l'hémisphère audio (ANNULÉE)

| | |
|---|---|
| **Début** | 2026-09-05 · **Fin** : annulée avant lancement |
| **Coût évité** | **~8 h** |
| **Statut** | ❌ annulée par son propre pré-vol |

**Pourquoi elle devait tourner** : 19 % du réseau alloué à l'audio pour un terme `Vocal` à
σ = 0,0000 sur un cursus spatial.

**Pourquoi elle a été annulée** : le run `--sans-audio` est sorti **bit-identique** au bras de
référence. Cause mesurée sur 80 cerveaux : **aucune synapse audio n'a jamais reçu de
gradient** — geler un membre déjà gelé ne change rien. Une ablation **vide**, pas négative.
[Carnet](../recherche/enquetes_closes/AUDIO_05092026_un_hemisphere_deja_gele.md)

---

*Une campagne sans ligne ici n'a pas eu lieu.*
