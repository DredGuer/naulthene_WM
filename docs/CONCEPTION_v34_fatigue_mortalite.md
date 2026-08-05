# v34 — La Fatigue, la Mort et le Soin Parental — cadrage

> **Statut : cadrage, aucune ligne de code écrite.** Rien de ce document n'existe dans
> `noyau.py` ni dans `colab.py`. Il pose le problème mesuré, propose un mécanisme, et
> liste les options écartées avec leurs raisons.
>
> Origine : diagnostic du 2026-08-05 (banc d'ablation + sonde de gradient + sonde de
> récompense). Décision utilisateur explicite : **remplacer la pénalité de stagnation par
> une conséquence biologique**, et **accompagner cette dureté d'un soin parental** qui
> s'estompe à mesure que l'agent se muscle.

---

## 1. Le diagnostic qui motive cette version

Trois instruments, trois mesures convergentes. Aucune n'est une hypothèse.

### 1.1 L'agent n'est pas cassé — il optimise correctement

| Instrument | Mesure | Conclusion |
|---|---|---|
| Sonde de gradient | `tete_motrice.grad` = 0,05 → 0,16 | l'apprentissage **fonctionne** |
| Sonde de gradient | 400 ticks / 400 reçoivent une récompense | le signal **arrive** |
| Banc d'ablation | JEPA à 0,0014 · odorat à 100 % (si ressources) | la perception **fonctionne** |

L'agent apprend parfaitement. Il apprend simplement **la bonne réponse à une mauvaise
question**.

### 1.2 L'économie est structurellement perdante

Sonde de récompense, 400 ticks, cerveau `REFERENCE_5000j` :

| Terme | Primaire | Doctorat | % du déficit |
|---|---|---|---|
| **`penalite_stagnation`** | **−5,89** | **−7,44** | **68 % → 76 %** |
| `MALUS_DOULEUR` | −2,14 | −2,28 | 25 % |
| `r_bio` (métabolisme) | −0,64 | 0,00 | 7 % |
| `dopamine_curiosite` | +0,76 | +0,15 | — |
| `micro_recompense_progres` | +0,36 | +0,15 | — |
| **`recompense_env` (victoire)** | **0,00** | **0,00** | **jamais déclenchée** |
| **SOLDE** | **−7,54** | **−9,42** | |

### 1.3 Le chiffre qui règle le débat

```
Coût moyen d'un épisode (215 ticks)  :  −5,23
Récompense d'une victoire            :  +1,00
                                        ──────
Solde en cas de VICTOIRE              :  −4,23
```

**Même en gagnant chaque épisode, l'agent reste largement négatif.** Et 54 ticks de
stagnation suffisent à annuler une victoire entière, alors que la patience est de
215 ticks : il est **mathématiquement impossible** de finir un épisode dans le vert.

Sa politique mesurée — `forward` joué 5,5 % du temps, 53,8 % d'actions stériles, 96 % de
ticks sur place — n'est pas un échec. **C'est la stratégie optimale d'un agent qui ne peut
que perdre en agissant.**

### 1.4 La cause racine : une pénalité exponentielle non bornée

```python
# ThermostatCinetiqueMultimodal.evaluer_tick
penalite_brute += self.penalite_base * (1.5 ** occurrences)
```

`occurrences` = nombre de fois où l'agent est repassé sur cette case dans ses 6 dernières
positions.

| Occurrences | Pénalité / tick |
|---|---|
| 1 | −0,022 |
| 3 | −0,051 |
| **6 (tourne sur place)** | **−0,171** |

Sur une journée de 400 ticks : **−68,3**.

**C'est une boucle auto-renforçante.** L'agent tourne → il est puni → toute action devient
perdante → il apprend à s'exposer le moins possible → il tourne davantage → la pénalité
**explose exponentiellement**. Le mécanisme censé corriger l'immobilité la fabrique.

---

## 2. Le principe : une conséquence, pas un jugement

