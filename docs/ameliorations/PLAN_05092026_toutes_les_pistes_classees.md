# LE PLAN — toutes les pistes pour rendre le cerveau intelligent, classées

**Date** : 2026-09-05, 23h58 · **Statut** : 🟡 **IDÉES** — aucune piste ci-dessous n'est
validée · **Écrit AVANT le verdict du chantier 1** (`--detach-c2`, 20 graines, en cours,
verdict attendu vers 07h00 le 06/09) — l'ordre est donc figé sans connaître le résultat, pour
qu'il ne soit pas réécrit en fonction de lui.

> Demande utilisateur : *« Il faut prendre en compte toutes les possibilités pour réussir à
> rendre vraiment intelligent nos cerveaux par tous les moyens. Créer un document plan de
> toutes les possibilités, de la plus probable à la moins probable. »*

---

## 0. L'objectif, reformulé

L'objectif affiché depuis août est *« franchir le niveau 5 »*. Il n'est **pas actionnable** :
**24 explications du plafond** ont été mesurées et réfutées, le tableau des suspects est vide.
Une 25ᵉ chasse à « la cause » a, sur ce dépôt précisément, une probabilité empirique
d'échec proche de 24/24.

Ce que les mesures des trois derniers jours disent, mises bout à bout :

| Fait mesuré | Source |
|---|---|
| **C2 est inerte** — δ maîtrise −1,375 pt, `t` = −1,15, n=20, C1 libre | [ABLATION_C2](../recherche/campagnes/ABLATION_C2_05092026_l_organe_muet.md) |
| **L'audio n'a jamais reçu un gradient** — 0 synapse myélinisée / 80 cerveaux | [AUDIO](../recherche/enquetes_closes/AUDIO_05092026_un_hemisphere_deja_gele.md) |
| **`Bio` pèse 2,64× la victoire** dans le gradient (60 000 nuits) | [MIXAGE](../recherche/enquetes_closes/MIXAGE_04092026_les_termes_morts_ne_sont_pas_du_code_mort.md) |
| **C1 s'atrophie chez 20/20 témoins**, masqué par `gain_c1` | [ATROPHIE](../recherche/campagnes/ATROPHIE_05092026_la_boucle_de_compensation.md) |
| **PPO 4× plus léger réussit 2,3× mieux** — au niveau 3 | [BASELINE_PPO](../recherche/campagnes/BASELINE_PPO_29082026_le_mur_n_existe_pas.md) |
| **Les victoires sont browniennes** — 14 à 18× le plus court chemin | [PLANCHER](../recherche/campagnes/PLANCHER_30082026_la_competence_existe_et_la_maitrise_ment.md) |

Ce n'est pas six problèmes, c'est **un** : *une infrastructure a poussé (bus 16 → 159, 1,5 M
de paramètres) sans que l'organe qui devait l'habiter existe.* Au bout du tuyau, la seule
chose qui décide est une tête de 8 logits — 0,53 % du réseau — qui vote presque seule.

**L'objectif proposé : faire exister un organe qui décide.** Le niveau 5 n'est pas la cible,
c'est le **juge**.

### Ce que « intelligent » veut dire, mesurablement

Trois juges, tous existants, à reporter sur **chaque** piste ci-dessous :

| Juge | Critère | Pourquoi celui-là |
|---|---|---|
| **J1 — Maîtrise** | δ apparié, `t` > 2,86 (Bonferroni 3 métriques, n=20) | seul juge non saturé au niveau 4 |
| **J2 — Directivité** | longueur du trajet victorieux / plus court chemin, vers **< 5×** | le seul prédicteur significatif du dépôt (`r` = −0,68) ; un cerveau qui *va* quelque part |
| **J3 — Le mur** | ≥ 6/15 sur ≥ 10 graines | le juge « niveau » est **saturé** (40/40 au niveau 4) : il ne parle qu'en franchissant |

⚠️ **J1 est bruité** (16 % de la variance de la compétence réelle) — d'où n=20 minimum et
jamais de conclusion sur un run en cours.

---

## 1. La méthode de classement

Chaque piste est notée sur **la probabilité qu'elle fasse bouger au moins un juge**, d'après
ce que le dépôt a déjà mesuré — pas sur son élégance ni son intérêt à coder. Quatre grades :

