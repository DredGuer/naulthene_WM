# AMÉLIORATION V1 — « Le Parent remplace le Programme »

Proposition d'évolution du Cerveau Bébé (candidate **v26.0-experimental**), construite en
croisant le diagnostic du run de 1440 jours ([1440_JOURS_NAULTHENE_V1.md](../recherche/1440_JOURS_NAULTHENE_V1.md)),
l'algorithme exact ([explications_readme.md](../fonctionnement/explications_readme.md)) et l'infrastructure déjà
en place ([readme.md](../../readme.md), v22 → v25).

## Les contraintes du cahier des charges

| # | Contrainte | Comment la proposition la respecte |
|---|---|---|
| 1 | **Pas de Transformer** | Aucun bloc d'attention, aucun QKV appris, aucun empilement de blocs. Le rappel mémoire passe par un **rappel hippocampique par indices** (lecture par similarité sur la mémoire spatiale déjà existante, §C) — de la *pattern completion* façon CA3, pas de l'attention apprise. |
| 2 | **Continuer JEPA** | JEPA reste le cœur. On le **durcit** (cible EMA + garde de variance + cristallisation souple des synapses matures, §A) au lieu de le remplacer — tous les ajouts réutilisent le patron mathématique maison $x_{t+1} = x_t + (x_{cible}-x_t)\tau$. |
| 3 | **Aucune instruction encodée** | `DetecteurJalonsDoorKey` (7 paliers codés en dur sur une carte) est **retiré du chemin de promotion**. À la place : un **Parent Universel** (§B) qui observe des événements 100 % génériques (progrès, nouveauté, complétion) et guide par habituation/célébration — comme un vrai parent, qui n'a pas le plan du labyrinthe non plus. |
| 4 | **Guider comme un enfant qu'on fait grandir** | Étayage dégressif (Vygotsky) : le Parent aide *juste assez*, et son aide **s'estompe automatiquement** à mesure que la compétence réelle monte (§B.4). |
| 5 | **Réussir MiniGrid + apprendre à parler** | La promotion redevient conditionnée aux **vraies victoires** (§B.6) ; le vocal garde son École de Rattrapage et gagne la **voix humaine enregistrée** en option (§D). |

---

## 0. Rappel du diagnostic (pourquoi ces choix)

Trois causes racines identifiées sur le run `Run_25_Bebe_Developpemental_4ans` :

1. **Collapse JEPA** : erreur 0,0000 en fin de run → cascade neurogenèse gelée (Bus 32/96),
   rêve 0,38 %, dopamine 2,4, plasticité 0,14, 18 164 synapses mortes. Le stop-gradient seul
   ne suffit pas.
2. **Proxy-hacking** : 6 218 portes franchies, 89 920 « records de proximité »…
   et `Recompense_Moyenne = 0` partout. Les détecteurs de progrès sont devenus la vraie
   fonction-objectif ; les 7 paliers DoorKey ont promu l'agent sans qu'il sache sortir.
3. **Parent punitif** : `Feedback_Parent_Jour` cumulé **−629 095** (négatif 1194 jours sur
   1200). L'agent apprend à éviter, pas à réussir.

La proposition attaque les trois par **quatre chantiers** : A (JEPA durci), B (Parent Universel),
C (rappel par indices), D (voix humaine). A et B sont critiques ; C débloque la planification
longue ; D est l'option demandée.

---

## A. JEPA durci — apprendre sans s'éteindre

### A.1 Cible EMA (`porte_visuelle_cible`)

Aujourd'hui la cible JEPA est `ReLU(porte_visuelle(obs_suivante))` sous `no_grad()` — le même
encodeur que la prédiction. Quand la politique devient répétitive, prédiction et cible glissent
ensemble vers une constante. Le correctif standard (BYOL, I-JEPA) : la cible vient d'un
**encodeur jumeau à mise à jour lente**, jamais entraîné par gradient :

$$
W_{cible} \leftarrow W_{cible} + (W_{porte\_visuelle} - W_{cible}) \times \tau_{EMA},
\qquad \tau_{EMA} = 0.01\ \text{par nuit}
$$

C'est **littéralement la relaxation exponentielle maison** ([explications §1](../fonctionnement/explications_readme.md)),
appliquée aux poids : l'encodeur-cible « suit » l'encodeur vivant avec un jour de retard
émotionnel, comme la dopamine suit les événements. Zéro concept étranger au projet.

