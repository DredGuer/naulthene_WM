# Changelog — Naulthène AGI

Historique des évolutions du projet, commit par commit. Voir [readme.md](../readme.md) pour la documentation narrative complète et [CLAUDE.md](../CLAUDE.md) pour les règles de maintenance de ce fichier.

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
