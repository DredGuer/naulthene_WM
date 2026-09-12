# CHANTIER EVA-01 — Le banc final standardisé

- **Registre** : [`REGISTRE_PROBLEMES_A_CORRIGER.md`](REGISTRE_PROBLEMES_A_CORRIGER.md) → **EVA-01**, priorité **P1 — 🔵 À mesurer**
- **Statut de ce document** : **design validé par l'auteur le 12/09/2026** (six sections relues et
  approuvées une par une). Il n'autorise **pas** encore l'implémentation : voir §12 « Porte ».
- **Nature** : chantier d'**instrument**. Il ne change aucune mécanique cognitive et **ne modifie
  pas une seule ligne de `noyau.py`** — c'est un choix explicite (§2, décision D1).

---

## 1. La question posée

Le registre formule le constat ainsi : « Le juge principal est bruité et dépend du palier atteint. »

Ce que le dépôt documente déjà : la maîtrise sur une fenêtre de 20 épisodes est quantifiée par pas
de 5 %, le niveau atteint peut saturer, la compétence au banc varie fortement **à maîtrise égale**,
et une promotion change la carte finale sur laquelle la maîtrise est lue.

La conséquence mesurée, qui motive la priorité P1 : **le juge de maîtrise n'explique qu'environ
16 % de la variance de la compétence réelle** (`r² = 0,157`, mesuré sur `historique_episodes_niveau`,
carnet [DIRECTIVITE_31082026](../recherche/campagnes/DIRECTIVITE_31082026_le_goulot_est_moteur.md)). Or la prochaine étape scientifique prévue est la
**campagne de soustraction (P3)** : mesurer la valeur d'un organe en le retirant d'un cerveau qui
fonctionne. Mesurer cela avec un juge à 16 % reproduirait l'erreur d'« effet nul » déjà consignée
dans le dépôt. **L'instrument passe donc avant la mesure.**

Le registre demande cinq choses (points 1 à 5 de son « Amélioration proposée ») et fixe trois
critères de clôture : protocole standard **versionné** · banc final **obligatoire** dans les
nouvelles campagnes majeures · **séparation claire** entre graines d'entraînement et d'évaluation.

---

## 2. Décisions validées

Quatre décisions ont été arbitrées par l'auteur avant toute écriture de code. Elles sont
**contraignantes** pour l'implémentation.

### D1 — Reproductibilité côté banc, `noyau.py` intact

Le banc fixe la graine **torch** par épisode, en plus de la graine d'environnement. On mesure donc
la politique **réellement entraînée** (celle qui échantillonne), et non un mode glouton qui
n'aurait pas appris. La source de vérité unique (ARC-01) n'est pas touchée.

