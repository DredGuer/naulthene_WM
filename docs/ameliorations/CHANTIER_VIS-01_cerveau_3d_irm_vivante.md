# CHANTIER VIS-01 — Le Cerveau 3D : une IRM vivante en trois dimensions

> **Statut** : ✅ **LIVRÉ le 10/09/2026** (les 10 tâches du
> [`PLAN_VIS-01_cerveau_3d.md`](PLAN_VIS-01_cerveau_3d.md) sont closes, jusqu'au commit `3281f3e`
> puis la clôture documentaire ; **tâche 11** (`2fad056` + `433cc14`) : le serveur relit le fichier
> de structure — **l'étape 2 est complète et vérifiée de bout en bout**, voir l'avenant de §4).
> Nature : **instrument de visualisation**, pas une mécanique
> cognitive.
> **Périmètre** : étapes 0 et 1 sans aucun impact sur `noyau.py` ; l'étape 2 est la seule qui
> touche le noyau (drapeau additif, éteint par défaut, comportement bit-identique sans lui).
> **Décisions de cadrage prises le 10/09** : rendu Web/three.js · sujet = **activité tick par
> tick** · disposition = **plaques stratifiées + colonne du bus** · spectateur **strictement en
> lecture seule** (pas de mode « vivre ») · documentation = **ce chantier + `INDEX.md` +
> registre**.
> ⚠️ **Ce document est conservé tel qu'il a été validé** : ses écarts avec ce qui a été livré sont
> écrits en **avenants** à leur place (le transport de la trame `structure` **et la relecture du
> fichier**, §4 ; les bornes sensorielles, §5), jamais réécrits en silence. Usage :
> [`LANCEMENT.md` §7bis](../fonctionnement/LANCEMENT.md).

---

## 0. En une phrase

Le cerveau n'est aujourd'hui observable qu'à plat — des courbes, des barres et une heatmap 2D
(`irm_cerveau.py`, `arene_visuelle.py`) ; VIS-01 lui donne **un corps visible** : ses 12 couches
et ses 220 255 synapses disposées dans l'espace, allumées en direct par l'activité réelle du
cerveau qui vit, puis alimentées à distance par **n'importe quel run en cours**.

## 1. La question posée

> « Peut-on voir le cerveau — pas ses courbes — pendant qu'il vit, et brancher cette
> représentation sur un run en cours plutôt que sur un rejeu ? »

Deux sous-questions, deux étapes distinctes :

1. **Voir** : une structure 3D fidèle au graphe de calcul réel, animée par les activations du
   tick (étape 0 : source factice ; étape 1 : vrai cerveau en processus local).
2. **Brancher** : un cerveau qui tourne **dans un autre processus** (une campagne SCI-01, un
   run de 1500 jours) alimente la même représentation, sans être ralenti ni modifié (étape 2).

## 2. Ce que le dépôt a déjà, et ce qui manque

| | État au 10/09/2026 |
|---|---|
| Instruments de rendu | **2D uniquement** : `arene_visuelle.py` (pygame, image MiniGrid + jauges + bande mini-IRM) et `irm_cerveau.py` (matplotlib 3×1 : activations, myéline, variance du bus) |
| Bibliothèques 3D / web dans le venv | **aucune** (pas de pyvista/trimesh/plotly/open3d, aucun serveur web, aucun websocket). Présents : `torch`, `numpy`, `pygame-ce 2.5.7`, `matplotlib 3.11.1` |
| Télémétrie par tick | **mince** : `infos_internes` ne contient que `dopamine`, `faim`, `parametres_vocaux` (`noyau.py`, ~10580). Les viewers existants ne consomment **aucun flux** : ils **recalculent** `_tronc_cerebral` en `no_grad()` **dans le même processus** |
| Cuve | `daemon_cerveau.py` est déjà un serveur socket qui héberge un cerveau vivant — précédent utile, mais il n'expose que `action`/`infos_internes`/`tick_absolu` |
| Rythme des runs | `FPS_ARENE = 10`, aligné sur le `render_fps` de MiniGrid : c'est la cadence naturelle d'une visualisation temps réel |

**Le point dur est donc identifié** : « cerveau en cours de run → 3D » n'est pas un branchement,
c'est **le** travail de l'étape 2. Les étapes 0 et 1 livrent la représentation et sa fidélité ;
l'étape 2 livre le canal.

## 3. Architecture — trois morceaux, **aucune dépendance ajoutée**

```
   ┌───────────────────────┐            ┌────────────────────────────┐          ┌───────────────┐
   │ LE CERVEAU            │    UDP     │ LE SERVEUR (stdlib seul)   │   SSE    │ LE NAVIGATEUR │
   │ étape 1 : lanceur     │ ────────►  │ ThreadingHTTPServer        │ ───────► │ page three.js │
   │ étape 2 : noyau.py    │   JSON     │  · sert page + three.js    │  JSON    │ WebGL local   │
   │  (drapeau optionnel)  │  (étape 2) │  · bus de trames borné     │          │               │
   └───────────────────────┘            └────────────────────────────┘          └───────────────┘
        rapporteur                        http.server + socket (stdlib)           three.js vendorisé
     (hooks, lecture seule)                zéro paquet tiers                      (aucun CDN au runtime)
```