| Grade | Sens |
|---|---|
| 🟢 **probable** | attaque un fait mesuré, sans voisine réfutée, test peu coûteux |
| 🟡 **plausible** | attaque un fait mesuré, mais une voisine a échoué ou le lien au plafond n'est pas établi |
| 🔴 **peu probable** | hypothèse séduisante sans mesure qui la soutienne |
| ⚫ **fermé** | réfuté à n ≥ 20, ou interdit par le dogme — listé pour ne pas être retesté |

Pour chaque piste : la **faille** attaquée, les **preuves pour**, les **preuves contre**, le
passage du **dogme** (rien en dur, rien sans témoin), le **test** et son **coût**.

⚠️ **Deux lectures du classement coexistent**, et elles ne coïncident pas :
- pour le juge **J3** (franchir), les pistes *mécaniques* (§3, §4) passent devant ;
- pour l'objectif *« un cerveau complet »*, la tête de C2 (§5) est la seule qui construise
  quelque chose. PPO n'a pas de C2 et fait mieux : **C2 n'est pas nécessaire à MiniGrid**,
  c'est le projet qui le veut.

---

## 2. 🟢 PISTE 0 — les deux prérequis à coût zéro

À faire **avant tout run**, parce que chacun peut annuler des pistes entières.

### 2.a Le modèle du monde distingue-t-il les actions ?

C2 évalue ses 8 branches par `_predire_bus(pensee, action_onehot)` (`noyau.py:1103`). Si
`generateur_attente` produit quasiment le **même** bus futur quelle que soit l'action, alors
`valeur_cumulee` est du bruit **avant** toute normalisation, `C2` vote une constante (c'est
exactement ce qui a été observé : 0 % d'accord, une action constante par voix), et **aucune
tête placée sur C2 ne pourra rien y changer** — la §5 serait vide avant d'être codée.

- **Mesure** : sur 20 `.brain` existants, distance moyenne entre `_predire_bus(p, a_i)` et
  `_predire_bus(p, a_j)` rapportée à la distance entre deux `p` successifs. Zéro run.
- **Ce que ça ferme** : si ratio ≈ 0 → **le modèle du monde est aveugle à l'action** ; la
  cause de l'inertie de C2 est en amont de C2, dans JEPA. La §5 est reportée derrière un
  chantier JEPA (perte contrastive sur l'action, pas sur l'état).

### 2.b Le tronc reçoit-il un gradient de la décision ?

`TRONC_PERCEPTIF_DETACHE = True` : l'acteur et le critique **ne rétropropagent jamais**
jusqu'à `porte_visuelle`. Seul JEPA sculpte la perception. Le tronc connecté a été testé
(bruit +48 %, niveau δ = 0,00) — mais au **régime témoin**, avec un C1 qui s'atrophiait.
Ce n'est pas une piste à relancer, c'est un fait à garder en tête pour lire §3 et §5 : *la
perception n'est pas formée par ce qui sert à décider.* Coût : zéro, c'est une lecture.

---

## 3. 🟢 PISTE 1 — la nuit ne fait que DEUX pas de gradient

**La faille.** `apprendre_journee` fait **un** `optimizer.step()` (`noyau.py:1954`), `rever`
en fait **un** (`:2007`). Une vie de 1500 jours = **~3 000 pas d'optimiseur** pour
**600 000 ticks**. Un PPO standard sur le même budget en fait de l'ordre de **10⁵** (10
époques × minibatches par rollout). **Cette différence n'a jamais été mesurée ni testée** —
elle n'est dans aucune des 24 réfutations.

**Pour.**
- La baseline PPO est la mesure la plus forte du dépôt : **4× moins de paramètres, 2,3×
  mieux**. La différence n'est donc pas la *capacité* ; ce qui reste, c'est l'**usage des
  données**. Le crédit temporel (MC/TD/GAE), l'entropie, la normalisation par épisode ont
  été testés et réfutés — le **nombre de passages** sur les données, jamais.
- Le rêve est déjà l'ébauche de ce mécanisme (rejeu nocturne à porosité adaptative), mais
  il ne fait qu'**un** pas lui aussi.

