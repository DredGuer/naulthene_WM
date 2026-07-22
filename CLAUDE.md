# CLAUDE.md

Instructions de travail pour Claude Code sur le projet **Naulthène AGI** — agent cognitif autonome hybride (RL + JEPA + mémoire épisodique + homéostasie neuro-mimétique), entraîné sur un cursus scolaire d'environnements MiniGrid à complexité croissante.

## Projet Overview

Naulthène AGI est un script de recherche unique (`agi_google_colab.py`, pensé pour tourner sur Google Colab) qui explore une architecture cognitive bio-inspirée plutôt qu'un pipeline RL classique. L'agent (`AGI_Naulthene`, `nn.Module`) combine :

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

Le projet tient dans un seul fichier à ce stade :

```
agi_google_colab.py     → script complet : modèle, détecteurs, boucle d'entraînement (972 lignes)
readme.md                → documentation narrative de l'architecture (table des matières, historique
                            des versions, description scientifique du modèle) — voir Maintenance ci-dessous
CHANGELOG.md              → suivi du projet, une entrée par évolution significative
CLAUDE.md                 → ce fichier
```

Structure interne de `agi_google_colab.py` (sections numérotées par des commentaires `# --- N. ... ---`) :

1. **Le Scalpel — Plasticité Structurelle** (`NaultheneLinearSynaptique`) : couche linéaire à poids base/annexe, cycle de sommeil (érosion + consolidation), et `agrandir()` pour la neurogenèse (extension des dimensions in/out sans perdre les poids appris)
2. **Le Cerveau Système 1 & 2** (`AGI_Naulthene`) : tronc cérébral commun (`porte_visuelle` → `hippocampe` → `analyseur`), lecture épisodique, tête motrice (Système 1), rollout mental (`simuler_futur_et_planifier`, Système 2), apprentissage journalier (`apprendre_journee`, Acteur-Critique + JEPA), rêve (`rever`), cycle de sommeil global, neurogenèse (`declencher_neurogenese`)
3. **Cursus & Détecteurs** :
   - 3a. `DetecteurJalonsDoorKey` — spécifique à l'environnement `DoorKey`, 7 paliers cognitifs codés en dur sur cette carte
   - 3b. Détecteurs génériques actifs sur n'importe quel niveau : `DetecteurFranchissementPortes`, `DetecteurProgresPersonnel`
4. **Exécution & Cursus** : configuration W&B, hyperparamètres (dopamine, planification, rêve adaptatif), programme des 5 niveaux (`PROGRAMME`), boucle principale jour/tick