- **Transport** : à l'**étape 1**, le rapporteur publie **directement** dans le bus interne du
  serveur (même processus, aucun réseau) ; à l'**étape 2**, il publie par **UDP**. C'est **le même
  format de trame** dans les deux cas — seul le transport change, ce qui évite deux chemins de
  code à maintenir et à tester.

- **Le serveur** : `http.server.ThreadingHTTPServer` + `socket` — bibliothèque standard.
  **Aucune dépendance Python n'est ajoutée** : `pyproject.toml` n'est pas modifié.
- **three.js** est **vendorisé** dans le dépôt (version figée, licence MIT conservée à côté du
  fichier). Le runtime n'a besoin d'aucun accès réseau ; l'installation, elle, utilise le réseau
  une fois.
- **Le rapporteur lit, il ne recalcule pas** : `register_forward_hook` sur les 12 couches
  `NaultheneLinearSynaptique` capture la sortie du **vrai** passage avant, celui de `penser()`.
  Aucun second forward, aucun `backward`, aucune réimplémentation du rollout — c'est exactement
  la discipline **MES-02** (« les sondes observent le rollout réel, elles ne le réimplémentent
  pas »). `trace=None` ⇒ le chemin observé est strictement inchangé.

## 4. Le contrat de données — trois canaux, trois cadences

Le cœur de la conception : **séparer ce qui change rarement de ce qui change à chaque tick.**

| Canal | Cadence | Contenu | Taille mesurée |
|---|---|---|---|
| **`structure`** | à la connexion, après chaque neurogenèse | 12 couches (nom, rang, `entree`, `sortie`), **matrices de poids quantifiées int8** + échelle par couche, bornes sensorielles, métadonnées (jour, `dim_bus`, niveau + `env_id`) | **220 255 octets** (somme des 12 formes mesurées, `dim_bus = 145`) → ≈ 294 Ko en base64 |
| **`activite`** | 10–20 Hz, avec étranglement | activation de chaque neurone (**1 182 neurones** mesurés), dopamine, faim, jauges, `force_planification`, action, logits C1/C2, variance du bus | **3 152 octets** (les 1 182 neurones en `float16` base64, calculé) → ≈ 47 Ko/s à 15 Hz |
| **`evenement`** | ponctuel | choc dopaminergique (LTP), victoire, promotion de niveau, neurogenèse, fin d'épisode | ~150 o |

**Pourquoi envoyer les matrices et pas une liste d'arêtes** : la connectivité est **dense et
totale** entre deux plaques (ce sont de vraies couches linéaires) — la topologie est donc
**implicite**, seule l'intensité varie. Envoyer les poids quantifiés (≈ 294 Ko, une fois) permet
au navigateur de dessiner **toutes** les synapses et de laisser l'auteur régler un **seuil
d'affichage** côté client. Aucun échantillonnage caché côté serveur : c'est un choix visible et
réversible, pas un biais silencieux.

> ⚠️ **Limite assumée** : à `dim_bus = 145`, 220 255 synapses sont affichables ; à l'échelle
> d'un cerveau plus gros elles resteraient bornées par le seuil d'affichage. Le seuil est une
> **commodité de lecture**, jamais une mesure — et l'interface l'affiche comme telle.

### 🔴 Avenant du 10/09/2026 — le canal `structure` ne passe **pas** par UDP (mesuré)

Cet avenant **corrige ce document** : la version initiale de ce chantier prévoyait les trois trames
sur le même transport UDP (étape 2). **C'est infaisable**, et la mesure est sans appel — relevée
pendant la tâche 6, puis **reproduite indépendamment par un relecteur** :

| Fait mesuré | Valeur |
|---|---|
| Trame `structure` à `dim_bus = 145` | **305 086 octets** |
| Trame `structure` à `dim_bus = 16` (naissance) | **13 517 octets** |
| Plafond **dur** d'un datagramme UDP | **65 507 octets** — insensible même à `SO_SNDBUF = 1 Mo` |
| `SO_SNDBUF` UDP par défaut sur macOS | **9 216 octets** ⇒ `OSError [Errno 40] Message too long` dès 13 517 |
| Trame `activite` à `dim_bus = 145` | **≈ 3 600 octets** ✅ passe |
| Trame `evenement` | **≈ 90 octets** ✅ passe |

**Conséquence observée de bout en bout** : en `--serveur-seul --udp`, la structure n'arrive jamais
et la page reste sur « en attente de la structure… ».

**Le protocole de l'étape 2 devient donc :**

| Canal | Transport | Pourquoi |
|---|---|---|
| `structure` (rare : démarrage + chaque neurogenèse) | **FICHIER** déposé par le run, lu par le serveur du spectateur | 305 Ko ne tiennent pas dans un datagramme ; la morceler imposerait un réassemblage sans perte garantie pour un gain nul (elle change au plus deux fois par vie) |
| `activite` (~3,6 Ko, 15 Hz) et `evenement` (~90 o) | **UDP**, comme prévu | légers, et une perte y est bénigne par construction (« le présent, jamais du retard ») |

⚠️ **Second mur, mesuré lui aussi** : à `SO_SNDBUF` par défaut, les trames d'**activité** meurent en
silence au-delà de `dim_bus ≈ 409` (408 → 9 198 o acceptés, 409 → 9 230 o perdus) — une neurogenèse
suffit à franchir ce seuil. Contrairement au plafond dur, **ce mur-là se relève** :
`EmetteurUDP` doit poser un `SO_SNDBUF` explicite.

