# CONCEPTION — V22 : L'Hémisphère Auditif & Vocal (expérimental)

> ✅ **Implémenté et corrigé** (voir `readme.md` section "🗣️ L'Hémisphère Auditif &
> Vocal", `CHANGELOG.md` entrées `[22.0-experimental]` et `[22.1-experimental]`). Ce
> document reste comme trace de la conception initiale ; deux décisions ont été
> **tranchées différemment** de ce qui était recommandé ici après une correction de
> trajectoire explicite de l'utilisateur (cerveau 100% multimodal unifié, pas de mode
> isolé) — voir §4.3 et §9 mis à jour ci-dessous.
>
> **v22.1 — correctif majeur post-revue** : trois défauts de conception ont été détectés
> après la v22.0 (revue critique de l'utilisateur, confirmée par exploration du code
> réel), dont un critique — voir §11 en fin de document pour le détail complet. En
> résumé : (1) `tete_vocale` ne recevait aucun gradient d'apprentissage dirigé (sortie
> détachée), corrigé par une perte MSE supervisée ; (2) l'oreille recevait l'embedding
> sémantique en même temps que le son, risquant de faire ignorer le son réel, déplacé
> vers une quête dans `vecteur_bio` ; (3) le JEPA audio pouvait perturber le JEPA visuel
> dès le tick 0, corrigé par une tête prédictive séparée à poids progressif.
>
> Comme les v18–v21, cette mécanique vit uniquement dans l'écosystème local
> (`agi_local_test.py` + `hemisphere_audio.py`, `professeur_gemma.py`,
> `client_professeur.py`), jamais portée sur `agi_google_colab.py` tant qu'elle n'est
> pas validée sur un run long. Statut : **expérimental**.

---

## 1. Le but, en une phrase

Doter Naulthène d'un **véritable hémisphère de traitement audio** dans son cerveau
(pas un module bricolé à côté), symétrique à l'hémisphère visuel existant
(`porte_visuelle` → bus → `tete_motrice`) : une **oreille** (`porte_auditive`) et une
**bouche** (`tete_vocale`). Un professeur externe (Gemma via Ollama) te fait dire un
mot au micro, le transmet à l'agent, écoute ce que l'agent produit, et **juge s'il a
bien répété** — ce jugement devient une récompense qui nourrit le réservoir
dopaminergique et la LTP existants, exactement comme les détecteurs MiniGrid.

## 2. Décisions déjà validées (par l'utilisateur)

| Question | Choix retenu |
|----------|--------------|
| **Oreille** (entrée) | **Double entrée** : `porte_auditive` reçoit à la fois le spectrogramme (le son brut, MFCC) ET l'embedding sémantique du mot (via Ollama) |
| **Bouche** (sortie) | **Vecteur de son continu**, décodé par un **synthétiseur de formants** (~8 paramètres physiques : f0 + formants F1/F2/F3 + durée/amplitude) — petit espace, réellement apprenable |
| **Gemma** | **Juge de répétition** : reçoit le mot cible et le son produit, renvoie un score de similarité [0,1] → devient `poids_evenement` / récompense |
| **Méthode de travail** | Ce plan de conception d'abord, puis implémentation par étapes testées |

## 3. Le problème dur, énoncé honnêtement

Le choix "vecteur de son continu" (bouche) crée une **récompense creuse** (sparse
reward) : au départ, `tete_vocale` produit des paramètres aléatoires → le synthétiseur
sort un son quelconque → Gemma juge « 0, ça ne ressemble à rien » → l'agent n'a
**aucune direction de correction**. Sans précaution, Naulthène babillerait du bruit
très longtemps sans converger.

**Ce que la synthèse par formants change** : au lieu d'un espace audio géant, l'agent
ne pilote que ~8 nombres physiques. L'espace des voyelles (a/e/i/o/u) est un petit
sous-ensemble atteignable de cet espace. C'est ce qui rend le problème *tractable* — on
apprend à « placer sa bouche », pas à générer une onde arbitraire.