*Pourquoi ce choix plutôt qu'un mode `argmax` d'évaluation* : un mode glouton mesure le **mode**
d'une distribution, pas le comportement — et le dépôt a déjà mesuré qu'une distribution « tiède »
(`P(avancer) = 0,376`) rend ce mode trompeur (`noyau.py`, section sur l'échantillonnage). Écarter
l'échantillonnage flatterait les cerveaux hésitants. Coût de D1 : la reproductibilité dépend d'un
RNG global — fragile si du parallélisme est introduit un jour. Ce coût est accepté et consigné.

### D2 — Métrique primaire : le succès binaire sur cartes figées

**Primaire** : taux de franchissement, binaire, sur deux cartes imposées à tous les cerveaux.
**Secondaires déclarées d'avance** : retour, longueur normalisée (médiane), chacune avec son
intervalle de confiance.

*Pourquoi binaire* : c'est la seule métrique qui discrimine déjà les cinq bras de SCI-01
(**0 · 1 · 13 · 18 · 4** franchissements sur 20) ; étant binaire, elle n'exige **aucune pondération
posée a priori** — le dogme « rien en dur » interdit précisément d'inventer un poids faute de
données pour le dériver ; et sur cartes figées, le **confondage par niveau** qui a tué le juge
actuel disparaît par construction. Un score composite (succès × efficacité) a été **écarté** : sa
pondération serait arbitraire et il masquerait les désaccords entre métriques au lieu de les
montrer.

*Limite assumée* : binaire = peu sensible aux petits effets. Le nombre d'épisodes devra donc être
suffisant pour la campagne de soustraction (voir §8).

### D3 — Critère de succès du banc : reproduire un verdict déjà connu

Le banc est **accepté** s'il reproduit l'**ordre** établi par mesure directe sur la cohorte SCI-01 :
`K8_NU` en tête, `K16_NU` en bas. Le franchissement en cursus est une **mesure directe**, la seule
nature de résultat que la Règle de Mesure tient pour fiable. Si le banc contredit cet ordre, **le
banc est refusé** et l'écart est enquêté.

Deux précisions non négociables :
- Le test porte sur l'**ordre**, **jamais** sur les valeurs. Le banc impose les mêmes cartes à tous
  les cerveaux : ses chiffres absolus **différeront forcément** des comptes obtenus en cursus.
- Un gain de « variance expliquée » contre le juge actuel a été **écarté** comme critère : la
  « compétence réelle » n'a aucune définition indépendante du banc, ce qui reviendrait à valider un
  instrument contre lui-même. Le A/A seul (δ_A/A = 0) est **nécessaire mais non suffisant** : le
  juge de maîtrise actuel est parfaitement déterministe et pourtant confondu.

### D4 — Architecture : banc neuf + primitives partagées testées

Un banc **neuf** (`banc_final.py`), un module de **primitives partagées et testées**, et
`evaluer_cerveau.py` **archivé**. Réparer l'outil existant en place a été écarté : cela rendrait le
protocole « gelé » indissociable d'un outil d'exploration qu'on veut pouvoir bricoler, et rendrait
les rapports déjà publiés dans `docs/recherche/evals` **non comparables** sans qu'on sache quelle
version les a produits.

---

## 3. Découvertes mesurées pendant le cadrage

Ces six points ont été établis **par lecture de code et par mesure**, avant toute écriture. Ils
sont la raison d'être de plusieurs garde-fous (§6).

### 3.1 Le banc actuel n'est pas reproductible — fait de code

`noyau.py` sélectionne l'action par échantillonnage :
```
9956:  dist = torch.distributions.Categorical(logits=logits_action)
9961:      action = dist.sample()
```
Aucun branchement sur `self.training` : **même en `eval()`, l'action est tirée au sort**.
Or `evaluer_cerveau.py` ne fixe **aucune** graine torch — il ne seede que l'environnement
(`etat.env.reset(seed=…)`, ligne 100). Le RNG d'action n'est donc pas contrôlé.

⚠️ **Ce qui est mesuré et ce qui ne l'est pas** : la non-reproductibilité est un **fait de code**.
Son **ampleur chiffrée** (le δ_A/A du banc) n'est **pas** mesurée à ce stade — c'est précisément ce
que le test d'acceptation (§7c) devra établir. Aucune conclusion sur la taille du bruit n'est tirée
ici.

### 3.2 La graine d'évaluation par défaut collisionne avec l'entraînement

`--seed-base` vaut `0` par défaut. Le pool d'entraînement réel des campagnes est **5…199**
(multiples de 11, lus dans `brains/08092026_sci01_balayage_K/manifeste.json`). D'où le garde-fou
`--graine-eval-base ≥ 1000` (§6).

### 3.3 Le dossier de sortie par défaut n'existe pas

`DOSSIER_EVALS_DEFAUT = "docs/notes/evals"` — ce dossier **n'existe pas** ; le dossier réel est
`docs/recherche/evals`. Chaque évaluation écrit dans un dossier fantôme.

### 3.4 Deux primitives sont dupliquées, non testées, et l'une se contredit

`plus_court_chemin` et `intervalle_wilson` sont définies **deux fois**, avec des corps
fonctionnellement identiques, dans `sonde_inertie_motrice.py` et `sonde_plancher_geometrique.py`.
**Aucun test ne les couvre** (aucun fichier de `tests/` ne les mentionne).

Plus grave : leurs docstrings affirment des conclusions **opposées** de la même prémisse
(« borne INFÉRIEURE du trajet optimal ») :
- `sonde_plancher_geometrique.py` : « elle ne peut que **SURESTIMER** la directivité » → **correct** ;
- `sonde_inertie_motrice.py` : « la directivité mesurée est par construction un peu **PESSIMISTE** »
  → **faux**.

Les deux fichiers calculent `ratios = [t / o for t, o in trajets]`, c'est-à-dire
`trajet / plus_court_chemin`. Puisque le BFS compte des **cases** et ignore le coût des rotations,
il minore le nombre de pas réels : le rapport ne peut donc qu'être **surestimé**. La docstring
d'`sonde_inertie_motrice.py` énonce la direction inverse. Un test de convention est inscrit en §7a
pour rendre cette erreur impossible à réintroduire.

### 3.5 Les cerveaux archivés comportent des doublons divergents

Le dossier de campagne SCI-01 contient, à côté du nom canonique écrit par `run_un.sh`
(`K8_NU_g155.brain`), des fichiers surnuméraires portant une **espace** dans le nom
(`K8_NU_g155 2.brain`), artefacts de synchronisation déjà rencontrés dans ce dépôt (cf. le
`tests/test_cerveau_3d 2.py` supprimé le 12/09).

Un scan d'intégrité (comparaison des membres et CRC de chaque archive `.brain`, format
`torch`-zip à 130 membres) a été lancé. **Relevé au moment de la rédaction** :
`K1_TEMOIN` : 40 `.brain` pour 20 graines · `K2_NU` : 67 · `K4_NU` : 63 · `K8_NU` : 22 ·
`K8_CLIP_e02` : 21 · `K16_NU` : 20.

