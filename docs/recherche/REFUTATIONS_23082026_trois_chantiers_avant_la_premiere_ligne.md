# Trois chantiers réfutés avant la première ligne de correctif

**23/08/2026** — carnet de recherche, **non normatif**.
Pour l'état courant, voir [`CHANGELOG.md`](../fonctionnement/CHANGELOG.md).
Pour le plan vivant, voir
[`PLAN_v41.32`](../ameliorations/PLAN_v41.32_table_de_mixage_et_neurogenese_dirigee.md).

> **Ce que ce document raconte** : une journée où **trois** propositions successives ont été
> réfutées **avant** d'être codées — la première par une sonde, la deuxième par un témoin
> aléatoire, la troisième par une lecture du code et une mesure de `.brain`.
>
> Ce n'est pas un échec : c'est la règle « mesurer avant de coder » qui rembourse son coût
> trois fois dans la même journée. **Chacune des trois aurait produit un correctif qui ne
> corrige rien**, et deux d'entre elles auraient modifié le monde ou l'architecture.

---

## 0. Le point de départ

Proposition utilisateur en trois volets, tous dogmatiquement séduisants :

1. **Table de mixage** — les 9 termes de récompense sont sommés à poids 1 ; les pondérer par
   un softmax d'urgence (« la faim coupe le son de la curiosité »).
2. **Famine** — dériver la densité de ressources des cases libres réelles.
3. **Neurogenèse dirigée** — répartir `agrandir()` selon le stress par couche.

**Aucune des trois n'a survécu à sa mesure.** Voici les trois enquêtes.

---

## 1. Réfutation n°1 — « le signal vital est écrasé » (par la sonde)

### L'hypothèse

Le soulagement de l'eau (`0,017`) serait noyé sous le bruit de fond du sol nu (`0,125`).
Un softmax redonnerait du volume à la voix vitale.

### L'instrument

Sonde de mixage (`_sonder_mixage` / `_resumer_mixage`), télémétrie **pure** : trois scalaires
par terme (`n`, `Σx`, `Σx²`), moyenne **et** écart-type reconstruits la nuit. Aucune liste
tick par tick — 1500 j × 400 ticks × 12 termes auraient fait 7,2 M de flottants pour un
résultat obtenable en O(1) mémoire.

**Test A/A : δ = 0.** Deux runs bit-identiques sur 40 nuits, même taille de `.brain` à
l'octet. Le banc est déterministe.

### La mesure (g11, 40 jours, cursus complet)

| TERME | MOYENNE | σ | **PART DU SIGNAL** |
|---|---|---|---|
| **Bio** | +0,00346 | **0,04357** | **44,0 %** |
| **Env** | +0,00136 | 0,02163 | 21,8 % |
| Stagnation | −0,01611 | 0,01359 | 13,7 % |
| Curiosite | **+0,02091** | 0,00889 | 9,0 % |
| SousObjectif | +0,00171 | 0,00679 | 6,8 % |
| Progres | +0,00090 | 0,00462 | 4,7 % |
| *5 autres* | 0,00000 | **0,00000** | 0,0 % |

🔴 **`Bio` ne se fait pas écraser : il DOMINE, à 44 % de la dispersion, le double d'`Env`.**

### Ce que la sonde a trouvé à la place

Le vrai défaut est **inversé**. `Curiosite` a la **plus forte moyenne de la table**
(+0,0209, **6× celle de `Bio`**) pour seulement la 4ᵉ dispersion (0,0089). C'est la signature
du **décalage d'origine** : une prime quasi constante versée à chaque tick, qui n'apprend
rien — elle ne distingue aucune action d'une autre — mais gonfle la valeur de tous les
états. `Stagnation` (−0,0161) est sa taxe symétrique.

**Ce ne sont pas neuf voix qui crient : ce sont deux bourdonnements continus.**

### Pourquoi l'écart-type, et pas la moyenne

C'est la leçon transférable. Le gradient n'apprend pas d'une constante : un terme qui vaut
toujours −0,015 est un décalage d'origine, pas un signal. Un terme rare mais massif porte
tout l'apprentissage. **Les deux peuvent avoir la même moyenne.** Rien ne mesurait la
dispersion avant cette sonde.

### ⚠️ Réserve — cinq termes à σ = 0 sont des ablations VIDES

`Jalons`, `Portes`, `Vocal`, `CoutC3`, `Guidage` affichent `σ = 0,00000` exact. Vérification
faite : l'agent est resté au **niveau 1/15** (`Empty-5x5`) — ni porte, ni DoorKey, ni tuteur
vocal, ni plug C3. Ces cinq termes n'ont **aucun support** sur cette carte : ablations
**vides**, pas **négatives**.

**Conséquence** : la table de mixage ne pourra être arbitrée qu'après un run au **niveau 4**.

---

## 2. L'eau innocentée — deuxième réfutation dans la même enquête

### Les chiffres corrigés

⚠️ Le « 0,017 contre 0,125 » qui circulait est faux. Mesuré sur le `.brain` :

| TYPE | VALENCE | VÉCU |
|---|---|---|
| `goal` | **+0,65143** | 36 |
| `FOOD` | **+0,57497** | 67 |
| `sol` | +0,11984 | 884 |
| `WATER` | **+0,11673** | 60 |

L'eau vaut **+0,117**, le sol nu **+0,120**. L'eau n'est pas « sept fois sous le sol nu » :
elle est **à son niveau exact**. Le point de comparaison qui compte est `FOOD` (**+0,575**),
à vécu quasi identique (67 contre 60).

### La question retournée

Non pas « pourquoi l'eau est-elle basse », mais **« pourquoi manger soulage et boire non »**.

**Ni la formule ni le profil ne sont asymétriques :**

| | Satiété | Hydratation |
|---|---|---|
| Terme du déficit | `(1 − satiete)²` | `(1 − hydratation)²` |
| Profil | `FOOD.satiete = 1.0` | `WATER.hydrique = 1.0` |

L'asymétrie est dans **l'état des jauges**, mesuré sur 40 nuits :

| Jauge | Min moyen | Nuits au plancher |
|---|---|---|
| **Satiété** | **0,0000** | **40/40 (100 %)** |
| Hydratation | 0,5333 | 3/40 (8 %) |

**L'agent n'a jamais soif.**

### Le test quantitatif — l'écart est expliqué à 4,4 % près

`r_bio` est la **dérivée** du déficit : une jauge pleine ne peut rien soulager.

| | Soulagement possible par prise |
|---|---|
| `FOOD` sur une satiété à 0,106 | **0,3842** |
| `WATER` sur une hydratation à 0,726 | **0,0747** |

| Ratio | Valeur |
|---|---|
| Prédit par l'état des jauges | **5,14×** |
| Réellement appris (valences) | **4,93×** |
| **Écart** | **4,4 %** |

🟢 **Les valences mesurent EXACTEMENT le soulagement réel.** Le canal `WATER` fonctionne, la
loi des rendements décroissants fonctionne, et elle est **physiologiquement juste** — boire
sans soif ne fait aucun bien.

Le correctif v41.7 est par ailleurs confirmé : `FOOD` est passé de `+0.000 (×4004)` à
**+0,575**, du même ordre que `goal`.

### ⚠️ Le piège évité

« Réparer » l'eau — augmenter sa portion ou son rendement — aurait créé une valence
**artificielle** sur une jauge déjà pleine. Un chiffre posé pour corriger un symptôme
**correct**. C'est exactement le geste que le dogme interdit, et la proposition initiale y
menait directement.

### Pourquoi l'eau est abondante et la nourriture rare

`RATIO_SOIF_SUR_FAIM = 10/30` : le besoin en eau est **trois fois plus faible**, pour une
récolte quasi identique (1,50 contre 1,68). L'agent boit **1,2× ses besoins** et mange
**60 % des siens**. L'asymétrie est la **conséquence arithmétique** d'un biotope à parts
égales sur deux axes aux besoins inégaux.

---

## 3. Réfutation n°2 — « la densité est le goulot » (par témoin aléatoire)

### L'hypothèse

Le biotope demanderait 14 sources sur une carte qui en tient 8 : l'agent serait « emmuré
avec un buffet qui ne peut pas spawner ». Correctif proposé : dériver la densité des cases
libres **réelles** de la carte courante (option **a**).

### ⚠️ D'abord, une erreur de diagnostic corrigée

J'avais moi-même avancé le « 14 sources sur 8 cases ». **C'est faux.** Mesuré en
instanciant les environnements réels :

| Carte | Cases libres | FOOD placées | WATER placées |
|---|---|---|---|
| `Empty-5x5` | 6 | **1** | 1 |
| `Empty-6x6` | 11 | 2 | 2 |
| `Empty-8x8` | 24 | 6 | 5 |

Le plafond `v41.2-fix3` (`budget = max(2, int(cases_libres × 0,35))`) **fonctionne
parfaitement**. Le « 7+7 » lu dans les logs est le **souhait**, jamais le **placé**.

### Le témoin qui tranche

Marcheur **aléatoire** sur la carte réelle, 3 graines × 400 ticks, avec la **même
distribution d'actions** que l'agent (uniforme sur les 7 actions réelles) :

| | FOOD/jour | WATER/jour |
|---|---|---|
| **Marcheur aléatoire** | **3,33** | 4,00 |
| **Agent entraîné** (40 nuits) | **1,68** | 1,50 |
| *Seuil de viabilité énergétique* | *2,78* | *—* |

🔴 **Le hasard pur franchit le seuil de viabilité (3,33 > 2,78). L'agent entraîné non.**

### Les trois conséquences

1. **Le monde PEUT nourrir l'agent** à densité inchangée. Le biotope n'est pas sous-doté.
2. **L'agent récolte 50 % de ce qu'aucune politique n'obtiendrait.** Son apprentissage le
   rend *activement moins bon* à se nourrir que le hasard. C'est le fait à expliquer, et
   aucune modification du monde ne le touche.
3. **L'option (a) aurait été le QUATRIÈME calibrage inopérant.** Le code annonce déjà les
   trois premiers (v41.2-fix3 : *« trois calibrages successifs restés sans le moindre
   effet »*) — ils réglaient un paramètre qui n'était pas le facteur limitant.

### Le bilan énergétique (pour mémoire)

