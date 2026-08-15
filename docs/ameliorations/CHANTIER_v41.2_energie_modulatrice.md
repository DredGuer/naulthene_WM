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
