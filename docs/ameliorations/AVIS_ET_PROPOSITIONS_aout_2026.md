# Avis & Propositions — 13 août 2026

> **Nature du document** : carnet de recherche, non normatif. Il contient deux choses :
> l'**avis complet** rendu sur le projet après la campagne des 11-13 août, et les
> **propositions de solutions** aux problèmes identifiés dans
> [ETAT_DU_PROJET_aout_2026.md](../recherche/ETAT_DU_PROJET_aout_2026.md).
>
> **La règle du jeu, posée par l'utilisateur** : *« Zéro limite, mais la seule condition :
> rien ne doit être écrit en dur si ça peut émerger. »* Chaque proposition est donc jugée
> à cette aune — et celles qui ne la respectent pas sont écartées d'office, même
> séduisantes.
>
> Rien ici n'est implémenté. Ce sont des propositions à discuter, prioriser, puis mesurer
> une par une — jamais empilées (leçon §3.2 de l'état des lieux : les gains ne
> s'additionnent pas).

---

## Sommaire

- [Partie I — L'avis](#partie-i--lavis)
  - [1. Ce que le projet a de véritablement rare](#1-ce-que-le-projet-a-de-véritablement-rare)
  - [2. Ce qui me préoccupe](#2-ce-qui-me-préoccupe)
  - [3. Le jugement d'ensemble](#3-le-jugement-densemble)
- [Partie II — Les propositions](#partie-ii--les-propositions)
  - [P0. Ce que la règle exclut d'office](#p0-ce-que-la-règle-exclut-doffice)
  - [P1. Versionner le cerveau](#p1--versionner-le-cerveau-préalable-non-négociable)
  - [P2. Dompter la variance sans la tuer](#p2--dompter-la-variance-sans-la-tuer)
  - [P3. La campagne de soustraction](#p3--la-campagne-de-soustraction--le-cerveau-minimal)
  - [P4. Le monde qui exige : nuit, digestion, saisons, apparences](#p4--le-monde-qui-exige--nuit-digestion-saisons-apparences)
  - [P5. Le parent émergent : l'aîné incarné](#p5--le-parent-émergent--laîné-incarné)
  - [P6. Le liage réparé : le temps comme superviseur, le rêve comme atelier](#p6--le-liage-réparé--le-temps-comme-superviseur-le-rêve-comme-atelier)
  - [P7. L'écoute de C2 comme synapse](#p7--lécoute-de-c2-comme-synapse-conditionnel)
  - [P8. Penser coûte : le métabolisme de la délibération](#p8--penser-coûte--le-métabolisme-de-la-délibération)
  - [P9. Les invariants exécutables](#p9--les-invariants-exécutables)
  - [P10. Le test de concept](#p10--le-test-de-concept--enfin-possible)
  - [P11. Ne pas jeter l'abstraction avec les coordonnées](#p11--ne-pas-jeter-labstraction-avec-les-coordonnées-issue-de-p2b-mesurée)
  - [P12. Le prior d'empreinte : brancher le consommateur](#p12--le-prior-dempreinte--brancher-le-consommateur)
  - [P13. Le bit de présence auditive](#p13--le-bit-de-présence-auditive--le-calme-enfin-perçu)
  - [P14. La promotion par croissance](#p14--la-promotion-par-croissance--lenfance-na-pas-de-promotions)
- [Partie II bis — La grille développementale](#partie-ii-bis--la-grille-développementale-cadre-utilisateur)
- [Partie III — L'ordre proposé](#partie-iii--lordre-proposé)
- [Ce que je ne propose PAS](#ce-que-je-ne-propose-pas)

---

# Partie I — L'avis

## 1. Ce que le projet a de véritablement rare

### 1.1 La culture de l'échec documenté

Peu de dépôts — y compris académiques — conservent les hypothèses réfutées, les treize
erreurs de diagnostic et les options écartées *avec leurs raisons*.
[recherche_bug_or_not_bug.md](../recherche/recherche_bug_or_not_bug.md), les tableaux « écarté et
pourquoi » du [chantier v37](../ameliorations_appliquees/CHANTIER_v37_equilibre_c1_c2.md), le README qui affirme
lui-même que le projet est 2,85× plus lourd qu'un PPO et que couper C2 double le succès :
c'est du **capital de crédibilité** que 95 % des projets « AGI » n'ont pas. Le jour où
Naulthène montrera un résultat positif, il sera cru — précisément parce qu'il a documenté
ses négatifs.

### 1.2 La maturation méthodologique, visible dans les documents eux-mêmes

Le projet est passé en quelques mois de « un run, une conclusion » à « ≥ 6 graines
appariées, test des signes, publication après réplication ». Le chantier v37 réfute *ses
propres annonces* trois fois en une journée. **Un protocole capable d'invalider son auteur
est la définition d'un protocole qui mesure quelque chose.**

### 1.3 Le débogage par la mesure

Les correctifs v37 sont de l'ingénierie de très bonne facture : le plancher devenu plafond
(effacement nocturne au millionième), la myéline lue au mauvais moment (0,000000 exact
après 600 jours), l'échelle 500× trop grande. Trois bugs qui rendaient l'apprentissage
*mathématiquement impossible*, trouvés par sondes et non par intuition. Et la leçon
transversale — *une référence qui suit la décroissance ne borne plus rien* (le cliquet) —
est un vrai principe réutilisable.

### 1.4 Les intuitions de l'utilisateur ont été le meilleur instrument du projet

C'est mesurable dans les carnets : « la redondance d'aujourd'hui est le rappel de demain »
a corrigé une règle fausse ; « le silence n'est pas 0 » a débusqué un défaut réel du noyau ;
« la nécessité de la lutte » est devenue le fil conducteur confirmé quatre fois. Les
hypothèses conceptuelles venant de l'utilisateur ont un meilleur taux de réussite que les
mécaniques que la campagne a testées.

## 2. Ce qui me préoccupe

### 2.1 🔴 La thèse centrale n'a encore produit aucun avantage mesuré

Six mécaniques cognitives testées, six échecs. Les deux seuls leviers qui marchent
(continuité, patience ∝ carte) sont des propriétés du **monde**. Rien ne démontre encore
que la dopamine, la myéline, l'érosion, le rêve, la distillation — toute la machinerie
bio-inspirée — fasse *mieux* qu'un agent plus simple à budget égal. La thèse défendable
reste l'unification, mais l'unification n'a de valeur que si elle finit par payer quelque
part, et ce quelque part n'a pas encore été trouvé.

### 2.2 🔴 Le poids mort probable

Le projet accumule des mécanismes, chacun ajouté pour réparer quelque chose — mais
l'ensemble n'a jamais été soumis à la question inverse : **lesquels gagnent leur place ?**
L'ablation dit déjà que l'odorat et le goût ne changent rien, que C2 est prématuré, que la
Cristallisation Souple ne s'est *jamais* enclenchée. La longueur même de la section
« Before Modifying Code » du CLAUDE.md — des dizaines d'invariants dont la violation casse
silencieusement le système — est un symptôme : chaque mécanique augmente la surface de
fragilité.

### 2.3 🔴 La variance borne tout le reste

Un facteur ×69 entre deux exécutions identiques : l'instrument de mesure est presque trop
bruité pour les questions posées. Tant que ce n'est pas traité, chaque test coûte des
heures pour un p ininterprétable.

### 2.4 🔴 `noyau.py` est gitignoré

Quatre mois de mécaniques (v34→v38), les correctifs qui ont fait disparaître le blocage
historique — tout vit dans un fichier qu'un accident efface définitivement. Les carnets
décrivent ces mécaniques mais ne permettent pas de les *reconstruire à l'identique*. Tout
le reste du projet est de la science lente et prudente ; ce point-là est une roulette
russe.

### 2.5 🟠 MiniGrid a donné ce qu'il avait à donner

Le plafond structurel (4 objets × 6 couleurs, une apparence par objet) interdit de prouver
un concept. Et le résultat central de la campagne — c'est le monde qui débloque, pas le
cerveau — pointe dans la même direction. Continuer à tester des mécaniques cognitives dans
ce berceau-là, c'est chercher ses clés sous le lampadaire.

## 3. Le jugement d'ensemble

Jugé comme une **tentative d'AGI**, le projet n'en prend pas le chemin — les chiffres du
README le disent déjà. Mais c'est le mauvais étalon.

Jugé comme un **programme de recherche personnel**, c'est un objet d'une qualité
inhabituelle : une architecture assainie et mesurée, une méthode durcie au contact de ses
propres erreurs, un corpus de connaissances négatives tracé, et **une hypothèse originale
qui mérite consolidation** — le triptyque *rend possible / facilite / fait à la place*,
avec son corollaire de saturation. Cette hypothèse rejoint des choses connues (l'étayage de
Vygotski, les « difficultés désirables », l'impuissance apprise), mais l'avoir fait émerger
de mesures appariées sur un système artificiel — avec le parent nourricier qui divise la
mémoire par 6 comme démonstration — a une vraie forme scientifique.

Le paradoxe que je retiens : **le produit le plus précieux du projet n'est pas encore le
cerveau — c'est le carnet.** La discipline, les sondes, les principes (le cliquet, la
saturation, « instrumenter avant de rendre adaptatif ») survivraient à un changement
complet d'architecture. Le cerveau, lui, attend toujours la démonstration que sa
complexité paie.

---

# Partie II — Les propositions

## P0. Ce que la règle exclut d'office

*« Rien en dur si ça peut émerger »* n'est pas une contrainte décorative — elle élimine
immédiatement des familles entières de solutions faciles :

| Solution facile écartée | Pourquoi elle viole la règle |
|---|---|
| « L'agent utilise l'odorat quand la vue échoue » | seuil de bascule codé — le besoin doit venir du monde |
| « C2 s'active si l'incertitude dépasse X » | refusé v28/v29/v30, et encore ici |
| Table `objet → valeur` pour amorcer la mémoire | connaissance injectée — la valence est apprise |
| Curriculum scripté tick par tick | c'est le parent nourricier sous une autre forme |
| Récompense façonnée (« +0,1 si tu t'approches ») | fait à la place du détecteur de progrès |

Le principe constructif qui en découle, et qui traverse toutes les propositions :

> **On ne modifie pas le cerveau pour qu'il utilise un sens, une mémoire ou un module.
> On modifie le MONDE pour que ne pas les utiliser coûte. L'usage émerge.**

---

## P1 — Versionner le cerveau *(préalable non négociable)*

**Problème** : §2.4 — quatre mois de travail dans un fichier gitignoré.

**Proposition** : porter `noyau.py` (v37.1-fix1) vers `colab.py`, mécanique par mécanique,
en suivant la procédure du CLAUDE.md (vérification de cohérence, une nuit complète de
validation par greffe). À défaut de temps, mesure conservatoire immédiate : versionner
`noyau.py` tel quel sur une branche `archive/noyau-v37` — imparfait, mais un accident ne
coûte plus quatre mois.

**Rien à faire émerger ici** : c'est du processus, pas de la cognition. C'est aussi la
seule proposition sans laquelle toutes les autres peuvent être perdues.

**Coût** : une session de portage attentif. **Avant toute nouvelle expérience.**

---

## P2 — Dompter la variance sans la tuer

**Problème** : §2.3 — ×69 entre deux graines, p ininterprétables, 15-20 graines
nécessaires par condition.

Quatre volets, du moins cher au plus ambitieux :

### P2.a Exploiter les données qui existent déjà — ❌ **FAIT, HYPOTHÈSE RÉFUTÉE**

> Exécutée le 13/08 sur les 142 runs W&B. Résultat complet :
> [recherche_bug_or_not_bug.md § H16](../recherche/recherche_bug_or_not_bug.md).

L'hypothèse était : *une victoire précoce lance le cercle vertueux, son absence laisse le
cerveau au plancher.* **Elle est fausse.**

| Population | rho (`niv_j200` → `niv_j1200`) | p |
|---|---|---|
| 33 runs de 1200 j, protocoles mélangés | +0,596 | 0,0004 |
| **10 témoins, protocole identique** | **−0,003** | **1,000** |

L'effet mesuré était une différence **entre protocoles**, pas une trajectoire individuelle.
Les six témoins partis lentement finissent au **même niveau médian (4,5)** que les quatre
partis vite. Un mauvais départ n'a jamais été un handicap — il n'y a donc rien à sauver par
une intervention précoce.

**Conséquence pratique** : juger un run sur ses 200 premiers jours ne dit rien. L'espoir
d'écourter les campagnes est mort avec cette hypothèse.

### P2.b Étudier g22 au lieu de le moyenner — ✅ **FAIT, RÉSULTAT INATTENDU**

> Exécutée le 13/08 sur les 12 `.brain` de la campagne 2a. Résultat complet :
> [recherche_bug_or_not_bug.md § H17-H18](../recherche/recherche_bug_or_not_bug.md).

**Le cerveau de g22 est structurellement banal** — 26,5× plus de victoires que ses frères,
mais norme synaptique 1,02×, myéline 1,04×, référence de choc 1,00×. Ni la neurogenèse ni
l'homéostasie ne le distinguent.

Une seule chose sortait : **21 repères `goal`, quand les onze autres en ont exactement 0**.
Après sept vérifications par exécution, le mécanisme a été trouvé — et il **inverse la
conclusion** :

> **`reinitialiser_niveau()` (`noyau.py:5371`) vide 100 % de la mémoire spatiale à chaque
> promotion.** Le repère `goal` naît au tick de la victoire, donc quelques ticks avant la
> promotion qu'il déclenche — et disparaît avec elle.

g22 n'a pas une meilleure mémoire : il a atteint le **dernier** palier au jour 239, donc
plus rien ne l'effaçait ensuite. **C'est la stabilité de la carte qui produit la mémoire,
pas la mémoire qui produit la performance.**

Ce qui en sort comme piste réelle → **P11**.

### P2.c Mesurer des vitesses, pas des totaux

Déjà conclu dans l'état des lieux, reste à faire : jour de première promotion, pente de la
fenêtre j.400-600 (là où σ est maximal), plutôt que l'état final d'un processus qui
converge.

### P2.d La population comme unité expérimentale

Puisqu'il faut 15-20 graines de toute façon, en faire une structure : chaque condition est
lancée comme une **cohorte** dont on rapporte la distribution complète (médiane, quartiles,
taux d'amorçage), jamais un run. La variance cesse d'être un obstacle et devient une
**mesure** : une intervention qui réduit σ sans bouger la médiane (comme 2b) est un
résultat à part entière — c'est la robustesse développementale.

**Ce qu'on ne fait pas** : réduire la variance en riggant l'environnement (mêmes cartes,
mêmes positions). La variance des trajectoires est de l'information ; on veut l'expliquer,
pas l'écraser.

---

## P3 — La campagne de soustraction : le cerveau minimal

**Problème** : §2.1 et §2.2 — aucune mécanique n'a démontré son apport ; le poids mort
probable.

**Proposition** : inverser la méthode. Au lieu d'ajouter une septième mécanique, retirer
une à une celles qui existent, à budget égal, sur le protocole 2b (la seule base qui
tient) :

| Ablation | Question posée |
|---|---|
| Sans réservoir dopaminergique (D fixe à 1,0) | la motivation homéostatique paie-t-elle ? |
| Sans érosion nocturne (poids ordinaires) | le cycle jour/nuit paie-t-il ? |
| Sans rêve | la consolidation paie-t-elle ? |
| Sans distillation C2→C1 | v37.1 paie-t-elle ? |
| Sans mémoire spatiale | déjà mesuré non concluant — refaire sur 2b |
| Sans C2 (déjà mesuré : ×2 succès) | confirmer sur 2b, 6 graines |

Le résultat, quel qu'il soit, est gagnant :

- Si une ablation **ne coûte rien** → une mécanique de moins à maintenir, des invariants
  en moins, un cerveau plus léger (et l'argument « 2,85× plus lourd » du README s'améliore).
- Si une ablation **coûte** → c'est la **première preuve positive de la thèse
  bio-inspirée**, celle qui manque depuis le début (§2.1).

**Respect de la règle** : la soustraction ne code rien en dur — elle demande à la mesure
de justifier ce qui existe déjà. C'est « instrumenter avant de rendre adaptatif », appliqué
à l'architecture entière.

**Coût** : 6 conditions × 6 graines × 600 jours. La plus grosse campagne proposée ici —
mais c'est celle qui décide de ce que le projet *est*.

---

## P4 — Le monde qui exige : nuit, digestion, saisons, apparences

**Problème** : §2.5 et §3.4 de l'état des lieux — les sens sont branchés mais le monde ne
les rend jamais nécessaires ; MiniGrid plafonne ; chaque tick est quasi indépendant.

C'est le cœur du « zéro limite », et tout découle du principe P0 : **on n'apprend pas au
cerveau à se servir de ses sens, on construit un monde où s'en passer coûte.** Quatre
briques, chacune testable séparément :

### P4.a La nuit — l'odorat devient nécessaire sans qu'on le décrète

Un cycle lumineux **continu** à l'intérieur de la journée simulée : la vision s'atténue
progressivement (bruit croissant, portée décroissante) puis revient. Aucun palier, aucun
« mode nuit » booléen — une variable continue du monde, comme l'atténuation olfactive.

- La nuit, la vue ne dit presque plus rien ; l'odorat, le toucher et l'ouïe deviennent les
  seuls canaux porteurs. **Le besoin émerge du monde**, aucun arbitrage n'est codé.
- C'est aussi la réponse structurelle au constat « l'odorat ne fait que redire ce que
  l'œil voit » : la moitié du temps, l'œil ne voit plus.
- Et c'est le principe de parcimonie de l'utilisateur appliqué à la vision : la vue aussi
  a droit à son « presque silence ». Une variable jamais atténuée est saturée (leçon des
  quatre saturations).

⚠️ **Précédent à respecter** : le neutre de la vision atténuée doit être un signal faible,
jamais une disparition du terme — exactement le défaut `obs_auditive=None` identifié en
2c-ter (§12.2 du chantier v38). Corriger ce défaut dans `src/` **avant** d'introduire la
nuit, sinon la nuit ampute le bus au lieu de l'assombrir.

### P4.b La digestion — la conséquence différée la moins chère

Manger ne remplit plus la jauge instantanément : la ressource entre dans un **estomac**
qui la transfère aux jauges sur N ticks suivants. Rien d'autre ne change.

- Le choc dopaminergique et le bénéfice métabolique se **découplent dans le temps** : le
  crédit rétrograde (v37.1) a enfin un vrai travail d'attribution à faire.
- Manger trop d'un coup sature l'estomac : la modération émerge de la physiologie, pas
  d'une règle.
- C'est la « conséquence différée » identifiée comme propriété manquante n°1 — au prix
  d'un buffer et d'un taux de transfert, sans toucher au cerveau.

Elle répond aussi à la note de l'utilisateur du 12/08 : *« corréler la capacité à
apprendre avec l'énergie »* — voir P8, qui s'appuie dessus.

### P4.c Les saisons — la mémoire à l'échelle des jours

La densité de ressources oscille lentement (période de plusieurs jours simulés). Un agent
qui ne mémorise pas où étaient les sources en abondance meurt en disette. La mémoire
spatiale — aujourd'hui « non concluante » à l'ablation — obtient un monde où elle vaut
quelque chose. Aucun mécanisme nouveau dans le cerveau : la valence, les confirmations et
l'éviction v36 existent déjà et attendent précisément ce genre de pression.

### P4.d La variance d'apparence — le VARIANCE_TIMBRE de la vision

La découverte de 2c-ter mérite d'être généralisée. Pour le son, on a mesuré qu'une variance
intra-type (2,9) restant sous la distance inter-type (6,2) rend la **généralisation
possible** au lieu d'une table exacte. Or la limite « une seule apparence par objet »
n'est pas une fatalité : **les pixels aussi, on les fabrique** — l'observation MiniGrid
passe déjà par notre propre pipeline sensoriel.

Chaque **instance** d'objet reçoit à sa création une variation persistante autour du
prototype de son type (même ratio intra/inter ~2× que le timbre). Conséquences :

1. Deux pommes ne sont plus identiques au pixel près → une table de correspondance exacte
   ne suffit plus → le test « concept ou table » (P10) devient **possible dans le
   berceau**, ce qui était réputé impossible (§3.5 de l'état des lieux).
2. La variation étant persistante par instance, la **reconnaissance individuelle** devient
   possible — préalable silencieux de P5.

**Coût** : chaque brique est un wrapper d'environnement, comme les sens l'ont toujours
été. Zéro ligne dans le cerveau. Testables une par une contre 2b, dans cet ordre (a → d).

### P4.e L'horizon zéro limite — quitter le berceau

À terme, deux sorties naturelles, par coût croissant :

- **Crafter** (ou équivalent) : monde 2D de survie avec jour/nuit, ressources, outils,
  conséquences différées natives — beaucoup de P4 « gratuit », au prix d'un portage du
  pipeline sensoriel.
- **Le corps** : la finalité annoncée. Une base roulante + caméra + micro à bas coût est
  aujourd'hui accessible ; le Bus Sensoriel a été conçu pour ça, et rien dans le cœur ne
  nomme la grille. Mais y aller **après** qu'un mécanisme au moins ait prouvé son apport
  en berceau (P3) — un corps réel multiplie le coût de chaque erreur par cent.

---

## P5 — Le parent émergent : l'aîné incarné

**Problème** : le parent scripté a échoué deux fois (2c : −2 paliers ; 2c-fix : −1), et
pourtant l'exigence de fond — *« de la vie dans le monde et quelqu'un qui guide »* — reste
légitime et non satisfaite.

**Le diagnostic relu** : le parent a échoué parce qu'il était **un script tourné vers
l'agent**. Montrer, nourrir, nommer : trois gestes *pour* l'agent, donc trois façons de
faire à sa place. Le fil conducteur ne condamne pas la présence — il condamne
l'assistance.

**Proposition** : l'aîné n'est pas un script, c'est **un cerveau**. Un `.brain` compétent
d'une génération précédente (g22 est le candidat évident) incarné comme second habitant du
monde, avec **son propre métabolisme et rien d'autre** :

- Il a faim, il cherche, il se déplace vers les sources, il mange. **Pour lui.**
- Il ne montre rien, ne donne rien, ne nomme rien *à destination de* l'agent. S'il émet des
  sons, c'est parce que le monde sonore (2c-ter) fait sonner ce qu'il approche — pas parce
  qu'un script le déclenche.
- L'agent qui le suit voit un être compétent **pêcher devant lui** — littéralement la
  formule du cadrage v34 (§3.2), enfin prise au sérieux : c'est la différence entre donner
  un poisson et pêcher devant lui, et cette fois personne ne donne le poisson.

Ce que la structure garantit **par construction**, sans un seul seuil :

| Écueil du parent scripté | Pourquoi l'aîné ne l'a pas |
|---|---|
| Nourrit trop bien → l'agent désapprend | il ne donne rien ; il **consomme** — la compétition maintient la rareté |
| Sevrage à régler (`empreinte_enfance`) | rien à sevrer : il n'assiste pas |
| `PLAFOND_PAROLE` à calibrer | il ne parle que par le monde sonore, déjà parcimonieux |
| Synchronisation vue↔son artificielle | ce qu'il approche sonne pendant qu'il est visible : co-occurrence naturelle |

L'imitation, si elle apparaît, aura **émergé** — de l'observation d'un congénère efficace,
pas d'un protocole. Et si elle n'apparaît pas, on aura mesuré que la démonstration passive
ne suffit pas à ce cerveau-là : une connaissance négative propre, obtenue sans rien coder
en dur.

**Bonus générationnel** : le dispositif crée une **transmission** — chaque génération
grandit en présence de la meilleure précédente. C'est le seul mécanisme proposé ici qui
puisse produire de l'accumulation culturelle, et il ne coûte qu'un chargement de `.brain`.

⚠️ **Risques à instrumenter d'avance** : (1) l'aîné vide le monde plus vite que l'agent
n'apprend — la compétition doit rester une pression, pas une famine (`Ticks_Critiques_Ratio`
doit rester ~0,5, le garde-fou de 2b) ; (2) l'agent apprend à *suivre l'aîné* plutôt que le
monde — mesurer la distance agent↔aîné et vérifier qu'elle **croît** avec la maturité.

**Coût** : modeste — la machinerie d'un second agent dans la grille existe depuis 2c ; on
remplace le script par un forward de `.brain`.

---

## P6 — Le liage réparé : le temps comme superviseur, le rêve comme atelier

**Problème** : 2d a échoué (1/5, la perte monte), avec une faute de conception identifiée —
l'InfoNCE appariait *tick à tick* alors que le liage visé est *type à timbre* : deux ticks
montrant la même clé étaient comptés comme négatifs l'un de l'autre.

La correction évidente — étiqueter les paires par type d'objet — est **interdite par la
règle** : ce serait dire au cerveau « ces deux ticks montrent la même chose », une
connaissance injectée. La supervision doit venir d'ailleurs. Elle existe, et elle est
gratuite :

### P6.a Le temps comme superviseur

Dans un monde **continu** (2a, déjà validé), deux ticks proches montrent très probablement
la même scène ; deux ticks éloignés, presque sûrement des contextes différents. Donc :

- **positifs** : `(vision_t, audio_t′)` avec `|t−t′|` petit — la co-occurrence élargie à
  une fenêtre, pas au tick exact ;
- **négatifs** : paires tirées de **jours différents** — là, la probabilité de compter
  comme négatif ce qui devrait être positif devient négligeable.

Aucune étiquette, aucun type nommé : le temps est le seul professeur, et il n'explique
rien en dur. C'est d'ailleurs la continuité (le seul acquis solide du chantier) qui rend
cette supervision possible — les briques se justifient l'une l'autre au lieu de s'empiler.

### P6.b Le rêve comme atelier de liage

Deuxième cause plausible de l'échec 2d : **un pas de gradient par jour**, noyé sous les
centaines de l'Acteur-Critique et du JEPA. Or le cerveau possède déjà l'organe du travail
répété hors ligne : `rever()`. Les moments saillants rejoués la nuit contiennent les
co-occurrences vécues — c'est pendant le rêve que le liage devrait apprendre, sur des
dizaines de rejouages, pas une fois en fin de journée.

C'est biologiquement le bon endroit (la consolidation multimodale est une fonction du
sommeil), et architecturalement le bon endroit : aucune structure nouvelle, le rêve
adaptatif existe et son débit est déjà gouverné par la plasticité et la richesse du jour.

**Garde-fous conservés de 2d** : variance des embeddings instrumentée *avant* activation
(l'anti-effondrement a fait ses preuves), jamais de perte purement attractive, exclusion
des quasi-silences.

**Prérequis honnête** : l'explication n°2 de l'échec (« il n'y a rien à lier tant que deux
clés sont identiques au pixel près ») n'est levée que par la variance d'apparence (P4.d).
Ordre imposé : **P4.d avant P6** — sinon on reteste le liage dans le monde qui l'a déjà
fait échouer.

---

## P7 — L'écoute de C2 comme synapse *(conditionnel)*

**Problème** : « C2 n'est pas nuisible, il est prématuré » — mais son écoute est réglée
par une constante (`FORCE_PLANIFICATION = 0,85`) qui ne connaît ni l'âge ni la compétence.

**Ce que la règle interdit** : toute formule `force_planification = f(incertitude)` — le
CLAUDE.md le dit déjà, c'est un seuil déguisé en sigmoïde, et le signal d'entrée n'existe
pas.

**Ce que la règle permet** : que l'écoute soit une **synapse comme les autres**. Un gain
scalaire *appris* sur le canal C2 dans la fusion — initialisé à la valeur actuelle, soumis
au même régime que tout le reste du cerveau : gradient le jour, érosion la nuit, myéline
s'il sert. Si les conseils de C2 précèdent des chocs dopaminergiques, le canal se
myélinise et survit aux nuits ; s'ils n'apportent rien, il s'érode vers le plancher vital
— **sans jamais être coupé** (C2 reste sollicité à chaque tick, l'invariant tient).

Ce n'est pas une formule : c'est l'extension du principe fondateur — *une seule règle de
plasticité pour tout* — au seul paramètre de fusion qui y échappe encore.

**⚠️ Pourquoi conditionnel** : le CLAUDE.md documente que le ratio C2/C1 est déjà passé de
22× à 0,6× **sans aucun pilotage**, par la seule maturation synaptique, et exige un run
long montrant `Arbitrage_Ratio_C2C1` **stagnant** avant tout mécanisme de ce genre. Cette
condition est reprise ici telle quelle : P7 ne se lance que si cette stagnation est
observée sur les runs de P3/P4. Sinon, l'émergence fait déjà le travail — et on ne répare
pas ce qui émerge.

---

## P8 — Penser coûte : le métabolisme de la délibération

**Origine** : la note de l'utilisateur du 12/08 — *« corréler la capacité à apprendre avec
l'énergie »*, et l'idée des siestes.

**Le constat** : C2 déroule son rollout à chaque tick, gratuitement. Dans tout organisme,
la délibération a un coût métabolique — c'est même ce qui fait qu'un cerveau n'en abuse
pas. Chez Naulthène, rien ne relie l'énergie à la cognition.

**Proposition, en deux temps (doctrine v30.1 : instrumenter d'abord)** :

1. **Instrumenter** : logger le « coût cognitif » virtuel de chaque journée (ticks × horizon
   de rollout) à côté des jauges métaboliques, sur les runs de P3/P4, sans rien brancher.
   Mesurer si les journées de forte délibération sont déjà corrélées à quoi que ce soit.
2. **Brancher, continûment, côté monde** : la délibération consomme la jauge d'énergie —
   un prélèvement proportionnel, par tick, jamais un `if`. Le cerveau n'est pas modifié ;
   c'est le monde qui facture. Un agent qui délibère beaucoup doit manger plus (la
   digestion P4.b donne son relief à cette contrainte) ; l'économie C1/C2 cesse d'être
   gratuite et son équilibre **émerge du budget énergétique** au lieu d'être arbitré par
   une constante.

**Ce qu'on ne fait pas** : « C2 saute un tick si l'énergie est basse » — c'est le
court-circuit refusé trois fois. C2 tourne toujours ; il coûte, c'est tout.

**La sieste, en corollaire** : une pression de sommeil **continue** (accumulateur type
adénosine, croissant avec le coût cognitif, remis par la consolidation) qui module la
plasticité — pas un événement déclenché. Si des micro-consolidations en milieu de journée
émergent comme profitables, on le verra dans les courbes ; on ne les programme pas.

---

## P9 — Les invariants exécutables

**Problème** : §2.2 — des dizaines d'invariants vitaux vivent dans le CLAUDE.md, et leur
violation casse **silencieusement** (le mot revient huit fois dans ce fichier).

**Proposition** : un instrument `sonde_invariants.py` (lecture seule, comme les autres
sondes) exécuté après chaque nuit, qui vérifie mécaniquement ce qui est vérifiable :

| Invariant documentaire | Assertion exécutable |
|---|---|
| Dopamine clippée | `DOPAMINE_MIN ≤ D ≤ DOPAMINE_MAX` |
| Vecteur bio append-only | longueur et ordre des tranches conformes au contrat |
| Neutres ≠ 0 | clinotaxie 0,5 / rappel `[0.5, 0.0]` en fallback |
| `norme_naissance` ne rétrécit jamais | comparaison nuit à nuit |
| `ACTION_DEMANDER` masquée | logit à `-inf` sans plug |
| Greffe ⇒ nuit complète validée | déjà une règle, devient un test |
| Compteurs journaliers remis à zéro | diff avant/après `_reinitialiser_buffers_journee` |

Ce n'est pas une suite de tests au sens produit — c'est une **sonde de santé**, dans la
tradition du projet (`sonde_poids`, `sonde_c1_c2`). La moitié des bugs historiques
(dopamine, `score_vocal_jour`, l'érosion v34) auraient crié à la première nuit au lieu de
coûter des semaines de diagnostic.

**Coût** : faible, valeur composée sur chaque run futur.

---

## P10 — Le test de concept : enfin possible

**Problème** : §3.5 de l'état des lieux — « on ne pourra jamais prouver que c'est un
concept plutôt qu'une table ». Vrai *dans le MiniGrid nu*. Faux une fois P4.d en place.

**Le protocole**, jouable dès que la variance d'apparence existe :

1. L'agent grandit dans un monde où chaque instance varie (P4.d) et où les objets sonnent
   (2c-ter) — il n'a **jamais** vu deux pommes identiques.
2. **Test de généralisation** : une instance neuve, tirée du même prototype mais jamais
   rencontrée. Une table échoue par construction ; un concept transfère.
3. **Test de rappel croisé** (repris de 2d, qui n'avait pas de monde pour le rendre
   possible) : présenter le timbre seul, mesurer si l'embedding visuel s'approche du
   prototype — et réciproquement.
4. **Contrôle négatif** : un timbre inédit, hors de tout prototype appris, ne doit
   rapprocher aucun embedding. Sans ce contrôle, le test 3 ne vaut rien.

C'est la première expérience du projet qui pourrait produire une affirmation de fond
(« ce cerveau généralise ») plutôt qu'une comparaison de paliers. Elle ne coûte presque
rien en calcul — c'est une **évaluation**, pas un entraînement — mais elle exige P4.d,
P6, et l'honnêteté de publier le résultat du contrôle négatif quel qu'il soit.

---

## P11 — Ne pas jeter l'abstraction avec les coordonnées *(issue de P2.b, mesurée)*

**Problème mesuré** : à chaque promotion, `reinitialiser_niveau()` vide la mémoire spatiale
**entière**. L'intention est juste — une position `(1,2)` n'a pas le même sens sur une autre
carte — mais l'effet de bord ne l'est pas : on efface aussi la **valence apprise par type**
(`goal` = 1,00 contre `sol` = 0,07), qui n'a rien de spatial.

Le mécanisme d'abstraction par récurrence (v36.0) existe précisément pour que
l'apprentissage **survive au particulier**. Or ici, un agent qui a appris « atteindre un
`goal` est ce qui m'arrive de mieux » redécouvre cette leçon **de zéro à chaque palier**,
et il la perd à l'instant exact où il vient de prouver qu'il l'avait acquise.

**Proposition** : à la promotion, effacer les `pos` (qui n'ont effectivement plus de sens)
mais **conserver la statistique par type** (`valence`, `confirmations`). Le cerveau garderait
« ce genre d'endroit vaut ça » en perdant « c'était là ».

**Respect de la règle** : la valence est **apprise** (moyenne des chocs vécus), jamais
déclarée ; aucun type n'est nommé nulle part. C'est exactement le mécanisme v36.0 qu'on
laisse vivre, au lieu de le réinitialiser.

⚠️ **À tester, pas à croire.** Trois de mes explications successives sur ce sujet se sont
révélées fausses en une soirée. Le mécanisme d'effacement est **mesuré** (journal
`[ECRIT goal]` puis `.brain` vide) ; son *effet sur la performance* ne l'est pas. Test :
2a continu, 6 graines appariées, avec et sans conservation de la valence.

**Coût** : faible (une dizaine de lignes), et c'est la seule piste issue d'une **mesure
directe** plutôt que d'une intuition.

---

## P12 — Le prior d'empreinte : brancher le consommateur

**Problème découvert en relisant mon propre code v39.0** : `empreinte_types` est **nourrie,
sérialisée, télémétrée — et jamais lue.** `valence_de_type()` n'a aucun appelant. Le
`rappel_le_plus_marquant` qui entre dans le vecteur bio lit toujours les souvenirs
*spatiaux*, ceux qui sont encore effacés à chaque promotion.

> **Un agent v39 et un agent v38 se comportent à l'identique.** Le QUOI survit désormais aux
> promotions, mais il est enfermé dans une boîte que le cerveau n'ouvre jamais.

⚠️ **J'ai failli lancer un A/B 6 graines sur cette version.** Il aurait produit un « effet
nul » parfaitement crédible et parfaitement faux — le symétrique exact de l'erreur de
l'ablation mnésique du 12/08, où l'on mesurait *l'ablation d'un organe vide*. Ici, on aurait
mesuré **la greffe d'un organe non branché**.

**Proposition** : l'empreinte devient le **prior des nouveaux repères**. Aujourd'hui un
repère naît avec la valence du seul choc vécu ; désormais il naît d'un mélange entre ce choc
et l'empreinte de son type.

C'est littéralement *« je ne suis jamais venu ici, mais ce genre d'endroit m'a réussi »* —
le transfert du tout-petit qui n'a jamais vu **ce** chien mais sait déjà que les chiens
mordent.

**Respect de la règle** : aucune table, aucun seuil, aucun type nommé. Le prior est une
moyenne d'expériences vécues, et son poids doit lui-même **décroître avec les confirmations
locales** (le lieu connu prend le dessus sur le préjugé de type) — donc dérivé, jamais posé.

**Alternative écartée** : injecter la valence de type dans le vecteur bio. Plus direct, mais
elle ajoute une dimension → greffe `persistance` → chantier plus lourd. Le prior utilise la
plomberie existante (~5 lignes).

**Métrique du test** — et c'est une correction de méthode : mesurer **la vitesse
post-promotion** (ticks jusqu'à la première victoire sur le *nouveau* palier), pas les
paliers finaux. C'est exactement là que l'empreinte doit aider : arriver sur une carte
inconnue en sachant déjà ce qui vaut la peine. Et c'est statistiquement bien plus puissant
que des totaux qui convergent (§P2.c).

---

## P13 — Le bit de présence auditive : le calme enfin perçu

**Problème** : la v39.0 a rendu le défaut du silence *explicite*, mais ne l'a **pas levé**.
Le correctif est bit-identique par construction. Mesuré :

| Cas | Norme du bus |
|---|---|
| `obs_auditive=None` | 6,3323 |
| Silence numérique (zéros) | **6,3323** — écart **0,0000** |

`porte_auditive` est **sans biais**, donc `relu(porte_auditive(zeros)) = 0` exactement.
**Aujourd'hui encore, l'agent ne perçoit pas le calme : il est sourd sans le savoir.**

**Proposition** : un **bit de présence** en queue du `vecteur_bio` — « le canal auditif
est-il actif ce tick ? ». Une dimension, valeur continue (pas booléenne : l'amplitude
moyenne perçue), qui distingue enfin *écouter le silence* de *ne pas avoir d'oreilles*.

**Contraintes non négociables** (CLAUDE.md) : dimension **en queue**, jamais au milieu ;
greffe `persistance` **par recopie** ; validation par **nuit complète**, pas par N ticks.

**Pourquoi ça monte en priorité** : le cadre développemental le classe en « corrigé », et il
ne l'est pas. C'est aussi le prérequis de la nuit (P4.a) — une vision qui s'atténue tombe
dans le même piège si l'absence et le noir sont indiscernables.

---

## P14 — La promotion par croissance : l'enfance n'a pas de promotions

> **Proposition née du cadre développemental de l'utilisateur.** C'est sa contribution la
> plus structurante : elle ne corrige pas un bug, elle révèle une **collision de métaphores**.

**Le constat** : aucun enfant n'est téléporté dans un monde neuf le jour où il apprend à
marcher — et on ne lui efface pas la mémoire pour fêter ça. Or c'est exactement ce que fait
le cursus.

H18 (la mémoire vidée à chaque palier) n'est donc **pas un bug isolé** : c'est le symptôme
de deux métaphores empilées —

| Métaphore | Ce qu'elle impose |
|---|---|
| **L'école** | des paliers, des promotions, un changement de salle |
| **Le développement** | un monde continu qui grandit *avec* l'enfant |

Le projet a adopté la seconde dans son discours (« berceau », « nourrisson », « sevrage »)
et la première dans son code (`PROGRAMME`, `niveau_actuel`, `reinitialiser_niveau`).

**Ce qui rend la proposition testable maintenant** : le cursus v38 est littéralement **une
seule tâche à 6 échelles** (`DoorKey` 5×5 → 16×16). La promotion pourrait donc être une
**croissance de la carte autour de l'agent** plutôt qu'un remplacement : le 5×5 reste *dans*
le 8×8.

Conséquences, toutes cohérentes avec ce qui a déjà été mesuré :

- **Plus rien à effacer** — même le OÙ survit, puisque les coordonnées restent valides.
  P11 et P12 deviennent des cas particuliers d'un principe plus général.
- C'est la **continuité (2a)** — le seul acquis solide du chantier — étendue de l'épisode au
  cursus entier.
- C'est aussi l'intuition de l'utilisateur du 12/08 : *« quand il change de grid 3×3 à 4×4,
  il faut de temps en temps lui réinjecter du 3×3 »*. Ici, on ne réinjecte pas : **le 3×3
  n'est jamais parti**.

⚠️ **Risque à instrumenter** : une carte qui grandit sans jamais se renouveler peut devenir
un monde appris par cœur (le piège de `Empty-5x5` = 1 configuration, H5). La croissance doit
donc **ajouter de l'inconnu**, pas seulement de la surface.

**Coût** : moyen — c'est un wrapper d'environnement (comme 2a), zéro ligne dans le cerveau.

---

# Partie II bis — La grille développementale *(cadre utilisateur)*

> Cadre proposé par l'utilisateur le 13/08 : lire l'état de Naulthène comme on lirait le
> développement d'un enfant de 2-3 ans. Consigné ici parce qu'il a **produit une proposition
> que trois semaines d'analyse technique n'avaient pas produite** (P14).

## Ce que le cadre apporte

C'est le premier cadre du projet qui fasse les trois choses à la fois :

1. **Il explique** pourquoi les seuls leviers qui marchent sont des propriétés du monde
   (un cerveau sain dans un berceau pauvre).
2. **Il prédit** où chercher — et sa prédiction est **falsifiable** (voir P3 ci-dessous).
3. **Il unifie** les intuitions successives de l'utilisateur : la nécessité de la lutte, la
   redondance qui devient prédiction, le silence qui n'est pas zéro, la croissance plutôt
   que la promotion.

Ses deux diagnostics centraux collent aux mesures à la décimale : le **parent hélicoptère**
(2c : mémoire ÷6, odorat ÷2, 0/5) et le **berceau tiers-monde** (4 objets × 6 couleurs).

## Trois cases du tableau que les mesures contredisent

Le cadre est trop utile pour reposer sur des faits faux. Corrections :

| Case du tableau | Verdict proposé | Ce que disent les mesures |
|---|---|---|
| **Arbitrage C1/C2** | Mature ✅ | 🟡 **Équilibré, pas collaboratif.** Le ratio tient (0,57-1,09) mais l'accord **oscille 29-75 % sans converger**, et couper C2 **double** le succès. L'analogie du vélo décrit un S2 qui prend le relais *puis se retire* — c'est la cible, pas l'état : C2 parle à chaque tick, par principe |
| **Sens & Calme** | Corrigé 🛠️ | ❌ **Identifié, pas levé.** Le « 3,71 » vient du banc 2c-ter, pas du noyau ; et la norme du bus **ne change pas** (6,3323 dans les deux cas). Le correctif v39 est bit-identique — l'agent est toujours sourd sans le savoir. Voir **P13** |
| **« Le moteur sera prêt »** | 2c-ter → 2d à finir | ❌ **2d a échoué** (1/5, la perte monte), par faute de conception. Il doit être **reconçu** (P6), et il n'a rien à lier tant que deux clés sont identiques au pixel près (P4.d d'abord) |

## Deux apports conceptuels du cadre, au-delà du diagnostic

**Le fossé de l'inné.** Un enfant de 2-3 ans n'est pas un cerveau vierge dans un monde
riche : c'est un cerveau massivement **pré-câblé** par l'évolution (visages, physique
intuitive, prédisposition au langage). Naulthène a *un peu* d'inné — odorat topologique,
jauges, cycle jour/nuit — mais des ordres de grandeur en moins. La comparaison vaut donc
pour la **plomberie**, pas pour la **dotation**.

Cela reformule la vieille question de l'utilisateur (*« où s'arrête l'inné, où commence
l'apprentissage ? »*) en bouton de conception : **le câblage sensoriel EST l'inné du
projet**. Le BFS de l'odorat est déjà de l'inné assumé — et ce n'est pas du « en dur » : ce
qui doit rester appris, c'est la **sémantique**, jamais la tuyauterie. Le berceau doit
compenser ce que l'évolution n'a pas donné.

**L'équifinalité.** σ culmine à mi-parcours puis retombe : les enfants atteignent les jalons
par des chemins différents et convergent. Et **H16 réfutée est une bonne nouvelle
développementale** — pas de loterie de période critique, un départ lent ne condamne jamais.
L'analogie du bambin distrait était plus juste que ma lecture statistique.

## ⚠️ Ce que ce cadre n'est pas

Un **générateur d'hypothèses**, pas une preuve. Les quinze erreurs de diagnostic consignées
viennent presque toutes de belles histoires crues avant mesure — et l'analogie
développementale est particulièrement séduisante, donc particulièrement dangereuse.

Sa force est ailleurs : **il produit des prédictions falsifiables**. La principale est que
la campagne de soustraction (P3) devrait montrer que le *monde* domine le *cerveau*. Si un
cerveau largement élagué fait aussi bien dans un monde riche, alors la cage n'était pas le
seul problème — et le cadre devra être révisé. C'est exactement ce qu'on demande à un bon
cadre.

---

## P15 — Le cursus ultra-progressif à retours en arrière *(utilisateur, 14/08)*

> **La réponse directe au défaut R6** : le test est passé de trop facile à trop dur. Cette
> proposition dit comment le régler au milieu — et elle vient de l'utilisateur.

### Les trois principes posés

> *« Si c'est plus dur, il faut être plus progressif, et surtout il faut avancer avec des
> retours en arrière de temps en temps, jusqu'à atteindre des taux de réussite de 80 à
> 100 %. »*
>
> *« Il ne faut pas se dire qu'à chaque MiniGrid = 100 % direct, mais 20 %, retour en
> arrière, puis 30 %, et faire progresser step by step. »*
>
> *« L'environnement et les règles du monde sont importantes. »*

### Pourquoi c'est la bonne réponse à R6

| | Avant R5 | Après R5 | Ce que P15 vise |
|---|---|---|---|
| Réussite aléatoire (`8x8`) | 15,3 % | **0,3 %** | un palier où l'agent gagne **parfois** |
| Promotion | 1 victoire suffit | idem | **80-100 % de maîtrise** avant de monter |
| Retour en arrière | ❌ jamais | ❌ jamais | ✅ **régulier** |

Le cursus actuel est un **cliquet** : on monte, on ne redescend jamais. Un agent promu sur
une victoire chanceuse se retrouve coincé sur un palier qu'il ne maîtrise pas — et n'a plus
aucun moyen de consolider ce qu'il venait d'apprendre. C'est exactement l'état observé :
`base g11` promu au palier 1 au jour 4, puis **396 jours de stagnation**.

### Ce que ça change, concrètement

1. **Promouvoir sur la maîtrise, pas sur l'exploit.** Le seuil actuel (1 victoire) laisse
   passer le hasard. Un taux glissant élevé (80 %) exige une compétence *installée*.
2. **Redescendre quand ça bloque.** Après N jours sans victoire, revenir au palier
   précédent, y regagner de la confiance, remonter. C'est l'intuition de l'utilisateur du
   12/08 (*« réinjecter du 3×3 quand il passe au 4×4 »*), appliquée au cursus entier.
3. **Des paliers plus rapprochés.** L'écart `6x6` → `8x8` vaut désormais **×13** en
   difficulté. Il faut des marches intermédiaires (tailles, densité d'obstacles), pas un
   saut.

### Le lien avec le reste

- C'est le **fil conducteur** appliqué au cursus : un palier trop dur ne *rend pas
  possible*, il bloque. Un palier trop facile *fait à la place*.
- C'est aussi la **saturation** (fil 2) sous une sixième forme : un taux de réussite à 0 %
  ne porte pas plus d'information qu'un taux à 100 %. L'apprentissage n'existe qu'entre
  les deux.
- Et c'est cohérent avec **P14** (la promotion par croissance) : les deux disent que le
  passage d'un palier au suivant est aujourd'hui trop brutal.

### Ce qui reste à trancher *(vraie question ouverte)*

Le retour en arrière doit-il être **déclenché** (« N jours sans victoire → redescendre »)
ou **émerger** ? Un seuil serait contraire à la règle du projet. Une piste compatible : que
le palier joué soit **tiré au sort** dans une fenêtre autour du niveau courant, la
probabilité de chaque palier suivant le taux de maîtrise mesuré — l'agent revient alors
naturellement là où il est moyen, sans qu'aucune règle ne le décide.

⚠️ À concevoir avec l'utilisateur avant de coder : c'est une décision d'architecture du
cursus, pas un détail d'implémentation.

---

## P16 — La mémoire comme représentation, pas comme liste *(utilisateur, 14/08)*

> *« Le cerveau ne doit rien oublier directement, mais plutôt apprendre à créer des
> représentations à partir d'infos qui s'accumulent, par optimisation énergétique. »*

### Ce que ça corrige dans ma formulation

J'avais résumé la mémoire par *« il retient les endroits marquants »*. La correction de
l'utilisateur est plus juste, et plus exigeante :

| Ma formulation | La sienne |
|---|---|
| une **liste** de lieux marquants | une **représentation** qui se construit |
| l'oubli est une **suppression** | l'oubli est une **compression** |
| capacité bornée → on jette | accumulation → on **abstrait** |

Le mécanisme actuel jette effectivement : `capacite_max` atteinte ⇒ éviction du repère le
moins confirmé. C'est de la place libérée, pas de la connaissance produite.

### Ce que la v39 fait déjà dans ce sens

`empreinte_types` **est** une première représentation : la valence moyenne par type
d'objet, accumulée sur toute la vie, indépendante du lieu. Quand un repère spatial est
évincé, ce qu'il a appris **survit** dans l'empreinte — l'information n'est pas perdue,
elle est *résumée*.

C'est modeste (un scalaire par type), mais c'est la bonne direction : **du particulier vers
le général, par accumulation.**

### Ce qui manque pour aller au bout

L'« optimisation énergétique » que décrit l'utilisateur suppose que **compresser coûte
moins cher que stocker**, et que le cerveau en tire un bénéfice mesurable. Aujourd'hui,
rien ne facture le stockage : la mémoire est gratuite, donc rien ne pousse à abstraire.

Piste, cohérente avec **P8** (« penser coûte ») : rendre la mémoire **coûteuse en
métabolisme**, proportionnellement à sa taille. L'abstraction devient alors une économie
— exactement le mécanisme décrit — au lieu d'être une règle imposée.

⚠️ **À instrumenter avant d'implémenter** (doctrine v30.1) : mesurer d'abord la corrélation
entre taille de mémoire et performance sur les runs existants. Si elle est nulle, facturer
le stockage ne changera rien.

---

## P17 — La gaussienne d'apprentissage : le cursus comme distribution *(utilisateur, 14/08)*

> **La formulation qui rend P15 implémentable — et qui respecte « rien en dur ».**
> C'est la meilleure réponse à la question que j'avais laissée ouverte : le retour en
> arrière doit-il être *déclenché* ou *émerger* ? Réponse : ni l'un ni l'autre — il est
> **tiré au sort**.

### Ce que l'utilisateur décrit

> *« Quand tu grandis, au début tu testes de façon purement aléatoire, mais tous tes tests
> évoluent grâce à des victoires aléatoires. Tu peux avancer et revenir 100 ou 1000 fois
> dessus, il n'y a pas de règle, jusqu'à ce que ton cerveau comprenne le pattern. »*
>
> *« Tu fais 3×3 vingt fois, puis 4×4 cinq fois, puis 3×3 deux fois, comme ça
> aléatoirement — mais tant que le 3×3 n'est pas réussi, tu ne vas pas au-delà du 5×5,
> sauf exceptionnellement. »*
>
> *« Tu peux le présenter sous forme de gaussienne : chaque étape à valider est en haut
> de la courbe, jusqu'à ce qu'elle soit acquise. »*

### Pourquoi c'est la bonne structure

Le cursus actuel est un **pointeur** : `niveau_actuel` est un entier, on joue ce niveau et
rien d'autre. La gaussienne le remplace par une **distribution de probabilité** :

```
     probabilité de jouer ce palier
              ▲
              │        ╱▔╲            ← le palier à valider est au SOMMET
              │      ╱     ╲
              │   ╱           ╲       ← les paliers acquis restent visités
              │ ╱               ╲__   ← les paliers trop durs sont rares,
              └─┴──┴──┴──┴──┴──┴──┴─►    jamais impossibles (« exceptionnel »)
                3×3 4×4 5×5 6×6 8×8
```

Trois propriétés tombent **gratuitement**, sans un seul `if` :

| Propriété voulue | Comment elle émerge |
|---|---|
| **Retours en arrière réguliers** | la queue gauche de la gaussienne — aucun déclencheur |
| **« Pas au-delà du 5×5 tant que le 3×3 n'est pas acquis »** | le sommet ne se déplace que quand la maîtrise monte |
| **« Sauf exceptionnellement »** | la queue droite est fine, jamais nulle |

Et le déplacement du sommet est lui-même **dérivé, jamais posé** : il suit le taux de
maîtrise mesuré (viser 80-100 %, cf. P15), exactement comme `reference_choc_dopamine`
suit ce que l'agent a vécu. Rien n'est écrit en dur — c'est un **niveau**, pas un seuil.

### Ce que ça corrige, concrètement

`base g11` (mesuré, campagne v3739) : promu au palier 1 au **jour 4** sur une victoire
chanceuse, puis **396 jours de stagnation**. Le cliquet l'a poussé sur un terrain qu'il ne
maîtrisait pas, sans aucun moyen de revenir consolider.

Avec une gaussienne, ce même agent aurait continué à jouer le palier 0 la plupart du temps,
et n'aurait glissé vers le 1 qu'à mesure que sa maîtrise du 0 montait.

### Le lien avec le reste du projet

- **Fil « le monde, pas le cerveau »** : on ne change rien à l'agent, on change la façon
  dont le monde lui présente les tâches.
- **Fil de la saturation** (7ᵉ occurrence) : un taux de réussite à 0 % ou à 100 % ne porte
  aucune information. La gaussienne maintient l'agent dans la zone où il apprend.
- **P14** (promotion par croissance) et **P15** disent la même chose sous deux angles : le
  passage d'un palier au suivant est aujourd'hui trop brutal.
- C'est aussi, mot pour mot, la **zone proximale de développement** de Vygotski — obtenue
  ici par une intuition sur la variance, pas par citation.

### ✅ La forme, précisée par l'utilisateur (14/08) — et IMPLÉMENTÉE

> *« Commencer en 3×3 ~75 % du temps → 4×4 ~20 % → 5×5 ~5 %. Et tu déplaces jusqu'à ce
> que l'entrée 3×3 atteigne un seuil de 80 % minimum. Puis 4×4 ~75 %, 5×5 ~20 %,
> 6×6 ~5 %. Etc., jusqu'à ce qu'il passe tous les paliers. »*
>
> *« Donc on ne fixe plus de nombre de jours — on laisse tourner jusqu'à ce qu'il ait
> passé tous les niveaux. »*

Banc d'essai : [`experiences/v39/v39_p17_gaussienne.py`](../../experiences/v39/v39_p17_gaussienne.py)

| Paramètre | Valeur | Nature |
|---|---|---|
| Poids de la courbe | **75 / 20 / 5 %** | une **forme**, pas une décision |
| Seuil de déplacement du sommet | **80 %** de réussite sur le socle | un **niveau** mesuré |
| Fenêtre de maîtrise | 20 épisodes, min. 10 | borne de significativité |
| Durée du run | **aucune** — s'arrête quand tout est acquis | conséquence du principe |

Vérifié en isolation (10 000 tirages) : **74,9 / 19,9 / 5,2 %**. Le sommet avance à 80 %,
**ne bouge pas** à 70 %, et le tirage se borne correctement au dernier palier.

**Ce qui change par rapport au cursus historique** : celui-ci ne tenait qu'**une seule**
fenêtre de maîtrise, celle du niveau courant — impossible de savoir si un palier ancien
était encore maîtrisé. La gaussienne en tient une **par palier**, ce qui est la condition
pour que « revenir en arrière » ait un sens mesurable.

### ⚠️ Le critère « 100 portes » corrigé par la mesure

L'utilisateur proposait de juger la journée sur *« 100 portes ouvertes »* plutôt que sur la
seule victoire. **L'intention est juste, le chiffre est impossible.** Mesuré sur 2 400
journées de logs réels :

| Portes franchies en une journée | min | médiane | **max** |
|---|---|---|---|
| Valeur observée | 1 | 1 | **2** |

Raison structurelle : `DoorKey` ne contient **qu'une seule porte** par carte, et la journée
compte ~2 épisodes. Un seuil à 100 ne se serait déclenché **0 fois sur 2 400 journées** —
le critère aurait été mort, et la gaussienne serait silencieusement retombée sur la seule
victoire.

C'est le piège documenté du projet (`SEUIL_CRISTAL = 0,80`, jamais franchi ; l'ablation
d'un organe vide) : **un seuil posé a priori, jamais confronté à une mesure.**

**L'intention est conservée, l'échelle est dérivée** : une journée est réussie si l'agent
gagne **ou** s'il franchit la porte dans **la majorité de ses épisodes**.

⚠️ **Deuxième ajustement (14/08)** — la première correction exigeait *une porte par
épisode* (`portes >= episodes`). Elle était **injuste et instable**, pour une raison
étrangère à la compétence : le nombre d'épisodes par jour dépend de la **patience**, qui
est adaptative.

| Patience | Épisodes/jour | Portes exigées *(v1)* |
|---|---|---|
| 120 ticks | ~3 | **3** |
| 250 ticks | ~1 | **1** |

Un agent dont la patience s'allonge — donc qui prend le temps de réfléchir, ce qu'on
veut — se voyait imposer une barre **plus basse** ; un agent pressé, une barre plus haute.
Le critère mesurait le **régime de patience** autant que la compétence.

`portes >= ceil(episodes / 2)` corrige : « la porte est franchie plus d'une fois sur
deux » garde le même sens quel que soit le nombre d'épisodes, et reste exigeant — sur un
seul épisode, il faut toujours franchir la porte.

### Ce qui reste à trancher

| Question | Pourquoi elle compte |
|---|---|
| σ fixe ou dérivé de la variance de maîtrise ? | cohérence avec la règle « rien en dur » — la forme 75/20/5 est posée, pas dérivée |
| Que devient `niveau_actuel` dans le `.brain` ? | entier aujourd'hui ; le banc contourne en gardant le pointeur et en tirant le palier au vol |

⚠️ **Rétrocompatibilité** : `niveau_actuel` est un INDEX sérialisé dans tous les `.brain`.
Le banc actuel ne le modifie pas (il intercepte `creer_env`), donc aucune greffe n'est
nécessaire — mais une intégration dans le noyau en exigerait une.

---

# Partie III — L'ordre proposé

L'ordre découle des dépendances et de la leçon « une brique à la fois, jamais empilées » :

L'ordre découle des dépendances, de la leçon « une brique à la fois », et **des ajustements
imposés par la grille développementale** (Partie II bis) :

| # | Action | Dépend de | Nature | Coût |
|---|---|---|---|---|
| ~~—~~ | ~~**P2.a/b** Analyse rétrospective (amorçage, g22)~~ | — | ✅ **FAIT 13/08** — H16 réfutée, H18 confirmée | — |
| ~~—~~ | ~~**P1** Versionner `noyau.py`~~ | — | ✅ **FAIT 13/08** — risque n°1 clos | — |
| ~~—~~ | ~~**P11** Conserver la valence à la promotion~~ | — | ✅ **FAIT 13/08** (v39.0) — mais **écrite seule, jamais lue** → P12 | — |
| **1** | **P12** Brancher le prior d'empreinte + A/B 6 graines, métrique **vitesse post-promotion** | P11 | cerveau, ~5 lignes | ~2 h |
| **2** | **P13** Le bit de présence auditive | greffe `persistance` | vecteur bio **en queue** | moyen |
| **3** | **P14** La promotion par croissance *(prototype `DoorKey`)* | — | wrapper monde | moyen |
| 4 | Consolider **2b sur 15-20 graines** | — | calcul | ~4 h |
| 5 | **P9** Sonde d'invariants | — | code léger | faible |
| 6 | **P3** Campagne de soustraction — **le test de falsification du cadre** | 4 | calcul lourd | la plus grosse |
| 7 | **P4.a→d** Le monde qui exige *(la nuit **après** P13)* | 5, **P13** | wrappers monde | moyen |
| 8 | **P5** L'aîné incarné | P4 partiel | monde + `.brain` | modeste |
| 9 | **P6** Liage **reconçu** : temps + rêve | **P4.d obligatoire** | cerveau (rêve) | moyen |
| 10 | **P10** Test de concept | P4.d, P6 | évaluation | faible |
| 11 | **P7** Écoute de C2 apprise | *si* ratio stagnant | cerveau | faible |
| 12 | **P8** Penser coûte | instrumentation d'abord | monde | faible |
| 13 | **P4.e** Crafter, puis le corps | qu'un mécanisme ait payé (P3) | horizon | élevé |

**Ce que le cadre développemental a changé dans cet ordre** :

- **P12 passe en tête** — sans consommateur, l'A/B de P11 mesurerait du vide.
- **P13 monte** de « correctif mineur » à priorité 2 : le cadre le croit fait, il ne l'est
  pas, et il conditionne la nuit (P4.a).
- **P14 apparaît** — elle n'existait pas avant le cadre.
- **P3 change de statut** : de « campagne de ménage » à **test de falsification** du cadre
  lui-même.

---

# Ce que je ne propose PAS

Par respect des réfutations déjà payées — chacune a coûté des runs :

| Écarté | Réfuté par |
|---|---|
| Toute forme de seuil dans le chemin de décision | v28, v29, v30, v37 |
| Réinjecter la confiance de C2 | chantier v37 §5.6 — deux implémentations, deux échecs |
| Un parent qui montre, nourrit ou nomme *pour* l'agent | 2c (0/5), 2c-fix — remplacé par P5 |
| Densifier davantage les sens | 2b : remplir un canal ne le rend pas utile |
| Empiler une brique de plus sur la pile actuelle | trois mesures : les gains ne s'additionnent pas |
| Étiqueter les paires du liage par type d'objet | violerait « rien n'est expliqué en dur » — remplacé par P6.a |
| Une nouvelle mécanique cognitive avant P3 | 6 testées, 6 échecs — la soustraction d'abord |

---

*Document arrêté au 13 août 2026. Il prolonge
[ETAT_DU_PROJET_aout_2026.md](../recherche/ETAT_DU_PROJET_aout_2026.md) (l'état des lieux) et
[CHANTIER_v38_monde_continu.md](../ameliorations_appliquees/CHANTIER_v38_monde_continu.md) (les mesures). Rien de ce
qui précède n'est implémenté ni validé : ce sont des propositions, à soumettre une par une
à la même méthode qui a réfuté les précédentes.*
