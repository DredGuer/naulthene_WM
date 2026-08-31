# Le Génome — audit des constantes qui font naître un cerveau

**30/08/2026** — photo horodatée, non mise à jour après cette date.

Demande : *« tout ce qui vient à l'encontre du dogme — les constantes du "génome" qui
permettent de créer les cerveaux »*.

Cet audit **prolonge** celui du [18/08/2026](18082026_revue_dogme_avant_publication.md),
il ne le remplace pas. Le précédent auditait le dogme **en général** (161 constantes triées).
Celui-ci pose une question plus étroite et plus dure :

> **Qu'est-ce qui, dans ce dépôt, décide de la forme et des désirs d'un cerveau *avant*
> qu'il ait vécu quoi que ce soit ?**

C'est la définition du génome. Une constante d'apprentissage se défend (« le vécu la
déplacera »). Une constante du génome, non : elle est **là à la naissance et ne bouge
jamais**.

Champ : `noyau.py` (11 818 l.), `bus_sensoriel.py` (966 l.), `persistance.py` (725 l.),
`colab.py` (1 440 l.). **173 constantes numériques littérales** recensées.

---

## Verdict en une phrase

> **Le chemin de décision est propre — la propriété centrale du projet TIENT.** Mais
> **95,61 % de ce que l'agent veut** provient de constantes posées, contre **4,39 %** du
> monde (mesuré, 2 400 ticks, 3 niveaux). Le génome ne façonne pas seulement le *corps* du
> cerveau : il façonne ses **désirs**, et il le fait presque seul.

---

## 0. 🔴 La découverte de cet audit — l'agent n'optimise pas la tâche

Mesuré avec `sonde_recompense` sur un cerveau réel (`A_g11`, campagne AB3 du 26/08),
800 ticks par niveau, trois niveaux dont celui du plafond.

| Niveau | Récompense du **monde** | Total positif | **Part du monde** |
|---|---:|---:|---:|
| N0 `Empty-5x5` | 1,0272 | 15,4523 | **6,65 %** |
| N3 `SimpleCrossingS9N1` *(le plafond)* | **0,0000** | 14,5106 | **0,00 %** |
| N4 `LavaGapS5` | 1,0382 | 17,0661 | **6,08 %** |
| **Ensemble (2 400 ticks)** | **2,0654** | **47,0290** | **4,39 %** |

**Sur le niveau où l'agent plafonne, MiniGrid lui verse exactement `0.0000` sur 800 ticks.**
La totalité de son signal d'apprentissage vient de quatre constantes posées :

| Terme | Somme (N3) | Part du positif | Origine |
|---|---:|---:|---|
| `dopamine_curiosite` | +7,2496 | **50,0 %** | `PLAFOND_ERREUR_DOPAMINE`, `DOPAMINE_*` |
| `sous_objectif_intrinseque` | +3,4457 | 23,7 % | quêtes bio, `SEUIL_CRITIQUE_BIO = 0.35` |
| `r_bio` | +2,9936 | 20,6 % | barème métabolique |
| `micro_recompense_progres` | +0,8217 | 5,7 % | valeur posée |
| `penalite_stagnation` | **−14,0527** | **100 % du négatif** | `PENALITE_STAGNATION_BASE = 0.015` |

> **Ce que cela veut dire.** L'agent ne plafonne pas « malgré » son barème : il **réussit**
> son barème. Il maximise la curiosité (50 % de ses gains) sur un niveau où la tâche ne
> paie rien. Aucune des seize hypothèses réfutées cette semaine n'a examiné **ce que
> l'agent veut** — toutes examinaient comment il apprend.
>
> ⚠️ **Ceci est une mesure directe, pas une explication du plafond.** Le lien
> « barème → plafond » n'est **pas** établi : il exige une comparaison appariée à n ≥ 20.
> Le tableau des suspects reste vide ; cette mesure dit seulement **où personne n'a
> encore regardé**.

