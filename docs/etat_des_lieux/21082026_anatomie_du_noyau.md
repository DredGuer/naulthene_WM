# Anatomie du noyau — le code génétique des cerveaux Naulthène

**Photo horodatée du 21/08/2026.** Ce document est une **photo à un instant donné** : il ne
sera pas mis à jour, il sera **remplacé** par une photo ultérieure. C'est ce qui permet de
comparer deux dates. État du fichier : `src/naulthene/cerveau/noyau.py` à la v41.31.

> ⚠️ **Non normatif.** Pour l'état courant faisant autorité, voir
> [`docs/fonctionnement/CHANGELOG.md`](../fonctionnement/CHANGELOG.md).

---

## 0. Le fichier en chiffres

| | |
|---|---|
| lignes | **11 144** |
| taille | **688 Ko** |
| classes | **16** |
| fonctions de module | **43** |
| méthodes | **120** |
| **code** | **5 500 lignes** |
| **commentaires** | **4 675 lignes — 41 %** |
| lignes vides | 969 |

**Deux lignes sur cinq sont du commentaire.** Ce n'est pas de la verbosité : le fichier porte
**137 ⚠️**, **43 🔴**, **53 occurrences de « Mesuré »** et **402 références à une version
v41.x**. Chaque invariant y est accompagné de la mesure qui l'a produit et, souvent, du bug
qu'il corrige. Le fichier est autant un **carnet de recherche** qu'un programme — c'est
délibéré : la connaissance du projet est majoritairement dans les commentaires, pas dans les
docs.

### Poids des classes

| classe | lignes | rôle |
|---|---|---|
| `EtatCognitif` | **4 622** | le contexte d'un run (buffers, compteurs, sous-modules) |
| `ChronometreJalonsDoorKey` | 1 975 | chronométrie du cursus DoorKey |
| `AGI_Naulthene` | **1 401** | **le cerveau** (`nn.Module`) |
| `BiologicalHomeostasisEngine` | **1 012** | **le corps** (métabolisme, douleur, énergie) |
| `MemoireEpisodiqueSpatiale` | 586 | repères, abstraction par récurrence |
| `NaultheneLinearSynaptique` | 443 | **la couche unique** (plasticité jour/nuit) |
| `DetecteurRessourcesBiologiques` | 214 | le monde nourricier |
| `ModuleAcceptationAbnegation` | 163 | patience, trait d'endurance |
| `LecteurCaseFrontale` | 154 | toucher |
| 7 autres | 40–115 | détecteurs, thermostat, curiosité, sursaut |

---

## 1. L'anatomie — 12 couches, 55 552 paramètres

**Toutes les couches sont du même type** (`NaultheneLinearSynaptique`). C'est la thèse
d'unification faite code : une seule règle de plasticité gouverne l'œil, l'oreille, la mémoire
et la décision.

| couche | forme | params | rôle |
|---|---|---|---|
| `porte_visuelle` | 147→64 | 9 408 | œil |
| `porte_auditive` | 130→64 | 8 320 | oreille |
| `hippocampe` | 128→64 | 8 192 | mémoire de travail |
| `fusion_memoire` | 128→64 | 8 192 | contexte épisodique |
| `integrateur_bio` | **105→64** | 6 720 | 5 sens + viscéral |
| `generateur_attente` | 72→64 | 4 608 | JEPA visuel |
| `generateur_attente_audio` | 72→64 | 4 608 | JEPA auditif |
| `analyseur` | 64→64 | 4 096 | tronc |
| `tete_motrice` | 64→8 | 512 | **C1 — le réflexe** |
| `tete_vocale` | 64→8 | 512 | la bouche |
| `tete_requete` | 64→5 | 320 | C3 ⚠️ **mort au runtime** |
| `cortex_prefrontal` | 64→1 | **64** | **C2 — la délibération** |
| **TOTAL** | | **55 552** | 217 Ko fp32 |