**Garde-fous supplémentaires prévus** (détaillés §7) : un **curriculum vocal** (voyelles
seules d'abord, puis syllabes), une **récompense continue** (Gemma/embedding renvoie un
score graduel, pas juste 0/1 — « tu t'approches » compte), et la réutilisation de la
**curiosité JEPA** existante pour récompenser l'exploration sonore.

---

## 4. Architecture : l'hémisphère audio greffé sur le cerveau

### 4.1 Nouvelles couches `NaultheneLinearSynaptique`

Symétrie exacte avec l'hémisphère visuel. Deux nouvelles couches :

```
# L'OREILLE — entrée sensorielle audio (miroir de porte_visuelle)
self.porte_auditive = NaultheneLinearSynaptique(DIM_AUDIO_ENTREE, dim_bus)

# LA BOUCHE — tête de sortie vocale (miroir de tete_motrice)
self.tete_vocale = NaultheneLinearSynaptique(dim_bus, DIM_VOCALE)
```

- `DIM_AUDIO_ENTREE` = `DIM_MFCC + DIM_EMBED_SEMANTIQUE` (double entrée : son brut
  concaténé au sens). Ex : 13 coefficients MFCC × quelques frames aplatis (~40) +
  embedding réduit (~32) — dimensions exactes à figer en début d'implémentation, mais
  **fixes** (comme `DIM_VECTEUR_BIO`), elles ne grandissent jamais avec la neurogenèse.
- `DIM_VOCALE` = ~8 (les paramètres de formants). Fixe également.

### 4.2 Les trois points de synchronisation OBLIGATOIRES (règle CLAUDE.md)

Toute nouvelle couche `NaultheneLinearSynaptique` doit être ajoutée aux **trois**
endroits, sinon le sommeil ou la neurogenèse casse silencieusement :

1. **`__init__`** : déclaration des deux couches (ci-dessus).
2. **`cycle_sommeil_global()`** : ajouter `porte_auditive.cycle_sommeil(...)` et
   `tete_vocale.cycle_sommeil(...)` à la liste sommée.
3. **`declencher_neurogenese()`** : ajouter les deux `agrandir(...)`. Par symétrie avec
   `porte_visuelle`/`tete_motrice` :
   - `self.porte_auditive.agrandir([(DIM_AUDIO_ENTREE, 0)], a)` — l'entrée audio ne
     grandit pas (comme `dim_visuelle`), seule la sortie vers le bus grandit de `a`.
   - `self.tete_vocale.agrandir([(d, a)], 0)` — l'entrée (bus) grandit de `a`, la
     sortie `DIM_VOCALE` ne grandit pas (comme `tete_motrice` garde `num_actions`).
4. **`fortifier_synapses()`** : ajouter les deux couches à la liste de la LTP (pour que
   les synapses auditives se gravent aussi sur un bon événement).

### 4.3 Flux dans `penser()` — TRANCHÉ : option intégrée

> **Décision finale de l'utilisateur** (correction de trajectoire explicite, citée
> intégralement dans le plan v22.0) : *« Si l'on sépare la vue et l'ouïe dans des
> "modes" isolés, on recrée des IAs étroites (Narrow AI). L'essence même de l'AGI,
> c'est la synesthésie [...] Naulthène doit percevoir le monde comme nous : un flux
> continu et simultané de pixels et d'ondes sonores, traité par un seul grand cortex
> multimodal. »* L'option intégrée a donc été retenue, contrairement à la
> recommandation initiale ci-dessous (conservée pour trace) :

- **Option intégrée (RETENUE, implémentée)** : l'entrée audio est fusionnée au bus
  visuel dans le même tronc cérébral (`_tronc_cerebral`, par simple somme
  `bus_latent = relu(porte_visuelle(vision)) + relu(porte_auditive(audio))`) — l'agent
  « voit et entend » simultanément, à chaque tick, sans mode dédié. `penser()` gagne un
  paramètre optionnel `obs_auditive=None` (silence = comportement identique à avant
  v22.0, non-régression validée).
- ~~Option modale (recommandée initialement pour la v1)~~ : écartée par décision
  utilisateur — un flux audio séparé, actif seulement pendant les « leçons », aurait
  recréé exactement la fragmentation en IA étroite que l'utilisateur voulait éviter.

---

## 5. La pile audio à installer

Rien de tout ça n'est présent aujourd'hui (vérifié). À installer dans le venv :

| Besoin | Outil proposé | Note |
|--------|---------------|------|
| Capturer le micro | `sounddevice` | demande l'autorisation micro macOS |
| Transcrire ta voix → texte | `openai-whisper` (ou `faster-whisper`) | modèle `base`/`small` suffit en local |
| Spectrogramme MFCC | `librosa` (ou `torchaudio`) | pour la double entrée (son brut) |
| Embedding sémantique du mot | **Ollama** (`nomic-embed-text` / `all-minilm`, déjà installés) | pour la double entrée (sens) |
| Synthèse par formants | **numpy seul** (déjà là) | un synthétiseur de formants basique s'écrit en ~50 lignes |
| Entendre l'agent / TTS de référence | **`say`** (déjà là, `say -o` produit un `.aiff`) | pour générer les sons cibles de référence |
| Juge de répétition | **Ollama `gemma4:e4b`** (déjà installé) | reçoit cible + description du son produit |

