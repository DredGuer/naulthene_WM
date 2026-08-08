# Les Sens Combinatoires — cadrage

> **Statut : cadrage, aucune ligne de code écrite.** Ce document décrit une mécanique
> *envisagée*, pas livrée. Rien de ce qu'il contient n'existe dans `noyau.py` ni dans
> `colab.py` à ce jour. Il pose le problème, mesure l'écart avec l'existant, et propose
> un plan par étapes — la première étant, conformément à la doctrine du projet,
> **d'instrumenter avant de concevoir**.
>
> Origine : discussion du 2026-08-05, pendant le run de 10 000 jours. Fait suite à la
> clôture du cycle v33 (voir `Old_Archive_rmd/CONCEPTION_v33_memoire_emotionnelle.md`),
> dont la leçon centrale est : **une prémisse non mesurée coûte un cycle entier**.

---

## 1. L'objectif, en une phrase

Faire qu'un objet perçu **simultanément** par plusieurs sens finisse, par répétition, par
former une **représentation unique** — au point que la réactivation d'une seule modalité
rappelle les autres.

> Il trouve une pomme, donc il entend « pomme », voit la pomme et touche la pomme →
> à terme, par répétition, quand il verra une pomme son cerveau se dira « pomme ».

C'est le mécanisme du cortex associatif : la **convergence multimodale par
co-occurrence**. Deux signaux qui arrivent ensemble, assez souvent, finissent par se
prédire l'un l'autre.

### La contrainte non négociable

**Le système doit fonctionner avec un seul sens.** Amputer un sens dégrade les chances de
survie, jamais la capacité de fonctionner. Un agent aveugle doit continuer à agir avec
l'ouïe et le toucher ; un agent réduit à la seule vue doit rester l'agent actuel, à
l'identique.

Cette contrainte est **plus forte** que l'objectif de liage, et prime sur lui en cas de
conflit. Elle interdit toute conception qui rendrait un sens *nécessaire*.

---

## 2. Les rôles asymétriques : chaque sens ne fait pas le même métier

C'est le principe directeur de tout ce document, et il change la conception.

L'architecture actuelle traite vue et ouïe en **miroir** : deux portes symétriques
(`porte_visuelle`, `porte_auditive`), deux têtes prédictives symétriques
(`generateur_attente`, `generateur_attente_audio`), deux pertes JEPA de même forme. Cette
symétrie est **fausse** au regard de ce que ces sens font réellement.

| Sens | Métier | Objectif d'apprentissage adapté |
|---|---|---|
| **Vue** | **Prédit.** Pose le concept, anticipe pour soulager le cerveau | Prédiction temporelle (JEPA) — ✅ déjà en place |
| **Ouïe** | **Compense.** Associe le connu à un nom/son ; peut halluciner | Association, **pas** prédiction temporelle |
| **Odorat** | **Annonce.** Oriente vers la ressource avant de la voir | Validation en amont |
| **Goût** | **Confirme.** Vérifie après coup, évite l'empoisonnement | Validation en aval |
| **Toucher** | **Situe le corps.** Chaud/froid/pression, état interne | Interoception, faible seul, précieux en appui |

### 2.1 La vue prédit — et ton code le fait déjà

Si l'agent devait traiter consciemment tout son champ visuel à chaque instant, il
saturerait. La vue anticipe, et **seule l'erreur de prédiction remonte** : c'est le
principe du *predictive coding*, et c'est exactement ce que `perte_jepa` implémente.

Preuve mesurée : le JEPA du run en cours est à **0,0006**, plat depuis le début. La vue
prédit si bien qu'elle ne se trompe presque plus. Le mécanisme fonctionne — ce n'est pas
là qu'est le problème du projet.

### 2.2 L'ouïe ne prédit pas, elle compense — et le code est en retard sur ce constat

Un son n'annonce pas le son suivant. Il **nomme ce qui est là**. Prédire la trame audio
suivante est un objectif mal posé pour un sens dont le métier est l'association.