**Contre.**
- Plusieurs époques de policy gradient Monte-Carlo **sans ratio d'importance** divergent —
  c'est précisément pourquoi PPO clippe. Tester « plus de pas » impose de tester « avec
  quel garde-fou » : deux variables, donc **trois bras** (règle §6.2).
- Sur-apprentissage d'une journée de 400 ticks : possible, non mesuré.

**Dogme.** Un nombre d'époques est une **constante posée** — exactement ce que le rêve a
refusé. La forme finale doit **émerger** (de la plasticité dopaminergique, comme
`pourcentage_reve`). Mais la méthode v30.1 impose de **mesurer le fixe avant de dériver** :
d'abord `--epochs-nuit K` à K fixe pour établir que l'effet *existe*, ensuite seulement la
dérivation.

**Test.** 3 bras × 20 graines × 1500 j : témoin · K=8 sans clip · K=8 avec ratio clippé.
Coût : **~12 h** (60 runs, 6 parallèles). Témoin atteint : compter les `step()` dans le log
de nuit (assertion runtime).

**Probabilité : 🟢 la plus haute du document pour J1/J3**, parce qu'elle explique le fait
le plus dur (PPO) par le mécanisme le plus simple, et qu'aucune mesure ne l'a encore touché.

---

## 4. 🟢 PISTE 2 — le mur est-il `LavaGapS5` ?

**La faille.** Le niveau 4, où **40 runs sur 40** s'arrêtent, est `MiniGrid-LavaGapS5-v0`.
La baseline PPO qui établit que « le mur n'existe pas » a été faite sur
`SimpleCrossingS9N1` — le **niveau 3**, que Naulthène **franchit** (20/20 en régime libre,
A_g66 à 37 % dans la fourchette de PPO). *« Le mur n'existe pas »* est donc une
**extrapolation** d'un niveau à l'autre, jamais mesurée au niveau du mur.

**Pour.**
- `LavaGapS5` est le niveau le plus étudié du dépôt côté **corps** : la mort y paie
  **0,0** (un mur coûte −0,01), **aucune case n'y est indolore** (77 % à distance 1 de la
  lave), et la nociception y a coûté **−25 % de récolte**. Un agent homéostatique dont
  `Bio` pèse 57 % du gradient a, sur cette carte-là, une raison de **ne pas bouger**.
- « 10/10 au niveau 4, 0 au niveau 5 » (v41.29) et « 40/40 au niveau 4 » (04/09) disent
  la même chose : **personne ne gagne deux fois de suite sur LavaGapS5**.

**Contre.**
- Les victoires sont browniennes **aussi au niveau 3** — le défaut de directivité ne
  vient pas de la lave.
- La maîtrise intra-palier au niveau 4 ne monte **jamais** (trois mesures sur ~700 j) ; un
  mur architectural donnerait le même profil.

**Test — deux mesures, aucune ligne de code neuve.**
1. `banc_ppo` sur `LavaGapS5` (le banc existe, v41.38) : **~1 h**. Si PPO plafonne aussi →
   le mur est le **niveau**, et tout ce document se réordonne.
2. Cursus complet avec `LavaGapS5` **déplacé** après `Fetch`/`GoToDoor` (le remappage par
   `env_id` de `persistance` rend la permutation sûre pour les `.brain`). 20 paires, ~8 h.
   Si les cerveaux atteignent le 6 en contournant la lave → le plafond n'était pas *un*
   plafond, c'était *une carte*.

**Probabilité : 🟢** — pas parce qu'elle est la plus probable d'être *vraie*, mais parce
qu'elle est la moins chère et qu'elle **conditionne l'ordre de toutes les autres**.

---

## 5. 🟢/🟡 PISTE 3 — la tête vectorielle d'intention de C2 *(chantier 2)*

**La faille.** `cortex_prefrontal : dim_bus → 1` est un **critique** : il ne peut dire que
*« ça va bien / ça va mal »*, jamais *« va par là »*. Et sa seule voie d'expression est une
**addition** sur les logits de C1 — d'où le conflit frontal mesuré (0 % d'accord, chaque
voix votant une constante, ratio 9,9× à 22,1× avant la v37). Détail structurel supplémentaire,
lu dans le rollout (`noyau.py:1141-1180`) : après le premier pas, chaque branche est
**poursuivie par l'argmax de `tete_motrice`**. C2 n'évalue donc jamais *ses* plans — il
évalue *« que se passe-t-il si je fais `a` puis laisse C1 conduire »*. Un C1 brownien donne
à C2 huit futurs browniens à départager.

