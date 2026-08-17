# Ce que C2 dit à C1, en mots simples

**17/08/2026** — carnet de recherche, non normatif.
Question de l'utilisateur : *« On ne peut pas savoir par les logs ce que C2 dit à C1 ? En
mots simples. Presque voir la chaîne de penser, et extrapoler entre cerveaux. »*

Outil : [`scripts/traducteur_pensee.py`](scripts/traducteur_pensee.py).

---

## 1. Pourquoi les logs ne peuvent pas répondre

Les logs enregistrent bien les deux votes ([`noyau.py:7313-7315`](../../src/naulthene/cerveau/noyau.py#L7313-L7315)),
mais dans **deux boîtes séparées** : `votes_c1_jour` et `votes_c2_jour`.

C'est comme noter, sur une journée de réunion : « Paul a dit *oui* 40 fois » et « Marie a
dit *oui* 50 fois ». On sait combien de fois chacun a dit quoi. On ne sait **jamais s'ils
l'ont dit en même temps**. Les couples sont perdus à l'écriture.

Le traducteur garde la **matrice 7×7 des couples** — l'objet manquant.

---

## 2. Une erreur de sonde qui aurait « confirmé » la thèse du projet

⚠️ Consignée parce qu'elle était parfaitement crédible et flatteuse.

Première version : la sonde lisait `etat.force_planification_jour` pour pondérer C2. Or
c'est un **accumulateur journalier**, remis à 0 par `_reinitialiser_buffers_journee`. Sur
un `.brain` fraîchement chargé il vaut **0.0** — la sonde multipliait donc C2 **par zéro**.

Résultat affiché : `veto de C2 : 0/300 = 0.0%`. Un chiffre propre, net, qui « confirmait »
la lecture historique du projet (« C2 ne sert à rien »).

Après correctif — la fusion réelle est `logits_c1 × gain_c1 + valeurs_c2 × acceptation()`,
avec `acceptation() = 0,87` sur ce cerveau :

```
veto de C2 : 371/400 = 92,8 %
```

**De 0 % à 92,8 %.** C'est exactement le §3 de la règle de mesure : *un résultat trop
propre est suspect*, et *un résultat favorable se vérifie deux fois plus qu'un défavorable*.

**Contrôle ajouté** : la sonde reproduit désormais l'action de `penser()` sur
**40 ticks / 40**. Sans ce test de concordance, aucun chiffre de cette page ne vaudrait.

---

## 3. La chaîne de pensée, telle qu'elle se lit

Cerveau `variante_g13` (niveau 4 atteint, 240 000 ticks) sur `SimpleCrossingS9N1` :

```
t 0 │ faim modérée, soif modérée, odeurs N0.42/E0.42, coincé
    │ C1 «avancer»           (0.13)   C2 «poser»            (1.06)
    │ → joue «poser»   ⚔️ C2 L'EMPORTE

t 3 │ faim modérée, nez contre un obstacle
    │ C1 «tourner à gauche»  (0.19)   C2 «tourner à droite» (0.58)
    │ → joue «tourner à droite»   ⚔️ C2 L'EMPORTE
```

Le tick 3 est lisible : l'agent a le nez contre un mur, C1 veut tourner à gauche, C2 dit
« non, à droite », et **C2 gagne**. C'est une délibération, au sens strict.

Le tick 0 l'est moins : C2 vote « poser » alors que l'agent ne tient rien. Voir §6.

---

## 4. La matrice, et les phrases qu'on en tire

```
C1 dit ↓ / C2 dit →     ←gauche  →droite  ↑avancer  ✋manger  ↓poser  ⚙activer  …attendre
tourner à gauche              ·       42         ·        ·      10         ·          2
avancer                       ·        3         ·        ·      72        30          3
prendre / manger              ·      150        18        ·      27        18         25
```

Traduit :

- Quand C1 veut **tourner à gauche**, C2 répond **« plutôt à droite »** — 78 % du temps.
- Quand C1 veut **avancer**, C2 répond **« plutôt poser »** — 67 % du temps.
- Quand C1 veut **manger**, C2 répond **« plutôt tourner à droite »** — 63 % du temps.

**Accord : 0/400.** La diagonale est vide : sur ce cerveau les deux voix ne tombent
d'accord sur *aucun* tick.

### Coïncidences corps ↔ vote de C2

| Sensation | ticks | C2 vote surtout |
|---|---|---|
| obstacle devant | 225 | **tourner à droite (85 %)** |
| coincé | 390 | tourner à droite (50 %) |
| sent la nourriture | 400 | tourner à droite (49 %) |

⚠️ **Des coïncidences, pas des causes.** C2 produit 7 scalaires, sans justification : « il
tourne quand il y a un mur » est mesurable, « il tourne *parce qu'*il y a un mur » ne l'est
pas. Le script ne l'écrit jamais.

Le 85 % sur « obstacle devant » est néanmoins le plus net du lot : c'est le meilleur candidat
au statut de comportement réellement appris.

---

## 5. L'extrapolation entre cerveaux — le résultat le plus important

Six cerveaux de la campagne n=20, 400 ticks chacun :

| Cerveau | niveau | veto | accord | C2 propose |
|---|---|---|---|---|
| `variante_g13` | 4 | **93 %** | 0 % | **5 actions**, entropie **0,664** |
| `variante_g4` | 4 | **64 %** | 32 % | **6 actions**, entropie **0,537** |
| `variante_g16` | 4 | 77 % | 23 % | 1 action, entropie **0,000** |
| `temoin_g10` | 3 | **6 %** | 86 % | 4 actions, entropie 0,204 |
| `temoin_g9` | 3 | **0 %** | 29 % | 2 actions, entropie 0,311 |
| `temoin_g1` | 3 | **0 %** | 100 % | 2 actions, entropie **0,009** |

**Les trois témoins ont un veto de 0 %, 0 % et 6 %.** Chez eux, C2 ne détourne
pratiquement jamais la décision : C1 décide seul. Deux des trois variantes montent à
64–93 % de veto avec une voix C2 **variée** (5 à 6 actions distinctes).

Et `temoin_g1` est le cas d'école du piège de l'`accord` : **100 % d'accord** avec une
entropie de **0,009**. Deux voix qui répètent chacune la même action s'accordent
parfaitement sans qu'aucune délibération n'ait eu lieu — c'est le défaut que la v41.14
documentait, ici pris en flagrant délit.

> **Ce que ça ajoute à la campagne n=20** : le brain-sparing n'a pas seulement débloqué
> C1 (1,78 → 4,58 actions distinctes). Il a rendu à C2 un **pouvoir de veto réel** — de
> 0 % chez les témoins à 64–93 % chez les variantes qui franchissent le niveau 4.

⚠️ **n=6, donc aucune conclusion.** À cette taille l'intervalle de Wilson fait ±30 points
(cf. §2 de la règle de mesure). Ce tableau est une **piste**, pas un résultat : il justifie
de passer les 40 cerveaux, pas d'affirmer une causalité. Et `variante_g16` la contredit
déjà partiellement : 77 % de veto avec une voix C2 **figée sur une seule action** — un veto
constant n'est pas une délibération, c'est un biais.

---

## 6. Le veto est-il utile ou vide ? — testé, et pas vide

**C2 vote massivement « poser » et « activer »** — 72 fois « poser » quand C1 veut avancer.
Or l'agent ne porte rien et il n'y a aucune porte sur `SimpleCrossing` : **ce sont des
actions sans effet dans ce monde.** D'où le soupçon : et si le « veto de C2 » consistait
surtout à imposer des gestes vides ?

Deux mesures ont été faites plutôt que de laisser la question ouverte.

### (a) La tête que C2 lit est-elle entraînée ?

Norme des 7 colonnes d'action de `generateur_attente`, sur 5 cerveaux : **0,19 à 0,44**,
sans colonne aberrante — `poser` (0,2415) et `activer` (0,2677) sont dans le même
intervalle que `avancer` (0,2642). Aucune colonne n'est morte ni gelée.

⚠️ **Un piège évité au passage** : `annexe_weight` vaut **exactement 0,000000** sur toutes
les couches des 5 cerveaux. Lu vite, ça ressemble à « rien n'a été appris ». C'est faux et
c'est normal : `cycle_sommeil` consolide l'annexe dans `base_weight` **puis la remet à
zéro**, et ces `.brain` sont sauvegardés après la nuit. L'indicateur utilisable est la
myéline — et `generateur_attente` porte **la plus forte du cerveau** (max 0,0094, contre
0,0024 pour `cortex_prefrontal`). La tête de C2 est la mieux entraînée de l'agent.

### (b) Les vetos imposent-ils des actions effectives ?

Veto **effectif** = impose gauche / droite / avancer / manger. Veto **vide** = impose
poser / activer / attendre.

| Cerveau | veto | effectif | vide | cases visitées |
|---|---|---|---|---|
| `variante_g4` | 146/400 | **145 (99 %)** | 1 (1 %) | 9 |
| `variante_g13` | 144/400 | **84 (58 %)** | 60 (42 %) | **17** |
| `variante_g16` | 301/400 | 156 (52 %) | 145 (48 %) | **18** |
| `temoin_g10` | 10/400 | 10 (100 %) | 0 | 6 |

**L'hypothèse du bruit structurel est écartée** : entre 52 % et 99 % des vetos imposent une
action qui agit sur le monde. C2 ne se contente pas de « passer son tour ».

⚠️ Deux réserves, dont une correction de ce que j'écrivais plus haut :

- **le taux de veto de `variante_g13` tombe de 92,8 % à 36 %** dans cette seconde mesure.
  L'écart vient d'un détail de protocole : ici `penser()` est appelé avant chaque tick, donc
  `gain_c1` est celui du tick courant, alors que la première passe réutilisait le `gain_c1`
  du chargement. C'est la seconde valeur qui est juste. **Le 92,8 % du §2 est donc à lire
  comme un ordre de grandeur, pas comme une mesure** — et le tableau du §5, calculé par le
  même chemin, est affecté de la même façon. Les *rangs* (témoins bas, variantes hauts) ne
  changent pas ; les niveaux, si.
- les cerveaux qui vétoient le plus visitent le plus de cases (17-18 contre 6), mais
  `variante_g4` en visite **9** avec 99 % de vetos effectifs. Le veto ne prédit donc pas
  l'exploration à lui seul.

**Ce qui reste vrai**, et qui est le point solide de cette page : chez les témoins C2 ne
détourne quasiment jamais la décision (0 %, 0 %, 6 %) ; chez les variantes il la détourne
massivement, et majoritairement vers des actions qui agissent.
