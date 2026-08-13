# Revue de code v39 — 13-14 août 2026

> **Nature du document** : carnet de revue, non normatif. Liste les défauts trouvés en
> relisant le code pendant que les campagnes P12/P14 tournaient.
>
> Chaque entrée porte : la **preuve** (mesure ou lecture), l'**impact réel**, et la
> **correction**.
>
> ## ✅ LES CINQ DÉFAUTS SONT CORRIGÉS *(14 août 2026)*
>
> | Défaut | Avant | Après | Vérification |
> |---|---|---|---|
> | **R5** réarmement 2a | jusqu'à **48,7 %** de cartes triviales | **0 %** | 600 réarmements, 4 tailles |
> | **R4** croissance P14 | **92 %** de cartes triviales | **0 %** | 200 croissances |
> | **R1** `_bornes_queue` | lésions décalées de **+3** | index exacts | 5 lésions vérifiées une à une |
> | **R3** paliers 10×10/12×12 | 2 instruments sur 2 en échec | lisibles | `sonde_poids`, `sonde_c1_c2` |
> | **R2** docstring | « 34 dims » périmé | la constante fait foi | — |
>
> Une **assertion exécutable** a été ajoutée dans `_bornes_queue` : toute dimension
> future ajoutée en queue fera désormais **échouer bruyamment** le banc d'ablation au
> lieu de décaler silencieusement les lésions.

---

## Tableau de bord

| # | Défaut | Gravité | Depuis | Impact réel |
|---|---|---|---|---|
| R1 | `_bornes_queue` : tranches décalées | 🔴 **Haute** | v36.0 | Le banc d'ablation coupe **le mauvais sens** |
| R2 | `DIM_VECTEUR_BIO` : docstring périmée | 🟡 Basse | v32.0 | Documentation trompeuse |
| R3 | Niveaux 10×10 / 12×12 enregistrés **hors du noyau** | 🟠 Moyenne | v38 (2a) | Les `.brain` de ces paliers sont **illisibles par les instruments** |
| R4 | **La croissance P14 casse la tâche DoorKey** | 🔴 **Bloquante** | v39-P14 | **92 %** des cartes agrandies sont solvables **sans clé ni porte** |
| R5 | **Le réarmement 2a rend 24 % des cartes triviales** | 🔴 **Haute** | v38 (2a) | Le témoin joue **0 %** de cartes triviales, le continu **24 %** — biais en faveur de la condition testée |

---

## R1 — 🔴 `_bornes_queue` découpe le vecteur bio aux mauvais index

**Fichier** : `src/naulthene/instruments/banc_ablation.py`

### Le défaut

La fonction calcule les tranches **en partant de la fin** du vecteur :

```python
q = DIM_TOUCHER + DIM_CHIMIE + DIM_EXO + DIM_ODORAT_DELTA   # = 18
d = n - q                        # « début de la queue sensorielle »
```

Cela suppose que **la clinotaxie est la dernière tranche du vecteur**. C'était vrai en
v32.0. Ça ne l'est plus depuis :

- **v36.0** — ajout de `DIM_RAPPEL_MARQUANT` (2 dims) en queue ;
- **v39.2** — ajout de `DIM_PRESENCE_AUDITIVE` (1 dim) en queue.

### La preuve (calculée)

| Tranche | Index **réels** (layout v39.2) | Index **calculés** par `_bornes_queue(37)` | Écart |
|---|---|---|---|
| toucher | `16:20` | `19:23` | **+3** |
| odorat | `20:22` | `23:25` | **+3** |
| goût | `22:24` | `25:27` | **+3** |
| exo | `24:32` | `27:35` | **+3** |
| clinotaxie | `32:34` | `35:37` | **+3** |

Et **même avant la v39.2**, avec `n = 36`, le décalage était déjà de **+2** (toucher
calculé à `18:22` au lieu de `16:20`).

### L'impact réel — et il est sérieux

Le banc d'ablation est l'outil qui a produit **le tableau d'ablation sensorielle publié
dans les deux README** :

