# L'ANCRAGE CINÉMATIQUE — l'information est là, C1 ne s'en sert pas

**Date** : 2026-09-02 · **Statut** : ❌ **LES DEUX JUGES SONT NÉGATIFS** · **n = 20 graines
appariées × 2 bras × 100 jours** · banc 150 épisodes, instrument corrigé.

---

## 1. La question posée

L'Étape 0 avait mesuré `P(avancer|avancer)/P(avancer) = 0,9959` — **aucune persistance
motrice**. La brique B (v41.49) injecte en queue du vecteur bio un couple **égocentrique**
(avance ressentie, dérive latérale), lissé sur une demi-vie **dérivée de la carte**.

**Juge n°1, fixé d'avance** : le ratio doit décoller de 0,9959. S'il ne décolle pas,
l'information n'a pas été captée par C1 et la directivité n'est pas interprétable.

## 2. Les chiffres bruts

| Graine | ACTIF | TÉMOIN | δ | stériles ACT | stériles TÉM |
|---|---|---|---|---|---|
| 11 | 1,1565 | 1,0110 | **+0,1455** | 68,0 % | 74,5 % |
| 22 | 1,2820 | 1,2581 | +0,0239 | 61,9 % | 69,9 % |
| 33 | 0,9810 | 1,0002 | −0,0191 | 60,7 % | 62,0 % |
| 44 | 0,9696 | 0,9953 | −0,0257 | 75,3 % | 79,9 % |
| 55 | 1,0961 | 0,9853 | +0,1108 | 61,7 % | 55,2 % |
| 66 | 1,0006 | 1,0013 | −0,0007 | 67,2 % | 67,9 % |
| 77 | 1,0644 | 1,0088 | +0,0556 | 63,4 % | 71,5 % |
| 88 | 1,0636 | 1,0559 | +0,0077 | 64,6 % | 64,5 % |
| 99 | 1,0810 | 1,0137 | +0,0674 | 62,1 % | 57,7 % |
| 111 | 1,0334 | 1,1162 | −0,0828 | 56,9 % | 64,0 % |
| 122 | 1,0279 | 0,9959 | +0,0319 | 62,2 % | 58,7 % |
| 133 | 0,9869 | 1,0894 | −0,1025 | 58,5 % | 64,8 % |
| 144 | 0,9817 | 0,9587 | +0,0230 | 42,5 % | 47,8 % |
| 155 | 0,9887 | 1,0498 | −0,0611 | 84,0 % | 82,1 % |
| 166 | 1,0163 | 1,0240 | −0,0077 | 54,8 % | 60,9 % |
| 177 | 1,0048 | 1,0246 | −0,0198 | 63,7 % | 60,2 % |
| 188 | 1,0390 | 1,0262 | +0,0128 | 65,3 % | 55,3 % |
| 199 | 1,0028 | 1,0914 | −0,0886 | 51,6 % | 61,3 % |
| 211 | 0,9788 | 0,9923 | −0,0135 | 59,5 % | 63,8 % |
| 222 | 0,9892 | 1,0359 | −0,0467 | 66,7 % | 72,7 % |

| Grandeur | Valeur |
|---|---|
| Référence Étape 0 (avant la brique B) | **0,9959** |
| Ratio moyen **ACTIF** | **1,0372** (médiane 1,0106) |
| Ratio moyen **TÉMOIN** | **1,0367** (médiane 1,0189) |
| **δ apparié** | **+0,0005** · **`t` = +0,036** · n=20 |
| ACTIF > TÉMOIN | **9 / 20 graines** |
| Seuil Bonferroni (2 métriques, df=19) | \|t\| > 2,43 |

🔴 **JUGE N°1 : NÉGATIF.** `t = +0,036` contre un seuil de 2,43. Les deux bras sont
**indiscernables** et la répartition est un tirage à pile ou face (9/20).

## 3. ⚠️ Le test de fumée qui désavoue le test de fumée

La veille au soir, la sonde avait été essayée sur **une seule paire** :

