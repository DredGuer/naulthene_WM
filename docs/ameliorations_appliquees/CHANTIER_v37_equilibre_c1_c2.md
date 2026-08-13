# Chantier v37.0 — L'Équilibre C1 / C2

> **Statut** : diagnostic terminé, équilibrage **implémenté et validé sur 600 jours** —
> l'équilibre C1/C2 tient (ratio 0,57-1,09 contre 9,9-22,1× avant), mais **le cursus reste
> bloqué** (niveau 2/15). L'équilibre était une condition nécessaire, pas suffisante. Verdict
> complet en §6bis. **Suite du diagnostic dans [dia_Aout_2026.md](../recherche/dia_Aout_2026.md)** (run de
> 1300 jours) : le blocage tient à **trois facteurs composés** — un saut de difficulté ×10 entre
> `Empty-6x6` et `Empty-8x8` (taux de réussite aléatoire 38,2 % → 3,8 %), une patience (120)
> inférieure à la moitié du budget natif MiniGrid (256), et une économie de récompense dont
> l'espérance vaut **−1,06** par épisode. Aucun n'est cognitif.
> **Branche** : `feat/v37-equilibre-c1-c2`
> **Date d'ouverture** : 2026-08-07
> **Cerveau de référence du diagnostic** : `brains/070820261310_V36_600_RMD.brain` (600 jours, bus 64)

---

## 1. Le point de départ

Trois cerveaux successifs (V34-fix1 900 j, V35 2700 j, V36 600 j) se sont arrêtés **au même
niveau du cursus** : `MiniGrid-SimpleCrossingS9N1-v0`, index 3 sur 15 (« Primaire 1 —
Contourner »). Le run V36 de 600 jours a atteint ce niveau au jour 288 et n'en est jamais
sorti : 2 victoires en 312 jours, contre 19 sur les 288 premiers.

L'hypothèse initiale — « le niveau 3 est mal placé dans le cursus » — a été **écartée par la
mesure**. Le blocage n'est pas pédagogique, il est architectural.

---

## 2. Ce que la mesure a montré

### 2.1 La sonde C1/C2 (`instruments/sonde_c1_c2.py`)

Le cerveau V36 a été sondé sur trois environnements, dont deux qu'il avait **maîtrisés** :

| Environnement | Ampl. C1 | Ampl. C2 | Ratio C2/C1 | Accord argmax |
|---|---|---|---|---|
| `Empty-5x5` (maîtrisé) | 0,217 | 2,138 | **9,9×** | **0 %** |
| `Empty-8x8` (maîtrisé) | 0,168 | 2,125 | **12,7×** | **0 %** |
| `SimpleCrossingS9N1` (bloqué) | 0,095 | 2,105 | **22,1×** | **0 %** |

Deux faits que ce tableau contient et qui ne sont pas anodins :

1. **L'accord C1/C2 est nul sur les trois cartes** — pas faible, *nul*. `argmax(C1) = 3` sur
   400 ticks sur 400 ; `argmax(C2) = 0` sur 400 ticks sur 400. Chaque module vote une action
   **constante**, différente de l'autre, indépendamment de l'observation.
2. **L'amplitude de C2 est identique (2,10 ± 0,02) sur trois cartes de difficultés très
   différentes.** Un module qui délibère devrait varier ; celui-ci ne varie pas.

Le déséquilibre existe **aussi sur les niveaux maîtrisés** (9,9× sur `Empty-5x5`). Il n'a donc
pas été causé par le blocage : il le précède. Les 21 victoires du run V36 (taux de vie 3,5 %)
sont attribuables à la marche aléatoire du `multinomial`, pas à une politique apprise.

### 2.2 La sonde des poids (`instruments/sonde_poids.py`)

