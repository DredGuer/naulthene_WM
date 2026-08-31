# La cohorte du barème — dix-septième réfutation, en une heure

**30/08/2026** · 40 cerveaux lus, 0 run lancé · document de `recherche/` : **non normatif**

## Question posée

L'[audit du génome](../../etat_des_lieux/30082026_le_genome_audit_des_constantes.md) avait
mesuré, **sur un seul cerveau**, que **95,6 % du signal d'apprentissage vient de constantes
posées** et **4,4 % du monde**. Sur le niveau du plafond, MiniGrid verse `0.0000` sur
800 ticks.

Hypothèse à tester : **un cerveau qui écoute un peu plus le monde s'en sort-il mieux ?**

---

## Verdict en une phrase

> ❌ **Non — et la corrélation qui semblait le dire est une TAUTOLOGIE.**
> `part_monde` ne mesure pas « l'écoute du monde » : elle mesure **avoir gagné**, puisque
> MiniGrid ne verse une récompense qu'à la victoire. Corréler cela à la maîtrise — un taux
> de victoire — revient à corréler la victoire avec elle-même. **Dix-septième réfutation.**

---

## Pourquoi ce protocole plutôt qu'une campagne

L'option évidente était de **couper la curiosité** et d'observer. Elle a été écartée
**avant** de brûler du calcul :

> Retirer la curiosité, c'est retirer **~40 % du signal positif**. L'agent s'effondrerait à
> coup sûr — un effet énorme et **ininterprétable**. « Un cerveau privé de signal va moins
> bien » n'apprend rien sur le plafond. C'est une ablation dont le résultat est **connu
> d'avance**.

À la place : **aucun run**. Les 40 cerveaux de la cohorte AB3 (26/08) existent déjà. On lit
la **variation naturelle** entre eux et on demande si elle prédit la performance **déjà
journalisée**. Coût : ~25 min de lecture contre ~48 h de campagne.

**C'est la méthode qui avait donné la quinzième réfutation** (la dérive) : une corrélation
est falsifiable dans les deux sens ; une description plus fine du phénomène ne l'est pas.

---

## Protocole

| Élément | Valeur |
|---|---|
| Cohorte | `brains/26082026_v4132_AB3_cursus` — **20 graines × 2 bras = 40 cerveaux** |
| Doublons Finder (`X 2.brain`) | **exclus** — ce sont les mêmes runs |
| Niveau mesuré | **3** (`SimpleCrossingS9N1`, le plafond), forcé pour tous |
| Durée | 2 jours = **800 ticks** par cerveau |
| Lecture | `sonde_recompense` **corrigée du 30/08**, en sous-processus isolé |
| Écriture | **aucune** — chaque `.brain` est lu depuis une **copie** |
| Performance | lue **dans** le `.brain` (`historique_episodes_niveau`), jamais recalculée |

⚠️ **Vérification préalable exigée avant lancement** : que la sonde nettoyée soit bien celle
qui lit la cohorte. Contrôlé sur trois plans — le fichier sur disque (0 ligne de code vivant
contenant `MALUS_DOULEUR`), le `__pycache__` **purgé**, et le module réellement chargé en
mémoire (`'MALUS_DOULEUR' in inspect.getsource(...)` → `False`).

**Sous-processus par cerveau, et c'est délibéré** : `sonde_recompense` installe un
`sys.settrace` global. Mutualiser le processus ferait fuir l'état d'un cerveau sur le
suivant, **en silence**.

---

## Test préalable — la variable indépendante varie-t-elle ?

Le piège de l'**ablation vide** (bit de portage, 16 runs perdus) est vérifié **avant** toute
corrélation :

| | Bras A | Bras B |
|---|---|---|
| moyenne `part_monde` | 15,53 % | 10,48 % |
| écart-type | 13,09 pt | 7,66 pt |
| étendue | **41,79 pt** | **24,52 pt** |

✅ **La variable varie largement.** La corrélation a un sens — ce n'est pas une mesure vide.

---

## Résultats bruts

| Prédicteur | n=40, r | t | Réplique A/B ? |
|---|---:|---:|---|
| **part du MONDE** | **+0,4191** | **+2,85** 🔴 | ✅ **oui** (+0,45 / +0,41) |
| part CURIOSITÉ | −0,0173 | −0,11 | ❌ **le signe s'inverse** (+0,23 / −0,26) |
| solde hors monde | +0,3745 | +2,49 🔴 | ✅ oui (+0,47 / +0,31) |

Seuil de Bonferroni (3 métriques, n=40) : **|t| ≥ 2,39**.

À ce stade, `part_monde` passait le seuil **et** répliquait dans les deux bras — le profil
d'un résultat solide.

---

## 🔴 Le test de tautologie — et l'effondrement