Les surnuméraires **ne sont pas des copies conformes** : les cas lisibles ont des CRC **et** des
tailles différentes, parfois du simple au quintuple (ex. `K1_TEMOIN_g188 2.brain` : 6 671 073 o en
canonique contre 1 250 657 o en copie). Plusieurs fichiers n'ont **pas pu être lus** après 8
tentatives.

⚠️ **Ce que ce n'est pas** : les échecs de lecture sont des `OSError` **errno 11**
(`Resource deadlock avoided`) — la **même erreur iCloud** déjà rencontrée sur `git` dans ce dépôt.
Ce n'est donc **pas** une preuve de corruption, mais une **indisponibilité de synchronisation**.
Aucun fichier n'est déclaré corrompu ici.

**Portée** : le verdict SCI-01 publié **n'est pas menacé** — il a été calculé par
`depouiller_SCI01.py` à partir des **logs**, pas des `.brain`. En revanche, EVA-01 **rejoue des
cerveaux** : la règle de cohorte (§6) est donc indispensable, et non une précaution théorique.

### 3.6 Deux vérifications qui ont **confirmé** le design (et une erreur corrigée)

- **Le seuil Bonferroni vit dans `depouillement.py`**, pas dans `journal_cursus.py` :
  `seuil_t(n, comparaisons, alpha)` y est défini (ligne 109) et **exporté** dans `__all__`. Le banc
  le **réutilise** — il n'est jamais recodé. (Correction d'une affirmation erronée faite en cours de
  cadrage, où ce seuil avait été attribué à `journal_cursus.py`.)
- **`depouillement.py` ne contient aucun intervalle de confiance** : `intervalle_wilson` extrait des
  deux sondes sera donc la **seule** implémentation du dépôt, pas une troisième.
- **Le forçage de carte est sain** : `_budget_natif_carte(env, defaut=…)` prend **l'environnement en
  argument**, et tous ses appelants passent `etat.env` (lignes 6179, 8384, 8469, 10319). Les
  grandeurs dérivées « par carte » suivent donc la carte **réellement chargée**, jamais
  `etat.niveau_actuel`. La crainte initiale — que le forçage laisse des grandeurs accrochées au
  niveau du cursus — est **levée par la lecture du code**. Un test la figera néanmoins (§7a).

---

## 4. Architecture — les cinq artefacts

Aucun ne modifie `noyau.py`.

| # | Artefact | Rôle |
|---|---|---|
| 1 | `src/naulthene/instruments/primitives_banc.py` *(nouveau)* | Foyer unique des primitives partagées. Pur stdlib (`collections`, `math`), n'importe **jamais** `noyau` (même règle que `bus_sensoriel.py`). |
| 2 | `src/naulthene/instruments/banc_final.py` *(nouveau)* | Le banc gelé. Rejoue des cerveaux sur cartes et graines figées. Ne s'entraîne jamais, ne promeut jamais, n'écrit jamais de `.brain`. |
| 3 | `docs/fonctionnement/PROTOCOLE_BANC_FINAL.md` *(nouveau, normatif)* | Le protocole **gelé et versionné** (§8). |
| 4 | `tests/test_primitives_banc.py` *(nouveau)* | Premiers tests jamais écrits sur ces primitives (§7a). |
| 5 | `src/naulthene/instruments/evaluer_cerveau.py` *(modifié : commentaires seuls)* | Bandeau **archive**, précédent exact `colab.py` / ARC-01. Ses rapports déjà publiés dans `docs/recherche/evals` restent intacts et attribuables. |

