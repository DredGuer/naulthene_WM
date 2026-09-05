# L'ATROPHIE DE C1 — la renormalisation est une boucle de compensation

**Date** : 2026-09-05 · **Statut** : ✅ **MÉCANISME ÉTABLI** · **n = 20 paires, 40 runs,
~59 000 nuits** · coût : **zéro run** (relecture des logs de `04092026_cursus_complet`).

> ⚠️ **Cette mesure RECTIFIE un mot du dossier publié la veille** — voir §2. Le mot
> « effondrement » était faux.

---

## 1. La question posée

Le [dossier du cursus complet](CURSUS_04092026_le_mur_tient_l_hemorragie_cesse.md) laissait
ouverte la question la plus lourde des trois campagnes :

> 🔴 **Pourquoi le témoin s'effondre-t-il ?** 9 cerveaux à maîtrise 0 %, 3 au niveau 1.
> Mécanisme inconnu — c'est le régime **par défaut** du projet.

Hypothèse de travail au lancement : une **voix figée** (`H_C1 → 0`, C1 ne votant plus qu'une
action) détruirait les acquis. Autopsie prévue : trajectoires d'amplitude C1, dérive de
`reference_choc_dopamine`, myéline, chez `g88`/`g111`/`g211` contre les autres.

## 2. 🔴 RECTIFICATION — « effondrement » est un mot faux

**Il n'existe aucune régression de niveau dans cette campagne.**

| Mesure | Résultat |
|---|---|
| Régressions de niveau, 40 runs × ~1477 nuits | **0** |
| `g88` · `g111` · `g211` : niveau max atteint | niveau 1, au jour **3 · 3 · 2** |
| … puis | **1497 jours sans bouger** |

Ces trois cerveaux ne sont pas *retombés* au niveau 1 : ils n'en sont **jamais partis**. Le
compteur `niveau_actuel` ne décroît structurellement jamais (invariant v35.0), donc
« effondré au niveau 1 » ne pouvait signifier que **jamais promu**.

⚠️ **Conséquence sur le juge 2 de la veille** : l'effet de niveau était porté par trois
cerveaux **bloqués de naissance**, pas par une dégénérescence. Cela ne change pas le verdict
(il tombait déjà au retrait des extrêmes), mais **change la nature du phénomène** : il n'y a
pas de « poison qui vide la tête de l'agent ». Le dossier de la veille est corrigé en place.

⚠️ **Corollaire méthodologique** : « le témoin décline » (juge 3, pente de maîtrise −0,416
pt/100j) reste vrai **au sein d'un palier**, mais ne doit jamais être lu comme une perte de
palier. Deux grandeurs différentes.

## 3. Le mécanisme réel — une boucle de compensation

Le vrai phénomène n'est pas propre aux 3 bloqués : il est **général au régime témoin**, et
il est **le plus fort de tout le dépôt**.

| Grandeur (médiane j1-100 → j1400-1500) | TÉMOIN | LIBRE |
|---|---|---|
| **Δ amplitude C1 brute** | **−0,8085** · `t` = **−7,82** · **20/20 en baisse** | +0,6159 · `t` = +2,34 · 8/20 en baisse |
| **Δ `gain_c1`** | **+1,0525** · `t` = **+7,96** | **0,0000** (σ = 0, témoin atteint) |
| `r(ΔC1_brut, Δgain)` | **−0,7546** · `t` = −4,88 ⇒ **compensation serrée** | — |

**C1 s'atrophie chez 20 témoins sur 20**, et `gain_c1` monte d'exactement ce qu'il faut pour
masquer l'atrophie. La renormalisation `clamp(2.1 × f / amplitude_c1, 0.25, 4)` est un
**asservissement** : elle retire toute pression sur C1 pour produire des logits amples,
puisque l'amplitude est reconstituée en aval à chaque tick.

### La voix réellement entendue

| Produit `gain × C1` | début | fin | Δ |
|---|---|---|---|
| **TÉMOIN** | 1,891 | 1,691 | **−0,1998** (`t` = −5,22) |
| **LIBRE** | 3,469 | **4,084** | **+0,6159** (`t` = +2,34) |

Le témoin **maintient** son volume de sortie (−0,2 en 1500 jours) tout en perdant 43 % de son
amplitude brute : la compensation fonctionne, et c'est précisément le problème — **elle rend
l'atrophie invisible au réseau lui-même**.

### L'écart apparié, et il écrase tout ce que le dépôt a mesuré

| Métrique | δ (LIBRE − TÉMOIN) | `t` | favorables |
|---|---|---|---|
| **Amplitude C1 finale** | **+3,2586** | **+16,55** | **20/20** |