#### 🔴 Constat de clôture du 10/09/2026 — la moitié « lue par le serveur » n'est pas implémentée

Le tableau ci-dessus décrit la cible : « `structure` → **FICHIER** déposé par le run, **lu par le
serveur du spectateur** ». **La seconde moitié n'existe pas.** Mesuré en clôture, avec un vrai
serveur et un vrai run (`brains/VIS01_surcout_10092026/`, section 8 de son `LISEZ_MOI.md`) :

| Fait | Valeur mesurée |
|---|---|
| Run lancé avec `--telemetrie-3d` + serveur en `--serveur-seul --udp 9998` | 81 datagrammes envoyés, **0 perdu** |
| Ce que le serveur a reçu | **13 trames d'activité + 68 événements** (`/sante` : `sequence` 13, `evenements_total` 68) |
| Ce que le serveur a reçu comme `structure` | **rien** — `/structure` rend `{}`, `sequence_structure` reste **0** |
| Où va la structure | dans `<brain>.vis01_structure.json` (30 517 o ici), écrit par `noyau.py` |
| Qui relit ce fichier | **personne** : `grep -rn "vis01_structure" src/` ne rend que `noyau.py` |

**Conséquence** : en `--serveur-seul`, la page reste sur « en attente de la structure… » — l'étape 2
est **livrée en partie**. Le run, lui, est bien observé sans être modifié (preuve A/A de §10), et sa
structure est sur le disque, complète et à jour. Ce qui manque est un chemin de lecture
(`--structure <fichier>`, ou une surveillance du dossier) dans le serveur du spectateur : une tâche
à part entière, **hors des fichiers autorisés de la clôture**. Enregistré au registre (VIS-01,
« livré en partie ») et dans `LANCEMENT.md` §7bis.

#### ✅ Avenant du 10/09/2026 (tâche 11) — la moitié « lue par le serveur » est LIVRÉE

Le constat ci-dessus **n'est plus vrai** depuis la tâche 11 (`2fad056` code + tests, `433cc14`
traces) : **le serveur du spectateur relit le fichier de structure**. `--structure-fichier CHEMIN`
(exige `--serveur-seul`) construit un `VeilleurStructureFichier` : un fil **dédié** (démon, 1 Hz,
aucun accès disque sur la voie chaude) qui relit le fichier **au démarrage** — premier tour
**synchrone**, pour que la toute première connexion du navigateur voie une structure déjà présente —
puis **à chaque changement**, sur **signature** (`mtime_ns` + taille : l'émetteur écrit de façon
atomique par `os.replace`, donc la signature change à chaque publication). Une trame refusée
n'écrase **rien** (la dernière structure valide reste publiée), et l'incident est **compté**
(`publications` / `absences` / `illisibles` / `invalides` + `derniere_erreur`), visible dans la
bannière, dans `/sante` (bloc `structure_fichier`) et dans le bilan d'arrêt `📡 structure : …`.

**La commande qui le prouve** — protocole exact de
`brains/VIS01_etape2_fichier_10092026/` (serveur lancé **avant** le run, donc fichier **absent** au
démarrage ; nouvelles valeurs de port pour ne pas gêner un serveur déjà ouvert) :

```bash
# terminal 1 — le serveur (fichier absent au démarrage : c'est le cas normal)
PYTHONPATH=src venv/bin/python3 -m naulthene.instruments.cerveau_3d --serveur-seul --udp 9998 \
    --port 8771 --structure-fichier \
    brains/VIS01_etape2_fichier_10092026/etape2.brain.vis01_structure.json

# terminal 2 — le run observé (ici un cerveau NEUF, né à dim_bus = 16)
PYTHONPATH=src venv/bin/python3 -m naulthene.cerveau.noyau --graine 11 --jours 60 --no-wandb \
    --brain brains/VIS01_etape2_fichier_10092026/etape2.brain --telemetrie-3d udp:127.0.0.1:9998

# le témoin, PENDANT le run (le port est celui de la bannière)
curl -s http://127.0.0.1:8771/structure | python3 -c "import json,sys; d=json.load(sys.stdin); \
    print(len(d['couches']), 'couches, dim_bus', d['dim_bus'])"
# → 12 couches, dim_bus 68
```

| Fait mesuré (10/09/2026, 19:28 → 19:30) | Valeur |
|---|---|
| `/structure` avant que le run écrive le fichier | **`{}`**, `sequence_structure` **0**, `absences 12` |
| `/structure` 4 s après le lancement du run (19:28:57) | **12 couches, `dim_bus` 16**, `sequence_structure` **1** |
| `/structure` en fin de run (60 jours en 75 s) | **`dim_bus` 68**, `sequence_structure` **6**, `illisibles 0`, `invalides 0` |
| Flux SSE (client connecté pendant le run) | **4 trames `structure`** (`dim_bus` 16, 32, 48, 51) + **252 `activite`** + **1 404 `evenement`**, la structure **en tête de flux** |
| Trame finale | **88 488 o** — toujours au-dessus du plafond dur de **65 507 o** d'un datagramme : le fichier reste la **seule** voie |
| Ce qui reste vrai | le run a écrit **11** structures, le serveur en a publié **6** : la veille publie le **dernier** état (deux neurogenèses dans la même seconde ⇒ une seule publication) |

