# Plan v41.32 — La Table de Mixage, la Neurogenèse Dirigée et le Métabolisme Modulaire

> **Nature du document** : `ameliorations/` — idées **proposées, non validées**.
> Rien de ce qui suit n'est livré. Ce document dit **où nous en sommes**, **ce qui reste
> à faire**, et surtout **ce qui doit être mesuré avant d'être codé**.
>
> **Date d'ouverture** : 2026-08-23
> **Branche** : `feat/v41.30-constantes-fossiles` (2 commits derrière `master`)
> **Origine** : proposition utilisateur en trois volets (Maslow émergent, neurogenèse
> dirigée, métabolisme modulaire), confrontée au noyau réel le 23/08/2026.
>
> ### 🟢 ÉTAPE 1 — **LIVRÉE ET MESURÉE** (23/08/2026)
>
> La sonde de mixage est en place (`_sonder_mixage` / `_resumer_mixage`, télémétrie pure),
> le test **A/A donne δ = 0** (deux runs bit-identiques sur 40 nuits), et la mesure est
> tombée. **Elle réfute la prémisse de la proposition 4.1** — voir §1bis.
>
> **Le résultat en une ligne** : le problème n'est pas que l'eau soit *mal pondérée*, c'est
> que **5 termes sur 11 sont rigoureusement muets** (σ = 0,00000) et que `Bio` **domine
> déjà** le signal à **44 %**. Campagne : `brains/23082026_v4132_mixage/`.

---

## 0. Où nous en sommes — l'état au 23/08/2026

### Ce qui est établi (mesures directes, fiables)

| Fait | Chiffre | Source |
|---|---|---|
| Cursus complet, campagne appariée n=20 | niveau **4,10** vs **4,05** (`t=+0,37`) | `docs/etat_des_lieux/22082026_campagne_v41.31_cursus_complet.md` |
| Aucun cerveau au-delà du niveau 5 | **0 / 40** | idem |
| Couper C2 ne change rien | **0,0 pt sur 6 niveaux** (78 cellules) | v41.29 |
| C2 a grossi ×13, sa part a **baissé** | dilution **N² contre N** | anatomie 21/08 |
| Taille du cerveau ~ niveau atteint | **r = −0,172** (NS, signe négatif) | campagne 22/08 |
| Neurogenèse éteinte depuis | **882 jours** en moyenne | campagne 22/08 |
| Constantes nues restantes | **107** | anatomie 21/08 |
| Point d'assemblage de la récompense | **UN SEUL** — `noyau.py:9041` | anatomie 21/08 |

### Ce qui n'est PAS établi (à ne pas citer comme acquis)

- ⚠️ **Le « 0,017 contre 0,125 » de l'eau n'a jamais été mesuré sur les 9 termes.** Il
  vient d'une lecture d'empreintes de valence, pas d'une instrumentation de la
  récompense. Tant qu'il n'est pas confirmé, il ne justifie **aucune** refonte.
- ⚠️ La proposition « rendre de la masse à C2 » n'a **aucun appui de mesure** : les deux
  cerveaux les plus lourds ET les plus légers sont tous les deux au niveau 4.

---

## 1. Découverte du 23/08 — l'instrumentation est déjà à 60 %

**C'était l'objet de la question posée ce jour : comment extraire moyenne et variance
des 9 termes sans polluer le temps de calcul du run de diagnostic ?**

La réponse courte : **il n'y a presque rien à ajouter, et le coût est nul.**
Le noyau accumule déjà cinq des neuf termes, selon la discipline v29.1 (compteur remis à
zéro dans `_reinitialiser_buffers_journee`, accumulé dans `traiter_tick`, agrégé dans
`executer_nuit` en ligne console **et** clé `log_wandb`).

### Inventaire réel des 9 termes de `noyau.py:9041`

| # | Terme | Accumulateur journalier | Ligne | État |
|---|---|---|---|---|
| 1 | `recompense_env` | ❌ **absent** | — | à ajouter |
| 2 | `dopamine_curiosite` | ❌ **absent** | — | à ajouter |
| 3 | `micro_recompense` (jalons DoorKey) | ❌ **absent** | — | à ajouter |
| 4 | `micro_recompense_porte` | 🟡 partiel (`portes_franchies_jour` = **compte**, pas somme) | 8736 | à compléter |
| 5 | `micro_recompense_progres` | 🟡 partiel (`progres_personnel_jour` = **compte**) | 8744 | à compléter |
| 6 | `penalite_stagnation` | ✅ `penalite_stagnation_jour` | 8717 | **fait** |
| 7 | `sous_objectif_intrinseque` | 🟡 partiel (`sous_objectifs_curiosite_jour` = **compte**) | 8813 | à compléter |
| 8 | `r_bio` | ✅ `r_bio_jour` | 8840 | **fait** |
| 9 | `micro_recompense_vocale` | ✅ `score_vocal_jour` (proxy) | 8975 | **fait** |
| 10 | `cout_requete_c3` | ✅ conditionnel (C3 inactif ⇒ non loggé) | — | **fait** |
| 11 | `recompense_continue` (guidage) | ✅ `guidage_but_journee` | 8765 | **fait** |

⚠️ **Le piège des « partiels »** : `portes_franchies_jour`, `progres_personnel_jour` et
`sous_objectifs_curiosite_jour` comptent des **ÉVÉNEMENTS**, pas des **AMPLITUDES**. Ils
répondent à « combien de fois ? », jamais à « combien de récompense ? ». Or c'est
exactement la seconde question qui décide de la table de mixage. Un terme qui se déclenche
souvent pour trois fois rien et un terme rare mais massif ont le même compteur aujourd'hui.

### Ce qui manque vraiment

- **4 sommes** à créer (`recompense_env`, `dopamine_curiosite`, `micro_recompense`, et les
  amplitudes des 3 partiels).
- **La VARIANCE de chaque terme** — aucun terme ne l'a. Or la variance est le vrai
  discriminant : un terme constant, si gros soit-il, n'apprend **rien** au gradient ; c'est
  la dispersion qui porte le signal.

---

## 1bis. LA MESURE — ce que la sonde a trouvé (23/08/2026)

