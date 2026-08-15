# v41.2 — L'énergie comme modulateur global (seuil non linéaire)

> **Statut : EN COURS D'IMPLÉMENTATION.** Complète
> [CHANTIER_v41.2_metabolisme_deux_etages.md](CHANTIER_v41.2_metabolisme_deux_etages.md)
> (les deux étages, la mort par insolvabilité, les bornes dérivables).
>
> Date : 15 août 2026 · Décision utilisateur : *« L'énergie a un genre de seuil non
> linéaire qui rentre dans tout (prise de décision C1 & C2, `calculer_deficit()`, etc.) »*

---

## 1. Le principe : un seul modulateur, pas dix branchements

L'énergie ne doit pas être « ajoutée » à chaque mécanisme un par un — ce serait dix
couplages à maintenir, et dix occasions de coder un `if`. Elle passe par **une seule
grandeur dérivée**, la **vigueur**, que tous les consommateurs lisent :

```
vigueur = énergie^κ  avec κ = exposant de non-linéarité
```

| Régime | `vigueur` | Effet vécu |
|---|---|---|
| Énergie haute (≈ 1) | ≈ 1 | tout fonctionne nominalement |
| Énergie moyenne (0,5) | **0,25** (κ=2) | déjà nettement diminué |
| Énergie basse (0,2) | **0,04** | effondrement — l'agent ne peut plus que survivre |

**C'est le « seuil non linéaire » demandé, sans seuil.** Il n'existe aucun `if énergie <
X`. La chute est continue mais **accélérante** : c'est une courbe, pas une marche. La
différence est capitale — une marche est un `if` déguisé, une puissance est un régime.

> Même discipline que `echelle_myeline` (v37.0) : l'échelle est **relative et dérivée**,
> jamais un seuil posé a priori.

---

## 2. Où la vigueur entre — les cinq consommateurs

### 2.1 `calculer_deficit()` — le corps

L'énergie devient un terme du déficit, **au même titre** que les autres jauges :

```
deficit = (1−satiété)² + (1−hydratation)² + (1−stimulation)² + (1−énergie)²
```

⚠️ **Risque de double comptage** (signalé en §10.3 du chantier parent, et en §7.2 de
CONCEPTION_v34) : l'effort est **déjà** facturé en dépense d'énergie. Si l'énergie entre
dans le déficit, elle y entre **une seule fois**, comme un état — pas comme un flux.

**Tranché** : l'énergie entre dans le déficit comme **état** (le carré de son manque),
et `r_bio` reste la **dérivée** de ce déficit. Dépenser de l'énergie fait donc baisser
`r_bio` — ce qui est exactement le signal voulu — mais l'effort n'est **pas** soustrait
une seconde fois ailleurs.

### 2.2 C1 — le réflexe

La vigueur module le **volume** de la voix réflexe, jamais son opinion :

```
voix_c1 = logits_instinct × gain_c1 × vigueur
```

⚠️ **Invariant v37.0 respecté** : le gain de C1 est un facteur **scalaire**. Les rapports
entre les 7 logits restent rigoureusement intacts. Un agent épuisé n'a pas d'autres
préférences — il a des préférences **moins affirmées**. C'est la définition d'un réflexe
qui faiblit.

### 2.3 C2 — la délibération

C'est ici que la non-linéarité prend tout son sens :

```
force_planification_effective = force_planification × vigueur
```

**Planifier coûte cher.** Un organisme épuisé cesse de simuler l'avenir bien avant de
cesser de marcher. Avec κ = 2, une énergie à 0,5 laisse C1 à 50 % mais C2 à **25 %** :
la délibération s'éteint **plus vite que le réflexe**, ce qui est biologiquement juste et
produit gratuitement une hiérarchie de survie.

> ⚠️ Ceci n'est **pas** le « court-circuit C1→C2 » refusé en v29.0, ni le déclenchement
> sur seuil d'incertitude refusé trois fois. C2 est **toujours sollicité à chaque tick**,
> sans aucune condition. Seul son **poids dans la fusion** varie continûment avec l'état
> du corps. Il n'y a pas de branche : il y a un facteur.

### 2.4 Le coût cognitif — la boucle qui se referme

L'effort cognitif est déjà facturé (20 % de `calculer_effort_metabolique`). Comme il
dépend de `force_planification_effective`, un agent épuisé **planifie moins, donc dépense
moins**. La boucle est stabilisatrice, sans aucune règle : l'épuisement protège de
l'épuisement.

### 2.5 La plasticité nocturne

Un corps épuisé consolide mal. La vigueur du jour module l'apprentissage nocturne — un
agent qui a passé sa journée à l'agonie apprend moins de cette journée.

---

## 3. Ce qui est CONSTANTE (borne) et ce qui est VARIABLE (dérivé)

| | Rôle |
|---|---|
| **CONSTANTES — bornes** | `KAPPA_VIGUEUR_MIN/MAX` (bornes de l'exposant), `VIGUEUR_PLANCHER` (un corps n'est jamais à zéro absolu tant qu'il vit), `ENERGIE_MIN/MAX` |
| **VARIABLES — dérivées** | `vigueur` ← énergie · `κ effectif` ← dérive adaptative · `force_planification_effective` ← force × vigueur · déficit ← état des 4 jauges |

**κ lui-même dérive** (§5 du chantier parent) : un métabolisme peut apprendre à mieux
résister à la baisse d'énergie — κ diminue vers 1 (dégradation plus linéaire, plus
douce) — mais s'en écarter coûte exponentiellement cher. La norme d'espèce est κ = 2 ;
les bornes sont `[KAPPA_MIN, KAPPA_MAX]`, et le rappel élastique interdit d'y camper.

---

## 4. `VIGUEUR_PLANCHER` — pourquoi il est indispensable

Sans plancher, `vigueur → 0` annule **les deux** voix : C1 × 0 et C2 × 0 produisent des
logits **tous nuls**, donc une politique uniforme, donc une action **aléatoire**. Un agent
mourant se mettrait à jouer à pile ou face au lieu de lutter — l'inverse exact du
comportement voulu.

Le plancher garantit qu'un agent affaibli reste **cohérent** : diminué, jamais aléatoire.
C'est le même raisonnement que `PLANCHER_POIDS_VITAL` en v34.0-fix1 — et la même leçon :
*« ne jamais le retirer parce qu'il ne sert jamais »*, on a mesuré que 6 couches sur 11 y
sont collées.

---

## 5. Ce qu'on attend, et comment on saura que c'est faux

