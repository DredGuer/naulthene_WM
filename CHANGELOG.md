# Changelog — Naulthène AGI

Historique des évolutions du projet, commit par commit. Voir [readme.md](readme.md) pour la documentation narrative complète et [CLAUDE.md](CLAUDE.md) pour les règles de maintenance de ce fichier.

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

*Note : les entrées v7.0 à v14.0 ont été reconstituées à partir du journal narratif de [readme.md](readme.md) lors de la mise en place initiale de ce changelog (2026-07-22) — les hash de commit réels n'étaient pas disponibles rétroactivement (dépôt git non initialisé jusqu'à cette date). Toute nouvelle entrée à partir de maintenant doit renseigner un hash réel.*
