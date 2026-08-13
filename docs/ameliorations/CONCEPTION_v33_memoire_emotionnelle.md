# CONCEPTION v33 — La Mémoire Émotionnelle & le Replay Orienté

> # 🗄️ ARCHIVÉ — 2026-08-05
>
> **Le chantier décrit ici n'a PAS été ouvert, et sa prémisse a été INFIRMÉE par la mesure.**
>
> Ce document proposait la Valence et le Replay Orienté pour corriger un agent supposé
> incapable de retenir ses victoires. Les étapes 0 → 0.6 qu'il prescrivait ont été livrées
> (chronométrie des jalons, ablation inversée, chronologie des victoires) — et c'est
> précisément cette instrumentation qui a démenti le diagnostic :
>
> | Hypothèse de ce document | Ce que le run de 5000 jours a mesuré |
> |---|---|
> | « L'agent ne retient rien, ses victoires sont du bruit stationnaire » | **Ratio de tendance 0,65** au Collège sur 45 intervalles — les victoires **se rapprochent** (126 → 50 → 65 → 51 jours par quart) |
> | « Le Palier 7 est un mur infranchissable » | **Franchi au jour 3335**, puis Lycée, Université et **Doctorat** atteints — le cursus complet |
> | « La promotion est mathématiquement inatteignable (2 victoires consécutives) » | **Faux** : trois enchaînements à 2 jours d'écart (j1083→1085, j1839→1841, j2769→2771) |
>
> **La leçon méthodologique, qui est la vraie valeur de cette archive** : le blocage
> diagnostiqué sur 700 jours n'était pas un blocage, mais une **phase d'apprentissage lente**
> observée trop tôt. Trois conclusions successives (« mur absolu », « désert de signal »,
> « verrou du cursus ») ont été tirées d'échantillons trop courts, et toutes trois démenties
> par un run plus long. Aucune des mécaniques proposées ici n'aurait traité un problème réel.
>
> Ce qui reste valable et mérite d'être relu avant toute future refonte de la mémoire : le
> constat que `abs(recompense_interne)` **détruit la valence** dans le calcul d'`importance`
> (§2), les **options écartées** et leurs raisons (§3 — fusion des mémoires, typage dans le
> tissu synaptique), et les **risques identifiés** (§6).
>
> Pour l'état courant : [../../readme.md](../../readme.md),
> [../CHANGELOG.md](../fonctionnement/CHANGELOG.md), [../LANCEMENT.md](../fonctionnement/LANCEMENT.md).

> **Statut d'origine : PROPOSITION — aucune ligne de code écrite.**
> Document de cadrage soumis à arbitrage utilisateur. Il précise ce qui est proposé, ce
> qui est **écarté et pourquoi**, l'ordre des incréments, et ce qu'il faut **mesurer
> avant** chacun. Rien ne doit être implémenté avant les arbitrages de la §8.

---

## 1. Le constat de départ

Trois discussions successives ont convergé sur un diagnostic unique : l'agent est bloqué
au Palier 7 de DoorKey non par incompréhension du monde (erreur JEPA à `0.0003`), mais
parce que le **dernier segment de la chaîne — porte déverrouillée → sortie — est un
désert de signal** :

| Ce que l'agent possède | Nourriture / Eau | Le But (Goal) |
|---|---|---|
| Gradient sensoriel continu | odorat exponentiel + clinotaxie ΔS (v32.0) | **aucun** |
| Récompense intermédiaire | `r_bio` + choc dopaminergique 0.25 | **aucune** en Mode Libre |
| Repère en mémoire spatiale | oui (`FOOD` / `WATER`) | **aucun** |
| Quête injectée dans `vecteur_bio` | oui (`SURVIVAL_*`) | **aucune** |

L'agent est mieux équipé — sensoriellement, mnésiquement et motivationnellement — pour
trouver une pomme que pour finir son cursus.

### 1.1. Pourquoi les mécanismes existants ne suffisent pas

Deux pistes ont été évaluées et **écartées en l'état** au cours de l'analyse :