Corollaire assumé : un canal qui complète est un canal qui **invente parfois**. Entendre
des bruits inexistants est le prix normal d'un système associatif, pas un défaut à
corriger.

> **Constat de code, vérifié le 2026-08-05.** `coeff_jepa_audio` vaut **0.0 par défaut**
> (`noyau.py`, docstring de `perte_jepa`) et n'est monté que progressivement par la boucle
> principale. Autrement dit, **l'ouïe ne prédit déjà quasiment pas dans les faits.**
> L'intuition est en avance sur l'implémentation : la symétrie vue/ouïe existe dans la
> structure du code mais pas dans son comportement effectif.

Conséquence pour la conception : donner à l'ouïe une **tête associative** plutôt qu'une
tête prédictive. C'est une question ouverte (§7.2), pas une décision prise.

### 2.3 Odorat et goût : une chaîne de validation, pas de prédiction

L'odorat oriente **à distance**, le goût confirme **au contact**. L'ordre temporel est
causal : sentir avant de goûter, c'est ce qui évite l'empoisonnement.

Cette chaîne est **déjà écrite dans le code**. Docstring de `lire_chimie`
(`bus_sensoriel.py:276`) :

> « l'odorat oriente vers la ressource avant même de la voir, le goût confirme après coup
> qu'elle a bien été ingérée »

Nuance importante par rapport à la formulation initiale : ces sens ne *prédisent* pas, ils
**valident**. L'odorat annonce une hypothèse, le goût la confirme ou la dément. C'est de
la vérification, pas de l'anticipation — et un signal de validation n'a **pas besoin d'une
tête prédictive**. Distinction qui économise deux couches.

### 2.4 Le toucher : le sens le plus complexe, et le plus pauvre dans le code actuel

Le toucher n'est pas un sens mais un faisceau : chaud, froid, pression, position. Seul il
renseigne mal sur le monde — mais il est le seul à renseigner sur **l'état du corps**.

Écart mesuré avec l'implémentation :

| Ce que le toucher devrait être | Ce que `lire_toucher` fait aujourd'hui (4 dims) |
|---|---|
| Chaud / froid | ❌ absent |
| Pression | ❌ absent |
| État du corps (interoception) | ❌ absent |
| Contact frontal | ✅ `contact_frontal` |
| Objet en main | ✅ `objet_en_main` |
| Orientation | ✅ `cos`, `sin` |

Le `lire_toucher` actuel fait de la **proprioception géométrique** (où je suis, ce que je
porte), pas de l'**interoception** (dans quel état est mon corps). Le sens décrit ici
n'existe pas encore.

Note : une partie de l'état corporel existe ailleurs dans le projet — le
`BiologicalHomeostasisEngine` porte faim, soif, fatigue. La question n'est donc pas
« créer » l'interoception mais décider si elle relève du toucher ou reste viscérale (§7.4).

---

## 3. Bibliothèque et indexeur : les deux chemins doivent coexister

### 3.1 Le principe

Chaque sens doit entrer **deux fois** :

- **seul**, en gardant sa représentation propre — c'est la **bibliothèque**, où chaque
  modalité reste consultable et interprétable pour elle-même ;
- **croisé** avec les autres — c'est l'**indexeur**, qui apprend les correspondances entre
  rayons.

Les deux ensemble fluidifient le travail et l'énergie : l'index évite de tout relire, la
bibliothèque garde le détail que l'index a résumé.

Cette architecture correspond à une distinction réelle du cortex : **cortex sensoriel
primaire** (chaque modalité, séparément) et **cortex associatif** (les liaisons). Ce n'est
pas une métaphore décorative, c'est le plan d'organisation.

### 3.2 Ce que ça condamne dans l'architecture actuelle

La somme du bus actuel (`noyau.py:389-394`) est un indexeur **sans bibliothèque** :

```python
bus_latent = stimulus_visuel + stimulus_auditif
```

Une fois sommés, les deux signaux sont **irrécupérables séparément**. Aucune couche en aval
ne peut consulter « ce que la vue seule disait ». La bibliothèque a été détruite au moment
de l'indexation.