> *« Couper le toucher coûte −2, −2, −2 : le seul sens démontré nécessaire. »*

Or `toucher_coupe` mettait à zéro les dims `18:22`, c'est-à-dire **2 dims de toucher + 2
dims d'odorat**, en laissant 2 dims de toucher intactes. De même, `odorat_coupe` coupait
en partie le goût, et `clinotaxie` écrasait le **rappel marquant** (dont le neutre est
`[0.5, 0.0]`, pas `0.5`).

⚠️ **Ce que ça ne remet PAS en cause** : la conclusion « le toucher porte la performance »
reste plausible — la lésion touchait bien du toucher, et elle a bien coûté. Mais elle
touchait **aussi autre chose**, donc l'attribution précise (« c'est le toucher, et lui
seul ») n'est pas établie. Les runs d'ablation devront être **refaits** après correction.

### La correction proposée

Ancrer les tranches sur le **début** du vecteur (les 16 premières dims sont stables depuis
la v22.1), jamais sur sa fin :

```python
t0 = 16                       # après jauges(3) + quête(3) + rappel spatial(2) + vocal(8)
c0 = t0 + bs.DIM_TOUCHER
e0 = c0 + bs.DIM_CHIMIE
k0 = e0 + bs.DIM_EXO
r0 = k0 + bs.DIM_ODORAT_DELTA          # rappel marquant
p0 = r0 + DIM_RAPPEL_MARQUANT          # présence auditive
```

Et **ajouter une assertion** : `p0 + DIM_PRESENCE_AUDITIVE == n`. Le contrat est
append-only, donc toute future dimension ajoutée en queue fera crier l'assertion au lieu
de décaler silencieusement toutes les lésions.

> C'est exactement le mode d'échec que `CLAUDE.md` décrit pour le vecteur bio (« une
> insertion au milieu décalerait silencieusement tous les acquis ») — sauf qu'ici
> l'insertion était **en queue**, conforme au contrat, et c'est le **lecteur** qui était
> écrit à l'envers.

---

## R2 — 🟡 La docstring de `obtenir_vecteur_bio` annonce 34 dims

**Fichier** : `src/naulthene/cerveau/noyau.py`

```python
"""Retourne le vecteur de DIM_VECTEUR_BIO=34 dims (3 jauges + 3 quête + 2 rappel
spatial + 8 quête vocale + 4 toucher + 4 chimie + 8 Exo-Sens + 2 clinotaxie)"""
```

La valeur réelle est **37** (v39.2), et l'énumération omet le rappel marquant (v36.0) et
la présence auditive (v39.2). La constante `DIM_VECTEUR_BIO` étant calculée, aucun bug
d'exécution n'en découle — mais c'est précisément ce genre de commentaire périmé qui a
produit R1.

**Correction** : recalculer l'énumération, ou mieux, ne plus écrire le total en dur dans
la docstring.

---

## R3 — 🟠 Les paliers 10×10 et 12×12 n'existent que dans le banc d'essai

**Fichiers** : `experiences/v38/v38_2a_continuite.py` (et par héritage tous les bancs v38/v39)

### Le défaut

MiniGrid ne fournit que **quatre** DoorKey : `5x5`, `6x6`, `8x8`, `16x16`. Le cursus de la
campagne v38 en utilise **six** — les deux manquants (`10x10`, `12x12`) sont enregistrés à
la volée par le banc lui-même :

```python
for _t in (10, 12):
    register(id=f"MiniGrid-DoorKey-{_t}x{_t}-v0", ...)
```

Cet enregistrement vit **dans le banc**, pas dans le noyau. Tout programme qui recharge un
`.brain` sans importer le banc ne connaît donc pas ces environnements.

### La preuve (exécutée)

```
$ python -m naulthene.instruments.sonde_poids /tmp/p14_smoke3.brain
gymnasium.error.NameNotFound: Environment `MiniGrid-DoorKey-12x12` doesn't exist.
$ python -m naulthene.instruments.sonde_c1_c2 /tmp/p14_smoke3.brain
gymnasium.error.NameNotFound: ... (idem)
```