⚠️ Correction d'un calcul intermédiaire : `conversion = min(debit_digestif,
reserve_mobilisable)` — la digestion est un **PLAFOND**, pas un prélèvement fixe. Le bilan
se fait en **énergie**, pas en estomac.

| Régime | Énergie fabriquée | Dépense | Solde |
|---|---|---|---|
| **3,00 repas/j** *(la calibration d'origine)* | 2,160 | 2,000 | **+0,160 → viable** |
| **1,68 repas/j** *(mesuré)* | 1,210 | 2,000 | **−0,790 → déficit permanent** |

Le commentaire de `DEPENSE_ENERGIE_JOUR = 2.0` le dit lui-même : *« balayage 1.0→3.0 **à 3
repas/jour** »*. C'est une **quatrième constante fossile**, de la même famille que les trois
supprimées en v41.30 — mais **la corriger ne servirait à rien** tant que le goulot est
comportemental.

### Où va le chantier famine

La cause est **dans la politique**, pas dans le monde. Trois pistes, toutes mesurables
**sans modifier une ligne du monde** :

| Piste | À mesurer |
|---|---|
| L'agent ne cherche pas la nourriture | distribution d'actions agent vs. aléatoire |
| **`pickup` n'est pas appris** | v41.2-fix5 a rendu manger un **acte volontaire** — quelle fraction des passages sur une source déclenche un `pickup` ? |
| Le gradient ne paie pas le fourrage | `Bio` porte 44 % de la dispersion — concentrée sur les 1,68 prises, ou diluée sur 400 ticks ? |

**Recommandation** : la deuxième. La plus mécanique, la plus rapide, et `v41.2-fix5` est un
suspect naturel — un acte à 1 chance sur 7 d'être tiré peut ne jamais s'apprendre si sa
récompense est noyée.

---

## 4. Réfutation n°3 — « répartir la neurogenèse selon le stress »

### L'hypothèse

`agrandir()` ajoute `+16` dimensions uniformément. Répartir ce budget proportionnellement au
stress de chaque couche (`budget × stress_i / Σ stress`) rendrait sa masse à C2 et corrigerait
sa dilution. Dogmatiquement irréprochable : aucun coefficient, tout sort du gradient reçu.

### (1) Impossible sous cette forme — le bus est partagé

Dans `declencher_neurogenese`, `a` apparaît **deux fois** par couche du tronc :

```python
self.analyseur.agrandir([(d, a)], a)
#                        ^^^^^^   ^
#                        entrée   SORTIE
```

La **sortie** d'`analyseur` **est** l'entrée d'`integrateur_bio`, qui alimente
`tete_motrice`, etc.

| Couche | Sortie |
|---|---|
| `porte_visuelle`, `hippocampe`, `fusion_memoire`, `analyseur`, `integrateur_bio`, `generateur_attente`, `porte_auditive`, `generateur_attente_audio` | **`+a` — contrainte** |
| `tete_motrice`, `cortex_prefrontal`, `tete_vocale`, `tete_requete` | fixe (8, **1**, 8, `DIM_ROUTAGE_C3`) |

**Huit couches sont chaînées sur la même largeur.** Donner 8 dims à l'une et 24 à l'autre
produit un `RuntimeError` au premier `forward`. **`dim_bus` n'est pas un budget
répartissable : c'est une largeur commune.**

### (2) Et son objectif est hors de portée — mesuré

Répartition réelle d'un `.brain` à `dim_bus = 70` (384 808 paramètres) :

| COUCHE | PARAMS | PART |
|---|---|---|
| `porte_visuelle` | 61 742 | 16,05 % |
| `hippocampe` | 58 802 | 15,28 % |
| `fusion_memoire` | 58 802 | 15,28 % |
| `porte_auditive` | 54 602 | 14,19 % |
| `integrateur_bio` | 46 622 | 12,12 % |
| `generateur_attente` | 32 762 | 8,51 % |
| `generateur_attente_audio` | 32 762 | 8,51 % |
| `analyseur` | 29 402 | 7,64 % |
| `tete_motrice` | 3 362 | 0,87 % |
| `tete_vocale` | 3 362 | 0,87 % |
| `tete_requete` | 2 102 | 0,55 % |
| **`cortex_prefrontal` (C2)** | **422** | **0,110 %** |

🔴 **La cause n'est pas dans `agrandir()`** : `cortex_prefrontal` a **une seule sortie** —
une valeur scalaire. Il croît en **N**, quoi qu'on lui donne, pendant que toute matrice
carrée croît en **N²** :

| Ajout | C2 gagne | `hippocampe` gagne | Rapport |
|---|---|---|---|
| 8 dims | 48 | 14 208 | **×296** |
| 16 dims | **96** | **29 952** | **×312** |
| 32 dims | 192 | 66 048 | **×344** |

**Même à 100 % du budget**, C2 gagnerait 96 paramètres quand le tronc en gagne 29 952. Une
répartition proportionnelle au stress aurait déplacé des **miettes** — et donné l'illusion
d'avoir traité la dilution.

**Le problème n'est pas combien de dimensions C2 reçoit en ENTRÉE. C'est qu'il n'a qu'une
SORTIE.**

### Ce qui resterait possible — non tranché, à ne pas coder sans décision

| Piste | Nature | Réserve |
|---|---|---|
| Élargir la **sortie** de C2 (tête de valeur multi-dim, agrégée ensuite) | change l'architecture | modifie la sémantique de la valeur ; greffe `persistance` obligatoire |
| Donner à C2 une **couche cachée** (`bus → h → 1`) | croissance en N·h | nouvelle couche ⇒ à déclarer dans `__init__`, `cycle_sommeil_global()` **et** `declencher_neurogenese()` |
| **Ne rien faire** | — | corrélation taille~niveau **négative** (r = −0,172) ; rien ne dit qu'un C2 plus gros aiderait |

⚠️ La neurogenèse est par ailleurs **éteinte depuis 882 jours** en moyenne : toute
correction de la croissance ne s'appliquerait qu'aux premières centaines de jours.

---

## 4bis. Réfutation n°4 — « le gradient a appris à ne plus manger »

### L'hypothèse

Le fil laissé ouvert : **l'agent entraîné récolte 1,68 FOOD/jour, le hasard 3,33.**
Hypothèse retenue pour la nuit : `ACTION_CONSOMMER` étant coûteux et sa récompense mal
attribuée, le gradient aurait appris à **ne plus tenter** — l'agent choisirait l'agonie
lente plutôt que l'effort.

### L'instrument

`_sonder_fourrage`, télémétrie **pure** (vérifiée statiquement : n'écrit que dans
`fourrage_*`). Manger exige une **conjonction** depuis la v41.2-fix5/fix6 :

1. faire **face** à la ressource (case frontale `agent_pos + dir_vec`),
2. **et** jouer `ACTION_CONSOMMER`.

Une conjonction se casse de deux façons, et il fallait savoir laquelle : défaut de
**navigation** (jamais en position) ou défaut de **décision** (en position, pas de geste).

**Test A/A : δ = 0**, 60 nuits bit-identiques, graine 11.

### La mesure

| Grandeur | Valeur |
|---|---|
| Occasions (face à une ressource) | **52,2/jour** |
| Gestes `consommer` joués | **52,5/jour** |
| **Saisies (conjonction réussie)** | **4,2/jour** |
| **Taux de saisie** | **8,1 %** |
| Gestes dans le vide | **92,0 %** |
| Faim moyenne aux occasions | **0,961** |

### 🔴 L'hypothèse est réfutée — les tentatives TRIPLENT

| | 1er tiers | 2ᵉ tiers | 3ᵉ tiers |
|---|---|---|---|
| Gestes `consommer`/jour | 27,2 | 56,0 | **74,2** |
| Taux de saisie | 4,2 % | 8,1 % | **13,0 %** |

Le geste n'est **pas réprimé, il est renforcé** — et le taux de saisie monte aussi. **L'agent
n'est pas anorexique** : il essaie de manger 52 fois par jour, de plus en plus souvent, en
famine quasi totale (0,961).

### Ce que la sonde trouve à la place — l'anti-corrélation

Les deux termes de la conjonction marchent **séparément** : 52,2 occasions et 52,5 gestes
par jour sur 400 ticks. **C'est leur intersection qui échoue.**

| | |
|---|---|
| Saisies attendues si les deux étaient **indépendants** | **378,9** |
| Saisies **observées** | **253** |
| **Ratio observé/attendu** | **0,67** |
| Nuits sous le hasard | **49/60 (82 %)** |

🔴 **L'agent fait moins bien que le hasard sur la conjonction.** Ses deux comportements ne
sont pas décorrélés : ils sont **anti-corrélés**. Il joue le geste quand il n'est pas en
face, et se trouve en face quand il ne joue pas le geste.

C'est cohérent avec le fait initial (1,68 contre 3,33 pour le hasard) : le marcheur aléatoire
n'a **aucune** anti-corrélation à surmonter, donc il ferme la conjonction au taux nominal.

### Pistes ouvertes (non tranchées, aucune mesure)

| Piste | Question |
|---|---|
| **Perception frontale** | la ressource est-elle perceptible dans la case frontale au moment de décider ? La vue est un cône, l'odorat topologique — le contact frontal a-t-il un canal dédié ? |
| **Crédit temporel** | le soulagement (v41.2-fix7) atteint-il le tick du geste, ou le suivant ? |
| **Geste piloté par l'état interne** | `ACTION_CONSOMMER` répond-il à la **faim** plutôt qu'à la **présence** ? Un geste piloté par la faim seule serait *exactement* anti-corrélé à l'occasion — c'est l'hypothèse la plus économique |

⚠️ **Une seule graine.** Le fait qualitatif (ratio < 1, tentatives croissantes) est net, mais
le chiffre exact lui est propre.

---

## 4ter. Réfutations n°5 et n°6 — les deux explications de l'anti-corrélation

Deux hypothèses proposées pour expliquer l'anti-corrélation du §4bis. **Les deux sont
réfutées** — la première par lecture du code, la seconde par l'API MiniGrid. Mais la
seconde laisse un fait mesuré qui, lui, tient.

### Réfutation n°5 — « le soulagement n'atteint pas le gradient »

**L'hypothèse** : `consommer_ressource()` remplirait la satiété **avant** que
`step_metabolisme()` ne calcule `deficit_avant`, donc `r_bio` serait quasi nul. Le réseau
moteur ne serait jamais récompensé pour avoir mangé — même défaut temporel que la chaleur
en v41.25-fix1.

🔴 **Réfutée : l'ordre est l'inverse, et le correctif existe déjà (v41.2-fix7).**

| Ligne | Ce qui s'exécute |
|---|---|
| 8993 | `step_metabolisme()` → `r_bio` ordinaire |
| 9049 | `evaluer_tick()` → la consommation a lieu |
| 9064 | `deficit_avant_repas = calculer_deficit()` |
| 9090 | `soulagement = deficit_avant_repas − calculer_deficit()` |
| **9092** | **`r_bio += soulagement`** ← le rattrapage |
| 9207 | `recompense_interne = … + r_bio + …` |

Le soulagement est mesuré **autour** de l'ingestion, puis **ajouté au `r_bio` du même
tick**. C'est exactement le correctif proposé — il a été livré en v41.2-fix7.

**Et il est énorme, mesuré sur 60 nuits :**

| | |
|---|---|
| Soulagement cumulé | **+1,263/jour** |
| Saisies | 4,22/jour |
| **Soulagement par repas** | **+0,300** |
| σ du canal `Bio` (étape 1) | 0,0436 |
| **Un repas vaut** | **≈ 7 écarts-types de `Bio`** |

Le signal n'est pas écrasé : c'est **le plus gros événement de récompense de la vie de
l'agent**. L'hypothèse « il n'est jamais récompensé pour avoir mangé » est fausse.

### Réfutation n°6 — « le toucher fantôme »

**L'hypothèse** : une ressource étant ramassable, elle serait traversable
(`can_overlap() == True`), donc `contact_frontal` resterait à 0 — aucun signal tactile ne
justifierait de s'arrêter.

🔴 **Réfutée par l'API MiniGrid :**

| Objet | `can_overlap()` |
|---|---|
| `Ball` (= FOOD/WATER) | **False** |
| `Wall` | False |
| `Goal` | True |

`Ball.can_overlap() == False` : la ressource **est** bloquante, donc `contact_frontal = 1.0`
quand elle est devant. Le canal existe et il s'active.

### 🟡 Mais la mesure laisse un fait — le bit de contact est AMBIGU

`contact_frontal` est **un seul bit**, et il ne distingue pas ce qui bloque. Mesuré sur
3000 ticks (`Empty-5x5`, marcheur uniforme sur 7 actions) :

| Quand `contact_frontal = 1.0` | Occurrences | Part |
|---|---|---|
| c'est un **MUR** | 1 498 | **81,5 %** |
| c'est une **RESSOURCE** | 339 | 18,5 % |

**Le même signal dit « obstacle à contourner » (82 %) et « nourriture à saisir » (18 %).**
Un réflexe tactile appris sur ce bit apprendrait donc majoritairement à **se détourner** —
et se détourner devant une ressource est *exactement* l'anti-corrélation mesurée au §4bis.

⚠️ **Ce n'est PAS une conclusion.** La vue voit la ressource (couleur, type), l'odorat
donne un gradient topologique : l'information de discrimination **existe ailleurs**. Le bit
ambigu est une hypothèse plausible, pas une cause démontrée. Ce qui est établi :

| Établi | Non établi |
|---|---|
| `contact_frontal` est à 1 pour un mur **et** pour une ressource | que l'agent s'en serve plutôt que de la vue |
| Le ratio est de **82 % / 18 %** en faveur du mur | que ce soit la cause de l'anti-corrélation |

**Ce qu'il faudrait mesurer pour trancher** : l'action jouée quand `contact_frontal = 1`,
séparément selon que la case frontale porte un mur ou une ressource. Si la distribution est
**identique** dans les deux cas, l'agent ne discrimine pas — et le bit ambigu est confirmé
comme cause. Si elle diffère, il discrimine par un autre canal et l'hypothèse tombe.

---

## 4quater. Réfutation n°7 — « les cartes du Doctorat sont stériles »

### L'hypothèse

Les cartes `MultiRoom` (niveaux 14-15) n'auraient **ni nourriture ni eau**. Trois sens
réduits au silence, homéostasie tournant à vide, neurogenèse anesthésiée. Correctif
proposé : injecter `DetecteurRessourcesBiologiques` dans `MultiRoom`.

### 🔴 Réfutée — le détecteur est générique et peuple TOUTE carte

Test direct, instanciation des environnements réels :

| CARTE | LIBRES | FOOD | WATER |
|---|---|---|---|
| `Empty-5x5` | 6 | 1 | 1 |
| `SimpleCrossingS9N1` | 28 | 7 | 7 |
| `DoorKey-8x8` | 19 | 4 | 5 |
| `MemoryS7` | 9 | 2 | 1 |
| **`MultiRoom-N2-S4`** | **494** | **7** | **7** |
| **`MultiRoom-N4-S5`** | **450** | **7** | **7** |

`MultiRoom` reçoit **7 FOOD + 7 WATER**, comme les autres. Le détecteur ne connaît aucun nom
de carte : il lit les cases vides et place. Il n'y a rien à « injecter ».

### 🟡 Mais le test révèle un vrai défaut — la densité s'effondre

| CARTE | LIBRES | SOURCES | **DENSITÉ** |
|---|---|---|---|
| `Empty-5x5` | 6 | 2 | **0,333** |
| `SimpleCrossingS9N1` | 28 | 14 | 0,500 |
| `DoorKey-8x8` | 19 | 9 | 0,474 |
| **`MultiRoom-N2-S4`** | **494** | **14** | **0,028** |
| **`MultiRoom-N4-S5`** | **450** | **14** | **0,031** |

**1 source toutes les 3 cases sur `Empty-5x5`, 1 toutes les 35 sur `MultiRoom` — la densité
chute d'un facteur 11,8.**

### La cause : une CINQUIÈME constante fossile

Sur `MultiRoom`, le plafond `budget = max(2, int(libres × 0,35))` **ne mord pas**
(0,35 × 494 = 172 ≫ 14). C'est le **souhait** qui borne — et il est dérivé de :

```python
_CASES_LIBRES_CARTE_MAXIMALE = 41.0   # « SimpleCrossingS9N1, la plus vaste
                                      #   du cursus ATTEINT À CE JOUR »
