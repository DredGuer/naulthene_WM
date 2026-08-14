# Chantier v40 / v40.1 — La Planification Émergente & l'Envie de Vivre

> **Nature** : chantier livré sur branche, en attente de validation par run long.
> Branches : `feat/v40-planification-emergente` puis `feat/v40.1-envie-de-vivre`.
> Portée : `noyau.py` uniquement — `colab.py` **n'est pas touché**.

---

## Ce que ces deux versions répondent

Deux questions distinctes, que le projet confondait :

| Version | La question | La réponse |
|---|---|---|
| **v40** | « est-ce que je **planifie** ? » | une **balance** okay / danger |
| **v40.1** | « est-ce que je **tente** ? » | une **dynamique** multiplicative |

Un agent peut savoir délibérer et refuser d'agir. Rien dans le cerveau ne portait la
seconde question : l'envie d'essayer était implicite et constante.

---

# Partie 1 — la v40 : la planification émergente

## Le problème

`force_planification` valait **0,5** en mode guidé et **0,85** en mode libre. Deux nombres
posés à la main, jamais confrontés à une mesure, et qui décidaient du poids de C2 dans
chaque décision de l'agent.

L'ablation du 14 août 2026 a montré qu'**aucune valeur unique ne peut être juste** :

| Niveau | Effet de couper C2 |
|---|---|
| `DoorKey-5x5` | **+11,7 pts** — le succès est **multiplié par 4,5** |
| `DoorKey-6x6` | −5,0 pts |
| `DoorKey-8x8` | −3,3 pts |

Sur la petite carte la planification **nuit** ; dès qu'elle grandit, elle **aide**. Une
constante qui devrait dépendre du contexte était figée pour tous les contextes.

## La formulation