> *« Il faut plutôt créer une baisse biologique (genre fatigue) et mourir s'il a une baisse
> trop importante. »*

C'est un changement de nature, pas de réglage.

| | Pénalité de stagnation (actuel) | Fatigue biologique (proposé) |
|---|---|---|
| Nature | amende extérieure | **état interne du corps** |
| Perception par l'agent | **aucune** — il la subit sans la voir | **une jauge dans `vecteur_bio`** |
| Divergence | exponentielle, non bornée | bornée par la mort |
| Fin de la boucle | jamais | **la mort clôt l'épisode** |
| Apprenable ? | non — bruit constant | **oui** — « je suis épuisé, je change » |

Trois raisons pour lesquelles c'est supérieur, et elles sont mesurables :

**(a) Ça ferme la boucle.** Aujourd'hui la pénalité diverge sans limite. La mort, elle,
termine l'épisode — le coût est borné par construction.

**(b) Ça rend le signal apprenable.** Une pénalité de −0,171/tick est un bruit uniforme
dans lequel aucune action ne se distingue. Une jauge de fatigue est **visible** : l'agent
peut apprendre une politique conditionnée à son propre épuisement. C'est la différence
entre punir et informer.

**(c) Ça réutilise l'architecture existante.** `satiete`, `hydratation`, `stimulation` et
`calculer_deficit()` existent déjà dans `BiologicalHomeostasisEngine`. La fatigue est le
quatrième membre naturel de cette famille et emprunte un chemin déjà éprouvé.

---

## 3. Le soin parental : la moitié indispensable du mécanisme

> *« Un enfant prend certes un malus de fatigue, mais il a quelqu'un pour le guider au
> début, le cajoler et remonter son énergie et sa dopamine, jusqu'à ce qu'elle soit assez
> musclée pour se débrouiller seul. »*

**Sans cette moitié, la v34 serait pire que l'existant.** Un agent mortel, sans aide, dans
un monde où il n'a jamais gagné, mourrait avant d'avoir appris quoi que ce soit. On
remplacerait une paralysie par une extinction.

### 3.1 Ce qui existe déjà et qu'il faut réutiliser

Le projet a **déjà** les deux pièces, mais séparées et incomplètes :

| Pièce existante | Ce qu'elle fait | Ce qui manque |
|---|---|---|
| `parent_actif` / `_appliquer_feedback_parent_vocal` | feedback social **vocal** (v25.0) | ne touche **ni l'énergie ni les jauges** |
| `empreinte_enfance = BUS_REFERENCE_INITIAL / dim_bus` | **mesure d'âge déjà calculée** (1,0 = nouveau-né → 0,20 mesuré aujourd'hui) | n'est pas branchée sur le soin |
| `JOUR_FIN_MASQUAGE_EXTERNE = 240` | fin du masquage de la récompense externe | seuil **fixe en jours**, pas dérivé de la maturité |

`empreinte_enfance` est la clé : **le projet dispose déjà d'une mesure continue de
maturité**, et elle décroît naturellement quand le cerveau grandit. C'est exactement le
sevrage progressif décrit, et il n'y a rien à inventer.

### 3.2 Les trois gestes du parent

| Geste | Effet | Se retire quand |
|---|---|---|
| **Nourrir** | remonte les jauges quand elles passent sous un seuil critique | l'agent sait trouver ses ressources seul |
| **Cajoler** | remonte la dopamine sur un effort réel, pas seulement sur un succès | l'agent produit sa propre dopamine par ses victoires |
| **Protéger** | atténue ou empêche la mort | l'agent survit seul assez longtemps |

### 3.3 Le sevrage doit être MÉRITÉ, pas daté

C'est le point de conception le plus important de cette section.

Un sevrage sur compteur de jours (`si jour > 240`) serait exactement le chiffre arbitraire
que le projet bannit — et pire, il retirerait l'aide à un agent qui n'est pas prêt.

