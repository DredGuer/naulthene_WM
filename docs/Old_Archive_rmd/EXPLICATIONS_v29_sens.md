# Naulthène v29.0 — Le Bus Sensoriel Multimodal & l'Identité C1/C2 explicite

> 📦 **ARCHIVÉ (v31.1)** — ce document décrit l'état de la **v29.0/v29.1**, dépassé depuis :
> l'odorat suit désormais une atténuation exponentielle (v30.0), le vecteur bio compte 32 dims et
> non 24 (Exo-Sens, v30.0), et la mémoire spatiale a été revue (v31.0/v31.1). Il reste ici parce
> qu'il documente en profondeur des choix **toujours en vigueur** : pourquoi les sens faibles
> restent hors de la cible JEPA (§4), l'identité C1/C2 (§5), la boucle de distillation (§6) et
> les deux options **écartées** (§9).
>
> ➡️ **Pour l'état courant**, voir [explications_readme.md](../explications_readme.md) §15 (résumé
> algorithmique à jour), [CHANGELOG.md](../CHANGELOG.md) et [LANCEMENT.md](../LANCEMENT.md).

Document explicatif complet de la v29.0, rédigé à partir d'une lecture directe du code livré. Pour l'historique commit par commit voir [CHANGELOG.md](../CHANGELOG.md) (entrée `[29.0-experimental]`), pour la narration générale [readme.md](../../readme.md), et pour la note de conception d'origine [Maj_V29_readme.md](Maj_V29_readme.md).

---

## Table des matières