```
couche                      |base|   |annexe|   myeline   n_naiss    ratio
porte_visuelle              0.8607    0.0000       nan     5.3207   16.18%
hippocampe                  1.1712    0.0000       nan     4.6802   25.03%
fusion_memoire              1.0351    0.0000       nan     4.5238   22.88%
analyseur                   0.8676    0.0000       nan     4.1177   21.07%
integrateur_bio             0.6577    0.0000       nan     4.9644   13.25%
tete_motrice                0.3195    0.0000       nan     3.1949   10.00%   ← plancher exact
cortex_prefrontal           0.1288    0.0000       nan     1.2879   10.00%   ← plancher exact
generateur_attente          0.4476    0.0000       nan     4.4759   10.00%   ← plancher exact
tete_requete                0.2898    0.0000       nan     2.8983   10.00%
porte_auditive              1.1852    0.0000       nan     5.4489   21.75%
tete_vocale                 0.3168    0.0000       nan     3.1677   10.00%
generateur_attente_audio    0.5559    0.0000       nan     4.4147   12.59%
```

---

## 3. Les trois causes, empilées

### Cause 1 — Les deux têtes de décision sont collées au plancher vital

`tete_motrice` et `cortex_prefrontal` sont à **exactement 10,00 %** de leur norme de naissance,
c'est-à-dire pile sur `FRACTION_NORME_MIN_COUCHE = 0.10`. Elles ne sont pas mortes : le
plancher vital v34.0-fix1 les en a empêchées, et c'est une confirmation supplémentaire de son
utilité (6 couches sur 12 y sont collées ici). Mais **il les maintient à 10 % de leur force**.

C1 produit des logits d'amplitude 0,1 parce qu'il ne lui reste que 10 % de ses poids. Le
plancher vital a converti une mort certaine en **survie muette** — ce qui est un progrès, mais
pas une solution.

> Le plancher vital est un garde-fou de dernier recours, pas un régime de croisière. Le fait
> que 6 couches y soient collées en permanence signifie que l'érosion reste trop forte pour un
> cerveau qui ne reçoit pas de récompense, pas que le plancher est mal réglé.

### Cause 2 — Aucune myéline, nulle part

`annexe_weight = 0.0000` sur les 12 couches, `myeline_M` non renseignée. La chaîne causale
documentée depuis la v34.0 se vérifie intégralement :

```
pas de victoire → pas de récompense → gradient ~0 → annexe ~0
                → myeline_M = max(myeline_M, |annexe|) ~0
                → érosion à taux plein (facteur = 1 − λ)
                → chute jusqu'au plancher vital
```

C'est un **cercle vicieux** : l'agent a besoin de gagner pour myéliniser, et de ses poids pour
gagner. Le plancher vital coupe la chute mais ne relance pas la machine.

### Cause 3 — C2 est normalisé, C1 ne l'est pas *(la cause immédiate du déséquilibre)*

Dans `simuler_futur_et_planifier` (`noyau.py:534-535`) :

```python
if valeur_cumulee.std() > 1e-6:
    valeur_cumulee = (valeur_cumulee - valeur_cumulee.mean()) / (valeur_cumulee.std() + 1e-8)
```

**C2 sort toujours avec un écart-type de 1**, quelle que soit sa confiance réelle. Un C2 qui
n'a aucun avis (toutes les branches équivalentes) et un C2 parfaitement sûr produisent des
sorties de **même amplitude**. L'information de confiance est calculée (`indecision_c2`, le std
brut d'avant normalisation) puis **jetée** du chemin de décision — elle ne sert que de
télémétrie.

C1, lui, conserve son échelle brute, qui est celle de ses poids érodés : ~0,1.

L'arbitrage `logits_instinct + valeurs_simulees × force_planification` additionne donc
**0,1 et 2,1 × 0,85 ≈ 1,8**. Le rapport de force 1:18 n'a jamais été un choix d'architecture :
c'est un artefact de la normalisation d'un seul des deux termes.

> **C2 n'écrase pas C1 parce qu'il est meilleur. Il l'écrase parce qu'il est le seul des deux à
> avoir une échelle garantie par construction.**

---

## 4. Ce qui a été écarté, et pourquoi

Traçabilité des options évaluées puis rejetées, pour éviter qu'elles soient réintroduites sans
l'argument qui les a écartées.

