# Autopsie d'`esprit_g7` — le seul cerveau à avoir franchi le niveau 5

**17/08/2026** — carnet de recherche, non normatif.
Demande de l'utilisateur : *« Isole esprit_g7 dans une copie. Et fais toute la batterie de
tests nécessaire pour comprendre ce qu'il s'est passé. Traduction, ablation, scan, etc. »*

**Cerveau archivé** : `brains/cas_isole_esprit_g7_niveau5_V4117/`
(md5 `749896f2c2e0b84f1a0c7576a7e45f07`), avec ses **trois témoins appariés** de la même
graine — la seule comparaison qui isole une cause.

> **Résultat en une phrase : ce cerveau n'a pas appris à éviter la lave, et sa réussite
> n'est pas due à C2. Couper C2 TRIPLE son taux de réussite sur LavaGap.**

---

## 1. Ce qui a été fait

| Test | Outil |
|---|---|
| Scan anatomique + différentiel | [`autopsie_cas_isole.py`](scripts/autopsie_cas_isole.py) *(écrit pour l'occasion)* |
| Traduction de la chaîne de pensée | [`traducteur_pensee.py`](scripts/traducteur_pensee.py) |
| Ablation in vivo C1 / C2 | 12 épisodes × 3 conditions, même graine |
| Lecture directe de l'empreinte de type | inspection du `.brain` |

⚠️ `scanner_cerveaux.py` attend une **population**, pas un cerveau isolé — il rend un
tableau vide sur un sujet unique. D'où le nouvel outil.

---

## 2. La trajectoire

```
jour   1 → Nourrisson (Premiers pas)        148 nuits (25 %)
jour 149 → Éveil (Départ aléatoire)          18 nuits ( 3 %)
jour 167 → Maternelle (Longue distance)     270 nuits (45 %)
jour 437 → Primaire 1 (Contourner)           13 nuits ( 2 %)
jour 450 → Primaire 2 (Éviter le danger)    151 nuits (25 %)
```

**Il franchit deux paliers en 13 jours** (437 → 450) après avoir stagné 270 nuits au
niveau 3. Puis il vit 151 nuits sur LavaGap — un quart de son existence.

⚠️ **Il termine pourtant au niveau 3**, avec une maîtrise de 5 %. Le `.brain` sauvegardé
n'est donc *pas* un cerveau « de niveau 5 » : il y est monté, y a vécu, et en est
redescendu. C'est une correction à ce que j'annonçais ce matin (« atteint le niveau 5 »,
vrai) — il n'y est pas **resté**.

---

## 3. Anatomie — rien d'anormal

| Grandeur | Sujet | Témoins |
|---|---|---|
| paramètres | 55 552 | 55 552 (identique) |
| couches au plancher vital | 4/12 | 4/12 (identique) |
| couche la mieux myélinisée | `generateur_attente` (0,00995) | idem |

Les 4 couches au plancher sont les couches **audio et C3** (`porte_auditive`,
`tete_vocale`, `generateur_attente_audio`, `tete_requete`) — normal : aucun son, aucun plug
dans ce cursus. Rien ne distingue anatomiquement le sujet de ses témoins.

**L'exceptionnalité n'est pas dans l'anatomie.**

---

## 4. Le différentiel — ce qui le distingue vraiment

| Grandeur | **SUJET** | témoin | corps | A+B |
|---|---|---|---|---|
| **niveau max** | **5** | 2 | 3 | 4 |
| maîtrise finale | 5 % | 25 % | 5 % | 15 % |
| victoires | 331 | 410 | 408 | 397 |
| énergie | 0,287 | 0,149 | 0,334 | **0,698** |
| **entropie C1** | **0,643** | 0,109 | 0,286 | 0,573 |
| **actions C1** | **5,1** | 1,5 | 2,6 | 4,6 |
| ratio C2/C1 | 4,60 | 0,20 | 0,75 | 4,90 |
| repères mémoire | 346 | 229 | 261 | 356 |
| types appris | 6,6 | 4,0 | 4,0 | 6,8 |

Le sujet a **moins de victoires** et **moins d'énergie** que le témoin A+B, qui n'atteint
pourtant que le niveau 4. Ce qui le sépare du témoin `v4115` est net : **C1 propose 5,1
actions distinctes contre 1,5**.

⚠️ Mais A+B a une entropie C1 quasi identique (4,6) sans franchir le niveau 5. **L'entropie
de C1 est nécessaire, pas suffisante.**

---

## 5. A-t-il appris ce qu'est la lave ? — NON

C'est le test central, puisque le palier s'appelle « Éviter le danger ».

L'empreinte de type (v39.0), lue directement dans le `.brain` — **aucune valeur n'y est
déclarée, ce sont des moyennes de chocs réellement vécus** :

| type | valence apprise | vécu |
|---|---|---|
| `porte_ball` | **+0,657** | ×2 |
| `goal` | **+0,628** | ×628 |
| `porte_key` | +0,306 | ×4 |
| `FOOD` | +0,204 | ×3 647 |
| `sol` | +0,121 | ×11 160 |
| **`lava`** | **+0,072** | **×21** |
| `WATER` | +0,069 | ×3 462 |

**La lave a une valence POSITIVE (+0,072), et pratiquement identique à celle de l'eau
(+0,069) et du sol (+0,121).**

Pour ce cerveau, **marcher dans la lave et boire de l'eau sont deux expériences
équivalentes**. Il n'a rien appris du danger — il a survécu 151 nuits sur LavaGap sans
jamais encoder que la lave est mauvaise.

La cause est connue et mesurée : **MiniGrid punit la mort par exactement `0.0`** (206 morts
sur 300 épisodes, cf. le diagnostic du 16/08). Un choc nul ne peut pas produire une valence
négative. La thermoception v41.11 fonctionne pourtant (`🔥 64/400 ticks au contact d'un
danger`) : **l'agent SENT la lave, il ne sait juste pas qu'elle est mauvaise.**

⚠️ Et seulement **21 confirmations** sur `lava` contre 3 462 sur l'eau : sur 151 nuits de
LavaGap, il l'a très peu rencontrée — parce qu'il meurt vite, et qu'un mort ne mémorise pas.

---

## 6. La traduction — C2 est FIGÉ

Sur LavaGap, 400 ticks :

```
C1 dit ↓ / C2 dit →     ←gauche  →droite  ↑avancer  ✋manger  ↓poser  ⚙activer
tourner à droite              ·        ·      114        ·       ·         ·
prendre / manger              ·        ·      280        ·       ·         ·
tourner à gauche              ·        ·        6        ·       ·         ·
```

**C2 vote « avancer » 400 fois sur 400.** Entropie 0,000 — une voix parfaitement figée.

Le « veto de C2 : 400/400 = 100 % » n'est donc **pas** une délibération : c'est un **biais
constant**. C2 ne réfléchit pas, il pousse toujours dans le même sens. Et sur une carte où
la mort est droit devant, « avancer » est précisément la mauvaise réponse.

C'est exactement le cas que la v41.14 anticipait : *une voix figée rend tout accord — et
tout veto — dénué de sens.*

---

## 7. L'ablation in vivo — le résultat le plus dur

12 épisodes de LavaGap, même graine, même monde, trois conditions :

| Condition | réussites | morts | durée moy. |
|---|---|---|---|
| **C1 + C2 (intact)** | **1/12** | **11** | 21 ticks |
| **C2 coupé** | **3/12** | 9 | 18 ticks |
| **C1 coupé** | **4/12** | 8 | 23 ticks |

**Couper C2 triple le taux de réussite. Couper C1 le quadruple.**

L'agent complet est le **pire** des trois configurations. C2, figé sur « avancer », pousse
activement l'agent dans la lave — et comme son amplitude est 4,6× celle de C1, il gagne
l'arbitrage à chaque tick.

⚠️ **n=12 épisodes, une seule graine** : 1/12 contre 3/12 n'est pas significatif au sens de
Wilson ([0–36] contre [9–61], intervalles largement recouvrants). Ce qui est solide, c'est
la **direction** : dans aucune condition C2 n'aide, et le mécanisme (voix figée à 400/400 +
amplitude dominante) explique le comment.