```
ACTIF_g11   ratio = 1,1491
TEMOIN_g11  ratio = 1,0202
```

Cela **ressemblait** à un signal, et `g11` reste le plus gros δ de la campagne (+0,1455).
À n=20, ce n'était que la **queue de la distribution**.

> C'est le troisième cas documenté du même motif sur ce dépôt : `maîtrise ~ énergie`
> (+0,710 à n=10 → −0,059 à n=20), l'inversion `r = −0,89` sur 4 cerveaux (→ +0,3961 à
> n=20), et maintenant celui-ci. **Aucune lecture sous 20 graines n'a jamais survécu.**

## 4. La vérification décisive : vide ou négative ?

| Vérification | Résultat |
|---|---|
| Le signal a-t-il vécu pendant l'entraînement ? | ✅ **OUI** — amplitude **0,087 à 0,161** selon la graine, demi-vie **9,0** correctement dérivée de `SimpleCrossingS9N1` |
| Le témoin est-il bien coupé ? | ✅ 0 ligne de télémétrie sur les 20 runs TÉMOIN |
| Les bras diffèrent-ils ? | ✅ vérifié aux contrôles préalables (δ_A/A = 0 des deux côtés) |

🟡 **L'ablation n'est donc PAS VIDE au sens strict.** L'information cinématique était
**présente, variée et correctement dimensionnée** dans le vecteur bio des 20 runs ACTIF.
Le réseau ne s'en est simplement **pas servi**.

C'est une nuance qui compte : le résultat ne dit pas « la proprioception ne peut pas
aider », il dit « **`integrateur_bio` n'a pas myélinisé ces deux dimensions en 100 jours** ».

## 5. Le seul écart qui frôle quelque chose

**Gestes stériles : ACTIF 62,5 % contre TÉMOIN 64,7 %** — δ = **−2,20 pt**, `t = −1,757`.

⚠️ **Ne passe pas Bonferroni** (|t| > 2,43 requis pour 2 métriques), et n'était **pas** un
juge déclaré d'avance. À traiter comme une piste, jamais comme un résultat — c'est
exactement ainsi que le ratio C2/C1 et `part_monde` sont devenus des tautologies publiées.

## 5b. 🔴 LA MESURE QUI EXPLIQUE POURQUOI — la myéline ne distingue pas l'élan

