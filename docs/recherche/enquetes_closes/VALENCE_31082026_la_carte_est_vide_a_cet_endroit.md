# La valence apprise n'atteint pas la décision — mais la carte est presque vide

**31/08/2026** · `recherche/enquetes_closes/` · **n = 20**, mesure directe

## 1. La question posée

Proposition de l'utilisateur : formaliser le **renforcement secondaire** — la porte
hériterait continûment de la valeur de ce qu'elle débloque, devenant intrinsèquement
attractive parce que corrélée à la survie.

Vérification préalable : **le mécanisme existe-t-il déjà ?** Puis, s'il existe :

> *« Est-ce que cette étiquette stockée dans `empreinte_types` atteint réellement les logits
> de `tete_motrice`, ou reste-t-elle une information décorative ? »*

---

## 2. Verdict

> ✅ **Le renforcement secondaire EXISTE déjà** : `porte_ball` a une valence apprise de
> **+0,8381 ± 0,0728** (19/20 cerveaux), au-dessus du but (+0,6524) et **5× la nourriture**
> (+0,1592). Aucune règle ne le dit — c'est la moyenne des chocs vécus sur une étiquette
> opaque.
> ❌ **Mais elle n'atteint pas la décision** : `r(valence porte, succès) = −0,2930`
> (`t = −1,30`, NS) et `r(valence porte, directivité) = **+0,0521**` (`t = +0,21`) —
> rigoureusement nul.
> 🔴 **Et la cause n'est pas cybernétique, elle est ÉCOLOGIQUE** : la valence des portes
> repose sur **2 à 36 confirmations** contre **8 621** pour la nourriture. La carte n'est pas
> ignorée — elle est **presque vide à cet endroit**.

---

## 3. Ce qui existait déjà, et qu'il fallait vérifier avant de coder

Les trois leviers proposés étaient soit déjà en place, soit fondés sur une prémisse fausse :

| Levier proposé | État réel |
|---|---|
| **A.** La porte comme réservoir de valence future | ✅ **existe** (`empreinte_types`, v39.0) et **fonctionne** — voir §4 |
| **B.** Habituation du besoin comblé | ❌ **prémisse fausse** : la satiété est à **exactement zéro sur 78–100 % des nuits**, toutes campagnes et versions. L'agent n'est jamais repu ; il n'y a pas de rente locale à éteindre. Le cliquet d'habituation existe par ailleurs (`reference_choc_dopamine`) |
| **C.** Basculement C1→C2 selon le déficit viscéral | ❌ **implémenté en v41.2, mesuré, RETIRÉ en v41.16** : les deux voix subissaient le même facteur, la part de C2 restait à **61,3 %** de vigueur 1,00 à 0,30 |

---

## 4. La valence des portes est réelle et stable

| Type | Valence moyenne | Écart-type | n |
|---|---:|---:|---:|
| **`porte_ball`** | **+0,8381** | 0,0728 | 19 |
| **`porte_key`** | **+0,7448** | 0,1866 | 20 |
| `goal` | +0,6524 | 0,0420 | 20 |
| `FOOD` | +0,1592 | 0,0374 | 20 |
| `lava` | +0,0675 | — | 20 |
| `WATER` | +0,0140 | 0,0374 | 20 |

`porte_ball` n'est jamais sous **+0,7093** sur 19 cerveaux. Tous ont appris la même chose,
sans qu'aucune table `objet → valeur` n'existe dans le code.

---

## 5. Le test principal — la valence n'atteint pas la décision

Seuil de Bonferroni (4 tests, n=20) : **|t| ≥ 2,50**.

| Corrélation | `r` | `t` | Verdict |
|---|---:|---:|---|
| valence porte → **succès au banc** | −0,2930 | −1,30 | ✅ non significatif |
| valence porte → **directivité** | **+0,0521** | **+0,21** | ✅ **rigoureusement nul** |
| confirmations portes → succès | +0,4455 | +2,11 | 🟠 échoue Bonferroni |
| valence goal → succès | +0,2702 | +1,19 | ✅ non significatif |