| Attendu | Falsifié si… |
|---|---|
| `vigueur` varie sur la journée (écart-type > 0,05) | reste constante → l'énergie ne bouge pas, le couplage est décoratif |
| C2 s'éteint **avant** C1 quand l'énergie chute | les deux tombent ensemble → κ mal calibré |
| L'agent alterne action / repos | jamais de repos, ou repos permanent |
| `r_bio` retrouve de la variance | écart-type ≈ 0 → le défaut n'était pas là |

⚠️ **Ce qui ne serait PAS une preuve** : un déblocage de cursus sur 1 à 3 graines. La
loterie natale (campagne v41) a montré qu'une graine peut débloquer seule. **≥ 10 graines
ou rien.**

---

*Document créé le 15 août 2026 avant implémentation. Les mesures d'impact sont consignées
au §6 à mesure des runs.*

---

## 6. Mesures d'impact — résultats des runs

### 6.1 ✅ L'invariant d'échelle est vérifié (le test qui conditionne tout le reste)

Sans lui, aucun run de réglage à 400 ticks ne dirait quoi que ce soit du run cible à 3600.

| ticks/journée | E_moy | E_min | E_écart-type | % basse énergie | S_moy |
|---|---|---|---|---|---|
| **400** | 0,929 | 0,786 | 0,070 | 0,0 % | 0,301 |
| **3600** | 0,928 | 0,785 | 0,070 | 0,0 % | 0,304 |

**Écart < 1 %.** Le vécu biologique est bien invariant : « diviser par 9 » divise le coût
de calcul, pas la mécanique.

### 6.2 ✅ Le seuil non linéaire produit la hiérarchie de survie voulue

`vigueur = énergie ** κ`, κ = 2 :

| énergie | vigueur | voix C1 | voix C2 | ratio C2/C1 |
|---|---|---|---|---|
| 1,00 | 1,000 | 1,000 | 1,000 | 1,000 |
| 0,80 | 0,640 | 0,640 | 0,410 | 0,640 |
| **0,50** | **0,250** | **0,250** | **0,062** | **0,250** |
| 0,30 | 0,150 | 0,150 | 0,022 | 0,150 |
| 0,00 | **0,150** ← plancher | 0,150 | 0,022 | 0,150 |

**À mi-énergie, C1 garde 25 % de sa voix et C2 seulement 6 %.** La délibération s'éteint
`vigueur²` quand le réflexe s'éteint en `vigueur` — un organisme épuisé cesse de simuler
l'avenir bien avant de cesser de marcher. Aucun `if` n'exprime cela.

Le plancher tient : à énergie nulle, la vigueur reste à 0,150. L'agent est **diminué,
jamais aléatoire**.

### 6.3 ✅ Les bornes ne sont pas des limites — et la dérive sature

Dérive sous pression constante, nuit après nuit :

| nuit | monde très dur (p=1,0) | monde moyen (p=0,5) |
|---|---|---|
| 10 | ×1,160 | ×1,080 |
| 50 | ×1,241 | ×1,144 |
| 100 | ×1,241 | ×1,145 |
| **1200** | **×1,241** | **×1,145** |

**Le rappel exponentiel fait mur : la dérive sature et ne diverge jamais.** Un monde dur
permet d'extraire +24 % de son stock, un monde moyen +14,5 %. κ dérive en sens inverse
(2,0 → 1,61) : l'agent apprend à dégrader plus doucement. C'est exactement la formulation
demandée — *« modifier les bornes devient exponentiellement plus complexe »*.

### 6.4 Trois défauts trouvés PAR la mesure, et corrigés

| # | Défaut | Symptôme mesuré | Correction |
|---|---|---|---|
| 1 | **Double comptage du stock** | la satiété se vidait par décroissance *et* par digestion : un repas finançait 59 ticks là où il faut en couvrir 133 | dans un modèle à deux étages, le stock ne baisse que parce qu'il est **digéré** |
| 2 | **Valeur nutritive en dur (0,4)** | énergie effondrée à 0,005 au 3ᵉ jour, agent mort *le ventre à moitié plein* (satiété bloquée à 0,392) | `valeur_nutritive()` **dérivée** du besoin réel : si la dépense change, la nutrition suit |
| 3 | **Cofacteur hydrique linéaire** | sous 50 % d'hydratation le bilan passait négatif **quoi que l'agent mange** — mort inévitable avant que la jauge d'eau n'atteigne zéro | plancher `COFACTEUR_HYDRIQUE_MIN` : la soif **ralentit** la digestion, jamais ne l'annule |

Les trois n'étaient **pas** visibles en lecture de code : ils ne sont apparus qu'en
simulant le métabolisme sur plusieurs journées.

### 6.5 🐛 Bug préexistant découvert et corrigé (hors périmètre v41.2)

Les compteurs de calibrage v34 (`jauge_min_*_jour`, `ticks_deficit_critique_jour`,
`effort_*_jour`, `ressources_vues_jour`) étaient initialisés **une seule fois**, dans
`__init__`, et **jamais réarmés** entre les journées.

- `jauge_min_satiete_jour` était donc le minimum **depuis la naissance**
- `ticks_deficit_critique_jour` un **cumul monotone**

C'est ce qui produisait les « **400/400 ticks en zone critique** » lus sur tous les runs de
la campagne : le chiffre **surestimait la détresse réelle du jour**. Corrigé par
`_reinitialiser_buffers_calibrage()`, appelée chaque nuit.

> ⚠️ Le commentaire d'origine de ce bloc invoquait explicitement *« le piège du bug
> `score_vocal_jour` v27.0 »* — le commentaire décrivait le piège, le code le contenait.
> **Troisième occurrence du fil n°3 de l'INDEX** (« un invariant en commentaire finit par
> être violé »).

### 6.6 État du run de vérification (300 jours)

Sur les 12 premiers jours d'un cerveau **neuf** :

| | avant v41.2 | après v41.2 |
|---|---|---|
| `okay / danger` | 676 saturé, identique sur 9 graines | **1,00 / 0,00 → 9,90 / 0,64** (variance retrouvée) |
| énergie | n'existait pas | 0,86 (j1) → 0,04 (j3) → 0,32 (j8) — **elle remonte** |
| vigueur | n'existait pas | 0,755 → 0,150 → 0,219 |
| accord C1/C2 | 0,5 % à 2000 j | 0,0–0,8 % (trop tôt pour conclure) |

⚠️ **Ce qui ne va pas encore** : l'énergie reste basse et instable. Un agent débutant ne
trouve que ~2 ressources/jour là où le métabolisme en demande 2,5. Il **survit** (il ne
meurt plus, contrairement aux trois premières versions) mais vit au plancher de vigueur.