🔴 **RÉTRACTATION DU 10/09/2026 (tâche 11 ; ancien énoncé en regard, dogme « rien sans écrit ») —
CE QUE DISAIT CE DOCUMENT :**

| Énoncé publié dans ce document | ❌ FAUX — re-mesuré le 10/09/2026 | Corrigé en |
|---|---|---|
| « Qui relit ce fichier \| **personne** : `grep -rn "vis01_structure" src/` ne rend que `noyau.py` » | Le `grep` rend **trois** fichiers : `noyau.py` (l'émetteur), `cerveau_3d/serveur.py` (`VeilleurStructureFichier`), `cerveau_3d/__main__.py` (`--structure-fichier`) | « le serveur du spectateur le relit, au démarrage et à chaque changement » |
| « en `--serveur-seul`, la page reste sur « en attente de la structure… » — l'étape 2 est **livrée en partie** » | La page n'attend plus **dès que `--structure-fichier` est donné** : 6 publications mesurées pendant un run de 75 s, sans redémarrer le serveur. L'étape 2 est **complète** | « l'étape 2 est livrée, structure comprise » |
| « Ce qui manque est un chemin de lecture (`--structure <fichier>`, ou une surveillance du dossier) … une tâche à part entière, **hors des fichiers autorisés de la clôture** » | Le chemin de lecture a été livré (tâche 11) : le « manque » était une limite de **périmètre** (liste de fichiers close), pas une impossibilité technique | « `--structure-fichier` (tâche 11), livré » |

⚠️ **La veille n'est PAS un historique** : elle publie le **dernier** état connu, sur signature —
11 structures écrites par le run, 6 publiées. C'est la limite principale du mécanisme (avec une
latence possible d'une seconde, la cadence de veille, et une signature réduite à `mtime_ns` +
taille) ; les cinq limites sont consignées dans le `LISEZ_MOI.md` de la campagne (§4, écrites
d'avance) et dans le rapport de la tâche 11 (§6).

### Formes exactes (indicatives, à figer à l'implémentation)

```jsonc
// structure
{ "type": "structure", "jour": 412, "dim_bus": 145,
  "niveau": {"index": 3, "affiche": "4/15", "env_id": "MiniGrid-SimpleCrossingS9N1-v0"},
  "couches": [ {"nom": "porte_visuelle", "rang": 0, "entree": 147, "sortie": 145,
                "echelle": 0.021, "poids_i8": "<base64 145×147>",
                "positions": "<base64 float16 145×3>"} ],
  "bornes":  [ {"nom": "vision", "dim": 147, "couche": "porte_visuelle", "rang_entree": [0, 147]} ],
  "compte":  {"parametres_appris": 7792, "buffers_base_weight": 39048} }

// activite
{ "type": "activite", "tick": 12345, "jour": 412,
  "neurones": {"porte_visuelle": "<base64 float16 ×145>"},
  "scalaires": {"dopamine": 0.31, "faim": 0.42, "force_planification": 0.18, "action": 3} }

// evenement
{ "type": "evenement", "genre": "choc_dopamine", "tick": 12345, "intensite": 1.0 }
```

## 5. La disposition spatiale — et ce qu'elle affirme exactement

⚠️ **La disposition est une CONVENTION DE LECTURE, pas une affirmation anatomique.** Naulthène
n'a ni cortex ni lobe : elle a un graphe de calcul. L'ordre des rangs ci-dessous est celui du
flux de données, déclaré ici une fois pour toutes, et **le même pour tous les cerveaux** — c'est
ce qui rend deux cerveaux comparables.

| Rang | Plaque | `sortie` (au bus 145) | Rôle |
|---|---|---|---|
| 0 | `porte_auditive` · `porte_visuelle` | 145 · 145 | les portes sensorielles entrent dans le bus |
| — | **colonne du bus latent** | 145 | le tronc commun, au centre ; jamais une « couche » |
| 1 | `hippocampe` | 145 | mémoire de travail (bus + mémoire précédente) |
| 2 | `analyseur` | 145 | la pensée |
| — | `fusion_memoire` | 145 | **boucle latérale** (2 itérations) vers la mémoire épisodique |
| 3 | `integrateur_bio` | 145 | **le corps entre dans la décision** (bus + 44 dims bio) |
| 4 | `tete_motrice` | 8 | l'action (C1) |
| 4 | `cortex_prefrontal` | 1 | la valeur (C2) |
| 4 | `tete_vocale` | 8 | la voix |
| 4 | `tete_requete` | 5 | le routage Exo-Sens (C3) |
| 5 | `generateur_attente` · `generateur_attente_audio` | 145 · 145 | les têtes JEPA : elles **prédisent le bus** |

**Bornes sensorielles** (non neuronales, dessinées distinctement) : vision 147, audio 130,
`vecteur_bio` 44, actions 8 — elles expliquent les `entree` non multiples du bus
(189 = 145 + 44, 153 = 145 + 8).

### Avenant du 10/09/2026 (clôture) — les bornes sont **COMPTÉES**, pas **DESSINÉES**

Le mot « dessinées » ci-dessus est **faux au regard de ce qui a été livré** : aucun glyphe, aucune
forme, aucune couleur n'est produite pour une borne. La page **compte** les entrées non neuronales
qu'elle écarte et l'**affiche en clair** dans sa ligne d'information
(`app.js`, `construireAretes()` → `horsBornes`, rendu `· N entrées non neuronales (bornes)`), et
elle ne relie par aucune arête une entrée de borne à un neurone — une borne n'est pas un neurone,
et lui dessiner un nœud inventerait une anatomie qui n'existe pas (§5, premier avertissement).

**Pourquoi l'écart est assumé plutôt que corrigé** : dessiner les bornes n'ajouterait aucune
information mesurable (leur `dim` est déjà dans la trame `structure`, sous `bornes[]`, et
`planDesEntrees` s'en sert pour savoir quelles entrées viennent d'un neurone du bus) ; le **compte**
suffit à expliquer au lecteur pourquoi un `entree` n'est pas un multiple du bus (189 = 145 + 44,
153 = 145 + 8). Ce qui est affiché est donc exact : les bornes sont **déclarées** dans la trame,
**exclues** des arêtes, et **comptées** à l'écran — jamais muettes, jamais simulées en neurones.