| Option écartée | Raison |
|---|---|
| **Insérer un palier entre `Empty-8x8` et `SimpleCrossing`** | Le déséquilibre C1/C2 est présent **aussi sur les niveaux maîtrisés** (9,9× sur `Empty-5x5`). Un palier de plus serait franchi par la même marche aléatoire, sans rien apprendre. À reconsidérer **après** la v37, si le blocage persiste. |
| **Supprimer la normalisation z-score de C2** | Elle a une fonction réelle : sans elle, l'échelle de `cortex_prefrontal` dérive librement et C2 peut exploser. Le problème n'est pas qu'elle existe, c'est qu'elle **efface la confiance**. |
| **Baisser `FORCE_PLANIFICATION` (0,85 → 0,05)** | Constante arbitraire remplaçant une constante arbitraire. Ne corrige pas la cause (l'asymétrie d'échelle) et casserait C2 sur un cerveau sain dont C1 serait fort. Interdit par la doctrine « instrumenter d'abord, calibrer ensuite ». |
| **Court-circuit « C1 saute C2 s'il est confiant »** | Refusé par l'utilisateur en v29.0, et à nouveau ici. C2 est sollicité à **chaque** tick ; l'équilibrage porte sur la fusion, jamais sur un `if`. |
| **Remonter `FRACTION_NORME_MIN_COUCHE` à 0,30** | Traite le symptôme (têtes faibles) sans traiter la cause (érosion sans myéline). Et masquerait le signal de diagnostic : le fait que 6 couches soient collées au plancher est une **information**, qu'il ne faut pas rendre invisible. |

---

## 5. L'équilibrage retenu (v37.0)

Le chantier a livré **deux mesures d'arbitrage et trois correctifs de fond**. Une troisième
mesure a été implémentée, mesurée, puis retirée (§5.4) — elle est documentée avec les autres
parce que son échec est le résultat le plus instructif du chantier.

### 5.1 — Mesure 2 : le gain de C1 est à double sens

L'amplitude de C1 est ramenée vers `VIGUEUR_MIN_C1` par un facteur **scalaire**, dans les deux
sens : il relève un réflexe étouffé par l'érosion, il tempère un réflexe devenu tonitruant.
L'opinion de C1 (les rapports entre ses 7 logits) reste rigoureusement intacte — seul son
volume est réglé.

`VIGUEUR_MIN_C1` n'est **pas posée à la main**, elle est dérivée de la seule échelle de
référence disponible :

```python
VIGUEUR_MIN_C1 = (AMPLITUDE_C2_NORMALISEE * FORCE_PLANIFICATION_LIBRE) / RATIO_C1C2_VISE
#              = (2.1 × 0.85) / 2.0 ≈ 0.89
```

`AMPLITUDE_C2_NORMALISEE = 2.1` est l'amplitude d'un z-score sur 7 actions, **vérifiée
empiriquement** sur trois environnements (2,105 / 2,096 / 2,103). `RATIO_C1C2_VISE = 2.0`
maintient C2 prépondérant — c'est voulu : C2 doit continuer de faire émerger l'intelligence,
pas être mis à égalité avec le réflexe.

> **La borne haute (`GAIN_C1_MAX`) a été ajoutée après mesure.** La première version ne faisait
> qu'amplifier (`min=1.0`) : une fois les têtes débloquées par les correctifs §5.2 et §5.3, la
> distillation a renforcé C1 bien plus vite que C2, et le ratio s'est **inversé à 0,21×**.
> C'était exactement le mode d'échec annoncé au §6. Le gain est donc borné des deux côtés.

### 5.2 — Correctif : le plancher vital ne doit jamais être un plafond

La v34.0 renormalisait à `norme_plancher` **depuis** la norme post-érosion, ramenant la couche
à *exactement* 10 % de sa naissance quelle que soit sa valeur d'entrée. Pour une couche collée
au plancher, tout ce que le gradient avait consolidé était donc effacé chaque nuit.

```python
# v34.0 — ramène à exactement le plancher, dans les deux sens
if 0 < norme_apres < norme_plancher:
    self.base_weight *= (norme_plancher / norme_apres)

# v37.0-fix — ne remonte que ce qui manque, ne redescend jamais
facteur_plancher = torch.clamp(norme_plancher / norme_apres, min=1.0)
```

### 5.3 — Correctif : la myéline doit voir l'apprentissage du jour