Deux lectures possibles, non tranchées : soit le calibrage reste trop dur, soit c'est
**normal pour un débutant** et l'apprentissage doit rattraper — ce que le run de 300 jours
doit dire. **Ne pas recalibrer avant d'avoir cette réponse** : ce serait supprimer la
pression qui doit précisément pousser l'agent à chercher sa nourriture.

### 6.7 ⚠️ Le run de 300 jours tranche : l'apprentissage ne compense PAS

Mesuré sur les 71 premiers jours d'un cerveau neuf :

| Fenêtre | énergie moy. | vigueur moy. | ticks basse énergie |
|---|---|---|---|
| j1–20 | 0,172 | 0,197 | 326/400 |
| j21–40 | **0,270** | 0,270 | 292/400 |
| j41–60 | 0,125 | 0,179 | 360/400 |
| **derniers 20** | **0,079** | **0,155** | **383/400** |

**La tendance est descendante, pas ascendante.** Seulement **10 % des jours** ont une
énergie saine (> 0,35).

La cause est directe — le taux de fourrage réel :

| Fenêtre | nourriture trouvée / jour |
|---|---|
| j1–20 | 1,85 |
| j21–40 | 2,55 |
| derniers 20 | **1,35** |
| **moyenne** | **1,92** (il en faut **2,5**) |

**L'agent ne cherche pas sa nourriture, et ne l'apprend pas en 71 jours.** Le taux
n'augmente pas ; il fluctue autour de 1,9. La question §6.6 est donc tranchée : ce n'est
pas un débutant qui rattrape, c'est un déficit structurel.

**Deux corrections possibles — et une seule est honnête :**

| Option | Ce qu'elle fait | Verdict |
|---|---|---|
| Baisser `REPAS_PAR_JOURNEE` vers 1,9 | cale le métabolisme sur ce que l'agent trouve **aujourd'hui** | ⚠️ **supprime la pression** qui doit le pousser à chercher. On mesurerait alors un agent confortable qui n'a rien appris |
| Rendre les ressources plus **trouvables** (densité, odorat utile) | agit sur le **MONDE**, pas sur le barème | ✅ cohérent avec le seul levier qui ait jamais marché sur ce projet |

⚠️ **Ne pas trancher seul.** Baisser le barème rendrait la mécanique « verte » sans rien
démontrer — c'est exactement le mode d'échec que ce chantier s'était engagé à éviter
(§5 : *« ce qui ne serait PAS une preuve »*). La décision appartient à l'utilisateur.

**Ce qui est acquis malgré tout** : l'agent ne meurt plus (les trois premières versions le
tuaient), il gagne (26 victoires en 65 jours), l'énergie **alterne** entre 0,86 et 0,03
selon les jours au lieu de s'effondrer définitivement, et `okay/danger` a retrouvé de la
variance (1,00/0,00 → 9,90/0,64) contre 676 saturé et identique sur 9 graines en v41.

---

## 7. Le profil nutritionnel à trois axes (décision utilisateur du 15/08)

> *« Il va falloir fixer plusieurs paramètres sur la nourriture : niveau d'hydratation,
> niveau de satiété, valeur énergétique. Manger coûte (pomme = hydratation 3 %, mais
> dépense de digestion). Seule l'eau hydrate à 100 %, mais l'eau a zéro valeur
> énergétique. »*

### 7.1 Le modèle

Une ressource n'est plus « un type qui remplit sa jauge » : c'est un **profil de trois
grandeurs indépendantes**, plus le coût de sa propre digestion.

| Ressource | satiété | hydrique | énergie | digestion |
|---|---|---|---|---|
| **WATER** | 0,0 | **1,0** | **0,0** | 0,0 |
| **FOOD** | 1,0 | **0,03** | 1,0 | **0,15** |

Mesuré sur une consommation réelle (portion dérivée = 0,889) :

| | satiété | hydratation | énergie |
|---|---|---|---|
| **FOOD** | +0,700 | **+0,027** | **−0,133** ← le coût de digérer |
| **WATER** | +0,000 | **+0,700** | 0,000 |

**L'eau hydrate totalement, n'apporte aucune calorie et ne coûte rien à digérer. La
nourriture remplit le stock, hydrate à peine, et se paie à l'ingestion.**

Le coût de digestion est exprimé en **fraction de l'apport énergétique de cette
ressource** — digérer une pomme coûte une part de la pomme, jamais une constante détachée
de ce qu'on avale. Un aliment dont `digestion` approcherait 1,0 serait **net-nul** :
entièrement consommé par l'effort de le digérer.

⚠️ **Rien n'est expliqué au cerveau.** Il n'existe aucune table `pomme = bon`. L'agent ne
perçoit que les conséquences sur ses jauges ; la valence de chaque type reste **apprise**
par `empreinte_types` (v39.0). Ce tableau décrit le **monde**, pas la connaissance qu'en a
l'agent.

### 7.2 Bilan net mesuré (avec coût de digestion)

| nourriture/j | eau/j | Résultat |
|---|---|---|
| 2 | 2 | **MORT (famine) au tick 992** |
| **2,5** | 2 | E_moy 0,716 · min 0,341 · **0 % basse énergie** |
| 3 | 2 | E_moy 0,925 |
| 2 | **0** | **MORT (déshydratation) au tick 587** |
| **0** | 2 | **MORT (famine) au tick 367** |

Les trois axes sont donc réellement contraignants : l'eau seule tue de faim, la nourriture
seule tue de soif, et il faut **les deux** dans les bonnes proportions.

### 7.3 Le correctif porte sur le MONDE, pas sur le barème

Le témoin de 300 jours complet a confirmé le diagnostic §6.7 :

| Fenêtre | énergie moy. | nourriture/jour |
|---|---|---|
| j1–50 | 0,213 | 2,16 |
| j100–150 | 0,200 | 1,98 |
| **j250–300** | **0,234** | **1,94** |

**Aucune progression en 300 jours.** 130 victoires, mais seulement 18 % de jours à énergie
saine. Avec 2 sources par carte pour un besoin de 2,5/jour, il aurait fallu que l'agent
les trouve **toutes, à chaque épisode, sans jamais échouer**. Le déficit était
**structurel**, pas comportemental — aucune politique n'aurait pu le combler.

D'où la correction, appliquée à la **trouvabilité** :

```
NB_SOURCES_FOOD = round(REPAS_PAR_JOURNEE × MARGE_TROUVABILITE)   # 2 → 5
```