> « C1 a toujours raison, **sauf si** C2 estime que le bénéfice dépasse le risque au vu des
> expériences passées. »
>
> *(L'enfant est entièrement piloté par C1 : chaque fois qu'il gagne = OKAY, chaque fois
> qu'il perd = DANGER. C2 mesure si le pari en vaut la peine.)*

## La mécanique

$$f_{planif} = \frac{\text{OKAY}}{\text{OKAY} + \text{DANGER} + \text{PRUDENCE\_NAISSANCE}}$$

`OKAY` et `DANGER` sont les sommes pondérées des retours **réellement ressentis**. Rien
n'est déclaré : l'agent ne sait pas ce qu'est une victoire, il sait qu'il a ressenti *n*
fois du bon et *m* fois du mauvais.

`PRUDENCE_NAISSANCE = 1.0` est un **a priori de Laplace** — une observation fictive de
prudence, qui donne un sens à la fraction quand rien n'a encore été vécu. À la naissance
$f = 0/1 = 0$ : **C1 seul**, littéralement l'enfant de la formulation.

## Trois constantes supprimées

| Constante | Valeur | Ce qu'elle décrétait |
|---|---|---|
| `FORCE_PLANIFICATION_GUIDE` | 0.5 | poids de C2 en mode guidé |
| `FORCE_PLANIFICATION_LIBRE` | 0.85 | poids de C2 en mode libre |
| `RATIO_C1C2_VISE` | 2.0 | « C2 doit peser 2× C1 » — **sans aucune mesure** |

`VIGUEUR_MIN_C1` devient la fonction `vigueur_min_c1(f) = AMPLITUDE_C2_NORMALISEE × f` :
la **parité**, seul point de référence non arbitraire. Le rapport de force n'est plus
décrété, il est une **conséquence** de l'expérience.

La bascule Guidé/Libre disparaît avec elles : plus de seuil de palier qui fait sauter la
planification d'un coup.

## Le cliquet

`OUBLI_OKAY = 0.9995` / `OUBLI_DANGER = 0.99990` — le danger s'efface **~5× plus lentement**.
Repris à l'identique de `reference_choc_dopamine` (v37.1-fix1). Sans cette asymétrie, une
bonne série effacerait la mémoire d'un danger réel, et l'agent redeviendrait imprudent là
où il s'était déjà brûlé.

## ⚠️ Deux défauts trouvés en implémentant

### 1. La source n'était pas signée

Première version branchée sur `chocs_dopamine_journee`. Mais `poids_evenement` est une
**intensité, toujours positive** — la distillation v37.1 ne s'intéresse qu'à « à quel point
c'était marquant », jamais à « était-ce bon ou mauvais ».

Mesuré sur 10 jours : `danger` restait à **0,00 exact**, `f` saturait à **0,97**. L'agent
ne pouvait *jamais* enregistrer un échec.

> **Le DANGER exige une grandeur qui peut être négative.** Une intensité ne porte pas de
> jugement. Source corrigée : `recompenses_journee`.

### 2. La mauvaise unité

Compté par tick, $f$ passait de **0,000 à 0,906 en une seule nuit** (400 ticks contre un a
priori de 1,0). L'agent naissait prudent et délibérait largement dès le lendemain —
l'inverse exact de « c'est l'expérience qui fera grandir la force ».

**L'unité juste est la journée** : au plus 1 point de vécu par jour, normalisé par
`reference_choc_dopamine`. Mesuré après correctif :

```
j1  🐣 réflexe pur              force 0.117
j2  🌱 planification naissante  force 0.281
j8  🌱                          force 0.335  ← le danger commence à s'inscrire
j13 🌱                          force 0.408
```

---

# Partie 2 — la v40.1 : l'envie de vivre

## La formulation

> « L'envie de vivre pousse au maximum la pondération à essayer quand même. Cependant quand
> C2 sera assez fort et l'expérience de C1 assez construite, il y a un risque non
> négligeable que l'envie de vivre diminue **au risque de tuer l'agent**. C'est le jeu de la
> vie. »
>
> « C1 est lui-même lié à cet élément comme une force qui est comme de **l'acceptation** et
> devient **exponentielle** liée à la compréhension de C2. »

## Ce que ce n'est pas

**Pas un troisième module** posé à côté de C1 et C2. L'envie de vivre est le **couplage
entre les deux** — ce qui fait que C1 accepte d'autant plus que C2 comprend.

## Le mécanisme central : la compétence produit sa propre paralysie

Deux forces opposées, appliquées comme des **facteurs** (jamais des termes) :

```
     LUCIDITÉ ↓                              FOI ↑
  ce que C2 comprend                  la part du vécu
  × ce que C1 a construit             qui a été bonne

  « je VOIS le risque »              « mais ça a marché »
```

Le mécanisme contre-intuitif est le suivant : **un débutant fonce parce qu'il ignore le
danger ; un expert hésite parce qu'il le voit.** Plus l'agent prévoit juste, plus il a de
raisons de ne pas tenter. L'envie de vivre est ce qui l'en empêche.

| Facteur | Formule | Source |
|---|---|---|
| compréhension de C2 | $1/(1+\text{erreur JEPA})$ | modèle du monde |
| expérience de C1 | $\text{amplitude}_{C1} / \text{AMPLITUDE\_C2\_NORMALISEE}$ | vigueur réelle |
| **lucidité** | leur **produit** | — |
| **foi** | $f_{planif}$ (v40) | le vécu |

## Pourquoi multiplicatif, jamais une moyenne

Trois propriétés demandées, qu'une moyenne glissante détruirait **toutes les trois** :

1. **Effet boule de neige** — le positif appelle le positif. Une suite de facteurs > 1
   s'emballe ; une moyenne lisse et ramène au centre.
2. **Inversion possible** — *« certains éléments peuvent littéralement changer le sens »*.
   Un seul facteur bas casse la série ; une moyenne diluerait l'événement.
3. **Les deux coexistent** — *« l'un n'empêche pas l'autre »*. Ce n'est pas un solde net :
   `vecu_okay` et `vecu_danger` vivent en parallèle.

> **La croissance exponentielle ÉMERGE de la composition, elle n'est jamais déclarée.**
> Il n'y a aucun `exp()` dans ce code — seulement des produits successifs.

## ⚠️ Aucun plancher (décision utilisateur explicite)

L'envie peut atteindre **zéro** et l'agent s'y figer définitivement. C'est un **résultat du
modèle, pas un bug**.

> Une variable qui ne peut pas atteindre zéro ne mesure pas la perte de foi.
> **Certains runs mourront** — c'est le jeu de la vie, et c'est observable
> (métrique `Envie_Vivre`).

## Où l'envie agit : sur toutes les décisions

Décision utilisateur : *« Sur toutes les décisions ! »* L'envie traverse les trois leviers
du chemin de décision, tous via `acceptation() = envie × confiance` :

| Levier | Effet | Ce que ça remplace |
|---|---|---|
| **Poids de C2** | `force_planification = acceptation` | la balance v40 seule |
| **Exploration** | `coeff_entropie` suit l'envie | la bascule 0.02 / 0.06 devient un **continuum** |
| **Patience** | `× (0.5 + 0.5 × envie)` | rien — s'ajoute à l'adaptatif existant |

Un agent qui a perdu la foi n'explore plus, n'insiste plus et ne planifie plus : il répète
le connu jusqu'à s'éteindre.

## ⚠️ Deux défauts trouvés en implémentant

### fix1 — zéro était absorbant

En **purement** multiplicatif, un agent tombé à 0,0001 puis redevenu très performant
remontait de 0,0001 à… **0,0001** (+3 % de presque rien reste presque rien).

L'inversion demandée était donc *nominalement vraie et pratiquement impossible* : la mort
était le seul état absorbant.

**Correctif** : un terme **additif** proportionnel à la foi **au carré**. Il ne dépend pas
de l'état courant, donc il fonctionne même depuis zéro. Le carré garantit qu'une foi tiède
ne suffit pas — il faut une vraie série de réussites pour rallumer quelqu'un d'éteint.

> Ceci **ne réintroduit pas de plancher** : envie = 0 reste atteignable et **stable** tant
> que la foi est nulle. On ne garantit pas la survie, seulement qu'une **rédemption** reste
> possible pour qui recommence à réussir.

Mesuré : `0,0038 → 1,0000` en 150 nuits de réussite.

### fix2 — l'agent le plus désespéré était immunisé

L'expérience de C1 était rapportée à `vigueur_min_c1(f)`. Or avec `vecu_okay = 0` on a
$f = 0$, donc cible = 0, donc `experience_c1` forcée à 0, donc **lucidité nulle**.

Mesuré : envie restait à **1,000000** après 1 000 nuits sans la moindre réussite.

**Correctif** : l'échelle est `AMPLITUDE_C2_NORMALISEE`. L'expérience de C1 est une
propriété de C1 — elle ne doit pas dépendre de la confiance accordée à C2.

## La grille de validation (1 000 nuits par scénario)

| Scénario | Envie finale | Lucidité | Foi | Attendu |
|---|---|---|---|---|
| désespéré (aucune réussite) | **0,0000** | 0,990 | 0,000 | ✅ meurt |
| compétent, foi faible | **0,0336** | 0,990 | 0,133 | ✅ s'éteint |
| compétent, qui réussit | **1,0000** | 0,990 | 0,842 | ✅ survit |
| ignorant (JEPA mauvais) | **1,0000** | 0,020 | 0,133 | ✅ n'a pas peur |
| C1 encore neuf | **1,0000** | 0,047 | 0,133 | ✅ n'a pas peur |

Les deux derniers cas sont la signature du mécanisme : **l'ignorance protège**.

---

---

# Partie 3 — fix3/fix4 : la chasse aux branches

> Remarque utilisateur : *« Règle numéro 1 du système : rien en dur et pas de If / Else !
> Ma remarque ne tient que si ce n'est pas lié à la mesure. »*

Audit complet du chemin cognitif de `noyau.py`. **Huit branches** supprimées en deux
passes, chacune avec son équivalence prouvée numériquement.

## Les deux catégories

Toutes les branches supprimées tombaient dans l'une des deux :

**A — la saturation déguisée.** Un `if x >= BORNE: MAX else: rampe` est un `clip` écrit en
deux lignes. Il laisse croire à deux régimes cognitifs là où il n'y a qu'une fonction
bornée.

**B — l'interrupteur cognitif.** Un `if mode_libre:` fait passer une faculté de 0 à 100 %
au franchissement d'un palier. C'est le défaut que le projet documente depuis la v35.1
(*« une falaise, là où il fallait une pente »*).

## Le tableau complet

| # | Site | Avant | Après | Cat. | Équivalence |
|---|---|---|---|---|---|
| 1 | plasticité nocturne | `if teneur >= NEUTRE` | `clip(rampe)` | A | 10 001 pts, **0.0** |
| 2 | tri du signe (vécu) | `if bilan >= 0` | `(\|b\|±b)/2` | A | 200k tirages, **0.0** |
| 3 | garde journée vide | `if not valeurs: return` | `max(len,1)` | A | exact |
| 4 | cliquet réf. choc | `A if monte else B` | `max(Δ,0)/min(Δ,0)` | A | 200k tirages, **0.0** |
| 5 | clip guidage | `if _g < 1.0` | `min(_g, 1.0)` | A | 200k tirages, **0.0** |
| 6 | sevrage (3 marches) | `if/elif/elif/else` | `clip` unique | A | 134k combinaisons, **0.0** |
| 7 | **falaise du guidage** | `if not mode_libre` | continu | **B** | ⚠️ comportement changé |
| 8 | **curiosité JEPA** | `if mode_libre` | × acceptation | **B** | ⚠️ comportement changé |
| 9 | **sursaut de volonté** | `if mode_libre` | ampleur × envie | **B** | ⚠️ comportement changé |

## Les trois interrupteurs cognitifs — ce qui change vraiment

Les six premiers sont des réécritures **à comportement identique**. Les trois derniers
**changent le comportement**, et c'était l'intention :

### 7. La falaise du guidage

`recompense_continue` était coupée d'un coup au palier 5. Elle est désormais multipliée par
`min(facteur_guidage, 1)`, qui tend continûment vers 0 avec la maîtrise **mesurée**.

> Le retrait de l'aide **émerge de la compétence** au lieu d'être décrété par un seuil de
> palier. Un agent au-delà du palier 5 qui ne maîtrise pas **garde son aide** — c'est
> précisément le défaut que le diagnostic v35.1 chiffrait à *0,00 record de proximité par
> jour pendant 2 000 jours*.

### 8. La curiosité JEPA

Passait de 0 à 100 % au palier 5. Désormais toujours évaluée, pondérée par
`acceptation() = envie × confiance`.

Le profil reproduit l'intention d'origine sans le seuil : un débutant ($f \approx 0$) a une
curiosité quasi nulle comme dans l'ancien mode guidé ; un agent mûr la déploie comme dans
l'ancien mode libre. **Et un agent qui a perdu l'envie cesse d'être curieux** — ce que
l'interrupteur était incapable d'exprimer.

### 9. Le sursaut de volonté

Le **déclenchement** reste discret (95 % du budget, une fois par épisode : c'est une
action, pas un régime). Son **ampleur** suit l'envie de vivre.

> *« L'envie de vivre pousse au maximum à essayer quand même »* — le sursaut est
> littéralement cette phrase. Son intensité ne pouvait pas être binaire. À envie nulle, le
> sursaut se déclenche mais ne porte rien : l'agent n'a plus la force de son second souffle.

## Ce qui reste, et pourquoi c'est légitime

Sur les 482 `if` du fichier, ceux qui subsistent dans le chemin cognitif sont de trois
natures — aucune n'est un seuil de décision :

| Nature | Exemple | Pourquoi ça reste |
|---|---|---|
| **Garde technique** | `if taux is None` | distingue « aucune donnée » de « mesuré à zéro » — aucune formule ne peut le faire |
| **Action discrète** | promotion de palier | on promeut ou non ; il n'existe pas de demi-promotion |
| **Sélection de source** | `if doorkey_actif` | choisit **où lire**, pas comment décider |
| **Plancher d'opération** | `if taille_lot < TAILLE_MIN` | rêver 2 souvenirs n'a pas de sens |

> **Un `if` qui choisit une source de donnée n'est pas un seuil de décision.** Ce que la
> règle interdit, c'est qu'une branche décide du *comportement cognitif*.

⚠️ `SEUIL_PALIER_MODE_LIBRE` **existe encore** : `mode_libre` reste calculé et loggé, mais
ne pilote plus aucune faculté cognitive — seulement l'affichage. Le retirer complètement
demanderait de toucher la télémétrie historique ; il est neutralisé, pas supprimé.

---

## Ce qui reste posé (et pourquoi c'est admissible)

| Constante | Rôle | Statut |
|---|---|---|
| `PRUDENCE_NAISSANCE` | a priori de Laplace | rend la fraction définie à t=0 |
| `ENVIE_NAISSANCE` / `ENVIE_PLAFOND` | 1.0 | bornes de l'échelle [0,1] |
| `POIDS_LUCIDITE` / `POIDS_FOI` | 0.02 / 0.03 | **dynamiques** (vitesses), pas seuils |
| `GAIN_C1_MIN` / `MAX` | 0.25 / 4.0 | bornes anti-explosion |
| `OUBLI_OKAY` / `OUBLI_DANGER` | cliquet | dynamiques |

Aucune ne fixe un **rapport de force** ni un **seuil de déclenchement**. Conforme à la
doctrine du projet : *les constantes bornent, les valeurs sont dérivées*.

⚠️ `POIDS_FOI > POIDS_LUCIDITE` est délibéré : un agent qui réussit doit pouvoir remonter
plus vite qu'il ne s'éteint, sinon la mort est le seul état absorbant et la mécanique ne
dit plus rien.

---

## Ce qui reste à mesurer

Le run de 100 jours dit que la mécanique **vit**. Il ne dit pas qu'elle **aide**.

**Le protocole de comparaison en trois temps** (demandé) :

| Condition | Ce qu'on teste |
|---|---|
| **avant v40** | `force_planification` = 0,5 / 0,85 constantes |
| **v40** | balance okay/danger |
| **v40.1** | + envie de vivre sur toutes les décisions |

Mêmes graines, comparés en **taux de victoire par niveau** — jamais en victoires brutes
(piège identifié dans [CAMPAGNE_P17](../recherche/CAMPAGNE_P17_ABLATION_aout_2026.md)).

**Une prédiction testable** : sur `DoorKey-5x5` où couper C2 multiplie le succès par 4,5,
un agent v40 qui échoue devrait voir $f$ baisser **tout seul** et converger vers le
comportement gagnant. Si ça se produit, l'ablation devient une **prédiction du modèle**
plutôt qu'une correction externe.

**Un risque à surveiller** : la boucle qui s'auto-verrouille — envie basse ⇒ moins
d'exploration ⇒ moins de réussites ⇒ envie encore plus basse. Le terme additif (fix1) la
limite, mais seul un run long dira si elle se déclenche en pratique.

---

*Chantier du 14 août 2026. Voir [CHANGELOG](../fonctionnement/CHANGELOG.md) v40.0 / v40.1 et
[explications_readme §7](../fonctionnement/explications_readme.md) pour l'insertion dans
l'architecture.*