C'est aussi ce qui rend l'ablation brutale : retirer l'ouïe change la **norme** du vecteur
sommé, donc l'échelle d'activation de tout l'aval (`hippocampe`, `analyseur`,
`tete_motrice`). Le réseau subit un changement de régime silencieux, non déclaré.

> **La somme n'est pas une association. C'est un écrasement.** Elle mélange sans lier, et
> détruit l'accès séparé.

---

## 4. Où en est l'architecture réellement (état vérifié au 2026-08-05)

### 4.1 Les deux chemins d'entrée existants

Le projet n'a pas un chemin sensoriel mais **deux**, et c'est le fait structurant.

| Sens | Chemin | Entre dans `bus_latent` ? | Cible JEPA ? |
|---|---|---|---|
| **Vue** (147 dims) | `porte_visuelle` → `bus_latent` | ✅ oui, par somme | ✅ oui |
| **Ouïe** (130 dims) | `porte_auditive` → `bus_latent` | ✅ oui, par somme | ⚠️ oui *en structure*, mais `coeff_jepa_audio = 0.0` par défaut |
| **Toucher** (4 dims) | queue du `vecteur_bio` → `integrateur_bio` | ❌ non | ❌ non |
| **Odorat** (2+2 dims) | queue du `vecteur_bio` → `integrateur_bio` | ❌ non | ❌ non |
| **Goût** (2 dims) | queue du `vecteur_bio` → `integrateur_bio` | ❌ non | ❌ non |
| **Exo-Sens** (8 dims) | queue du `vecteur_bio` → `integrateur_bio` | ❌ non | ❌ non |

**Conséquence pour l'objectif** : dans l'exemple de la pomme, vue et ouïe convergent déjà
(par somme) ; **le toucher, lui, n'y est pas**. Il rejoint le flux beaucoup plus loin,
après compression, concaténé et non sommé. Il ne peut pas participer à une liaison au sens
où on l'entend ici.

C'est un invariant v29.0 explicite, pas un oubli (`CLAUDE.md`, invariant 3 du Bus
Sensoriel). Le remettre en cause est une décision utilisateur (§7.1).

### 4.2 Il n'existe aucune pression au liage

**Additionner deux signaux ne crée aucune association.** Le JEPA prédit l'instant suivant
*dans chaque modalité séparément* : `generateur_attente` pour la vue,
`generateur_attente_audio` pour l'audio, avec deux pertes **délibérément disjointes**
depuis la v22.1 (correctif « empoisonnement du JEPA »).

Il n'existe **aucun terme de perte** disant « ces deux signaux arrivent ensemble,
rapproche-les ». Une co-occurrence traverse le bus sans laisser de trace structurelle.

> **Le liage n'est pas un effet de bord de la convergence. C'est un objectif
> d'apprentissage à part entière, qu'il faut écrire.**

### 4.3 Le trou technique : « absent » et « nul » sont le même vecteur

Aujourd'hui, un sens indisponible retombe sur une valeur neutre :

| Sens | Valeur si indisponible | Code |
|---|---|---|
| Toucher | `[0.0] × 4` | `bus_sensoriel.py:246, 271` |
| Exo-Sens | `[0.0] × 8` | `bus_sensoriel.py:481` |
| Clinotaxie | `[0.5, 0.5]` | `bus_sensoriel.py:334` |
| Ouïe | branche `else`, terme absent de la somme | `noyau.py:393` |

Le problème : **ces valeurs neutres sont indistinguables de vraies mesures.**

- Un toucher à `0.0` signifie « pas de contact frontal » — une information réelle.
- Un toucher à `0.0` signifie aussi « je n'ai pas de sens du toucher » — l'absence
  d'information.

Le réseau reçoit le même vecteur dans les deux cas et **ne peut pas les distinguer**. Il
apprend une moyenne des deux situations, fausse dans chacune.

---

## 5. Le principe proposé : présence explicite

### 5.1 La règle

Chaque modalité entre au bus **à chaque tick, sans exception**, accompagnée d'un **bit de
présence** qui dit si sa valeur est une mesure ou un silence.