Le second est le plus parlant : la **directivité** est le seul prédicteur significatif du
succès (`r = −0,82`, mesuré le 31/08). La valence apprise n'a **aucun** lien avec elle.

---

## 6. 🔴 L'artefact écarté — et il a failli passer pour une découverte

Un test intermédiaire donnait `r(valence porte, confirmations) = **−0,6294**` (`t = −3,44`,
**significatif**). Lecture tentante : *« les cerveaux qui valorisent le plus les portes sont
ceux qui les rencontrent le moins »*.

**C'est une régression vers la moyenne.** La valence est une **moyenne** : avec 2
confirmations elle est dominée par deux événements extrêmes, avec 36 elle converge.

Test décisif — le motif apparaît-il sur des types **sans rapport** avec les portes ?

| Type | `r`(valence, confirmations) | `t` |
|---|---:|---:|
| `porte_key` | −0,8196 | −6,07 |
| **`sol`** | **−0,7428** | −4,71 |
| **`FOOD`** | **−0,7169** | −4,36 |
| **`WATER`** | −0,5276 | −2,64 |
| `goal` | **+0,8724** | +7,57 |

Le sol et l'eau montrent le **même** motif que les portes. C'est bien un artefact
statistique, pas un fait cognitif. **Écarté.**

`goal` y échappe parce qu'il a **1 081 à 2 534 confirmations** par cerveau : avec autant
d'échantillons la moyenne est stable et croît avec l'expérience.

---

## 7. La vraie cause : la carte est presque vide

| Type | Confirmations moyennes |
|---|---:|
| `sol` | 18 368 |
| `FOOD` | 8 621 |
| `WATER` | 7 981 |
| `goal` | 1 715 |
| **`porte_key`** | **7,8** |
| **`porte_ball`** | **6,1** |

> **Le découplage est réel, mais sa cause n'est pas « le volant moteur ne lit pas la
> carte ». C'est que la carte est presque vide à cet endroit.**

L'agent croise si rarement une porte que sa valence n'a pas le temps de se consolider —
2 à 36 événements contre plusieurs milliers pour la nourriture. Et c'est mécaniquement
attendu : **l'agent plafonne au niveau 4, les portes apparaissent au niveau 7**
(`GoToDoor-6x6`). Les repères existants viennent de rencontres marginales.

---

## 8. Ce que cela ferme, ce que cela laisse

**Fermé** :
- Construire un mécanisme de renforcement secondaire — **il existe et il fonctionne**.
- L'habituation du besoin comblé — la prémisse (un agent repu) est **fausse**.
- Le basculement C1→C2 sur déficit viscéral — implémenté, mesuré, retiré en v41.16.
- « La valence guide la trajectoire » — `r = +0,05` avec la directivité.

**Ouvert, et non mesuré** : la valence des portes se consoliderait-elle si l'agent
atteignait les niveaux où elles abondent ? Question **circulaire en l'état** — il faudrait y
arriver pour le savoir, et c'est précisément ce qui bloque.

---

## 9. Limites

1. **Mesure directe, aucune causalité** (§4 de la règle de mesure). Les corrélations lient
   des grandeurs lues dans 20 `.brain`, sans manipulation.
2. **La valence est lue dans le fichier, pas dans le chemin de décision.** Ce document
   montre qu'elle **ne corrèle pas** avec le comportement ; il ne montre **pas** par quel
   chemin elle échoue à l'influencer. `integrateur_bio` reçoit bien `rappel_marquant`
   (2 dims), mais son poids réel dans les logits n'a pas été mesuré ici.
3. **`door` n'apparaît que sur 5 cerveaux** — trop peu pour être analysé séparément.
4. Le succès au banc provient de la campagne du 31/08, avec ses propres limites (vecteur bio
   figé, `eval()`, un seul environnement).
