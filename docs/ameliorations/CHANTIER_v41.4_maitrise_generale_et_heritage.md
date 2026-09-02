# Chantier v41.4 — La maîtrise générale et l'héritage de sevrage

> **Statut** : implémenté (v41.4, CHANGELOG du 15/08/2026). ⚠️ **Campagne JAMAIS CONCLUE** —
> annoncée « 10 graines × 2 variantes en cours » le 15/08 ; au 02/09 **aucun dossier de
> campagne ni document de résultat n'existe**, et le cycle v41.41 → v41.51 est parti sur
> d'autres pistes. La mécanique est donc **dans le code, non évaluée à n ≥ 20**.
> *(Statut requalifié le 02/09/2026 — voir
> [état du dépôt](../etat_des_lieux/02092026_etat_du_depot_et_reste_a_faire.md) §3.5.)*
> **Fichier** : `src/naulthene/cerveau/noyau.py` (expérimental — pas dans `colab.py`).
> **Décision utilisateur** : *« Tu as une maîtrise générale des cartes et une maîtrise
> carte par carte »*, et *« reporter une proportion du niveau précédent de maîtrise sur
> le suivant »*.

---

## 1. Le défaut mesuré

Le run v41.3 de 300 jours (voir `CHANTIER_v41.2_energie_modulatrice.md` §11) a produit
**deux promotions** — les premières du projet — puis un effondrement.

| Jalon | Niveau | Maîtrise 50 derniers j | Autonomie moy | Maturité moy |
|---|---|---|---|---|
| 117 j | 2/15 | 41 % | 43 % | 0,182 |
| 215 j | 3/15 | 6 % | 7 % | 0,008 |
| 300 j | 3/15 | **2 %** | **3 %** | **0,002** |

**La cause est mécanique, pas comportementale.** À chaque promotion :

```python
etat.historique_episodes_niveau = []    # invariant NON NÉGOCIABLE (v35.0)
```

Donc `_maturite_niveau()` retombe à **0,000 exactement** (régularité 0 × consolidation 0
× autonomie 0), et `facteur_guidage` remonte à **1,0 — l'aide maximale**. L'agent
**redevient un nouveau-né sur chaque carte**, quelle que soit son expérience.

Or un agent qui vient de tenir 60 % sur trois cartes n'est pas un débutant absolu : il
sait viser un but, contourner un mur, terminer un épisode. Ce qui est périmé au
changement de carte, c'est le **plan** — pas la **compétence motrice**.

## 2. La mesure préalable — le report est-il seulement justifié ?

⚠️ **Méthode du projet** (posée en v30.1) : *avant de rendre une constante adaptative,
l'instrumenter et la mesurer d'abord*. Un report de « X % » posé à la main aurait été un
chiffre arbitraire de plus.

Mesure sur les **15 niveaux du PROGRAMME**, 40 resets chacun, propriétés structurelles
lues sur la grille (`docs/recherche/` — script `mesure_parente.py`) :

| Transition | Parenté | Nouveau vocabulaire |
|---|---|---|
| Nourrisson → Éveil | **0,70** | — |
| Éveil → Maternelle | **0,59** | — |
| Maternelle → Primaire 1 | **0,85** | — |
| Primaire 1 → Primaire 2 | **0,20** ⚠️ | `lava` |
| Primaire 2 → Primaire 3 | **0,00** ⚠️ | `ball`, `key` |
| Primaire 3 → Collège 1 | **0,00** ⚠️ | `door` |
| Collège 1 → Collège 2 | **0,17** ⚠️ | `goal`, `key` |
| Collège 2 → Collège 3 | 0,66 | — |
| Collège 3 → Lycée 1 | 0,58 | — |
| Lycée 1 → Lycée 2 | 0,95 | — |
| Lycée 2 → Lycée 3 | 0,66 | `box` |
| Lycée 3 → Université | **0,31** ⚠️ | `ball` |
| Université → Doctorat 1 | **0,00** ⚠️ | `door`, `goal` |
| Doctorat 1 → Doctorat 2 | 0,74 | — |

**6 transitions sur 14 sont des ruptures** (< 0,50), dont **trois à 0,00**.

> 🎯 **Ce que la mesure tranche.** L'intuition « reporter une proportion » est juste,
> mais un report **uniforme** serait faux dans au moins six cas sur quatorze. Le report
> doit être **proportionnel à la parenté**, et la parenté doit être **mesurée**.
>
> Elle explique aussi rétrospectivement l'effondrement de v41.3 : l'agent a calé au
> niveau 3 → 4 (`SimpleCrossing` → `LavaGap`), une transition à **parenté 0,20** avec un
> vocabulaire neuf (`lava`).

## 3. La mécanique

### 3.1 Deux grandeurs, deux rôles

| Grandeur | Vidée à la promotion ? | Pilote |
|---|---|---|
| `historique_episodes_niveau` (par carte) | ✅ oui | la **PROMOTION** |
| `historique_episodes_general` (transversale) | ❌ **non** | le **SEVRAGE** |

### 3.2 La parenté, lue sur la grille

`_profil_carte(env)` lit surface, espace libre, densité d'obstacles, et l'**ensemble
opaque** des étiquettes d'objets. `_parente_cartes(a, b)` en dérive :

```
parenté = forme × vocabulaire
  forme       = 1 − moyenne des écarts relatifs (surface, libres, densité)
  vocabulaire = |types(b) ∩ types(a)| / |types(b)|
```