### Contenu de `primitives_banc.py` — strictement YAGNI

Uniquement ce qui est **réellement appelé** ; aucune primitive « au cas où ».

- `plus_court_chemin(env) -> int | None` — extrait des deux sondes ; **docstring corrigée**
  (borne inférieure ⇒ directivité **surestimée**, cf. §3.4).
- `intervalle_wilson(k, n, z=1.96) -> tuple[float, float]` — extrait à l'identique.
- `longueur_normalisee(trajet: int, optimal: int | None) -> float | None` — **nomme** la convention
  au lieu de la laisser implicite ; `None` si `optimal` est `None`.
- `taux_avec_ic(k, n) -> dict` — forme unique `{k, n, taux, ic_bas, ic_haut}` pour que tous les
  rapports soient comparables entre eux.

**Consommateurs** : `banc_final.py` **et** les deux sondes, qui **migrent** — ce qui met fin à la
duplication. Le seuil Bonferroni n'est **pas** ici : il est importé de `depouillement.seuil_t`.

---

## 5. Interfaces et flux de données

### Identité d'un épisode = un seul entier `s`

C'est la clé de D1 :
```
etat.env.reset(seed=s)     ← mécanisme existant de evaluer_cerveau.py, préservé tel quel
demarrer_journee(etat)     ← ne passe pas de seed : consomme celui du reset ci-dessus
torch.manual_seed(s)       ← AJOUT EVA-01 : rend l'échantillonnage de l'action reproductible
```
L'épisode devient adressable par un nombre, et **tout résultat devient rejouable à l'identique**.

⚠️ **Piège documenté dans le code existant** (`evaluer_cerveau.py`, lignes 103-117) et à ne pas
réintroduire : `traiter_tick` ne se contente pas de signaler la fin d'épisode — dès que
`etat.fin_episode` bascule, il **enchaîne lui-même** sur un nouvel épisode. La victoire et le nombre
de ticks doivent donc être capturés **au tick même** où `fin_episode` bascule, avant tout tick
suivant. `victoire_aujourdhui` est en outre un drapeau de **journée**, jamais d'épisode.

### CLI gelée

```
PYTHONPATH=src venv/bin/python3 -m naulthene.instruments.banc_final \
  --cohorte brains/08092026_sci01_balayage_K --bras K8_NU K16_NU \
  --cartes 3 4 --episodes 100 --graine-eval-base 10000 \
  --dossier-sortie docs/recherche/evals/banc_final
```

- `--cartes 3 4` = `MiniGrid-SimpleCrossingS9N1-v0` (le mur) + `MiniGrid-LavaGapS5-v0` (le suivant),
  **imposées à tous les cerveaux**. Le forçage réutilise le mécanisme existant
  (`etat.env.close()` puis `etat.env = creer_env(PROGRAMME[index][0], DIM_VISUELLE)`) — il remplace
  l'environnement **sans** toucher `etat.niveau_actuel`. C'est exactement ce qu'exige le point 5 du
  registre : le niveau reste une **mesure de développement**.
- `--graine-eval-base` **refuse** toute valeur `< 1000` (§3.2).

### Flux

```
.brain (lecture seule) ─┐
PROTOCOLE gelé ─────────┼─► banc_final ──► primitives_banc (BFS, Wilson, longueur normalisée)
(cartes, n, pool)       ┘        │
                                 ▼
              JSON par (cerveau, carte)  +  agrégat de cohorte
                                 ▼
       comparaison appariée : graine d'entraînement (appariement)
                            × graine d'éval (équité : identique pour tous)
```

### Hiérarchie du verdict

1. **Primaire** : taux de franchissement + IC Wilson, par carte.
2. **Secondaires déclarées d'avance** : retour, longueur normalisée (médiane + IC).
3. `niveau_actuel` / maîtrise du cursus : reportés en **métadonnée de développement**, **jamais**
   comme métrique de verdict.