```
canal = (valeur, présence)

présence = 1.0  → la valeur est une mesure réelle
présence = 0.0  → la valeur est un remplissage, à ignorer
```

Quand `présence = 0`, la valeur est mise au neutre de sa modalité (`0.0` pour le toucher,
`0.5` pour la clinotaxie — le neutre v32.0, à ne surtout pas changer) et le réseau **sait**
qu'elle ne veut rien dire.

C'est le rôle du `None` : non pas une absence de canal, mais un canal présent qui déclare
son propre silence.

### 5.2 Pourquoi ça débloque le fonctionnement mono-sens

Sans bit de présence, retirer un sens change la distribution d'entrée de façon opaque. Avec
le bit, c'est une opération **déclarée** : le réseau apprend, dès l'entraînement, à
fonctionner avec des canaux muets parce qu'il en rencontre.

L'ablation devient gracieuse au lieu d'être une corruption d'entrée. **Un seul sens présent
reste un état valide et connu**, pas un cas dégénéré jamais vu.

### 5.3 Le corollaire obligatoire : le dropout modal

Un réseau qui n'a jamais vu de canal muet ne saura pas en gérer un. **Un bit de présence
qui vaut toujours 1 ne sert à rien.**

Il faut couper aléatoirement une modalité pendant l'entraînement, à faible probabilité.
C'est ce qui force le réseau à ne dépendre d'aucun sens en particulier, et ce qui rend la
dégradation progressive plutôt que brutale.

> **Sans dropout modal, pas de robustesse mono-sens. C'est la contrepartie du bit de
> présence, pas une option.**

Ne jamais couper toutes les modalités simultanément — un agent sans aucun sens n'a rien à
apprendre de ce tick. Ordre de grandeur à calibrer par mesure (§8), jamais par intuition.

---

## 6. Le croisement N-aire : la réponse au point d'incertitude

> *« Mon seul point d'incertitude est la liaison entre les sens en in pour le out, car le
> cerveau humain peut traiter les signaux séparés, et croiser avec 2/3/4 sens. »*

C'est le bon point d'incertitude, et il n'a qu'une réponse propre.

### 6.1 Pourquoi il ne faut câbler aucune combinaison

Avec 6 canaux, il y a **2⁶ − 1 = 63** combinaisons possibles (vue seule, vue+ouïe,
vue+toucher, vue+ouïe+toucher…). Écrire un chemin par combinaison est ingérable — et
chaque nouveau sens **doublerait** le nombre de chemins.

### 6.2 La réponse : un croisement qui ne dépend pas de N

Un mécanisme d'attention prend **N canaux présents** et les croise, quel que soit N. Chaque
canal peut consulter les autres ; le masque de présence exclut les canaux muets du
croisement.

Les combinaisons ne sont **pas déclarées, elles émergent**. Rien à câbler, rien à
maintenir.

### 6.3 La combinatoire exacte à 5 sens

Ce que le croisement doit produire, énoncé exhaustivement.

**Niveau 1 — les 5 solos (certains à 100 %, la bibliothèque du §3.1)**

Chaque sens doit rester **récupérable seul**, indépendamment de tout croisement :

`vue` · `ouïe` · `odorat` · `goût` · `toucher`

C'est ce qui garantit la contrainte du §1 : un sens amputé ne casse rien, un sens seul
suffit à agir.

**Niveau 2 — les 10 paires (à confirmer par émergence ou par règle logique)**