> **Nature** : mesure directe, intra-run, sur banc déterministe (δ_A/A = 0). Fiable au sens
> du tableau §4 de la règle de mesure. ⚠️ **Une seule graine** : les chiffres exacts sont
> propres à g11, mais le fait qualitatif (σ = 0 exact sur 5 termes) ne dépend pas d'elle.

### Protocole

Graine 11 · 40 jours · cursus complet (**pas** de `--env-force`) · deux répétitions.
`δ_A/A = 0` — les deux runs sont **bit-identiques**, lignes de mixage et niveaux compris.
Le banc est déterministe : un futur A/B pourra attribuer son effet.

### La table de mixage, mesurée

Triée par **écart-type décroissant** — c'est la dispersion qui porte le signal, jamais la
moyenne seule.

| TERME | MOYENNE | σ | **PART DU SIGNAL** |
|---|---|---|---|
| **Bio** | +0,00346 | **0,04357** | **44,0 %** |
| **Env** | +0,00136 | 0,02163 | 21,8 % |
| Stagnation | −0,01611 | 0,01359 | 13,7 % |
| Curiosite | +0,02091 | 0,00889 | 9,0 % |
| SousObjectif | +0,00171 | 0,00679 | 6,8 % |
| Progres | +0,00090 | 0,00462 | 4,7 % |
| Jalons | 0,00000 | **0,00000** | 0,0 % |
| Portes | 0,00000 | **0,00000** | 0,0 % |
| Vocal | 0,00000 | **0,00000** | 0,0 % |
| CoutC3 | 0,00000 | **0,00000** | 0,0 % |
| Guidage | 0,00000 | **0,00000** | 0,0 % |
| *TOTAL assemblé* | *+0,01223* | *0,05955* | — |

### Trois faits qui changent le plan

**(1) `Bio` domine DÉJÀ le signal — 44 %, soit le double d'`Env`.**
La prémisse de la proposition 4.1 (« le soulagement vital est écrasé par le bruit de fond
du sol nu ») est **fausse au niveau de la récompense**. La biologie n'est pas la voix
faible du mixage : c'est **la plus forte**. Un softmax qui lui donnerait encore plus de
volume amplifierait un terme déjà dominant.

**(2) 5 termes sur 11 sont rigoureusement MUETS.**
`Jalons`, `Portes`, `Vocal`, `CoutC3` et `Guidage` affichent `σ = 0,00000` **exact** sur
40 nuits × 400 ticks. Ils ne distinguent **aucune** action d'une autre : le gradient ne les
entend pas. Pondérer ces termes — dans un sens ou dans l'autre — ne peut **rien** changer.
⚠️ **Vérification faite** (§3 de la règle de mesure : un résultat trop propre est
suspect). L'agent est resté au **niveau 1/15** (`Empty-5x5`) sur les 40 jours : pas de
porte, pas de DoorKey, donc `Jalons`, `Portes` et `Guidage` (qui dérive du détecteur
DoorKey) **n'ont aucun support sur cette carte** ; pas de tuteur vocal ni de plug C3 pour
les deux autres. Les cinq sont donc des ablations **VIDES** (jamais activées), pas
**NÉGATIVES** (mesurées à zéro) — la distinction exacte qu'impose la règle de mesure.

🔴 **Ce que cela impose** : ces cinq termes ne pourront être jugés que sur une carte où ils
existent. La table de mixage ne peut donc **pas** être arbitrée sur ce seul run — il en
faudra un au **niveau 4** (là où la population plafonne), sans quoi on pondérerait cinq
termes dont on n'a jamais vu la dispersion. Les six termes vivants, eux, sont mesurés.

**(3) Le vrai déséquilibre est une MOYENNE, pas une dispersion.**
`Curiosite` a la **plus forte moyenne** de tous les termes (+0,0209, soit 6× celle de
`Bio`) pour la **4ᵉ** dispersion (0,0089). C'est la signature exacte du décalage d'origine :
un terme qui verse une prime quasi constante à chaque tick, donc n'apprend rien, mais
gonfle la valeur de tous les états. Symétriquement `Stagnation` (−0,0161) est une taxe
quasi constante. Les deux se compensent partiellement — et ce sont eux, pas l'eau, qui
constituent le « bruit de fond ».

### La vérification WATER (1.e) — le correctif v41.7 marche, mais l'eau reste plate

Lecture directe du `.brain` :

| TYPE | VALENCE | VÉCU |
|---|---|---|
| `goal` | **+0,65143** | 36 |
| `FOOD` | **+0,57497** | 67 |
| `sol` | +0,11984 | 884 |
| `WATER` | **+0,11673** | 60 |

- ✅ **Le correctif v41.7 fonctionne** : `FOOD` est passé de `+0.000 (×4004)` à **+0,575**,
  du même ordre que `goal`. Le canal n'est plus débranché.
- 🔴 **Mais `WATER` reste à +0,117 — la valence du SOL NU**, avec un vécu comparable à
  `FOOD` (60 contre 67). Ce n'est donc pas un problème d'échantillon.
- ⚠️ **C'est ici, et NULLE PART dans la table de mixage, que se trouve le « 0,017 contre
  0,125 » de l'intuition initiale.** Le problème est réel — mais il est **métabolique**,
  pas pondéral : boire ne produit pas de soulagement mesurable, alors que manger si.

**Conséquence directe** : l'écart `FOOD` / `WATER` renvoie au **métabolisme** (§6), pas à
la table de mixage.

### 1ter. L'EAU N'EST PAS CASSÉE — deuxième réfutation (23/08/2026)

> ⚠️ **Correction d'un chiffre qui a circulé** : l'eau vaut **`+0,117`**, pas `0,017`, et le
> sol nu vaut **`+0,120`**, pas `0,125`. L'eau n'est donc **pas** « sept fois sous le sol
> nu » : elle est **à son niveau exact**. Le point de comparaison qui compte est `FOOD`
> (**+0,575**), à vécu quasi identique (67 contre 60).

**La question n'est pas « pourquoi l'eau est-elle basse » mais « pourquoi manger soulage et
boire non ».** Mesuré, la réponse est complète — et elle innocente le canal.

#### Ni la formule ni le profil ne sont asymétriques

| | Satiété | Hydratation |
|---|---|---|
| Terme du déficit | `(1 − satiete)²` | `(1 − hydratation)²` |
| Profil de la ressource | `FOOD.satiete = 1.0` | `WATER.hydrique = 1.0` |