`myeline_M = max(myeline_M, |annexe|)` n'était calculée que dans `forward()`, donc **pendant**
la journée — à un moment où `annexe_weight` vaut encore la valeur de la veille. Or la séquence
nocturne est `apprendre_journee` (step #1) → `rever` (step #2) → `cycle_sommeil` : aucun
`forward` n'a lieu entre le dernier pas d'optimiseur et l'érosion.

**La myéline qui protège une couche ignorait donc systématiquement tout ce qu'elle venait
d'apprendre.** Le rafraîchissement a été placé en tête de `cycle_sommeil`, seul point qui voit
l'état final de `annexe_weight`. L'invariant est intact : la myéline vient toujours **uniquement
du gradient** — seul le *moment* de la lecture change.

### 5.4 — Correctif : l'échelle de la myéline est relative, plus absolue

`q_ref = 1.0` (paramètre jamais passé par aucun appelant depuis l'origine) suppose une myéline
d'ordre 1. La mesure dit ~0,002. **L'échelle était 500× trop grande**, donc `myeline_norm`
restait collée à 0 et *toute* couche s'érodait au taux plein, myélinisée ou non : la protection
promise par la Cristallisation Souple n'a jamais pu s'exercer sur aucun cerveau du dépôt.

C'est le défaut de `SEUIL_CRISTAL = 0.80` à l'identique — une échelle absolue posée a priori,
jamais confrontée à une mesure.

L'échelle suit désormais le **3ᵉ quartile de `myeline_M` de la couche elle-même**. Le quantile
plutôt que le maximum : normaliser par le max fait porter toute l'échelle par une seule synapse
extrême et écrase les 99 % restantes (distribution mesurée sur `tete_motrice` : médiane 0,027,
p90 0,197, p99 1,000 — protection moyenne 12,7 % seulement). La hiérarchie entre synapses est
strictement conservée : c'est l'unité qui change, jamais l'ordre.

### 5.5 — Mesure 3 : le réflexe reçoit un gradient qui ne dépend pas de la victoire

Tant que seule une victoire produit du gradient, un agent qui ne gagne pas ne consolide rien.
C1 est donc tiré vers ce que C2 a jugé meilleur **après délibération** — auto-distillation.

**Rien n'est expliqué en dur** : la cible n'est pas une table « action 2 = bien », c'est la
sortie d'un module du cerveau lui-même, `.detach()`ée. Ce `.detach()` est essentiel — sans lui,
le gradient remonterait dans le rollout et C2 apprendrait à se rendre *prévisible* plutôt que
juste. Vérifié : `cortex_prefrontal` reçoit bien un gradient de **0,00000000** par ce canal.

Désactivable entièrement par `TAUX_DISTILLATION_C1 = 0.0`.

### 5.6 — Mesure 1 : ESSAYÉE, MESURÉE, RETIRÉE

L'idée : la normalisation z-score efface la confiance de C2 (un C2 sans avis et un C2 certain
sortent tous deux à std=1), il faudrait donc la réinjecter. **Deux implémentations, deux échecs :**

| Tentative | Résultat mesuré | Cause |
|---|---|---|
| Échelle **absolue** (`valeur × std_brut`) | **Éteint C2** — ratio tombé à 0,01× | Le std brut vaut 0,0008 et ne varie que de **1,00×** entre min et max sur 300 ticks |
| Échelle **relative** (rapport à une moyenne glissante de son propre std) | **Sature** — `confiance = 2.0000` en permanence | La moyenne glissante décroît plus vite que le signal ; effet net = facteur constant, donc rien |

**Conclusion : tant que `cortex_prefrontal` est au plancher, C2 n'a aucune confiance variable à
exprimer — il n'y a rien à réinjecter.** Le code a été retiré, la trace conservée dans
`simuler_futur_et_planifier` à l'endroit exact où il aurait vécu. À reconsidérer seulement si
un run montre `indecision_c2` réellement variable.

### 5.7 — Correctif : la normalisation de C2 devient inconditionnelle

L'ancien `if std > 1e-6` laissait, en dessous du seuil, `valeur_cumulee` à son échelle brute
(~1e-7) — un C2 **numériquement éteint** qui disparaissait de la fusion sans que rien ne le
signale. Observé sur les runs de validation : des journées entières à `C2=0.000` alternant avec
des journées normales.

« C2 hésite entre des branches proches » ne veut pas dire « C2 n'a pas d'avis » : la hiérarchie
relative entre les 7 actions reste porteuse d'information. L'epsilon au dénominateur suffit à
couvrir le cas dégénéré sans jamais éteindre le module.

---

## 5bis. v37.1 — La distillation devient sélective

> Ajout postérieur à la v37.0, issu d'une remarque de l'utilisateur : *« rejouer
> prioritairement les épisodes où l'intervention de C2 a mené à un succès »*.

### Le défaut corrigé

La distillation v37.0 était **plate** : C1 imitait C2 à chaque tick, au même poids, que C2
ait eu raison ou tort. Sur un C2 aussi médiocre que l'actuel (amplitude constante, argmax
figé), cela revient à **faire apprendre à C1 les erreurs de C2**.

