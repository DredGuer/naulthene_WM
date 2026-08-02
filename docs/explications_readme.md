# Naulthène AGI — Comprendre l'algorithme en profondeur

Ce document explique **comment** et **pourquoi** le cerveau `AGI_Naulthene` fonctionne, avec les vraies formules mathématiques et les vrais noms de variables du code (référence : `agi_google_colab.py` v17 ; les mécaniques expérimentales additionnelles de `agi_local_test.py` sont signalées explicitement). Il complète le [readme.md](../readme.md) narratif par un niveau de détail algorithmique et mathématique complet.

---

## Table des matières

1. [Vue d'ensemble : pourquoi cette architecture ?](#1-vue-densemble--pourquoi-cette-architecture-)
2. [JEPA — le modèle du monde](#2-jepa--le-modèle-du-monde)
3. [Pourquoi JEPA et Naulthène fonctionnent en complémentarité](#3-pourquoi-jepa-et-naulthène-fonctionnent-en-complémentarité)
4. [Le tronc cérébral commun](#4-le-tronc-cérébral-commun)
5. [Système 1 — l'instinct (Acteur-Critique)](#5-système-1--linstinct-acteur-critique)
6. [Système 2 — la raison (rollout mental)](#6-système-2--la-raison-rollout-mental)
7. [Arbitrage Système 1 / Système 2](#7-arbitrage-système-1--système-2)
8. [Plasticité structurelle — `NaultheneLinearSynaptique`](#8-plasticité-structurelle--naultheneLinearsynaptique)
9. [Le réservoir dopaminergique](#9-le-réservoir-dopaminergique)
10. [Le rêve nocturne adaptatif](#10-le-rêve-nocturne-adaptatif)
11. [Le cursus académique et la patience adaptative](#11-le-cursus-académique-et-la-patience-adaptative)
12. [Évolutions du projet (v7 → v26)](#12-évolutions-du-projet-v7--v26)
13. [Glossaire des constantes](#13-glossaire-des-constantes)
14. [La Cascade C1 → C2 → C3 & le Port Exocortex (expérimental)](#14-la-cascade-c1--c2--c3--le-port-exocortex-expérimental)
15. [Le Bus Sensoriel & l'identité C1/C2 explicite (expérimental)](#15-le-bus-sensoriel--lidentité-c1c2-explicite-expérimental)

---

## 1. Vue d'ensemble : pourquoi cette architecture ?

Le RL (Reinforcement Learning) classique a un défaut connu : quand on donne à un agent une seule source de signal (la récompense externe), il apprend à **maximiser ce chiffre par tous les moyens**, y compris des raccourcis qui n'ont rien à voir avec une vraie compréhension du monde (le "reward hacking"). Naulthène part d'un pari différent, inspiré de la psychologie développementale (Piaget, Dehaene) et de la neurobiologie computationnelle : faire émerger la compétence à partir de **plusieurs signaux complémentaires** qui s'équilibrent entre eux, plutôt que d'un seul optimisé à l'excès.

Quatre briques coexistent et s'alimentent mutuellement :

| Brique | Rôle | Section |
|---|---|---|
| **JEPA** | Comprendre "comment le monde bouge" (modèle prédictif) | §2-3 |
| **Système 1 + Système 2** | Décider quoi faire (réflexe + planification mentale) | §5-7 |
| **Plasticité structurelle** | Apprendre et grandir sans tout réécrire (mémoire base/annexe) | §8 |
| **Réservoir dopaminergique + rêve** | Réguler la motivation et consolider la nuit | §9-10 |

Le fil conducteur mathématique de tout le projet est le suivant : **presque toutes les mises à jour d'état du cerveau (dopamine, érosion synaptique, ressort nocturne) suivent la même forme de relaxation exponentielle** :

$$
x_{t+1} = x_t + (x_{cible} - x_t) \times \tau
$$

où $\tau$ est un taux de convergence (friction, choc, ressort, érosion...). C'est un choix délibéré de simplicité : un seul patron mathématique, réutilisé à toutes les échelles de temps (le tick, la nuit, la synapse), au lieu d'une équation différente pour chaque mécanisme.

---

## 2. JEPA — le modèle du monde

**JEPA** signifie *Joint Embedding Predictive Architecture*. L'idée centrale, contrairement à un auto-encodeur classique qui reconstruit l'observation pixel par pixel, est de **prédire la représentation latente de l'état suivant**, pas l'observation brute elle-même.

### 2.1 Ce que JEPA prédit, concrètement

Le "générateur d'attente" (`generateur_attente`, une couche `NaultheneLinearSynaptique`) prend en entrée l'action réellement exécutée (encodée en one-hot, 7 dimensions) concaténée à la "pensée" courante du réseau (`dim_bus` dimensions, 16 au départ) :

```python
def _predire_bus(self, pensee, actions_onehot):
    return self.generateur_attente(torch.cat([actions_onehot, pensee], dim=-1))
```

Avec les dimensions par défaut (`dim_bus=16`), c'est une transformation linéaire unique **23 → 16** (pas de MLP profond caché) — le pari de conception est qu'un modèle de transition simple suffit dans un espace latent déjà compact, plutôt qu'un réseau profond dans l'espace pixel.

### 2.2 La perte JEPA — formule exacte

```python
def perte_jepa(self, attente, obs_suivante):
    with torch.no_grad():
        bus_reel = F.relu(self.porte_visuelle(obs_suivante))
    return F.mse_loss(attente, bus_reel)
```

Mathématiquement, en notant $z_t$ la sortie brute de `generateur_attente` (la prédiction) et $\hat{z}_{t+1} = \text{ReLU}(W_{porte\_visuelle} \cdot o_{t+1})$ l'embedding **réel** de l'observation suivante :

$$
\mathcal{L}_{JEPA} = \frac{1}{D_{bus}} \sum_{i=1}^{D_{bus}} \left(z_{t,i} - \hat{z}_{t+1,i}\right)^2
$$

Deux détails cruciaux dans le code :

1. **C'est un MSE dans l'espace latent (16 dimensions), jamais dans l'espace pixel (147 dimensions).** La cible n'est pas l'image brute suivante, mais sa version déjà encodée par le réseau.
2. **`torch.no_grad()` sur le calcul de la cible** : c'est un "stop-gradient", la technique caractéristique de JEPA. Sans lui, le réseau pourrait "tricher" en faisant converger prédicteur et encodeur vers une représentation triviale constante (le fameux "representation collapse" — prédire correctement une valeur qui ne varie jamais est trop facile pour être un signal d'apprentissage utile). Ici, seule la branche de prédiction reçoit le gradient ; la cible évolue indépendamment au fil de l'apprentissage des autres pertes (acteur-critique).

### 2.3 Pourquoi prédire le latent plutôt que le pixel ?

Trois raisons observables directement dans la structure du code :

- **Compression du signal utile** : l'espace `dim_bus` (16-96 dims) est bien plus compact que l'observation brute (147 dims), ce qui élimine le bruit de bas niveau (texture, détail non pertinent à la décision) qui polluerait un MSE pixel-à-pixel.
- **Anti-effondrement** : le stop-gradient empêche la solution dégénérée où prédire et encoder convergent vers une constante triviale.
- **Espace partagé avec la décision** : `dim_bus` est l'espace dans lequel vivent aussi la tête motrice et le critique. Apprendre à prédire cet espace revient à apprendre une dynamique **compatible avec le contrôle**, contrairement à une reconstruction pixel qui optimiserait un objectif complètement indépendant de la prise de décision.

### 2.4 Double usage de JEPA

**(a) Modèle du monde appris.** La perte JEPA moyenne de la journée entre directement dans la perte totale rétropropagée :

```python
perte_totale = torch.stack(jepa_losses).mean() + perte_acteur + perte_critique + perte_entropie
```

**(b) Signal de curiosité.** L'erreur JEPA du tick courant module la récompense interne, pondérée par la dopamine :

$$
r_{curiosite} = \frac{D_t - D_{min}}{D_{max} - D_{min}} \times \min(\mathcal{L}_{JEPA,t},\ 2.0)
$$

Autrement dit : **un agent démotivé (dopamine basse) ne tire presque aucune récompense de la surprise, même forte** ; un agent motivé en tire une récompense proportionnelle pleine. La curiosité n'est donc jamais un signal isolé, elle est toujours filtrée par l'état émotionnel global.

Un second mécanisme, `DetecteurCuriositeJEPA` (actif en Mode Libre seulement), transforme un **dépassement relatif** de l'erreur JEPA en sous-quête ponctuelle :

$$
\mathcal{L}_{JEPA,t} > 1.5 \times \overline{\mathcal{L}_{JEPA}}_{[t-50,\,t]} \implies \text{micro-récompense } +0.04,\ \text{poids de choc } 0.15
$$

C'est un déclencheur (0 ou 1), pas un facteur d'échelle continu comme (b) — les deux mécanismes coexistent sans se substituer l'un à l'autre.

---

## 3. Pourquoi JEPA et Naulthène fonctionnent en complémentarité

C'est la question centrale : **JEPA seul ne "veut" rien, et l'Acteur-Critique seul ne "comprend" rien.** Leur complémentarité vient de trois boucles de rétroaction concrètes câblées dans le code :

**Boucle 1 — JEPA nourrit la décision (Système 2).** Le rollout mental (`simuler_futur_et_planifier`, détaillé §6) utilise `_predire_bus` — c'est-à-dire exactement le prédicteur JEPA — comme moteur de transition d'état pour "imaginer" les conséquences futures d'une action, **sans jamais interroger l'environnement réel**. Si JEPA prédit mal, le Système 2 planifie sur une hallucination ; si JEPA prédit bien, le Système 2 anticipe correctement un couloir de MultiRoom sur plusieurs pas. Naulthène ne peut donc "raisonner" que dans la mesure où JEPA "comprend" la physique de l'environnement.

**Boucle 2 — la décision nourrit JEPA.** L'espace latent (`dim_bus`) que JEPA doit prédire n'est pas un espace de reconstruction arbitraire : c'est **le même espace** que celui utilisé par la tête motrice et le critique (`tete_motrice`, `cortex_prefrontal` prennent tous deux `pensee` en entrée). Optimiser JEPA façonne donc indirectement une représentation qui sert aussi à agir, pas seulement à décrire.

**Boucle 3 — l'erreur JEPA pilote la motivation et la structure du réseau elle-même**, à trois échelles de temps différentes :
- *Par tick* : l'erreur JEPA alimente `dopamine_curiosite` (§2.4) — un monde mal compris devient une source de motivation intrinsèque.
- *Par journée* : la moyenne glissante de l'erreur JEPA sur 3 jours pilote le **thermostat de neurogenèse** (§8.4) — si l'erreur reste élevée et stable, le réseau grandit littéralement (`agrandir()`, +16 dimensions) pour se donner plus de capacité de représentation.
- *Par nuit* : pendant le rêve, seul le canal JEPA est rejoué (§10.2) — la consolidation nocturne renforce le modèle du monde, jamais directement la politique motrice (qui en bénéficie indirectement via le tronc partagé).

En résumé : **JEPA fournit la "physique interne" sur laquelle le Système 2 peut planifier sans agir réellement, pendant que l'Acteur-Critique fournit l'objectif (la récompense) qui façonne quelle physique vaut la peine d'être apprise finement.** Aucun des deux ne fonctionnerait seul — un Acteur-Critique sans JEPA n'aurait pas de Système 2 (rien sur quoi "imaginer" l'avenir) ; un JEPA sans Acteur-Critique apprendrait une dynamique du monde sans jamais savoir quelle partie de cette dynamique est pertinente pour agir.

---

## 4. Le tronc cérébral commun

Toute perception passe par la même chaîne avant de se diviser en têtes spécialisées (`_tronc_cerebral`) :

```python
def _tronc_cerebral(self, obs, memoire_precedente):
    bus_latent = F.relu(self.porte_visuelle(obs))
    fusion_temporelle = torch.cat([bus_latent, memoire_precedente], dim=-1)
    memoire_actuelle = F.relu(self.hippocampe(fusion_temporelle))
    pensee = F.relu(self.analyseur(memoire_actuelle))
    return bus_latent, memoire_actuelle, pensee
```

Chaîne dimensionnelle (config de base) :

$$
\underbrace{obs\ (147)}_{\text{pixels/objets}} \xrightarrow{porte\_visuelle} \underbrace{bus\_latent\ (16)}_{\text{ReLU}} \xrightarrow{\oplus\ memoire\_prec} \underbrace{(32)}_{\text{concat}} \xrightarrow{hippocampe} \underbrace{memoire\_actuelle\ (16)}_{\text{ReLU}} \xrightarrow{analyseur} \underbrace{pensee\ (16)}_{\text{ReLU}}
$$

Puis la **lecture épisodique** raffine `pensee` en la fusionnant deux fois de suite avec le contexte (moyenne glissante des 20 derniers `bus_latent`, `CAPACITE_MEMOIRE = 20`) :

```python
def lecture_episodique(self, pensee, contexte):
    x = pensee
    for _ in range(2):
        x = F.relu(self.fusion_memoire(torch.cat([x, contexte], dim=-1)))
    return x
```

Cette double passe est un raffinement itératif, pas un simple passage unique — chaque itération reconcatène le résultat courant avec le même contexte fixe.

---

## 5. Système 1 — l'instinct (Acteur-Critique)

Deux têtes de sortie à partir de `pensee` (détachée du graphe pour ces deux têtes) :

- `tete_motrice` : `pensee` (16) → logits des 7 actions.
- `cortex_prefrontal` : `pensee` (16) → valeur scalaire $V(s)$.

C'est un **REINFORCE avec baseline** (pas un PPO/GAE), calculé **une fois par journée entière**, pas par mini-batch de trajectoire courte.

**Retour Monte-Carlo actualisé** (calcul rétrograde) :

$$
R_t = r_t + \gamma \cdot R_{t+1} \cdot \mathbb{1}[\text{pas terminal}], \qquad \gamma = 0.95
$$

**Standardisation des retours** (si plus d'un élément, écart-type non nul) :

$$
\tilde{R}_t = \frac{R_t - \mu_R}{\sigma_R + 10^{-8}}
$$

**Avantage** (le critique est détaché pour ce calcul, pas de double gradient) :

$$
A_t = \tilde{R}_t - V(s_t)
$$

**Les trois pertes** :

$$
\mathcal{L}_{acteur} = -\frac{1}{T}\sum_t \log\pi(a_t \mid s_t) \cdot A_t
$$

$$
\mathcal{L}_{critique} = \frac{1}{T}\sum_t \left(V(s_t) - \tilde{R}_t\right)^2
$$

$$
\mathcal{L}_{entropie} = -c_{entropie} \cdot \frac{1}{T}\sum_t H\big(\pi(\cdot \mid s_t)\big), \qquad c_{entropie} \in \{0.02_{\text{guidé}},\ 0.06_{\text{libre}}\}
$$

**Perte totale rétropropagée** (JEPA inclus, §2.4a) :

$$
\mathcal{L}_{totale} = \overline{\mathcal{L}_{JEPA}} + \mathcal{L}_{acteur} + \mathcal{L}_{critique} + \mathcal{L}_{entropie}
$$

Un seul `backward()` sur cette somme, gradient clippé à une norme globale de 1.0 (`clip_grad_norm_`), puis un pas Adam (`lr=1e-3`). C'est ce qu'on entend par "alignement graph-gradient" dans le changelog v8.0 : JEPA et RL partagent le même graphe de calcul et le même appel `backward()`, pas deux passes séparées.

---

## 6. Système 2 — la raison (rollout mental)

`simuler_futur_et_planifier` est décorée `@torch.no_grad()` : c'est de l'**inférence pure**, aucun gradient n'en sort — elle sert à moduler l'action choisie, pas à s'entraîner elle-même.

### 6.1 Le principe des sauts non-linéaires

Plutôt qu'une chaîne stricte $t{+}1 \to t{+}2 \to t{+}3 \to \dots$, le rollout saute directement à des horizons `HORIZONS_PLANIFICATION = (1, 3, 7)` :

1. **Premier horizon (t+1)** : branche sur les **7 actions réelles simultanément** (`self.actions_eye`) — c'est la seule vraie décision évaluée.
2. **Horizons suivants (t+3, t+7)** : chaque branche continue **seule**, en suivant le réflexe glouton (`argmax`) de `tete_motrice` — jamais de nouveau branchement à 7 actions.
3. **La transition d'état simulée réutilise le prédicteur JEPA** (`_predire_bus`) pour "avancer" mentalement sans jamais toucher l'environnement réel :

```python
futur_bus = F.relu(self._predire_bus(pensee_branche, actions_pas))
futur_mem = F.relu(self.hippocampe(torch.cat([futur_bus, mem_branche], dim=-1)))
futur_pensee = F.relu(self.analyseur(futur_mem))
```

### 6.2 Pourquoi cette restriction est essentielle

Si chaque horizon rebranchait sur 7 nouvelles actions, la complexité exploserait en $7^{\text{horizon}}$ (343 branches à l'horizon 3, plus de 800 000 à l'horizon 7). En ne branchant qu'une seule fois et en suivant l'argmax ensuite, la complexité reste **linéaire** :

$$
O\Big(A \times \textstyle\sum \Delta h\Big), \qquad A = 7,\quad \sum \Delta h = 1 + (3{-}1) + (7{-}3) = 7
$$

C'est une contrainte de conception explicitement protégée dans `CLAUDE.md` : ne jamais rebrancher sur 7 nouvelles actions aux horizons suivants.

### 6.3 Valeur cumulée du futur imaginé

$$
V_{cumulée}(a) = \sum_{h \in \{1,3,7\}} \gamma_{planif}^{\,h} \cdot V\big(\hat{s}_{t+h} \mid a\big), \qquad \gamma_{planif} = 0.9
$$

où $\hat{s}_{t+h}$ est l'état latent simulé atteint à l'horizon $h$. Un chemin qui traverse un bon état à $t{+}3$ compte, même si $t{+}7$ reste incertain — le Système 2 obtient une **vision de tendance à moyen terme**, utile sur les longs couloirs de MultiRoom (Doctorat), sans calculer chaque micro-état intermédiaire.

Standardisation finale entre les 7 candidats :

$$
\tilde{V}_{cumulée} = \frac{V_{cumulée} - \mu}{\sigma + 10^{-8}}
$$

---

## 7. Arbitrage Système 1 / Système 2

Les logits des deux systèmes sont combinés directement, `penser()` :

```python
logits_finaux = logits_instinct + (valeurs_simulees * force_planification)
```

$$
\text{logits}_{finaux} = \text{logits}_{instinct} + f_{planif} \cdot \tilde{V}_{cumulée}
$$

$f_{planif}$ vaut **0.5 en mode guidé**, **0.85 en Mode Libre** (dès `palier_cible >= 5`). Le Système 2 pèse donc structurellement plus lourd précisément au moment où le guidage artificiel externe disparaît — l'agent est forcé de s'appuyer davantage sur sa propre planification interne. L'action finale est échantillonnée par `Categorical(logits=logits_finaux)`.

---

## 8. Plasticité structurelle — `NaultheneLinearSynaptique`

Chaque couche du réseau (y compris `porte_visuelle`, `generateur_attente`, etc.) n'est **pas** une `nn.Linear` standard, mais une couche à deux poids superposés.

### 8.1 Poids de base + poids annexe

```python
weight_total = self.base_weight + self.annexe_weight
y = F.linear(x, weight_total)
```

$$
W_{total} = W_{base} + W_{annexe}, \qquad y = x \cdot W_{total}^\top
$$

**Différence fondamentale** : `base_weight` est un **buffer** (jamais optimisé par Adam directement) — c'est la mémoire de long terme, figée. `annexe_weight` est le seul `nn.Parameter` réellement entraîné — c'est la mémoire à court terme de la journée. `base_weight` n'évolue que lors de la consolidation nocturne explicite (§8.2).

À chaque forward en entraînement, une **trace de myéline** s'accumule par maximum courant :

$$
M_t = \max\big(M_{t-1},\ |W_{annexe}|\big)
$$

### 8.2 Le cycle de sommeil — érosion et consolidation

```python
def cycle_sommeil(self, lambda_erosion=0.05, q_ref=1.0):
    self.base_weight += self.annexe_weight
    myeline_norm = torch.clamp(self.myeline_M / q_ref, 0.0, 1.0)
    self.base_weight *= (1.0 - (lambda_erosion * (1.0 - myeline_norm)))
    masque_mort = torch.abs(self.base_weight) < 1e-4
    self.base_weight[masque_mort] = 0.0
    self.myeline_M[masque_mort] = 0.0
    self.annexe_weight.zero_()
```

**Étape 1 — consolidation** : l'apprentissage de la journée s'intègre dans la mémoire de long terme.
$$
W_{base} \leftarrow W_{base} + W_{annexe}
$$

**Étape 2 — normalisation de la myéline** :
$$
M_{norm} = \text{clip}\left(\frac{M}{1.0},\ 0,\ 1\right)
$$

**Étape 3 — érosion sélective**, protégeant les synapses fortement myélinisées :
$$
W_{base} \leftarrow W_{base} \times \Big(1 - \lambda_{erosion} \cdot (1 - M_{norm})\Big), \qquad \lambda_{erosion} = 0.05 \times \text{plasticite\_base}
$$
Une synapse totalement myélinisée ($M_{norm}=1$) n'est **pas du tout érodée**. Une synapse jamais activée ($M_{norm}=0$) subit l'érosion maximale.

**Étape 4 — élagage synaptique** : tout poids tombant sous $10^{-4}$ est mis à exactement zéro (compté comme "synapse morte", loggé sur W&B).

Enfin `annexe_weight` est remis à zéro — **chaque nouvelle journée repart avec un poids plastique vierge**, seule la mémoire consolidée persiste.

### 8.3 LTP hebbien (expérimental, `agi_local_test.py` uniquement, v20.0)

Une **trace d'éligibilité** supplémentaire s'accumule à chaque tick :

$$
E_t = 0.9 \cdot E_{t-1} + 0.1 \cdot |W_{annexe,t}|
$$

Sur un pic de dopamine (`poids_evenement > 0` : manger, franchir une porte, réussir un palier) :

$$
\text{ancrage} = E_t \times p_{dopamine}
$$
$$
W_{base} \leftarrow W_{base} + W_{annexe} \cdot \text{clip}(\text{ancrage},\ 0,\ 1), \qquad M \leftarrow M + \text{ancrage}, \qquad E_t \leftarrow 0
$$

C'est une vraie **Potentiation à Long Terme événementielle** : contrairement à `cycle_sommeil` qui consolide indistinctement une fois par nuit, ce mécanisme grave la synapse **immédiatement**, proportionnellement à son activité récente (fenêtre implicite ~10 ticks) et à l'intensité du pic — un bon repas isolé au milieu d'une journée difficile n'est plus dilué dans une moyenne.

### 8.4 `agrandir()` — la neurogenèse

Quand le réseau doit grandir (+16 dimensions), une nouvelle matrice est initialisée en Xavier uniforme puis **atténuée ×0.1** (pour ne pas perturber violemment le réseau déjà entraîné), et les anciens poids sont **copiés par blocs exacts** aux bonnes positions — une greffe, jamais un réentraînement complet.

Déclenchement (`mutation_possible`) :

```python
mutation_possible = (jours_depuis_mutation >= 5
                     and dim_bus + 16 <= DIM_BUS_MAX  # 96
                     and plasticite_base > 0.05)
```

combiné à `erreur_moyenne > seuil_actuel` (l'erreur JEPA moyenne de la journée dépasse le seuil de tolérance courant) — **c'est littéralement l'erreur du modèle du monde qui décide de faire grandir le cerveau.**

### 8.5 Cristallisation Souple (expérimental, `agi_local_test.py` uniquement, v26.0)

Le plancher de plasticité global protège tout le cerveau d'un coup, à l'aveugle. La
Cristallisation Souple ajoute une protection **ciblée** : les synapses sollicitées fortement et
régulièrement sur plusieurs nuits deviennent quasi indestructibles à l'érosion, sans jamais geler
leur apprentissage diurne (règle dissymétrique sommeil ≠ gradient).

**Accumulation inter-nuits.** Une seconde trace, `myeline_cumul`, distincte de la myéline
instantanée `myeline_M` (§8.1, maximum courant intra-journée), s'accumule sur plusieurs *nuits*
avec le même patron de relaxation exponentielle que partout ailleurs dans le projet (§1) :

$$
M_{\text{cumul}}(t) = \alpha \cdot M_{\text{cumul}}(t-1) + (1-\alpha) \cdot M(t), \qquad \alpha = \text{ALPHA\_CRISTAL} = 0.95
$$

écrit dans le code comme `myeline_cumul += (myeline_M - myeline_cumul) * (1 - ALPHA_CRISTAL)`,
calculé à l'intérieur de `cycle_sommeil()` juste après l'érosion (Étape 3) et juste avant
l'élagage (Étape 4) — sur la myéline de cette nuit, avant que les positions mortes ne soient
remises à zéro.

**Le cliquet de cristallisation.** Dès que $M_{\text{cumul}} \ge \text{SEUIL\_CRISTAL} = 0.80$, la
synapse reçoit un flag booléen `cristallisee = True` (buffer de la taille de `base_weight`,
granularité par poids individuel). C'est un **cliquet à sens unique** (`|=`, jamais réinitialisé) :
une fois la synapse suffisamment consolidée, sa protection contre l'oubli passif ne se perd
jamais — seul le poids lui-même, via le gradient diurne, peut encore être affiné.

**La falaise sigmoïde (correctif post-implémentation).** Plutôt qu'un plancher d'érosion rigide
appliqué en tout-ou-rien, la protection d'une synapse cristallisée est une transition continue :

$$
p_{\text{protection}} = \sigma\big(k \cdot (M_{\text{cumul}} - \text{SEUIL\_CRISTAL})\big),
\qquad k = \text{K\_RAIDEUR\_CRISTAL} = 10.0
$$

$$
M_{\text{norm,effectif}} = \max\big(M_{\text{norm}},\ \mathbb{1}[\text{cristallisee}] \cdot p_{\text{protection}}\big)
$$

```python
myeline_norm = torch.clamp(self.myeline_M / q_ref, 0.0, 1.0)
p_protection = torch.sigmoid(K_RAIDEUR_CRISTAL * (self.myeline_cumul - SEUIL_CRISTAL))
plancher_cristal = self.cristallisee.float() * p_protection
myeline_norm_effectif = torch.max(myeline_norm, plancher_cristal)
self.base_weight *= (1.0 - (lambda_erosion * (1.0 - myeline_norm_effectif)))
```

Une synapse très éprouvée ($M_{\text{cumul}} \gg 0.80$) voit $p_{\text{protection}} \to 1.0$ :
érosion nocturne quasi nulle, ancrage indestructible d'un fondamental (se déplacer, reconnaître
une porte). Une synapse **jamais** cristallisée ne bénéficie d'aucun plancher : elle s'érode au
taux plein `lambda_erosion` et tombe sous le masque de mort (`< 1e-4`, Étape 4) en temps fini —
**zéro synapse fantôme** qui traînerait indéfiniment avec une érosion ralentie sans raison. La
falaise remplace un plancher constant (`MYELINE_MIN_CRISTAL = 0.50`, première version du plan)
par une régulation continue, plus fidèle au principe du projet : aucune règle en dur, tout émerge
d'une formule paramétrée.

**Règle dissymétrique.** `forward()` et `fortification_dopaminergique()` ne lisent ni n'écrivent
jamais `myeline_cumul`/`cristallisee` — la cristallisation ne fige que l'érosion nocturne
(`cycle_sommeil`), jamais le gradient diurne sur `annexe_weight`. Un hard freeze romprait la
capacité de l'agent à réviser un fondamental si le monde change (nouvelle couleur de porte,
nouvel angle) ; ici, la synapse cristallisée continue d'apprendre normalement, elle est juste
protégée de mourir de silence pendant qu'elle ne sert pas.

`agrandir()` traite `myeline_cumul`/`cristallisee` exactement comme `myeline_M`/`trace_activation`
(§8.4) : colonnes existantes copiées par segment, nouvelles dimensions nées à `0`/`False` — aucune
synapse neuve ne naît pré-cristallisée.

---

## 9. Le réservoir dopaminergique

Un seul scalaire $D_t \in [0.001,\ 10.0]$ régule à la fois la motivation (récompense de curiosité) et la plasticité (érosion nocturne). Trois forces s'y appliquent, toutes de la même forme de relaxation exponentielle :

**Friction quotidienne** (à chaque tick sans événement marquant) :
$$
D_{t+1} = D_t + (D_{min} - D_t) \times 0.01
$$

**Choc au succès** (`poids_evenement > 0`) :
$$
D_{t+1} = D_t + (D_{max} - D_t) \times 0.9 \times w_{evenement}
$$

Jusqu'à la v26.0, `poids_evenement` était le **maximum** des poids de tous les détecteurs actifs ce tick (jalons, portes, progrès, curiosité, ressources bio, vocal) — un seul canal "gagnait", les autres étaient purement ignorés ce tick-là.

### 9.1 Dopamine unifiée multimodale (expérimental, `noyau.py` uniquement, v27.0)

Un agent qui franchit une porte **et** prononce correctement le mot qu'il regarde au même tick recevait, avec le `max()`, exactement la même dopamine que s'il n'avait fait que l'un des deux — les deux hémisphères (vue, ouïe) ne se renforçaient jamais mutuellement. `poids_evenement` devient une agrégation probabiliste ("OU doux") entre un agrégat visuel (le `max()` d'avant, inchangé en interne) et le canal vocal :

$$
w_{visuel} = \max\big(w_{palier},\ w_{porte},\ w_{progres},\ w_{curiosite},\ w_{ressource\_bio},\ \mathbb{1}[r_{env}>0]\big)
$$

$$
w_{evenement} = 1 - \big(1 - W_{visuel} \cdot w_{visuel}\big)\big(1 - W_{vocal} \cdot w_{vocal}\big), \qquad W_{visuel}=1.0,\ W_{vocal}=0.7
$$

Trois propriétés motivent ce choix plutôt qu'une simple somme pondérée : **(1) bornée dans $[0,1]$ par construction** pour tout $w_{visuel}, w_{vocal} \in [0,1]$ — invariant nécessaire puisque $w_{evenement}$ multiplie directement le choc ci-dessus ; une somme pondérée exigerait un `clip` explicite, ce formalisme n'en a structurellement pas besoin. **(2) rétrocompatible au bit près** : sans audio ($w_{vocal}=0$), $w_{evenement} = 1-(1-w_{visuel})(1-0) = w_{visuel}$, exactement le `max()` d'avant v27.0. **(3) monotone sans écrasement** : les deux canaux augmentent strictement le résultat, et un canal saturé n'annule jamais l'autre — contrairement au `max()` (canal faible perdu) ou à une moyenne (un canal nul diluerait un canal excellent). $W_{vocal}=0.7 < W_{visuel}=1.0$ car le score vocal est **continu** (non nul à presque chaque tick d'une leçon), contre des canaux visuels **événementiels** (rares) — à parité, le vocal saturerait le réservoir par simple fréquence d'occurrence.

**Ressort nocturne** (une fois par nuit, retour vers la neutralité) :
$$
D_{nuit} = D_{fin\_jour} + (5.0 - D_{fin\_jour}) \times 0.4
$$

Cette teneur pilote directement la **plasticité de base** :

$$
\text{plasticite\_base} =
\begin{cases}
1.0 & \text{si } D \ge 5.0 \\
\max\left(0,\ \dfrac{D - 0.001}{5.0 - 0.001}\right) & \text{sinon}
\end{cases}
$$

Et via elle, l'érosion nocturne (§8.2, $\lambda_{erosion} = 0.05 \times \text{plasticite\_base}$) et le pourcentage de rêve (§10). **Un agent en échec prolongé (dopamine basse) voit son érosion synaptique ralentir** — une protection contre la dégradation du réseau pendant une période de stress, plutôt qu'un cercle vicieux qui s'auto-aggraverait.

---

## 10. Le rêve nocturne adaptatif

### 10.1 Combien de souvenirs rejouer ?

```python
facteur_richesse = min(1.0, importance_moyenne_jour / IMPORTANCE_REFERENCE_REVE)
pourcentage_reve = POURCENTAGE_REVE_MIN + (PLAGE_REVE_MAX - POURCENTAGE_REVE_MIN) * plasticite_base * facteur_richesse
```

$$
\%_{reve} = 0.0001 + (0.60 - 0.0001) \times \text{plasticite\_base} \times \min\left(1,\ \frac{\overline{\text{importance}}_{jour}}{0.5}\right)
$$

Ce pourcentage **émerge** du produit de deux facteurs bornés dans [0,1] : la plasticité (l'état dopaminergique global) et la richesse informationnelle de la journée (moyenne d'importance des souvenirs, normalisée). Aucune taille de batch fixe n'est jamais utilisée — c'est un principe de conception explicitement protégé du projet. Sous `TAILLE_MIN_REVE = 8` souvenirs, aucun rêve n'a lieu (lot jugé trop petit pour un gradient stable).

### 10.2 L'importance d'un souvenir

$$
\text{importance}_t = \Big(|r_{interne,t}| + 2 \cdot \mathcal{L}_{JEPA,t} + 10^{-5}\Big) \times \text{boost}_{ancrage,t} \times \text{empreinte\_enfance}
$$

où `empreinte_enfance = BUS_REFERENCE / dim_bus` décroît à mesure que le réseau grandit — les souvenirs formés quand le cerveau était plus "jeune" (plus petit) reçoivent une pondération plus forte.

**Échantillonnage pondéré par importance, sans remise** :

$$
P(\text{sélection du souvenir } i) = \frac{\text{importance}_i}{\sum_j \text{importance}_j}
$$

**Ce qui est rejoué** : uniquement le canal JEPA (recalcul complet du forward pass et de `perte_jepa` sur les tenseurs bruts conservés, backward, pas Adam). **Aucune perte acteur/critique/entropie n'est rejouée** — le rêve consolide le modèle du monde, la politique motrice en bénéficie seulement indirectement via le tronc partagé.

---

## 11. Le cursus académique et la patience adaptative

### 11.1 Progression entre les 5 niveaux MiniGrid

Primaire → Collège → Lycée → Université → Doctorat, promotion après **2 journées consécutives avec au moins une victoire réelle** (`victoires_consecutives >= VICTOIRES_REQUISES=2`), compteur remis à zéro à chaque journée sans victoire.

### 11.2 Patience adaptative (pas un plafond de ticks fixe)

```python
potentiometre = 0.7 * taux_succes + 0.3 * facteur_vitesse
base_patience = 50 + potentiometre * (350 - 50)
```

$$
\text{potentiometre} = 0.7 \times \text{taux\_succes}_{[20\ derniers]} + 0.3 \times \max\left(0.2,\ 1 - \frac{\overline{v}_{succès}}{350}\right)
$$

$$
\text{patience} = \min\left(350,\ \big(50 + \text{potentiometre} \times 300\big) \times f_{complexite}\right)
$$

Un agent qui réussit souvent **et** vite obtient une patience de base plus élevée — contre-intuitif, mais cela évite d'abandonner trop tôt un épisode qui dérape alors que l'agent maîtrise généralement la tâche.

### 11.3 Le cursus à 7 paliers DoorKey (Abnégation)

Chaque palier requiert **4 succès cumulés en 2 sous-seuils** :
- **Sous-Seuil 1 (Amorçage)** : 2 succès, `facteur_complexite = 1.0`.
- **Sous-Seuil 2 (Abnégation)** : 2 succès supplémentaires, patience étirée ×1.6 (`COEFF_ABNEGATION_SOUS_SEUIL_2`) — l'agent doit prouver sa persévérance sous contrainte accrue avant la vraie promotion.

Dès `palier_cible >= 5` (Viser la Porte), le **Mode Libre** s'active : le guidage artificiel disparaît, remplacé par la curiosité JEPA et le Sursaut de Volonté (boost dopaminergique ponctuel + extension de patience, une fois par épisode, à 95% de la patience consommée).

---

## 12. Évolutions du projet (v7 → v26)

| Version | Ce qui a changé | Pourquoi |
|---|---|---|
| v7-v9 | Socle Système 1+2, rêve, cursus 5 niveaux | Architecture hybride initiale |
| v10-v11 | Rollout mental vectorisé, réservoir dopaminergique homéostatique | Remplacer un tonus fixe par une vraie dynamique |
| v12-v14 | 7 paliers DoorKey, rêve adaptatif, planification 3 pas | Dépasser le sparse reward |
| v15-v17 | Sauts non-linéaires (1,3,7), pression cinétique, Mode Libre, Sursaut de Volonté | Décrochage progressif du guidage externe |
| v18-v20 (expérimental) | Homéostasie biologique, métabolisme 20/80, mémoire épisodique spatiale + LTP hebbien | Motivation par réduction de drive (Hull), pas seulement récompense externe |
| v21-v22 (expérimental) | Cerveau persistant en Cuve (client-serveur), hémisphère auditif/vocal | Séparer Conscience et Corps ; ajouter la modalité son |
| v23-v24 (expérimental) | Cursus Développemental par Ères, Arène de visualisation | Faire cohabiter apprentissage MiniGrid et vocal sur 1000 jours |
| v25 (expérimental) | Le Cerveau Bébé (0→4 ans), masquage de récompense externe, Module Parent | Pousser le principe développemental à l'extrême : 8 mois 100% auto-supervisés |
| v26.0 (expérimental, §A.5 seul) | Cristallisation Souple — protection ciblée des synapses matures contre l'érosion nocturne (falaise sigmoïde) | Protéger les fondamentaux acquis sans jamais geler l'apprentissage diurne |
| v27.0-27.1 (expérimental) | L'École de la Parole & Synesthésie — voix réelle (LPC), synesthésie ancrée (`LecteurCaseFrontale`), dopamine unifiée vue/ouïe, rêve audio, tirage aléatoire d'une prise par tick | Sortir de la table théorique et du curriculum déconnecté de la vision ; unifier le réservoir dopaminergique entre les deux hémisphères |
| v28.0 (expérimental) | La Cascade C1→C2→C3 & le Port Exocortex — 8ème action apprise (`ACTION_DEMANDER`), Port Multiplexeur `PortC3` + Plugs interchangeables, greffe rétrocompatible 7→8 actions | Ouvrir le Cœur Organique à un greffon externe optionnel sans jamais compromettre l'autonomie biologique ni casser un cerveau existant |

Voir [CHANGELOG.md](CHANGELOG.md) pour le détail commit par commit et [readme.md](../readme.md) pour la description narrative complète de chaque version.

---

## 13. Glossaire des constantes

| Constante | Valeur | Rôle |
|---|---|---|
| `DIM_VISUELLE` | 147 | Dimension de l'observation MiniGrid aplatie |
| `dim_bus` | 16 → 96 (`DIM_BUS_MAX`) | Espace latent partagé, +16 par neurogenèse |
| `num_actions` | 7 | Actions MiniGrid |
| `HORIZONS_PLANIFICATION` | (1, 3, 7) | Horizons du rollout Système 2 |
| `GAMMA_PLANIFICATION` | 0.9 | Actualisation du rollout mental |
| `gamma` (RL) | 0.95 | Actualisation du retour Monte-Carlo réel |
| `FORCE_PLANIFICATION_GUIDE / LIBRE` | 0.5 / 0.85 | Poids du Système 2 vs Système 1 |
| `COEFF_ENTROPIE_GUIDE / LIBRE` | 0.02 / 0.06 | Régularisation d'entropie |
| `DOPAMINE_MIN / NEUTRE / MAX` | 0.001 / 5.0 / 10.0 | Bornes du réservoir dopaminergique |
| `TAUX_FRICTION / CHOC_BASE / RESSORT` | 0.01 / 0.9 / 0.4 | Vitesses de relaxation dopaminergique |
| `PLAFOND_ERREUR_DOPAMINE` | 2.0 | Plafond de l'erreur JEPA dans le calcul de curiosité |
| `POURCENTAGE_REVE_MIN / PLAGE_REVE_MAX` | 0.0001 / 0.60 | Bornes du pourcentage de rêve nocturne |
| `IMPORTANCE_REFERENCE_REVE` | 0.5 | Échelle de normalisation de la richesse journalière |
| `PATIENCE_MIN / MAX` | 50 / 350 | Bornes de patience adaptative |
| `COEFF_ABNEGATION_SOUS_SEUIL_2` | 1.6 | Étirement de patience au Sous-Seuil 2 |
| `SEUIL_PALIER_MODE_LIBRE` | 5 | Palier DoorKey déclenchant le Mode Libre |
| `JOURS_ENTRE_MUTATIONS` | 5 | Cooldown minimal entre deux neurogenèses |
| `SEUIL_APHASIE_NEUROGENESE` | 0.05 | Plasticité minimale pour autoriser une mutation |
| `ALPHA_CRISTAL` (v26.0, expérimental) | 0.95 | Vitesse d'accumulation de la myéline cumulée inter-nuits (`myeline_cumul`) |
| `SEUIL_CRISTAL` (v26.0, expérimental) | 0.80 | Seuil de `myeline_cumul` déclenchant le cliquet `cristallisee = True` |
| `K_RAIDEUR_CRISTAL` (v26.0, expérimental) | 10.0 | Raideur de la falaise sigmoïde de protection d'une synapse cristallisée |
| `POIDS_DOPAMINE_VISUEL` (v27.0, expérimental) | 1.0 | Poids du canal visuel dans la dopamine unifiée (§9.1) — modalité mature, poids plein |
| `POIDS_DOPAMINE_VOCAL` (v27.0, expérimental) | 0.7 | Poids du canal vocal dans la dopamine unifiée (§9.1) — volontairement < 1.0, le score vocal étant continu plutôt qu'événementiel |
| `POIDS_RECOMPENSE_FORMANTS / SPECTRALE` (v27.0, expérimental) | 0.6 / 0.4 | Pondération du score vocal mixte (`recompense_vocale_mixte`) entre distance de formants et distance spectrale MFCC↔MFCC |
| `PERIODE_EVAL_SPECTRALE` (v27.0, expérimental) | 10 | Ticks entre deux réévaluations du canal spectral (coût ~100× un score de formants, dernier score réutilisé entre deux évaluations) |
| `NUM_ACTIONS_BASE / AVEC_C3` (v28.0, expérimental) | 7 / 8 | Nombre d'actions sans/avec la 8ème action `ACTION_DEMANDER` (§14) |
| `DIM_ROUTAGE_C3` (v28.0, expérimental) | 5 | Sortie fixe de `tete_requete` — jusqu'à 4 plugs adressables en `1_1` + 1 canal de diffusion `1_X` |
| `COUT_REQUETE_C3` (v28.0, expérimental) | 0.01 | Pénalité en `recompense_interne` à chaque `ACTION_DEMANDER` — rend le choix économique, jamais gratuit |
| `POIDS_DOPAMINE_C3` (v28.0, expérimental) | 0.5 | Poids du 3ème canal (C3) dans la dopamine unifiée (§14.4) — plus faible que `POIDS_DOPAMINE_VOCAL` |
| `SEUIL_OVERRIDE_C3` (v28.0, expérimental) | 0.85 | Confiance à partir de laquelle une `ReponseC3` impose l'action plutôt que de biaiser les logits |
| `FORCE_C3` (v28.0, expérimental) | 0.5 | Poids du biais logits appliqué sous `SEUIL_OVERRIDE_C3` — même ordre de grandeur que `FORCE_PLANIFICATION_GUIDE` |
| `COOLDOWN_PLUG_ECHEC` (v28.0, expérimental) | 200 | Ticks de quarantaine d'un plug après une exception, avant d'être retenté (`naulthene.exocortex.port_c3`) |

---

## 14. La Cascade C1 → C2 → C3 & le Port Exocortex (expérimental)

> ⚠️ **Statut expérimental** : vit dans `src/naulthene/cerveau/noyau.py` et le sous-package versionné `src/naulthene/exocortex/`, pas encore porté sur `agi_google_colab.py`. Voir [docs/CHANGELOG.md](CHANGELOG.md) (entrée v28.0-experimental) pour le détail commit par commit.

### 14.1 Principe : un troisième cerveau, jamais dans le chemin critique

Jusqu'ici, `penser()` (§5-7) fusionne uniquement C1 (`tete_motrice`) et C2 (`simuler_futur_et_planifier`) en une seule ligne (`logits_finaux = logits_instinct + valeurs_simulees * force_planification`). La v28.0 ajoute un **troisième canal optionnel**, C3 (l'Exocortex), conçu explicitement comme un **Port Multiplexeur** plutôt qu'un appel figé vers un unique service externe :

```python
class RequeteC3:
    latent: np.ndarray        # pensee_bio, dim_bus — jamais un tenseur PyTorch
    num_actions: int
    indecision_c2: float       # contexte, jamais un déclencheur (voir 14.3)
    erreur_jepa: float
    palier_vocal: int
    mot_frontal: str | None

class ReponseC3:
    preferences: np.ndarray   # avis sur les num_actions actions, taille (num_actions,)
    confiance: float           # dans [0, 1]
    origine: str
```

`PortC3` (le bus) ne connaît que ce contrat — jamais l'agent, jamais PyTorch. Des `PlugC3` interchangeables s'y enregistrent (`PlugNul` toujours absent, `PlugSimule` déterministe pour les tests, `PlugHTTP` backend générique JSON/HTTP). **Invariant non négociable** : sans plug enregistré, le comportement est bit-identique à la v27.6 — c'est la garantie de fond de toute cette section.

### 14.2 Le choix appris — une 8ème action, pas un seuil

`num_actions` passe de `NUM_ACTIONS_BASE=7` à `NUM_ACTIONS_AVEC_C3=8`. La 8ème action, `ACTION_DEMANDER`, est une action comme les autres pour la tête motrice — apprise par le même REINFORCE, jamais déclenchée par un `if`. Le masquage a lieu dans `penser()`, après la fusion C1+C2 :

```python
logits_finaux = logits_instinct + (valeurs_simulees * force_planification)
if not plugs_c3_disponibles:
    logits_finaux[..., ACTION_DEMANDER] = float("-inf")
```

Sans plug disponible, l'action est mathématiquement inexistante dans `Categorical(logits=logits_finaux)` — pas juste improbable. Une nouvelle tête `tete_requete` (dim_bus → `DIM_ROUTAGE_C3=5`) choisit en plus vers quel plug émettre (`mode="1_1"`) ou s'il faut diffuser à tous (`mode="1_X"`, dernier canal de sortie). Quand `ACTION_DEMANDER` est choisie, l'action réellement transmise à `env.step()` est toujours l'action MiniGrid "done" (6) — la seule véritablement neutre du jeu (agent immobile, déjà documentée comme telle en v27.4) — jamais un pas d'environnement inventé. Une pénalité `COUT_REQUETE_C3` entre dans `recompense_interne` à chaque demande : sans coût, REINFORCE apprendrait à spammer un canal gratuit.

### 14.3 Le détecteur d'impasse — contexte, jamais déclencheur

Le rollout mental (§6) calculait déjà l'écart-type de ses valeurs cumulées avant de le jeter à la ligne de normalisation :

```python
indecision_c2 = float(valeur_cumulee.std().item())
if valeur_cumulee.std() > 1e-6:
    valeur_cumulee = (valeur_cumulee - valeur_cumulee.mean()) / (valeur_cumulee.std() + 1e-8)
```

`indecision_c2` (std proche de 0 = C2 n'a pas d'avis tranché) est désormais remonté et transmis dans `RequeteC3.indecision_c2`, aux côtés de l'erreur JEPA du tick (`RequeteC3.erreur_jepa`). **Décision utilisateur explicite** : ces deux valeurs ne déclenchent jamais l'appel à C3 — elles ne font qu'informer le plug interrogé du niveau d'incertitude de l'agent au moment de la requête. Le déclenchement reste entièrement le fait de la tête motrice, un choix appris comme les 7 autres.

### 14.4 Isolation et repli — la trappe de secours

`PortC3.canal_emission` enveloppe chaque appel de plug dans un `try/except` large : aucune panne externe (réseau, timeout, format invalide) ne remonte jamais au noyau. Un plug qui échoue est mis en cooldown (`COOLDOWN_PLUG_ECHEC=200` ticks) plutôt que réinterrogé à chaque tick — la leçon retenue du seul précédent d'appel externe du projet, `professeur_gemma.py` (§ voir `docs/CHANGELOG.md` v28.0), qui n'a ni health-check ni cache d'indisponibilité et peut faire payer jusqu'à 60s de timeout par appel. Sans réponse (bus vide ou plug en échec), l'action a tout de même été jouée « à vide » : l'agent a payé `COUT_REQUETE_C3` sans bénéfice, et la curiosité intrinsèque (`DetecteurCuriositeJEPA`, §2.4) ainsi que le Sursaut de Volonté restent la réponse de repli — ils n'ont jamais été conditionnés à la présence de C3.

### 14.5 Le registre d'assimilation

Une `ReponseC3` reçue lors d'un tick où `ACTION_DEMANDER` a été jouée est mise en attente (`reponse_c3_en_attente`) et appliquée au tick **suivant** — le bus répond à une pensée déjà écoulée, jamais à celle qui vient de se jouer :

$$
\text{logits}_{finaux} \mathrel{+}= F_{C3} \cdot \text{preferences}_{C3} \qquad \text{si confiance} < \text{SEUIL\_OVERRIDE\_C3}
$$

Au-delà de `SEUIL_OVERRIDE_C3=0.85`, la réponse **impose** l'action plutôt que de biaiser les logits — le `log_prob` poussé dans le buffer d'entraînement reste alors celui de l'action réellement exécutée sous la distribution courante (`dist.log_prob(action_imposee)`), jamais celui d'un échantillon fictif, pour ne pas invalider le gradient REINFORCE (ce tick devient de facto légèrement off-policy).

Un conseil C3 suivi d'un succès (recompense visuelle positive au même tick) devient un 3ème canal du "OU doux" v27.0 (§9.1), étendu sans rien casser :

$$
w_{evenement} = 1 - \big(1 - W_{visuel} \cdot w_{visuel}\big)\big(1 - W_{vocal} \cdot w_{vocal}\big)\big(1 - W_{C3} \cdot w_{C3}\big), \qquad W_{C3} = \text{POIDS\_DOPAMINE\_C3} = 0.5
$$

Toujours bornée dans $[0,1]$ par construction, toujours rétrocompatible à l'identique si $w_{C3}=0$. Le choc dopaminergique qui en résulte appelle déjà `fortifier_synapses` (LTP par tick, §8.3) et majore `micro_boost_ancrage`, donc l'importance du souvenir dans `memoire_moyen_terme` — ce souvenir sera rejoué en priorité la nuit par l'échantillonnage pondéré de `rever()` (§10.2). Aucune perte supervisée dédiée n'est ajoutée : l'assimilation passe entièrement par les mécaniques homéostatiques déjà existantes, jamais par un nouveau canal de gradient — cohérent avec la contrainte "pas de Transformer, pas de signal supervisé externe dans la politique" du plan v26.0 (`docs/AMELIORATION_V1.md`).

### 14.6 Rétrocompatibilité des `.brain` — la greffe par recopie

Passer de 7 à 8 actions change la **forme** de `tete_motrice` (sortie), `generateur_attente`/`generateur_attente_audio` (entrée, le bloc `actions_onehot` de la concaténation `[actions_onehot, pensee]`) et du buffer `actions_eye`. `load_state_dict(strict=False)` (§ voir `persistance.py`) gère les clés *absentes* mais lève une `RuntimeError` sur un mismatch de forme d'une clé *présente* des deux côtés.

`_greffer_action_supplementaire` généralise le patron déjà utilisé pour `integrateur_bio` (filtrage conditionnel sur la forme réelle), mais par **recopie** plutôt que par **exclusion** — jeter ces couches ferait perdre des centaines de jours de tête motrice et de modèle du monde appris. Pour chaque couche affectée, chaque buffer (`base_weight`, `myeline_M`, `trace_activation`, `myeline_cumul`, `cristallisee`) est recopié à l'identique sur son ancien bloc `[:7]`, la 8ème ligne/colonne restant à l'initialisation Xavier atténuée du nouveau tenseur — exactement la sémantique de `NaultheneLinearSynaptique.agrandir()` (§8.4). `annexe_weight` repart toujours de zéro (comme `cycle_sommeil` le fait chaque nuit). Validé sur les trois `.brain` réels du dépôt, dont un cerveau de 300 jours (`naulthene_parole.brain`, palier vocal 19/19) — poids des 7 actions préservés à l'identique bit à bit après chargement.

---

## 15. Le Bus Sensoriel & l'identité C1/C2 explicite (expérimental)

> ⚠️ **Statut expérimental** : vit dans `src/naulthene/cerveau/noyau.py`, le module versionné `src/naulthene/cerveau/bus_sensoriel.py` et `src/naulthene/cerveau/persistance.py`, pas encore porté sur `colab.py`.
>
> 📖 **Cette section est un résumé.** Le détail complet (formules, schémas, table des validations, options écartées, glossaire) est dans un document dédié : **[EXPLICATIONS_v29_sens.md](EXPLICATIONS_v29_sens.md)**.

### 15.1 Les 5 sens et leur hiérarchie de coût

Jusqu'en v28.0, l'agent n'avait que ses deux sens gourmands : la vue (`porte_visuelle`, 147 dims) et l'ouïe (`porte_auditive`, 130 dims MFCC), chacun avec sa porte synaptique sommée dans `bus_latent` (§4) et sa place dans la cible JEPA (§2). La v29.0 ajoute les trois manquants — justement les moins coûteux et les plus liés à la survie — via un module dédié, `bus_sensoriel.py`, **pur numpy et qui n'importe jamais `noyau.py`** (même discipline que `exocortex/port_c3.py`, §14) :

| Sens | Gourmandise | Dims | Chemin | Cible JEPA |
|------|-------------|------|--------|------------|
| Vue | Extrême | 147 | `porte_visuelle` → `bus_latent` | ✅ |
| Ouïe | Élevée | 130 | `porte_auditive` → `bus_latent` | ✅ |
| Toucher | Moyenne | 4 | `vecteur_bio` → `integrateur_bio` | ❌ |
| Odorat | Faible | 2 | `vecteur_bio` → `integrateur_bio` | ❌ |
| Goût | Faible | 2 | `vecteur_bio` → `integrateur_bio` | ❌ |

Le **toucher** donne le contact frontal (via l'API native `can_overlap()`), l'objet en main (`carrying`) et l'orientation encodée sur le cercle $(\cos\theta, \sin\theta)$ avec $\theta = \frac{\pi}{2}\cdot\text{agent\_dir}$ — l'encodage circulaire supprime la fausse discontinuité entre les directions 3 et 0, voisines dans le monde réel mais distantes de 3 unités en entier brut. L'**odorat** décroît linéairement sur `PORTEE_ODORAT=4` cases (distance de Manhattan, comme §11). Le **goût** est une rémanence décroissant à `DECROISSANCE_GOUT=0.85`/tick, seul état inter-tick du bus, remis à zéro par épisode.

### 15.2 Pourquoi les sens faibles n'entrent pas dans `bus_latent`

Décision structurante. `perte_jepa` (§2) compare toujours l'attente au bus réel de la **vision seule** :

```python
with torch.no_grad():
    bus_reel_vision = F.relu(self.porte_visuelle(obs_suivante))
perte = F.mse_loss(attente, bus_reel_vision)
```

Sommer le toucher et la chimie dans `bus_latent` les ferait mécaniquement entrer dans ce que le modèle du monde doit prédire — trois canaux bruités venant perturber une physique visuelle apprise sur des centaines de jours, pour un gain nul (prédire l'odeur future n'est pas l'objet du JEPA). En passant par `integrateur_bio` (§ voir `integrer_bio`), ils informent la **décision** sans jamais toucher au **modèle du monde**.

`DIM_VECTEUR_BIO` passe donc de 16 à 24 dims, les 8 nouvelles étant ajoutées **en queue** — un contrat partagé entre `obtenir_vecteur_bio`, `BusSensoriel.interpreter` et `persistance._greffer_vecteur_bio_etendu` (15.4).

### 15.3 C1 et C2, enfin nommés

La distinction existait dans le code depuis la v7.0 (`tete_motrice` d'un côté, `simuler_futur_et_planifier` de l'autre, §5-7) mais restait entrelacée dans le corps de `penser()`. Elle est désormais encapsulée :

- **`_executer_c1_reflexe()`** — compression des 5 sens, lecture épisodique, intégration viscérale, réflexe moteur en latence zéro.
- **`_solliciter_c2_neocortex()`** — JEPA + rollout mental multi-échelle. Ne reçoit **que** `pensee_bio`, l'état déjà compressé par C1 : jamais les pixels, jamais le MFCC brut.

`penser()` se réduit à l'arbitrage, dont la ligne est **inchangée depuis la v13.0** (§7). C'est une **restructuration pure** : C2 reste sollicité à chaque tick, le comportement d'un cerveau existant est bit-identique à la v28.0.

> ⚠️ Le court-circuit conditionnel (« C1 saute C2 s'il est confiant ») a été **volontairement écarté** : ce serait un déclenchement sur seuil codé en dur dans le chemin de décision, exactement de la nature de ce que §14.3 s'interdit déjà pour C3. La voie cohérente, si l'économie devient un objectif, serait d'en faire une **action apprise** comme `ACTION_DEMANDER`.

### 15.4 La distillation C2 → C1 : déjà là

Résultat le plus important de l'audit v29.0 : la « boucle de distillation » de la note de conception **était déjà entièrement implémentée** par le cycle de vie de `NaultheneLinearSynaptique` (§8), et le bon geste a été de ne rien réécrire.

`annexe_weight` accumule le gradient diurne (C2 guide l'expérience) → `cycle_sommeil()` le consolide dans `base_weight` (C2 → C1) → la Cristallisation Souple (§8.5) fige définitivement les synapses les plus myélinisées, libérant C2. C'est le mécanisme d'apprendre à conduire : C2 consomme une énergie monstre au début, C1 conduit tout seul quelques mois plus tard.

### 15.5 Rétrocompatibilité — la greffe du vecteur bio

Même problème qu'en §14.6 : `DIM_VECTEUR_BIO` 16 → 24 change la **forme** de `integrateur_bio` (entrée `dim_bus+16` → `dim_bus+24`), et `load_state_dict(strict=False)` lève une `RuntimeError` sur un mismatch de forme d'une clé présente des deux côtés.

Le filtre historique **excluait** la couche, qui renaissait à neuf — c'est le symptôme exact du bug v24.0-fix4 (bouche silencieuse dans l'Arène, `integrateur_bio` étant la couche qui réinjecte la quête vocale vers `tete_vocale`). `_greffer_vecteur_bio_etendu`, appelée en amont, recopie chaque buffer sur ses colonnes existantes (y compris le booléen `cristallisee`), remet `annexe_weight` à zéro et laisse les 8 nouvelles colonnes à leur initialisation Xavier atténuée — la sémantique de `agrandir()` (§8.4). Le filtre d'exclusion reste en trappe de secours pour les mismatchs qu'on ne sait pas greffer.

**Règle générale du projet** : greffe par **recopie**, jamais par **exclusion**.

### 15.6 Télémétrie des 5 sens (v29.1)

La v29.0 câblait les sens dans la décision sans les instrumenter — corrigé en v29.1 par 7 clés W&B (`Sens_Bus_Actif`, `Sens_Toucher_Contact_Ratio`, `Sens_Toucher_Portage_Ratio`, `Sens_Odorat_Moyen`/`_Max`/`_Ticks_Actifs_Ratio`, `Sens_Gout_Ticks_Actifs`) et une ligne au bilan de nuit. Purement observationnel : jamais relu par la décision ni le gradient.

Premier diagnostic livré par cette télémétrie : **l'odorat sature sur les petites cartes** (97,6 % de couverture sur `Empty-8x8`, 100 % sur `DoorKey-6x6` avec `PORTEE_ODORAT=4`), donc il y porte peu d'information. Constat documenté, constante **inchangée** — l'arbitrage (portée réduite vs normalisation par taille de carte) appartient à l'auteur. Détail complet en [EXPLICATIONS_v29_sens.md](EXPLICATIONS_v29_sens.md) §12.

---

*Document généré à partir d'une lecture directe du code source (`agi_google_colab.py` v17, `src/naulthene/cerveau/noyau.py` jusqu'à v29.0) — voir [readme.md](../readme.md) pour la documentation narrative complète et [CLAUDE.md](../CLAUDE.md) pour les règles de maintenance du projet.*