Rigoureusement symétriques. L'asymétrie est **ailleurs**.

#### Elle vient de l'ÉTAT DES JAUGES, mesuré sur 40 nuits

| Jauge | Minimum moyen | Fin de nuit moyenne | Nuits au plancher |
|---|---|---|---|
| **Satiété** | **0,0000** | 0,1065 | **40/40 (100 %)** |
| **Hydratation** | 0,5333 | 0,7255 | 3/40 (8 %) |

L'agent **n'a jamais soif**. Il est en famine permanente et correctement hydraté.

#### Le test quantitatif — l'écart est expliqué à 4,4 % près

`r_bio` est la **dérivée** du déficit. Une jauge déjà pleine ne peut donc rien soulager :

| | Soulagement possible par prise |
|---|---|
| `FOOD` sur une satiété à 0,106 | **0,3842** |
| `WATER` sur une hydratation à 0,726 | **0,0747** |

| Ratio | Valeur |
|---|---|
| Prédit par l'état des jauges | **5,14×** |
| Réellement appris (valences) | **4,93×** |
| **Écart** | **4,4 %** |

🟢 **Les valences ne sont pas cassées : elles mesurent EXACTEMENT le soulagement réel.**
Le canal `WATER` fonctionne, la loi des rendements décroissants fonctionne, et elle est
**physiologiquement juste** — boire sans soif ne fait aucun bien.

#### Ce que cela déplace

L'objet du chantier 1 change une seconde fois :

| | Avant | Après |
|---|---|---|
| Diagnostic | « boire ne procure aucun soulagement » | ✅ **faux** — boire soulage à proportion de la soif, qui est nulle |
| Le vrai défaut | l'eau | **la satiété est au plancher 40 nuits sur 40** |
| Cible | `valeur_hydrique`, profil nutritionnel | **la boucle énergie/digestion** — pourquoi la faim n'est-elle JAMAIS rassasiée ? |

⚠️ **Ne pas « réparer » l'eau.** Augmenter son rendement ou sa portion créerait une valence
artificielle sur une jauge déjà pleine — un chiffre posé pour corriger un symptôme correct.
C'est exactement le geste que le dogme interdit.

### 1quater. LA FAMINE — la chaîne causale complète (23/08/2026)

La question devient : **pourquoi la satiété est-elle au plancher 40 nuits sur 40 ?**
Mesurée bout à bout, la chaîne se referme — et ses deux extrémités étaient **déjà
documentées dans le code**, sans que personne les ait reliées.

#### Le bilan énergétique

⚠️ **Correction d'une erreur de ma part** : j'avais d'abord calculé un « déficit de 1,656
estomac/jour » en traitant `DEBIT_DIGESTIF_JOUR` comme un prélèvement fixe. C'est faux —
`conversion = min(debit_digestif, reserve_mobilisable)` : la digestion est un **PLAFOND**,
l'agent ne digère que ce qu'il a. Le bilan se fait donc en **énergie**, pas en estomac.

