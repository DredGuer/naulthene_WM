# Changelog — Naulthène AGI

Historique des évolutions du projet, commit par commit. Voir [readme.md](../readme.md) pour la documentation narrative complète et [CLAUDE.md](../CLAUDE.md) pour les règles de maintenance de ce fichier.

---

## [30.0-experimental] - 2026-08-02

### L'Unification & l'Extensibilité — l'Odorat Dynamique & l'Exo-Sens (C3 devient le 6ᵉ sens)

| Type | Details |
|------|---------|
| **Commit** | N/A — en attente du commit de cette version |
| **Catégorie** | feat (nouvelle mécanique cognitive majeure, expérimentale) |
| **Impact** | Critique (architecture du réseau, persistance, contrat des plugs) |

**Arbitrages utilisateur, tranchés avant implémentation (voir `docs/CONCEPTION_v30_exo_sens.md`) : (1) l'odorat passe d'une rampe linéaire à une atténuation exponentielle `exp(-0.8·d)`, un gradient de diffusion chimique plutôt qu'un cercle à bord net ; (2) C3 cesse d'être un « 3ᵉ cerveau » interrogé par une action apprise pour devenir un 6ᵉ sens perçu en continu, SANS aucun seuil de déclenchement — l'attention à ce canal doit émerger de la myélinisation de `integrateur_bio`, pas d'un `if` ; (3) `num_actions` reste à 8 avec `ACTION_DEMANDER` masquée en permanence, pour ne jamais amputer les `.brain` existants.**

**1. Chantier 1 — l'Odorat Dynamique (atténuation exponentielle)**

La v29.1 avait diagnostiqué la saturation de l'odorat (97,6 % de couverture sur `Empty-8x8`, 100 % sur `DoorKey-6x6`). Une portée relative à la géométrie (`min(W,H)/3`) avait été envisagée puis **écartée** : elle ne corrigeait pas les cartes 4×4 et *aggravait* le Doctorat (portée 4→5). Le problème n'était pas la portée mais la **forme** de la décroissance.

$$S(d) = \exp(-\lambda \cdot d), \qquad \lambda = \text{LAMBDA\_ODORAT} = 0.8$$

| d | 0 | 1 | 2 | 3 | 4 |
|---|---|---|---|---|---|
| S(d) | 1.000 | 0.449 | 0.202 | 0.091 | 0.041 |

Le critère retenu pour juger n'est **pas la couverture mais le GRADIENT** (écart de signal entre cases voisines) — c'est lui qui permet à l'agent de savoir vers où aller. Mesuré sur 600 placements aléatoires de 4 sources :

| Carte | linéaire portée 4 | exponentiel λ=0.8 |
|---|---|---|
| `Empty-8x8` | 0.208 | **0.221** |
| `DoorKey-6x6` | 0.196 | **0.305** (+56 %) |
| `MemoryS7` | 0.207 | **0.259** |
| `MultiRoom` | 0.118 | 0.084 |

Sur un run réel de 400 ticks (`Empty-8x8`), l'intensité moyenne passe de ~0.54 à **0.316**, et l'odeur forte (> 0.45) ne survient plus que **29,8 %** du temps au lieu d'être quasi permanente : le sens redevient une boussole de proximité. **Contrepartie assumée et documentée** : `MultiRoom` (Doctorat) perd du gradient, l'exponentielle portant moins loin qu'une rampe à 4 cases — cohérent avec le rôle voulu (proximité, pas cartographie longue distance), mais à surveiller via `Sens_Odorat_*` sur un run au Doctorat.

**2. Chantier 2 — l'Exo-Sens : C3 devient le 6ᵉ sens**

`DIM_VECTEUR_BIO` passe de **24 à 32** dims (8 dims d'Exo-Sens **en queue**, contrat append-only). Le pivot conceptuel complet :

| | v28/v29 (C3 = 3ᵉ cerveau) | v30 (C3 = 6ᵉ sens) |
|---|---|---|
| Nature | Action apprise (`ACTION_DEMANDER`) | Entrée perceptive continue |
| Déclenchement | L'agent **décide** d'interroger | L'agent **perçoit**, sans décider |
| Sortie du plug | `ReponseC3.preferences` (avis sur les actions) | `ReponseC3.perception` (vecteur 8 dims) |
| Chemin | `tete_motrice` → `env.step` | `bus_sensoriel` → `integrateur_bio` |
| Attention | — | Émerge de la myélinisation, **aucun `if`** |

C'est l'option « perception continue » retenue par l'utilisateur contre le déclenchement sur erreur JEPA : un seuil codé en dur dans le chemin de décision aurait violé la règle déjà défendue deux fois (v28 pour l'appel à C3, v29 pour le court-circuit C1→C2). Si le plug envoie du bruit, `integrateur_bio` fera tomber ces poids vers 0 ; s'il envoie de l'information utile, il les renforcera.

**Latence — le garde-fou pratique** : un plug HTTP coûte de 100 ms à 30 s par appel. L'interroger à chaque tick rendrait impraticable un run de 120 000 ticks. La perception est donc **rafraîchie tous les `PERIODE_PERCEPTION_EXO = 20` ticks et mise en cache** (mesuré : 20 rafraîchissements pour 400 ticks). C'est une fréquence d'échantillonnage de capteur, pas une règle de décision — le cerveau perçoit bien quelque chose à chaque tick.

**3. La 8ᵉ action : masquée en permanence, jamais amputée**

`ACTION_DEMANDER` n'a plus de rôle (C3 n'est plus interrogé) mais **reste dans le réseau**, masquée à `-inf` quelle que soit la disponibilité du bus. Motif : 4 des `.brain` du dépôt sont déjà à 8 actions, dont `naulthene_cursus.brain` (cerveau actif, bus 48). Revenir à `num_actions = 7` aurait imposé une greffe **inverse** jetant des poids appris — première violation de la règle « greffe par recopie, jamais par exclusion ». La colonne 8 devient dormante, conservée, réactivable sans nouvelle greffe.

**4. Contrat `PlugC3` — perceptif et décisionnel coexistent**

`ReponseC3` porte désormais deux champs optionnels : `perception` (v30, 8 dims) et `preferences` (v28, conservé). `PortC3.agreger` agrège les deux **indépendamment**, en ignorant les plugs qui ne fournissent pas l'un ou l'autre — un bus mélangeant un plug v28 et un plug v30 fonctionne sans qu'aucun ne plante sur le `None` de l'autre. Les 3 plugs existants sont inchangés et continuent de fonctionner.