Commande d'installation prévue :
`pip install sounddevice openai-whisper librosa` (torchaudio optionnel).

---

## 6. Le rôle de Gemma (professeur & juge), concrètement

Gemma a **deux fonctions** (comme demandé) :

1. **Enseigner** : au début d'une leçon, il choisit/annonce le mot ou le son à répéter
   (curriculum vocal, §7). Il te le dit, tu le prononces au micro.
2. **Juger la répétition** : il reçoit (a) le mot cible et (b) une **description
   textuelle du son produit** par Naulthène (ex : « voyelle proche de `a`, F1≈730,
   F2≈1090 ») ou la transcription Whisper de ce son, et renvoie un **score [0,1]**.

⚠️ Point de réalisme : Gemma est un LLM **texte**, il n'« entend » pas un `.wav`
directement. Deux façons de lui faire juger le son produit :
- **Via Whisper** : on synthétise le son de l'agent, Whisper tente de le transcrire, on
  donne la transcription à Gemma → « l'agent a produit un son que Whisper entend comme
  "ah", la cible était "a" → proche ». Robuste, réutilise la pile.
- **Via les formants** : on décrit numériquement les formants produits vs. les formants
  cibles → Gemma (ou un simple calcul de distance) note la proximité. Plus direct, pas
  besoin de re-transcrire.

Recommandation : **distance de formants pour la récompense par tick** (déterministe,
rapide, pas d'appel LLM à chaque son), et **Gemma pour le dialogue/curriculum et un
jugement qualitatif périodique** (« bravo, tu maîtrises les voyelles, passons aux
syllabes »). Cela évite d'appeler un LLM 9,6 Go à chaque tick, ce qui serait trop lent
pour un entraînement RL. → à confirmer (§9 Question ouverte B).

Le score obtenu alimente le pipeline existant **sans le modifier** : il devient un
`poids_evenement` (→ choc dopaminergique + `fortifier_synapses`) et une composante de
`recompense_interne`, exactement comme `poids_ressource_bio` ou les jalons DoorKey.

---

## 7. Curriculum vocal (le cursus de la parole)

Symétrique au cursus MiniGrid (Primaire → Doctorat). Progression proposée :

| Palier vocal | Cible | Validation |
|--------------|-------|------------|
| 1. Vocaliser | produire un son voisé (pas du silence) | énergie audio > seuil |
| 2. Voyelle unique | répéter `a` | distance formants < seuil |
| 3. Jeu de voyelles | `a`, `e`, `i`, `o`, `u` | chacune validée |
| 4. Syllabe simple | `ba`, `ma`, `pa` (consonne + voyelle) | proximité globale |
| 5. Mot court | `papa`, `maman` | transcription Whisper ≈ cible |

Réutilise les mécaniques existantes : `GestionnaireCursusAbnegation` (promotion par
succès cumulés), la patience par Abnégation, la curiosité JEPA (récompense
l'exploration de nouveaux sons), le rêve nocturne (rejoue les bonnes vocalisations).

---

## 8. Architecture logicielle (nouveaux fichiers)

Cohérent avec la séparation V21 (fichiers dédiés qui importent les composants) :

```
hemisphere_audio.py   → le synthétiseur de formants (vecteur → son), l'extraction MFCC,
                        la capture micro (sounddevice), la transcription Whisper.
                        Aucune dépendance au réseau — pur traitement du signal.
professeur_gemma.py   → le client Ollama : choisit le mot à enseigner (curriculum vocal),
                        juge la répétition (score), dialogue. Isolé pour pouvoir le
                        tester/mocker sans réseau de neurones.
leçon_parole.py       → la boucle de « leçon » : orchestre micro → cerveau → synthèse →
                        jugement → récompense. Analogue à traiter_tick mais pour le mode
                        audio. Consomme les helpers d'agi_local_test.py.
```

Modifications dans `agi_local_test.py` : uniquement l'ajout des deux couches
(`porte_auditive`, `tete_vocale`) aux 4 points de synchro (§4.2) + les constantes
`DIM_AUDIO_ENTREE`, `DIM_VOCALE`, `DIM_MFCC`, `DIM_EMBED_SEMANTIQUE`. La persistance
(`persistance.py`) suit automatiquement puisqu'elle sauve `state_dict()` complet — les
nouvelles couches y seront incluses sans changement (à vérifier : rétrocompat des vieux
`.brain` sans ces couches — §9 Question ouverte C).

---

## 9. Questions ouvertes — TOUTES TRANCHÉES (implémentation terminée)

- **A. Intégration** : ✅ **fusionnée au tronc visuel** (option intégrée, voir §4.3) —
  décision utilisateur explicite, cerveau 100% multimodal unifié.
- **B. Fréquence d'appel Gemma** : ✅ **distance de formants par tick + Gemma
  périodique**, confirmé nécessaire par mesure réelle : `gemma4:e4b` met ~8 à 30
  secondes par réponse sur cette machine — un jugement par tick était de toute façon
  hors de portée pour du RL.
- **C. Rétrocompatibilité des `.brain`** : ✅ **greffe sur le cerveau existant**
  (`load_state_dict(strict=False)`, voir `persistance.py`), acquis MiniGrid préservés.
  Piège détecté et corrigé pendant les tests : l'ancien optimiseur (moins de groupes de
  paramètres) fait planter `optimizer.load_state_dict` après une greffe — un optimiseur
  frais est recréé automatiquement dans ce cas, sans perte de poids.
- **D. Mode d'entraînement** : ✅ **client dédié séparé** (`client_professeur.py`,
  option ii) — un seul cerveau persistant dans la Cuve, mais deux clients distincts
  (`client_corps.py` pour MiniGrid, `client_professeur.py` pour les leçons vocales) qui
  se connectent à tour de rôle. Cohérent avec le cerveau unifié : c'est le *client* qui
  change, pas le cerveau qui bascule de mode.