Le principe biologique est le bon : on n'automatise pas tous ses gestes, on automatise ceux
qui ont marché.

### Le crédit rétrograde

Un tick est crédité si un choc dopaminergique le **suit**, et le crédit décroît
exponentiellement à mesure qu'on remonte le temps — le geste juste avant la récompense
compte plus que celui d'il y a trente ticks. C'est le patron de `trace_activation`
(LTP v20.0), appliqué ici à la sélection de ce qui vaut d'être gravé dans le réflexe.

La propagation **s'arrête aux frontières d'épisode** : créditer un tick de l'épisode
précédent pour une réussite du suivant serait une superstition, l'agent ayant été téléporté
entre les deux.

```
chocs : [0, 0, 0, 0, 0, 0.8, 0, 0, | 0, 0, 0.4, 0]      (| = fin d'épisode)
poids : [.66,.72,.78,.85,.92, 1.0, 0., 0., .56,.61,.67, 0.]
                                    └──┬──┘
                              crédit coupé net
```

### Rien n'est en dur : le niveau, pas le seuil

Il n'existe **aucun seuil** du type « si choc > X, imiter ». Le crédit est **continu** et
proportionnel au choc. Et l'échelle à laquelle un choc est jugé fort n'est pas une
constante : c'est `reference_choc_dopamine`, moyenne glissante de ce que **cet agent** a
lui-même vécu, sérialisée dans le `.brain`.

Vérifié en simulation :