**Le sevrage doit dériver de la compétence mesurée**, par exemple : la capacité de l'agent
à maintenir ses propres jauges au-dessus du seuil critique sans intervention, mesurée sur
une fenêtre glissante. Un agent qui se nourrit seul n'a plus besoin qu'on le nourrisse —
c'est la définition même de l'autonomie.

> **La force du soin doit être une VARIABLE dérivée de la maturité, jamais une constante
> datée.** `empreinte_enfance` en est déjà le support naturel.

---

## 4. Constantes-bornes vs variables-dérivées

> *« Il faut créer des variables (pas de constantes), les constantes sont plutôt des
> bornes. »*

C'est la doctrine du projet appliquée à un nouveau domaine (cf. le rêve adaptatif :
`pourcentage_reve` émerge de plasticité × richesse, jamais d'un batch fixe).

| | Rôle | Exemples pour la v34 |
|---|---|---|
| **CONSTANTE** | une **borne**, jamais une valeur de fonctionnement | `FATIGUE_MAX`, `FATIGUE_MIN`, `SEUIL_MORT`, plafond du soin |
| **VARIABLE** | la valeur réelle, **dérivée de l'état** | taux d'épuisement ← effort réel · force du soin ← maturité · seuil de mort effectif ← âge |

**Ce qui est en défaut aujourd'hui** : `PENALITE_STAGNATION_BASE = 0,015` est une constante
*de fonctionnement*. C'est précisément ce que cette règle interdit.

**Ce qui est déjà bien fait et sert de modèle** : `calculer_effort_metabolique` dérive
l'effort de l'action réelle (`COUT_CORPOREL_PAR_ACTION`, 80 %) **et** de l'intensité de
planification (20 %). Le taux d'épuisement doit s'y brancher, pas inventer sa propre échelle.

⚠️ **Piège identifié** : `COUT_CORPOREL_PAR_ACTION` punit déjà `forward` (0,5) **plus** que
tourner (0,2). Si la fatigue se branche naïvement dessus, elle **renforcerait** le biais
anti-mouvement déjà mesuré (5,5 % de `forward`). Le coût doit pénaliser l'**effort inutile**,
pas le déplacement. À traiter explicitement, c'est le principal risque technique de la v34.

---

## 5. Le plan par étapes

Ordre imposé par la doctrine : **instrumenter d'abord, calibrer ensuite** (v30.1), et ne
jamais concevoir sur une prémisse non mesurée (leçon v33).

### Étape 0 — Mesurer avant d'écrire la moindre mécanique

**La seule étape à faire tant que rien n'est tranché.** Sans elle, on choisirait le taux
d'épuisement au doigt mouillé — et on remplacerait un chiffre arbitraire par un autre.

| Métrique | Ce qu'elle détermine |
|---|---|
| `Effort_Distribution` | l'effort réel par tick (existe, jamais loggé) — l'échelle du taux de fatigue |
| `Survie_Ticks_Simules` | combien de ticks l'agent tiendrait à divers taux — calibre `SEUIL_MORT` |
| `Deficit_Au_Seuil` | l'état des 3 jauges quand le déficit devient critique |
| `Autonomie_Jauges` | % de ticks où l'agent maintient ses jauges **seul** — le critère de sevrage |
| `Ressources_Par_Niveau` | nourriture/eau disponibles par niveau — **au Doctorat : zéro** |

> ⚠️ **`Ressources_Par_Niveau` est bloquant.** Les cartes MultiRoom du Doctorat n'ont
> **ni nourriture ni eau** (mesuré : odorat à 0,0 % des ticks, `r_bio` à 0,000). Rendre
> l'agent mortel dans un monde sans nourriture, c'est le condamner à mort — quelle que
> soit sa compétence. **Peupler l'environnement est un préalable, pas une option.**

Validation obligatoire : **empreinte MD5 à graine fixée**, identique avec et sans les
appels de télémétrie (protocole qui a validé la v33).