---

## 10. Étapes d'implémentation — TOUTES TERMINÉES

1. ✅ **Pile audio** : `sounddevice`, `librosa`, `openai-whisper`, `requests` installés ;
   `say`/Ollama confirmés déjà présents et fonctionnels.
2. ✅ **Synthétiseur de formants** (`hemisphere_audio.py`) : validé par tests (pics
   spectraux alignés sur F1 à 20-70 Hz près, voyelles mutuellement discriminables) et à
   l'oreille (séquence a-e-i-o-u confirmée reconnaissable par l'utilisateur).
3. ✅ **Couches audio** dans `agi_local_test.py` : les 4 points de synchro validés par
   exécution réelle (neurogenèse préserve les poids, LTP touche les 2 couches,
   `cycle_sommeil_global` sans crash) ; rétrocompatibilité `.brain` testée sur un
   scénario reproduisant fidèlement un vieux checkpoint.
4. ✅ **Professeur Gemma** (`professeur_gemma.py`) : testé contre le vrai Ollama local
   (embedding, curriculum, jugement qualitatif avec repli propre si indisponible).
5. ✅ **Boucle de leçon** (`client_professeur.py`, nommé ainsi plutôt que
   `leçon_parole.py` pour rester cohérent avec la convention `client_*.py` de V21) :
   orchestration complète validée bout-en-bout (daemon de test + leçon réelle, son joué
   en temps réel, jugement Gemma reçu).
6. ✅ **Validation courte durée (v22.1)** : score de formants confirmé en progression
   réelle (0.0045→0.1111 sur 5 jours × 24 ticks, seed fixe) — la preuve que le
   correctif du défaut 1 (§11) fonctionne. Validation longue durée sur run réel
   prolongé (convergence vers un `a` pleinement reconnaissable) toujours à suivre par
   l'utilisateur sur ses propres sessions.

---

## 11. Correctif v22.1 — trois défauts de conception détectés à la revue

Après implémentation de la v22.0, une revue critique de l'utilisateur (avec verdict
détaillé confirmé par exploration du code réel) a identifié trois défauts. Les trois
ont été corrigés, testés et documentés (`CHANGELOG.md [22.1-experimental]`).

### 11.1 Défaut 1 — "Le membre fantôme" (CRITIQUE)

**Constat** : dans `traiter_tick`, `parametres_vocaux.detach()` était appelé avant tout
calcul de score de récompense. Le score alimentait bien la dopamine et
`recompense_interne`, mais **aucun gradient dirigé n'apprenait jamais à `tete_vocale` à
viser la cible** — `apprendre_journee` ne connaissait que 3 pertes (JEPA, acteur,
critique), la voix n'y entrait pas du tout. La bouche produisait des formants
aléatoires, corrigés uniquement par LTP hebbien et rêve, jamais par une erreur dirigée.
Ce n'était pas la « collision de pertes discret/continu » redoutée initialement (§3
ci-dessus) — c'était une absence totale de perte vocale : rien ne crashait parce que
rien n'apprenait.