**Deux instruments de diagnostic sur deux échouent** sur un cerveau parfaitement valide,
simplement parce qu'il s'est arrêté sur un palier « maison ».

### L'impact réel

- Les **runs eux-mêmes ne sont pas affectés** : le banc enregistre avant de lancer, donc
  toute la campagne v38/v39 est valide. Ce n'est pas un bug de résultats.
- En revanche, **tout `.brain` sauvegardé sur 10×10 ou 12×12 est inauditable** : ni
  `sonde_poids`, ni `sonde_c1_c2`, ni `irm_cerveau`, ni l'Arène ne peuvent l'ouvrir. Sur la
  campagne 2a, plusieurs cerveaux finissent précisément à ces paliers.
- C'est un **échec silencieux différé** : rien ne prévient au moment du run ; la panne
  n'apparaît que le jour où on veut diagnostiquer, souvent des semaines plus tard.

### La correction proposée

Déplacer l'enregistrement dans le **noyau** (près de `creer_env`), pour qu'il soit effectif
partout où le noyau est importé — bancs, instruments, Cuve, Arène. Trois lignes, et
l'enregistrement reste idempotent (`try/except` déjà en place).

⚠️ **Ne pas se contenter de l'ajouter aux instruments un par un** : ce serait réparer les
symptômes, et le prochain point d'entrée écrit oublierait à nouveau.

---

## R4 — 🔴 BLOQUANT : la croissance rend la tâche DoorKey triviale

**Fichier** : `experiences/v39/v39_p14_croissance.py`, fonction `agrandir_monde`

### Le défaut

Dans `DoorKey`, un mur intérieur sépare la carte en **deux pièces**, reliées par une seule
porte verrouillée. Ce mur ne sépare que parce qu'il **butte sur la bordure extérieure**.

En agrandissant, la bordure recule — mais le mur intérieur, lui, garde sa longueur
d'origine. Il ne touche plus rien : **l'agent le contourne.**

```
AVANT (5×5)          APRÈS croissance (8×8)
  #####                ########
  #.D.#                #.D....#
  #@#.#                #@#...G#     le mur s'arrête ligne 3
  #k#G#                #k#....#     -> on passe par-dessous
  #####                #..#..##     -> la clé et la porte ne servent plus
                       #......#
                       #......#
                       ########
```

### La preuve (exécutée, 200 configurations)

BFS depuis l'agent, **portes traitées comme infranchissables** (elles sont verrouillées) :

```
configurations où le but est atteignable SANS la clé : 185/200  (92 %)
```

40 graines × 5 croissances successives (5→6→8→10→12→16).

### L'impact réel — et pourquoi c'est bloquant

**La campagne P14 en cours mesure une tâche qui n'est plus DoorKey.** L'agent « croissance »
n'a plus besoin de chercher la clé ni d'ouvrir la porte : il marche vers le but. Il
progressera donc probablement *plus vite* que le témoin — pour une raison qui n'a **rien à
voir** avec l'hypothèse testée (« garder sa mémoire aide »).

C'est exactement le piège déjà rencontré en 2a (« continuité naïve ⇒ tâche triviale, trois
états absorbants »), sous une forme nouvelle que le réarmement de tâche ne couvre pas :
le réarmement remet la clé au sol et reverrouille la porte, mais **ne vérifie jamais que la
porte est encore le seul passage**.

> ⚠️ **Sans cette revue, j'aurais interprété un gain P14 comme une victoire du cadre
> développemental.** C'aurait été un faux positif de plus, et un faux positif *séduisant* —
> il allait dans le sens de l'hypothèse.

### La correction proposée

Prolonger le mur intérieur jusqu'à la nouvelle bordure au moment de la croissance : la
séparation en deux pièces est **l'invariant de la tâche**, il doit survivre à
l'agrandissement au même titre que la clé et la porte.

