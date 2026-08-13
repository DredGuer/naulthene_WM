# Chantier v38 — Le Monde Continu et la Superposition Sensorielle

> **Statut** : plan arrêté, étape 2a en cours.
> **Branche** : `feat/v38-monde-continu`
> **Ouvert le** : 2026-08-12
> **Origine** : exigences utilisateur — *« la continuité permanente »* et *« la superposition
> possible (association des 5 sens en permanence et en tout lieu et temps) »*, avec
> *« de la vie dans le monde et quelqu'un qui guide l'agent (un parent physique) »*.

---

## 1. Pourquoi ce chantier — la correction qui l'a déclenché

L'ablation sensorielle du 12/08 ([recherche_bug_or_not_bug.md](../recherche/recherche_bug_or_not_bug.md)
§H15) a montré que **couper l'odorat et le goût ne change rien** (2,33 victoires contre 2,67
pour le témoin, signes incohérents). J'en avais tiré une règle :

> ~~« Un sens n'est utile que s'il apporte une information qu'aucun autre canal ne donne. »~~

**Cette règle est fausse**, et l'utilisateur l'a corrigée :

> *« Un humain, parce qu'il voit, n'a pas besoin de sentir ! Le sens de l'odorat permet de
> faire des prévisualisations par rapport à la vue : tu vois et tu sens une pomme → plus
> tard tu cherches de la nourriture, tu peux anticiper où est la pomme par son odeur. »*

La formulation juste est l'inverse :

> **Un sens redondant à l'instant T devient prédictif à T+n. La co-occurrence d'aujourd'hui
> est le rappel de demain.**

La redondance n'est pas un défaut du canal : **c'est le mécanisme même de l'association**.
Un sens qui double la vue au moment de la perception est précisément celui qui pourra la
remplacer plus tard, quand la vue manquera.

### La chaîne d'associations décrite par l'utilisateur

```
vue + odorat   → localiser sans voir        (la pomme derrière le mur)
vue + goût     → juger sans goûter          (« elle a l'air bonne »)
odorat + goût  → juger sans voir            ← la chaîne de survie
vue + toucher  → imaginer les yeux fermés
ouïe + tout    → le liant universel + la spatialisation binaurale
```

Le goût est **doublement redondant** (vue *et* odorat) — c'est ce qui en fait le
**confirmateur de dernier recours** : il valide au contact, quand il est trop tard pour
fuir. L'ouïe est le **liant universel** : « j'entends une voiture que je ne vois pas » est
le cas d'école du rappel croisé.

### Pourquoi l'ablation n'a rien vu

Ce n'est pas que les sens soient inutiles. C'est que **le monde n'a pas de T+n**.

Avec un `reset()` toutes les ~120 ticks, l'agent n'a jamais le temps de revenir vers une
source qu'il a sentie. La redondance ne se transforme jamais en prédiction. **Le sens est
inutile parce que le monde est plat, pas parce que le canal est mauvais.**

### ⚠️ Une erreur de diagnostic à corriger dans les documents antérieurs

J'ai écrit à plusieurs reprises que « l'agent voit déjà ce qu'il sent, donc l'odorat est
redondant ». **C'est faux, et vérifié dans le code :**

```
agent_view_size   = 7      → cône 7×7 agent-centré
see_through_walls = False  → occlusion réelle par les murs
cases visibles    ≈ 49 sur 256 en 16×16   (mesuré, 12 à 49 selon la position)
```

**MiniGrid a déjà l'occlusion.** Une pomme hors du cône est **sentie sans être vue**. Le
problème n'a jamais été le champ de vision — c'est la discontinuité temporelle.

---

## 2. Ce que MiniGrid permet — vérifié avant d'écrire le plan

| Exigence | Faisable ? | Mécanisme vérifié |
|---|---|---|
| **Continuité permanente** | ✅ | `max_steps` illimité : **3000 ticks sans une seule terminaison** |
| **Superposition des 5 sens** | ✅ | `grid.set()` / `grid.get()` fonctionnent **à chaud**, en cours de partie |
| **De la vie dans le monde** | ✅ | objets créables/supprimables dynamiquement ; `agent_pos` assignable |
| **Parent physique** | ✅ | une entité mobile dans la grille, déplacée tick par tick |
| **Occlusion** | ✅ | **déjà présente** (7×7, `see_through_walls=False`) |

**Aucun fork de MiniGrid n'est nécessaire.**

### La limite structurelle, posée d'avance

**4 types d'objets × 6 couleurs, une seule apparence par objet.** Une « pomme » aura
*toujours* exactement les mêmes pixels.

> On pourra **valider que le liage fonctionne**. On ne pourra **jamais prouver que c'est un
> concept** plutôt qu'une table de correspondance apparence→nom.

C'est déjà écrit dans [les_sens_combinatoire.md](../ameliorations/les_sens_combinatoire.md) §7.6. Aucune
quantité de code ne contourne cette limite — elle appartient à l'environnement. Elle est
posée ici pour qu'elle ne soit pas redécouverte dans trois semaines comme une surprise.

---

## 3. La hiérarchie physiologique — l'ordre n'est pas négociable

> *« L'humain parle parce qu'il s'est redressé. Donc il faut déjà créer l'intelligence
> réflexe (se déplacer, voir, entendre, etc.) et C2 lui permettra vraiment de faire émerger
> l'intelligence comme l'humain. »*

**C1 d'abord, C2 par-dessus.** C2 ne fait pas émerger l'intelligence *à la place* de C1 : il
émerge **sur** un C1 qui fonctionne déjà.

Cela relit un résultat qu'on n'avait pas su interpréter — le banc d'ablation mesure que
**couper C2 double le taux de succès** (1,7 % → 22,5 % sur `Empty-8x8`). Rangé jusqu'ici en
« C2 est peut-être nuisible ». La lecture de l'utilisateur est meilleure :