**Pour.**
- C'est le seul organe délibératif, et le cœur de la thèse. Tout le reste est réglage.
- L'ablation propre (05/09) a rendu le verdict sans ambiguïté : **inerte**, effet minimal
  détectable 3,42 pt. Il n'y a rien à *réparer*, il y a quelque chose à *construire*.

**Contre — à ne pas cacher.**
- **PPO n'a pas de C2 et réussit 2,3× mieux.** Pour le juge J3, C2 n'est pas nécessaire.
- Une tête `dim_bus → 8` à côté de `tete_motrice` risque d'être **un second C1** — même
  entrée, même sortie, même gradient. Ce qui la distingue doit être ce qu'elle *voit* :
  les **futurs imaginés** (`pensee_branche` par branche), pas l'état courant.
- 25ᵉ hypothèse.

**Les trois invariants posés (utilisateur, 05/09).**
1. **Indépendance de la baseline** : ne jamais élargir `cortex_prefrontal` — une tête
   **à côté**, jamais à la place ([c2-petit-par-construction](../../CLAUDE.md)).
2. **Contournement de la queue viscérale** : ne pas passer par une dimension en queue
   d'`integrateur_bio` — deux ajouts passifs, deux effets nuls à n=20.
3. **Modulation, pas addition** : la sortie agit comme un **filtre** sur `voix_c1`
   (multiplicatif ou routage), jamais comme un terme sommé.

**Esquisse — à détailler dans un document de conception séparé.**
- `tete_intention : dim_bus → num_actions`, nourrie de la `pensee_branche` **finale** de
  chaque branche du rollout (elle voit 8 futurs, C1 en voit 0).
- Sortie passée par une sigmoïde, appliquée **multiplicativement** à `voix_c1` : une
  intention à 1 laisse C1 parler, une intention à 0 lui coupe la parole sur cette action.
  C'est une porte, pas une voix — donc pas de conflit d'échelle, donc `gain_c1` n'a rien à
  compenser.
- Apprentissage : le même policy gradient, à travers la porte ; **`.detach()` sur la cible
  de distillation** conservé (invariant v37.0-4).
- Témoin : `--sans-intention` (porte à 1 partout, bit-identique au régime libre).

**Dogme.** Aucun seuil : la porte est apprise, continue, jamais un `if`. ⚠️ Le
prérequis §2.a doit passer d'abord — sinon la tête modulera à partir de futurs que le
modèle du monde ne distingue pas.

**Test.** 20 paires × 1500 j, ~8 h. Juges J1 et J2 (une intention qui marche doit d'abord
rendre les trajets **moins browniens**).

**Probabilité : 🟡 pour J3, 🟢 pour l'objectif « cerveau ».** Classée ici, et non première,
parce qu'elle dépend de §2.a et parce que la preuve PPO joue contre sa nécessité.

---

## 6. 🟢/🟡 PISTE 4 — l'échelle de `Bio` dérivée du corps

**La faille.** Les 11 termes de `recompense_interne` (`noyau.py:10011`) sont sommés **à
poids 1**. Dispersion réelle : `Bio` 57,0 %, `Env` 21,6 %. Le corps pèse **2,64×** la
victoire dans le gradient.

**Pour.** Mesure directe sur 60 000 nuits, 40 runs — la plus solide du dépôt sur le signal
d'apprentissage. PPO, sans corps, fait mieux : c'est un argument pour la lecture
« pathologie ».

**Contre.** `maîtrise ~ énergie` réfutée **deux fois** (r = −0,0588 à n=20) : le corps ne
semble pas *gêner*. Un organisme homéostatique consacre *réellement* l'essentiel de son
apprentissage à ne pas mourir. **Le ratio n'est pas tranché** — c'est précisément pourquoi
c'est une piste et pas une correction.