### ✅ Étape 0 — LIVRÉE le 2026-08-06 — ce qu'elle a mesuré

Télémétrie livrée dans `noyau.py` (14 clés `Calibrage_*` + ligne console dédiée),
**invariance validée par empreinte MD5** : `efb6ff6506e852ed` identique avec et sans les
appels de télémétrie (neutralisation différentielle, protocole v33).

Mesure sur `REFERENCE_5000j`, 2 jours × 400 ticks, les 5 niveaux :

| Niveau | Ressources | **Autonomie** | Ticks critiques | Déficit moy | Déficit max |
|---|---|---|---|---|---|
| Primaire | 8 | **0,0 %** | **100 %** | 2,49 | 2,95 |
| Collège | 8 | **0,0 %** | **100 %** | 2,93 | 3,00 |
| Lycée | 8 | **0,0 %** | **100 %** | 2,94 | 3,00 |
| Université | 10 | **0,0 %** | **100 %** | 2,98 | 3,00 |
| Doctorat | 16 | **0,0 %** | **100 %** | 2,99 | 3,00 |

**Jauges minimales atteintes : satiété 0,00 · hydratation 0,00 · stimulation 0,00** sur
tous les niveaux.

#### Les trois faits qui changent le plan

**1. 🔴 L'agent est DÉJÀ mort — sur les 5 niveaux, 100 % du temps.**

`Autonomie_Jauges = 0,0 %` signifie qu'à **aucun tick** l'agent ne maintient ses trois
jauges au-dessus du seuil critique. Le déficit est à **2,99 sur un maximum théorique de
3,00** : les trois jauges sont vides en permanence.

Conséquence directe : **l'Étape 3 (la mort) est déjà satisfaite par l'état actuel.** Ajouter
un seuil létal tuerait l'agent au premier tick, sur tous les niveaux, quelle que soit sa
compétence. Ce n'est pas une nuance de calibrage : c'est un empêchement absolu.

**2. 🟢 Le blocage §7.4 est LEVÉ — les ressources existent.**

Contrairement à ce que le run de 5000 jours laissait croire (odorat à 0,0 %, `r_bio` à
0,000), les cartes contiennent bien **8 à 16 sources** de nourriture/eau, **y compris au
Doctorat**. `DetecteurRessourcesBiologiques` les génère sur tous les niveaux.

L'odorat à 0 % du run n'était donc pas une absence de ressources — c'était une conséquence
de l'agent qui ne les atteint jamais. **Peupler l'environnement n'est plus un préalable.**

**3. 🟠 Le risque §4 est CONFIRMÉ et chiffré.**

| Mesure | Valeur |
|---|---|
| Effort moyen d'`avancer` | **0,510** |
| Effort moyen de `tourner` | **0,270** |
| Part de ticks à `avancer` | **6,5 %** |

**Avancer coûte 1,9× plus cher que tourner**, et l'agent avance 6,5 % du temps. Le lien est
mécanique. Une fatigue branchée naïvement sur `calculer_effort_metabolique` **renforcerait**
ce biais — c'est le risque critique du §4, désormais mesuré et non plus supposé.

#### Ce que ces mesures imposent au plan

L'ordre des étapes 1→3 devient **inapplicable en l'état**. Avant toute fatigue :

- **Le métabolisme actuel est déjà létal** : `taux_satiete=0,008` et `taux_hydratation=0,005`
  par tick vident les jauges en ~125-200 ticks, sans que l'agent sache se nourrir. Ajouter
  une 4ᵉ jauge d'épuisement à un corps déjà à zéro n'ajouterait aucune information.
- **Le soin parental (Étape 2) devient le point de départ, pas le deuxième temps.** Un
  agent dont les jauges sont vides 100 % du temps est exactement l'enfant qui ne peut pas
  survivre seul. C'est là que le mécanisme doit commencer.