Vérification à ajouter au banc (et à faire échouer bruyamment si elle casse) :

```python
assert not atteignable_sans_porte(env), "la croissance a ouvert un contournement"
```

C'est le même principe que l'assertion proposée en R1 : un invariant qu'on peut tester
mécaniquement ne doit pas rester une intention écrite dans une docstring.

### Conséquence immédiate sur la campagne en cours

**Les runs P14 « croissance » sont à jeter** une fois la campagne finie — ils mesurent une
tâche dégradée. Le banc doit être corrigé, puis la campagne relancée. La campagne **P12
(prior d'empreinte) n'est pas affectée** : elle n'utilise pas la croissance.

---

## R5 — 🔴 Le réarmement de tâche (2a) rend un quart des cartes triviales

**Fichier** : `experiences/v38/v38_2a_continuite.py`, fonction `_rearmer_tache`

> ⚠️ **Ce défaut ne touche pas seulement la v39 : il touche le seul résultat que le
> chantier v38 présente comme solide.**

### Le défaut

`_rearmer_tache` repose le but sur une case libre **« loin de l'agent »** (≥ 50 % de la
distance max). Il vérifie la distance — jamais **de quel côté de la porte** la case se
trouve.

Sur `DoorKey`, l'agent démarre dans la pièce fermée. Si le but est reposé **dans cette même
pièce**, la clé et la porte ne servent plus à rien : l'agent marche jusqu'au but.

### La preuve (exécutée)

BFS depuis l'agent, portes verrouillées traitées comme infranchissables :

| Condition | Cartes solvables **sans la clé** |
|---|---|
| **MiniGrid natif** (le témoin, `reset()` classique) | **0 / 180** — **0 %** |
| **Réarmement 2a** (la condition « continu ») | **86 / 360** — **24 %** |

60 graines × 3 tailles pour le natif ; 30 graines × 3 tailles × 4 réarmements pour 2a.

### L'impact réel

**Le témoin et la condition testée ne jouent pas la même tâche.** Un quart des épisodes du
« continu » sont des `Empty` déguisés en `DoorKey`. La condition testée est donc
**structurellement plus facile** que son témoin — indépendamment de la continuité.

Ce que ça remet en cause, précisément :

| Résultat v38 | Statut après R5 |
|---|---|
| **2a** (continuité) : 3,0 vs 1,5 paliers, p = 0,375 | ⚠️ **biais possible** — une partie du gain peut venir des 24 % de cartes faciles |
| **2b** (le seul résultat « qui tient », p = 0,062) | ⚠️ **construit sur 2a**, donc hérite du biais |
| **g22** (69 victoires, cursus complet) | ⚠️ 65 de ses victoires sont sur `DoorKey-16x16` réarmé — combien étaient triviales ? **inconnu** |
| 2c / 2c-fix / 2c-ter / 2d (résultats **négatifs**) | ✅ **non menacés** — un biais qui *facilite* ne peut pas expliquer une régression |

⚠️ **Je ne conclus pas que 2a est faux.** Le biais est réel et mesuré, son ampleur sur les
résultats ne l'est pas : 24 % des cartes triviales ne veut pas dire 24 % du gain. Mais
l'affirmation *« la continuité rend possible quelque chose »* repose désormais sur une
comparaison dont un terme est plus facile que l'autre, et **cela doit être écrit dans les
documents qui la citent**.

### La correction proposée

Reposer le but **de l'autre côté de la porte**, ou à défaut vérifier explicitement :

```python
# le but doit rester inatteignable sans franchir une porte
if atteignable_sans_porte(env):
    choisir une autre case
```

Puis **rejouer 2a et 2b** avec le réarmement corrigé, sur les mêmes 6 graines, pour mesurer
la part du gain qui survit.

### Ce que cet incident dit de la méthode

Le carnet documente déjà le piège « continuité naïve ⇒ tâche triviale », et 2a a été conçu
*avec* un réarmement précisément pour l'éviter. Le réarmement traitait trois états
absorbants (clé en main, porte ouverte, souvenirs figés) — mais **pas la topologie**.