- **« Ajouter un RPE sur l'erreur JEPA »** → *déjà implémenté depuis la v17.0*
  (`DetecteurCuriositeJEPA` → `poids_visuel` → `poids_evenement` →
  `fortifier_synapses`). Il ne fonctionne plus parce qu'il se déclenche sur
  `erreur > moyenne_récente × 1.5` : à `0.0003`, il n'y a plus de surprise à
  récompenser. **Objection de fond** : ouvrir la porte n'est *pas* une surprise pour cet
  agent — il prédisait déjà l'événement. Un signal fondé sur la surprise récompense
  l'ignorance qui se dissipe, jamais la compétence qui s'exerce. Il ne peut
  structurellement pas atteindre une séquence parfaitement prédite et non récompensée.
- **« Écrire des repères spatiaux de type SURPRISE »** → l'écriture est triviale
  (`enregistrer_evenement` accepte déjà un type libre), mais **personne ne les lirait** :
  la mémoire spatiale n'est interrogée que si une quête de survie est active, et
  uniquement sur le type de cette quête. Le repère irait dans une FIFO cappée à 3
  souvenirs/case, où il évincerait des repères alimentaires. **Effet net négatif.**

---

## 2. La découverte qui fonde cette version

`memoire_moyen_terme` — la mémoire du jour, seule matière première du rêve — pondère
chaque souvenir par :

```python
'importance': (abs(recompense_interne) + valeur_erreur * 2.0 + 1e-5)
              * micro_boost_ancrage * etat.empreinte_enfance
```

**Ce `abs()` détruit la valence.** À magnitude égale, tomber dans la lave et boire de
l'eau produisent exactement la même trace mnésique. L'agent sait qu'un événement fut
*fort*, jamais s'il fut *bon*.

La même amputation existe sur le canal dopaminergique : `poids_evenement` est borné dans
`[0,1]` par construction (le « OU doux » v27.0) et pilote à la fois le choc
(`TAUX_CHOC_BASE`) et la LTP (`fortifier_synapses`) — toujours **sans signe**.

> **Ce n'est donc pas l'ajout d'une couche bio-inspirée décorative : c'est la
> restauration d'une information que le code détruit activement.**

Chez l'humain, l'amygdale module l'encodage hippocampique *avec* la valence — c'est ce
qui permet l'évitement, l'apprentissage en un essai, la peur. L'agent en est aujourd'hui
structurellement incapable.

---

## 3. Ce qui est ÉCARTÉ (et pourquoi) — jurisprudence

Cette section a autant de valeur que la suivante. Elle enregistre les options refusées
pour éviter qu'elles soient réintroduites plus tard sans leur contre-argument.

### 3.1. ❌ Fusionner les mémoires en « 2 mémoires »

Proposition initiale : fusionner épisodique + spatiale + mémoire du jour + corporelle.

**Refusé.** Ces mémoires ont des **cycles de vie incompatibles** :

| Mémoire | Durée de vie | Effacée par |
|---|---|---|
| `memoire_moyen_terme` (jour) | 1 journée | `clear()` chaque nuit |
| `memoire_episodique_spatiale` | des centaines de jours | changement de niveau |
| Corporelle (jauges, dopamine) | toute la vie | jamais |
| `vecteurs_episodiques` | 1 journée | début de journée |

Un objet unique devrait porter quatre politiques d'oubli contradictoires. De plus, la
v31.0 a précisément démontré que **confondre ces mémoires produit de faux diagnostics**
(« le rêve ne libère pas la mémoire spatiale » — il ne la touche jamais).

**Ce qui est réellement souhaité n'est pas la fusion mais le LIAGE** : qu'un souvenir
spatial pointe vers ce qu'on percevait et ressentait à cet endroit. C'est un
enrichissement de *contenu*, pas une fusion de *conteneurs*. Argument biologique : chez
l'humain, l'hippocampe ne *contient* pas les modalités sensorielles — il les
**réassemble** depuis les cortex. L'architecture actuelle est déjà plus proche du
cerveau que la fusion proposée.

### 3.2. ❌ Typer les souvenirs *dans* la mémoire synaptique

Proposition initiale : « la mémoire synaptique avec plusieurs types de souvenirs
(positif, négatif, marquant) ».

**Erreur de catégorie.** La mémoire synaptique n'a pas de souvenirs : c'est un tissu de
connexions (`base_weight`), il n'y a nulle part où accrocher une étiquette. Ce qui est
typable, c'est ce qui **entre** dedans — le pic dopaminergique qui déclenche la LTP.