- Implémentation : un buffer `poids_cible` dans `NaultheneLinearSynaptique` (comme `base_weight`
  et `myeline_M`, déjà des buffers), mis à jour dans `cycle_sommeil_global()`. Coût mémoire :
  une matrice de plus pour `porte_visuelle` (et `porte_auditive`) uniquement.
- `perte_jepa` cible désormais `ReLU(porte_visuelle_cible(obs_suivante))` — toujours sous
  `no_grad()`, le stop-gradient est conservé, il est juste **secondé**.

### A.2 Garde de variance (anti-constante explicite)

Un terme VICReg-minimal, une seule ligne de plus dans `perte_totale` :

$$
\mathcal{L}_{variance} = c_{var} \cdot \frac{1}{D_{bus}} \sum_{i=1}^{D_{bus}}
\max\big(0,\ \sigma_{min} - \sigma_i(z)\big), \qquad \sigma_{min}=0.1,\ c_{var}=0.5
$$

où $\sigma_i(z)$ est l'écart-type de la dimension $i$ du `bus_latent` sur la journée. Une
dimension qui cesse de varier **coûte** — la solution constante devient une perte, plus un
refuge. Ce n'est pas un Transformer ni un gros ajout : c'est un plancher de vie sur les neurones.

### A.3 L'Ennui — recycler l'effondrement en motivation

Le run a montré que « erreur JEPA basse » est ambigu : maîtrise **ou** mort. Le discriminant est
la **variance de la cible** :

```
si  erreur_jepa_moy < SEUIL_ENNUI  et  variance_bus < SEUIL_VARIANCE_ENNUI :
    → le monde n'apprend plus rien au bébé  →  ENNUI
```

Réaction : **pas** une récompense de plus (leçon du proxy-hacking) — on passe par l'homéostasie
déjà en place (v18) : l'ennui **vide la jauge `Bio_Stimulation`**, exactement comme la faim vide
la satiété. La quête auto-générée `SURVIVAL_STIMULATION` prend le relais et pousse l'agent vers
la nouveauté avec la machinerie de drive existante (Hull), sans nouveau canal de récompense à
hacker. Un enfant qui s'ennuie va chercher du nouveau — il n'est pas « payé » pour ça, il ne
*supporte pas* l'ennui.

### A.4 Plancher de plasticité et érosion prudente

- `plasticite_base = max(0.30, plasticite_base)` — le figement terminal (0,14) devient impossible ;
  un enfant, même démotivé, reste plastique.
- Érosion nocturne **gelée** quand aucune neurogenèse n'est possible ET que le rêve est sous
  `TAILLE_MIN_REVE` : on n'érode pas un cerveau qui n'a plus les moyens de reconstruire
  (les 18 164 synapses mortes venaient de là, [1440_JOURS §3](../recherche/1440_JOURS_NAULTHENE_V1.md)).

**Effet attendu en chaîne** : erreur JEPA stabilisée à un plateau non nul → le thermostat de
neurogenèse peut se réarmer (Bus > 32, enfin) → l'importance des souvenirs ne s'effondre plus →
le rêve continue → la dopamine garde sa source de curiosité.

### A.5 La Cristallisation Souple — protéger sans paralyser

Le plancher global de §A.4 (`plasticite_base ≥ 0.30`) protège le cerveau *entier* d'un coup, à
l'aveugle — c'est un filet de sécurité, pas une mémoire. Or les 18 164 synapses mortes du run ne
sont pas toutes égales : certaines codaient un comportement acquis des milliers de fois (« ouvrir
une porte »), d'autres n'ont jamais vraiment servi. **Un plancher uniforme protège les deux de la
même façon — ou n'en protège aucune assez fort.** La nuance manquante, indispensable pour ne pas
retomber dans le défaut inverse : un **hard freeze** (poids totalement gelés) rendrait l'agent
incapable de réviser un fondamental si le monde change (une porte d'une autre couleur, un nouvel
angle de couloir) — on veut protéger la synapse **de l'oubli passif** (l'érosion du sommeil), pas
la protéger **de l'apprentissage actif** (le gradient du jour).