```

Le commentaire l'admet lui-même. La constante décrit le cursus **tel qu'il était quand elle
a été écrite** — `MultiRoom` a **494** cases libres, soit **12×** ce chiffre.

| Constante fossile | Écart mesuré |
|---|---|
| `EPISODES_PAR_JOURNEE_REFERENCE = 4.0` | ×2,58 |
| `DEPENSE_ENERGIE_JOUR` (calibré à 3 repas/j) | ×1,79 |
| **`_CASES_LIBRES_CARTE_MAXIMALE = 41`** | **×12,0** |

### ⚠️ Ce n'est PAS l'option (a) réfutée au §3 — et ce n'est pas actionnable

**Sur `Empty-5x5`** : le plafond mord déjà (0,35 × 6 = 2) et le témoin aléatoire y récolte
3,33 FOOD/jour, au-dessus du seuil de viabilité. Ajouter des sources n'y changerait rien —
la réfutation du §3 **tient**.

**Sur `MultiRoom`** : la situation est inversée, c'est le souhait fossile qui borne, et la
même correction y aurait un effet **réel**.

🔴 **Mais l'agent n'atteint jamais le niveau 14.** Maximum mesuré : **5/15**, et **0 sur 40**
brains au-delà du niveau 5 (campagne n=20 du 22/08). Corriger la densité de `MultiRoom`
aujourd'hui serait **optimiser une carte que l'agent ne verra jamais** — une ablation
**vide** au sens de la règle de mesure, exactement comme la nociception mesurée sur un
cursus où la lave n'apparaît pas.

**À corriger le jour où l'agent franchit le niveau 13.** Consigné ici pour que la cause soit
connue à ce moment-là, plutôt que rediagnostiquée.

---

## 4quinquies. La table de mixage aux niveaux supérieurs — `Env` s'effondre ×240

### Le piège évité avant de lancer

L'étape 1 laissait 5 termes en ablation **vide** au niveau 1. L'arbitrage proposé était « un
run au niveau 4 ». **Vérification en code avant lancement** : le niveau 4 est
`SimpleCrossingS9N1`, où `est_doorkey() = False`, il n'y a **pas de porte**, pas de tuteur —
**aucun des 5 termes ne s'y réveille**. Le run aurait reproduit l'ablation vide à l'identique.

Seul **`DoorKey-5x5`** porte `Jalons` + `Guidage` + `Portes` simultanément. **Deux runs ont
donc été lancés**, pour deux questions distinctes.

### Résultat 1 — Niveau 4 (`SimpleCrossingS9N1`), 80 nuits

| TERME | MOYENNE | σ | PART SIGNAL |
|---|---|---|---|
| **Bio** | +0,00362 | **0,04141** | **52,1 %** |
| Stagnation | −0,01383 | 0,01388 | 17,5 % |
| SousObjectif | +0,00437 | 0,01125 | 14,2 % |
| Curiosite | +0,01255 | 0,00856 | 10,8 % |
| Progres | +0,00065 | 0,00422 | 5,3 % |
| **Env** | **+0,00001** | **0,00009** | **0,1 %** |

### Résultat 2 — `DoorKey-5x5`, 80 nuits

| TERME | MOYENNE | σ | PART SIGNAL |
|---|---|---|---|
| **Bio** | +0,00248 | **0,03141** | **36,4 %** |
| **Jalons** | +0,00255 | **0,02926** | **33,9 %** |
| Stagnation | −0,01109 | 0,01221 | 14,1 % |
| SousObjectif | +0,00169 | 0,00556 | 6,4 % |
| Curiosite | +0,00727 | 0,00386 | 4,5 % |
| Guidage | +0,00017 | 0,00203 | 2,4 % |
| Portes | +0,00005 | 0,00113 | 1,3 % |
| Env | +0,00004 | 0,00084 | 1,0 % |

### 🔴 Le fait principal — la récompense de la TÂCHE s'effondre

| Carte | σ de `Env` | Part |
|---|---|---|
| `Empty-5x5` (niveau 1) | 0,02163 | **21,8 %** |
| **`SimpleCrossingS9N1` (niveau 4)** | **0,00009** | **0,1 %** |
| `DoorKey-5x5` | 0,00084 | 1,0 % |

**Sur la carte où l'agent est réellement bloqué, le but porte 0,1 % de la dispersion —
facteur 240 par rapport au niveau 1.**

Ce n'est **pas** une ablation vide : σ n'est pas nul, il est **écrasé**. L'agent atteint le
but, mais si rarement que le signal devient négligeable. Recoupé par la maîtrise finale :
**15 % au niveau 1, 5 % au niveau 4**.

C'est un **cercle**, pas un bug : peu de victoires ⇒ signal faible ⇒ peu d'apprentissage de
la tâche ⇒ peu de victoires. Et `Bio` monte de 44 % à **52,1 %** — le corps occupe la place
que le but laisse vide. **Ce n'est pas que la biologie crie trop fort : c'est que la tâche
s'est tue.**

### Ce que ces tables établissent

1. **`Bio` domine partout** (52,1 % · 36,4 %) — la prémisse « le vital est écrasé » reste
   réfutée sur les trois cartes.
2. **`Curiosite` et `Stagnation` sont des décalages d'origine partout** : forte moyenne,
   faible dispersion. C'est le vrai objet du chantier « table de mixage ».
3. **`Jalons` est un vrai signal** quand il existe (33,9 %, second de la table). Il n'était
   pas mort, il était **absent**.
4. **`Vocal` et `CoutC3` sont muets partout** : ablations vides **par configuration**, jamais
   par carte.

⚠️ **Bancs forcés** (niveau bloqué à 1/15 par construction) et **une seule graine** : ces
runs mesurent des **dispersions**, jamais des performances.

---

## 4sexies. La sonde de discrimination — hypothèse confirmée, mécanisme réfuté

### 🔴 D'abord : un artefact de MA sonde, attrapé par la règle du « résultat trop propre »

Le premier run donnait `consommer sur ressource = 0,0 %` sur **60/60 nuits**. Le même run
enregistrait **295 saisies réelles** — incompatible.

**Cause** : `env.step` s'exécute ~370 lignes **avant** la sonde. MiniGrid a déjà exécuté
`pickup`, la Ball est dans `carrying`, la case est vide — `can_overlap()` ne voyait plus
rien. Même défaut temporel qu'en v41.25-fix1 (chaleur) et v41.5 (maturité) : *une grandeur
lue après un `env.step` qui l'a périmée*.

**Correctif** : tester `positions_food`/`positions_water`, les ensembles du détecteur, vidés
seulement à `evaluer_tick` — donc **après** la sonde. C'est exactement pourquoi la sonde de
fourrage, qui les utilisait déjà, n'avait pas ce biais.

⚠️ Sans le recoupement « 295 saisies contre 0 compté », ce zéro aurait été publié comme une
découverte. C'est le troisième artefact du projet attrapé par cette règle (après v41.4 et
v41.7).

### Les résultats corrigés (graine 11, 60 jours, 2 cartes)

| ACTION | `Empty-5x5` mur/ressource | Niveau 4 mur/ressource |
|---|---|---|
| gauche | 7,9 / 9,6 | 8,4 / 11,3 |
| droite | 6,4 / 9,3 | 4,9 / 10,3 |
| avancer | 23,3 / 24,7 | 21,1 / 21,9 |
| **consommer** | **12,1 / 9,8** | **16,0 / 16,0** |
| poser | 16,6 / 14,9 | 7,2 / 6,5 |
| activer | 16,0 / 12,3 | 35,5 / 25,3 |
| parler | 17,7 / 19,5 | 6,7 / 8,8 |
| **DISTANCE** | **0,1943** | **0,2640** |

### Le témoin de bruit — sans lui ces chiffres sont illisibles

Deux échantillons tirés de la **même** distribution, aux mêmes tailles, 4000 tirages :

| Carte | Mesure | Bruit p50 | Bruit p95 | Verdict |
|---|---|---|---|---|
| `Empty-5x5` | **0,194** | 0,127 | **0,213** | **sous le p95 — indistinguable du bruit** |
| Niveau 4 | **0,264** | 0,150 | **0,249** | à peine au-dessus |

### Verdict

🟢 **L'hypothèse « les distributions sont identiques » est CONFIRMÉE.** La distance mesurée
est au niveau du bruit d'échantillonnage : **l'agent ne discrimine pas** une ressource d'un
mur.

🔴 **Mais le mécanisme proposé est réfuté.** L'hypothèse prédisait que l'agent **se détourne**
devant une ressource (plus de rotations, moins de `consommer`). Les écarts vont dans ce sens
mais **restent dans le bruit**, et au niveau 4 `consommer` est **rigoureusement identique**
(16,0 / 16,0).

Ce n'est pas que l'agent **fuit** la ressource. C'est qu'il fait **exactement la même chose**
dans les deux cas : il ne voit pas la différence, et ne l'exploite pas.

### Le fait le plus net — la distance DÉCROÎT

| Carte | 1er tiers | 2ᵉ tiers | 3ᵉ tiers |
|---|---|---|---|
| `Empty-5x5` | 0,253 | 0,186 | **0,144** |
| Niveau 4 | 0,255 | 0,263 | 0,274 |

Sur `Empty-5x5`, l'agent devient **avec le temps moins discriminant**. Il n'apprend pas à
distinguer : il apprend à **uniformiser** sa réponse.

### ⚠️ Sur le correctif envisagé — attention au dogme

Scinder `contact_frontal` en `contact_obstacle` / `contact_interactif` **nommerait une
catégorie** — déclarer au cerveau ce qu'est une ressource, ce que l'invariant v36.0 interdit
(*« il ne doit exister nulle part de table du type lave = danger »*).

La forme propre existe : `can_overlap()` est déjà une propriété **lue de l'API**, jamais
déclarée. On peut exposer une seconde propriété lue — `can_pickup()` — sans nommer ce qu'elle
désigne. Le cerveau recevrait **deux bits mesurés** au lieu d'un et apprendrait seul ce qu'ils
valent. Même discipline que `lava` en v41.11 : le nom vit dans `bus_sensoriel.py`, jamais
dans `noyau.py`.

⚠️ **Et ce n'est pas encore justifié** : rien ne prouve que la non-discrimination vienne du
bit plutôt que de la politique elle-même. La vue et l'odorat portent déjà l'information. Un
second bit qui ne serait pas plus exploité que le premier ne changerait rien.

⚠️ **Bancs forcés, une seule graine.** Le témoin de bruit rend la lecture honnête, il ne
remplace pas n ≥ 20.

---

## 4septies. Réfutation n°9 — « la politique s'aplatit vers l'uniforme »

### L'hypothèse

L'extinction de `Env` priverait le gradient de signal ; les 7 logits se rapprocheraient ;
l'entropie monterait vers son maximum **ln(7) = 1,94591**, et l'agent deviendrait un marcheur
aléatoire. C'était la synthèse unifiant les trois symptômes (indifférence tactile,
anti-corrélation du fourrage, `Env` éteint).

### Aucun run nécessaire — la mesure était déjà dans les données

La sonde de discrimination enregistre la **distribution des 7 actions**. L'entropie de la
politique réellement jouée s'en reconstruit directement.

| Carte | H début | H fin | % du max | Tendance |
|---|---|---|---|---|
| `Empty-5x5` | 1,7695 | **1,7034** | 88,1 % | **baisse** |
| Niveau 4 | 1,7130 | **1,6565** | 82,0 % | **baisse** |

🔴 **L'entropie NE MONTE PAS — elle BAISSE sur les deux cartes.** L'écart au maximum se
**creuse** : 0,176 → 0,243 et 0,233 → 0,289.

### Comparaison au bug historique — l'échelle du contraste

La v34.0-fix1 documente le cas réel d'un cerveau **éteint** (8 couches sur 11 à zéro après
1500 nuits) : entropie **1,94587** pour un max de 1,94591, soit un écart de **0,00004**.

| | Écart au maximum |
|---|---|
| Cerveau éteint (v34.0, août) | **0,00004** |
| Agent mesuré ce jour | **0,34961** |

L'agent d'aujourd'hui est **~8700× plus décidé** qu'un cerveau réellement aplati. Il n'est pas
près de l'uniforme, il s'en éloigne.

### Ce que cela change au diagnostic

**« Il n'a plus d'opinion » est faux. Il en a une — elle est simplement LA MÊME quel que soit
le contexte.**

La distinction n'est pas cosmétique :

| | Aplatissement stochastique | Politique non conditionnelle |
|---|---|---|
| Signature | entropie → ln(7) | entropie basse, **distance mur/ressource ≈ bruit** |
| Mesuré | ❌ réfuté | ✅ **c'est ce qu'on observe** |
| Cause | manque de signal | défaut de **représentation** — l'état n'entre pas dans la décision |
| Correctif | rendre du signal | faire entrer le contexte dans la politique |

Un aplatissement se corrige en rendant du signal. Une politique **concentrée mais non
conditionnelle** est un défaut plus profond : l'agent a des préférences stables qu'il applique
partout **sans lire l'état**. Ajouter du signal de récompense ne l'aiderait pas — il ne
conditionne déjà pas sur ce qu'il perçoit.

⚠️ **Une seule graine, bancs forcés, entropie reconstruite depuis des pourcentages arrondis à
l'entier** (donc précise à ~±0,01). Le fait qualitatif — la tendance baisse, l'écart au max
est de 4 ordres de grandeur au-dessus du cas éteint — ne dépend pas de cette précision.

---

## 4octies. CHANTIER 0 — la perméabilité : le goulot n'est pas où on le cherchait

### L'hypothèse

*Representation collapse* : pendant des centaines de nuits sans `Env`, ignorer le monde
serait devenu la stratégie la plus économe ; l'information se perdrait dans les couches
profondes. **Signature attendue** : `bus_latent` distinct, **logits identiques**.

### L'instrument

`src/naulthene/instruments/sonde_permeabilite.py` — instrument **en lecture seule**, même
discipline qu'`irm_cerveau.py`. Deux protocoles, délibérément :

- **(A) états FORGÉS** (jauges aux extrêmes) — contraste maximal, donc **borne supérieure**
  de sensibilité. Mais **hors distribution** : une réponse plate y prouverait beaucoup, une
  réponse vive n'y prouve rien du comportement réel.
- **(B) états RÉELS capturés en jeu** — ce qui compte, contraste plus faible.

### 🔴 La signature mesurée est L'INVERSE EXACT de l'hypothèse

| ÉTAGE | (A) forgé | (B) réel | Lecture |
|---|---|---|---|
| `bus_latent` | 0,000000 | **0,0721** | quasi identique |
| `pensee_bio` | 0,0911 | 0,0936 | léger écart |
| **`logits_C1`** | **0,6667** | **0,8607** | **très différent** |

**L'information n'est pas perdue : elle est AMPLIFIÉE.** 0,07 au bus → 0,09 après fusion →
**0,86** aux logits, un facteur **×12**. Les couches profondes font exactement leur travail.

⚠️ Le `0,000000` en (A) est un **test de sanité réussi**, pas un défaut : les jauges
n'entrent pas dans `bus_latent` (invariant v29.0 — les sens faibles passent par
`integrateur_bio`, hors cible JEPA). Même image ⇒ même bus.

⚠️ **Correction d'une métrique de ma sonde** : `valeur_C2` est un **scalaire**
(`cortex_prefrontal.out_features == 1`), donc une distance cosinus n'y vaut que 0 ou 2 — elle
ne mesure que le **signe**. Le « 2,000000 » du premier tirage était un artefact de métrique,
pas une découverte. La sonde publie désormais les deux valeurs brutes : **+0,176 face à une
ressource, −0,082 face à un mur**. C2 *distingue*, et dans le bon sens.

### Ce que cela déplace — le goulot est l'AMPLITUDE, pas la représentation

Le réseau **discrimine** (logits à 0,86 de distance). Mais la politique **jouée** ne
discrimine pas (0,194, sous le bruit p95 de 0,213). L'écart est donc dans
l'**échantillonnage**, pas dans la représentation.

La politique est tirée par `multinomial` sur le softmax, **jamais** `argmax` (choix explicite
du projet — l'agent est entraîné par REINFORCE). Or les logits ont une norme de **0,65** face
à une ressource et **0,26** face à un mur :

| Norme des logits | Proba de l'action préférée |
|---|---|
| **0,26** (mur, mesuré) | **17,8 %** |
| **0,65** (ressource, mesuré) | **24,2 %** |
| 2,0 | 55,2 % |
| 5,0 | 96,1 % |
| *uniforme* | *14,3 %* |

**L'agent sait quelle action préférer — mais il ne la joue qu'une fois sur quatre.** Sa
préférence est réelle et correcte ; elle est simplement **trop faible pour survivre au
tirage**.

### La chaîne complète, enfin cohérente

Cela réconcilie les mesures qui semblaient se contredire :

| Mesure | Explication |
|---|---|
| Entropie **basse** et qui baisse (1,70) | l'agent A des préférences |
| Distance des politiques **au bruit** (0,194) | elles sont trop faibles pour se voir dans les actions tirées |
| Anti-corrélation du fourrage (ratio 0,67) | le geste correct est préféré mais rarement tiré |
| `Env` à **0,1 %** au niveau 4 | trop peu de succès pour renforcer l'amplitude |

**Ce n'est ni un capteur, ni une récompense, ni une géométrie, ni un effondrement de
représentation. C'est un problème d'AMPLITUDE de la politique.**

### ⚠️ Ce qui reste NON établi

- **Une seule graine, un seul `.brain`.** Le fait qualitatif (logits distincts, norme
  faible) est net ; les chiffres exacts lui sont propres.
- **La cause de la faible amplitude n'est PAS établie.** Trois candidats, aucun mesuré :
  le coefficient d'entropie (`COEFF_ENTROPIE_GUIDE = 0,02`) qui pousse activement vers
  l'uniforme ; l'érosion nocturne qui rabote `tete_motrice` ; le manque de succès qui ne
  consolide aucune préférence forte.
- ⚠️ **Ne pas « corriger » en passant à `argmax`** : le projet documente que l'agent, entraîné
  par REINFORCE, n'a jamais expérimenté son mode déterministe — le forcer produit des boucles
  infinies et un diagnostic faux (leçon du banc d'ablation, en tête de `sonde_c1_c2.py`).

---

## 4nonies. Les quatre suspects de la faible amplitude — deux disculpés (25/08/2026)

La sonde de perméabilité a établi que le goulot est **l'amplitude des logits** (norme 0,65 ⇒
l'action préférée n'est tirée que **24 %** du temps). Quatre causes candidates étaient
ouvertes. Deux tombent, une est réfutée, une reste.

### Suspect 1 — `COEFF_ENTROPIE` — 🟢 DISCULPÉ

Le bonus d'entropie est *littéralement conçu* pour pénaliser les logits trop grands. Si le
gradient de tâche s'effondre, il n'aurait plus de contre-pouvoir.

**Mesure analytique** (les deux gradients sont en forme fermée, aucune approximation) :

| Norme des logits | coeff | ‖grad ACTEUR‖ | ‖grad ENTROPIE‖ | ratio |
|---|---|---|---|---|
| 0,263 (mur, mesuré) | 0,02 | 0,8985 | 0,0007 | **0,0008** |
| 0,651 (ressource, mesuré) | 0,02 | 0,9122 | 0,0016 | **0,0018** |
| 0,651 | **0,06** (maximum) | 0,9122 | 0,0049 | **0,0053** |

Même au coefficient **maximum**, l'entropie pèse **0,5 %** du gradient de l'acteur. Le seuil
de bascule est un avantage de **0,0019** ; l'avantage réel est de l'ordre de **0,2**
(σ = 0,049 par tick × √20 ticks cumulés à γ=0,95), soit **~100×** au-dessus.

**Pourquoi le raisonnement ne se déclenche pas** : `Env` s'est effondré, mais **pas la
récompense totale**. `Bio` en porte 52,1 % et fournit toujours un avantage exploitable. Le
contre-pouvoir existe — il vient du corps, plus du but.

🟡 **Un point relevé en lisant le code, non mesuré** : la perte d'acteur est **masquée** par
le gradient causal (v41.31, ~38 % des ticks retenus), l'entropie **ne l'est pas** — c'est
documenté comme voulu. Sur les ticks stériles, l'entropie est donc le **seul** gradient
atteignant `tete_motrice`. Ça ne renverse pas le verdict global, mais mérite une mesure
séparée.

### Suspect 2 — L'érosion nocturne — 🟢 DISCULPÉ

| COUCHE | ‖base‖ | ‖naissance‖ | % |
|---|---|---|---|
| **`tete_motrice`** | 3,4078 | 3,4077 | **100,0 %** |
| `hippocampe` | 4,6430 | 4,6483 | 99,9 % |
| `cortex_prefrontal` | 1,4390 | 1,4624 | 98,4 % |
| `fusion_memoire` | 4,4597 | 4,6258 | 96,4 % |
| `analyseur` | 3,6555 | 4,0885 | 89,4 % |
| `porte_visuelle` | 4,4952 | 5,2593 | 85,5 % |
| `integrateur_bio` | 4,1319 | 5,1722 | 79,9 % |

**`tete_motrice` est à 100,0 % de sa norme de naissance** — pas érodée du tout. Le plancher
vital (10 %) n'est atteint par **aucune** couche. Le bug d'extinction v34.0 est bien corrigé.

⚠️ **Correction d'une sur-lecture de ma part** : j'avais noté `annexe_weight = 0,000000` comme
une découverte (« la tête motrice n'a rien appris »). **C'est attendu** :
`annexe_weight.zero_()` (l. 343) fait partie du cycle de sommeil — consolidation dans
`base_weight`, puis remise à zéro pour le jour suivant. Le `.brain` étant sauvé **après** la
nuit, l'annexe y est **toujours** nulle. Ce n'était pas un signal.

### La seule trace exploitable — la myéline

La myéline, elle, **n'est pas remise à zéro** la nuit : c'est une trace cumulative, et elle
ne peut venir **que** du gradient (invariant v34.0).

| | Valeur |
|---|---|
| `myeline_M` max sur `tete_motrice` | **0,001040** |
| Référence historique du dépôt (v34.0-fix1) | 0,0038 |
| `SEUIL_CRISTAL` (jamais franchi) | 0,80 |

Le gradient atteignant la tête motrice est effectivement **minuscule** — mais ce n'est **pas
nouveau** : c'est l'état chronique du projet depuis des mois.

### Suspect 4 — Le manque de temps — 🔴 RÉFUTÉ

Campagne appariée **n = 20 × 1500 jours** : plafond au niveau 4, et la tendance de maîtrise
n'est **jamais positive** sur trois mesures (−0,44 · −4,57 · −4,78). Ce n'est pas de la
lenteur, c'est un **plateau**.

### Bilan des quatre

| Suspect | Verdict | Preuve |
|---|---|---|
| 1. Coefficient d'entropie | 🟢 **disculpé** | 0,5 % du gradient de l'acteur |
| 2. Érosion nocturne | 🟢 **disculpé** | `tete_motrice` à 100,0 % |
| 3. Manque de signal | 🟡 **compatible** | myéline à 0,00104 |
| 4. Manque de temps | 🔴 **réfuté** | plateau sur 1500 j, n=20 |

⚠️ **« Compatible » n'est pas « démontré ».** Le suspect 3 est le dernier debout, mais par
élimination — pas par mesure directe. Il faudrait instrumenter le gradient **réellement reçu
par `tete_motrice` pendant une journée**, pas l'état du cerveau après la nuit.

---

## 4decies. LE DOSSIER SE FERME — c'est du THRASHING, pas un gradient minuscule

### 🔴 D'abord : la sonde de gradient était CASSÉE depuis deux versions

`sonde_gradient.py` (v33.1) avait une signature figée qui ignorait `chocs_dopamine`
(v37.1, distillation sélective) et `transitions` (v41.31, gradient causal). Elle plantait
sur `TypeError` **dans `executer_nuit`** — donc **après une journée complète de calcul**,
invisible à toute vérification courte.

C'est exactement le défaut que le CLAUDE.md décrit pour la détection de greffe : *« le crash
ne survient ni au chargement, ni pendant la journée, mais à la première `executer_nuit` »*.
Corrigé par `**extra`, qui repasse tout à l'originale — la sonde ne cassera plus au prochain
paramètre ajouté.

### La mesure — 8 jours, graine 11

Les deux causes candidates, et leur discriminant `‖Σg‖ / Σ‖g‖` :
**proche de 1** = pas alignés (gradient faible mais cohérent) · **proche de 0** = annulation.

| jour | ‖g_jour‖ | ‖Σg‖ (cumul) | Σ‖g‖ | alignement | repère 1/√n |
|---|---|---|---|---|---|
| 1 | 0,2042 | 0,2042 | 0,2042 | 1,0000 | 1,0000 |
| 2 | 0,2274 | 0,3394 | 0,4316 | 0,7864 | 0,7071 |
| 4 | 0,0930 | 0,4845 | 0,6639 | 0,7298 | 0,5000 |
| 6 | 0,1628 | 0,6807 | 0,9606 | 0,7086 | 0,4082 |
| 7 | 0,0947 | 0,6436 | 1,0552 | 0,6099 | 0,3780 |
| **8** | **0,2569** | **0,5204** | 1,3121 | **0,3966** | **0,3536** |

### 🔴 Verdict : le gradient N'EST PAS minuscule — il S'ANNULE

**Le gradient arrive** : 0,164 en moyenne sur `tete_motrice`, et **3200 ticks sur 3200**
portent une récompense non nulle. La cause « signal absent » est donc **écartée**.

**Mais il s'annule.** L'alignement final est **0,3966** contre un repère de marche aléatoire
de **0,3536** : les pas sont **quasi indépendants** d'un jour à l'autre. Et la trajectoire est
le vrai signal — 0,79 → 0,73 → 0,71 → 0,61 → **0,40**, une **décroissance monotone vers le
hasard**.

**Le jour 8 est décisif** : `‖g_jour‖ = 0,2569`, le **plus gros gradient des 8 jours** — et le
cumul `‖Σg‖` **RECULE** de 0,6436 à 0,5204.

> **Un gradient de 0,257 a fait reculer le cumul de 0,123.** Le plus gros pas de la semaine
> pointe **contre** la direction accumulée. C'est la définition exacte du thrashing.

### La hiérarchie du gradient — l'explication probable

| COUCHE | gradient moyen | CV | |
|---|---|---|---|
| **`integrateur_bio`** (le CORPS) | **0,9142** | **0,04** | écrase tout, et très stable |
| `tete_motrice` (la DÉCISION) | 0,1640 | 0,37 | |
| `hippocampe` | 0,0269 | 0,92 | |
| `analyseur` | 0,0240 | 0,92 | |
| **`porte_visuelle`** (la VUE) | **0,0117** | 0,94 | **78× moins que le corps** |

`integrateur_bio` reçoit **5,6×** le gradient de la tête motrice et **78×** celui de la vue —
avec un coefficient de variation de **0,04**, donc un signal quasi constant.

C'est cohérent avec la table de mixage (`Bio` = 52,1 % de la dispersion au niveau 4) : **le
gradient suit le signal, et le signal est corporel.** La vue ne reçoit presque rien à
apprendre, ce qui explique qu'elle ne conditionne pas la décision.

### Ce que cela ferme, et ce que cela ouvre

| Suspect | Verdict final |
|---|---|
| 1. Coefficient d'entropie | 🟢 disculpé (0,5 % du gradient) |
| 2. Érosion nocturne | 🟢 disculpé (`tete_motrice` à 100,0 %) |
| 3. Manque de signal | 🟢 **DISCULPÉ** — gradient 0,164, 3200/3200 ticks récompensés |
| 4. Manque de temps | 🔴 réfuté (plateau, n=20 × 1500 j) |
| **5. THRASHING** | 🔴 **CONFIRMÉ** — alignement 0,40 vs hasard 0,35 |

**La politique ne grandit pas parce qu'elle est tirée dans des directions contradictoires
d'un jour à l'autre.** L'amplitude faible n'est pas un défaut d'apprentissage : c'est
l'**équilibre** d'une marche aléatoire.

⚠️ **NON établi — la cause du thrashing.** Trois pistes, aucune mesurée :
- **le corps domine** (`integrateur_bio` à 78× la vue) et ses besoins **alternent** —
  affamé un jour, assoiffé le lendemain, donc une direction opposée ;
- **le masquage causal** (v41.31) retient ~38 % des ticks, différents chaque jour ;
- **la carte change** entre les jours (P17), donc la politique optimale aussi.

⚠️ **Une seule graine, 8 jours.** L'alignement à 0,40 est net face au repère 0,35, mais
8 points ne permettent pas d'écarter le bruit avec certitude — il faudrait n ≥ 20 jours et
plusieurs graines pour en faire une mesure et non un indice.

---

## 4undecies. Les trois pistes du thrashing — A et C réfutées, le plafond expliqué

### Le protocole

A/B **apparié** : même `.brain` de départ, même graine (11), 12 jours, un seul facteur change
par bras. Le témoin A a servi aux deux comparaisons.

⚠️ **`--soif-figee` a dû être créé** : contrairement à ce que j'avais annoncé, aucun drapeau
d'ablation métabolique n'existait (seulement `--sans-heritage`, `--sans-memoire-cartes`,
`--sans-corps-rollout`, `--sans-economie-action`, `--sans-douleur`). Il **gèle** l'axe
hydrique à 1.0 plutôt que de le supprimer — l'agent garde ses cinq sens, seul l'axe cesse de
tirer la politique. Même discipline que `--sans-douleur`, avec **assertion runtime** que le
drapeau atteint le module (correctif du bug v41.4, où trois bras étaient identiques).

### Les trois bras

| BRAS | alignement final | écart vs témoin |
|---|---|---|
| **A — cursus libre** (témoin) | **0,3428** | — |
| **B — carte verrouillée** (piste A) | **0,2630** | **−0,0798** |
| **C — soif figée** (piste C) | **0,3389** | **−0,0039** |
| *repère marche aléatoire (1/√12)* | *0,2887* | |

🔴 **Piste A réfutée, effet INVERSE** : verrouiller le monde **aggrave** le thrashing de 23 %,
et fait passer l'alignement **sous** le hasard — une annulation *active*. L'instabilité du
cursus serait plutôt un facteur **stabilisant**.

🔴 **Piste C réfutée, effet NUL** : geler l'axe hydrique change l'alignement de **−0,0039**,
soit **20× moins** que la piste A. Le conflit des organes n'est pas la cause.

### 🟢 Le vrai résultat — le plafond est le CLIPPING

`‖Σg‖` plafonne au **même endroit** dans les trois bras :

| | A | B | C |
|---|---|---|---|
| `‖Σg‖` final | **0,8219** | **0,8329** | **0,8201** |

La direction utile sature identiquement, que la carte soit fixe ou libre, que le corps tire
sur un ou deux axes. **Le plafond ne dépend d'aucune des causes testées.**

`apprendre_journee` appelle `clip_grad_norm_(toutes les params, max_norm=1.0)`. Norme globale
mesurée :

| COUCHE | gradient moyen | part du budget global |
|---|---|---|
| **`integrateur_bio`** | **0,9142** | **98 %** |
| `tete_motrice` | 0,1640 | 18 % |
| `fusion_memoire` | 0,0511 | 5 % |
| `porte_visuelle` | 0,0117 | **1 %** |
| **TOTAL (norme globale)** | **0,9315** | **93 % du plafond de 1,0** |

**Le gradient global est à 93 % du seuil de clipping à chaque nuit — et `integrateur_bio`
en consomme 98 %.**

> **Le clipping ne CRÉE pas le déséquilibre, il le FIGE.** Quand le corps sature le budget,
> la vue ne peut pas grandir — quelle que soit l'information qu'elle porte. C'est le
> mécanisme qui relie toutes les mesures de la campagne : le ratio 78× vue/corps, la
> non-discrimination mur/pomme, et le plafond de `‖Σg‖` insensible aux ablations.

### ⚠️ Ce qui reste NON établi

- **Le clipping est une hypothèse cohérente, pas une mesure.** Il faudrait mesurer la norme
  globale **avant** clipping, nuit par nuit, et compter les nuits effectivement clippées.
  La sonde lit les `.grad` **après** `backward` mais l'ordre exact vis-à-vis du clip n'a pas
  été vérifié.
- **Piste B (masquage causal) reste non testée.**
- **Une seule graine, 12 jours** par bras. Les sens des effets sont nets (A négatif, C nul),
  mais ce ne sont pas des mesures au sens des 20 graines.
- ⚠️ L'ablation A était **partielle** (P17 révisait encore 1 fois/jour sur 9 jours), donc son
  écart est un **minorant**.

---

## 4duodecies. LE CLIPPING SE DÉCLENCHE — 12 nuits sur 12

### 🔴 D'abord : ma mesure précédente était une TAUTOLOGIE

J'avais annoncé « la norme globale vaut 0,9315, soit 93 % du plafond de 1,0 » comme un
indice fort. **C'était sans valeur.** L'ordre réel est :

```python
perte_totale.backward()
torch.nn.utils.clip_grad_norm_(..., 1.0)   # ← le clip
self.optimizer.step()
```

La sonde lit les `.grad` **après** que la fonction a rendu la main, donc **après** le clip.
Ma valeur était déjà écrasée, et **mécaniquement bornée à 1,0 par construction**. Une norme
post-clip ne peut par définition jamais démontrer que le clip se déclenche.

Ce n'était pas un résultat « trop propre » mais **trop cohérent** — une variante du même
piège.

**Le correctif** : `clip_grad_norm_` **retourne** la norme totale avant écrêtage. On
l'intercepte le temps de l'appel (restauration dans un `finally`), ce qui donne la seule
mesure honnête.

### La mesure — 12 jours, graine 11

| jour | norme brute | clippé ? | facteur | corps | décision | vue |
|---|---|---|---|---|---|---|
| 1 | 2,4702 | **OUI** | 0,4048 | 36,6 % | 8,3 % | 0,1 % |
| 4 | **6,6533** | **OUI** | **0,1503** | 13,8 % | 1,4 % | 0,1 % |
| 6 | 1,5089 | **OUI** | 0,6627 | 64,0 % | 10,8 % | 0,2 % |
| 12 | 1,3081 | **OUI** | 0,7645 | 66,1 % | 31,4 % | 0,7 % |

| | |
|---|---|
| **Nuits clippées** | **12 / 12 (100 %)** |
| Norme brute moyenne | **2,8193** — soit **×2,8** le plafond |
| Norme brute maximale | **6,6533** — **×6,7** le plafond |
| Facteur de division moyen | **0,4435** (tout divisé par ~2,3) |

🔴 **Le clipping se déclenche à chaque nuit, sans exception.** Le gradient brut dépasse le
plafond d'un facteur 1,3 à 6,7 selon les jours.

### Part du budget BRUT (la seule lecture valable)

| | moyenne | min | max |
|---|---|---|---|
| **corps** (`integrateur_bio`) | **40,1 %** | 13,8 % | 66,1 % |
| **décision** (`tete_motrice`) | **10,0 %** | 1,4 % | 31,4 % |
| **vue** (`porte_visuelle`) | **0,67 %** | 0,1 % | 1,8 % |

**Le corps prend 60× plus de budget que la vue.**

### ⚠️ LA NUANCE QUI CHANGE LA CONCLUSION

**`clip_grad_norm_` divise TOUTES les composantes par le même facteur.** Il ne change donc
**pas** les parts relatives : la vue aurait ses 0,67 % du budget **avec ou sans clip**.

> **Le clipping n'est PAS la cause du déséquilibre. Il réduit l'amplitude ABSOLUE de
> l'apprentissage (÷2,3 en moyenne), pas la répartition.**

Ce que le clipping explique réellement :

| Il explique | Il n'explique PAS |
|---|---|
| la **faible amplitude** des logits (tout est divisé par 2,3 chaque nuit) | le **déséquilibre** corps/vue (les parts sont intactes) |
| le **plafond de `‖Σg‖`** identique dans les 3 bras (la norme est bornée à 1,0) | le **thrashing** (une division uniforme ne change aucune direction) |

**Le déséquilibre 60× est ANTÉRIEUR au clip** — il vient de la structure du signal
(`Bio` = 52,1 % de la dispersion de la récompense, mesuré à l'étape 3), pas de l'optimiseur.

### ⚠️ Ce qui reste ouvert

- **Le thrashing reste inexpliqué.** Le clipping est une division scalaire : il ne peut pas
  faire pointer un gradient dans la direction opposée. Les pistes A et C sont réfutées, la
  **piste B (masquage causal)** reste non testée.
- **Les parts ne somment qu'à ~51 %** : les couches suivies ne couvrent pas tout le réseau
  (audio, C2, têtes vocales et C3 manquent). La moitié du budget n'est pas attribuée.
- **Une seule graine, 12 jours.**

⚠️ **Ne pas « corriger » en relevant `max_norm`.** Le clipping à 1,0 est un garde-fou
standard, et la norme brute atteint **6,65** certains jours — le relever exposerait le réseau
à des pas de gradient massifs sur des couches déjà instables. Toute modification exige un
A/B, et le fait que le clip morde 12/12 est une **observation**, pas un défaut démontré.

---

## 4terdecies. La « matière noire » n'existait pas — et le corps prend 93 % du gradient

### 🔴 Le troisième bug de lecture de la campagne, le mien

J'ai annoncé successivement « 49 % du gradient manquant », puis « 84 % ». **Les deux étaient
faux**, pour la même raison :

```python
def _clip_espion(params, max_norm, *a, **k):
    totale = _clip_reel(params, max_norm, ...)   # ← le clip a lieu ICI
    _brut["norme"] = float(totale)               # ✅ valeur AVANT
    for ... : parts[nom] = |p.grad|              # ❌ lu APRÈS le clip