- **Le seuil de mort ne peut pas être un seuil de déficit absolu** — il serait franchi
  immédiatement. Il devra dépendre de la durée passée en zone critique, ou d'une jauge
  d'épuisement distincte qui, elle, part de zéro.

### Étape 1 — La fatigue comme 4ᵉ jauge

En queue du `vecteur_bio` (**contrat append-only**, invariant 2 du Bus Sensoriel), taux
dérivé de `calculer_effort_metabolique`, bornée par `FATIGUE_MIN`/`FATIGUE_MAX`.

À ce stade **la fatigue ne tue pas encore** — elle est seulement perçue et mesurée. On
vérifie qu'elle est apprenable avant de la rendre létale.

### Étape 2 — Le soin parental (AVANT la mort, jamais après)

Les trois gestes du §3.2, avec une force dérivée de `empreinte_enfance`.

**Cet ordre n'est pas négociable** : livrer la mort avant le soin produirait une extinction
immédiate, et on ne saurait pas distinguer « le mécanisme est mauvais » de « il manquait
l'aide ».

### Étape 3 — La mort

L'épisode se termine quand le déficit dépasse le seuil. Le seuil effectif doit être
**adouci par le soin parental** tant que l'agent est jeune (§3.2, « protéger »).

### Étape 4 — Retirer `penalite_stagnation`

**Pas avant** : il faut pouvoir comparer les deux régimes sur le même cerveau, avec le banc
d'ablation. Une lésion `stagnation_coupee` serait le bon instrument.

### Étape 5 — Remesurer, puis décider des points 2 et 3 du diagnostic