La densité est désormais **dérivée du besoin**, plus posée à 2. La marge de 2,0 couvre
l'échec de recherche : trouver la moitié des sources suffit à survivre, et l'agent qui
cherche mieux vit mieux.

> ⚠️ **Pourquoi pas baisser `REPAS_PAR_JOURNEE`** — l'option était plus simple et aurait
> immédiatement mis la mécanique au vert. Elle aurait calé le barème sur ce que l'agent
> trouve **déjà**, donc supprimé la pression même qui doit le pousser à chercher : on
> aurait mesuré un agent confortable qui n'a rien appris. Agir sur le monde est cohérent
> avec le **fil n°1** du projet — *« ce qui rend possible fait progresser, ce qui facilite
> ne change rien »* — et c'est le seul levier qui ait jamais fonctionné ici.

### 7.4 ❌ Première version des profils : ÉCHEC mesuré au jour 57

Le run lancé avec les profils + 5 sources a été **arrêté à 57 jours** :

| | témoin (2 sources) | **profils v1** |
|---|---|---|
| énergie moyenne | 0,21 | **0,072** |
| nourriture/jour | 1,94 | **2,48** ✅ |
| eau/jour | — | **1,04** |
| % jours énergie saine | 18 % | **4 %** |
| **victoires** | 130 (à 300 j) | **0** (à 57 j) |

**Le fourrage s'est amélioré et l'énergie s'est effondrée.** Contre-intuitif, donc
diagnostiqué plutôt que recalibré :

- L'agent buvait **0,97 eau/jour** pour un besoin théorique de **0,94** — il buvait donc
  *exactement ce qu'il fallait*.
- Mais son hydratation tombait à **0,00** la plupart des jours.

**La cause : une portion unique partagée entre les deux axes.** `valeur_nutritive()` valait
0,889, appliquée aussi bien à la satiété qu'à l'hydratation, sur des jauges plafonnées à
1,0. Mesuré sur une journée : **2,0 unités d'eau perdues par débordement**. Boire tôt
gaspillait, boire tard laissait la conversion déjà bridée par la soif — la fenêtre utile
était trop étroite pour être trouvée par apprentissage.

### 7.5 Le correctif : une portion par axe, dérivée de sa propre perte

```
valeur_nutritive() = besoin_énergie_journalier / REPAS_PAR_JOURNEE          → 0,889
valeur_hydrique()  = perte_eau_journalière / PRISES_HYDRIQUES_PAR_JOURNEE   → 0,208
```

**On boit plus souvent qu'on ne mange, et par plus petites gorgées** (4 prises/jour contre
2,5 repas). C'est ce qui évite le débordement : une prise ne dépasse jamais de beaucoup ce
qui manque à la jauge. La densité d'eau suit son propre rythme (`NB_SOURCES_WATER = 8`),
au lieu d'être recopiée de celle de la nourriture.

Effet mesuré :

| | portion partagée | **portions découplées** |
|---|---|---|
| eau gaspillée / journée | **2,00** | **0,07** (÷28) |
| énergie (régime nominal) | — | **0,806** |
| hydratation | 0,00 la plupart des jours | **0,896** |

Les trois axes restent contraignants : 2,5 food + 1 eau → **mort de déshydratation** au
tick 787 ; 2 food + 3 eau → **mort de famine** au tick 786. Le régime ne pardonne toujours
pas la négligence d'un axe.

> **Leçon de méthode.** Le fourrage *s'était amélioré* — un tableau de bord qui n'aurait
> regardé que « ressources trouvées » aurait conclu au succès. C'est l'écart entre deux
> métriques (fourrage ↑, énergie ↓) qui a révélé le défaut, pas l'une des deux seule.

### 7.6 ❌❌ Deuxième échec — et la vraie cause, qui invalide les deux correctifs

Le run relancé avec les portions découplées est **pire encore**, arrêté au jour 78 :

| | témoin | v1 (profils) | **v2 (hydrique découplé)** |
|---|---|---|---|
| énergie moyenne | 0,21 | 0,072 | **0,012** |
| % jours énergie saine | 18 % | 4 % | **2 %** |
| victoires | 130 (300 j) | 0 (57 j) | **0** (78 j) |

**La mesure qui tranche** — taux de récolte réel sur les 60 premiers jours des trois runs :

| Version | sources/carte | consommé/jour | **taux de récolte** |
|---|---|---|---|
| témoin | 20 | **3,72** | 18,5 % |
| v1 | 35 | **3,52** | 10,0 % |
| v2 | 35 | **3,47** | 9,9 % |

> **Le nombre absolu de ressources consommées est IDENTIQUE dans les trois versions
> (~3,5/jour).** Multiplier les sources par 1,75 n'a strictement rien changé : l'agent en
> ramasse autant, pas plus. Il rate ~90 % des opportunités (≈39 par jour, 13 par épisode ×
> 4,2 épisodes).

**Le correctif §7.3 était donc inopérant, et mon diagnostic était faux.** J'avais conclu
« déficit structurel, le monde est trop pauvre » — le monde n'était pas le facteur
limitant. L'agent ne récolte pas plus quand il y a plus.

**La vraie cause, arithmétique :**

```
besoin   = 2,5 food + 4,0 eau = 6,5 ressources/jour
capacité = ~3,5 ressources/jour, invariante depuis le début
```

Le besoin est **près du double** de ce que l'agent sait récolter. Et ce n'est pas un
problème de monde : c'est un problème de **comportement**. Il ne cherche pas sa
nourriture — cohérent avec les 48,6 % d'approche olfactive (= le hasard) mesurés dès H15,
et avec l'ablation qui montre l'odorat **inerte** (+0,0 sur 6 niveaux).

⚠️ **Le correctif §7.5 (portions découplées) a aggravé la situation** : en portant le
besoin hydrique de 1 à 4 prises/jour, il a creusé l'écart entre besoin et capacité. La
mécanique interne est plus juste (gaspillage ÷28, vérifié en simulation), mais elle exige
davantage d'un agent qui ne suit déjà pas.

### 7.7 Deux erreurs de diagnostic à consigner

1. **« Le déficit est structurel, il faut plus de ressources » (§7.3)** — faux. Mesuré :
   +75 % de sources → **0 % de récolte en plus**. J'ai raisonné sur la disponibilité
   théorique sans vérifier que l'agent y répondait.