**Dogme.** ⚠️ **Jamais de normalisation par σ** — ce serait poser une pondération à la place
d'une autre. L'échelle doit être **dérivée** : le précédent est `GAIN_MINIMAL_VICTOIRE /
max_steps` (v41.43). Candidat : rapporter `r_bio` au **déficit maximal survivable**
(`calculer_deficit` au point de mort), de sorte qu'un tick de faim vaille une fraction
mesurable d'une vie, comme un tick de piétinement vaut une fraction d'une victoire.

**Test.** 20 paires, ~8 h. Témoin `--bio-fossile` (échelle actuelle), assertion runtime.
Juge J1 ; J3 si le blocage était bien l'immobilité de survie (§4).

**Probabilité : 🟡, 🟢 si §4 (PPO sur LavaGap) montre que Naulthène s'y immobilise.**

---

## 7. 🟡 PISTE 5 — la table de mixage des PERTES

**La faille.** Il y a une **seconde** table de mixage, jamais mesurée : `perte_totale` =
JEPA + `COEFF_PERTE_VOCALE` × vocal + acteur + critique + entropie + `TAUX_DISTILLATION_C1` ×
distillation (`noyau.py:1794-1946`), **un seul Adam, un seul `lr`**. Six gradients d'organes
différents dans le même pas.

**Pour.** Même pathologie que la récompense, un étage plus bas. L'entropie a déjà été
mesurée à **0,44–1,05 %** du gradient de l'avantage — la sonde existe, elle n'a pas été
passée sur les six termes.

**Contre.** Le tronc est détaché, donc JEPA et RL touchent surtout des couches **distinctes**
— le mélange ne se fait que dans les couches du rollout (`hippocampe`, `analyseur`,
`integrateur_bio`). L'effet est peut-être local.

**Test.** Sonde de gradient par terme et par couche, **zéro run** (sur 20 `.brain`, une
journée rejouée). Puis, seulement si un terme écrase les autres : un `lr` par organe,
dérivé de la norme de gradient mesurée, jamais posé.

**Probabilité : 🟡** — coût nul pour la mesure, gain incertain pour les juges.

---

## 8. 🟡 PISTE 6 — la perméabilité d'`integrateur_bio` *(chantier 0 du plan v41.32)*

**La faille.** `integrateur_bio : dim_bus + DIM_VECTEUR_BIO → dim_bus`. Deux ajouts en queue
du vecteur bio (bit de portage, ancrage cinématique) ont donné **deux effets nuls à n=20**.
L'hypothèse de dilution n'a jamais été **mesurée** : quelle part du gradient de la décision
atteint chaque tranche d'entrée (vue · jauges · odorat · thermoception · rappel marquant) ?

**Pour.** Si les tranches sensorielles reçoivent ~0 de gradient, alors **les cinq sens sont
décoratifs** : l'agent joue à la vue seule, et tout le chantier sensoriel v29–v41 est inerte
comme l'audio l'était. C'est le même type de découverte que l'audio, au même coût.

**Contre.** Ce serait un diagnostic, pas un levier — il dirait *où* le signal meurt, pas
comment le ranimer.

**Test.** Sonde, zéro run : norme du gradient de `perte_acteur` par colonne d'entrée de
`integrateur_bio`, 20 cerveaux. Ensuite seulement, si dilution : une porte par sens dans le
tronc (⚠️ **invariant v29.0-3**, exige une demande utilisateur explicite).

**Probabilité : 🟡** pour les juges, **🟢 pour la connaissance** — et elle peut fermer §5
(si le rappel marquant est inerte, une intention nourrie du même bus le sera).

---

## 9. 🟡 PISTE 7 — la directivité : donner l'INFORMATION du chemin, pas une pénalité

**La faille.** Victoires à 14–18× le plus court chemin ; `Stagnation` pèse **0,6 %** du
gradient. L'agent ne sait pas où il est déjà passé — `historique` spatial n'existe que dans
la mémoire à repères, jamais dans ce que C1 voit à chaque tick.

**Pour.** J2 est le seul prédicteur significatif du dépôt (`r` = −0,68). Une trajectoire
dirigée exige de *percevoir* sa propre trace.

**Contre.** ⚠️ Corrélationnel : à λ=0,9 la **meilleure** directivité allait avec le **pire**
succès (v41.47). La directivité peut être un *symptôme*. Et la seule voie naturelle — une
dimension « trace de pas » en queue du vecteur bio — est **exactement** celle qui a échoué
deux fois.