| Régime | Énergie fabriquée | Dépense | Solde |
|---|---|---|---|
| **3,00 repas/j** (la calibration d'origine) | 2,160 | 2,000 | **+0,160 → viable** |
| **1,68 repas/j** (mesuré) | 1,210 | 2,000 | **−0,790 → déficit permanent** |

**Seuil de viabilité : 2,78 repas/jour.** L'agent en fait **1,68 — soit 60 % du minimum
vital**, en permanence.

#### La constante fossile — la même faute que la v41.30

Le commentaire de `DEPENSE_ENERGIE_JOUR = 2.0` le dit lui-même :

> « balayage 1.0→3.0 **à 3 repas/jour** […] À 2.0 : jamais critique **avec 3 repas** »

**La constante est calibrée pour un régime que l'agent n'a jamais eu.** C'est exactement la
forme des trois constantes fossiles supprimées en v41.30 :

| Constante | Suppose | L'agent fait | Écart |
|---|---|---|---|
| `EPISODES_PAR_JOURNEE_REFERENCE = 4.0` | 4 épisodes/j | 1,55 | ×2,58 |
| `DEPENSE_ENERGIE_JOUR = 2.0` | **3 repas/j** | **1,68** | **×1,79** |

#### Mais la cause racine est en amont : le biotope sature

| Étape | Mesure |
|---|---|
| Le biotope **demande** | 7 food + 7 eau = **14 sources** |
| `Empty-5x5` **contient** | ~**8 cases libres** |
| Récolte réelle | 1,68 + 1,50 = **3,18 prises/jour** |
| Plafond annoncé par le code | ~**3,5/jour quelle que soit la densité** |

Le défaut `v41.2-fix3` est **déjà écrit dans `noyau.py`** : *« l'agent était quasi emmuré,
et la récolte plafonnait à ~3,5/jour QUELLE QUE SOIT la densité demandée […] C'est ce qui
rendait inopérants les trois calibrages successifs : ils réglaient un paramètre déjà
saturé. »*

🔴 **Conséquence de méthode** : toucher à `DEPENSE_ENERGIE_JOUR` serait le **quatrième**
calibrage inopérant. La récolte est bornée par la **géométrie de la carte**, pas par le
métabolisme. Un agent qui ne peut pas rencontrer 2,78 sources/jour ne les rencontrera pas
davantage parce qu'on a baissé sa dépense — on aura seulement rendu la famine indolore,
donc **invisible**, ce qui est pire.

#### Pourquoi l'eau va bien, elle

`RATIO_SOIF_SUR_FAIM = 10/30` : le besoin en eau est **trois fois plus faible** pour une
récolte quasi identique (1,50 contre 1,68). L'agent boit donc **1,2× ses besoins** et mange
**60 % des siens**. L'asymétrie FOOD/WATER n'est pas un bug : c'est la **conséquence
arithmétique** d'un biotope à parts égales sur deux axes aux besoins inégaux.

#### Ce qu'il reste à trancher (décision utilisateur)

| Piste | Nature | Risque |
|---|---|---|
| **(a)** Dériver la densité du **nombre de cases libres RÉELLES** de la carte courante, pas de la carte la plus vaste du cursus (`_CASES_LIBRES_CARTE_MAXIMALE = 41`) | ✅ dogmatique — la densité redevient une propriété du biotope **réel** | aucun chiffre posé ; mais change le monde sur toutes les cartes |
| **(b)** Répartir food/eau selon `RATIO_SOIF_SUR_FAIM` au lieu de parts égales | 🟡 dérivé, mais le code écarte explicitement cette option (défaut §8.6, v41.2) | relire l'argument avant de le rouvrir |
| **(c)** Baisser `DEPENSE_ENERGIE_JOUR` | 🔴 **à écarter** | 4ᵉ calibrage d'un paramètre saturé ; rend la famine indolore, donc invisible |

⚠️ **Aucune de ces pistes ne se code avant un A/B à n ≥ 20.** La récolte est le levier le
plus structurant du monde : la v41.25 a montré qu'un changement métabolique bon sur une
carte coûtait **−25 % de récolte** partout ailleurs.

### 1quinquies. 🔴 LE TÉMOIN RÉFUTE L'OPTION (a) — la densité n'est pas le goulot

> **Décision utilisateur du 23/08** : appliquer l'option (a) — dériver la densité des cases
> libres réelles. **Le témoin lancé avant de coder l'a réfutée.** Elle est **abandonnée**.

#### Ce que le témoin mesure

Un **marcheur aléatoire** sur la carte réelle (`Empty-5x5`, 3 graines, 400 ticks), avec la
même distribution d'actions que l'agent (uniforme sur les 7 actions réelles) :

| | FOOD/jour | WATER/jour |
|---|---|---|
| **Marcheur aléatoire** | **3,33** | 4,00 |
| **Agent entraîné** (mesuré, 40 nuits) | **1,68** | 1,50 |
| *Seuil de viabilité énergétique* | *2,78* | *—* |

🔴 **Le hasard pur récolte 2,0× plus de nourriture que l'agent entraîné — et le hasard, lui,
franchit le seuil de viabilité (3,33 > 2,78).**

#### Les trois conséquences

**(1) Le monde PEUT nourrir l'agent.** À densité inchangée, un comportement aléatoire suffit
à survivre. Le biotope n'est donc **pas** sous-doté.

**(2) L'agent récolte 50 % de ce qu'un hasard obtiendrait.** Son apprentissage le rend
**activement moins bon** à se nourrir qu'aucune politique du tout. C'est le fait à expliquer,
et aucune modification du monde ne le touchera.

**(3) L'option (a) aurait été le QUATRIÈME calibrage inopérant.** Le code l'annonce déjà
(v41.2-fix3) : *« trois calibrages successifs restés sans le moindre effet »*. Ils réglaient
un paramètre qui n'était pas le facteur limitant. Ajouter des sources à un agent qui
n'exploite pas celles qui existent aurait produit un quatrième résultat nul — et cette fois
après avoir modifié le monde sur **toutes** les cartes.

#### ⚠️ Correction d'une erreur de mon diagnostic précédent

J'avais écrit que « le biotope demande 14 sources sur une carte qui en tient 8 ». **C'est
faux** : le plafond `v41.2-fix3` fonctionne parfaitement. Mesuré sur les environnements
réels :

| Carte | Cases libres | FOOD placées | WATER placées |
|---|---|---|---|
| `Empty-5x5` | 6 | **1** | 1 |
| `Empty-6x6` | 11 | 2 | 2 |
| `Empty-8x8` | 24 | 6 | 5 |

Le « 7+7 » lu dans les logs est le **souhait**, jamais le placé. Le monde clampe déjà
correctement. Ma lecture confondait les deux.

#### Où va le chantier maintenant

La cause est **comportementale**, donc dans la boucle apprentissage — pas dans le monde.
Trois pistes, par ordre de ce que la mesure justifie :

| Piste | À mesurer d'abord |
|---|---|
| **L'agent ne cherche pas la nourriture** | la politique privilégie-t-elle `avancer` vers le but au détriment du fourrage ? Comparer la distribution d'actions agent vs. aléatoire |
| **`pickup` n'est pas appris** | v41.2-fix5 a rendu manger un ACTE volontaire. Quelle fraction des passages sur une source déclenche un `pickup` ? |
| **Le gradient ne récompense pas assez le fourrage** | `Bio` porte 44 % de la dispersion — mais est-elle concentrée sur les 1,68 prises, ou diluée sur les 400 ticks ? |

⚠️ Ces trois pistes se mesurent **sans modifier une ligne du monde**. C'est la leçon de ce
témoin : la prochaine action est encore une mesure.

### Ce que la mesure impose au plan

| Décision | Avant la mesure | Après |
|---|---|---|
| Table de mixage (4.1) | priorité 4, prémisse à vérifier | 🔴 **prémisse RÉFUTÉE** — l'objet change : ce n'est plus « amplifier le vital », c'est « retirer les décalages d'origine » |
| Écart FOOD/WATER | supposé mnésique (v41.7) | ✅ mnésique **résolu** ; le reliquat est **métabolique** → chantier 3 |
| Chantier métabolique (3) | priorité 3 | ⬆️ **priorité 2** — il porte maintenant deux dossiers |
| Neurogenèse dirigée (2) | priorité 2 | inchangée, toujours sans dépendance |

---

## 2. Le coût de calcul — le point qui inquiétait, et pourquoi il ne devrait pas

### La méthode : accumulateurs de Welford, jamais de listes

**Ne JAMAIS stocker les valeurs tick par tick.** Un run de 1500 jours × 400 ticks =
600 000 valeurs × 11 termes = 6,6 M de flottants Python. C'est de la mémoire et du GC, pour
un résultat qu'on peut obtenir en O(1) par tick et O(1) en mémoire.

Trois scalaires suffisent par terme : `n`, `somme`, `somme_carres`.

```python
# Dans _reinitialiser_buffers_journee — 3 scalaires par terme, remis à zéro comme
# TOUT buffer journalier (piège `score_vocal_jour` v27.0, rappelé en tête de la méthode)
self.mix_n = 0
self.mix_somme = {}        # nom_terme -> float
self.mix_somme_carres = {} # nom_terme -> float

# Dans traiter_tick, juste APRÈS l'assemblage l. 9041 — un seul point, comme
# l'assemblage lui-même
def _sonder_mixage(etat, **termes):
    etat.mix_n += 1
    for nom, v in termes.items():
        v = float(v)
        etat.mix_somme[nom] = etat.mix_somme.get(nom, 0.0) + v
        etat.mix_somme_carres[nom] = etat.mix_somme_carres.get(nom, 0.0) + v * v

# Dans executer_nuit — moyenne ET écart-type, en O(nb_termes)
for nom, s in etat.mix_somme.items():
    moy = s / max(1, etat.mix_n)
    var = etat.mix_somme_carres[nom] / max(1, etat.mix_n) - moy * moy
    log_wandb[f"Mix_Moy_{nom}"] = moy
    log_wandb[f"Mix_Ecart_{nom}"] = math.sqrt(max(0.0, var))
```

### Le coût réel, chiffré

| Poste | Coût |
|---|---|
| Par tick | **11 additions + 11 multiplications** sur des `float` Python |
| Comparé à un tick | un `forward` réseau + un rollout C2 sur 7 actions × horizon |
| Ordre de grandeur | **< 0,01 %** du temps de tick |
| Mémoire | **33 scalaires**, constants — aucune liste, aucune croissance |
| Par nuit | ~22 divisions + 11 `sqrt` |

**Le vrai coût du run de diagnostic n'est pas la sonde : c'est le run.** Un run de
1500 jours coûte ~1 h ; la sonde y ajoute quelques secondes. La question du coût de calcul
est donc **résolue par la méthode**, pas par un compromis sur la précision.

### Trois pièges à éviter (chacun a déjà coûté un cycle au projet)

1. **Ne pas créer un compteur par `getattr(etat, "...", 0)` sans l'ajouter à
   `_reinitialiser_buffers_journee`** — c'est le bug `score_vocal_jour` v27.0, où « la
   moyenne du jour » cumulait depuis la naissance du cerveau.
2. **Rendre les clés conditionnelles** quand la mécanique peut être inactive (voir les
   blocs `Sens_*` et C3) plutôt que de logger des zéros trompeurs. Un terme jamais actif
   doit être **absent**, pas à zéro — c'est la distinction ablation *vide* / ablation
   *négative* de la règle de mesure.
3. **Sonder APRÈS le guidage dégressif** (`_g`, l. 8760-8765), jamais avant : on veut
   mesurer l'aide **réellement versée**, pas l'aide brute. Le noyau prend déjà
   explicitement cette précaution pour `guidage_but_journee`.

### Variante « profil fin » — seulement si le résumé ne tranche pas

Si moyenne + écart-type ne suffisent pas à décider, ajouter un **histogramme à bacs
fixes** (ex. 12 bacs log-espacés par terme) : toujours O(1) par tick, toujours borné en
mémoire, et il révèle la forme de la distribution (un terme bimodal se voit, un
écart-type le cache). **Ne pas le faire d'emblée** — commencer par le résumé, c'est la
doctrine v30.1 : instrumenter, mesurer, et seulement ensuite raffiner.

---

## 3. Le canal WATER — l'audit est déjà écrit dans le code

⚠️ **Correction d'une prémisse de ma part.** J'annonçais l'audit du canal WATER comme une
tâche à faire. **Elle a déjà été faite en v41.7** et le correctif est en place
(`noyau.py:8925-8963`).

Le bug historique, documenté dans le code lui-même :

```
↑ 'goal' +0.515 (×1037)      ← appris, valence positive
↓ 'FOOD' +0.000 (×4004)      ← QUATRE MILLE repas, valence RIGOUREUSEMENT NULLE
```

`enregistrer_evenement` était appelé pour `"FOOD"`/`"WATER"` **sans `intensite`**, donc
avec son défaut de `0.0`. L'abstraction par récurrence (v36.0) et l'empreinte de type
(v39.0) **moyennaient des zéros** sur les ressources. Corrigé : l'intensité est désormais
le `soulagement` réel (`deficit_avant − deficit_apres`), mesuré et non posé.

**Ce qui reste à faire n'est donc pas un audit mais une VÉRIFICATION post-correctif** :

- [ ] Lire `Empreinte_Valence_*` sur un `.brain` récent et confirmer que `'WATER'` et
      `'FOOD'` ont une valence **non nulle**.
- [ ] Vérifier qu'elle est **positive** et d'un ordre comparable à `'goal'`.
- [ ] Si elle est encore quasi nulle : c'est que le soulagement lui-même est petit, et le
      problème est **métabolique** (§6), pas mnésique.

🔴 **Blocage matériel** : les 40 `.brain` de la campagne du 22/08 ont été **détruits** (voir
`brains/old_V4131_cursus_complet/LISEZ_MOI.md`). Cette vérification exige donc un **nouveau
run**, ce qui la rend indissociable de l'étape 1. Les deux se font dans le même run.

---

## 4. Verdict sur les trois propositions

### 4.1 — Table de Mixage / Maslow émergent : 🟡 **principe retenu, formule à revoir**

Le diagnostic est juste (9 termes à poids 1 = le dernier gros coefficient posé), la
biologie est juste (la faim coupe le son de la curiosité). **Trois défauts** dans le
pseudo-code proposé :

| Défaut | Conséquence | Correctif |
|---|---|---|
| **(a) `TEMPERATURE` est une constante posée** | le softmax ne supprime pas le coefficient magique, il le **concentre** : `T→0` redonne la moyenne uniforme actuelle, `T` grand éteint 8 termes sur 9. Toute la dynamique tient dans ce seul nombre, **invisible**. | dériver `T` du vécu — candidat : `reference_choc_dopamine` et son cliquet v41.1-fix1, qui porte déjà « l'échelle de ce que **cet** agent juge remarquable » |
| **(b) diviser par `poids_total` détruit l'échelle absolue** | une moyenne pondérée est **bornée par son plus grand terme**. Le meilleur tick d'une vie (eau + but + curiosité **simultanés**) serait plafonné à l'amplitude d'**un seul** canal. Le pic dopaminergique s'aplatit — or il alimente `reference_choc_dopamine`, la distillation sélective v41.1 et la valence v39.0. On ne corrigerait pas la valence de l'eau, on la **plafonnerait**. | pondérer puis **remultiplier par la somme des poids bruts** : on garde la réallocation d'attention, on garde qu'un tick où tout va bien vaut plus qu'un tick où une seule chose va bien |
| **(c) la prémisse n'est pas mesurée** | si `r_bio` sur l'eau vaut réellement 0,017 parce que le soulagement est mal converti, le softmax amplifiera 0,017 — ce qui reste petit. **On aurait refondu la table de mixage pour amplifier un signal absent** (précédent v41.7 : 4004 repas à valence nulle). | **étape 1 d'abord** |

### 4.2 — Neurogenèse Dirigée : ✅ **retenue, la meilleure des trois**

Seule proposition qui attaque une cause **géométrique** — donc sans solution par constante.
Quand `dim_bus` passe de 16 à 154, `bus→bus` croît en N², `bus→1` en N : C2 a grossi ×13 et
sa part a **baissé quand même**.

Et elle est **dogmatiquement irréprochable** : `budget × stress_i / Σ stress` ne contient
aucun coefficient, la répartition sort intégralement du gradient reçu. Même famille que le
rêve adaptatif ou la porosité nocturne — une proportion émergente, pas un partage décidé.

**Trois contraintes d'implémentation** que le pseudo-code ne voit pas :

| Contrainte | Détail |
|---|---|
| **`segments_in` doit rester exact** | `assert total_ancien == self.in_features` (CLAUDE.md). Si les couches grandissent de montants **différents**, la concaténation de `forward()`/`penser()` se désaligne **silencieusement**. C'est le vrai travail, et le seul endroit qui peut casser sans bruit. |
| **Lire le stress sur la myéline rafraîchie** | la v41.0-fix a établi que la myéline doit être relue **en tête de `cycle_sommeil`** — sinon elle ignore tout ce que la couche vient d'apprendre (mesuré : `0.000000` exact sur `tete_motrice` après 600 jours). Réutiliser l'existant plutôt qu'ajouter un capteur. |
| **Toute couche doit être dans les 3 endroits** | `__init__`, `cycle_sommeil_global()`, `declencher_neurogenese()`. En oublier un casse silencieusement le sommeil **ou** la neurogenèse pour cette couche. |

### 🔴 4.2bis — LA NEUROGENÈSE DIRIGÉE NE PEUT PAS CORRIGER LA DILUTION (23/08/2026)

> **Décision utilisateur du 23/08** : coder la répartition de `agrandir()` selon le stress
> de la myéline. **Lecture du code faite avant d'écrire : la mécanique est structurellement
> impossible sous cette forme, et son objectif est hors de portée.** Deux résultats.

#### (1) Un `a` différent par couche est IMPOSSIBLE — le bus est partagé

Dans `declencher_neurogenese`, `a` apparaît **deux fois** par couche du tronc :

```python
self.analyseur.agrandir([(d, a)], a)
#                        ^^^^^^   ^
#                        entrée   SORTIE
```

La **sortie** de `analyseur` **est** l'entrée de `integrateur_bio`, qui alimente
`tete_motrice`, etc. Huit couches sont chaînées sur le **même** bus de largeur `dim_bus` :

| Couche | Sortie |
|---|---|
| `porte_visuelle`, `hippocampe`, `fusion_memoire`, `analyseur`, `integrateur_bio`, `generateur_attente`, `porte_auditive`, `generateur_attente_audio` | **`+a` — contrainte** |
| `tete_motrice`, `cortex_prefrontal`, `tete_vocale`, `tete_requete` | fixe (8, 1, 8, `DIM_ROUTAGE_C3`) |

Donner 8 dims à `analyseur` et 24 à `integrateur_bio` produirait un `RuntimeError` au
premier `forward` : le tenseur qui sort de l'un ne rentre plus dans l'autre. **`dim_bus`
n'est pas un budget répartissable, c'est une largeur commune.**

#### (2) Même à 100 % du budget, C2 resterait dilué — mesuré

Répartition réelle d'un `.brain` à `dim_bus = 70` (384 808 paramètres) :

| COUCHE | PARAMS | PART |
|---|---|---|
| `porte_visuelle` | 61 742 | 16,05 % |
| `hippocampe` | 58 802 | 15,28 % |
| `fusion_memoire` | 58 802 | 15,28 % |
| `porte_auditive` | 54 602 | 14,19 % |
| `integrateur_bio` | 46 622 | 12,12 % |
| … | | |
| **`cortex_prefrontal` (C2)** | **422** | **0,110 %** |

**La cause n'est pas dans `agrandir()`** : `cortex_prefrontal` a **une seule sortie** (une
valeur scalaire). Il croît donc en **N**, quoi qu'on lui donne, pendant que toute matrice
carrée croît en **N²** :