> **Un résultat favorable se vérifie deux fois plus qu'un défavorable** (règle de mesure §3).

MiniGrid ne verse `recompense_env` **que** lorsque l'agent atteint le but. Donc :

```
part_monde > 0   ⟺   « ce cerveau a gagné pendant les 800 ticks mesurés »
maîtrise         =   taux de victoire sur 20 épisodes
```

**Les deux mesurent la victoire.** La corrélation était structurellement garantie.

| Vérification | r | t | n |
|---|---:|---:|---|
| Toute la cohorte | +0,4191 | **+2,85** 🔴 | 40 |
| **Chez les seuls cerveaux ayant gagné** (`part_monde > 0`) | **+0,3722** | **+2,34** | **36** |

Conditionnellement au fait d'avoir gagné, **le signal passe SOUS le seuil** (2,34 < 2,39).
Ce que la corrélation captait n'était pas *combien* le cerveau écoute le monde, mais
**s'il a gagné au moins une fois** :

| Groupe | Maîtrise moyenne | n |
|---|---:|---:|
| `part_monde > 0` | **14,17 %** | 36 |
| `part_monde = 0` | **5,00 %** | 4 |

Toute la corrélation tient dans ces **4 cerveaux** qui n'ont jamais gagné.

> **C'est exactement la tautologie du ratio C2/C1 (v41.32)** — un `t = +3,82` dont la
> décomposition montrait qu'il mesurait sa propre définition. Deuxième occurrence du même
> piège en une semaine : une métrique dérivée de la récompense **ne peut pas** servir à
> prédire la réussite, puisque la récompense **est** la réussite.

`solde hors monde` souffre du même défaut : `t` chute de **+4,13 → +2,27** dès qu'on retire
la récompense du monde du bras A.

---

## Ce qui reste vrai — et non tautologique

Trois faits survivent, mesurés sur les 40 cerveaux :

1. **La curiosité ne prédit RIEN, et son signe s'inverse entre les deux bras**
   (+0,23 contre −0,26). Ce n'est même pas un effet faible : c'est du bruit. Elle pèse
   pourtant **40,4 %** du signal positif en moyenne (min 20,0 %, max 64,6 %).

2. **`PENALITE_STAGNATION_BASE` porte 100 % du coût sur 40 cerveaux sur 40.** Une seule
   constante posée, à `0.015`, est **l'unique force négative** de toute la cohorte. Il n'y a
   aucune variation à corréler — c'est le seul terme rigoureusement invariant.

3. **La part du monde reste dérisoire** : moyenne **13,0 %**, médiane 9,7 %, et **4 cerveaux
   sur 40 à exactement 0,00 %**. Le constat de l'audit du génome tient à n=40 — il est
   seulement **sans pouvoir prédictif**.

État de la cohorte : maîtrise moyenne **13,25 %** (max 45 %, 5 cerveaux à 0 %), niveaux
atteints `{2: 2, 3: 32, 4: 6}`.

---

## Ce que cela change pour la suite

| Ce qui est acquis | Statut |
|---|---|
| « écouter le monde prédit la réussite » | ❌ **réfuté** (tautologique) |
| « la curiosité nuit à la performance » | ❌ **réfuté** (signe instable entre bras) |
| « 95,6 % du signal vient de constantes posées » | ✅ **confirmé à n=40** |
| Le tableau des suspects | **toujours vide** |

⚠️ **L'audit du génome n'est pas invalidé** : sa mesure descriptive tient et se généralise.
Ce qui est réfuté, c'est **l'hypothèse causale** qu'on pouvait en tirer.

**Ce qui n'est PAS testé par cette campagne** : la variation *entre cerveaux* est faible
(tous ont le même barème, seuls leurs vécus diffèrent). Un barème **structurellement
différent** — pas juste un cerveau qui écoute un peu plus — reste non testé. Mais cela exige
une campagne A/B, et **rien dans ces 40 lectures ne la justifie**.

---

## Limites

1. **La maîtrise est lue au niveau COURANT du cerveau**, pas au niveau 3 forcé par la sonde.
   5 cerveaux sur 20 (bras A) sont ailleurs. Sur la sous-cohorte propre (n=15, niveau 3
   réel), `part_monde` tombe à **`t = +1,21`** — conforme au verdict, mais **n=15 est sous la
   barre des 20 graines** et cette sous-analyse ne vaut donc que comme corroboration.
2. **Mesure directe, jamais comparaison appariée** (§4 de la règle de mesure). Aucune
   causalité n'est établie ici, dans aucun sens.
3. **Un seul niveau mesuré** (le 3). Le barème pourrait se comporter autrement ailleurs —
   l'audit du génome montre 6,65 % / 0,00 % / 6,08 % sur les niveaux 0/3/4.