Nouveau **`PlugMemoireAugmentee`** : le premier plug perceptif, 100 % local et déterministe (résumé de la mémoire épisodique spatiale de l'agent), pour valider que C1/C2 digèrent un signal exogène avant d'introduire la latence d'un vrai service. Le contrat générique reste inchangé, donc un `PlugRAG`/`PlugOllama` se branche par simple configuration de `PlugHTTP`.

| Fichier modifié | Changement |
|-----------------|------------|
| `src/naulthene/cerveau/bus_sensoriel.py` | `LAMBDA_ODORAT`/`SEUIL_COUPURE_ODORAT` (atténuation exponentielle) ; `DIM_EXO=8` ; `percevoir_exogene()` (transducteur du 6ᵉ sens, clip défensif, avertissement isolé) ; `interpreter(..., reponse_c3=None)` → 16 dims ; `hierarchie_sensorielle()` étendue à `exo_sens` |
| `src/naulthene/cerveau/noyau.py` | `DIM_VECTEUR_BIO` 24 → 32 ; `PERIODE_PERCEPTION_EXO` ; `_rafraichir_perception_exogene()` (cache + diffusion `1_X`) ; masquage **permanent** de `ACTION_DEMANDER` ; 4 compteurs journaliers + ligne « Exo-Sens (C3) » au bilan + 4 clés `Sens_Exo_*` |
| `src/naulthene/exocortex/port_c3.py` | `ReponseC3.perception` (v30) ; `preferences` devient optionnel ; `agreger` réécrite via `_moyenne_ponderee`, tolérante aux champs absents |
| `src/naulthene/exocortex/plugs/plug_memoire_augmentee.py` | **Nouveau.** Premier plug perceptif + `source_depuis_memoire_spatiale()` (closure d'injection, garde `exocortex/` indépendant de `cerveau/`) |
| `src/naulthene/cerveau/persistance.py` | Libellé de greffe déduit de la **largeur bio réelle** du checkpoint (et non du nombre de dims ajoutées, ambigu : `DIM_TOUCHER+DIM_CHIMIE` et `DIM_EXO` valent tous deux 8) |

**Validation** (aucun test automatisé dans ce projet — vérifications manuelles) :
- **Invariance sans plug** : 400 ticks, `ACTION_DEMANDER` jamais jouée, 8 dims d'Exo-Sens nulles, **aucune clé `Sens_Exo_*` loggée**, bilan de nuit identique à la v29.1.
- **Odorat** : sur run réel, moyenne 0.316 (vs ~0.54), écart-type 0.256, odeur forte 29,8 % des ticks — le signal a changé de nature, pas seulement d'échelle.
- **Avec `PlugMemoireAugmentee`** : perception continue sur 95 % des ticks, **20 rafraîchissements pour 400 ticks** (le cache tient), ligne « Exo-Sens (C3) » et 4 clés `Sens_Exo_*` présentes.
- **Robustesse (4 cas)** : plug en panne en vol → aucune exception ; vecteur malformé (2 dims au lieu de 8) → Exo-Sens neutre, **les 5 sens physiques non affectés** ; bus mixte v28+v30 → agrégation correcte des deux canaux ; valeurs à 999 → clippées à 1.0.
- **Nuit + neurogenèse** : `integrateur_bio` (16,48) → (32,64), segment bio fixe à 32 pendant que `dim_bus` double.
- **Round-trip** persistance identique ; 30 ticks après résurrection.
- **`.brain` RÉELS du dépôt** : `naulthene_parole` (pré-v29, 7 actions) greffé 64→80 dims + 7→8 actions, **480 000 ticks et palier vocal 19/19 préservés** ; `naulthene_cursus` (v29, 8 actions) greffé 72→80, 120 000 ticks préservés. 30 ticks OK sur chacun.
- Chemins `vocal_isole` et MiniGrid+audio ; tous les modules importent.

---

## [master] - 2026-08-02 — Intégration des v28.0 et v29.0/v29.1

### Merge de `feat/v28-exocortex-c3` dans `master` + ouverture de la branche v30

| Type | Details |
|------|---------|
| **Commit** | `3582ade` (merge `--no-ff`) |
| **Catégorie** | chore (intégration) |
| **Impact** | Organisation du dépôt — aucun changement de code |

**`master` portait encore la v27.6.** Les trois versions suivantes vivaient sur la branche
`feat/v28-exocortex-c3`. Merge `--no-ff` (et non fast-forward) pour garder une trace lisible de
l'intégration dans l'historique.

`master` contient désormais :

| Version | Apport |
|---------|--------|
| **v28.0** | La Cascade C1→C2→C3 & le Port Exocortex — 8ᵉ action apprise, `PortC3` multiplexeur, plugs interchangeables, greffe 7→8 actions |
| **v29.0** | Le Bus Sensoriel Multimodal & l'identité C1/C2 explicite — les 5 sens, `DIM_VECTEUR_BIO` 16→24, greffe du vecteur bio |
| **v29.1** | Télémétrie des 5 sens — 7 clés W&B `Sens_*`, ligne au bilan de nuit, diagnostic de saturation de l'odorat |

La branche `feat/v30-exo-sens` a été **rebasée sur ce `master`** — elle ne contient pour l'instant
que le document de cadrage `docs/CONCEPTION_v30_exo_sens.md` (aucun code livré).

| Fichier modifié | Changement |
|-----------------|------------|
| `readme.md` | Encadré « État du dépôt » ; nouvelle section v29.1 (absente jusqu'ici) ; section v30.0 explicitement marquée **en cours de conception** ; 2 entrées de table des matières |
| `CLAUDE.md` | Nouvelle sous-section « État des branches » dans *Git Workflow* ; `CONCEPTION_v30_exo_sens.md` ajouté à l'arborescence |
| `docs/CHANGELOG.md` | Cette entrée |
| `docs/LANCEMENT.md`, `docs/Parcourt_readme.md`, `docs/explications_readme.md` | Références de version harmonisées (v29.1) et renvoi vers le cadrage v30 |

⚠️ **La v30.0 n'existe pas encore.** Toute la documentation la présente comme une cible, jamais
comme un état livré — deux points de sa spécification restent d'ailleurs ouverts (voir le document
de cadrage) : la formule d'odorat dynamique ne corrige pas les cartes 4×4 et aggrave le Doctorat,
et la boucle d'attention exogène réintroduirait un seuil codé en dur dans le chemin de décision.

---

## [29.1-experimental] - 2026-08-02

### Télémétrie des 5 Sens — les rendre observables, et un diagnostic de saturation de l'odorat

| Type | Details |
|------|---------|
| **Commit** | `6368e02` |
| **Catégorie** | feat (télémétrie, expérimentale) |
| **Impact** | Fonctionnel (observabilité — aucun impact sur la décision ni le gradient) |

**Constat utilisateur : « dans les tests tu as implémenté tous les sens et mis dans chaque jour pour suivre entièrement tous les éléments ? » — non. La v29.0 câblait bien les 5 sens dans la décision (l'agent les utilise réellement), mais AUCUN des 3 sens ajoutés n'était instrumenté : zéro clé W&B, zéro ligne au bilan de nuit, zéro compteur journalier. Les validations v29.0 étaient des tests PONCTUELS (lecture des signaux à un instant T), pas du suivi. Conséquence concrète : sur un run de 300 jours, il aurait été impossible de répondre à « l'odorat a-t-il jamais servi ? », et une désactivation silencieuse du bus (dégradation gracieuse) n'aurait laissé qu'un unique avertissement console, noyé dans les logs.**

**Audit préalable** : comparaison systématique des 21 compteurs `*_jour` de `EtatCognitif` avec ce qui est réellement loggé. Résultat — **tous les compteurs pré-v29 sont correctement instrumentés** (y compris la télémétrie C3 de la v28.0). L'écart était strictement limité à la v29.0.

**Les 7 nouvelles clés W&B** (préfixe `Sens_`, absentes du log si aucun tick sensoriel n'a été vécu — même logique conditionnelle que le bloc C3) :

| Clé | Ce qu'elle mesure |
|-----|-------------------|
| `Sens_Bus_Actif` | **Métrique de santé** : 0 si le bus s'est désactivé en vol (API minigrid incompatible) |
| `Sens_Toucher_Contact_Ratio` | Part des ticks au contact d'un obstacle (proxy de blocage) |
| `Sens_Toucher_Portage_Ratio` | Part des ticks avec un objet en main — très parlant sur DoorKey (la clé) |
| `Sens_Odorat_Moyen` | Intensité moyenne (nourriture + eau) sur la journée |
| `Sens_Odorat_Max` | Pic d'intensité de la journée |
| `Sens_Odorat_Ticks_Actifs_Ratio` | Part des ticks où au moins une odeur est perçue |
| `Sens_Gout_Ticks_Actifs` | Nombre de ticks avec une trace gustative rémanente |

Plus une ligne au bilan de nuit console, dans le style des lignes existantes, affichée uniquement si des ticks sensoriels ont eu lieu :

```
  ├─ Les 5 Sens     : ✋ Contact 28.5% | 🔑 Portage 20.5% | 👃 Odorat 96.0% des ticks (max 1.50) | 👅 Goût 75 tick(s)
```

Le suffixe `⚠️ BUS DÉSACTIVÉ` s'ajoute si le bus est tombé — l'alerte devient visible à chaque nuit au lieu d'un unique message au moment de la panne.

**⚠️ Diagnostic immédiat livré par cette télémétrie : l'odorat sature sur les petites cartes.** Dès le premier jour instrumenté, `Sens_Odorat_Ticks_Actifs_Ratio = 0.96` et `Sens_Odorat_Max = 1.50` (sur un maximum théorique de 2.0). Vérification par calcul de couverture (4 sources, portée de Manhattan) :

| Carte | `PORTEE_ODORAT=4` (actuelle) | portée 2 | portée 1 |
|-------|------------------------------|----------|----------|
| `Empty-8x8` (intérieur 6×6) | **97.6 %** | 73.3 % | 41.6 % |
| `DoorKey-6x6` (intérieur 4×4) | **100.0 %** | 94.9 % | 71.8 % |
| `MultiRoom-N4-S5` (~13×13) | 56.7 % | 24.5 % | 10.7 % |

Sur les 4 premiers niveaux du `PROGRAMME` (les plus petits), l'odorat est donc **quasi constamment saturé** : un signal presque toujours actif porte très peu d'information, et l'agent ne peut pas s'en servir pour s'orienter. Il ne redevient discriminant qu'au Doctorat (`MultiRoom`).

**Aucune valeur n'a été modifiée** — `PORTEE_ODORAT` reste à 4.0. C'est un constat livré à l'utilisateur, pas un correctif appliqué unilatéralement : le bon réglage dépend de l'intention (un odorat « ambiance de proximité » saturé est un choix valide ; un odorat « boussole vers la ressource » demanderait une portée 1-2, ou une normalisation par la taille de la carte). La télémétrie est désormais en place pour trancher sur données réelles.

| Fichier modifié | Changement |
|-----------------|------------|
| `src/naulthene/cerveau/noyau.py` | 7 compteurs journaliers dans `_reinitialiser_buffers_journee` ; accumulation dans `traiter_tick` juste après la lecture du bus (indices figés par le contrat de `BusSensoriel.interpreter`) ; ligne « Les 5 Sens » au bilan de nuit ; bloc de 7 clés `Sens_*` dans `log_wandb`. |

**Validation** :
- **400 ticks + nuit** : compteurs cohérents (400 ticks sensoriels, contact 114, portage 82, goût 75) et 7 clés `Sens_*` présentes dans le dict retourné par `executer_nuit`.
- **Remise à zéro** confirmée au `demarrer_journee` suivant (pas de cumul depuis la naissance — le piège exact du bug `score_vocal_jour` de la v27.0).
- **Mode `vocal_isole` pur** (aucun env MiniGrid) : `ticks_sensoriels_jour = 0` et clés `Sens_*` **absentes** du log — pas de ligne trompeuse ni de division par zéro.
- **Désactivation du bus en vol** : `Sens_Bus_Actif = 0` et `⚠️ BUS DÉSACTIVÉ` affiché au bilan.
- **Non-régression** : 400 ticks + nuit + neurogenèse + plug C3 + 200 ticks + nuit ; 44 puis 47 clés loggées, les 7 `Sens_*` présentes les deux nuits ; tous les modules importent.
- Les 4 points d'entrée (`cursus_developpemental`, `cursus_bebe`, `cursus_parole`, `daemon_cerveau`) loggent le dict retourné par `executer_nuit` — **les nouvelles clés y remontent automatiquement**, sans modification de ces scripts.

---

## [29.0-experimental] - 2026-08-02

### Le Bus Sensoriel Multimodal & l'Identité C1/C2 explicite — les 5 sens, et une frontière nommée entre le réflexe et le néo-cortex

| Type | Details |
|------|---------|
| **Commit** | `6fbe3df` |
| **Catégorie** | feat (nouvelle mécanique cognitive majeure, expérimentale) |
| **Impact** | Critique (architecture du réseau, persistance) |

**Contexte utilisateur (voir `docs/Maj_V29_readme.md`) : trois idées à intégrer au dépôt existant sans casser ce qui fonctionne. (1) La hiérarchie des 5 sens — tous les sens ne coûtent pas le même prix en calcul, mais c'est la combinaison de leur diversité qui fait émerger une compréhension du monde ; jusqu'en v28.0 Naulthène n'avait que ses deux sens gourmands (vue, ouïe), les trois sens faibles à moyens n'existaient nulle part. (2) L'identité C1/C2 explicite — la distinction réflexe/néo-cortex existait déjà dans le code (`tete_motrice` d'un côté, `simuler_futur_et_planifier` de l'autre) mais restait implicite, entrelacée dans le corps de `penser()`. (3) La boucle de distillation C2 → C1 — qui, contrairement au reste, n'avait PAS besoin d'être écrite : elle est déjà réalisée par le cycle jour/nuit existant (`annexe_weight` → `base_weight` → Cristallisation Souple v26.0), et l'audit de cette version l'a confirmée plutôt que de la réimplémenter en double.**

**Deux décisions structurantes prises par l'utilisateur à la conception :**
- **Câblage des nouveaux sens** : `DIM_VECTEUR_BIO` passe de 16 à 24 dims — le toucher et la chimie entrent par la **queue du vecteur bio** (donc par `integrateur_bio`, juste avant la décision), **pas** par une nouvelle porte synaptique sommée dans le bus latent. Conséquence voulue : les sens faibles ne polluent jamais la cible JEPA (`perte_jepa` compare toujours le bus prédit au bus réel de la **vision seule**), et un cerveau entraîné sur 300+ jours ne voit pas son modèle du monde perturbé.
- **Portée du refactor C1/C2** : **restructuration pure, zéro changement de comportement**. C2 continue d'être sollicité à chaque tick. L'alternative (C1 court-circuite C2 quand il est confiant) a été explicitement écartée : elle aurait introduit un déclenchement sur seuil codé en dur dans le chemin de décision — exactement de la même nature que ce que `CLAUDE.md` interdit déjà pour l'appel à C3.

**1. Le Bus Sensoriel — l'Interpréteur des 5 Sens (`bus_sensoriel.py`, nouveau)**

Module **pur numpy**, qui n'importe jamais `noyau.py` (même discipline que `exocortex/port_c3.py` : aucun cycle d'import, aucune dépendance au réseau). Il ne fait que traduire l'environnement en signaux normalisés. La hiérarchie de gourmandise énergétique implémentée suit exactement le document de conception :

| Sens | Gourmandise | Dims | Chemin dans le cerveau | Dans la cible JEPA ? |
|------|-------------|------|------------------------|----------------------|
| **Vue** | Extrême | 147 | `porte_visuelle` → `bus_latent` | ✅ oui |
| **Ouïe** | Élevée | 130 | `porte_auditive` → `bus_latent` | ✅ oui (tête séparée) |
| **Toucher** | Moyenne | 4 | `vecteur_bio` → `integrateur_bio` | ❌ non |
| **Odorat** | Faible | 2 | `vecteur_bio` → `integrateur_bio` | ❌ non |
| **Goût** | Faible | 2 | `vecteur_bio` → `integrateur_bio` | ❌ non |

- **Le toucher (`DIM_TOUCHER=4`)** : contact frontal (via l'API native `can_overlap()`, plus fiable qu'une liste de types codée en dur), objet en main (`carrying` — en v28.0 l'agent ne savait qu'il tenait la clé qu'indirectement, par la vue), et orientation encodée **sur le cercle** (cos, sin) plutôt qu'en entier 0-3, pour éviter la discontinuité artificielle entre les directions 3 et 0 qui sont voisines dans le monde réel.
- **L'odorat (2 dims)** : intensité de la source de Nourriture/Eau la plus proche, décroissant linéairement sur `PORTEE_ODORAT=4` cases (distance de Manhattan, cohérente avec `DetecteurJalonsDoorKey._distance`). Réutilise la convention déjà posée par `DetecteurRessourcesBiologiques` (Ball rouge = Nourriture, Ball bleue = Eau). Portée volontairement courte : c'est un signal de survie grossier qui oriente, pas une carte — la cartographie précise reste le travail de la vue et de `MemoireEpisodiqueSpatiale`.
- **Le goût (2 dims)** : trace **rémanente** de la dernière ressource réellement consommée, décroissant à `DECROISSANCE_GOUT=0.85`/tick (~10 ticks de persistance). C'est le seul état inter-tick du bus, remis à zéro à chaque épisode — un goût est une sensation immédiate liée à une bouchée, pas un état vital continu comme les jauges du `BiologicalHomeostasisEngine`.
- **Dégradation** : identique aux détecteurs génériques §3b — `_MINIGRID_OK` faux ou toute exception d'API désactive le bus définitivement après **un** avertissement et renvoie des zéros. Jamais de crash, jamais de changement du chemin de gradient.

**2. L'identité C1/C2 explicite (`noyau.py` §2, renommée)**

La section 2 devient « LE CERVEAU C1 (RÉFLEXE) & C2 (NÉO-CORTEX) ». Le corps de `penser()` est désormais l'**arbitrage seul**, et la frontière est encapsulée dans deux méthodes nommées :

- **`_executer_c1_reflexe()`** — tout ce qui coûte quasi rien : compression du flux des 5 sens (`_tronc_cerebral` pour les deux sens gourmands, queue du `vecteur_bio` pour les trois autres), contexte épisodique, intégration viscérale, et le réflexe moteur immédiat (`tete_motrice`) en latence zéro.
- **`_solliciter_c2_neocortex()`** — le moteur analytique lourd (`simuler_futur_et_planifier` + JEPA). Il ne reçoit **que** `pensee_bio`, l'état déjà compressé par C1 : jamais les pixels, jamais le MFCC brut, jamais l'environnement — exactement le schéma de `Maj_V29_readme.md`.

La fusion `logits_instinct + valeurs_simulees * force_planification` reste **strictement inchangée** depuis la v13.0.

**3. La distillation C2 → C1 : auditée, pas réimplémentée**

Le document de conception présente la distillation comme « la pièce maîtresse ». L'audit de cette version confirme qu'elle est **déjà entièrement réalisée** par le cycle de vie existant de `NaultheneLinearSynaptique` : `annexe_weight` accumule le gradient diurne (C2 guide l'expérience) → `cycle_sommeil()` le consolide dans `base_weight` (C2 → C1) → la Cristallisation Souple (v26.0) fige définitivement les synapses les plus myélinisées. Aucun code ajouté ; la boucle est documentée dans `readme.md` plutôt que dupliquée.

**4. Rétrocompatibilité des `.brain` — greffe par recopie, jamais par exclusion**

`DIM_VECTEUR_BIO` 16 → 24 change la **forme** de `integrateur_bio` (entrée `dim_bus + 16` → `dim_bus + 24`). Le filtre historique de `charger_ou_naitre` traitait ce cas en **excluant** la couche, qui renaissait à neuf — c'est le symptôme exact du bug v24.0-fix4 (bouche silencieuse dans l'Arène). Inacceptable sur un `.brain` portant 1000 jours de vécu.

Nouvelle fonction `_greffer_vecteur_bio_etendu`, appelée **en amont** du filtre : les `dim_bus + 16` premières colonnes gardent leurs poids appris, les 8 dernières conservent leur initialisation Xavier atténuée (même sémantique que `NaultheneLinearSynaptique.agrandir()`). L'agent se réveille avec tous ses acquis et découvre simplement qu'il a désormais un toucher, un odorat et un goût, encore muets. Le filtre d'exclusion reste en place derrière, comme trappe de secours pour tout autre mismatch qu'on ne sait pas greffer.

| Fichier modifié | Changement |
|-----------------|------------|
| `src/naulthene/cerveau/bus_sensoriel.py` | **Nouveau.** `BusSensoriel` (toucher, odorat, goût), constantes `DIM_TOUCHER`/`DIM_CHIMIE`/`PORTEE_ODORAT`/`DECROISSANCE_GOUT`, et `hierarchie_sensorielle()` (description déclarative des 5 sens, lecture seule, pour la doc/télémétrie). Pur numpy, aucun import de `noyau`. |
| `src/naulthene/cerveau/noyau.py` | Version 28 → 29. §2 renommée « LE CERVEAU C1 (RÉFLEXE) & C2 (NÉO-CORTEX) » + note de restructuration. Ajout de `_executer_c1_reflexe()` et `_solliciter_c2_neocortex()` ; `penser()` réduit à l'arbitrage. `DIM_VECTEUR_BIO` 16 → 24. `obtenir_vecteur_bio(..., signaux_sensoriels=None)`. `EtatCognitif.bus_sensoriel`, lecture des sens dans `traiter_tick` avant `penser()`, signal de goût sur consommation FOOD/WATER, reset de la trace de goût aux 2 sites de fin d'épisode. |
| `src/naulthene/cerveau/persistance.py` | Nouvelle `_greffer_vecteur_bio_etendu()` (recopie partielle de `integrateur_bio`, 16 → 24 dims bio), câblée en amont du filtre d'exclusion existant, qui devient une trappe de secours. Import de `DIM_VECTEUR_BIO`. |
| `docs/EXPLICATIONS_v29_sens.md` | **Nouveau.** Document explicatif dédié en 11 sections : le problème résolu, la hiérarchie des 5 sens, le détail du Bus Sensoriel (formules du toucher/odorat/goût), pourquoi les sens faibles restent hors de la cible JEPA, l'identité C1/C2, la boucle de distillation (avec table de correspondance note de conception ↔ code existant), JEPA comme Intuition globale, la greffe des `.brain`, les 2 options **volontairement écartées** et pourquoi, la table des 13 validations, le glossaire des constantes. |
| `docs/explications_readme.md` | Nouvelle §15 (résumé algorithmique en 5 sous-sections, renvoi vers le document dédié) + entrée dans la table des matières + pied de page mis à jour (v28.0 → v29.0). |
| `docs/LANCEMENT.md` | En-tête V21-V28 → V21-V29 + encadré « rien à configurer ». Note de greffe `👃` en §1. Nouvelle **§9** (observer les 5 sens en direct, vérifier la hiérarchie, tester la greffe sur une copie de `.brain`, ce que la v29.0 ne change pas). 4 nouvelles lignes de dépannage. |
| `readme.md` | Section « Nouveautés v29.0 » + entrée `3s.` dans la table des matières + diagramme d'architecture cognitico-biologique refait (les 5 sens en entrée, blocs C1/C2 nommés, flèche de distillation) + 3 nouvelles sous-sections d'architecture (Bus Sensoriel & hiérarchie, JEPA comme Intuition, boucle de distillation). |
| `CLAUDE.md` | `bus_sensoriel.py` et `EXPLICATIONS_v29_sens.md` ajoutés à l'arborescence ; §2 renommée « C1 (Réflexe) & C2 (Néo-Cortex) » ; 2 puces d'aperçu (C1/C2 nommés, Bus Sensoriel) ; **3 nouveaux garde-fous** dans *Before Modifying Code* (invariants du Bus Sensoriel/vecteur bio, frontière C1/C2 sans court-circuit, greffe par recopie jamais par exclusion) ; version expérimentale de référence 28.0 → 29.0. |

**Validation** (aucun test automatisé dans ce projet — vérifications manuelles exécutées avant livraison) :
- `DIM_VECTEUR_BIO = 24`, `integrateur_bio` en `(16, 40)` sur un cerveau neuf ; `penser()` renvoie 8 logits, `ACTION_DEMANDER` toujours masquée à `-inf` sans plug (**invariant v28.0 préservé**).
- **Greffe d'un `.brain` simulé pré-v29.0** : les 32 premières colonnes recopiées **bit à bit** (`torch.equal` = True) sur tous les buffers (y compris `cristallisee`, booléen), `annexe_weight` remis à zéro, 8 nouvelles colonnes non nulles ; `load_state_dict` sans clé manquante ni inattendue. Un `.brain` déjà v29.0 traverse la fonction **sans modification**.
- **400 ticks** consécutifs sur `MiniGrid-DoorKey-5x5-v0` : signaux sensoriels cohérents (contact frontal = 1.0 face à un mur, odorat = 0.25 pour une source d'eau à 3 cases, goût décroissant de 1.0 → 0.142 en 12 ticks).
- **Nuit complète** puis **neurogenèse** : `integrateur_bio` passe de `(16, 40)` à `(32, 56)` — le segment bio reste fixe à 24 dims pendant que `dim_bus` double (**invariant `segments_in` respecté**) ; 60 ticks post-neurogenèse OK.
- **Round-trip complet** `PersistanceAnatomique.sauvegarder()` → `charger_ou_naitre()` : `integrateur_bio` identique (`torch.equal` = True), 30 ticks après résurrection OK.
- Chemins **`mode_perception="vocal_isole"`** (sans env MiniGrid, 8 nouvelles dims neutres) et **MiniGrid + audio** testés ; tous les modules de la Cuve, des salles de classe et des instruments importent sans erreur.

---

## [28.0-docs2] - 2026-07-30

### Parcourt_readme.md déplacé de la racine vers docs/

| Type | Details |
|------|---------|
| **Commit** | N/A — en attente du commit de cette version |
| **Catégorie** | docs |
| **Impact** | Documentation |

**Demande utilisateur : ranger `Parcourt_readme.md` dans `docs/` plutôt qu'à la racine.**

`git mv Parcourt_readme.md docs/Parcourt_readme.md` (historique préservé). Tous les liens
relatifs internes au fichier corrigés (`../readme.md` pour remonter à la racine, chemins courts
vers `CHANGELOG.md`/`LANCEMENT.md`/`explications_readme.md` désormais dans le même dossier).
`readme.md` et `CLAUDE.md` mis à jour pour pointer vers `docs/Parcourt_readme.md`.

| Fichier modifié | Changement |
|-----------------|------------|
| `docs/Parcourt_readme.md` | Déplacé depuis la racine (`git mv`), liens internes corrigés pour le nouvel emplacement. |
| `readme.md` | Liens mis à jour : `Parcourt_readme.md` → `docs/Parcourt_readme.md`. |
| `CLAUDE.md` | Entrée déplacée de la liste des fichiers racine vers la description du dossier `docs/`. |

---

## [28.0-docs] - 2026-07-30

### Parcourt_readme.md — guide pratique complet du système de cursus (commandes, jours/ticks, paliers, FAQ)

| Type | Details |
|------|---------|
| **Commit** | N/A — en attente du commit de cette version |
| **Catégorie** | docs |
| **Impact** | Documentation |

**Demande utilisateur : un document unique, à la racine, qui explique de façon vulgarisée et exhaustive TOUT le fonctionnement des 4 parcours d'entraînement (Cursus par Ères, Cerveau Bébé, Cursus de la Parole, la Cuve) — commandes de lancement copier-collables, durée en jours et en ticks/jour de chacun, détail complet des 5 niveaux MiniGrid, des 7 paliers DoorKey, des 19 paliers vocaux, Mode Guidé/Libre, patience adaptative, et un rappel explicite qu'aucune progression ne régresse actuellement. Rédigé à partir d'une lecture directe du code (`noyau.py`, les 3 scripts de `salles_de_classe/`), pas de mémoire — toutes les valeurs (ticks/jour, seuils, poids de choc) vérifiées contre les constantes réelles.**

Nouveau fichier `Parcourt_readme.md`, à la racine du dépôt (comme `readme.md`) plutôt que dans
`docs/` — c'est un guide pratique de premier niveau ("je veux lancer un run"), complémentaire à
`docs/LANCEMENT.md` (guide opérationnel technique, options CLI complètes) et
`docs/explications_readme.md` (détail algorithmique/mathématique). Référencé depuis `readme.md`
(table des matières + lien en tête de la Vue d'Ensemble) et `CLAUDE.md` (arborescence).

| Fichier modifié | Changement |
|-----------------|------------|
| `Parcourt_readme.md` | **Nouveau.** 14 sections : vue d'ensemble des 4 parcours, détail par cursus (commande, rythme ticks/jour, phases/ères), les 5 niveaux MiniGrid, les 7 paliers DoorKey, les 19 paliers vocaux, Mode Guidé/Libre, patience adaptative, absence de régression, emplacement des `.brain`, lecture annotée d'un bilan de nuit, FAQ. |
| `readme.md` | Entrée `3t.` dans la table des matières pointant vers `Parcourt_readme.md` ; lien de renvoi ajouté juste après le tableau des 5 niveaux dans la Vue d'Ensemble. |
| `CLAUDE.md` | `Parcourt_readme.md` ajouté à l'arborescence *Architecture* (fichiers racine). |

**Validation** : toutes les valeurs numériques du document (ticks/jour par cursus : 400/3600/800 ; seuils DoorKey 2+2 ; seuils vocaux 0.15→0.45 ; `PATIENCE_MIN/MAX` 50/350 ; `FORCE_PLANIFICATION_GUIDE/LIBRE` 0.5/0.85 ; `SEUIL_PALIER_MODE_LIBRE=5` ; `JOUR_FIN_MASQUAGE_EXTERNE=240`) vérifiées par grep direct sur `noyau.py` et les 3 scripts de cursus avant rédaction, aucune valeur inventée ou approximée.

---

## [28.0-experimental] - 2026-07-30

### La Cascade C1 → C2 → C3 & le Port Exocortex — un troisième cerveau optionnel, jamais dans le chemin de gradient

| Type | Details |
|------|---------|
| **Commit** | N/A — en attente du commit de cette version |
| **Catégorie** | feat (nouvelle mécanique cognitive majeure, expérimentale) |
| **Impact** | Critique (architecture du réseau, persistance) |

**Contexte utilisateur : ouvrir Naulthène à un greffon externe optionnel (Exocortex C3 — LLM lourd, RAG, recherche web, ou un autre cerveau Naulthène) sans jamais compromettre l'autonomie biologique du Cœur Organique [C1 (réflexe) + C2 (raison/JEPA)]. Principe non négociable posé par l'utilisateur : couper le courant de C3 ne doit ni planter, ni renvoyer d'erreur, ni changer le comportement d'un cerveau existant — l'agent bascule silencieusement sur sa curiosité intrinsèque déjà présente. Décision structurante : "interroger C3" n'est PAS un déclenchement sur seuil d'incertitude, c'est un CHOIX APPRIS par REINFORCE (une 8ème action, "tendre la main"), au même titre que les 7 actions MiniGrid — l'agent apprend lui-même quand demander de l'aide, jamais un `if erreur > seuil`. C3 est conçu comme un Port Multiplexeur (bus) sur lequel des "Plugs" interchangeables s'enregistrent (BrainToBrain, Ollama, VectorDB, Web...), plutôt qu'un appel figé vers un service unique.**

**Chantier 1 — Le Port Multiplexeur** (nouveau sous-package versionné `src/naulthene/exocortex/`) : `PortC3` (le bus), `RequeteC3`/`ReponseC3` (le contrat neutre — uniquement des vecteurs numpy et des scalaires, jamais un tenseur PyTorch, jamais l'agent lui-même), `PlugC3` (classe de base abstraite). Isolation totale : `canal_emission` capture TOUTE exception d'un plug (jamais de fuite vers le noyau) et met le plug fautif en cooldown (`COOLDOWN_PLUG_ECHEC=200` ticks) plutôt que de repayer un timeout complet à chaque tick — la leçon retenue du seul précédent d'appel externe du projet (`professeur_gemma.py`, aucun health-check, jusqu'à 60s de timeout par appel). Trois plugs livrés : `PlugNul` (toujours absent, mode nominal), `PlugSimule` (déterministe, flag `panne` activable en vol pour les crash-tests), `PlugHTTP` (backend générique JSON/HTTP, choix explicite de l'utilisateur plutôt qu'un fournisseur figé).

**Chantier 2 — Le choix appris.** `num_actions` passe de 7 (`NUM_ACTIONS_BASE`) à 8 (`NUM_ACTIONS_AVEC_C3`) : la 8ème action, `ACTION_DEMANDER`, est masquée à `-inf` dans les logits tant qu'aucun plug n'est disponible (`penser()`) — comportement bit-identique à la v27.6 sans plug branché. Nouvelle couche `tete_requete` (tête de routage : vers quel plug émettre, ou diffusion `1_X`), ajoutée aux 4 points de synchronisation (`__init__`, `fortifier_synapses`, `cycle_sommeil_global`, `declencher_neurogenese` — les 4, pas 3, contrairement à la formulation générique de CLAUDE.md). Le rollout mental (`simuler_futur_et_planifier`) remonte désormais aussi `indecision_c2` (l'écart-type brut du rollout, calculé puis jeté depuis la v10.0) — un simple CONTEXTE transmis dans `RequeteC3`, jamais un déclencheur (décision utilisateur explicite). L'action `ACTION_DEMANDER` substitue l'action MiniGrid "done" (6, seule action réellement neutre) à `env.step()` — jamais un pas d'environnement inventé — et coûte `COUT_REQUETE_C3=0.01` en `recompense_interne` (sans quoi REINFORCE apprendrait à spammer le bus gratuitement).

**Chantier 3 — La trappe de secours.** Purement structurelle, aucun code nouveau : sans plug, le masquage rend l'action inexistante ; un plug qui échoue en vol part en cooldown et la curiosité intrinsèque (`DetecteurCuriositeJEPA`) et le Sursaut de Volonté restent actifs en permanence, jamais conditionnés à C3.

**Chantier 4 — Registre d'Assimilation.** Une réponse C3 est mise en attente (`reponse_c3_en_attente`) et appliquée au tick SUIVANT (le bus répond après coup, jamais dans le même pas que l'émission) : sous `SEUIL_OVERRIDE_C3=0.85` de confiance, elle biaise les logits (`+= FORCE_C3 * préférences`, même forme que l'arbitrage C2) ; au-dessus, elle impose l'action (le `log_prob` reste alors celui de l'action réellement jouée sous la distribution courante, pour ne pas invalider REINFORCE). Un conseil C3 suivi d'un succès devient un 3ème canal du "OU doux" v27.0 (`POIDS_DOPAMINE_C3=0.5`, formule étendue à 3 facteurs, toujours bornée dans [0,1] et rétrocompatible à l'identique si `poids_c3=0`) — le LTP (`fortifier_synapses`) et l'importance majorée du souvenir (`micro_boost_ancrage`, déjà existant) font le reste : la trace est rejouée en priorité la nuit, sans réintroduire de distillation supervisée dans la politique (hors du chemin de gradient, cohérent avec la contrainte "pas de Transformer" de `docs/AMELIORATION_V1.md`).

**Le risque n°1 : rétrocompatibilité des `.brain` existants.** `load_state_dict(strict=False)` gère les clés absentes mais PAS un mismatch de forme sur une clé présente des deux côtés — passer à 8 actions change la forme de `tete_motrice`/`generateur_attente`/`generateur_attente_audio`/`actions_eye`. Nouvelle fonction `_greffer_action_supplementaire` (généralise le patron du filtre `integrateur_bio` déjà existant, mais par RECOPIE plutôt que par exclusion) : chaque bloc `[:7]` existant est recopié dans le nouveau tenseur `[:8]`, la 8ème ligne/colonne restant à son initialisation Xavier atténuée — même sémantique que `NaultheneLinearSynaptique.agrandir()`.

| Fichier modifié | Changement |
|-----------------|------------|
| `src/naulthene/exocortex/__init__.py`, `port_c3.py`, `plugs/{__init__,plug_nul,plug_simule,plug_http}.py` | **Nouveaux**, versionnés — le Port Multiplexeur et 3 plugs. |
| `src/naulthene/cerveau/noyau.py` | Nouvelle section `# --- 3h. LE PORT EXOCORTEX C3 ---` (constantes) ; `num_actions=8` par défaut ; couche `tete_requete` (4 points de sync) ; `port_c3` sur `AGI_Naulthene` ; `penser()` masque l'action 7 et retourne `logits_routage`/`indecision_c2` en plus ; `simuler_futur_et_planifier` remonte `indecision_c2` ; `traiter_tick` : émission/réception C3, coût, dopamine 3ème canal, override/biais de la réponse en attente, télémétrie W&B (`Dopamine_Poids_C3_Moyen`, `Requetes_C3_Jour`, `Reponses_C3_Jour`, `Taux_Reponse_C3`). |
| `src/naulthene/cerveau/persistance.py` | Nouvelle fonction `_greffer_action_supplementaire` (greffe par recopie 7→8) appelée dans `charger_ou_naitre` avant `load_state_dict`. |

**Validation** : import de tous les modules du package sans erreur (`noyau`, `persistance`, `daemon_cerveau`, `client_corps`, `lancer_arene`, `irm_cerveau`, `evaluer_cerveau`) ; test d'invariance (300 ticks sans plug, `ACTION_DEMANDER` jamais échantillonnée, seules les 7 actions historiques apparaissent) ; test de rétrocompatibilité sur les 3 vrais `.brain` existants (`naulthene_parole.brain` 300j palier vocal 19/19, `naulthene_cursus.brain`, `naulthene_bb.brain`) chargés sans exception, poids des 7 actions existantes préservés au bit près (vérifié par égalité tensorielle exacte) ; test de déconnexion en vol (`PlugSimule.panne` basculé en cours d'épisode) : aucune exception ne remonte, le plug part en cooldown, l'action redevient masquée au tick suivant ; test des 4 points de synchronisation (`tete_requete` correctement traitée par `cycle_sommeil_global`/`fortifier_synapses`/`declencher_neurogenese`) ; runs réels de 2 jours subjectifs sur les 3 cursus (`cursus_developpemental.py`, `cursus_bebe.py`, `cursus_parole.py`, cerveaux neufs isolés) sans aucune erreur, y compris une neurogenèse réelle traversant `tete_requete`. Les `.brain` réels du dépôt vérifiés strictement inchangés (comparaison octet à octet) après tous les tests.

---

## [27.6-experimental] - 2026-07-27

### Gradient vocal étendu aux 8 paramètres — la voix intègre f0/F3/durée/amplitude, dynamiquement, jamais en dur

| Type | Details |
|------|---------|
| **Commit** | N/A — en attente du commit de cette version |
| **Catégorie** | feat (correctif de conception majeur, mécanique expérimentale) |
| **Impact** | Critique (apprentissage vocal) |

**Décision utilisateur : "le cerveau doit intégrer le son peu importe la forme, en même temps que la vue, et être capable de le restituer — rien ne doit être écrit en dur, tout doit être dynamique." Diagnostic sur un cerveau réel de 300 jours (`naulthene_parole.brain`, palier vocal 19/19) : 6 des 8 paramètres physiques de `tete_vocale` (f0, F3, F1_bw, F2_bw, durée, amplitude) étaient restés figés à leur valeur de naissance au dixième près, quel que soit le nombre de jours d'entraînement — seuls F1/F2 (la "voyelle") recevaient jamais de gradient MSE dirigé (`indices_contraints = [1, 2]`, en dur depuis v22.1). L'agent produisait donc toujours le même timbre/hauteur/durée de voix, même après une longue exposition à une voix réelle riche. La question complémentaire de l'utilisateur ("le cerveau écoute-t-il précisément le temps du mot ?") a confirmé que l'entrée auditive (MFCC figé) était déjà correcte — le problème était uniquement du côté de l'APPRENTISSAGE de la sortie, pas de la perception.**

**Correctif en trois volets, tous DYNAMIQUES (aucune valeur écrite en dur) :** (1) `hemisphere_audio.py` gagne `estimer_pitch_f0` (autocorrélation, technique standard de pitch-tracking — aucune constante, la fréquence est cherchée dans la plage physique `BORNES_F0`), `estimer_duree_amplitude` (mesures directes du signal : longueur réelle, crête absolue), et l'extraction de F3 est ajoutée à `estimer_formants_lpc` (3e racine LPC triée, déjà calculée mais jusqu'ici ignorée). `estimer_parametres_vocaux_complets`/`_agreges` combinent les trois pour produire les 8 paramètres à partir d'UN enregistrement réel (F1_bw/F2_bw n'ont pas d'équivalent mesurable simplement par LPC — repli sur le centre de leur plage de synthèse, pas une valeur de voix théorique). (2) `lecons_vocales.CacheReferencesVocales` retourne désormais ce dict à 8 dimensions — dérivé de la banque personnelle si elle existe, SINON de la référence `say` elle-même (déjà générée dans ce chemin) : même le repli `say` devient une estimation acoustique dynamique, plus une table théorique figée (`VOYELLES_CIBLES` et `_voyelle_dominante`, devenues mortes, retirées). (3) `noyau._construire_cible_vocale` normalise chaque dimension EFFECTIVEMENT présente dans `formants_cibles` (au lieu de F1/F2 systématiquement) ; `_evaluer_production_vocale` calcule `indices_contraints` à partir des clés réellement fournies — un appelant qui ne donne encore que F1/F2 (`client_professeur.py`) reste contraint à `[1, 2]`, rétrocompatibilité stricte ; un appelant qui fournit les 8 clés (les 3 cursus, l'Arène, via `CacheReferencesVocales`) contraint désormais les 8 dimensions.**

| Fichier modifié | Changement |
|-----------------|------------|
| `src/naulthene/audio/hemisphere_audio.py` | `estimer_formants_lpc` retourne aussi `F3` (3e candidat trié des racines LPC déjà calculées). Nouvelles `estimer_pitch_f0` (autocorrélation), `estimer_duree_amplitude` (mesure directe), `estimer_parametres_vocaux_complets`/`_agreges` (les 8 paramètres, combinant les trois). |
| `src/naulthene/audio/lecons_vocales.py` | `_generer_si_absent` utilise `estimer_parametres_vocaux_agreges`(banque)/`estimer_parametres_vocaux_complets`(repli `say`) au lieu de `estimer_formants_agrege`(2 dims)/`VOYELLES_CIBLES` théorique. `_mot_cible_du_palier` simplifiée (ne retourne plus de formants théoriques, devenus inutiles). `_voyelle_dominante` retirée (plus aucun appelant). |
| `src/naulthene/cerveau/noyau.py` | Import étendu (`BORNES_F0/F3/BW/DUREE/AMPLITUDE`). `_construire_cible_vocale` : boucle sur les 8 dimensions (clé présente → normalisée, absente → neutre 0.5) au lieu de F1/F2 en dur. `_evaluer_production_vocale` : `indices_contraints` calculés dynamiquement depuis les clés présentes dans `formants_cibles`, plus `[1, 2]` fixe. |

**Validation** : `estimer_pitch_f0`/`estimer_duree_amplitude`/`estimer_parametres_vocaux_complets` testés sur les 5 voyelles + "porte" via `say` (f0 dans une plage plausible 135-207Hz, durée/amplitude cohérentes avec le signal réel, valeurs clampées correctement) ; agrégation multi-prises et repli sur liste vide vérifiés ; `_construire_cible_vocale` testée avec dict complet (8 dims normalisées) et partiel (F1/F2 seuls, reste neutre) ; indices contraints vérifiés dynamiques dans les deux cas (`[0..7]` complet, `[1,2]` partiel = rétrocompatibilité stricte avec `client_professeur.py`) ; run réel de 2 jours sur `naulthene_parole.brain` (cerveau de 300 jours, palier 19/19) confirmant le déblocage effectif : `f0` 190.0→187-189 (mouvement vers la cible 114.7), `F3` 2750.0 (figé depuis 300 jours)→2730-2744 (mouvement vers la cible 2502.1), `durée` 0.3→0.4 (vers la cible 0.6), en seulement 2 jours d'entraînement supplémentaires ; non-régression confirmée sur `cursus_developpemental.py` (2 jours, aucune erreur) ; les 4 points de synchronisation des couches vérifiés intacts ; tous les modules consommateurs importés sans erreur. Les deux cerveaux de test restaurés à leur état pré-vérification après validation.

---

## [27.5-experimental] - 2026-07-27

### Dopamine vocale proportionnelle à la méconnaissance — corrige la "boucle infinie de promotion vocale"

| Type | Details |
|------|---------|
| **Commit** | N/A — en attente du commit de cette version |
| **Catégorie** | fix (défaut de conception, mécanique expérimentale) |
| **Impact** | Critique (réservoir dopaminergique) |

**Diagnostic détaillé de l'utilisateur, confirmé par lecture du code : une fois le dernier palier du curriculum vocal (19) atteint, `promouvoir_palier_vocal_si_merite` continuait d'enregistrer des succès et d'afficher `🎓 [PROMOTION VOCALE]` tous les ~2 jours (bug de log — la garde existante empêchait bien le dépassement du palier 19, mais pas l'affichage du message ni l'accumulation de "succès fantômes" dans le gestionnaire). Plus important : `poids_vocal` (le score de prononciation du tick) alimentait la dopamine (`POIDS_DOPAMINE_VOCAL * poids_vocal`), le LTP hebbien et la micro-récompense RL SANS AUCUNE décroissance liée à la maîtrise déjà acquise — un agent qui maîtrise parfaitement le curriculum vocal depuis longtemps recevait le même choc dopaminergique qu'un débutant qui vient de réussir sa première voyelle. Sur un cerveau resté bloqué sur MiniGrid (Collège, palier DoorKey 7), ce shoot quotidien maintenait `teneur_dopamine`/`plasticite_base` artificiellement hauts, sans la tension motivationnelle nécessaire pour progresser sur le reste du cursus — exactement le mécanisme décrit par l'utilisateur ("moins il sait, plus l'effet est fort ; plus il sait, moins les effets sont forts").**

**Correctif en deux volets.** (1) Nouvelle fonction `facteur_nouveaute_vocale(etat)` : décroissance LINÉAIRE de 1.0 (palier 1) à `FACTEUR_NOUVEAUTE_VOCALE_MIN=0.1` (palier 19, jamais 0 — cohérent avec `TAUX_FRICTION`, rien dans ce moteur ne tombe à un plancher dur exactement nul), appliquée à `poids_vocal` **uniquement** pour la dopamine/le LTP/la micro-récompense — **jamais** pour la perte MSE supervisée (l'agent doit continuer à s'entraîner à plein régime, sinon il désapprendrait) ni pour `score_vocal_jour`/la logique de promotion (sinon le mécanisme de promotion s'auto-invaliderait). Le Module Parent ("Oui !"/"Non !") continue de juger le score BRUT, pas le score pondéré, pour ne jamais fausser sa décision. (2) `promouvoir_palier_vocal_si_merite` court-circuite dès `etat.palier_vocal >= len(CURRICULUM_VOCAL)`, avec un unique message `🏆 [MAÎTRISE VOCALE]` affiché une seule fois à la transition finale plutôt qu'un `🎓 [PROMOTION VOCALE]` répété indéfiniment.

**Question complémentaire de l'utilisateur, clarifiée** : le système n'écoute PAS "pendant X secondes le temps du mot" en fonction de ce que l'agent regarde — `obs_auditive` est un vecteur MFCC statique (un instantané figé, pas un flux temporel), envoyé identique à chaque tick tant que la cible ne change pas. Le mécanisme de stabilité de la case frontale (v27.4, `SEUIL_STABILITE_SYNESTHESIE`) contrôle QUAND la cible peut changer, pas combien de temps l'oreille "écoute" — ce sont deux mécanismes distincts, et aucun des deux ne modélise une vraie durée d'écoute.

| Fichier modifié | Changement |
|-----------------|------------|
| `src/naulthene/cerveau/noyau.py` | Nouvelle constante `FACTEUR_NOUVEAUTE_VOCALE_MIN=0.1`. Nouvelle fonction `facteur_nouveaute_vocale(etat) -> float`. `_traiter_tick_vocal_isole` : `poids_vocal_dopamine = poids_vocal * facteur_nouveaute_vocale(etat)` utilisé dans `poids_evenement`, `poids_vocal` brut conservé pour `_appliquer_feedback_parent_vocal`. `traiter_tick` : même principe, plus `micro_recompense_vocale` également pondérée avant d'entrer dans `recompense_interne`. `promouvoir_palier_vocal_si_merite` : court-circuit au dernier palier + message `🏆 [MAÎTRISE VOCALE]` unique. |

**Validation** : `facteur_nouveaute_vocale` testée sur plusieurs paliers (1→1.0, 5→0.8, 10→0.55, 15→0.3, 19→0.1, clamp au-delà de 19) ; comparaison directe de la contribution dopaminergique pour un même score de prononciation (0.9) : 0.630 au palier 1 vs 0.063 au palier 19 (facteur 10 de réduction) ; court-circuit du message de fausse promotion vérifié (aucun affichage à `palier_vocal=19` avec un score parfait sur 100 ticks) ; transition réelle 18→19 vérifiée (4 appels simulant les 4 succès requis, message de maîtrise affiché une seule fois, silence confirmé sur 5 appels suivants) ; run réel de 2 jours sur un cerveau neuf `naulthene_parole.brain` (phase 1, synesthésie active) sans erreur ni message de fausse promotion.

---

## [27.4-experimental] - 2026-07-27

### Cible synesthésique stabilisée — la cible vocale n'est publiée qu'après une exposition continue

| Type | Details |
|------|---------|
| **Commit** | N/A — en attente du commit de cette version |
| **Catégorie** | fix (défaut de conception, mécanique expérimentale) |
| **Impact** | Fonctionnel (mécanisme d'apprentissage vocal, phases 1-2 du Cursus de la Parole) |

**Diagnostic de l'utilisateur, confirmé par lecture du code : en phases 1-2 (synesthésie active), `LecteurCaseFrontale.lire`/`lire_syntagme` sont relues à CHAQUE tick, donc la cible vocale changeait aussi vite que le regard de l'agent — jusqu'à 10×/seconde dans l'Arène, sans aucune notion de "temps nécessaire pour apprendre un mot". Un agent qui tournait sur lui-même voyait sa cible passer de "mur" à "vide" à "porte" en 2-3 ticks, sans jamais laisser à `porte_auditive`/`tete_vocale` le temps d'associer le son au bon objet. Nouvelle méthode `LecteurCaseFrontale.lire_stable` : la cible publiée ne change que si l'agent a regardé LE MÊME mot pendant au moins `SEUIL_STABILITE_SYNESTHESIE=20` ticks CONSÉCUTIFS (un aller-retour du regard remet le compteur à zéro, sans tolérance) ; tant qu'aucune cible n'a jamais été stabilisée, aucune correction n'est appliquée (`formants_cibles=None`) plutôt que de risquer une fausse association. `cursus_parole._cible_synesthesique` retourne désormais un booléen `notable` en plus de `(mot, mfcc, formants)`, consommé par `_perception_du_tick_parole` pour désactiver la correction/le score spectral tant que la cible n'est pas stabilisée.**

| Fichier modifié | Changement |
|-----------------|------------|
| `src/naulthene/cerveau/noyau.py` | Nouvelle constante `SEUIL_STABILITE_SYNESTHESIE=20`. `LecteurCaseFrontale.__init__` gagne un état de stabilisation (`_mot_brut_courant`, `_ticks_stables`, `_cible_stabilisee`). Nouvelle méthode `lire_stable(env, seuil_stabilite, syntagme) -> (mot, type_objet, couleur, stable_ce_tick)`. |
| `src/naulthene/salles_de_classe/cursus_parole.py` | `_cible_synesthesique` utilise `lire_stable` au lieu de `lire`/`lire_syntagme` bruts, retourne `(mot, mfcc, formants, notable)`. `_perception_du_tick_parole` (phase 1 matin, phase 2) : `formants_cibles`/`mfcc_references` conditionnés par `guide AND notable` au lieu de `guide` seul. |

**Validation** : test sur `MiniGrid-DoorKey-6x6-v0` réel — agent qui tourne en boucle (action "left" en continu) ne stabilise jamais aucune cible sur 60 ticks (comportement voulu : jamais de fausse association) ; agent immobile (action "done" en boucle) stabilise sa cible exactement au tick `SEUIL_STABILITE_SYNESTHESIE` puis la conserve. Run réel de 3 jours sur `naulthene_parole.brain` traversant la transition phase 0→phase 1 (jour 300, `lire_stable` exercée en conditions réelles) : aucune erreur, promotion de palier vocal validée normalement.

---

## [27.3-experimental] - 2026-07-27

### Rythme de lecture vocale ralenti dans l'Arène — corrige l'effet "métronome" (TUT TUT TUT)

| Type | Details |
|------|---------|
| **Commit** | N/A — en attente du commit de cette version |
| **Catégorie** | fix (mécanique expérimentale) |
| **Impact** | Fonctionnel (qualité de la démo audio, aucune conséquence sur l'entraînement) |

**Second correctif signalé par l'utilisateur après [27.2] : les micro-coupures avaient disparu, mais le résultat sonnait comme un martèlement régulier ("TUT TUT TUT") plutôt qu'un rythme de parole — `PERIODE_LECTURE_VOCALE=5` (0.5s) laissait le son finir mais enchaînait quasi immédiatement le suivant, sans silence perceptible. Remonté à 18 ticks (≈1.8s à `FPS_ARENE=10`), plus proche du rythme naturel d'un mot prononcé toutes les 1.5-2s. `hemisphere_audio.BORNES_DUREE` (0.1-0.6s, la plage physique que `tete_vocale` apprend à viser sur TOUS les cursus) n'est volontairement PAS touchée — ce n'est qu'un problème de cadence d'AFFICHAGE dans l'Arène, la faire bouger perturberait l'apprentissage en cours sur les autres cursus pour un problème qui n'existe que dans un outil d'observation.**

**Diagnostic complémentaire (échantillonnage réel sur `naulthene_parole.brain`, jour 20/300)** : le "bip" répété plutôt qu'une syllabe qui varie est cohérent avec l'état d'apprentissage — sur 6 ticks consécutifs, `tete_vocale` produit des paramètres vocaux quasi identiques (`f0≈190Hz`, `F1_bw`/`F2_bw`/`durée`/`amplitude` figés sur des valeurs rondes, F1/F2 ne variant que de quelques Hz). Seuls F1/F2 reçoivent un vrai gradient supervisé (voir `noyau._evaluer_production_vocale`) ; les 6 autres paramètres n'évoluent qu'indirectement (LTP/rêve) et n'ont pas encore développé de variation temporelle notable à ce stade — pas un bug, un cerveau encore jeune sur le plan vocal.

| Fichier modifié | Changement |
|-----------------|------------|
| `src/naulthene/instruments/lancer_arene.py` | `PERIODE_LECTURE_VOCALE` 5 → 18 (≈0.5s → ≈1.8s). |

**Validation** : import du module vérifié sans erreur ; échantillonnage direct des paramètres vocaux produits par `naulthene_parole.brain` sur 6 ticks réels (`traiter_tick`) pour confirmer que le manque de variation vient de l'état d'apprentissage, pas d'un défaut de synthèse.

---

## [27.2-experimental] - 2026-07-27

### Lecture vocale espacée dans l'Arène — corrige les micro-coupures audio permanentes

| Type | Details |
|------|---------|
| **Commit** | N/A — en attente du commit de cette version |
| **Catégorie** | fix (mécanique expérimentale) |
| **Impact** | Fonctionnel (qualité de la démo audio, aucune conséquence sur l'entraînement) |

**Signalé par l'utilisateur : le babil de l'agent joué par l'Arène (`lancer_arene.py`) sonnait comme une suite ininterrompue de micro-coupures/craquements. Cause : `jouer_son_temps_reel` était appelée à CHAQUE tick (10/s, `FPS_ARENE`) en mode non-bloquant (`sd.play(..., bloquant=False)`) — un son synthétisé dure entre 0.1 et 0.6s (`hemisphere_audio.BORNES_DUREE`), donc un nouveau `sd.play()` coupait quasi systématiquement le son précédent en plein milieu, indépendamment du niveau réel d'apprentissage vocal du cerveau observé. La lecture (pas le calcul du score) est désormais espacée : un seul son émis toutes les `PERIODE_LECTURE_VOCALE=5` ticks (0.5s, au-dessus de la durée maximale d'un son), laissant chaque vocalisation se terminer avant la suivante. Le score de formants et la télémétrie continuent d'être recalculés à CHAQUE tick — seule l'émission sonore est ralentie.**

| Fichier modifié | Changement |
|-----------------|------------|
| `src/naulthene/instruments/lancer_arene.py` | Nouvelle constante `PERIODE_LECTURE_VOCALE=5`. L'appel à `synth.synthetiser`/`jouer_son_temps_reel` est conditionné à `ticks_journee_observation % PERIODE_LECTURE_VOCALE == 0` ; le calcul de `formants_produits`/`score_vocal` (télémétrie) reste hors de cette condition, à chaque tick. |

**Validation** : import du module vérifié sans erreur ; la garantie de non-altération du `.brain` (aucun `executer_nuit`/`apprendre_journee`/`rever` appelé) est inchangée par ce correctif, qui ne touche qu'à la cadence de lecture audio.

---

## [27.1-experimental] - 2026-07-27

### Tirage aléatoire d'une prise vocale à chaque appel — variation naturelle plutôt qu'un gabarit moyenné figé

| Type | Details |
|------|---------|
| **Commit** | `18e8c7a` |
| **Catégorie** | feat (correctif de conception, mécanique expérimentale) |
| **Impact** | Fonctionnel (mécanisme d'apprentissage vocal) |

**Décision utilisateur : quand plusieurs prises existent pour un mot (`voix/<mot>/<mot>_01.wav`, `_02.wav`, `_03.wav`...), l'oreille de l'agent (`porte_auditive`) ne doit jamais entendre un seul gabarit artificiel figé, mais la vraie variation naturelle d'une voix humaine — pour forcer l'agent à généraliser (reconnaître "mur" malgré le bruit inter-prise) plutôt qu'à mémoriser un son qui n'existe pas en dehors du cache. Jusqu'ici, `CacheReferencesVocales.obtenir_pour_palier` — la méthode appelée à chaque tick par les 3 cursus et l'Arène — renvoyait la MOYENNE des MFCC de toutes les prises d'un mot, calculée une fois et mise en cache : un seul son moyenné et identique du premier au dernier tick d'un run. Elle tire désormais UNE prise au hasard, uniformément, À CHAQUE APPEL (donc potentiellement à chaque tick) — vérifié sur 300 tirages avec 3 prises synthétiques distinctes : les 3 reviennent, en proportions proches de l'uniforme (83/94/123). Avec 0 ou 1 prise (repli `say` ou banque incomplète), le tirage se réduit trivialement à cette unique prise — comportement strictement inchangé.**

| Fichier modifié | Changement |
|-----------------|------------|
| `src/naulthene/audio/lecons_vocales.py` | `_generer_si_absent` : condition de présence en cache basée sur `_cache_mfcc_prises` (liste des prises individuelles) au lieu de `_cache_mfcc` (moyenne) — la moyenne (`_cache_mfcc`) est conservée pour diagnostic/repli `say` mais n'est plus lue par `obtenir_pour_palier`. `obtenir_pour_palier` : tire `prises[np.random.randint(len(prises))]` à chaque appel au lieu de renvoyer la moyenne mise en cache. `obtenir_mfcc_prises` (canal spectral, `recompense_vocale_mixte`) inchangée — continue de comparer au score MAX sur TOUTES les prises, indépendamment de celle tirée pour l'audition ce tick-là. |

**Validation** : fixture de test à 3 prises synthétiques acoustiquement distinctes (tonalités 400/600/800 Hz) — 300 tirages donnent bien 3 signatures MFCC distinctes, aucune ne domine anormalement ; repli `say`/1-prise vérifié strictement stable (10 tirages consécutifs → 1 seule signature) ; tous les modules consommateurs (`cursus_parole.py`, `cursus_bebe.py`, `cursus_developpemental.py`, `lancer_arene.py`) réimportés sans erreur après le changement.

---

## [27.0-experimental] - 2026-07-27

### L'École de la Parole & Synesthésie — voix réelle de l'utilisateur, synesthésie ancrée dans la vision, dopamine unifiée

| Type | Details |
|------|---------|
| **Commit** | N/A — `src/naulthene/cerveau/noyau.py` est gitignored (terrain d'essai expérimental), aucun commit ne le modifie ; voir la table ci-dessous pour les fichiers packagés réellement commités |
| **Catégorie** | feat (nouvelle mécanique cognitive majeure) |
| **Impact** | Critique (mécanisme de récompense/dopamine) + Fonctionnel (local uniquement) |

**Trois décisions structurantes referment les trois plus gros écarts entre l'hémisphère audio (v22.0-v26.0) et une vraie acquisition du langage ancrée dans le monde. (1) La cible vocale n'est plus une table théorique (`VOYELLES_CIBLES`) mais la voix RÉELLE de l'utilisateur : une banque d'enregistrements disque (`voix/<mot>/<mot>_NN.wav`, `instruments/enregistreur_voix.py`, recadrage de silence via `librosa.effects.trim`) alimente un estimateur de formants par analyse LPC (`hemisphere_audio.estimer_formants_lpc`, filtre inverse du modèle source-filtre du synthétiseur, clampé aux bornes physiques de `tete_vocale` pour rester atteignable), et une distance/récompense spectrale MFCC↔MFCC (`distance_spectrale`/`recompense_spectrale`) note l'agent sur le son RÉELLEMENT synthétisé et pas seulement sur deux nombres — `recompense_vocale_mixte` combine les deux (0.6 formants / 0.4 spectral, F1/F2 restant dominants car ce sont les seules dimensions sur lesquelles `tete_vocale` reçoit un gradient MSE dirigé), avec repli exact sur `recompense_formants` seule quand aucune prise n'existe (rétrocompatibilité stricte). (2) La synesthésie devient réelle : un nouveau lecteur générique (`LecteurCaseFrontale`, section 3g, `env.unwrapped.front_pos`) lit le mot à nommer directement dans la case devant l'agent — mur/porte/clé/but/vide, puis des syntagmes couleur+objet ("porte jaune") — au lieu d'un curriculum vocal déroulé indépendamment de ce que l'agent regarde ; 5 nouveaux paliers (15-19) étendent `CURRICULUM_VOCAL` en conséquence. (3) La dopamine devient unifiée entre les deux modalités : le `max(canaux visuels…, canal vocal)` pré-v27.0, qui laissait un agent recevoir la même dopamine qu'il ait fait UNE chose bien ou DEUX à la fois, est remplacé par une agrégation probabiliste "OU doux" (`1 - (1 - w_v·visuel)·(1 - w_a·vocal)`, `POIDS_DOPAMINE_VISUEL=1.0`, `POIDS_DOPAMINE_VOCAL=0.7`), bornée dans [0,1] par construction et rétrocompatible au bit près quand `poids_vocal=0`. En plus : la consolidation nocturne rejoue désormais l'audio pendant le rêve (`AGI_Naulthene.rever` gagne `coeff_jepa_audio`, `memoire_moyen_terme` stocke `obs_auditive`) — jusqu'ici tout l'apprentissage vocal du jour s'érodait la nuit sans jamais être consolidé ; le synthétiseur de formants est vectorisé (`scipy.signal.lfilter`, ~100× plus rapide, sortie numériquement identique) pour absorber le coût du canal spectral ; deux bugs bloquants sont corrigés (`score_vocal_jour`/`ticks_vocaux_jour` jamais remis à zéro → promotion vocale figée après quelques centaines de jours ; standardisation MFCC par constantes calibrées sur `say` → risque de re-saturer la sigmoid face à une vraie voix, remplacée par une standardisation par échantillon) ; un bug latent est corrigé (`"clé"` ne contenait aucune voyelle de `VOYELLES_CIBLES` avant dépliage NFD des accents). Nouveau troisième cursus développemental, `salles_de_classe/cursus_parole.py` (`naulthene_parole.brain`, dédié, jamais partagé), 900 jours × 800 ticks en 3 phases pédagogiques : Imprégnation totale (guidage=1.0 constant, correction même quand l'agent a bon) → Autonomie guidée (matin synesthésie/après-midi curriculum, guidage 1.0→0.4) → Émancipation (synesthésie + syntagmes toute la journée, guidage 0.4→0.1, Gemma en jugement qualitatif de fin de journée uniquement).**

| Fichier modifié | Changement |
|-----------------|------------|
| `src/naulthene/cerveau/noyau.py` | En-tête corrigé (v20→v27). Import module-level de `hemisphere_audio` (pur numpy, sans risque de cycle). Nouveaux helpers §4b factorisés (`_construire_cible_vocale`, `_evaluer_production_vocale`, `promouvoir_palier_vocal_si_merite`) remplaçant 2 paires de blocs dupliqués entre `traiter_tick`/`_traiter_tick_vocal_isole`. Nouvelle section 3g `LecteurCaseFrontale` (générique, sans état inter-tick). Dopamine unifiée (`POIDS_DOPAMINE_VISUEL`/`POIDS_DOPAMINE_VOCAL`, formule "OU doux") dans les deux chemins de tick. `_reinitialiser_buffers_journee` : reset de `score_vocal_jour`/`ticks_vocaux_jour` + nouveaux accumulateurs de télémétrie (`score_formants_jour`, `score_spectral_jour`, `dopamine_poids_*_jour`) + cache du canal spectral (`_tick_dernier_spectral`). `AGI_Naulthene.rever` : nouveau paramètre `coeff_jepa_audio`, reconstruit le batch audio seulement si tous les souvenirs tirés en ont un. `traiter_tick`/`_traiter_tick_vocal_isole` gagnent `mfcc_references` (par défaut `None`, inerte). `NB_PALIERS_VOCAUX` 14→19. Nouvelles constantes/helpers du Cursus de la Parole (`TICKS_PAR_JOUR_PAROLE=800`, `BORNES_PHASES_PAROLE=(300,600)`, `taux_guidage_parole`, `phase_parole`). Nom de run W&B du mode standalone mis à jour. |
| `src/naulthene/audio/hemisphere_audio.py` | `SynthetiseurFormants._resonateur` vectorisé via `scipy.signal.lfilter` (repli sur la boucle Python si scipy absent). `extraire_mfcc` gagne `standardisation="echantillon"` (CMVN par échantillon, remplace les constantes `MFCC_MOYENNE_EMPIRIQUE`/`MFCC_ECART_TYPE_EMPIRIQUE` calibrées sur `say` ; mode `"constantes"` conservé pour A/B). Nouvelle section « Analyse acoustique de références réelles » : `estimer_formants_lpc` (LPC de Burg, pré-accentuation, filtrage par bande passante, clamp aux bornes physiques du synthétiseur), `estimer_formants_agrege` (médiane inter-prises), `distance_spectrale`/`recompense_spectrale` (cosinus sur MFCC), `recompense_vocale_mixte` (score pondéré 0.6/0.4, repli exact sur `recompense_formants` sans banque). |
| `src/naulthene/audio/lecons_vocales.py` | `CacheReferencesVocales` lit d'abord `voix/<mot>/<mot>_NN.wav` (nouvelle `_references_depuis_banque`), replie sur `say` si aucune prise — interface `obtenir_pour_palier` inchangée. Nouveau `obtenir_mfcc_prises` (MFCC individuels, pour le canal spectral) et `resume_banque()`. `_voyelle_dominante` (nouveau, dépliage NFD) corrige le bug `"clé"` ; `_mot_cible_du_palier` mis à jour. |
| `src/naulthene/audio/professeur_gemma.py` | `CURRICULUM_VOCAL` étendu 14→19 paliers (15 mur, 16 clé, 17 but, 18 vide, 19 "porte jaune"). |
| `src/naulthene/instruments/enregistreur_voix.py` (nouveau) | CLI d'enregistrement de la banque vocale : capture micro + recadrage de silence (`librosa.effects.trim`) + relecture/validation interactive, convention `voix/<mot>/<mot>_NN.wav`, jamais d'écrasement d'une prise existante. Ne modifie jamais un `.brain`. |
| `src/naulthene/salles_de_classe/cursus_parole.py` (nouveau) | Troisième cursus développemental, calqué sur `cursus_bebe.py`/`cursus_developpemental.py` : 900 jours × 800 ticks, 3 phases (Imprégnation/Autonomie guidée/Émancipation), `_cible_synesthesique` relie `LecteurCaseFrontale` au curriculum vocal, `_perception_du_tick_parole` orchestre mode/guidage par phase. Cerveau dédié `naulthene_parole.brain`. |
| `.gitignore` | Nouvelle entrée `voix/*` (+ `!voix/.gitkeep` tracké) — banque vocale personnelle, données binaires lourdes, même raisonnement que `brains/*.brain`. |

**Changements de dynamique à surveiller sur les runs existants** (non-régression structurelle garantie par ailleurs — tous les nouveaux paramètres ont une valeur par défaut inerte) :
- **Dopamine vocale −30% en mode `vocal_isole`** : `POIDS_DOPAMINE_VOCAL=0.7` réduit le choc dopaminergique de tous les ticks vocaux isolés des cursus existants (`cursus_developpemental.py`, `cursus_bebe.py`) par rapport au comportement pré-v27.0 (poids plein) — effet en cascade possible sur `plasticite_base` → pourcentage de rêve → neurogenèse. En mode `"minigrid"` avec `poids_vocal=0` (aucune leçon active), le comportement reste identique au bit près.
- **Seuils de promotion vocale abaissés** : `NB_PALIERS_VOCAUX` 14→19 abaisse mécaniquement le seuil de chaque palier intermédiaire déjà atteint (interpolation sur une plage plus longue) — assouplissement, aucun risque de blocage.
- **Cascade de promotions possible sur les `.brain` anciens** : le correctif de reset quotidien débloque d'un coup une moyenne qui était figée depuis la naissance du cerveau — comportement correct (rattrapage d'une dette), pas un bug.

**Validation** : non-régression numérique de la vectorisation du synthétiseur (`np.allclose` boucle Python vs `lfilter`, écart max nul) ; estimateur LPC testé sur les 5 voyelles théoriques via `say` (F1/F2 dans la bonne topologie relative, garde-fou du percentile d'énergie de trame validé empiriquement contre l'inversion F1/F2 sur les trames d'attaque/chute) ; invariants de `recompense_vocale_mixte` vérifiés (rétrocompatibilité stricte sans banque, bornes [0,1] avec banque) ; `LecteurCaseFrontale` testé sur 300 pas aléatoires réels (`MiniGrid-DoorKey-6x6-v0`) — mur/porte/clé/vide et syntagmes couleur+objet tous détectés, aucune `AssertionError` de `Grid.get` ; les 19 paliers du curriculum vérifiés individuellement résolubles vers une cible de voyelle valide ; `rever()` testé avec et sans audio dans le lot (rétrocompatibilité + nouveau chemin, tous deux sans erreur) ; run réel bout-en-bout d'1 jour de `cursus_parole.py` sur cerveau neuf (préchauffage, 800 ticks, dream, cristallisation, sans crash) ; les 3 phases pédagogiques testées individuellement en forçant `etat.jour` (imprégnation, autonomie guidée avec bascule matin/après-midi synesthésie/curriculum, émancipation avec syntagmes) ; non-régression confirmée sur `cursus_developpemental.py` (2 jours sur le cerveau existant `naulthene_cursus.brain`, resurrection/palier/sursaut/rêve/cristallisation fonctionnels, aucune exception) ; les 4 points de synchronisation des couches `NaultheneLinearSynaptique` vérifiés intacts (`fortifier_synapses`/`cycle_sommeil_global`/`declencher_neurogenese`) ; tous les modules consommateurs (`cursus_bebe.py`, `cursus_developpemental.py`, `lancer_arene.py`, `client_professeur.py`, `daemon_cerveau.py`) importés sans erreur.

---

## [26.0-experimental] - 2026-07-27

### L'Arène augmentée — mini-IRM en pygame et télémétrie complète en direct

| Type | Details |
|------|---------|
| **Commit** | `47bfa2e` |
| **Catégorie** | feat |
| **Impact** | Fonctionnel (instrumentation d'observation) |

**L'Arène (`lancer_arene.py`/`arene_visuelle.py`) fusionne désormais en une seule fenêtre pygame ce qui vivait jusqu'ici dans deux outils séparés : voir l'agent bouger dans MiniGrid ET observer les activations de son cerveau, sur le MÊME agent en mémoire (pas un second `charger_ou_naitre()` qui aurait divergé). Une bande "mini-IRM" sous l'image affiche en direct les barres d'activation du bus latent aux 3 étapes du tronc cérébral (vision/mémoire/pensée) — le pendant temps-réel du panneau 1 de `irm_cerveau.py`, mais rendu avec des primitives `pygame.draw` plutôt qu'en matplotlib (mélanger les deux frameworks GUI dans le même thread est fragile sur macOS, SDL et le backend GUI de matplotlib se disputant la boucle d'événements native Cocoa). Le panneau de télémétrie de droite est étendu à la parité complète avec le bilan de nuit console (13 lignes : état mental, plasticité, jalons DoorKey, abnégation, mode décision, portes, potentiomètre, curiosité JEPA, viscéral, métabolisme, mémoire épisodique, erreur JEPA/thermostat) — les trois métriques qui n'existent QUE après une vraie nuit (plasticité base, souvenirs rejoués, thermostat de neurogenèse) sont remplacées par des proxys recalculés en continu avec la même formule, explicitement marqués comme estimés plutôt que présentés comme un vrai bilan nocturne. Un bandeau d'événement temporaire signale un changement de palier DoorKey observé en direct ; une note affichée au démarrage documente explicitement qu'une promotion de NIVEAU MiniGrid ne peut structurellement jamais se produire dans l'Arène (décidée uniquement par `executer_nuit`, jamais appelée ici — garantie de non-altération inchangée).**

| Fichier modifié | Changement |
|-----------------|------------|
| `src/naulthene/instruments/arene_visuelle.py` | Fenêtre élargie (1032×652) ; nouvelle bande mini-IRM (`_dessiner_panneau_bus`) ; panneau de télémétrie réécrit pour les 13 lignes de parité avec le bilan de nuit ; nouveau bandeau d'événement (`_dessiner_bandeau_evenement`) ; `dessiner_frame` accepte `activations`/`evenement` optionnels |
| `src/naulthene/instruments/lancer_arene.py` | Recalcul en lecture seule du tronc cérébral (`_tronc_cerebral` sous `torch.no_grad()`) avant chaque `traiter_tick`, pour alimenter le mini-IRM sur l'observation du tick courant ; `_construire_telemetrie` étendu avec les proxys continus (plasticité base, erreur JEPA/récompense moyenne, thermostat simplifié) ; détection de changement de palier DoorKey par diff entre deux ticks pour déclencher le bandeau |

**Validation** : script de vérification manuel (pas de suite de tests automatisée) — panneau testé en headless (`SDL_VIDEODRIVER=dummy`) sur toutes les combinaisons de clés manquantes/DoorKey actif ou non/bandeau présent ou non, sans crash ; run réel bout-en-bout sur `brains/naulthene_bb.brain` (niveau Doctorat) confirmant des valeurs de télémétrie cohérentes tick par tick ; test synthétique forçant un changement de palier DoorKey sur `brains/naulthene_cursus.brain` confirmant le déclenchement et l'extinction du bandeau ; aucune altération constatée sur les fichiers `.brain` sur disque après les runs de test.

---

## [26.0-experimental] - 2026-07-27

### Cristallisation Souple — protection ciblée des synapses matures contre l'érosion nocturne (falaise sigmoïde)

| Type | Details |
|------|---------|
| **Commit** | N/A — `src/naulthene/cerveau/noyau.py` est gitignored (terrain d'essai expérimental), aucun commit ne le modifie |
| **Catégorie** | feat (mécanique expérimentale) |
| **Impact** | Fonctionnel (plasticité structurelle) — `agi_local_test.py`/`noyau.py` uniquement |

**Implémente le chantier §A.5 du plan v26.0 « Le Parent remplace le Programme » ([docs/AMELIORATION_V1.md](AMELIORATION_V1.md)) : les synapses `NaultheneLinearSynaptique` sollicitées fortement et régulièrement sur plusieurs nuits deviennent quasi indestructibles à l'érosion nocturne, sans jamais geler leur apprentissage diurne. Une seconde trace `myeline_cumul` accumule la myélinisation consolidée nuit après nuit (même patron de relaxation exponentielle que partout dans le projet, `ALPHA_CRISTAL = 0.95`) ; au-delà de `SEUIL_CRISTAL = 0.80`, la synapse devient `cristallisee` — un cliquet à sens unique, jamais réversible. Correctif appliqué en cours d'implémentation : le plancher d'érosion initialement prévu comme une constante rigide (`MYELINE_MIN_CRISTAL = 0.50`, tout-ou-rien) a été remplacé par une falaise continue — une sigmoïde de `myeline_cumul` centrée sur le seuil (`K_RAIDEUR_CRISTAL = 10.0`) — plus fidèle au principe du projet de régulation dynamique sans règle en dur : une synapse cristallisée voit son érosion tendre vers zéro à mesure qu'elle s'éloigne du seuil, tandis qu'une synapse jamais cristallisée s'érode normalement et finit élaguée en temps fini (zéro synapse fantôme).**

| Fichier modifié | Changement |
|-----------------|------------|
| `src/naulthene/cerveau/noyau.py` | `NaultheneLinearSynaptique.__init__` : 2 nouveaux buffers (`myeline_cumul`, `cristallisee`). `cycle_sommeil()` : nouvelle Étape 3.5 (accumulation inter-nuits + cliquet de cristallisation) et érosion (Étape 3) plancher-protégée par une falaise sigmoïde plutôt qu'un plancher rigide. `agrandir()` : les 2 nouveaux buffers suivent le même triptyque resize/copie-par-segment que `myeline_M`/`trace_activation` (nouvelles dimensions nées à `0`/`False`). 3 nouvelles constantes module (`ALPHA_CRISTAL`, `SEUIL_CRISTAL`, `K_RAIDEUR_CRISTAL`). `forward()` et `fortification_dopaminergique()` inchangées — garantit par construction la règle dissymétrique (le gradient diurne sur `annexe_weight` reste identique, cristallisée ou non). |
| `docs/AMELIORATION_V1.md` | §A.5 mis à jour pour refléter la falaise sigmoïde implémentée (remplace le plancher rigide de la proposition initiale) ; glossaire §G : `MYELINE_MIN_CRISTAL` remplacé par `K_RAIDEUR_CRISTAL = 10.0` |
| `docs/explications_readme.md` | Nouvelle section §8.5 « Cristallisation Souple » (formules exactes, extrait de code, règle dissymétrique) ; table §12 et glossaire §13 mis à jour (v26.0, `ALPHA_CRISTAL`/`SEUIL_CRISTAL`/`K_RAIDEUR_CRISTAL`) |
| `readme.md` | Nouvelle entrée « Nouveautés v26.0 (expérimental, §A.5 seul) » en tête du Journal des Mises à Jour + entrée table des matières `3x` |

**Validation** : script de vérification manuel isolé (pas de suite de tests automatisée dans ce projet) — cristallisation asymétrique confirmée (la synapse sollicitée bascule `cristallisee=True` vers la nuit 40 sur 80 simulées, l'inactive reste `False`), falaise sigmoïde confirmée (une synapse cristallisée résiste nettement mieux à l'érosion qu'une synapse juste sous le seuil, 0.987 vs 0.950 de rétention sur un cycle), zéro synapse fantôme confirmé (une synapse jamais cristallisée est élaguée en 89 nuits, temps fini), règle dissymétrique confirmée (`backward()` produit un gradient non nul sur `annexe_weight` même aux positions cristallisées), `agrandir()` confirmé préservant l'historique sans hallucination de cristallisation sur les nouvelles dimensions.

---

## [25.0-docs] - 2026-07-26

### Réorganisation en package Python + renforcement de l'attribution (NOTICE)

| Type | Details |
|------|---------|
| **Commit** | N/A — en attente du commit de cette version |
| **Catégorie** | refactor + docs |
| **Impact** | Fonctionnel (imports, arborescence) + Documentation/Légal |

**Le projet passe d'un ensemble de scripts plats à la racine à un vrai package Python `src/naulthene/`, organisé en sous-modules thématiques suivant le vocabulaire du projet : `cerveau/` (noyau.py ex-`agi_local_test.py`, colab.py ex-`agi_google_colab.py`, persistance.py), `salles_de_classe/` (cursus_bebe.py, cursus_developpemental.py), `cuve/` (daemon_cerveau.py, client_corps.py, client_professeur.py), `audio/` (hemisphere_audio.py, lecons_vocales.py, professeur_gemma.py), `instruments/` (arene_visuelle.py, lancer_arene.py, irm_cerveau.py). Tous les imports inter-modules sont passés en chemins de package absolus (`from naulthene.cerveau.noyau import ...`). Les cerveaux cristallisés (`*.brain`) sont rangés dans `brains/`, la documentation complémentaire dans `docs/` — `readme.md` reste à la racine (aux côtés de `LICENSE`/`NOTICE`/`CLAUDE.md`) pour rester immédiatement visible. En parallèle, le fichier `NOTICE` est renforcé : au-delà de la simple demande d'attribution, il précise explicitement (en s'appuyant sur la Section 4(d) de la licence Apache 2.0) qu'Adrien Nault doit être crédité comme auteur original du concept et de l'architecture Naulthène AGI dans toute redistribution, usage public, publication ou œuvre dérivée — pas seulement dans le code source.**

| Fichier modifié | Changement |
|-----------------|------------|
| `src/naulthene/**/*.py` (tous) | Déplacement en package (`git mv`), réécriture de tous les imports locaux en chemins de package absolus, chemins `.brain` par défaut pointant vers `brains/` |
| `.gitignore` | Chemins mis à jour vers `brains/*.brain` et `src/naulthene/cerveau/noyau.py` |
| `readme.md` | Reste à la racine du dépôt ; formulation d'attribution durcie en tête de document |
| `docs/CHANGELOG.md`, `docs/explications_readme.md`, `docs/LANCEMENT.md`, `docs/AMELIORATION_V1.md` | Liens relatifs corrigés vers la nouvelle arborescence (`../readme.md`, `../CLAUDE.md`, `../LICENSE`, `../NOTICE`) |
| `CLAUDE.md` | Section Architecture réécrite pour décrire le package ; commandes de lancement mises à jour (`PYTHONPATH=src python -m naulthene....`) |
| `NOTICE` | Attribution renforcée : exigence explicite de citer Adrien Nault comme auteur du concept/architecture original, dans tout usage public (pas seulement redistribution de code), avec référence à la Section 4(d) de la licence |
| `LICENSE` | Texte légal Apache 2.0 inchangé (Sections 1-9) ; ajout d'un renvoi explicite vers `NOTICE` en fin de fichier |

**Validation** : les 12 modules du package s'importent sans erreur (`python -c "import naulthene...."` pour chaque sous-module) ; run réel d'1 jour de `cursus_bebe` exécuté de bout en bout, confirmant la résolution correcte de `brains/naulthene_bb.brain` en lecture et en écriture (reprise du jour 1440 → 1441 sans perte de progression) ; `git status` confirme la préservation de l'historique (renommages `R`/`RM`, pas de suppression/ajout).

---

## [25.0-experimental] - 2026-07-24

### Le Cerveau Bébé Développemental — 4 ans, masquage de récompense externe & Module Parent (expérimental, non porté sur le script de référence)

| Type | Details |
|------|---------|
| **Commit** | N/A — en attente du commit de cette version |
| **Catégorie** | feat (nouvelle mécanique cognitive majeure) |
| **Impact** | Fonctionnel (local uniquement) |

**Nouveau paradigme développemental bio-inspiré (Piaget / Dehaene, décision utilisateur) qui pousse plus loin le Cursus Développemental par Ères (v23.0) : au lieu du RL classique (qui force l'agent à "tricher" pour maximiser une récompense), le bébé traverse 4 ans (1440 jours × 3600 ticks) découpés en 5 phases d'âge, avec la récompense externe VERROUILLÉE à zéro pendant les 8 premiers mois (jour < 240) — l'agent "n'a aucune idée s'il fait bien ou mal", seuls le JEPA, l'homéostasie et la curiosité pilotent l'apprentissage — puis un Module "Parent" qui réintroduit un feedback social vocal déterministe ("Oui !"/"Non !"). Le cerveau vit dans un fichier dédié `naulthene_bb.brain`, distinct de `naulthene_cursus.brain` (Cursus par Ères) et `naulthene_v21.brain` (Cuve/daemon) — les trois écosystèmes ne partagent jamais le même cerveau. Le Cursus par Ères existant reste intact et utilisable tel quel.**

| Fichier modifié | Changement |
|-----------------|------------|
| `agi_local_test.py` | Ajout des constantes/helpers du paradigme (`TICKS_PAR_JOUR_BEBE=3600`, `TICKS_MATIN_BEBE=1800`, `JOURS_TOTAUX_BEBE=1440`, `BORNES_PHASES_BEBE=(90,180,360,720)`, `JOUR_FIN_MASQUAGE_EXTERNE=240`, `PLAFOND_REVE_PAR_PHASE=(0.70,0.60,0.50,0.40,0.35)`, `SEUIL_PARENT_OUI=0.45`, `SEUIL_PARENT_NON=0.15`, `TAUX_CORTISOL_PARENT=0.5`, helpers `phase_bebe()`/`plafond_reve_bebe()`). `traiter_tick()` gagne deux paramètres optionnels **par défaut inertes** : `masquer_recompense_externe=False` (gèle `recompense_env` à 0.0 juste après `env.step`, neutralisant à la fois sa contribution à `recompense_interne` ET à `poids_evenement` — donc plus de choc dopaminergique "victoire", plus de `victoire_aujourdhui`, plus de promotion de niveau MiniGrid tant que le masquage est actif) et `parent_actif=False` (déclenche le nouveau Module Parent). `_traiter_tick_vocal_isole()` gagne le même `parent_actif`. Nouveau helper `_appliquer_feedback_parent_vocal()` : "Oui !" (score de formants ≥ `SEUIL_PARENT_OUI`) renforce le choc dopaminergique déjà existant ; "Non !" (score < `SEUIL_PARENT_NON`) pousse activement la dopamine vers `DOPAMINE_MIN` via un nouveau canal "cortisol" (`TAUX_CORTISOL_PARENT`), toujours reclippé dans `[DOPAMINE_MIN, DOPAMINE_MAX]`. Un second canal "Oui !" se déclenche quand une ressource bio est atteinte pendant une quête de survie active (`poids_ressource_bio > 0`). Nouveau compteur de journée `feedback_parent_jour` (net Oui − Non), loggé sur W&B. `executer_nuit()` gagne `plafond_reve=None` : quand fourni, remplace `PLAGE_REVE_MAX` dans le calcul de `pourcentage_reve` — le pourcentage rejoué reste émergent (plasticité × richesse), seul son plafond suit le "% Dodo" de la phase d'âge (aucune taille de batch fixe réintroduite). Normalisations `erreur_moyenne`/`rec_moy`/`effort_moyen_jour` corrigées pour utiliser le nombre RÉEL de ticks de la journée (`len(etat.jepa_losses)`) plutôt que la constante globale `ticks_par_jour` (400) — nécessaire car `cursus_bebe.py` tourne sur 3600 ticks/jour, sans effet sur le Cursus par Ères/mode standalone (résultat identique dans ce cas). `NB_PALIERS_VOCAUX` passe de 11 à 14 (paliers "porte" + combinatoire ajoutés, voir ci-dessous) |
| `professeur_gemma.py` | `CURRICULUM_VOCAL` étendu de 11 à 14 paliers : palier 12 (mot "porte"), paliers 13-14 (combinatoire minimale "ouvre porte" / "prends clé") — couvre la roadmap "mots papa/maman/porte" puis "combinatoire Action+Objet" du concept. Chaque nouveau mot est géré automatiquement par `CacheReferencesVocales` (référence `say`) ; sa voyelle dominante ("porte"→"o", "ouvre"→"o", "prends"→"e") est déjà une clé connue de `hemisphere_audio.VOYELLES_CIBLES` via le fallback existant de `_mot_cible_du_palier` — aucune modification requise dans `hemisphere_audio.py` |
| `cursus_bebe.py` (nouveau) | Orchestrateur calqué sur `cursus_developpemental.py` : boucle sur `JOURS_TOTAUX_BEBE` (1440) jours × `TICKS_PAR_JOUR_BEBE` (3600) ticks, `_perception_du_tick_bebe()` mappe les 5 phases d'âge au curriculum vocal et au mode de perception (vocal isolé pour les phases 0-1, multimodal matin dès la phase 2, verbalisation de l'action aux phases 3-4 — même principe que l'Ère Intégration du Cursus par Ères), câble `masquer_recompense_externe`/`parent_actif` sur `JOUR_FIN_MASQUAGE_EXTERNE` et `plafond_reve_bebe(jour)` sur `executer_nuit`. Réutilise le même garde-fou "École de Rattrapage Vocal" (compteur de session local, pas `etat.jour` cumulatif) et le même mécanisme de promotion vocale 2+2 succès que le Cursus par Ères. Persistance dédiée : `PersistanceAnatomique(fichier="naulthene_bb.brain")`, sauvegarde après chaque nuit, reprise automatique, sauvegarde d'urgence sur `KeyboardInterrupt` |

**Validation** : non-régression structurelle garantie — les trois nouveaux paramètres (`masquer_recompense_externe`, `parent_actif`, `plafond_reve`) ont tous une valeur par défaut inerte, et tous les appelants existants (`__main__` standalone, `cursus_developpemental.py`, `lancer_arene.py`, `daemon_cerveau.py`) appellent `traiter_tick`/`executer_nuit` sans ces arguments — vérifié par grep sur tous les call sites. Testé bout-en-bout : (1) `cursus_bebe.py` exécuté sur cerveau neuf (3 jours, ticks réduits pour la vitesse du test) sans crash, phases/persistance/rêve/neurogenèse fonctionnels ; (2) masquage vérifié directement — un `recompense_env` forcé à 1.0 avec `masquer_recompense_externe=True` laisse `victoire_aujourdhui=False` et n'entre pas dans `recompense_interne`, alors que `masquer_recompense_externe=False` sur le même signal déclenche bien la victoire et la contribution ; (3) plafond de rêve vérifié — `plasticite_base` forcée à 1.0 (qui pousserait normalement `pourcentage_reve` vers 0.60) reste bornée à `plafond_reve=0.35` passé en paramètre ; (4) Module Parent testé en isolation — score ≥ 0.45 incrémente `feedback_parent_jour` sans toucher la dopamine (le choc positif est déjà géré par l'appelant), score < 0.15 la décrémente et pousse la dopamine vers `DOPAMINE_MIN` en respectant le clip, score intermédiaire neutre ; `parent_actif=False` laisse `feedback_parent_jour` totalement inchangé ; (5) non-régression confirmée sur `cursus_developpemental.py` (2 jours, inchangé, exécution normale).

---

## [24.0-fix5-experimental] - 2026-07-23

### L'Arène injecte enfin une cible vocale — fin du "(silence)" systématique (expérimental, non porté sur le script de référence)

| Type | Details |
|------|---------|
| **Commit** | N/A — vit dans `lancer_arene.py` |
| **Catégorie** | fix (bug bloquant, signalé par l'utilisateur avec une hypothèse de seuil à corriger) |
| **Impact** | Fonctionnel (local uniquement) |

**L'hypothèse initiale (un seuil de décodage type `if score_similarite < 0.55` masquant les scores 0.45-0.55 observés dans le cursus) ne correspondait pas au code réel : aucun seuil de ce type n'existe. Le vrai bug, plus simple : `lancer_arene.py` appelait `traiter_tick(etat)` SANS jamais passer `obs_auditive`/`formants_cibles` — `score_vocal` restait donc toujours `None` par construction, quel que soit le niveau réel de l'agent. L'Arène affichait "Palier vocal : Mot 'maman'" dans le panneau tout en ne présentant jamais ce mot à répéter au cerveau.**

| Fichier modifié | Changement |
|-----------------|------------|
| `lancer_arene.py` | Instancie `lecons_vocales.CacheReferencesVocales` (même mécanisme que `cursus_developpemental.py`) et injecte à CHAQUE tick le MFCC + les formants cibles du `etat.palier_vocal` courant dans `traiter_tick`. Le score est ensuite calculé via `hemisphere_audio.recompense_formants` sur les formants réellement produits, au lieu de rester `None` |

**Validation** : testé avec un `.brain` forcé au palier 11 ("maman") — confirmé que `score_vocal` n'est plus jamais `None` sur 10 ticks consécutifs (il se calcule à chaque fois, la valeur numérique dépendant ensuite du niveau réel de l'agent testé).

---

## [24.0-fix4-experimental] - 2026-07-23

### L'exclusion d'integrateur_bio devient conditionnelle à la forme réelle (expérimental, non porté sur le script de référence)

| Type | Details |
|------|---------|
| **Commit** | N/A — vit dans `persistance.py` |
| **Catégorie** | fix (bug bloquant, signalé par l'utilisateur) |
| **Impact** | Critique (local uniquement) — expliquait le silence de l'Arène |

**Le filtre `integrateur_bio` introduit en v22.1 pour gérer le changement DIM_VECTEUR_BIO 8→16 était INCONDITIONNEL : il testait seulement `startswith('integrateur_bio.')`, sans jamais comparer la forme réelle du checkpoint à la forme attendue. Conséquence : tout `.brain` sauvegardé depuis la v22.1 (donc avec `integrateur_bio` déjà à la bonne taille et correctement appris) se faisait quand même amputer de cette couche à CHAQUE rechargement — remplacée par des poids aléatoires. Comme `integrateur_bio` réinjecte justement la quête vocale vers `tete_vocale`, cette réinitialisation systématique produisait une bouche silencieuse dans l'Arène (amplitude prédite sous le seuil d'audibilité en mode `eval()`).**

| Fichier modifié | Changement |
|-----------------|------------|
| `persistance.py` | `charger_ou_naitre` compare désormais la shape réelle de `checkpoint['state_dict']['integrateur_bio.base_weight']` à la shape attendue par l'agent fraîchement recréé (`agent.integrateur_bio.base_weight.shape`). L'exclusion ne se déclenche que si les deux diffèrent (vieux `.brain` pré-v22.1) ; un checkpoint déjà à la bonne forme charge `integrateur_bio` intégralement, sans perte |

**Validation** : deux cas testés directement. (1) Un `.brain` simulé à l'ancienne forme (8 dims, `integrateur_bio` en `(16,24)`) déclenche toujours correctement l'exclusion, avec un message affichant la comparaison exacte des formes. (2) Un `.brain` à la forme actuelle (16 dims) avec des poids `integrateur_bio` marqués (valeur repère `0.777`) est rechargé avec ces poids **strictement préservés** — aucune exclusion, aucune réinitialisation. C'est ce second cas qui corrige le silence observé dans l'Arène sur `naulthene_cursus.brain`.

---

## [24.0-fix3-experimental] - 2026-07-23

### Correction du compteur du garde-fou vocal (expérimental, non porté sur le script de référence)

| Type | Details |
|------|---------|
| **Commit** | N/A — vit dans `cursus_developpemental.py` |
| **Catégorie** | fix (bug bloquant sur le garde-fou introduit en fix2) |
| **Impact** | Fonctionnel (local uniquement) |

**Le garde-fou de l'École de Rattrapage (v24.0-fix2) comparait `etat.jour` — cumulatif depuis la naissance du cerveau — au seuil de 100 jours. Sur un cerveau qui avait déjà vécu 970 jours AVANT le correctif de seuil (v24.0-fix1), la reprise après application du fix1 s'est vue couper la parole dès le premier jour de la nouvelle tentative (970 ≥ 100), sans laisser au nouveau seuil la moindre chance de prouver qu'il fonctionne réellement.**

| Fichier modifié | Changement |
|-----------------|------------|
| `cursus_developpemental.py` | Nouveau compteur local `jours_ecoules_session` (incrémenté à chaque itération de `lancer_cursus`, remis à zéro à chaque nouveau lancement du script) — le garde-fou compare désormais ce compteur au seuil, pas `etat.jour`. Une reprise sur un vieux cerveau obtient une vraie fenêtre de `JOURS_MAX_SANS_PREMIERE_LETTRE` jours depuis CETTE tentative, indépendamment de son passé |

**Validation** : testé avec un cerveau simulé à `etat.jour=970`/`palier_vocal=1` (reproduisant exactement le cas réel signalé) — un run de 5 jours (`jours_totaux=5`, sous le seuil de 100) se termine désormais normalement au lieu de déclencher le garde-fou dès le premier jour.

---

## [24.0-fix2-experimental] - 2026-07-23

### Garde-fou de l'École de Rattrapage Vocal (expérimental, non porté sur le script de référence)

| Type | Details |
|------|---------|
| **Commit** | N/A — vit dans `cursus_developpemental.py` |
| **Catégorie** | fix (garde-fou, détection précoce d'un blocage) |
| **Impact** | Fonctionnel (local uniquement) |

**Le run de 1000 jours qui a révélé le blocage du seuil de promotion (v24.0-fix1) a tourné intégralement à vide côté vocal sans qu'aucun signal ne le signale — il a fallu inspecter le `.brain` à la main après coup. Ajout d'un garde-fou : si après `JOURS_MAX_SANS_PREMIERE_LETTRE` (100) jours subjectifs cumulés le palier vocal n'a jamais quitté le palier 1 (aucune voyelle validée), le cursus s'arrête proprement — sauvegarde incluse — au lieu de tourner jusqu'au bout des jours demandés.**

| Fichier modifié | Changement |
|-----------------|------------|
| `cursus_developpemental.py` | Nouvelle constante `JOURS_MAX_SANS_PREMIERE_LETTRE = 100`. Dans `lancer_cursus`, après chaque sauvegarde nocturne, vérifie `etat.palier_vocal == 1 and etat.jour >= JOURS_MAX_SANS_PREMIERE_LETTRE` — si vrai, arrête la boucle (`break`) avec un message dédié. Ne se déclenche qu'une fois avant la toute première promotion (`GestionnaireCursusAbnegation` n'a aucun mécanisme de rétrogradation, donc `palier_vocal` ne peut jamais redescendre à 1 une fois monté) |

**Validation** : testé avec un seuil de promotion vocale rendu volontairement inatteignable (99.0) — arrêt confirmé exactement au jour du seuil (testé à 5 jours), `.brain` bien sauvegardé avant l'arrêt. Testé aussi le cas négatif (moins de jours que le seuil, promotion possible) — aucun faux déclenchement, le cursus se termine normalement.

---

## [24.0-fix1-experimental] - 2026-07-23

### École de Rattrapage Vocal — débloquer l'apprentissage vocal (expérimental, non porté sur le script de référence)

| Type | Details |
|------|---------|
| **Commit** | N/A — vit dans `agi_local_test.py` (seuil progressif + atténuation d'érosion) et `cursus_developpemental.py` (appel du nouveau seuil) |
| **Catégorie** | fix (critique — bloquait tout apprentissage vocal du Cursus) |
| **Impact** | Critique (local uniquement) |

**Diagnostic sur un vrai run de 1000 jours (`naulthene_cursus.brain`) : avec le seuil de promotion vocale fixe introduit en v23.0 (0.5), `gestionnaire_cursus_vocal_succes_courant` est resté à 0 du premier au dernier jour — aucune promotion vocale en 1000 jours, et `porte_auditive.base_weight` a fini à norme EXACTEMENT ZÉRO (l'oreille n'a strictement rien appris). Cause racine identifiée : sans un premier succès pour amorcer la myélinisation, le peu de gradient accumulé par jour se fait entièrement raser par l'érosion nocturne (`cycle_sommeil`) avant d'avoir pu s'accumuler — un cercle vicieux qui ne se débloque jamais tout seul.**

| Fichier modifié | Changement |
|-----------------|------------|
| `agi_local_test.py` | Remplace la constante `SEUIL_JOUR_VOCAL_REUSSI` (0.5 fixe) par `seuil_jour_vocal_reussi(palier_vocal)`, une interpolation progressive de `SEUIL_VOCAL_PALIER_DEBUTANT=0.15` (palier 1) à `SEUIL_VOCAL_PALIER_AVANCE=0.45` (palier 11) — jamais 0.5, pour ne jamais retomber dans le blocage diagnostiqué. Second volet : `AGI_Naulthene.cycle_sommeil_global` gagne un paramètre `attenuation_erosion_audio` appliqué uniquement à `porte_auditive`/`tete_vocale`/`generateur_attente_audio`, réduit à 10% (`ATTENUATION_EROSION_AUDIO_DEBUT`) tant que `palier_vocal <= PALIER_VOCAL_FIN_PROTECTION` (3) — laisse au tout premier apprentissage le temps de survivre à plusieurs nuits avant d'être soumis à l'érosion standard |
| `cursus_developpemental.py` | `_promouvoir_palier_vocal_si_merite` utilise le nouveau seuil progressif au lieu de la constante fixe |

**Validation** : non-régression MiniGrid confirmée byte-identique (le fix n'affecte le comportement que via `palier_vocal`/`attenuation_erosion_audio`, neutres par défaut). Test dédié bout-en-bout sur cerveau neuf (seed fixe, curriculum réel via `professeur_gemma.choisir_lecon` + `_promouvoir_palier_vocal_si_merite`) : **3 promotions vocales obtenues en 60 jours** (palier 1→2→3, voyelles a→a→e), score de formants monté jusqu'à 0.53 — alors que le seuil fixe précédent n'avait produit AUCUNE promotion en 1000 jours sur un vrai run.

---

## [24.0-experimental] - 2026-07-23

### L'Arène & Démo Live — observer un cerveau entraîné en action (expérimental, non porté sur le script de référence)

| Type | Details |
|------|---------|
| **Commit** | N/A — vit dans `agi_local_test.py` (`creer_env` render_mode), `persistance.py`, `cursus_developpemental.py` (modifiés) + `arene_visuelle.py`, `lancer_arene.py` (nouveaux fichiers) |
| **Catégorie** | feat (Phase 2 du plan à 3 phases : Cursus → Arène → boucle méta) |
| **Impact** | Fonctionnel (local uniquement) |

**Ajoute une fenêtre graphique temps réel (image MiniGrid + panneau de télémétrie composés dans une seule fenêtre pygame) et le son joué en direct, pour observer un agent entraîné en action — sans jamais l'altérer. Préalable indispensable résolu au passage : le Cursus Développemental (v23.0) ne sauvegardait jamais son état ; il persiste désormais chaque nuit dans un fichier dédié, avec reprise automatique d'un run interrompu.**

| Fichier modifié | Changement |
|-----------------|------------|
| `persistance.py` | Ajout de `palier_vocal` et de l'état de `gestionnaire_cursus_vocal` (instance séparée de celle de DoorKey) au checkpoint sauvegardé/restauré — absents jusqu'ici, une reprise perdait la progression vocale. Rétrocompatible (`.get(..., défaut)`) pour les vieux `.brain` |
| `cursus_developpemental.py` | `lancer_cursus` charge désormais un cerveau existant via `PersistanceAnatomique` (fichier dédié `naulthene_cursus.brain`, distinct de `naulthene_v21.brain` de la Cuve) au lieu de toujours faire naître un cerveau neuf, et sauvegarde après CHAQUE nuit. `try/except KeyboardInterrupt` avec sauvegarde d'urgence — un cursus interrompu ne perd au plus que la journée en cours |
| `agi_local_test.py` | `creer_env` gagne un paramètre optionnel `render_mode=None` (rétrocompatible, tous les appels existants inchangés), passé à `gym.make()` — permet `render_mode="rgb_array"` pour récupérer une image numpy de la grille |
| `arene_visuelle.py` (nouveau) | `FenetreArene` : rendu pygame pur (aucune dépendance au réseau de neurones) — image MiniGrid à gauche, panneau de télémétrie à droite (jauges dopamine/satiété/hydratation/stimulation, curriculum MiniGrid + DoorKey, ère + curriculum vocal, score de formants). Gère aussi `pygame.QUIT` pour une fermeture par clic sur la croix |
| `lancer_arene.py` (nouveau) | Orchestrateur : charge un `.brain`, recrée l'env avec rendu activé, boucle `traiter_tick` (mode `"minigrid"` normal) en lisant `EtatCognitif` directement pour la télémétrie (`traiter_tick` ne retourne que peu d'infos, mais `EtatCognitif` est accessible sans encapsulation). `agent.eval()` après le chargement, `executer_nuit`/`apprendre_journee` jamais appelés — garantie explicite de non-altération du cerveau observé |

**Validation** : non-régression confirmée (`creer_env` avec `render_mode=None` par défaut, logs byte-identiques). Cycle complet de persistance du cursus testé (naissance → sauvegarde chaque nuit → reprise exacte au bon jour, `tick_absolu` et `palier_vocal` restaurés) ; robustesse confirmée même sur arrêt brutal (`kill -9`, écriture atomique intacte). Arène testée en conditions réelles sur un `.brain` produit par le cursus : 20 ticks avec rendu d'image (256×256×3) et télémétrie complète sans crash, `agent.training=False` confirmé. **Non-altération du cerveau prouvée directement** : comparaison `torch.equal` de tous les tenseurs du `state_dict` avant/après 50 ticks d'observation — strictement identiques.

---

## [23.0-experimental] - 2026-07-23

### Le Cursus Développemental par Ères — 1000 jours d'apprentissage autonome (expérimental, non porté sur le script de référence)

| Type | Details |
|------|---------|
| **Commit** | N/A — vit dans `agi_local_test.py` (mode `vocal_isole` + constantes d'ères) + `lecons_vocales.py`, `cursus_developpemental.py` (nouveaux fichiers) |
| **Catégorie** | feat (nouvelle mécanique cognitive majeure) |
| **Impact** | Fonctionnel (local uniquement) |

**Fait passer l'apprentissage vocal du statut de leçon manuelle ponctuelle (`client_professeur.py --palier N`) à celui de programme de développement autonome sur 1000 jours subjectifs, organisé en 3 ères de difficulté croissante — Alternance (matin MiniGrid / après-midi vocal isolé), Synesthésie (multimodal simultané le matin, syllabes/mots l'après-midi), Intégration (verbalisation de l'action toute la journée). Le curriculum MiniGrid et le curriculum vocal progressent en parallèle, chacun par son propre mécanisme de promotion — les ères orchestrent QUAND chaque apprentissage est actif, sans remplacer ni l'un ni l'autre.**

| Fichier modifié | Changement |
|-----------------|------------|
| `agi_local_test.py` | Nouveau paramètre `mode_perception="minigrid"` (défaut, non-régression validée byte-identique) ou `"vocal_isole"` sur `traiter_tick` — en `vocal_isole`, AUCUN `env.step` n'est appelé (l'environnement MiniGrid est en pause, validé par un test espionnant explicitement les appels) et la vision est un tenseur de zéros ; seuls la pensée multimodale, le JEPA, la perte vocale supervisée et la dopamine sur le score de formants s'exécutent, via une nouvelle fonction `_traiter_tick_vocal_isole` qui ne touche jamais aux buffers acteur-critique (`log_probs_journee`/`entropies_journee`/`valeurs_journee`/`recompenses_journee`/`dones_journee`) pour ne jamais les désynchroniser. Ajout des constantes `DUREE_ERE`, `TICKS_MATIN`, `BORNES_ERES`, `SEUIL_JOUR_VOCAL_REUSSI` et du helper `ere_courante(jour)`. `EtatCognitif` gagne `palier_vocal` et `gestionnaire_cursus_vocal` (instance séparée de `GestionnaireCursusAbnegation`, indépendante de celle des 7 paliers DoorKey) |
| `lecons_vocales.py` (nouveau) | `CacheReferencesVocales` : génère les références audio (`say` → MFCC) des voyelles UNE SEULE FOIS au démarrage du cursus et les met en cache mémoire, dédupliquées par mot cible — évite de ré-invoquer `say`/`afconvert` à chaque tick sur un run de centaines de milliers de ticks vocaux |
| `cursus_developpemental.py` (nouveau) | Script standalone autonome (sans client réseau, décision utilisateur) qui pilote la boucle des 1000 jours, réutilisant à l'identique `demarrer_journee`/`traiter_tick`/`executer_nuit` — seule la logique de *quoi* passer à `traiter_tick` change selon l'ère et le moment de la journée (`_perception_du_tick`). La promotion du palier vocal (`_promouvoir_palier_vocal_si_merite`) réutilise le mécanisme 2+2 succès de `GestionnaireCursusAbnegation` sur le score de formants moyen du jour |

**Validation** : non-régression MiniGrid byte-identique (`mode_perception="minigrid"` par défaut, seed=42). Mode `vocal_isole` validé par espionnage explicite de `env.step` (0 appel sur 120 ticks de test) et par une progression réelle du score de formants (0.17→0.19 sur 3 jours de test dédié). Journée mixte matin/après-midi validée sans crash malgré des buffers de longueurs différentes (`log_probs_journee` 20 entrées vs `jepa_losses` 40). Promotion vocale validée par simulation (4 jours réussis → palier a→e). Cache de références validé (déduplication : 10 appels `say` pour 11 paliers). Run complet de 2 jours du cursus exécuté de bout en bout sans erreur (préchauffage, matin, après-midi, nuit, neurogenèse).

---

## [22.1-experimental] - 2026-07-23

### Correction de l'Hémisphère Audio — un vrai signal d'apprentissage pour la bouche (expérimental, non porté sur le script de référence)

| Type | Details |
|------|---------|
| **Commit** | N/A — vit dans `agi_local_test.py`, `persistance.py`, `daemon_cerveau.py`, `client_professeur.py` |
| **Catégorie** | fix (correctif de conception majeur) |
| **Impact** | Critique (local uniquement) |

**Corrige trois défauts de conception détectés à la revue de la v22.0, dont un critique confirmé par l'exploration du code réel : la bouche (`tete_vocale`) ne recevait aucun gradient d'apprentissage dirigé (sortie détachée avant tout calcul) — elle produisait des formants sans jamais apprendre à viser la cible. Les trois corrections ont été validées expérimentalement : le score de formants progresse désormais de 0.0045 à 0.1111 sur 5 jours de leçon (×24), la preuve directe que la bouche apprend enfin.**

| Fichier modifié | Changement |
|-----------------|------------|
| `agi_local_test.py` | **Défaut 1 (CRITIQUE, "membre fantôme")** : `tete_vocale` recevait un score de récompense mais aucun gradient dirigé (`.detach()` avant tout calcul). Ajout d'une perte MSE supervisée (`etat.pertes_vocales`, nouveau 6e buffer de journée) calculée sur le tenseur `parametres_vocaux` non détaché, restreinte aux dimensions F1/F2 réellement contraintes par la leçon, sommée à `perte_totale` dans `apprendre_journee` (`COEFF_PERTE_VOCALE`). **Défaut 2 ("court-circuit de la double entrée")** : `porte_auditive` ne reçoit plus l'embedding sémantique du mot (qui aurait fait ignorer le son réel par le réseau) — `DIM_AUDIO_ENTREE` passe de 162 à 130 (MFCC seul). Le concept-cible devient une "quête vocale" de 8 dims dans `vecteur_bio` (`DIM_VECTEUR_BIO` 8→16), au même titre que les quêtes SURVIVAL_FOOD/WATER. **Défaut 3 ("empoisonnement du JEPA")** : nouvelle tête prédictive séparée `generateur_attente_audio` (4 points de synchro respectés), pondérée par un coefficient `coeff_jepa_audio` monté progressivement de 0 à `COEFF_JEPA_AUDIO_MAX` sur `RAMPE_JEPA_AUDIO` ticks audio reçus — protège le JEPA visuel (physique MiniGrid) d'une perturbation par un signal audio bruyant dès le premier tick |
| `persistance.py` | Bug détecté et corrigé pendant les tests : le passage `DIM_VECTEUR_BIO` 8→16 change la *forme* de `integrateur_bio` (pas seulement des clés manquantes) — `load_state_dict(strict=False)` seul ne suffit pas, une `RuntimeError` de mismatch de shape a été confirmée sur le vrai `.brain`. `integrateur_bio` est désormais explicitement exclu du chargement et renaît à neuf (décision assumée : cette couche a une `base_weight` quasi vide, <3% de poids non-nuls, après 481 jours — l'acquis perdu est négligeable) |
| `client_professeur.py` | Cesse d'envoyer l'embedding sémantique dans `perception['audio']` (n'envoie plus que le MFCC), cohérent avec le défaut 2 |
| `daemon_cerveau.py` | Commentaires mis à jour pour refléter le nouveau format du canal audio |

**Validation** : score de formants prouvé en progression réelle (0.0045→0.1111 sur 5 jours×24 ticks, seed fixe) — la preuve clé que le défaut 1 est corrigé. Les 4 points de synchro de `generateur_attente_audio` validés par exécution (neurogenèse préserve les poids, optimiseur resynchronisé). Rampe `coeff_jepa_audio` confirmée quasi nulle au démarrage (0.00015 au premier tick). Non-régression MiniGrid sans audio confirmée cohérente (les logs changent légèrement par rapport à la v22.0 à cause du changement dimensionnel `DIM_VECTEUR_BIO`, effet attendu et documenté, pas un bug). Résurrection du vrai `.brain` (481 jours, testée sur copie) validée de bout en bout : acquis intacts, `integrateur_bio` renaît proprement, 10 ticks MiniGrid post-greffe exécutés sans erreur.

---

## [22.0-experimental] - 2026-07-23

### L'Hémisphère Auditif & Vocal — Naulthène apprend à parler (expérimental, non porté sur le script de référence)

| Type | Details |
|------|---------|
| **Commit** | N/A — vit dans `agi_local_test.py` (greffe des 2 nouvelles couches) + `persistance.py`, `daemon_cerveau.py` (modifiés) + `hemisphere_audio.py`, `professeur_gemma.py`, `client_professeur.py` (nouveaux fichiers) |
| **Catégorie** | feat (expérimental) |
| **Impact** | Architectural (local uniquement) |

**Greffe un véritable hémisphère audio dans le cerveau `AGI_Naulthene` — une oreille (`porte_auditive`, miroir de `porte_visuelle`) et une bouche (`tete_vocale`, miroir de `tete_motrice`) — plutôt qu'un module de traitement audio bricolé à côté. Décision structurante : cerveau 100% multimodal unifié, vision et audio fusionnés dans le même bus latent (pas de "mode" audio isolé) ; l'agent voit et entend, bouge et vocalise, au même tick. Le cortex auditif est prédictif dès le départ (JEPA étendu au son, pas seulement à l'image). La récompense par tick est une distance de formants déterministe (Gemma via Ollama met ~8-30s par réponse, mesuré, incompatible avec le RL par tick) ; Gemma intervient en professeur périodique (curriculum vocal + jugement qualitatif de fin de leçon). Le babil de l'agent est synthétisé et joué en temps réel dans les haut-parleurs, dès qu'il est produit.**

| Fichier modifié | Changement |
|-----------------|------------|
| `agi_local_test.py` | Ajout de `porte_auditive` (double entrée MFCC⊕embedding sémantique, `DIM_AUDIO_ENTREE=162`) et `tete_vocale` (sortie `DIM_VOCALE=8`, paramètres de formants) aux 4 points de synchro obligatoires (`__init__`, `fortifier_synapses`, `cycle_sommeil_global`, `declencher_neurogenese`) ; `_tronc_cerebral` fusionne vision et audio par somme dans le même bus (silence = comportement identique à avant v22.0, non-régression validée sur run déterministe) ; `penser()` retourne désormais 6 valeurs (ajout de `parametres_vocaux`) ; `perte_jepa` étendue pour prédire aussi le son (cortex auditif prédictif) ; `traiter_tick` accepte `obs_auditive`/`formants_cibles` optionnels et remonte `parametres_vocaux` dans `infos_internes` à chaque tick |
| `hemisphere_audio.py` (nouveau) | Pur traitement du signal, sans dépendance au réseau : `SynthetiseurFormants` (synthèse source-filtre, cascade de 3 résonateurs biquad, validée à l'oreille sur les 5 voyelles a/e/i/o/u), `extraire_mfcc`, `distance_formants`/`recompense_formants` (récompense continue, pas binaire), `capture_micro`/`transcrire_whisper` |
| `professeur_gemma.py` (nouveau) | Client Ollama isolé (API HTTP, testable sans réseau de neurones) : `choisir_lecon` (curriculum vocal à 11 paliers, déterministe), `embedding_semantique` (réduction 384→32 dims), `juger_qualitatif` (jugement périodique, repli propre sur le score de formants si Ollama indisponible) |
| `persistance.py` | `charger_ou_naitre` passe en `load_state_dict(strict=False)` pour la rétrocompatibilité des vieux `.brain` (sans couches audio) — greffe les hémisphères en initialisation aléatoire tout en préservant les acquis existants ; bug découvert et corrigé pendant les tests : l'ancien optimiseur (moins de groupes de paramètres) plantait sur `load_state_dict` après une greffe — un optimiseur frais est désormais recréé dans ce cas précis |
| `daemon_cerveau.py` | `_vivre_connexion` décode `perception['audio']`/`perception['formants_cibles']` du paquet client et les transmet à `traiter_tick` — ouvre le verrou qui empêchait jusqu'ici tout canal de perception réel d'atteindre le cerveau (le paquet JSON était reçu mais entièrement ignoré, voir limite assumée v21.0) |
| `client_professeur.py` (nouveau) | Boucle de leçon de parole : Gemma annonce la cible du palier → référence audio via `say` (ou micro) → encodée et envoyée à la Cuve à chaque tick → `parametres_vocaux` reçus synthétisés et **joués immédiatement** (temps réel) → récompense de formants affichée → jugement Gemma périodique en fin de leçon |

**Validation** : tests exécutés (pas de suite automatisée dans ce projet) — non-régression MiniGrid byte-identique (seed fixe, `obs_auditive=None`) ; les 4 points de synchro vérifiés par exécution réelle (neurogenèse préserve les poids audio existants, LTP touche bien les 2 nouvelles couches, `cycle_sommeil_global` s'exécute sans crash) ; JEPA audio validé par `backward()` réel (gradient confirmé sur `porte_auditive`) ; greffe rétrocompatible testée sur un scénario reproduisant fidèlement un vieux `.brain` (state_dict + optimizer sans couches audio) ; flux bout-en-bout validé (daemon de test + `client_professeur.py`, son synthétisé et joué en temps réel, jugement Gemma reçu).

---

## [21.0-experimental] - 2026-07-23

### Le Cerveau Persistant en Cuve — Architecture Client-Serveur (expérimental, non porté sur le script de référence)

| Type | Details |
|------|---------|
| **Commit** | N/A — vit dans `agi_local_test.py` (refactor) + `persistance.py`, `daemon_cerveau.py`, `client_corps.py` (nouveaux fichiers) |
| **Catégorie** | feat (expérimental) |
| **Impact** | Architectural (local uniquement) |

**Sépare définitivement la Conscience (le réseau + son état biologique, hébergé par un daemon persistant) du Corps (l'environnement MiniGrid, jetable), via une architecture Client-Serveur en sockets TCP/IP. L'agent traverse désormais les redémarrages de process : dopamine, satiété, mémoire épisodique, dimension du bus et progression de cursus survivent à l'arrêt/relance du daemon.**

| Fichier modifié | Changement |
|-----------------|------------|
| `agi_local_test.py` | Refactor pur (aucun changement de comportement, validé par comparaison de logs avant/après sur run déterministe) : extraction de la boucle principale (~500 lignes, jusque-là au niveau module) en un conteneur d'état `EtatCognitif` et quatre fonctions réutilisables — `initialiser_etat_cognitif()`, `demarrer_journee(etat)`, `traiter_tick(etat)`, `executer_nuit(etat)`. Le mode standalone (`if __name__ == "__main__":`) et la Cuve du daemon consomment désormais les mêmes fonctions — zéro duplication de la logique dopamine/détecteurs/curriculum/rêve adaptatif |
| `persistance.py` (nouveau) | `PersistanceAnatomique` : cristallise/ressuscite l'état complet d'un `EtatCognitif` dans un fichier `.brain` (`torch.save`/`torch.load`, écriture atomique via fichier temporaire + `os.replace`) — dimension du bus (pour reconstruire l'agent à la bonne taille AVANT `load_state_dict`), poids + traces de myéline/éligibilité, état de l'optimiseur Adam, chimie viscérale (dopamine, jauges biologiques, quête active), mémoire épisodique spatiale, curriculum (niveau, palier, victoires), thermostat de neurogenèse, compteurs de temps |
| `daemon_cerveau.py` (nouveau) | `CuveDeMaintien` : serveur socket TCP qui héberge le cerveau en continu. Cryostase (`socket.accept()` bloquant, CPU ~0%) tant qu'aucun corps n'est connecté. Modèle de temps hybride (décision utilisateur) : une nuit complète (apprentissage + rêve adaptatif + ressort dopaminergique + thermostat de neurogenèse + `cycle_sommeil_global`) se déclenche soit **in-session** dès qu'une journée subjective (`ticks_par_jour`) est accumulée, soit **à la déconnexion** si assez de ticks se sont écoulés depuis la dernière nuit ; sinon une simple **micro-sieste** (cristallisation sans érosion ni rêve) préserve le cerveau — protection explicite contre l'« Alzheimer numérique » d'une nuit relancée à vide sur des sessions courtes et répétées |
| `client_corps.py` (nouveau) | Pilote de session jetable : ouvre/maintient/ferme une connexion vers la Cuve selon le protocole JSON prévu par le design. Limite assumée de cette itération (documentée dans le fichier et dans `daemon_cerveau.py`) : l'environnement MiniGrid réel tourne côté serveur (les détecteurs biologiques/spatiaux lisent les internes MiniGrid, intransmissibles par un simple flux pixels+action) — le découplage total est une évolution future, pas un correctif oublié |
| `.gitignore` | Ajout de `*.brain` (cerveaux cristallisés, données binaires lourdes) ; les 3 nouveaux fichiers `.py` restent trackés |

**Validation** : run de non-régression déterministe (seed fixe) comparant les logs console avant/après le refactor de l'Étape 1 — coïncidence exacte. Test end-to-end de persistance à travers un redémarrage complet du process daemon (résurrection avec `tick_absolu`, dopamine, niveau et dimension du bus fidèles à l'état sauvegardé, y compris après neurogenèse 16→32 dims). Test dédié par assertions du régime micro-sieste vs nuit complète (seuil de ticks).

---

## [20.0-experimental] - 2026-07-23

### Mémoire Épisodique Spatiale & LTP Hebbien (expérimental, non porté sur le script de référence)

| Type | Details |
|------|---------|
| **Commit** | N/A — vit uniquement dans `agi_local_test.py`, non tracké par git |
| **Catégorie** | feat (expérimental) |
| **Impact** | Fonctionnel (local uniquement) |

**Ajoute une mémoire épisodique spatiale (où/quand/quoi) persistante dans la journée, consommée par le vecteur bio existant, et une Potentiation à Long Terme (LTP) hebbienne pilotée par les pics de dopamine par tick.**

| Fichier modifié | Changement |
|-----------------|------------|
| `agi_local_test.py` | Ajout de `MemoireEpisodiqueSpatiale` : enregistre position/type/tick des ressources trouvées, persiste à travers les épisodes d'une même journée, vidée uniquement au changement de niveau (`reinitialiser_niveau`) |
| `agi_local_test.py` | `BiologicalHomeostasisEngine.obtenir_vecteur_bio()` accepte un `rappel_spatial` (distance normalisée + fraîcheur) ; `DIM_VECTEUR_BIO` passe de 6 à 8 dims |
| `agi_local_test.py` | Boucle principale : récupération de contexte avant construction du vecteur bio (si une quête de survie est active), enregistrement d'événement à la consommation d'une ressource, compteur `tick_absolu` global |
| `agi_local_test.py` | `NaultheneLinearSynaptique` : ajout de `trace_activation` (trace d'éligibilité, accumulation exponentielle à chaque tick) et de `fortification_dopaminergique()` (LTP : grave les synapses actives dans `base_weight` proportionnellement au pic de dopamine) ; `agrandir()` étend `trace_activation` comme `myeline_M` ; `cycle_sommeil()` la remet à zéro |
| `agi_local_test.py` | `AGI_Naulthene.fortifier_synapses()` : nouvelle méthode appelant `fortification_dopaminergique()` sur toutes les couches plastiques, appelée depuis la boucle principale sur `poids_evenement` (par tick, pas une seule fois par jour sur la moyenne des récompenses comme le pseudo-code initial — évite de diluer un événement isolé) |
| `agi_local_test.py` | Nouvelle métrique W&B : `Memoire_Episodique_Taille` |

---

## [19.0-experimental] - 2026-07-22

### Métabolisme 20/80 & Forage 80/20 (expérimental, non porté sur le script de référence)

| Type | Details |
|------|---------|
| **Commit** | N/A — vit uniquement dans `agi_local_test.py`, non tracké par git |
| **Catégorie** | feat (expérimental) |
| **Impact** | Fonctionnel (local uniquement) |

**Remplace le coût énergétique fixe de la v18.0 par un calcul dynamique 20% Cerveau / 80% Corps, et introduit un cycle de forage (respawn) 80% Nid / 20% Dispersion pour la Nourriture.**

| Fichier modifié | Changement |
|-----------------|------------|
| `agi_local_test.py` | `BiologicalHomeostasisEngine.calculer_effort_metabolique()` : nouvelle méthode fusionnant coût corporel (80%, dépend du type d'action MiniGrid réelle — tourner/avancer/manipuler) et coût cognitif (20%, dérivé de `force_planification` et de la somme des `HORIZONS_PLANIFICATION`) ; remplace la constante fixe `COUT_ACTION_METABOLIQUE` (supprimée) |
| `agi_local_test.py` | `DetecteurRessourcesBiologiques` : ajout d'un `nid_position` (dérivé de la carte courante à l'initialisation de l'épisode, jamais une coordonnée fixe codée en dur) et de `_faire_repousser_food()` — la Nourriture consommée réapparaît immédiatement (80% près du nid ±1 case, 20% dispersée aléatoirement) ; l'Eau ne respawn pas |
| `agi_local_test.py` | Boucle principale : câblage de `calculer_effort_metabolique()` avant `step_metabolisme()`, nouveau compteur `effort_metabolique_jour` |
| `agi_local_test.py` | Nouvelle métrique W&B : `Bio_Effort_Metabolique_Moyen` |

---

## [18.0-experimental] - 2026-07-22

### Architecture Homéostatique Biologique (expérimental, non porté sur le script de référence)

| Type | Details |
|------|---------|
| **Commit** | N/A — vit uniquement dans `agi_local_test.py`, non tracké par git |
| **Catégorie** | feat (expérimental) |
| **Impact** | Fonctionnel (local uniquement) |

**Trois jauges vitales (satiété, hydratation, stimulation) régies par la Théorie de la Réduction du Drive (Hull), avec génération procédurale de ressources et quêtes de survie autonomes. Existe uniquement dans `agi_local_test.py` en attendant validation sur un run local suffisamment long avant portage sur `agi_google_colab.py`.**

| Fichier modifié | Changement |
|-----------------|------------|
| `agi_local_test.py` | Ajout de `BiologicalHomeostasisEngine` : jauges satiété/hydratation/stimulation dégradées à chaque tick, déficit homéostatique $D(t)$, récompense `r_bio` = réduction du déficit, injectée dans `TENEUR_DOPAMINE` existant (pas de second réservoir de dopamine parallèle, contrairement au pseudo-code initial) |
| `agi_local_test.py` | Ajout de `DetecteurRessourcesBiologiques` : génération procédurale de sources Nourriture/Eau via `Ball` colorées (rouge/bleu) placées sur des cases vides aléatoires par épisode, consommées et retirées de la grille au contact |
| `agi_local_test.py` | Génération autonome de quêtes de survie (`SURVIVAL_FOOD` > `SURVIVAL_WATER` > `EXPLORATION_STIM`) dès qu'une jauge passe sous 0.35 |
| `agi_local_test.py` | Ajout de la couche `integrateur_bio` (`NaultheneLinearSynaptique`, `dim_bus + 6 → dim_bus`) dans `AGI_Naulthene` : fusionne la pensée avec le vecteur bio (jauges + quête) avant la tête motrice et le rollout mental — intégré à l'architecture existante plutôt que de dupliquer un agent/encodeur parallèle (`V18BiologicalAgent` du pseudo-code initial) |
| `agi_local_test.py` | `declencher_neurogenese`/`cycle_sommeil_global` mis à jour pour couvrir `integrateur_bio` ; le vecteur bio (6 dims) ne grandit jamais avec la neurogenèse |
| `agi_local_test.py` | Nouvelles métriques W&B : `Bio_Satiete`, `Bio_Hydratation`, `Bio_Stimulation`, `Bio_Deficit`, `Bio_R_Bio_Jour`, `Bio_Food_Consommes_Jour`, `Bio_Water_Consommes_Jour`, `Bio_Quete_Active` |

---

## [17.0] - 2026-07-22

### Volonté Émergente & Sous-Objectifs Intrinsèques

| Type | Details |
|------|---------|
| **Commit** | `a0aa9e0` |
| **Catégorie** | feat |
| **Impact** | Fonctionnel |

**Décrochage précoce du Mode Libre (Palier 5 au lieu de 7), génération de sous-quêtes intrinsèques par curiosité JEPA, et Sursaut de Volonté qui étire la patience à 95% du seuil plutôt que de laisser l'agent abandonner.**

| Fichier modifié | Changement |
|-----------------|------------|
| `agi_google_colab.py` | `SEUIL_PALIER_MODE_LIBRE = 5` : le guidage artificiel (`RECOMPENSE_APPROCHE_BUT`) se désactive dès le Palier 5 (Viser la Porte) au lieu du Palier 7 |
| `agi_google_colab.py` | Ajout de `DetecteurCuriositeJEPA` : génère une micro-récompense de sous-quête quand l'erreur JEPA du tick dépasse 1.5x la moyenne récente (surprise du World Model), actif uniquement en Mode Libre — distinct de `dopamine_curiosite` existant (scaling continu, pas un signal de sous-quête) |
| `agi_google_colab.py` | Ajout de `ModuleSursautVolonte` : à 95% de la patience du jour, déclenche un boost dopaminergique ponctuel (`BOOST_SECOND_SOUFFLE`) et étire la patience de l'épisode (+50 ticks, plafonnée), un seul sursaut par épisode — actif uniquement en Mode Libre |
| `agi_google_colab.py` | `ModuleAcceptationAbnegation.augmenter_patience_de_base_definitivement()` : une victoire réelle obtenue après un Sursaut de Volonté augmente durablement `patience_min` (apprentissage de la récurrence) |
| `agi_google_colab.py` | Nouvelles métriques W&B : `Sursauts_Volonte_Jour`, `Patience_Min_Actuelle`, `Sous_Objectifs_Curiosite_Jour` |
| `agi_google_colab.py` | Omission assumée par rapport à la spécification initiale : le "chuchotement d'indice visuel" (illumination du chemin) n'est pas implémenté — nécessiterait de modifier l'observation renvoyée par MiniGrid, hors de portée sans toucher au moteur de rendu de l'environnement |

---

## [16.0] - 2026-07-22

### Thermostat Multimodal & Patience par Abnégation

| Type | Details |
|------|---------|
| **Commit** | `65d70d2` |
| **Catégorie** | feat |
| **Impact** | Fonctionnel |

**Pression cinétique modulée par le contexte perception-action (multimodalité) et promotion de palier DoorKey remplacée par un compteur cumulatif à 4 succès (2 sous-seuils), avec patience étirée sur le sous-seuil le plus exigeant.**

| Fichier modifié | Changement |
|-----------------|------------|
| `agi_google_colab.py` | `ThermostatCinetique` renommé `ThermostatCinetiqueMultimodal` : la pénalité brute de stagnation (inchangée) est désormais atténuée selon le contexte du tick — déplacement libre ($\times 1.00$), objet transporté (`carrying`, $\times 0.30$), interaction face à `Key`/`Door`/`Goal` avec `pickup`/`toggle` ($\times 0.05$) |
| `agi_google_colab.py` | `ModuleAcceptationAdaptative` renommé `ModuleAcceptationAbnegation` : `obtenir_seuil_patience()` accepte désormais un `facteur_complexite_sous_seuil` qui étire la patience de base |
| `agi_google_colab.py` | Ajout de `GestionnaireCursusAbnegation` : remplace la promotion de palier DoorKey par taux de réussite journalier (`SEUIL_MAITRISE_PALIER`, supprimé) par un compteur cumulatif de 4 succès répartis en 2 sous-seuils (Amorçage ×2, Consolidation/Abnégation ×2 sous patience `× COEFF_ABNEGATION_SOUS_SEUIL_2 = 1.6`) |
| `agi_google_colab.py` | Boucle principale : câblage du facteur de complexité par jour, appel du gestionnaire de cursus à chaque fin d'épisode (au lieu du calcul de taux en fin de journée), nouvelles constantes `FACTEUR_ATTENUATION_*`, `SUCCES_PAR_SOUS_SEUIL`, `COEFF_ABNEGATION_SOUS_SEUIL_2` |
| `agi_google_colab.py` | Nouvelles métriques W&B : `Sous_Seuil_Abnegation`, `Succes_Sous_Seuil_Courant`, `Facteur_Complexite` |

---

## [15.0] - 2026-07-22

### Planification Non-Linéaire, Pression Cinétique & Patience Adaptative

| Type | Details |
|------|---------|
| **Commit** | N/A — en attente du commit de cette version |
| **Catégorie** | feat |
| **Impact** | Fonctionnel |

**Système 2 étendu à un rollout multi-échelle à sauts temporels, ajout d'un coût de stagnation générique et d'un seuil de patience adaptatif remplaçant le plafond de ticks fixe.**

| Fichier modifié | Changement |
|-----------------|------------|
| `agi_google_colab.py` | `simuler_futur_et_planifier` : remplacement du rollout pas-à-pas ($t+1 \to t+2 \to t+3$) par un rollout à sauts exponentiels sur des horizons `(1, 3, 7)` — le premier horizon branche sur les 7 actions réelles, les suivants comblent l'écart en suivant le réflexe glouton de la politique, évalués à chaque point d'arrivée et sommés avec actualisation $\gamma^{\text{horizon}}$ |
| `agi_google_colab.py` | `penser()` : paramètre `horizon_planification` (entier) remplacé par `horizons_planification` (tuple) ; `HORIZONS_PLANIFICATION = (1, 3, 7)` dans la config d'exécution |
| `agi_google_colab.py` | Ajout de `ThermostatCinetique` : détecteur générique de pression cinétique, pénalise l'immobilité stricte et le piétinement (positions répétées dans une fenêtre glissante) — actif sur tous les niveaux du `PROGRAMME` |
| `agi_google_colab.py` | Ajout de `ModuleAcceptationAdaptative` : calcule un seuil de patience par épisode (`obtenir_seuil_patience()`) à partir du taux de succès et de la vitesse des succès sur les 20 derniers épisodes ; déclenche une troncature volontaire (`abandon_par_patience`) si l'épisode dépasse ce seuil sans conclusion naturelle, avec une friction dopaminergique douce dédiée (`TAUX_FRICTION_DOUCE_ABANDON`) plutôt qu'un choc négatif |
| `agi_google_colab.py` | Nouvelles métriques W&B : `Patience_Max_Episode`, `Abandons_Patience_Jour`, `Penalite_Stagnation` |

---

## [14.0] - 2026-07-22

### Rêves Adaptatifs & Planification Étendue à 3 Pas

| Type | Details |
|------|---------|
| **Commit** | `2247f2b` (commit initial groupé) |
| **Catégorie** | feat |
| **Impact** | Fonctionnel |

**Consolidation nocturne à porosité adaptative et Système 2 étendu à un horizon de 3 pas.**

| Fichier modifié | Changement |
|-----------------|------------|
| `agi_google_colab.py` | Suppression de la taille de batch de rêve fixe (64) au profit d'un pourcentage adaptatif dérivé de la plasticité base et de la richesse moyenne de la journée |
| `agi_google_colab.py` | `simuler_futur_et_planifier` poussé à un horizon de 3 pas (pas 1 = 7 actions réelles, pas 2/3 = réflexe glouton de la politique, pour éviter l'explosion combinatoire $7^3$) |
| `agi_google_colab.py` | Ajout de `DetecteurFranchissementPortes` (micro-récompense au franchissement d'une porte ouverte) |
| `agi_google_colab.py` | Ajout de `DetecteurProgresPersonnel` (quêtes auto-générées sur les records de proximité au but) |

---

## [13.0] - 2026-07-22

### Décision Autonome & Mode Libre

| Type | Details |
|------|---------|
| **Commit** | `2247f2b` (commit initial groupé) |
| **Catégorie** | feat |
| **Impact** | Fonctionnel |

**Retrait du guidage artificiel une fois le Palier 7 validé, avec relais méta-cognitif renforcé.**

| Fichier modifié | Changement |
|-----------------|------------|
| `agi_google_colab.py` | `Mode_Libre` : désactivation de la récompense de guidage vers l'objectif dès la première validation du Palier 7 |
| `agi_google_colab.py` | `force_planification` monte à 0.85 et `coeff_entropie` à 0.06 en Mode Libre, pour maintenir une exploration active sans béquille |

---

## [12.0] - 2026-07-22

### Cursus à 7 Paliers & Correctif d'Épisodes

| Type | Details |
|------|---------|
| **Commit** | `2247f2b` (commit initial groupé) |
| **Catégorie** | feat |
| **Impact** | Fonctionnel |

**Décomposition du cursus DoorKey en 7 paliers cognitifs et correction du bug des épisodes tronqués.**

| Fichier modifié | Changement |
|-----------------|------------|
| `agi_google_colab.py` | `DetecteurJalonsDoorKey` : division de la tâche `DoorKey` en 7 paliers (Regarder → S'approcher → Toucher/Prendre → Transporter → Viser la Porte → Déverrouiller → Franchir & Sortir) |
| `agi_google_colab.py` | Correction du bug `0/0 épisodes (maîtrise: N/A)` causé par la fin de journée à t=250 ; durée de journée augmentée à 400 ticks |

---

## [11.0] - 2026-07-22

### Réservoir Dopaminergique V3

| Type | Details |
|------|---------|
| **Commit** | `2247f2b` (commit initial groupé) |
| **Catégorie** | feat |
| **Impact** | Fonctionnel |

**Remplacement du tonus dopaminergique fixe par un réservoir homéostatique dynamique.**

| Fichier modifié | Changement |
|-----------------|------------|
| `agi_google_colab.py` | Réservoir `TENEUR_DOPAMINE` (0.001 à 10.0) régi par Friction (décroissance quotidienne), Choc (succès) et Ressort (reset nocturne vers 5.0) |
| `agi_google_colab.py` | `EMPREINTE_ENFANCE` : modulation de l'intensité d'apprentissage par la taille du bus visuel initial |

---

## [10.0-fix1] - 2026-07-22

### Correctif de Stabilité JEPA & Thermostat

| Type | Details |
|------|---------|
| **Commit** | `2247f2b` (commit initial groupé) |
| **Catégorie** | fix |
| **Impact** | Critique |

**Correctif de stabilité sur le modèle du monde JEPA et le thermostat de neurogenèse.**

| Fichier modifié | Changement |
|-----------------|------------|
| `agi_google_colab.py` | Stabilisation de la perte JEPA et du déclenchement du thermostat de mutation |

---

## [10.0] - 2026-07-22

### Système 2 & Rollout Mental Vectorisé

| Type | Details |
|------|---------|
| **Commit** | `2247f2b` (commit initial groupé) |
| **Catégorie** | feat |
| **Impact** | Fonctionnel |

**Introduction du Système 2 délibératif via un rollout mental vectorisé.**

| Fichier modifié | Changement |
|-----------------|------------|
| `agi_google_colab.py` | `simuler_futur_et_planifier` : simulation mentale vectorisée des conséquences des actions, arbitrage avec le Système 1 instinctif via `force_planification` |

---

## [9.1] - 2026-07-22

### Intégration du Tampon Épisodique (Université)

| Type | Details |
|------|---------|
| **Commit** | `2247f2b` (commit initial groupé) |
| **Catégorie** | feat |
| **Impact** | Fonctionnel |

**Ajout de la mémoire épisodique de contexte pour la rétention d'informations temporelles.**

| Fichier modifié | Changement |
|-----------------|------------|
| `agi_google_colab.py` | `vecteurs_episodiques` / `lecture_episodique` : moyenne glissante des états latents récents de l'épisode, utile pour `MemoryS7` (Université) |

---

## [9.0-fix1] - 2026-07-22

### Correctif de la Neurogenèse Bloc par Bloc

| Type | Details |
|------|---------|
| **Commit** | `2247f2b` (commit initial groupé) |
| **Catégorie** | fix |
| **Impact** | Critique |

**Correction de la segmentation des dimensions lors de l'agrandissement des couches.**

| Fichier modifié | Changement |
|-----------------|------------|
| `agi_google_colab.py` | `NaultheneLinearSynaptique.agrandir()` : correction de la reconstruction bloc par bloc des poids existants lors de la neurogenèse |

---

## [9.0] - 2026-07-22

### Cursus Académique Progressif (Primaire à Doctorat)

| Type | Details |
|------|---------|
| **Commit** | `2247f2b` (commit initial groupé) |
| **Catégorie** | feat |
| **Impact** | Fonctionnel |

**Mise en place du programme complet des 5 niveaux MiniGrid.**

| Fichier modifié | Changement |
|-----------------|------------|
| `agi_google_colab.py` | `PROGRAMME` : Primaire (`Empty-8x8`) → Collège (`DoorKey-6x6`) → Lycée (`Unlock-5x5`) → Université (`MemoryS7`) → Doctorat (`MultiRoom-N4-S5`), promotion après 2 victoires consécutives |

---

## [8.0] - 2026-07-22

### Alignement Graph-Gradient RL & Rêve Nocturne

| Type | Details |
|------|---------|
| **Commit** | `2247f2b` (commit initial groupé) |
| **Catégorie** | feat |
| **Impact** | Fonctionnel |

**Introduction du mécanisme de rêve nocturne (replay) et alignement des gradients RL/JEPA.**

| Fichier modifié | Changement |
|-----------------|------------|
| `agi_google_colab.py` | `rever()` : rejeu d'un lot de souvenirs pondéré par importance pendant la phase de sommeil |
| `agi_google_colab.py` | Alignement du graphe de calcul entre la perte Acteur-Critique et la perte JEPA pour un unique `backward()` cohérent |

---

## [7.0] - 2026-07-22

### Phase 7 Initiale (Architecture Hybride Duale)

| Type | Details |
|------|---------|
| **Commit** | `2247f2b` (commit initial groupé) |
| **Catégorie** | feat |
| **Impact** | Fonctionnel |

**Première version documentée de l'architecture hybride RL + JEPA.**

| Fichier modifié | Changement |
|-----------------|------------|
| `agi_google_colab.py` | Socle initial : `AGI_Naulthene`, tronc cérébral commun, tête motrice Acteur-Critique, modèle du monde JEPA |

---

*Note : les entrées v7.0 à v14.0 ont été reconstituées à partir du journal narratif de [readme.md](../readme.md) lors de la mise en place initiale de ce changelog (2026-07-22) — les hash de commit réels n'étaient pas disponibles rétroactivement (dépôt git non initialisé jusqu'à cette date). Toute nouvelle entrée à partir de maintenant doit renseigner un hash réel.*