2. **La simulation ne prédisait pas le run.** Mes trois calibrages (`DEPENSE_ENERGIE_JOUR`,
   `REPAS_PAR_JOURNEE`, portions) ont été validés sur un simulateur qui **suppose l'agent
   mangeant à intervalles réguliers**. Le run réel montre un agent qui mange **quand il
   trébuche sur une ressource**. Un simulateur qui postule le comportement qu'on cherche à
   obtenir ne peut rien valider.

> **La règle qui en sort** : ne calibrer un métabolisme qu'avec une trace de consommation
> **issue d'un run réel**, jamais avec un rythme supposé.

### 7.8 État : la mécanique est saine, le calibrage ne l'est pas

**Ce qui est acquis et vérifié** — invariant d'échelle (< 1 % d'écart 400 vs 3600), seuil
non linéaire (C2 s'éteint avant C1), dérive qui sature sans diverger, mort par
insolvabilité sans `if`, profils à trois axes conformes à la spécification, trois défauts
d'implémentation trouvés et corrigés, un bug préexistant corrigé.

**Ce qui ne l'est pas** : le barème est calé sur un agent qui saurait se nourrir. Il ne
sait pas. Tant que la récolte plafonne à 3,5/jour, **tout métabolisme exigeant plus de
3,5 le condamne**, et aucun réglage de densité ou de portion n'y changera rien.

**Trois voies possibles — arbitrage utilisateur nécessaire, je n'en prends aucune :**

| Voie | Ce qu'elle fait | Risque |
|---|---|---|
| **A.** Caler le besoin sous 3,5/jour | l'agent survit dès aujourd'hui et le reste de la mécanique devient mesurable | supprime la pression alimentaire — mais c'est peut-être le prix à payer pour tester le reste |
| **B.** Rendre l'odorat réellement utile | attaque la vraie cause (il ne cherche pas) | c'est un chantier en soi, et H15 a montré que le capteur seul ne suffit pas : il faut **retirer à la vue** ce qu'on confie à l'odorat |
| **C.** Ressource consommée au contact | supprime le besoin de viser | change les règles du monde, effet non mesuré |

Ma recommandation : **A d'abord** (pour débloquer la mesure du reste), **B ensuite** comme
chantier séparé. Faire B seul reviendrait à parier sur un mécanisme qui n'a jamais rien
donné en 9 tentatives.

---

## 8. 🎯 LA CAUSE RÉELLE — la carte était saturée

> Les trois voies du §7.8 sont **caduques**. Aucune n'était nécessaire : le défaut n'était
> ni le barème, ni l'odorat, ni le comportement de l'agent.

### 8.1 La mesure

Sur `Empty-5x5` — le niveau où l'agent est bloqué :

| | |
|---|---|
| Cases libres à l'intérieur | **8** |
| Ressources demandées (5 food + 8 eau) | **13** |
| Ressources réellement placées | **7** |
| **Cases libres restantes** | **1** |

**L'agent était emmuré dans un garde-manger.** Une seule case libre pour se déplacer sur
toute la carte.

### 8.2 Pourquoi les trois calibrages n'ont rien changé

Parce qu'ils réglaient un paramètre **déjà saturé**. La récolte était identique dans tous
les runs — 3,72 / 3,52 / 3,47 / 3,56 — non pas parce que l'agent « ne cherchait pas », mais
parce que **le monde ne pouvait pas contenir ce que je lui demandais**.

C'est aussi ce qui explique le paradoxe du §7.6 : passer de 20 à 35 sources n'augmentait pas
la récolte, puisque la carte plafonnait bien avant.

### 8.3 Le correctif : la densité est RELATIVE à la carte

```
budget = max(2, cases_libres × FRACTION_CASES_RESSOURCES_MAX)   # 35 %
total  = min(souhait_métabolique, budget)
```

`nb_sources_*` redevient un **souhait** dérivé du besoin ; la carte a le dernier mot. Le
plafond préserve la proportion food/eau plutôt que de tronquer la liste — sans quoi l'eau,
placée en second, aurait disparu la première.

| Carte | cases libres | food | eau | **restant** |
|---|---|---|---|---|
| `Empty-5x5` | 8 | 1 | 1 | **6** |
| `Empty-6x6` | 15 | 2 | 2 | **11** |
| `Empty-8x8` | 35 | 4 | 7 | **24** |
| `DoorKey-5x5` | 4 | 1 | 1 | **2** |

Sur le niveau bloquant : **2 ressources/épisode × 4,2 épisodes = 8,4 opportunités/jour**
pour un besoin de 6,5, plus le respawn 80/20 après consommation. Tendu, mais faisable —
là où 13 sources sur 8 cases rendaient la carte impraticable.

> **Même discipline que `DENSITE_MAX_PAR_CASE` (v31.0)** pour la mémoire spatiale : une
> quantité qui dépend du monde doit être bornée **par le monde**, jamais posée en absolu.

### 8.4 Troisième erreur de diagnostic — et la plus coûteuse

| # | Ce que j'ai affirmé | Réalité |
|---|---|---|
| 1 | « déficit structurel, le monde est trop pauvre » | le monde était **trop plein** |
| 2 | « il ne cherche pas sa nourriture » | il n'avait **pas la place** de la chercher |
| 3 | « c'est un problème de comportement, pas de monde » | c'était **exactement** un problème de monde |

**J'ai conclu trois fois sur le comportement de l'agent sans jamais avoir regardé la carte
qu'il habitait.** Le §7.7 posait la règle « ne calibrer qu'avec une trace de run réel » —
elle était juste mais insuffisante : *il faut aussi vérifier que le monde peut physiquement
accueillir ce que le calibrage suppose.*

Une seule commande — compter les cases libres — aurait invalidé les trois hypothèses avant
d'écrire la moindre ligne. C'est le coût de raisonner sur un modèle du monde plutôt que sur
le monde.

### 8.5 ✅ Premier résultat positif de tout le chantier

Run avec densité relative, comparé **à jour égal** (j61) :

| | témoin | v1 | v2 | v3 | **v4 (densité relative)** |
|---|---|---|---|---|---|
| **Victoires à j61** | 26 | 0 | 0 | 0 | **46** |
| Taux de récolte | 18,5 % | 10,0 % | 9,9 % | ~10 % | **26 %** |
| **Accord C1/C2** | ~0,5 % | — | — | — | **94,8 %** |

**+77 % de victoires sur le témoin**, et un rythme d'une victoire par jour (intervalle
moyen : 1 jour, n=53). Les trois runs intermédiaires étaient à **zéro**.

Le taux de récolte passe de 10 % à **26 %** : l'agent exploite bien mieux un monde
praticable, alors même qu'il y a **moins** de ressources (10,7 disponibles contre 35).