**L'analogie du chemin de montagne.** Un sentier peu emprunté est de l'herbe : la pluie (le
sommeil) peut l'effacer en une nuit. Un sentier emprunté des milliers de fois se grave dans la
roche : la pluie ne l'efface plus, mais les marcheurs peuvent toujours l'élargir, le dévier ou en
tracer un meilleur juste à côté. La roche résiste à l'érosion, pas aux pas.

**Mécanisme — accumulation de myéline dans le temps.** Une seconde trace, distincte de la
myéline instantanée `myeline_M` (§8.1, maximum courant intra-journée), qui accumule sur
plusieurs *nuits* avec le patron de relaxation maison :

$$
M_{\text{cumul}}(t) = \alpha \cdot M_{\text{cumul}}(t-1) + (1 - \alpha) \cdot M(t), \qquad \alpha = 0.95
$$

où $M(t)$ est la myéline consolidée de la nuit $t$ (post-`cycle_sommeil`). Une synapse
sollicitée fortement et régulièrement (les portes, ouvertes des centaines de fois) voit
$M_{\text{cumul}}$ monter et se stabiliser haut ; une synapse sollicitée une fois puis oubliée
retombe vers 0 avec la même relaxation.

**L'interrupteur de cristallisation.** Dès que $M_{\text{cumul}} \ge S_{\text{cristal}} = 0.80$,
la synapse reçoit un flag `Cristallisee = True` — un **cliquet à sens unique** : une fois levé, il
ne redescend jamais, même si la synapse redevient calme ensuite (seul le poids lui-même, via le
gradient diurne, peut encore évoluer). Granularité retenue à l'implémentation : **par poids
individuel** (buffer booléen de la taille de la matrice de poids par couche) plutôt que par
neurone de sortie — coût mémoire négligeable même à `dim_bus=96` (deux buffers de plus par couche,
même forme que `myeline_M`/`trace_activation` déjà alloués), et ça permet à `agrandir()` de
réutiliser exactement le même chemin de code (resize + copie par segment) que ces deux buffers
existants ; le grain par neurone aurait sur-protégé (toute une ligne de poids entrants dès qu'un
sous-ensemble est actif), contraire à l'analogie du sentier individuel.

**La règle dissymétrique — sommeil ≠ gradient.** C'est le cœur du mécanisme : la protection
n'agit *que* sur l'érosion nocturne, jamais sur l'apprentissage diurne.

- 🌙 **Pendant le sommeil (`cycle_sommeil`, §8.2)** — l'érosion de l'Étape 3 utilise désormais une
  myéline effective plancher-protégée plutôt que la myéline brute.
- ☀️ **Pendant la journée (rétropropagation)** — totalement inchangé. `annexe_weight` reçoit le
  gradient normalement, sur *toutes* les synapses, cristallisées ou non :
  $$
  W_{annexe} \leftarrow W_{annexe} - \eta \cdot \nabla_{W_{annexe}} \mathcal{L}
  $$
  Si l'environnement change (nouvelle couleur de porte, nouvel angle), l'erreur JEPA remonte sur
  ce cas précis et le gradient redevient non nul — la synapse cristallisée **continue d'apprendre
  et de se réviser**, elle est juste protégée de mourir de silence pendant qu'elle ne sert pas.

**Correctif « Falaise » sigmoïde (implémenté dans `noyau.py`, remplace le plancher rigide initial).**
La première version de ce document proposait un plancher constant $M_{\text{min}} = 0.50$ appliqué
en tout-ou-rien dès que `Cristallisee = True`. À l'implémentation, ce plancher rigide a été
remplacé par une **falaise continue** : une sigmoïde de $M_{\text{cumul}}$ centrée sur
$S_{\text{cristal}}$, plus fidèle au principe du projet — « régulation dynamique continue, jamais
de règle en dur » — que ne l'était une marche d'escalier.

$$
p_{\text{protection}} = \sigma\big(k \cdot (M_{\text{cumul}} - S_{\text{cristal}})\big)
= \frac{1}{1 + e^{-k(M_{\text{cumul}} - S_{\text{cristal}})}}, \qquad k = K_{\text{raideur\_cristal}} = 10.0
$$

$$
M_{\text{norm,effectif}} = \max\big(M_{\text{norm}},\ \mathbb{1}[\text{Cristallisee}] \cdot p_{\text{protection}}\big)
$$