```

La norme totale était juste, mais les **parts** étaient lues après que le clip les avait
toutes divisées. **La signature était sous mes yeux** : `racine(Σ carrés) = 1,000000
EXACTEMENT` sur 6/6 jours — c'est la norme post-clip par construction.

**Vérification structurelle décisive** : le réseau ne contient que **12 paramètres
entraînables** (un `annexe_weight` par couche, énumérés). Il n'existe matériellement aucun
endroit où du gradient pourrait se cacher — la somme des carrés *doit* égaler la norme
globale au carré.

C'est le **troisième** défaut de cette famille dans la campagne (chaleur v41.25-fix1, sonde
de discrimination fix1, celui-ci) : **lire une grandeur après l'opération qui la modifie.**

### La vraie répartition (parts lues AVANT le clip)

`Σ(carrés)/n² = 100,0 %` sur 6/6 jours — comptabilité exacte, aucune matière noire.

| | moyenne | min | max |
|---|---|---|---|
| **corps** (`integrateur_bio`) | **92,7 %** | 90,4 % | 96,5 % |
| **décision** (`tete_motrice`) | **16,0 %** | 9,3 % | 22,7 % |
| **vue** (`porte_visuelle`) | **0,77 %** | 0,2 % | 1,7 % |

**Rapport corps / vue : 121×.**

⚠️ Mon chiffre précédent (40,1 % / 0,67 %, ratio 60×) était **faux**. Le corps ne prend pas
40 % du budget mais **93 %**.

### Les trois faits qui tiennent

**(1) Le corps dicte 93 % du gradient.** L'intuition initiale (« le corps dicte 98 % ») était
donc juste dès le départ ; c'est la mesure qui était cassée. La vue reçoit **0,77 %** — elle
ne peut pas apprendre à distinguer une pomme d'un mur avec ça, ce qui referme le dossier de
la non-discrimination (§4sexies).

**(2) L'audio ne dissipe RIEN.** `porte_auditive`, `generateur_attente_audio`, `tete_vocale`
et `tete_requete` sont à **0,000000 exact sur 6/6 jours**, les quatre. Ils coûtent des
**paramètres** (24 % du réseau) et du **calcul**, jamais du gradient — ils ne peuvent donc
pas causer le thrashing. L'hypothèse « la moitié de l'énergie se dissipe dans des organes
morts » est **réfutée**.

**(3) C2 reçoit 2,02× le gradient de la décision** (0,3241 contre 0,1601) — alors que le
couper ne change le score de **0,0 point sur 6 niveaux** (v41.29, 78 cellules). C'est du
gradient réellement investi dans un module sans effet mesuré. **Suspect sérieux, non testé.**

### ⚠️ Ce que cela ne dit toujours pas

Le **thrashing reste inexpliqué**. Le clipping est une division scalaire (il ne renverse
aucune direction), l'audio est à zéro, et les pistes A et C sont réfutées. Restent la
**piste B** (masquage causal) et le nouveau suspect **C2**.

⚠️ Une seule graine, 6 jours pour la répartition.

---

## 4quaterdecies. 🔴 LA VUE EST STRUCTURELLEMENT COUPÉE DE LA POLITIQUE

### Le mécanisme proposé, et ce qui l'a réfuté

L'hypothèse : C2 pèse le double de C1 dans le budget, donc **il dicte les mises à jour du
tronc commun** — le sol se dérobe sous C1, d'où le thrashing.

**Vérification par lecture du code**, ligne 1149 de `_executer_c1_reflexe` :

```python
pensee_detachee = pensee_enrichie.detach()      # ← LE TRONC EST COUPÉ
pensee_bio = self.integrer_bio(pensee_detachee, vecteur_bio)
logits_instinct = self.tete_motrice(pensee_bio)
```

⚠️ Ce `.detach()` est **non documenté**, contrairement à tous les autres du fichier.

### La carte des chemins de gradient — mesurée, pas déduite

Trois pertes injectées séparément, gradient lu couche par couche :

| Source de la perte | `porte_visuelle` | `hippocampe` | `analyseur` | `integrateur_bio` | `tete_motrice` | `cortex_prefrontal` |
|---|---|---|---|---|---|---|
| **logits C1** (la politique) | **0,000000** | **0,000000** | **0,000000** | 6,127 | 5,016 | 0,000000 |
| **valeur C2** | **0,000000** | **0,000000** | **0,000000** | 4,907 | 0,000000 | 1,774 |
| `bus_latent` (JEPA) | **92,581** | 0,000000 | 0,000000 | 0,000000 | 0,000000 | 0,000000 |

### 🔴 Trois conséquences

**(1) Le mécanisme proposé est réfuté.** C2 ne peut pas secouer le tronc : il en est
**coupé**. Une ablation du gradient de C2 ne toucherait que `integrateur_bio` et C2 lui-même
— jamais `porte_visuelle`, `hippocampe` ou `analyseur`.

**(2) Les 0,77 % de la vue étaient MAL INTERPRÉTÉS** — y compris par moi. Ce n'est pas une
compétition perdue contre le corps : **la vue ne reçoit AUCUN gradient de la politique**.
Zéro exact, pas « peu ». Ses 0,77 % viennent uniquement du **JEPA** — apprendre à *prédire*
l'état suivant, jamais à *agir* dessus.

> **La vision de l'agent n'est pas asphyxiée par le corps. Elle est structurellement
> déconnectée de la récompense.** Aucun rééquilibrage de budget ne pourrait la reconnecter :
> il n'y a pas de fil.

**(3) Le vrai point de collision est `integrateur_bio`.** C'est la **seule** couche où C1
(6,127) et C2 (4,907) rétropropagent **tous les deux**. Le mécanisme proposé est donc juste
dans son principe — deux têtes qui se disputent une couche partagée — mais **d'un étage trop
haut**. La collision n'a pas lieu dans le tronc, elle a lieu dans l'intégrateur bio.

### Ce que cela change au plan

L'ablation « couper le gradient de C2 » devient **plus précise, pas caduque** : elle teste
maintenant une hypothèse exacte — *C1 et C2 se disputent-ils `integrateur_bio` ?* — au lieu
d'une hypothèse fausse sur le tronc.

⚠️ **Ce `.detach()` non documenté est un chantier à part entière.** Il peut être un choix
délibéré (empêcher la politique de déformer les représentations perceptives, une pratique
courante) ou un défaut. Rien dans le code ne le dit. **Ne pas le retirer sans A/B** : le
supprimer rebrancherait la politique sur la vue, ce qui est un changement architectural
majeur, exactement le genre de modification que cette campagne a appris à ne pas faire sans
mesure.

---

## 4quindecies. 🟢 LE THRASHING EST EXPLIQUÉ — la collision C1/C2 dans `integrateur_bio`

### L'ablation

`--sans-gradient-c2` : `valeurs_tensor` est détaché avant la perte critique. Le **forward de
C2 reste intact** — il produit ses valeurs, pèse dans l'arbitrage, fournit les avantages.
Seule sa **rétropropagation** cesse. C'est ce qui isole la *collision* de l'*utilité*.

Écrit dans le module nommé puis relu par assertion ; sortie confirmée
`🔬 [ABLATION] gradient de C2 COUPÉ — forward intact`.

### 🟢 Le résultat — l'alignement DOUBLE

| BRAS | alignement final | écart vs témoin |
|---|---|---|
| Témoin (cursus libre) | 0,3428 | — |
| Piste A — carte verrouillée | 0,2630 | −0,0798 |
| Piste C — soif figée | 0,3389 | −0,0039 |
| **AB1 — gradient de C2 coupé** | **0,6751** | **+0,3323** |
| *repère marche aléatoire* | *0,2887* | |

**+97 %.** L'effet est **4,2×** celui de la piste A et **85×** celui de la piste C.

### La trajectoire s'inverse

| | jour 1 | 2 | 6 | 8 | 12 |
|---|---|---|---|---|---|
| Témoin | 1,00 | 0,79 | 0,71 | 0,40 | **0,34** |
| **AB1** | 1,00 | 0,53 | 0,75 | 0,76 | **0,68** |

Le témoin **décroît vers le hasard** ; AB1 **monte et se stabilise**.

### Et la saturation disparaît

| | `‖Σg‖` final |
|---|---|
| Témoin | **0,8219** (plafonne dès le jour 6) |
| AB1 | **3,8388** — **×4,7**, croissance continue |

### ⚠️ Le confondant, écarté

Couper le gradient de C2 le retire du total — cela pourrait mécaniquement gonfler
l'alignement. **Ce n'est pas le cas** : l'alignement est mesuré sur `tete_motrice` **seule**,
et `cortex_prefrontal` n'entrait pas dans son calcul.

Mieux, le gradient de `tete_motrice` **augmente** :

| | gradient moyen sur `tete_motrice` |
|---|---|
| Témoin | 0,1998 |
| **AB1** | **0,4739** — **×2,37** |

**Plus de signal ET mieux orienté.**

### Le mécanisme

C1 et C2 se disputaient `integrateur_bio` — la **seule** couche partagée (6,127 contre
4,907), dont la sortie est **l'entrée de `tete_motrice`**. Quand C2 tirait la représentation
bio dans sa direction, C1 devait réapprendre sur un **sol mouvant**. Le sol cesse de bouger,
C1 construit enfin une direction stable.

> **Le thrashing n'était ni le monde, ni les organes, ni le clipping. C'était le critique qui
> déformait, chaque nuit, la représentation sur laquelle la politique s'appuyait.**

### ⚠️ Ce que cela ne dit PAS

- **Ce n'est PAS un correctif à appliquer.** Couper le gradient de C2 **empêche le critique
  d'apprendre** : ses estimations dérivent, donc les avantages qu'il fournit à l'acteur se
  dégradent. Ce bras mesure l'**alignement**, jamais la performance. Un agent au gradient
  parfaitement aligné vers une mauvaise direction n'apprend rien de bon.
- **La vraie question devient : comment faire cohabiter C1 et C2 sans collision ?** Deux
  pistes classiques, aucune mesurée — une couche bio **par tête** (coûteuse, mais supprime le
  partage), ou un `.detach()` côté C2 seulement (C2 lirait la représentation sans la
  déformer, symétrique du `.detach()` déjà présent l. 1149 pour le tronc).
- **Une seule graine, 12 jours.** L'effet est énorme (+97 %) et sa direction sans ambiguïté,
  mais il faut n ≥ 20 pour en faire une mesure.
- **Piste B (masquage causal) en cours** — son résultat peut être additif ou redondant.

---

## 4sedecies. La matrice complète des ablations du thrashing (26/08/2026)

| BRAS | alignement | `‖Σg‖` final | grad/jour sur `tete_motrice` |
|---|---|---|---|
| **Témoin** | 0,3428 | 0,8219 | 0,1998 |
| A — carte verrouillée | 0,2630 | 0,8329 | — |
| C — soif figée | 0,3389 | 0,8201 | — |
| **AB1 — gradient C2 coupé** | **0,6751** | **3,8388** | **0,4739** |
| AB2 — sans masquage causal | 0,5879 | **0,5571** | **0,0790** |
| AB3 — detach asymétrique | 0,4298 | 1,8674 | 0,3621 |

### AB2 — piste B réfutée : le masquage CONCENTRE, il ne perturbe pas

L'alignement monte (+71 %) **mais le gradient s'effondre** : 0,1998 → **0,0790**, soit
**÷2,5**. Et `‖Σg‖` **baisse** (0,82 → 0,56).

**L'alignement monte parce qu'il reste moins de signal à contredire.** C'est l'alignement de
l'inertie, pas de l'apprentissage.

🟢 **Le code l'avait prédit** (commentaire v41.31) : *« un `.mean()` naïf laisserait `T` au
dénominateur : à 61,7 % de masquage, le gradient des gestes UTILES serait divisé par ~2,6 »*.
**Mesuré : ÷2,5.** Le masquage causal est une mécanique de **concentration**, pas une source
de chaos. Piste B close.

### AB3 — le detach asymétrique : à moitié concluant

✅ **La garde est passée** : `cortex_prefrontal` reçoit **0,638/jour** (min 0,294, max 0,945).
Le drapeau a bien pris, et ce n'est **pas** AB1 déguisé — C2 apprend toujours.

| | résultat |
|---|---|
| alignement | 0,3428 → **0,4298** (+25 %, contre +97 % pour AB1) |
| `‖Σg‖` final | 0,8219 → **1,8674** (×2,3 — **la saturation disparaît**) |
| gradient/jour | 0,1998 → **0,3621** (×1,8) |

**Mais la trajectoire s'effondre en fin de run :**

| jours | alignement |
|---|---|
| 1 → 8 | 1,000 → 0,723 (**supérieur à AB1** sur cette portion) |
| 9 → 12 | 0,520 → **0,430** (chute brutale) |

### 🔴 Mon explication de cette chute était FAUSSE

J'ai supposé que le detach était **incomplet** : C2 lit `pensee_bio` à deux endroits
(l. 1397 pour la valeur courante, l. 1204 pour le rollout), et je n'avais couvert que le
premier. Le rollout rappelle `integrateur_bio` à chaque saut d'horizon (l. 1058) — la
collision aurait donc persisté par ce second chemin.

**Réfuté par le code et par la mesure** : `simuler_futur_et_planifier` porte
**`@torch.no_grad()`** (l. 971). Le rollout ne rétropropage **rien**. Preuve empirique —
`valeurs_simulees.sum().backward()` lève :

```
RuntimeError: element 0 of tensors does not require grad and does not have a grad_fn
```

**Le second chemin n'existe pas. Mon detach couvrait bien tout le gradient de C2 vers
`integrateur_bio`.**

### Ce qui reste pour expliquer la chute — non mesuré

La différence entre AB1 et AB3 n'est **pas** le chemin des poids partagés (identique dans les
deux) mais le fait que **C2 continue d'apprendre** en AB3. Or un C2 qui apprend **change ses
valeurs**, donc **change les avantages** `A = R − V`, donc **change le gradient de l'acteur**.

**Ce couplage passe par la récompense, pas par les poids.** Il subsiste dans AB3 et disparaît
dans AB1 — ce qui explique pourquoi AB1 obtient un alignement supérieur *sans être un
correctif viable* (sa ligne de base dérive, donc la variance des avantages explose).

⚠️ **Hypothèse, pas mesure.** Elle se testerait en lisant la variance des avantages jour par
jour dans les deux bras.

### ⚠️ Portée

**Une seule graine, 12 jours, sur banc de sonde — pas sur le cursus.** Même excellent, AB3
devrait passer une campagne appariée à **n ≥ 20** avant d'être revendiqué : la v41.31 a
montré ce que vaut un résultat de banc qui ne survit pas au cursus complet (+2,57 pt au banc,
+0,05 sur 20 graines).

---

## 4septdecies. La variance des avantages — ni confirmée, ni réfutée

### L'hypothèse

La chute d'alignement d'AB3 au jour 9 viendrait de la **ligne de base** : C2 continue
d'apprendre, donc `V(s)` bouge, donc l'avantage `A = R − V` tremble, donc une même action
est récompensée un jour et pénalisée le lendemain.

⚠️ **Précaution de lecture** : `apprendre_journee` **normalise** les retours quand
`std > 1e-6`. La sonde réplique fidèlement cette normalisation, donc `|avant|` est bien la
valeur que le gradient voit — mais une explosion de variance *brute* y serait masquée.

### 🟡 La signature temporelle existe

| jour | `|ret|` | `|avant|` | alignement | Δ align |
|---|---|---|---|---|
| 7 | 0,1354 | 0,7276 | 0,7746 | +0,0216 |
| **8** | **0,2837** ← max | 0,8503 | 0,7231 | −0,0515 |
| **9** | 0,0994 | **0,5644** ← min | **0,5196** | **−0,2035** |
| 10 | 0,2135 | 0,7815 | 0,3938 | −0,1258 |

Le jour 8 porte le `|ret|` **le plus haut** des 12 (0,2837 contre 0,161 de moyenne), et le
jour 9 le `|avant|` **le plus bas** — avec la plus forte chute d'alignement du run.

AB3 a par ailleurs une **volatilité des retours 1,5×** celle d'AB1 (0,0520 contre 0,0336).

### 🔴 Mais elle ne suffit pas — trois réserves

**(1) La corrélation est faible et non significative.** « `|ret|` élevé un jour → chute
d'alignement le lendemain » donne **r = −0,391** sur 11 points. À n=11 il faudrait |r| > 0,60
environ. Ce n'est pas concluant.

**(2) Le mécanisme ne se déclenche pas de façon reproductible.** Le jour 10 a aussi un `|ret|`
élevé (0,2135) et l'alignement continue de chuter — mais le jour 5 (0,1674) ne produit
**rien**. Un mécanisme causal devrait se déclencher à chaque fois.

**(3) La variance des avantages N'EXPLOSE PAS.** L'écart-type de `|avant|` vaut **0,0839** en
AB3 contre **0,0793** en AB1 — soit **+5,8 %**. Le mécanisme proposé prédit une explosion ;
la mesure donne un écart négligeable.

### Verdict

🟡 **Ni confirmée, ni réfutée.** Il y a une coïncidence temporelle nette au jour 8-9, mais
**pas la signature statistique que le mécanisme exige**. À une seule graine et 12 points, un
décrochage unique peut être du bruit — c'est exactement le cas que la règle de mesure classe
comme **anecdote**, jamais comme mesure.

**Ce qu'il faudrait pour trancher** : 20 graines × 12 jours minimum, en comparant la
distribution des chutes d'alignement conditionnellement au `|ret|` de la veille. Trois heures
de calcul, contre une conclusion tirée d'un seul décrochage.

⚠️ **Ne pas coder de correctif sur cette base.** Les remèdes classiques (learning rate
réduit pour le critique, clipping de la perte de valeur, lissage temporel) sont tous
plausibles — mais appliquer l'un d'eux maintenant reviendrait à corriger une cause non
établie, exactement ce que cette campagne a passé trois jours à éviter.

---

## 5. Ce que la journée établit — et ce qu'elle ne dit pas

### Établi (mesures directes, banc déterministe δ_A/A = 0)

| Fait | Chiffre |
|---|---|
| `Bio` domine la dispersion de la récompense | **44,0 %** |
| `Curiosite` est un décalage d'origine | moyenne 6× `Bio`, σ 4ᵉ |
| Satiété au plancher | **40/40 nuits** |
| Valences ≡ soulagement réel | écart **4,4 %** |
| Le hasard récolte mieux que l'agent | **3,33 vs 1,68 FOOD/jour** |
| L'agent TENTE de manger, de plus en plus | 27,2 → **74,2** gestes/jour |
| Mais la conjonction échoue | taux de saisie **8,1 %**, ratio vs hasard **0,67** |
| Le soulagement d'un repas | **+0,300**, soit **≈7 σ** du canal `Bio` |
| `contact_frontal` est ambigu | **82 % mur / 18 % ressource** |
| `MultiRoom` EST peuplé | 7 FOOD + 7 WATER, comme les autres |
| Mais sa densité s'effondre | **0,028 contre 0,333** — facteur **11,8** |
| **`Env` s'effondre au niveau 4** | **0,1 % du signal** — facteur **240** vs niveau 1 |
| `Bio` y monte à | **52,1 %** |
| `Jalons` est un vrai signal quand il existe | **33,9 %**, σ = 0,029 |
| L'agent ne discrimine PAS mur / ressource | distance **0,194** vs bruit p95 **0,213** |
| Et il devient MOINS discriminant | 0,253 → **0,144** sur `Empty-5x5` |
| L'entropie de la politique BAISSE | 1,7695 → **1,7034** (max ln7 = 1,946) |
| L'agent n'est PAS aplati | écart au max **0,350** contre **0,00004** pour un cerveau éteint |
| Le réseau DISCRIMINE | distance des logits **0,861** (bus 0,072 → ×12) |
| Mais ses logits sont FAIBLES | norme **0,65** ⇒ l'action préférée tirée **24 %** du temps |
| L'entropie n'y est pour rien | **0,5 %** du gradient de l'acteur, même au coeff max |
| L'érosion n'y est pour rien | `tete_motrice` à **100,0 %** de sa naissance |
| Le gradient ARRIVE | **0,164** sur `tete_motrice`, **3200/3200** ticks récompensés |
| Mais il S'ANNULE | alignement **0,3966** contre un hasard à **0,3536** |
| Le corps écrase la vue | `integrateur_bio` **0,914** contre `porte_visuelle` **0,012** (**78×**) |
| Piste A (instabilité du monde) | 🔴 réfutée — effet **inverse** (−0,0798) |
| Piste C (conflit des organes) | 🔴 réfutée — effet **nul** (−0,0039) |
| Le clipping se déclenche | **12 nuits sur 12**, norme brute moyenne **2,82** (plafond 1,0) |
| Le corps prend | **92,7 %** du budget brut contre **0,77 %** pour la vue (**121×**) |
| L'audio ne consomme RIEN | **0,000000** exact, 4 couches, 6/6 jours |
| C2 reçoit | **2,02×** le gradient de `tete_motrice`, pour **0,0 pt** d'effet mesuré |
| 🔴 La politique n'atteint JAMAIS la vue | **0,000000** exact — `.detach()` non documenté (l. 1149) |
| C1 et C2 ne partagent QUE | `integrateur_bio` (6,127 et 4,907) |
| 🟢 **Couper le gradient de C2** | alignement **0,3428 → 0,6751** (**+97 %**) |
| Et `tete_motrice` reçoit | **×2,37** de gradient (0,1998 → 0,4739) |
| Piste B (masquage causal) | 🔴 réfutée — le masque **concentre** (le retirer divise le gradient par **2,5**) |
| Detach asymétrique (AB3) | 🟡 mi-figue — alignement **+25 %**, saturation levée, mais chute au jour 9 |
| La ligne de base explique-t-elle la chute ? | 🟡 **indécis** — r = −0,391 (NS), variance des avantages +5,8 % seulement |
| Mais le clip ne cause PAS le déséquilibre | il divise tout par le même facteur (~2,3) |
| C2 pèse | **0,110 %** de 384 808 params |
| C2 croît en N, le tronc en N² | rapport **×312** à 16 dims |

### NON établi — à ne pas citer comme acquis

- ⚠️ **Une seule graine** pour la table de mixage (g11, 40 jours). Les chiffres exacts lui
  sont propres ; seul le fait qualitatif (σ = 0 exact, `Bio` dominant) est robuste.
- ⚠️ **Cinq termes jamais observés** — ablations vides. La table ne peut être arbitrée
  qu'après un run au niveau 4.
- ⚠️ **Le témoin aléatoire est à 3 graines**, sous le seuil des 20. Il établit un ordre de
  grandeur (le hasard fait mieux), pas une mesure d'effet.
- ⚠️ **Aucune des trois pistes de remplacement n'a d'appui de mesure.**

---

## 6. La leçon de méthode

**Neuf propositions, neuf réfutations, zéro ligne de correctif écrite.** Le coût total :
une sonde (~180 lignes de télémétrie pure), deux runs de 40 jours, et trois scripts de
mesure. Ce qui a été évité :

| Proposition | Ce qu'elle aurait produit |
|---|---|
| Softmax sur la table de mixage | amplification d'un terme **déjà dominant** ; et une `TEMPERATURE` posée, invisible, dont dépendraient les 9 poids |
| Densité dérivée des cases libres | 4ᵉ calibrage inopérant, **après** avoir modifié le monde sur toutes les cartes |
| Neurogenèse dirigée | `RuntimeError` au premier forward ; et si contournée, un déplacement de **miettes** présenté comme un correctif de dilution |

> **La règle n'est pas « mesurer avant de conclure ». C'est « mesurer avant de CODER ».**
> Les trois propositions étaient dogmatiquement séduisantes et internement cohérentes.
> Aucune n'était vérifiable sans instrument, et chacune aurait laissé un correctif inutile
> dans le noyau — le plus difficile à retirer, parce qu'il aurait eu l'air d'une amélioration.

---

## 7. Documents liés

- [`PLAN_v41.32`](../ameliorations/PLAN_v41.32_table_de_mixage_et_neurogenese_dirigee.md) — le plan vivant, avec l'état d'avancement
- [`21082026_anatomie_du_noyau.md`](../etat_des_lieux/21082026_anatomie_du_noyau.md) — les 225 constantes, le point d'assemblage unique
- [`22082026_campagne_v41.31_cursus_complet.md`](../etat_des_lieux/22082026_campagne_v41.31_cursus_complet.md) — la falsification n=20
- [`METABOLISME_20082026_la_variable_morte.md`](METABOLISME_20082026_la_variable_morte.md) — le chantier métabolique ouvert
- [`EXPANSION_17082026_le_frein_de_la_neurogenese.md`](EXPANSION_17082026_le_frein_de_la_neurogenese.md) — l'enquête antérieure sur la croissance
- `brains/23082026_v4132_mixage/` — la campagne (protocole, JSON, `.brain` et `.log`)
