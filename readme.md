Voici le **`README.md`** révisé, complété et restructuré en profondeur.

Il intègre la structure de table des matières globale (avec le contexte applicatif/métier et la vision AGI), enrichie de toute l'architecture neuro-mimétique de l'agent **Naulthène AGI** (réservoir dopaminergique, cursus à 7 paliers par Abnégation, mode libre à décrochage précoce, sous-quêtes intrinsèques par curiosité JEPA, Sursaut de Volonté, planification multi-échelle non-linéaire, consolidation nocturne adaptative, détecteurs génériques, pression cinétique multimodale et patience évolutive).

---

# 🧠 Naulthène AGI — Architecture & Documentation Technique

> **Agent Cognitif Autonome Hybride (RL + JEPA + Mémoire Épisodique + Bio-Homéostasie)**
> *Un modèle d'apprentissage universel guidé par le développement cognitif, la plasticité neuro-mimétique et le libre arbitre.*

**Auteur** : Adrien Nault ([@DredGuer](https://github.com/DredGuer)) — Licence [Apache 2.0](LICENSE). Toute réutilisation, redistribution, publication ou œuvre dérivée reprenant le concept ou l'architecture de ce projet (code, mécaniques, idée originale) **doit citer Adrien Nault comme auteur original de Naulthène AGI** — voir [NOTICE](NOTICE) pour l'exigence d'attribution complète.

---

## 📋 Table des Matières

1. [Vue d'Ensemble du Projet](https://www.google.com/search?q=%23vue-densemble-du-projet)
2. [Journal des Mises à Jour (Changelog)](https://www.google.com/search?q=%23journal-des-mises-%C3%A0-jour)
3. [Plan d'Action](https://www.google.com/search?q=%23plan-daction)
3t. **[Parcourt_readme.md — Guide Complet du Système de Cursus](docs/Parcourt_readme.md)** (commandes de lancement, jours/ticks par parcours, détail des paliers, FAQ)
3q. 🚧 [v30.0 (en cours de conception) — L'Unification & l'Extensibilité (l'Exo-Sens)](#-v300-en-cours-de-conception--lunification--lextensibilité-lexo-sens)
3r. [Nouveautés v29.1 (expérimental) — Télémétrie des 5 Sens](#nouveautés-v291-expérimental--télémétrie-des-5-sens-2026-08-02)
3s. [Nouveautés v29.0 (expérimental) — Le Bus Sensoriel Multimodal & l'Identité C1/C2](#nouveautés-v290-expérimental--le-bus-sensoriel-multimodal--lidentité-c1c2-explicite-2026-08-02)
3u. [Nouveautés v28.0 (expérimental) — La Cascade C1→C2→C3 & le Port Exocortex](#nouveautés-v280-expérimental--la-cascade-c1c2c3--le-port-exocortex-2026-07-30)
3v. [Nouveautés v27.6 (expérimental) — L'École de la Parole & Synesthésie](#nouveautés-v276-expérimental--lécole-de-la-parole--synesthésie-2026-07-2728)
3w. [Nouveautés v26.0 (expérimental) — L'Arène augmentée (mini-IRM + télémétrie complète)](#nouveautés-v260-expérimental--larène-augmentée-mini-irm--télémétrie-complète-2026-07-27)
3x. [Nouveautés v26.0 (expérimental, §A.5 seul) — Cristallisation Souple](#nouveautés-v260-expérimental-a5-seul--cristallisation-souple-2026-07-27)
3y. [Nouveautés v25.0 (expérimental) — Le Cerveau Bébé Développemental (0→4 ans)](#nouveautés-v250-expérimental--le-cerveau-bébé-développemental-04-ans-2026-07-24)
3z. [Correctifs v24.0-fix1 à fix5 (expérimental) — École de Rattrapage Vocal & silence de l'Arène](#correctifs-v240-fix1-à-fix5-expérimental--école-de-rattrapage-vocal--silence-de-larène-2026-07-2324)
4. [Nouveautés v24.0 (expérimental) — L'Arène & Démo Live](#nouveautés-v240-expérimental--larène--démo-live-2026-07-23)
4z. [Nouveautés v23.0 (expérimental) — Le Cursus Développemental par Ères](#nouveautés-v230-expérimental--le-cursus-développemental-par-ères-2026-07-23)
4a. [Nouveautés v22.1 (expérimental) — Correction de l'Hémisphère Audio](#nouveautés-v221-expérimental--correction-de-lhémisphère-audio-2026-07-23)
4b. [Nouveautés v22.0 (expérimental) — L'Hémisphère Auditif & Vocal](#nouveautés-v220-expérimental--lhémisphère-auditif--vocal-2026-07-23)
5. [Nouveautés v21.0 (expérimental) — Le Cerveau Persistant en Cuve](#nouveautés-v210-expérimental--le-cerveau-persistant-en-cuve-2026-07-23)
5. [Nouveautés v20.0 (expérimental) — Mémoire Épisodique Spatiale & LTP Hebbien](#nouveautés-v200-expérimental--mémoire-épisodique-spatiale--ltp-hebbien-2026-07-23)
6. [Nouveautés v19.0 (expérimental) — Métabolisme 20/80 & Forage 80/20](#nouveautés-v190-expérimental--métabolisme-2080--forage-8020-2026-07-22)
7. [Nouveautés v18.0 (expérimental) — Architecture Homéostatique Biologique](#nouveautés-v180-expérimental--architecture-homéostatique-biologique-2026-07-22)
8. [Nouveautés v17.0 — Volonté Émergente & Sous-Objectifs Intrinsèques](#nouveautés-v170--volonté-émergente--sous-objectifs-intrinsèques-2026-07-22)
9. [Nouveautés v16.0 — Thermostat Multimodal & Patience par Abnégation](#nouveautés-v160--thermostat-multimodal--patience-par-abnégation-2026-07-22)
10. [Nouveautés v15.0 — Planification Non-Linéaire, Pression Cinétique & Patience Adaptative](#nouveautés-v150--planification-non-linéaire-pression-cinétique--patience-adaptative-2026-07-22)
11. [Nouveautés v14.0 — Rêves Adaptatifs & Planification Étendue à 3 Pas](https://www.google.com/search?q=%23nouveaut%C3%A9s-v140---r%C3%AAves-adaptatifs--planification-%C3%A9tendue-%C3%A0-3-pas-2026-07-22)
12. [Nouveautés v13.0 — Décision Autonome & Mode Libre](https://www.google.com/search?q=%23nouveaut%C3%A9s-v130---d%C3%A9cision-autonome--mode-libre-2026-07-22)
13. [Nouveautés v12.0 — Cursus à 7 Paliers & Correctif d'Épisodes](https://www.google.com/search?q=%23nouveaut%C3%A9s-v120---cursus-%C3%A0-7-paliers--correctif-d%C3%A9pisodes-2026-07-22)
14. [Nouveautés v11.0 — Réservoir Dopaminergique V3](https://www.google.com/search?q=%23nouveaut%C3%A9s-v110---r%C3%A9servoir-dopaminergique-v3-2026-07-22)
15. [Nouveautés v10.0-fix1 — Correctif de Stabilité JEPA & Thermostat](https://www.google.com/search?q=%23nouveaut%C3%A9s-v100-fix1---correctif-de-stabilit%C3%A9-jepa--thermostat)
16. [Nouveautés v10.0 — Système 2 & Rollout Mental Vectorisé](https://www.google.com/search?q=%23nouveaut%C3%A9s-v100---syst%C3%A8me-2--rollout-mental-vectoris%C3%A9)
17. [Nouveautés v9.1 — Intégration du Tampon Épisodique (Université)](https://www.google.com/search?q=%23nouveaut%C3%A9s-v91---int%C3%A9gration-du-tampon-%C3%A9pisodique-universit%C3%A9)
18. [Nouveautés v9.0-fix1 — Correctif de la Neurogenèse Bloc par Bloc](https://www.google.com/search?q=%23nouveaut%C3%A9s-v90-fix1---correctif-de-la-neurogen%C3%A8se-bloc-par-bloc)
19. [Nouveautés v9.0 — Cursus Académique Progressif (Primaire à Doctorat)](https://www.google.com/search?q=%23nouveaut%C3%A9s-v90---cursus-acad%C3%A9mique-progressif-primaire-%C3%A0-doctorat)
20. [Nouveautés v8.0 — Alignement Graph-Gradient RL & Rêve Nocturne](https://www.google.com/search?q=%23nouveaut%C3%A9s-v80---alignement-graph-gradient-rl--r%C3%AAve-nocturne)
21. [Nouveautés v7.0 — Phase 7 Initiale (Architecture Hybride Duale)](https://www.google.com/search?q=%23nouveaut%C3%A9s-v70---phase-7-initiale-architecture-hybride-duale)
22. [Architecture Cognitico-Biologique Complète](https://www.google.com/search?q=%23architecture-cognitico-biologique-compl%C3%A8te)
23. [Cursus Académique & Paliers Comportementaux](https://www.google.com/search?q=%23cursus-acad%C3%A9mique--paliers-comportementaux)
24. [Moteur Émotionnel & Réservoir Dopaminergique](https://www.google.com/search?q=%23moteur-%C3%A9motionnel--r%C3%A9servoir-dopaminergique)
25. [Algorithme de Rêve Nocturne Adaptatif](https://www.google.com/search?q=%23algorithme-de-r%C3%AAve-nocturne-adaptatif)
26. [Détecteurs Génériques d'Intention & Quêtes Auto](https://www.google.com/search?q=%23d%C3%A9tecteurs-g%C3%A9n%C3%A9riques-dintention--qu%C3%AAtes-auto)
27. [Pression Cinétique Multimodale & Patience par Abnégation](#pression-cinétique-multimodale--patience-par-abnégation)
28. [Volonté Émergente : Sous-Objectifs Intrinsèques & Sursaut](#volonté-émergente--sous-objectifs-intrinsèques--sursaut)
29. [Architecture Homéostatique Biologique (expérimental)](#architecture-homéostatique-biologique-expérimental)
30. [Mémoire Épisodique Spatiale & LTP Hebbien (expérimental)](#mémoire-épisodique-spatiale--ltp-hebbien-expérimental)
31. [Le Cerveau Persistant en Cuve — Architecture Client-Serveur (expérimental)](#le-cerveau-persistant-en-cuve--architecture-client-serveur-expérimental)
32. [Stack Technique](https://www.google.com/search?q=%23stack-technique)
33. [Modèle de Données & Métriques W&B](https://www.google.com/search?q=%23mod%C3%A8le-de-donn%C3%A9es--m%C3%A9triques-wb)
34. [Démarrage Rapide](https://www.google.com/search?q=%23d%C3%A9marrage-rapide)
35. [Mise en Production & Monitoring](https://www.google.com/search?q=%23mise-en-production--monitoring)
36. [Configuration](https://www.google.com/search?q=%23configuration)
37. [Troubleshooting & Guide de Dépannage](https://www.google.com/search?q=%23troubleshooting--guide-de-d%C3%A9pannage)

---

## 🎯 Vue d'Ensemble du Projet

**Naulthène AGI** est une tentative de concilier le **Reinforcement Learning (RL)**, la **prédiction spatio-temporelle sous contrainte d'énergie (JEPA - Joint Embedding Predictive Architecture)** et la **neurobiologie computationnelle**.

L'agent évolue à travers un cursus scolaire modélisé sous forme d'environnements à complexité croissante (MiniGrid) :

* **Primaire** : Navigation basique et proprioception (`Empty-8x8`).
* **Collège** : Logique d'objets, clés et portes (`DoorKey-6x6`).
* **Lycée** : Manipulation avancée, coffres et outils (`Unlock-5x5`).
* **Université** : Rétention d'informations temporelles et mémoire à long terme (`MemoryS7`).
* **Doctorat** : Planification à très long horizon à travers de multiples sous-objectifs (`MultiRoom-N4-S5`).

📖 **Envie de lancer un run et de comprendre concrètement ce qui se passe (commandes, jours,
ticks par jour, paliers, FAQ) ?** Voir **[docs/Parcourt_readme.md](docs/Parcourt_readme.md)** —
le guide pratique complet des 4 parcours d'entraînement (Cursus par Ères, Cerveau Bébé, Cursus de
la Parole, la Cuve).

---

## 📜 Journal des Mises à Jour

Pour un historique complet commit par commit, consultez [docs/CHANGELOG.md](docs/CHANGELOG.md).

> 📍 **État du dépôt (2026-08-02)** — la branche `master` intègre désormais les versions
> **v28.0** (Port Exocortex C3), **v29.0** (Bus Sensoriel & identité C1/C2) et **v29.1**
> (télémétrie des 5 sens). La **v30.0** (« l'Exo-Sens ») est **en cours de conception** sur la
> branche `feat/v30-exo-sens` — rien n'en est encore livré, voir
> [docs/CONCEPTION_v30_exo_sens.md](docs/CONCEPTION_v30_exo_sens.md) pour le cadrage.

### 🚧 v30.0 (en cours de conception) — L'Unification & l'Extensibilité (l'Exo-Sens)

> ⚠️ **Rien n'est encore implémenté.** Cette section décrit une cible, pas un état livré. Le
> document de cadrage complet (décisions tranchées, points ouverts, invariants) est dans
> [docs/CONCEPTION_v30_exo_sens.md](docs/CONCEPTION_v30_exo_sens.md).

La v30.0 doit concrétiser le pivot conceptuel amorcé par la v29 : transformer l'Exocortex **C3**
d'un « 3ᵉ cerveau » en un **6ᵉ sens exogène** (l'*Exo-Sens*), et corriger la physique de l'odorat
local. Trois chantiers :

1. **L'Odorat Dynamique** — portée relative à la géométrie de la carte, pour corriger la
   saturation diagnostiquée en v29.1.
2. **Le pivot de C3** — l'Exocortex cesse d'être un canal de *décision* (une action jouée) pour
   devenir un canal de *perception* : `DIM_VECTEUR_BIO` passerait de 24 à 32 dims, l'agent
   « percevant » le monde numérique (LLM/RAG, bases vectorielles, APIs, IoT) au lieu de
   l'interroger. Le contrat `PlugC3` (v28.0) est déjà générique et n'a pas à être réinventé.
3. **La Boucle d'Attention Exogène** — comment l'agent module son attention à ce 6ᵉ sens.

**Deux points restent ouverts et sont documentés comme tels** : la formule d'odorat proposée ne
corrige pas les cartes 4×4 (et aggrave le Doctorat), et le déclenchement d'attention envisagé
réintroduirait un seuil codé en dur — exactement ce que les v28 et v29 ont refusé deux fois.

### Nouveautés v29.1 (expérimental) — Télémétrie des 5 Sens (2026-08-02)

> ⚠️ **Statut expérimental** : vit dans `src/naulthene/cerveau/noyau.py` (gitignored, terrain d'essai local), pas encore porté sur `src/naulthene/cerveau/colab.py`.

La v29.0 câblait les 5 sens **dans la décision** — l'agent les utilisait réellement — mais n'en
instrumentait **aucun** : sur un run de 300 jours, il aurait été impossible de répondre à
« l'odorat a-t-il jamais servi ? », et une désactivation silencieuse du Bus Sensoriel n'aurait
laissé qu'un unique avertissement console, noyé dans les logs.

* **Sept métriques W&B** (`Sens_*`) et une ligne au bilan de nuit, absentes du log si aucun tick
  sensoriel n'a été vécu. La plus utile au quotidien : **`Sens_Toucher_Portage_Ratio`**, le temps
  passé à porter la clé sur DoorKey — un indicateur *avancé* de la maîtrise des paliers 3-4, qui
  monte souvent avant que les victoires n'arrivent. La plus critique : **`Sens_Bus_Actif`**, qui
  rend visible une panne du bus à chaque nuit plutôt qu'une seule fois.
* **Un audit systématique** des 21 compteurs journaliers de `EtatCognitif` a confirmé que tout le
  reste du projet était correctement instrumenté (y compris la télémétrie C3 de la v28.0) —
  l'écart était strictement limité à la v29.0.
* **Diagnostic livré immédiatement par cette télémétrie** : l'odorat **sature sur les petites
  cartes** (97,6 % de couverture sur `Empty-8x8`, 100 % sur `DoorKey-6x6`), donc y porte très peu
  d'information. `PORTEE_ODORAT` a été laissée **inchangée** — le constat est documenté, mais
  l'arbitrage (portée réduite, moins de sources, ou normalisation par taille de carte) appartient
  à l'auteur du projet. C'est devenu le chantier 1 de la v30.0.
* **Leçon retenue en règle de projet** (`CLAUDE.md`) : toute mécanique observable doit être
  instrumentée **dans le même commit** que son implémentation.

### Nouveautés v29.0 (expérimental) — Le Bus Sensoriel Multimodal & l'Identité C1/C2 explicite (2026-08-02)

> ⚠️ **Statut expérimental** : vit dans `src/naulthene/cerveau/noyau.py` (gitignored, terrain d'essai local), le nouveau module **versionné** `src/naulthene/cerveau/bus_sensoriel.py` et `src/naulthene/cerveau/persistance.py`, pas encore porté sur `src/naulthene/cerveau/colab.py`.

Trois chantiers issus de [docs/Maj_V29_readme.md](docs/Maj_V29_readme.md) : donner à Naulthène **les cinq sens** au lieu de deux, **nommer explicitement** la frontière C1/C2 déjà présente dans le code, et **auditer** la boucle de distillation C2 → C1 — qui, elle, n'avait pas besoin d'être écrite.

* **La hiérarchie des 5 sens, et son coût.** Tous les sens ne se valent pas en gourmandise énergétique, mais c'est la **combinaison de leur diversité** qui fait émerger une compréhension du monde. Jusqu'en v28.0, l'agent n'avait que ses deux sens gourmands — la vue (`porte_visuelle`, 147 dims) et l'ouïe (`porte_auditive`, 130 dims MFCC), chacun avec sa porte synaptique dédiée. Le nouveau module `bus_sensoriel.py` ajoute les trois sens manquants, qui sont justement les moins coûteux à calculer et les plus directement liés à la survie :

  | Sens | Gourmandise | Dims | Chemin dans le cerveau | Dans la cible JEPA ? |
  |------|-------------|------|------------------------|----------------------|
  | **Vue** | Extrême | 147 | `porte_visuelle` → `bus_latent` | ✅ oui |
  | **Ouïe** | Élevée | 130 | `porte_auditive` → `bus_latent` | ✅ oui (tête séparée) |
  | **Toucher** | Moyenne | 4 | `vecteur_bio` → `integrateur_bio` | ❌ non |
  | **Odorat** | Faible | 2 | `vecteur_bio` → `integrateur_bio` | ❌ non |
  | **Goût** | Faible | 2 | `vecteur_bio` → `integrateur_bio` | ❌ non |

* **Le toucher, l'odorat, le goût.** Le **toucher** donne le contact frontal (via l'API MiniGrid native `can_overlap()`), l'objet en main (`carrying` — en v28.0 l'agent ne savait qu'il tenait la clé qu'indirectement, par la vue) et l'orientation encodée **sur le cercle** (cos/sin) plutôt qu'en entier 0-3, pour supprimer la discontinuité artificielle entre les directions 3 et 0, voisines dans le monde réel. L'**odorat** perçoit la source de Nourriture/Eau la plus proche, décroissant sur 4 cases — un signal de survie grossier qui *oriente* avant même de voir, pas une carte : la cartographie précise reste le travail de la vue et de la mémoire spatiale. Le **goût** est une trace **rémanente** (~10 ticks) de la dernière ressource réellement ingérée, remise à zéro à chaque épisode.

* **Décision structurante : les sens faibles n'entrent pas dans le bus latent.** Le toucher et la chimie passent par la **queue du `vecteur_bio`** (`DIM_VECTEUR_BIO` 16 → 24), donc par `integrateur_bio`, juste avant la décision — et **jamais** par une porte sommée dans `bus_latent`. Conséquence voulue : ils ne polluent jamais la cible JEPA (`perte_jepa` compare toujours le bus prédit au bus réel de la **vision seule**), et un cerveau entraîné sur des centaines de jours ne voit pas son modèle du monde perturbé par trois nouveaux canaux bruités.

* **L'identité C1/C2, enfin nommée.** La distinction existait déjà (`tete_motrice` d'un côté, `simuler_futur_et_planifier` de l'autre) mais restait implicite, entrelacée dans le corps de `penser()`. Elle est désormais encapsulée dans deux méthodes explicites : **`_executer_c1_reflexe()`** (compression des 5 sens, contexte épisodique, intégration viscérale, réflexe moteur en latence zéro) et **`_solliciter_c2_neocortex()`** (le moteur analytique lourd, JEPA + simulation mentale), qui ne reçoit **que** l'état déjà compressé par C1 — jamais les pixels, jamais le MFCC brut. `penser()` se réduit à l'arbitrage.

* **Restructuration pure, zéro changement de comportement** (décision utilisateur explicite). C2 continue d'être sollicité à chaque tick. L'alternative — C1 court-circuite C2 quand il est confiant, pour une vraie économie d'énergie — a été **écartée volontairement** : elle aurait introduit un déclenchement sur seuil codé en dur dans le chemin de décision, exactement de la même nature que ce que le projet s'interdit déjà pour l'appel à C3.

* **La distillation C2 → C1 : auditée, pas réimplémentée.** Le document de conception la présente comme la pièce maîtresse. L'audit confirme qu'elle est **déjà entièrement réalisée** par le cycle jour/nuit existant : `annexe_weight` accumule le gradient diurne (C2 guide l'expérience) → `cycle_sommeil()` le consolide dans `base_weight` (C2 → C1) → la Cristallisation Souple (v26.0) fige définitivement les synapses les plus myélinisées, libérant C2 pour de futurs apprentissages. Aucun code ajouté — la boucle est documentée plutôt que dupliquée.

* **La rétrocompatibilité des `.brain`**, principal risque technique de cette version. Étendre le vecteur bio change la **forme** de `integrateur_bio` ; le filtre historique traitait ce cas en *excluant* la couche, qui renaissait à neuf — le symptôme exact du bug v24.0-fix4 (bouche silencieuse dans l'Arène). Une greffe par **recopie partielle** (`_greffer_vecteur_bio_etendu`) préserve désormais au bit près toute l'intégration viscérale et vocale déjà apprise, les 8 nouvelles dimensions naissant à une initialisation atténuée. L'agent se réveille avec tous ses acquis et découvre simplement qu'il a désormais un toucher, un odorat et un goût — encore muets.

* **v29.1 — les sens rendus observables.** La v29.0 câblait les 5 sens dans la décision mais n'en instrumentait aucun : impossible, sur un run de 300 jours, de répondre à « l'odorat a-t-il jamais servi ? ». Sept métriques W&B (`Sens_*`) et une ligne au bilan de nuit comblent ce trou — dont `Sens_Bus_Actif`, qui rend visible une désactivation silencieuse du bus. Premier diagnostic livré immédiatement : **l'odorat sature sur les petites cartes** (97,6 % de couverture sur `Empty-8x8`, 100 % sur `DoorKey-6x6`), donc y porte peu d'information. Constat documenté, `PORTEE_ODORAT` **inchangée** — l'arbitrage appartient à l'auteur.

📖 **Documentation dédiée** : **[docs/EXPLICATIONS_v29_sens.md](docs/EXPLICATIONS_v29_sens.md)** — le document explicatif complet de cette version (formules, schémas, table des 13 validations, options écartées et pourquoi, glossaire des constantes). Voir aussi [docs/CHANGELOG.md](docs/CHANGELOG.md) (entrée v29.0-experimental) pour le détail commit par commit, [docs/explications_readme.md](docs/explications_readme.md) §15 pour le résumé algorithmique, et [docs/LANCEMENT.md](docs/LANCEMENT.md) §9 pour observer les 5 sens en direct.

### Nouveautés v28.0 (expérimental) — La Cascade C1→C2→C3 & le Port Exocortex (2026-07-30)

> ⚠️ **Statut expérimental** : vit dans `src/naulthene/cerveau/noyau.py` (gitignored, terrain d'essai local) et le nouveau sous-package **versionné** `src/naulthene/exocortex/`, pas encore porté sur `src/naulthene/cerveau/colab.py`.

Ouvre le Cœur Organique fermé [C1 (réflexe/instinct) + C2 (raison/JEPA)], 100% autonome depuis l'origine du projet, à un **troisième canal optionnel** : un Exocortex (C3) conçu comme un **Port Multiplexeur** plutôt qu'un appel figé vers un service unique — un bus sur lequel des "Plugs" interchangeables s'enregistrent (`PlugNul`, `PlugSimule`, `PlugHTTP` livrés ; `Plug_Ollama`/`Plug_VectorDB`/`Plug_Web`/`Plug_BrainToBrain` pourront se brancher plus tard sans toucher au noyau). **Principe non négociable, posé par l'utilisateur** : couper le courant de C3 ne doit ni planter, ni changer le comportement d'un cerveau existant — sans plug branché, l'agent se comporte au bit près comme en v27.6.

* **Un choix appris, jamais un seuil.** "Interroger C3" n'est pas un `if erreur_jepa > seuil` : c'est une **8ème action** (`ACTION_DEMANDER`, `num_actions` 7→8) que la tête motrice apprend à jouer par REINFORCE, exactement comme elle apprend à tourner ou ramasser une clé — masquée à `-inf` dans les logits tant qu'aucun plug n'est disponible, et assortie d'un coût (`COUT_REQUETE_C3`) pour que demander reste un choix économique plutôt qu'un réflexe gratuit. Une nouvelle tête de routage (`tete_requete`) choisit en plus vers quel plug émettre, ou de diffuser à tous.
* **Le détecteur d'impasse fournit un contexte, jamais un déclenchement.** Le rollout mental (`simuler_futur_et_planifier`) calculait déjà, puis jetait, l'écart-type de ses valeurs simulées — c'était l'unique mesure d'indécision du Système 2. Cette valeur (`indecision_c2`) est désormais transmise dans la requête envoyée sur le bus, en simple contexte, aux côtés de l'erreur JEPA du tick — jamais comme condition d'appel.
* **La trappe de secours est structurelle, pas du code défensif ajouté.** Un plug qui échoue en vol part en quarantaine (cooldown) et n'apparaît plus disponible ; l'action redevient masquée au tick suivant. La curiosité intrinsèque (`DetecteurCuriositeJEPA`) et le Sursaut de Volonté, déjà présents dans le projet, n'ont jamais été conditionnés à C3 — ils restent la réponse par défaut.
* **L'assimilation réutilise la mécanique existante, sans ouvrir de nouveau canal de gradient.** Une réponse C3 acceptée devient un 3ème canal du "OU doux" v27.0 (dopamine), déclenche le même LTP par tick (`fortifier_synapses`) que tout autre événement marquant, et majore l'importance du souvenir pour qu'il soit rejoué en priorité la nuit — sans introduire de perte supervisée externe dans la politique.
* **La rétrocompatibilité des `.brain` existants**, le principal risque technique de cette version : passer à 8 actions change la forme de plusieurs couches (`tete_motrice`, `generateur_attente`, `generateur_attente_audio`). Une greffe par recopie partielle (et non par exclusion) préserve au bit près les 7 actions déjà apprises sur tout cerveau existant, la 8ème naissant à une initialisation atténuée — validé sur les trois `.brain` réels du dépôt, dont `naulthene_parole.brain` (300 jours, palier vocal 19/19).

Voir [docs/CHANGELOG.md](docs/CHANGELOG.md) (entrée v28.0-experimental) pour le détail technique complet et [docs/explications_readme.md](docs/explications_readme.md) pour la description algorithmique de la cascade et du protocole du bus.

### Nouveautés v27.6 (expérimental) — L'École de la Parole & Synesthésie (2026-07-27/28)

> ⚠️ **Statut expérimental** : vit uniquement dans `src/naulthene/cerveau/noyau.py` (gitignored, terrain d'essai local) et les modules `src/naulthene/audio/`, `salles_de_classe/cursus_parole.py`, `instruments/enregistreur_voix.py`, pas encore porté sur `agi_google_colab.py`.

Referme trois écarts entre l'hémisphère audio (v22.0-v26.0) et une vraie acquisition du langage ancrée dans le monde : la cible vocale était une table théorique jamais entendue par l'agent, le mot à nommer n'avait aucun rapport avec ce que l'agent regardait, et la dopamine multimodale écrasait un canal au profit de l'autre. Six correctifs successifs (v27.1-27.6), pour la plupart des diagnostics posés par l'utilisateur en observant l'Arène et les runs réels, ont ensuite affiné la mécanique — le résumé ci-dessous couvre l'état final, pas juste la version initiale.

* **La voix de l'utilisateur remplace la table théorique — sur les 8 paramètres physiques, pas seulement 2.** Un outil dédié (`instruments/enregistreur_voix.py`) enregistre plusieurs prises de la voix de l'utilisateur par mot du curriculum (`voix/<mot>/<mot>_NN.wav`, recadrage automatique du silence) ; `obtenir_pour_palier` tire une prise DIFFÉRENTE au hasard à chaque appel (v27.1) plutôt qu'une moyenne figée, pour que l'oreille entende la vraie variation naturelle d'une voix plutôt qu'un gabarit artificiel unique. À l'origine (v27.0), seuls F1/F2 étaient extraits par analyse LPC et appris ; un diagnostic de l'utilisateur sur un cerveau de 300 jours a montré que les 6 autres paramètres (f0, F3, durée, amplitude, largeurs de bande) restaient figés à leur valeur de naissance quel que soit le temps d'entraînement. v27.6 étend l'extraction acoustique aux 8 dimensions (pitch-tracking par autocorrélation pour f0, mesure directe pour durée/amplitude, F3 récupéré du même calcul LPC que F1/F2) et la perte d'apprentissage de `tete_vocale` contraint désormais dynamiquement toutes les dimensions effectivement fournies par la cible — plus aucune valeur théorique écrite en dur (`VOYELLES_CIBLES` retirée), y compris le repli sans banque enregistrée (dérivé de la référence `say` elle-même). La récompense se mélange en plus d'une distance spectrale MFCC↔MFCC comparant le son réellement synthétisé aux prises de référence. Sans banque enregistrée, le comportement de base reste inchangé (repli automatique sur `say`).
* **La synesthésie devient réelle, et stabilisée dans le temps.** Un lecteur générique (`LecteurCaseFrontale`) lit le mot à nommer directement dans la case devant l'agent — mur, porte, clé, but, vide, puis des syntagmes couleur+objet — au lieu d'un curriculum déroulé indépendamment de ce que l'agent voit. Correctif v27.4 (diagnostic utilisateur) : la cible ne change plus à chaque tick où le regard bouge, mais seulement après ~20 ticks consécutifs passés devant le même objet — sans quoi la cible vocale changeait jusqu'à 10×/seconde dans l'Arène, sans jamais laisser le temps d'associer un mot à l'objet regardé.
* **La dopamine devient unifiée entre les deux modalités, et proportionnelle à la méconnaissance.** Le `max(canaux visuels, canal vocal)` pré-v27.0 est remplacé par une agrégation probabiliste bornée qui laisse les deux canaux se renforcer sans s'écraser. Correctif v27.5 (diagnostic utilisateur, "boucle infinie de promotion vocale") : la contribution dopaminergique du canal vocal décroît désormais avec le palier déjà atteint (pleine à un mot neuf, ~10% à un mot maîtrisé) — un agent qui répète un mot déjà su ne reçoit plus le même shoot dopaminergique qu'un débutant, ce qui empêchait auparavant la dopamine de retomber assez pour motiver la progression sur MiniGrid.
* **Le rêve consolide enfin l'audio** : la nuit ne rejouait auparavant que la mémoire visuelle — le rêve rejoue désormais l'audio quand le lot tiré en contient (même rampe de prudence que l'apprentissage diurne).
* **Nouveau cursus dédié** : `salles_de_classe/cursus_parole.py` (`naulthene_parole.brain`), 900 jours × 800 ticks en 3 phases — Imprégnation totale (le professeur nomme systématiquement, corrige même quand l'agent a bon), Autonomie guidée (bascule matin/après-midi entre synesthésie et curriculum, guidage décroissant), Émancipation (synesthésie + syntagmes toute la journée, professeur presque silencieux).
* **Correctifs de restitution dans l'Arène** : la lecture audio en direct se chevauchait à chaque tick (10/s), produisant un crépitement continu indépendant du niveau d'apprentissage — la lecture est désormais espacée (~1.8s entre deux vocalisations, v27.2-27.3), laissant chaque son se terminer avant le suivant.

Voir [docs/CHANGELOG.md](docs/CHANGELOG.md) (entrées v27.0 à v27.6) pour le détail technique complet, et [docs/LANCEMENT.md](docs/LANCEMENT.md) pour le guide de lancement (enregistrement de la voix, commande du cursus).

### Nouveautés v26.0 (expérimental) — L'Arène augmentée (mini-IRM + télémétrie complète) (2026-07-27)

> ⚠️ **Statut expérimental** : vit dans `src/naulthene/instruments/arene_visuelle.py` et `lancer_arene.py`, tous deux versionnés (contrairement à `noyau.py`), immédiatement disponibles sur `PYTHONPATH=src python -m naulthene.instruments.lancer_arene`.

L'Arène fusionne en une seule fenêtre pygame ce qui vivait jusqu'ici dans deux outils séparés : observer l'agent bouger dans MiniGrid ET observer les activations de son cerveau — sur le **même** agent en mémoire, pas un second `charger_ou_naitre()` qui aurait divergé.

* **Mini-IRM en pygame pur** : une bande sous l'image MiniGrid affiche en direct les barres d'activation du bus latent à 3 étapes du tronc cérébral (vision/mémoire/pensée, une couleur par étape) — le pendant temps-réel du panneau 1 de `irm_cerveau.py`, mais rendu avec des primitives `pygame.draw` plutôt qu'en matplotlib. Mélanger pygame (SDL) et matplotlib (Tk/Qt/macosx) dans le même thread est fragile sur macOS — les deux se disputent la boucle d'événements native Cocoa — d'où le choix de tout garder dans un seul framework graphique.
* **Télémétrie complète** : le panneau de droite atteint la parité avec le bilan de nuit console (état mental, plasticité, jalons DoorKey, abnégation, mode décision, portes, potentiomètre, curiosité JEPA, viscéral, métabolisme, mémoire épisodique, erreur JEPA/thermostat). Les trois métriques qui n'existent QUE après une vraie nuit (plasticité base, souvenirs rejoués, thermostat de neurogenèse) sont remplacées par des **proxys continus recalculés à la volée** avec la même formule, explicitement marqués comme estimés — jamais confondus avec un vrai bilan nocturne.
* **Bandeau d'événement** : un changement de palier DoorKey (observable en direct, contrairement à une promotion de *niveau* MiniGrid) déclenche un bandeau temporaire. Une note affichée au démarrage documente explicitement qu'une promotion de niveau MiniGrid ne peut structurellement jamais se produire dans l'Arène — elle est décidée uniquement pendant une vraie nuit (`executer_nuit`), jamais appelée ici pour garantir que l'observation n'altère jamais le cerveau.

Garantie de non-altération inchangée : tout ajout reste de la lecture pure (`torch.no_grad()`, `agent.eval()` déjà en place), aucun nouvel appel à `executer_nuit`/`apprendre_journee`/`rever`/`declencher_neurogenese`.

### Nouveautés v26.0 (expérimental, §A.5 seul) — Cristallisation Souple (2026-07-27)

> ⚠️ **Statut expérimental** : vit uniquement dans `agi_local_test.py` (`NaultheneLinearSynaptique`), pas encore porté sur `agi_google_colab.py`. Premier chantier implémenté du plan v26.0 « Le Parent remplace le Programme » ([docs/AMELIORATION_V1.md](docs/AMELIORATION_V1.md)) — les autres chantiers (§A.1-A.4 durcissement JEPA, §B Parent Universel, §C rappel hippocampique, §D voix humaine) restent à l'état de proposition.

Protège de l'érosion nocturne les synapses matures — sollicitées fortement et régulièrement sur plusieurs nuits — sans jamais geler leur apprentissage diurne. Une seconde trace `myeline_cumul` accumule la myélinisation nuit après nuit (même patron de relaxation exponentielle que partout dans le projet, `ALPHA_CRISTAL = 0.95`) ; au-delà de `SEUIL_CRISTAL = 0.80`, la synapse devient `cristallisee` (cliquet à sens unique, jamais réversible).

* **Correctif « Falaise » sigmoïde** : plutôt qu'un plancher d'érosion rigide en tout-ou-rien, la protection d'une synapse cristallisée est une transition continue — `p_protection = sigmoid(K_RAIDEUR_CRISTAL * (myeline_cumul - SEUIL_CRISTAL))`, `K_RAIDEUR_CRISTAL = 10.0` — plus fidèle au principe du projet (régulation dynamique continue, jamais de règle en dur). Une synapse très éprouvée voit son érosion nocturne tendre vers zéro (ancrage indestructible des fondamentaux) ; une synapse jamais cristallisée s'érode normalement et finit élaguée en temps fini (zéro synapse fantôme).
* **Règle dissymétrique sommeil ≠ gradient** : la protection n'agit que sur l'érosion nocturne (`cycle_sommeil`). Le gradient diurne (`annexe_weight`, rétropropagation) reste **totalement inchangé**, cristallisée ou non — une synapse cristallisée continue d'apprendre et de se réviser si le monde change (nouvelle couleur de porte, nouvel angle), elle est juste protégée de mourir de silence pendant qu'elle ne sert pas.

Voir [docs/explications_readme.md §8.5](docs/explications_readme.md#85-cristallisation-souple-expérimental-agi_local_testpy-uniquement-v260) pour le détail algorithmique complet.

### Nouveautés v25.0 (expérimental) — Le Cerveau Bébé Développemental (0→4 ans) (2026-07-24)

> ⚠️ **Statut expérimental** : nouveau paradigme, vit dans `agi_local_test.py` (mécaniques ajoutées) + `professeur_gemma.py` (curriculum vocal étendu) + `cursus_bebe.py` (nouveau, orchestrateur), pas encore porté sur `agi_google_colab.py`. Distinct du Cursus Développemental par Ères (v23.0) : les deux paradigmes coexistent, chacun avec son propre `.brain` (`naulthene_bb.brain` vs `naulthene_cursus.brain`).

Vision bio-inspirée (Piaget / Dehaene) plutôt que RL classique : au lieu de mesurer le cursus en réussites de tâche, le bébé traverse **4 ans (1440 jours subjectifs × 3600 ticks/jour)** découpés en 5 phases d'âge, avec un principe directeur — **l'absence de notation pendant les 8 premiers mois est la véritable clé**. Donner une récompense trop tôt perturbe la construction des représentations visuelles et auditives ; pendant cette période, l'agent apprend de façon purement auto-supervisée (JEPA + Homéostasie + Curiosité), son seul moteur étant de prédire le monde et de satisfaire ses besoins biologiques.

**Tableau de Progression Développementale** :

| Phase (âge) | Jours | % Dodo | Monde visuel/moteur | Audio/vocal | Validation |
|-------------|-------|--------|---------------------|-------------|------------|
| Éveil des Sens (0-3 mois) | 1-90 | 70% | vision floue, réflexes | babil brut (palier 1) | 100% intrinsèque |
| Exploration Motrice (3-6 mois) | 91-180 | 60% | coordination œil-main | voyelles a/e/i/o/u (paliers 2-6) | 100% intrinsèque |
| Locomotion & Concepts (6-12 mois) | 181-360 | 50% | déplacements, objets | syllabes ba/ma/pa (paliers 7-9) | **feedback social dès jour 240** |
| Association Forte (12-24 mois) | 361-720 | 40% | navigation ciblée | mots papa/maman/porte (paliers 10-12) | +dopamine / −cortisol |
| Jeune Enfant (24-48 mois) | 721-1440 | 35% | planification complexe | combinatoire Action+Objet (paliers 13-14) | autonomie guidée |

* **Masquage de la récompense externe (jours 1-239)** : `recompense_env` est gelée à 0.0 dans `traiter_tick` (`masquer_recompense_externe=True`) — neutralise à la fois sa contribution à `recompense_interne` (Système 1/2) ET à `poids_evenement` (donc plus de choc dopaminergique "victoire", plus de `victoire_aujourdhui`, plus de promotion de niveau MiniGrid tant que le masquage est actif). JEPA, curiosité, homéostasie (r_bio) et vocal restent intacts — seul le signal RL externe est verrouillé.
* **Sommeil variable par phase** : le "% Dodo" du tableau ci-dessus devient le **plafond** du pourcentage de rêve nocturne (remplace `PLAGE_REVE_MAX` dans la formule de `pourcentage_reve`, voir `plafond_reve_bebe()`) — le pourcentage réellement rejoué reste émergent (plasticité × richesse de la journée), jamais une taille de batch fixe, seul son maximum suit l'âge du bébé.
* **Module "Parent" (jour 240+)** : feedback social vocal déterministe, sans appel Gemma par tick — un score de formants ≥ `SEUIL_PARENT_OUI` (0.45) déclenche un "Oui !" (renforce le choc dopaminergique déjà existant sur le score vocal), un score < `SEUIL_PARENT_NON` (0.15) déclenche un "Non !" (nouveau canal "cortisol", pousse activement la dopamine vers `DOPAMINE_MIN`, toujours reclippée dans `[DOPAMINE_MIN, DOPAMINE_MAX]`). Un second "Oui !" se déclenche quand une ressource bio est atteinte pendant une quête de survie active.
* **Curriculum vocal étendu** : `professeur_gemma.CURRICULUM_VOCAL` passe de 11 à 14 paliers (ajout du mot "porte" et d'une combinatoire minimale "ouvre porte"/"prends clé"), couvrant toute la roadmap babil→voyelles→syllabes→mots→combinatoire.

Toutes les nouvelles mécaniques sont **additives et neutres par défaut** (`masquer_recompense_externe=False`, `parent_actif=False`, `plafond_reve=None`) — aucune régression sur le Cursus par Ères (`cursus_developpemental.py`, inchangé), le mode standalone classique, l'Arène ou le daemon.

### Correctifs v24.0-fix1 à fix5 (expérimental) — École de Rattrapage Vocal & silence de l'Arène (2026-07-23/24)

> ⚠️ **Statut expérimental** : cinq correctifs successifs sur `agi_local_test.py`, `cursus_developpemental.py`, `persistance.py`, `lancer_arene.py`, tous découverts sur des runs réels (1000 jours puis relances). Détail complet dans [CHANGELOG.md](docs/CHANGELOG.md).

Après le premier run complet de 1000 jours du Cursus Développemental, inspection du `.brain` obtenu : **aucune promotion vocale en 1000 jours**, `porte_auditive` à norme exactement zéro — l'oreille n'avait strictement rien appris. Quatre bugs en cascade, chacun découvert en corrigeant le précédent :

* **fix1 — École de Rattrapage Vocal** : le seuil fixe de promotion (0.5) était trop haut pour un cerveau neuf, et l'érosion nocturne rasait le peu de gradient accumulé avant qu'il ait pu s'amorcer — un cercle vicieux. Remplacé par un seuil **progressif** (`seuil_jour_vocal_reussi`, 0.15 au palier 1 → 0.45 au palier 11) et une **érosion atténuée à 10%** sur les couches audio tant que le palier vocal reste bas. Validé : 3 promotions obtenues en 60 jours de test, contre 0 en 1000 jours avant le fix.
* **fix2 — Garde-fou** : ajout de `JOURS_MAX_SANS_PREMIERE_LETTRE = 100` — si le palier vocal n'a validé aucune voyelle après 100 jours, le cursus s'arrête proprement (sauvegarde incluse) plutôt que de tourner à vide jusqu'au bout.
* **fix3 — Correction du compteur du garde-fou** : le garde-fou comparait `etat.jour` (cumulatif depuis la naissance du cerveau) au lieu des jours écoulés dans la session courante — un vieux cerveau (970 jours vécus avant le fix1) se voyait couper la parole dès le premier jour de sa nouvelle tentative. Corrigé avec un compteur local à `lancer_cursus`, remis à zéro à chaque lancement.
* **fix4 — `integrateur_bio` exclu à tort** : le filtre de rétrocompatibilité introduit en v22.1 (pour gérer le passage `DIM_VECTEUR_BIO` 8→16) excluait `integrateur_bio` du chargement de façon **inconditionnelle**, sans jamais vérifier si le checkpoint avait déjà la bonne forme — tout `.brain` sauvegardé depuis la v22.1 perdait cette couche (réinitialisée aléatoirement) à *chaque* rechargement. Corrigé : l'exclusion ne se déclenche plus que si la forme réelle diffère de la forme attendue.
* **fix5 — L'Arène n'injectait aucune cible vocale** : `lancer_arene.py` appelait `traiter_tick` sans jamais passer de mot à répéter — `score_vocal` restait donc toujours `None` ("silence" systématique dans le panneau), quel que soit le niveau réel de l'agent. Corrigé : l'Arène injecte désormais la référence audio du palier vocal courant à chaque tick, via le même `CacheReferencesVocales` que le Cursus.

### Nouveautés v24.0 (expérimental) — L'Arène & Démo Live (2026-07-23)

> ⚠️ **Statut expérimental** : Phase 2 du plan à 3 phases (Cursus → Arène → boucle méta-évolutive), vit dans `agi_local_test.py`/`persistance.py`/`cursus_developpemental.py` (étendus) + `arene_visuelle.py`, `lancer_arene.py` (nouveaux), pas encore portée sur `agi_google_colab.py`.

Le Cursus Développemental (v23.0) faisait tourner l'agent seul pendant 1000 jours, mais sans jamais rien montrer ni sauvegarder — un cerveau qui a vécu 1000 jours disparaissait intégralement à la fin du script. La v24.0 corrige d'abord ce préalable, puis ajoute une **fenêtre graphique temps réel** :

* **Persistance du Cursus** : `cursus_developpemental.py` charge et sauvegarde désormais un cerveau via `PersistanceAnatomique` (fichier dédié `naulthene_cursus.brain`, jamais mélangé avec `naulthene_v21.brain` de la Cuve), à chaque nuit — un run interrompu (Ctrl+C, panne) reprend exactement où il en était, avec sa progression vocale (`palier_vocal`) désormais elle aussi sauvegardée.
* **L'Arène** (`lancer_arene.py`) : une seule fenêtre pygame composant l'image MiniGrid rendue en direct (`render_mode="rgb_array"`) et un panneau de télémétrie (dopamine, jauges biologiques, curriculum MiniGrid/DoorKey, ère et palier vocal courants). Le babil de l'agent est joué en temps réel dans les haut-parleurs.
* **Garantie de non-altération** : l'Arène observe sans jamais entraîner (`agent.eval()`, aucun appel à `executer_nuit`/`apprendre_journee`) — validé par comparaison directe des poids (`torch.equal`) avant/après un run d'observation, strictement identiques. Tu peux lancer l'Arène autant de fois que tu veux sans risque pour le `.brain`.

### Nouveautés v23.0 (expérimental) — Le Cursus Développemental par Ères (2026-07-23)

> ⚠️ **Statut expérimental** : nouvelle mécanique cognitive, vit dans `agi_local_test.py` (mode `vocal_isole` + constantes d'ères) + `lecons_vocales.py`, `cursus_developpemental.py` (nouveaux), pas encore portée sur `agi_google_colab.py`.

Jusqu'ici, l'apprentissage vocal ne se déclenchait que par une leçon manuelle ponctuelle (`client_professeur.py --palier N`, un humain choisit le palier). La v23.0 en fait un **programme de développement autonome de 1000 jours subjectifs**, organisé en 3 ères de difficulté croissante — exactement comme un enfant qui passe de la crèche à l'école primaire :

* **Ère Alternance (jours 1-399)** : chaque journée se scinde en un **matin** (MiniGrid pur, 200 ticks) et un **après-midi** (parole isolée, l'agent « au calme, écran noir » — vision à zéro, l'environnement MiniGrid explicitement en pause, aucun `env.step` appelé).
* **Ère Synesthésie (jours 400-599)** : le matin devient multimodal — MiniGrid **et** audio simultanés, le cerveau unifié gère les deux à la fois. L'après-midi étend le vocabulaire aux syllabes/mots.
* **Ère Intégration (jours 600-999)** : toute la journée est multimodale — l'agent verbalise une voyelle liée à l'action MiniGrid qu'il vient de jouer (mapping action→voyelle, une v1 volontairement minimale).

Le curriculum MiniGrid (`PROGRAMME`, Primaire→Doctorat) et le curriculum vocal (11 paliers, voyelles→syllabes→mots) progressent **en parallèle**, chacun par son propre mécanisme de promotion — les ères orchestrent *quand* chaque apprentissage est actif dans la journée, elles ne remplacent ni l'un ni l'autre. La promotion vocale réutilise le mécanisme 2+2 succès de `GestionnaireCursusAbnegation` (déjà utilisé pour les 7 paliers DoorKey), sur une instance totalement séparée, pilotée par le score de formants moyen du jour. Les références audio des voyelles sont générées une seule fois au démarrage (`say` → MFCC) et mises en cache, plutôt que ré-invoquées à chaque tick sur un run de centaines de milliers de ticks vocaux.

### Nouveautés v22.1 (expérimental) — Correction de l'Hémisphère Audio (2026-07-23)

> ⚠️ **Statut expérimental** : correctif de conception sur la v22.0, mêmes fichiers locaux, pas encore porté sur `agi_google_colab.py`.

Trois défauts détectés à la revue de la v22.0 (dont un critique) et corrigés :

* **La bouche apprend enfin (défaut 1, CRITIQUE)** : en v22.0, `tete_vocale` produisait des formants dont la sortie était détachée avant tout calcul — un score de récompense alimentait la dopamine, mais **aucun gradient dirigé** n'apprenait jamais à viser la cible. C'était un membre fantôme : la bouche bougeait au hasard. Une perte MSE supervisée (sur F1/F2, les dimensions réellement contraintes par la leçon) donne désormais un vrai signal d'apprentissage. **Validé expérimentalement** : le score de formants progresse de 0.0045 à 0.1111 sur 5 jours de leçon (×24 ticks).
* **L'oreille écoute vraiment (défaut 2)** : l'embedding sémantique du mot, qui était concaténé au son brut dans l'entrée de `porte_auditive`, aurait pu faire ignorer le son réel par le réseau (le concept parfait est plus facile à exploiter que l'acoustique bruitée). Il devient une **quête vocale** dans `vecteur_bio` (la cible à atteindre), jamais un cadeau en entrée — l'agent doit traduire ce qu'il perçoit vers la cible.
* **Le JEPA visuel est protégé (défaut 3)** : une tête prédictive `generateur_attente_audio`, séparée de la tête visuelle, avec un poids `coeff_jepa_audio` monté progressivement (quasi nul au premier tick audio) — la physique MiniGrid acquise sur 481 jours n'est jamais perturbée par un signal audio bruyant en début de leçon.
* **Rétrocompatibilité** : un bug de mismatch de forme sur `integrateur_bio` (conséquence du changement `DIM_VECTEUR_BIO` 8→16) a été détecté et corrigé pendant les tests — cette couche renaît désormais à neuf lors d'une greffe (décision assumée : elle n'avait quasiment rien appris sur le vrai cerveau de production).

### Nouveautés v22.0 (expérimental) — L'Hémisphère Auditif & Vocal (2026-07-23)

> ⚠️ **Statut expérimental** : comme les v18.0–v21.0, cette version n'existe que dans l'écosystème local (`agi_local_test.py` étendu + `hemisphere_audio.py`, `professeur_gemma.py`, `client_professeur.py` nouveaux, `persistance.py`/`daemon_cerveau.py` étendus), pas encore portée sur `agi_google_colab.py`.

* **Un véritable hémisphère audio, greffé dans le cerveau** : `porte_auditive` (l'OREILLE, miroir de `porte_visuelle`, double entrée MFCC⊕embedding sémantique) et `tete_vocale` (la BOUCHE, miroir de `tete_motrice`, 8 paramètres de synthèse par formants) — pas un module de traitement audio bricolé à côté. Les deux couches respectent les 4 points de synchro obligatoires (`__init__`, `fortifier_synapses`, `cycle_sommeil_global`, `declencher_neurogenese`).
* **Cerveau 100% multimodal unifié** (décision structurante de l'utilisateur) : vision et audio se fondent dans le *même* bus latent par simple somme, à chaque tick — pas de "mode audio" isolé du reste. L'agent voit et entend, bouge et vocalise simultanément.
* **Cortex auditif prédictif dès le départ** : le JEPA (modèle du monde) ne prédit plus seulement l'image suivante, mais aussi le son — `perte_jepa` fusionne la cible visuelle et la cible auditive, avec un vrai gradient qui remonte jusqu'à `porte_auditive`.
* **Récompense de formants, déterministe et instantanée** : Gemma (`gemma4:e4b` via Ollama) met ~8 à 30 secondes par réponse (mesuré) — totalement incompatible avec une récompense par tick RL. La récompense de babillage vient donc d'une distance de formants (numpy pur, immédiate) ; Gemma n'intervient qu'en professeur périodique, pour choisir la leçon (curriculum vocal à 11 paliers) et juger qualitativement en fin de leçon.
* **Babil entendu en temps réel** : chaque son produit par `tete_vocale` est synthétisé (synthèse par formants, cascade de résonateurs) et joué immédiatement dans les haut-parleurs — l'utilisateur entend l'agent babiller en direct pendant une leçon (`client_professeur.py`).
* **Greffe rétrocompatible** : les vieux `.brain` (sans couches audio) se chargent avec `strict=False` — l'agent garde tous ses acquis visuels/MiniGrid, les hémisphères audio naissent à neuf et s'apprennent par babillage. Un bug d'incompatibilité de l'optimiseur Adam après greffe a été détecté et corrigé pendant les tests.

### Nouveautés v21.0 (expérimental) — Le Cerveau Persistant en Cuve (2026-07-23)

> ⚠️ **Statut expérimental** : comme les v18.0/v19.0/v20.0, cette version n'existe que dans l'écosystème local (`agi_local_test.py` refactoré + trois nouveaux fichiers `persistance.py`, `daemon_cerveau.py`, `client_corps.py`), pas encore portée sur `agi_google_colab.py`.

* **Refactor en helpers partagés** : la boucle principale (~500 lignes jusque-là au niveau module) est extraite en un conteneur d'état `EtatCognitif` et quatre fonctions réutilisables (`initialiser_etat_cognitif`, `demarrer_journee`, `traiter_tick`, `executer_nuit`), consommées à l'identique par le mode standalone et par le daemon — refactor pur, sans changement de comportement (validé par comparaison de logs sur run déterministe).
* **`PersistanceAnatomique`** (`persistance.py`) : cristallise/ressuscite l'état complet du cerveau dans un fichier `.brain` — dimension du bus, poids et traces synaptiques, état de l'optimiseur, chimie viscérale, mémoire épisodique spatiale, curriculum et thermostat de neurogenèse. L'agent traverse un redémarrage de process avec son `tick_absolu`, sa dopamine, ses souvenirs et sa dimension de bus intacts, y compris après une neurogenèse.
* **`CuveDeMaintien`** (`daemon_cerveau.py`) : daemon socket TCP qui héberge le cerveau en continu. Trois états métaboliques : Éveil (connexion active), Sommeil (nuit complète ou micro-sieste), Cryostase (`socket.accept()` bloquant, CPU ~0% hors connexion). Modèle de temps **hybride** : une nuit complète se déclenche soit in-session dès qu'une journée subjective de ticks est accumulée, soit à la déconnexion si assez de vécu s'est accumulé depuis la dernière nuit ; sinon une micro-sieste (simple sauvegarde, sans érosion ni rêve) protège le cerveau d'une consolidation relancée à vide sur des sessions courtes.
* **`client_corps.py`** : pilote de session jetable. Limite assumée de cette itération : l'environnement MiniGrid tourne côté serveur (les détecteurs biologiques/spatiaux ont besoin des internes MiniGrid, intransmissibles par un simple flux pixels+action) — le découplage total du Corps est une évolution future.

### Nouveautés v20.0 (expérimental) — Mémoire Épisodique Spatiale & LTP Hebbien (2026-07-23)

> ⚠️ **Statut expérimental** : comme les v18.0/v19.0, cette version n'existe que dans `agi_local_test.py`, pas encore portée sur `agi_google_colab.py`.

* **`MemoireEpisodiqueSpatiale`** : nouvelle mémoire épisodique au sens propre (où/quand/quoi), distincte de `vecteurs_episodiques` existant (une moyenne glissante d'états latents, plus proche d'une mémoire de travail). Enregistre position + type + tick des ressources biologiques trouvées (v18.0/v19.0) ; persiste à travers les épisodes d'une même journée, ne se vide qu'au changement de niveau du `PROGRAMME`. Un rappel (distance normalisée + fraîcheur) est injecté dans le vecteur bio existant via `integrateur_bio` (`DIM_VECTEUR_BIO` passe de 6 à 8) plutôt que de créer un agent/encodeur parallèle.
* **LTP Hebbien** : `NaultheneLinearSynaptique` gagne une `trace_activation` (trace d'éligibilité accumulée à chaque tick) et une méthode `fortification_dopaminergique()` — sur chaque événement marquant (`poids_evenement > 0` : manger, franchir une porte, valider un palier...), les synapses récemment actives sont gravées instantanément dans `base_weight`, une vraie Potentiation à Long Terme pilotée par l'événement plutôt que par la seule moyenne journalière du pseudo-code initial.

### Nouveautés v19.0 (expérimental) — Métabolisme 20/80 & Forage 80/20 (2026-07-22)

> ⚠️ **Statut expérimental** : comme la v18.0, cette version n'existe que dans `agi_local_test.py`, pas encore portée sur `agi_google_colab.py`.

* **Moteur Métabolique 20/80** : le coût énergétique fixe de la v18.0 (`COUT_ACTION_METABOLIQUE`, constante unique) est remplacé par un calcul dynamique fusionnant un Effort Corporel (80% du poids, dépend du TYPE d'action MiniGrid réellement exécutée — tourner coûte peu, manipuler/pickup coûte cher) et un Effort Cognitif (20% du poids, dérivé de `force_planification` et de la profondeur du rollout `HORIZONS_PLANIFICATION` — le Système 2 pèse plus lourd en Mode Libre qu'en Mode Guidé).
* **Forage 80/20** : la Nourriture (uniquement) réapparaît désormais immédiatement après consommation, selon une distribution 80% à proximité d'un "Nid" (dérivé de la carte courante, jamais une coordonnée fixe codée en dur) / 20% dispersée aléatoirement sur la grille — l'Eau reste une ressource par épisode, sans respawn.

### Nouveautés v18.0 (expérimental) — Architecture Homéostatique Biologique (2026-07-22)

> ⚠️ **Statut expérimental** : cette version n'existe pour l'instant que dans `agi_local_test.py` (variante de test local sur Mac, non trackée par git — voir [Démarrage Rapide](#démarrage-rapide)). Elle n'a pas encore été portée sur `agi_google_colab.py`, le script de référence. Le portage aura lieu une fois la mécanique validée sur un run local suffisamment long.

* **`BiologicalHomeostasisEngine`** : trois jauges vitales (satiété, hydratation, stimulation) se dégradent à chaque tick selon la Théorie de la Réduction du Drive (Hull). Le déficit homéostatique $D(t)$ est la somme des écarts au carré à l'équilibre idéal (1.0) ; la récompense biologique `r_bio` est la réduction de ce déficit entre deux ticks — injectée directement dans le réservoir `TENEUR_DOPAMINE` existant plutôt que de créer un second système de dopamine parallèle.
* **`DetecteurRessourcesBiologiques`** : génération procédurale de sources de Nourriture/Eau sur la grille MiniGrid courante, via des `Ball` colorées (rouge = Nourriture, bleu = Eau) placées sur des cases vides aléatoires à chaque épisode — aucune sous-classe `WorldObj` custom, pour rester simple.
* **Génération autonome de quêtes de survie** : dès qu'une jauge passe sous 0.35, une quête intrinsèque (`SURVIVAL_FOOD` > `SURVIVAL_WATER` > `EXPLORATION_STIM`, dans cet ordre de priorité) est générée et son vecteur cible transmis au réseau.
* **`integrateur_bio`** (nouvelle couche `NaultheneLinearSynaptique`) : fusionne la pensée du réseau avec l'état viscéral (jauges + vecteur de quête, 6 dims) juste avant la tête motrice et le rollout mental — intégré à l'architecture `AGI_Naulthene` existante plutôt que de dupliquer un agent/encodeur parallèle.

### Nouveautés v17.0 — Volonté Émergente & Sous-Objectifs Intrinsèques (2026-07-22)

* **Décrochage précoce du Mode Libre** : le seuil qui désactive la béquille de guidage artificiel (`RECOMPENSE_APPROCHE_BUT`) descend du Palier 7 au **Palier 5** (Viser la Porte). L'agent affronte le vide de l'auto-détermination plus tôt, pendant qu'il travaille encore les paliers 5/6/7 sous le régime d'Abnégation.
* **`DetecteurCuriositeJEPA`** : en Mode Libre, une sous-quête intrinsèque est générée par le Modèle du Monde lui-même — quand l'erreur JEPA du tick dépasse $1.5\times$ la moyenne récente de l'agent (une "zone d'ombre" imprévue), une micro-récompense de curiosité comble le vide laissé par le retrait du guidage externe.
* **`ModuleSursautVolonte`** (le Muscle de la Volonté) : à 95% de la patience du jour, un sursaut se déclenche en Mode Libre — jamais une solution donnée, mais un boost dopaminergique ponctuel (`BOOST_SECOND_SOUFFLE`) et une extension mathématique de la patience de l'épisode (+50 ticks, plafonnée). Un seul sursaut par épisode.
* **Apprentissage de la récurrence** : si l'épisode se solde par une vraie victoire ($\text{recompense\_env} > 0$) après avoir consommé un Sursaut, la `patience_min` de base augmente **définitivement** — l'agent apprend par l'expérience que l'effort prolongé mène à la victoire, pas seulement le temps d'une journée.

### Nouveautés v16.0 — Thermostat Multimodal & Patience par Abnégation (2026-07-22)

* **`ThermostatCinetiqueMultimodal`** : la pénalité de stagnation de la v15.0 est désormais *modulée* par le contexte multimodal du tick plutôt qu'appliquée uniformément. Déplacement libre (rien en main, rien en face) → pénalité pleine ($\times 1.00$). Objet transporté (`carrying`) → fortement atténuée ($\times 0.30$, arrêts légitimes). Face à un objet clé (`Key`/`Door`/`Goal`) avec une action de ciblage (`pickup`/`toggle`) → quasi effacée ($\times 0.05$, le temps de traiter l'interaction).
* **`ModuleAcceptationAbnegation` & `GestionnaireCursusAbnegation`** : la promotion de palier DoorKey abandonne le taux de réussite journalier ($\ge 80\%$) au profit d'un compteur cumulatif de **4 succès** répartis en 2 sous-seuils. Sous-Seuil 1 (Amorçage, 2 succès, patience de base) puis Sous-Seuil 2 (Consolidation/Abnégation, 2 succès supplémentaires, patience étirée $\times 1.6$) — l'agent apprend que l'effort prolongé est une condition naturelle des sous-étapes complexes, pas un échec.

### Nouveautés v15.0 — Planification Non-Linéaire, Pression Cinétique & Patience Adaptative (2026-07-22)

* **Planification Multi-Échelle (Sauts Temporels)** : `simuler_futur_et_planifier` abandonne la chaîne stricte $t+1 \to t+2 \to t+3$ au profit d'horizons à pas exponentiel ($t+1, t+3, t+7$). Le premier horizon branche sur les 7 actions réelles ; les horizons suivants comblent l'écart de ticks en suivant le réflexe glouton de la politique, puis sont évalués à leur point d'arrivée — complexité toujours linéaire, jamais d'explosion combinatoire. La valeur retenue est la somme actualisée ($\gamma^{\text{horizon}}$) des valeurs évaluées à *chaque* horizon.
* **`ThermostatCinetique` (Pression Cinétique)** : détecteur générique, agnostique de la carte, qui pénalise l'immobilité stricte et le piétinement (aller-retour entre positions déjà visitées récemment). L'immobilité devient sous-optimale par construction du signal de récompense plutôt que par une règle écrite en dur.
* **`ModuleAcceptationAdaptative` (Potentiomètre d'Acceptation)** : la patience maximale tolérée par épisode (avant abandon volontaire/troncature) est recalculée chaque jour à partir du taux de succès récent et de la vitesse des succès passés — remplace un plafond de ticks fixe. Un abandon par patience applique une friction dopaminergique douce dédiée, jamais un choc négatif : l'agent accepte lucidement l'échec au lieu de le subir comme un traumatisme.

### Nouveautés v14.0 — Rêves Adaptatifs & Planification Étendue à 3 Pas (2026-07-22)

* **Consolidation Nocturne à Porosité Adaptative** : Suppression de la taille de batch de rêve fixe (`64`). La fraction rejouée la nuit ($0.01\% \to 60\%$) dérive désormais de la plasticité basale ($\text{Plasticité}$) et de la richesse importance moyenne de la journée ($\text{Richesse}$).
* **Système 2 (Horizon 3 Pas)** : Simulation mentale poussée à $t+3$. Pour éviter l'explosion combinatoire ($7^3 = 343$ branches), le pas 1 évalue les 7 actions réelles, tandis que les pas 2 et 3 suivent le réflexe de la politique. La valeur retenue est la somme actualisée des prédictions.
* **`DetecteurFranchissementPortes`** : Module générique détectant le franchissement de portes ouvertes pour attribuer une micro-décharge dopaminergique.
* **`DetecteurProgresPersonnel`** : Génération autonome de quêtes ("Ai-je battu mon record de proximité au But cet épisode ?") sans aucun code en dur spécifique à une carte.

### Nouveautés v13.0 — Décision Autonome & Mode Libre (2026-07-22)

* **Béquille vs Auto-Détermination** : Le guidage artificiel vers l'objectif est retiré dès la première validation du Palier 7.
* **Relais Méta-Cognitif** : En Mode Libre, `force_planification` monte à **0.85** (poids accru du Système 2) et `coeff_entropie` augmente à **0.06** pour maintenir une exploration active.

### Nouveautés v12.0 — Cursus à 7 Paliers & Correctif d'Épisodes (2026-07-22)

* **Extension du Cursus Collège** : Division de la tâche `DoorKey` en **7 Paliers** : `Regarder` $\to$ `S'approcher` $\to$ `Toucher/Prendre` $\to$ `Transporter` $\to$ `Viser la Porte` $\to$ `Déverrouiller` $\to$ `Franchir & Sortir`.
* **Correctif des Épisodes Tronqués** : Résolution du bug `0/0 épisodes (maîtrise: N/A)` causé par la fin de journée à $t=250$. Augmentation du temps de journée à **400 ticks**.

### Nouveautés v11.0 — Réservoir Dopaminergique V3 (2026-07-22)

* **Homéostasie par Triplet de Forces** : Remplacement du tonus fixe par un réservoir dynamique (0.001 à 10.0) régi par la *Friction* (décroissance quotidienne), le *Choc* (succès) et le *Ressort* (reset nocturne vers 5.0).
* **Empreinte de l'Enfance** : Modulation de l'intensité d'apprentissage par la taille du Bus visuel.

---

## 🛠️ Plan d'Action

Le plan de développement se lit aujourd'hui à travers trois documents complémentaires :
[docs/Parcourt_readme.md](docs/Parcourt_readme.md) (guide pratique des 4 parcours d'entraînement),
[docs/AMELIORATION_V1.md](docs/AMELIORATION_V1.md) (pistes d'évolution de l'architecture) et
[docs/CHANGELOG.md](docs/CHANGELOG.md) (ce qui a déjà été livré, version par version).

> *Note : ce paragraphe renvoyait auparavant à un fichier `plan_creat.md` qui n'a jamais existé
> dans le dépôt — lien mort corrigé en v29.1.*

---

## 🧠 Architecture Cognitico-Biologique Complète

L'agent **Naulthène** repose sur deux systèmes interconnectés — **C1** (le cerveau automatique et réflexe) et **C2** (le néo-cortex analytique) — orchestrés par une régulation neurobiologique, et alimentés depuis la v29.0 par les **cinq sens**.

```
   LES 5 SENS (v29.0)          gourmandise      entrée dans le cerveau
   ┌───────────────────────────────────────────────────────────────┐
   │ 👁  Vue      (147 dims)     extrême    →  porte_visuelle   ┐   │
   │ 👂 Ouïe     (130 MFCC)     élevée     →  porte_auditive   ├─► bus_latent
   │ ✋ Toucher  (4 dims)       moyenne    →  vecteur_bio  ┐   ┘   │
   │ 👃 Odorat   (2 dims)       faible     →  vecteur_bio  ├─► integrateur_bio
   │ 👅 Goût     (2 dims)       faible     →  vecteur_bio  ┘       │
   └───────────────────────────────┬───────────────────────────────┘
                                   v
        ┌──────────────────────────────────────────────────────────┐
        │ C1 — LE CERVEAU AUTOMATIQUE & RÉFLEXE   (léger, ~0 coût)  │
        │  • Compresse les 5 sens en un latent compact (bus_latent) │
        │  • Chimie & émotions : dopamine, homéostasie biologique   │
        │  • Réflexe moteur immédiat (tete_motrice), latence zéro   │
        │  • Mémoire distillée : base_weight de chaque synapse      │
        └───────────┬──────────────────────────────────▲───────────┘
                    │ état DÉJÀ COMPRESSÉ              │ distillation
                    │ (jamais les pixels bruts)        │ C2 ──► C1
                    v                                  │ (chaque nuit)
        ┌───────────┴──────────────────────────────────┴───────────┐
        │ C2 — LE NÉO-CORTEX                     (lourd, coûteux)   │
        │  • JEPA / modèle du monde : prédit Z(t+1) — l'Intuition   │
        │  • Simulation mentale multi-échelle (sauts t+1, t+3, t+7) │
        │  • Mémoire épisodique spatiale (où / quand / quoi)        │
        └───────────────────────────┬──────────────────────────────┘
                                    │
            +-----------------------+-----------------------+
            |                                               |
            v                                               v
+-----------+-----------+                       +-----------+-----------+
|   SYSTÈME 1 (Instinct)|                       |   SYSTÈME 2 (Raison)  |
|  Policy Network (RL)  |                       | Rollout Multi-Échelle |
|   = la tête de C1     |                       |   (Sauts t+1,t+3,t+7) |
+-----------+-----------+                       +-----------+-----------+
            |                                               |
            +-----------------------+-----------------------+
                                    |
                                    v
                     +--------------+--------------+
                     | Arborage & Prise de Décision |
                     |  (Poids: force_planif)      |
                     +--------------+--------------+
                                    |
                                    v
                     +--------------+--------------+
                     |  Action exécutée dans le Mde|
                     +--------------+--------------+
                                    |
                                    v
                     +--------------+--------------+
                     |   Réservoir Dopaminergique   |
                     |   & Consolidation Nocturne  |
                     +-----------------------------+

```

### 1. Système 1 (Instinctif / RL)

Un réseau d'Acteur-Critique (PPO/A2C) qui projette l'état latent du JEPA directement vers la distribution de probabilité des 7 actions fondamentales (`Move Forward`, `Turn Left`, `Turn Right`, `Pick Up`, `Drop`, `Toggle`, `Done`).

### 2. Système 2 (Raisonnement / Rollout Multi-Échelle Non-Linéaire, depuis v15.0)

Plutôt qu'une chaîne stricte pas-à-pas $t+1 \to t+2 \to t+3$, l'agent simule les conséquences futures de ses choix par **sauts temporels exponentiels** ($t+1, t+3, t+7$) :

* **Horizon $t+1$** : Branching sur l'ensemble des 7 actions réelles — c'est la décision évaluée maintenant.
* **Horizons suivants ($t+3$, $t+7$)** : Le rollout comble l'écart de ticks avec l'horizon précédent en suivant le propre réflexe du réseau (argmax de la tête motrice, sans ré-instancier de nouvelles branches à chaque niveau), maintenant une complexité algorithmique linéaire $O(7 \times \sum \text{écarts})$ — jamais l'explosion combinatoire $7^N$ d'un rollout pas-à-pas branché à chaque étage.
* **Évaluation** : La valeur du futur imaginé est une somme actualisée ($\gamma^{\text{horizon}}$) des prédictions de récompenses du JEPA évaluées à *chaque* horizon — un chemin qui traverse un bon état à $t+3$ compte, même si $t+7$ reste incertain. Cela donne au Système 2 une vision de tendance à moyen terme (utile sur les longs couloirs de MultiRoom/Doctorat) sans calculer chaque micro-état intermédiaire.

### 3. Le Bus Sensoriel & la hiérarchie des 5 sens (depuis v29.0, expérimental)

Chaque sens est capté puis traduit en signal électrique unifié par un **interpréteur** (`src/naulthene/cerveau/bus_sensoriel.py`), mais tous ne coûtent pas le même prix — et c'est la **combinaison de leur diversité** qui fait émerger une compréhension du monde plutôt qu'une simple co-occurrence de signaux :

| Sens | Gourmandise | Rôle cognitif & vital | Chemin dans le cerveau |
| --- | --- | --- | --- |
| **Vue** (147 dims) | **Extrême** (bande passante massive) | Cartographie spatiale, géométrie, prédiction d'objets | `porte_visuelle` → `bus_latent`, moteur principal du JEPA |
| **Ouïe** (130 MFCC) | **Élevée** (traitement temporel & séquentiel) | Analyse du danger, langage, communication | `porte_auditive` → `bus_latent`, JEPA audio à tête séparée |
| **Toucher** (4 dims) | **Moyenne** (retour de force) | Proprioception, contact immédiat, objet en main | queue du `vecteur_bio` → `integrateur_bio` |
| **Odorat** (2 dims) | **Faible** (analyse chimique à distance) | Détection de ressource avant même de la voir | queue du `vecteur_bio` → `integrateur_bio` |
| **Goût** (2 dims) | **Faible** (analyse chimique de contact) | Validation des ressources ingérées (rémanence ~10 ticks) | queue du `vecteur_bio` → `integrateur_bio` |

> **Pourquoi les sens faibles n'entrent pas dans le bus latent** : seuls la vue et l'ouïe ont une porte synaptique sommée dans `bus_latent`, donc une place dans la **cible JEPA**. Le toucher et la chimie arrivent par la queue du `vecteur_bio`, juste avant la décision. C'est ce qui garantit qu'ajouter trois canaux bruités ne perturbe jamais le modèle du monde d'un cerveau déjà entraîné sur des centaines de jours — `perte_jepa` continue de comparer le bus prédit au bus réel de la **vision seule**.

### 4. JEPA : de l'outil visuel à l'Intuition globale

JEPA n'est pas seulement un filtre pour la vue, c'est **l'architecture de l'Intuition**. Pour la vue, il prédit à quoi ressemblera l'espace latent de la scène suivante sans calculer chaque pixel — c'est la physique de l'environnement. Au niveau global, c'est la capacité du système à anticiper *« ce qui devrait arriver »* dans l'espace compressé où tous les sens se rejoignent. Et quand la perception ne correspond pas à la prédiction, le système ressent une **surprise** (erreur JEPA) : elle nourrit la stimulation du moteur homéostatique, déclenche une sous-quête de curiosité (`DetecteurCuriositeJEPA`) et alimente le thermostat de neurogenèse.

### 5. La boucle de distillation $C2 \to C1$ (l'apprentissage par le sommeil)

C'est la pièce maîtresse du système — et elle **n'a pas eu besoin d'être ajoutée en v29.0** : elle était déjà entièrement réalisée par le cycle de vie de `NaultheneLinearSynaptique`. C'est exactement le mécanisme d'apprendre à conduire : au début C2 consomme une énergie monstre à chaque geste ; quelques mois plus tard C1 conduit sans qu'on ait à y penser.

```
          [ EXPÉRIENCE DIURNE — C2 aux commandes ]
          • Actions complexes guidées par la planification / JEPA
          • Le gradient du jour s'accumule dans annexe_weight
                                 │
                                 ▼
          [ CONSOLIDATION NOCTURNE — le Rêve ]
          1. Rejeu des souvenirs à haute importance (rêve adaptatif)
          2. Transfert : base_weight += annexe_weight    (C2 ──► C1)
          3. Érosion sélective + Cristallisation Souple (v26.0)
                                 │
                                 ▼
          [ RÉFLEXE ANCRÉ DANS C1 ]
          • La fois suivante, C1 exécute via base_weight, quasi gratuitement
          • C2 est libéré pour de NOUVEAUX apprentissages
```

Les synapses sollicitées de façon répétée par C2 voient leur trace de myéline se consolider jusqu'à être **définitivement figées** dans `base_weight` par la Cristallisation Souple — le geste devient un réflexe, et le néo-cortex n'a plus à être dérangé pour lui.

---

## 🎓 Cursus Académique & Paliers Comportementaux

Pour éviter le problème du *Sparse Reward* dans les environnements complexes, l'apprentissage repose sur la décomposition en **7 Paliers Cognitifs** (appliqués notamment au Collège / `DoorKey`) :

| Palier | Nom | Condition de Validation |
| --- | --- | --- |
| **1** | **Regarder** | Orienté vers la clé ou la porte dans le champ de vision |
| **2** | **S'approcher** | Distance à la clé $< 2$ cases |
| **3** | **Toucher / Prendre** | Clé présente dans l'inventaire de l'agent |
| **4** | **Transporter** | Déplacement sur $> 3$ cases tout en maintenant la clé |
| **5** | **Viser la Porte** | Positionnement adjacent à la porte verrouillée |
| **6** | **Déverrouiller** | Exécution de l'action `Toggle` face à la porte |
| **7** | **Franchir & Sortir** | Traversée du trou de la porte et contact avec l'objectif |

> **Promotion par Abnégation (depuis v16.0)** : la promotion d'un palier au suivant n'est plus décidée par un taux de réussite journalier ($\ge 80\%$), mais par un compteur cumulatif de **4 succès** répartis en 2 sous-seuils — voir [Pression Cinétique Multimodale & Patience par Abnégation](#pression-cinétique-multimodale--patience-par-abnégation).
>
> **Mode Libre (décrochage précoce depuis v17.0)** : le guidage artificiel se désactive dès que `palier_cible >= 5` (Viser la Porte), au lieu d'attendre la maîtrise complète du Palier 7 — l'agent est confronté à l'auto-détermination plus tôt, pendant qu'il travaille encore les paliers 5/6/7. L'agent passe en `Mode_Libre = 1`. `force_planification` monte à $0.85$ et `coeff_entropie` à $0.06$. Voir [Volonté Émergente](#volonté-émergente--sous-objectifs-intrinsèques--sursaut) pour ce qui remplace le guidage perdu.

---

## 🧪 Moteur Émotionnel & Réservoir Dopaminergique

La motivation de l'agent n'est pas statique ; elle est régie par un réservoir homéostatique $D_t \in [0.001, 10.0]$ :

$$\frac{dD}{dt} = \underbrace{-\alpha (D_t - 0.001)}_{\text{Friction (Spleen)}} + \underbrace{\beta \cdot R_{\text{interne}} \cdot (10.0 - D_t)}_{\text{Choc (Plaisir de Découverte)}}$$

Chaque nuit, pendant la phase de sommeil :

$$D_{\text{matin}} = D_{\text{soir}} + \gamma (5.0 - D_{\text{soir}}) \quad \text{(Ressort Homéostatique)}$$

* **Sous-motivé ($D < 3.5$)** : La plasticité basale chute ($< 0.40$), gelant les poids synaptiques pour éviter le désapprentissage ou la sur-correction.
* **Motivé ($D > 6.5$)** : La plasticité monte à $1.00$, maximisant l'incorporation de nouveaux souvenirs lors du rêve.

---

## 💤 Algorithme de Rêve Nocturne Adaptatif

Contrairement aux approches de Replay Buffer classique à taille fixe, Naulthène calcule sa dose de sommeil paradoxal en fonction de son activité diurne.

$$\text{Pourcentage Rêvé} = 0.01\% + 60\% \times \text{Plasticité}_{\text{base}} \times \text{Richesse}_{\text{journée}}$$

Où $\text{Richesse}_{\text{journée}} = \min\left(1.0, \frac{\bar{I}_{\text{journee}}}{\text{IMPORTANCE\_REF}}\right)$.

* **Journée creuse / Aphasie** : $0$ à $2\%$ des souvenirs réexécutés (économie d'énergie synaptique).
* **Journée d'apprentissage intense** : Jusqu'à $60\%$ des transitions rejouées avec calcul d'attente à partir des tenseurs bruts (recalcul complet des gradients).

---

## 🧭 Détecteurs Génériques d'Intention & Quêtes Auto

Afin de dépasser la logique de règles écrites à la main, l'agent intègre deux détecteurs passifs agnostiques de la carte :

1. **`DetecteurFranchissementPortes`** : Analyse l'état spatial de la grille. Attribue une micro-récompense ($\delta = +0.05$) la première fois que les coordonnées de l'agent coïncident avec une case de type `Door` à l'état `open`.
2. **`DetecteurProgresPersonnel`** : Maintient un registre des records de proximité spatiale à l'objectif au cours de l'épisode. Chaque saut vers un nouveau minimum de distance Manhattan/Euclidienne génère une micro-émotion positive, stimulant la progression dans les grands labyrinthes (Doctorat / `MultiRoom`).

---

## 🏃 Pression Cinétique Multimodale & Patience par Abnégation

Trois mécaniques génériques (les deux premières introduites en v15.0, affinées en v16.0 ; la troisième nouvelle en v16.0), actives sur tous les niveaux du cursus (la troisième spécifique à DoorKey), qui traduisent une "envie de bouger" contextualisée et une gestion de l'abandon contrôlé qui apprend la persévérance par étapes.

### 1. `ThermostatCinetiqueMultimodal` — Pression Cinétique Contextualisée (v16.0)

Calcule d'abord une pénalité **brute** de stagnation, identique à la v15.0 :

* **Immobilité stricte** : rester sur la même case entre deux ticks coûte $2 \times$ la pénalité de base.
* **Piétinement** : revenir sur une case déjà visitée dans la fenêtre récente (6 derniers ticks) coûte une pénalité croissant géométriquement avec le nombre d'occurrences ($1.5^{\text{occurrences}}$).

Puis **module** cette pénalité brute par le contexte multimodal du tick (`facteur_attenuation_multimodal` $\in [0, 1]$) plutôt que de l'appliquer à plein partout :

| Contexte | Condition | Facteur | Effet |
| --- | --- | --- | --- |
| **Déplacement Libre** | Rien en main, rien en face | $\times 1.00$ | Pénalité pleine — stagner ici est de la léthargie |
| **Manipulation** | `carrying` non nul (objet transporté) | $\times 0.30$ | Fortement atténuée — transporter justifie des arrêts |
| **Interaction Vis-à-Vis** | Face à `Key`/`Door`/`Goal` + action `pickup`/`toggle` | $\times 0.05$ | Quasi effacée — laisse le temps de traiter l'interaction |

L'immobilité reste sous-optimale par construction du signal de récompense, mais ne pénalise plus les comportements légitimes (s'arrêter pour ouvrir une porte) de la même façon qu'une vraie léthargie.

### 2. `ModuleAcceptationAbnegation` — Potentiomètre d'Acceptation (Patience Évolutive)

Remplace un plafond de ticks par épisode fixe par un seuil de patience $\tau_{\text{patience}}$ recalculé chaque jour :

$$\tau_{\text{patience}} = \Big(\text{patience}_{\min} + \big(0.7 \cdot S_{\text{hist}} + 0.3 \cdot V_{\text{hist}}\big) \times (\text{patience}_{\max} - \text{patience}_{\min})\Big) \times \text{facteur\_complexite}$$

Où $S_{\text{hist}}$ est le taux de succès sur les 20 derniers épisodes, $V_{\text{hist}}$ un facteur dérivé de la vitesse (en ticks) des succès passés, et `facteur_complexite` (nouveau en v16.0) provient du `GestionnaireCursusAbnegation` ci-dessous — il étire la patience de base lors des sous-étapes plus exigeantes.

Quand le compteur de ticks de l'épisode dépasse ce seuil sans conclusion naturelle de l'environnement, l'agent déclenche une **troncature volontaire (abandon lucide)** : il accepte l'échec courant pour préserver ses ressources cognitives, avec une **friction dopaminergique douce** dédiée (`TAUX_FRICTION_DOUCE_ABANDON`) plutôt qu'un choc négatif traumatique.

### 3. `GestionnaireCursusAbnegation` — Promotion de Palier en 2 Sous-Seuils (v16.0, DoorKey uniquement)

Remplace la promotion de palier par taux de réussite journalier ($\ge 80\%$) par un compteur cumulatif de **4 succès**, indépendant des frontières de journée :

| Sous-Seuil | Nom | Succès requis | Facteur de complexité (patience) |
| --- | --- | --- | --- |
| **1** | Amorçage | 2 | $\times 1.0$ (base) |
| **2** | Consolidation / Abnégation | 2 | $\times 1.6$ (`COEFF_ABNEGATION_SOUS_SEUIL_2`) |

Le Sous-Seuil 1 valide l'acquisition de base du palier. Le Sous-Seuil 2 exige 2 succès supplémentaires sous une patience étirée : l'agent doit démontrer qu'il peut persévérer plus longtemps sur ce même palier avant d'être promu au suivant. Le palier n'est promu qu'après les 4 succès (2+2) — l'agent apprend que l'effort prolongé est une condition naturelle des sous-étapes complexes, pas un échec à corriger prématurément.

---

## 🕊️ Volonté Émergente : Sous-Objectifs Intrinsèques & Sursaut

Trois mécaniques introduites en v17.0, actives uniquement en Mode Libre (désormais accessible dès le Palier 5, voir [Cursus Académique & Paliers Comportementaux](#cursus-académique--paliers-comportementaux)), qui traduisent l'objectif de faire émerger une volonté propre à l'agent plutôt que de la lui prescrire.

### 1. `DetecteurCuriositeJEPA` — Sous-Quêtes Intrinsèques

Le Mode Libre retire toute récompense de guidage externe (`RECOMPENSE_APPROCHE_BUT`) — un grand vide que l'agent doit combler lui-même. Ce détecteur générique transforme une **surprise du Modèle du Monde** en sous-objectif :

* Compare l'erreur JEPA du tick courant à la moyenne glissante des 50 derniers ticks.
* Si l'erreur dépasse $1.5\times$ (`FACTEUR_SEUIL_SURPRISE`) cette moyenne — une "zone d'ombre", un état que le JEPA n'a pas su anticiper — une micro-récompense de curiosité ($\delta = 0.04$) est accordée.

Distinct de `dopamine_curiosite` (scaling continu et global de la teneur en dopamine par l'erreur JEPA, déjà existant) : ce détecteur ne produit un signal que sur un **dépassement relatif**, un vrai déclencheur de sous-quête plutôt qu'un facteur d'échelle permanent.

### 2. `ModuleSursautVolonte` — Le Muscle de la Volonté

Quand l'agent a consommé 95% de sa patience du jour (`SEUIL_DECLENCHEMENT_SURSAUT`) sans que l'épisode ne conclue, un **sursaut** se déclenche — jamais une solution donnée (pas de béquille de triche), mais un renfort de ses propres ressources :

1. Un boost dopaminergique ponctuel lié à l'effort (`BOOST_SECOND_SOUFFLE = 0.5`).
2. Une extension mathématique de la patience de l'épisode courant (`EXTENSION_PATIENCE_SURSAUT = 50` ticks, plafonnée à `PATIENCE_MAX`).

Un seul sursaut par épisode — ce n'est pas un mécanisme qui se répète en boucle jusqu'à épuisement total de la patience maximale.

> **Omission assumée** : la spécification initiale prévoyait aussi un "chuchotement d'indice visuel" (illuminer temporairement l'objet pertinent dans le champ de vision). Cela demanderait de modifier l'observation renvoyée par MiniGrid à l'agent — hors de portée de l'architecture actuelle sans toucher au moteur de rendu de l'environnement. Le sursaut reste donc purement interne (dopamine + temps), jamais une correction de la perception.

### 3. Apprentissage de la Récurrence

Si l'épisode se solde par une **vraie victoire** ($\text{recompense\_env} > 0$) après avoir consommé un Sursaut de Volonté, `ModuleAcceptationAbnegation.augmenter_patience_de_base_definitivement()` augmente la `patience_min` de base **de façon permanente** (`BOOST_PATIENCE_MIN_PAR_RECURRENCE = 10`, jamais repris). L'agent apprend par la récurrence que l'effort prolongé mène à la victoire — une trace durable, pas seulement une moyenne glissante qui finira par s'estomper.

---

## 🧬 Architecture Homéostatique Biologique (expérimental)

> ⚠️ **Uniquement dans `agi_local_test.py`** (voir [Nouveautés v19.0](#nouveautés-v190-expérimental--métabolisme-2080--forage-8020-2026-07-22) et [v18.0](#nouveautés-v180-expérimental--architecture-homéostatique-biologique-2026-07-22)), pas encore portée sur `agi_google_colab.py`.

Trois jauges vitales complètent le réservoir dopaminergique existant, sans le remplacer, en s'inspirant de la Théorie de la Réduction du Drive (Hull, 1943) : la motivation naît de la réduction d'un manque physiologique, pas seulement d'un signal de récompense externe.

### 1. `BiologicalHomeostasisEngine` — Jauges Vitales & Métabolisme

| Jauge | Rôle | Taux de dégradation par tick |
| --- | --- | --- |
| **Satiété** | Nourriture / énergie motrice | $-0.008 \times (1 + \text{effort métabolique})$ |
| **Hydratation** | Fluide informationnel | $-0.005$ (constant) |
| **Stimulation** | Découverte / complexité | $-0.012$ + bonus de nouveauté (case inédite + erreur JEPA) |

Le déficit homéostatique global :

$$D(t) = (1 - \text{satiete})^2 + (1 - \text{hydratation})^2 + (1 - \text{stimulation})^2$$

$$r_{\text{bio}} = D(t-1) - D(t)$$

`r_bio` est positif quand l'agent comble un manque (ex: mange), négatif s'il continue de se dégrader. Contrairement au pseudo-code initial qui introduisait un second réservoir de dopamine indépendant, `r_bio` est injecté dans `TENEUR_DOPAMINE` (déjà existant) via le même mécanisme `poids_evenement`/`TAUX_CHOC_BASE` que les autres détecteurs — une seule notion de motivation, jamais deux qui se chevauchent.

### 2. Moteur Métabolique 20% Cerveau / 80% Corps (v19.0)

L'effort métabolique qui alimente la dégradation de la satiété n'est plus une constante fixe (v18.0) mais une fusion pondérée :

$$\text{effort} = 0.80 \times \text{cout\_corps}(\text{action}) + 0.20 \times \text{cout\_cerveau}(\text{force\_planification})$$

* **Coût Corporel (80%)** : dépend du TYPE d'action MiniGrid réellement exécutée — tourner (`left`/`right`) coûte $0.2$, avancer $0.5$, manipuler (`pickup`/`drop`) $0.8$ (le plus cher), `toggle` $0.6$, `done` $0.1$ (quasi inaction). Recalé sur les vrais indices `Actions.*` du projet, pas sur un mapping numérique arbitraire.
* **Coût Cérébral (20%)** : $\min(1.0,\ \text{force\_planification} \times \sum(\text{HORIZONS\_PLANIFICATION}) / 10)$ — en Mode Libre (`force_planification=0.85`), le Système 2 pèse structurellement plus lourd qu'en Mode Guidé (`0.5`), reflétant la vraie profondeur fixe du rollout mental (horizons 1+3+7=11), sans inventer une notion de "profondeur MCTS variable" absente de l'architecture réelle.

### 3. `DetecteurRessourcesBiologiques` — Ressources Procédurales & Forage 80/20

MiniGrid n'a pas d'objets Nourriture/Eau natifs. Ce détecteur réutilise `Ball` avec une couleur dédiée par ressource (rouge = Nourriture, bleu = Eau, `NB_SOURCES_FOOD`/`NB_SOURCES_WATER` par épisode), placées sur des cases vides aléatoires à chaque `reinitialiser_episode` — cohérent avec les autres détecteurs génériques (aucune carte codée en dur). La ressource est retirée de la grille (`grid.set(x, y, None)`) dès qu'elle est consommée.

**Forage 80/20 (v19.0)** : contrairement à la v18.0 où une ressource consommée disparaissait définitivement, la Nourriture (uniquement — l'Eau ne respawn pas) réapparaît immédiatement après consommation :

* **80%** : sur une case libre à proximité (±1 case) d'un "Nid" — la première case vide trouvée à l'initialisation de l'épisode, jamais une coordonnée fixe codée en dur, pour rester agnostique de la carte et fonctionner identiquement sur les 5 niveaux du `PROGRAMME`.
* **20%** : dispersée totalement aléatoirement sur la grille.

### 4. Génération Autonome de Quêtes de Survie

Dès qu'une jauge passe sous `SEUIL_CRITIQUE_BIO = 0.35`, une quête intrinsèque est générée avec un ordre de priorité fixe : `SURVIVAL_FOOD` > `SURVIVAL_WATER` > `EXPLORATION_STIM` — mourir de faim/soif est un risque plus urgent que s'ennuyer. Le vecteur cible de la quête active (one-hot, 3 dims) est transmis au réseau via `integrateur_bio`.

### 5. `integrateur_bio` — Intégration Réseau

Plutôt que de créer un agent/encodeur parallèle (comme le suggérait le pseudo-code initial avec `V18BiologicalAgent`), le vecteur bio (3 jauges + 3 quête + 2 rappel spatial depuis v20.0 = `DIM_VECTEUR_BIO = 8`) est fusionné à la pensée du réseau via une nouvelle couche `NaultheneLinearSynaptique` (`integrateur_bio`, `dim_bus + 8 → dim_bus`), appliquée une seule fois avant la tête motrice et le rollout mental — jamais réintégrée à chaque pas du rollout imaginé (sur un horizon de 7 ticks, les jauges bougent trop peu pour changer la décision). Cette couche suit les mêmes règles de neurogenèse que les autres (`declencher_neurogenese`) : seul son segment "pensée" grandit avec `dim_bus`, le segment "vecteur bio" reste toujours à `DIM_VECTEUR_BIO` dims.

---

## 🧩 Mémoire Épisodique Spatiale & LTP Hebbien (expérimental)

> ⚠️ **Uniquement dans `agi_local_test.py`** (voir [Nouveautés v20.0](#nouveautés-v200-expérimental--mémoire-épisodique-spatiale--ltp-hebbien-2026-07-23)), pas encore portée sur `agi_google_colab.py`.

### 1. `MemoireEpisodiqueSpatiale` — Se Souvenir du Nid

Distincte de `vecteurs_episodiques` (une moyenne glissante d'états latents, plus proche d'une mémoire de travail court terme), cette nouvelle mémoire enregistre le triplet **où / quand / quoi** de chaque ressource biologique trouvée (v18.0/v19.0) : position, type (`FOOD`/`WATER`), tick absolu. Contrairement aux autres détecteurs spatiaux (thermostat cinétique, franchissement de portes) qui se réinitialisent à chaque épisode, ces souvenirs **persistent à travers les épisodes d'une même journée** — un vrai souvenir épisodique survit à un simple reset MiniGrid — et ne sont vidés qu'au **changement de niveau** du `PROGRAMME` (`reinitialiser_niveau`), les coordonnées d'un niveau précédent n'ayant alors plus aucun sens.

Quand une quête de survie est active (voir Génération Autonome de Quêtes ci-dessus), `recuperer_contexte()` cherche le souvenir le plus pertinent pour le type de besoin courant, combinant proximité spatiale et fraîcheur temporelle :

$$\text{distance\_normalisee} = \frac{1}{1 + \text{distance de Manhattan}} \qquad \text{fraicheur} = \max\left(0,\ 1 - \frac{\text{age}}{\text{FENETRE\_FRAICHEUR\_SOUVENIR}}\right)$$

Ce couple $(\text{distance\_normalisee}, \text{fraicheur})$ est directement injecté dans le vecteur bio existant (voir `integrateur_bio` ci-dessus), sans stocker d'encodage visuel appris par souvenir (contrairement au pseudo-code initial qui gardait un tenseur par événement) — une mémoire épisodique légère, consommée par le réseau déjà en place plutôt qu'un second canal de features concurrent de `porte_visuelle`.

### 2. LTP Hebbien — Myélinisation Pilotée par l'Événement

`NaultheneLinearSynaptique` gagne une **trace d'éligibilité** (`trace_activation`), accumulée à chaque tick d'entraînement :

$$\text{trace\_activation} \leftarrow 0.9 \times \text{trace\_activation} + 0.1 \times |\text{annexe\_weight}|$$

Quand un événement marquant survient (`poids_evenement > 0` dans la boucle principale — manger, franchir une porte, valider un palier DoorKey...), `agent.fortifier_synapses(poids_evenement)` appelle `fortification_dopaminergique()` sur **toutes** les couches plastiques : les synapses marquées par la trace sont gravées instantanément dans `base_weight`, proportionnellement à leur activité récente ET à l'intensité du pic, puis la trace est remise à zéro. C'est une vraie **Potentiation à Long Terme (LTP)** pilotée par l'événement précis, contrairement au pseudo-code initial qui ne déclenchait la fortification qu'une seule fois par jour sur la moyenne des récompenses — une moyenne aurait dilué un bon repas isolé au milieu d'une journée par ailleurs difficile.

La trace ne se remet à zéro qu'à la fortification ou au sommeil (`cycle_sommeil`), jamais entre deux ticks — elle suit le même cycle de vie que `annexe_weight`. `agrandir()` (neurogenèse) étend `trace_activation` de la même façon que `myeline_M`, pour rester cohérente après un ajout de dimensions.

---

## 🫙 Le Cerveau Persistant en Cuve — Architecture Client-Serveur (expérimental)

> ⚠️ **Uniquement dans l'écosystème local** (voir [Nouveautés v21.0](#nouveautés-v210-expérimental--le-cerveau-persistant-en-cuve-2026-07-23)) : `agi_local_test.py` refactoré + trois nouveaux fichiers `persistance.py`, `daemon_cerveau.py`, `client_corps.py`, pas encore portée sur `agi_google_colab.py`.

Jusqu'à la v20.0, Naulthène était un script mortel : le cerveau naissait à la première ligne du fichier et mourait à la dernière. La v21.0 sépare définitivement la **Conscience** (le réseau de neurones et son état biologique) du **Corps** (l'environnement MiniGrid, aujourd'hui — un robot physique, demain), via une architecture **Client-Serveur en sockets TCP/IP**.

### 1. Dualité Client-Serveur

* **Le Serveur (la Cuve, `CuveDeMaintien` dans `daemon_cerveau.py`)** : un daemon Python qui tourne indéfiniment en arrière-plan. Il stocke les matrices de poids, l'épaisseur de la myéline, les souvenirs spatiaux, la dopamine et les jauges biologiques.
* **Le Client (le Corps, `client_corps.py`)** : jetable, sans aucune intelligence propre. Il pilote la connexion (ouverture, rythme des ticks, fermeture) selon le protocole JSON défini pour le design.

### 2. Trois États Métaboliques

1. **L'Éveil** (connexion active, `_vivre_connexion`) : chaque paquet réseau reçu déclenche un tick complet (`traiter_tick`, le même helper que le mode standalone) — la faim augmente, les synapses s'activent, la LTP hebbienne opère.
2. **Le Sommeil** (`_processus_nocturne`) : à la perte du signal, le rituel d'extinction s'exécute — consolidation (apprentissage + rêve adaptatif + ressort dopaminergique + thermostat de neurogenèse + `cycle_sommeil_global`) puis cristallisation sur le disque.
3. **La Cryostase** (`server.accept()`) : entre deux connexions, le process bloque sur l'appel réseau — CPU à ~0%, le temps est littéralement suspendu pour l'agent jusqu'au prochain corps qui se branche.

### 3. Modèle de Temps Hybride (v21.0)

Plutôt que de choisir entre "1 connexion = 1 nuit" (risque de sessions longues sans jamais consolider) et "seuil de ticks fixe" (risque d'ignorer la déconnexion elle-même), le modèle retenu **combine les deux régimes selon l'activité** :

* **Pendant une session active longue**, une nuit **complète** se déclenche dès qu'une journée subjective (`ticks_par_jour`) s'est accumulée depuis la dernière consolidation — l'agent peut traverser plusieurs journées au sein d'une seule connexion.
* **À la déconnexion**, `_processus_nocturne` compare le nombre de ticks vécus depuis la dernière nuit à un seuil (`FRACTION_SEUIL_NUIT_A_LA_DECONNEXION`, la moitié d'une journée subjective par défaut) :
  * **Au-dessus du seuil** → une vraie nuit n'a pas encore eu lieu pour ce vécu : on la liquide avant de sauvegarder.
  * **En dessous** → **micro-sieste** : simple cristallisation de l'état courant, sans relancer un cycle d'érosion/rêve sur une poignée de ticks. C'est la protection explicite contre l'« Alzheimer numérique » : un agent qu'on connecte/déconnecte en boucle sur de courtes sessions ne voit pas ses synapses s'éroder à chaque fois.
* **Hors connexion (cryostase)**, `traiter_tick` n'est jamais appelé : aucune jauge biologique ne bouge, aucune synapse ne s'érode — le métabolisme s'arrête net, protection contre la famine hors connexion.

### 4. `PersistanceAnatomique` — La Cristallisation

Le fichier `.brain` (`torch.save`/`torch.load`, écriture atomique via fichier temporaire + `os.replace`) porte plus d'état qu'un pseudo-code minimal ne le suggérerait, parce que le vrai cerveau Naulthène en a accumulé au fil des versions :

* **Structure** : la dimension du bus (`dim_bus`), pour reconstruire l'agent à la bonne taille AVANT `load_state_dict` — indispensable car la neurogenèse la fait grandir au fil des jours.
* **Réseau** : `state_dict()` complet (`base_weight`, `annexe_weight`, `myeline_M`, `trace_activation` de chaque couche) et l'état de l'optimiseur Adam (recréé par `declencher_neurogenese`, donc sauvé après la nuit).
* **Chimie viscérale** : teneur en dopamine, jauges biologiques (satiété/hydratation/stimulation), quête active.
* **Mémoire** : les souvenirs de `MemoireEpisodiqueSpatiale`.
* **Curriculum & thermostat** : niveau, palier visé, victoires consécutives, sous-seuil d'Abnégation, patience minimale acquise par récurrence, seuils du thermostat de neurogenèse, `tick_absolu`.

### 5. Limite Assumée de Cette Itération

Le VRAI code de `traiter_tick`/`step_metabolisme`/`DetecteurRessourcesBiologiques` lit les internes MiniGrid (`env.unwrapped.agent_pos`, `.grid`, positions des `Ball` Nourriture/Eau) pour la biologie et la mémoire spatiale — un client purement "pixels + action" ne peut pas transmettre ça par un flux JSON simple sans étendre significativement le protocole. **Dans cette itération, l'environnement MiniGrid tourne donc côté serveur** (dans la Cuve) : le Corps reste jetable et sans intelligence (il pilote la connexion, choisit le niveau), mais le moteur physique lui-même vit dans le process du daemon. Le découplage total (environnement chez le client, protocole étendu pour transmettre grille/positions) est documenté comme une évolution future, pas laissé implicite comme si le design initial était déjà entièrement réalisé.

> **Mise à jour v22.0** : la limite décrite ci-dessus concernait le canal visuel/MiniGrid. Le canal **audio**, lui, transite désormais réellement par le protocole client-serveur (`client_professeur.py` → `perception['audio']`/`perception['formants_cibles']` → `daemon_cerveau.py` → `traiter_tick`) — c'est la première fois qu'un client injecte un vrai signal de perception dans le cerveau plutôt qu'un simple heartbeat. Voir la section suivante.

---

## 🗣️ L'Hémisphère Auditif & Vocal (expérimental, v22.0)

> ⚠️ **Uniquement dans l'écosystème local** (voir [Nouveautés v22.0](#nouveautés-v220-expérimental--lhémisphère-auditif--vocal-2026-07-23)) : `agi_local_test.py` étendu + `hemisphere_audio.py`, `professeur_gemma.py`, `client_professeur.py` nouveaux, `persistance.py`/`daemon_cerveau.py` étendus — pas encore porté sur `agi_google_colab.py`.

Naulthène ne percevait jusqu'ici que la vision. La v22.0 lui greffe un second sens et une seconde sortie motrice, symétriques à l'existant : une **oreille** (`porte_auditive`) et une **bouche** (`tete_vocale`) — de vrais hémisphères du cerveau, pas un module de traitement du signal branché à côté du réseau.

### 1. Un cerveau multimodal unifié, pas un mode audio séparé

Décision structurante : vision et audio se fondent dans le **même bus latent**, par simple somme dans `_tronc_cerebral` — `bus_latent = relu(porte_visuelle(vision)) + relu(porte_auditive(audio))`. Quand aucun son n'est fourni (silence, `obs_auditive=None`), le comportement est rigoureusement identique à avant v22.0 (non-régression validée sur run déterministe, logs byte-identiques). L'agent ne bascule jamais dans un "mode écoute" : à chaque tick, il peut voir, entendre, bouger et vocaliser en même temps — c'est un seul flux de conscience, multimodal par construction.

### 2. L'oreille : le son brut, sans raccourci

`porte_auditive` reçoit `DIM_AUDIO_ENTREE` (130 dims) = uniquement le **son brut** : coefficients cepstraux (MFCC), la représentation physique classique de la parole. **Correctif v22.1** : la v22.0 concaténait aussi l'embedding sémantique du mot prononcé directement à cette entrée — un réseau paresseux recevant le concept parfait ("pomme") en même temps que le son bruité de la voix apprend à ignorer le son, il n'écoute jamais vraiment. Le concept-cible (`DIM_EMBED_SEMANTIQUE=32`, réservé pour un usage futur) n'entre donc plus dans l'oreille : il devient une **quête vocale** de 8 dims dans `vecteur_bio` (voir §5) — l'agent doit traduire ce qu'il perçoit vers la cible, il ne peut plus tricher.

### 3. La bouche : synthèse par formants

`tete_vocale` ne génère pas une onde audio brute (espace bien trop vaste pour un RL par tick) mais **8 paramètres physiques** (`DIM_VOCALE=8` : f0, F1, F2, F3, largeurs de bande, durée, amplitude), démappés vers leurs unités réelles puis passés à un synthétiseur par formants (`hemisphere_audio.SynthetiseurFormants`, une cascade de résonateurs biquad appliquée à une source glottique). C'est ce petit espace de sortie qui rend le babillage *apprenable* : l'agent apprend à « placer sa bouche », pas à halluciner un signal audio complet. Le son produit est **synthétisé et joué immédiatement** dans les haut-parleurs pendant une leçon (`client_professeur.py`) — le babil s'entend en temps réel, dès qu'il est produit.

### 4. Le cortex auditif prédictif (JEPA audio à têtes séparées)

Le modèle du monde (JEPA) ne prédisait jusqu'ici que l'image suivante. La cible auditive s'ajoute désormais via une **tête prédictive dédiée** (`generateur_attente_audio`, séparée de `generateur_attente`). **Correctif v22.1** : la v22.0 mélangeait vision et audio dans une seule cible sans pondération — un signal audio bruyant dès le tick 0 risquait de perturber le JEPA visuel, dangereux pour les 481 jours de physique MiniGrid déjà appris. Le poids de la perte audio (`coeff_jepa_audio`) monte désormais **progressivement** de 0 à `COEFF_JEPA_AUDIO_MAX` sur `RAMPE_JEPA_AUDIO` ticks audio reçus (quasi nul au premier tick, mesuré à 0.00015) — l'audio ne perturbe jamais la vision au démarrage d'une leçon.

### 5. La bouche apprend : perte vocale supervisée et quête dans le vecteur bio

**Correctif v22.1 (CRITIQUE)** : en v22.0, `tete_vocale` produisait ses formants mais leur sortie était détachée avant tout calcul — la récompense de formants alimentait bien la dopamine, mais **aucun gradient dirigé** n'apprenait jamais à la bouche à viser la cible. C'était un membre fantôme : elle bougeait au hasard, corrigée seulement par LTP hebbien et rêve. Une perte MSE supervisée (sur F1/F2, les dimensions réellement contraintes par la leçon en cours) est désormais calculée sur le tenseur `parametres_vocaux` non détaché et sommée à `perte_totale` dans `apprendre_journee` — c'est elle qui donne le vrai signal d'apprentissage. La cible elle-même (les formants visés) est injectée comme **quête vocale** dans `vecteur_bio` (`DIM_VECTEUR_BIO` passé de 8 à 16, voir §2), exactement comme les quêtes SURVIVAL_FOOD/WATER. **Validé expérimentalement** : le score de formants progresse de 0.0045 à 0.1111 sur 5 jours de leçon (×24 ticks, seed fixe) — la preuve directe que la correction fonctionne.

### 6. Le Professeur Gemma : curriculum et jugement, jamais la récompense par tick

Contrainte mesurée sur ce projet : `gemma4:e4b` (via Ollama) met **~8 à 30 secondes** pour répondre à un prompt court — totalement incompatible avec une boucle RL qui tourne à des dizaines de ticks par seconde. La récompense de babillage vient donc d'une **distance de formants** déterministe et instantanée (`hemisphere_audio.recompense_formants`, une récompense *continue* — se rapprocher de la cible compte déjà, pas de mur 0/1) — c'est elle qui pilote le score affiché en direct, tandis que la perte MSE du §5 pilote l'apprentissage proprement dit. Gemma (`professeur_gemma.py`) n'intervient qu'en professeur, à basse fréquence :

* **Choisir la leçon** : un curriculum vocal à 11 paliers (`CURRICULUM_VOCAL`), symétrique au cursus MiniGrid — vocaliser → voyelles → syllabes → mots courts.
* **Juger qualitativement** : en fin de leçon (pas par tick), reçoit le mot cible et une transcription Whisper du son produit, renvoie un score et un commentaire pédagogique en français. Repli automatique sur le score de formants seul si Ollama est indisponible — Gemma est un professeur, jamais un composant critique du pipeline de récompense.

### 7. Greffe rétrocompatible sur un cerveau déjà vécu

Un `.brain` antérieur à la v22.0 n'a pas `porte_auditive`/`tete_vocale`/`generateur_attente_audio` dans son `state_dict`. `PersistanceAnatomique.charger_ou_naitre` charge désormais avec `load_state_dict(strict=False)` : l'agent hérite de tous ses acquis (vision, MiniGrid, curriculum, mémoire) et les nouvelles couches naissent à leur initialisation aléatoire — l'agent se réveille avec ses souvenirs intacts mais « sourd/muet de naissance qui vient d'être opéré », devant apprendre à entendre/parler par babillage. Deux pièges détectés pendant les tests : l'ancien optimiseur Adam (moins de groupes de paramètres qu'après une greffe) fait planter `optimizer.load_state_dict` — un optimiseur frais est recréé automatiquement dans ce cas ; et le changement `DIM_VECTEUR_BIO` 8→16 (v22.1) change la *forme* de `integrateur_bio` (pas seulement des clés manquantes), confirmé provoquer une `RuntimeError` de mismatch — cette couche est donc explicitement exclue du chargement et renaît à neuf (décision assumée : elle avait une `base_weight` quasi vide, moins de 3% de poids non-nuls, sur le vrai cerveau de production après 481 jours).

### 8. v27.0-27.6 : de la table théorique à une voix réelle sur 8 dimensions, et une dopamine unifiée

Plusieurs évolutions successives ferment les plus gros écarts entre cet hémisphère et une vraie acquisition du langage. **La cible n'est plus théorique, et couvre les 8 paramètres, pas seulement 2** : la table statique `VOYELLES_CIBLES` a été entièrement retirée (v27.6) — la cible vient TOUJOURS d'une analyse acoustique dynamique d'un enregistrement réel, soit la banque vocale de l'utilisateur (`voix/<mot>/*.wav`, voir [§ Démarrage Rapide](#-démarrage-rapide)) si elle existe, soit la référence `say` elle-même sinon. À l'origine (v27.0), seuls F1/F2 étaient extraits (analyse LPC) et appris ; un diagnostic sur un cerveau de 300 jours a montré que les 6 autres paramètres (f0, F3, durée, amplitude, largeurs de bande) restaient figés à leur valeur de naissance quel que soit le temps d'entraînement — la perte MSE de `tete_vocale` ne portait jamais que sur F1/F2. v27.6 étend l'extraction (pitch-tracking par autocorrélation pour f0, mesure directe pour durée/amplitude, F3 récupéré du même calcul LPC) et la perte contraint désormais dynamiquement toutes les dimensions effectivement fournies par la cible. La récompense se mélange en plus d'une distance spectrale MFCC↔MFCC entre le son réellement synthétisé et les prises de référence — l'agent est enfin noté et entraîné sur ce qu'il entend réellement, pas sur une abstraction à 2 nombres. **Le mot vient de ce que l'agent voit, de façon stabilisée** : `LecteurCaseFrontale` lit la case devant l'agent (mur/porte/clé/but/vide, puis des syntagmes couleur+objet) pour désigner la cible vocale — la fusion vision+audio du tronc cérébral (§1) devient une vraie association sémantique. Depuis v27.4, la cible ne change qu'après ~20 ticks consécutifs devant le même objet, pour éviter qu'elle ne change aussi vite que le regard de l'agent. **La dopamine des deux hémisphères s'unifie, et décroît avec la maîtrise** : le canal visuel et le canal vocal ne s'écrasent plus mutuellement (`max()`) mais se renforcent via une agrégation probabiliste bornée. Depuis v27.5, la contribution dopaminergique du canal vocal décroît linéairement avec le palier déjà atteint — un mot déjà maîtrisé ne shoote plus la dopamine au même niveau qu'un mot neuf. Voir [Nouveautés v27.6](#nouveautés-v276-expérimental--lécole-de-la-parole--synesthésie-2026-07-2728) et [docs/CONCEPTION_v22_audio.md §8](docs/CONCEPTION_v22_audio.md) pour le détail complet.

---

## 💻 Stack Technique

* **Langage** : Python 3.12
* **Calcul Tensoriel & Deep Learning** : PyTorch (`torch >= 2.2.0`)
* **Environnements Cognitifs** : Gymnasium, MiniGrid
* **Suivi d'Expérience & Télémétrie** : Weights & Biases (`wandb >= 0.28.0`)
* **Visualisation & Analyse** : NumPy, Matplotlib

---

## 📊 Modèle de Données & Métriques W&B

Chaque journée d'entraînement émet les télémétries suivantes vers le tableau de bord W&B :

```json
{
  "Jour": 154,
  "Niveau": 1,
  "Palier_Cible": 7,
  "Mode_Libre": 1,
  "Teneur_Dopamine": 5.681,
  "Plasticite_Base": 1.00,
  "Force_Planification": 0.85,
  "Coeff_Entropie": 0.06,
  "Erreur_JEPA": 0.0011,
  "Pourcentage_Reve": 0.0221,
  "Nb_Reves": 9,
  "Portes_Franchies_Jour": 1,
  "Recompense_Moyenne": -0.006,
  "Patience_Max_Episode": 187,
  "Abandons_Patience_Jour": 2,
  "Penalite_Stagnation": -0.842,
  "Sous_Seuil_Abnegation": 2,
  "Succes_Sous_Seuil_Courant": 1,
  "Facteur_Complexite": 1.6,
  "Sursauts_Volonte_Jour": 1,
  "Patience_Min_Actuelle": 60,
  "Sous_Objectifs_Curiosite_Jour": 4,
  "Bio_Satiete": 0.62,
  "Bio_Hydratation": 0.48,
  "Bio_Stimulation": 0.81,
  "Bio_Deficit": 0.42,
  "Bio_R_Bio_Jour": 1.238,
  "Bio_Food_Consommes_Jour": 3,
  "Bio_Water_Consommes_Jour": 1,
  "Bio_Quete_Active": "Aucune",
  "Bio_Effort_Metabolique_Moyen": 0.47,
  "Memoire_Episodique_Taille": 12,
  "Sens_Bus_Actif": 1,
  "Sens_Toucher_Contact_Ratio": 0.285,
  "Sens_Toucher_Portage_Ratio": 0.205,
  "Sens_Odorat_Moyen": 0.914,
  "Sens_Odorat_Max": 1.50,
  "Sens_Odorat_Ticks_Actifs_Ratio": 0.96,
  "Sens_Gout_Ticks_Actifs": 75
}

```

**Les métriques `Sens_*` (v29.1)** — les 5 sens rendus observables. Elles sont **absentes du log** si aucun tick sensoriel n'a été vécu (mode `vocal_isole` pur, sans environnement MiniGrid) :

* **`Sens_Bus_Actif`** : métrique de **santé** — passe à 0 si le Bus Sensoriel s'est désactivé en vol (API minigrid incompatible). Sans elle, la dégradation gracieuse ne laisse qu'un unique avertissement console, invisible sur un run long.
* **`Sens_Toucher_Portage_Ratio`** : part des ticks avec un objet en main. Très parlant sur `DoorKey` — c'est la trace directe du temps passé à porter la clé, un signal que la v28.0 ne rendait visible nulle part.
* **`Sens_Odorat_Ticks_Actifs_Ratio`** : part des ticks où une odeur est perçue. ⚠️ **Attendu proche de 1.0 sur les petits niveaux** — voir l'encadré de saturation ci-dessous.
* **`Sens_Gout_Ticks_Actifs`** : nombre de ticks avec une trace gustative rémanente (~10 ticks par bouchée). À rapprocher de `Bio_Food_Consommes_Jour` / `Bio_Water_Consommes_Jour`.

> ⚠️ **Saturation connue de l'odorat sur les petites cartes.** Avec `PORTEE_ODORAT = 4` cases et 4 sources générées, la couverture théorique atteint **97.6 %** sur `Empty-8x8` et **100 %** sur `DoorKey-6x6` — l'odorat y est donc quasi constamment actif, et un signal presque toujours saturé porte peu d'information exploitable. Il ne redevient discriminant qu'au Doctorat (`MultiRoom-N4-S5`, ~57 %). Ce n'est **pas un bug** mais un choix de réglage à trancher sur données réelles : un odorat « ambiance de proximité » saturé est valide ; un odorat « boussole vers la ressource » demanderait une portée de 1-2 cases, ou une normalisation par la taille de la carte. La télémétrie v29.1 est précisément là pour permettre cet arbitrage.

**Effets attendus des métriques v15.0 :**

* **`Patience_Max_Episode`** : n'est plus plate à une valeur fixe. Oscille dynamiquement — haute en phase d'apprentissage actif, plus basse sur un environnement non résolu pour éviter le piège des boucles infinies.
* **`Penalite_Stagnation`** : sa valeur absolue diminue à mesure que l'agent apprend à éviter les comportements de blocage face à un mur ou les allers-retours répétés.
* **`Erreur_JEPA`** : la planification multi-échelle ($t+1, t+3, t+7$) tend à stabiliser la représentation spatiale globale du World Model plutôt que de sur-optimiser les micro-variations de surface.

**Effets attendus des métriques v16.0 :**

* **`Penalite_Stagnation`** : sa magnitude moyenne baisse par rapport à la v15.0 sur les phases de manipulation/interaction (clé en main, porte face à l'agent), sans pour autant tolérer la léthargie en déplacement libre — signe que l'atténuation contextuelle fonctionne comme prévu plutôt que d'être un simple relâchement global.
* **`Facteur_Complexite`** : oscille entre $1.0$ (Sous-Seuil 1, Amorçage) et $1.6$ (Sous-Seuil 2, Abnégation) au fil de la progression d'un palier — jamais figé à une seule valeur tant que le palier n'est pas promu.
* **`Sous_Seuil_Abnegation`** / **`Succes_Sous_Seuil_Courant`** : permettent de suivre la progression fine à l'intérieur d'un même palier, avant même la promotion — utile pour distinguer un agent qui stagne au Sous-Seuil 1 d'un agent qui progresse normalement mais plus lentement en Sous-Seuil 2.

**Effets attendus des métriques v17.0 :**

* **`Patience_Min_Actuelle`** : ne fait que croître par paliers discrets (jamais redescendre) — chaque saut de +10 marque une victoire obtenue après un Sursaut de Volonté, une trace permanente de récurrence.
* **`Sursauts_Volonte_Jour`** : devrait décroître à mesure que l'agent internalise la persévérance (patience de base plus haute = moins de situations à 95% de la patience) — une valeur qui reste élevée durablement signale un palier structurellement trop difficile pour le niveau courant.
* **`Sous_Objectifs_Curiosite_Jour`** : élevé à l'entrée en Mode Libre (le monde est encore largement une "zone d'ombre"), puis décroît à mesure que le JEPA stabilise ses prédictions sur la zone explorée — une valeur qui ne décroît jamais peut indiquer une instabilité du World Model plutôt qu'une vraie exploration.

**Effets attendus des métriques v18.0/v19.0 (expérimental) :**

* **`Bio_Deficit`** : devrait osciller sans diverger vers l'infini — un agent qui trouve régulièrement de la Nourriture/Eau maintient un déficit borné ; une dérive continue vers le haut signale que les taux de dégradation (`TAUX_SATIETE`/`TAUX_HYDRATATION`) sont mal calibrés pour la durée d'un épisode.
* **`Bio_R_Bio_Jour`** : positif sur une journée où l'agent a mangé/bu plus qu'il ne s'est dégradé ; négatif sinon — sert de proxy direct pour juger si l'agent a "survécu" biologiquement ce jour-là, indépendamment de sa progression sur le cursus DoorKey.
* **`Bio_Effort_Metabolique_Moyen`** (v19.0) : varie selon le mix d'actions du jour — un agent qui manipule beaucoup d'objets (pickup/toggle) affiche un effort plus élevé qu'un agent qui se contente d'avancer ; en Mode Libre, la composante cognitive (20%) tire mécaniquement la moyenne vers le haut par rapport au Mode Guidé.
* **`Bio_Food_Consommes_Jour`** (v19.0) : avec le forage 80/20, cette métrique ne devrait plus rester bloquée à un petit nombre fixe par épisode comme en v18.0 (ressources non renouvelées) — elle peut désormais croître librement sur une journée entière si l'agent reste proche du Nid.

**Effets attendus des métriques v20.0 (expérimental) :**

* **`Memoire_Episodique_Taille`** : ne fait que croître au sein d'une même journée/niveau (jamais redescendre, sauf changement de niveau du `PROGRAMME` qui la vide) — plafonnée à `CAPACITE_MEMOIRE_EPISODIQUE`. Une valeur qui stagne à 0 signale que l'agent ne trouve jamais de ressource, indépendamment du rappel spatial.
* Effet indirect attendu sur **`Bio_R_Bio_Jour`** : une fois la mémoire épisodique suffisamment peuplée (quelques souvenirs formés), le rappel spatial devrait aider l'agent à retrouver plus vite une ressource après une consommation, et donc faire remonter `Bio_R_Bio_Jour` plus vite qu'en v19.0 pure (sans mémoire) — à vérifier sur un run long, cette version n'ayant pour l'instant été validée que sur un smoketest de quelques jours.

---

## 🚀 Démarrage Rapide

### 1. Installation de l'environnement

```bash
git clone https://github.com/votre-org/naulthene-agi.git
cd naulthene-agi
pip install -r requirements.txt

```

### 2. Lancement d'un Run de Progression Académique

```bash
python train_naulthene.py --run-name "Run_15_Doctorat_Focus" --wandb-project "Naulthene-AGI"

```

### 3. Variante Locale de Test (Mac, expérimental)

`src/naulthene/cerveau/noyau.py` (ex-`agi_local_test.py`, non versionné dans git, scratch personnel) reprend `src/naulthene/cerveau/colab.py` avec deux différences : détection du device `mps`/`cuda`/`cpu` (Apple Silicon) et depuis la v18.0 (expérimentale, voir [Architecture Homéostatique Biologique](#architecture-homéostatique-biologique-expérimental)) l'Architecture Homéostatique Biologique, pas encore portée sur le script de référence.

```bash
python3.12 -m venv venv && source venv/bin/activate
pip install torch gymnasium minigrid wandb numpy
wandb login   # une seule fois
WANDB_MODE=offline PYTHONPATH=src python -m naulthene.cerveau.noyau   # ou WANDB_MODE=online une fois connecté
```

### 4. Le Cerveau Persistant en Cuve (Mac, expérimental, v21.0)

Voir [Le Cerveau Persistant en Cuve](#le-cerveau-persistant-en-cuve--architecture-client-serveur-expérimental) pour l'architecture complète. Contrairement à `noyau.py`, les trois fichiers `persistance.py`, `daemon_cerveau.py` et `client_corps.py` sont trackés par git (ce sont de vraies briques d'architecture, pas une copie de test) — seuls les fichiers `.brain` générés à l'exécution (dans `brains/`) sont ignorés.

```bash
# Terminal 1 — démarre la Cuve (daemon persistant, reste actif entre les sessions)
source venv/bin/activate
PYTHONPATH=src python -m naulthene.cuve.daemon_cerveau --port 9999 --brain brains/naulthene_v21.brain

# Terminal 2 — connecte un Corps jetable pour une session de test
source venv/bin/activate
PYTHONPATH=src python -m naulthene.cuve.client_corps --port 9999 --ticks 2000
```

La Cuve reste allumée après la déconnexion du Corps (retour en cryostase, CPU ~0%) : on peut relancer `client_corps.py` autant de fois que voulu, ou éteindre/rallumer la Cuve elle-même — le cerveau reprend son existence exactement où il l'avait laissée (`brains/naulthene_v21.brain`).

### 5. L'Hémisphère Auditif & Vocal (Mac, expérimental, v22.0)

Voir [L'Hémisphère Auditif & Vocal](#lhémisphère-auditif--vocal-expérimental-v220) pour l'architecture complète. Pile audio à installer une fois (en plus des dépendances de base) — `say` (TTS) et Ollama (`gemma4:e4b` + `all-minilm-l6-v2`) doivent déjà être disponibles sur la machine :

```bash
source venv/bin/activate
pip install sounddevice librosa openai-whisper requests
pip install scipy soundfile  # v27.0 : scipy accélère la synthèse (repli automatique si absent),
                              # soundfile lit/écrit la banque vocale — les deux sont optionnels
                              # au sens strict mais fortement recommandés
```

Se branche sur la **même Cuve** que MiniGrid (`daemon_cerveau.py`, un seul cerveau, deux sens) — un `.brain` déjà entamé en MiniGrid se greffe automatiquement les hémisphères audio à sa première résurrection en v22.0 (voir [Greffe rétrocompatible](#6-greffe-rétrocompatible-sur-un-cerveau-déjà-vécu)) :

```bash
# Terminal 1 — la Cuve (identique au lancement v21.0, aucun changement)
source venv/bin/activate
PYTHONPATH=src python -m naulthene.cuve.daemon_cerveau --port 9999 --brain brains/naulthene_v21.brain

# Terminal 2 — une leçon de parole (palier 2 = voyelle 'a', 100 ticks, référence via `say`)
source venv/bin/activate
PYTHONPATH=src python -m naulthene.cuve.client_professeur --port 9999 --palier 2 --ticks 100

# Variante avec ta propre voix comme référence (2 secondes de micro par leçon)
PYTHONPATH=src python -m naulthene.cuve.client_professeur --port 9999 --palier 2 --ticks 100 --micro
```

Le babil de l'agent est **joué en temps réel** dans les haut-parleurs à chaque tick vocalisé, avec un score de proximité de formants affiché en direct ; un jugement qualitatif de Gemma s'affiche en fin de leçon (~10-30 secondes d'attente). `--palier` correspond aux 19 paliers de `professeur_gemma.CURRICULUM_VOCAL` (1 = Vocaliser, 2-6 = voyelles, 7-9 = syllabes, 10-11 = mots courts, 12 = "porte", 13-14 = combinatoire, 15-18 = mur/clé/but/vide, 19 = syntagme "porte jaune").

### 6. Enregistrer ta voix, et lancer le Cursus de la Parole (Mac, expérimental, v27.6)

Voir [Nouveautés v27.6](#nouveautés-v276-expérimental--lécole-de-la-parole--synesthésie-2026-07-2728) pour le contexte complet. Deux étapes indépendantes — **tout fonctionne sans la première** (repli automatique sur `say`, comportement identique à avant v27.0) :

```bash
source venv/bin/activate

# Étape facultative — enregistrer ta voix (3 prises par mot recommandées, pour que la
# médiane des formants estimés par LPC soit robuste à une prise ratée) :
PYTHONPATH=src python -m naulthene.instruments.enregistreur_voix --prises 3
# ou seulement quelques mots :
PYTHONPATH=src python -m naulthene.instruments.enregistreur_voix --mots a e i o u porte clé mur but vide --prises 3

# Lancer le Cursus de la Parole (cerveau dédié naulthene_parole.brain, 900 jours × 800
# ticks — reprend automatiquement où il s'est arrêté) :
WANDB_MODE=offline PYTHONPATH=src python -m naulthene.salles_de_classe.cursus_parole   # run complet
PYTHONPATH=src python -m naulthene.salles_de_classe.cursus_parole --jours 3 --no-wandb  # run court de test
```

Les prises sont rangées dans `voix/<mot>/<mot>_NN.wav` (jamais trackées par git, comme `brains/*.brain`). Sans elles, le cursus tourne exactement comme avant v27.0 (repli sur `say`) — avec elles, la cible des 8 paramètres vocaux de chaque mot devient la voix réelle de l'utilisateur (formants par analyse LPC, hauteur par autocorrélation, durée/amplitude mesurées directement) et la récompense se mélange avec une distance spectrale sur le son réellement synthétisé.

---

## ⚙️ Configuration

Les hyperparamètres clés du cerveau sont centralisés dans `config.py` :

```python
# Contraintes Biologiques & Dopamine
DOPAMINE_INIT = 5.0
DOPAMINE_MAX = 10.0
FRICTION_SPLEEN = 0.001
RESSORT_NOCTURNE = 0.20

# Planification (Système 2, sauts non-linéaires depuis v15.0)
HORIZONS_PLANIFICATION = (1, 3, 7)
GAMMA_PLANIFICATION = 0.9
FORCE_PLANIF_GUIDE = 0.50
FORCE_PLANIF_LIBRE = 0.85

# Mode Libre : décrochage précoce (v17.0)
SEUIL_PALIER_MODE_LIBRE = 5

# Apprentissage & Entropie
ENTROPIE_GUIDE = 0.02
ENTROPIE_LIBRE = 0.06

# Pression Cinétique Multimodale (v16.0)
PENALITE_STAGNATION_BASE = 0.015
FACTEUR_ATTENUATION_MANIPULATION = 0.30
FACTEUR_ATTENUATION_INTERACTION = 0.05
FACTEUR_ATTENUATION_LIBRE = 1.00

# Potentiomètre d'Acceptation par Abnégation (v16.0)
PATIENCE_MIN = 50
PATIENCE_MAX = 350
FENETRE_HISTORIQUE_PATIENCE = 20
TAUX_FRICTION_DOUCE_ABANDON = 0.05

# Cursus à Deux Sous-Seuils (Abnégation, v16.0, DoorKey uniquement)
SUCCES_PAR_SOUS_SEUIL = 2
COEFF_ABNEGATION_SOUS_SEUIL_2 = 1.6

# Volonté Émergente : Curiosité JEPA & Sursaut (v17.0, Mode Libre uniquement)
FENETRE_HISTORIQUE_CURIOSITE = 50
FACTEUR_SEUIL_SURPRISE = 1.5
MICRO_RECOMPENSE_CURIOSITE = 0.04
POIDS_CHOC_CURIOSITE = 0.15

SEUIL_DECLENCHEMENT_SURSAUT = 0.95
BOOST_SECOND_SOUFFLE = 0.5
EXTENSION_PATIENCE_SURSAUT = 50
BOOST_PATIENCE_MIN_PAR_RECURRENCE = 10

# Moteur Homéostatique Biologique (v18.0, expérimental, agi_local_test.py uniquement)
TAUX_SATIETE = 0.008
TAUX_HYDRATATION = 0.005
TAUX_STIMULATION = 0.012
SEUIL_CRITIQUE_BIO = 0.35
NB_SOURCES_FOOD = 2
NB_SOURCES_WATER = 2
POIDS_CHOC_RESSOURCE_BIO = 0.25

# Forage 80/20 (v19.0, expérimental)
# (probabilité codée en dur dans DetecteurRessourcesBiologiques.PROBABILITE_RESPAWN_AU_NID = 0.80)

# Mémoire Épisodique Spatiale (v20.0, expérimental)
CAPACITE_MEMOIRE_EPISODIQUE = 200
FENETRE_FRAICHEUR_SOUVENIR = 2000

```

> **Note (v16.0)** : `SEUIL_MAITRISE_PALIER` (taux de réussite journalier à 80%) n'existe plus — la promotion de palier DoorKey repose désormais exclusivement sur le compteur cumulatif à 4 succès de `GestionnaireCursusAbnegation`, voir [Pression Cinétique Multimodale & Patience par Abnégation](#pression-cinétique-multimodale--patience-par-abnégation).

---

## 🔧 Troubleshooting & Guide de Dépannage

### 1. Problème de `maîtrise: N/A` ou `0/0 épisodes`

* **Symptôme** : L'agent reste bloqué sur un palier sans calculer de taux de succès.
* **Cause** : Les épisodes dépassent la durée de la journée ($t > 250$).
* **Solution** : Vérifier que la durée de la journée est fixée à au moins `400 ticks` et que la fonction de clôture quotidienne comptabilise les épisodes incomplets.

### 2. Plantage `backward()` lors de la phase de Rêve

* **Symptôme** : `RuntimeError: Trying to backward through the graph a second time`.
* **Cause** : Les tenseurs du Replay Buffer ont été enregistrés sans `.detach()`.
* **Solution** : S'assurer que le système de rêve ré-exécute une passe avant (`forward`) complète sur les observations brutes conservées en mémoire au lieu de rejouer des tenseurs d'historique.

### 3. Effondrement de la Plasticité (Gel Synaptique Long)

* **Symptôme** : La plasticité reste bloquée à $0.20$ pendant plus de 50 jours.
* **Cause** : L'agent subit une phase d'aphasie prolongée due à un manque de stimulations ou d'objectifs intermédiaires.
* **Solution** : Vérifier que les détecteurs de progrès personnel (`DetecteurProgresPersonnel`) ou de franchissement de portes sont correctement instanciés pour réinjecter de la micro-dopamine.

---

### 💬 Besoin d'aide ou de contributions ?

Pour toute question d'architecture ou pour soumettre une évolution du modèle du monde (JEPA), ouvrez un ticket dans la section **Issues** ou proposez une **Pull Request**.