Seuil Bonferroni à 3 métriques : 2,86. **`t` = +16,55.**

## 4. L'hypothèse de départ est réfutée

La « voix figée » ne prédit **rien** de ce qu'on lui attribuait :

| | `r(maîtrise, H_C1)` | `t` |
|---|---|---|
| **TÉMOIN** | **−0,6699** | −3,83 |
| **LIBRE** | +0,0160 | +0,07 |

⚠️ Le signe est **l'inverse de l'hypothèse** : chez le témoin, une voix **plus figée** va avec
une **meilleure** maîtrise. Les deux voix les plus figées du dépôt (`H_C1 = 0,0000`, une seule
action distincte) sont `TEMOIN_g11` — **30 % de maîtrise, le meilleur score de la campagne** —
et `LIBRE_g211`. Et l'effet disparaît en régime libre.

Les 3 bloqués ne se distinguent des 17 autres témoins **par rien** :

| | 3 bloqués | 17 autres | δ |
|---|---|---|---|
| `H_C1` final | 0,4915 | 0,5187 | −0,027 |
| actions distinctes C1 | 4,33 | 4,21 | +0,13 |
| `reference_choc` | 0,2253 | 0,2317 | −0,006 |
| **maîtrise finale** | **7,50 %** | 5,88 % | **+1,62** |

Leur maîtrise est **supérieure** à celle des autres témoins (`g111` est à 22,5 % — au niveau 1).
**Il n'y a pas de cohorte pathologique** : il y a un blocage de promotion précoce, sur un
mécanisme d'atrophie qui touche les 20 témoins de la même façon.

## 5. Vérifications passées

| Vérification | Résultat |
|---|---|
| **Témoin atteint** (leçon v41.4) | ✅ `gain ≡ 1,0000` sur 20/20 LIBRE, σ = 0 exactement |
| **Tautologie** (le prédicteur est-il une victoire déguisée ?) | ✅ l'amplitude C1 est une norme de logits, **jamais** dérivée de la récompense |
| **Extrêmes** (le test qui a tué la directivité) | ✅ 20/20 favorables : aucun extrême à retirer |
| **Bonferroni 3 métriques** (`t` > 2,86) | ✅ `t` = +16,55 |
| Fichiers fantômes | ✅ 17 copies Finder, **toutes antérieures** à l'original ⇒ inertes |
| Appariement | ✅ 40 runs, 20 graines × 2 bras ; le 41ᵉ log est `campagne.log` (lanceur) |

## 6. Limites — écrites avant qu'on me les oppose

1. ⚠️ **Corrélationnel sur le lien atrophie → blocage.** Que C1 s'atrophie chez 20/20 témoins
   est une **mesure directe**. Que cette atrophie *cause* le mur du niveau 4 ne l'est pas :
   **LIBRE ne s'atrophie pas et bute au même niveau 4.**
2. ⚠️ **Ce dossier n'explique donc PAS le plafond** — il explique la *différence* entre les
   deux régimes, et pourquoi le témoin est le pire des deux.
3. ⚠️ **Myéline non mesurée** : elle n'est pas dans les bilans de nuit (elle exigerait
   d'ouvrir les 40 `.brain`). Le volet « la couche motrice se fige-t-elle physiquement ? »
   reste ouvert.
4. ⚠️ Médianes sur 100 nuits ; aucune analyse tick à tick.

## 7. Ce que ça ferme, ce que ça laisse ouvert

**Fermé** :
- « Le témoin s'effondre » : **faux**, aucune régression de niveau. Blocage de naissance.
- « Une voix figée détruit les acquis » : **réfuté**, le signe est inversé (`r` = −0,67).
- « Les 3 bloqués forment une cohorte pathologique » : **non**, ils ne diffèrent en rien.

**Ouvert** :
1. 🔴 **L'atrophie est-elle une CAUSE ou un symptôme ?** Elle est réelle à `t` = −7,82 sur
   20/20, mais LIBRE bute au même mur sans elle.
2. 🟡 **La myéline de `tete_motrice`** dans les 40 `.brain` — la seule mesure qui dirait si
   l'atrophie est physique.
3. 🔴 **L'ablation C2 en régime libre** reste le prérequis intact : `c2_coupe` met `force = 0`
   → `gain_c1 = 0,25`, ce qui étranglait C1 **aussi**. En régime libre `gain ≡ 1`, donc
   l'ablation devient **propre pour la première fois**.

---

*24ᵉ explication mesurée. Elle ne réfute pas le plafond : elle réfute le récit qu'on en faisait.*
