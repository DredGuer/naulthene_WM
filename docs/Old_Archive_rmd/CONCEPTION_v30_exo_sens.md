# Conception v30.0 — L'Unification & l'Extensibilité (l'Exo-Sens)

> ✅ **Statut : IMPLÉMENTÉE ET VALIDÉE** (2026-08-02, branche `feat/v30-exo-sens`).
> Ce document reste le cadrage d'origine — il conserve la trace des arbitrages, y compris des
> options **écartées** et pourquoi. Pour ce qui a réellement été livré et les validations
> exécutées, voir [CHANGELOG.md](../CHANGELOG.md), entrée `[30.0-experimental]`.
>
> **Deux arbitrages tranchés par l'utilisateur après ce cadrage**, qui remplacent ce qui était
> alors « point ouvert » : l'odorat suit une **atténuation exponentielle** `exp(-0.8·d)` (et non
> une portée relative à la géométrie, qui ne corrigeait pas les cartes 4×4 — voir §2), et le
> chantier 3 retient la **perception continue sans aucun seuil** (voir §4).

La v29.1 a validé la séparation explicite **C1/C2** et les **5 sens physiques**. La v30.0
concrétise le pivot conceptuel : transformer l'Exocortex **C3** d'un « 3ᵉ cerveau » en un
**6ᵉ sens exogène** (l'*Exo-Sens*), et corriger la physique de l'odorat local.

---

## Table des matières

1. [Vision architecturale](#1-vision-architecturale)
2. [Chantier 1 — l'Odorat Dynamique](#2-chantier-1--lodorat-dynamique)
3. [Chantier 2 — le pivot de C3 en 6ᵉ sens](#3-chantier-2--le-pivot-de-c3-en-6e-sens)
4. [Chantier 3 — la Boucle d'Attention Exogène](#4-chantier-3--la-boucle-dattention-exogène)
5. [Décisions déjà tranchées](#5-décisions-déjà-tranchées)
6. [Points ouverts, à trancher avant implémentation](#6-points-ouverts-à-trancher-avant-implémentation)
7. [Feuille de route fichier par fichier](#7-feuille-de-route-fichier-par-fichier)
8. [Invariants à ne pas casser](#8-invariants-à-ne-pas-casser)

---

## 1. Vision architecturale

```
 [ LE MONDE PHYSIQUE ]               [ LE MONDE NUMÉRIQUE / EXOGÈNE ]
 ┌───────────────────┐               ┌──────────────────────────────┐
 │ Vue, Ouïe, Toucher│               │ LLM / RAG, VectorDB, APIs,   │
 │ Odorat, Goût      │               │ capteurs IoT, Web            │
 └─────────┬─────────┘               └──────────────┬───────────────┘
           │ signaux physiques                      │ vecteur contextuel
           ▼                                        ▼
 ┌──────────────────────────────────────────────────────────────────┐
 │ 1. BUS SENSORIEL MULTIMODAL UNIFIÉ (bus_sensoriel.py)            │
 │    • Transduction des 5 sens physiques (odorat DYNAMIQUE)        │
 │    • Transduction du 6ᵉ sens : l'EXO-SENS (prothèse cognitive)   │
 └────────────────────────────────┬─────────────────────────────────┘
                                  │ signal normalisé Z_élec
                                  ▼
 ┌──────────────────────────────────────────────────────────────────┐
 │ 2. C = LE CERVEAU UNIFIÉ (C1 + C2)                               │
 │    • C1 : filtrage, homéostasie, réflexes 0-latence              │
 │    • C2 : modèle du monde JEPA, intuition, planification         │
 └──────────────────────────────────────────────────────────────────┘
```

Le gain conceptuel : l'agent ne subit plus de « schizophrénie » entre plusieurs cerveaux qui
se disputent la décision. C'est **un organisme unique (C1+C2) doté d'une perception augmentée**.

---

## 2. Chantier 1 — l'Odorat Dynamique

**Problème** (diagnostiqué par la télémétrie v29.1, voir
[EXPLICATIONS_v29_sens.md](EXPLICATIONS_v29_sens.md) §12) : `PORTEE_ODORAT = 4` couvre 97,6 % de
`Empty-8x8` et 100 % de `DoorKey-6x6`. L'odorat y est un bruit de fond permanent, donc
quasi dépourvu d'information.

**Correctif** — portée relative à la géométrie de la carte courante :

$$\text{portée} = \max\left(1,\ \left\lfloor \frac{\min(\text{largeur},\ \text{hauteur})}{3} \right\rfloor\right)$$

**Effet attendu** sur les 5 niveaux du `PROGRAMME` — couverture théorique calculée (4 sources,
distance de Manhattan, moyenne sur 600 placements aléatoires) :

| Carte | Intérieur | Portée v29 → couverture | Portée v30 → couverture |
|---|---|---|---|
| `Empty-8x8` (Primaire) | 6×6 | 4 → 97,6 % | **2** → **73,0 %** ✅ |
| `DoorKey-6x6` (Collège) | 4×4 | 4 → 100,0 % | **2** → 95,1 % ⚠️ |
| `Unlock` (Lycée) | 4×4 | 4 → 100,0 % | **2** → 95,1 % ⚠️ |
| `MemoryS7` (Université) | 5×5 | 4 → 99,6 % | **2** → 84,3 % 🟡 |
| `MultiRoom-N4-S5` (Doctorat) | 13×13 | 4 → 56,8 % | **5** → 70,1 % ⚠️ |

> ⚠️ **Deux effets contre-intuitifs à ne pas ignorer.**
>
> **(a) Les cartes 4×4 restent saturées à 95 %.** `DoorKey-6x6` et `Unlock` ont une grille
> intérieure de 4×4 : avec 4 sources, la carte est couverte quoi qu'on fasse. La formule seule
> ne résout PAS le problème là où il a été diagnostiqué (le Collège). Leviers à évaluer sur run
> réel : réduire `NB_SOURCES_FOOD/WATER` (2+2 aujourd'hui) sur les petites cartes, ou accepter
> que l'odorat ne devienne informatif qu'au Doctorat.
>
> **(b) La formule AUGMENTE la portée au Doctorat** (4 → 5), donc la saturation y monte de 57 %
> à 70 % — le seul niveau où l'odorat était déjà discriminant. C'est l'inverse de l'intention.
> Un `min(4, ...)` ou une formule décroissante serait peut-être préférable ; à trancher.
>
> Ne pas conclure au succès sans relire `Sens_Odorat_Ticks_Actifs_Ratio` par niveau.

**Validation** : run court (10 jours) et comparaison de `Sens_Odorat_Ticks_Actifs_Ratio` et
`Sens_Odorat_Moyen` avant/après. La télémétrie v29.1 existe précisément pour cet arbitrage.

---

## 3. Chantier 2 — le pivot de C3 en 6ᵉ sens

C3 cesse d'être un canal de **décision** (une action jouée) pour devenir un canal de
**perception** (une entrée sensorielle).

| | v28/v29 (C3 = 3ᵉ cerveau) | v30 (C3 = 6ᵉ sens) |
|---|---|---|
| Nature | Action apprise (`ACTION_DEMANDER`) | Entrée perceptive continue |
| Déclenchement | L'agent **décide** d'interroger | L'agent **perçoit** en continu |
| Sortie du plug | Biaise/impose l'action suivante | Alimente `Z_exogène` dans le vecteur bio |
| Chemin | `tete_motrice` → `env.step` | `bus_sensoriel` → `integrateur_bio` |

**Mise en œuvre** :

1. `DIM_VECTEUR_BIO` : **24 → 32** (8 dims d'Exo-Sens **en queue**, contrat append-only).
2. Un transducteur `ExoSens` dans `bus_sensoriel.py` accueille un vecteur exogène normalisé.
3. C1 filtre et compresse cette perception augmentée ; C2 l'intègre dans ses rollouts.
4. La greffe `.brain` 24 → 32 réutilise `_greffer_vecteur_bio_etendu` (v29.0), qui est déjà
   écrite de façon générique — **à vérifier, mais elle devrait fonctionner sans modification**.

### Le sort de la 8ᵉ action — décision utilisateur

La spec initiale disait « l'agent conserve ses 7 actions (`num_actions = 7`) ». **Écarté**, car
4 des `.brain` du dépôt sont déjà en 8 actions, dont `naulthene_cursus.brain` (le cerveau actif,
bus 48) :

| `.brain` | `tete_motrice` | actions |
|---|---|---|
| `naulthene_cursus.brain` | (8, 48) | **8** |
| `naulthene_cursus_archive_20260802_1138.brain` | (8, 96) | **8** |
| `naulthene_c3_test.brain` | (8, 16) | **8** |
| `naulthene_parole.brain` | (7, 48) | 7 |
| `naulthene_bb.brain` | (7, 32) | 7 |
| `naulthene_v21.brain` | (7, 48) | 7 |

Revenir à 7 imposerait une greffe **inverse** (8→7) qui **jetterait** des poids appris — la
première fois que le projet retirerait de la matière, en contradiction directe avec la règle
« greffe par recopie, jamais par exclusion » (CLAUDE.md).

**Décision retenue** : `num_actions` **reste à 8**, et `ACTION_DEMANDER` est masquée à `-inf`
**en permanence**, qu'un plug soit branché ou non. Conséquences :

- Aucun `.brain` n'est amputé — les 8 actions sont chargées telles quelles, les cerveaux à 7
  actions continuent d'utiliser la greffe v28 existante.
- La colonne 8 devient **dormante** : jamais échantillonnée, ses poids gelés de fait, mais
  conservés. Réactivable plus tard sans nouvelle greffe si un usage se présente.
- Le comportement moteur redevient strictement équivalent à 7 actions, comme demandé — mais
  par masquage, pas par amputation.

---

## 4. Chantier 3 — la Boucle d'Attention Exogène

Si l'agent doit choisir **quand** « écouter » son Exo-Sens plutôt que de le percevoir en
permanence, la spec propose : quand l'erreur de prédiction JEPA monte, C1 stimule le canal.

> ⚠️ **Point de vigilance à arbitrer explicitement.** Tel qu'énoncé (« quand l'erreur JEPA monte,
> C1 stimule le canal »), c'est un **déclenchement sur seuil codé en dur dans le chemin de
> décision** — exactement ce que le projet s'interdit depuis la v28 pour l'appel à C3, et ce qui
> a fait écarter le court-circuit C1→C2 en v29 (voir CLAUDE.md, garde-fous).
>
> Trois voies cohérentes avec la philosophie du projet, par ordre de préférence :
>
> 1. **Perception continue, sans porte** (le plus simple et le plus « sens ») — un sens ne se
>    déclenche pas, il est toujours là. Le coût est celui du plug, pas de l'architecture.
> 2. **Gain d'attention appris** — une sortie continue du réseau module l'amplitude de
>    `Z_exogène`, apprise par REINFORCE comme le reste. C'est « apprendre à prêter attention »,
>    pas un `if`.
> 3. **Seuil sur l'erreur JEPA** — la proposition initiale. Simple, mais réintroduit exactement
>    le type de règle en dur que les v28/v29 ont refusé deux fois.
>
> **Non tranché.** À décider avant d'écrire ce chantier — les chantiers 1 et 2 n'en dépendent pas
> et peuvent avancer sans.

---

## 5. Décisions déjà tranchées

| Sujet | Décision | Raison |
|---|---|---|
| 8ᵉ action | **`num_actions` reste à 8**, `ACTION_DEMANDER` masquée en permanence | Ne jamais amputer un `.brain` ; 4 cerveaux du dépôt sont déjà à 8 actions |
| Vecteur bio | 24 → 32, **8 dims en queue** | Contrat append-only, greffe par recopie (v29.0) |
| Plug de démonstration | **Local d'abord** (`PlugMemoireAugmentee`), puis backends réels | Ne pas déboguer deux inconnues à la fois |
| Interface des plugs | **Générique** — RAG, Ollama, API IA, IoT… | Voir ci-dessous |

### L'interface générique existe déjà

Le contrat `PlugC3` (v28.0) est déjà exactement ce qu'il faut — trois méthodes, aucune
dépendance externe, aucune connaissance du cerveau :

```python
class PlugC3(ABC):
    nom: str
    def est_disponible(self) -> bool: ...
    def interroger(self, requete: RequeteC3) -> Optional[ReponseC3]: ...
```

`PlugHTTP` (livré en v28.0) est déjà un **backend générique JSON/HTTP** : n'importe quel service
exposant une API HTTP (Ollama, un serveur RAG, une API IA commerciale, une passerelle IoT) s'y
branche par configuration, sans écrire une ligne dans le noyau. La v30.0 n'a donc **pas** à
inventer une nouvelle abstraction : elle doit seulement adapter la **sortie** du contrat, qui
passe d'un avis sur les actions (`ReponseC3.preferences`) à un vecteur perceptif
(`Z_exogène`, 8 dims normalisées).

C'est le seul vrai changement de contrat de ce chantier, et il devra rester rétrocompatible avec
les plugs existants (`PlugNul`, `PlugSimule`, `PlugHTTP`).

---

## 6. Points ouverts, à trancher avant implémentation

1. **Structure exacte des 8 dims de `Z_exogène`** — quelle sémantique par dimension ? Un
   embedding brut tronqué à 8 dims est peu lisible ; un vecteur structuré (pertinence,
   confiance, fraîcheur, 5 dims de contenu) serait interprétable en télémétrie.
2. **Normalisation** — les 5 sens physiques sont bornés dans `[0,1]` (ou `[-1,1]` pour
   l'orientation). L'Exo-Sens doit suivre la même discipline, sans quoi il dominera
   `integrateur_bio` par simple échelle.
3. **Absence de plug** — l'invariant v28 doit tenir : sans plug, `Z_exogène` est un vecteur nul
   et le comportement reste identique à la v29.1. À valider explicitement.
4. **Latence** — un plug HTTP lent (Ollama : 100 ms à 30 s) ne peut pas bloquer un tick. Le
   signal exogène devra probablement être mis en cache et rafraîchi de façon asynchrone, pas lu
   à chaque tick — sinon un run de 400 ticks/jour devient impraticable.
5. **Chantier 3** — voir l'encadré du §4 (perception continue / gain appris / seuil).
6. **Coût de l'Exo-Sens dans le métabolisme** — les 5 sens physiques n'ont pas de coût explicite,
   mais l'Exo-Sens en a un réel (réseau, calcul). Faut-il l'intégrer à
   `calculer_effort_metabolique` ?
7. **La formule d'odorat dynamique elle-même** (voir §2) — telle qu'énoncée, elle ne corrige pas
   les cartes 4×4 (95 % de saturation persistante) et *aggrave* le Doctorat (57 % → 70 %). Trois
   pistes à arbitrer : plafonner (`min(4, ...)`), réduire le nombre de sources sur petites
   cartes, ou viser directement une cible de couverture (ex. ajuster la portée pour rester sous
   ~60 % quel que soit le niveau).

---

## 7. Feuille de route fichier par fichier

| Fichier | Travail |
|---|---|
| `src/naulthene/cerveau/bus_sensoriel.py` | Odorat dynamique (portée relative à `env.width`/`env.height`) ; transducteur `ExoSens` (8 dims normalisées) ; étendre `hierarchie_sensorielle()` au 6ᵉ sens |
| `src/naulthene/cerveau/noyau.py` | `DIM_VECTEUR_BIO` 24 → 32 ; `obtenir_vecteur_bio(..., signaux_exogenes=None)` ; masquage permanent de `ACTION_DEMANDER` ; télémétrie `Sens_Exo_*` (dans le **même** commit, cf. garde-fou v29.1) |
| `src/naulthene/cerveau/persistance.py` | Vérifier que `_greffer_vecteur_bio_etendu` gère 24 → 32 sans modification (elle est écrite de façon générique — à confirmer par test) |
| `src/naulthene/exocortex/port_c3.py` | Faire évoluer `ReponseC3` pour porter un vecteur perceptif, en restant rétrocompatible avec les 3 plugs existants |
| `src/naulthene/exocortex/plugs/` | `PlugMemoireAugmentee` (local, déterministe) ; vérifier que `PlugHTTP` couvre bien Ollama/RAG/API par simple configuration |
| `docs/` | `CHANGELOG.md`, `readme.md`, `LANCEMENT.md`, `Parcourt_readme.md`, `explications_readme.md`, et ce document |

### Ordre d'exécution

1. **Odorat dynamique** + validation W&B sur 10 jours (indépendant du reste, gain immédiat).
2. **Spécifier `Z_exogène`** (les 8 dims, leur sémantique, leur normalisation).
3. **Greffe 24 → 32** dans `noyau.py` + `persistance.py`, avec les mêmes validations qu'en v29.0
   (recopie bit à bit, neurogenèse, round-trip, non-régression).
4. **`PlugMemoireAugmentee`** pour observer la digestion du signal par C1/C2, puis les backends
   réels via `PlugHTTP`.

---

## 8. Invariants à ne pas casser

Repris de CLAUDE.md — ce sont les règles que les v28 et v29 ont établies et défendues :

- **Aucun plug ⇒ comportement identique.** Sans greffon branché, l'agent doit se comporter
  exactement comme en v29.1.
- **Greffe par recopie, jamais par exclusion.** Aucun `.brain` ne perd de poids appris.
- **Dimensions du vecteur bio toujours ajoutées EN QUEUE**, jamais insérées au milieu.
- **Les sens faibles restent hors de la cible JEPA.** L'Exo-Sens passe par `integrateur_bio`,
  jamais sommé dans `bus_latent` — un canal externe bruité ne doit pas polluer le modèle du monde.
- **Pas de déclenchement sur seuil codé en dur** dans le chemin de décision (voir §4).
- **Toute mécanique observable est instrumentée dans le même commit** (leçon v29.1).
- **`PortC3` capture TOUTE exception d'un plug** — jamais de fuite vers le noyau.

---

*Document de cadrage rédigé à l'ouverture de la branche `feat/v30-exo-sens`, à partir de la
spécification utilisateur et d'une lecture directe du code v29.1. Voir
[EXPLICATIONS_v29_sens.md](EXPLICATIONS_v29_sens.md) pour l'état livré dont part cette version.*
