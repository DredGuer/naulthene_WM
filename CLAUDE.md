# CLAUDE.md

Instructions de travail pour Claude Code sur le projet **Naulthène AGI** — agent cognitif autonome hybride (RL + JEPA + mémoire épisodique + homéostasie neuro-mimétique), entraîné sur un cursus scolaire d'environnements MiniGrid à complexité croissante.

## Projet Overview

Naulthène AGI est un projet de recherche (packagé en `src/naulthene/`, cœur de référence pensé pour tourner sur Google Colab) qui explore une architecture cognitive bio-inspirée plutôt qu'un pipeline RL classique. L'agent (`AGI_Naulthene`, `nn.Module`) combine :

- Un **modèle du monde JEPA** (Joint Embedding Predictive Architecture) qui prédit l'état latent suivant plutôt que l'observation brute (`generateur_attente`, `perte_jepa`)
- Un **Système 1** instinctif (tête motrice Acteur-Critique classique) et un **Système 2** délibératif qui simule mentalement les conséquences de ses actions sur un horizon de plusieurs pas (`simuler_futur_et_planifier`) avant de arbitrer entre les deux — nommés explicitement **C1** (réflexe) et **C2** (néo-cortex) depuis la v29.0, C2 ne recevant jamais que l'état déjà compressé par C1
- Une **mémoire à flux enrichi** (v36.0) : tout événement saillant laisse un repère spatial, la **récurrence** le transforme en abstraction (`confirmations`, `valence` apprise), et l'oubli retire le moins abstrait plutôt que le plus ancien — sans qu'aucun type d'objet ne soit jamais nommé dans le code
- Un **Bus Sensoriel multimodal** (`bus_sensoriel.py`, v29.0/v30.0) qui donne à l'agent les **5 sens** hiérarchisés par gourmandise énergétique : vue et ouïe (gourmands, chacun avec sa porte synaptique dans le bus latent et sa cible JEPA), puis toucher, odorat et goût (faibles à moyens, injectés en queue du `vecteur_bio` donc hors de la cible JEPA) — plus, depuis la v30.0, un **6ᵉ sens exogène** (l'**Exo-Sens**) : le monde numérique (LLM/RAG, APIs, IoT) perçu en continu via le Port C3, sans jamais être « interrogé » par une action
- Une **mémoire épisodique** de contexte (moyenne glissante des états latents récents de l'épisode, `vecteurs_episodiques`) et une mémoire tampon court terme (`hippocampe`)
- Un **réservoir dopaminergique homéostatique** ($D_t \in [0.001, 10.0]$) qui module la motivation et la plasticité synaptique en fonction des succès/échecs vécus dans la journée
- Une **plasticité structurelle** (`NaultheneLinearSynaptique`) : chaque couche a un poids de base figé et un poids "annexe" appris pendant la journée, consolidé (ou érodé) chaque nuit selon une trace de myéline — avec neurogenèse (ajout de dimensions) déclenchée par un thermostat d'erreur JEPA
- Une **consolidation nocturne (rêve)** à porosité adaptative : le pourcentage de souvenirs rejoués la nuit dépend de la plasticité du moment et de la richesse (importance moyenne) de la journée, pas d'une taille de batch fixe
- Des **détecteurs de progrès génériques**, agnostiques de la carte (franchissement de portes, records de proximité à l'objectif), en plus du détecteur de jalons spécifique à `DoorKey` (cursus à 7 paliers)

L'agent progresse à travers un **cursus académique** de **15 niveaux** MiniGrid (v35.0 — 5 avant), du Nourrisson (`Empty-5x5`) au Doctorat (planification longue distance), promu par **2 victoires consécutives OU 60 % de maîtrise sur une fenêtre glissante de 20 épisodes**.

Ce n'est pas une application produit : c'est un script de recherche exécuté en continu (boucle de jours/ticks), instrumenté avec **Weights & Biases** pour le suivi expérimental — projet public [`Naulthene-AGI`](https://wandb.ai/naultadrien123-nvnc/Naulthene-AGI), ~90 métriques par nuit simulée. Pas de tests automatisés, pas de build — la validation passe par l'observation des courbes W&B et des logs console.

### Le positionnement du projet (à préserver dans toute communication)

**Naulthène a vocation à être un CERVEAU COMPLET EN ATTENTE D'UN CORPS**, et il est
**toujours en cours de développement**.

MiniGrid n'est pas la finalité : c'est un **berceau** — un monde peu coûteux et rapide où élever,
casser et mesurer un cerveau. Ce qui se construit est l'organe : des sens qui alimentent tous le
même espace, un métabolisme, une couche réflexe et une couche délibérative, une mémoire qui
abstrait par répétition, un cycle jour/nuit. **Le cœur ne nomme presque rien du monde** —
⚠️ audit du 18/08/2026 : `COULEUR_FOOD="red"`/`COULEUR_WATER="blue"` et un test
`type == "ball"` subsistent dans `noyau.py` (voir
`docs/etat_des_lieux/18082026_revue_dogme_avant_publication.md`), donc ne jamais affirmer
« rien en dur » sans nuance — c'est précisément ce qui rend envisageable le remplacement du berceau par une
caméra, un micro et un bus moteur.

Deux conséquences pour la rédaction de toute doc, tout commit, toute description :

- Ne jamais présenter le projet comme un solveur MiniGrid, ni comme un système livré.
- Ne jamais masquer l'état réel : l'agent est **bloqué au niveau 1 sur 15** — **0 promotion
  sur 10 graines × 2000 jours**, maîtrise maximale 40 % pour un seuil à 60 %, et **couper C2
  ne change le score de 0,0 point sur les 6 niveaux** (78 cellules d'ablation). Une graine
  antérieure avait atteint le niveau 4 : c'était une **loterie natale**, non reproductible.
  L'échec fait partie du carnet de recherche et se documente (voir
  `docs/recherche/CAMPAGNE_v41_population_et_ablation_aout_2026.md` pour la mesure, et
  `docs/recherche/dia_Aout_2026.md` pour le diagnostic).

### La règle de miroir — `readme.md` (EN) ↔ `readme_fr.md` (FR)

**`readme.md` est la page d'accueil GitHub et il est en ANGLAIS.** `readme_fr.md` en est le
**miroir français** : son en-tête reprend la même thèse, les mêmes chiffres et les mêmes
tableaux, avant de dérouler la documentation narrative longue (architecture, formules, journal
des versions) qui n'existe qu'en français.

**Toute modification de l'en-tête de l'un doit être répercutée dans l'autre, dans le même
commit** — un lecteur francophone et un lecteur anglophone doivent lire les mêmes faits.

| Bloc | Dans les deux |
|---|---|
| La thèse (espace vectoriel unifié) · « un cerveau complet en attente d'un corps » | ✅ |
| L'avertissement **« cela ne fonctionne pas encore »** | ✅ |
| Paramètres par couche + total · comparaison aux baselines RL et son verdict défavorable | ✅ |
| L'état du blocage · le tableau d'ablation sensorielle · l'empreinte mémoire | ✅ |
| Le lien W&B public | ✅ |
| Journal des versions, formules détaillées, paliers | ❌ **français seulement** |

Ne mettre ces blocs à jour que si l'un de ces trois éléments bouge : **(1)** le nombre de
paramètres — le recompter réellement, jamais l'estimer (`sum(p.numel() for p in
agent.parameters())`) ; **(2)** l'état du blocage ; **(3)** un tableau de benchmark — dès
qu'une mesure existe, elle y entre, des deux côtés.

⚠️ **Ne jamais écrire une supériorité non mesurée.** Les deux README affirment que Naulthène
est **2,85× plus lourd** qu'un PPO CNN (55 232 contre 19 384 paramètres), qu'il **ne résout
pas** `Empty-8x8`, et que **couper C2 ne change rien** (0,0 pt sur 6 niveaux). Ces chiffres
sont vérifiables en cinq minutes par n'importe quel lecteur ; les enjoliver coûterait toute la
crédibilité du dépôt. La thèse défendable est **l'unification** (une seule règle de
plasticité, un seul bus, ajout de sens additif) — la légèreté reste à démontrer par un
benchmark à budget égal.

## Architecture

Le projet est organisé en **package Python** sous `src/naulthene/`, avec un dossier par grande fonction cognitive — le vocabulaire des dossiers suit celui du projet (le cerveau, les salles de classe, la Cuve) :

```
21. AGI/                          racine du dépôt (CWD de lancement de tous les scripts)
├── LICENSE, NOTICE               licence Apache 2.0 et attribution — voir readme_fr.md
├── readme.md                     VITRINE en anglais — la thèse (espace vectoriel unifié), les
│                                   chiffres de comparaison aux baselines RL, l'état du blocage.
│                                   C'est la page d'accueil GitHub : la garder courte et factuelle
├── readme_fr.md                  documentation narrative de référence en français (table des
│                                   matières, historique des versions v7→v37, description
│                                   scientifique du modèle) — c'est ici que vont les détails
├── CLAUDE.md                     ce fichier
├── .gitignore
│
├── src/naulthene/                LE PACKAGE
│   ├── cerveau/                  ← LE CERVEAU (cœur cognitif)
│   │   ├── noyau.py              terrain d'essai local (ex-agi_local_test.py, versionné depuis v39.0)
│   │   ├── colab.py              script de référence versionné (ex-agi_google_colab.py)
│   │   ├── bus_sensoriel.py      l'Interpréteur des sens (v29.0/v30.0) — toucher, odorat, goût,
│   │   │                          et l'Exo-Sens (6ème sens) ; pur numpy, n'importe JAMAIS noyau.py
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
│   │                               PlugHTTP, PlugMemoireAugmentee) qui s'enregistrent sur le port
│   └── instruments/               ← INSTRUMENTS D'OBSERVATION (lecture seule)
│       ├── arene_visuelle.py     fenêtre pygame de visualisation en direct
│       ├── lancer_arene.py       lance l'Arène (pygame + audio)
│       ├── irm_cerveau.py        scanner d'activations internes, ne modifie jamais le .brain
│       ├── sonde_c1_c2.py        rapport de force C1/C2 (v37.0) — amplitudes, ratio, accord
│       └── sonde_poids.py        santé synaptique couche par couche (v37.0) — signale les
│                                   couches collées au plancher vital
│
├── brains/                       cerveaux cristallisés (*.brain, gitignorés) — un fichier par run,
│   ├── old_V30/                    nommé DDMMYYYYHHMM_VXX_NMRTOUR_RMD.brain (voir « Convention de
│   ├── old_testV30-V34/            nommage des cerveaux ») ; old_VXX/ archive les générations
│   ├── old_V37/                    précédentes, jamais supprimées. old_V37/ contient la lignée
│   │   └── recherche_aout2026/     v34→v37 (8 cerveaux) et, dans son sous-dossier, les 70 cerveaux
│   │                               de la campagne d'ablation/hypothèses du 11-12 août 2026
│   └── ablations/                  résultats JSON du banc d'ablation
└── docs/                         DOCUMENTATION — 4 dossiers, un rôle chacun.
    │                               👉 POINT D'ENTRÉE : docs/INDEX.md (dit où chercher)
    ├── INDEX.md                  la carte : quelle question → quel document
    ├── fonctionnement/           NORMATIF — fait autorité sur l'état courant
    │                               CHANGELOG.md (référence factuelle version par version),
    │                               LANCEMENT.md (commandes, dépannage), Parcourt_readme.md,
    │                               explications_readme.md (détail algorithmique, §15 sens)
    ├── recherche/                ENQUÊTES — non normatif, mais à consulter AVANT toute
    │                               idée neuve : recherche_bug_or_not_bug.md (H1→H18, les
    │                               hypothèses réfutées), dia_Aout_2026.md (diagnostic),
    │                               ETAT_DU_PROJET_aout_2026.md, REVUE_CODE_v39_aout_2026.md
    │                               (les 6 défauts trouvés), evals/ (sorties JSON)
    ├── ameliorations/            IDÉES proposées, PAS encore validées :
    │                               AVIS_ET_PROPOSITIONS_aout_2026.md (P1→P16),
    │                               les_sens_combinatoire.md, CONCEPTION_v34, v33
    └── ameliorations_appliquees/ LIVRÉ dans le code — garde la trace des options
                                    ÉCARTÉES et de leurs raisons : CHANTIER_v37, v38,
                                    CONCEPTION_v22_audio, v30_exo_sens, EXPLICATIONS_v29
```

Le cœur de référence est `src/naulthene/cerveau/colab.py` (ex-`agi_google_colab.py`, pensé pour tourner sur Google Colab). Structure interne (sections numérotées par des commentaires `# --- N. ... ---`) :

1. **Le Scalpel — Plasticité Structurelle** (`NaultheneLinearSynaptique`) : couche linéaire à poids base/annexe, cycle de sommeil (érosion + consolidation), et `agrandir()` pour la neurogenèse (extension des dimensions in/out sans perdre les poids appris)
2. **Le Cerveau C1 (Réflexe) & C2 (Néo-Cortex)** (`AGI_Naulthene`) — section renommée en v29.0, l'identité C1/C2 étant désormais explicite dans le code : tronc cérébral commun (`porte_visuelle` → `hippocampe` → `analyseur`), lecture épisodique, **C1** (`_executer_c1_reflexe` : compression des 5 sens, intégration viscérale, tête motrice / Système 1), **C2** (`_solliciter_c2_neocortex` → `simuler_futur_et_planifier`, JEPA / Système 2), `penser()` réduit à l'arbitrage des deux, apprentissage journalier (`apprendre_journee`, Acteur-Critique + JEPA), rêve (`rever`), cycle de sommeil global, neurogenèse (`declencher_neurogenese`)
3. **Cursus & Détecteurs** :
   - 3a. `DetecteurJalonsDoorKey` — spécifique à l'environnement `DoorKey`, 7 paliers cognitifs codés en dur sur cette carte
   - 3b. Détecteurs génériques actifs sur n'importe quel niveau : `DetecteurFranchissementPortes`, `DetecteurProgresPersonnel`
4. **Exécution & Cursus** : configuration W&B, hyperparamètres (dopamine, planification, rêve adaptatif), programme des niveaux (`PROGRAMME` — 15 depuis la v35.0, 5 dans `colab.py`), boucle principale jour/tick

Voir le [README](readme_fr.md) pour la description narrative complète (formules d'homéostasie, tableau des 7 paliers, architecture cognitico-biologique en diagramme ASCII).

Tous les imports entre modules du package sont des **chemins absolus de package** (`from naulthene.cerveau.noyau import ...`, `import naulthene.audio.professeur_gemma as pg`) — jamais d'imports relatifs à plat. Tout script se lance depuis la **racine du dépôt** avec `PYTHONPATH=src` et l'option `-m` (voir [Essential Commands](#essential-commands)) ; les chemins `.brain` par défaut sont relatifs à cette racine (`brains/naulthene_*.brain`).

## Variante Locale de Test (Mac) — `src/naulthene/cerveau/noyau.py`

En plus du script de référence `colab.py`, le projet dispose d'une copie de travail (`src/naulthene/cerveau/noyau.py`, ex-`agi_local_test.py`) utilisée pour tester rapidement de nouvelles mécaniques sur Mac (Apple Silicon, device `mps`) avant de les porter — ou non — sur le script de référence.

> ⚠️ **Depuis la v39.0 (2026-08-13), ce fichier est VERSIONNÉ.** Il était gitignoré depuis
> l'origine, et portait à lui seul toute l'évolution **v34 → v37.1** — 369 Ko, quatre mois de
> mécaniques, en **un exemplaire sur un disque**. Les carnets décrivent ces mécaniques, ils ne
> permettent pas de les reconstruire à l'identique : c'était le risque structurel n°1 du projet.
> **Sa nature ne change pas pour autant** — il reste le terrain d'essai des mécaniques
> expérimentales, `colab.py` reste le script de référence, et le portage noyau → colab reste à
> faire mécanique par mécanique. Ce qui change est seulement qu'un accident ne l'efface plus.

- **Deux différences permanentes avec `colab.py`** : détection du device `cuda`/`mps`/`cpu` (au lieu de `cuda`/`cpu` seul) et un `jours_totaux` ajustable localement pour des runs de test plus courts que les 400 jours de Colab
- **C'est le terrain d'essai des mécaniques expérimentales** (actuellement v18.0 Architecture Homéostatique Biologique, v19.0 Métabolisme 20/80 & Forage 80/20, et toute mécanique suivante tant qu'elle n'a pas été validée sur un run long) — ces versions vivent **uniquement** dans ce fichier tant qu'elles ne sont pas explicitement portées sur `colab.py`. Exceptions notables : `exocortex/` (v28.0) et `cerveau/bus_sensoriel.py` (v29.0) sont des modules **versionnés** dans git, même si la mécanique qui les consomme n'existe pour l'instant que dans `noyau.py`
- Toute modification doit être documentée dans `readme_fr.md`/`docs/fonctionnement/CHANGELOG.md` avec la mention explicite **"expérimental"** et l'avertissement qu'elle ne vit que dans `noyau.py` — ne jamais laisser croire qu'une mécanique expérimentale est déjà dans le script de référence. Le fichier est désormais versionné (v39.0), mais cela ne le promeut **pas** au rang de référence : la distinction noyau (essai) / colab (référence) reste entière
- Avant de porter une mécanique validée vers `colab.py`, vérifier qu'elle est cohérente avec toute l'évolution parallèle qu'a pu subir le script de référence entre-temps (les deux fichiers peuvent diverger sur plusieurs versions)
- Setup local : voir [Démarrage Rapide](readme_fr.md#démarrage-rapide) dans le README (venv Python 3.12, `pip install torch gymnasium minigrid wandb numpy`, `wandb login`, puis `WANDB_MODE=offline PYTHONPATH=src python -m naulthene.cerveau.noyau` ou en direct sans la variable une fois connecté)

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
- Vérifier si la modification touche au **Bus Sensoriel / vecteur bio** (`src/naulthene/cerveau/bus_sensoriel.py`, `DIM_VECTEUR_BIO`, `DIM_TOUCHER`, `DIM_CHIMIE`, `obtenir_vecteur_bio`) : trois invariants v29.0. (1) `bus_sensoriel.py` reste **pur numpy** et n'importe **jamais** `noyau.py` — c'est ce qui garantit l'absence de cycle d'import, même discipline que `exocortex/port_c3.py`. (2) Toute nouvelle dimension du vecteur bio s'ajoute **EN QUEUE**, jamais au milieu : l'ordre de concaténation de `obtenir_vecteur_bio` est un contrat partagé avec `BusSensoriel.interpreter` et avec `persistance._greffer_vecteur_bio_etendu`, qui recopie les N premières colonnes d'un ancien `.brain` — une insertion au milieu décalerait silencieusement tous les acquis. (3) Les sens faibles (toucher, odorat, goût) n'entrent **jamais** dans `bus_latent` : ils passent par `integrateur_bio`, donc restent hors de la cible JEPA (`perte_jepa` compare toujours le bus prédit au bus réel de la **vision seule**). Ne pas leur donner de porte synaptique sommée dans le tronc cérébral sans demande explicite de l'utilisateur
- Vérifier si la modification touche à la **frontière C1/C2** (`_executer_c1_reflexe`, `_solliciter_c2_neocortex`, `penser`) : le découpage v29.0 est une **restructuration pure** (décision utilisateur explicite) — C2 est sollicité à chaque tick, exactement comme avant, et l'arbitrage `logits_instinct + valeurs_simulees * force_planification` est inchangé depuis la v13.0. Ne **pas** y introduire de court-circuit conditionnel ("C1 saute C2 s'il est confiant") sans demande explicite : ce serait un déclenchement sur seuil codé en dur dans le chemin de décision, de la même nature que ce que ce fichier interdit déjà pour l'appel à C3. C2 ne doit par ailleurs jamais recevoir autre chose que l'état déjà compressé par C1 (`pensee_bio`) — jamais l'observation brute, jamais l'environnement. **Quatre invariants v37.0** (chantier `docs/ameliorations_appliquees/CHANTIER_v37_equilibre_c1_c2.md`), posés après la mesure que C1 et C2 n'étaient d'accord sur **aucun tick** (0 %, y compris sur les niveaux maîtrisés), chacun votant une action constante, avec un ratio d'amplitude de 9,9× à 22,1× : (1) **le gain de C1 est un facteur SCALAIRE à double sens** (`GAIN_C1_MIN/MAX`) — il règle le VOLUME de la voix, jamais l'OPINION : les rapports entre les 7 logits doivent rester rigoureusement intacts. La borne haute n'est pas décorative : sans elle, une fois les têtes débloquées, la distillation renforce C1 plus vite que C2 et le ratio **s'inverse à 0,21×** (mesuré sur 30 jours). (2) **`VIGUEUR_MIN_C1` est DÉRIVÉE, jamais posée** : `(AMPLITUDE_C2_NORMALISEE × FORCE_PLANIFICATION_LIBRE) / RATIO_C1C2_VISE`. Le 2,1 est l'amplitude d'un z-score sur 7 actions, vérifiée empiriquement sur trois environnements — ne pas le remplacer par un chiffre rond. (3) **La normalisation de C2 est INCONDITIONNELLE** : l'ancien `if std > 1e-6` laissait `valeur_cumulee` à son échelle brute (~1e-7) sous le seuil, soit un C2 **numériquement éteint** qui disparaissait de la fusion sans aucun signal (observé : des journées entières à `C2=0.000`). « C2 hésite entre des branches proches » ≠ « C2 n'a pas d'avis ». (4) **L'auto-distillation C2 → C1 exige `.detach()` sur la cible** — sans lui le gradient remonte dans le rollout et C2 apprend à se rendre *prévisible* plutôt que juste ; vérifier que `cortex_prefrontal` reçoit bien **0,00000000** par ce canal. **v37.1 — la distillation est SÉLECTIVE** (`_ponderer_distillation`, `reference_choc_dopamine`, `chocs_dopamine_journee`) : C1 n'automatise que ce qui a marché. Trois invariants. (a) Le crédit **s'arrête aux frontières d'épisode** (`dones`) — créditer un tick de l'épisode précédent pour une réussite du suivant serait une superstition, l'agent ayant été téléporté entre les deux. (b) La moyenne est **pondérée**, dénominateur = somme des poids : une journée entièrement stérile ne distille **rien**, au lieu de distiller uniformément du bruit. (c) **`reference_choc_dopamine` est un NIVEAU, jamais un SEUIL** — il n'existe aucune règle « si choc > X, imiter » : le crédit est continu et proportionnel, et l'échelle qui juge un choc « fort » est dérivée de ce que **cet agent** a lui-même vécu (mesuré : le même choc de 0,1 vaut **100 % pour un débutant et 11,4 % pour le même agent devenu expert**). Ne jamais remplacer ce niveau par une constante : c'est l'exemple de référence du principe « rien n'est en dur, les niveaux évoluent avec l'âge et les habitudes ». (d) **v37.1-fix1 — cette référence est un CLIQUET : montée rapide, descente ~50× plus lente** (`INERTIE_OUBLI_REFERENCE_CHOC`). Ne **jamais** revenir à une moyenne glissante symétrique : mesuré sur 600 jours, quand l'agent cesse de gagner il ne reste que des micro-chocs, la référence descend **vers eux** (0,2149 → 0,0932, −57 %) et, le crédit valant `choc / référence`, le même événement médiocre crédite de plus en plus (10 % → 69 %, ×7). L'agent devenait **de plus en plus facile à impressionner** — l'inverse exact du principe — et C1 distillait 70 % de bruit. La protection « une journée stérile ne distille rien » n'y suffit pas : la journée n'est jamais *stérile*, elle est *médiocre*. C'est le défaut de `norme_naissance` (v34.0-fix2) à l'identique — une référence qui suit la décroissance ne borne plus rien. La descente doit rester **non nulle** (un monde durablement plus pauvre doit pouvoir recalibrer), mais sur des centaines de nuits, jamais sur une saison creuse. ⚠️ Ne **pas** réintroduire « l'échelle de C2 porte sa confiance » (réinjecter `indecision_c2` après normalisation) sans lire §5.6 du chantier : implémentée deux fois, mesurée deux fois, échouée deux fois (échelle absolue → éteint C2 à 0,01× ; échelle relative → sature à la borne, effet net nul). Tant que `cortex_prefrontal` est au plancher vital, C2 n'a aucune confiance variable à exprimer. ⚠️ Ne **pas** rendre `force_planification` fonction de l'incertitude (entropie de C1, erreur JEPA) sans un run long montrant `Arbitrage_Ratio_C2C1` **stagnant** : c'est un déclenchement sur seuil déguisé en formule continue (une sigmoïde reste un `if` avec une pente), le signal d'entrée n'existe pas (`indecision_c2` varie de **1,00×** entre min et max sur 300 ticks), et surtout le ratio est déjà passé de 22× à 0,6× **sans aucun pilotage**, par la seule maturation synaptique une fois les bugs d'érosion corrigés. La décroissance de l'écoute de C2 avec la maturité doit **émerger**, jamais être formulée
- Vérifier si la modification touche à l'**Exo-Sens** (`DIM_EXO`, `percevoir_exogene`, `_rafraichir_perception_exogene`, `PERIODE_PERCEPTION_EXO`, `ReponseC3.perception`) : quatre invariants v30.0. (1) L'Exo-Sens est une **perception continue**, jamais une action ni un déclenchement — ne **pas** y réintroduire de seuil (« si l'erreur JEPA monte, interroger C3 ») : c'est ce que le projet a refusé trois fois (v28 pour l'appel à C3, v29 pour le court-circuit C1→C2, v30 pour cette boucle d'attention). L'attention accordée aux 8 dims doit émerger de la myélinisation de `integrateur_bio`. (2) `ACTION_DEMANDER` reste masquée à `-inf` **en permanence** et `num_actions` reste à 8 — la colonne est dormante mais jamais amputée (4 `.brain` du dépôt sont à 8 actions). (3) `percevoir_exogene` **clippe toujours** dans [0,1] et rejette un vecteur de mauvaise taille : un service externe n'est pas maîtrisé, et une dimension hors échelle écraserait `integrateur_bio`. Un Exo-Sens invalide ne doit **jamais** désactiver les 5 sens physiques (avertissement séparé, voir `_avertir_exo`). (4) Le bus n'est interrogé qu'un tick sur `PERIODE_PERCEPTION_EXO` avec mise en cache — un plug HTTP à 100 ms-30 s rendrait sinon impraticable un run de 120 000 ticks
- **Toute nouvelle mécanique observable doit être instrumentée dans le même commit** (leçon de la v29.1) : un compteur remis à zéro dans `_reinitialiser_buffers_journee`, accumulé dans `traiter_tick`, puis agrégé dans `executer_nuit` (ligne du bilan console **et** clé dans le dict `log_wandb` retourné). Sans cela, la mécanique est invisible sur un run long et son utilité réelle indémontrable — la v29.0 avait livré les 5 sens sans aucune télémétrie, écart corrigé en v29.1. Deux règles : ne jamais créer un compteur journalier par `getattr(etat, "...", 0)` sans l'ajouter à `_reinitialiser_buffers_journee` (piège du bug `score_vocal_jour` v27.0, où la « moyenne du jour » cumulait depuis la naissance), et rendre les clés **conditionnelles** quand la mécanique peut être inactive (voir les blocs `Sens_*` et C3), plutôt que de logger des zéros trompeurs
- Vérifier si la modification touche à la **capacité mnésique** (`MemoireEpisodiqueSpatiale.ajuster_capacite`, `SOUVENIRS_PAR_DIM`, `capacite_plancher`) ou au **facteur de richesse du rêve** (`reference_richesse`, `empreinte_enfance`) : trois invariants v31.0. (1) La capacité est recalculée **une fois par nuit**, jamais par tick — une capacité fluctuante rendrait la FIFO illisible et le diagnostic impossible. (2) Elle ne descend **jamais** sous `capacite_plancher` (200) et, si elle rétrécit, la troncature se fait **par l'AVANT** (`pop(0)`, les plus anciens partent) — tronquer par la fin jetterait les souvenirs les plus frais, les plus utiles au rappel. (3) Un souvenir spatial est un **repère**, jamais un journal d'événements : `enregistrer_evenement` **déduplique** sur `(pos, type)` en rafraîchissant le tick, et la capacité est bornée par la taille du monde (`DENSITE_MAX_PAR_CASE`) — un `.brain` réel contenait 91 % de doublons avant ce correctif. (4) `reference_richesse` doit rester proportionnelle à `empreinte_enfance` : sans cela, `%_reve` s'effondre mécaniquement quand le cerveau grandit (mesuré : 60 % à dim_bus=16 → 15 % à dim_bus=96). Attention à ne pas sur-corriger : une part de la baisse de rêve sur un cerveau mature est **saine** (l'erreur JEPA chute parce que l'agent comprend mieux son monde) — ne jamais compenser ce signal-là
- Vérifier si la modification touche à l'**odorat** (`_distances_topologiques`, `_bfs_vers_agent`, `SURCOUT_PORTE_FERMEE`, `TYPES_BLOQUANTS_ODORAT`) ou à la **clinotaxie** (`DIM_ODORAT_DELTA`, `_calculer_deltas_odorat`, `_odeurs_precedentes`) : quatre invariants v32.0. (1) La distance olfactive est **topologique**, jamais euclidienne/Manhattan — une odeur qui traverse un mur produit un gradient *trompeur*, pire que pas de gradient du tout, car `integrateur_bio` ne peut pas apprendre à ignorer un signal qui n'est faux qu'une partie du temps. Sans obstacle, le BFS retombe exactement sur Manhattan : c'est le test de non-régression à conserver. (2) Une porte fermée **« fuit »** (surcoût `+4`), elle ne bloque pas : la bloquer rendrait l'odorat inutile précisément quand l'agent cherche la clé de cette porte. (3) Le neutre de la clinotaxie est **0.5, jamais 0.0** — 0.0 signifierait un éloignement maximal, et `obtenir_vecteur_bio` doit le respecter dans son fallback hors MiniGrid (vocal isolé, rêve), sans quoi l'agent perçoit une fuite olfactive permanente qui n'existe pas. (4) `_odeurs_precedentes` **doit** être remis à `None` dans `reinitialiser_episode` : au `reset()` l'agent est téléporté et les sources régénérées, donc comparer au dernier tick de l'épisode précédent injecterait un ΔS énorme et fictif. Ne pas réintroduire d'**habituation au capteur** (`max(0, S − α·S_lissé)`) : c'est une dérivée en moins lisible, elle détruirait tout le signal d'éloignement et rendrait l'odorat non-markovien
- Vérifier si la modification touche à la **détection de greffe dans `persistance.py`** (`greffe_detectee`) : elle ne doit **jamais** se fonder sur `missing_keys` seul. Une greffe **par recopie** — la règle du projet — ne produit aucune clé manquante (la couche existe, seule sa forme change), et l'optimiseur Adam restait alors chargé à l'ancienne largeur. Le symptôme est particulièrement traître : le crash ne survient **ni au chargement, ni pendant la journée, mais à la première `executer_nuit`**, donc invisible à toute vérification de type « N ticks post-résurrection ». Bug latent depuis la v29.0, corrigé en v32.0 en s'appuyant sur le drapeau retourné par la greffe elle-même. **Toute validation d'une greffe doit inclure une nuit complète**, pas seulement des ticks
- **Avant de rendre une constante ADAPTATIVE, l'instrumenter et la mesurer d'abord** (méthode posée en v30.1). Le projet bannit les chiffres arbitraires (voir le rêve adaptatif : `pourcentage_reve` émerge de la plasticité × richesse, jamais d'un batch fixe) — mais remplacer un chiffre arbitraire par une **formule** arbitraire ne vaut pas mieux, elle est juste plus difficile à remettre en cause. Une constante a été calibrée par cette méthode en v31.0 (`MemoireEpisodiqueSpatiale.capacite_max`, devenue `dim_bus × SOUVENIRS_PAR_DIM × (1 + déficit_bio)` après lecture des métriques `Memoire_*`). Il en reste une, instrumentée et en attente de données : `EXTENSION_PATIENCE_SURSAUT = 50` (métriques `Sursaut_*`, dont `Sursaut_Taux_Victoire` qui doit trancher entre un renforcement « muscle » et une atténuation « habituation »). Ne pas écrire ces formules sans avoir lu les courbes d'un run long, et vérifier ensuite par empreinte à graine fixée que la mécanique adaptative fait **mieux** que le fixe, pas seulement « différemment »
- Vérifier si la modification touche au **`PROGRAMME` du cursus** (`PROGRAMME`, `VICTOIRES_REQUISES`, `TAUX_PROMOTION`, `FENETRE_PROMOTION`, `MIN_EPISODES_PROMOTION`, `historique_episodes_niveau`) : quatre invariants v35.0. (1) `niveau_actuel` est un **INDEX** dans `PROGRAMME` — changer la taille ou l'ordre de la liste **rétrograde silencieusement tous les `.brain` existants**. C'est pourquoi `persistance` remappe par `env_id` (la seule donnée non ambiguë) et affiche `🔀 Niveau remappé` ; toute nouvelle modification du programme doit conserver ce remappage. (2) La promotion a **deux voies en OU** — série de victoires (rapide, fragile) et taux de maîtrise (lent, robuste) : ne jamais supprimer la première, elle garantit qu'aucun cerveau ne régresse en vitesse de promotion. (3) `historique_episodes_niveau` **doit être vidé à chaque promotion** — un taux hérité d'un niveau plus facile promouvrait en chaîne sans que l'agent ait rien montré sur le nouveau. (4) La réussite d'un épisode se juge sur `recompense_env > 0`, **jamais sur `termine` seul** : `termine` vaut aussi True quand l'agent meurt dans la lave (`LavaGap`), et compter ça comme un succès promouvrait un agent qui se suicide vite. Le principe du programme est qu'**une seule compétence change entre deux paliers voisins** (`DoorKey-5x5` → `6x6` → `8x8` est la même tâche à trois échelles) — ne pas y insérer un niveau qui cumule plusieurs nouveautés
- Vérifier si la modification touche au **flux mnésique** (`_memoriser_si_saillant`, `rappel_le_plus_marquant`, `enregistrer_evenement`, `SEUIL_SAILLANCE_MEMOIRE`, `SOUVENIRS_CONFIRMATIONS_REFERENCE`, `DIM_RAPPEL_MARQUANT`) : cinq invariants v36.0. (1) **Rien n'est expliqué en dur** — le cerveau ne sait pas ce qu'est une clé ni une pomme. Les étiquettes de souvenirs sont dérivées de l'API MiniGrid et restent **opaques** : il ne doit exister nulle part de table du type `lave = danger` ou `clé = utile`. La valeur d'un type est **apprise** (moyenne des chocs dans `valence`), jamais déclarée — c'est ce qui distingue ce mécanisme d'un système expert. (2) **Pas de routeur centralisé** — les mémoires ne sont pas des destinations qu'un aiguilleur choisit, elles **sont** les filtres, en parallèle. Un routeur unique en amont serait un goulot et un point de défaillance ; le chantier consiste à enrichir le flux, jamais à le centraliser. (3) **La récurrence produit de l'abstraction** : un doublon n'est jamais jeté, il incrémente `confirmations` et affine `valence`. Avant la v36.0, 98,6 % du flux était rejeté par déduplication — c'était la matière première de l'abstraction mise à la poubelle. (4) **L'oubli est un archivage post-abstraction** : l'éviction retire le repère le **moins confirmé** (à égalité, le plus ancien), jamais le plus ancien tout court. Une régularité du monde survit, un accident se dégrade. (5) Le neutre du rappel marquant est **`[0.5, 0.0]`**, jamais `[0.0, 0.0]` : une valence à 0.0 signifierait « le pire souvenir possible » et rendrait l'agent craintif partout où il n'a rien vécu (même piège que la clinotaxie v32.0)
- Vérifier si la modification touche à l'**érosion nocturne** (`cycle_sommeil`, `PLANCHER_POIDS_VITAL`, `FRACTION_NORME_MIN_COUCHE`, `norme_naissance`) : deux invariants v34.0-fix1/fix2, posés après un bug qui a rendu un cerveau **entièrement aveugle et sourd** (8 couches sur 11 à zéro exact après 1500 nuits). (1) L'érosion est **géométrique** (`base *= 1 − λ(1 − myéline)`) et la myéline ne peut venir **que** du gradient : un agent sans récompense ne myélinise rien, donc s'érode à taux plein et meurt en ~121 nuits. Le plancher vital est ce qui l'en empêche — ne jamais le retirer « parce qu'il ne sert jamais » : mesuré, **6 couches sur 11 y sont collées** sur un run réel. (2) `norme_naissance` ne doit **jamais rétrécir** : `agrandir()` recopie des poids déjà érodés, donc la norme du tenseur agrandi peut être plus petite que l'originale — d'où le `torch.maximum`. Sans lui, chaque neurogenèse divisait la protection par ~7 et le correctif s'auto-annulait. ⚠️ `SEUIL_CRISTAL = 0.80` n'a **jamais** été franchi (myéline réelle max mesurée : **0.0038**) : la Cristallisation Souple v26.0 ne s'est enclenchée sur aucun cerveau du dépôt — ne pas s'appuyer dessus comme protection. **Trois invariants supplémentaires en v37.0**, posés après un bug qui rendait l'apprentissage des deux têtes de décision *mathématiquement impossible* : (3) **le plancher vital ne doit jamais devenir un plafond** — la remontée est `torch.clamp(norme_plancher / norme_apres, min=1.0)`, jamais une renormalisation sèche à `norme_plancher`. La v34.0 ramenait la couche à *exactement* 10 % depuis la norme post-érosion, ce qui effaçait chaque nuit tout ce que le gradient venait de consolider (mesuré sur `tete_motrice` : 0,319490 → +0,0139 d'annexe → **0,319490**, au millionième). (4) **La myéline doit être rafraîchie en tête de `cycle_sommeil`**, jamais seulement dans `forward()` : la séquence nocturne est `apprendre_journee` (step) → `rever` (step) → `cycle_sommeil`, et aucun `forward` n'a lieu entre le dernier pas d'optimiseur et l'érosion — la myéline qui protège une couche ignorait donc systématiquement tout ce qu'elle venait d'apprendre (mesuré : **0.000000 exact** sur `tete_motrice` et `cortex_prefrontal` après 600 jours). L'invariant « la myéline ne vient que du gradient » est **intact** : seul le *moment* de la lecture change. (5) **L'échelle de la myéline est RELATIVE à la couche** (`echelle_myeline`, 3ᵉ quartile de `myeline_M`), jamais absolue — `q_ref = 1.0` supposait une myéline d'ordre 1 alors qu'elle vaut ~0,002, soit une échelle **500× trop grande** : `myeline_norm` restait collée à 0 et *toute* couche s'érodait au taux plein, myélinisée ou non. Prendre le **quantile et non le maximum** : normaliser par le max fait porter l'échelle par une seule synapse extrême et écrase les 99 % restantes (mesuré : p50 = 0,027, p99 = 1,000). C'est exactement le défaut de `SEUIL_CRISTAL` — une échelle absolue posée a priori, jamais confrontée à une mesure. ⚠️ **La norme d'une couche est un mauvais indicateur d'apprentissage** : `tete_motrice` reste à 10,00 % en norme tout en modifiant **7,43 % de ses poids en 5 nuits** (cosinus 0,9972) — sa consolidation fait *baisser* la norme parce que le gradient corrige les poids au lieu de les grossir. Toujours vérifier la direction (cosinus), pas seulement la magnitude
- Vérifier si la modification touche à l'**empreinte de type** (`empreinte_types`, `_nourrir_empreinte`, `valence_de_type`, `reinitialiser_niveau`) : **trois invariants v39.0**, posés après la mesure que 11 cerveaux sur 12 avaient **exactement zéro** repère `goal` (run instrumenté : 4 repères écrits, 3 promotions, 0 survivant, 0 jamais confirmé une seule fois). (1) **`reinitialiser_niveau` efface le OÙ, jamais le QUOI** : les coordonnées `(x,y)` sont périmées au changement de carte et doivent partir, mais `empreinte_types` — la valence apprise par *type* — n'a rien de spatial et survit. Le repère du but naît **au tick de la victoire**, donc juste avant la promotion qu'il déclenche : tout effacer revenait à faire oublier à l'agent ce qu'il venait de démontrer. (2) **L'empreinte se nourrit à l'écriture ET à la confirmation** — ne pas la limiter aux premières impressions, c'est la récurrence qui produit l'abstraction (v36.0). (3) **Rien n'y est déclaré** : aucune table `objet → valeur`, seulement la moyenne des chocs réellement vécus sur une étiquette opaque ; `_nourrir_empreinte` ne doit jamais tester le contenu de `type_evenement`. L'empreinte est sérialisée dans le `.brain` et rechargée par `.get(..., {})` — un `.brain` antérieur repart avec une empreinte vierge, sans greffe ni erreur (vérifié sur un cerveau de 600 jours, 3 nuits complètes)
- Vérifier si la modification touche à la **mémoire par carte** (`basculer_carte`, `archives_cartes`, `total_souvenirs`, `carte_courante`) : **quatre invariants v41.10**, posés après la mesure que la mémoire spatiale tournait à **1 % de sa capacité** (`5/200 souvenirs — 51 715 doublons évités`) parce que P17 l'effaçait **~3750 fois par run**. (1) **Quitter une carte n'est pas la perdre** : la bascule ARCHIVE, elle ne détruit pas. Avant P17 les deux coïncidaient (un pointeur qui ne recule jamais ne revient jamais) ; P17 a invalidé cette hypothèse — c'est le piège à ne pas réintroduire à chaque nouvelle mécanique de cursus. (2) **L'invariant v39.0 est RENFORCÉ, pas affaibli** : une coordonnée n'est jamais lue hors de sa carte d'origine, puisque seule la liste de la carte courante est exposée sous `souvenirs`. Toute modification doit conserver le test de fuite (un repère de A invisible depuis B). (3) **`len(souvenirs)` ne mesure plus le vécu** — il ne compte que la carte courante : utiliser `total_souvenirs()` pour toute télémétrie, sinon on reproduit exactement la fausse alerte « mémoire à 1 % » qui a motivé le correctif. (4) **`reinitialiser_niveau` est conservée** comme témoin d'ablation (`--sans-memoire-cartes`) et pour un vrai déménagement — ne pas la supprimer, mais ne pas la rebrancher sur le chemin des bascules fréquentes. `archives_cartes` et `carte_courante` sont sérialisées avec lecture défensive `.get()` ; un `.brain` antérieur repart avec sa seule carte courante, sans greffe (vérifié sur une nuit complète)
- Vérifier si la modification touche à la **thermoception** (`DIM_THERMOCEPTION`, `TYPES_BRULANTS`, `lire_thermoception`, `_chaleur_precedente`) : **quatre invariants v41.11**, posés après quatre mesures convergentes — MiniGrid punit la mort par **exactement `0.0`** (206 morts sur 300 épisodes ; toucher un mur coûte `-0,01`, donc **infiniment plus cher que mourir**) ; le vecteur bio était **rigoureusement identique** sur la case adjacente à la lave et à trois cases de là ; la lave figurait dans `TYPES_BLOQUANTS_ODORAT` donc **arrêtait** l'odeur sans jamais en **émettre** ; la vue la voit comme un symbole discret parmi d'autres. (1) **Le danger est un CHAMP CONTINU, jamais un malus conditionnel** : ne pas réintroduire `si mort → récompense -= X`, ce serait un seuil en dur sur un type nommé, exactement ce que l'invariant v36.0 interdit. L'agent doit découvrir ce que valent ces deux scalaires par ce qui lui arrive quand ils montent. (2) **La chaleur RAYONNE depuis les cases brûlantes** (franchissables comme points de départ du BFS), mais les **murs font de l'ombre thermique** — un gradient qui traverserait une cloison serait pire que pas de gradient, même raison qu'en v32.0 pour l'odorat. (3) **Le neutre est ASYMÉTRIQUE** : chaleur `0.0` (absence de danger, pas une inconnue) mais variation `0.5` (0.0 signifierait un refroidissement maximal, donc une fuite permanente devant un feu inexistant — même piège que la clinotaxie v32.0 et le rappel marquant v36.0). `_chaleur_precedente` **doit** repartir à `None` dans `reinitialiser_episode`. (4) **Toute tranche du vecteur sensoriel doit être bornée en HAUT** : `deltas_odorat` était une tranche ouverte `[début:]` qui aurait avalé les 2 dims thermiques — c'est le défaut dont la v32.0 avertit déjà pour l'Exo-Sens, et il se reproduit à chaque ajout en queue. Le nom `lava` n'apparaît QUE dans `bus_sensoriel.py` (traduction sensorielle, au même titre que `red`/`blue` pour nourriture/eau depuis la v29.0) — **jamais** dans `noyau.py`, qui ne reçoit que deux nombres
- Vérifier si la modification touche à la **nociception thermique** (`calculer_deficit`, `BiologicalHomeostasisEngine.chaleur`, `chaleur_seule`, `_champ_thermique`, `DOULEUR_THERMIQUE_ACTIVE`) : **quatre invariants v41.25**, posés après la mesure que la valence apprise de la lave était **positive** (`+0,059` à `+0,066`, soit celle de l'eau) sur 17 graines × 2000 jours — MiniGrid punit la mort par **exactement `0.0`** quand un mur coûte `−0,01`, donc **mourir était infiniment moins cher que se cogner**. (1) **La douleur est un DÉFICIT, jamais une pénalité** : la chaleur entre dans `calculer_deficit` comme un quatrième manque (`+ chaleur**2`), au même titre et à la même échelle que la faim. Ne **jamais** réintroduire `si mort: récompense −= X` — ce serait un seuil en dur sur un type nommé, exactement ce que l'invariant v41.11 interdit. Aucun coefficient n'est posé : `(1−x)²` et `T²` sont tous deux dans [0,1] **par construction**, et c'est `lambda_diffusion_carte` (dérivé des dimensions de la carte) qui règle seul la pente. (2) **La douleur se facture LÀ OÙ LE CORPS EST ARRIVÉ** : la thermoception est lue en tête de tick, donc AVANT `env.step`, alors que `step_metabolisme` s'exécute APRÈS. Sans la relecture post-step, l'agent qui marche dans la lave paie la température de la case **quittée** (~0,457) et, l'épisode se terminant aussitôt, **ne ressent JAMAIS `T=1`** — le signal le plus important du mécanisme serait précisément celui qui n'arrive pas. C'est le décalage temporel corrigé en v41.5 sur la maturité, reproduit pour la même raison : une grandeur lue en tête et consommée en queue traverse un `env.step` qui l'a périmée. (3) **La relecture passe par `chaleur_seule()`, JAMAIS par `lire_thermoception()`** : cette dernière écrit `_chaleur_precedente`, donc un second appel dans le même tick ferait comparer deux mesures séparées par un demi-tick et **diviserait par deux la clinotaxie** du tick suivant — le signal d'approche, seul moyen d'apprendre à FUIR, faussé en silence. Le BFS est partagé via `_champ_thermique` pour que les deux lectures ne puissent pas diverger. (4) **Ne jamais mesurer ce mécanisme sur le cursus normal** : la lave n'apparaît qu'au niveau 5 (`LavaGapS5`) et l'agent est bloqué au 4, donc la chaleur moyenne y vaut **0,001 (1 tick actif sur 400)**. Un A/B lancé là comparerait deux bras dont le terme mesuré est nul dans **99,7 %** des ticks — une ablation **VIDE**, pas négative (§4 de la règle de mesure). Utiliser `--env-force MiniGrid-LavaGapS5-v0` (banc, 300-400 ticks actifs / 400) et `--sans-douleur` comme témoin — un témoin qui garde le **sens** identique et ne coupe que la **douleur**, ce qui isole la boucle nociceptive du capteur lui-même
- Vérifier si la modification touche au **silence auditif** (`_tronc_cerebral`, branche `obs_auditive is None`) : `porte_auditive` est **sans biais**, donc `relu(porte_auditive(zeros))` vaut **0 exactement** et la norme du bus est **identique** avec ou sans le terme (6,3323, écart 0,0000 — mesuré). ⚠️ Ne pas répéter l'erreur du CHANGELOG v38, qui affirmait que « la norme change » : c'est faux. Le vrai défaut est qu'**un silence parfait et une oreille absente sont mathématiquement indiscernables**. La v39.0 rend seulement ce défaut explicite (correctif **bit-identique**) ; sa levée réelle exige un **bit de présence** dans le vecteur bio, donc une dimension de plus **en queue** et une greffe `persistance` — chantier à part entière, à ne pas bricoler dans la branche `else`
- Vérifier si la modification touche à la **rétrocompatibilité des `.brain`** (`persistance.py`) : la règle générale est **greffe par recopie, jamais par exclusion**. Exclure une couche sur mismatch de forme la fait renaître à neuf et détruit des centaines de jours d'acquis (bug v24.0-fix4, symptôme : bouche silencieuse dans l'Arène). Les deux greffes existantes — `_greffer_action_supplementaire` (7→8 actions, v28.0) et `_greffer_vecteur_bio_etendu` (vecteur bio 16→24, v29.0) — sont le modèle à suivre ; le filtre d'exclusion ne reste qu'en trappe de secours pour les mismatchs qu'on ne sait pas greffer
- Après toute modification des hyperparamètres de la section 4, vérifier la cohérence avec le [README](readme_fr.md) (tableau `config.py` narratif, formules) et mettre à jour la documentation si les valeurs divergent
- Ce script est prévu pour tourner sur GPU si disponible (`DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")`) — ne pas supposer un device fixe, toujours passer par `DEVICE` ou `.to(DEVICE)`

## Essential Commands

Pas de build au sens classique, mais le projet est un package Python (`src/naulthene/`) — tout lancement se fait **depuis la racine du dépôt**, avec `PYTHONPATH=src` et l'option `-m` (jamais `python <fichier>.py` directement) :

```bash
pip install torch gymnasium minigrid wandb numpy
PYTHONPATH=src python -m naulthene.cerveau.colab
```

Autres points d'entrée du même écosystème (voir [Architecture](#architecture) et [docs/fonctionnement/LANCEMENT.md](docs/fonctionnement/LANCEMENT.md) pour le guide complet) :

```bash
PYTHONPATH=src python -m naulthene.cerveau.noyau                              # terrain d'essai local (Mac)
PYTHONPATH=src python -m naulthene.cuve.daemon_cerveau --port 9999            # la Cuve (serveur persistant)
PYTHONPATH=src python -m naulthene.cuve.client_corps --port 9999              # client MiniGrid
PYTHONPATH=src python -m naulthene.salles_de_classe.cursus_developpemental    # Cursus par Ères (1000 jours, standalone)
PYTHONPATH=src python -m naulthene.instruments.lancer_arene                   # observer un cerveau entraîné
```

### Convention de nommage des cerveaux (`brains/*.brain`, depuis v30.0)

Tout nouveau cerveau produit par un run suit ce format — **un fichier par run**, jamais un chemin
générique réutilisé d'un run à l'autre :

```
DDMMYYYYHHMM_VXX_NMRTOUR_RMD.brain
└──────┬───┘ └┬┘ └───┬──┘ └┬┘
       │      │      │     └── RMD : initiales / identifiant du run
       │      │      └──────── nombre de jours (tours) demandé au lancement
       │      └─────────────── version de l'architecture au moment du run
       └────────────────────── date+heure de lancement (jour mois année heure minute)
```

Exemple : `020820261304_V30_700_RMD.brain` — run lancé le 2 août 2026 à 13h04, architecture
v30.0, 700 jours demandés.

- **L'horodatage est celui du LANCEMENT**, jamais mis à jour ensuite : le fichier est écrasé à
  chaque nuit par `PersistanceAnatomique.sauvegarder()`, mais son nom garde la trace du départ du
  run. Générer la date avec `date "+%d%m%Y%H%M"`.
- **`VXX` est la version de l'architecture**, pas celle du fichier : un `.brain` v29 rechargé par
  un binaire v30 est greffé automatiquement (voir `_greffer_vecteur_bio_etendu`) mais **garde son
  nom d'origine** — c'est la trace de sa naissance, pas de son état courant.
- Les cerveaux d'une génération antérieure sont rangés dans un sous-dossier
  `brains/old_VXX/` (ex. `brains/old_V30/` contient tout ce qui précède la v30.0). **Toujours
  archiver, jamais supprimer** : un `.brain` représente des centaines de jours de run.
- `brains/**/*.brain` est gitignoré, sous-dossiers d'archive compris — vérifier avec
  `git check-ignore -v <chemin>` après avoir créé un nouveau sous-dossier.
- Les trois cursus acceptent `--brain <chemin>` (ajouté en v30.0) ; le dossier parent est créé
  automatiquement s'il n'existe pas. Sans ce flag, ils retombent sur leur chemin historique
  (`brains/naulthene_cursus.brain`, `naulthene_bb.brain`, `naulthene_parole.brain`) — utile pour
  reprendre un ancien run, mais **ne pas s'en servir pour un nouveau run** : deux runs partageant
  le même fichier s'écrasent mutuellement.

```bash
# Nouveau cerveau, 700 jours, convention de nommage complète
WANDB_MODE=offline PYTHONPATH=src python -m naulthene.salles_de_classe.cursus_developpemental \
    --jours 700 --brain "brains/$(date +%d%m%Y%H%M)_V30_700_RMD.brain"
```

`wandb.init(project="Naulthene-AGI", ...)` demande une session W&B active (login `wandb login` au préalable, ou variable d'environnement `WANDB_API_KEY`) — sans clé configurée, W&B tombe en mode anonyme ou local selon la config de l'environnement.

Il n'y a ni linter ni suite de tests automatisés configurés. Toute vérification passe par l'observation des logs console (progression de palier, teneur en dopamine, thermostat de neurogenèse) et des courbes du tableau de bord W&B (voir [Modèle de Données & Métriques W&B](readme_fr.md#modèle-de-données--métriques-wb) dans le README).

## La Règle de Mesure — « rien sans témoin »

> **Règle jumelle de « rien en dur ».** Celle-ci gouverne la conception ; celle-là gouverne
> ce qu'on a le droit de conclure. Posée le 16/08/2026 après une nuit entière de
> comparaisons qui ne mesuraient rien.

**Aucune conclusion sans avoir vérifié que le test pouvait la produire.**

### 1. Le test A/A avant tout test A/B

Avant de comparer une version A à une version B, lancer **A contre A** — deux runs
identiques, même graine, même code.

- Si les deux A **diffèrent** autant que A et B diffèrent, **le test ne mesure rien**.
- Ce contrôle coûte cinq minutes et invalide des nuits de calcul.

C'est ainsi qu'a été découvert le défaut de reproductibilité v41.9 : `env.reset()` n'était
jamais seedé, MiniGrid tirait ses cartes sur l'entropie système, et deux runs de même
`--graine` voyaient des mondes différents. **Toutes les comparaisons appariées du projet
antérieures à la v41.9 sont donc non concluantes** — elles ne sont pas fausses, elles
n'établissent rien.

### 2. La taille d'échantillon — ne jamais conclure sous 20 graines

Mesuré le 16/08 : le taux de franchissement de référence vaut **40 % avec un intervalle de
confiance à 95 % de [22 % ; 61 %]** sur 20 graines.

| Échantillon | Intervalle de confiance | Ce qu'on peut détecter |
|---|---|---|
| 6 graines | ± ~30 points | **rien** |
| 20 graines | ± ~20 points | un effet qui double le taux |
| 40 graines | ± ~14 points | un effet de +50 % |

Trois campagnes de 6 graines menées la même nuit ont donné 33 %, 50 % et 33 % : **les trois
tombent dans l'intervalle du taux de base**. Aucune ne mesurait un effet, et j'ai
interprété leurs écarts pendant des heures avant de le calculer.

> ⚠️ **Interdit** : conclure « cette version est meilleure » sur moins de 20 graines.
> **Obligatoire** : donner l'intervalle de confiance à côté de chaque taux, jamais le taux
> seul.

### 3. Se méfier des résultats qui font plaisir

Deux réflexes qui ont chacun débusqué un bug réel :

- **Un résultat trop propre est suspect.** Trois runs rigoureusement identiques, une
  valence à `0.000` exact, un delta de `+0,0` sur toutes les cellules : c'est presque
  toujours un canal débranché, pas une découverte. (v41.4 : le drapeau d'ablation
  n'atteignait pas le module ; v41.7 : la valence de la nourriture ne recevait que des
  zéros sur 4004 repas.)
- **Un résultat favorable se vérifie deux fois plus qu'un défavorable.** La promotion la
  plus précoce jamais observée (jour 23) s'est révélée être du bruit une fois l'intervalle
  calculé.

### 4. Distinguer trois natures de résultat

| Nature | Fiable ? | Exemple |
|---|---|---|
| **Mesure directe** (lecture d'un `.brain`, statistique intra-run) | ✅ oui | `'FOOD' +0.000` sur 4004 repas |
| **Comparaison appariée** (A vs B, mêmes graines) | 🟡 seulement depuis la v41.9, et à n ≥ 20 | héritage ON/OFF |
| **Anecdote** (une graine, un run) | ❌ jamais | « g22 promue au jour 23 » |

Une ablation dont le témoin est à zéro ne mesure rien : distinguer une ablation
**négative** (mesurée à 0) d'une ablation **vide** (jamais activée).

---

## Format de Rapport — 3 / 3 / 3

⚠️ **UNIQUEMENT SUR DÉCLENCHEUR** (règle posée le 16/08/2026). Ce rapport est le compte
rendu d'une session **en autonomie**, jamais un gabarit de réponse ordinaire.

| L'utilisateur dit… | Réponse |
|---|---|
| « **bonne nuit** », « **à toute** », « **Acti.333** » | le rapport 3/3/3 complet |
| tout le reste | **réponse normale**, sans le format |

**Quand le déclencheur est donné, produire :**

### ✅ 3 avancées
Ce qui a progressé, **chiffré**. Une avancée sans chiffre n'est pas une avancée.

### ⛔ 3 retards
Ce qui a bloqué, échoué, ou été découvert comme cassé — **y compris mes propres erreurs**.
Un rapport sans retard est un rapport incomplet : sur ce projet, les défauts trouvés dans
le banc d'essai ont plus fait avancer que les mécaniques ajoutées.

### 💡 3 améliorations
Ce qu'il faudrait faire ensuite, **classé par ce que la mesure justifie**, pas par ce qui
est le plus intéressant à coder. Distinguer ce qui est arbitré de ce qui attend une
décision utilisateur.

> Si l'une des trois catégories est vide, le dire explicitement plutôt que de la remplir
> artificiellement.

---

## Git Workflow

### État des branches (2026-08-15)

| Branche | Contenu | État |
|---|---|---|
| `master` | tout le cycle **v28 → v38** (Port C3, Bus Sensoriel, Exo-Sens, odorat topologique, mémoire proportionnelle, extinction synaptique, cursus à 15 niveaux, flux enrichi, équilibre C1/C2, monde continu) | intégrée, poussée |
| **`feat/v41-ligne-flottaison`** | **branche de travail courante** — v39 → v41.2, **48 commits d'avance sur `master`**, dont **15 non poussés** | ⚠️ **non mergée** |
| `feat/v39-…`, `feat/v40-…`, `feat/v40.1-…` | étapes intermédiaires du même cycle | conservées pour l'historique |
| `feat/v28-…` → `feat/v38-…` | branches déjà mergées dans `master` | conservées pour l'historique |

Le travail en cours se fait sur **`feat/v41-ligne-flottaison`**. Ce qu'elle porte et que
`master` **n'a pas encore** :

- **v39.0** — `noyau.py` versionné (risque structurel n°1 levé) ; empreinte de type ; silence auditif rendu explicite (correctif bit-identique)
- **v40.0/v40.1** — planification émergente : 3 constantes d'arbitrage supprimées, **9 branches `if` éliminées** du chemin cognitif, 3 interrupteurs cognitifs rendus continus
- **v41.0** — la **ligne de flottaison métabolique** : le vécu se compte en saillances au-dessus du coût d'exister, plus en moyenne
- **v41.2** *(en cours, non entrée au CHANGELOG)* — métabolisme à deux étages, `vigueur = énergie ** κ` comme modulateur global unique, profil nutritionnel à 3 axes

⚠️ **Deux résultats de cette branche contredisent des affirmations antérieures** — les avoir en
tête avant toute nouvelle piste : la campagne de 10 graines donne **0 promotion** (le niveau 4 de
g22 était une **loterie natale**), et **couper C2 ne change le score de 0,0 point sur les 6
niveaux**. Voir `docs/recherche/CAMPAGNE_v41_population_et_ablation_aout_2026.md`.

Décisions structurantes toujours en vigueur depuis la v30 : `num_actions` **reste à 8** avec
`ACTION_DEMANDER` masquée en permanence (ne jamais amputer un `.brain`), toute dimension du
vecteur bio s'ajoute **en queue**, et l'Exo-Sens est perçu **en continu sans aucun seuil de
déclenchement**.

- Ne créer un commit que si l'utilisateur le demande explicitement
- Toujours créer un nouveau commit plutôt qu'un `--amend`, sauf demande contraire
- Ne jamais `push --force`, `reset --hard` ou sauter les hooks (`--no-verify`) sans autorisation explicite
- Un commit qui modifie `src/naulthene/cerveau/colab.py` de façon significative (nouvelle mécanique, changement d'hyperparamètre structurant, nouvelle section) doit s'accompagner de la mise à jour de `docs/fonctionnement/CHANGELOG.md` et, si le changement est narrativement significatif, de `readme_fr.md` — voir [Maintenance du Changelog](#maintenance-du-changelog)

## Maintenance du Changelog

**OBLIGATOIRE** : à chaque commit modifiant `src/naulthene/cerveau/colab.py` de façon significative, mettre à jour les fichiers suivants.

### 1. `docs/fonctionnement/CHANGELOG.md`

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

### 2. `readme_fr.md`

- Mettre à jour la ligne `#Version actuelle N.` en tête de `src/naulthene/cerveau/colab.py` si la version change
- Ajouter une nouvelle section "Nouveautés vX.X — Titre" en haut du Journal des Mises à Jour si le changement est significatif (feat / fix majeur), et mettre à jour la table des matières en conséquence
- Ne pas toucher aux sections narratives (architecture, formules) pour des commits `docs` / `chore` mineurs

⚠️ Si le changement touche l'**en-tête** de `readme_fr.md`, la **règle de miroir** s'applique
(voir [Projet Overview](#la-règle-de-miroir--readmemd-en--readme_frmd-fr)) : `readme.md` doit
être modifié **dans le même commit**.

### 3. Les cinq dossiers de `docs/` (réorganisés le 2026-08-14)

**Point d'entrée : [`docs/INDEX.md`](docs/INDEX.md)** — il dit quelle question mène à quel
document. Tout nouveau document doit y être ajouté, sinon il sera oublié.

| Dossier | Nature | Fait autorité sur l'état courant ? |
|---|---|---|
| `docs/fonctionnement/` | **normatif** (CHANGELOG, LANCEMENT, explications) | ✅ oui |
| `docs/recherche/` | **enquêtes** — investigations, hypothèses réfutées | ❌ non |
| `docs/ameliorations/` | **idées** proposées, non validées | ❌ non |
| `docs/ameliorations_appliquees/` | **livré** dans le code | 🟡 partiellement |
| `docs/etat_des_lieux/` | **synthèses datées** — une photo à un instant donné | ❌ non (**périmable**) |

Un document d'`etat_des_lieux/` est une **photo horodatée** (`DDMMYYYY_Version.md`), jamais
mise à jour après sa date : les anciennes sont **conservées**, jamais écrasées — c'est ce qui
permet de comparer deux dates.

Un document de `recherche/` est **vivant mais non normatif** : il raconte une
investigation, conserve les hypothèses réfutées et les erreurs de diagnostic. **Ne jamais
y chercher l'état courant** — c'est le rôle du CHANGELOG. Mais **toujours le consulter
avant de relancer une piste** : c'est ce qui évite de retester une idée déjà écartée.

`ameliorations_appliquees/` garde la trace des options **ÉCARTÉES** et de leurs raisons,
ce qu'aucun document à jour ne raconte — c'est ce qui évite qu'une idée déjà rejetée soit
réintroduite sans connaître l'argument qui l'avait écartée.

Procédure de déplacement : `git mv` (jamais `mv` seul) et correction de **tous** les liens
entrants — README (FR **et** EN, règle de miroir), `CLAUDE.md`, les autres docs, **et les
docstrings du code source**. Vérifier ensuite qu'aucun lien ne pointe dans le vide.

### 4. Où ranger un document

Un document rejoint `ameliorations_appliquees/` quand sa mécanique est **livrée et
documentée ailleurs** — jamais parce qu'il est simplement « vieux ». Une idée non encore
testée reste dans `ameliorations/`. Voir §3 pour les cinq dossiers et la procédure.

### Règles de versioning

| Type de commit | Incrément version | Exemple |
|----------------|-------------------|---------|
| `feat` (nouvelle mécanique cognitive) | +1.0 | 13.0 → 14.0 |
| `fix` critique / `perf` majeur | +0.1 (suffixe `-fix1`) | 10.0 → 10.0-fix1 |
| `fix` mineur / `refactor` / `docs` | même version + suffixe | 14.0-fix1, 14.0-docs |
| `chore` / `style` | pas d'incrément | - |

Le script de référence `src/naulthene/cerveau/colab.py` est actuellement en version **17** (voir `readme_fr.md`, table des matières et journal des mises à jour). `src/naulthene/cerveau/noyau.py` porte en plus toutes les mécaniques expérimentales non encore portées sur `colab.py` (actuellement jusqu'à **v37.0/v37.1** — l'Équilibre C1/C2 & la Distillation Sélective — en passant par v36.0 le Flux Enrichi & l'Abstraction par Récurrence, v35.0/v35.1 le Cursus Progressif à 15 niveaux, le Guidage Dégressif & le Filet de Sécurité, v34.0-fix1/fix2 le correctif d'Extinction Synaptique, v32.0 l'Odorat Topologique & la Clinotaxie, v31.0/v31.1 la Mémoire Proportionnelle, le Rêve Invariant d'Échelle & la Déduplication Mnésique, en passant par v18.0 Architecture Homéostatique Biologique, v22 Hémisphère Auditif & Vocal, v27.x École de la Parole, v28.0 Cascade C1→C2→C3 & Port Exocortex, v29.0/v29.1 Bus Sensoriel & télémétrie des 5 sens, v30.0/v30.1 Odorat Dynamique, Exo-Sens & instrumentation, voir [Variante Locale de Test](#variante-locale-de-test-mac--srcnaulthenecerveaunoyaupy) et `readme_fr.md`/`docs/fonctionnement/CHANGELOG.md` pour le détail) — toute nouvelle mécanique testée localement suit la même échelle de version que le script de référence, marquée `-experimental` tant qu'elle n'y est pas portée. Poursuivre sur cette échelle entière (+1.0 pour la prochaine mécanique majeure) sauf décision contraire de l'utilisateur.