**Correctif** : ajout d'un buffer de journée `etat.pertes_vocales`, peuplé dans
`traiter_tick` par une perte `F.mse_loss` calculée sur le tenseur `parametres_vocaux`
**non détaché** (celui retourné par `penser()`, toujours dans le graphe), restreinte
aux dimensions F1/F2 réellement contraintes par la leçon (les 6 autres dimensions du
vecteur 8-dim n'ont pas de cible explicite, les inclure pousserait `tete_vocale` vers
une valeur neutre par pur artefact de normalisation). Sommée à `perte_totale` dans
`apprendre_journee` via `COEFF_PERTE_VOCALE`. Le score détaché continue d'alimenter la
dopamine en parallèle — les deux usages coexistent, calculés séparément.

**Validation** : score de formants passé de 0.0045 (jour 1) à 0.1111 (jour 5) sur un
run de test dédié (5 jours × 24 ticks, seed fixe, cible = voyelle "a").

### 11.2 Défaut 2 — "Le court-circuit de la double entrée"

**Constat** : `porte_auditive` recevait `DIM_AUDIO_ENTREE=162` = MFCC (130) concaténé à
l'embedding sémantique du mot (32), dans la même entrée. Un réseau recevant le concept
parfait en même temps que le son bruité peut apprendre à ignorer le son — il
n'« écoute » jamais vraiment, la tâche devient triviale sans qu'il ait besoin de
traiter l'acoustique.

**Correctif** : `DIM_AUDIO_ENTREE` réduit à 130 (MFCC seul). L'embedding devient une
**quête vocale** compacte de 8 dims (les formants cibles normalisés) injectée dans
`vecteur_bio` (`DIM_VECTEUR_BIO` 8→16), au même titre que les quêtes
SURVIVAL_FOOD/SURVIVAL_WATER déjà existantes — le concept-cible dit "voici ce qu'il
faut produire", jamais mélangé au son perçu. `porte_auditive.agrandir` et
`obtenir_vecteur_bio` mis à jour en conséquence.

**Effet de bord assumé** : `DIM_VECTEUR_BIO` 8→16 change la forme de `integrateur_bio`
(entrée `dim_bus + DIM_VECTEUR_BIO`) — voir §11.4 pour la conséquence sur la
rétrocompatibilité `.brain`.

### 11.3 Défaut 3 — "L'empoisonnement du JEPA"

**Constat** : `perte_jepa` ajoutait la contribution auditive à la cible du bus dès le
tick 0, sans pondération, via la même tête prédictive que la vision
(`generateur_attente`). Le risque était moindre que "prédire le chaos audio brut" (la
cible passe par `porte_auditive`, une projection apprise, pas le MFCC brut), mais une
tête unique non pondérée pouvait laisser un signal audio bruyant perturber les
gradients de la vision — dangereux pour la physique MiniGrid acquise sur 481 jours.

**Correctif** : nouvelle couche `generateur_attente_audio`, miroir exact de
`generateur_attente`, ajoutée aux 4 points de synchro obligatoires (`__init__`,
`fortifier_synapses`, `cycle_sommeil_global`, `declencher_neurogenese`). `perte_jepa`
calcule désormais deux pertes MSE strictement séparées (vision, jamais affectée par
l'audio ; audio, via la tête dédiée), la seconde pondérée par `coeff_jepa_audio` monté
**progressivement** de 0 à `COEFF_JEPA_AUDIO_MAX=0.3` sur `RAMPE_JEPA_AUDIO=2000` ticks
audio cumulés (`etat.ticks_audio_recus`).

**Validation** : coefficient confirmé quasi nul au démarrage (0.00015 après le premier
tick audio reçu), montée linéaire vérifiée sur plusieurs points de mesure.

### 11.4 Effet de bord — rétrocompatibilité `.brain` et `integrateur_bio`

Le changement `DIM_VECTEUR_BIO` 8→16 (§11.2) modifie la *forme* de `integrateur_bio`
(pas seulement des clés manquantes/en trop, que `strict=False` gère nativement). Testé
sur le vrai `.brain` de production (copie) : `load_state_dict(strict=False)` seul lève
une `RuntimeError` ("size mismatch for integrateur_bio..."). Décision : `integrateur_bio`
est explicitement exclu du `state_dict` chargé et renaît à neuf — assumé car cette
couche a une `base_weight` quasi vide (norme ~0.01, moins de 3% de poids non-nuls) sur
le vrai cerveau après 481 jours : elle n'avait presque rien appris, la perte est
négligeable. Résurrection complète re-testée après correctif : `tick_absolu`, `jour`,
dopamine et souvenirs spatiaux tous préservés ; 10 ticks MiniGrid post-greffe exécutés
sans erreur.
