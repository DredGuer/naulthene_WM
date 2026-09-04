# LA VOIX LIBRE À 200 JOURS — l'effet se confirme, et le témoin s'effondre

**Date** : 2026-09-04 · **Statut** : ✅ **JUGE 2 PASSÉ, JUGE 0 ÉCHOUE (et c'est le résultat)** ·
**n = 20 graines appariées × 2 bras × 200 jours** · banc 300 épisodes, instrument v41.50.

> **Protocole écrit AVANT le lancement** (`brains/03092026_brasA_200j/LISEZ_MOI.md`, 03/09).
> Suite de [`VOIX_LIBRE_03092026`](VOIX_LIBRE_03092026_le_premier_levier_du_depot.md), qui
> avait mesuré **+12,43 pt** sur une politique **non asymptotique**.
> **Lignée reprise**, pas rejouée : ce n'est **pas** une réplication indépendante.

---

## 1. La question posée

À j100, l'entropie descendait encore dans 12/15 graines. Le +12,43 pt valait donc pour
« la netteté à H ≈ 1,5 », pas pour l'effet terminal. **Que vaut le levier une fois la
politique stabilisée ?**

Trois issues avaient été écrites d'avance : l'effet grandit · stagne · se réduit.
**C'est une quatrième qui s'est produite.**

## 2. Le résultat central

| | j100 | **j200** |
|---|---|---|
| LIBRE | 24,17 % | **25,75 %** |
| TÉMOIN | 11,73 % | **6,25 %** |
| **δ apparié** | +12,43 pt | **+19,50 pt** |
| **`t`** | +5,21 | **+9,581** |
| Favorables | 18/20 | **19/20** |

L'écart **augmente de 57 %**. Mais la décomposition lignée par lignée dit *pourquoi*, et ce
n'est pas ce qu'on aurait supposé :

| Bras | Évolution j100 → j200 | `t` | Régressent |
|---|---|---|---|
| **LIBRE** | **+1,58 pt** | +0,670 (**NS**) | 8/20 |
| **TÉMOIN** | **−5,48 pt** | **−3,049** ✅ | **17/20** |

> **Le bras libre ne progresse pas significativement. C'est le témoin qui se dégrade.**

Deux effondrements spectaculaires : `g144` 27,00 % → **0,33 %**, `g166` 23,67 % → **2,00 %**.
Le régime normal (avec renormalisation) ne stagne pas sur 100 jours de plus : **il perd ce
qu'il avait acquis**.

⚠️ **C'est la lecture qui compte** : `gain_c1` ne bride pas seulement l'apprentissage, il
**laisse la compétence se déliter**. Retirer la renormalisation ne fait pas tant *monter*
l'agent qu'il ne l'**empêche de redescendre**.

## 3. Les quatre juges

| Juge | Critère | Mesuré | Verdict |
|---|---|---|---|
| **0. Asymptote** | \|pente\| < 0,002/j sur ≥ 15/20 | pente **+0,00736/j**, **3/20** plats | ❌ **ÉCHOUE** |
| **1. Netteté** | médiane LIBRE < 1,35 | **1,488** (témoin 1,718) · δ = −0,227 (`t` = −3,77) | 🟡 absolu manqué, apparié significatif |
| **2. Succès** | δ significatif | **+19,50 pt** · `t` = **+9,581** · 19/20 | ✅ **PASSE** |
| **3. Directivité** | médiane < 10× | **13,00×** (témoin 19,67×) · δ = **−7,02×** (`t` = −6,80) | 🟡 absolu manqué, apparié très significatif |

### Le juge 0 — la découverte, et elle est structurelle

L'asymptote **n'est pas atteinte**, et la pente s'est **inversée** : elle descendait
(−0,00745/j à j100), elle **remonte** (+0,00736/j à j200).

**Les 20 cerveaux LIBRE sur 20** passent par un minimum d'entropie — entre **j110 et j192**,
à des valeurs très basses (0,220 à 1,317) — puis **remontent** de **+0,26 à +1,22**.

| | valeur |
|---|---|
| Cerveaux qui rebondissent (> 0,05) | **20/20** |
| Minimum médian | ~j135 |
| Remontée médiane | ≈ +0,67 |

**La politique ne converge pas vers la netteté : elle sur-durcit, puis se relâche.**

Et le relâchement est **sain** — le succès de LIBRE ne baisse pas pendant ce temps (+1,58 pt,
NS). Ce n'est donc **pas** le mode d'échec « confiant dans l'erreur » (λ=0,9, 01/09) que le
protocole redoutait ; cela ressemble à un cycle exploitation → réexploration.

⚠️ **Conséquence de méthode** : les juges 1 à 3 mesurent l'effet **à j200**, pas l'effet
terminal. Une campagne à 300-400 jours serait nécessaire pour trancher — mais le rebond étant
unanime, il est possible qu'**il n'existe pas d'asymptote** au sens attendu.

## 4. Les huit vérifications — toutes passées

| # | Vérification | Résultat |
|---|---|---|
| 1 | **Témoin aléatoire** | **5,67 % sur 40/40** — exact, l'invariant du dépôt |
| 2 | Saturation de budget (≥ 27,0×) | **0** |
| 3 | Zéro victoire | LIBRE **0** · TÉMOIN 1 (g155) |
| 4 | **Sans les 4 extrêmes** | δ = **+16,71 pt**, `t` = **+8,541** (n=16) ✅ |
| 5 | Sans témoins au plancher (< 5 %) | δ = **+12,70 pt**, `t` = **+5,323** (n=9) ✅ |
| 6 | Mode d'échec v37.0 (C1 écrase C2) | C1 = 4,952 · ratio 0,505 · **0/20** sous 0,3 |
| 7 | Régime sérialisé | LIBRE `True` 20/20 · TÉMOIN `False` 20/20 |
| 8 | Drapeau / contamination | 20/20 LIBRE · **0/20** témoins contaminés |

La vérification **n°5** est la plus exigeante : en retirant les 11 témoins effondrés sous 5 %,
il ne reste que 9 paires — et l'effet **tient toujours** (`t` = +5,32). L'écart n'est donc pas
un artefact de l'effondrement du témoin.

**L'amplitude C1 s'est stabilisée** : 4,526 (j100) → **4,952** (j200), soit +9 % en 100 jours
contre ×3,7 sur les 100 premiers. Pas d'emballement — le mode d'échec v37.0 ne revient pas.

## 5. Ce que ça ferme, ce que ça laisse ouvert

**Fermé** :
- Le levier **n'était pas un artefact de politique immature**. Il se renforce (+12,43 → +19,50 pt) et survit à toutes les contre-épreuves, y compris le retrait des extrêmes.
- L'hypothèse « l'effet va s'épuiser en durcissant » (« confiant dans l'erreur ») : **réfutée**, LIBRE ne régresse pas.