Voir le [README](readme.md) pour la description narrative complète (formules d'homéostasie, tableau des 7 paliers, architecture cognitico-biologique en diagramme ASCII).

## Before Modifying Code

- **Toute nouvelle section doit rester dans le style commenté existant** (`# --- N. NOM DE LA SECTION ---`) — c'est la seule table des matières du fichier tant qu'il reste monolithique
- Vérifier si la modification touche à l'**architecture du réseau** (`AGI_Naulthene.__init__`) : toute nouvelle couche `NaultheneLinearSynaptique` doit être ajoutée à la fois dans `__init__`, dans `cycle_sommeil_global()` et dans `declencher_neurogenese()` — oublier l'un des trois casse silencieusement soit le sommeil soit la neurogenèse pour cette couche
- Vérifier si la modification touche au **rollout mental** (`simuler_futur_et_planifier`) : le premier pas doit toujours brancher sur les 7 actions réelles (`self.actions_eye`) et les pas suivants doivent suivre le réflexe glouton (`argmax`) plutôt que rebrancher sur 7 nouvelles actions — sinon la complexité explose en $7^{\text{horizon}}$ au lieu de rester linéaire. Ne pas changer cette restriction sans une raison explicite de l'utilisateur
- Vérifier si la modification touche au **réservoir dopaminergique** (`TENEUR_DOPAMINE`, constantes `DOPAMINE_*`, `TAUX_FRICTION/CHOC_BASE/RESSORT`) : la teneur doit toujours rester dans `[DOPAMINE_MIN, DOPAMINE_MAX]` via `np.clip` après chaque mise à jour — tester qu'aucun nouveau point de mise à jour n'oublie ce clip
- Vérifier si la modification touche à la **plasticité structurelle** (`NaultheneLinearSynaptique.agrandir`) : la segmentation `segments_in` doit couvrir exactement `in_features` existant (`assert total_ancien == self.in_features`) — toute nouvelle couche ajoutée à `declencher_neurogenese()` doit répercuter ses vraies dimensions d'entrée dans `segments_in`, dans le même ordre que la concaténation faite dans `forward()`/`penser()`
- Vérifier si la modification touche aux **détecteurs génériques** (`DetecteurFranchissementPortes`, `DetecteurProgresPersonnel`) : ils doivent rester agnostiques de la carte — ne jamais y coder un identifiant de niveau ou une position en dur, c'est tout l'intérêt de les distinguer de `DetecteurJalonsDoorKey`
- Vérifier si la modification touche au **cursus des 7 paliers DoorKey** (`DetecteurJalonsDoorKey`) : les noms de paliers (`NOMS`) et l'ordre de validation sont spécifiques à cet environnement — ne pas réutiliser cette classe telle quelle pour un autre niveau du `PROGRAMME`
- Vérifier si la modification touche au **rêve adaptatif** (`pourcentage_reve`, `POURCENTAGE_REVE_MIN`, `PLAGE_REVE_MAX`, `IMPORTANCE_REFERENCE_REVE`, `TAILLE_MIN_REVE`) : ne pas réintroduire une taille de batch fixe — le principe explicite du projet est que le pourcentage rejoué émerge de la plasticité et de la richesse de la journée, jamais d'une constante externe
- Après toute modification des hyperparamètres de la section 4, vérifier la cohérence avec le [README](readme.md) (tableau `config.py` narratif, formules) et mettre à jour la documentation si les valeurs divergent
- Ce script est prévu pour tourner sur GPU si disponible (`DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")`) — ne pas supposer un device fixe, toujours passer par `DEVICE` ou `.to(DEVICE)`

## Essential Commands

Pas de build, pas de packaging — c'est un script exécuté directement :

```bash
pip install torch gymnasium minigrid wandb numpy
python agi_google_colab.py
```

`wandb.init(project="Naulthene-AGI", ...)` demande une session W&B active (login `wandb login` au préalable, ou variable d'environnement `WANDB_API_KEY`) — sans clé configurée, W&B tombe en mode anonyme ou local selon la config de l'environnement.

Il n'y a ni linter ni suite de tests automatisés configurés. Toute vérification passe par l'observation des logs console (progression de palier, teneur en dopamine, thermostat de neurogenèse) et des courbes du tableau de bord W&B (voir [Modèle de Données & Métriques W&B](readme.md#modèle-de-données--métriques-wb) dans le README).

## Git Workflow

- Ne créer un commit que si l'utilisateur le demande explicitement
- Toujours créer un nouveau commit plutôt qu'un `--amend`, sauf demande contraire
- Ne jamais `push --force`, `reset --hard` ou sauter les hooks (`--no-verify`) sans autorisation explicite
- Un commit qui modifie `agi_google_colab.py` de façon significative (nouvelle mécanique, changement d'hyperparamètre structurant, nouvelle section) doit s'accompagner de la mise à jour de `CHANGELOG.md` et, si le changement est narrativement significatif, de `readme.md` — voir [Maintenance du Changelog](#maintenance-du-changelog)

## Maintenance du Changelog

**OBLIGATOIRE** : à chaque commit modifiant `agi_google_colab.py` de façon significative, mettre à jour les fichiers suivants.

### 1. `CHANGELOG.md` (racine)

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
| `agi_google_colab.py` | Description du changement |

---
```

Utiliser le hash court réel du commit (`git rev-parse --short HEAD`) une fois le commit créé. Si l'entrée est rédigée avant le commit correspondant, renseigner temporairement `N/A — en attente du commit de cette version` puis la corriger après coup.

### 2. `readme.md` (racine)

- Mettre à jour la ligne `#Version actuelle N.` en tête de `agi_google_colab.py` si la version change
- Ajouter une nouvelle section "Nouveautés vX.X — Titre" en haut du Journal des Mises à Jour si le changement est significatif (feat / fix majeur), et mettre à jour la table des matières en conséquence
- Ne pas toucher aux sections narratives (architecture, formules) pour des commits `docs` / `chore` mineurs

### Règles de versioning

| Type de commit | Incrément version | Exemple |
|----------------|-------------------|---------|
| `feat` (nouvelle mécanique cognitive) | +1.0 | 13.0 → 14.0 |
| `fix` critique / `perf` majeur | +0.1 (suffixe `-fix1`) | 10.0 → 10.0-fix1 |
| `fix` mineur / `refactor` / `docs` | même version + suffixe | 14.0-fix1, 14.0-docs |
| `chore` / `style` | pas d'incrément | - |

Le projet est actuellement en version **14** (voir `readme.md`, table des matières et journal des mises à jour). Poursuivre sur cette échelle entière (14 → 15 pour la prochaine mécanique majeure) sauf décision contraire de l'utilisateur.