**Dogme.** Un sens, jamais une récompense : durcir `penalite_stagnation` serait poser une
constante de plus. La trace doit être **perçue** (un canal, comme l'odorat rayonne), pas
facturée.

**Test.** Bloqué par §8 : tant que la perméabilité n'est pas mesurée, un canal de plus en
queue est un troisième effet nul annoncé.

**Probabilité : 🟡, conditionnelle à §8.**

---

## 10. 🟡 PISTE 8 — le professeur PPO : la distillation comme DIAGNOSTIC *(P5, le parent)*

**La faille.** Le dépôt possède déjà un canal de distillation sélective C2 → C1
(`_ponderer_distillation`, v37.1) et une politique compétente (PPO, `banc_ppo`). Personne
n'a jamais branché l'une sur l'autre.

**Pour.** Ce n'est pas un levier, c'est **l'expérience qui sépare les deux familles
d'explications restantes**. Si C1, nourri d'une politique PPO par le canal existant,
**franchit** le niveau 5 → le corps et la perception suffisent, c'est le **signal
d'apprentissage** qui manque (→ §3, §6). S'il **plafonne quand même** → l'information ne
passe pas par `integrateur_bio` (→ §8), quelle que soit la politique.

**Contre.** Change la question : un cerveau qui apprend d'un maître n'est plus « un cerveau
qui apprend seul ». À ne présenter que comme instrument, jamais comme résultat. Et
l'assistanat **atrophie** (parent nourricier v38-2c : mémoire ÷ 6) — le bras doit être
**sevré** avant d'être jugé.

**Test.** 20 paires : PPO-professeur pendant 500 j puis sevrage, contre témoin. ~8 h + le
temps d'écrire le pont PPO → `pensee_bio` (non trivial : PPO lit l'observation, pas le bus).

**Probabilité : 🟡 comme levier, 🟢 comme instrument.**

---

## 11. 🔴 PISTE 9 — l'élagage dur

Mesuré : **0 synapse morte sur 259 329**. L'érosion géométrique et le plancher vital
l'empêchent structurellement. **Mais aucun lien à un juge n'est établi** — c'est un écart
avec la biologie, pas une cause mesurée. Test possible (seuil d'élimination sous X % de la
norme de couche, 20 paires, ~8 h), ⚠️ le X est une constante posée. Voir
[NEUROSCIENCES §1](NEUROSCIENCES_05092026_developpement_et_heredite.md).

## 12. 🔴 PISTE 10 — le bus plafonné

`r(dim_bus, maîtrise)` = +0,50 mais `r(dim_bus, victoires)` = **+0,68** et le signe s'inverse
entre bras : le bus mesure la **survie**. Figer `dim_bus` à 64 contre neurogenèse libre (20
paires) répondrait à « la neurogenèse aide-t-elle ? », pas à « qu'est-ce qui bloque ? ».

## 13. 🔴 PISTE 11 — l'hérédité `W₀` et les lignées