> On a vérifié que la tâche était toujours *armée*. On n'a jamais vérifié qu'elle était
> toujours *la même tâche*.

C'est le même schéma qu'en R1 : un invariant énoncé dans une docstring, jamais transformé
en assertion exécutable.

---

## Ce que la revue a VÉRIFIÉ et trouvé sain

Pour que le document ne liste pas que du négatif — ces points ont été contrôlés
explicitement :

| Vérification | Résultat |
|---|---|
| `DIM_VECTEUR_BIO` cohérent avec la longueur réelle produite | ✅ 37 == 37 |
| Les 3 appelants de `obtenir_vecteur_bio` | ✅ le 3ᵉ (banc d'ablation) omet `presence_auditive` → défaut 0.0, sûr |
| Greffe 36 → 37 dims sur un vrai `.brain` | ✅ détectée, optimiseur réinitialisé, **3 nuits complètes** |
| Rétrocompatibilité `empreinte_types` absent d'un vieux `.brain` | ✅ `.get(..., {})`, repart vierge sans erreur |
| Le correctif du silence est bit-identique | ✅ écart max mesuré **0.0** |
| `_nourrir_empreinte` n'interprète aucune étiquette | ✅ accumule ce qu'on lui donne, aucun `if type == ...` |
| Le prior ne peut pas écraser le vécu | ✅ poids `n/(n+5)` tend vers 1 sans l'atteindre ; vérifié : −0,50 → +0,36 après vécu contraire |
| `souvenirs_spatiaux` lu ailleurs | ✅ seulement en affichage (Arène), aucun index en dur |

---

---

## ⚠️ R6 — LE CORRECTIF R5 A RENDU LA TÂCHE 50× PLUS DURE *(14 août, mesuré)*

> **La campagne de validation v37→v39 (30 runs) est INEXPLOITABLE.** Elle a été lancée
> avec le réarmement corrigé, et le correctif ne s'est pas contenté de retirer un biais :
> il a changé la difficulté de la tâche d'un ordre de grandeur.

### Le symptôme

Les 30 runs se sont effondrés — **0 à 2 paliers partout**, contre 3 à 5 en v38, et
**zéro repère `goal` dans les 30**. Y compris la condition `base`, qui n'a rien de
neutralisé. Un effondrement uniforme sur toutes les conditions n'est pas un résultat :
c'est une panne.

Comparaison décisive, **même graine, même durée, même banc** :

| Run | Réarmement | Palier atteint en 400 j |
|---|---|---|
| `p12_temoin_g11` | **avant** R5 | **3** |
| `v3739_base_g11` | **après** R5 | **1**, puis 396 jours de stagnation |

### La cause, mesurée

Taux de réussite d'une politique **aléatoire** (300 essais, 250 pas), qui est l'étalon de
difficulté d'un environnement :

| Carte | Avant R5 | Après R5 | Facteur |
|---|---|---|---|
| `DoorKey-5x5` | 16,3 % | 15,0 % | ×1,1 |
| `DoorKey-6x6` | 22,0 % | **4,0 %** | **×5,5** |
| `DoorKey-8x8` | 15,3 % | **0,3 %** | **×51** |

**Le correctif est juste, et c'est précisément pour ça qu'il fait mal.** Avant, une carte
sur quatre laissait aller droit au but ; désormais le parcours est **toujours** clé → porte
→ but. Sur 8×8, une politique aléatoire ne réussit plus qu'une fois sur 300.

### Ce que ça implique

1. **Les 30 runs de validation v37→v39 sont à jeter.** Ils ne mesurent pas les mécaniques :
   ils mesurent un plancher où aucune condition n'a le temps d'exprimer quoi que ce soit.
   Aucun `p` de cette campagne n'a de sens.
2. **La comparaison v38 ↔ v39 est définitivement impossible.** Les deux ne jouent pas la
   même tâche — et c'est irréparable a posteriori.
3. **Le biais R5 était plus structurant qu'estimé.** Je l'avais présenté comme « un quart
   des cartes plus faciles » ; la mesure dit que le retirer divise le taux de réussite
   aléatoire par 51 sur 8×8. Les résultats 2a/2b reposaient donc sur une tâche
   substantiellement plus permissive que ce que j'avais écrit.

### Ce qu'il faut faire *(et ne pas faire)*

❌ **Ne pas revenir en arrière.** Le correctif est correct : c'est la tâche DoorKey
authentique. Annuler R5 reviendrait à préférer une mesure facile à une mesure juste.

✅ **Recalibrer le berceau, pas le cerveau.** L'agent doit pouvoir gagner *parfois*, sinon
il n'y a aucun gradient à apprendre — c'est exactement le diagnostic du blocage d'août
(espérance −1,06, patience deux fois trop courte). Trois leviers, à mesurer :

| Levier | Pourquoi |
|---|---|
| Repartir de `DoorKey-5x5` seul | c'est la seule taille encore à 15 % de réussite aléatoire |
| Allonger la patience | 250 pas ne suffisent plus pour clé → porte → but sur 8×8 |
| Un palier intermédiaire | l'écart 6×6 → 8×8 vaut désormais ×13 en difficulté |

> **La leçon** : corriger un biais **change l'échelle de difficulté**, donc invalide la
> comparabilité avec tout ce qui précède. Il aurait fallu mesurer le taux de réussite
> aléatoire **avant et après** le correctif, avant de lancer 30 runs dessus. C'est la
> même faute que « instrumenter avant de rendre adaptatif », appliquée à un correctif.

---

## 📊 IMPACT SUR LES DONNÉES — ce qui est touché, et à quel point

> Section demandée explicitement. Elle distingue ce qui est **mesuré** de ce qui est
> **estimé**, et refuse d'aller plus loin que les mesures.

### La mesure centrale : le biais croît avec la taille de la carte

Taux de cartes solvables **sans la clé** après réarmement 2a (BFS, porte verrouillée
traitée comme un mur) :

| Carte | Avant correctif | Après correctif |
|---|---|---|
| `DoorKey-5x5` | 7,3 % | **0 %** |
| `DoorKey-6x6` | 26,7 % | **0 %** |
| `DoorKey-8x8` | 36,7 % | **0 %** |
| **`DoorKey-16x16`** | **48,7 %** | **0 %** |
| *MiniGrid natif (le témoin)* | *0 %* | *0 %* |

**Le biais n'est pas uniforme : il double à chaque palier.** Et il est **unilatéral** —
vérifié dans le code, `_rearmer_tache` n'est appelé que par la condition « continu »
(`installer_continuite`) ; le témoin joue un `reset()` natif, donc 0 % partout.

### Ce qui est AFFECTÉ

| Résultat | Ampleur du biais | Verdict |
|---|---|---|
| **2a** — continuité, 3,0 vs 1,5 paliers (p = 0,375) | 7 à 37 % selon le palier atteint | ⚠️ **à refaire** |
| **2b** — « le seul résultat qui tient » (p = 0,062) | idem, construit sur 2a | ⚠️ **à refaire** |
| **g22** — 69 victoires, cursus complet en 239 j | **65 victoires sur `16x16`**, la carte la plus biaisée | ⚠️ **fortement suspect** |
| **P14** — campagne croissance | 92 % | ❌ **arrêtée en cours, jetée** |
| **Tableau d'ablation** des deux README | lésions décalées de +2 (v36) puis +3 (v39) | ⚠️ **à refaire** |

**Le cas g22 mérite d'être dit franchement.** C'était le run exceptionnel du projet — 69
victoires quand le record était 22. Or 65 de ces victoires sont sur `DoorKey-16x16`, dont
**48,7 % des cartes réarmées étaient solvables sans clé**. Une estimation par le taux de
base donnerait ~32 victoires « faciles » sur 65.

⚠️ **Ce chiffre est une ESTIMATION, pas une mesure.** Le taux de base ne dit pas ce qui
s'est réellement passé dans ce run précis : les cartes réellement rencontrées dépendent de
la graine et des positions successives de l'agent. La seule façon de trancher serait de
rejouer g22 avec le réarmement corrigé.

### Ce qui n'est PAS affecté

| Résultat | Pourquoi il tient |
|---|---|
| **2c** parent nourricier (−2 paliers, 0/5) | Un biais qui **facilite** ne peut pas produire une **régression** |
| **2c-fix**, **2c-ter**, **2d** | Idem — tous des résultats négatifs ou nuls |
| **H16** loterie d'amorçage (réfutée) | Analyse rétrospective sur runs W&B, sans réarmement |
| **H18** la promotion efface la mémoire | Mécanisme observé dans le code et par journal, indépendant de la topologie |
| **Les correctifs v37** (0 synapse morte) | Mesurés sur la santé synaptique, pas sur la difficulté de la tâche |
| **La campagne P12** (prior d'empreinte) | N'utilise ni la croissance ni le réarmement modifié — **elle continue** |

### La lecture honnête

Le biais **ne renverse aucune conclusion négative**, et c'est important : tout ce que le
projet a *réfuté* reste réfuté. Ce qu'il fragilise, c'est précisément la seule chose que le
projet présentait comme **acquise** — « la continuité rend possible quelque chose ».

> On ne peut pas dire « 2a est faux ». On doit dire : **2a a été mesuré avec un témoin
> plus difficile que la condition testée, et la comparaison doit être refaite.**

Il reste une raison de penser que l'effet n'est pas entièrement artefactuel : 2a avait
**une graine en recul** (−2) et 2b **aucune**. Un biais qui facilite uniformément
expliquerait mal qu'une graine régresse. Mais c'est un argument, pas une preuve.

---

## Ordre de correction *(appliqué le 14 août 2026)*

| # | Défaut | Pourquoi ce rang |
|---|---|---|
| 1 | **R5** réarmement 2a | Il menace le **seul résultat solide** du projet. Tout ce qui s'empile dessus en dépend |
| 2 | **R4** croissance P14 | Bloquant pour la campagne P14, qui doit être **relancée** ensuite |
| 3 | **R1** `_bornes_queue` | Le banc d'ablation est faux depuis la v36.0 ; les ablations sont à refaire |
| 4 | **R3** enregistrement des paliers | Faible coût, débloque tous les instruments |
| 5 | **R2** docstring | Cosmétique, mais c'est ce type d'écart qui a produit R1 |

**Principe commun aux cinq correctifs** : trois d'entre eux (R1, R4, R5) sont des
invariants qui existaient déjà **en toutes lettres dans une docstring**, sans jamais être
transformés en assertion exécutable. C'est l'argument le plus fort en faveur de **P9**
(les invariants exécutables) : un invariant qu'on peut tester mécaniquement et qu'on
laisse en commentaire finit par être violé sans bruit.

---

## Bilan de la revue

**Cinq défauts trouvés, dont deux graves et un bloquant.** Aucun n'a été corrigé — les
campagnes tournaient, et modifier le code pendant qu'il s'exécute invaliderait les runs.

Ce que la revue a coûté et rapporté :

- **P14 a été arrêtée en cours de route** (R4) : la campagne mesurait une tâche dégradée.
  Sans la revue, un gain aurait été lu comme une victoire du cadre développemental — un
  faux positif *séduisant*, puisqu'il allait dans le sens de l'hypothèse.
- **P12 continue** : elle n'utilise ni la croissance ni le réarmement modifié.
- Le résultat le plus inconfortable est **R5** : il touche 2a/2b, c'est-à-dire la seule
  chose que le projet présente comme acquise.

> Une revue qui ne trouve rien sur 6 000 lignes écrites en deux jours n'aurait pas été une
> bonne nouvelle — elle aurait signifié qu'on ne cherchait pas au bon endroit.

---

*Revue menée le 13-14 août 2026, pendant l'exécution des campagnes P12/P14.*
