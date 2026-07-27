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

**Choc au succès** (`poids_evenement > 0`, le maximum des poids de tous les détecteurs actifs ce tick) :
$$
D_{t+1} = D_t + (D_{max} - D_t) \times 0.9 \times w_{evenement}
$$

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

---

*Document généré à partir d'une lecture directe du code source (`agi_google_colab.py` v17, `agi_local_test.py`) — voir [readme.md](../readme.md) pour la documentation narrative complète et [CLAUDE.md](../CLAUDE.md) pour les règles de maintenance du projet.*