**Multipliés, jamais sommés** — même raison que la maturité : une carte de forme
identique au vocabulaire inconnu n'est **pas** un niveau parent, et une somme laisserait
la forme compenser la nouveauté.

⚠️ **Le vocabulaire reste opaque.** Aucune table `objet → difficulté` : « lava est
dangereux » n'est écrit nulle part, seulement « `lava` est un symbole que cette carte-ci
n'avait pas ». Même discipline que l'empreinte de type (v39.0).

### 3.3 L'héritage

```python
fraîcheur       = min(1, len(historique_niveau) / FENETRE_PROMOTION)
poids_héritage  = (1 − fraîcheur) × parenté
taux_sevrage    = taux_niveau × (1 − poids) + taux_général × poids
```

Le produit de deux grandeurs mesurées décide seul. Rien n'est posé.

## 4. Les cinq invariants — tous vérifiés

| # | Invariant | Vérification |
|---|---|---|
| 1 | L'héritage ne touche **que** le sevrage | `_maturite_niveau` lit toujours la seule maîtrise par carte |
| 2 | À fenêtre pleine, héritage = **0 exact** | guidage **1,000** mesuré (= v41.3) |
| 3 | Parenté 0 (rupture) ⇒ **aucun** héritage | guidage **1,000** mesuré |
| 4 | Une baisse de compréhension **remonte** l'aide | 100 % → autonomie 100 % ; 0 % → 0 % |
| 5 | Un `.brain` antérieur repart héritage nul | vérifié sur un cerveau de **2700 jours**, **2 nuits complètes** |

> L'invariant 5 exige une **nuit complète**, pas des ticks : le bug de greffe v32.0 ne se
> manifestait **ni au chargement ni pendant la journée**, mais à la première
> `executer_nuit`.

### L'effet, sur une transition parente (0,73)

| Épisodes joués sur la nouvelle carte | Autonomie |
|---|---|
| 0 | **49 %** (au lieu de 0 %) |
| 5 | 36 % |
| 10 | 24 % |
| 15 | 12 % |
| 20 (fenêtre pleine) | **0 %** — retour exact à v41.3 |

L'héritage est une **avance**, jamais une rente : il s'efface à mesure que les données
réelles arrivent.

## 5. Le protocole de campagne

⚠️ **Une graine ne prouve rien** — précédent g22 (niveau 4 en solo, invalidé comme
loterie natale par la campagne à 10 graines). Et comparer 10 graines v41.4 à un run
antérieur ne vaudrait rien non plus : les trajectoires natales diffèrent.

**Protocole retenu** : 10 graines × 2 variantes = **20 runs de 300 jours**, mêmes
graines des deux côtés, lancés au même moment, la seule mécanique testée étant coupée
côté témoin par `--sans-heritage` (ablation vérifiée : guidage 1,000 contre 0,513).

Graines : 11, 22, 33, 44, 55, 66, 77, 88, 99, 111.

## 6. Résultats