> ⚠️ **L'accord C1/C2 à 94,8 %** est le chiffre le plus frappant. Toute la campagne v41
> l'avait mesuré à **0,5 %** au terme de 2000 jours, et le chantier v37 à **0 %**. Il est
> trop tôt pour conclure (68 jours, une seule graine) — mais aucune mécanique cognitive
> n'avait jamais produit un tel écart. À confirmer sur ≥ 10 graines avant toute annonce.

### 8.6 Dernier ajustement — un besoin que le monde ne peut satisfaire n'est pas une pression

Malgré ces victoires, l'énergie restait à 0,023 et l'hydratation à 0,00. Cause mesurée :

```
Empty-5x5 : 1 source d'eau/épisode × 4,2 épisodes = 4,2 prises/jour
besoin (PRISES_HYDRIQUES_PAR_JOURNEE = 4,0)      = 4,0 prises/jour
→ marge : ×1,05, soit AUCUNE marge d'erreur
```

L'agent devait boire **à chaque occasion, sans jamais en rater une**. C'est le défaut du
§8.1 en plus subtil : non plus un monde physiquement saturé, mais un besoin que le monde ne
peut satisfaire **que dans le cas parfait**.

`PRISES_HYDRIQUES_PAR_JOURNEE` ramené de **4,0 à 2,0** — le ratio soif/faim reste > 1 (on
boit plus souvent qu'on ne mange, ce qui était le point du §7.5), mais les marges
redeviennent réelles :

| Carte | food | eau | marge food | marge eau |
|---|---|---|---|---|
| `Empty-5x5` | 4,2/j | 4,2/j | **×1,7** | **×2,1** |
| `Empty-6x6` | 8,4/j | 8,4/j | ×3,4 | ×4,2 |
| `Empty-8x8` | 21,0/j | 16,8/j | ×8,4 | ×8,4 |

> **La règle qui sort de tout le chantier** : un barème métabolique doit être confronté à
> ce que le monde peut **physiquement** offrir, carte par carte. Ni la simulation (§7.7) ni
> la trace de run (§8.4) ne suffisent — il faut mesurer **l'offre du monde**, puis vérifier
> que le besoin tient dedans avec de la marge.

---

## 9. Manger comme ACTE, et la boucle corporelle

Formulation utilisateur : *« les premiers jours il doit tout mettre à la bouche, mais dès
qu'il n'a plus faim il se met en pause et doit associer manger/boire = besoin. C'est le
corps qui pousse à manger pour vivre. »*

### 9.1 Deux défauts trouvés, deux corrections

**a) Manger était un effet de bord du déplacement.** Marcher sur une case chargée
consommait la ressource automatiquement. Un agent rassasié qui traversait une pomme
l'avalait et la gaspillait. **La « récolte » de tout ce chantier n'était donc pas un
comportement de recherche** mais une conséquence mécanique des déplacements — ce qui
invalide rétrospectivement la lecture des §7 et §8.

Corrigé : la consommation passe par `ACTION_CONSOMMER` (le `pickup` de MiniGrid).

**b) Le geste visait la mauvaise case.** `pickup` agit sur la case **devant** l'agent ;
le détecteur testait celle **sous ses pieds**. Les deux ne coïncident jamais — efficacité
mesurée : **2,9 %**. Pire, MiniGrid retirait quand même la Ball pour la mettre en
`carrying`, donc la ressource disparaissait sans nourrir ni repousser.

| | avant | après |
|---|---|---|
| Efficacité du geste | 2,9 % | **14,1 %** |
| Récolte | 2/jour | **10/jour** |

**c) Le soulagement n'était pas crédité au geste.** `r_bio` était calculé (l. 6400) *avant*
la consommation (l. 6449), et consommé dans la récompense (l. 6551). Le soulagement tombait
donc **au tick suivant**, sur une action sans rapport. Corrigé en mesurant le déficit
avant/après ingestion.

### 9.2 ✅ La formule de l'utilisateur est vérifiée dans le code

| État | Manger rapporte |
|---|---|
| **Affamé** (S=0,05 E=0,05) | **+0,7945** |
| Moyen (S=0,50 E=0,50) | +0,1267 |
| **Rassasié** (S=0,95 E=0,95) | **−0,0227** |

Manger repu est **puni** : gain nul et geste coûteux. Contraste affamé/rassasié : **15×**.
Aucune règle n'interdit de manger sans faim — le corps s'en charge, exactement comme
formulé.

### 9.3 ⚠️ Mais l'agent n'apprend pas à viser — et c'est arithmétique

Run de 65 jours, cerveau neuf :

| | 20 premiers j | 20 derniers j |
|---|---|---|
| Gestes joués | 58/jour (**17 % des ticks**) | 58/jour |
| Efficacité | 12,4 % | **10,6 %** |
| Soulagement/jour | +2,17 | +2,19 |

**Parfaitement plat.** L'agent mitraille le geste au hasard, 58 fois par jour, sans jamais
apprendre à le diriger.

La cause est une **espérance noyée dans le bruit** :

```
geste réussi (12 %)  : +0,323
geste raté   (88 %)  : −0,0047 (coût énergie)
espérance            : +0,033
```

À comparer au bruit ordinaire du tick : `dopamine_curiosite` 0,01–0,05, micro-récompenses
0,04. **Le signal du geste est du même ordre que le bruit qui l'entoure.**

Et surtout : **rater ne coûte presque rien**. Sur 58 gestes/jour, le gaspillage total
représente ~14 % de la dépense journalière pour 12 % de réussite. **Mitrailler est
rationnel** — le problème n'est pas que le geste coûte trop peu, c'est que *viser* ne
rapporte pas assez plus que *mitrailler*.

> ⚠️ Le coût nominal de 0,8 est **dilué** : `METABOLISME_BASAL_PART = 0,65` fait que
> l'écart entre l'action la moins chère (0,1) et la plus chère (0,8) ne représente que
> **24 %** de variation sur la dépense réelle du tick. Le barème d'actions a beaucoup
> moins d'effet que ses valeurs ne le laissent croire.

### 9.4 Ce qui est acquis, et ce qui reste ouvert

**Acquis** — la récolte passe de 2,0 à **7,4/jour**, et les victoires de 26 (témoin) à
**47** à jour égal. L'agent va mieux malgré une énergie encore basse.

**Ouvert** — trois voies, aucune prise sans arbitrage :

