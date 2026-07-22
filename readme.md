Voici le **`README.md`** révisé, complété et restructuré en profondeur.

Il intègre la structure de table des matières globale (avec le contexte applicatif/métier et la vision AGI), enrichie de toute l'architecture neuro-mimétique de l'agent **Naulthène AGI** (réservoir dopaminergique, cursus à 7 paliers, mode libre, planification multi-échelle non-linéaire, consolidation nocturne adaptative, détecteurs génériques, pression cinétique et patience adaptative).

---

# 🧠 Naulthène AGI — Architecture & Documentation Technique

> **Agent Cognitif Autonome Hybride (RL + JEPA + Mémoire Épisodique + Bio-Homéostasie)**
> *Un modèle d'apprentissage universel guidé par le développement cognitif, la plasticité neuro-mimétique et le libre arbitre.*

---

## 📋 Table des Matières

1. [Vue d'Ensemble du Projet](https://www.google.com/search?q=%23vue-densemble-du-projet)
2. [Journal des Mises à Jour (Changelog)](https://www.google.com/search?q=%23journal-des-mises-%C3%A0-jour)
3. [Plan d'Action](https://www.google.com/search?q=%23plan-daction)
4. [Nouveautés v15.0 — Planification Non-Linéaire, Pression Cinétique & Patience Adaptative](#nouveautés-v150--planification-non-linéaire-pression-cinétique--patience-adaptative-2026-07-22)
5. [Nouveautés v14.0 — Rêves Adaptatifs & Planification Étendue à 3 Pas](https://www.google.com/search?q=%23nouveaut%C3%A9s-v140---r%C3%AAves-adaptatifs--planification-%C3%A9tendue-%C3%A0-3-pas-2026-07-22)
6. [Nouveautés v13.0 — Décision Autonome & Mode Libre](https://www.google.com/search?q=%23nouveaut%C3%A9s-v130---d%C3%A9cision-autonome--mode-libre-2026-07-22)
7. [Nouveautés v12.0 — Cursus à 7 Paliers & Correctif d'Épisodes](https://www.google.com/search?q=%23nouveaut%C3%A9s-v120---cursus-%C3%A0-7-paliers--correctif-d%C3%A9pisodes-2026-07-22)
8. [Nouveautés v11.0 — Réservoir Dopaminergique V3](https://www.google.com/search?q=%23nouveaut%C3%A9s-v110---r%C3%A9servoir-dopaminergique-v3-2026-07-22)
9. [Nouveautés v10.0-fix1 — Correctif de Stabilité JEPA & Thermostat](https://www.google.com/search?q=%23nouveaut%C3%A9s-v100-fix1---correctif-de-stabilit%C3%A9-jepa--thermostat)
10. [Nouveautés v10.0 — Système 2 & Rollout Mental Vectorisé](https://www.google.com/search?q=%23nouveaut%C3%A9s-v100---syst%C3%A8me-2--rollout-mental-vectoris%C3%A9)
11. [Nouveautés v9.1 — Intégration du Tampon Épisodique (Université)](https://www.google.com/search?q=%23nouveaut%C3%A9s-v91---int%C3%A9gration-du-tampon-%C3%A9pisodique-universit%C3%A9)
12. [Nouveautés v9.0-fix1 — Correctif de la Neurogenèse Bloc par Bloc](https://www.google.com/search?q=%23nouveaut%C3%A9s-v90-fix1---correctif-de-la-neurogen%C3%A8se-bloc-par-bloc)
13. [Nouveautés v9.0 — Cursus Académique Progressif (Primaire à Doctorat)](https://www.google.com/search?q=%23nouveaut%C3%A9s-v90---cursus-acad%C3%A9mique-progressif-primaire-%C3%A0-doctorat)
14. [Nouveautés v8.0 — Alignement Graph-Gradient RL & Rêve Nocturne](https://www.google.com/search?q=%23nouveaut%C3%A9s-v80---alignement-graph-gradient-rl--r%C3%AAve-nocturne)
15. [Nouveautés v7.0 — Phase 7 Initiale (Architecture Hybride Duale)](https://www.google.com/search?q=%23nouveaut%C3%A9s-v70---phase-7-initiale-architecture-hybride-duale)
16. [Architecture Cognitico-Biologique Complète](https://www.google.com/search?q=%23architecture-cognitico-biologique-compl%C3%A8te)
17. [Cursus Académique & Paliers Comportementaux](https://www.google.com/search?q=%23cursus-acad%C3%A9mique--paliers-comportementaux)
18. [Moteur Émotionnel & Réservoir Dopaminergique](https://www.google.com/search?q=%23moteur-%C3%A9motionnel--r%C3%A9servoir-dopaminergique)
19. [Algorithme de Rêve Nocturne Adaptatif](https://www.google.com/search?q=%23algorithme-de-r%C3%AAve-nocturne-adaptatif)
20. [Détecteurs Génériques d'Intention & Quêtes Auto](https://www.google.com/search?q=%23d%C3%A9tecteurs-g%C3%A9n%C3%A9riques-dintention--qu%C3%AAtes-auto)
21. [Pression Cinétique & Patience Adaptative](#pression-cinétique--patience-adaptative)
22. [Stack Technique](https://www.google.com/search?q=%23stack-technique)
23. [Modèle de Données & Métriques W&B](https://www.google.com/search?q=%23mod%C3%A8le-de-donn%C3%A9es--m%C3%A9triques-wb)
24. [Démarrage Rapide](https://www.google.com/search?q=%23d%C3%A9marrage-rapide)
25. [Mise en Production & Monitoring](https://www.google.com/search?q=%23mise-en-production--monitoring)
26. [Configuration](https://www.google.com/search?q=%23configuration)
27. [Troubleshooting & Guide de Dépannage](https://www.google.com/search?q=%23troubleshooting--guide-de-d%C3%A9pannage)

---

## 🎯 Vue d'Ensemble du Projet

**Naulthène AGI** est une tentative de concilier le **Reinforcement Learning (RL)**, la **prédiction spatio-temporelle sous contrainte d'énergie (JEPA - Joint Embedding Predictive Architecture)** et la **neurobiologie computationnelle**.

L'agent évolue à travers un cursus scolaire modélisé sous forme d'environnements à complexité croissante (MiniGrid) :

* **Primaire** : Navigation basique et proprioception (`Empty-8x8`).
* **Collège** : Logique d'objets, clés et portes (`DoorKey-6x6`).
* **Lycée** : Manipulation avancée, coffres et outils (`Unlock-5x5`).
* **Université** : Rétention d'informations temporelles et mémoire à long terme (`MemoryS7`).
* **Doctorat** : Planification à très long horizon à travers de multiples sous-objectifs (`MultiRoom-N4-S5`).

---

## 📜 Journal des Mises à Jour

Pour un historique complet commit par commit, consultez [CHANGELOG.md](https://www.google.com/search?q=CHANGELOG.md).

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

Retrouvez le plan de développement stratégique complet dans [plan_creat.md](https://www.google.com/search?q=plan_creat.md).

---

## 🧠 Architecture Cognitico-Biologique Complète

L'agent **Naulthène** repose sur deux systèmes interconnectés, orchestrés par une régulation neurobiologique.

```
                  +-----------------------------------+
                  |  Perception (Grille / MiniGrid)   |
                  +-----------------+-----------------+
                                    |
                                    v
                     +--------------+--------------+
                     |   JEPA (World Model)        |
                     | Representation & Prediction |
                     +--------------+--------------+
                                    |
            +-----------------------+-----------------------+
            |                                               |
            v                                               v
+-----------+-----------+                       +-----------+-----------+
|   SYSTÈME 1 (Instinct)|                       |   SYSTÈME 2 (Raison)  |
|  Policy Network (RL)  |                       | Rollout Multi-Échelle |
|                       |                       |   (Sauts t+1,t+3,t+7) |
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

> **Mode Libre (Seuil de promotion $\ge 80\%$)** : Une fois le Palier 7 maîtrisé, le guidage artificiel se désactive. L'agent passe en `Mode_Libre = 1`. `force_planification` monte à $0.85$ et `coeff_entropie` à $0.06$.

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

## 🏃 Pression Cinétique & Patience Adaptative

Deux mécaniques génériques introduites en v15.0, actives sur tous les niveaux du cursus, qui traduisent une "envie de bouger" et une gestion de l'abandon contrôlé en signaux de RL exploitables.

### 1. `ThermostatCinetique` — Pression Cinétique ("Envie de Bouger")

Coûte de l'énergie synaptique à l'agent qui stagne :

* **Immobilité stricte** : rester sur la même case entre deux ticks coûte $2 \times$ la pénalité de base.
* **Piétinement** : revenir sur une case déjà visitée dans la fenêtre récente (6 derniers ticks) coûte une pénalité croissant géométriquement avec le nombre d'occurrences ($1.5^{\text{occurrences}}$).

L'immobilité devient ainsi sous-optimale par construction du signal de récompense, sans qu'aucune règle ne code un comportement de mur ou de couloir spécifique à une carte.

### 2. `ModuleAcceptationAdaptative` — Potentiomètre d'Acceptation (Patience Adaptative)

Remplace un plafond de ticks par épisode fixe par un seuil de patience $\tau_{\text{patience}}$ recalculé chaque jour :

$$\tau_{\text{patience}} = \text{patience}_{\min} + \big(0.7 \cdot S_{\text{hist}} + 0.3 \cdot V_{\text{hist}}\big) \times (\text{patience}_{\max} - \text{patience}_{\min})$$

Où $S_{\text{hist}}$ est le taux de succès sur les 20 derniers épisodes et $V_{\text{hist}}$ un facteur dérivé de la vitesse (en ticks) des succès passés — plus l'agent réussissait vite par le passé, plus il tolère d'insister sur l'épisode courant.

Quand le compteur de ticks de l'épisode dépasse ce seuil sans conclusion naturelle de l'environnement, l'agent déclenche une **troncature volontaire (abandon lucide)** : il accepte l'échec courant pour préserver ses ressources cognitives, avec une **friction dopaminergique douce** dédiée (`TAUX_FRICTION_DOUCE_ABANDON`) plutôt qu'un choc négatif traumatique.

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
  "Penalite_Stagnation": -0.842
}

```

**Effets attendus des métriques v15.0 :**

* **`Patience_Max_Episode`** : n'est plus plate à une valeur fixe. Oscille dynamiquement — haute en phase d'apprentissage actif, plus basse sur un environnement non résolu pour éviter le piège des boucles infinies.
* **`Penalite_Stagnation`** : sa valeur absolue diminue à mesure que l'agent apprend à éviter les comportements de blocage face à un mur ou les allers-retours répétés.
* **`Erreur_JEPA`** : la planification multi-échelle ($t+1, t+3, t+7$) tend à stabiliser la représentation spatiale globale du World Model plutôt que de sur-optimiser les micro-variations de surface.

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

# Apprentissage & Entropie
ENTROPIE_GUIDE = 0.02
ENTROPIE_LIBRE = 0.06
SEUIL_MAITRISE_PALIER = 0.80

# Pression Cinétique (v15.0)
PENALITE_STAGNATION_BASE = 0.015

# Potentiomètre d'Acceptation (v15.0)
PATIENCE_MIN = 40
PATIENCE_MAX = 350
FENETRE_HISTORIQUE_PATIENCE = 20
TAUX_FRICTION_DOUCE_ABANDON = 0.05

```

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