Le cliquet `Cristallisee` reste la mémoire de consolidation irréversible (§ ci-dessus) ; la
sigmoïde ne lisse que **l'intensité** de la protection une fois le cliquet levé :
- Si $M_{\text{cumul}} \gg S_{\text{cristal}}$ (synapse très éprouvée) : $p_{\text{protection}} \to
  1.0$, érosion nocturne quasi nulle — ancrage indestructible des fondamentaux (se déplacer,
  repérer la nourriture, reconnaître une porte).
- Une synapse **jamais** cristallisée (`Cristallisee = False`) ne bénéficie d'aucun plancher : elle
  s'érode au taux plein et tombe sous le masque de mort (Étape 4) en temps fini — **zéro synapse
  fantôme** qui traînerait des centaines de nuits avec une érosion ralentie sans raison.

| | Synapse non-cristallisée | Synapse cristallisée |
|---|---|---|
| Dopamine basse prolongée | Myéline → 0, érosion max, élagage en temps fini | $p_{\text{protection}} \to 1.0$, érosion quasi nulle |
| Sommeil (`cycle_sommeil`) | Peut être élaguée (`< 1e-4`) | Ne peut jamais atteindre le seuil d'élagage |
| Gradient diurne | Apprend normalement | **Apprend normalement — aucune différence** |

**Cohérence avec les invariants du projet.** Aucun concept étranger : $M_{\text{cumul}}$
réutilise le patron $x_{t+1} = x_t + (x_{cible}-x_t)\tau$ déjà de règle dans tout le projet
([explications §1](../fonctionnement/explications_readme.md)) ; la falaise sigmoïde est un **affinement continu**
du plancher global de §A.4, pas un mécanisme concurrent — les deux coexistent (le plancher global
protège tout le cerveau faiblement, la cristallisation protège les synapses avérées fortement) ;
et la distinction buffer (`myeline_M`, `myeline_cumul`, `Cristallisee`, non optimisés) vs
`nn.Parameter` (`annexe_weight`, optimisé) suit exactement la séparation base/annexe déjà en place
(§8.1) — deux buffers de plus par couche `NaultheneLinearSynaptique`, pas une nouvelle catégorie
d'état.

---

## B. Le Parent Universel — guider sans programme

C'est le cœur philosophique de la proposition. Aujourd'hui, le « guidage » est un programme :
`DetecteurJalonsDoorKey` connaît la carte (7 jalons, noms codés en dur), et le Module Parent v25
est un juge à seuils fixes qui a dit « Non ! » un demi-million de fois. **Un vrai parent ne
connaît pas le plan du labyrinthe et ne note pas sur 20** : il regarde, s'émerveille de ce qui
est *nouveau*, se lasse de ce qui est répété, et fait la fête quand l'enfant *finit* quelque
chose. Trois mécanismes suffisent à encoder ça — tous génériques, aucun ne mentionne une carte.

### B.1 Ce que le Parent observe (événements génériques uniquement)

Le Parent est un module unique (`ParentUniversel`) branché sur les événements **déjà émis** par
les détecteurs génériques ([explications §11](../fonctionnement/explications_readme.md), `DetecteurFranchissementPortes`,
`DetecteurProgresPersonnel`) plus deux nouveaux, tout aussi agnostiques :

| Événement | Source | Réaction parentale |
|---|---|---|
| `progres` (record de proximité, porte) | détecteurs génériques existants | Encouragement **soumis à habituation** (§B.2) |
| `nouveaute` (état latent jamais vu, distance kNN à la mémoire spatiale > seuil) | mémoire §C | Encouragement doux (« regarde ce que tu as trouvé ! ») |
| `completion` (épisode réellement gagné, `recompense_env > 0`) | l'environnement lui-même | **Célébration** (§B.3) |
| `detresse` (patience presque épuisée + dopamine basse) | état interne existant | Apaisement : petit ressort dopaminergique vers la neutralité — jamais de punition |

`DetecteurJalonsDoorKey` **n'alimente plus la promotion** — il peut rester en télémétrie
descriptive (savoir *où en est* le bébé), mais il ne décide plus rien. C'est la traduction
exacte de « aucune instruction encodée » : le système sait *observer* génériquement, il ne sait
plus *prescrire* spécifiquement.