### 🔴 Le compte publié est faux

Les deux README annoncent **55 232**. Le vrai chiffre est **55 552**, mesuré par
`sum(p.numel() for p in agent.parameters())`.

**Cause** : la thermoception (v41.11) a ajouté 2 dimensions au vecteur bio, qui est passé de
36 à **41**. `integrateur_bio` fait donc **105→64** et non 100→64 : **+320 paramètres**.
Le compte n'a pas été refait depuis. ⚠️ `CLAUDE.md` impose de **recompter réellement, jamais
estimer** — la règle existait, elle n'a pas été appliquée.

### Ce que révèle la répartition

**C2 pèse 64 paramètres sur 55 552 — 0,1 % du cerveau.** Toute la délibération tient dans une
projection 64→1. À rapprocher du résultat d'ablation (« couper C2 ne change le score de 0,0
point sur les 6 niveaux ») : ce n'est peut-être pas que C2 soit inutile, c'est qu'il est
**minuscule**.

À l'inverse, **l'hémisphère audio pèse 13 440 paramètres (24 %)** pour une faculté qui ne sert
sur aucun niveau du cursus MiniGrid.

---

## 2. Le chemin de l'information

```
   vision ──┐
            ├──►  bus_latent  ──┬──► hippocampe ──► analyseur ──► pensée
   ouïe ────┘     (SOMME)       │    (+ mémoire)                    │
                                │                                   ├──► tete_motrice      C1
 5 sens + viscéral ─────────────┴──► integrateur_bio                ├──► cortex_prefrontal C2
                                                                    └──► generateur_attente JEPA
```

**Le bus est une SOMME, pas une concaténation.** C'est ce qui rend l'ajout d'un sens
*additif* : une modalité de plus est une projection de plus dans le même espace, pas une
dimension de plus à câbler partout.

⚠️ **Défaut connu, non corrigé** (v39.0) : `porte_auditive` est sans biais, donc
`relu(porte_auditive(zeros)) = 0` **exactement**. Un **silence parfait** et une **oreille
absente** sont mathématiquement indiscernables. Le lever exige un bit de présence dans le
vecteur bio — donc une dimension de plus en queue et une greffe `persistance`.

### L'arbitrage C1 / C2

```python
logits_final = (c1_logits × gain_c1) + (c2_values × force_planification)
```

C2 est consulté **à chaque tick**, sans seuil ni court-circuit — un choix refusé quatre fois
par le projet, parce qu'un seuil dans le chemin de décision est une règle en dur déguisée en
mécanisme. C2 ne reçoit jamais que l'état **déjà compressé par C1** (`pensee_bio`) : jamais
l'observation brute, jamais l'environnement.

---

## 3. Le vecteur bio — 41 dimensions, un contrat d'ordre

| tranche | dims | ajoutée en |
|---|---|---|
| viscéral (satiété, hydratation, stimulation, énergie…) | 19 | v18–v41.2 |
| toucher | 4 | v29.0 |
| chimie (odorat + goût) | 4 | v29.0 |
| **exo-sens (C3)** | **8** | v30.0 ⚠️ **dormant** |
| Δodorat (clinotaxie) | 2 | v32.0 |
| rappel marquant | 2 | v36.0 |
| **thermoception** | **2** | v41.11 |
| **total** | **41** | |

⚠️ **Toute nouvelle dimension s'ajoute EN QUEUE, jamais au milieu.** `persistance` recopie les
N premières colonnes d'un ancien `.brain` : une insertion au milieu décalerait **silencieusement**
tous les acquis. C'est un contrat partagé entre `obtenir_vecteur_bio`, `BusSensoriel.interpreter`
et `_greffer_vecteur_bio_etendu`.

⚠️ **8 dimensions sur 41 (20 %) sont l'exo-sens, qui ne reçoit jamais rien** — aucun plug n'est
enregistré. Elles entrent dans `integrateur_bio` à zéro constant.