⚠️ Aucun test ne fige ce point : `tests/test_cerveau_3d.py` vérifie que les `bornes` sont dans la
trame et que les arêtes relient deux neurones distincts, pas le libellé de la ligne d'information.

### Encodage visuel — chaque canal a un sens mesuré

| Donnée | Encodage |
|---|---|
| Activation post-ReLU d'un neurone | intensité émissive (échelle auto-calibrée sur la trame) |
| Poids d'une synapse | épaisseur + opacité, sous seuil réglable |
| Myéline (`myeline_M`) | gaine claire le long de l'arête |
| Cristallisation (`cristallisee`) | arête blanche figée |
| **Neurone mort** (activation nulle en permanence) | gris sourd — le fait mesuré « **56 % de `pensee_bio`** » devient **visible** |
| Dopamine | halo global |
| **Choc dopaminergique (LTP)** | flash, puis gravure : les arêtes concernées s'épaississent — c'est le moment où le cerveau **écrit** |
| `force_planification` | bascule visible entre les deux voix C1/C2 sur la plaque motrice |

⚠️ **Le hook capture la sortie LINÉAIRE de la couche** (`NaultheneLinearSynaptique.forward`) ; le
ReLU est appliqué **après**, par l'appelant (`_tronc_cerebral`, `penser`). Le rapporteur reproduit
donc le ReLU **là où le cerveau l'applique**, et nulle part ailleurs — un miroir, pas une
convention : là où le cerveau n'applique pas de ReLU (les têtes), la valeur affichée est la valeur
linéaire.

## 6. Les trois étapes livrables

| Étape | Contenu | Critère d'acceptation | Touche `noyau.py` ? |
|---|---|---|---|
| **0 · Démonstration** | page + 12 plaques + **source factice** (activité synthétique déterministe) | l'auteur voit la structure et le mouvement, juge la forme, sans aucun cerveau chargé | non |
| **1 · Spectateur-pilote** | le lanceur fait vivre un **vrai** `.brain` (pattern `lancer_arene.py`), IRM 3D complète | le cerveau affiché est celui qui joue ; **aucun fichier écrit** ; surcoût mesuré et reporté | non |
| **2 · Passerelle** | drapeau `--telemetrie-3d udp:127.0.0.1:9998` + serveur en mode `--serveur-seul` | **run bit-identique sans le drapeau** ; un run de campagne observé en direct depuis un second terminal | **oui** → CHANGELOG + bump + test de non-régression |

**Le mode factice de l'étape 0 n'est pas jetable** : il devient la **fixture** des tests du rendu,
qui tournent alors sans `torch` ni MiniGrid (les 44 tests CPU existants restent inchangés).

### Commandes prévues

```bash
# étape 0 — démonstration, source factice
PYTHONPATH=src venv/bin/python3 -m naulthene.instruments.cerveau_3d --source factice --port 8770

# étape 1 — spectateur-pilote, cerveau réel, lecture seule
PYTHONPATH=src venv/bin/python3 -m naulthene.instruments.cerveau_3d \
    --brain brains/08092026_sci01_balayage_K/K4_NU/K4_NU_g11.brain --port 8770 --hz 15

# étape 2 — serveur seul, puis un run observé depuis un autre terminal
# ⚠️ `--structure-fichier` est REQUIS à l'étape 2 (avenant de la tâche 11, §4) : sans lui la page
# reste sur « en attente de la structure… », la trame `structure` ne passant pas par UDP.
PYTHONPATH=src venv/bin/python3 -m naulthene.instruments.cerveau_3d --serveur-seul --udp 9998 \
    --port 8770 --structure-fichier "brains/<campagne>/run.brain.vis01_structure.json"
PYTHONPATH=src venv/bin/python3 -m naulthene.cerveau.noyau --graine 11 --jours 200 \
    --brain "brains/<campagne>/run.brain" --telemetrie-3d udp:127.0.0.1:9998
```

## 7. Fichiers prévus