| Ajout | C2 gagne | `hippocampe` gagne | Rapport |
|---|---|---|---|
| 8 dims | 48 | 14 208 | **×296** |
| 16 dims | 96 | 29 952 | **×312** |
| 32 dims | 192 | 66 048 | **×344** |

🔴 **Le budget de neurogenèse n'est pas le levier.** Le problème n'est pas *combien de
dimensions C2 reçoit en entrée*, c'est qu'il **n'a qu'une sortie**. Une répartition
proportionnelle au stress aurait déplacé des miettes en laissant le rapport intact — et
elle aurait donné l'illusion d'avoir traité la dilution.

#### Ce qui resterait possible (non tranché, à ne pas coder sans décision)

| Piste | Nature | Réserve |
|---|---|---|
| **Élargir la SORTIE de C2** (une tête de valeur multi-dimensionnelle, agrégée ensuite) | change l'architecture, pas le budget | ⚠️ modifie la sémantique de la valeur ; greffe `persistance` obligatoire ; aucun appui de mesure (r = −0,172) |
| **Donner à C2 une couche cachée** (`bus → h → 1` au lieu de `bus → 1`) | croissance en N·h, plus en N | ⚠️ nouvelle couche ⇒ à ajouter dans `__init__`, `cycle_sommeil_global()` **et** `declencher_neurogenese()` |
| **Ne rien faire** | — | la corrélation taille~niveau est **négative** ; rien ne dit qu'un C2 plus gros aiderait |