### 0.1 🔴 Et l'instrument mentait — `MALUS_DOULEUR` fantôme

En menant cette mesure, `sonde_recompense` affichait un **`MALUS_DOULEUR` de −4,6200 sur
462 ticks (57,8 %)** — alors que la v41.27 a **supprimé** cette constante du chemin.

La sonde ne le **lisait** pas : elle le **reconstruisait**.

```python
if nom == "MALUS_DOULEUR":
    ligne[nom] = (nx.MALUS_DOULEUR if loc.get("mur_touche") else 0.0)   # ← inventé
```

Preuve arithmétique :

| Grandeur | Valeur |
|---|---:|
| Récompense **réelle** (somme des `recompense_interne`) | **+0,4579** |
| Solde **affiché** par la sonde | **−4,1621** |
| Écart | **−4,6200** |
| Fantôme `MALUS_DOULEUR` | **−4,6200** |
| Écart − fantôme | **−0,0001** |

Le terme inventé expliquait **la totalité** de l'écart, et **retournait le signe de la
conclusion** : « 🔴 SOLDE NÉGATIF » là où la récompense réelle est **positive**. Pire, la
douleur v41.27 passe par `calculer_deficit`, donc elle était **déjà comptée dans `r_bio`** :
double comptage d'un coût supprimé.

✅ **Corrigé le 30/08/2026.** Après correctif, `SOLDE = +0,4579`, exactement égal à la
récompense réelle.

> **Leçon de méthode, à ranger à côté de « rien sans témoin » :**
> **un instrument qui RECONSTRUIT une grandeur au lieu de la LIRE survit à la suppression
> de cette grandeur, en silence.** Le code mort est visible ; l'instrument mort ne l'est
> pas — il continue de produire des chiffres plausibles.

---

## 1. Le génome au sens strict — ce qui fixe la FORME

Un cerveau naît par `AGI_Naulthene(dim_visuelle=DIM_VISUELLE, dim_bus=BUS_REFERENCE_INITIAL)`.
Douze couches, dont les dimensions sortent de **onze constantes**.

| Constante | Valeur | Ce qu'elle décide | Dérivable ? |
|---|---:|---|---|
| `BUS_REFERENCE_INITIAL` | **16** | largeur du bus à la naissance → **toutes** les couches | 🔴 **posée** |
| `DIM_VISUELLE` | 147 | 7×7×3, imposé par MiniGrid | ✅ le monde |
| `DIM_VECTEUR_BIO` | 42 | somme de sens (+ socle `16` littéral) | 🟠 mixte |
| `DIM_AUDIO_ENTREE` | 130 | 13 MFCC × 10 frames | 🟠 calibration |
| `DIM_VOCALE` | 8 | formants de sortie | 🟠 physiologie |
| `NUM_ACTIONS_AVEC_C3` | 8 | 7 réelles + 1 **masquée en permanence** | 🟠 gel de compat. |
| `DIM_ROUTAGE_C3` | 5 | `tete_requete` — **morte au runtime** | 🔴 posée |
| `DIM_EXO` | 8 | 8 dims **toujours nulles** (aucun plug) | 🔴 posée |
| `AJOUT_DIM_BASE` | 16 | mutation à plein rendement | ✅ borne assumée |
| `JOURS_ENTRE_MUTATIONS` | 5 | rythme de neurogenèse | 🔴 posée |
| `DIM_BUS_MAX` | 160 | dérivé RAM/cœurs (v41.22) | ✅ **la machine** |

### 1.1 🔴 Le cerveau ne naît PAS à 55 616 paramètres

**Mesuré :**

| `dim_bus` | Paramètres |
|---:|---:|
| 8 | 3 368 |
| **16 (naissance réelle)** | **7 760** |
| 32 | 19 616 |
| **64** | **55 616** |