**Famille de métriques = 3** (1 primaire + 2 secondaires) ⇒ seuil `seuil_t(n, 3, 0.05)`, conformément
à la convention **MES-04** (famille de 3, α = 0,05 ⇒ `t` = 2,625 à n=20). Le nombre de métriques est
annoncé **avant** tout `t`.

---

## 6. Erreurs et garde-fous

| Situation | Comportement exigé |
|---|---|
| Nom de cerveau ambigu (`X_g11 2.brain`) | **Refus explicite**, fichiers listés. Jamais de choix silencieux. |
| `.brain` illisible | Refus ; le cerveau est **exclu et compté** dans le rapport — jamais silencieusement absent. |
| `--graine-eval-base < 1000` | **Refus** : garantit la disjonction avec le pool d'entraînement (5…199). |
| Cohorte incomplète | **Refus** : réutilise la règle **MES-01** de `depouillement.py`, qui refuse déjà une cohorte incomplète. Pas de réécriture. |
| Épisode non terminé avant `max_ticks` | Compté **échec**, avec un drapeau `tronque: true`. Jamais écarté en silence. |
| Carte sans but (`plus_court_chemin` → `None`) | `longueur_normalisee` → `None` : la métrique est **absente, pas zéro**. Zéro serait un mensonge. |
| Niveau de cursus < carte forcée | **Accepté** : c'est le principe même du banc. Le niveau reste métadonnée. |
| `n = 0` | IC Wilson `(0,0)` ; **aucun taux n'est publié sans IC**. |
| Écriture d'un `.brain` | **Impossible par construction** : `banc_final.py` n'importe jamais la sauvegarde de `PersistanceAnatomique`. |

**Règle de cohorte** : seuls les noms canoniques `<BRAS>_g<GRAINE>.brain` sont éligibles. Les
`<BRAS>_g<GRAINE> N.brain` sont **mis en quarantaine**, et le banc **refuse un nom ambigu** au lieu
de choisir en silence — justifié par la mesure du §3.5.

---

## 7. Tests

### 7a) Primitives — `tests/test_primitives_banc.py`

1. BFS sans obstacle = **exactement** Manhattan (invariant du dépôt, non-régression).
2. Un mur force un détour **strictement** plus long.
3. `lava` est bloquée ; `goal` est traversable.
4. Pas de but ⇒ `None`.
5. **Convention du ratio** : trajet 12 sur optimum 6 ⇒ `2.0`, **jamais** `0.5`. C'est le test qui
   aurait attrapé la docstring inversée du §3.4.
6. Wilson : `n=0` ⇒ `(0,0)` ; `k=n` ⇒ borne haute ≤ 1 ; largeur décroissante avec `n`.
7. **Non-régression de migration** : après migration, les deux sondes doivent rendre, sur un cerveau
   donné, **exactement** les mêmes nombres qu'avant.

### 7b) Acceptation du banc — critère D3

Rejouer la cohorte SCI-01 (cartes 3 et 4, pool d'éval gelé) et **exiger l'ordre connu** :
`K8_NU` en tête, `K16_NU` en bas. Le test porte sur l'**ordre, jamais sur les valeurs**. Si l'ordre
n'est pas reproduit, **le banc est refusé** et l'écart est enquêté. La publication du banc est
conditionnée à ce test.

⚠️ Deux réserves à traiter **avant** de courir ce test : les cerveaux de `K1_TEMOIN` sont
d'intégrité douteuse (§3.5), et `K8_NU` comporte 2 surnuméraires. La cohorte du test sera donc
**explicitement énumérée**, pas dérivée par glob.

### 7c) δ_A/A du banc

Deux évaluations du même cerveau ⇒ écart **mesuré et publié**. Attendu `0`, mais **vérifié, jamais
supposé** : `torch.manual_seed` ne garantit pas le bit-à-bit sur MPS.

### 7d) Trace

Conformément à la Règle de Trace, le test d'acceptation **est une mesure** : il produira un **carnet**
dans `docs/recherche/` **et** un agrégat machine, pas seulement un test vert. De même, le scan
d'intégrité du §3.5 sera consigné avec son relevé complet (aucune mesure non écrite n'a eu lieu).

---

## 8. Protocole gelé — `docs/fonctionnement/PROTOCOLE_BANC_FINAL.md`

### Constantes gelées (v1)