| Voie | Ce qu'elle fait | Risque |
|---|---|---|
| **A.** Augmenter le contraste réussi/raté | rendre le signal lisible au-dessus du bruit | un échec trop puni peut inhiber le geste entièrement |
| **B.** Réduire `METABOLISME_BASAL_PART` | redonner du poids au barème d'actions | touche un ancrage biologique (~65 % dans le vivant) |
| **C.** Ne rien faire, laisser le run à 300 j | l'apprentissage est peut-être plus lent que 65 jours | 65 jours parfaitement plats, peu d'espoir |

Ma lecture : **C d'abord** — la mesure est en cours et coûte zéro décision. A et B modifient
tous deux un ancrage posé, et A risque de produire l'effet inverse de celui recherché.

---

## 10. 🏁 Le run de 300 jours — résultat et verrou trouvé

### 10.1 Face au témoin, à durée égale

| | témoin (300 j) | **v41.2 (300 j)** |
|---|---|---|
| **Victoires** | 130 | **231** (×1,78) |
| **Maîtrise max** | 30 % | **60 %** (le seuil !) |
| Récolte/jour | 3,69 | **7,54** (×2,04) |
| Accord C1/C2 moyen | 47,4 % | **61,3 %** |
| Accord, 50 derniers jours | 50,6 % | **84,6 %** |
| Énergie moyenne | 0,200 | 0,120 |
| Niveau final | 1/15 | 1/15 |

**Le meilleur résultat du chantier** — et le premier à battre le témoin sur presque tous
les axes. L'énergie reste plus basse, ce qui est cohérent : l'agent bouge et agit davantage.

### 10.2 ⚠️ Ce qui n'a pas bougé

L'agent **n'apprend toujours pas à viser** : efficacité 13,5 % → 13,4 % sur 300 jours,
58 → 59 gestes/jour, récolte 7,8 → 7,8. Parfaitement plat, comme au jalon 65. Le §9.3 tient :
l'espérance du geste est noyée dans le bruit, et rater ne coûte presque rien.

Le soulagement moyen baisse même légèrement (+2,17 → +2,08) : l'agent ne mange pas *mieux à
propos* avec le temps.

### 10.3 🔒 LE VERROU — la promotion est mathématiquement impossible

La maîtrise a touché **60 % deux fois** (jours 137 et 195) — soit `TAUX_PROMOTION` exactement.
Aucune promotion. Diagnostic :

```
maturité = régularité × consolidation × autonomie      (v40.2, un PRODUIT)
```

Mesuré sur les 300 jours :

| Facteur | max | moyenne |
|---|---|---|
| régularité | 60 % | 30 % |
| consolidation | 100 % | 99 % |
| **autonomie** | **0 %** | **0 %** |
| **→ maturité** | **0,000** | seuil : **0,38** |

**`autonomie` vaut zéro sur les 300 jours, donc le produit est nul quoi qu'il arrive.**

La cause est une **dépendance circulaire entre deux constantes** :

```
autonomie      = 1 − facteur_guidage
facteur_guidage = 1 − clip((maîtrise − SEUIL_DEBUT_SEVRAGE) / (FIN − DEBUT))
SEUIL_DEBUT_SEVRAGE = 0.60   ← le sevrage COMMENCE à 60 %
TAUX_PROMOTION      = 0.60   ← la promotion EXIGE 60 %
```

| Maîtrise | Guidage | Autonomie |
|---|---|---|
| 30 % | 1,00 | **0,00** |
| **60 %** | **1,00** | **0,00** |
| 75 % | 0,50 | 0,50 |
| 90 % | 0,00 | 1,00 |

**À 60 % de maîtrise, l'autonomie vaut encore exactement 0.** Le sevrage *démarre* là où la
promotion était censée être acquise — il faut atteindre ~75 % pour que l'autonomie devienne
non nulle, et le run n'a tenu 60 % que 2 jours sur 300 (18 jours ≥ 50 %).

L'aide est restée **« pleine » 300 jours sur 300**.

> ⚠️ **Ce n'est pas un bug, c'est un défaut de conception entre deux mécaniques justes
> séparément.** La v40.2 a remplacé les deux portes scolaires par une maturité continue —
> décision saine (« un examen se passe par chance »). Mais elle a introduit `autonomie`
> comme facteur multiplicatif sans vérifier que le sevrage pouvait le rendre non nul dans
> la plage où la promotion se joue. Le commentaire du code le dit d'ailleurs en toutes
> lettres (l. 4623) : *« le sevrage n'a pas commencé, donc l'autonomie y est nulle par
> construction »* — écrit, jamais confronté au seuil de promotion.
>
> **Quatrième occurrence du fil n°3 de l'INDEX** (« un invariant en commentaire finit par
> être violé »).

### 10.4 Ce que cela implique

Le blocage au niveau 1/15 mesuré sur **10 graines × 2000 jours** (campagne v41) doit être
relu : aucune de ces graines ne pouvait être promue, quelle que soit sa performance. Le
« mur du cursus » n'était peut-être pas un mur de compétence.

**Ce que ce chantier a produit de plus solide n'est donc pas le métabolisme, mais ceci :**
un agent qui gagne 1,78× plus, atteint 2× la maîtrise du témoin, et reste bloqué par une
incompatibilité entre deux constantes.

⚠️ **Ne rien corriger sans arbitrage.** Trois options, aucune neutre :

| Option | Effet | Risque |
|---|---|---|
| Abaisser `SEUIL_DEBUT_SEVRAGE` sous `TAUX_PROMOTION` | rend l'autonomie non nulle dans la plage utile | sevrer trop tôt un agent qui n'a rien acquis |
| Retirer `autonomie` du produit de maturité | débloque immédiatement | perd le critère « il n'a plus besoin d'aide », qui est le plus significatif des trois |
| Remplacer le produit par une moyenne pondérée | un facteur nul ne bloque plus tout | change la sémantique : « toutes les conditions » devient « en moyenne » |

---

## 11. 🏁 v41.3 — le sevrage proportionnel : deux promotions, puis le mur

**Décision utilisateur du 15/08** : *« il faut créer une autonomisation inversement
proportionnelle au taux de maîtrise ! on essaye déjà avec ça et on avisera »* — soit la
première des trois options du §10.4, dans sa forme la plus radicale : pas d'abaissement du
seuil de départ, mais sa **suppression**.

### 11.1 Le correctif

`SEUIL_DEBUT_SEVRAGE` est supprimé. Le guidage décroît **dès le premier point de maîtrise** :