*(en attente de la fin de campagne — cette section sera remplie par la mesure, pas par
l'attente)*

---

## 6. Résultats

### 6.1 ⚠️ Première campagne INVALIDÉE — l'ablation n'atteignait pas le module

Les 20 runs lancés le 15/08 à 14h20 sont **jetés**. L'analyseur a montré que témoin et
variante produisaient des logs **rigoureusement identiques** (maturité 0,361 des deux
côtés sur g11, 0,278 sur g22, sur 135 jours).

**Cause.** `python -m naulthene.cerveau.noyau` charge le fichier **deux fois**, sous deux
noms : `__main__` (le bloc CLI) et `naulthene.cerveau.noyau` (celui que voient les
fonctions définies plus haut). Le `globals()["HERITAGE_SEVRAGE_ACTIF"] = False` du bloc
CLI écrivait dans la copie `__main__` ; `facteur_guidage` lisait l'autre, restée à `True`.
Le message « ABLATION » s'imprimait, et **rien n'était coupé**.

> 🔁 **Deuxième occurrence du défaut que ce même bloc dénonce quelques lignes plus haut**
> — le bug du 14/08 où trois graines différentes produisaient trois runs identiques.
> Ajouté depuis : une **assertion à l'exécution**, pour qu'une ablation muette ne puisse
> plus produire une campagne entière de résultats faux sans aucun signal.

**Second défaut, de télémétrie seule.** La ligne de bilan comparait `taux_sevrage_jour`
(calculé en **début** de journée) au taux de **fin** de journée : entre les deux la
fenêtre glissante a bougé, et cet écart — une simple dérive temporelle — était étiqueté
« héritage ». Jusqu'à **−33 pt** affichés sur un run où l'héritage était pourtant coupé.

Correctifs en `35bb93b`. Cerveaux archivés dans `brains/old_V414_invalides/`.

### 6.2 🎯 La limite STRUCTURELLE de la mécanique — mesurée, pas supposée

Sur le code corrigé, l'héritage affiche encore **+0 %** — mais pour une raison entièrement
différente, et celle-ci est **de conception** :

```
parente_niveau_precedent  n'est calculée QU'AU MOMENT D'UNE PROMOTION
poids_heritage = (1 − fraîcheur) × parenté
```

**Tant qu'aucune promotion n'a eu lieu, la parenté vaut 0, donc l'héritage vaut 0.**

C'est logiquement correct — avant une promotion il n'existe aucune carte précédente dont
hériter — mais la conséquence est sévère :

> ⚠️ **L'héritage ne peut pas débloquer un agent bloqué au niveau 1.** Il ne sait
> qu'*accélérer* un agent qui franchit déjà des paliers. Or c'est au niveau 1 que les
> agents restent.

La mécanique traite donc le symptôme observé en v41.3 (**l'effondrement après promotion**)
et non la cause du blocage initial.

### 6.3 Les 4 runs longs — 2000 jours, graines 11/22/33/44

| Graine | Jour | Niveau | Promotions | Maturité max | Maîtrise max |
|---|---|---|---|---|---|
| g11 | ~395 | 1/15 | **0** | **0,397** | 65 % |
| g22 | ~398 | 1/15 | **0** | 0,278 | 55 % |
| g33 | ~399 | 1/15 | **0** | 0,306 | 55 % |
| g44 | ~392 | 1/15 | **0** | 0,250 | 55 % |
| *v41.3 (g42)* | *74* | *2/15* | *1* | *0,467* | *70 %* |

**g11 a manqué la promotion de 3 millièmes** (0,397 contre un seuil à 0,400).

### 6.4 ⚠️ Ce que ces chiffres disent de la v41.3 — relecture

Vérifié par `git diff` : à héritage nul, `facteur_guidage` calcule **exactement** la même
chose qu'en v41.3 (`taux_pour_sevrage = taux_effectif`). Il n'y a donc **aucune
régression** — la différence tient à la **graine**.

Or v41.3 tournait sur la graine **42** (défaut du CLI) et atteignait 70 % de maîtrise, là
où **4 graines sur 4** plafonnent à 55-65 %.

> 🔴 **La promotion du jour 74 était très probablement une loterie natale de plus** — le
> même phénomène que g22 (niveau 4 en solo, invalidé par la campagne à 10 graines). Le
> §11.5 du chantier v41.2 avait posé l'avertissement ; ces 4 graines commencent à le
> confirmer.
>
> Conséquence : le « verrou de mesure levé » annoncé en v41.3 reste vrai (la maturité
> peut désormais être non nulle), mais **« deux paliers franchis » n'est pas un résultat
> de population** et ne doit pas être présenté comme tel.

### 6.5 🧬 PREMIÈRE ACTIVATION RÉELLE — g44, jours 477 et 493

g44 est le premier agent à franchir un palier sur le code v41.4 corrigé. La mécanique
s'active donc pour la première fois **en conditions réelles**, et se comporte exactement
comme conçue.

```
🎓 PROMOTION → Éveil       (maturité 40% = régularité 60% × 20 ép. × autonomie 67%)
   🧬 parenté avec la carte quittée : 65%
🎓 PROMOTION → Maternelle  (maturité 47% = régularité 65% × 20 ép. × autonomie 72%)
   🧬 parenté avec la carte quittée : 55%
```

**Les parentés mesurées en vol (65 %, 55 %) correspondent à la mesure hors-ligne**
(0,70 et 0,59 sur `Empty-5x5 → Empty-Random-6x6 → Empty-8x8`) — l'écart tient à la carte
tirée au moment de la promotion, la mesure hors-ligne moyennant 40 resets.

**L'héritage décroît comme prévu** (extraits consécutifs après la 2ᵉ promotion) :

| Sevrage appliqué | Héritage | Fenêtre |
|---|---|---|
| 26 % | **+26 pt** | vide |
| 22 % | +22 pt | ↓ |
| 20 % | +20 pt | ↓ |
| 17 % | +17 pt | ↓ |
| 13 % | +13 pt | ↓ |
| 14 % | **+6 pt** | se remplit |
| … | **+0 pt** | pleine |

> ✅ **Les invariants 2, 3 et 4 tiennent en conditions réelles**, pas seulement en test
> unitaire : l'héritage est une avance qui s'efface, jamais une rente.

### 6.6 📊 LE CHIFFRE QUI COMPTE — 477 jours, puis 16

| Promotion | Jour | Écart |
|---|---|---|
| 1ʳᵉ (Nourrisson → Éveil) | **477** | — |
| 2ᵉ (Éveil → Maternelle) | **493** | **+16 jours** |

**La deuxième promotion a coûté 30× moins de temps que la première.** C'est précisément
l'effet recherché : l'agent est arrivé sur `Empty-Random-6x6` avec ~27 pt d'autonomie
héritée au lieu de 0, et n'a pas eu à reconstruire son sevrage depuis zéro.

⚠️ **Ce chiffre ne prouve encore rien à lui seul** : `Empty-Random-6x6` est aussi un
niveau plus facile que `Empty-5x5` sur certains tirages, et **n = 1**. Seule la
comparaison appariée avec le témoin (`--sans-heritage`, même graine) peut trancher — elle
est en cours.

### 6.7 ❌ Ce que l'héritage ne fait PAS — 355 jours de stagnation au niveau 3

Après la 2ᵉ promotion, g44 stagne sur `Empty-8x8` :

```
Cursus   : Niveau 3/15 — maîtrise 20% (n=20) | sevrage 83%
Maturité : 0,033 / 0,40 — régularité 20% × consolidation 100% × autonomie 17%
```

Maturité **0,469 juste après la promotion** (portée par l'héritage), puis **0,033** —
355 jours plus tard, toujours au même palier.

> 🔴 **Confirmation du §6.2 : l'héritage accélère, il ne débloque pas.** Il donne une
> avance au démarrage ; si l'agent ne sait pas résoudre la carte, l'avance s'épuise en
> ~20 épisodes et le mur reste entier. La maîtrise réelle sur `Empty-8x8` est de **20 %**.
>
> Et l'invariant 4 fonctionne : maîtrise tombée à 20 % ⇒ sevrage **83 %**, l'aide est
> revenue presque au maximum. C'est exactement le comportement demandé
> (« une baisse de compréhension augmente aussi l'aide proportionnellement ») — mais il
> ne suffit pas à faire apprendre `Empty-8x8`.

### 6.8 🏁 VERDICT DE LA CAMPAGNE APPARIÉE — 300 jours, 5 paires

Comparaison appariée, même graine des deux côtés, seul l'héritage diffère :

| Graine | v41.4 | témoin | Δ niveau | Δ promotions |
|---|---|---|---|---|
| g11 | 1/15 | 1/15 | **0** | 0 vs 0 |
| g22 | 1/15 | 1/15 | **0** | 0 vs 0 |
| g33 | 1/15 | 1/15 | **0** | 0 vs 0 |
| g44 | 1/15 | 1/15 | **0** | 0 vs 0 |
| g55 | 1/15 | 1/15 | **0** | 0 vs 0 |

| Agrégat | v41.4 | témoin |
|---|---|---|
| Niveau max moyen | 1,00 | 1,00 |
| Promotions totales | **0** | **0** |
| Maturité max moyenne | **0,295** | **0,295** |
| Autonomie moyenne | **28,5 %** | **28,6 %** |
| Héritage moyen | **0,0 pt** | 0,0 pt |

**Test des signes : aucune paire discordante. Δ = +0,00 sur 5 paires.**

> ⚠️ **Ce n'est PAS un verdict « la mécanique ne sert à rien » — c'est un verdict
> « la mécanique n'a pas pu être testée ».** L'héritage moyen mesuré vaut **0,0 pt** des
> deux côtés : avec 0 promotion en 300 jours, `parente_niveau_precedent` n'est jamais
> calculée, donc le poids d'héritage reste nul par construction (§6.2). Le témoin et la
> variante exécutent littéralement le même code.
>
> C'est la différence entre une ablation **négative** (mesurée à 0, comme C2) et une
> ablation **vide** (jamais activée). Confondre les deux serait exactement l'erreur
> dénoncée dans `CAMPAGNE_P17_ABLATION` : *« une ablation dont le témoin est à zéro ne
> mesure rien »*.

**Ce que la campagne mesure quand même**, et qui est solide : le sevrage v41.3 fonctionne
en population — **autonomie moyenne 28,5 % sur 10 runs**, contre **0 % sur 300 jours** en
v41.2. Le verrou de mesure est bien levé, sur population cette fois et non sur une graine.

**Ce qu'elle confirme aussi** : 300 jours ne suffisent pas à produire une promotion sur
ces graines. La seule promotion observée sur code v41.4 (g44) est survenue au jour **477**.
Toute campagne future visant la promotion doit donc durer **≥ 1000 jours**, sans quoi elle
mesure le vide.

### 6.9 📌 Décision

| Élément | Statut | Motif |
|---|---|---|
| Maîtrise générale (`historique_episodes_general`) | **CONSERVÉ** | grandeur mesurée, coût nul, instrumentée |
| Parenté lue sur la grille (`_parente_cartes`) | **CONSERVÉ** | mesure vérifiée en vol (65 %/55 %), utile en soi |
| Héritage de sevrage | **CONSERVÉ, NON PROUVÉ** | n = 1 favorable (477 j → 16 j), 0 mesure appariée |
| `--sans-heritage` | **CONSERVÉ** | l'ablation devra être rejouée sur ≥ 1000 jours |

**L'héritage n'est pas retiré, mais il n'est pas non plus revendiqué.** Il ne peut pas
entrer dans les README : la seule mesure favorable est n = 1, et la campagne appariée n'a
rien pu mesurer.

⚠️ **Ce que la mécanique ne fait pas, et qui est désormais établi sur deux sources**
(§6.2 par conception, §6.7 par mesure sur g44) : elle **accélère** un agent qui franchit
déjà des paliers, elle ne **débloque** pas un agent bloqué. Le blocage au niveau 1 —
**3 graines sur 4 à 1300 jours, 10 runs sur 10 à 300 jours** — reste entier et n'est pas
de son ressort.

### 6.10 ⚠️ Troisième erreur d'analyse du chantier, consignée

L'analyseur a d'abord affiché **« autonomie 0,0 % »** sur des runs où elle valait
réellement 28 %. Cause : le regex exigeait `autonomie (\d+)%\)` — avec parenthèse
fermante, présente sur la ligne de *promotion* mais absente de la ligne de *bilan*. Seules
les promotions étaient captées ; sans promotion, la moyenne tombait à 0.

J'ai reporté ce chiffre faux avant de le vérifier. Corrigé, il vaut **28,5 %** — et il
change la conclusion : le sevrage v41.3 **fonctionne en population**, là où le chiffre
erroné suggérait qu'il ne mordait pas du tout.

> **Fil récurrent du projet** : un outil de mesure est du code comme un autre, et il se
> vérifie avant qu'on lui fasse confiance. C'est la 3ᵉ erreur de lecture consignée sur ce
> chantier, après les 4 du v41.2.

---

## 7. 🔴 DÉCOUVERTE — la maturité est calculée avec une autonomie en retard d'un jour

Trouvé en analysant pourquoi **g11 n'a jamais été promu en 1750 jours** alors qu'il a
atteint **65 % de maîtrise** — soit plus que `TAUX_PROMOTION = 60 %`.

### 7.1 Le fait mesuré

Les 4 jours où g11 a frôlé le seuil :

| Maîtrise | Sevrage | Autonomie | Maturité | Seuil |
|---|---|---|---|---|
| 50 % | 28 % | 72 % | 0,361 | 0,400 |
| **65 %** | 39 % | **61 %** | **0,397** | 0,400 |
| 55 % | 28 % | 72 % | 0,397 | 0,400 |
| 60 % | 39 % | 61 % | 0,367 | 0,400 |

**Manqué de 3 millièmes, quatre fois, en 1750 jours.**

### 7.2 La cause — un décalage temporel d'une journée

```
jour J, demarrer_journee (l. 5775) : facteur_guidage(etat)  ← lit la fenêtre de la VEILLE
jour J, executer_nuit    (l. 7117) : _maturite_niveau(etat) ← lit la maîtrise DU JOUR J
```

`_maturite_niveau` multiplie donc la **maîtrise d'aujourd'hui** par l'**autonomie
d'hier**. Tant que la maîtrise est stable, l'écart est nul. Mais **au moment précis où la
maîtrise monte** — c'est-à-dire au moment où la promotion se joue — l'autonomie
correspond encore à la maîtrise de la veille, plus basse. La maturité est
**systématiquement sous-estimée pendant les phases de progression**.

Vérification arithmétique sur la ligne à 65 % :

```
autonomie cohérente  : 65 % / 90 %  = 72 %  →  maturité = 0,65 × 0,72 = 0,469  ✅ PROMU
autonomie réellement lue (veille, 55 %) : 61 %  →  0,65 × 0,61 = 0,397  ❌ refusé
```

**L'agent avait la compétence requise et le calcul le lui a refusé sur un décalage
d'index.**

### 7.3 Portée

Le tableau théorique dit que **60 % de maîtrise suffit** (maturité 0,400 = seuil exact) :

| Maîtrise | Autonomie | Maturité | Promu ? |
|---|---|---|---|
| 55 % | 61 % | 0,336 | non |
| **60 %** | **67 %** | **0,400** | **OUI — tout juste** |
| 65 % | 72 % | 0,469 | oui |

Or le seuil est franchi **à l'égalité exacte** à 60 %. Un décalage d'un jour, même petit,
suffit à faire passer en dessous. La marge est **nulle par construction** —
`SEUIL_MATURITE` étant dérivé de `TAUX_PROMOTION` via la même formule que l'autonomie, les
deux se touchent sans se croiser.

> C'est le même motif que le verrou du §10 (v41.2) : deux constantes justes séparément,
> dont la composition se neutralise. La v41.3 avait corrigé le cas « autonomie nulle » ;
> il reste le cas « autonomie en retard ».

### 7.4 ⚠️ Correctif NON appliqué — décision utilisateur requise

Trois options, aucune neutre :

| Option | Effet | Risque |
|---|---|---|
| Recalculer l'autonomie dans `_maturite_niveau` à partir de la maîtrise courante | supprime le décalage, la maturité redevient cohérente | le guidage *appliqué* de la journée reste celui de la veille — la maturité mesurerait alors une autonomie qui n'a pas été vécue |
| Évaluer la promotion **avant** la mise à jour de la fenêtre | aligne les deux termes sur la veille | retarde toute promotion d'un jour (inoffensif) |
| Ne rien changer | statu quo | la promotion exige *de facto* ~65 % là où le projet dit 60 % |

**Je penche pour la 2ᵉ** : elle aligne les deux termes sur le même instant sans inventer
une autonomie non vécue, et son seul coût est un jour de retard. Mais c'est un changement
du critère de promotion — donc un arbitrage utilisateur, pas une correction de bug.

### 7.5 🎯 PREUVE DIRECTE — g44 promu à 60 %, g11 refusé à 65 %

Les deux runs de 2000 jours fournissent la comparaison qui tranche :

| | Maîtrise | Autonomie utilisée | Maturité | Résultat |
|---|---|---|---|---|
| **g44** (jour 477) | **60 %** | **67 %** — cohérente (60/90) | **0,400** | ✅ **PROMU** |
| **g11** (4 fois) | **65 %** | **61 %** — celle de la veille (55/90) | 0,397 | ❌ refusé |

> 🔴 **g11 avait une MEILLEURE maîtrise que g44 et n'a pas été promu.** La seule
> différence entre les deux : chez g44 l'autonomie était synchrone avec la maîtrise ce
> jour-là ; chez g11 elle était en retard d'un jour.
>
> Ce n'est plus une hypothèse sur un décalage d'index : c'est deux agents, même code,
> même seuil, dont **le moins compétent est promu et le plus compétent refusé**.

Et g44 a été promu avec une maturité de **0,400 pile** — l'égalité exacte annoncée au
§7.3. La marge est bien nulle : la promotion ne passe que si l'autonomie est parfaitement
synchrone, ce qui n'arrive que par coïncidence (fenêtre stable la veille et le jour même).

**Cela reclasse le « blocage au niveau 1 »** : ce n'était pas, pour g11, un mur de
compétence. Combien des blocages historiques du projet relèvent de ce décalage plutôt que
de l'incapacité reste une question ouverte — mais elle doit être posée avant toute
nouvelle mécanique cognitive.

## 8. Bilan final des 4 runs de 2000 jours

| Graine | Niveau | Promotions | Maturité max | Maîtrise max | Jours frôlant le seuil |
|---|---|---|---|---|---|
| g11 | 1/15 | 0 | **0,397** | **65 %** | **4** |
| g22 | 1/15 | 0 | 0,278 | 55 % | 0 |
| g33 | 1/15 | 0 | 0,306 | 55 % | 0 |
| **g44** | **3/15** | **2** (j477, j493) | 0,469 | 65 % | 1 |

Aucun crash, aucune mort métabolique sur 8000 jours cumulés.

**Lecture** : 2 graines sur 4 (g11, g44) atteignent 65 % de maîtrise — au-dessus de
`TAUX_PROMOTION`. Une seule est promue. g22 et g33 plafonnent réellement à 55 % et leur
blocage, lui, semble bien être un mur de compétence.

---

## 9. 🔬 La paire g77 — première (et seule) mesure appariée VALIDE

Sur les 10 paires de la campagne 300 jours, **une seule** a produit une promotion :
g77, au **jour 290**, des deux côtés. C'est donc la seule paire où l'ablation mesure
réellement quelque chose.

**L'ablation coupe bien** — vérification directe :

| | Lignes d'héritage non nul |
|---|---|
| g77 v41.4 | **+29 pt**, +23, +16, +1, +1… |
| g77 témoin | **aucune** |

La promotion tombe au **même jour (290) des deux côtés**, ce qui est attendu : avant toute
promotion la parenté vaut 0, donc les deux codes sont strictement identiques. La
divergence ne peut commencer qu'**après**.

### 9.1 Les 10 jours post-promotion — signal défavorable, mais non concluant

| | Sevrage moyen | Maîtrise max | Maturité max |
|---|---|---|---|
| **v41.4** | **63,0 %** | **38 %** | 0,506 |
| **témoin** | 48,7 % | **47 %** | 0,506 |

> ⚠️ **Contre-intuitif, et je le consigne tel quel** : l'agent avec héritage a reçu
> **moins d'aide** (sevrage 63 % contre 48,7 %) et atteint une **maîtrise inférieure**
> (38 % contre 47 %).
>
> C'est cohérent avec le mécanisme : l'héritage retire de l'aide *par anticipation*, en
> pariant que l'agent saura faire. Si le pari est faux, l'agent est sevré trop tôt et
> apprend **moins bien** — exactement le risque que la §5 du chantier v41.2 avait identifié
> pour l'option « abaisser le seuil de sevrage » (*« sevrer trop tôt un agent qui n'a rien
> acquis »*).

**n = 1 paire, 10 jours, une seule graine.** Ce n'est pas un verdict — c'est un signal
dont le **sens** est défavorable et qui doit être mesuré sérieusement avant toute
revendication. Il renforce la décision du §6.9 : **conservé, non revendiqué, rien dans les
README**.

### 9.2 Ce que la campagne établit définitivement

| Question | Réponse |
|---|---|
| L'héritage change-t-il le niveau atteint en 300 j ? | **Δ +0,00 sur 10 paires** — mais 9 paires sur 10 sans promotion, donc ablation vide |
| L'ablation fonctionne-t-elle ? | ✅ oui, vérifié sur g77 |
| Le sevrage v41.3 fonctionne-t-il en population ? | ✅ **autonomie 26,1 % sur 20 runs** (v41.2 : 0 %) |
| L'héritage aide-t-il après promotion ? | ❓ **une paire, signal défavorable** (maîtrise 38 % vs 47 %) |
| Faut-il une campagne plus longue ? | ✅ **≥ 1000 jours** — la promotion médiane arrive vers j290-477 |

---

## 10. 🏁 LA COMPARAISON APPARIÉE 2000 JOURS — l'héritage accélère la 2ᵉ promotion de 3,1×

Campagne décisive : **mêmes 4 graines, 2000 jours, héritage ON vs `--sans-heritage`**.
Contrairement à la campagne 300 jours (§6.8), les promotions ont ici le temps d'arriver —
la comparaison n'est donc plus vide.

**L'ablation est propre** : côté témoin, **0 ligne** d'héritage non nul sur tout le run,
alors que la parenté est bien calculée (65 % affichée). Le drapeau coupe exactement ce
qu'il doit couper, et rien d'autre.

### 10.1 g44 — le seul agent qui franchit des paliers

| | 1ʳᵉ promotion | 2ᵉ promotion | Écart entre les deux |
|---|---|---|---|
| **Héritage ACTIF** | jour **477** | jour **493** | **16 jours** |
| **Témoin (sans)** | jour **477** | jour **527** | **50 jours** |

> ✅ **La 1ʳᵉ promotion est identique au jour près** (477, maturité 40 %, mêmes facteurs
> `régularité 60 % × 20 épisodes × autonomie 67 %`). C'est **attendu et c'est une
> validation** : avant toute promotion la parenté vaut 0, donc les deux codes sont
> strictement identiques. Voir un écart ici aurait signalé une fuite du drapeau.
>
> ✅ **La 2ᵉ promotion arrive 3,1× plus vite avec l'héritage** — 16 jours contre 50.
> C'est le premier effet **apparié** et **positif** mesuré pour cette mécanique.

Maturité maximale sur les 45 premiers jours du niveau 2, même fenêtre de jours :

| | Maturité max |
|---|---|
| Héritage actif | **0,469** |
| Témoin | 0,400 |

### 10.2 Ce que cela corrige de la lecture du §9

Le §9 (paire g77, campagne 300 j) donnait un signal **défavorable** : maîtrise 38 % contre
47 % pour le témoin. Cette lecture portait sur **10 jours** après promotion et **une seule
paire** — j'avais écrit qu'elle n'était pas concluante, elle ne l'était effectivement pas.

Sur 50 jours et avec le résultat qui compte (la promotion suivante), le signe s'inverse :
l'héritage **accélère**. Les deux mesures ne se contredisent pas vraiment — l'héritage
sèvre plus tôt, donc la maîtrise instantanée peut baisser, mais la **maturité** (qui
inclut l'autonomie) monte plus vite et franchit le seuil plus tôt.

### 10.3 Ce que cela ne change PAS

| Fait | Statut |
|---|---|
| 3 graines sur 4 (g11, g22, g33) restent au **niveau 1** sur 2000 jours | ⚠️ inchangé — l'héritage n'y est **jamais activé** (0,0 pt) |
| Le blocage initial | ⚠️ **non résolu** — l'héritage accélère, il ne débloque pas (§6.2, §6.7) |
| n = **1 graine** pour l'effet mesuré | ⚠️ g44 est le seul à franchir des paliers |

> **Le résultat est positif mais repose sur une seule graine.** Il ne peut pas entrer dans
> les README : la règle du dépôt exige une population, et la loterie natale g22 a déjà
> montré ce qu'une graine unique peut faire croire.

### 10.4 Où l'effet s'arrête — le niveau 3 est un mur des deux côtés

Comparaison sur **fenêtre égale** (490 premiers jours sur `Empty-8x8`, les deux runs
n'étant pas au même point du cursus au même jour calendaire) :

| | Maturité max | Maîtrise max | Jours au-dessus de 0,40 |
|---|---|---|---|
| Héritage actif | 0,469 | 40 % | **1** |
| Témoin | 0,400 | 50 % | **1** |

**Aucune 3ᵉ promotion d'aucun côté.** L'héritage donne une avance au démarrage du palier
(maturité 0,469 contre 0,400), mais elle s'épuise en ~20 épisodes et ne suffit pas à
franchir `Empty-8x8`.

> 🎯 **La portée de l'effet est donc précisément bornée** : l'héritage réduit le **délai
> entre deux promotions** quand l'agent est capable des deux (16 j contre 50 j), et
> **rien de plus**. Il n'ouvre aucun palier que l'agent ne pouvait pas franchir.
>
> C'est cohérent avec sa nature : il transfère de l'**autonomie**, pas de la
> **compétence**. Un agent qui ne sait pas résoudre la carte reste un agent qui ne sait
> pas résoudre la carte — seule l'aide qu'on lui retire change.

### 10.5 Convergence à mi-parcours (j~1020, les deux campagnes)

| Graine | Avec héritage | Sans héritage |
|---|---|---|
| g11 | niveau 1, 0 promo | niveau 1, 0 promo |
| g22 | niveau 1, 0 promo | niveau 1, 0 promo |
| g33 | niveau 1, 0 promo | niveau 1, 0 promo |
| g44 | **niveau 3**, 2 promo | **niveau 3**, 2 promo |

**Le niveau atteint est identique des deux côtés sur les 4 graines.** Seul le *délai*
diffère (g44 : 2ᵉ promotion 3,1× plus rapide).

---

## 11. 💰 Le coût du décalage, chiffré — g11 a perdu ses deux promotions

Le §7 établissait que la maturité multiplie la maîtrise du jour par l'autonomie de la
veille. Reste à savoir **ce que ça a coûté**. Rejeu du critère sur les logs, en
remplaçant l'autonomie lue par celle qui serait cohérente avec la maîtrise du jour même
(script `docs/recherche/scripts/cout_decalage_maturite.py`) :

| Run | Jours | Promotions réelles | Si synchrone | **Manquées** |
|---|---|---|---|---|
| **g11** (héritage) | 2000 | **0** | **2** | **2** |
| g22 (héritage) | 2000 | 0 | 0 | 0 |
| g33 (héritage) | 2000 | 0 | 0 | 0 |
| g44 (héritage) | 2000 | 2 | 3 | **1** |
| **g11** (témoin) | 1528 | **0** | **2** | **2** |
| g22 (témoin) | 1531 | 0 | 0 | 0 |
| g33 (témoin) | 1542 | 0 | 0 | 0 |
| g44 (témoin) | 1531 | 2 | 2 | 0 |

> ⚠️ **Borne SUPÉRIEURE** : une promotion plus tôt vide la fenêtre et change toute la
> suite du run. Le chiffre dit « combien de fois le critère a refusé un agent qui
> remplissait la condition », pas « combien de niveaux il aurait atteint ».

### 11.1 Ce que ça sépare

**g11 n'était pas bloqué par un mur de compétence.** Il a rempli la condition de promotion
**deux fois**, des deux côtés de l'ablation, et a été refusé les deux fois. Son « blocage
au niveau 1 sur 2000 jours » est un artefact du critère.

**g22 et g33 le sont réellement** : zéro promotion même avec le critère corrigé, des deux
côtés. Ils plafonnent à 55 % de maîtrise, sous le seuil, et aucune correction d'index n'y
changera rien.

> 🎯 **Le « mur du niveau 1 » recouvrait donc DEUX phénomènes distincts** que rien ne
> distinguait jusqu'ici : un défaut de mesure (g11) et une vraie limite d'apprentissage
> (g22, g33). Sur 4 graines, **1 sur 4** relevait du premier.
>
> Cela ne dit rien encore des 10 graines de la campagne v41 ni des 2000 jours × 10 du
> blocage historique — mais cela impose de **rejouer cette mesure dessus avant** d'attribuer
> le blocage à la cognition.

### 11.2 Le correctif reste NON appliqué

Le §7.4 posait trois options. Ce chiffrage renforce la 2ᵉ (**évaluer la promotion avant la
mise à jour de la fenêtre**) : elle aligne les deux termes sans inventer une autonomie non
vécue, et le coût mesuré du statu quo est de **2 promotions sur une graine sur quatre**.

Mais cela modifie le **critère de promotion** du projet — donc arbitrage utilisateur.

---

## 12. 🏁 VERDICT FINAL — comparaison appariée complète, 8 × 2000 jours

| Graine | Variante | Niveau | Promotions | Jours promo | Maturité max | Maîtrise max | Héritage moy |
|---|---|---|---|---|---|---|---|
| g11 | héritage | 1 | 0 | — | 0,397 | 65 % | **0,0 pt** |
| g11 | témoin | 1 | 0 | — | 0,397 | 65 % | 0,0 pt |
| g22 | héritage | 1 | 0 | — | 0,278 | 55 % | **0,0 pt** |
| g22 | témoin | 1 | 0 | — | 0,278 | 55 % | 0,0 pt |
| g33 | héritage | 1 | 0 | — | 0,306 | 55 % | **0,0 pt** |
| g33 | témoin | 1 | 0 | — | 0,306 | 55 % | 0,0 pt |
| **g44** | **héritage** | **3** | **2** | **477, 493** | **0,469** | 65 % | **0,1 pt** |
| **g44** | **témoin** | **3** | **2** | **477, 527** | 0,400 | 60 % | 0,0 pt |

**Δ niveau = +0,00 · Δ promotions = +0,00 · aucune paire discordante.**

### 12.1 Trois graines sur quatre sont BIT-IDENTIQUES

g11, g22, g33 : maturité, maîtrise, autonomie et sevrage moyens **rigoureusement égaux**
des deux côtés, au dixième près. Ce n'est pas une coïncidence — c'est la démonstration
que **l'héritage n'y a jamais été activé** (`her.moy = 0,0 pt`, aucune promotion, donc
parenté nulle en permanence).

> ✅ C'est aussi la **validation de l'ablation** : un drapeau qui laisse trois runs
> strictement inchangés et n'altère que celui où la mécanique s'active fait exactement ce
> qu'on attend de lui. Aucune fuite.

### 12.2 Le seul effet réel, sur la seule graine où la mécanique existe

| g44 | 1ʳᵉ promo | 2ᵉ promo | **Délai** | Maturité max |
|---|---|---|---|---|
| Héritage | j477 | **j493** | **16 j** | **0,469** |
| Témoin | j477 | j527 | 50 j | 0,400 |

**3,1× plus rapide entre les deux paliers.** Même jour pour la première (attendu :
parenté nulle avant toute promotion, donc codes identiques).

### 12.3 Le bilan, sans ambiguïté

| Question | Réponse mesurée |
|---|---|
| L'héritage change-t-il le **niveau atteint** ? | ❌ **non** — Δ +0,00 sur 4 paires |
| Change-t-il le **nombre de promotions** ? | ❌ **non** — Δ +0,00 |
| Change-t-il le **délai** entre deux paliers franchissables ? | ✅ **oui — 3,1×** (n = 1) |
| Débloque-t-il un agent bloqué ? | ❌ **non** — jamais activé sur 3 graines /4 |
| L'ablation est-elle propre ? | ✅ **oui** — 3 runs bit-identiques |

### 12.4 📌 DÉCISION FINALE

**L'héritage est CONSERVÉ, INACTIF PAR DÉFAUT n'est PAS retenu — il reste actif.**
Motifs :

1. Il ne **dégrade rien** : Δ niveau et Δ promotions strictement nuls, et il est
   littéralement inerte tant qu'aucune promotion n'a lieu.
2. Son seul effet mesuré est **favorable** (3,1× sur le délai).
3. Son coût est nul : aucune constante posée, tout est dérivé de grandeurs déjà mesurées.

**Mais il n'est pas revendiqué et n'entre pas dans les README** : l'effet repose sur
**une graine**, et le dépôt a déjà payé le prix d'une conclusion tirée d'une graine unique
(loterie natale g22).

⚠️ **Ce chantier n'a pas traité le problème du projet.** Le blocage tient à deux causes
distinctes, séparées au §11 et dont aucune ne relève de l'héritage :

| Cause | Graines | Piste |
|---|---|---|
| **Défaut de mesure** — le critère refuse un agent qui remplit la condition | g11 (1/4) | §7 — correctif en attente d'arbitrage |
| **Mur d'apprentissage réel** — plafonne à 55 %, sous le seuil | g22, g33 (2/4) | P17 — le cursus comme distribution |
