# Avis & Propositions — 13 août 2026

> **Nature du document** : carnet de recherche, non normatif. Il contient deux choses :
> l'**avis complet** rendu sur le projet après la campagne des 11-13 août, et les
> **propositions de solutions** aux problèmes identifiés dans
> [ETAT_DU_PROJET_aout_2026.md](ETAT_DU_PROJET_aout_2026.md).
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
- [Partie III — L'ordre proposé](#partie-iii--lordre-proposé)
- [Ce que je ne propose PAS](#ce-que-je-ne-propose-pas)

---

# Partie I — L'avis

## 1. Ce que le projet a de véritablement rare

### 1.1 La culture de l'échec documenté

Peu de dépôts — y compris académiques — conservent les hypothèses réfutées, les treize
erreurs de diagnostic et les options écartées *avec leurs raisons*.
[recherche_bug_or_not_bug.md](recherche_bug_or_not_bug.md), les tableaux « écarté et
pourquoi » du [chantier v37](CHANTIER_v37_equilibre_c1_c2.md), le README qui affirme
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

### P2.a Exploiter les données qui existent déjà *(coût : zéro calcul)*

Le dépôt contient **~180 runs W&B et une centaine de `.brain`**. Une analyse
rétrospective peut tester dès maintenant l'hypothèse la plus importante sur la variance :

> **La loterie des premiers jours.** Corréler, sur tous les runs existants, le *jour de la
> première victoire* avec le *palier final*. Si la corrélation est forte, la variance n'est
> pas du bruit : c'est un effet d'amorçage — une victoire précoce lance le cercle vertueux
> (dopamine → myéline → consolidation), son absence laisse le cerveau au plancher.

Si c'est confirmé, le levier n'est pas statistique mais développemental : ce que 2b fait
peut-être déjà (aucune régression = personne ne rate l'amorçage ?).

### P2.b Étudier g22 au lieu de le moyenner

Le run g22 (69 victoires, cursus complet en 239 jours) est traité comme un outlier à
neutraliser. C'est peut-être **l'observation la plus précieuse du projet** : le régime
existe, il est atteignable, une graine l'a trouvé. Analyse de trajectoire complète :
séquence des premières expériences, chocs dopaminergiques des 50 premiers jours, ordre des
promotions. On ne cherche pas la moyenne d'un phénomène rare — on cherche **sa porte
d'entrée**.

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

# Partie III — L'ordre proposé

L'ordre découle des dépendances et de la leçon « une brique à la fois, jamais empilées » :

| # | Action | Dépend de | Nature | Coût |
|---|---|---|---|---|
| 1 | **P1** Versionner `noyau.py` | — | processus | une session |
| 2 | **P2.a/b** Analyse rétrospective (amorçage, g22) | — | zéro calcul | une session |
| 3 | Consolider **2b sur 15-20 graines** *(priorité 1 de l'état des lieux, inchangée)* | — | calcul | ~4 h |
| 4 | **P9** Sonde d'invariants + les 2 correctifs identifiés (silence, `%` rêve) | P1 | code léger | faible |
| 5 | **P3** Campagne de soustraction | 3 | calcul lourd | la plus grosse |
| 6 | **P4.a→d** Le monde qui exige, brique par brique | 3, 4 | wrappers monde | moyen |
| 7 | **P5** L'aîné incarné | P4 partiel | monde + `.brain` | modeste |
| 8 | **P6** Liage : temps + rêve | **P4.d obligatoire** | cerveau (rêve) | moyen |
| 9 | **P10** Test de concept | P4.d, P6 | évaluation | faible |
| 10 | **P7** Écoute de C2 apprise | *si* ratio stagnant | cerveau | faible |
| 11 | **P8** Penser coûte | instrumentation d'abord | monde | faible |
| 12 | **P4.e** Crafter, puis le corps | qu'un mécanisme ait payé (P3) | horizon | élevé |

Les trois premières lignes ne se discutent pas entre elles : elles sont indépendantes,
peu coûteuses, et tout le reste s'appuie dessus.

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
[ETAT_DU_PROJET_aout_2026.md](ETAT_DU_PROJET_aout_2026.md) (l'état des lieux) et
[CHANTIER_v38_monde_continu.md](CHANTIER_v38_monde_continu.md) (les mesures). Rien de ce
qui précède n'est implémenté ni validé : ce sont des propositions, à soumettre une par une
à la même méthode qui a réfuté les précédentes.*