**Ouvert** :
1. ⚠️ **Il n'y a peut-être pas d'asymptote.** 20/20 rebonds : le durcissement n'est pas monotone. Une campagne 300-400 j dirait si le cycle se répète ou s'amortit.
2. 🔴 **Le mécanisme de l'effondrement du témoin est INCONNU.** C'est le fait le plus important de cette campagne et il n'est **pas expliqué**. Pourquoi un agent sous `gain_c1` perd-il 5,48 pt entre j100 et j200 ? Hypothèses non testées : érosion nocturne non compensée, dérive de la référence de choc, `f` qui monte et resserre le gain. **À instruire avant toute autre chose.**
3. ⚠️ **Banc forcé** : ne prouve **rien** sur le cursus. Le passage en cursus complet reste l'étape suivante et obligatoire.
4. 🔴 **L'ablation « C2 coupé = 0,0 pt » reste confondue** et non refaite.

## 6. Ce qu'il faut faire ensuite

| # | Chantier | Pourquoi |
|---|---|---|
| 1 | **Cursus complet, sans `--env-force`** | le juge de paix : le gain permet-il de franchir le mur du niveau 5 ? |
| 2 | **Instruire l'effondrement du témoin** | fait majeur, mécanisme inconnu — et il touche le régime **par défaut** du projet |
| 3 | Refaire l'ablation C2 sous régime libre | l'un des résultats les plus cités du dépôt est confondu |
| 4 | Bras C (C2 seul) | après 3 |

⚠️ **Les README ne sont toujours pas modifiés** : règle de mesure §6, un banc forcé ne prouve
rien sur le cursus. Aucune revendication publique avant l'étape 1.

## 7. Protocole (reproductible)

```bash
zsh brains/03092026_brasA_200j/lancer.sh   # 40 runs, reprise j100 -> j200, ~4 h
zsh brains/03092026_brasA_200j/banc.sh     # 40 bancs x 300 episodes, ~9 h
```

Agrégat machine : `brains/03092026_brasA_200j/agregat.json` (20 paires, les 4 juges, les
8 vérifications, l'évolution intra-lignée).

**Limite structurelle** : lignée **reprise** depuis j100, donc les deux points ne sont pas
indépendants. Mesurer l'effet du temps supplémentaire était l'objectif ; répliquer le
+12,43 pt sur une population neuve reste à faire.