> **C2 n'est pas nuisible, il est prématuré.** On demande au néo-cortex de délibérer alors
> que le tronc cérébral ne sait pas encore marcher.

Conséquence pour ce chantier : **on ne touche pas à C2.** On répare les conditions
d'exercice de C1 (un monde continu, des sens qui portent un signal), et on vérifie
seulement, à la fin, si le rapport C1/C2 bouge de lui-même.

---

## 4. Le plan par étapes

Chaque étape suit le même protocole : **implémenter → cerveau témoin → commit sur la
branche**. L'analyse comparative se fait à la fin, sur les quatre cerveaux.

### Protocole commun à toutes les étapes

- **3 graines appariées** (11, 22, 33) — jamais moins (règle du 12/08 : la variance atteint
  ×7 entre deux exécutions du même protocole).
- **600 jours** par run, cohérent avec la campagne d'ablation pour rester comparable.
- **Le témoin de l'étape N−1 est le point de comparaison de l'étape N.** Chaque étape ajoute
  **une seule** chose.
- Toute nouvelle mécanique est **instrumentée dans le même commit** (règle v29.1 :
  compteur remis à zéro dans `_reinitialiser_buffers_journee`, accumulé dans `traiter_tick`,
  agrégé dans `executer_nuit` — ligne console **et** clé `log_wandb`, conditionnelle).

---

### Étape 2a — LA CONTINUITÉ *(le socle)*

**Ce qui change** : suppression du `reset()` de fin d'épisode (`noyau.py:5221`). Le monde
persiste, l'agent aussi. Le Goal atteint est **repositionné ailleurs** au lieu de terminer.

**Ce qui NE change pas** : les sens, le cursus, C1/C2, la mémoire. Une seule chose bouge.

**Pourquoi c'est le socle** : sans T+n, aucune association ne peut se former. Toutes les
étapes suivantes en dépendent.

**Questions auxquelles cette étape doit répondre :**

| # | Question | Métrique |
|---|---|---|
| 2a.1 | L'agent revient-il vers une source sentie il y a N ticks ? | `Continu_Retour_Source` |
| 2a.2 | Le taux d'approche olfactive décolle-t-il de 0,55 ? | `Sens_Odorat_Taux_Approche` |
| 2a.3 | La mémoire spatiale devient-elle utile (corrélation rappel↔victoire) ? | `Memoire_Taux_Rappel_Reussi` |
| 2a.4 | Sans `reset()`, l'agent reste-t-il coincé dans un coin ? | `Continu_Cases_Distinctes_Jour` |

**⚠️ Risque principal, à surveiller** : la promotion du cursus repose sur des *épisodes*
(`_enregistrer_episode_niveau`, `historique_episodes_niveau`). Sans fin d'épisode, **plus
aucune promotion n'est possible** — il faudra définir ce qu'est un « épisode » dans un monde
continu (proposition : chaque Goal atteint compte comme une réussite, chaque N ticks sans
Goal comme un échec).

**Ce qui invaliderait l'étape** : l'agent tourne en rond dans une zone réduite sans jamais
explorer (la téléportation du `reset()` jouait un rôle d'exploration forcée qu'on n'avait
jamais mesuré).

---

### Étape 2b — LA PERMANENCE DES 5 SENS

**Ce qui change** : nourriture et eau semées **en continu** pour que l'odorat et le goût
cessent de se taire. Mesure actuelle : le goût n'existe que sur **~4 % des ticks**
(14,7 ticks/jour sur 400).

**Pourquoi** : une association ne peut pas se former sur un canal muet 96 % du temps.
« Superposition des 5 sens **en permanence et en tout lieu** » est littéralement cette étape.

| Canal | Présence actuelle mesurée | Cible |
|---|---|---|
| Vue | 100 % | 100 % |
| Toucher | 42-58 % | ≥ 80 % |
| Odorat | 91,7 % (**0 % au Doctorat**) | ≥ 90 % partout |
| Goût | **~4 %** | ≥ 30 % |
| Ouïe | **jamais avec la vue** | traité en 2c |

**Questions :**

| # | Question | Métrique |
|---|---|---|
| 2b.1 | Les 5 canaux co-occurrent-ils enfin ? | `Cooc_N_Canaux` (distribution) |
| 2b.2 | Le goût devient-il un signal exploitable ? | `Sens_Gout_Ticks_Actifs` |
| 2b.3 | Couper l'odorat fait-il **enfin** une différence ? | ablation à refaire en fin de chantier |

**⚠️ Risque** : un monde saturé de ressources supprime la rareté, donc l'enjeu. Le déficit
métabolique est aujourd'hui à **100 % des ticks en zone critique** — passer à 0 % supprimerait
toute pression. La densité doit être **mesurée puis calibrée**, jamais posée.

---

### Étape 2c — LE PARENT PHYSIQUE