Si `integrateur_bio` avait capté quelque chose, ses **deux dernières colonnes** (les dims
d'élan) devraient être plus myélinisées dans le bras ACTIF que dans le TÉMOIN — qui porte
les mêmes 2 colonnes, à la même largeur, mais **figées au neutre 0,5**.

| Bras | myéline(dims élan) | myéline(autres dims bio) | ratio |
|---|---|---|---|
| **ACTIF** | 0,000929 | 0,000434 | **2,140** |
| **TÉMOIN** | 0,000939 | 0,000442 | **2,127** |

**δ apparié = −0,0000104, `t` = −1,008.** Rigoureusement identiques.

> Les deux colonnes sont bien un peu plus myélinisées que les autres dims du vecteur bio —
> **mais autant dans les deux bras**. C'est donc un effet d'**initialisation** (colonnes
> fraîchement greffées, Xavier atténué), **pas** une réponse au signal. Le réseau n'a pas
> myélinisé l'élan *parce que c'était de l'élan* : il a traité deux colonnes neuves
> quelconques.

⚠️ **Note technique** : `annexe_weight` vaut **0,000000 exact** sur toutes les couches et
tous les cerveaux (100 comme 1440 jours). Ce n'est **pas** un défaut — la sauvegarde suit
`cycle_sommeil`, qui verse l'annexe dans la base et la remet à zéro. Mais cela signifie
qu'un `.brain` **ne permet pas de lire l'apprentissage du jour** : seule la myéline,
cumulative, est lisible post-hoc. À retenir pour toute future analyse de poids.

## 5c. JUGE N°2 — la directivité, pour mémoire

| Graine | ACTIF % | TÉM % | ACTIF dir | TÉM dir |
|---|---|---|---|---|
| 11 | 5,33 | 4,67 | 18,29 | 22,42 |
| 22 | 11,33 | 9,33 | 16,92 | 18,50 |
| 33 | 2,67 | 10,67 | 23,96 | 10,67 |
| 44 | 7,33 | 2,67 | 16,00 | 18,88 |
| 55 | 17,33 | 16,67 | 12,21 | 19,42 |
| 66 | 13,33 | 16,00 | 16,71 | 17,50 |
| 77 | 8,00 | 11,33 | 20,58 | 16,75 |
| 88 | 2,67 | 2,00 | 25,62 | 20,50 |
| 99 | 6,00 | 16,00 | 16,75 | 20,42 |
| 111 | 16,00 | 2,67 | 13,33 | 23,21 |
| 122 | 18,00 | 21,33 | 15,08 | 15,08 |
| 133 | 6,00 | 9,33 | 20,42 | 22,54 |
| 144 | 16,00 | 5,33 | 18,29 | 18,79 |
| 155 | 0,00 | 1,33 | — | 21,83 |
| 166 | 23,33 | 13,33 | 19,67 | 16,75 |
| 177 | 4,00 | 3,33 | 22,29 | 23,58 |
| 188 | 5,33 | 23,33 | 19,92 | 16,42 |
| 199 | 18,00 | 7,33 | 18,33 | 16,08 |
| 211 | 19,33 | 15,33 | 15,92 | 14,83 |
| 222 | 22,00 | 16,00 | 16,25 | 17,00 |

| Grandeur | Valeur | `t` |
|---|---|---|
| **Directivité médiane ACTIF** | **18,29×** | cible **< 6×**, échec **≥ 12×** |
| Directivité médiane TÉMOIN | 18,65× | — |
| δ directivité | −0,147× | **−0,129** (NS), n=19 |
| δ succès | +0,700 pt | **+0,410** (NS), n=20 |

🔴 **ÉCHEC sur le critère utilisateur** : 18,29× contre une cible de 6×, soit **3× la
cible** et 1,5× le seuil d'échec.

**Vérifications** : pas de saturation (max 25,62× contre un plafond de 27,0×) · 1 graine
à zéro victoire côté ACTIF (`g155`), donc n=19 pour la directivité · victoires au banc
333 contre 312, un écart de bruit sur 3 000 épisodes par bras · répartition 12 mieux /
8 pire en succès, 11/19 en directivité — **pile ou face**.

## 6. Limites

1. **100 jours.** `integrateur_bio` myélinise lentement ; l'absence d'effet à 100 jours
   n'exclut pas un effet à 1 500. Mais l'Étape 2 était conditionnée au juge n°1.
2. **Banc forcé** : le niveau reste à 1/15 par construction (règle §6).
3. Le juge n°2 est **rapporté au §5c**, mais il n'est **pas interprétable seul** puisque
   le juge n°1 est négatif — c'est la règle fixée d'avance.
4. Un **seul** couple de dimensions, une **seule** définition de l'élan (égocentrique,
   demi-vie = côté de la carte). D'autres formulations existent.

## 7. Ce que ça ferme, ce que ça laisse ouvert

**Fermé** : l'ancrage cinématique **comme simple entrée sensorielle passive**. Donner
l'information au réseau ne suffit pas — il faut apparemment le **contraindre** à s'en
servir. Les **deux** juges sont négatifs, et le second confirme le premier plutôt que de
le contredire.

**Ouvert, et c'est le point important** : les 21 réfutations partagent désormais un motif
unique. Qu'on retire du signal (curiosité, barème, rendement) ou qu'on en **ajoute**
(bit de portage, élan cinématique), **le comportement ne bouge pas**. La brique B était
censée être différente parce qu'elle *ajoutait une information* — elle ne l'est pas.

> L'hypothèse qui survit à cette campagne : ce n'est ni le signal d'apprentissage, ni
> l'information disponible qui limite l'agent, mais **sa capacité à convertir une
> information disponible en politique**. `integrateur_bio` reçoit déjà 44 dimensions ;
> la 45ᵉ ne change rien.
