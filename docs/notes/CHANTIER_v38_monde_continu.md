# Chantier v38 — Le Monde Continu et la Superposition Sensorielle

> **Statut** : plan arrêté, étape 2a en cours.
> **Branche** : `feat/v38-monde-continu`
> **Ouvert le** : 2026-08-12
> **Origine** : exigences utilisateur — *« la continuité permanente »* et *« la superposition
> possible (association des 5 sens en permanence et en tout lieu et temps) »*, avec
> *« de la vie dans le monde et quelqu'un qui guide l'agent (un parent physique) »*.

---

## 1. Pourquoi ce chantier — la correction qui l'a déclenché

L'ablation sensorielle du 12/08 ([recherche_bug_or_not_bug.md](recherche_bug_or_not_bug.md)
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

C'est déjà écrit dans [les_sens_combinatoire.md](les_sens_combinatoire.md) §7.6. Aucune
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
([les_sens_combinatoire.md](les_sens_combinatoire.md) §9). Tant que c'est le cas, **aucune
association vue↔son ne peut se former**, quel que soit le monde.

Le parent résout la synchronisation **par construction** : il est *dans* le monde, donc ce
qu'il nomme est visible au moment où il le nomme.

**Le cadrage v34 s'applique intégralement**
([CONCEPTION_v34_fatigue_mortalite.md](CONCEPTION_v34_fatigue_mortalite.md) §3) : les quatre
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