| # | Paire | Plausibilité *a priori* |
|---|---|---|
| 1 | vue ↔ ouïe | forte — le liage nommé (la pomme et son nom) |
| 2 | vue ↔ odorat | forte — l'odeur annonce, la vue confirme la source |
| 3 | vue ↔ goût | moyenne — voir avant d'ingérer |
| 4 | vue ↔ toucher | forte — objet vu / objet tenu |
| 5 | ouïe ↔ odorat | faible — peu de lien causal naturel |
| 6 | ouïe ↔ goût | faible — sauf nommage explicite (« c'est amer ») |
| 7 | ouïe ↔ toucher | moyenne — un contact fait du bruit |
| 8 | odorat ↔ goût | **très forte** — la chaîne de survie du §2.3 |
| 9 | odorat ↔ toucher | faible |
| 10 | goût ↔ toucher | moyenne — texture et saveur au même contact |

C(5,2) = 10 : la liste est **complète**, aucune paire manquante.

⚠️ La colonne « plausibilité » est un **pronostic**, pas une prescription. Elle sert à
savoir quelles paires devraient émerger si le mécanisme fonctionne — et donc à repérer un
liage qui triche (paires fortes absentes, paires faibles dominantes). Elle ne doit
**jamais** être câblée en dur : ce serait exactement le « déclenchement sur seuil codé en
dur » que le projet a refusé trois fois (v28, v29, v30).

**Niveau 3+ — les triplets et au-delà : décision ouverte**

Le principe « chaque entrée associée à **un seul** autre sens » s'arrête aux paires. Mais
un croisement N-aire (§6.2) produit naturellement tous les ordres :

| Niveau | Nombre | Exemple |
|---|---|---|
| Solos | 5 | vue |
| Paires | 10 | vue + ouïe |
| **Triplets** | **10** | vue + ouïe + toucher |
| Quadruplets | 5 | vue + ouïe + odorat + goût |
| Quintuplet | 1 | les 5 ensemble |
| **Total** | **31** | 2⁵ − 1 |

Deux lectures possibles, à trancher :

- **Paires seules** — les triplets se composent à partir des paires. Plus simple, plus
  lisible, moins coûteux. Cohérent avec la formulation initiale.
- **Ordre libre** — le croisement N-aire les produit tous sans code supplémentaire, et le
  cerveau humain croise bien 3-4 sens simultanément (point d'incertitude du §6).

**Ce n'est pas une décision à prendre a priori.** Si le croisement du §6.2 est retenu, les
triplets viennent gratuitement : la question devient alors de savoir s'il faut les
*contraindre* à ne pas apparaître, ce qui serait un travail supplémentaire pour une
restriction non justifiée. La télémétrie `Cooc_N_Canaux` (§8, Étape 0) mesurera d'abord
combien de canaux co-occurrent réellement — si la réponse est « rarement plus de 2 », la
question se referme d'elle-même.

Trois propriétés qui tombent gratuitement :

- **Mono-sens** = le cas `N = 1`. Aucun code spécial : un seul canal présent, rien à croiser,
  le canal passe seul. La contrainte du §1 est satisfaite *par construction*, pas par une
  branche `if`.
- **Ajouter un 7ᵉ sens** = ajouter un canal, sans toucher au croisement.
- **La bibliothèque survit** : chaque canal garde sa voie propre en sortie, l'index
  s'ajoute au lieu d'écraser (§3.1).

### 6.4 Le point d'attention : le coût

L'attention sur N canaux coûte plus cher qu'une somme. Sur 6 canaux le surcoût reste
modeste, mais il doit être **mesuré** avant d'être accepté — ce projet tourne sur des runs
de 10 000 jours × 400 ticks, où un facteur 2 en temps de tick n'est pas anodin.

À noter aussi : rien n'oblige à mettre les 6 canaux à la même granularité. Vue (147 dims)
et toucher (4 dims) ne pèsent pas pareil, et une projection préalable vers une dimension
commune sera probablement nécessaire — sinon la vue écrase tout par simple effet d'échelle,
exactement comme aujourd'hui.

---

## 7. Décisions ouvertes — à trancher par l'utilisateur

Ces points **ne doivent pas être tranchés par le code**. Plusieurs touchent des invariants
documentés dans `CLAUDE.md`.

### 7.1 Le toucher entre-t-il dans le croisement ?

| Option | Conséquence |
|---|---|
| **A — statu quo** (le toucher reste dans `integrateur_bio`) | Invariant v29.0 respecté. Mais le toucher **ne participe pas** au liage : la pomme se réduit à vue+ouïe. |
| **B — canal à part entière** dans le croisement | Le toucher devient liable, conformément au §2.4. Mais : nouvelle couche à déclarer dans `__init__` **et** `cycle_sommeil_global` **et** `declencher_neurogenese` (oublier l'un des trois casse silencieusement), et 4 dims face à 147 dims visuelles seront écrasées sans projection préalable (§6.4). |

⚠️ `CLAUDE.md` interdit explicitement B « sans demande explicite de l'utilisateur ».
**Recommandation : commencer par A.** Prouver le liage sur vue↔ouïe, où les deux portes
existent déjà, avant de toucher à la hiérarchie sensorielle.

### 7.2 L'ouïe garde-t-elle une tête prédictive ?

Le §2.2 suggère que non : son métier est l'association, pas la prédiction temporelle. Mais
`generateur_attente_audio` existe et a été construite délibérément en v22.1.

Trois options : la garder telle quelle, la remplacer par une tête associative, ou garder les
deux (`coeff_jepa_audio` restant bas). **Le fait que ce coefficient soit déjà à 0.0 par
défaut rend cette décision moins coûteuse qu'elle n'en a l'air** — l'ouïe ne prédit
pratiquement pas aujourd'hui.

### 7.3 Le liage entre-t-il dans la cible JEPA ?

Le JEPA compare aujourd'hui le bus prédit au bus réel **de la vision seule**
(`noyau.py:636`). Si le bus contient des signaux liés multimodaux, cette cible change de
nature. À examiner avant, pas après — c'est exactement le défaut que la v22.1 avait corrigé
sous le nom d'« empoisonnement du JEPA ».

### 7.4 L'interoception relève-t-elle du toucher ou du viscéral ?

Le §2.4 décrit un toucher qui renseigne sur l'état du corps. Mais faim, soif et fatigue
existent déjà dans `BiologicalHomeostasisEngine`, sur un chemin séparé.

Faut-il les faire remonter dans le toucher (cohérent avec le rôle décrit), ou garder la
séparation actuelle ? Décision de modèle, pas d'implémentation.

### 7.5 Où entrent les bits de présence ?

Le contrat **append-only** est absolu (`CLAUDE.md`, invariant 2) : toute nouvelle dimension
va **en queue**, jamais au milieu, sous peine de décaler silencieusement les acquis des
`.brain` existants.

Les bits des sens faibles peuvent aller en queue du `vecteur_bio`. Ceux de la vue et de
l'ouïe, non — ces modalités n'ont pas de dims dans le `vecteur_bio`. Il faudra un autre
point d'entrée, et `_greffer_vecteur_bio_etendu` devra être étendue (**greffe par recopie,
jamais par exclusion**).

### 7.6 MiniGrid suffit-il ?

Non, et il faut le dire franchement.

MiniGrid a **4 types d'objets × 6 couleurs**, rendus identiques au pixel près : **une seule
apparence possible** par objet.

Un concept n'a de raison d'exister que s'il faut **généraliser sur des instances variées**.
Avec une seule instance, mémoriser suffit — et une table de correspondance apparence→nom
est indistinguable d'un concept.

> Le liage marchera peut-être techniquement sur MiniGrid. Mais on ne pourra pas **prouver**
> que c'est un concept plutôt qu'une table de correspondance. C'est une limite de
> l'environnement, pas de l'architecture — aucune quantité de code ne la contourne.

MiniGrid permet de **valider la mécanique** ; il ne permettra pas de **démontrer la
conceptualisation**. Le second objectif demandera une source visuelle à variance interne
réelle — un changement de nature du projet.

---

## 8. Plan par étapes

Ordre imposé par la doctrine : **instrumenter d'abord, calibrer ensuite** (v30.1), et ne
jamais concevoir sur une prémisse non mesurée (leçon v33).

### Étape 0 — Mesurer la co-occurrence (télémétrie pure, aucun changement de comportement)

**La seule étape à faire tant que les décisions du §7 ne sont pas tranchées.**

| Métrique | Ce qu'elle répond |
|---|---|
| `Cooc_Vue_Ouie` | % de ticks où vue **et** ouïe sont présentes |
| `Cooc_Vue_Toucher` | % de ticks avec contact frontal ET vision |
| `Cooc_N_Canaux` | distribution du nombre de canaux présents (1, 2, 3…) — dimensionne le §6 |
| `Presence_Ouie` | % de ticks où `obs_auditive is not None` |

Contraintes, reprises de la v33 (§ télémétrie de `CLAUDE.md`) :

- compteurs remis à zéro dans `_reinitialiser_buffers_journee` (piège `score_vocal_jour`
  v27.0 : sans ça la « moyenne du jour » cumule depuis la naissance) ;
- accumulés dans `traiter_tick`, agrégés dans `executer_nuit` (ligne console **et** clé
  `log_wandb`) ;
- clés **conditionnelles** — pas de zéros trompeurs quand la mécanique dort ;
- **validation par empreinte MD5 à graine fixée** : identique avec et sans les appels de
  télémétrie.

**Verdict attendu.** Si `Cooc_Vue_Ouie ≈ 0 %` — hypothèse la plus probable (§9) — alors une
perte de liage n'aurait rien à apprendre, et l'Étape 1 devient **la synchronisation, pas le
modèle**. C'est ce qui éviterait de refaire l'erreur de la v33.

### Étape 1 — La synchronisation (conditionnelle au verdict)

Faire coexister environnement visuel et professeur sur le même tick (§9). Le plus gros
travail d'ingénierie du chantier, et le moins spectaculaire. Pas de liage possible avant.

### Étape 2 — Bit de présence + dropout modal

Les deux ensemble, jamais séparément (§5.3).

Validation : le run nominal (tous sens présents) doit rester **équivalent** à l'actuel,
prouvé par empreinte à graine fixée. Si le nominal se dégrade, revoir avant d'aller plus
loin.

### Étape 3 — Le croisement N-aire

Remplacer la somme par un croisement masqué par la présence (§6), en conservant la voie
propre de chaque canal (§3.1).

Mesurer le **coût en temps de tick** avant d'accepter (§6.3).

### Étape 4 — La perte de liage

Un terme qui **rapproche** les modalités co-occurrentes et **éloigne** les paires qui ne
co-occurrent pas. La seconde moitié est indispensable : sans négatifs, la solution triviale
est l'**effondrement** — tout au même point, perte nulle, plus rien de distingué. Mode
d'échec silencieux : la courbe descend magnifiquement pendant que la représentation meurt.

Sources de négatifs, par simplicité croissante : décalage temporel (faible), souvenirs de
l'hippocampe (francs), autres objets du même tick (le plus fort, mais dépend de l'Étape 1).

Une paire dont une modalité est muette doit être **exclue** du terme : rapprocher un signal
réel d'un silence apprendrait à rendre le silence prédictif — l'inverse du but. Le bit de
présence est donc aussi un **masque de perte**.

Instrumenter la variance des embeddings **avant** d'activer la perte, pas après.

### Étape 5 — La preuve

**Test de rappel croisé** : présenter une modalité seule et mesurer si l'autre se réactive.
Montrer la pomme sans le son → l'embedding auditif s'approche-t-il de « pomme » ? Si oui,
liage. Si non, simple co-activation.

**Test d'ablation** : couper un sens sur un cerveau entraîné et mesurer la dégradation. Une
ablation qui ne dégrade rien signale un canal mort. C'est aussi la vérification directe de
la contrainte du §1 — la dégradation doit être **progressive**, jamais un effondrement.

---

## 9. L'obstacle qu'aucune architecture ne résout : la synchronisation

Le mécanisme suppose que la pomme est **vue et nommée au même instant**. Or dans le projet
actuel, ça n'arrive jamais.

- Les parcours de navigation (`cursus_developpemental`, `cursus_bebe`) ont un environnement
  MiniGrid mais **aucun professeur qui parle des objets**.
- L'École de la Parole (`client_professeur`, `professeur_gemma`) a un professeur qui parle
  mais **pas d'environnement visuel synchronisé**.

Les deux existent, **jamais ensemble sur le même tick**. Il n'y a donc à ce jour **aucune
co-occurrence vue↔son à apprendre**. Une perte de liage n'aurait rien à mordre.

> **C'est le vrai premier chantier — de la plomberie, pas du modèle.** Faire prononcer par
> le professeur le nom de l'objet regardé, au tick où il est regardé.

---

## 9 bis. Mesure préalable : la disponibilité réelle des sens (run `az794yzw`)

Le run de 5 000 jours au Doctorat (jours 5001→10000, terminé le 2026-08-05) fournit une
mesure directe qui **précède et contraint** l'Étape 0 : la plupart des canaux ne sont
jamais présents.

| Canal | Disponibilité mesurée au Doctorat | Conséquence pour le liage |
|---|---|---|
| **Vue** | 100 % des ticks | seul canal toujours là |
| **Toucher** (contact frontal) | ~49-58 % des ticks | co-occurrence vue↔toucher **réelle et fréquente** |
| **Odorat** | **0,0 % des ticks** (max 0.00) | aucune source sur les cartes MultiRoom |
| **Goût** | **0 tick** | jamais de consommation |
| **Ouïe** | non instrumentée sur ce parcours | co-occurrence vue↔ouïe présumée nulle (§9) |

> **8 des 10 paires du §6.3 sont aujourd'hui inobservables**, faute de signal. Les seules
> co-occurrences réellement disponibles au Doctorat sont **vue↔toucher** (fréquente) et,
> potentiellement, vue↔ouïe si la synchronisation du §9 est faite.

Ce constat déplace la priorité : avant de concevoir un croisement à 5 canaux, il faut des
canaux qui portent un signal. La paire **odorat↔goût** — pronostiquée « très forte » au
§6.3 parce qu'elle est la chaîne de survie du §2.3 — est **strictement inobservable** dans
l'environnement actuel, où ni nourriture ni eau n'apparaissent.

**Implication pour l'Étape 0** : `Cooc_N_Canaux` risque de répondre « 1 ou 2 canaux, jamais
plus » — ce qui refermerait de lui-même le débat des triplets (§6.3), mais surtout
signalerait que le chantier commence par **peupler l'environnement**, pas par croiser des
canaux vides.

---

## 10. Ce que ce document ne prétend pas

- **Aucune ligne de code n'a été écrite.** Tout est au conditionnel.
- **L'Étape 0 seule est recommandée à ce stade**, et seulement après la fin du run en cours
  (10 000 jours) — l'interrompre détruirait la seule série longue disponible.
- **La conceptualisation (« distinguer un fruit d'un légume ») n'est pas atteignable sur
  MiniGrid** (§7.6). Ce document vise le **liage** : brique nécessaire, pas suffisante.
- Les rôles asymétriques du §2 sont un **modèle de travail**, pas un fait démontré. Ils
  guident la conception ; ils ne la justifient pas à eux seuls.
- Les six décisions du §7 appartiennent à l'utilisateur. Plusieurs touchent des invariants
  que `CLAUDE.md` protège explicitement.

---

## 11. Références internes

| Sujet | Où |
|---|---|
| Hiérarchie des 5 sens, identité C1/C2, Exo-Sens | `explications_readme.md` §15 |
| Invariants du Bus Sensoriel (pur numpy, append-only, sens faibles hors JEPA) | `CLAUDE.md` |
| Formules d'origine du toucher/odorat/goût, options écartées v29 | `Old_Archive_rmd/EXPLICATIONS_v29_sens.md` ⚠️ chiffres dépassés |
| Pivot de C3 en 6ᵉ sens, options écartées v30 | `Old_Archive_rmd/CONCEPTION_v30_exo_sens.md` |
| Séparation des pertes JEPA vision/audio (« empoisonnement du JEPA ») | `CHANGELOG.md`, v22.1 |
| Leçon méthodologique « prémisse non mesurée » | `Old_Archive_rmd/CONCEPTION_v33_memoire_emotionnelle.md` |
