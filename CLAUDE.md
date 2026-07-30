# CLAUDE.md

Instructions de travail pour Claude Code sur le projet **Naulthène AGI** — agent cognitif autonome hybride (RL + JEPA + mémoire épisodique + homéostasie neuro-mimétique), entraîné sur un cursus scolaire d'environnements MiniGrid à complexité croissante.

## Projet Overview

Naulthène AGI est un projet de recherche (packagé en `src/naulthene/`, cœur de référence pensé pour tourner sur Google Colab) qui explore une architecture cognitive bio-inspirée plutôt qu'un pipeline RL classique. L'agent (`AGI_Naulthene`, `nn.Module`) combine :

- Un **modèle du monde JEPA** (Joint Embedding Predictive Architecture) qui prédit l'état latent suivant plutôt que l'observation brute (`generateur_attente`, `perte_jepa`)
- Un **Système 1** instinctif (tête motrice Acteur-Critique classique) et un **Système 2** délibératif qui simule mentalement les conséquences de ses actions sur un horizon de plusieurs pas (`simuler_futur_et_planifier`) avant de arbitrer entre les deux
- Une **mémoire épisodique** de contexte (moyenne glissante des états latents récents de l'épisode, `vecteurs_episodiques`) et une mémoire tampon court terme (`hippocampe`)
- Un **réservoir dopaminergique homéostatique** ($D_t \in [0.001, 10.0]$) qui module la motivation et la plasticité synaptique en fonction des succès/échecs vécus dans la journée
- Une **plasticité structurelle** (`NaultheneLinearSynaptique`) : chaque couche a un poids de base figé et un poids "annexe" appris pendant la journée, consolidé (ou érodé) chaque nuit selon une trace de myéline — avec neurogenèse (ajout de dimensions) déclenchée par un thermostat d'erreur JEPA
- Une **consolidation nocturne (rêve)** à porosité adaptative : le pourcentage de souvenirs rejoués la nuit dépend de la plasticité du moment et de la richesse (importance moyenne) de la journée, pas d'une taille de batch fixe
- Des **détecteurs de progrès génériques**, agnostiques de la carte (franchissement de portes, records de proximité à l'objectif), en plus du détecteur de jalons spécifique à `DoorKey` (cursus à 7 paliers)

L'agent progresse à travers un **cursus académique** de 5 niveaux MiniGrid, du Primaire (navigation basique) au Doctorat (planification longue distance), promu après 2 victoires consécutives sur le niveau courant.

Ce n'est pas une application produit : c'est un script de recherche exécuté en continu (boucle de jours/ticks), instrumenté avec **Weights & Biases** pour le suivi expérimental. Pas de tests automatisés, pas de build — la validation passe par l'observation des courbes W&B et des logs console.

## Architecture

Le projet est organisé en **package Python** sous `src/naulthene/`, avec un dossier par grande fonction cognitive — le vocabulaire des dossiers suit celui du projet (le cerveau, les salles de classe, la Cuve) :

```
21. AGI/                          racine du dépôt (CWD de lancement de tous les scripts)
├── LICENSE, NOTICE               licence Apache 2.0 et attribution — voir readme.md
├── readme.md                     documentation narrative de référence (table des matières,
│                                   historique des versions, description scientifique du modèle)
├── CLAUDE.md                     ce fichier
├── .gitignore
│
├── src/naulthene/                LE PACKAGE
│   ├── cerveau/                  ← LE CERVEAU (cœur cognitif)
│   │   ├── noyau.py              terrain d'essai local (ex-agi_local_test.py, gitignoré)
│   │   ├── colab.py              script de référence versionné (ex-agi_google_colab.py)
│   │   └── persistance.py        cristallisation/résurrection de l'état cognitif (.brain)
│   ├── salles_de_classe/         ← LES SALLES DE CLASSE (cursus d'entraînement)
│   │   ├── cursus_bebe.py        paradigme développemental "Bébé" (0→4 ans)
│   │   └── cursus_developpemental.py   Cursus par Ères (1000 jours)
│   ├── cuve/                     ← LA CUVE (client-serveur, cerveau persistant)
│   │   ├── daemon_cerveau.py     le serveur (héberge le cerveau en cryostase)
│   │   ├── client_corps.py       client MiniGrid jetable
│   │   └── client_professeur.py  client leçons de parole jetable
│   ├── audio/                    ← L'HÉMISPHÈRE AUDIO / VOCAL
│   │   ├── hemisphere_audio.py   formants, MFCC, synthèse, micro, Whisper
│   │   ├── lecons_vocales.py     cache de références vocales (TTS macOS)
│   │   └── professeur_gemma.py   le "Professeur", appelle Gemma via Ollama
│   ├── exocortex/                ← LE PORT EXOCORTEX C3 (greffon optionnel, v28.0)
│   │   ├── port_c3.py             bus multiplexeur (PortC3) et contrat neutre
│   │   │                          (RequeteC3/ReponseC3/PlugC3)
│   │   └── plugs/                 greffons interchangeables (PlugNul, PlugSimule,
│   │                               PlugHTTP) qui s'enregistrent sur le port
│   └── instruments/               ← INSTRUMENTS D'OBSERVATION (lecture seule)
│       ├── arene_visuelle.py     fenêtre pygame de visualisation en direct
│       ├── lancer_arene.py       lance l'Arène (pygame + audio)
│       └── irm_cerveau.py        scanner d'activations internes, ne modifie jamais le .brain
│
├── brains/                       cerveaux cristallisés (*.brain, gitignorés)
└── docs/                         documentation complémentaire (CHANGELOG.md, explications_readme.md,
                                    LANCEMENT.md, Parcourt_readme.md — guide pratique vulgarisé du
                                    système de cursus, commandes de lancement, jours/ticks par parcours,
                                    détail des paliers, FAQ — CONCEPTION_v22_audio.md, et les analyses de run)
```

Le cœur de référence est `src/naulthene/cerveau/colab.py` (ex-`agi_google_colab.py`, pensé pour tourner sur Google Colab). Structure interne (sections numérotées par des commentaires `# --- N. ... ---`) :

1. **Le Scalpel — Plasticité Structurelle** (`NaultheneLinearSynaptique`) : couche linéaire à poids base/annexe, cycle de sommeil (érosion + consolidation), et `agrandir()` pour la neurogenèse (extension des dimensions in/out sans perdre les poids appris)
2. **Le Cerveau Système 1 & 2** (`AGI_Naulthene`) : tronc cérébral commun (`porte_visuelle` → `hippocampe` → `analyseur`), lecture épisodique, tête motrice (Système 1), rollout mental (`simuler_futur_et_planifier`, Système 2), apprentissage journalier (`apprendre_journee`, Acteur-Critique + JEPA), rêve (`rever`), cycle de sommeil global, neurogenèse (`declencher_neurogenese`)
3. **Cursus & Détecteurs** :
   - 3a. `DetecteurJalonsDoorKey` — spécifique à l'environnement `DoorKey`, 7 paliers cognitifs codés en dur sur cette carte
   - 3b. Détecteurs génériques actifs sur n'importe quel niveau : `DetecteurFranchissementPortes`, `DetecteurProgresPersonnel`
4. **Exécution & Cursus** : configuration W&B, hyperparamètres (dopamine, planification, rêve adaptatif), programme des 5 niveaux (`PROGRAMME`), boucle principale jour/tick

Voir le [README](readme.md) pour la description narrative complète (formules d'homéostasie, tableau des 7 paliers, architecture cognitico-biologique en diagramme ASCII).

Tous les imports entre modules du package sont des **chemins absolus de package** (`from naulthene.cerveau.noyau import ...`, `import naulthene.audio.professeur_gemma as pg`) — jamais d'imports relatifs à plat. Tout script se lance depuis la **racine du dépôt** avec `PYTHONPATH=src` et l'option `-m` (voir [Essential Commands](#essential-commands)) ; les chemins `.brain` par défaut sont relatifs à cette racine (`brains/naulthene_*.brain`).

## Variante Locale de Test (Mac) — `src/naulthene/cerveau/noyau.py`

En plus du script de référence `colab.py`, le projet dispose d'une copie de travail **non trackée par git** (`src/naulthene/cerveau/noyau.py`, ex-`agi_local_test.py`, listée dans `.gitignore`) utilisée pour tester rapidement de nouvelles mécaniques sur Mac (Apple Silicon, device `mps`) avant de les porter — ou non — sur le script de référence.

- **Deux différences permanentes avec `colab.py`** : détection du device `cuda`/`mps`/`cpu` (au lieu de `cuda`/`cpu` seul) et un `jours_totaux` ajustable localement pour des runs de test plus courts que les 400 jours de Colab
- **C'est le terrain d'essai des mécaniques expérimentales** (actuellement v18.0 Architecture Homéostatique Biologique, v19.0 Métabolisme 20/80 & Forage 80/20, et toute mécanique suivante tant qu'elle n'a pas été validée sur un run long) — ces versions vivent **uniquement** dans ce fichier tant qu'elles ne sont pas explicitement portées sur `colab.py`
- Le fichier n'étant pas versionné, toute modification doit être documentée dans `readme.md`/`docs/CHANGELOG.md` avec la mention explicite **"expérimental"** et l'avertissement qu'elle ne vit que dans `noyau.py` — ne jamais laisser croire qu'une mécanique expérimentale est déjà dans le script de référence
- Avant de porter une mécanique validée vers `colab.py`, vérifier qu'elle est cohérente avec toute l'évolution parallèle qu'a pu subir le script de référence entre-temps (les deux fichiers peuvent diverger sur plusieurs versions)
- Setup local : voir [Démarrage Rapide](readme.md#démarrage-rapide) dans le README (venv Python 3.12, `pip install torch gymnasium minigrid wandb numpy`, `wandb login`, puis `WANDB_MODE=offline PYTHONPATH=src python -m naulthene.cerveau.noyau` ou en direct sans la variable une fois connecté)

## Before Modifying Code

- **Toute nouvelle section dans `colab.py`/`noyau.py` doit rester dans le style commenté existant** (`# --- N. NOM DE LA SECTION ---`) — c'est la table des matières de ces deux fichiers, qui restent volontairement monolithiques même si le reste du projet est packagé en modules
- Tout nouvel import entre modules du package doit être un **chemin absolu de package** (`from naulthene.<sous_package>.<module> import ...`), jamais un import à plat — voir la structure en [Architecture](#architecture)
- Vérifier si la modification touche à l'**architecture du réseau** (`AGI_Naulthene.__init__`) : toute nouvelle couche `NaultheneLinearSynaptique` doit être ajoutée à la fois dans `__init__`, dans `cycle_sommeil_global()` et dans `declencher_neurogenese()` — oublier l'un des trois casse silencieusement soit le sommeil soit la neurogenèse pour cette couche
- Vérifier si la modification touche au **rollout mental** (`simuler_futur_et_planifier`) : le premier pas doit toujours brancher sur les 7 actions réelles (`self.actions_eye`) et les pas suivants doivent suivre le réflexe glouton (`argmax`) plutôt que rebrancher sur 7 nouvelles actions — sinon la complexité explose en $7^{\text{horizon}}$ au lieu de rester linéaire. Ne pas changer cette restriction sans une raison explicite de l'utilisateur
- Vérifier si la modification touche au **réservoir dopaminergique** (`TENEUR_DOPAMINE`, constantes `DOPAMINE_*`, `TAUX_FRICTION/CHOC_BASE/RESSORT`) : la teneur doit toujours rester dans `[DOPAMINE_MIN, DOPAMINE_MAX]` via `np.clip` après chaque mise à jour — tester qu'aucun nouveau point de mise à jour n'oublie ce clip
- Vérifier si la modification touche à la **plasticité structurelle** (`NaultheneLinearSynaptique.agrandir`) : la segmentation `segments_in` doit couvrir exactement `in_features` existant (`assert total_ancien == self.in_features`) — toute nouvelle couche ajoutée à `declencher_neurogenese()` doit répercuter ses vraies dimensions d'entrée dans `segments_in`, dans le même ordre que la concaténation faite dans `forward()`/`penser()`
- Vérifier si la modification touche aux **détecteurs génériques** (`DetecteurFranchissementPortes`, `DetecteurProgresPersonnel`) : ils doivent rester agnostiques de la carte — ne jamais y coder un identifiant de niveau ou une position en dur, c'est tout l'intérêt de les distinguer de `DetecteurJalonsDoorKey`
- Vérifier si la modification touche au **cursus des 7 paliers DoorKey** (`DetecteurJalonsDoorKey`) : les noms de paliers (`NOMS`) et l'ordre de validation sont spécifiques à cet environnement — ne pas réutiliser cette classe telle quelle pour un autre niveau du `PROGRAMME`
- Vérifier si la modification touche au **rêve adaptatif** (`pourcentage_reve`, `POURCENTAGE_REVE_MIN`, `PLAGE_REVE_MAX`, `IMPORTANCE_REFERENCE_REVE`, `TAILLE_MIN_REVE`) : ne pas réintroduire une taille de batch fixe — le principe explicite du projet est que le pourcentage rejoué émerge de la plasticité et de la richesse de la journée, jamais d'une constante externe
- Vérifier si la modification touche au **Port Exocortex C3** (`src/naulthene/exocortex/`, `port_c3`, `tete_requete`, `ACTION_DEMANDER`) : l'invariant non négociable est qu'**aucun plug enregistré ⇒ comportement bit-identique à avant v28.0** — l'action `ACTION_DEMANDER` doit rester masquée à `-inf` dans `penser()` tant qu'aucun plug n'est disponible, et `PortC3.canal_emission` doit capturer TOUTE exception d'un plug (jamais de fuite vers le noyau). Ne jamais coder de déclenchement sur seuil d'incertitude pour appeler C3 — c'est un choix appris par REINFORCE (décision utilisateur explicite), pas un `if`. Toute modification touchant `num_actions` doit vérifier que `persistance._greffer_action_supplementaire` reste cohérente (greffe par recopie, jamais par exclusion, sur `tete_motrice`/`generateur_attente`/`generateur_attente_audio`/`actions_eye`) — sinon les `.brain` existants perdent leur tête motrice au chargement
- Après toute modification des hyperparamètres de la section 4, vérifier la cohérence avec le [README](readme.md) (tableau `config.py` narratif, formules) et mettre à jour la documentation si les valeurs divergent
- Ce script est prévu pour tourner sur GPU si disponible (`DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")`) — ne pas supposer un device fixe, toujours passer par `DEVICE` ou `.to(DEVICE)`

## Essential Commands

Pas de build au sens classique, mais le projet est un package Python (`src/naulthene/`) — tout lancement se fait **depuis la racine du dépôt**, avec `PYTHONPATH=src` et l'option `-m` (jamais `python <fichier>.py` directement) :

```bash
pip install torch gymnasium minigrid wandb numpy
PYTHONPATH=src python -m naulthene.cerveau.colab
```

Autres points d'entrée du même écosystème (voir [Architecture](#architecture) et [docs/LANCEMENT.md](docs/LANCEMENT.md) pour le guide complet) :

```bash
PYTHONPATH=src python -m naulthene.cerveau.noyau                              # terrain d'essai local (Mac)
PYTHONPATH=src python -m naulthene.cuve.daemon_cerveau --port 9999            # la Cuve (serveur persistant)
PYTHONPATH=src python -m naulthene.cuve.client_corps --port 9999              # client MiniGrid
PYTHONPATH=src python -m naulthene.salles_de_classe.cursus_developpemental    # Cursus par Ères (1000 jours, standalone)
PYTHONPATH=src python -m naulthene.instruments.lancer_arene                   # observer un cerveau entraîné
```

`wandb.init(project="Naulthene-AGI", ...)` demande une session W&B active (login `wandb login` au préalable, ou variable d'environnement `WANDB_API_KEY`) — sans clé configurée, W&B tombe en mode anonyme ou local selon la config de l'environnement.

Il n'y a ni linter ni suite de tests automatisés configurés. Toute vérification passe par l'observation des logs console (progression de palier, teneur en dopamine, thermostat de neurogenèse) et des courbes du tableau de bord W&B (voir [Modèle de Données & Métriques W&B](readme.md#modèle-de-données--métriques-wb) dans le README).

## Git Workflow

- Ne créer un commit que si l'utilisateur le demande explicitement
- Toujours créer un nouveau commit plutôt qu'un `--amend`, sauf demande contraire
- Ne jamais `push --force`, `reset --hard` ou sauter les hooks (`--no-verify`) sans autorisation explicite
- Un commit qui modifie `src/naulthene/cerveau/colab.py` de façon significative (nouvelle mécanique, changement d'hyperparamètre structurant, nouvelle section) doit s'accompagner de la mise à jour de `docs/CHANGELOG.md` et, si le changement est narrativement significatif, de `readme.md` — voir [Maintenance du Changelog](#maintenance-du-changelog)

## Maintenance du Changelog

**OBLIGATOIRE** : à chaque commit modifiant `src/naulthene/cerveau/colab.py` de façon significative, mettre à jour les fichiers suivants.

### 1. `docs/CHANGELOG.md`

Ajouter une entrée **en haut du fichier** (juste après l'introduction) avec ce format :

```markdown
## [X.X] - YYYY-MM-DD

### Titre court de la mise à jour

| Type | Details |
|------|---------|
| **Commit** | `hash` |
| **Catégorie** | feat/fix/perf/refactor/docs |
| **Impact** | Critique/Fonctionnel/Performance/Documentation |

**Description courte du changement.**

| Fichier modifié | Changement |
|-----------------|------------|
| `src/naulthene/cerveau/colab.py` | Description du changement |

---
```

Utiliser le hash court réel du commit (`git rev-parse --short HEAD`) une fois le commit créé. Si l'entrée est rédigée avant le commit correspondant, renseigner temporairement `N/A — en attente du commit de cette version` puis la corriger après coup.

### 2. `readme.md`

- Mettre à jour la ligne `#Version actuelle N.` en tête de `src/naulthene/cerveau/colab.py` si la version change
- Ajouter une nouvelle section "Nouveautés vX.X — Titre" en haut du Journal des Mises à Jour si le changement est significatif (feat / fix majeur), et mettre à jour la table des matières en conséquence
- Ne pas toucher aux sections narratives (architecture, formules) pour des commits `docs` / `chore` mineurs

### Règles de versioning

| Type de commit | Incrément version | Exemple |
|----------------|-------------------|---------|
| `feat` (nouvelle mécanique cognitive) | +1.0 | 13.0 → 14.0 |
| `fix` critique / `perf` majeur | +0.1 (suffixe `-fix1`) | 10.0 → 10.0-fix1 |
| `fix` mineur / `refactor` / `docs` | même version + suffixe | 14.0-fix1, 14.0-docs |
| `chore` / `style` | pas d'incrément | - |

Le script de référence `src/naulthene/cerveau/colab.py` est actuellement en version **17** (voir `readme.md`, table des matières et journal des mises à jour). `src/naulthene/cerveau/noyau.py` porte en plus toutes les mécaniques expérimentales non encore portées sur `colab.py` (actuellement jusqu'à **v28.0** — Cascade C1→C2→C3 & Port Exocortex — en passant par v18.0 Architecture Homéostatique Biologique, v22 Hémisphère Auditif & Vocal, v27.x École de la Parole, voir [Variante Locale de Test](#variante-locale-de-test-mac--srcnaulthenecerveaunoyaupy) et `readme.md`/`docs/CHANGELOG.md` pour le détail) — toute nouvelle mécanique testée localement suit la même échelle de version que le script de référence, marquée `-experimental` tant qu'elle n'y est pas portée. Poursuivre sur cette échelle entière (+1.0 pour la prochaine mécanique majeure) sauf décision contraire de l'utilisateur.
