# CLAUDE.md

Instructions de travail pour Claude Code sur le projet **Naulthène AGI** — agent cognitif autonome hybride (RL + JEPA + mémoire épisodique + homéostasie neuro-mimétique), entraîné sur un cursus scolaire d'environnements MiniGrid à complexité croissante.

## Projet Overview

Naulthène AGI est un projet de recherche (packagé en `src/naulthene/`, cœur de référence pensé pour tourner sur Google Colab) qui explore une architecture cognitive bio-inspirée plutôt qu'un pipeline RL classique. L'agent (`AGI_Naulthene`, `nn.Module`) combine :

- Un **modèle du monde JEPA** (Joint Embedding Predictive Architecture) qui prédit l'état latent suivant plutôt que l'observation brute (`generateur_attente`, `perte_jepa`)
- Un **Système 1** instinctif (tête motrice Acteur-Critique classique) et un **Système 2** délibératif qui simule mentalement les conséquences de ses actions sur un horizon de plusieurs pas (`simuler_futur_et_planifier`) avant de arbitrer entre les deux — nommés explicitement **C1** (réflexe) et **C2** (néo-cortex) depuis la v29.0, C2 ne recevant jamais que l'état déjà compressé par C1
- Un **Bus Sensoriel multimodal** (`bus_sensoriel.py`, v29.0/v30.0) qui donne à l'agent les **5 sens** hiérarchisés par gourmandise énergétique : vue et ouïe (gourmands, chacun avec sa porte synaptique dans le bus latent et sa cible JEPA), puis toucher, odorat et goût (faibles à moyens, injectés en queue du `vecteur_bio` donc hors de la cible JEPA) — plus, depuis la v30.0, un **6ᵉ sens exogène** (l'**Exo-Sens**) : le monde numérique (LLM/RAG, APIs, IoT) perçu en continu via le Port C3, sans jamais être « interrogé » par une action
- Une **mémoire épisodique** de contexte (moyenne glissante des états latents récents de l'épisode, `vecteurs_episodiques`) et une mémoire tampon court terme (`hippocampe`)
- Un **réservoir dopaminergique homéostatique** ($D_t \in [0.001, 10.0]$) qui module la motivation et la plasticité synaptique en fonction des succès/échecs vécus dans la journée
- Une **plasticité structurelle** (`NaultheneLinearSynaptique`) : chaque couche a un poids de base figé et un poids "annexe" appris pendant la journée, consolidé (ou érodé) chaque nuit selon une trace de myéline — avec neurogenèse (ajout de dimensions) déclenchée par un thermostat d'erreur JEPA
- Une **consolidation nocturne (rêve)** à porosité adaptative : le pourcentage de souvenirs rejoués la nuit dépend de la plasticité du moment et de la richesse (importance moyenne) de la journée, pas d'une taille de batch fixe
- Des **détecteurs de progrès génériques**, agnostiques de la carte (franchissement de portes, records de proximité à l'objectif), en plus du détecteur de jalons spécifique à `DoorKey` (cursus à 7 paliers)

L'agent progresse à travers un **cursus académique** de **15 niveaux** MiniGrid (v35.0 — 5 avant), du Nourrisson (`Empty-5x5`) au Doctorat (planification longue distance), promu par **2 victoires consécutives OU 60 % de maîtrise sur une fenêtre glissante de 20 épisodes**.

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
│       └── irm_cerveau.py        scanner d'activations internes, ne modifie jamais le .brain
│
├── brains/                       cerveaux cristallisés (*.brain, gitignorés) — un fichier par run,
│   └── old_V30/                    nommé DDMMYYYYHHMM_VXX_NMRTOUR_RMD.brain (voir « Convention de
│                                   nommage des cerveaux ») ; old_VXX/ archive les générations
│                                   précédentes, jamais supprimées
└── docs/                         DOCUMENTS VIVANTS uniquement (4) :
    │                               CHANGELOG.md — historique version par version, la référence
    │                               factuelle ; LANCEMENT.md — toutes les commandes et le dépannage ;
    │                               Parcourt_readme.md — guide vulgarisé des 4 parcours ;
    │                               explications_readme.md — détail algorithmique et mathématique
    │                               (dont §15 : Bus Sensoriel, identité C1/C2, Exo-Sens)
    └── Old_Archive_rmd/          documents historiques : conceptions dont la mécanique est livrée
                                    (CONCEPTION_v22_audio, CONCEPTION_v30_exo_sens, Maj_V29_readme,
                                    EXPLICATIONS_v29_sens),
                                    plans partiellement réalisés (AMELIORATION_V1) et analyses de run.
                                    Précieux car ils gardent la trace des options ÉCARTÉES et de leurs
                                    raisons — mais ne jamais s'y référer pour l'état courant. Voir son
                                    README.md pour la convention d'archivage
```

Le cœur de référence est `src/naulthene/cerveau/colab.py` (ex-`agi_google_colab.py`, pensé pour tourner sur Google Colab). Structure interne (sections numérotées par des commentaires `# --- N. ... ---`) :

1. **Le Scalpel — Plasticité Structurelle** (`NaultheneLinearSynaptique`) : couche linéaire à poids base/annexe, cycle de sommeil (érosion + consolidation), et `agrandir()` pour la neurogenèse (extension des dimensions in/out sans perdre les poids appris)
2. **Le Cerveau C1 (Réflexe) & C2 (Néo-Cortex)** (`AGI_Naulthene`) — section renommée en v29.0, l'identité C1/C2 étant désormais explicite dans le code : tronc cérébral commun (`porte_visuelle` → `hippocampe` → `analyseur`), lecture épisodique, **C1** (`_executer_c1_reflexe` : compression des 5 sens, intégration viscérale, tête motrice / Système 1), **C2** (`_solliciter_c2_neocortex` → `simuler_futur_et_planifier`, JEPA / Système 2), `penser()` réduit à l'arbitrage des deux, apprentissage journalier (`apprendre_journee`, Acteur-Critique + JEPA), rêve (`rever`), cycle de sommeil global, neurogenèse (`declencher_neurogenese`)
3. **Cursus & Détecteurs** :
   - 3a. `DetecteurJalonsDoorKey` — spécifique à l'environnement `DoorKey`, 7 paliers cognitifs codés en dur sur cette carte
   - 3b. Détecteurs génériques actifs sur n'importe quel niveau : `DetecteurFranchissementPortes`, `DetecteurProgresPersonnel`
4. **Exécution & Cursus** : configuration W&B, hyperparamètres (dopamine, planification, rêve adaptatif), programme des niveaux (`PROGRAMME` — 15 depuis la v35.0, 5 dans `colab.py`), boucle principale jour/tick

Voir le [README](readme.md) pour la description narrative complète (formules d'homéostasie, tableau des 7 paliers, architecture cognitico-biologique en diagramme ASCII).

Tous les imports entre modules du package sont des **chemins absolus de package** (`from naulthene.cerveau.noyau import ...`, `import naulthene.audio.professeur_gemma as pg`) — jamais d'imports relatifs à plat. Tout script se lance depuis la **racine du dépôt** avec `PYTHONPATH=src` et l'option `-m` (voir [Essential Commands](#essential-commands)) ; les chemins `.brain` par défaut sont relatifs à cette racine (`brains/naulthene_*.brain`).

## Variante Locale de Test (Mac) — `src/naulthene/cerveau/noyau.py`

En plus du script de référence `colab.py`, le projet dispose d'une copie de travail **non trackée par git** (`src/naulthene/cerveau/noyau.py`, ex-`agi_local_test.py`, listée dans `.gitignore`) utilisée pour tester rapidement de nouvelles mécaniques sur Mac (Apple Silicon, device `mps`) avant de les porter — ou non — sur le script de référence.

- **Deux différences permanentes avec `colab.py`** : détection du device `cuda`/`mps`/`cpu` (au lieu de `cuda`/`cpu` seul) et un `jours_totaux` ajustable localement pour des runs de test plus courts que les 400 jours de Colab
- **C'est le terrain d'essai des mécaniques expérimentales** (actuellement v18.0 Architecture Homéostatique Biologique, v19.0 Métabolisme 20/80 & Forage 80/20, et toute mécanique suivante tant qu'elle n'a pas été validée sur un run long) — ces versions vivent **uniquement** dans ce fichier tant qu'elles ne sont pas explicitement portées sur `colab.py`. Exceptions notables : `exocortex/` (v28.0) et `cerveau/bus_sensoriel.py` (v29.0) sont des modules **versionnés** dans git, même si la mécanique qui les consomme n'existe pour l'instant que dans `noyau.py`
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
- Vérifier si la modification touche au **Bus Sensoriel / vecteur bio** (`src/naulthene/cerveau/bus_sensoriel.py`, `DIM_VECTEUR_BIO`, `DIM_TOUCHER`, `DIM_CHIMIE`, `obtenir_vecteur_bio`) : trois invariants v29.0. (1) `bus_sensoriel.py` reste **pur numpy** et n'importe **jamais** `noyau.py` — c'est ce qui garantit l'absence de cycle d'import, même discipline que `exocortex/port_c3.py`. (2) Toute nouvelle dimension du vecteur bio s'ajoute **EN QUEUE**, jamais au milieu : l'ordre de concaténation de `obtenir_vecteur_bio` est un contrat partagé avec `BusSensoriel.interpreter` et avec `persistance._greffer_vecteur_bio_etendu`, qui recopie les N premières colonnes d'un ancien `.brain` — une insertion au milieu décalerait silencieusement tous les acquis. (3) Les sens faibles (toucher, odorat, goût) n'entrent **jamais** dans `bus_latent` : ils passent par `integrateur_bio`, donc restent hors de la cible JEPA (`perte_jepa` compare toujours le bus prédit au bus réel de la **vision seule**). Ne pas leur donner de porte synaptique sommée dans le tronc cérébral sans demande explicite de l'utilisateur
- Vérifier si la modification touche à la **frontière C1/C2** (`_executer_c1_reflexe`, `_solliciter_c2_neocortex`, `penser`) : le découpage v29.0 est une **restructuration pure** (décision utilisateur explicite) — C2 est sollicité à chaque tick, exactement comme avant, et l'arbitrage `logits_instinct + valeurs_simulees * force_planification` est inchangé depuis la v13.0. Ne **pas** y introduire de court-circuit conditionnel ("C1 saute C2 s'il est confiant") sans demande explicite : ce serait un déclenchement sur seuil codé en dur dans le chemin de décision, de la même nature que ce que ce fichier interdit déjà pour l'appel à C3. C2 ne doit par ailleurs jamais recevoir autre chose que l'état déjà compressé par C1 (`pensee_bio`) — jamais l'observation brute, jamais l'environnement
- Vérifier si la modification touche à l'**Exo-Sens** (`DIM_EXO`, `percevoir_exogene`, `_rafraichir_perception_exogene`, `PERIODE_PERCEPTION_EXO`, `ReponseC3.perception`) : quatre invariants v30.0. (1) L'Exo-Sens est une **perception continue**, jamais une action ni un déclenchement — ne **pas** y réintroduire de seuil (« si l'erreur JEPA monte, interroger C3 ») : c'est ce que le projet a refusé trois fois (v28 pour l'appel à C3, v29 pour le court-circuit C1→C2, v30 pour cette boucle d'attention). L'attention accordée aux 8 dims doit émerger de la myélinisation de `integrateur_bio`. (2) `ACTION_DEMANDER` reste masquée à `-inf` **en permanence** et `num_actions` reste à 8 — la colonne est dormante mais jamais amputée (4 `.brain` du dépôt sont à 8 actions). (3) `percevoir_exogene` **clippe toujours** dans [0,1] et rejette un vecteur de mauvaise taille : un service externe n'est pas maîtrisé, et une dimension hors échelle écraserait `integrateur_bio`. Un Exo-Sens invalide ne doit **jamais** désactiver les 5 sens physiques (avertissement séparé, voir `_avertir_exo`). (4) Le bus n'est interrogé qu'un tick sur `PERIODE_PERCEPTION_EXO` avec mise en cache — un plug HTTP à 100 ms-30 s rendrait sinon impraticable un run de 120 000 ticks
- **Toute nouvelle mécanique observable doit être instrumentée dans le même commit** (leçon de la v29.1) : un compteur remis à zéro dans `_reinitialiser_buffers_journee`, accumulé dans `traiter_tick`, puis agrégé dans `executer_nuit` (ligne du bilan console **et** clé dans le dict `log_wandb` retourné). Sans cela, la mécanique est invisible sur un run long et son utilité réelle indémontrable — la v29.0 avait livré les 5 sens sans aucune télémétrie, écart corrigé en v29.1. Deux règles : ne jamais créer un compteur journalier par `getattr(etat, "...", 0)` sans l'ajouter à `_reinitialiser_buffers_journee` (piège du bug `score_vocal_jour` v27.0, où la « moyenne du jour » cumulait depuis la naissance), et rendre les clés **conditionnelles** quand la mécanique peut être inactive (voir les blocs `Sens_*` et C3), plutôt que de logger des zéros trompeurs
- Vérifier si la modification touche à la **capacité mnésique** (`MemoireEpisodiqueSpatiale.ajuster_capacite`, `SOUVENIRS_PAR_DIM`, `capacite_plancher`) ou au **facteur de richesse du rêve** (`reference_richesse`, `empreinte_enfance`) : trois invariants v31.0. (1) La capacité est recalculée **une fois par nuit**, jamais par tick — une capacité fluctuante rendrait la FIFO illisible et le diagnostic impossible. (2) Elle ne descend **jamais** sous `capacite_plancher` (200) et, si elle rétrécit, la troncature se fait **par l'AVANT** (`pop(0)`, les plus anciens partent) — tronquer par la fin jetterait les souvenirs les plus frais, les plus utiles au rappel. (3) Un souvenir spatial est un **repère**, jamais un journal d'événements : `enregistrer_evenement` **déduplique** sur `(pos, type)` en rafraîchissant le tick, et la capacité est bornée par la taille du monde (`DENSITE_MAX_PAR_CASE`) — un `.brain` réel contenait 91 % de doublons avant ce correctif. (4) `reference_richesse` doit rester proportionnelle à `empreinte_enfance` : sans cela, `%_reve` s'effondre mécaniquement quand le cerveau grandit (mesuré : 60 % à dim_bus=16 → 15 % à dim_bus=96). Attention à ne pas sur-corriger : une part de la baisse de rêve sur un cerveau mature est **saine** (l'erreur JEPA chute parce que l'agent comprend mieux son monde) — ne jamais compenser ce signal-là
- Vérifier si la modification touche à l'**odorat** (`_distances_topologiques`, `_bfs_vers_agent`, `SURCOUT_PORTE_FERMEE`, `TYPES_BLOQUANTS_ODORAT`) ou à la **clinotaxie** (`DIM_ODORAT_DELTA`, `_calculer_deltas_odorat`, `_odeurs_precedentes`) : quatre invariants v32.0. (1) La distance olfactive est **topologique**, jamais euclidienne/Manhattan — une odeur qui traverse un mur produit un gradient *trompeur*, pire que pas de gradient du tout, car `integrateur_bio` ne peut pas apprendre à ignorer un signal qui n'est faux qu'une partie du temps. Sans obstacle, le BFS retombe exactement sur Manhattan : c'est le test de non-régression à conserver. (2) Une porte fermée **« fuit »** (surcoût `+4`), elle ne bloque pas : la bloquer rendrait l'odorat inutile précisément quand l'agent cherche la clé de cette porte. (3) Le neutre de la clinotaxie est **0.5, jamais 0.0** — 0.0 signifierait un éloignement maximal, et `obtenir_vecteur_bio` doit le respecter dans son fallback hors MiniGrid (vocal isolé, rêve), sans quoi l'agent perçoit une fuite olfactive permanente qui n'existe pas. (4) `_odeurs_precedentes` **doit** être remis à `None` dans `reinitialiser_episode` : au `reset()` l'agent est téléporté et les sources régénérées, donc comparer au dernier tick de l'épisode précédent injecterait un ΔS énorme et fictif. Ne pas réintroduire d'**habituation au capteur** (`max(0, S − α·S_lissé)`) : c'est une dérivée en moins lisible, elle détruirait tout le signal d'éloignement et rendrait l'odorat non-markovien
- Vérifier si la modification touche à la **détection de greffe dans `persistance.py`** (`greffe_detectee`) : elle ne doit **jamais** se fonder sur `missing_keys` seul. Une greffe **par recopie** — la règle du projet — ne produit aucune clé manquante (la couche existe, seule sa forme change), et l'optimiseur Adam restait alors chargé à l'ancienne largeur. Le symptôme est particulièrement traître : le crash ne survient **ni au chargement, ni pendant la journée, mais à la première `executer_nuit`**, donc invisible à toute vérification de type « N ticks post-résurrection ». Bug latent depuis la v29.0, corrigé en v32.0 en s'appuyant sur le drapeau retourné par la greffe elle-même. **Toute validation d'une greffe doit inclure une nuit complète**, pas seulement des ticks
- **Avant de rendre une constante ADAPTATIVE, l'instrumenter et la mesurer d'abord** (méthode posée en v30.1). Le projet bannit les chiffres arbitraires (voir le rêve adaptatif : `pourcentage_reve` émerge de la plasticité × richesse, jamais d'un batch fixe) — mais remplacer un chiffre arbitraire par une **formule** arbitraire ne vaut pas mieux, elle est juste plus difficile à remettre en cause. Une constante a été calibrée par cette méthode en v31.0 (`MemoireEpisodiqueSpatiale.capacite_max`, devenue `dim_bus × SOUVENIRS_PAR_DIM × (1 + déficit_bio)` après lecture des métriques `Memoire_*`). Il en reste une, instrumentée et en attente de données : `EXTENSION_PATIENCE_SURSAUT = 50` (métriques `Sursaut_*`, dont `Sursaut_Taux_Victoire` qui doit trancher entre un renforcement « muscle » et une atténuation « habituation »). Ne pas écrire ces formules sans avoir lu les courbes d'un run long, et vérifier ensuite par empreinte à graine fixée que la mécanique adaptative fait **mieux** que le fixe, pas seulement « différemment »
- Vérifier si la modification touche au **`PROGRAMME` du cursus** (`PROGRAMME`, `VICTOIRES_REQUISES`, `TAUX_PROMOTION`, `FENETRE_PROMOTION`, `MIN_EPISODES_PROMOTION`, `historique_episodes_niveau`) : quatre invariants v35.0. (1) `niveau_actuel` est un **INDEX** dans `PROGRAMME` — changer la taille ou l'ordre de la liste **rétrograde silencieusement tous les `.brain` existants**. C'est pourquoi `persistance` remappe par `env_id` (la seule donnée non ambiguë) et affiche `🔀 Niveau remappé` ; toute nouvelle modification du programme doit conserver ce remappage. (2) La promotion a **deux voies en OU** — série de victoires (rapide, fragile) et taux de maîtrise (lent, robuste) : ne jamais supprimer la première, elle garantit qu'aucun cerveau ne régresse en vitesse de promotion. (3) `historique_episodes_niveau` **doit être vidé à chaque promotion** — un taux hérité d'un niveau plus facile promouvrait en chaîne sans que l'agent ait rien montré sur le nouveau. (4) La réussite d'un épisode se juge sur `recompense_env > 0`, **jamais sur `termine` seul** : `termine` vaut aussi True quand l'agent meurt dans la lave (`LavaGap`), et compter ça comme un succès promouvrait un agent qui se suicide vite. Le principe du programme est qu'**une seule compétence change entre deux paliers voisins** (`DoorKey-5x5` → `6x6` → `8x8` est la même tâche à trois échelles) — ne pas y insérer un niveau qui cumule plusieurs nouveautés
- Vérifier si la modification touche à l'**érosion nocturne** (`cycle_sommeil`, `PLANCHER_POIDS_VITAL`, `FRACTION_NORME_MIN_COUCHE`, `norme_naissance`) : deux invariants v34.0-fix1/fix2, posés après un bug qui a rendu un cerveau **entièrement aveugle et sourd** (8 couches sur 11 à zéro exact après 1500 nuits). (1) L'érosion est **géométrique** (`base *= 1 − λ(1 − myéline)`) et la myéline ne peut venir **que** du gradient : un agent sans récompense ne myélinise rien, donc s'érode à taux plein et meurt en ~121 nuits. Le plancher vital est ce qui l'en empêche — ne jamais le retirer « parce qu'il ne sert jamais » : mesuré, **6 couches sur 11 y sont collées** sur un run réel. (2) `norme_naissance` ne doit **jamais rétrécir** : `agrandir()` recopie des poids déjà érodés, donc la norme du tenseur agrandi peut être plus petite que l'originale — d'où le `torch.maximum`. Sans lui, chaque neurogenèse divisait la protection par ~7 et le correctif s'auto-annulait. ⚠️ `SEUIL_CRISTAL = 0.80` n'a **jamais** été franchi (myéline réelle max mesurée : **0.0038**) : la Cristallisation Souple v26.0 ne s'est enclenchée sur aucun cerveau du dépôt — ne pas s'appuyer dessus comme protection
- Vérifier si la modification touche à la **rétrocompatibilité des `.brain`** (`persistance.py`) : la règle générale est **greffe par recopie, jamais par exclusion**. Exclure une couche sur mismatch de forme la fait renaître à neuf et détruit des centaines de jours d'acquis (bug v24.0-fix4, symptôme : bouche silencieuse dans l'Arène). Les deux greffes existantes — `_greffer_action_supplementaire` (7→8 actions, v28.0) et `_greffer_vecteur_bio_etendu` (vecteur bio 16→24, v29.0) — sont le modèle à suivre ; le filtre d'exclusion ne reste qu'en trappe de secours pour les mismatchs qu'on ne sait pas greffer
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

Il n'y a ni linter ni suite de tests automatisés configurés. Toute vérification passe par l'observation des logs console (progression de palier, teneur en dopamine, thermostat de neurogenèse) et des courbes du tableau de bord W&B (voir [Modèle de Données & Métriques W&B](readme.md#modèle-de-données--métriques-wb) dans le README).

## Git Workflow

### État des branches (2026-08-02)

| Branche | Contenu | État |
|---|---|---|
| `master` | v28.0 (Port Exocortex C3) + v29.0 (Bus Sensoriel & identité C1/C2) + v29.1 (télémétrie des 5 sens) | intégrée, poussée |
| `feat/v30-exo-sens` | v30.0 — l'Exo-Sens (C3 en 6ᵉ sens, odorat dynamique exponentiel) | **implémentée et validée**, en attente de merge — voir `docs/Old_Archive_rmd/CONCEPTION_v30_exo_sens.md` |
| `feat/v28-exocortex-c3` | branche d'origine des v28/v29, désormais mergée dans `master` | conservée pour l'historique |

Le travail en cours se fait sur `feat/v30-exo-sens`, rebasée sur `master`. Décisions structurantes
de la v30, déjà appliquées : `num_actions` **reste à 8** avec `ACTION_DEMANDER` masquée en
permanence (ne jamais amputer un `.brain` — 4 des cerveaux du dépôt sont déjà à 8 actions), le
vecteur bio passe de 24 à 32 dims **en queue**, et l'Exo-Sens est perçu **en continu sans aucun
seuil de déclenchement**.

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

### 3. Archivage documentaire (`docs/Old_Archive_rmd/`, depuis v30.1)

`docs/` ne contient que des **documents vivants** (4 aujourd'hui). Un document rejoint
`docs/Old_Archive_rmd/` quand sa mécanique est **livrée et documentée ailleurs** — jamais parce
qu'il est simplement « vieux ». Un cadrage archivé reste précieux : il garde la trace des options
**écartées** et de leurs raisons, ce qu'aucun document à jour ne raconte, et c'est ce qui évite
qu'une idée déjà évaluée soit réintroduite sans connaître l'argument qui l'avait rejetée.

Procédure : `git mv` (jamais `mv` seul — l'historique du fichier est précieux), puis **corriger
tous les liens entrants**. Attention : ces documents sont référencés depuis `readme.md`,
`CLAUDE.md`, les autres docs **et les docstrings du code source** (`bus_sensoriel.py`,
`hemisphere_audio.py`, `professeur_gemma.py`, `lecons_vocales.py`, `client_professeur.py`,
`daemon_cerveau.py`, `irm_cerveau.py`). Vérifier ensuite qu'aucun lien ne pointe dans le vide.

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

Le script de référence `src/naulthene/cerveau/colab.py` est actuellement en version **17** (voir `readme.md`, table des matières et journal des mises à jour). `src/naulthene/cerveau/noyau.py` porte en plus toutes les mécaniques expérimentales non encore portées sur `colab.py` (actuellement jusqu'à **v32.0** — l'Odorat Topologique & la Clinotaxie — en passant par v31.0/v31.1 la Mémoire Proportionnelle, le Rêve Invariant d'Échelle & la Déduplication Mnésique, en passant par v18.0 Architecture Homéostatique Biologique, v22 Hémisphère Auditif & Vocal, v27.x École de la Parole, v28.0 Cascade C1→C2→C3 & Port Exocortex, v29.0/v29.1 Bus Sensoriel & télémétrie des 5 sens, v30.0/v30.1 Odorat Dynamique, Exo-Sens & instrumentation, voir [Variante Locale de Test](#variante-locale-de-test-mac--srcnaulthenecerveaunoyaupy) et `readme.md`/`docs/CHANGELOG.md` pour le détail) — toute nouvelle mécanique testée localement suit la même échelle de version que le script de référence, marquée `-experimental` tant qu'elle n'y est pas portée. Poursuivre sur cette échelle entière (+1.0 pour la prochaine mécanique majeure) sauf décision contraire de l'utilisateur.