⚠️ **Réserve sur l'ambition, pas sur le mécanisme** : la neurogenèse est **éteinte depuis
882 jours** en moyenne. Une croissance mieux répartie ne s'applique qu'aux premières
centaines de jours — elle réparerait la dilution **future**, jamais celle déjà subie. Ne
pas en attendre le déblocage du niveau 5 sur les cerveaux actuels.

### 4.3 — Métabolisme Modulaire : 🔴 **bonne biologie, mauvais levier — reporté**

La biologie est exacte (le cortex visuel baisse sa consommation dans le noir). Deux
objections, une de dogme et une de chiffre.

**(a) `if norme(signal) > 0.01` est un seuil en dur dans le chemin cognitif.** Le projet
l'a refusé **quatre fois** : v28 (seuil d'incertitude pour appeler C3), v29 (court-circuit
C1→C2), v30 (boucle d'attention Exo-Sens), v41.11 (malus conditionnel de mort). *Une
sigmoïde reste un `if` avec une pente.* Remède immédiat qui **améliore** la proposition :
facturer **proportionnellement à la norme d'activation**, continûment. Le silence coûte
alors zéro sans qu'on ait eu à décider ce qu'est le silence.

**(b) Le chiffre ne suit pas.** `DEBIT_DIGESTIF_JOUR = DEPENSE_ENERGIE_JOUR × 1,5` — la
dépense est une **constante globale**, indexée ni sur `dim_bus` ni sur le nombre d'organes.
**Éteindre l'hémisphère audio ne rendrait aucune calorie**, parce qu'il n'en consomme
aucune aujourd'hui. Les 24 % de paramètres audio coûtent du **calcul**, pas de l'**énergie
simulée**.

La famine à 80 % vient du chantier déjà ouvert : `taux_satiete` est une **variable morte**
(rien ne la soustrait depuis la v41.2) et la digestion est indexée sur une dépense
forfaitaire au lieu de l'effort réel. **La proposition 4.3 devient excellente une fois §6
faite** — mais dans cet ordre, sinon on branche un économiseur d'énergie sur un compteur
qui ne tourne pas.

---

## 🔴 CHANTIER 0 — LE DIAGNOSTIC RACINE (23/08/2026, en tête de tout le reste)

> **Ce chantier précède les cinq autres.** Il ne les remplace pas : il conditionne leur
> utilité. Ouvert après neuf réfutations dans la même journée, dont la dernière a renversé
> le diagnostic.

### Le constat

L'agent n'est **ni apathique ni aléatoire** — c'est ce que l'entropie a établi :

| | Écart au maximum `ln(7)` |
|---|---|
| Cerveau réellement éteint (v34.0-fix1, août) | **0,00004** |
| Agent mesuré le 23/08 | **0,34961** |

Il est **~8700× plus décidé** qu'un cerveau aplati, et son entropie **baisse** (1,7695 →
1,7034). Il a donc des certitudes.