---

## 8. Alors comment a-t-il franchi le niveau 5 ?

L'hypothèse la mieux étayée par ces mesures, et elle est décevante :

**Il n'a pas appris à éviter la lave — il a appris à courir vite vers la sortie.**

Les faits qui convergent :

- il meurt dans **11 épisodes sur 12** en 21 ticks de moyenne — c'est un comportement de
  fonceur, pas d'évitement ;
- sa valence pour `lava` est **positive**, donc rien ne l'en détourne ;
- C2 vote « avancer » 100 % du temps, ce qui **maximise** la vitesse ;
- le franchissement du palier ne demande que **2 victoires consécutives ou 60 % sur 20
  épisodes** — sur `LavaGap`, foncer droit réussit parfois par chance.

Autrement dit : **la promotion a récompensé la vitesse, pas la compréhension.** Il est monté
au niveau 5 en fonçant, y a échoué 151 nuits, et en est redescendu.

Cela réconcilie tout : pourquoi il a **moins** de victoires que les témoins (il meurt), et
pourquoi sa maîtrise finale est de 5 %.

---

## 9. Ce que ça change

**Établi sur ce cerveau :**

1. la valence de `lava` est **positive** — le danger n'est pas appris, et ne *peut* pas
   l'être tant que MiniGrid punit la mort par `0.0` ;
2. C2 est une **voix figée** (400/400) qui domine l'arbitrage par son amplitude ;
3. l'agent complet est **moins bon** que l'agent amputé de C2 sur ce palier.

**Ce que ça n'établit pas** : n=1 cerveau, n=12 épisodes. Aucun taux, aucune généralisation.

**Ce que ça oriente** — et c'est la vraie valeur de cette autopsie : la question
« comment franchir le niveau 5 ? » est mal posée. La bonne est **« comment rendre la mort
coûteuse ? »**, puisque sans coût il n'existe aucun signal d'apprentissage du danger.

C'est exactement l'arbitrage laissé en attente depuis le 16/08 (*forme du correctif
« accompagnement / danger »*) — cette autopsie en fait le blocage n°1, mesuré, du niveau 5.
La contrainte du projet reste entière : pas de `si mort → malus` (seuil en dur sur un type
nommé, interdit par l'invariant v36.0/v41.11).