Les deux README annoncent **« 55 616 paramètres à la naissance »**. C'est la taille d'un
cerveau à `dim_bus = 64` — soit **quatre neurogenèses plus tard**. Un cerveau qui vient de
naître pèse **7 760 paramètres**, soit **7,2× moins**.

Le tableau détaillé des README le trahit : il liste `porte_visuelle (147 → 64)`, donc
`dim_bus = 64`. ⚠️ **Corrigé dans les deux README dans le même commit que ce document.**

C'est exactement le défaut que le projet s'interdit : un chiffre vérifiable en un `grep`,
publié faux. Il **n'avantage** pourtant pas le projet — il le fait paraître 7× plus lourd
qu'il n'est à la naissance.

### 1.2 🟠 33,4 % du cerveau naissant est de l'audio jamais exercé

| Bloc | Params (naissance) | Part |
|---|---:|---:|
| Audio (`porte_auditive` + `tete_vocale` + JEPA audio) | **2 592** | **33,4 %** |
| Mort au runtime (`DIM_EXO` + `tete_requete`) | 208 | 2,7 % |
| **Total naissance** | **7 760** | 100 % |

Un tiers du cerveau à la naissance sert une faculté qu'**aucun niveau MiniGrid n'exerce**.
Ce n'est pas une violation du dogme — c'est un choix assumé (« un cerveau complet en attente
d'un corps »). Mais toute comparaison de taille avec une baseline RL doit le dire.

---

## 2. Le génome au sens fort — ce qui fixe les DÉSIRS

Le plus grave. Ces constantes ne décrivent pas un corps : elles décrivent **ce que
l'agent trouvera agréable ou pénible**, avant toute expérience.

| Constante | Valeur | Part mesurée du signal | Statut |
|---|---:|---|---|
| `PENALITE_STAGNATION_BASE` | **0.015** | **100 % du négatif** (93 % des ticks) | 🔴 posée |
| `PLAFOND_ERREUR_DOPAMINE` | 2.0 | plafonne la curiosité = **50 % du positif** | 🔴 posée |
| `MICRO_RECOMPENSE_CURIOSITE` | 0.04 | prime à la surprise JEPA | 🔴 posée |
| `RECOMPENSE_APPROCHE_BUT` | 0.05 | guidage (béquille) | 🔴 posée |
| `MICRO_RECOMPENSE_VOCALE` | 0.05 | prime vocale | 🔴 posée |
| `SEUIL_CRITIQUE_BIO` | 0.35 | déclenche les quêtes = **23,7 % du positif** | 🔴 seuil posé |
| ~~`MALUS_DOULEUR`~~ | ~~−0.01~~ | ✅ **retirée du chemin en v41.27** | ✅ morte |

✅ **Progrès réel depuis le 18/08** : l'audit précédent comptait **4 récompenses posées**.
`MALUS_DOULEUR` a été retirée du chemin (v41.27) — vérifié, **aucune lecture** dans
`noyau.py`. **Il en reste trois**, plus deux constantes qui pèsent bien plus lourd et que
l'audit du 18/08 n'avait pas classées comme telles : `PENALITE_STAGNATION_BASE` et
`PLAFOND_ERREUR_DOPAMINE`.

> ⚠️ **`MALUS_DOULEUR = -0.01` subsiste comme définition morte** (l. 4901), lue par
> aucun code du noyau — mais elle était encore lue par `sonde_recompense` (§0.1). Une
> constante morte n'est pas inerte tant qu'un instrument la ressuscite.

---

## 3. Ce qui TIENT — et qu'il faut continuer de dire

### 3.1 ✅ Aucun seuil dans le chemin de décision — **vérifié à nouveau**

Inspection de `penser()` : les seuls `if` sont des **drapeaux d'ablation**
(`BRAIN_SPARING_ACTIF`, `DETACH_C2_ASYMETRIQUE`) et le **masquage permanent** de la 8ᵉ
action. Aucun seuil sur une grandeur cognitive. C'est la propriété la plus forte du projet
et elle **tient toujours**, cinq refus documentés à l'appui (v28, v29, v30, v37 ×2).

### 3.2 ✅ Une seule règle de plasticité, une seule classe

`NaultheneLinearSynaptique` gouverne les douze couches. Vérifié : `xavier_uniform_` à la
naissance — une initialisation **standard**, pas un réglage maison.

### 3.3 ✅ Les grandeurs d'apprentissage sont dérivées

`reference_choc_dopamine`, `pourcentage_reve`, `capacite_memoire`, `echelle_myeline`,
`DIM_BUS_MAX`, `patience_de_vie`, `lambda_diffusion` — toutes dérivées du vécu ou de la
machine. C'est le cœur de la thèse et il n'est pas entamé.

### 3.4 ✅ Aucune table « objet → valeur »

Vérifié : la valence reste la moyenne des chocs sur une étiquette **opaque**. C'est ce qui a
permis la mesure embarrassante — mais vraie — que *la lave avait la valence de l'eau*.

---

## 4. Le décompte honnête

| Catégorie | Nombre | Verdict |
|---|---:|---|
| Bornes (`MIN`/`MAX`/plancher/plafond/fraction) | 39 | ✅ conformes |
| Constantes de temps / poids (inertie, demi-vie, γ, κ) | 42 | 🟠 défendables |
| **Valeurs posées nues** | **92** | 🟠 à trier |
| **dont récompenses posées actives** | **3** (+2 non classées) | 🔴 **violation** |
| **dont génome de forme posé** | **4** | 🔴 **violation** |
| Noms du monde dans `noyau.py` | 4 sites | 🔴 inchangé depuis le 18/08 |
| Seuil jamais atteint (`SEUIL_CRISTAL = 0.80`) | 1 | 🟠 vivant, jamais franchi |
| Constante morte encore ressuscitée | 1 | ✅ corrigée ce jour |

---

## 5. Propositions de remplacement

Classées par **ce que la mesure justifie**, pas par intérêt.

### P1 — Corriger « 55 616 à la naissance » ⭐⭐⭐ · 10 min · **fait ce jour**

Remplacer par : **7 760 à la naissance (`dim_bus = 16`), 55 616 à `dim_bus = 64`**.
Un chiffre faux vérifiable en un `grep` coûte plus que ce qu'il rapporte — d'autant qu'ici
il **dessert** le projet.

### P2 — Mesurer le barème avant de toucher au reste ⭐⭐⭐ · 1 j

`95,61 %` du signal vient de constantes posées, et **personne n'a testé ce levier**. Le
protocole existe déjà : trois bras (`--sans-curiosite`, `--sans-stagnation`, témoin),
20 graines, cursus complet, A/A d'abord.

⚠️ Ce n'est **pas** une hypothèse sur le plafond : c'est la zone que seize réfutations
n'ont jamais visitée.

### P3 — Dériver `PENALITE_STAGNATION_BASE` ⭐⭐⭐ · ✅ **LIVRÉ v41.43 — mais REFORMULÉ**

> 🔴 **La proposition ci-dessous était FAUSSE et la mesure l'a corrigée le 30/08 au soir.**
> Le basal facture le **TEMPS** (0,003250/tick), la stagnation la **REDONDANCE SPATIALE**
> (`1.5 ** occurrences`) : **un agent qui avance en ligne droite paie le basal et RIEN en
> stagnation.** Ce n'est **pas** un doublon, et supprimer la pénalité aurait retiré le seul
> signal anti-piétinement du barème.
>
> Le vrai défaut est **l'échelle**, non reliée à ce que vaut une victoire : mesuré sur
> 40 cerveaux, la stagnation efface l'équivalent de **14,4 victoires** quand l'agent en
> obtient 2 ou 3. Livré : `pénalité = GAIN_MINIMAL_VICTOIRE / max_steps`, dérivé du monde.
> Voir [chantier v41.43](../ameliorations_appliquees/CHANTIER_v41.43_hygiene_du_genome.md).

<details><summary>La proposition initiale, conservée parce qu'elle était fausse</summary>


**Aujourd'hui** : `0.015` posé, 100 % du coût, 93 % des ticks.
**Proposition** : la stagnation n'a pas besoin d'être *punie* — elle **coûte déjà**, par le
métabolisme basal (`METABOLISME_BASAL_PART`, mesuré : `0,325` par 100 ticks d'inaction).
Poser la pénalité **en plus** facture deux fois la même chose.

```python
PENALITE_STAGNATION_BASE = depense_basale_par_tick   # ❌ REJETÉ — pas le même objet
```

Précédent invoqué à tort : `MALUS_DOULEUR`. La faute réelle n'était pas le double
comptage, mais l'échelle arbitraire.

</details>

### P4 — Dériver `PLAFOND_ERREUR_DOPAMINE` de l'erreur vécue ⭐⭐⭐ · 3 h

**Aujourd'hui** : `2.0` posé, plafonne la curiosité = **50 % du positif**.
**Proposition** : le cliquet de `reference_choc_dopamine` existe déjà et fonctionne. Le
même patron s'applique — un **niveau** d'erreur JEPA de référence, montée rapide, descente
~50× plus lente. La curiosité devient alors **relative au vécu** : une surprise de 2,0 est
énorme pour un nouveau-né et banale pour un adulte.

C'est l'exemple canonique du projet (« 100 % pour un débutant, 11,4 % pour un expert »)
appliqué au terme qui pèse **la moitié** de ce que l'agent veut.

### P5 — Dériver `BUS_REFERENCE_INITIAL` de l'entrée sensorielle ⭐⭐ · 4 h

**Aujourd'hui** : `16` posé.
**Proposition** : un bus est un **goulot de compression**. Sa largeur naturelle est une
fraction de ce qu'il doit comprimer :

```python
BUS_REFERENCE_INITIAL = 2 ** round(log2((DIM_VISUELLE + DIM_VECTEUR_BIO) / FACTEUR_COMPRESSION))
```

⚠️ **À mesurer avant d'implémenter** (doctrine v30.1 : instrumenter d'abord). `DIM_BUS_MAX`
est déjà dérivé de la machine ; le **plancher** ne l'est pas. Et trois campagnes montrent
que **grossir le bus ne change rien** — donc ce chantier est de cohérence, pas de
performance.

### P6 — Retirer `SEUIL_CRISTAL` ou le rendre relatif ⭐⭐ · ✅ **LIVRÉ v41.44**

> Rendu **relatif** (`echelle_myeline × 3.0`). Mesuré : **0 synapse sur 1 906 360** franchissait le seuil absolu ; après correctif, **3 071** cristallisent sur un cerveau mature. Voir [chantier v41.44](../ameliorations_appliquees/CHANTIER_v41.44_p6_p8_audit_solde.md).

Vivant dans le code (3 usages effectifs), **jamais franchi** : myéline réelle max mesurée
**0,0038** contre un seuil de **0,80**, soit **210× moins**. Même défaut que le `q_ref = 1.0`
corrigé en v37.0. Soit le rendre relatif (quantile de la couche), soit le retirer.

### P7 — Supprimer la définition morte `MALUS_DOULEUR` ⭐⭐ · ✅ **LIVRÉ v41.43**

Plus lue par le noyau, mais elle a **ressuscité dans un instrument** pendant trois
versions. Supprimer la ligne 4901.

### P8 — Déplacer `COULEUR_FOOD` / `COULEUR_WATER` / test `ball` ⭐⭐ · ✅ **LIVRÉ v41.44 (partiel)**

> Les trois sites pointent désormais `bus_sensoriel`. ⚠️ Les tables `MOT_PAR_*` restent (télémétrie vocale : nommer y est la fonction) et **le cœur reste le jardinier du monde** — le nom a quitté le cœur, pas la dépendance.

**Inchangé depuis le 18/08** : `noyau.py` l. 3727-3728, 3781-3784, 3839-3844, 7815. Leur
place est `bus_sensoriel.py`, la frontière corps/monde, où `lava` a déjà droit de cité.
Rendrait **vraie** l'affirmation « le cœur ne nomme rien ».

### P9 — Isoler les vestiges DoorKey ⭐ · 2 h

`SEUIL_PALIER_MODE_LIBRE = 5`, `SUCCES_PAR_SOUS_SEUIL = 2`,
`COEFF_ABNEGATION_SOUS_SEUIL_2 = 1.6`, les 7 paliers de `DetecteurJalonsDoorKey` :
spécifiques à **un** environnement sur quinze.

---

## 6. Ce qu'il faut dire à un chercheur — version 30/08/2026

**❌ Ne pas dire** : « rien n'est en dur », ni « 55 616 paramètres à la naissance ».

**✅ Dire** :

> « L'architecture ne contient **aucun seuil de déclenchement dans le chemin de décision**
> — vérifié, cinq propositions en ce sens ont été refusées explicitement. Les grandeurs
> d'apprentissage sont **dérivées du vécu**. Un cerveau naît à **7 760 paramètres**
> (`dim_bus = 16`) et atteint 55 616 à `dim_bus = 64` par neurogenèse.
>
> Il subsiste **trois récompenses posées** et **deux constantes de barème** qui pèsent
> davantage — et nous avons mesuré que **95,6 % du signal d'apprentissage vient de ces
> constantes, contre 4,4 % du monde**. Sur le niveau où l'agent plafonne, MiniGrid verse
> exactement **0,0000** sur 800 ticks : l'agent optimise un barème, pas une tâche. Nous ne
> savons pas encore si c'est la cause du plafond — c'est la seule zone que seize
> réfutations n'ont pas visitée. »

Cette version résiste à l'audit **parce qu'elle est vraie et qu'on a compté**.

---

## 7. Ce qui a changé depuis le 18/08/2026

| Point | 18/08 | 30/08 |
|---|---|---|
| Récompenses posées actives | 4 | **3** ✅ (`MALUS_DOULEUR` retirée en v41.27) |
| Noms du monde dans `noyau.py` | 7 sites | 4 sites 🟠 (inchangé sur le fond) |
| `SEUIL_CRISTAL` | jamais franchi | **inchangé** 🟠 |
| Part du monde dans le signal | *non mesurée* | **4,39 %** 🔴 **nouveau** |
| Paramètres à la naissance | *non vérifiée* | **7 760**, README faux 🔴 **nouveau** |
| Instrument `sonde_recompense` | supposé fiable | **terme fantôme, corrigé** 🔴 **nouveau** |

---

## 8. Limites de cet audit

À dire avant que quelqu'un d'autre ne le dise :

1. **Les mesures de §0 portent sur UN cerveau** (`A_g11`) et 2 400 ticks. Le motif est
   reproduit sur trois niveaux, mais **n = 1 cerveau** — sous la barre des 20 graines. Ce
   sont des **mesures directes** (§4 de la règle de mesure : fiables *en tant que lecture*),
   pas une comparaison appariée. Elles décrivent, elles n'établissent aucune causalité.
2. **Aucun lien causal barème → plafond n'est démontré.** Le tableau des suspects reste
   **vide**. P2 est une proposition d'expérience, pas un résultat.
3. **Le décompte « 92 valeurs posées nues » est automatique** (motif de nom), donc
   approximatif aux frontières. Les chiffres cités individuellement, eux, sont vérifiés un
   à un.
4. **`colab.py` n'a pas été audité en profondeur** — c'est le script de référence, mais il
   est en retard de plusieurs versions sur `noyau.py`, qui porte les mécaniques vivantes.