Mais sa réponse est **la même face à un mur et face à une pomme** — distance des politiques
**0,194** contre un bruit d'échantillonnage à **0,213** (p95).

**Ses certitudes ne dépendent pas de ce qu'il perçoit.**

### L'implication — pourquoi ce chantier passe devant

| Chantier | Présupposait |
|---|---|
| Famine / métabolisme | que le corps atteint la décision |
| Table de mixage | que la récompense façonne une politique **conditionnelle** |
| Neurogenèse | que plus de capacité serait exploitée |

Si l'état n'entre pas dans la décision, **les trois réparent des signaux qui viendront
s'écraser sur la même porte close.** Aucun n'est faux ; tous sont prématurés.

### L'action — mesurer la PERMÉABILITÉ du réseau

Trouver **à quel étage** l'état cesse d'influencer la décision. Télémétrie pure, hors
entraînement, sur les `.brain` existants.

**A. Deux états contrastés**
- *Survie* : face à une ressource, satiété 0,0 · hydratation 0,0 · énergie au plancher
- *Confort* : face à un mur, satiété 1,0 · hydratation 1,0 · énergie au maximum

⚠️ **Forger les jauges à la main produit un état que l'agent n'a JAMAIS vécu** — un point
hors distribution, où la réponse du réseau ne dit rien de son comportement réel. Le protocole
doit donc mesurer **les deux** : états forgés (contraste maximal, borne supérieure de la
sensibilité) **et** états réellement capturés en jeu (ce qui compte).

**B. Remonter la chaîne, étage par étage**

| Étage | Ce qu'on compare |
|---|---|
| `bus_latent` | les portes sensorielles envoient-elles des signaux distincts ? |
| `pensee_bio` | la fusion bus + corps produit-elle des vecteurs distincts ? |
| logits `tete_motrice` (C1) | la décision change-t-elle ? |
| valeur `cortex_prefrontal` (C2) | l'évaluation d'état change-t-elle ? |

**C. Le diagnostic**

| Signature | Verdict |
|---|---|
| `bus_latent` distinct, logits identiques | **effondrement de représentation** dans les couches profondes |
| `bus_latent` déjà identique | les **portes sensorielles** sont éteintes (cf. extinction v34.0) |
| tout distinct | la politique lit l'état — la non-discrimination vient d'ailleurs |

### L'hypothèse de travail

Pendant des centaines de nuits où `Env` était introuvable (0,1 % de la dispersion au
niveau 4), **ignorer le monde a pu devenir la stratégie la plus économe** — l'érosion
nocturne ne préserve que ce que le gradient myélinise, et un capteur qui ne prédit aucune
récompense ne myélinise rien. C'est le mécanisme exact de l'extinction synaptique v34.0,
mais appliqué à la **conditionnalité** plutôt qu'à l'amplitude.

⚠️ **Hypothèse, pas conclusion.** Elle se teste par le protocole ci-dessus.

---

## 5. Ce qu'il reste à faire — l'ordre et le pourquoi