| Agent | Référence apprise | Crédit accordé à un choc de 0,1 |
|---|---|---|
| **Débutant** (n'a connu que des micro-progrès) | 0,100 | **100 %** |
| **Le même, expert** (200 jours de victoires) | 0,879 | **11,5 %** |

Le même événement est **8,7× moins marquant** pour l'expert que pour le débutant. Le niveau
évolue avec l'âge et les habitudes, exactement comme la faim ou la soif — pas de seuil, un
niveau relatif à une histoire.

Les deux seules constantes ajoutées sont des **dynamiques**, jamais des seuils de décision :
`DECROISSANCE_CREDIT_DISTILLATION` (à quelle vitesse un crédit s'efface vers le passé) et
`INERTIE_REFERENCE_CHOC` (à quelle vitesse la référence suit la maturation).

### Effet mesuré

| | v37.0 (plate) | v37.1 (sélective) |
|---|---|---|
| Part de la journée distillée | 100 % | **~25-35 %** |
| Gradient reçu par `tete_motrice` | 0,01117 | 0,00912 (**−18 %**) |

Une journée entièrement stérile (aucun choc) ne distille désormais **rien du tout**, au lieu
de distiller uniformément du bruit.

### Ce qui a été écarté

| Option | Raison |
|---|---|
| **`f_planif` piloté par l'entropie de C1 / l'erreur JEPA** | Le signal n'existe pas : `indecision_c2` varie de **1,00×** entre min et max (0,000756 → 0,000773 sur 300 ticks). Et c'est un déclenchement sur seuil déguisé en formule continue — refusé v28/v29/v30. Le ratio est déjà passé de 22× à 0,6× **sans aucun pilotage**, par la seule maturation synaptique : c'est le principe A de la réflexion utilisateur, et il se suffit à lui-même. À reconsidérer si un run long montre le ratio **stagnant**. |
| **C2 réinjecté comme canal continu dans `integrateur_bio`** | Crée une boucle : C2 est calculé **à partir de** `pensee_bio`, qui sort de `integrateur_bio`. Exigerait un décalage d'un tick, donc un C2 qui conseille sur l'état précédent. |
| **Rejouer les épisodes « C2-réussis » dans `rever()`** | Retenu dans l'esprit, mais implémenté **dans le gradient diurne** plutôt que dans le tirage du rêve : `memoire_moyen_terme` ne conserve aucune trace de la contribution de C2 à chaque tick, alors que la pondération de la perte y a directement accès. Même effet, sans nouvelle structure de données. |

---

## 6. Critères de validation

Le chantier ne sera déclaré réussi que si **les quatre** sont observés sur un run long.

| # | Critère | Cible | État au 2026-08-08 (run **600 j**, `8wequiqg`) |
|---|---|---|---|
| 1 | Le ratio C2/C1 descend sous 3× | `< 3,0` | ✅ **0,57 à 1,09** sur tout le run (contre 9,9-22,1×) |
| 2 | L'accord C1/C2 cesse d'être nul | `> 15 %` | 🟡 **29 à 75 %** — le critère est franchi, mais il **oscille** au lieu de converger |
| 3 | Les têtes décollent du plancher vital | `> 12 %` de `n_naiss` | 🟡 partiel — `cortex_prefrontal` décollé, `tete_motrice` toujours à 10,00 % (mais se remodèle, voir §8) |
| 4 | Le niveau 3 est franchi | niveau ≥ 4 | ❌ **niveau 2/15** — et **aucune victoire après le jour 288** (312 jours) |

**Le critère 4 est le seul qui compte vraiment.** Les trois premiers peuvent être atteints sans
que l'agent progresse — ce serait alors un équilibrage cosmétique, et il faudrait revenir au
cursus (§4, première ligne du tableau).

### Lecture honnête de l'état actuel

Le chantier a corrigé des **bugs réels et mesurés** (§5.2, §5.3, §5.4, §5.7), dont deux qui
rendaient l'apprentissage des têtes de décision *mathématiquement impossible*. L'équilibre
d'arbitrage est atteint et stable. Trois couches sur cinq ont quitté le plancher vital.

Mais **le critère 2 n'a pas bougé d'un pouce** : C1 et C2 restent en désaccord sur 100 % des
ticks. Les deux modules ont maintenant des voix comparables, ils ne convergent pas pour autant.
Il est trop tôt pour dire si l'auto-distillation les rapprochera sur plusieurs centaines de
jours, ou si un autre mécanisme les maintient orthogonaux.

**Rien ne permet encore d'affirmer que la v37 débloquera le niveau 3.** C'est ce que le run long
doit trancher.

### Ce qui invaliderait le chantier

- Le ratio descend mais l'agent **régresse** sur les niveaux 0-2 déjà acquis → C2 était utile,
  la mesure 2 l'a trop affaibli.
- L'accord monte à ~100 % → C1 et C2 sont devenus redondants, l'auto-distillation (mesure 3) a
  écrasé la diversité au lieu de l'équilibrer. **C'est le risque principal de la mesure 3.**

---

## 6bis. Le verdict du run de 600 jours (`8wequiqg`, 2026-08-08)

### L'équilibre est acquis, le déblocage ne l'est pas

| Tranche | Accord | Ratio C2/C1 | C1 | C2 |
|---|---|---|---|---|
| 0-100 | 50,0 % | 0,90 | 1,90 | 1,57 |
| 100-200 | **75,2 %** | 0,57 | 2,82 | 1,59 |
| 200-300 | 65,8 % | 0,70 | 2,28 | 1,59 |
| 300-400 | 35,2 % | 0,88 | 1,62 | 1,40 |
| 400-500 | 41,1 % | 0,91 | 1,61 | 1,45 |
| 500-600 | **29,2 %** | 1,09 | 1,41 | 1,53 |

Le ratio ne quitte jamais la plage saine [0,57 ; 1,09] : **l'équilibrage de la v37.0 tient sur la
durée**, et c'est le résultat solide du chantier.

Mais **l'accord oscille au lieu de converger**. Un pic à 100 % observé vers le jour 227 avait été
lu en cours de run comme une convergence — c'était une oscillation. Ni le mode d'échec redouté
(redondance à 100 %) ni la convergence espérée : les deux modules coexistent sans s'accorder
durablement.

### Le critère qui compte a échoué

```
jour 266 : niveau 0 → 1
jour 287 : niveau 1 → 2
jour 288-600 : plus AUCUNE victoire (312 jours), guidage saturé à ×3,0 depuis ~387
```

**22 victoires, toutes avant le jour 300. Niveau 2/15 à l'arrivée**, contre 3/15 pour le run V36
de référence. L'agent est *plus lent* que sans la v37, tout en gagnant plus souvent sur un niveau
plus facile.

### Un bug introduit par la v37.1, trouvé par ce run

`reference_choc_dopamine` utilisait une moyenne glissante **symétrique** : quand l'agent cesse de
gagner, elle descend vers les micro-chocs (0,2149 → 0,0932, **−57 %**) et, le crédit valant
`choc / référence`, le même événement médiocre crédite de plus en plus (10 % → **69 %**, ×7).

L'agent devenait **de plus en plus facile à impressionner** — l'inverse exact du principe — et C1
distillait 70 % de bruit. Corrigé en v37.1-fix1 par un **cliquet** (montée rapide, descente ~50×
plus lente), même remède que `norme_naissance` en v34.0-fix2.

### Ce que ce run ne dit pas, et qu'il faut isoler

- ~~**Le rêve est quasi inexistant** : `Pourcentage_Reve` à **0,1 %**~~ ❌ **FAUX — corrigé le
  2026-08-08** ([dia_Aout_2026.md](../recherche/dia_Aout_2026.md) §2.2). La valeur est une **fraction**
  affichée avec un `%` en trop : le rêve rejoue en réalité **15-18 %** de la journée (70 rêves
  par nuit en fin de run) et **fonctionne**. Les nuits sans rêve du début sont réelles mais
  disparaissent après le jour 400.
- **`Recompense_Moyenne = 0.000`** sur l'intégralité du run, comme sur tous les runs précédents.

### Où en est le chantier

L'équilibre C1/C2 était **une condition nécessaire, pas suffisante**. Les quatre bugs de fond
(plancher-plafond, timing de la myéline, échelle absolue, normalisation conditionnelle) sont
corrigés et validés. Mais le blocage du cursus persiste, et il faut maintenant chercher ailleurs
— le run de 1300 jours ([dia_Aout_2026.md](../recherche/dia_Aout_2026.md)) a tranché : le blocage est
**les conditions d'exercice**, pas une mécanique cognitive — saut de difficulté ×10 au niveau 2,
patience deux fois trop courte, et espérance de −1,06 par épisode.

---

## 7. Invariants à ne pas casser

- **C2 est sollicité à chaque tick.** Aucun court-circuit conditionnel, aucun seuil dans le
  chemin de décision (refusé en v28, v29, v30 — et ici).
- **C2 ne reçoit que `pensee_bio`**, l'état déjà compressé par C1. Jamais l'observation brute,
  jamais l'environnement.
- **Le rollout garde sa complexité linéaire** : premier pas sur les 7 actions réelles, pas
  suivants en argmax glouton. Jamais 7^horizon.
- **Rien n'est expliqué en dur.** Aucune table action→valeur, aucun objet nommé. Le signal de
  la mesure 3 vient de la cohérence entre modules, pas d'une connaissance injectée.
- **Les constantes sont des bornes, les valeurs sont dérivées.** `confiance_c2` est mesurée à
  chaque tick, jamais fixée.
- **Rétrocompatibilité des `.brain`** : la v37 ne change aucune dimension ni forme de tenseur.
  Un `.brain` v36 se recharge sans greffe.

---

## 8. Journal du chantier

| Date | Étape | Résultat |
|---|---|---|
| 2026-08-07 | Sonde C1/C2 sur 3 environnements | Ratio 9,9× à 22,1×, accord **0 %** partout |
| 2026-08-07 | Sonde des poids sur cerveau V36 | 5 couches sur 12 collées au plancher vital ; `annexe = 0` partout |
| 2026-08-07 | Identification de la cause immédiate | Normalisation z-score de C2 non appliquée à C1 |
| 2026-08-07 | Mesure 1, tentative absolue | **Échec** — éteint C2 (ratio 0,01×) |
| 2026-08-07 | Mesure 1, tentative relative | **Échec** — sature au plafond (confiance = 2,0000 constante) |
| 2026-08-07 | Mesure 1 retirée | Trace conservée dans le code ; le déséquilibre se corrige côté C1 |
| 2026-08-07 | Mesure 2 (gain amplificateur seul) | Ratio ramené à 2,36× et **stable sur les 3 cartes** (contre 9,9-22,1× dérivant) |
| 2026-08-07 | Correctif plancher-plafond | Le gradient consolidé n'est plus effacé chaque nuit |
| 2026-08-07 | Correctif timing myéline | Myéline de `tete_motrice` : 0,000000 → 0,0033 |
| 2026-08-07 | Correctif échelle myéline (quantile) | Protection moyenne 0 % → 45,9 % ; érosion effective 0,050 → 0,027 |
| 2026-08-07 | Run 30 j | **Ratio inversé à 0,21×** — C1 écrase C2, mode d'échec §6 déclenché |
| 2026-08-07 | Gain rendu à double sens | Ratio remonté et **convergent vers 1,5×** |
| 2026-08-07 | Normalisation C2 inconditionnelle | Fin des `C2=0.000` intermittents |
| 2026-08-07 | Run 40 j de validation | Ratio **1,48-1,59× stable**, C2 constant à ~1,48 |
| 2026-08-07 | Sonde des poids finale | **3 couches** au plancher (contre 5) ; `cortex_prefrontal` décollé à 11,07 % |
| 2026-08-07 | Vérification remodelage `tete_motrice` | Norme constante mais **cosinus 0,9972 / 7,43 % des poids modifiés en 5 nuits** — la couche apprend |
| 2026-08-07 | v37.1 — distillation sélective (crédit rétrograde) | Part de journée distillée 100 % → ~25-35 % ; gradient `tete_motrice` −18 % |
| 2026-08-08 | **Run 600 j (`8wequiqg`)** | Ratio **0,57-1,09** stable ✅ ; accord **29-75 % oscillant** 🟡 ; **niveau 2/15**, aucune victoire après le jour 288 ❌ |
| 2026-08-08 | Bug trouvé PAR ce run | `reference_choc_dopamine` symétrique s'effondre de **−57 %** quand l'agent cesse de gagner ; crédit ×7 (10 % → 69 %) |
| 2026-08-08 | v37.1-fix1 — le cliquet | Simulation du scénario exact : dérive **−71,3 % → −4,4 %**, crédit **87,2 % → 26,1 %** ; principe débutant/expert préservé (×8,8) |
| 2026-08-08 | ~~Anomalie du rêve~~ | ❌ **Erreur de diagnostic** : fraction lue comme un pourcentage. Le rêve rejoue **15-18 %** de la journée et fonctionne — voir [dia_Aout_2026.md](../recherche/dia_Aout_2026.md) §2.2 |
| 2026-08-08 | **Run 1300 j (`ous47258`)** — v37.1-fix1 | Cliquet validé (dérive **−7,4 %** sur 2× plus long) ; **1 couche au plancher contre 5** ; mais **niveau 2/15**, 678 j sans victoire |
| 2026-08-08 | Cause du blocage identifiée | **Trois facteurs composés, aucun cognitif** : saut de difficulté ×10 (`Empty-6x6` 38,2 % → `Empty-8x8` 3,8 % en politique aléatoire) ; patience 120 contre 256 natifs (4,7 % → 21,0 % de réussite atteignable) ; espérance **−1,06** par épisode. Diagnostic complet : [dia_Aout_2026.md](../recherche/dia_Aout_2026.md) |

### Note sur `tete_motrice` restée à 10,00 %

La couche reste collée au plancher en **norme**, ce qui a d'abord été lu comme un échec. La
mesure dit autre chose : sa consolidation nocturne fait *baisser* la norme (0,31949 → 0,31823),
parce que le gradient pointe en sens opposé aux poids existants — **il les corrige, il ne les
grossit pas**. Le plancher la remonte ensuite à son échelle d'origine.

Vérifié sur 5 nuits : similarité cosinus 0,9972, distance relative **7,43 %**. La couche se
remodèle activement à norme constante. Le plancher normalise l'échelle, pas le contenu — c'est
un comportement sain, et la norme seule est un mauvais indicateur d'apprentissage.