### B.2 L'habituation — l'anti-proxy-hacking naturel

Le bug central du run (6 218 portes, zéro sortie) vient de récompenses de sous-buts **plates** :
la 6 000ᵉ porte rapporte autant que la première. Aucun parent ne fonctionne comme ça. On donne
au Parent une mémoire de lassitude par type d'événement, la relaxation maison encore :

$$
w_{parent}(e) = w_{base}(e) \times \underbrace{e^{-n_e / \tau_{hab}}}_{\text{lassitude}},
\qquad \tau_{hab} = 20\ \text{(par jour, remis à zéro chaque nuit)}
$$

où $n_e$ = nombre de fois que l'événement de type $e$ (même détecteur, même granularité) s'est
produit aujourd'hui. La première porte du jour émerveille (poids plein), la vingtième laisse le
Parent indifférent (poids ≈ 0,37), la centième ne rapporte rien. **Tourner en rond devient
mécaniquement non rentable** — sans coder une seule connaissance de la carte. La seule stratégie
qui ne s'épuise jamais : faire du *nouveau* (la nouveauté §B.1 réarme les compteurs) et *finir*
(§B.3, jamais habitué).

### B.3 La célébration — graver la chaîne complète

L'événement `completion` (vraie victoire) est le **seul** exempt d'habituation, et il déclenche
un traitement de faveur qui existe déjà dans le code : le **LTP hebbien v20**
([explications §8.3](../fonctionnement/explications_readme.md)). Un pic dopaminergique maximal
(`poids_evenement = 1.0`) au moment de la sortie grave immédiatement, via la trace d'éligibilité
$E_t$ (fenêtre ~10 ticks), **les synapses actives pendant les derniers gestes de la chaîne**
clé→porte→sortie. C'est précisément le chaînon qui manquait : le run apprenait les
sous-comportements séparément mais ne consolidait jamais la *séquence*. Ici, la fête du Parent
et la LTP font le travail ensemble — la biologie du projet servait déjà ça, elle n'était juste
jamais nourrie du bon événement.

### B.4 L'étayage dégressif — la Zone Proximale de Développement

Le Parent module son aide selon la compétence réelle, mesurée par le taux de victoires
vraies sur les 20 derniers jours (fenêtre déjà utilisée par la patience adaptative,
[explications §11.2](../fonctionnement/explications_readme.md)) :

$$
\text{etayage} = 1 - \text{taux\_victoires}_{[20j]}
$$

- **etayage ≈ 1** (le bébé n'y arrive pas) : le Parent encourage plus fort les `progres` et
  `nouveaute` (facteur ×(1+etayage)), et la patience reçoit le coefficient d'Abnégation.
- **etayage → 0** (le bébé maîtrise) : les encouragements de sous-buts **s'éteignent d'eux-mêmes**,
  seule la célébration de complétion demeure — le guidage disparaît progressivement, comme les
  petites roues d'un vélo. C'est le *guidance fading* de Vygotsky, et c'est la généralisation
  propre de ce que le « Mode Libre » v13 faisait par un seuil brutal (`palier_cible >= 5`).

### B.5 Rééquilibrer Oui/Non — le Parent bienveillant

Le canal « Non ! » (cortisol, v25) est conservé mais bridé :

- **Budget quotidien** : au plus `RATIO_NON_MAX = 1` « Non ! » pour 3 « Oui ! » émis dans la
  journée (au-delà, le Parent se tait — l'indifférence est déjà un signal, via la friction
  dopaminergique naturelle).
- **Feedback relatif, pas absolu** : le « Oui ! » vocal se déclenche sur *progrès personnel*
  (score de formants du jour > moyenne des 5 derniers jours), pas sur un seuil absolu
  (`SEUIL_PARENT_OUI = 0.45`) hors de portée d'un débutant. « Mieux qu'hier » est le seul
  standard qu'un enfant puisse toujours atteindre.

Cible mesurable : `Feedback_Parent_Jour` cumulé **positif** sur le prochain run (contre −629 095).

### B.6 La promotion redevient une vraie remise de diplôme

La règle v17 existait déjà et était saine ([explications §11.1](../fonctionnement/explications_readme.md)) :
**2 journées consécutives avec victoire réelle**. On la rétablit comme **seul** chemin de
promotion de niveau MiniGrid — plus aucun palier partiel ne peut promouvoir. Les niveaux
redeviennent la mesure de la compétence, pas de l'ancienneté. (Côté vocal, rien à changer :
l'École de Rattrapage à seuil progressif a bien fonctionné — 10 paliers en 846 jours, sans
triche.)

