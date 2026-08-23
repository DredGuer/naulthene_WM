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

**Sept propositions, sept réfutations, zéro ligne de correctif écrite.** Le coût total :
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