1. [Le problème que cette version résout](#1-le-problème-que-cette-version-résout)
2. [La hiérarchie des 5 sens](#2-la-hiérarchie-des-5-sens)
3. [Le Bus Sensoriel en détail (toucher, odorat, goût)](#3-le-bus-sensoriel-en-détail)
4. [Pourquoi les sens faibles n'entrent PAS dans le bus latent](#4-pourquoi-les-sens-faibles-nentrent-pas-dans-le-bus-latent)
5. [L'identité C1 / C2 explicite](#5-lidentité-c1--c2-explicite)
6. [La boucle de distillation C2 → C1](#6-la-boucle-de-distillation-c2--c1)
7. [JEPA, de l'outil visuel à l'Intuition globale](#7-jepa-de-loutil-visuel-à-lintuition-globale)
8. [Rétrocompatibilité des `.brain`](#8-rétrocompatibilité-des-brain)
9. [Ce qui a été volontairement ÉCARTÉ](#9-ce-qui-a-été-volontairement-écarté)
10. [Validations exécutées](#10-validations-exécutées)
11. [Glossaire des constantes v29.0](#11-glossaire-des-constantes-v290)
12. [Télémétrie des 5 sens (v29.1) & saturation de l'odorat](#12-télémétrie-des-5-sens-v291--saturation-de-lodorat)

---

## 1. Le problème que cette version résout

Trois constats, issus de [Maj_V29_readme.md](Maj_V29_readme.md) :

**a) Naulthène était un organisme à deux sens.** Jusqu'en v28.0, l'agent percevait le monde par la vue (`porte_visuelle`, 147 dims) et l'ouïe (`porte_auditive`, 130 dims MFCC) — les deux sens les plus gourmands en calcul. Les trois autres (toucher, odorat, goût) n'existaient nulle part, alors qu'ils sont justement **les moins coûteux** et **les plus directement liés à la survie**. Conséquence concrète : l'agent ne savait qu'il tenait la clé que de façon *indirecte*, en la déduisant de son champ visuel — il n'avait littéralement pas de sens du toucher pour la sentir dans sa main.

**b) La frontière C1/C2 existait, mais n'était pas nommée.** Le code séparait bien le réflexe (`tete_motrice`) de la délibération (`simuler_futur_et_planifier`), mais les deux étaient entrelacés dans le corps de `penser()`, sans frontière explicite. Lire le fichier ne permettait pas de dire *où finit le cerveau automatique et où commence le néo-cortex*.

**c) La distillation C2 → C1 était présentée comme le grand chantier… alors qu'elle existait déjà.** C'est le résultat le plus important de l'audit de cette version : voir §6.

---

## 2. La hiérarchie des 5 sens

Tous les sens ne se valent pas en gourmandise énergétique, mais c'est la **combinaison de leur diversité** qui fait émerger une vraie compréhension du monde — croiser *voir* un objet et *entendre* son bruit crée une information qu'aucun des deux canaux ne portait seul.

| Sens | Gourmandise | Rôle cognitif & vital | Dims | Chemin dans le cerveau | Dans la cible JEPA ? |
|------|-------------|----------------------|------|------------------------|----------------------|
| **1. Vue** | **Extrême** (bande passante massive) | Cartographie spatiale, géométrie, prédiction d'objets | 147 | `porte_visuelle` → `bus_latent` | ✅ oui |
| **2. Ouïe** | **Élevée** (traitement temporel & séquentiel) | Danger dynamique, langage, communication | 130 | `porte_auditive` → `bus_latent` | ✅ oui (tête séparée) |
| **3. Toucher** | **Moyenne** (retour de force) | Proprioception, contact immédiat, objet en main | 4 | `vecteur_bio` → `integrateur_bio` | ❌ non |
| **4. Odorat** | **Faible** (chimie à distance) | Détecter une ressource avant de la voir | 2 | `vecteur_bio` → `integrateur_bio` | ❌ non |
| **5. Goût** | **Faible** (chimie de contact) | Valider une ressource réellement ingérée | 2 | `vecteur_bio` → `integrateur_bio` | ❌ non |

Cette table n'est pas qu'un commentaire : elle est **interrogeable dans le code** via `BusSensoriel.hierarchie_sensorielle()`, une méthode statique en lecture seule (sans effet de bord) destinée à la documentation, à la télémétrie W&B et à l'IRM. Aucune de ses valeurs n'est consommée par `penser()`.

---

## 3. Le Bus Sensoriel en détail

Le nouveau module `src/naulthene/cerveau/bus_sensoriel.py` est l'**Interpréteur des 5 sens**. Deux règles de conception structurent tout le fichier :

- **Pur numpy** — aucun réseau de neurones, aucun tenseur PyTorch.
- **N'importe JAMAIS `noyau.py`** — même discipline que `exocortex/port_c3.py` : pas de cycle d'import, pas de dépendance au cerveau. Le bus lit le monde et rend des nombres ; il ignore totalement qui les consomme.

Il ne calcule **ni la vue ni l'ouïe** : ces deux sens gourmands gardent leur porte synaptique dédiée dans `AGI_Naulthene` et leurs encodeurs existants (`noyau.encoder`, `hemisphere_audio`).

### 3.1 Le toucher (`DIM_TOUCHER = 4`)

```python
[contact_frontal, objet_en_main, orientation_cos, orientation_sin]
```

- **`contact_frontal`** — 1.0 si la case devant l'agent est bloquante. Utilise l'API MiniGrid native **`can_overlap()`** plutôt qu'une liste de types codée en dur (`wall`, `door`…) : c'est l'environnement lui-même qui dit ce qui est franchissable, donc le signal reste juste sur n'importe quelle carte. Hors grille → 1.0 (le bord d'un niveau MiniGrid *est* un mur).
- **`objet_en_main`** — 1.0 si `carrying` est non nul. C'est la proprioception de la main.
- **`orientation_cos` / `orientation_sin`** — l'orientation encodée **sur le cercle** plutôt qu'en entier 0-3 :

$$\theta = \frac{\pi}{2} \cdot \text{agent\_dir}, \qquad \text{toucher}[2{:}4] = (\cos\theta,\ \sin\theta)$$

  Pourquoi : en encodage brut, les directions 3 et 0 sont **voisines dans le monde réel** (un quart de tour) mais distantes de 3 unités pour le réseau. L'encodage circulaire supprime cette discontinuité artificielle.

### 3.2 L'odorat (2 dims)

Intensité de la source de Nourriture / Eau la plus proche, décroissant **linéairement** avec la distance de Manhattan (la même métrique que `DetecteurJalonsDoorKey._distance` et `MemoireEpisodiqueSpatiale`) :

$$\text{odeur} = \max\left(0,\ 1 - \frac{d_{\min}}{\text{PORTEE\_ODORAT}}\right), \qquad \text{PORTEE\_ODORAT} = 4$$

Réutilise la convention déjà posée par `DetecteurRessourcesBiologiques` : **Ball rouge = Nourriture, Ball bleue = Eau**. Aucune position ni aucun niveau codé en dur — l'odorat est *générique* au sens de CLAUDE.md §3b, il fonctionne sur n'importe quelle carte du `PROGRAMME`.

> **Pourquoi une portée aussi courte (4 cases) ?** C'est un signal de survie **grossier** qui oriente avant même de voir, pas une carte. La cartographie précise reste le travail de la vue et de `MemoireEpisodiqueSpatiale` — un odorat à longue portée aurait rendu ces deux mécaniques redondantes.

### 3.3 Le goût (2 dims)

Contrairement aux quatre autres, le goût est une **rémanence**, pas un instantané. C'est le seul état inter-tick du bus :

$$\text{gout}_{t+1} = \text{gout}_t \times \text{DECROISSANCE\_GOUT}, \qquad \text{DECROISSANCE\_GOUT} = 0.85$$

`signaler_consommation("FOOD"/"WATER")` met la trace à 1.0 au moment exact où `BiologicalHomeostasisEngine.consommer_ressource` est appelée, puis elle décroît (~10 ticks de persistance) jusqu'à être coupée sous $10^{-3}$.

La trace est **remise à zéro à chaque épisode** (`reinitialiser_episode`) — contrairement aux jauges du moteur homéostatique, qui traversent les épisodes parce qu'elles modélisent un métabolisme continu. Un goût, lui, est lié à une bouchée précise, pas à un état vital.

### 3.4 Dégradation gracieuse

Exactement le même contrat que les détecteurs génériques §3b de `noyau.py` : si `_MINIGRID_OK` est faux ou si une exception d'API survient, le bus se désactive **définitivement** après **un** avertissement et renvoie des zéros. Jamais de crash de l'entraînement, jamais de changement du chemin de gradient.

---

## 4. Pourquoi les sens faibles n'entrent PAS dans le bus latent

C'est **la décision de conception la plus structurante** de cette version, et elle mérite d'être comprise.

Deux câblages étaient possibles :

| | Option retenue ✅ | Option écartée |
|---|---|---|
| **Câblage** | Queue du `vecteur_bio` → `integrateur_bio` | Nouvelle `porte_tactile` sommée dans `bus_latent` |
| **Symétrie** | Moins symétrique avec vue/ouïe | Plus symétrique |
| **Cible JEPA** | Les sens faibles en sont **exclus** | Les sens faibles y **entrent** |
| **Risque** | Faible | Perturbe un modèle du monde entraîné sur 300+ jours |

Le point décisif est la **cible JEPA**. `perte_jepa` compare toujours le bus prédit au bus réel de la **vision seule** :

```python
with torch.no_grad():
    bus_reel_vision = F.relu(self.porte_visuelle(obs_suivante))
perte = F.mse_loss(attente, bus_reel_vision)
```

Si le toucher et la chimie étaient sommés dans `bus_latent`, ils entreraient mécaniquement dans ce que le modèle du monde doit prédire. Trois nouveaux canaux bruités viendraient perturber une physique visuelle déjà apprise sur des centaines de jours — pour un gain nul, puisque prédire l'odeur future n'est pas l'objet du JEPA.

En entrant par `integrateur_bio`, les sens faibles arrivent **juste avant la décision** : ils informent le choix de l'action sans jamais toucher au modèle du monde.

> **Règle à retenir pour la suite** (inscrite dans CLAUDE.md) : toute nouvelle dimension du `vecteur_bio` s'ajoute **EN QUEUE**, jamais au milieu. L'ordre de concaténation est un **contrat** partagé entre `obtenir_vecteur_bio`, `BusSensoriel.interpreter` et `persistance._greffer_vecteur_bio_etendu` — une insertion au milieu décalerait silencieusement tous les acquis d'un `.brain` existant.

### Composition finale du `vecteur_bio` (24 dims)

```
[0:3]    jauges      satiété / hydratation / stimulation        (v18.0)
[3:6]    quête       one-hot FOOD / WATER / STIM                (v18.0)
[6:8]    rappel      distance normalisée + fraîcheur du souvenir (v20.0)
[8:16]   quête vocale formants cibles de la leçon, ou [0]*8     (v22.1)
[16:20]  TOUCHER     contact, objet en main, orient. cos/sin    ← v29.0
[20:24]  CHIMIE      odorat food/water + goût food/water        ← v29.0
```

---

## 5. L'identité C1 / C2 explicite

`penser()` se réduit désormais à l'**arbitrage**, et la frontière est encapsulée dans deux méthodes nommées.

```
                 [ LES 5 SENS ]
                        │
                        ▼
   ┌────────────────────────────────────────────────┐
   │ C1 — _executer_c1_reflexe()      (léger, ~0 €) │
   │  1. Compression des 5 sens → bus_latent        │
   │  2. Lecture épisodique (contexte de l'épisode) │
   │  3. Intégration viscérale → pensee_bio         │
   │  4. Réflexe moteur (tete_motrice), latence 0   │
   └───────────┬──────────────────────────▲─────────┘
               │ pensee_bio               │ distillation
               │ (état DÉJÀ compressé)    │ C2 ──► C1 (nuit)
               ▼                          │
   ┌───────────┴──────────────────────────┴─────────┐
   │ C2 — _solliciter_c2_neocortex()  (lourd, cher) │
   │  • JEPA : prédit Z(t+1) — l'Intuition          │
   │  • Rollout mental multi-échelle (t+1, t+3, t+7)│
   └────────────────────────────────────────────────┘
                        │
                        ▼
   logits_finaux = logits_instinct + valeurs_simulees × force_planification
```

**Le point clé** : C2 ne reçoit **jamais** autre chose que `pensee_bio`, l'état déjà compressé par C1 — jamais les pixels bruts, jamais le MFCC, jamais l'environnement. C'est exactement le schéma de la note de conception : *« C2 reçoit l'état DÉJÀ COMPRESSÉ par C1 »*.

### Restructuration pure : zéro changement de comportement

Décision utilisateur explicite. C2 continue d'être sollicité **à chaque tick**, et la fusion `logits_instinct + valeurs_simulees * force_planification` est **inchangée depuis la v13.0**. Le comportement d'un cerveau existant est bit-identique à la v28.0 ; seule la lisibilité change.

---

## 6. La boucle de distillation C2 → C1

La note de conception la présente comme *« la pièce maîtresse du système »*. **L'audit de cette version conclut qu'elle était déjà entièrement implémentée** — et c'est le résultat le plus important de la v29.0 : le bon geste d'ingénierie a été de **ne rien écrire**, plutôt que d'ajouter un second mécanisme concurrent à celui qui tournait déjà.

C'est le cycle de vie de `NaultheneLinearSynaptique`, en place depuis les toutes premières versions :

```
   [ EXPÉRIENCE DIURNE — C2 aux commandes ]
   • Actions complexes guidées par la planification / JEPA
   • Le gradient du jour s'accumule dans annexe_weight
                        │
                        ▼
   [ CONSOLIDATION NOCTURNE — le Rêve ]
   1. Rejeu des souvenirs à haute importance (rêve adaptatif)
   2. Transfert : base_weight += annexe_weight     (C2 ──► C1)
   3. Érosion sélective + Cristallisation Souple (v26.0)
                        │
                        ▼
   [ RÉFLEXE ANCRÉ DANS C1 ]
   • La fois suivante, C1 exécute via base_weight, quasi gratuitement
   • C2 est libéré pour de NOUVEAUX apprentissages
```

Correspondance terme à terme entre la note de conception et le code existant :

| Note de conception | Réalisation dans le code | Depuis |
|---|---|---|
| « Accumulation du gradient diurne » | `annexe_weight` (poids annexe appris dans la journée) | v7.0 |
| « Rejeu des souvenirs à haute importance » | `rever()`, échantillonnage pondéré par importance | v8.0 |
| « Transfert `base_weight += annexe_weight` » | `NaultheneLinearSynaptique.cycle_sommeil()` | v7.0 |
| « Érosion sélective / myélinisation » | `myeline_M`, `lambda_erosion` modulé par la plasticité | v7.0 |
| « Cristallisation » | Cristallisation Souple : `myeline_cumul` + cliquet `cristallisee` | v26.0 |
| « C2 n'a plus besoin d'être sollicité » | Réflexe joué par `tete_motrice` depuis `base_weight` consolidé | v7.0 |

C'est exactement le mécanisme d'apprendre à conduire : au début C2 consomme une énergie monstre à chaque geste ; quelques mois plus tard C1 conduit sans qu'on ait à y penser. Les synapses sollicitées de façon répétée par C2 voient leur trace de myéline se consolider jusqu'à être **définitivement figées** dans `base_weight`, libérant le néo-cortex.

---

## 7. JEPA, de l'outil visuel à l'Intuition globale

JEPA n'est pas seulement un filtre pour la vue — c'est **l'architecture de l'Intuition** :

- **Pour la vue** : il prédit à quoi ressemblera l'espace latent de la scène suivante **sans calculer chaque pixel**. C'est la physique de l'environnement.
- **Au niveau global** : c'est la capacité à anticiper *« ce qui devrait arriver »* dans l'espace compressé où les sens se rejoignent (`bus_latent` somme déjà vue + ouïe).
- **L'émergence de la surprise** : quand la perception ne correspond pas à la prédiction, l'écart (erreur JEPA) est un signal de **surprise** qui, dans le code, alimente déjà trois mécaniques distinctes — la stimulation du moteur homéostatique (`step_metabolisme`), une sous-quête de curiosité (`DetecteurCuriositeJEPA`), et le thermostat de neurogenèse. La surprise « réveille » donc bien C2 sur l'anomalie, via des canaux qui existaient déjà.

---

## 8. Rétrocompatibilité des `.brain`

C'était **le principal risque technique** de cette version.

Étendre `DIM_VECTEUR_BIO` de 16 à 24 change la **forme** de `integrateur_bio` : son entrée passe de `dim_bus + 16` à `dim_bus + 24` colonnes. Or `load_state_dict(strict=False)` ne gère que les clés *absentes* — il lève une `RuntimeError` sur un mismatch de forme d'une clé *présente des deux côtés*.

Le filtre historique traitait ce cas en **excluant** la couche, qui renaissait à neuf. C'est précisément le symptôme du bug **v24.0-fix4** : `integrateur_bio` étant la couche qui réinjecte la quête vocale vers `tete_vocale`, sa réinitialisation systématique produisait une **bouche silencieuse dans l'Arène**. Inacceptable sur un `.brain` portant des centaines de jours de vécu.

**Solution — `_greffer_vecteur_bio_etendu()`**, appelée **en amont** du filtre :

```
ancien .brain (dim_bus + 16)          nouveau tenseur (dim_bus + 24)
┌──────────────────────────┐          ┌──────────────────────────┬────────┐
│ poids appris (préservés) │  ──────► │ poids appris (bit à bit) │ Xavier │
└──────────────────────────┘          └──────────────────────────┴────────┘
                                                                   ▲
                                          8 nouvelles dims, init atténuée
```

- Chaque buffer (`base_weight`, `myeline_M`, `trace_activation`, `myeline_cumul`, `cristallisee`) est recopié à l'identique sur ses colonnes existantes.
- `annexe_weight` repart de zéro — comme `cycle_sommeil` le fait déjà chaque nuit, et parce qu'il n'a de sens que pour la journée en cours.
- Les 8 nouvelles colonnes gardent leur initialisation Xavier atténuée — exactement la sémantique de `NaultheneLinearSynaptique.agrandir()`.
- Un `.brain` **déjà en v29.0** traverse la fonction **sans aucune modification**.
- Garde-fous : la greffe ne s'applique que si le nombre de lignes correspond et si la largeur du checkpoint est cohérente avec `dim_bus`. Tout autre écart retombe sur le filtre d'exclusion, conservé en **trappe de secours**.

L'agent se réveille donc avec **tous ses acquis**, et découvre simplement qu'il a désormais un toucher, un odorat et un goût — encore muets.

> **Règle générale du projet** (inscrite dans CLAUDE.md) : **greffe par recopie, jamais par exclusion**. Les deux greffes existantes — `_greffer_action_supplementaire` (7→8 actions, v28.0) et `_greffer_vecteur_bio_etendu` (vecteur bio 16→24, v29.0) — sont le modèle à suivre.

---

## 9. Ce qui a été volontairement ÉCARTÉ

Deux options crédibles ont été explicitement rejetées. Les documenter évite qu'elles soient réintroduites par inadvertance plus tard.

### 9.1 Le court-circuit conditionnel de C2

La note de conception dit *« C2 s'active uniquement sur demande de C1 »*. L'implémentation littérale aurait été :

```python
# ÉCARTÉ — ne pas réintroduire sans demande explicite
if _c1_hesite(logits_c1) or erreur_jepa > SEUIL:
    valeurs = self._solliciter_c2_neocortex(...)
else:
    valeurs = 0     # C2 dort, tick quasi gratuit
```

**Pourquoi c'est écarté** : cela introduit un **déclenchement sur seuil codé en dur dans le chemin de décision** — exactement de la même nature que ce que le projet s'interdit déjà pour l'appel à C3 (« interroger C3 est un choix appris par REINFORCE, jamais un `if erreur > seuil` »). Ce serait incohérent d'interdire le seuil pour C3 et de l'accepter pour C2. Cela changerait en outre le comportement de tous les cerveaux existants.

Si l'économie d'énergie devient un objectif réel, la voie cohérente avec la philosophie du projet serait de faire de « solliciter C2 » **une action apprise**, comme `ACTION_DEMANDER` l'est pour C3 — pas un seuil.

### 9.2 Une porte tactile dans le bus latent

Voir §4 : plus symétrique avec vue/ouïe, mais fait entrer trois canaux bruités dans la cible JEPA d'un modèle du monde déjà entraîné.

---

## 10. Validations exécutées

Le projet n'a ni linter ni suite de tests automatisés (voir CLAUDE.md) — toutes les vérifications ci-dessous ont été exécutées manuellement avant livraison.

| # | Vérification | Résultat |
|---|--------------|----------|
| 1 | `DIM_VECTEUR_BIO = 24`, `integrateur_bio` en `(16, 40)` sur cerveau neuf | ✅ |
| 2 | `penser()` renvoie 8 logits ; `ACTION_DEMANDER` masquée à `-inf` sans plug (**invariant v28.0**) | ✅ |
| 3 | **Greffe d'un `.brain` simulé pré-v29** : 32 premières colonnes recopiées **bit à bit** (`torch.equal` = True) sur tous les buffers, **y compris le booléen `cristallisee`** | ✅ |
| 4 | `annexe_weight` remis à zéro ; 8 nouvelles colonnes non nulles ; `load_state_dict` sans clé manquante ni inattendue | ✅ |
| 5 | Un `.brain` déjà v29.0 traverse la greffe **sans modification** | ✅ |
| 6 | **400 ticks** sur `DoorKey-5x5` : contact = 1.0 face à un mur, odorat = 0.25 pour une eau à 3 cases, goût 1.0 → 0.142 en 12 ticks | ✅ |
| 7 | **Nuit complète** puis **neurogenèse** : `integrateur_bio` (16, 40) → (32, 56) — segment bio fixe à 24 pendant que `dim_bus` double (**invariant `segments_in`**) | ✅ |
| 8 | 60 ticks post-neurogenèse | ✅ |
| 9 | **Round-trip** `sauvegarder()` → `charger_ou_naitre()` : `integrateur_bio` identique ; 30 ticks après résurrection | ✅ |
| 10 | Chemin `mode_perception="vocal_isole"` (sans env MiniGrid, 8 dims neutres) | ✅ |
| 11 | Chemin MiniGrid + audio simultanés | ✅ |
| 12 | **Cascade C3 v28.0 intacte** : 150 ticks sans plug, puis 60 ticks avec `PlugSimule` enregistré | ✅ |
| 13 | Import de tous les modules (Cuve, salles de classe, instruments, persistance) | ✅ |

---

## 11. Glossaire des constantes v29.0

| Constante | Valeur | Rôle |
|-----------|--------|------|
| `DIM_VECTEUR_BIO` | **24** (était 16) | Largeur du vecteur viscéral consommé par `integrateur_bio`. Ne grandit **jamais** avec la neurogenèse |
| `DIM_TOUCHER` | 4 | Contact frontal, objet en main, orientation cos/sin |
| `DIM_CHIMIE` | 4 | Odorat (nourriture, eau) + goût (nourriture, eau) |
| `PORTEE_ODORAT` | 4.0 | Portée de l'odorat en cases (distance de Manhattan) ; 0 au-delà |
| `DECROISSANCE_GOUT` | 0.85 | Facteur de décroissance par tick de la trace gustative (~10 ticks) |
| `COULEUR_NOURRITURE` | `"red"` | Convention héritée de `DetecteurRessourcesBiologiques` (Ball rouge) |
| `COULEUR_EAU` | `"blue"` | Convention héritée de `DetecteurRessourcesBiologiques` (Ball bleue) |

---

## 12. Télémétrie des 5 sens (v29.1) & saturation de l'odorat

### 12.1 Le trou de la v29.0

La v29.0 câblait les 5 sens **dans la décision** (l'agent les utilise réellement), mais n'en instrumentait **aucun** : pas de clé W&B, pas de ligne au bilan de nuit, pas de compteur journalier. Les 13 validations du §10 étaient des tests **ponctuels** — lecture des signaux à un instant T — pas du **suivi**.

Distinction importante : ces tests prouvaient que la mécanique fonctionne, pas qu'on pourrait l'**observer** sur la durée. Sur un run de 300 jours, il aurait été impossible de répondre à « l'odorat a-t-il jamais servi à quelque chose ? », et une désactivation silencieuse du bus (§3.4) n'aurait laissé qu'un unique avertissement console, noyé dans des milliers de lignes.

Un audit systématique des 21 compteurs `*_jour` de `EtatCognitif` a confirmé que **tous les compteurs antérieurs étaient correctement loggés**, y compris la télémétrie C3 de la v28.0 : l'écart était strictement limité à la v29.0.

### 12.2 Les 7 métriques ajoutées

| Clé W&B | Mesure |
|---------|--------|
| `Sens_Bus_Actif` | **Santé** — 0 si le bus s'est désactivé en vol |
| `Sens_Toucher_Contact_Ratio` | Part des ticks au contact d'un obstacle |
| `Sens_Toucher_Portage_Ratio` | Part des ticks avec un objet en main (la clé, sur DoorKey) |
| `Sens_Odorat_Moyen` | Intensité moyenne (nourriture + eau) |
| `Sens_Odorat_Max` | Pic d'intensité de la journée |
| `Sens_Odorat_Ticks_Actifs_Ratio` | Part des ticks avec au moins une odeur perçue |
| `Sens_Gout_Ticks_Actifs` | Ticks avec une trace gustative rémanente |

Plus une ligne au bilan de nuit :

```
  ├─ Les 5 Sens     : ✋ Contact 28.5% | 🔑 Portage 20.5% | 👃 Odorat 96.0% des ticks (max 1.50) | 👅 Goût 75 tick(s)
```

Trois garde-fous de conception :

- **Purement observationnel** — ces compteurs ne sont jamais relus par la décision, le gradient ou la dopamine.
- **Absents du log si `ticks_sensoriels_jour == 0`** (mode `vocal_isole` pur) : pas de ligne trompeuse, pas de division par zéro. Même logique conditionnelle que le bloc C3 de la v28.0.
- **Remis à zéro dans `_reinitialiser_buffers_journee`** — le piège exact du bug `score_vocal_jour` de la v27.0, où une « moyenne du jour » était en réalité cumulée depuis la naissance du cerveau.

### 12.3 Le diagnostic immédiat : l'odorat sature

Dès le premier jour instrumenté, la télémétrie a livré un constat que les tests ponctuels ne pouvaient pas donner : `Sens_Odorat_Ticks_Actifs_Ratio = 0.96` et `Sens_Odorat_Max = 1.50` (sur un maximum théorique de 2.0).

Vérification par calcul de couverture (4 sources, distance de Manhattan, moyenne sur 400 placements aléatoires) — **pourcentage des cases de la carte situées à portée d'au moins une source** :

| Carte | `PORTEE_ODORAT = 4` (actuelle) | portée 2 | portée 1 |
|-------|-------------------------------|----------|----------|
| `Empty-8x8` (intérieur 6×6) | **97.6 %** | 73.3 % | 41.6 % |
| `DoorKey-6x6` (intérieur 4×4) | **100.0 %** | 94.9 % | 71.8 % |
| `MultiRoom-N4-S5` (~13×13) | 56.7 % | 24.5 % | 10.7 % |

Sur les **4 premiers niveaux du `PROGRAMME`** (les plus petits), l'odorat est donc quasi constamment saturé. Or un signal presque toujours actif porte très peu d'information : l'agent ne peut pas s'en servir pour s'orienter, puisqu'il « sent » à peu près partout pareil. Le sens ne redevient discriminant qu'au Doctorat.

C'est un cas d'école du principe rappelé en §2 : ce qui fait émerger la compréhension, ce n'est pas d'*ajouter* un canal, c'est qu'il soit **informatif**.

### 12.4 Pourquoi la constante n'a PAS été changée

`PORTEE_ODORAT` reste à **4.0**. C'est un constat livré, pas un correctif appliqué unilatéralement — le bon réglage dépend de l'intention, et c'est une décision de conception qui appartient à l'auteur du projet :

- **Odorat « ambiance de proximité »** (saturé) : un choix valide si l'intention est un fond permanent signalant « il y a de la ressource dans cette zone ».
- **Odorat « boussole vers la ressource »** : demanderait une portée de 1-2 cases, ou une normalisation par la taille de la carte (`PORTEE_ODORAT` proportionnelle à `grid.width`), pour rester discriminant à tous les niveaux.

La télémétrie v29.1 est précisément l'instrument qui permet de trancher **sur données réelles** plutôt qu'à l'intuition — et de vérifier après coup que le réglage retenu produit bien l'effet voulu.

---

*Document rédigé à partir d'une lecture directe du code livré (`src/naulthene/cerveau/bus_sensoriel.py`, `noyau.py` v29, `persistance.py`) — voir [readme.md](../../readme.md) pour la documentation narrative complète, [CHANGELOG.md](../CHANGELOG.md) pour l'historique commit par commit, et [CLAUDE.md](../../CLAUDE.md) pour les règles de maintenance du projet.*