---

## C. Le rappel hippocampique par indices — se souvenir de la clé, sans Transformer

Le blocage terminal du run est un échec de **planification longue** : l'agent ne sait pas
rappeler « où est la clé » au moment où il voit la porte. La solution Transformer (attention)
est exclue par le cahier des charges — et elle n'est pas nécessaire, parce que le cerveau a
**déjà** l'organe qu'il faut : la `MemoireEpisodiqueSpatiale` v20 (200 souvenirs persistants,
saturée mais **jamais lue par le réseau** pour décider).

### C.1 Le mécanisme : lecture par similarité (pattern completion, façon CA3)

À chaque tick, au moment de la `lecture_episodique` :

1. Prendre le `bus_latent` courant comme **indice de rappel** (la situation présente).
2. Chercher les $k=3$ souvenirs les plus proches dans la mémoire spatiale
   (similarité cosinus — un simple produit matriciel sur 200 vecteurs, négligeable).
3. Ne rappeler que si le meilleur souvenir dépasse `SEUIL_RAPPEL = 0.5` de similarité
   (sinon : pas de souvenir pertinent, on ne rappelle rien — pas de bruit).
4. Le rappel $m_t$ (moyenne des $k$ souvenirs pondérée par leur similarité **et leur importance**)
   est concaténé au contexte existant dans `fusion_memoire` :

```python
x = F.relu(self.fusion_memoire(torch.cat([x, contexte, rappel], dim=-1)))
```