---

## 4. Les constantes — où en est le dogme

**225 constantes majuscules** dans le fichier. Classement :

| nature | n | verdict |
|---|---|---|
| **bornes déclarées** (commentaire « borne ») | 36 | ✅ légitimes |
| **dérivées** (calcul, pas littéral) | 7 | ✅ |
| **structurelles** (dimensions, index d'action) | 16 | ✅ imposées par MiniGrid/l'archi |
| seuils / plafonds / planchers | 15 | 🟡 examinés ci-dessous |
| **taux, coefficients, poids** | **107** | 🔴 le vrai grain |

Sur **138 littéraux nus** : **67 ont un commentaire justificatif**, **71 n'en ont aucun**.

### Les seuils dans un `if` — vérifiés un par un

Le dogme interdit un seuil **sur le chemin de décision**. Trois seuils apparaissent dans un
`if` ; leur nature réelle :

| seuil | où | verdict |
|---|---|---|
| `SEUIL_CRITIQUE_BIO = 0.35` | `if _energie < …: ticks_energie_basse += 1` | ⚪ **télémétrie seule**, aucune décision |
| `SEUIL_OVERRIDE_C3 = 0.85` | impose l'action si C3 est confiant | ⚪ **branche morte** — `reponse_c3_en_attente` reste `None`, aucun plug n'existe |
| `SEUIL_SAILLANCE_MEMOIRE = 0.05` | filtre d'écriture mémoire | 🟡 hors chemin moteur |
| `SEUIL_APHASIE_NEUROGENESE = 0.05` | déclenche la croissance | 🟡 hors chemin moteur |

> ✅ **Le chemin de décision moteur est effectivement sans seuil.** C'est vérifié ligne à
> ligne, pas supposé.

⚠️ **`SEUIL_CRISTAL = 0.80` n'a jamais été franchi** (myéline réelle max mesurée : **0,0038**).
La Cristallisation Souple v26.0 ne s'est enclenchée sur aucun cerveau du dépôt.

### Les constantes par domaine

**Dopamine (motivation)** — `NEUTRE 5.0` · `MIN 0.001` · `MAX 10.0` · friction `0.01` ·
choc `0.9` · ressort `0.4`

**Métabolisme** — `DEPENSE_ENERGIE_JOUR 2.0` 🔴 *fossile connu* · basal `0.65` ·
rendement `0.9` · marge digestive `1.5` · débit `3.0` · réserve max `3.0` ·
`KAPPA_VIGUEUR 2.0` · plancher vigueur `0.15`

**Monde (biotope)** — fraction de cases `0.35` · marge trouvabilité `2.0` · marge subsistance
`2.0` · **7 + 7 sources** (dérivées de la surface depuis v41.30-fix1) · part d'estomac `0.8`

**Plasticité** — plancher vital `0.001` · fraction norme `0.10` · `SEUIL_CRISTAL 0.80` ⚠️ ·
rêve min `0.0001` · plage rêve max `0.60`

**Patience** — `PATIENCE_MIN 50` · plafond hors monde `400` (le vrai plafond vient de
`max_steps`) · inertie du trait `0.02` · extension sursaut `50`

**Douleur** — demi-vie brûlure `60.0` · demi-vie choc `5.0` · capacité d'évacuation `0.40` ·
seuil de nociception plancher `0.12`

---

## 5. Le cursus — 15 niveaux

| # | palier | environnement |
|---|---|---|
| 0 | Nourrisson (Premiers pas) | `Empty-5x5` |
| 1 | Éveil (Départ aléatoire) | `Empty-Random-6x6` |
| 2 | Maternelle (Longue distance) | `Empty-8x8` |
| **3** | **Primaire 1 (Contourner)** | **`SimpleCrossingS9N1`** ⬅️ **le mur** |
| 4 | Primaire 2 (Éviter le danger) | `LavaGapS5` |
| 5 | Primaire 3 (Ramasser) | `Fetch-5x5-N2` |
| 6 | Collège 1 (Viser une porte) | `GoToDoor-6x6` |
| 7–9 | Collège 2/3, Lycée 1 | `DoorKey` 5x5 / 6x6 / 8x8 |
| 10–11 | Lycée 2/3 | `Unlock`, `UnlockPickup` |
| 12 | Université (Mémoire) | `MemoryS7` |
| 13–14 | Doctorat 1/2 | `MultiRoom` N2-S4 / N4-S5 |

**Promotion par OU** : `2 victoires consécutives` **OU** `60 % de maîtrise sur 20 épisodes`
(minimum 10 épisodes). Les deux voies sont nécessaires — la première garantit qu'aucun cerveau
ne régresse en vitesse, la seconde qu'un coup de chance ne suffit pas.

⚠️ **Le principe est qu'une seule compétence change entre deux paliers voisins.** `niveau_actuel`
est un **index** : changer la taille ou l'ordre de la liste rétrograderait silencieusement tous
les `.brain`, d'où le remappage par `env_id` dans `persistance`.

---

## 6. Le génome acquis — ce qui vit dans un `.brain`

Au-delà des poids, **~30 grandeurs** évoluent avec l'individu. Mesure sur **10 cerveaux à
1500 jours** (campagne v41.30, bras DERIVE) :

| grandeur | moyenne | min | max | ce qu'elle dit |
|---|---|---|---|---|
| `rythme_episodes` | **2,712** | 2,38 | 3,10 | épisodes/jour réellement vécus |
| `endurance_duree_reussite` | **84,0 t** | 52,9 | 96,3 | durée moyenne d'une victoire |
| `endurance_duree_echec` | **167,4 t** | 146,6 | 177,8 | durée avant abandon |
| `endurance_capital` | **0,000** | 0,00 | 0,00 | ⬅️ **jamais crédité** |
| `chaleur_habituee` | 0,027 | 0,00 | 0,16 | seuil de douleur propre au vécu |
| `patience_min` | **50,0** | 50 | 50 | ⬅️ plancher, plus de cliquet |
| `jours_depuis_mutation` | **881,7** | 105 | 1389 | dernière neurogenèse |
| `tick_absolu` | 571 206 | 474 329 | 594 421 | vie totale |

### Trois lectures

**1. `endurance_capital = 0,000` sur 10/10 cerveaux.** L'agent réussit en **84 ticks** et
abandonne à **167** — il gagne **2× plus vite** qu'il ne renonce. Le contraste
`(réussite − abandon) / abandon` est donc **négatif**, et le gain de patience ne se déclenche
jamais. C'est le comportement **voulu** (il a déjà assez de patience), mais cela signifie que
la mécanique v41.30 est **inerte en pratique** sur ces cerveaux.

**2. `jours_depuis_mutation = 881,7` en moyenne.** Le cerveau moyen n'a plus grandi depuis
**882 jours sur 1500** — soit **59 % de sa vie**. Sur un cerveau, la dernière neurogenèse date
du jour **111** : il a passé **93 %** de son existence à taille fixe.

**3. Un cerveau sur douze porte `rendement_moyen = 2,66e-136`** (les onze autres : 0 à 32).
Underflow isolé, sans effet visible, mais la neurogenèse de ce cerveau-là est **éteinte de
fait** — le thermostat ne peut plus rien déclencher.

---

## 7. Les mécanismes vivants, par ordre d'apparition dans un tick

1. **`demarrer_journee`** — tirage du niveau (P17), patience du jour, envie de vivre
2. **`traiter_tick`** (l. 8132) — le cœur :
   - lecture des sens → `obtenir_vecteur_bio` (41 dims)
   - `penser()` → C1 puis C2, arbitrage
   - `env.step` → transition, douleur si choc, thermoception
   - `step_metabolisme` → énergie, satiété, hydratation
   - mémorisation si saillant, buffers d'apprentissage
3. **`executer_nuit`** (l. 9361) — la consolidation :
   - `_rafraichir_rythme_metabolique` (v41.30)
   - `apprendre_journee` → acteur-critique **masqué** (v41.31) + JEPA + vocal
   - `rever` → rejeu à porosité adaptative
   - ressort dopaminergique, thermostat de neurogenèse
   - `cycle_sommeil_global` → consolidation, érosion, plancher vital

---

## 8. Ce qui est mort ou dormant

| élément | état | pourquoi c'est conservé |
|---|---|---|
| **Port C3 / exocortex** | ⚪ **mort** — aucun plug, `ACTION_DEMANDER` masquée à `-inf` en permanence | `DIM_EXO` (8) est dans `DIM_VECTEUR_BIO` (41) et `num_actions` = 8 : le retirer casserait **tous** les `.brain` |
| `tete_requete` (320 params) | ⚪ jamais entraînée utilement | idem |
| `SEUIL_OVERRIDE_C3` | ⚪ branche inatteignable | idem |
| `taux_satiete` | 🔴 **variable morte** — rien ne la soustrait depuis v41.2 | rétrocompatibilité `.brain` |
| `SEUIL_CRISTAL = 0.80` | ⚪ jamais franchi (myéline max 0,0038) | ne pas s'appuyer dessus comme protection |
| `DEBIT_DIGESTIF_VECU_ACTIF` | ⚪ inerte depuis v41.31-fix2 | ne pas casser les scripts de campagne |
| **hémisphère audio** (13 440 params, 24 %) | 🟡 actif mais hors cursus MiniGrid | c'est un organe du « cerveau complet », pas un solveur |

---

## 9. Les trois points d'attention

### 🔴 1. Le compte de paramètres publié est faux
55 232 annoncé, **55 552** réel. Vérifiable en une commande — donc coûteux en crédibilité.
**Corrigé dans les deux README le 21/08/2026.**

### 🟡 2. La neurogenèse est quasi éteinte
882 jours en moyenne sans mutation, jusqu'à 1389. Le cerveau atteint une taille et n'en bouge
plus. Cohérent avec le résultat mesuré (« agrandir le cerveau ne change rien sur 3 campagnes »),
mais cela signifie que le thermostat ne joue plus aucun rôle après la première centaine de jours.

### 🟡 3. Le trait d'endurance ne se déclenche jamais
`endurance_capital = 0` sur 10/10. La mécanique v41.30 est correcte mais **inerte** : le monde
ne produit pas la condition qui l'active (réussir plus lentement qu'on n'abandonne).

---

## 10. Ce que ce fichier est vraiment

Un **monolithe assumé** de 11 144 lignes, dont 41 % de commentaires, qui contient à la fois :

- **le cerveau** (`AGI_Naulthene`, 1 401 l.) — 12 couches d'une seule espèce
- **le corps** (`BiologicalHomeostasisEngine`, 1 012 l.) — faim, soif, douleur, énergie
- **le monde** (`DetecteurRessourcesBiologiques`, 214 l.) — le biotope nourricier
- **l'école** (`PROGRAMME` + détecteurs) — 15 paliers
- **le carnet** (4 675 lignes de commentaires) — chaque invariant avec sa mesure

Le vocabulaire est celui du vivant, pas du logiciel : *le Scalpel*, *le tronc cérébral*, *la
Cuve*, *le rêve*, *le sursaut de volonté*. Ce n'est pas décoratif — c'est ce qui rend
l'architecture pensable comme un **organe** plutôt que comme un pipeline.

> **La règle qui structure tout** : une constante ne peut être qu'une **borne** ; une valeur
> doit être **dérivée du vécu de l'agent**. 36 bornes déclarées, 7 dérivations explicites — et
> **107 coefficients** qui n'ont encore ni l'un ni l'autre statut. C'est là que se trouve le
> travail restant.