| Constante | Valeur | Justification |
|---|---|---|
| Carte du blocage | index **3** = `MiniGrid-SimpleCrossingS9N1-v0` | Le mur réel du cursus au 12/09/2026. |
| Palier suivant | index **4** = `MiniGrid-LavaGapS5-v0` | Exigé par le point 3 du registre. |
| Pool de graines d'éval | **10000…10099** | Disjoint du pool d'entraînement (5…199). |
| Épisodes par carte | **100** | IC Wilson ≈ ±6 pts à p=0,9. |
| `max_ticks` | **budget natif du monde** (`max_steps`) | Jamais un plafond posé à la main. |
| Famille de métriques | **3** (1 primaire + 2 secondaires) | Convention MES-04. |

### Règles de clôture (les trois du registre)

1. **Protocole standard versionné** → ce document, versionné, référencé par tout rapport du banc.
2. **Banc final obligatoire** dans les nouvelles campagnes majeures.
3. **Séparation claire** entraînement / évaluation : un banc qui réutilise une graine d'entraînement
   est **invalide**.

Règle de version : toute modification du protocole **incrémente sa version** et **invalide la
comparabilité** des rapports antérieurs.

### Interdit explicite — invariant existant respecté

Le banc mesure une compétence **sur cartes imposées**. Il ne prouve **rien** sur le cursus (règle
« un banc forcé ne prouve rien sur le cursus », CLAUDE.md §7) et **ne remplace jamais** un run de
cursus.

---

## 9. Ce que ce chantier ferme

- **EVA-01** : banc reproductible + protocole gelé + primitives testées.
- La **duplication** de `plus_court_chemin` et `intervalle_wilson` (motif MES-01/MES-02 appliqué une
  fois de plus).
- La **docstring inversée** d'`sonde_inertie_motrice.py`.
- Le **dossier fantôme** `docs/notes/evals`.
- L'**ambiguïté de cohorte** (` N.brain`) : désormais refusée **et** consignée comme fait mesuré.

---

## 10. Ce que ce chantier NE fait PAS — à ne pas laisser croire

- **K=8 reste une constante posée**, pas dérivée. EVA-01 ne la dérive pas : c'est la **Phase C** du
  registre.
- La **campagne de soustraction (P3) n'est pas faite**. EVA-01 est l'**instrument**, pas la mesure.
  C'est le chantier suivant — et c'est précisément parce que la soustraction est la prochaine mesure
  que l'instrument passe avant.
- Le banc **ne dit rien du cursus** (§8).
- Le banc **ne prouve pas** être meilleur juge avant que le test d'acceptation D3 n'ait réussi. Tant
  qu'il n'a pas reproduit l'ordre SCI-01, **aucune supériorité n'est revendiquée**.

### Hors périmètre — chantier distinct proposé

L'**audit d'intégrité de `brains/`** (doublons divergents, fichiers non lisibles) est un chantier
**distinct**, à ouvrir au registre comme item propre : EVA-01 n'a besoin que de la **règle de
cohorte**, pas du nettoyage de l'archive (YAGNI). Son relevé complet (§7d) servira de point de départ.

---

## 11. Recherche préalable — pistes déjà écartées, consultées avant d'écrire

Conformément à la consigne « consulter `docs/recherche/` avant toute idée neuve » :

- Le **banc forcé** (`--env-force`) existe et est documenté : il a servi à valider des mécaniques
  (douleur, thermohoméostasie) **avec témoin obligatoire**, et sa limite est écrite (il ne prouve
  rien sur le cursus). EVA-01 en réutilise le **mécanisme de forçage**, pas la conclusion.
- Le **juge de maîtrise** et sa quantification par pas de 5 % sont documentés dans le CHANGELOG et
  les carnets de campagne : EVA-01 ne les corrige pas, il fournit un juge **parallèle** et
  indépendant, à cartes figées.
- Les **6 rapports** déjà publiés dans `docs/recherche/evals` restent attribués à
  `evaluer_cerveau.py` : ils ne sont ni réécrits ni rejoués.

---

## 12. Porte — ce que ce document n'autorise pas

**Aucune ligne de code ne doit être écrite avant l'approbation explicite de ce document par
l'auteur.** Après approbation, le seul skill suivant autorisé est `writing-plans` (plan
d'implémentation multi-étapes). Toute découverte qui élargirait le périmètre impose une
**reclassification** et un nouveau cadrage avant de continuer.