**Ce qui change** : une entité mobile dans la grille qui **montre** (se déplace vers une
ressource devant l'agent), **nourrit** (dépose une ressource quand les jauges sont basses),
et **nomme** (émet le son associé à l'objet qu'il montre, **au tick où il le montre**).

**Pourquoi c'est la pièce manquante** : `Cooc_Vue_Ouie = 0` aujourd'hui — le professeur parle
*ou* l'agent regarde, **jamais les deux sur le même tick**
([les_sens_combinatoire.md](../ameliorations/les_sens_combinatoire.md) §9). Tant que c'est le cas, **aucune
association vue↔son ne peut se former**, quel que soit le monde.

Le parent résout la synchronisation **par construction** : il est *dans* le monde, donc ce
qu'il nomme est visible au moment où il le nomme.

**Le cadrage v34 s'applique intégralement**
([CONCEPTION_v34_fatigue_mortalite.md](../ameliorations/CONCEPTION_v34_fatigue_mortalite.md) §3) : les quatre
gestes sont **montrer, nourrir, cajoler, protéger**, et *« montrer »* est le geste principal,
pas un appoint. Le sevrage doit être **mérité, jamais daté** — dérivé de `empreinte_enfance`,
qui est déjà une mesure continue de maturité.

**Questions :**

| # | Question | Métrique |
|---|---|---|
| 2c.1 | La co-occurrence vue↔ouïe existe-t-elle enfin ? | `Cooc_Vue_Ouie` (0 aujourd'hui) |
| 2c.2 | L'agent imite-t-il le parent ? | `Parent_Imitation_Ratio` |
| 2c.3 | L'autonomie décolle-t-elle de 0,0 % ? | `Calibrage_Autonomie_Jauges` |

**⚠️ Risque** : un parent trop présent devient une béquille permanente. Le sevrage dérivé de
la maturité est **obligatoire**, pas optionnel.

---

### Étape 2d — LE LIAGE

**Ce qui change** : un terme de perte qui **rapproche** les modalités co-occurrentes et
**éloigne** celles qui ne co-occurrent pas.

**Ne se fait qu'après 2c** : sans co-occurrence réelle, une perte de liage n'a rien à mordre.
C'est exactement l'erreur de la v33 (concevoir sur une prémisse non mesurée).

**⚠️ Mode d'échec silencieux** : sans paires négatives, la solution triviale est
l'**effondrement** — toutes les représentations au même point, perte nulle, plus rien de
distingué. La courbe descend magnifiquement pendant que la représentation meurt.
Instrumenter la **variance des embeddings avant** d'activer la perte, jamais après.

**La preuve attendue** : test de **rappel croisé** — présenter une modalité seule et mesurer
si l'autre se réactive. Montrer la pomme sans le son → l'embedding auditif s'approche-t-il de
« pomme » ? Si oui, liage. Sinon, simple co-activation.

---

## 5. Invariants à ne pas casser *(rappel `CLAUDE.md`)*

- **L'Exo-Sens n'est jamais amputé** : `num_actions` reste à 8, `ACTION_DEMANDER` masquée à
  `-inf` en permanence. 4 `.brain` du dépôt sont à 8 actions.
- **Le `vecteur_bio` est append-only** : toute nouvelle dimension va **en queue**, jamais au
  milieu — sinon tous les acquis des `.brain` existants se décalent silencieusement.
- **Les neutres ne sont pas zéro** : clinotaxie → `0.5`, rappel marquant → `[0.5, 0.0]`. Un
  zéro signifierait « éloignement maximal » et « pire souvenir possible ».
- **Greffe par recopie, jamais par exclusion** (`persistance.py`).
- **Aucun seuil de déclenchement dans le chemin de décision** — refusé en v28, v29, v30.
- **Rien n'est expliqué en dur** : le cerveau ne sait pas ce qu'est une pomme. Aucune table
  `objet → valeur`. La valence est **apprise**.
- **On ne touche pas à C2** (§3) : il est prématuré, pas cassé.

---

## 6. Journal du chantier

| Date | Étape | Résultat |
|---|---|---|
| 2026-08-12 | Ouverture, vérification de faisabilité | Continuité, écriture dynamique, parent : **tous faisables**. Occlusion **déjà présente** (correction d'une erreur de diagnostic) |
| 2026-08-12 | 2a — piège trouvé au smoke test | Continuité naïve ⇒ tâche triviale (3 états absorbants). Corrigé par le réarmement de tâche |
| 2026-08-13 | 2a — 3 premières graines | **69 victoires sur g22** (record projet : 22). Mais 1 et 3 sur les autres ⇒ relance sur 3 graines de plus |
| | 2b — permanence des sens | ⏳ |
| | 2c — parent physique | ⏳ |
| | 2d — liage | ⏳ |

---

## 7. Résultats de l'étape 2a

### 7.1 Première salve (graines 11, 22, 33)

| | g11 | g22 | g33 | Moyenne |
|---|---|---|---|---|
| **Continu** | 1 vict. / niv. 1 | **69 / niv. 5** | 3 / niv. 3 | **24,3** |
| **Témoin** | 3 / niv. 3 | 1 / niv. 1 | 2 / niv. 2 | **2,0** |

Écarts appariés : **−2, +68, +1**. Un seul run porte tout l'effet.

⚠️ **Ne pas conclure « ×12 » sur cette base.** C'est exactement la forme du « ×4,5 » annoncé
puis réfuté le 12/08. La moyenne est portée par un point unique.

### 7.2 Mais la graine 22 n'est pas du bruit

L'analyse détaillée montre un comportement **qualitativement nouveau**, qu'aucun run du
projet n'avait produit :

```
promotions : jours 11, 48, 65, 103, 239        → cursus complet en 239 jours
victoires  : niv.1 ×1, niv.2 ×1, niv.3 ×1, niv.4 ×1, niv.5 ×65
```

**65 des 69 victoires sont sur `DoorKey-16x16` — la carte la plus dure — de façon soutenue
du jour 239 au jour 600.** Intervalles entre victoires en fin de run : `[5, 41, 1, 1, 5, 10,
1, 1]` — l'agent gagne parfois deux jours d'affilée.

Ce n'est pas une série chanceuse sur un niveau facile : c'est une **maîtrise entretenue de
la carte la plus difficile**, sur 361 jours. Le record antérieur du projet était de 22
victoires en 1300 jours, toutes sur des niveaux faciles.

**Lecture honnête** : la continuité **rend possible** quelque chose qui ne l'était pas, mais
ne le **déclenche pas de façon fiable**. C'est un plafond qui se lève, pas un plancher qui
monte.

### 7.3 Une métrique cassée, corrigée

`Continu_Cases_Distinctes_Jour` donnait une **médiane de 2 dans les deux conditions** —
métrique morte, incapable de rien départager.

Cause : l'échantillonnage portait sur les 400 ticks de la journée, alors que **les 200 de
l'après-midi sont vocaux** (`_perception_du_tick`, ère « alternance »). L'agent n'est alors
pas dans la grille et `agent_pos` reste figée.

Corrigé : l'échantillonnage est conditionné à `mode == "minigrid"`. La question 2a.4
(« l'agent reste-t-il coincé ? ») reste **sans réponse** sur la première salve.

### 7.4 Verdict de 2a — 6 graines appariées

| Graine | Continu | Témoin | Écart |
|---|---|---|---|
| 11 | 1 vict. / niv. 1 | 3 / niv. 3 | −2 |
| **22** | **69 / niv. 5** | 1 / niv. 1 | **+68** |
| 33 | 3 / niv. 3 | 2 / niv. 2 | +1 |
| 44 | 4 / niv. 4 | 1 / niv. 1 | +3 |
| 55 | 3 / niv. 3 | 0 / niv. 0 | +3 |
| 66 | 2 / niv. 2 | 2 / niv. 2 | 0 |

**4 gagne / 1 perd / 1 nul**, test des signes **p ≈ 0,375** — non significatif au sens strict.

Le chiffre pertinent n'est **pas** la moyenne (13,7 contre 1,5, entièrement portée par g22)
mais la **médiane des paliers : 3,0 contre 1,5**. En retirant l'outlier, l'effet subsiste
(2,6 paliers contre 1,6).

**Lecture** : la continuité lève un plafond, elle ne monte pas un plancher. Elle rend
accessible un régime d'apprentissage qui ne l'était pas, sans le déclencher de façon fiable.

---

## 8. Résultats de l'étape 2b — la permanence des sens

Densité 3 sources/20 cases utiles (soit 29 food + 29 water sur `16x16`, contre 2+2 avant).

### 8.1 Les deux comparaisons

| Comparaison | Paliers médians | Écarts appariés | p |
|---|---|---|---|
| **2b vs 2a** *(apport de la densité)* | 3,0 vs 3,0 | +3, −1, −1, −2, −2, +2 | **1,000** |
| **2b vs origine** *(la pile entière)* | **3,0 vs 1,5** | **+1, +3, 0, +1, +1, +2** | **0,062** |
| 2a vs origine *(rappel)* | 3,0 vs 1,5 | −2, +4, +1, +3, +3, 0 | 0,375 |

### 8.2 ❌ La densité seule n'apporte rien

2 positifs sur 6, p = 1,000. Les canaux sont pourtant **bien remplis** — odorat actif
**100 %** des ticks contre 91,7 % avant, goût présent sur plusieurs runs.

C'est cohérent avec l'ablation du 12/08 : **donner plus d'odeur à un agent qui ne s'en sert
pas ne change rien.** Remplir un canal ne suffit pas à le rendre utile — il faut que le
monde rende son usage *nécessaire*, ce qu'aucune densité ne fait à elle seule.

### 8.3 ✅ Mais la pile progresse — le signal le plus régulier de l'investigation

`2b vs origine` : **5 positifs sur 5, aucun négatif, p = 0,062**.

Aucune graine ne régresse — ce qui n'était vrai **ni pour 2a seul, ni pour aucun levier
testé le 12/08** (tous avaient au moins une graine en recul).

### 8.4 L'échange que je n'avais pas anticipé

| | 2a seul | 2b (pile) |
|---|---|---|
| Victoires moyennes | **13,7** | 2,8 |
| Écarts appariés | −2, +4, +1, +3, +3, 0 | +1, +3, 0, +1, +1, +2 |
| Graines en recul | 1 | **0** |

On **perd le cas exceptionnel** (g22 et ses 69 victoires) mais **tout le monde monte**. La
densité ne fait pas gagner plus : elle rend le gain **fiable**.

⚠️ À vérifier plutôt qu'à habiller : 6 graines, et p = 0,062 **n'est pas** p < 0,05.

### 8.5 Le garde-fou a tenu

`Calibrage_Ticks_Critiques_Ratio = 0,50` sur les 6 runs — la rareté survit. Rappel :
**1,00** = famine permanente (l'état de tous les runs antérieurs), **0,00** aurait signifié
un monde sans enjeu, donc un test invalide. La densité choisie est dans la plage utile.

---

## 9. Étape 2c — le parent physique

### 9.1 La remarque qui cadre l'étape *(utilisateur)*

> *« L'ouïe est peut-être le plus difficile à exploiter, par sa nature dans MiniGrid où il y
> a tout à créer comme son. »*

C'est exact, et ça distingue 2c des étapes précédentes. La vue, le toucher, l'odorat et le
goût **dérivent d'un état de la grille** (une case occupée, un contact, une distance
topologique). **L'ouïe ne dérive de rien** : MiniGrid est un monde muet. Il n'y a pas de son
à capter, il y a un son à *fabriquer*.

### 9.2 Ce qui existe déjà, vérifié

Bonne nouvelle : la machinerie audio est là, et elle n'a rien de spécifique à la voix
humaine.

| Brique | État |
|---|---|
| `SynthetiseurFormants` | ✅ synthèse source-filtre pure numpy, vecteur 8 dims → onde |
| `extraire_mfcc` | ✅ onde → **130 dims**, exactement l'entrée qu'attend `porte_auditive` |
| `porte_auditive` | ✅ couche existante, déjà branchée sur le bus latent |

**Un « nom d'objet » est donc simplement un vecteur de 8 paramètres formantiques.** Vérifié :
quatre noms synthétiques (clé, porte, but, ressource) produisent des MFCC dont les distances
deux à deux valent 2,59 à 5,66 — **distinguables**, donc apprenables.

Aucune brique nouvelle n'est nécessaire : le parent nomme en synthétisant.

### 9.3 Pourquoi c'est la vraie pièce manquante

`Cooc_Vue_Ouie = 0` aujourd'hui. Le professeur parle **ou** l'agent regarde, jamais les deux
au même tick ([les_sens_combinatoire.md](../ameliorations/les_sens_combinatoire.md) §9). Tant que c'est le
cas, **aucune association vue↔son ne peut se former**, quel que soit le monde.

Le parent résout la synchronisation **par construction** : il est *dans* la grille, donc ce
qu'il nomme est visible au moment où il le nomme.

### 9.4 Les gestes retenus

Repris du cadrage v34 §3.2
([CONCEPTION_v34_fatigue_mortalite.md](../ameliorations/CONCEPTION_v34_fatigue_mortalite.md)), où *« montrer »*
est explicitement le geste principal, pas un appoint :

| Geste | Implémentation |
|---|---|
| **Montrer** | le parent se déplace vers l'objet saillant le plus proche de l'agent |
| **Nommer** | il émet le MFCC du type d'objet qu'il montre, **au tick où il le montre** |
| **Nourrir** | il dépose une ressource quand les jauges de l'agent sont basses |
| **Se retirer** | sa fréquence d'intervention décroît avec `empreinte_enfance` |

⚠️ **Le sevrage est mérité, jamais daté** (v34 §3.3). `empreinte_enfance` est déjà une
mesure continue de maturité (1,0 à la naissance → 0,25 mesuré) : elle sert de curseur, aucun
compteur de jours n'est introduit.

⚠️ **Rien n'est expliqué en dur** : le son associé à un type d'objet est **arbitraire et
opaque**. Le cerveau ne reçoit jamais « ceci est une clé » — il reçoit un MFCC qui
co-occurre avec une forme visuelle. L'association est à apprendre, jamais déclarée.

### 9.5 ❌ Résultat — le parent BLOQUE l'apprentissage

| Graine | 2c parent | 2b pile | Origine |
|---|---|---|---|
| 11 | 1 (1v) | 4 (4v) | 3 (3v) |
| 22 | 1 (1v) | 4 (4v) | 1 (1v) |
| 33 | 1 (1v) | 2 (2v) | 2 (2v) |
| 44 | 1 (1v) | 2 (2v) | 1 (1v) |
| 55 | 1 (1v) | 1 (1v) | 0 (0v) |
| 66 | 1 (1v) | 4 (4v) | 2 (2v) |
| **Paliers médians** | **1,0** | **3,0** | 1,5 |

`2c vs 2b` : **−3, −3, −1, −1, 0, −3 — 0 positif sur 5**, p = 1,000.

**Les six graines se figent au palier 1, exactement.** Cette uniformité n'est pas du bruit :
c'est un mécanisme. Le parent fait *pire que l'absence de parent*, et même pire que le monde
d'origine.

### 9.6 Le mécanisme — l'agent désapprend à chercher

| | 2b (sans parent) | 2c (avec parent) |
|---|---|---|
| Repères mnésiques finaux | **74** en moyenne | **12** |
| Approche olfactive moyenne | **0,306** | **0,128** |

Trajectoire de la mémoire spatiale (graine 11) :

```
jour   1 :  5 repères
jour  61 :  7 repères
jour 121 :  1 repère    ← effondrement
jour 481 :  9 repères   (2b en avait 74)
```

**Le parent nourrit trop bien.** Il dépose une ressource dès que les jauges baissent : l'agent
n'a plus besoin de chercher, donc plus besoin de sentir (approche olfactive divisée par
2,4) ni de mémoriser où sont les choses (repères divisés par 6).

### 9.7 ⚠️ L'erreur de méthode — j'ai cité l'avertissement sans le mesurer

Le cadrage v34 §3.2 contient exactement ce risque, et je l'ai **recopié en écrivant
l'étape** :

> *« Nourrir sans montrer masque l'incompétence : les jauges remontent, l'agent ne sait
> toujours pas chercher, et le sevrage le ramène au point de départ. C'est la différence
> entre donner un poisson et pêcher devant lui. »*

J'ai codé le poisson. Citer un avertissement dans une docstring ne le mesure pas — c'est la
même faute que « instrumenter avant de rendre adaptatif », appliquée à un risque connu
d'avance.

### 9.8 ✅ Ce que 2c acquiert malgré tout

`Cooc_Vue_Ouie` passe de **0** (valeur sur *tous* les runs du projet) à **~0,23**. La
synchronisation vue↔son fonctionne, et elle est le préalable non négociable de 2d.

Le sevrage mérité fonctionne aussi : `force` décroît de 0,35 à 0,23 avec la maturation, sans
aucun compteur de jours.

### 9.9 🔬 2c-fix — montrer sans nourrir

Le parent n'est pas à jeter, il est **mal réglé**. Le geste que v34 désigne comme principal
est **montrer**, pas nourrir. La correction isole donc le premier en supprimant le second
(`--sans-nourrir`).

Si les paliers remontent au niveau de 2b **et** que `Cooc_Vue_Ouie` reste à ~0,23, alors le
parent apporte l'association sans coûter l'autonomie — et 2d devient possible.

### 9.10 Résultat de 2c-fix — la correction aide, sans suffire

| Condition | g11 | g22 | g33 | g44 | g55 | g66 | Médiane |
|---|---|---|---|---|---|---|---|
| origine | 3 | 1 | 2 | 1 | 0 | 2 | 1,5 |
| 2b pile | 4 | 4 | 2 | 2 | 1 | 4 | **3,0** |
| 2c parent nourricier | 1 | 1 | 1 | 1 | 1 | 1 | 1,0 |
| **2c-fix montrer seul** | 2 | 2 | 2 | 1 | 2 | 2 | **2,0** |

| Comparaison | Écarts appariés | p |
|---|---|---|
| 2c-fix vs origine | −1, +1, 0, 0, +2, 0 | 1,000 |
| **2c-fix vs 2b** *(apport du parent)* | **−2, −2, 0, −1, +1, −2** | **1,000** |

Retirer la nourriture **aide** (paliers 1,0 → 2,0 ; repères 13 → 26 ; odorat 0,127 → 0,201)
mais **ne restaure pas le niveau de 2b**. Verdict : même réduit au seul geste « montrer »,
**le parent coûte plus qu'il ne rapporte**.

---

## 10. Le fil conducteur — ce que trois jours de mesures dessinent

| Intervention | Nature | Effet sur les paliers |
|---|---|---|
| **Continuité** (2a) | *rend possible* | **+1,5** |
| **Densité** (2b) | *facilite* | 0 |
| **Parent nourricier** (2c) | *fait à la place* | **−2,0** |
| **Parent montreur** (2c-fix) | *fait à la place, en partie* | **−1,0** |

> **Tout ce qui facilite la tâche de l'agent le fait régresser. Tout ce qui la rend possible
> sans la faciliter le fait progresser.**

C'est le prolongement direct de l'intuition de l'utilisateur — *« un cerveau qui revoit en
boucle les mêmes choses se meurt de bêtise »* — auquel les mesures ajoutent son symétrique :
**un cerveau à qui on épargne l'effort désapprend aussi**.

### ⚠️ Les gains ne se sont jamais additionnés

| Pile | Gain vs origine |
|---|---|
| 2a | +1,5 |
| 2a + 2b | +1,5 *(pas +3)* |
| 2a + 2b + 2c | −0,5 |

Même constat qu'avec H11+H09 le 12/08. Ces briques ne sont pas des additifs indépendants :
la continuité **crée une possibilité**, et les briques suivantes occupent l'espace qu'elle a
ouvert — ou le remplissent d'assistance.

**Nuance qui compte** : 2b n'a pas augmenté la moyenne, il a **supprimé les régressions**
(5/5 positifs contre 4/5 pour 2a). C'est un gain réel, invisible si l'on ne regarde que la
moyenne.

---

## 11. Étape 2c-bis — le monde sonore *(sans assistant)*

### 11.1 Pourquoi cette étape s'intercale

2c a produit la co-occurrence vue↔ouïe (0 → 0,24) **mais au prix de 1 à 2 paliers**.
Conséquence méthodologique : **2d n'est pas interprétable sur cette pile**. Un résultat nul
ne permettrait pas de distinguer « le liage n'apporte rien » de « le parent a annulé l'apport
du liage » — deux effets de signe opposé mesurés par un seul chiffre.

### 11.2 Le principe

Le son ne vient plus d'un assistant mais **du monde lui-même** : un objet proche émet son
timbre. Personne ne montre, personne ne nourrit, personne ne décide à la place de l'agent.

C'est l'application directe du fil conducteur du §10 : un objet qui sonne **rend possible**
l'association sans rien **faciliter**. L'agent doit toujours chercher, sentir, mémoriser et
atteindre le but seul. Le son devient une **propriété du monde**, comme l'odeur — qui n'a
jamais rien fait à sa place.

### 11.3 Le piège, rencontré une troisième fois

Sans contrainte de portée, le son est émis à **100 % des ticks** (mesuré : 400 sonores /
0 silencieux) — une porte est presque toujours dans le champ. **Un signal permanent est un
bruit de fond : il ne peut rien prédire puisqu'il est toujours là.**

C'est le même piège qu'en 2c (`PLAFOND_PAROLE`) et, avant lui, que la continuité naïve
(états absorbants). Trois formes, une seule cause : **une variable saturée cesse de porter de
l'information.**

`PORTEE_SONORE = 2` est le pendant auditif de l'atténuation olfactive. Vérifié sur 300 ticks
réels : **58 % sonores / 42 % silencieux** — le silence redevient informatif.

### 11.4 Critère de réussite

| Métrique | Cible |
|---|---|
| `Cooc_Vue_Ouie` | ~0,2-0,3 (le niveau de 2c) |
| Paliers médians | **3,0** (le niveau de 2b), pas 2,0 |

Si les deux tiennent, la co-occurrence est obtenue **sans son coût**, et 2d devient
mesurable.

### 11.5 ❌ Résultat de 2c-bis — le canal saturé, quatrième fois

`120 200 ticks sonores / 0 silencieux`. La portée ne mordait pas, pour une raison que je
n'avais pas anticipée : **`Ball` était dans le vocabulaire sonore, et 2b en sème des
dizaines** (29 par carte en 16×16). Il y avait donc toujours une ressource à portée.

**Mes deux propres étapes se contredisaient.** 2b remplit le monde de ressources, 2c-bis fait
sonner les ressources.

Paliers médians **2,0** contre 3,0 pour 2b : un canal saturé ne coûte pas rien — il
**encombre**. Ces runs ne testent donc pas la co-occurrence ; ils mesurent « la pile + un
bruit de fond ».

---

## 12. Étape 2c-ter — la parcimonie, la variance et le vrai silence

### 12.1 Les trois remarques de l'utilisateur qui cadrent l'étape

> *« Il y a autant de variations, de possibilités et d'états pour le dire. Chaque variation
> nourrit les précédentes. Je pense que c'est ce qui permet d'appréhender un nouveau son qui
> ressemble. »*

> *« Le cerveau est fait pour être stimulé, mais finit par perdre de l'information s'il l'est
> trop, surtout dans ses débuts. Trop de son, rien ne passe ; pas assez, rien ne s'établit. »*

> *« Le silence n'est pas 0, le silence est quand il y a presque plus rien à établir. »*

### 12.2 ⚠️ La troisième remarque corrige un défaut RÉEL du noyau

Ce n'est pas seulement un défaut de mon banc d'essai. Dans `noyau.py:548-552` :

```python
if obs_auditive is not None:
    bus_latent = stimulus_visuel + stimulus_auditif
else:
    bus_latent = stimulus_visuel          # le terme DISPARAÎT
```

**`obs_auditive=None` ne produit pas un silence : il fait disparaître le terme de la somme.**
La norme du bus change, donc l'échelle d'activation de tout l'aval (`hippocampe`,
`analyseur`, `tete_motrice`). Le cerveau ne perçoit pas le calme — **il perd le canal**, sans
qu'aucun signal ne l'indique.

C'est exactement le défaut annoncé dans
[les_sens_combinatoire.md](../ameliorations/les_sens_combinatoire.md) §4.3 (« absent » et « nul » sont
indistinguables), jamais corrigé depuis.

Ici, le silence devient un son de **très faible amplitude**, donc perçu : distance mesurée au
timbre plein **3,71**, non nulle.

> **C'est un acquis indépendant de tous ces runs, et il mérite d'être porté dans `src/`.**

### 12.3 La variance des timbres — ce qui rend la généralisation possible

Chaque émission varie autour de son prototype (`VARIANCE_TIMBRE = 0.04`) :

| Mesure | Valeur |
|---|---|
| Variance **intra**-type (20 prises) | 2,909 |
| Distance **inter**-type | 6,201 |
| **Ratio** | **2,1×** |

Les types restent distinguables **malgré** la variance — condition pour qu'il y ait quelque
chose à *généraliser* plutôt qu'une table à mémoriser. Sans cela, l'agent ne peut construire
qu'une correspondance exacte, indiscernable d'un concept (limite posée en
[les_sens_combinatoire.md](../ameliorations/les_sens_combinatoire.md) §7.6 pour la vision — que j'avais
reproduite dans le canal auditif **alors que rien ne m'y obligeait** : le son, contrairement
aux pixels, je le fabrique).

### 12.4 La portée, calibrée par mesure

Une portée fixe donnait **0 %** de son sur les grandes cartes. Balayage 4 diviseurs ×
4 tailles, 400 ticks, à densité 2b réelle :

| diviseur | 5×5 | 8×8 | 12×12 | 16×16 | |
|---|---|---|---|---|---|
| /3 | 33 % | 8 % | **0 %** | 3 % | trop rare |
| /2 | 33 % | 4 % | 3 % | 18 % | trop rare |
| **/1.5** | **34 %** | **33 %** | **22 %** | **10 %** | ✅ équilibré |
| /1 | 36 % | 50 % | 40 % | 48 % | retour au bruit de fond |

Même erreur d'échelle que la patience (A3) et la densité (2b) : **une constante calibrée sur
la petite carte ne transpose pas**.

### 12.5 Résultats — le meilleur essai sonore, mais non concluant

| Condition | g11 | g22 | g33 | g44 | g55 | g66 | Médiane | Victoires |
|---|---|---|---|---|---|---|---|---|
| origine | 3 | 1 | 2 | 1 | 0 | 2 | 1,5 | 9 |
| 2a | 1 | 5 | 3 | 4 | 3 | 2 | 3,0 | **82** |
| **2b** | 4 | 4 | 2 | 2 | 1 | 4 | **3,0** | 17 |
| 2c | 1 | 1 | 1 | 1 | 1 | 1 | 1,0 | 6 |
| 2c-fix | 2 | 2 | 2 | 1 | 2 | 2 | 2,0 | 11 |
| **2c-ter** | **5** | **5** | 1 | 3 | 2 | 1 | 2,5 | **37** |

| Comparaison | Écarts appariés | p |
|---|---|---|
| 2c-ter vs origine | +2, +4, −1, +2, +2, −1 | 0,688 |
| 2c-ter vs 2b | +1, +1, −1, +1, +1, −3 | 0,688 |

**Deux graines atteignent le palier 5** (cursus complet), dont une avec **25 victoires**. Le
canal auditif **cesse de coûter des paliers** — c'est l'acquis. Mais il n'améliore pas 2b de
façon démontrable : 4 montent, 2 chutent, p = 0,688.

### 12.6 ⚠️ Une anomalie non expliquée

La graine 22 finit à **`cooc = 0,00`** tout en atteignant le palier 5 avec 5 victoires. Un run
**sans aucune co-occurrence sonore** réussit aussi bien que celui à 0,67.

Cela affaiblit l'idée que le son explique la progression. **Aucune explication à ce stade**, et
je n'en invente pas.

---

## 13. Bilan du chantier v38 — ce qui tient, ce qui ne tient pas

### 13.1 Le seul résultat propre reste 2b

| Condition | p (vs origine) | Régressions |
|---|---|---|
| 2a | 0,375 | 1 graine |
| **2b** | **0,062** | **aucune** |
| 2c | — | 5 graines |
| 2c-fix | 1,000 | 3 graines |
| 2c-ter | 0,688 | 2 graines |

**Aucune brique post-2b n'a démontré son apport.** Avec une variance qui va de 1 à 25
victoires sur une même condition, il faudrait 15 à 20 graines pour trancher.

### 13.2 Le fil conducteur, confirmé quatre fois

> **Ce qui REND POSSIBLE fait progresser · ce qui FACILITE ne change rien · ce qui FAIT À LA
> PLACE fait régresser.**

### 13.3 La saturation, rencontrée quatre fois sous quatre formes

| # | Forme | Symptôme | Correctif |
|---|---|---|---|
| 1 | états absorbants (2a) | Portage 100 %, souvenirs figés | réarmement de tâche |
| 2 | parole permanente (2c) | `Cooc = 1,000` | `PLAFOND_PAROLE` |
| 3 | portée trop large (2c-bis) | 0 tick silencieux | portée + vocabulaire réduit |
| 4 | portée trop étroite (2c-ter v1) | 0 % de son sur 8×8 | portée ∝ carte |

**Une seule cause** : *une variable saturée — dans un sens comme dans l'autre — cesse de
porter de l'information.* C'est la leçon technique la plus réutilisable du chantier.

---

## 14. Étape 2d — le liage multimodal : ÉCHEC

### 14.1 La base choisie, et pourquoi

2d est empilé sur **2b** (la seule condition qui tient, p = 0,062), **pas** sur la pile
complète. Empiler sur 2c-ter — dont l'apport n'est pas démontré — aurait rendu un résultat
nul ininterprétable : « le liage n'apporte rien » et « la brique du dessous l'a annulé » se
confondent en un seul chiffre.

Le **son** de 2c-ter est conservé (seul moyen d'obtenir la co-occurrence) ; c'est le
**parent** qui est écarté.

### 14.2 Le mécanisme

InfoNCE symétrique sur les sorties de `porte_visuelle` et `porte_auditive` :

- **positif** : `(vision_t, audio_t)` — même tick, donc même objet
- **négatifs** : `(vision_t, audio_t')` avec `t' ≠ t` — in-batch, jamais de perte purement
  attractive
- **exclusion** : les ticks de quasi-silence ne sont jamais appariés — rapprocher une forme
  visuelle du silence apprendrait au silence à être prédictif, l'inverse du but

### 14.3 Résultats

| Condition | g11 | g22 | g33 | g44 | g55 | g66 | Médiane | Victoires |
|---|---|---|---|---|---|---|---|---|
| **2b** | 4 | 4 | 2 | 2 | 1 | 4 | **3,0** | 17 |
| **2d liage** | 3 | 1 | 2 | 1 | 4 | 1 | **1,5** | 12 |

| Comparaison | Écarts appariés | p |
|---|---|---|
| 2d vs 2b *(apport du liage)* | −1, −3, 0, −1, **+3**, −3 | **1,000** |
| 2d vs origine | 0, 0, 0, 0, +4, −1 | 1,000 |

**1 positif sur 5.** Le liage ne fonctionne pas, et il coûte 1,5 palier médian par rapport à
2b.

### 14.4 Le diagnostic : la perte MONTE

| | Début (j.1-4) | Fin (j.600) |
|---|---|---|
| Perte de liage | 4,3 | **4,9 à 5,3** |

**La perte augmente au lieu de descendre : le liage n'apprend rien.** Ce n'est pas un
effondrement (le garde-fou a bien fonctionné — variance vision 0,002 à 0,153, audio 0,31 à
0,75, jamais nulle), c'est une **absence pure d'apprentissage**.

Trois explications possibles, aucune tranchée :

1. **Un pas de gradient par jour est trop peu.** La perte est appliquée une fois en fin de
   journée sur le lot accumulé, alors que l'Acteur-Critique et le JEPA en reçoivent des
   centaines. Le liage est noyé.
2. **Il n'y a rien à lier.** Le timbre dépend du *type* d'objet, mais la vision de MiniGrid
   rend un objet identique au pixel près : les deux canaux portent la même information sans
   redondance exploitable — le cas exact du §7.6 de `les_sens_combinatoire.md`.
3. **La cible est mal posée.** L'InfoNCE demande d'apparier un *tick* à un *tick*, alors que
   le liage visé est entre un *type* et un *timbre*. Deux ticks montrant la même clé sont
   comptés comme des négatifs l'un de l'autre — ce qui est faux.

**La 3 est la plus probable et c'est une faute de conception de ma part** : mes négatifs
in-batch contiennent des paires qui devraient être positives.

### 14.5 Ce qui a bien fonctionné malgré l'échec

- **Le garde-fou anti-effondrement**, instrumenté *avant* activation comme prévu : la
  variance ne s'est jamais effondrée, donc l'échec est lisible au lieu d'être masqué par une
  courbe qui descend.
- **La suppression du `except` silencieux** : la première version appelait `optimiseur` au
  lieu de `optimizer` (`noyau.py:533`) à l'intérieur d'un `try/except` nu. L'exception aurait
  été avalée, le liage n'aurait **jamais appris**, et le run aurait produit un « effet nul »
  parfaitement crédible. **Un banc d'essai qui masque ses propres pannes mesure du vide.**

---

## 15. Verdict du chantier v38

| Étape | Paliers médians | p vs origine | Verdict |
|---|---|---|---|
| origine | 1,5 | — | référence |
| 2a continuité | 3,0 | 0,375 | 🟡 prometteur, non significatif |
| **2b + densité** | **3,0** | **0,062** | ✅ **le seul qui tient** |
| 2c parent | 1,0 | — | ❌ nuisible |
| 2c-fix montrer | 2,0 | 1,000 | ❌ |
| 2c-ter son | 2,5 | 0,688 | 🟡 cesse de nuire |
| 2d liage | 1,5 | 1,000 | ❌ |

**Une seule brique sur six a démontré quelque chose.** Le chantier a produit plus de
connaissances négatives que positives — ce qui reste une avancée, à condition de ne pas
présenter le reste comme un succès.

> Voir [ETAT_DU_PROJET_aout_2026.md](../recherche/ETAT_DU_PROJET_aout_2026.md) pour la synthèse générale,
> les forces et faiblesses du projet, et les priorités qui en découlent.