Une fois le coût d'épisode réparé, remesurer :
- le **ratio victoire / coût d'épisode** (19 % aujourd'hui)
- le **taux de choc contre les murs** (57 % aujourd'hui)

Et *alors seulement* décider s'il faut y toucher (§6.2, §6.3).

---

## 6. Options écartées, et pourquoi

### 6.1 Plafonner l'exponentielle `1,5^occurrences` — ÉCARTÉE

C'était **ma proposition initiale**, remplacée par celle de l'utilisateur.

Plafonner à `1,5²` diviserait le coût par 5. Mais ça reste un **pansement** : une pénalité
arbitraire posée à côté de la biologie, que l'agent subit sans la percevoir. Ça traite le
symptôme (le montant) sans traiter la cause (une punition non perçue et non apprenable).

**Conservée en trappe de secours** : si la fatigue s'avère impraticable, borner
l'exponentielle reste la correction minimale à appliquer.

### 6.2 Multiplier la récompense de victoire par 10 — ÉCARTÉE POUR L'INSTANT

Le ratio à 19 % n'est **pas causé par une victoire trop faible** : il est causé par un coût
trop lourd (−5,23 par épisode). Réparer le coût répare le ratio mécaniquement.

Multiplier par 10 serait un chiffre arbitraire **qui masquerait le vrai problème**.

**Décision** : ne pas y toucher, et **remesurer après l'Étape 4**. Si la victoire reste
sous-dimensionnée, on le saura par la mesure, pas par pronostic.

### 6.3 Rééquilibrer `MALUS_DOULEUR` maintenant — REPORTÉE

L'agent se cogne 57 % des ticks **parce qu'il n'a pas de politique**. Calibrer maintenant,
c'est calibrer sur un comportement pathologique — la valeur choisie serait fausse dès que
l'agent se mettrait à décider.

**Décision** : après l'Étape 4, sur un taux de choc remesuré.

### 6.4 Un sevrage sur compteur de jours — ÉCARTÉE

`si jour > 240` est exactement le chiffre arbitraire que le projet bannit, et il retirerait
l'aide à un agent qui n'est pas prêt. Le sevrage doit être **mérité** (§3.3).

### 6.5 Une mort à coût persistant — QUESTION OUVERTE

Non tranchée, et elle appartient à l'utilisateur (§7.1).

---

## 7. Décisions ouvertes — à trancher par l'utilisateur

### 7.1 La mort a-t-elle un coût qui persiste ?

| Option | Conséquence |
|---|---|
| **A — reset propre** | l'épisode redémarre, jauges réinitialisées. Simple, mais la mort n'est qu'un `done` de plus — peu de poids pédagogique |
| **B — coût persistant** | la mort laisse une trace (dopamine effondrée, mémoire marquée). Plus proche du vivant, mais risque de spirale : mourir rend plus faible, donc on remeurt |

⚠️ L'option B touche au **réservoir dopaminergique**, dont `CLAUDE.md` protège les
invariants. À ne pas décider dans le code.

### 7.2 La fatigue entre-t-elle dans `calculer_deficit()` ?

Y entrer la ferait compter dans `r_bio` — donc dans la récompense — et créerait un
**double comptage** avec l'effort déjà facturé. À examiner avant, pas après.

### 7.3 Le soin parental touche-t-il la dopamine directement ?

« Cajoler » suggère oui. Mais la dopamine a ses propres invariants (clip
`[DOPAMINE_MIN, DOPAMINE_MAX]` après chaque mise à jour). Un canal de soin qui l'injecte
doit respecter ce clip — et ne pas devenir une source de dopamine gratuite qui rendrait
l'apprentissage inutile.

### 7.4 Faut-il peupler MultiRoom en ressources ?

**Techniquement bloquant pour l'Étape 3** (§5, Étape 0). Sans nourriture, un agent mortel
au Doctorat meurt quoi qu'il fasse.

Deux voies : peupler les cartes (`DetecteurRessourcesBiologiques` sait déjà le faire), ou
rendre la mort inopérante sur les niveaux sans ressources — la seconde étant une exception
codée en dur, donc contraire à la doctrine.

---

## 8. Risques identifiés

| Risque | Gravité | Mitigation |
|---|---|---|
| **Mort trop précoce** — l'agent n'atteint jamais le But, n'apprend rien | 🔴 critique | Étape 2 (soin) **avant** Étape 3 (mort) ; seuil dérivé de l'Étape 0 |
| **La fatigue renforce le biais anti-mouvement** (§4) | 🔴 critique | pénaliser l'effort **inutile**, pas le déplacement |
| **Double comptage** effort ↔ fatigue ↔ `r_bio` | 🟠 | trancher §7.2 avant de coder |
| **Le soin devient une béquille permanente** | 🟠 | sevrage mérité (§3.3), jamais daté |
| **Spirale de mort** (option B du §7.1) | 🟠 | mesurer le taux de mort avant/après |
| **Doctorat sans ressources** | 🔴 bloquant | §7.4, préalable à l'Étape 3 |

---

## 9. Ce que ce document ne prétend pas

- **Aucune ligne de code n'a été écrite.** Tout est au conditionnel.
- **Seule l'Étape 0 est recommandée à ce stade.**
- Les quatre décisions du §7 appartiennent à l'utilisateur ; deux touchent des invariants
  que `CLAUDE.md` protège explicitement (dopamine, `vecteur_bio`).
- Le diagnostic du §1 est **mesuré et reproductible** (banc d'ablation `resultats_complet.json`,
  sondes de gradient et de récompense). Le mécanisme du §2 est une **proposition**.

---

## 10. Références internes

| Sujet | Où |
|---|---|
| Le banc d'ablation, les 13 lésions, la grille de lecture | `LANCEMENT.md` §15 |
| Résultats bruts du diagnostic | `brains/ablations/resultats_complet.json`, `comparaison_700j.json` |
| Homéostasie, jauges, `calculer_deficit`, effort 20/80 | `explications_readme.md` |
| Invariants du `vecteur_bio` (append-only), dopamine, rêve adaptatif | `CLAUDE.md` |
| Leçon « prémisse non mesurée » | `Old_Archive_rmd/CONCEPTION_v33_memoire_emotionnelle.md` |
| Liage multimodal des sens (chantier parallèle) | `les_sens_combinatoire.md` |