Principe retenu (hériter les poids initiaux, jamais l'expérience), **jamais testé**, coût
non chiffré (une campagne par génération). C'est la seule voie pour tester l'**empreinte
précoce** (3 témoins figés au jour 2-3) — mais l'empreinte n'a pas été reliée au plafond :
les 3 bloqués ont une maîtrise *supérieure* aux 17 autres.

## 14. 🔴 PISTE 12 — les périodes critiques

Plasticité décroissante avec l'âge, fenêtres sensibles par organe. Séduisant, **aucune
mesure** dans le dépôt — pas même la courbe de myéline en fonction de l'âge, qui serait le
prérequis (zéro run). À mesurer avant d'en parler.

## 15. 🔴 PISTE 13 — l'Exo-Sens LLM comme professeur (C3)

Le port existe (`exocortex/`), la perception est continue et sans seuil (invariant v30.0).
Un LLM y injecterait 8 dims — **en queue du vecteur bio**, la voie qui a échoué deux fois
(§8). Bloqué par la perméabilité, et coûteux (latence réseau × 600 000 ticks).

## 16. 🔴 PISTE 14 — remplacer une brique du cœur (CNN, GRU, attention)

`porte_visuelle` est **linéaire** sur 147 dims ; PPO a un CNN. Mais `r(d', réussite)` =
**−0,04** chez PPO, qui réussit 2,3× mieux avec un d' 4,5× plus faible : la qualité de la
représentation **ne prédit rien**. Remplacer le cœur abandonne la thèse (une seule règle de
plasticité) pour un gain non prédit par les mesures.

## 17. 🔴 PISTE 15 — la recherche évolutive sur les constantes libres

La seule façon de *dériver* sans *poser*… mais chaque évaluation coûte 20 graines × 1500 j.
Une génération = 8 h par candidat. Hors de portée sur une machine à 6 processus.

## 18. ⚫ PISTE 16 — la 3D temps réel

Différée par décision utilisateur (05/09). Déclencheur : **un franchissement du niveau 5-6
reproductible**. Un cerveau qui n'exploite pas 15 cases n'exploitera pas un monde continu.

---

## 19. ⚫ Ce qui est FERMÉ — à ne pas retester

| Piste | Verdict | n |
|---|---|---|
| Thrashing du gradient (AB3, detach asymétrique) | `t` = −0,70, seul `t` significatif tautologique | 20 |
| Crédit temporel (TD(0), GAE) | MC est le moins mauvais des trois | 20 |
| Tronc connecté (attention descendante) | bruit +48 %, niveau δ = 0,00 | 20 |
| Dérive de représentation | `r` = +0,14 NS ; PPO dérive 10× plus | 20 |
| Coefficient d'entropie | 0,44–1,05 % du gradient de l'avantage | — |
| `maîtrise ~ énergie` | +0,710 à n=10 → **−0,0588** à n=20 | 20 |
| La curiosité (rente 40 %) | 15,0 % vs 15,0 % de maîtrise | 40 |
| Récompense creuse | prémisse fausse : 86 % du signal est dense | 60/60 |
| Le barème (`part_monde`) | tautologie | 40 |
| Rendement mécanique · ancrage cinématique | livrés puis réfutés | 20 + 20 |
| Rebond d'entropie au changement de carte | réfuté à coût zéro | — |
| La voix libre en cursus | mur intact, effet tombe sans les extrêmes | 20 |
| Le « cerveau obèse » | signe positif, et il mesure la survie | 18 |
| **Amputer l'audio** | aucun gradient ne l'a jamais traversé → **aucun effet comportemental possible** ; ce serait de la mémoire gagnée, pas de l'intelligence | 80 |
| **Supprimer les 5 termes morts** | capteurs hors domaine, nécessaires au niveau 6-7 | 60 000 nuits |
| **Normaliser par σ** | interdit — pose une pondération à la place d'une autre | — |
| **Un seuil / un `if` dans le chemin de décision** | interdit — refusé trois fois (v28, v29, v30) | — |
| `--detach-c2` en régime libre | **en cours** — prédiction pré-enregistrée : probablement rien | 20 |

---

## 20. L'ordre d'exécution proposé

```
J0  (zéro run)   §2.a sensibilité JEPA à l'action  ·  §7 sonde des pertes  ·  §8 perméabilité
J0  (~1 h)       §4.1 PPO sur LavaGapS5
     │
     ├─ PPO plafonne aussi ──► le mur est la carte : §4.2 (permutation) passe devant tout
     │
     └─ PPO franchit ─────────► le mur est l'architecture :
                                 §3 (pas d'optimiseur, 3 bras)  ∥  §6 (échelle Bio)   ~12 h + 8 h
                                 puis §5 (tête d'intention), si §2.a a passé
                                 §10 (professeur PPO) en arbitre si §3 et §6 échouent
```

Trois règles, toutes déjà payées :
- **Un LISEZ_MOI par campagne, écrit avant le lancement**, avec les juges et la prédiction.
- **Jamais deux mécaniques dans un bras** — §3 en exige déjà trois.
- **Aucun chiffre de ce document n'est un résultat.** Tout ce qui précède est une
  hypothèse jusqu'à n=20, run terminé, `t` corrigé.

---

*Écrit à 23h58 le 05/09/2026, six runs `--detach-c2` au jour ~620. L'ordre ci-dessus ne sera
pas modifié après le verdict — s'il le contredit, on l'écrira en dessous, avec la date.*

---

# ADDENDUM DU 06/09/2026 — ce que la nuit a mesuré

> Écrit **après** les mesures, comme annoncé en tête : *« s'il le contredit, on l'écrira en
> dessous, avec la date »*. L'ordre original (§20) n'a pas été modifié.
> Campagne `--detach-c2` toujours en cours (~jour 1000/1500) au moment d'écrire.

## Ce qui a été fait cette nuit — 4 mesures, ~40 min de calcul

| Piste | Verdict | Détail |
|---|---|---|
| **§4.1 PPO sur `LavaGapS5`** | ❌ **hypothèse réfutée** | PPO **97,27 %** (n=5, δ_A/A=0) contre 6,67 % aléatoire. [Carnet](../recherche/campagnes/PPO_LAVAGAP_06092026_le_mur_n_est_pas_la_carte.md) |
| **§2.a JEPA distingue-t-il les actions ?** | ✅ **oui — §5 débloquée** | ratio 0,48 (médiane 0,46, aucun cerveau < 0,10) |
| **§8 dilution d'`integrateur_bio`** | ❌ **réfutée** | le corps pèse **2,5 à 5,6×** la vision |
| **§7 table de mixage des pertes** | 🔴 **résultat fort** | le critique prend **89,24 %** du gradient d'`integrateur_bio`, 40/40 cerveaux |

## Les trois corrections à apporter au plan

### 1. 🔴 §4 (le mur est la carte) est FERMÉE — et le constat s'aggrave

PPO résout `LavaGapS5` à **97,27 %** là où Naulthène ne franchit **jamais** (40/40 runs).
Au niveau 3 l'écart était de 2,3× ; au niveau 4 il est total. **L'écart se creuse avec la
facilité de la tâche.** La permutation du cursus (§4.2) perd sa justification.

### 2. 🔴 §7 (la trace du chemin) perd SA justification, pas sa pertinence

Elle était classée « bloquée par la dilution ». **Il n'y a pas de dilution.** Si un canal
de plus échoue, ce sera pour une autre raison — et la démonstration est déjà là : `élan`
pèse **3,41×** la vision et son effet fut **nul à n=20**. **Une norme n'est pas un usage.**

### 3. 🟢 UNE PISTE NEUVE, absente du document original

**Découpler le gradient du critique de celui de l'acteur dans `integrateur_bio`.**
Le critique y prend **89,24 %** contre **6,57 %** — 40 cerveaux sur 40, médiane 11,50×.
Cette couche est **l'entrée unique de la décision**.

⚠️ **Et le run en cours la teste déjà** : `--detach-c2` coupe exactement cette voie
(`noyau.py:1556`). La piste sera donc **ouverte ou fermée par le verdict**, sans run
supplémentaire.

## Ce qui n'a PAS changé

- L'ordre §20 reste valide pour la branche « le mur est l'architecture » — qui est
  désormais **la seule** puisque §4 est fermée.
- **§3 (la nuit ne fait que deux pas de gradient) reste la piste 🟢 la plus haute** et
  n'a **pas** été touchée cette nuit. Elle sort même renforcée : si PPO résout à 97 % une
  carte que Naulthène ne franchit jamais, l'écart d'**usage des données** est le candidat
  qui reste debout.
- §5 (tête d'intention) est débloquée mais reste derrière §3.

## 🔴 Un fait nouveau qui n'était dans aucune hypothèse

**Le levier de l'agent s'efface au fil de l'apprentissage** : la sensibilité de JEPA à
l'action est divisée par **10** entre un cerveau neuf (4,79) et un cerveau de 1500 jours
(0,48) — `δ_action` ÷5 pendant que `δ_temps` ×2,5.

⚠️ **Non interprété** : cette décroissance peut être **saine** (un bon modèle du monde
apprend que la plupart des actions ne changent rien). Il manque le ratio d'un modèle du
monde **compétent**, qui n'existe pas dans le dépôt. À ne pas citer comme pathologie.

---

*4 mesures, 0 run de cursus, ~40 min. Les trois sondes créées sont réutilisables :
`sonde_jepa_action.py`, `sonde_permeabilite_bio.py`, `sonde_mixage_pertes.py`.*