**Pourquoi ce n'est pas un Transformer** : aucun poids d'attention appris (pas de $W_Q, W_K, W_V$),
aucun bloc empilé, aucune position — c'est une lecture de plus proche voisin sur une mémoire
externe, le mécanisme de *Neural Episodic Control* et du rappel par indices de l'hippocampe
biologique (une odeur rappelle la madeleine ; la vue de la porte rappelle l'endroit de la clé).
La seule chose apprise reste `fusion_memoire`, qui existe déjà — elle apprend à *utiliser* le
rappel, pas à le calculer.

### C.2 Ce qu'on stocke : les moments gravés par la dopamine

Plutôt que stocker tous les ticks (bruit), la mémoire n'archive que les états latents des ticks
à `poids_evenement > 0` — ramasser la clé, franchir une porte, manger, être célébré (§B.3).
Le même signal qui déclenche la LTP hebbienne tague le souvenir : **ce qui grave les synapses
grave aussi la mémoire épisodique**. Un seul critère de saillance, déjà en place, deux mémoires
servies.

### C.3 Cohérence avec les invariants du projet

- Le Système 2 en profite gratuitement : `simuler_futur_et_planifier` part d'une `pensee`
  enrichie du rappel — le rollout linéaire (1, 3, 7) et son argmax glouton **ne changent pas
  d'un iota** (contrainte protégée par CLAUDE.md).
- `agrandir()` doit répercuter la nouvelle entrée de `fusion_memoire` dans `segments_in`
  (règle CLAUDE.md sur la neurogenèse) — point de vigilance d'implémentation n°1.

---

## D. La Voix du Parent — l'option « j'enregistre ma voix »

L'infrastructure v22 rend cette option étonnamment peu coûteuse : les références vocales sont
déjà des **MFCC mis en cache** (`lecons_vocales.CacheReferencesVocales`, alimenté par `say`), et
la bouche vise déjà des **formants F1/F2** extraits de la cible. Il suffit de changer la source.

### D.1 Enregistrement (une fois, ~10 minutes)

Un petit script `enregistrer_voix_parent.py` (nouveau, autonome) :

```
voix_parent/
  a.wav  e.wav  i.wav  o.wav  u.wav          # les 5 voyelles, tenues ~1 s
  ba.wav  ma.wav  pa.wav                       # syllabes
  papa.wav  maman.wav  porte.wav               # mots du curriculum
  oui.wav  non.wav  bravo.wav                  # le feedback social du Parent
```

Micro du Mac, 16 kHz mono, 2-3 prises par item (la variance naturelle de ta voix est une
*feature* : le bébé apprend un phonème, pas un fichier).

### D.2 Le bébé apprend TA voix

- `CacheReferencesVocales.prechauffer()` charge `voix_parent/*.wav` **en priorité**, et ne
  retombe sur `say` que pour les items manquants — même pipeline MFCC, zéro changement en aval.
- Les formants cibles ne viennent plus de la table codée en dur `VOYELLES_CIBLES` mais sont
  **extraits de tes enregistrements** (estimation LPC, `scipy.signal` — standard, pas de réseau) :
  le babil converge vers *tes* F1/F2, pas vers ceux d'une table générique. Ton « a » devient
  la définition du « a ». C'est le pendant technique du *motherese* : l'enfant calibre sa bouche
  sur la voix qu'il entend le plus.

### D.3 Le Parent parle avec ta voix

Les « Oui ! » / « Non ! » / « Bravo ! » du Parent Universel (§B) sont **joués depuis tes
enregistrements** (et leurs MFCC injectés dans `porte_auditive` comme perception réelle) :
le feedback social n'est plus un scalaire silencieux, c'est un **son entendu**, dans la même
oreille qui apprend les voyelles. À terme (hors périmètre v26), cela ouvre l'association son
de la récompense ↔ situation — le mot « bravo » devenant lui-même prédicteur de dopamine,
comme chez l'enfant réel.

### D.4 Garde-fous

- `say` reste le repli complet : sans dossier `voix_parent/`, comportement identique à v25.
- Les MFCC de tes wav sont mis en cache une fois au préchauffage (comme aujourd'hui) — aucun
  coût par tick.
- Vie privée : les wav restent locaux, jamais versionnés (ajout `voix_parent/` au `.gitignore`).

---

## E. Ce qu'on ne touche pas (invariants protégés)

Conformément à [CLAUDE.md](../../CLAUDE.md) et à la philosophie du projet :

- **Rollout mental linéaire** (1, 3, 7), branchement unique puis argmax — inchangé.
- **Pas de taille de batch de rêve fixe** — le pourcentage reste émergent ; §A.4 ne change que
  l'érosion, pas le rêve.
- **Clip dopaminergique** `[DOPAMINE_MIN, DOPAMINE_MAX]` après chaque mise à jour — le canal
  cortisol bridé de §B.5 reclippe comme en v25.
- **Le patron relaxation exponentielle** — les cinq nouveautés à dynamique (EMA §A.1,
  habituation §B.2, étayage §B.4, ennui §A.3 via les jauges bio, cristallisation §A.5)
  le réutilisent toutes.
- **La rétropropagation reste 100 % active sur `annexe_weight`, toujours** — la cristallisation
  souple (§A.5) ne gèle **jamais** le gradient diurne, seulement l'érosion nocturne ; un hard
  freeze des poids romprait la capacité de l'agent à réviser un fondamental si le monde change
  (nouvelle couleur de porte, nouvel angle), ce que le projet exclut explicitement.
- **Masquage des 240 premiers jours** — conservé tel quel : c'est la partie du paradigme que le
  run a *validée* (JEPA 1,49 → 0,20 sans récompense).
- Toute nouvelle couche/entrée respecte le triptyque `__init__` / `cycle_sommeil_global()` /
  `declencher_neurogenese()` (règle CLAUDE.md).

---

## F. Plan de validation — run de contrôle avant les 1440 jours

Un run court `python cursus_bebe.py --jours 300` (cerveau neuf, pour couvrir masquage +
60 jours de Parent) avec critères **Go/No-Go** chiffrés :

| Critère | Seuil Go | Ce que ça valide | Contre-référence run v25 |
|---|---|---|---|
| Erreur JEPA J250-300 | plateau **> 0,02** et **< 0,5** | anti-collapse §A | tendait vers 0,0000 |
| Variance `bus_latent` (nouvelle métrique W&B) | > 0,1 en continu | §A.2 | non mesurée (invisible) |
| `Recompense_Moyenne` post-J240 | **> 0 sur ≥ 10 jours** | victoires réelles §B | 0 partout |
| Neurogenèse | ≥ 1 mutation après J100 | thermostat réarmé | 1 seule (J39), plus jamais |
| `Feedback_Parent_Jour` cumulé | **positif** | Parent bienveillant §B.5 | −629 095 |
| Ratio portes/victoires | < 50:1 | anti proxy-hacking §B.2 | 6 218:19 (327:1) |
| `Pourcentage_Reve` fin de run | > 5 % | cascade cassée | 0,38 % |
| Score vocal (si voix enregistrée) | progression ≥ v25 au même jour | §D non régressif | paliers 1→5 avant J240 |

Nouvelles métriques W&B à logger (leçon de l'invisibilité du régime Doctorat J456-1440) :
`Variance_Bus`, `Rappels_Memoire_Jour`, `Habituation_Moyenne`, `Etayage`, `Ratio_Oui_Non`,
et surtout **`Niveau`/`Palier_Cible`/`Mode_Libre` loggés tous les jours** jusqu'au bout.

### Ordre d'implémentation recommandé

1. **§A (JEPA durci)** — sans lui, tout se refige ; testable seul sur 60 jours masqués
   (l'erreur doit plafonner, pas s'annuler).
2. **§B (Parent Universel)** — dépend de rien, remplace les chemins de promotion.
3. **§C (rappel par indices)** — après A (il lit un latent sain) ; c'est lui qui doit débloquer
   le Doctorat.
4. **§D (ta voix)** — indépendant, peut se faire en parallèle ; commence par enregistrer les
   16 wav.

---

## G. Glossaire des nouvelles constantes proposées

| Constante | Valeur proposée | Rôle | Chantier |
|---|---|---|---|
| `TAUX_EMA_CIBLE` | 0.01 / nuit | Vitesse de suivi de l'encodeur-cible | A.1 |
| `SIGMA_MIN_BUS` / `COEFF_VARIANCE` | 0.1 / 0.5 | Plancher de variance par dimension du bus | A.2 |
| `SEUIL_ENNUI` / `SEUIL_VARIANCE_ENNUI` | 0.01 / 0.05 | Détection du couple (erreur basse, variance basse) | A.3 |
| `PLANCHER_PLASTICITE` | 0.30 | Plasticité minimale incompressible | A.4 |
| `ALPHA_CRISTAL` | 0.95 | Vitesse d'accumulation de la myéline cumulée inter-nuits | A.5 |
| `SEUIL_CRISTAL` | 0.80 | Seuil de $M_{\text{cumul}}$ déclenchant `Cristallisee = True` | A.5 |
| `K_RAIDEUR_CRISTAL` | 10.0 | Raideur de la falaise sigmoïde de protection (remplace le plancher rigide `MYELINE_MIN_CRISTAL` initialement proposé) | A.5 |
| `TAU_HABITUATION` | 20 évts/jour | Lassitude parentale par type d'événement | B.2 |
| `SEUIL_RAPPEL` / `K_RAPPEL` | 0.5 / 3 | Similarité minimale et nombre de souvenirs rappelés | C.1 |
| `RATIO_NON_MAX` | 1 « Non » / 3 « Oui » | Budget quotidien du canal cortisol | B.5 |
| `DOSSIER_VOIX_PARENT` | `voix_parent/` | Enregistrements humains (prioritaires sur `say`) | D |

---

> ⚠️ **Statut** : proposition **v26.0-experimental** — à implémenter dans `agi_local_test.py`
> (+ `cursus_bebe.py`, `lecons_vocales.py`, nouveau `enregistrer_voix_parent.py`) uniquement,
> jamais dans `agi_google_colab.py` avant validation sur run long (règles
> [CLAUDE.md](../../CLAUDE.md), section « Variante Locale de Test »). À la mise en œuvre : entrée
> CHANGELOG.md + section « Nouveautés v26.0 » dans readme.md, avec mention explicite
> **expérimental**.
>
> *Document de conception rédigé le 2026-07-24, croisant
> [1440_JOURS_NAULTHENE_V1.md](../recherche/1440_JOURS_NAULTHENE_V1.md) (diagnostic chiffré du run
> u773ulep), [explications_readme.md](../fonctionnement/explications_readme.md) (algorithme v17-v25) et
> [readme.md](../../readme.md) (infrastructure vocale v22-v25).*