| # | Action | Pourquoi à ce rang | Bloque | Coût |
|---|---|---|---|---|
| **0** | 🔴 **PERMÉABILITÉ DU RÉSEAU** (Chantier 0) | conditionne l'utilité des cinq autres : si l'état n'entre pas dans la décision, réparer les signaux ne sert à rien | **tous** | 1 nuit |
| **1** | **Sonde de mixage** (§2) + vérification WATER (§3) | décide si 4.1 est un correctif ou un pansement. Mesure **avant** refonte — doctrine v30.1. | 4.1 | 1 nuit |
| **2** | **Neurogenèse dirigée** (§4.2) | seule des trois **sans dépendance**, dogmatiquement propre, cause géométrique | — | ~1 j + campagne |
| **3** | **Dépense énergétique réelle** (§6) | débloque le métabolisme **et** rend 4.3 mesurable | 4.3 | chantier v41.32 |
| **4** | **Table de mixage** (§4.1) | une fois connus les 9 chiffres, et avec `T` dérivé | — | après (1) |
| **5** | Métabolisme modulaire (§4.3) | dépend de (3) | — | après (3) |

### État d'avancement

- [x] **1.a** — 4 sommes manquantes + amplitudes des 3 partiels (§1)
- [x] **1.b** — variance par Welford, 3 scalaires/terme (§2)
- [x] **1.c** — ligne console + clés `log_wandb` conditionnelles (règle v29.1)
- [x] **1.d** — run de diagnostic **+ test A/A (δ = 0)**, 11 couples lus
- [x] **1.e** — `FOOD` **réparé** (+0,575) · `WATER` **plat** (+0,117) → renvoyé au §6
- [ ] **2.a** — mesure du stress par couche (lecture seule, aucun effet)
- [ ] **2.b** — répartition proportionnelle dans `declencher_neurogenese()`
- [ ] **2.c** — `segments_in` exact sous croissance non uniforme
- [ ] **2.d** — campagne A/B, **un seul bras**, n ≥ 20
- [ ] **3** ⬆️ **PRIORITÉ 2** — chantier métabolique (porte aussi l'écart FOOD/WATER) (voir `METABOLISME_20082026_la_variable_morte.md`)
- [ ] **4** 🔄 **OBJET CHANGÉ** — non plus amplifier le vital (déjà à 44 %), mais retirer les décalages d'origine (`Curiosite` +0,0209 pour σ=0,0089 ; `Stagnation` −0,0161)
- [ ] **5** — métabolisme modulaire, facturation continue

---

## 6. Le chantier métabolique en attente (rappel)

Ouvert le 20/08, non clos — voir
`docs/recherche/METABOLISME_20082026_la_variable_morte.md`.

- `taux_satiete` est **morte** : rien ne la soustrait depuis que la v41.2 l'a remplacée par
  la digestion. Le vrai régulateur est `DEBIT_DIGESTIF_JOUR`, qui impose **3,333
  estomacs/jour identiques dans les deux bras** d'une ablation censée les distinguer.
- Le commentaire de `noyau.py:2991` est **FAUX sur le POURQUOI** (« `taux_satiete` prélève
  déjà à chaque tick ») — mais ✅ le basal **est** bien facturé, par
  `METABOLISME_BASAL_PART` : un agent totalement inactif à l'estomac vide perd
  **0,325000** en 100 ticks, exactement le basal. C'est le **texte** à réparer, pas le
  comportement.
- Indexer la digestion sur la dépense **réelle** est ce qui rend §4.3 mesurable.

---

## 7. Les garde-fous qui s'appliquent aux cinq étapes

Non négociables — chacun a déjà coûté un cycle au projet.

1. **A/A avant tout A/B.** Deux runs identiques, même graine, même code. S'ils diffèrent
   autant que A et B, **le test ne mesure rien** (défaut de reproductibilité v41.9).
2. **Jamais de conclusion sous 20 graines.** À n=6, l'intervalle est de ±30 points : on ne
   détecte **rien**. Toujours donner l'intervalle **à côté** du taux, jamais le taux seul.
3. **Jamais de `t` sur un run en cours.** La maîtrise lue à n=5 valait **+4,95** ; à n=20,
   **+1,09** — divisée par 4,5. Un `t` sur un run inachevé choisit implicitement sa fenêtre.
4. **Un bras d'ablation par mécanique**, jamais deux ensemble (leçon v41.30 : patience et
   rythme couplés ⇒ ablation **confondue**).
5. **Un résultat trop propre est suspect.** Une valence à `0.000` exact, un delta `+0,0`
   partout : c'est presque toujours un canal débranché, pas une découverte (v41.4, v41.7).
6. **Correction de Bonferroni** dès qu'on teste plusieurs métriques : 3 métriques ⇒ seuil
   `t ≈ 2,86`. La satiété à `+2,17` **ne passe pas** (p ≈ 0,13).
7. **Une campagne écrit dans `brains/<nom>/`, jamais dans un scratchpad** — dossier créé
   **avant** le lancement. Règle née de la perte des 40 `.brain` du 22/08.
8. **Instrumenter dans le même commit que la mécanique** (règle v29.1) : compteur remis à
   zéro dans `_reinitialiser_buffers_journee`, accumulé dans `traiter_tick`, agrégé dans
   `executer_nuit` — ligne console **et** clé `log_wandb`.

---

## 8. Ce qui reste ouvert et attend une décision utilisateur

| Question | Mon avis | Tranché ? |
|---|---|---|
| Élargir `cortex_prefrontal` d'emblée ? | **non** — la corrélation taille~niveau est **négative** (r = −0,17) ; grossir n'a jamais aidé | ❌ |
| Hémisphère audio : 24 % des paramètres pour une faculté non exercée | ni le supprimer ni le garder par défaut — §4.2 le fera **s'atrophier tout seul** si le monde reste muet | ❌ **arbitrage utilisateur** |
| Sort des 20 branches locales déjà mergées | supprimables sans perte (toutes sur `origin`), mais CLAUDE.md dit « conservées pour l'historique » | ❌ |
| Les 107 constantes nues restantes | traiter par vagues thématiques, jamais en masse | ❌ |

---

## 9. Documents liés

- `docs/etat_des_lieux/21082026_anatomie_du_noyau.md` — les 225 constantes, le point
  d'assemblage unique
- `docs/etat_des_lieux/22082026_campagne_v41.31_cursus_complet.md` — la falsification n=20
- `docs/recherche/METABOLISME_20082026_la_variable_morte.md` — le chantier §6
- `docs/ameliorations/EPISODES_REFERENCE_20082026_la_derniere_constante_posee.md`
- `brains/old_V4131_cursus_complet/LISEZ_MOI.md` — la campagne perdue et sa règle