```python
taux = _taux_maitrise_niveau(etat)
taux_effectif = 0.0 if taux is None else taux
base = 1.0 - max(0.0, min(1.0, taux_effectif / SEUIL_FIN_SEVRAGE))
```

L'autonomie devient donc strictement proportionnelle à la maîtrise, et `SEUIL_MATURITE`
cesse d'être posé — il est **dérivé** de l'autonomie réellement atteignable au point de
promotion :

```python
_AUTONOMIE_A_PROMOTION = min(1.0, TAUX_PROMOTION / SEUIL_FIN_SEVRAGE)   # 0.667
SEUIL_MATURITE = TAUX_PROMOTION * _AUTONOMIE_A_PROMOTION                # 0.400
```

Le seuil de maturité n'est plus un chiffre choisi : c'est **ce qu'un agent tout juste
promouvable peut atteindre**, par construction.

### 11.2 Le résultat — run de 300 jours, graine unique

| Jalon | Niveau | Victoires | Maîtrise max | Maîtrise 50 derniers | Autonomie moy | Maturité max | Maturité moy |
|---|---|---|---|---|---|---|---|
| 62 j | 1/15 | 57 | 55 % | 35 % | 38 % | 0,336 | 0,139 |
| **117 j** | **2/15** | 98 | 70 % | 41 % | 43 % | **0,467** | 0,182 |
| **215 j** | **3/15** | 118 | 70 % | 6 % | 7 % | 0,469 | 0,008 |
| 300 j | 3/15 | 127 | 70 % | **2 %** | **3 %** | 0,469 | **0,002** |
| *v41.2 (témoin)* | *1/15* | *231* | *60 %* | — | **0 % sur 300 j** | **0,000** | *0,000* |

**Première promotion : jour 74.**

```
🎓 [PROMOTION] L'Agent passe en Éveil (Départ aléatoire) ! 🚀
   maturité 47% (régularité 60% × 20 épisodes × autonomie 78%)
```

Elle est légitime au sens strict de la v40.2 : fenêtre **pleine** (20 épisodes), taux tenu à
`TAUX_PROMOTION` exactement, agent sevré à 78 %. Ce n'est pas un examen réussi par chance.
Une seconde promotion suit, entre les jalons 117 et 215.

### 11.3 Ce que le correctif a levé — et ce qu'il n'a pas levé

✅ **Levé — le verrou de MESURE.** La maturité passe de 0,000 (300 jours) à 0,469, et deux
paliers sont franchis. Le §10 est confirmé : la promotion était **mathématiquement
impossible**, indépendamment de toute compétence.

❌ **Non levé — le verrou de COMPÉTENCE.** Après le niveau 3, l'effondrement est net :
20 victoires en 98 jours, maîtrise à **2 %** sur les 50 derniers jours, maturité moyenne à
0,002. Les 185 derniers jours ne produisent **aucune** promotion supplémentaire.

> **L'autonomie retombée à 3 % n'est pas une régression du correctif** — c'est son
> fonctionnement nominal : le sevrage étant inversement proportionnel à la maîtrise, une
> maîtrise à 2 % **doit** produire un guidage quasi maximal. Le mécanisme aide beaucoup un
> agent qui échoue beaucoup. Le défaut est en amont : il échoue.

### 11.4 Relecture de la campagne v41

Le §10.4 supposait que le blocage au niveau 1/15 sur 10 graines × 2000 jours pouvait n'être
qu'un artefact de mesure. **Ce run tranche partiellement** : les niveaux 1 et 2 étaient
effectivement acquis sans pouvoir être validés — c'était bien un artefact. Mais le mur
réapparaît **deux paliers plus loin**, sur le premier niveau qui exige une séquence.

Autrement dit : le correctif déplace le mur, il ne le supprime pas. Les deux promotions sont
du **rattrapage** — la validation de compétences déjà installées — et non un apprentissage
neuf.

### 11.5 ⚠️ Ce que ce run NE prouve PAS

- **Une graine ne prouve rien.** Précédent établi par ce projet même : g22 avait atteint le
  niveau 4 seule, et la campagne à 10 graines a montré que c'était une **loterie natale**
  (§ `CAMPAGNE_v41_population_et_ablation_aout_2026.md`). Affirmer que le sevrage
  proportionnel « débloque le cursus » sur la foi de ce seul run répéterait exactement
  l'erreur que la campagne avait servi à corriger.
- **Rien n'entre dans les README** tant qu'une campagne à ≥ 10 graines n'a pas confirmé la
  reproductibilité. La règle de miroir ne s'applique qu'aux chiffres mesurés sur population.
- Le verdict de **couper C2 = 0,0 pt** n'est pas affecté par ce correctif.

### 11.6 Prochaine étape proposée (non engagée)

Rejouer les **10 graines de la campagne v41** avec le sevrage proportionnel, sur 2000 jours,
et comparer les distributions de niveau atteint. C'est la seule mesure qui distingue un
correctif réel d'une seconde loterie natale.

### 11.7 ⚠️ CORRECTION (15/08, même jour) — la promotion du jour 74 était une loterie

Le §11.5 avertissait qu'une graine ne prouve rien. **Quatre graines fraîches l'ont
confirmé le jour même**, sur le code v41.4 (dont le calcul de sevrage est *identique* à
v41.3 quand l'héritage est nul — vérifié par `git diff`) :

| Graine | Jours | Niveau | Promotions | Maîtrise max |
|---|---|---|---|---|
| g11 | 1300 | 1/15 | **0** | 65 % |
| g22 | 1310 | 1/15 | **0** | 55 % |
| g33 | 1310 | 1/15 | **0** | 55 % |
| g44 | 1290 | **3/15** | 2 (j477, j493) | — |
| *g42 (v41.3)* | *300* | *3/15* | *2 (j74)* | *70 %* |

**Trois graines sur quatre ne franchissent aucun palier en 1300 jours.** La quatrième en
franchit deux, mais **six fois plus tard** (jour 477 contre 74).

> 🔴 **Ce que je dois corriger de ma propre lecture** : j'ai qualifié la promotion du jour
> 74 de *« premier franchissement de palier reproductible du projet »*. L'avertissement
> était posé deux paragraphes plus bas, et je l'ai quand même écrit. **Le mot était faux.**
> C'était un franchissement — pas un franchissement *reproductible*.
>
> Ce qui reste vrai et démontré sur population (10 runs) : le **verrou de mesure** est levé
> — l'autonomie moyenne passe de **0 %** (v41.2, 300 jours) à **28,5 %**. La maturité peut
> désormais être non nulle. C'est un résultat réel, et il est suffisant sans être enjolivé.