| Fichier | Rôle |
|---|---|
| `src/naulthene/cerveau/telemetrie.py` | **feuille SANS `torch`** (numpy seul, déjà une dépendance cœur) : format des trois trames, quantification int8, bus borné, émetteur UDP non bloquant. Ne connaît ni `torch` ni `noyau` — c'est ce qui permet à `noyau.py` de l'importer **sans cycle** (même motif que `bus_sensoriel.py`) |
| `src/naulthene/instruments/cerveau_3d/__main__.py` | point d'entrée CLI |
| `src/naulthene/instruments/cerveau_3d/rapporteur.py` | hooks de lecture seule → trames (seul fichier qui connaît `torch`/`noyau`) |
| `src/naulthene/instruments/cerveau_3d/serveur.py` | HTTP + SSE + bus borné + réception UDP |
| `src/naulthene/instruments/cerveau_3d/static/` | `index.html`, `app.js`, `three.module.js` (vendorisé), licence three.js |
| `tests/test_cerveau_3d.py` | deux familles : **sans `torch`** (trames, quantification, disposition, SSE, UDP — via la fixture factice) et **un test avec un cerveau minuscule** (`dim_bus = 16`) pour la neutralité des hooks |
| `docs/fonctionnement/LANCEMENT.md` | section « Le cerveau 3D » (l'instrument doit être lançable sans lire le code) |

**Justification du domicile de `telemetrie.py`** : CLAUDE.md §1 (ARC-01) réserve `noyau.py` à la
mécanique cognitive. Un émetteur de télémétrie n'est **pas** une mécanique — et le placer dans
`instruments/` créerait un cycle (`instruments` importe `noyau`). Le pattern existant est
`cerveau/bus_sensoriel.py` : un module feuille du même paquet, qui n'importe jamais `noyau`.

## 8. Garanties — et ce qu'elles valent exactement

| Garantie | Portée réelle |
|---|---|
| **Aucun pas d'optimiseur** | `apprendre_journee`, `rever`, `executer_nuit`, `cycle_sommeil` ne sont **jamais** appelés par les étapes 0/1 |
| **Aucun fichier écrit** | `persistance.sauvegarder` n'est jamais appelé : **le `.brain` observé reste identique sur le disque** (vérifiable par empreinte) |
| **Aucun `backward()`** | vrai, mais **insuffisant** à lui seul — voir la découverte D1 ci-dessous |
| **Comportement inchangé dans le cerveau observé** | `register_forward_hook` n'altère pas la valeur de sortie ; le rapporteur ne fait que lire. Toute écriture qu'il ferait serait un bug, pas un effet de bord attendu |
| **Un run n'est jamais ralenti** | réseau **UDP** et **file bornée** : si le serveur est absent, lent ou saturé, la trame est **perdue**, jamais le tick retardé. Aucun `send` bloquant, aucune attente — ⚠️ **vrai au sens du RÉSEAU, faux au sens du CALCUL** : l'instrument lui-même coûte, et c'est désormais chiffré (avenant ci-dessous) |
| **Pas de fuite hors de la machine** | le serveur écoute sur `127.0.0.1` |

### Avenant de clôture du 10/09/2026 — « jamais ralenti » : le réseau, oui ; le calcul, non (mesuré)

La ligne ci-dessus a été écrite comme une garantie sur le **réseau**, et elle tient : un
consommateur absent, lent ou saturé ne retarde jamais un tick (UDP non bloquant, file bornée) —
mesuré, **0 datagramme perdu sur 3 762**.

Mais elle se lit facilement comme « la télémétrie est gratuite », **et c'est faux**. La preuve
« surcoût du rapporteur — chiffré, jamais estimé » de §10 a été faite en clôture
([`brains/VIS01_surcout_10092026/LISEZ_MOI.md`](../../brains/VIS01_surcout_10092026/LISEZ_MOI.md)) :

| Mesure (même cerveau copié, même graine 11, 3 paires de 50 jours = 20 000 ticks) | SANS le drapeau | AVEC le drapeau |
|---|---:|---:|
| Temps mural médian | **58,05 s** | **62,14 s** |
| **ticks/s** (démarrage soustrait) | **364,0** | **337,4** |
| Écart | — | **+7,87 % de temps · −7,30 % de débit** (de +7,05 % à +7,87 % selon la convention de soustraction du démarrage ; dispersion intra-bras 0,47–1,55 %) |

Ce chiffre est un **minorant** : il est mesuré à `bus = 32 → 71`, et c'est l'encodage des trames qui
grossit avec le bus (le `dim_bus = 145` de cette spec n'a pas été mesuré). C'est la raison d'être du
mode `--serveur-seul` par défaut et du drapeau **éteint par défaut** : observer coûte ~7,5 %, donc
on observe quand on veut regarder.

### D1 — la garantie « ne modifie aucun poids » des instruments existants est inexacte (mesuré)

Les docstrings d'`irm_cerveau.py` (l. 35-38) et de `lancer_arene.py` (l. 39-42) affirment que
`traiter_tick` « ne modifie aucun poids hors d'un `backward()` explicite ». **C'est faux dans sa
mécanique** :

- `traiter_tick` appelle `fortifier_synapses` sur tout événement marquant
  (`noyau.py` ~10430-10434) ;
- `fortifier_synapses` (~2284-2298) appelle `fortification_dopaminergique` sur **les 12 couches** ;
- celle-ci écrit **en place**, sous `no_grad`, dans `base_weight` **et** `myeline_M` (~176-189) —
  **sans aucun `backward()`**.

**Mesuré sur `brains/08092026_sci01_balayage_K/K4_NU/K4_NU_g11.brain`** (lecture seule) :
`|trace_activation|max = 0,000e+00` sur **les 12 couches**. Or `ancrage = trace_activation × pic` :
la trace étant nulle, **l'écriture est numériquement nulle**. Ce n'est pas un hasard —
`cycle_sommeil` remet la trace à zéro (`noyau.py` ~364), donc **tout `.brain` sauvegardé après
une nuit porte une trace nulle**.

**Conséquences, exactement :**

1. Pour un `.brain` sauvegardé après une nuit : la garantie **pratique** tient (écriture nulle),
   et la garantie **mécanique** est mal formulée.
2. Pour un `.brain` sauvegardé **en pleine journée** — cas réel : la **micro-sieste** de la Cuve
   (`daemon_cerveau.py`, `_processus_nocturne`, qui appelle `sauvegarder` **sans** nuit) — la
   trace est **non nulle**, et le premier pic dopaminergique d'une session d'observation écrirait
   alors de **vraies** valeurs dans `base_weight`/`myeline_M`.
3. Dans les deux cas, **le fichier `.brain` n'est jamais modifié** (aucune sauvegarde) : c'est la
   garantie qui compte pour l'utilisateur, et elle est intacte.

→ Proposition : une ligne de correction dans les deux docstrings, et une entrée de registre.
**Hors périmètre de VIS-01** — décision de l'auteur.

### D2 — écart entre l'en-tête de version de `noyau.py` et le CHANGELOG (à trancher)

`noyau.py` déclare `#Version actuelle 41.68`. Le CHANGELOG porte des entrées **v41.71 → v41.75**
et `ETAT_COURANT.md` parle de **v41.72** (ARC-01). Deux lectures possibles :

- soit CLAUDE.md §1 s'applique (« docs/refactor → même version ») et l'en-tête est **correct**,
  mais alors les entrées v41.69 → v41.75 ne devraient pas porter de numéro ;
- soit le CHANGELOG fait foi et l'en-tête est **en retard de 7 versions**.

⚠️ Second point, non ambigu : dans `CHANGELOG.md`, **l'entrée la plus récente n'est pas en tête**
— `[v41.71]` est en ligne 7 et `[v41.75]` en ligne 46, alors que CLAUDE.md §13 exige la plus
récente en haut. C'est exactement le piège que CLAUDE.md signale (« l'en-tête est resté périmé de
20 versions une fois — ne pas reproduire »).

→ **Hors périmètre de VIS-01**, mais l'étape 2 ajoutera une entrée de CHANGELOG : autant que le
numéro soit juste au moment où on l'écrit. Décision de l'auteur requise **avant** l'étape 2.

## 9. Robustesse

| Situation | Comportement attendu |
|---|---|
| Serveur absent / port occupé | le run **continue normalement** (UDP silencieux) ; le serveur le dit et se ferme proprement |
| Navigateur fermé / rouvert | rien ne casse côté cerveau ; le client récupère `structure` à la reconnexion |
| Datagramme tronqué ou non-JSON | **ignoré**, compteur d'incréments, jamais d'exception propagée |
| `dim_bus` change (neurogenèse) | nouvelle trame `structure` ; le client reconstruit la scène |
| Serveur plus lent que le cerveau | la file bornée **écrase la plus ancienne** trame : on voit le présent, jamais du retard accumulé |
| Cerveau dans un état inattendu (NaN) | affiché comme tel (gris), **jamais** corrigé |

## 10. Tests et preuves exigées

**Tests** (`tests/test_cerveau_3d.py`) — les points 1 à 5 tournent **sans `torch`** (fixture
factice) ; le point 6 instancie un cerveau minuscule (`dim_bus = 16`). Tous sont lancés par la
**commande unique existante** :

1. la quantification int8 → flottant respecte la borne d'erreur annoncée ;
2. la disposition est **déterministe** (mêmes entrées ⇒ mêmes positions, à l'octet) ;
3. le serveur émet des trames SSE bien formées (`event:`/`data:`), et un client factice les lit ;
4. un datagramme malformé **n'interrompt pas** la réception ;
5. la file bornée conserve bien la **dernière** trame et non la première ;
6. le rapporteur, `hooks` actifs **et** inactifs, produit des sorties de couche **identiques**
   (témoin que l'observation n'observe pas en modifiant).

**Preuves** (dogme « rien sans témoin ») — état au **10/09/2026**, à la clôture du chantier :

| Preuve | Protocole | État |
|---|---|---|
| **Le fichier `.brain` n'est pas touché** | empreinte SHA-256 avant/après une session de spectateur-pilote | ✅ faite (tâche 8, `[v41.76]`) |
| **Le cerveau observé ne dérive pas** | normes de `base_weight` et `myeline_M` avant/après, à l'étape 1 | ✅ faite (tâche 8, `[v41.76]`) |
| **Surcoût du rapporteur — chiffré, jamais estimé** | ticks/s avec et sans hooks, même graine, même cerveau | ✅ **faite le 10/09** : **364,0 → 337,4 ticks/s**, soit **+7,87 % de temps / −7,30 % de débit** (3 paires de 20 000 ticks ; `brains/VIS01_surcout_10092026/LISEZ_MOI.md`) — **minorant**, mesuré à `bus = 32 → 71` |
| **Étape 2 : run bit-identique sans drapeau** | deux runs même graine (5 jours) avec et sans télémétrie active, `diff` des niveaux promus — **le test qui compte** | ✅ **faite (tâche 9)** : `diff` vide ; **re-mesurée par la clôture sur 3 paires de 50 jours** (`diff` vide, `dim_bus` final identique des deux côtés) — `brains/VIS01_preuve/LISEZ_MOI.md` |
| **Le canal tient la cadence** | nombre de trames émises/affichées/perdues sur une session, reporté tel quel | ✅ **faite le 10/09 (tâche 11)** : **4 463 datagrammes envoyés / 0 perdu**, et **4 `structure` + 252 `activite` + 1 404 `evenement`** reçus par un vrai serveur **sur le même flux SSE**, la structure **en tête de flux** (`brains/VIS01_etape2_fichier_10092026/LISEZ_MOI.md` §5). ⚠️ Cette ligne disait « 🟡 **faite côté ÉMISSION, partielle côté AFFICHAGE** … le nombre de trames **affichées** dépend du lien manquant `structure` (avenant §4) » : le lien est livré. Reste non prouvé : le **rendu** three.js lui-même (aucun navigateur ouvert) |

## 11. Ce qui est explicitement écarté (YAGNI)

- ❌ **WebSocket** : le flux est unidirectionnel (cerveau → navigateur), SSE suffit et évite une
  dépendance.
- ❌ **Comparaison de plusieurs cerveaux côte à côte** : c'est un 3ᵉ étage, il suppose qu'un seul
  s'affiche bien.
- ❌ **Vue « temps long » (myéline, érosion, 1500 jours)** : exige d'échantillonner à chaque nuit,
  pas à chaque tick — chantier distinct, et incompatible avec le choix « lecture seule ».
- ❌ **Mode `--vivre` (vraies nuits dans le spectateur)** : écarté par la décision de cadrage ; le
  spectateur ne dort jamais.
- ❌ **VR, replay vidéo, export d'images** : aucune demande, aucun besoin mesuré.
- ❌ **MiniGrid dans la 3D** : l'Arène le montre déjà en 2D, et le sujet est le cerveau.
- ❌ **Forcer la caméra / les couleurs par défaut « jolies »** : la lisibilité prime.

## 12. Risques

| Risque | Parade |
|---|---|
| Le rendu devient un joli mensonge (couleurs arbitraires, échelles choisies) | chaque encodage est **déclaré** (§5) et adossé à une grandeur mesurée du cerveau |
| Le surcoût du rapporteur fausse un run observé | mode `--serveur-seul` par défaut à l'étape 2 ; surcoût **mesuré** et publié ; drapeau éteint par défaut |
| `noyau.py` touché à l'étape 2 → risque de régression sur un dépôt à 44 contrats | un seul ajout, éteint par défaut, + le test bit-identique de §10 |
| Le vendor de three.js alourdit le dépôt (≈ 331 Ko minifié, mesuré) | version figée, licence conservée, chargée depuis le serveur local — aucun impact sur les runs |
| Le navigateur ne suit pas 220 000 arêtes | seuil d'affichage par défaut ; géométrie statique construite une fois, seule la couleur change par trame |

## 13. Références

- Instruments existants : `src/naulthene/instruments/irm_cerveau.py` ·
  `src/naulthene/instruments/arene_visuelle.py` · `src/naulthene/instruments/lancer_arene.py`
- Cuve (précédent de serveur hébergeant un cerveau vivant) : `src/naulthene/cuve/daemon_cerveau.py`
- Discipline des sondes : CLAUDE.md §8 (`MES-02`), `tests/test_contrats_cognitifs.py`
- Drapeau et instrumentation : CLAUDE.md §9 (« Instrumentation obligatoire », v29.1)
- Versionnage et CHANGELOG : CLAUDE.md §1, §13
- Mesures citées (relevées le 10/09/2026 sur
  `brains/08092026_sci01_balayage_K/K4_NU/K4_NU_g11.brain`, **lecture seule**, par
  `torch.load` du seul `state_dict`) : `dim_bus = 145` · 12 couches et leurs formes exactes ·
  `|trace_activation|max = 0,000e+00` sur les 12 couches. **Dérivés** de ces formes (arithmétique,
  pas mesure) : 1 182 neurones de sortie, 220 255 synapses, 3 152 octets de trame d'activité.
  Taille de three.js minifié : `three.module.min.js` v0.180.0, **338 908 octets**.
- ✅ ~~⚠️ **Aucune mesure de performance n'a été faite** : le surcoût du rapporteur (§10) est à
  mesurer, pas à supposer.~~ **FAIT le 10/09/2026** : **364,0 → 337,4 ticks/s** (SANS vs AVEC le
  drapeau), soit **+7,87 % de temps de run / −7,30 % de débit**, sur 3 paires entrelacées de
  50 jours (20 000 ticks) partant du **même cerveau copié** à la **même graine** — dispersion
  intra-bras 0,47–1,55 %, donc l'effet est 5 à 15 fois plus grand que le bruit. **Minorant** :
  mesuré à `bus = 32 → 71`, pas au `dim_bus = 145` de ce document (c'est l'encodage des trames qui
  grossit avec le bus). Détail, chiffres bruts et limites :
  [`brains/VIS01_surcout_10092026/LISEZ_MOI.md`](../../brains/VIS01_surcout_10092026/LISEZ_MOI.md) ·
  entrée de journal : [`JOURNAL_DES_RUNS.md`](../fonctionnement/JOURNAL_DES_RUNS.md).