L'idée est donc retenue, mais **déplacée** : la valence vit dans le *canal
dopaminergique*, pas dans la structure synaptique. Cette nuance transforme une refonte
en une modification ciblée.

### 3.3. ⏸️ « All times / real times » — ajourné, distinction déjà présente

Si l'intention est « le vécu instantané vs le savoir intemporel », la distinction existe
déjà : la mémoire synaptique **est** le all-times (elle ne date rien, elle distille), les
buffers **sont** le real-time. Si une autre notion est visée, elle doit être reformulée
en mécanisme avant d'entrer dans une version. **Aucun code sur ce point.**

### 3.4. ❌ Un seuil codé en dur dans le chemin motivationnel

Toute formulation du type « *si* la loss JEPA baisse soudainement, *alors* libérer un
pic » est refusée par jurisprudence : le projet a écarté cette forme **trois fois** (v28
appel à C3, v29 court-circuit C1→C2, v30 boucle d'attention Exo-Sens). Ce qui est
proposé ici doit rester **continu et modulatoire**, jamais un `if` sur un seuil.

---

## 4. La proposition — deux attributs transversaux, six mémoires conservées

Les six mémoires restent distinctes. On ajoute **deux attributs transversaux** :

| Attribut | Ce qu'il ajoute | Où il vit |
|---|---|---|
| **Valence** | le *signe* en plus de l'intensité | `importance`, canal dopaminergique, repères spatiaux |
| **Contexte multimodal** | ce qu'on voyait / sentait / entendait là | contenu du repère spatial |

### 4.1. Incrément A — La Valence (le cœur de la version)

Un scalaire `v ∈ [-1, +1]` calculé par tick, à côté de `poids_evenement` (qui reste
inchangé dans `[0,1]` — **invariant non négociable**, il est facteur du choc et de la
LTP).

Sources naturelles du signe, toutes déjà présentes dans le code :
`recompense_interne` (signe direct), `r_bio` (négatif quand les jauges se dégradent),
`penalite_stagnation`, `recompense_env`.

Trois consommateurs :

1. **`importance` du rêve** — remplacer `abs(r)` par une forme qui conserve le signe et
   permet une **asymétrie négative** (biologiquement : un événement négatif se grave
   plus fort qu'un positif de même magnitude).
2. **LTP** — `fortification_dopaminergique` reçoit aujourd'hui un scalaire positif. Une
   valence négative doit produire une gravure **d'évitement**, pas un renforcement.
   ⚠️ **C'est le point le plus délicat de toute la version** (voir §6).
3. **Repères spatiaux** — un repère porte sa valence : « ici il y avait à manger » vs
   « ici j'ai souffert ».

### 4.2. Incrément B — Le Replay Orienté (le plus prometteur pour le Palier 7)

**C'est la conséquence la plus importante de l'incrément A, et elle n'était dans aucune
des pistes précédentes.**

Aujourd'hui `rever()` ne calcule **que `perte_jepa`** : rejouer une trajectoire apprend
« voilà comment le monde évolue si je vais à gauche », jamais « aller à gauche était
bien » (constat v31.1, vérifié). Le rêve est **motoriquement neutre**.

Avec une valence, le rêve peut cesser de l'être — et c'est exactement le mécanisme par
lequel un rat consolide un labyrinthe pendant son sommeil (*hippocampal replay*) :
rejouer préférentiellement les trajectoires **gagnantes** en les renforçant.

Cela adresse **directement** le blocage du Palier 7 : une victoire rare, aujourd'hui
noyée dans une journée d'échecs et jamais rejouée motoriquement, serait consolidée.

⚠️ **Rupture doctrinale à assumer explicitement** : cela ajoute une perte acteur au rêve,
ce que le projet n'a jamais fait depuis la v8.0. À trancher en §8 — c'est le choix le
plus structurant du document.

### 4.3. Incrément C — Le Liage Multimodal

Le repère spatial passe de `{pos, type, tick}` à un enregistrement portant aussi une
**empreinte perceptive compacte** (ce qu'on voyait/sentait/entendait) et sa valence.

C'est l'incrément le plus proche de « la mémoire humaine »… et **probablement celui qui
touchera le moins le Palier 7**. Il est donc placé en dernier, sciemment.

### 4.4. Incrément D — Rendre la mémoire spatiale lisible hors survie

Prérequis de C, et correctif du blocage identifié en §1.1 : la mémoire spatiale n'est
lue que sous quête de survie. Deux sous-chantiers :

- un **déclencheur de lecture** hors `SURVIVAL_*` ;
- l'élargissement de `vecteur_rappel`, aujourd'hui **2 dims** (`[distance, fraîcheur]`)
  sans encodage du *type* rappelé — il n'y a physiquement pas la place pour deux rappels
  concurrents.

---

## 5. Ordre recommandé, et pourquoi

> **Le projet a une doctrine explicite (v30.1) : instrumenter d'abord, calibrer ensuite.**
> La v31.1 a démontré qu'une intuition forte peut être infirmée par la mesure (« le rêve
> cristallise des réflexes d'échec » : faux, il ne calcule que le JEPA).

| Étape | Contenu | Coût | Risque | Mesure préalable |
|---|---|---|---|---|
| **0** | **Télémétrie inter-jalons Δt₁/Δt₂/Δt₃** | très faible | nul | — |
| **1** | Valence : calcul + télémétrie **seules**, aucun consommateur | faible | nul | issue de l'étape 0 |
| **2** | Valence → `importance` du rêve | faible | modéré | distribution de valence de l'étape 1 |
| **3** | Replay orienté (perte acteur au rêve) | **élevé** | **élevé** | effet mesuré de l'étape 2 |
| **4** | Valence → LTP (gravure d'évitement) | moyen | **élevé** | étapes 2-3 stabilisées |
| **5** | Lecture spatiale hors survie (D) | moyen | modéré | — |
| **6** | Liage multimodal (C) | élevé | modéré | étape 5 livrée |

**L'étape 0 est non négociable.** Tout ce document repose sur une déduction *de lecture
de code* — que Δt₃ (déverrouillage → sortie) est le désert. **Ce n'est pas mesuré.** Si
la mesure montre que c'est Δt₂ qui explose (l'agent erre avec la clé en cherchant à
manger), le diagnostic reste valable mais la **priorité change** : ce serait alors le
conflit viscéral qu'il faut traiter en premier, pas la consolidation.

Coût de l'étape 0 : très inférieur à un seul des incréments ci-dessus.

### 5.1. Une intervention concurrente, bien moins chère, à évaluer d'abord

`DetecteurProgresPersonnel` — « ai-je battu mon record de proximité au But ? », générique,
aucune position codée en dur — est **volontairement désactivé sur DoorKey** pour éviter un
double guidage avec `RECOMPENSE_APPROCHE_BUT`.

Or en **Mode Libre**, `RECOMPENSE_APPROCHE_BUT` est justement coupée : **il n'y a plus de
double guidage à craindre, l'exclusion est devenue caduque.** L'activer sur DoorKey en
Mode Libre seulement rendrait le dernier segment récompensé — avec un détecteur qui
existe déjà, **sans nouvelle dimension, sans greffe `.brain`, sans rupture doctrinale**.

> **Recommandation forte : tester cette hypothèse AVANT l'incrément A.** Si elle suffit à
> débloquer le Palier 7, une grande partie de cette version devient facultative pour cet
> objectif (elle resterait justifiée pour l'objectif « mémoire humaine », qui est distinct).

---

## 6. Risques identifiés

### 6.1. 🔴 Valence négative → LTP : le risque majeur

`fortification_dopaminergique` **grave dans `base_weight`** proportionnellement à la
trace d'éligibilité. Une valence négative mal traitée peut :

- graver un évitement *trop* fort (l'agent développe une phobie d'une zone traversée une
  fois par malchance) ;
- ou, pire, **renforcer** le comportement négatif si le signe est mal propagé.

Contraintes : la borne `[0,1]` de `poids_evenement` doit rester intacte, et
`TENEUR_DOPAMINE` doit rester dans `[DOPAMINE_MIN, DOPAMINE_MAX]` via `np.clip` après
**chaque** point de mise à jour. Étape 4 tardive, jamais groupée avec une autre.

### 6.2. 🔴 Perte acteur au rêve : rupture doctrinale + risque de boucle

Rejouer motoriquement risque d'ancrer une politique sur des trajectoires hors-distribution
(le rêve ne rejoue pas l'environnement réel). Le garde-fou naturel — ne rejouer
motoriquement que le **positif fort** — doit être posé dès la conception.

### 6.3. 🟠 Rétrocompatibilité des `.brain` — contrainte dure

Deux cerveaux réels à **280 000** et **480 000 ticks** existent. Règle du projet : **greffe
par recopie, jamais par exclusion**.

- Toute dimension ajoutée au `vecteur_bio` va **EN QUEUE** (contrat append-only partagé
  entre `obtenir_vecteur_bio`, `BusSensoriel.interpreter` et
  `persistance._greffer_vecteur_bio_etendu`).
- `souvenirs_spatiaux` est persisté **brut** (liste de dicts). Ajouter un champ impose une
  **migration au chargement** (valence neutre par défaut pour les souvenirs historiques),
  sur le modèle de `dedupliquer()` en v31.1.
- ⚠️ Leçon v32.0 : **toute validation d'une greffe doit inclure une nuit complète.** Le
  crash de l'optimiseur Adam ne survenait ni au chargement ni pendant la journée, mais à
  la première `executer_nuit`.

### 6.4. 🟠 Renforcement involontaire de l'attracteur homéostatique

Piège déjà identifié : câbler la valence sur « complétion d'une sous-quête intrinsèque »
renforcerait FOOD/WATER/STIM — **l'exact inverse de l'effet recherché.** Les sources de
valence doivent être auditées une par une.

### 6.5. 🟡 Instrumentation obligatoire (leçon v29.1)

Chaque incrément livre dans le **même commit** : compteur remis à zéro dans
`_reinitialiser_buffers_journee`, accumulé dans `traiter_tick`, agrégé dans
`executer_nuit` (ligne de bilan **et** clé W&B, conditionnelle si la mécanique peut être
inactive). Ne jamais créer un compteur journalier via `getattr(etat, "...", 0)` sans
l'ajouter à `_reinitialiser_buffers_journee` (piège `score_vocal_jour` v27.0).

### 6.6. 🟡 Non-régression à graine fixée

Le projet dispose d'une empreinte MD5 de la séquence des 400 actions à graine fixée
(`e5ce5f49e406`, stable depuis la v30.1). Toute étape à effet purement nocturne
(1, 2, 3) doit la **conserver identique**. Une étape qui la change (4, 5, 6) doit le
faire **sciemment**, et démontrer qu'elle fait *mieux*, pas seulement *différemment*.

---

## 7. Fichiers touchés (estimation)

| Fichier | Étapes | Nature |
|---|---|---|
| `src/naulthene/cerveau/noyau.py` | 0-6 | calcul de valence, `importance`, `rever()`, `fortifier_synapses`, compteurs, bilan, clés W&B |
| `src/naulthene/cerveau/persistance.py` | 2, 5, 6 | migration `souvenirs_spatiaux`, greffe `vecteur_bio` |
| `src/naulthene/cerveau/bus_sensoriel.py` | 6 | empreinte perceptive compacte (reste **pur numpy**, n'importe jamais `noyau.py`) |
| `docs/fonctionnement/CHANGELOG.md`, `readme_fr.md` | toutes | mention **expérimental** obligatoire (vit uniquement dans `noyau.py`) |

---

## 8. Arbitrages demandés avant toute implémentation

1. **Objectif prioritaire** : débloquer le Palier 7, ou se rapprocher de la mémoire
   humaine ? Les deux sont légitimes mais ne donnent pas le même premier pas (Palier 7 →
   valence + replay ; mémoire humaine → liage multimodal).
2. **Étape 0 (télémétrie inter-jalons) d'abord ?** Recommandation : **oui**, sans réserve.
3. **§5.1 (`DetecteurProgresPersonnel` en Mode Libre) avant l'incrément A ?**
   Recommandation : **oui** — coût quasi nul, et peut rendre une partie de la version
   facultative.
4. **Perte acteur au rêve (étape 3)** : rupture doctrinale assumée depuis la v8.0 ?
   C'est le choix le plus structurant du document.
5. **Périmètre de la v33.0** : livrer les étapes 0-2 seulement, ou aller jusqu'à 4 ?
   Recommandation : **0-2**, et rouvrir sur données réelles.
6. **§3.3 « all times / real times »** : reformuler en mécanisme, ou classer ?
