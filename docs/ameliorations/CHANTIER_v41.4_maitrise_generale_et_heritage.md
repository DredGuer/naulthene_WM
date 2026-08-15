# Chantier v41.4 — La maîtrise générale et l'héritage de sevrage

> **Statut** : implémenté, campagne 10 graines × 2 variantes en cours (15/08/2026).
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
