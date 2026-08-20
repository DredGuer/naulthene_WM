# Changelog — Naulthène AGI

Historique des évolutions du projet, commit par commit. Voir [readme.md](../../readme_fr.md) pour la documentation narrative complète et [CLAUDE.md](../../CLAUDE.md) pour les règles de maintenance de ce fichier.

---

## [v41.27-mesure-fix1] - 2026-08-20 — La baseline était fausse ; et on sait POURQUOI l'agent économise

### Deux résultats : une rectification, et la cause du blocage

| Type | Details |
|------|---------|
| **Commit** | `7b8c77c` |
| **Catégorie** | docs (rectification + mesure) |
| **Impact** | **Critique — inverse une conclusion publiée dans les deux README** |
| **Carnet** | [`POURQUOI_20082026_l_agent_economise.md`](../recherche/POURQUOI_20082026_l_agent_economise.md) |

**🔴 RECTIFICATION.** Le CHANGELOG et les deux README affirmaient que l'agent « plafonne
21 points SOUS une politique aléatoire » (54,4 % contre 75,7 %). **C'est faux** : la
baseline tirait parmi **3 actions**, l'agent en a **7**. Ce n'est pas la même tâche.

```
hasard sur 3 actions (baseline fausse) : 75,7 %
hasard sur 7 actions (équitable)       : 39,2 %
Naulthène                              : 54,4 %
```

**L'agent bat le hasard équitable de 15 points.** Troisième erreur de mesure en trois
jours, et la plus grave — elle avait été publiée.

**✅ LA CAUSE DU GASPILLAGE EST TROUVÉE.** Sur `Empty-5x5`, **57,2 % des ticks** partent en
gestes stériles (`poser`/`activer`/`parler` : **100 %** stériles). Pourquoi :

| geste | effort facturé |
|---|---|
| **AVANCER** (le seul qui rapproche du but) | **4,0000** |
| tourner | 1,4545 |
| **STÉRILE** | **1,0909** |

> **Le seul geste utile coûte 3,7× plus cher que ne rien faire.** La punition de l'effort
> est immédiate et à chaque tick ; la récompense du but est rare et lointaine.

**L'agent n'est pas irrationnel : il optimise exactement ce qu'on lui demande.** Le
comportement est une **conséquence** de la fonction de coût, pas un défaut d'apprentissage.

Deux hypothèses concurrentes **écartées** : l'entropie d'exploration (C1 à **0,499**, 4
actions distinctes sur 7 — il a de vraies préférences) et une tête motrice qui n'apprend
pas (maîtrise 13,8 % → 54,4 % sur 10/10 graines).

⚠️ **Ce n'est pas un argument pour re-poser une table de coûts.** Le problème n'est pas que
l'effort soit dérivé — c'est que le **bénéfice ne l'est pas symétriquement** : un geste qui
ne change rien coûte le minimum et rapporte zéro, donc il gagne.

**🗑️ C3 est mort au runtime** (constat vérifié) : aucun plug n'est jamais enregistré,
`ACTION_DEMANDER` est masquée à `-inf` en permanence, l'action 7 apparaît dans **zéro** log
de run. Non supprimé car `DIM_EXO` (8) et `num_actions` (8) sont dans la **forme des
poids** — les retirer casserait tout `.brain` existant. Noté en tête de section dans
`noyau.py` et dans les deux README.

---

## [v41.27-mesure] - 2026-08-20 — L'agent APPREND, mais plafonne sous le hasard

### La baseline aléatoire révèle le vrai blocage — après trois nuits passées ailleurs

| Type | Details |
|------|---------|
| **Commit** | `632ae7f` |
| **Catégorie** | docs (résultat de mesure) |
| **Impact** | **Mesure — réoriente le chantier** |
| **Carnet** | [`NAVIGATION_20082026_le_vrai_blocage.md`](../recherche/NAVIGATION_20082026_le_vrai_blocage.md) |

**L'agent apprend — 10 graines sur 10.** Sur `Empty-5x5` (aucun danger, but à 4 cases),
maîtrise par quart : **13,8 % → 26,7 % → 43,8 % → 54,4 %**, sans plateau. Toutes les
graines progressent, et l'intervalle entre victoires se raccourcit (5,4 j → 1,4 j) : la
politique s'améliore, ce n'est pas de la chance.

**Mais il plafonne 21 points SOUS une politique aléatoire** — 54,4 % contre **75,7 %**
(baseline mesurée sur 2000 épisodes). **3/10 graines** dépassent le hasard, donc la
compétence est atteignable par cette architecture, mais pas atteinte de façon fiable.

⚠️ **Rectification d'une conclusion du 19/08 au soir** : j'avais annoncé « 15× moins bon
que le hasard, 5 % de maîtrise ». C'était lu **au jour 23 d'un run de 300** — un
transitoire pris pour un plateau. Deuxième erreur de la même famille en deux jours.

**Campagne v41.27 (n=20, 3 bras)** — la douleur ne change rien, le coût de la mort si :

| bras | approche du danger | récolte | survie |
|---|---|---|---|
| **A** (douleur + mort coûteuse) | **36,0 %** | 2,67 | 5,89 % [4,8–7,2] |
| **B** (douleur seule) | 62,5 % | 11,56 | 8,98 % [8,5–9,4] |
| **C** (témoin) | 63,0 % | 12,19 | 9,79 % [9,4–10,2] |

```
B vs C (douleur seule)  : approche −0,48 pt  t = −1,51   NON significatif
A vs B (coût de la mort): approche −26,5 pts t = −15,21  SIGNIFICATIF
```

**La douleur informe ; la conséquence enseigne.** Trois versions de douleur (v41.25 brute,
v41.26 graduée, v41.27 unifiée) : **aucune** ne modifie le comportement. ⚠️ L'option (b)
reste inutilisable telle quelle — 275 ticks perdus/jour, récolte ÷4, et la **survie la plus
basse des trois bras** : l'agent évite parce qu'il meurt de faim, pas parce qu'il comprend.

**Conséquence pour la suite** : le blocage n'est ni la lave ni la douleur. C'est que la
politique plafonne sous le hasard sur la tâche la plus simple du cursus. Converge avec
« couper C2 = 0,0 point » et « grossir le cerveau n'apporte rien ».

---

## [v41.27-experimental] - 2026-08-19 — La douleur unique : un seul état, deux signatures

### Il y avait DEUX douleurs sans rapport ; il n'y en a plus qu'une

| Type | Details |
|------|---------|
| **Commit** | `1b0ab5d` |
| **Catégorie** | feat (expérimental) — **refonte** |
| **Impact** | **Fonctionnel — homéostasie / nociception / récompense** |
| **Carnet** | [`DOULEUR_UNIQUE_19082026_refonte.md`](../recherche/DOULEUR_UNIQUE_19082026_refonte.md) |

**Le défaut.** Deux canaux sans rapport : `MALUS_DOULEUR = −0,01` (constante, dans la
récompense) pour le mur, et `chaleur²` (dans le déficit) pour le feu. Deux échelles, deux
traitements — l'empilement que le projet refuse. `MALUS_DOULEUR` était l'une des **4
récompenses en dur** de l'audit du dogme, et celle qui produisait l'inversion *« mourir
coûte moins cher que se cogner »*. **Elle est SUPPRIMÉE.**

**La forme** (formulation utilisateur du 19/08) :

```
douleur(t) = douleur(t−1) × (1 − dégradation(t)) + pic(t)
```

Un **seul** état corporel. Le « type » n'est pas un canal — c'est le couple
**(pic, demi-vie)** fourni par l'organe sensoriel :

| événement | pic | demi-vie |
|---|---|---|
| brûlure | ∝ excès thermique | **60 ticks** — ça s'installe |
| choc mural | ∝ **vitesse d'impact** | **5 ticks** — ça passe |

Les signatures vivent dans `bus_sensoriel.py` ; **`noyau.py` ne reçoit que deux nombres**
et ignore ce qui l'a blessé.

**⚠️ Le temps n'augmente PAS la douleur aiguë — il allonge la RÉCUPÉRATION.**

| exposition | douleur pendant | après 50 ticks de repos |
|---|---|---|
| 1 tick | 0,1973 | **0,0955** |
| 50 ticks | 0,9744 | **0,6925** |

**La chaleur est un état MAINTENU par la source** (correction utilisateur). Une première
version infligeait un pic à chaque tick → douleur **0,898** en régime permanent, pire que
la v41.26. Un corps **évacue** la chaleur et ne se lèse que si l'apport dépasse sa
capacité :

```
apport net = max(0, chaleur − CAPACITE_EVACUATION_THERMIQUE)
```

⚠️ **Évacuer ≠ percevoir** : seuil de perception 0,12, capacité d'évacuation 0,40. Les
confondre faisait brûler l'agent partout où il sentait quelque chose — le défaut de fond
des v41.25 et v41.26. La distance module désormais le **palier d'équilibre** :

| distance | douleur permanente (400 ticks) |
|---|---|
| d≥2 | **0,0000** |
| d=1 (longer) | 0,1664 |
| d=0 (dedans) | **0,8057** |

**Option (b)** — mourir coûte le reste de la journée (`--mort-sans-cout` pour le témoin).
⚠️ Bien plus lourd que prévu : **90 % de la journée perdue**, l'agent ne vit que ~39 ticks
sur 400, et il meurt **à côté** de la lave (chaleur 0,457) faute de temps pour manger.

| Fichier modifié | Changement |
|-----------------|------------|
| `src/naulthene/cerveau/noyau.py` | `encaisser_douleur()`, `douleur_corporelle()` ; état `douleur`/`exposition` ; vitesse d'impact ; `MALUS_DOULEUR` supprimé du chemin ; option (b) + son ablation |
| `src/naulthene/cerveau/bus_sensoriel.py` | `DEMI_VIE_BRULURE` / `DEMI_VIE_CHOC` — les signatures nociceptives |
| `docs/recherche/scripts/banc_douleur_unique.py` | **nouveau** — teste le **régime permanent** (400 ticks), l'erreur qui a fait passer la v41.26 |

**Campagne en cours** : **3 bras × 20 graines × 300 jours**. A (tout) / B (douleur seule) /
C (témoin). Deux changements simultanés seraient confondus — B vs C isole la douleur,
A vs B isole l'option (b). Vérifié : déficits distincts **1,641 / 2,758 / 2,009**.

---

## [v41.26-experimental] - 2026-08-18 — La thermohoméostasie : la douleur devient graduée

### Le défaut : une douleur sans zéro, donc sans lieu de repos

| Type | Details |
|------|---------|
| **Commit** | `a8c49b7` |
| **Catégorie** | feat (expérimental) |
| **Impact** | **Fonctionnel — homéostasie / nociception** |
| **Carnet** | [`THERMOHOMEOSTASIE_18082026_...`](../recherche/THERMOHOMEOSTASIE_18082026_la_douleur_graduee.md) |

**Le défaut mesuré.** `douleur = T²` est continue et **jamais nulle** : sur les cartes du
banc, **100 %** des cases libres portent une chaleur > 0,10 et **77 %** > 0,25. L'agent
n'avait **aucun lieu de repos** — déficit creusé partout, `r_bio` négatif en permanence,
fuite sans fin possible.

**La cause n'était PAS métabolique.** `self.chaleur` ne touche ni l'énergie, ni la satiété,
ni la dépense — vérifié. La chaîne est **comportementale** : douleur permanente → évitement
permanent → **moins de nourriture atteinte** → énergie basse → vigueur au plancher → C2
éteint. Mesuré sur **deux cartes sans rien de commun** :

| ressources récoltées/jour | douleur ON | témoin | écart |
|---|---|---|---|
| `LavaGapS5` | 8,88 | 11,98 | **−26 %** |
| `LavaCrossingS9N1` | 10,24 | 13,73 | **−25 %** |

⚠️ *Rectification* : un diagnostic antérieur de la même nuit concluait « c'est
métabolique ». C'était une corrélation prise pour une cause.

**La gradation (formulation utilisateur).**

```
seuil    = max(FRACTION × habituation, plancher)   ← palier 1, DÉRIVÉ du vécu
instant  = ((T − seuil) / (1 − seuil))³            ← paliers 2/3/4
brûlure  = brûlure × (1 − dissipation) + instant   ← la durée
douleur  = min(1, instant + brûlure)
```

Les quatre paliers **émergent**, aucun n'est codé (banc `banc_gradation_douleur.py`) :

| distance | chaleur | douleur | palier |
|---|---|---|---|
| 0 | 1,0000 | **1,000000** | 4. intense (dégât) |
| 1 | 0,4573 | 0,112629 | 3. douloureux |
| 2 | 0,2091 | 0,002078 | 2. gênant |
| 3 | 0,0956 | **0,000000** | **1. ça va — ZÉRO EXACT** |

**La durée** (distance 1, l'agent reste) : 0,113 → 0,160 → 0,236 → **0,329** en 8 ticks.
Supportable un instant, insupportable si l'on s'attarde. Dissipation : 0,103 après 6 ticks
hors du danger.

**Rien n'est empilé** : l'habituation est le **même cliquet** que
`reference_choc_dopamine` (v37.1), déjà validé. Aucune jauge « adrénaline » ou
« endorphine » ajoutée.

**Deux défauts trouvés par le banc et corrigés avant lancement :**
1. **L'habituation montait trop vite** (cliquet immédiat repris tel quel) : elle
   rattrapait la chaleur en UN tick, et la brûlure **DÉCROISSAIT pendant que l'agent
   restait dans le feu** (0,0956 → 0,0307). L'inverse du palier 3.
2. **Le palier 1 n'avait pas de vrai zéro** : `T³` vaut `0,000084` à distance 4 — un
   epsilon. Un nocicepteur a une intensité minimale d'activation.

| Fichier modifié | Changement |
|-----------------|------------|
| `src/naulthene/cerveau/noyau.py` | `douleur_thermique()`, `_douleur_instantanee()`, `encaisser_chaleur()` ; état `chaleur_habituee` + `brulure` ; reset de la brûlure par épisode ; instrumentation |
| `src/naulthene/cerveau/persistance.py` | `chaleur_habituee` sérialisée (lecture défensive) |
| `docs/recherche/scripts/banc_gradation_douleur.py` | **nouveau** — vérifie les 4 paliers en sortie de moteur |

⚠️ **Limite du banc à connaître avant lecture des résultats.** Sur `LavaGapS5`, **aucune
case n'est à distance ≥ 3 de la lave** (77 % à d=1) : le lieu de repos **n'existe pas
géométriquement**. La gradation divise la douleur moyenne par ~2 (0,16 → 0,087) mais ne
peut pas créer un repos absent de la carte. Cases indolores : **0 %** sur `LavaGapS5`,
**11 %** sur `LavaCrossingS9N1`.

**Campagne en cours** : 20 graines × 2 bras × 300 jours. Critère n°1 = **la récolte
remonte-t-elle ?**

---

## [v41.25-mesure] - 2026-08-18 — La peur s'apprend (20/20), la survie baisse (−3,1 pts)

### Résultat de campagne : mécanisme validé, objectif manqué

| Type | Details |
|------|---------|
| **Commit** | `62210e7` |
| **Catégorie** | docs (résultat de mesure) |
| **Impact** | **Mesure — aucun changement de code** |
| **Carnet** | [`CAMPAGNE_18082026_...`](../recherche/CAMPAGNE_18082026_nociception_20_graines.md) |

**Banc** : `LavaGapS5` forcé, 20 graines × 2 bras × 300 jours, **40/40 runs terminés**.

**✅ Le mécanisme fonctionne — sans ambiguïté.**

| | ON (douleur) | OFF (témoin) |
|---|---|---|
| Valence apprise de `lava` | **−0,7614** | **+0,0615** |
| Graines à valence négative | **20/20** | **0/20** |

`delta = −0,8229` · `t apparié = −1066` (seuil 2,09) · **aucun chevauchement**. C'est la
**première fois du projet** que la lave porte une valence négative — elle valait celle de
l'eau sur tous les cerveaux depuis l'origine. Le comportement suit : **−5,60 points**
d'approche du danger (`t = −5,51`).

**❌ Mais la survie BAISSE.**

| | survie | IC95 Wilson |
|---|---|---|
| ON | **6,71 %** | [6,19 – 7,27] |
| OFF | **8,57 %** | [8,19 – 8,96] |

`delta apparié = −3,10 pts` · `t = −3,36` · 14 graines sur 20 dans ce sens · **les IC ne
se chevauchent pas**.

**Ce que les chiffres disent** : l'agent qui a mal **meurt 2,4× moins** (7 800 vs 18 531)
mais **gagne 2,9× moins** (0,40 vs 1,16 victoire/jour), avec des épisodes 2,4× plus longs.
Il ne se jette plus dans la lave — **il n'arrive plus non plus**. Sur `LavaGapS5` le but
est *derrière* le couloir de lave : fuir le danger, c'est fuir l'objectif. La douleur
enseigne l'évitement, pas le franchissement prudent.

🔴 **Cette lecture a été RÉFUTÉE le soir même.** Vérification : le chemin sûr existe sur
**10/10 graines** et le détour coûte **+0,0 case** dans `LavaGap` **comme** dans
`LavaCrossing` — éviter la lave ne coûte rien géométriquement. La cause réelle est
**métabolique** : 86 % des ticks en hypoglycémie, vigueur à 0,020 du plancher, donc C2
éteint à ~97 %. Voir
[`DIAGNOSTIC_18082026_...`](../recherche/DIAGNOSTIC_18082026_pourquoi_la_douleur_coute.md).

**Contrôle clé** : chaleur moyenne ressentie **0,3617 (ON) vs 0,3553 (OFF)** — les deux
bras voient autant de danger, seule la douleur diffère.

**Conclusion.** Une contrainte homéostatique **peut** faire émerger une aversion sans
qu'aucune règle ne nomme le danger. Mais **la peur seule ne produit pas la compétence**.
Bilan général inchangé : **1 mécanique cognitive sur 13** a amélioré une métrique de tâche.

---

## [v41.25-fix1-experimental] - 2026-08-18 — La douleur était annulée par sa propre soustraction

### Une erreur de MESURE, pas de conception : `r_bio = −1,000` n'a jamais existé

| Type | Details |
|------|---------|
| **Commit** | `b648e1f` |
| **Catégorie** | fix critique |
| **Impact** | **Critique — la mécanique v41.25 était entièrement inopérante** |
| **Banc** | [`banc_intra_tick_douleur.py`](../recherche/scripts/banc_intra_tick_douleur.py) |

**Le défaut.** `r_bio` est la DIFFÉRENCE `deficit_avant − deficit_apres`, et
`step_metabolisme` calcule `deficit_avant` **en interne**. La v41.25 écrivait
`moteur_bio.chaleur` **avant** d'appeler cette méthode : les deux déficits contenaient
donc la **même** valeur de `T²`, qui **disparaissait de la soustraction**.

```
r_bio en entrant dans la lave : −0,000238
r_bio sans aucune chaleur     : −0,000238
ÉCART                         :  0,000000     ← la douleur, exactement annulée
```

**Comment l'erreur est passée.** Le `r_bio = −1,000` annoncé en v41.25 était mesuré
**à la main**, hors du tick réel : deux appels à `calculer_deficit` encadrant une
affectation. **Le moteur n'a jamais produit ce chiffre.** C'est exactement le défaut que
le §3 de la règle de mesure décrit — un résultat trop propre, jamais confronté au chemin
réel d'exécution.

**Le signe qui aurait dû alerter immédiatement.** Sur 5 paires de graines, les valences
étaient identiques **à la 6ᵉ décimale** — y compris `FOOD +0.254431` et `sol +0.160835`,
qui n'ont aucun rapport avec la lave. Ce n'était pas « la douleur n'atteint pas la
lave » : **les deux cerveaux étaient le même cerveau**. J'ai lu la ligne `lava` en
premier et raisonné dessus au lieu de voir que la colonne entière était identique.

⚠️ **Le diagnostic initial était faux lui aussi.** L'hypothèse retenue sur le moment
était que `poids_evenement = 1.0 if recompense_env > 0 else 0.0` fermait la porte du
choc dopaminergique. Vérification faite, **la valence ne lit jamais `poids_evenement`** :
elle moyenne directement `intensite` = `recompense_interne`, où `r_bio` **est** présent
(`noyau.py:8194`). Cette porte existe, mais pour la dopamine et la fortification
synaptique — pas pour la valence.

**Le correctif.** `chaleur_apres` devient un **argument** de `step_metabolisme`, appliqué
**ENTRE** les deux mesures : `deficit_avant` porte la chaleur de la case quittée,
`deficit_apres` celle de la case atteinte. C'est la **transition** qui fait mal, jamais
le niveau seul.

| Fichier modifié | Changement |
|-----------------|------------|
| `src/naulthene/cerveau/noyau.py` | `step_metabolisme(..., chaleur_apres=None)` ; la relecture post-step STOCKE au lieu d'appliquer |
| `docs/recherche/scripts/banc_intra_tick_douleur.py` | **nouveau** — lit `r_bio` À LA SORTIE du moteur, interdiction de recalculer un déficit à la main |

**Mesures après correctif** (banc intra-tick, produites **par le moteur**) :

| transition thermique | `r_bio` | douleur vs témoin |
|---|---|---|
| 0,00 → 0,00 (témoin) | −0,000238 | 0,000000 |
| 0,00 → 0,46 (case adjacente) | −0,211838 | **−0,2116** |
| 0,46 → 1,00 (**pas réel dans la lave**) | **−0,791111** | **−0,7909** |
| **1,00 → 0,00 (fuite)** | **+0,999762** | **SOULAGEMENT** |
| même pas, `--sans-douleur` | −0,000238 | écart **−1,000000** |

**Effet mesuré sur la valence apprise** (25 jours, graine 1) :

| | douleur ON | témoin OFF |
|---|---|---|
| **`lava`** | **−0,752562** | **+0,062455** |

La valence de la lave devient **négative pour la première fois du projet**. Elle était
positive (+0,059 à +0,081, soit celle de l'eau) sur **tous** les cerveaux mesurés depuis
l'origine.

⚠️ Cela prouve que **le canal fonctionne**, pas que le comportement s'améliore : la
campagne 20 graines × 2 bras est relancée pour mesurer la **survie**.

---

## [v41.25-experimental] - 2026-08-18 — La chaleur qui fait mal : fermer la boucle nociceptive

### La lave avait la valence de l'eau

| Type | Details |
|------|---------|
| **Commit** | `5b361a7` |
| **Catégorie** | feat (expérimental) |
| **Impact** | **Fonctionnel — homéostasie / apprentissage du danger** |
| **Carnet** | [`NOCICEPTION_18082026_...`](../recherche/NOCICEPTION_18082026_la_chaleur_qui_fait_mal.md) |

**Le défaut mesuré.** Sur la campagne v41.24 (17 graines × 2000 jours), la valence
apprise de la lave est **`+0,059` à `+0,066` — POSITIVE**, à peu près celle de l'eau.
Cause directe : MiniGrid punit la mort par **exactement `0.0`**, quand toucher un mur
coûte `−0,01`. **Mourir était infiniment moins cher que se cogner.**

**Ce qui existait déjà.** La v41.11 avait livré le **sens**, pas la **douleur** : champ
de rayonnement `T = e^{−λd}`, BFS topologique, murs faisant ombre thermique, 2 dims
(chaleur + ΔT) en queue du vecteur bio, `λ` dérivé de la carte. Tout cela était en
place. L'agent **percevait** la chaleur sans qu'elle lui **coûte** quoi que ce soit :
la boucle était ouverte.

**Le correctif — une ligne, aucun coefficient.**

```python
D(t) = (1−satiété)² + (1−hydratation)² + (1−stimulation)² + (1−énergie)² + T(t)²
```

`r_bio = D(t−1) − D(t)` étant une **dérivée**, tout en découle sans qu'aucune règle ne
le décrive : approcher fait mal proportionnellement, entrer dans la source produit
**`r_bio = −0,791`** sur un vrai pas dans la lave (banc intra-tick, transition
0,457 → 1,000), soit ~3300× le coût métabolique d'un tick ordinaire (−0,000238).
⚠️ **Le `−1,000` publié initialement était FAUX** — voir l'entrée `v41.25-fix1`
ci-dessus. **Aucune échelle n'est posée** — les trois jauges donnent `(1−x)² ∈ [0,1]`, la chaleur donne `T² ∈ [0,1]` par
construction du champ.

**Le piège du décalage d'un tick.** La thermoception est lue **en tête de tick**, donc
avant `env.step` ; la facturation a lieu **après**. Sans correctif, l'agent qui marche
dans la lave payait la température de la case **quittée** (~0,457) et, l'épisode
s'arrêtant aussitôt, **n'aurait jamais ressenti `T=1`**. C'est le décalage temporel
corrigé en v41.5 sur la maturité, reproduit ici pour la même raison. Corrigé par
`chaleur_seule()`, accesseur **sans effet de bord** — rappeler `lire_thermoception()`
aurait écrasé `_chaleur_precedente` et faussé la clinotaxie du tick suivant.

**Ce qui a été REFUSÉ.**
- ❌ `si mort: récompense −= X` — seuil en dur sur un type nommé (invariant v41.11).
- ❌ Drain d'hydratation au contact (**arbitrage utilisateur**) — double comptage, le
  risque n°3 déjà écarté dans `calculer_deficit`. À `T=1` le déficit est déjà maximal.

| Fichier modifié | Changement |
|-----------------|------------|
| `src/naulthene/cerveau/noyau.py` | `+ chaleur**2` dans `calculer_deficit` ; état `chaleur` ; relecture post-step ; compteurs de survie ; drapeau `DOULEUR_THERMIQUE_ACTIVE` ; `ENV_FORCE` |
| `src/naulthene/cerveau/bus_sensoriel.py` | `_champ_thermique()` extrait (BFS partagé) + `chaleur_seule()` sans effet de bord |

**Banc de mesure (`--env-force`).** La lave n'apparaît qu'au **niveau 5** et l'agent est
bloqué au **4** : sur le cursus, la chaleur moyenne vaut **0,001 (1 tick actif / 400)**.
Un A/B lancé là aurait comparé deux bras dont le terme mesuré est nul dans **99,7 %**
des ticks — une ablation **VIDE**, pas négative (§4 de la règle de mesure). Sur
`LavaGapS5` forcé : **300 à 400 ticks actifs / 400**.

**Contrôles.** Test **A/A identique** ✅ · ablation atteignant le module (déficit
**1,107 ON vs 0,998 OFF**) · `chaleur_seule` sans effet de bord ✅ · ablation **vide**
sur monde sans lave (chaleur max `0,000000`) · `chaleur moy. à la mort = 1,000`.

⚠️ **Résultat non encore établi.** À 5 jours, la survie est **identique** dans les deux
bras : le déficit diffère bien, mais la douleur n'a pas encore changé les **décisions**.
Campagne **20 graines × 2 bras × 800 jours** en cours ; aucune conclusion ne sera tirée
sous 20 graines, et chaque taux sera donné **avec son intervalle de Wilson**.

---

## [v41.24-experimental] - 2026-08-18 — La croissance n'est plus un droit, c'est un budget

### L'hypertrophie : 512 dimensions, 60 % de synapses mortes, aucun gain de niveau

| Type | Details |
|------|---------|
| **Commit** | `54f2f1b` |
| **Catégorie** | feat (expérimental) |
| **Impact** | **Fonctionnel — neurogenèse** |
| **Carnet** | [`NUIT_18082026_...`](../recherche/NUIT_18082026_le_niveau_5_franchi_et_le_frein_qui_ne_borne_pas.md) |

**Le défaut mesuré.** Plafond relevé à 512 : `dim_bus` finissait à **512/512 sur
3 graines (31 mutations)** pour un niveau atteint **identique** (4/3/4), une énergie
divisée par 11 (0,19 → 0,017) et un effort triplé. Et **60 % des synapses** du gros
cerveau n'étaient **jamais myélinisées** — on ajoutait du tissu, pas de la capacité.

**Le piège d'auto-justification** : un gros réseau prédit marginalement mieux (0,0013
contre 0,0047), donc `seuil_base` relaxe vers cette erreur ultra-basse, donc l'agent se
crée un standard d'exigence infini — chaque agrandissement justifie le suivant. Le frein
v41.23 stabilise le **rapport** erreur/seuil, jamais la **taille**.

**Le principe (décision utilisateur)** : un organisme n'investit dans du tissu neural que
si les calories dépensées rapportent un bénéfice de survie.

```
rendement = Δ(erreur JEPA gagnée) / Δ(effort métabolique payé)
vitalité  = rendement courant / rendement de référence
ajout     = round(AJOUT_DIM_BASE × vitalité)
```

⚠️ **Aucun `if rendement < X`.** L'arrêt est **arithmétique** : `round(16 × 0.03) == 0`.
L'agent déclenche sa mutation, la biologie ne lui accorde aucun neurone. Mesuré sur les
gains réels de `t512_g7` : l'ajout tombe **16 → 11 → 7 → 5 → 3 → 2 → 1 → 0**.

**Ce que la mesure a imposé de corriger dans la conception initiale.** `rendement_ref`
devait être figé au premier rendement. Testé : si la première mutation tombe sur un
rendement anormalement bas (l'erreur baissait déjà seule), la vitalité **explose** —
simulé, **ajout = 1020 dimensions**. C'est le défaut de `norme_naissance` (v34.0-fix2) à
l'identique. `rendement_ref` est donc un **cliquet** : montée immédiate, descente 50× plus
lente (`INERTIE_OUBLI_RENDEMENT`), et `vitalité` est bornée à 1.0.

**Vérifié en run réel** (60 jours) : `MUTATION +16` → `MUTATION +1` →
`Rendement nul (croissance refusée)`, `dim_bus` final **75** au lieu de 160.

**Persistance** : les quatre champs du rendement sont sérialisés. Sans cela un `.brain`
rechargé repartirait à vitalité 1.0, donc +16 — l'agent oublierait à chaque résurrection
que grandir ne lui rapporte plus rien. Lecture défensive `.get()` : un `.brain` antérieur
repart avec un rendement vierge, sans greffe.

| Fichier modifié | Changement |
|-----------------|------------|
| `src/naulthene/cerveau/noyau.py` | neurogenèse budgétée par le rendement · `AJOUT_DIM_BASE` · `INERTIE_OUBLI_RENDEMENT` |
| `src/naulthene/cerveau/persistance.py` | sérialisation du rendement structurel (4 champs, lecture défensive) |

---

## [v41.23-experimental] - 2026-08-18 — Le frein d'expansion en formules, et ce qu'il ne borne pas

### Le thermostat n'avait que des `if` ; il a maintenant deux pressions continues

| Type | Details |
|------|---------|
| **Commit** | `bfc546f` |
| **Catégorie** | fix (expérimental) — conformité au dogme |
| **Impact** | **Fonctionnel — neurogenèse** |
| **Carnet** | [`EXPANSION_17082026_le_frein_de_la_neurogenese.md`](../recherche/EXPANSION_17082026_le_frein_de_la_neurogenese.md) · [`NUIT_18082026_...`](../recherche/NUIT_18082026_le_niveau_5_franchi_et_le_frein_qui_ne_borne_pas.md) |

**Deux remarques de l'utilisateur, le même défaut.** *« C'est quoi la différence entre
avant V30 où le système se stabilisait tout seul ? »* et *« Je ne vois que des conditions…
alors qu'il faudrait des formules. »*

**La régression.** Les `.brain` V30 archivés se stabilisent à **dim_bus 48** (plafond 96,
jamais atteint). Après la v41.21 : **20/20 collent au plafond**. J'avais remplacé la
condition historique par la seule cristallisation cosmologique, en jugeant la ligne
`variance < 0.005 AND moyenne > seuil*1.5` sur son membre mort (la variance, toujours
vraie) — alors que le second membre faisait **monter `seuil_base` vers l'erreur**, et que
c'est ce rattrapage qui éteignait la neurogenèse.

**Le correctif (Option B, arbitrage utilisateur)** — deux pressions continues, aucun seuil :

```python
exigence = 1.0 + 1.0 / JOURS_ENTRE_MUTATIONS          # 1,20 — remplace le 1.5 posé
pression_structure   = (coh/fr) / (1 + coh/fr)        # limite physique (Landau)
_ecart               = moyenne / (seuil_base * exigence)
pression_habituation = _ecart / (1 + _ecart)          # limite d'habituation
pas = max(pression_structure, pression_habituation)   # le « OU » devient un max continu
```

`x/(1+x)` est une saturation : pas de pente réglable, pas de point de bascule. Le « OU »
logique devient un `max` continu — c'est ce qui fait disparaître le `if`. L'exigence
dérive de la fenêtre d'observation, plus du `1.5` posé.

**Résultats mesurés (nuit du 18/08, 20 graines × 1500 jours) :**

| Palier | Atteint | Wilson 95 % |
|---|---|---|
| niveau 4 | **20/20** | **100 %** [84–100] |
| niveau 5 | **4/20** | **20 %** [8–42] |

Trois cerveaux vivent 521 à **1078 nuits** au palier 5 et y terminent — le palier est
**tenu**, contrairement à `esprit_g7` (17/08) qui y montait puis redescendait.

⚠️ **Ce que le frein NE fait PAS.** Plafond relevé à 512 (banc `NAULTHENE_PLAFOND_BUS`) :
`dim_bus` finit à **512/512** sur 3 graines. Le frein rattrape bien l'erreur, mais un gros
cerveau prédit **3,6× mieux** (0,0013 contre 0,0047), donc son seuil descend avec elle. Il
stabilise le **rapport** erreur/seuil, jamais la **taille** — exactement le défaut de
`reference_choc_dopamine` (v37.1-fix1) reproduit dans un autre organe.

**Et grandir ne rapporte rien** : à plafond 512, niveau identique (4/3/4) pour une énergie
divisée par 11 (0,19 → 0,017) et un effort triplé.

| Fichier modifié | Changement |
|-----------------|------------|
| `src/naulthene/cerveau/noyau.py` | pressions continues dans le thermostat · `NAULTHENE_PLAFOND_BUS` (banc) |

---

## [v41.21-experimental] - 2026-08-17 — La cristallisation cosmologique & la loi des 2 % / 20 %

### Le thermostat comparait une variance absolue à un nombre posé ; la biologie donne les poids

| Type | Details |
|------|---------|
| **Commit** | `89ac5ad` |
| **Catégorie** | fix (expérimental) — conformité au dogme |
| **Impact** | **Fonctionnel — neurogenèse & métabolisme** |
| **Carnet** | [`REVUE_DOGME_17082026_rien_en_dur.md`](../recherche/REVUE_DOGME_17082026_rien_en_dur.md) |
| **Source** | [`docs/naulthene_cosmologie/`](../naulthene_cosmologie/) — modèle v5.0/v5.1 |

**Violation n°2 levée — le thermostat de neurogenèse.** L'ancienne condition était :

```python
if variance_erreur < 0.005 and moyenne_glissante > etat.seuil_base * 1.5:
    etat.seuil_base = (0.7 * etat.seuil_base) + (0.3 * moyenne_glissante)
```

Cinq nombres nus, et surtout une **échelle absolue** : l'erreur JEPA réelle vaut 0,0111 à
0,0173, donc une variance de ~4e-6 — **mille fois sous le seuil**. La condition était
**toujours vraie** : elle ne discriminait rien. C'est le défaut exact de `SEUIL_CRISTAL =
0.80` (myéline réelle 0,0038) et de `q_ref = 1.0`, tous deux corrigés en v37.0.

**Le correctif vient du modèle cosmologique du projet.** Le potentiel de Landau
`V(Q,K) = C(c)Q²/2 + K²ln(N)/2 − Q·K + Q⁴/4` fait émerger la cristallisation d'une seule
condition de survie — `C(c) > ln(N)`, **cohésion interne contre friction d'expansion** —
dont le seuil `c_min = 5` n'est pas posé mais **calculé** (c=3 → 28,07 et c=4 → 120,69
échouent contre ln(10¹²²) ≈ 280,9 ; c=5 → 448,58 survit).

Transposition terme à terme, adimensionnelle :

| Cosmologie | Thermostat |
|---|---|
| `C(c)` cohésion du cluster | `1/CV²` où `CV = σ/μ` de l'erreur JEPA |
| `ln(N)` friction d'expansion | `ln(nb de paramètres du cerveau)` |
| cristallise si `C(c) > ln(N)` | fige la référence si `cohésion > friction` |

La fenêtre suit désormais `JOURS_ENTRE_MUTATIONS` (seule échelle de temps que la
neurogenèse connaisse) et le pas de relaxation vaut `1/fenêtre`, plus `0.7/0.3`.

**Mesuré** — le thermostat discrimine enfin : sur 60 jours, 4 mutations puis 48 nuits
stables, avec une erreur JEPA qui converge de 0,1543 à 0,0053.

**La loi des 2 % / 20 % — `POIDS_CORPS` et `POIDS_CERVEAU` ne sont plus posés.**
Chez l'humain adulte le cerveau pèse **2 % de la masse** et consomme **20 % de l'énergie**
au repos. Ces deux mesures suffisent à produire les deux poids :

```python
FRACTION_MASSE_CERVEAU   = 0.02
FRACTION_ENERGIE_CERVEAU = 0.20
POIDS_CERVEAU = FRACTION_ENERGIE_CERVEAU        # 0,20
POIDS_CORPS   = 1.0 - FRACTION_ENERGIE_CERVEAU  # 0,80
```

Les valeurs numériques sont **inchangées** — le « 20/80 » de la v19.0 tombait juste — mais
leur statut change : ce ne sont plus des facteurs d'échelle tolérés, ce sont les
conséquences d'une loi vérifiable. Le rapport 20/2 = **10** est la densité métabolique
cérébrale : un gramme de cerveau coûte dix grammes de corps.

**La masse totale découle du cerveau** : `masse_totale = m_cerveau / 0,02 + réserve +
charge`. Le corps qui porte l'encéphale entre enfin dans le modèle, et la part cérébrale
reste rigoureusement à 2 % quelle que soit la neurogenèse.

**`rayon = 0.5` éliminé.** Il est remplacé par `PAS_GRILLE / 2` : MiniGrid est discret,
l'agent occupe exactement une case, son rayon est donc une demi-case. Le `0.5` n'était que
cette division, non écrite.

| Fichier modifié | Changement |
|-----------------|------------|
| `src/naulthene/cerveau/noyau.py` | thermostat en cohésion/friction · `FRACTION_MASSE_CERVEAU`/`FRACTION_ENERGIE_CERVEAU` · `PAS_GRILLE` · masse totale à 2 % |

---

## [v41.20-experimental] - 2026-08-17 — Le coût moteur devient un travail physique

### Sept valeurs déclarées facturaient 79 % de leur montant pour des gestes sans effet

| Type | Details |
|------|---------|
| **Commit** | `89ac5ad` |
| **Catégorie** | fix (expérimental) — conformité au dogme |
| **Impact** | **Fonctionnel — métabolisme** |
| **Carnet** | [`REVUE_DOGME_17082026_rien_en_dur.md`](../recherche/REVUE_DOGME_17082026_rien_en_dur.md) |

**Violation n°1 levée.** `COUT_CORPOREL_PAR_ACTION` posait sept valeurs indexées par
action MiniGrid (`0: 0.2` … `6: 0.1`), lues **à chaque tick** et pesant 80 % de l'effort.
Structurellement la même faute que la table `lava = danger` interdite par l'invariant
v36.0, déplacée du *quoi* vers le *combien*.

**Mesuré** (sonde v41.19, 6 graines × 400 jours, 2400 nuits) :

| action | tarif | part | stérile |
|---|---|---|---|
| tourner G/D | 0,2 | 25,3 % | **0 %** |
| avancer | 0,5 | 15,3 % | **53 %** |
| prendre | 0,8 | 21,8 % | **89 %** |
| poser | 0,8 | 9,4 % | **100 %** |
| activer | 0,6 | 19,3 % | **100 %** |

Coût facturé **0,5016/tick dont 0,3957 pour du vide** — une sur-facturation de **×4,73**.

**Le correctif** : l'effort est un travail (`masse × déplacement réel`), mesuré autour du
`env.step`. Deux erreurs écartées en chemin, toutes deux mesurées :

1. `E_corps = M × (1 + d)` **double-comptait le basal** — déjà prélevé par `taux_satiete`
   et `taux_hydratation`. Effort mesuré à **2,269** contre 0,639 au témoin.
2. `r = √(M/π)` rendait la rotation **quadratique** (×49 à masse 7), et `d = (π/2)·r`
   faisait coûter une rotation **2,3× plus cher qu'une translation**.

**Résultat de la campagne (20 graines × 2 bras × 600 j)** : `physique gagne 2 · perd 3 ·
nul 15`, **p = 1,0000**. Aucun gain de performance — c'est une victoire de **conformité**,
pas d'efficacité. La table survit uniquement comme témoin d'ablation
(`--cout-moteur-table`).

| Fichier modifié | Changement |
|-----------------|------------|
| `src/naulthene/cerveau/noyau.py` | `calculer_effort_metabolique` physique · `masse_totale` · sonde v41.19 · `--cout-moteur-table` |

---

## [v41.16-experimental] - 2026-08-17 — Le brain-sparing : la faim ne coupe plus la lucidité

### L'agent affamé ne ralentissait pas — il décidait au hasard

| Type | Details |
|------|---------|
| **Commit** | `ef7925d` |
| **Catégorie** | fix (expérimental) |
| **Impact** | **Critique — cognitif** |
| **Carnet** | [`DIAGNOSTIC_17082026_pourquoi_C2_est_etouffe.md`](../recherche/DIAGNOSTIC_17082026_pourquoi_C2_est_etouffe.md) |

**Le défaut.** La v41.2 multipliait les **logits** par `vigueur`, et son commentaire
promettait : *« le plancher garantit qu'il reste COHÉRENT — sans lui l'action deviendrait
ALÉATOIRE »*. La mesure dit l'inverse exact, **plancher compris** :

```
vigueur 1.00 → amplitude 1.219 → proba de l'action favorite 0.231 → entropie 0.955
vigueur 0.15 → amplitude 0.191 → proba de l'action favorite 0.158 → entropie 0.999
                                                          (1/7 = 0.143 = HASARD PUR)
```

`softmax` est invariante par translation, **pas par échelle** : diviser l'écart entre les
7 logits n'atténue pas une préférence, elle l'**efface**.

Et c'est le régime **normal** de cet agent — énergie moyenne 0,041 sur les runs longs,
`400/400 ticks en basse énergie` dès le premier jour. Toute sa vie, il a décidé au hasard.

**La loi du vivant** (formulation utilisateur) : en pénurie sévère, le corps ne coupe
jamais le cerveau en premier — il sacrifie la périphérie. *Un animal affamé qui perd sa
motricité peut survivre immobile ; un animal qui perd sa lucidité est condamné.*

**Le correctif.** `vigueur` cesse de multiplier les logits, des **deux** côtés (C1 et
`force_planification`). Elle continue de moduler le coût des actions, le déficit, la
plasticité et l'envie de vivre : **le corps ralentit toujours, seul l'esprit reste allumé**.

⚠️ **Ce n'est pas « renforcer C2 ».** Les deux voix subissaient le même facteur : le
retirer des deux laisse l'arbitrage inchangé (55,8 % pour C2 avant comme après, à
vigueur 1,0). Ce qui change est la **netteté** de la décision.

| Mesure (vigueur 0,15) | avant | après |
|---|---|---|
| amplitude des logits | 0,191 | **1,219** |
| entropie de la décision | 0,999 | **0,955** |
| part de C2 dans la fusion | 81,1 % *(dérive)* | **55,8 %** *(stable)* |

Run réel, graine 202, 100 jours : ratio C2/C1 **0,22× → 1,23×**, maîtrise finale
0 % → 25 %.

| Fichier modifié | Changement |
|-----------------|------------|
| `src/naulthene/cerveau/noyau.py` | `voix_c1` et `force_planification` ne subissent plus `vigueur` ; drapeau `--vigueur-sur-logits` (témoin v41.15) |

**Campagne 10 graines × 2 bras × 400 jours en cours.**

---

## [v41.13-experimental] - 2026-08-16 — C2 imaginait un monde sans corps

### Le vecteur bio n'entrait jamais dans le rollout mental

| Type | Details |
|------|---------|
| **Commit** | `f2f6105` |
| **Catégorie** | feat (expérimental) |
| **Impact** | **Critique — architectural** |
| **Carnet** | [`CORRECTIF_v4113_corps_dans_le_rollout.md`](../recherche/CORRECTIF_v4113_corps_dans_le_rollout.md) |

**Le défaut.** `integrateur_bio` n'apparaissait **nulle part** dans
`simuler_futur_et_planifier`. Les **41 dims** du vecteur bio entraient une seule fois via
C1, puis C2 simulait 7 futurs × 7 sauts **sans jamais reprojeter un seul sens**. C2 ne
pouvait donc pas simuler « si j'avance je serai collé au mur » ni « si je continue la
chaleur montera ».

**Ce que ça unifie.** Trois mesures lues séparément jusqu'ici — couper C2 = 0,0 pt sur 6
niveaux ; C2 36 % plus gros chez ceux qui échouent ; 4 sens sur 6 ablatables sans effet —
admettent une cause commune : **les sens n'atteignent pas le modèle du monde, et le modèle
du monde simule un agent désincarné**. Hypothèse *confortable*, donc soumise à campagne
A/B plutôt qu'affirmée.

**Étape 1 — mesurer d'abord (coût nul).** Ventilation de l'erreur JEPA existante, sans
ajouter une tête. Résultat : l'erreur **se concentre** (0,625 → 0,888 sur 3 jours, où 0,25
serait un étalement parfait), l'amplitude de la cible reste **non nulle** (0,21–0,30), et
la pire dimension est à **8×** l'erreur moyenne. Le modèle du monde n'est **pas** saturé —
l'étape 2 est justifiée.

**Étape 2 — le correctif, en une ligne.** Réutilisation d'`integrateur_bio` dans la boucle
de rollout : aucune tête nouvelle, aucun paramètre, aucune constante. L'alternative
(5 têtes JEPA + 5 portes) ferait grossir de ~30 % un cœur déjà 2,85× plus lourd qu'un PPO
qui le bat.

| Fichier modifié | Changement |
|-----------------|------------|
| `src/naulthene/cerveau/noyau.py` | `simuler_futur_et_planifier(vecteur_bio=...)`, transmis par `_solliciter_c2_neocortex` et `penser` ; ventilation JEPA (4 diagnostics, `no_grad`) ; drapeau `--sans-corps-rollout` ; ligne de bilan + 3 clés W&B |

**Vérifié** : A/A **bit-identique** sur les deux bras (graine 33) ; témoin ≠ variante ;
ablation confirmée par assertion runtime ; `vecteur_bio=None` ⇒ chemin v41.12 exact (le
rêve est inchangé).

⚠️ **Assumé** : le vecteur bio est tenu **constant** sur le rollout — l'agent imagine son
corps *actuel* projeté dans les futurs. Prédire l'évolution des sens exigerait les têtes
JEPA par sens (étape 3), à n'envisager que si cette campagne montre un effet.

**Campagne 20 graines × 2 bras × 3000 jours en cours.**

---

## [v41.12-experimental] - 2026-08-16 — Le toucher à distance & la portée qui suit le monde

### Les sens étaient des interrupteurs, pas des gradations

| Type | Details |
|------|---------|
| **Commit** | `907f391` |
| **Catégorie** | feat (expérimental) |
| **Impact** | **Fonctionnel** |

**Le défaut (utilisateur, 16/08)** : *« les sens sont des éléments de gradation, pas 0 ça
marche pas et 1 ça marche »*. Deux mesures le confirment.

1. **Le toucher était un interrupteur à portée ZÉRO.** `contact_frontal` vaut 1 ou 0 sur
   la seule case devant : aucune anticipation (l'agent apprend le mur **en le
   percutant**), aucune gradation (un couloir et une plaine donnent le même `0.0`),
   aucune direction.
2. **L'odorat s'éteignait à 5 cases** quelle que soit la carte. Sur `Empty-8x8` l'agent
   était olfactivement aveugle sur la moitié de son monde ; sur MultiRoom, sur les trois
   quarts.

**Les correctifs.** `DIM_PRESSION = 2` — encombrement gradué + asymétrie gauche/droite, en
directions **relatives au corps**. Et λ **dérivé de la géométrie** de la carte, avec une
fraction **mesurée** (critère : le gradient entre cases voisines, jamais la couverture).

| Carte | Portée | Gradient |
|---|---|---|
| Empty-5x5 | 4 → 5 | −0 % *(aucune régression)* |
| **Empty-8x8** | 4 → **8** | **+12 %** |
| **SimpleCrossing** | 4 → **9** | **+20 %** |
| MultiRoom | 4 → **25** | **+195 %** |

⚠️ **Erreur corrigée en cours de route** : la première version bornait λ à `LAMBDA_ODORAT`
« par prudence ». Cette borne rendait le correctif **inopérant sur Empty-8x8** — le niveau
du blocage — en y préservant le pire réglage des sept testés.

| Fichier modifié | Changement |
|-----------------|------------|
| `src/naulthene/cerveau/bus_sensoriel.py` | `DIM_PRESSION`, `PORTEE_PRESSION`, `lire_pression()`, `lambda_diffusion_carte()`, `FRACTION_PORTEE_CARTE` |
| `src/naulthene/cerveau/noyau.py` | `DIM_VECTEUR_BIO` 39 → 41 ; borne haute sur la tranche `_thermo` ; 3 compteurs + ligne de bilan + 3 clés W&B |

**Vérifié** : greffe `.brain` **101 → 105 dims sans exclusion** ; asymétrie mesurée à
0,170–0,224 (le signal latéral porte de l'information, il n'est pas plat).

---

## [v41.11-experimental] - 2026-08-16 — La thermoception : le danger comme champ continu

### L'agent ne pouvait apprendre le danger ni par les sens, ni par l'expérience

| Type | Details |
|------|---------|
| **Commit** | `bb1da9a` |
| **Catégorie** | feat (expérimental) |
| **Impact** | **Fonctionnel** |
| **Carnet** | [`CORRECTIF_v4110_memoire_par_carte.md`](../recherche/CORRECTIF_v4110_memoire_par_carte.md) §3 |

**L'idée (utilisateur, 16/08).** *« Peut-être que MiniGrid manque de gradation (2 cases de
lave = chaud / 1 case = brûlant / sur la case = mort). Et quand on est mort = 0 XP = mort ! »*

**Les quatre mesures qui la valident.**

1. MiniGrid punit la mort par **exactement `0.0`** — 206 morts sur 300 épisodes, toutes à
   récompense nulle. Toucher un mur coûte `MALUS_DOULEUR = -0,01` : **toucher un mur coûte
   infiniment plus cher que mourir.**
2. Le vecteur bio était **rigoureusement identique** sur la case adjacente à la lave et à
   trois cases de distance.
3. La lave figurait dans `TYPES_BLOQUANTS_ODORAT` : elle **arrêtait** l'odeur sans jamais
   en **émettre**. Une cloison, jamais une source.
4. La vue la voit (indice `9`) mais comme un symbole parmi d'autres — `9` ne se distingue
   de `1` (sol) par rien de continu.

**Le correctif.** Deux dimensions **en queue** du vecteur bio (37 → 39) : `chaleur` et
`delta_chaleur`, calculées par la **même machinerie que l'odorat** (BFS topologique, même
loi `exp(-λd)`). Le danger devient « une odeur de plus ». Les murs font de l'ombre
thermique ; les cases brûlantes rayonnent (donc franchissables comme points de départ du
BFS, contrairement au calcul olfactif).

Champ mesuré sur `LavaGapS5` — exactement la gradation demandée :

| Distance | Chaleur |
|---|---|
| sur la lave | **1,000** |
| adjacent | **0,449** |
| 2 cases | **0,202** |

**Pourquoi un champ et pas un malus.** `si mort → récompense −= X` serait un seuil en dur
sur un type nommé, ce que l'invariant v36.0 interdit. Un champ est un **sens de plus** :
l'agent en découvre le sens par ce qui lui arrive quand il monte, jamais par déclaration.

| Fichier modifié | Changement |
|-----------------|------------|
| `src/naulthene/cerveau/bus_sensoriel.py` | `DIM_THERMOCEPTION`, `TYPES_BRULANTS`, `lire_thermoception()`, `_chaleur_precedente` (remis à `None` au reset), branchement en queue d'`interpreter()` |
| `src/naulthene/cerveau/noyau.py` | `DIM_VECTEUR_BIO` 37 → 39 ; borne HAUTE sur la tranche `deltas_odorat` (sans quoi la thermoception aurait été comptée comme clinotaxie) ; 5 compteurs journaliers ; ligne de bilan + 4 clés W&B conditionnelles |

**Vérifié** : gradient cohérent sur toute la grille ; clinotaxie thermique correcte dans
les deux sens (approche 0,624 / recul 0,376) ; **non-régression exacte** `(0.0, 0.5)` sur
Empty-5x5, DoorKey-6x6 et Empty-8x8 ; greffe `.brain` **101 → 103 dims sans exclusion**,
validée sur deux nuits complètes.

**Première mesure** : l'agent **approche du danger 69–80 % des ticks de variation**. C'est
la ligne de base contre laquelle l'apprentissage se mesurera (`Thermo_Taux_Approche` doit
décroître).

---

## [v41.10-experimental] - 2026-08-16 — La mémoire par carte

### P17 effaçait la mémoire spatiale ~3750 fois par run

| Type | Details |
|------|---------|
| **Commit** | `89ac5ad` |
| **Catégorie** | fix (expérimental) |
| **Impact** | **Fonctionnel** |
| **Carnet** | [`CORRECTIF_v4110_memoire_par_carte.md`](../recherche/CORRECTIF_v4110_memoire_par_carte.md) |

**Le défaut.** P17 (v41.6) tire le niveau de chaque épisode au sort : l'agent change de
carte ~1,5 fois par jour. Chaque bascule appelait `reinitialiser_niveau()`, soit un
**effacement complet** de la mémoire spatiale — ~3750 fois sur un run de 2500 jours.

Mesuré sur la campagne des 20 graines du 16/08 :

```
🗺️ 5/200 souvenir(s) spatial(aux) — 51 715 doublon(s) évité(s)
```

La mémoire tournait à **1 % de sa capacité**. L'abstraction par récurrence (v36.0), dont
tout le principe est que `confirmations` monte avec la répétition, ne pouvait
**structurellement** jamais accumuler.

**L'erreur de raisonnement.** L'effacement confondait « changer de carte » (les
coordonnées courantes ne s'appliquent plus) et « ne plus jamais y aller » (elles ne valent
plus rien). Avant P17 les deux coïncidaient en pratique ; P17 a invalidé cette hypothèse
sans que l'effacement soit revu.

**Le correctif.** Une **archive par carte** : `souvenirs` reste la vue de la carte
courante, les autres dorment dans `archives_cartes`. L'invariant v39.0 (une coordonnée
n'est jamais lue hors de sa carte) est **renforcé**, pas affaibli.

| Fichier modifié | Changement |
|-----------------|------------|
| `src/naulthene/cerveau/noyau.py` | `basculer_carte()`, `total_souvenirs()`, `archives_cartes` ; `dedupliquer()` compacte aussi les archives ; drapeau d'ablation `--sans-memoire-cartes` ; ligne de bilan `Cartes v41.10` + 3 clés W&B |
| `src/naulthene/cerveau/persistance.py` | `archives_cartes` et `carte_courante` sérialisées, lecture défensive `.get()` |

**Vérifié** : 9 invariants en test unitaire (dont le test de fuite v39.0) ; A/A
bit-identique sur graine 7 ; ablation confirmée coupante (1 carte vs 4) ; rétrocompatibilité
d'un `.brain` v41.9 sur une **nuit complète**.

Effet immédiat sur 3 jours : 4 cartes en mémoire et 33 repères contre 1 et 16.

---

## [v41.9-experimental] - 2026-08-16 — Le banc d'essai devient reproductible

### `env.reset()` n'était jamais seedé — le projet ne pouvait mesurer aucun effet

| Type | Details |
|------|---------|
| **Commit** | `3e2304d` |
| **Catégorie** | fix (expérimental) |
| **Impact** | **Critique — méthodologique** |
| **Carnet** | [`NUIT_15082026_trois_questions.md`](../recherche/NUIT_15082026_trois_questions.md) §6 |

**Le défaut.** `env.reset()` était appelé **sans graine** aux quatre points du fichier
(0 occurrence de `reset(seed=` avant cette version). MiniGrid possède son **propre**
générateur, initialisé sur l'entropie système : `torch.manual_seed`, `np.random.seed` et
`random.seed` n'ont **aucun effet** dessus.

Mesuré, même processus, les trois générateurs Python semés à 11 avant chaque essai :

```
reset()        → agent en (1,2), puis (2,4), puis (2,2)   ← 3 mondes DIFFÉRENTS
reset(seed=11) → agent en (4,2), (4,2), (4,2)             ← identique
```

**Deux runs de même `--graine` voyaient donc des cartes différentes** et divergeaient dès
le jour 1 (maîtrise 45 % contre 50 % sur 3 jours).

| Fichier modifié | Changement |
|-----------------|------------|
| `src/naulthene/cerveau/noyau.py` | `_graine_episode` / `_reset_seede` — graine dérivée de `graine_run × 1 000 003 + episodes_vecus`, reproductible **et** variée |
| `src/naulthene/cerveau/noyau.py` | les 4 resets centralisés : un futur appel ne peut plus réintroduire le défaut |
| `src/naulthene/cerveau/persistance.py` | `episodes_vecus` persisté — sans lui, un `.brain` repris rejouerait les mondes de sa naissance |

**Vérifié (test A/A)** : deux runs de graine 11 donnent `0.0841 / 0.0845 / 0.0418`,
identiques au chiffre près ; deux graines différentes restent distinctes (11 → 0,0841,
22 → 0,1846). Confirmé ensuite sur runs longs en parallèle : **A/A OK sur 12 jours**.

### ⚠️ Ce que ce correctif implique pour tout le dépôt

> **Toute comparaison appariée antérieure à la v41.9 est non concluante** — elle n'est pas
> fausse, elle n'établit rien : les deux branches différaient aussi par les cartes tirées.
> Cela inclut la comparaison v41.4 « héritage ON/OFF » et, potentiellement, la conclusion
> historique « 9 mécaniques cognitives sur 9 sans effet ».
>
> **Les chiffres antérieurs ne sont pas comparables aux suivants** : les cartes tirées ont
> changé. Coût accepté une fois, en échange de la seule chose qui manquait — savoir si une
> modification a un effet.

**Taux de référence mesuré la veille** (20 graines × 600 j, code v41.8-fix1) :
**40 % de graines franchissent ≥ 1 palier, IC 95 % [22 % ; 61 %]**. Les trois campagnes de
6 graines de la nuit (33 %, 50 %, 33 %) tombent **toutes** dans cet intervalle.

---

## [v41.4-experimental] - 2026-08-15 — Deux maîtrises, un héritage proportionnel à la parenté

### La mécanique marche ; elle n'a pas pu être prouvée — et elle ne débloque rien

| Type | Details |
|------|---------|
| **Commits** | `d12359a`, `c5e91bf`, `80e844c`, `35bb93b`, `4768b26`, `96a8c20`, `52b5834` |
| **Catégorie** | feat + fix (expérimental) |
| **Impact** | Fonctionnel — **`noyau.py` uniquement** |
| **Chantier** | [`CHANTIER_v41.4_maitrise_generale_et_heritage.md`](../ameliorations/CHANTIER_v41.4_maitrise_generale_et_heritage.md) |

Décision utilisateur : *« tu as une maîtrise générale des cartes et une maîtrise carte par
carte »*, et *« reporter une proportion du niveau précédent de maîtrise sur le suivant »*.

**Le défaut visé** (mesuré en v41.3) : à chaque promotion `historique_episodes_niveau`
est vidé, donc la maturité retombe à **0,000** et l'aide à **100 %** — l'agent redevient
un nouveau-né sur chaque carte.

| Fichier modifié | Changement |
|-----------------|------------|
| `src/naulthene/cerveau/noyau.py` | `historique_episodes_general` — maîtrise **transversale**, jamais vidée, pilote le **sevrage** seul |
| `src/naulthene/cerveau/noyau.py` | `_profil_carte` / `_parente_cartes` — parenté **lue sur la grille**, forme × vocabulaire (opaque), jamais tabulée |
| `src/naulthene/cerveau/noyau.py` | `facteur_guidage` — `poids = (1 − fraîcheur) × parenté` ; l'héritage **s'efface** quand la fenêtre se remplit |
| `src/naulthene/cerveau/noyau.py` | `--sans-heritage` : ablation pour témoin apparié |
| `src/naulthene/cerveau/persistance.py` | les deux grandeurs persistées (mesures de **vie**), lecture défensive |

**Mesure préalable** (15 niveaux × 40 resets) : la parenté entre voisins va de **0,85** à
**0,00**, **6 transitions sur 14** sont des ruptures — un report uniforme aurait été faux
six fois. En vol, g44 mesure **65 %** puis **55 %**, cohérent avec la mesure hors-ligne.

### Deux bugs corrigés (`35bb93b`)

- **L'ablation n'atteignait pas le module.** `python -m` charge le fichier sous deux noms ;
  `globals()` écrivait dans `__main__`, `facteur_guidage` lisait `naulthene.cerveau.noyau`.
  Témoin et variante étaient **le même run**. 2ᵉ occurrence du défaut que ce bloc dénonce.
  Assertion d'exécution ajoutée. **Campagne de 20 runs jetée.**
- **Télémétrie décalée** : héritage comparé entre début et fin de journée → jusqu'à
  **−33 pt** affichés sous ablation.

### Résultats — comparaison appariée définitive (8 × 2000 jours)

| Graine | Héritage | Témoin | Δ |
|---|---|---|---|
| g11, g22, g33 | niveau 1, 0 promo | niveau 1, 0 promo | **bit-identiques** |
| **g44** | niveau 3 — promos j477, **j493** | niveau 3 — promos j477, **j527** | **délai 16 j vs 50 j** |

| Question | Réponse mesurée |
|---|---|
| Change le **niveau atteint** ? | ❌ **Δ +0,00** sur 4 paires |
| Change le **nombre de promotions** ? | ❌ **Δ +0,00** |
| Change le **délai** entre paliers franchissables ? | ✅ **3,1× plus rapide** *(n = 1)* |
| Débloque un agent bloqué ? | ❌ **non** — jamais activé sur 3 graines /4 |
| L'ablation est-elle propre ? | ✅ **oui** — 3 runs strictement inchangés |

Autonomie moyenne en population : **26,1 % sur 20 runs** *(v41.2 : 0 % sur 300 j)*.

**Décision : conservé et actif** — il ne dégrade rien (deltas nuls, inerte sans
promotion), son seul effet mesuré est favorable, son coût est nul (aucune constante
posée). **Non revendiqué, rien dans les README** : l'effet repose sur **une graine**.

⚠️ **L'ablation est VIDE, pas négative** : sans promotion, la parenté n'est jamais
calculée, donc les deux branches exécutent le même code. Distinction déjà posée par
`CAMPAGNE_P17_ABLATION` — *« une ablation dont le témoin est à zéro ne mesure rien »*.

⚠️ **L'héritage ACCÉLÈRE, il ne DÉBLOQUE pas** — établi par conception et par mesure.
**Conservé, non revendiqué** : n = 1 favorable, zéro mesure appariée, **rien dans les
README**. Toute campagne future visant la promotion doit durer **≥ 1000 jours**.

⚠️ **Relecture de la v41.3** : à héritage nul le calcul est identique à v41.3 (vérifié par
`git diff`), or **4 graines sur 4** plafonnent à 55-65 % de maîtrise là où g42 atteignait
70 %. La promotion du jour 74 était **très probablement une loterie natale de plus**.

### 🔴 Découverte majeure — la maturité mélange deux instants (chantier §7)

`facteur_guidage` est calculé en **début** de journée sur la fenêtre de la **veille** ;
`_maturite_niveau` est évalué la **nuit** avec la maîtrise **du jour**. Le produit
`régularité × consolidation × autonomie` multiplie donc la **maîtrise d'aujourd'hui** par
l'**autonomie d'hier** — et sous-estime la maturité **exactement pendant les phases de
progression**, c'est-à-dire quand la promotion se joue.

**Preuve directe, 2000 jours :**

| | Maîtrise | Autonomie utilisée | Maturité | |
|---|---|---|---|---|
| **g44** | 60 % | 67 % *(synchrone)* | **0,400** | ✅ promu |
| **g11** | **65 %** | 61 % *(de la veille)* | 0,397 | ❌ refusé ×4 |

**Le moins compétent est promu, le plus compétent refusé.** Et g44 passe avec **0,400
pile** : `SEUIL_MATURITE` étant dérivé de `TAUX_PROMOTION` par la même formule que
l'autonomie, la marge est **nulle par construction** — un décalage d'un jour suffit.

Même motif que le verrou du §10 (v41.2) : deux constantes justes séparément dont la
composition se neutralise. **Correctif NON appliqué** — il modifie le critère de
promotion, donc arbitrage utilisateur (3 options consignées au §7.4).

**Coût chiffré** (rejeu du critère sur les 8 runs longs, §11) :

| Run | Promotions réelles | Si synchrone | **Manquées** |
|---|---|---|---|
| **g11** | **0** | **2** | **2** |
| g22 / g33 | 0 | 0 | 0 |
| g44 | 2 | 3 | 1 |

> 🎯 **Le « mur du niveau 1 » recouvrait DEUX phénomènes distincts** : un **défaut de
> mesure** (g11 remplissait la condition deux fois et a été refusé — 1 graine /4) et un
> **mur d'apprentissage réel** (g22, g33 plafonnent à 55 %, sous le seuil — 2 graines /4).
> Le blocage historique (**0 promotion sur 10 graines × 2000 jours**, cité dans les README
> et `CLAUDE.md`) a été mesuré avec ce même critère : **cette mesure doit être rejouée
> dessus avant d'attribuer le blocage à la cognition**. Chiffre = borne supérieure.

---

## [v41.3-experimental] - 2026-08-15 — Le sevrage proportionnel : deux promotions, puis le mur revient

### Le premier franchissement de palier du projet — et ce qu'il ne prouve pas

| Type | Details |
|------|---------|
| **Commit** | `2b042c0` |
| **Catégorie** | fix (expérimental) |
| **Impact** | Critique — **`noyau.py` uniquement** |
| **Branche** | `feat/v41-ligne-flottaison` |
| **Chantier** | [`CHANTIER_v41.2_energie_modulatrice.md`](../ameliorations/CHANTIER_v41.2_energie_modulatrice.md) §10 (diagnostic) et §11 (résultat) |

**Le §10 avait établi que la promotion était mathématiquement impossible** : la maturité
v40.2 est un **produit** (`régularité × consolidation × autonomie`), et `SEUIL_DEBUT_SEVRAGE
= 0.60` plaçait le début du sevrage exactement où `TAUX_PROMOTION = 0.60` exigeait la
promotion. À 60 % de maîtrise, l'autonomie valait encore **exactement 0** — donc la maturité
aussi, quelle que soit la performance.

Décision utilisateur : *« une autonomisation inversement proportionnelle au taux de
maîtrise »*.

| Fichier modifié | Changement |
|-----------------|------------|
| `src/naulthene/cerveau/noyau.py` | `SEUIL_DEBUT_SEVRAGE` **supprimée** ; `facteur_guidage` devient `1 − min(1, taux / SEUIL_FIN_SEVRAGE)` — l'aide décroît dès le premier point de maîtrise |
| `src/naulthene/cerveau/noyau.py` | `SEUIL_MATURITE` n'est plus posé mais **dérivé** : `TAUX_PROMOTION × min(1, TAUX_PROMOTION / SEUIL_FIN_SEVRAGE)` = 0,400 — soit ce qu'un agent tout juste promouvable peut atteindre |

### Résultat — run 300 jours, graine unique

| Jalon | Niveau | Maîtrise 50 derniers | Autonomie moy | Maturité max |
|---|---|---|---|---|
| 62 j | 1/15 | 35 % | 38 % | 0,336 |
| **117 j** | **2/15** | 41 % | 43 % | **0,467** |
| **215 j** | **3/15** | 6 % | 7 % | 0,469 |
| 300 j | 3/15 | **2 %** | 3 % | 0,469 |
| *v41.2 (témoin)* | *1/15* | — | **0 % / 300 j** | **0,000** |

**Première promotion au jour 74** — maturité 47 % (régularité 60 % × 20 épisodes ×
autonomie 78 %), fenêtre pleine, agent quasi sevré. Une seconde suit avant le jalon 215.

✅ **Verrou de MESURE levé** — maturité 0,000 → 0,469, deux paliers franchis.
❌ **Verrou de COMPÉTENCE intact** — au niveau 3, effondrement à 2 % de maîtrise, aucune
promotion sur les 185 derniers jours. Les deux promotions sont du **rattrapage** de
compétences déjà acquises, pas un apprentissage neuf.

> L'autonomie retombée à 3 % **n'est pas une régression** : le sevrage étant inversement
> proportionnel à la maîtrise, une maîtrise à 2 % doit produire un guidage maximal. Le
> mécanisme fonctionne ; c'est en amont que l'agent échoue.

⚠️ **Une graine ne prouve rien** — précédent g22 (niveau 4 en solo, invalidé comme loterie
natale par la campagne à 10 graines). **Rien n'entre dans les README** avant une campagne
≥ 10 graines. Le verdict « couper C2 = 0,0 pt » n'est pas affecté.

---

## [v41.2-fix5→fix8-experimental] - 2026-08-15 — Manger devient un acte, et le corps fait des réserves

### « C'est le corps qui pousse à manger pour vivre »

| Type | Details |
|------|---------|
| **Commits** | `0609beb`, `9c75d84`, `a149d53`, `32402ea`, `00298dc` |
| **Catégorie** | feat + fix (expérimental) |
| **Impact** | Fonctionnel — **`noyau.py` uniquement** |
| **Branche** | `feat/v41-ligne-flottaison` |

### fix5 — Manger était un effet de bord du déplacement

Marcher sur une case chargée consommait la ressource **automatiquement**. Un agent rassasié
qui traversait une pomme l'avalait et la gaspillait ; un affamé se nourrissait sans l'avoir
voulu.

> ⚠️ **Conséquence rétroactive** : la « récolte » mesurée dans tout ce chantier n'était pas
> un comportement de recherche mais une **conséquence mécanique des déplacements**. La
> lecture des chiffres de fourrage antérieurs est invalidée.

La consommation passe désormais par `ACTION_CONSOMMER` (le `pickup` de MiniGrid), l'action
la plus coûteuse du barème (0,8 contre 0,2 pour tourner). Aucun `if faim then manger` : le
geste reste une sortie de la tête motrice, apprise par le gradient.

### fix5bis — Le rythme métabolique est dérivé, plus posé

`REPAS_PAR_JOURNEE = 2.5` et `PRISES_HYDRIQUES = 4.0` avaient été posés puis recalibrés
**à la main trois fois**. Désormais :

```
budget_min   = cases_libres(carte la plus PAUVRE) × FRACTION_CASES_MAX
opportunités = budget_min × épisodes_par_journée
besoin/axe   = (opportunités / 2) / MARGE_SUBSISTANCE
```

⚠️ **Le sens de la dérivation compte.** Faire dépendre le besoin de la carte *courante*
donnerait un corps qui change de nature en changeant de pièce (`Empty-8x8` : 24 repas/jour).
Le métabolisme est une propriété de l'**espèce** — c'est donc la carte la plus pauvre qui
fixe le rythme.

> **Erreur consignée dans le code** : une première dérivation répartissait le besoin selon
> `RATIO_SOIF_SUR_FAIM`. Résultat : marge food ×2,86 mais **marge eau ×0,95** — le défaut
> corrigé la veille, reproduit par une *formule* au lieu d'un chiffre posé. **Une dérivation
> n'est pas une garantie de justesse.**

### fix6 — Le geste visait la mauvaise case

`pickup` agit sur la case **devant** l'agent ; le détecteur testait celle **sous ses pieds**.
Les deux ne coïncident jamais. Pire : MiniGrid retirait quand même la Ball pour la mettre en
`carrying`, donc la ressource disparaissait **sans nourrir ni repousser**.

| | avant | après |
|---|---|---|
| Efficacité du geste | **2,9 %** | **14,1 %** |
| Récolte | 2/jour | **10/jour** |

`carrying` est vidé après ingestion : sans quoi la main reste pleine et **tout `pickup`
suivant échoue** — un agent ayant mangé une fois ne pourrait plus jamais se nourrir.

### fix7 — Le soulagement n'était pas crédité au geste

`r_bio` était calculé (l. 6400) **avant** la consommation (l. 6449) et consommé dans la
récompense (l. 6551). Le soulagement tombait donc **au tick suivant**, sur une action sans
rapport : l'agent ne pouvait pas apprendre « ce geste-ci m'a soulagé ».

**La boucle corporelle est vérifiée** — le contraste existait déjà :

| État | Manger rapporte |
|---|---|
| **Affamé** (S=0,05 E=0,05) | **+0,7945** |
| Moyen | +0,1267 |
| **Rassasié** (S=0,95 E=0,95) | **−0,0227** |

Manger repu est **puni** (gain nul, geste coûteux). Contraste **15×**. Aucune règle
n'interdit de manger sans faim — le corps s'en charge.

### fix8 — La réserve (la graisse)

Le surplus au-dessus du plafond était **perdu** : un jour faste ne préparait pas un jour
maigre. Désormais il devient réserve, remobilisée en cas de manque. Deux rendements < 1
(stockage 0,8, mobilisation 0,9) : la réserve est utile sans être gratuite.

| Prévoyance | Réserve | Survie au jeûne |
|---|---|---|
| 0 jour faste | 0,00 | 433 ticks (1,1 j) |
| 3 jours fastes | 1,19 | 672 ticks (1,7 j) |
| 6 jours fastes | 2,29 | **806 ticks (2,0 j)** |

**Un agent prévoyant vit presque deux fois plus longtemps**, sans qu'aucune règle ne le
décrète. C'est aussi ce qui fait que deux agents mangeant autant, à des rythmes différents,
n'ont pas le même destin.

### ⚠️ Ce qui ne marche pas — l'agent n'apprend pas à viser

Run de 65 jours, cerveau neuf :

| | 20 premiers j | 20 derniers j |
|---|---|---|
| Gestes joués | 58/jour (**17 % des ticks**) | 58/jour |
| Efficacité | 12,4 % | **10,6 %** |

**Parfaitement plat.** Cause arithmétique : l'espérance du geste (**+0,033**) est du même
ordre que le bruit du tick (curiosité 0,01–0,05, micro-récompenses 0,04). Et **rater ne coûte
presque rien** → mitrailler est rationnel. Le problème n'est pas que le geste coûte trop peu,
c'est que **viser ne rapporte pas assez plus que mitrailler**.

> Le coût nominal de 0,8 est **dilué** : `METABOLISME_BASAL_PART = 0,65` fait que l'écart
> entre l'action la moins chère (0,1) et la plus chère (0,8) ne représente que **24 %** de
> variation sur la dépense réelle du tick.

### 🏁 Run de 300 jours terminé — et un verrou trouvé

| | témoin (300 j) | **v41.2 (300 j)** |
|---|---|---|
| **Victoires** | 130 | **231** (×1,78) |
| **Maîtrise max** | 30 % | **60 %** |
| Récolte/jour | 3,69 | **7,54** (×2,04) |
| Accord C1/C2 (50 derniers j) | 50,6 % | **84,6 %** |
| Niveau final | 1/15 | 1/15 |

### 🔒 LA PROMOTION ÉTAIT MATHÉMATIQUEMENT IMPOSSIBLE

La maîtrise a touché **60 %** — exactement `TAUX_PROMOTION` — deux fois, sans promotion.

```
maturité = régularité × consolidation × autonomie      (v40.2, un PRODUIT)
```

| Facteur | max sur 300 j |
|---|---|
| régularité | 60 % |
| consolidation | 100 % |
| **autonomie** | **0 %** |
| **→ maturité** | **0,000** (seuil : 0,38) |

**Dépendance circulaire entre deux constantes** : `SEUIL_DEBUT_SEVRAGE = 0.60` est le point
où le sevrage *commence*, et `TAUX_PROMOTION = 0.60` celui où la promotion est *exigée*. À
60 % de maîtrise, `autonomie = 1 − guidage` vaut donc encore **exactement 0** — il faut
~75 % pour qu'elle devienne non nulle. L'aide est restée **pleine 300 jours sur 300**.

> ⚠️ Le commentaire du code le disait déjà (l. 4623) : *« le sevrage n'a pas commencé, donc
> l'autonomie y est nulle par construction »* — écrit, jamais confronté au seuil de
> promotion. **4ᵉ occurrence du fil n°3 de l'INDEX.**

**Conséquence pour la campagne v41** : le blocage au niveau 1/15 sur 10 graines × 2000 jours
doit être relu — aucune de ces graines ne *pouvait* être promue, quelle que soit sa
performance. Le « mur du cursus » n'était peut-être pas un mur de compétence.

**Non corrigé** — trois options possibles, aucune neutre, arbitrage utilisateur requis (voir
[chantier §10.4](../ameliorations/CHANTIER_v41.2_energie_modulatrice.md)).

### 📈 Signal à confirmer

À jour égal contre le témoin : **83 victoires contre 26** (j61), récolte **7,4/jour** contre
2,0, et **accord C1/C2 à 80,1 %** au jalon 101 — contre **0,5 %** sur toute la campagne v41
et **0 %** en v37.

⚠️ **Une seule graine.** La campagne v41 a montré qu'une graine peut réussir seule par
loterie natale. À confirmer sur ≥ 10 graines avant toute conclusion.

---

## [v41.2-experimental] - 2026-08-15 — Le métabolisme à deux étages (EN COURS)

### « L'énergie module tout — et la faim s'indexe sur elle, pas seulement sur le ventre »

| Type | Details |
|------|---------|
| **Commits** | `4c85452`, `84ee828`, `95fdb31`, `b33f3dd`, `cb61f7f` |
| **Catégorie** | feat (expérimental) |
| **Impact** | Fonctionnel — **`noyau.py` uniquement**, `colab.py` inchangé |
| **Branche** | `feat/v41-ligne-flottaison` |
| **Chantiers** | [métabolisme](../ameliorations/CHANTIER_v41.2_metabolisme_deux_etages.md) · [énergie modulatrice](../ameliorations/CHANTIER_v41.2_energie_modulatrice.md) |

⚠️ **CALIBRAGE NON VALIDÉ — ne pas porter sur `colab.py`.** La mécanique est vérifiée,
le barème ne l'est pas (voir « ce qui bloque » plus bas).

### Ce qui est livré et vérifié

| Mécanique | Vérification |
|---|---|
| **Deux étages** — satiété = *stock*, énergie = *flux* | l'estomac plein avec l'énergie basse devient représentable |
| **Mort par insolvabilité, sans aucun `if`** | repos sans manger → mort t=411 ; activité sans manger → t=319. Le repos **retarde** sans prévenir |
| **Seuil non linéaire** `vigueur = énergie ** κ` | à mi-énergie C1 garde 25 % de sa voix, **C2 seulement 6 %** — la délibération s'éteint avant le réflexe |
| **Invariant d'échelle** 400 ↔ 3600 ticks | E_moy 0,929 vs 0,928 — **écart < 1 %** |
| **Bornes dérivables** `norme × exp(dérive)` | sur 1200 nuits la dérive **sature** (+24 % monde dur, +14,5 % monde moyen), ne diverge jamais |
| **Profils à 3 axes + coût de digestion** | eau : +0,700 hydratation, 0 calorie · nourriture : +0,700 satiété, **−0,133 énergie** |
| **Faim indexée énergie × satiété** | corrige un agent qui cherchait de l'eau à `énergie 0,015` parce que son ventre était à 0,70 |

`VIGUEUR_PLANCHER` est indispensable : sans lui, `vigueur → 0` annule C1 **et** C2, les
logits deviennent tous nuls et l'action **aléatoire**. Un mourant doit rester cohérent.

⚠️ Le couplage à C2 **n'est pas** le court-circuit refusé en v29.0 : C2 est toujours
sollicité à chaque tick, seul son **poids** varie. Pas de branche, un facteur.

### Quatre défauts trouvés PAR la mesure

1. **Double comptage du stock** — la satiété se vidait par décroissance *et* par digestion : un repas finançait 59 ticks au lieu de 133.
2. **Valeur nutritive en dur (0,4)** — l'agent mourait *le ventre à moitié plein*, satiété bloquée à 0,392.
3. **Cofacteur hydrique linéaire** — sous 50 % d'hydratation, bilan négatif **quoi que l'agent mange**.
4. **Portion unique partagée entre les axes** — 2,0 unités d'eau perdues par débordement/jour ; corrigé en dérivant chaque axe de sa propre perte (**÷28**).

### 🐛 Bug préexistant corrigé (hors périmètre)

Les compteurs de calibrage v34 (`jauge_min_*_jour`, `ticks_deficit_critique_jour`,
`effort_*_jour`, `ressources_vues_jour`) n'étaient **jamais réarmés** entre les journées.
`jauge_min_satiete_jour` était donc le minimum **depuis la naissance**.

> C'est ce qui produisait les « **400/400 ticks en zone critique** » de tous les runs de la
> campagne : le chiffre **surestimait la détresse réelle du jour**. Le commentaire d'origine
> invoquait pourtant *« le piège du bug `score_vocal_jour` v27.0 »* — **3ᵉ occurrence du
> fil n°3** de l'INDEX.

### ⚠️ Ce qui bloque — et deux erreurs de diagnostic consignées

Taux de récolte réel, 60 premiers jours, trois runs :

| Version | sources/carte | consommé/jour |
|---|---|---|
| témoin | 20 | **3,72** |
| profils | 35 | **3,52** |
| + hydrique découplé | 35 | **3,47** |

**Le nombre absolu consommé est identique.** Multiplier les sources par 1,75 n'a rien
changé : l'agent rate ~90 % des opportunités.

1. **« Le déficit est structurel, le monde est trop pauvre »** — **faux**. +75 % de sources
   → 0 % de récolte en plus. Le monde n'était pas le facteur limitant.
2. **Le simulateur postulait la réponse** — les calibrages ont été validés sur un modèle qui
   **suppose l'agent mangeant à intervalles réguliers**, alors qu'il mange quand il trébuche
   sur une ressource. *Ne calibrer un métabolisme qu'avec une trace de run réel.*

La cause réelle est **comportementale** : besoin 6,5/jour contre une capacité de récolte de
~3,5/jour, invariante. Cohérent avec les 48,6 % d'approche olfactive (= le hasard, H15) et
l'odorat mesuré **inerte** à l'ablation.

---

## [v41.0-docs] - 2026-08-15 — Les README disent enfin ce que les mesures disent

### « Couper C2 double le taux de succès » → **0,0 point sur 6 niveaux**

| Type | Details |
|------|---------|
| **Commit** | `89ac5ad` |
| **Catégorie** | docs (**aucune ligne de `src/` modifiée**) |
| **Impact** | Documentation — corrige une affirmation fausse de la vitrine publique |
| **Branche** | `feat/v41-ligne-flottaison` |
| **Carnet** | [CAMPAGNE_v41_population_et_ablation_aout_2026.md](../recherche/CAMPAGNE_v41_population_et_ablation_aout_2026.md) |

Application de la **règle de miroir** (CLAUDE.md §2bis) : `readme.md` (EN) et `readme_fr.md`
(FR) modifiés **dans le même commit**, mêmes chiffres des deux côtés.

### Ce qui était faux

| Affirmation publiée | Mesure réelle (78 cellules) |
|---|---|
| « Couper C2 **double** le taux de succès » (4,50 % → 10,67 %) | **0,0 point sur les 6 niveaux** |
| « Le système délibératif est *activement nuisible* » | ni nuisible ni utile — **causalement déconnecté** |
| Table d'ablation : 13 lésions × 5 niveaux, **témoin 4,50 %** | 13 × 3 × 2 cerveaux, témoins **8,7 % à 46,7 %** |
| Bloqué au **niveau 2/15**, 678 jours sans victoire | **niveau 1/15**, 10 graines × 2000 j, **0 promotion** |
| « 0 sur **8** mécaniques testées » | **0 sur 9** |

L'ancien chiffre venait d'un banc dont le témoin était à 4,50 % — et dont plusieurs cellules
avaient un **témoin à 0 %**, ce qui ne mesure rien : aucune lésion ne peut faire baisser un
score déjà au plancher. L'effet « ×2 » était porté presque entièrement par `Empty-8x8`
(1,7 % → 22,5 %), donc par du bruit sur un plancher.

### Ce qui est publié maintenant

| Fichier | Changement |
|---|---|
| `readme.md` | table d'ablation **78 cellules** (Δ par niveau, 2 cerveaux) + note de protocole sur le témoin non nul + état du blocage réécrit + ligne baseline `Empty-8x8` → `Empty-5x5` 44,7 % |
| `readme_fr.md` | **miroir strict** des mêmes blocs |
| `docs/recherche/recherche_bug_or_not_bug.md` | **H15 tranchée** — « les sens sont-ils utilisés ? » → non, 4 sur 6 sont inertes |
| `docs/recherche/CAMPAGNE_P17_ABLATION_aout_2026.md` | §« suite donnée » — la **Lecture 2** (« C2 change de signe selon la carte ») est **contredite** : c'était du bruit sur témoin au plancher |
| `docs/INDEX.md` | pointeurs mis à jour |

⚠️ **Une lecture antérieure est explicitement contredite.** La campagne P17 concluait que
« C2 change de signe selon la taille de la carte ». Sur témoin non nul, C2 ne change rien du
tout, sur aucun niveau. La contradiction est consignée dans les deux carnets plutôt que
corrigée en silence.

---

## [v41.0-campagne] - 2026-08-15 — La campagne qui infirme le résultat v41

### « 0 promotion sur 10 graines — et C2 est débranchable sans effet »

| Type | Details |
|------|---------|
| **Commit** | `89ac5ad` |
| **Catégorie** | docs (campagne de mesure, **aucune ligne de `src/` modifiée**) |
| **Impact** | Critique — infirme le résultat mis en avant en v41.0 |
| **Branche** | `feat/v41-ligne-flottaison` |
| **Carnet** | [CAMPAGNE_v41_population_et_ablation_aout_2026.md](../recherche/CAMPAGNE_v41_population_et_ablation_aout_2026.md) |

**20 000 jours simulés (10 graines × 2000 j) + 78 cellules d'ablation.**

### Le déblocage de g22 n'est pas reproductible

L'entrée v41.0 ci-dessous annonce « le premier franchissement de palier du projet »
(g22 → niveau 4/15) sur **3 graines**. La campagne de 10 graines fraîches, même code,
tranche :

| | v41 (3 graines) | **Campagne (10 graines)** |
|---|---|---|
| Niveau max atteint | **4/15** | **1/15** |
| Promotions | 1 graine | **0** |
| Maîtrise max (seuil : 60 %) | — | **40 %** |
| Victoires cumulées | — | **7 602** |

Le taux de déblocage n'est donc pas « 1 sur 3 » mais au plus **1 sur 13**. Le succès de
g22 était un tirage favorable de la **loterie natale** — l'ambiguïté flaguée en §10.3 du
chantier est levée, dans le mauvais sens. Face à l'étalon V40 : **match nul**.

### Le réveil de C2 est décoratif — deux mesures indépendantes

**Ablation** : `c2_coupe` et `c2_horizon_court` donnent **+0,0 sur les 6 niveaux**, deux
cerveaux, 300 épisodes/cellule. Douze mesures, douze zéros exacts.

**Population** : l'accord C1/C2 s'éteint sur la durée.

| Jalon | 500 | 1000 | 1500 | **2000** |
|---|---|---|---|---|
| Accord médian | **37 %** | 21 % | 4 % | **0,5 %** |

Le gain le plus visible de la v41 (37 % contre **0 % historique**, cf. chantier v37) est
un **transitoire de 500 jours** qui retourne au niveau d'avant-correctif. C2 revit dans
les métriques — amplitude, ratio, non-extinction — **sans peser sur les actes**.

### Six lésions sur treize ne changent rien

`ouie_coupee`, `gout_coupe`, `exo_coupe`, `c2_coupe`, `c2_horizon_court` : **+0,0 × 6**.
`odorat_coupe` : +0,0 × 5. Quatre des six sens sont coupables sans conséquence.

Portent réellement quelque chose : le **toucher** et le **vecteur bio**, dont l'effet
grandit avec la difficulté (bio : −4,4 sur `Empty-5x5` → **−8,0** sur `Longue distance`).
La **vue est instable** (aide sur 3 niveaux, nuit sur 3).

⚠️ **Les trois mémoires sont plutôt nuisibles** : `hippocampe_fige` et
`episodique_coupe` **améliorent** le score sur 4 niveaux sur 6 (jusqu'à **+4,7**). Seule
exception nette : `spatiale_coupee` coûte **−7,4** sur `Primaire 3 (Ramasser)`.

### Le découplage victoires / progression

g111 : **1346 victoires → 15 %** de maîtrise. g909 : **409 victoires → 30 %**. Le nombre
de succès ne prédit ni la maîtrise ni le vécu — le mur du cursus est la **régularité**
sur la fenêtre de 20 épisodes, pas le volume.

Trois variables sont mortes au terme du run : `envie` (**1,0000 sur 10/10** depuis j263),
`danger` (**676 sur 9/10** à l'unité près), accord C1/C2 (0 % sur 7/10). Septième
rencontre du **fil n°2** de l'INDEX.

### ⚠️ Une affirmation des README est fausse

Les deux README affirment que **« couper C2 double le taux de succès »**. Mesure :
**0,0 point d'écart sur 6 niveaux**. À corriger des deux côtés dans le même commit
(règle de miroir) — **non fait dans ce commit**, en attente d'arbitrage utilisateur.

### Note de méthode — trois lectures révisées en cours de campagne

Consignées dans le carnet : g606 lu comme « seconde solution stable » (c'était un
décrochage), `danger` lu comme « saturé à 541 » (le plafond monte : 541 → 631 → 676), et
g111 lu comme « seule trajectoire ascendante » à 50 % (fluctuation — redescend à 15 %).

> **Sur une métrique à fenêtre glissante, un jalon isolé ne porte pas de tendance.**
> Même défaut que la projection d'envie démentie en v41.

**9ᵉ mécanique cognitive testée, 9ᵉ sans apport démontré.**

---

## [v41.0-experimental] - 2026-08-14 — La ligne de flottaison métabolique

### « Le zéro n'est pas 0.0, c'est le coût incompressible d'un organisme vivant »

| Type | Details |
|------|---------|
| **Commit** | `04080c4` |
| **Catégorie** | fix critique |
| **Impact** | Critique — C2 passe de mort (2000 nuits/2000) à dominant (ratio 1,41×) |
| **Branche** | `feat/v41-ligne-flottaison` |
| **Chantier** | [CORRECTIFS_v41_ligne_de_flottaison.md](../ameliorations/CORRECTIFS_v41_ligne_de_flottaison.md) |

**Le vécu se compte en SAILLANCES au-dessus du coût d'exister, plus en moyenne.**

### Le défaut — mesuré, pas supposé

Benchmark « C1 pur » (3 graines × 2000 jours). Journée type de g11, reconstituée
depuis les logs :

| Terme | Valeur |
|---|---|
| `r_bio` cumulé sur 400 ticks | −2,30 |
| victoires (0,46/jour × 1,0) | +0,46 |
| **somme de la journée** | **−1,84** |
| ÷ 400 ticks | −0,004593 |
| ÷ référence de choc (0,208) | −0,0221 |
| → apport **OKAY** | **0,0000** ← un jour AVEC victoire |
| → apport **DANGER** | 0,0221 |

Le modèle prédisait `f = 0,0028` ; le run affichait **0,003**. Reproduction au
millième — la cause était établie sans ambiguïté.

> « En moyennant 399 ticks d'effort continu avec 1 tick de victoire, on forçait
> l'algorithme à conclure que **vivre est une punition**. »

`r_bio` est une **dérivée de déficit** (`deficit_avant − deficit_apres`), donc
structurellement négative dès que les jauges dérivent vers zéro. Sans zéro de
référence, exister coûte — donc exister est un danger.

### Pourquoi corriger l'opérateur seul ne suffisait pas

Mesuré **avant** implémentation : sommer sans flottaison est *pire* que moyenner.

| opérateur | okay (avec victoire) | danger | okay (sans victoire) |
|---|---|---|---|
| moyenne (v40) | 0,0000 | 0,0146 | 0,0000 |
| somme nue | 1,0000 | 1,0000 | **0,2503** ← inutilisable |
| somme au-dessus flottaison | 1,0000 | ~1,0 | **0,0209** |

La saturation venait du **NOMBRE** (198 ticks négatifs contre 1 victoire), pas de
l'intensité. Les correctifs C1 et C2 du chantier ne sont donc **pas dissociables** —
arbitrage utilisateur, option B.

### Ce qui est livré

| Fichier modifié | Changement |
|-----------------|------------|
| `src/naulthene/cerveau/noyau.py` | `nourrir_vecu_journee` : somme des saillances au-dessus de la flottaison ; flottaison dérivée à cliquet ; demi-vies d'oubli recalibrées |
| `src/naulthene/cerveau/persistance.py` | `flottaison_metabolique` sérialisée (`None` traverse tel quel) |

1. **Flottaison DÉRIVÉE, jamais posée** — médiane des `|r|` du jour, mesurée stable à
   **0,00574 ± 0,00026** sur 200 jours (amplitude 23 %). Médiane et non moyenne : la
   moyenne serait tirée par la victoire elle-même (+1,0 pèse autant que 176 ticks
   ordinaires) — même raison que le 3ᵉ quartile de `echelle_myeline` (v37.0).
2. **Cliquet de flottaison** — montée 2 %/nuit, descente 50× plus lente. Sans lui une
   famine prolongée ferait *descendre* la ligne vers la famine, normalisant l'agonie
   comme état ordinaire : le défaut de `norme_naissance` à l'identique.
3. **Demi-vies d'oubli recalibrées.** `OUBLI_DANGER = 0,99990` avait une demi-vie de
   **6931 jours** : sur un run de 2000 jours l'oubli n'existait pas, d'où la croissance
   **linéaire** observée (pente encore +0,096/j au jour 1800). Le cliquet n'était pas
   asymétrique, il était **inopérant des deux côtés**. Désormais en demi-vies
   explicites : 300 j / 500 j (asymétrie ×1,7).

### Résultat — run test 300 jours, graine 11

| | V40 (2000 j) | **V41 (300 j)** |
|---|---|---|
| `vecu_okay` | 0,04 | **211,50** |
| `vecu_danger` | 186,02 | 245,61 |
| **force planif.** | 0,000 | **0,462** |
| **envie** | 0,0000 💀 | **1,0000** 🔥 |
| C2 | 0,000 | **1,425** |
| ratio C1/C2 | 0,00× | **1,41×** |
| erreur JEPA | 0,0116 | **0,0035** |

**C2 est mort 1 nuit sur 300** — contre 2000 sur 2000 en V40. Le rapport de force
s'est même inversé : C2 parle désormais plus fort que C1, et ça se stabilise dès le
jour ~30 (ratio 0,96×–1,32× sur tout le run).

### ✅ Le run long a tranché — 2000 jours × 3 graines

**Le premier franchissement de palier du projet.** Zéro graine V40 n'a quitté le
niveau 1 en 2000 jours ; **g22 atteint le niveau 4** et y tient 1223 jours.

| | V40 (étalon) | **V41** |
|---|---|---|
| Niveau max (3 graines) | **1/15** | **4/15** |
| Victoires g11 | 774 | **1266** (+64 %) |
| force | 0,000–0,002 | 0,370–**0,724** |
| envie | 0,0000 sur les 3 | 0,46–**1,00** |
| C2 mort | **2000 nuits/2000** | ~0 |

**La promotion est un DÉBLOCAGE, pas une montée** : jour 770 → niv. 2, jour 775 →
niv. 3, jour 778 → niv. 4, puis plus rien pendant 1223 jours. Trois paliers en 8 jours
après 769 jours de plateau — la compétence était là bien avant, il manquait le seuil.

### ⚠️ La loterie natale — le résultat le plus dérangeant

Les trois graines partent du **postulat strictement identique**. La divergence est
visible dès la **nuit 1** : g22 a eu une première nuit **sans aucun danger** (zéro, pas
« peu ») et sa 1ʳᵉ victoire au jour 2 contre 6–7 pour les autres. **Au jour 50, l'écart
de `danger` est déjà de 38×** (1,28 contre 41–48).

Le mécanisme s'auto-entretient : carte facile → danger bas → force haute → C2 délibère
→ C2 fait gagner → force encore plus haute. Et symétriquement pour g33, qui s'éteint
(C1 = 6,788 contre C2 = 0,567). **Les demi-vies rendent la divergence quasi
irréversible** — un danger accumulé au jour 50 met 500 jours à s'effacer de moitié.

> La boule de neige demandée en v40.1 fonctionne dans les deux sens, comme spécifié.
> Mais **la trajectoire se joue dans les 50 premiers jours** : on mesure aussi une part
> de chance natale. `PRUDENCE_NAISSANCE = 1,0` ne pèse rien face à 38×.
>
> **Campagne de 10 graines lancée** (14/08, 19h35) pour savoir si 1/3 est le taux réel.
> Détail complet : [chantier §10.3](../ameliorations/CORRECTIFS_v41_ligne_de_flottaison.md).

### Note de méthode — une projection démentie

La projection annonçait une envie stabilisée à **0,11–0,20**, donc sous le critère
fixé (> 0,30). Mesure : **1,0000**. L'erreur venait d'une hypothèse `lucidité ≈ 0,99`
alors qu'elle vaut **0,574** — la lucidité est le produit `compréhension_C2 ×
expérience_C1`, et C1 s'étant affaibli relativement, le second terme reste bas.
L'érosion (`0,02 × 0,574 = 0,0115`) est donc battue par l'apport (`0,03 × 0,462 =
0,0139`). *La foi n'avait pas besoin d'atteindre 0,66 : il suffisait que la lucidité
reste modérée.*

---

## [v40.1-fix3/fix4-experimental] - 2026-08-14 — La chasse aux branches

### « Rien en dur et pas de If / Else — sauf si c'est lié à la mesure »

| Type | Details |
|------|---------|
| **Commit** | `89ac5ad` |
| **Catégorie** | refactor + feat |
| **Impact** | Critique — 3 interrupteurs cognitifs deviennent continus |
| **Branche** | `feat/v40.1-envie-de-vivre` |

Audit complet du chemin cognitif : **9 branches supprimées**, chacune avec son équivalence
prouvée numériquement.

### Les six réécritures à comportement IDENTIQUE

| Site | Avant | Après | Équivalence |
|---|---|---|---|
| plasticité nocturne | `if teneur >= NEUTRE` | `clip(rampe)` | 10 001 pts, **0.0** |
| tri du signe (vécu) | `if bilan >= 0` | `(\|b\|±b)/2` | 200k tirages, **0.0** |
| garde journée vide | `if not valeurs` | `max(len,1)` | exact |
| cliquet réf. choc | `A if monte else B` | `max(Δ,0)/min(Δ,0)` | 200k tirages, **0.0** |
| clip guidage | `if _g < 1.0` | `min(_g, 1.0)` | 200k tirages, **0.0** |
| sevrage (3 marches) | `if/elif/elif/else` | `clip` unique | 134k combinaisons, **0.0** |

Toutes étaient des **saturations déguisées** : un `if x >= BORNE: MAX else: rampe` est un
`clip` écrit en deux lignes, qui laisse croire à deux régimes cognitifs.

### ⚠️ Les trois interrupteurs cognitifs — comportement CHANGÉ

Ceux-là pilotaient une faculté par `if mode_libre` — de 0 à 100 % au franchissement du
palier 5.

**1. La falaise du guidage.** `recompense_continue` est désormais multipliée par
`min(facteur_guidage, 1)`, qui tend continûment vers 0 avec la maîtrise **mesurée**. Le
retrait de l'aide **émerge de la compétence** — un agent au-delà du palier 5 qui ne
maîtrise pas **garde son aide**. C'est le défaut chiffré par le diagnostic v35.1 (*0,00
record de proximité par jour pendant 2 000 jours*).

**2. La curiosité JEPA.** Toujours évaluée, pondérée par `acceptation()`. Un débutant a une
curiosité quasi nulle comme dans l'ancien mode guidé, un agent mûr la déploie comme dans
l'ancien mode libre — **et un agent qui a perdu l'envie cesse d'être curieux**, ce que
l'interrupteur ne pouvait pas exprimer.

**3. Le sursaut de volonté.** Le déclenchement reste discret (c'est une action) ; son
**ampleur** suit l'envie. À envie nulle, le sursaut se déclenche mais ne porte rien.

### Ce qui reste, et pourquoi

Sur 482 `if`, ceux du chemin cognitif sont des **gardes techniques** (`is None` distingue
« aucune donnée » de « mesuré à zéro »), des **actions discrètes** (une promotion n'a pas
de demi-mesure), des **sélections de source** (`if doorkey_actif` choisit *où lire*) ou des
**planchers d'opération**. Aucun n'est un seuil de décision.

⚠️ `SEUIL_PALIER_MODE_LIBRE` existe encore mais **ne pilote plus aucune faculté** — seulement
l'affichage. Neutralisé, pas supprimé.

**Non-régression** : grille des 5 scénarios identique (0.0000 / 0.0336 / 1.0000 / 1.0000 /
1.0000). Run réel 40 jours, **0 erreur**.

---

## [v40.1-experimental] - 2026-08-14 — L'Envie de Vivre (le couplage C1 ↔ C2)

### « L'envie de vivre pousse au maximum à essayer quand même »

| Type | Details |
|------|---------|
| **Commit** | `89ac5ad` |
| **Catégorie** | feat |
| **Impact** | Critique — module TOUTES les décisions |
| **Branche** | `feat/v40.1-envie-de-vivre` |
| **Portée** | `noyau.py` uniquement — `colab.py` **non touché** |
| **Chantier** | [CHANTIER_v40](../ameliorations_appliquees/CHANTIER_v40_planification_emergente.md) |

**La v40 répondait à « est-ce que je planifie ? ». La v40.1 répond à « est-ce que je
TENTE ? ».** Un agent peut savoir délibérer et refuser d'agir — rien dans le cerveau ne
portait cette question.

### Le mécanisme : la compétence produit sa propre paralysie

Deux forces opposées, appliquées comme des **facteurs** (jamais des termes) :

| Force | Composition | Effet |
|---|---|---|
| **Lucidité** ↓ | compréhension de C2 × expérience de C1 | « je VOIS le risque » |
| **Foi** ↑ | $f_{planif}$ (v40) | « mais ça a marché » |

Un débutant fonce parce qu'il **ignore** le danger ; un expert hésite parce qu'il le
**voit**. L'envie de vivre est ce qui l'en empêche.

**L'envie n'est pas un troisième module** : c'est le **couplage** entre C1 et C2 —
`acceptation() = envie × confiance` module les trois leviers de décision.

### Multiplicatif, jamais une moyenne

Trois propriétés demandées qu'une moyenne détruirait : effet **boule de neige**,
**inversion** possible, et les deux réservoirs qui **coexistent**. La croissance
exponentielle **émerge de la composition** — il n'y a aucun `exp()` dans le code.

### ⚠️ Aucun plancher (décision utilisateur explicite)

L'envie peut atteindre **zéro** et l'agent s'y figer définitivement. **Certains runs
mourront** — c'est un résultat du modèle, pas un bug. Une variable qui ne peut pas
atteindre zéro ne mesure pas la perte de foi.

### Où l'envie agit — sur toutes les décisions

| Levier | Effet |
|---|---|
| Poids de C2 | `force_planification = acceptation` |
| Exploration | `coeff_entropie` suit l'envie — la bascule 0.02/0.06 devient un **continuum** |
| Patience | `× (0.5 + 0.5 × envie)`, borné par `PATIENCE_MIN` |

### ⚠️ Deux défauts trouvés pendant l'implémentation

**fix1 — zéro était absorbant.** En purement multiplicatif, un agent tombé à 0,0001 puis
redevenu performant remontait à… 0,0001. L'inversion était nominalement vraie et
pratiquement impossible. **Correctif** : un terme additif $\propto \text{foi}^2$, qui ne
dépend pas de l'état courant. Mesuré : `0,0038 → 1,0000` en 150 nuits. Ceci ne réintroduit
**pas** de plancher — envie = 0 reste stable tant que la foi est nulle.

**fix2 — l'agent le plus désespéré était immunisé.** L'expérience de C1 était rapportée à
`vigueur_min_c1(f)` ; avec `vecu_okay = 0` la cible valait 0, donc lucidité nulle. Mesuré :
envie à **1,000000** après 1 000 nuits sans la moindre réussite. **Correctif** : échelle
`AMPLITUDE_C2_NORMALISEE` — l'expérience de C1 est une propriété de C1.

### Grille de validation (1 000 nuits par scénario)

| Scénario | Envie | Verdict |
|---|---|---|
| désespéré | 0,0000 | ✅ meurt |
| compétent, foi faible | 0,0336 | ✅ s'éteint |
| compétent, qui réussit | 1,0000 | ✅ survit |
| ignorant (JEPA mauvais) | 1,0000 | ✅ n'a pas peur |
| C1 encore neuf | 1,0000 | ✅ n'a pas peur |

| Fichier modifié | Changement |
|-----------------|------------|
| `src/naulthene/cerveau/noyau.py` | `envie_de_vivre`, `acceptation()`, `reviser_envie_de_vivre()` ; branchement sur entropie + patience + poids C2 ; ligne console `Envie v40.1` ; 6 clés W&B |
| `src/naulthene/cerveau/persistance.py` | `envie_de_vivre` sérialisée — défaut 1.0, un `.brain` antérieur repart entier |

---

## [v40.0-experimental] - 2026-08-14 — La Planification Émergente

### « C1 a toujours raison, sauf si C2 estime que le bénéfice dépasse le risque »

| Type | Details |
|------|---------|
| **Commit** | `89ac5ad` |
| **Catégorie** | feat |
| **Impact** | Critique — change le chemin de décision |
| **Branche** | `feat/v40-planification-emergente` |
| **Portée** | `noyau.py` uniquement — `colab.py` **non touché** |

**`force_planification` n'est plus une constante. Elle est la fraction du vécu que l'agent
a trouvée bénéfique.**

$$f_{planif} = \frac{\text{OKAY}}{\text{OKAY} + \text{DANGER} + \text{PRUDENCE\_NAISSANCE}}$$

OKAY et DANGER sont les sommes pondérées des récompenses internes **réellement ressenties**
(positives / négatives). Rien n'est déclaré : l'agent ne sait pas ce qu'est une victoire,
il sait qu'il a ressenti *n* fois du bon et *m* fois du mauvais.

### Trois constantes supprimées

| Constante | Valeur | Ce qu'elle décrétait |
|---|---|---|
| `FORCE_PLANIFICATION_GUIDE` | 0.5 | le poids de C2 en mode guidé |
| `FORCE_PLANIFICATION_LIBRE` | 0.85 | le poids de C2 en mode libre |
| `RATIO_C1C2_VISE` | 2.0 | « C2 doit peser 2× C1 » — sans aucune mesure |

`VIGUEUR_MIN_C1` devient la fonction `vigueur_min_c1(f)` = `AMPLITUDE_C2_NORMALISEE × f` :
la **parité**, seul point de référence non arbitraire. Le rapport de force n'est plus
décrété, il est une **conséquence** de l'expérience.

**Ce qui a motivé la suppression** : l'ablation du 14/08 a montré que couper C2 **multiplie
le succès par 4,5 sur `DoorKey-5x5` mais l'annule sur `8x8`**. Aucune valeur unique ne peut
être juste — une constante qui devrait dépendre du contexte était figée pour tous.

### Le cliquet (repris de v37.1-fix1)

`OUBLI_OKAY = 0.9995` / `OUBLI_DANGER = 0.99990` — le danger s'efface **~5× plus lentement**.
Sans cette asymétrie, un agent traversant une mauvaise passe verrait `f` s'effondrer et
perdrait sa planification précisément quand il en a le plus besoin.

### ⚠️ Défaut trouvé et corrigé pendant l'implémentation

La première version branchait `nourrir_vecu` sur `chocs_dopamine_journee`. **Erreur** :
`poids_evenement` est une **intensité**, toujours positive (la distillation v37.1 ne
s'intéresse qu'à « à quel point c'était marquant »). Mesuré sur 10 jours : `danger` restait
à **0,00 exact** et `f` saturait à **0,97** — l'agent ne pouvait jamais enregistrer un échec.

Source corrigée : `recompenses_journee`, la grandeur **signée**.

> **Leçon** : le DANGER exige une grandeur qui peut être négative. Une intensité ne porte
> pas de jugement.

| Fichier modifié | Changement |
|-----------------|------------|
| `src/naulthene/cerveau/noyau.py` | `force_planification_vecue()`, `nourrir_vecu()`, `vigueur_min_c1()` ; 3 constantes supprimées ; métrique `accord` corrigée (`.all()` → moyenne) ; ligne console `Planif. v40` ; 3 clés W&B |
| `src/naulthene/cerveau/persistance.py` | `vecu_okay` / `vecu_danger` sérialisés — `.get(…, 0.0)`, un `.brain` antérieur repart à f=0 sans greffe |
| `src/naulthene/instruments/sonde_c1_c2.py` | lit la force **vécue** au lieu de la constante supprimée |

### 🐛 Correctif joint — la métrique d'accord C1/C2 était fausse

`noyau.py:868` fermait sur `.all()` : l'accord ne valait 1 que si les **400 ticks** du batch
votaient la même action. Une seule divergence écrivait 0 — **le résultat était garanti à 0 %
par construction**.

| Source | Accord mesuré |
|---|---|
| Log de nuit (avant) | **0,0 %** |
| Banc d'ablation (par tick) | **26 à 31 %** |

Ce 0 % circulait depuis le chantier v37 et faisait paraître le désaccord total. Le désaccord
réel est de ~70 %. **Défaut de mesure, pas de cognition** — aucune décision ne change.

---

## [v39.0-experimental] - 2026-08-13 (nuit) — L'abstraction s'émancipe de l'espace

### Le QUOI survit au OÙ — et `noyau.py` entre enfin dans git

| Type | Details |
|------|---------|
| **Commit** | `89ac5ad` |
| **Catégorie** | chore (versionnement) + fix (mémoire, audio, télémétrie) |
| **Impact** | **Critique** — premier correctif issu d'une mesure directe, et fin du risque structurel n°1 |
| **Branche** | `feat/v39-memoire-abstraite` |

**🔴 `noyau.py` est désormais VERSIONNÉ.** Le fichier était gitignoré depuis l'origine et
portait à lui seul toute l'évolution **v34 → v37.1** : 369 Ko, quatre mois de mécaniques, en
**un exemplaire sur un disque**. Les carnets *décrivent* ces mécaniques, ils ne permettent pas
de les *reconstruire*. Risque signalé dans `ETAT_DU_PROJET_aout_2026.md` §5.2 puis
`AVIS_ET_PROPOSITIONS_aout_2026.md` (P1) — il est clos. La **nature** du fichier ne change pas :
il reste le terrain d'essai, `colab.py` reste la référence, le portage reste à faire.

---

**🧬 Correctif 1 — l'empreinte de type (le QUOI qui survit au OÙ).**

Mesuré par run instrumenté (300 jours, graine 22) :

```
[ECRIT goal] tick=22091 pos=(1,2) int=1.0035
[ECRIT goal] tick=22142 pos=(1,3) int=1.0119
🎓 [PROMOTION] L'Agent passe en DoorKey 6x6 !
→ .brain sauvegardé juste après : ZÉRO repère `goal`
```

**4 repères `goal` écrits, 3 promotions, 0 survivant, 0 jamais confirmé une seule fois.**
Sur les 12 cerveaux de la campagne 2a, onze ont exactement 0 repère `goal` ; le seul qui en
garde (21) est celui qu'aucune promotion n'effaçait plus — il avait atteint le dernier palier.

Cause : `reinitialiser_niveau()` vidait la mémoire **entière** à chaque palier. Le repère du
but naît **au tick de la victoire**, donc quelques ticks avant la promotion qu'il déclenche.

> **La distinction (formulée par l'utilisateur)** : le **OÙ** — les coordonnées `(x,y)` —
> est périmé au changement de carte et doit partir. Le **QUOI** — la valence apprise par
> *type* — est vrai partout. *« L'abstraction doit s'émanciper de l'espace. »*

⚠️ **Rien n'est expliqué en dur** : `empreinte_types` n'est pas une table `goal = bien`,
c'est la moyenne des chocs réellement vécus sur chaque étiquette opaque. Vérifié après
12 jours réels : `porte_key` **+0,175** (×12) contre `sol` **−0,006** (×111) — la
discrimination est **apprise**, jamais déclarée.

---

**🔇 Correctif 2 — le silence n'est pas l'absence.**

⚠️ **Correction d'un fait publié dans l'entrée v38 ci-dessous.** Il y était écrit que
`obs_auditive=None` fait *« changer la norme du bus »*. **C'est faux, et la mesure le montre :**

| Cas | Norme du bus |
|---|---|
| `obs_auditive=None` | 6,3323 |
| Silence numérique (zéros) | **6,3323** — écart **0,0000** |

`porte_auditive` est **sans biais**, donc `relu(porte_auditive(zeros)) = 0` exactement. Le vrai
défaut n'est pas une échelle qui bouge : c'est qu'**un silence parfait et une oreille absente
sont mathématiquement indiscernables**. *« Le silence, c'est quand il y a presque plus rien à
établir »* — pas quand il n'y a pas d'oreille.

Le correctif est **bit-identique** (écart max vérifié : `0.0`) : il rend le défaut explicite et
localisé. La vraie levée demande un **bit de présence** dans le vecteur bio, donc une greffe
`persistance` — chantier séparé, délibérément non fait ici.

---

**📊 Correctif 3 — `Pourcentage_Reve` est une fraction.**

Ambiguïté ayant causé une erreur de diagnostic propagée dans deux documents (0,001 lu
« 0,1 % », rêve déclaré éteint alors qu'il rejouait 15-18 %). La clé n'est **pas renommée** —
190 runs historiques l'utilisent — mais deux clés explicites l'accompagnent désormais.

| Fichier modifié | Changement |
|-----------------|------------|
| `.gitignore` | règle `noyau.py` retirée, avec l'argumentaire du choix |
| `src/naulthene/cerveau/noyau.py` | `empreinte_types` + `_nourrir_empreinte` + `valence_de_type` ; `reinitialiser_niveau` conserve le QUOI ; silence auditif explicite ; télémétrie console + 5 clés W&B |
| `src/naulthene/cerveau/persistance.py` | sérialisation de `empreinte_types`, rechargement rétrocompatible (`.get(..., {})`) |

⚠️ **Aucun effet sur la performance n'est démontré.** Les trois correctifs sont *mesurés dans
leur mécanisme*, pas dans leur *conséquence*. Test à faire : 2a continu, 6 graines appariées,
avec et sans conservation de l'empreinte.

---

## [v38.0-experimental] - 2026-08-13 (soir) — clôture du chantier

### 2c-ter et 2d : le chantier se termine avec UNE brique validée sur six

| Type | Details |
|------|---------|
| **Commit** | `89ac5ad` |
| **Catégorie** | feat (expérimental) / docs |
| **Impact** | **Documentation** — aucune ligne de `src/naulthene/` modifiée |

**🔔 2c-ter — le son parcimonieux, variable, et le vrai silence.**

Trois corrections issues de remarques utilisateur, toutes mesurées :

| Correction | Mesure |
|---|---|
| **Variance des timbres** | intra-type 2,909 vs inter-type 6,201 → **ratio 2,1×** : distinguables *malgré* la variance |
| **Parcimonie** | 10 à 34 % de ticks sonores selon la carte, jamais 0 %, jamais 100 % |
| **Le silence n'est pas 0** | quasi-silence perçu (distance 3,71 au timbre plein) au lieu de `None` |

⚠️ **La troisième corrige un défaut RÉEL du noyau** : `noyau.py:548-552`,
`obs_auditive=None` ne produit pas un silence — le terme **disparaît** de la somme du bus.
~~La norme change, donc l'échelle de tout l'aval.~~ Le cerveau ne perçoit pas le calme, **il perd
le canal**. Défaut annoncé dans `les_sens_combinatoire.md` §4.3, jamais corrigé.

> ❌ **CORRECTION (v39.0, 2026-08-13)** — la phrase barrée est **fausse**. Mesuré :
> `porte_auditive` est **sans biais**, donc `relu(porte_auditive(zeros)) = 0` exactement, et
> la norme du bus est **identique** dans les deux cas (6,3323, écart 0,0000). Le défaut est
> réel mais il est ailleurs : un silence parfait et une oreille absente sont **mathématiquement
> indiscernables**. Voir l'entrée v39.0 en tête de fichier.

Résultat : paliers 5, 5, 1, 3, 2, 1 (médiane 2,5), **37 victoires** contre 17 pour 2b. Deux
graines franchissent le cursus complet. Le canal auditif **cesse de coûter des paliers** —
mais n'améliore pas 2b de façon démontrable (p = 0,688).

⚠️ **Anomalie non expliquée** : la graine 22 finit à `cooc = 0,00` tout en atteignant le
palier 5. Un run **sans aucune co-occurrence sonore** réussit aussi bien qu'un run à 0,67.

**🔗 2d — le liage multimodal : ÉCHEC.**

InfoNCE symétrique sur les sorties de porte, empilé sur **2b** (la seule base qui tient),
négatifs in-batch obligatoires, ticks de quasi-silence exclus.

| | 2b | 2d |
|---|---|---|
| Paliers médians | **3,0** | 1,5 |
| Écarts appariés | — | −1, −3, 0, −1, +3, −3 (**1/5**, p = 1,000) |

**La perte MONTE** (4,3 → 5,0) : le liage n'apprend rien. Ce n'est pas un effondrement — le
garde-fou a fonctionné, la variance ne s'est jamais annulée — c'est une absence pure
d'apprentissage. Explication la plus probable, et c'est **une faute de conception de ma
part** : l'InfoNCE apparie un *tick* à un *tick*, alors que le liage visé est entre un *type*
et un *timbre*. Deux ticks montrant la même clé sont comptés comme négatifs l'un de l'autre.

**Bug attrapé avant lancement** : `optimiseur` au lieu de `optimizer` (`noyau.py:533`), dans
un `try/except` nu. L'exception aurait été avalée, le liage n'aurait jamais appris, et le run
aurait produit un « effet nul » crédible. **Un banc d'essai qui masque ses propres pannes
mesure du vide.**

**📊 Verdict du chantier v38**

| Étape | Paliers médians | p vs origine | Verdict |
|---|---|---|---|
| origine | 1,5 | — | référence |
| 2a continuité | 3,0 | 0,375 | 🟡 non significatif |
| **2b + densité** | **3,0** | **0,062** | ✅ **le seul qui tient** |
| 2c parent | 1,0 | — | ❌ nuisible |
| 2c-fix | 2,0 | 1,000 | ❌ |
| 2c-ter son | 2,5 | 0,688 | 🟡 cesse de nuire |
| 2d liage | 1,5 | 1,000 | ❌ |

**Une brique sur six.** Le chantier produit plus de connaissances négatives que positives —
ce qui reste une avancée, à condition de ne pas présenter le reste comme un succès.

**Le fil conducteur des 4 jours** : *ce qui **rend possible** fait progresser · ce qui
**facilite** ne change rien · ce qui **fait à la place** fait régresser.*

**La saturation, rencontrée 4 fois** (états absorbants, parole permanente, portée trop
large, portée trop étroite). Une cause unique : *une variable saturée — dans un sens comme
dans l'autre — cesse de porter de l'information.*

| Fichier modifié | Changement |
|-----------------|------------|
| `docs/recherche/ETAT_DU_PROJET_aout_2026.md` | **NOUVEAU** — état complet : forces, faiblesses, ce qui reste à faire |
| `docs/ameliorations_appliquees/CHANTIER_v38_monde_continu.md` | 2c-ter, 2d, verdict du chantier |
| `experiences/v38/*.py` | bancs 2c-ter et 2d |

---

## [v38.0-experimental] - 2026-08-13

### Le Monde Continu — 2a, 2b, 2c : la pile progresse, le parent la fait régresser

| Type | Details |
|------|---------|
| **Commit** | `864a8d0` (2a/2b/2c), suite en cours |
| **Catégorie** | feat (expérimental) |
| **Impact** | **Fonctionnel** — aucune ligne de `src/naulthene/` modifiée |
| **Branche** | `feat/v38-monde-continu` |

Chantier ouvert sur deux exigences utilisateur : **la continuité permanente** et **la
superposition des 5 sens en permanence et en tout lieu**. Protocole imposé : chaque étape
s'**empile** sur la précédente, 6 graines appariées, 600 jours, et **deux points de
comparaison** — l'étape N−1 (ce que la brique ajoute) et le monde d'origine (ce que la pile
entière vaut).

⚠️ Tout vit dans `experiences/v38/` par surcharge en mémoire. **`src/naulthene/` est
intact** — aucune de ces mécaniques n'est portée.

**Correction d'une erreur de diagnostic propagée dans plusieurs documents** : j'avais écrit
que « l'agent voit déjà ce qu'il sent, donc l'odorat est redondant ». **C'est faux**, vérifié
dans le code — MiniGrid a **déjà l'occlusion** (cône 7×7 agent-centré,
`see_through_walls=False`, ~49 cases visibles sur 256 en 16×16). Le problème n'a jamais été
le champ de vision : c'est la **discontinuité temporelle**.

**🌍 2a — la continuité.** Le `reset()` de fin d'épisode est remplacé par un **réarmement de
tâche** : le monde et le corps persistent, seule la tâche se régénère.

| Graine | Continu | Témoin | Écart |
|---|---|---|---|
| 22 | **69 vict. / niv. 5** | 1 / niv. 1 | **+68** |
| autres | 1, 3, 4, 3, 2 | 3, 2, 1, 0, 2 | −2, +1, +3, +3, 0 |

4 gagne / 1 perd / 1 nul, **p ≈ 0,375**. Paliers médians **3,0 contre 1,5**. La moyenne
(13,7) est portée par une seule graine — ne jamais la citer seule. Sans l'outlier, l'effet
subsiste (2,6 contre 1,6 paliers).

La graine 22 est notable : **65 des 69 victoires sur `DoorKey-16x16`**, la carte la plus
dure, du jour 239 au jour 600, intervalles descendant à 1 jour. Record antérieur du projet :
22 victoires en 1300 jours, sur des niveaux faciles. **La continuité lève un plafond, elle ne
monte pas un plancher.**

*Piège trouvé au smoke test* : une continuité naïve rend la tâche **triviale** dès la
première réussite — `carrying` n'est jamais relâché (Portage 100 %), la porte reste ouverte à
jamais, les souvenirs se figent à 1. D'où la distinction qui est le vrai contenu de l'étape :
**le monde et le corps persistent, la tâche se réarme**.

**🌾 2b — la permanence des sens.** Densité de ressources proportionnelle à la surface utile
(29+29 sur `16x16` contre 2+2 avant).

| Comparaison | Écarts appariés | p |
|---|---|---|
| 2b vs 2a *(apport densité)* | +3, −1, −1, −2, −2, +2 | **1,000** |
| **2b vs origine** *(la pile)* | **+1, +3, 0, +1, +1, +2** | **0,062** |

**La densité seule n'apporte rien**, alors même que les canaux sont bien remplis (odorat
actif **100 %** des ticks). Cohérent avec l'ablation du 12/08 : remplir un canal ne le rend
pas utile.

**Mais la pile progresse — 5 positifs sur 5, aucun négatif.** C'est le signal le plus
régulier de l'investigation : ni 2a seul ni aucun levier du 12/08 n'avait évité d'avoir au
moins une graine en recul. L'échange, non anticipé : on **perd le cas exceptionnel**
(69 victoires) mais **tout le monde monte**. ⚠️ p = 0,062 n'est pas p < 0,05.

**👪 2c — le parent physique : ÉCHEC, et il apprend quelque chose.**

Remarque utilisateur qui cadre l'étape : *« l'ouïe est peut-être le plus difficile à
exploiter, il y a tout à créer comme son »*. Exact — vue, toucher, odorat et goût **dérivent**
d'un état de la grille ; l'ouïe ne dérive de rien. Vérifié : `SynthetiseurFormants` +
`extraire_mfcc` suffisent (4 noms synthétiques, MFCC distants de 2,59 à 5,66).

| | 2c parent | 2b pile | Origine |
|---|---|---|---|
| Paliers médians | **1,0** | **3,0** | 1,5 |
| Repères mnésiques | **12** | **74** | — |
| Approche olfactive | **0,128** | **0,306** | — |

`2c vs 2b` : **0 positif sur 5**, p = 1,000. **Les six graines se figent au palier 1** — cette
uniformité est un mécanisme, pas du bruit.

**Le parent nourrit trop bien** : l'agent n'a plus besoin de chercher, donc plus besoin de
sentir ni de mémoriser. La mémoire spatiale s'effondre au jour 121 (7 → 1 repère) et ne
remonte jamais.

⚠️ **Erreur de méthode consignée** : le cadrage v34 §3.2 contient *exactement* cet
avertissement (« nourrir sans montrer masque l'incompétence… la différence entre donner un
poisson et pêcher devant lui »), et je l'ai **recopié dans la docstring de l'étape** avant de
coder le poisson. **Citer un avertissement ne le mesure pas.**

✅ **L'acquis de 2c** : `Cooc_Vue_Ouie` passe de **0** — valeur sur *tous* les runs du projet
— à **~0,23**. La synchronisation vue↔son fonctionne, préalable non négociable de 2d. Le
sevrage mérité fonctionne aussi (`force` 0,35 → 0,23 avec la maturation, aucun compteur de
jours).

🔬 **2c-fix en cours** : montrer et nommer **sans nourrir**, pour isoler le geste que v34
désigne comme principal.

| Fichier modifié | Changement |
|-----------------|------------|
| `experiences/v38/*.py` | bancs d'essai 2a, 2b, 2c (surcharge en mémoire) |
| `docs/ameliorations_appliquees/CHANTIER_v38_monde_continu.md` | plan interrogeable, résultats, erreurs |
| `.gitignore` | `docs/notes/` n'ignore plus que `evals/` ; ajout de `*.brain.tmp` |

---

## [recherche] - 2026-08-12 (nuit, 2) — ablation sensorielle

### 🔴 Le toucher porte 75 % de la performance ; l'odorat et le goût ne servent à rien

| Type | Details |
|------|---------|
| **Commit** | `89ac5ad` |
| **Catégorie** | docs (recherche expérimentale) |
| **Impact** | **Documentation** — aucun changement de code |

12 runs de 600 jours (4 conditions × 3 graines, **témoins appariés**), par surcharge en
mémoire. `src/naulthene/` intact, **Exo-Sens jamais amputé** (invariant v30.0 (2) :
`num_actions` reste à 8, `ACTION_DEMANDER` masquée).

| Condition | g11 | g22 | g33 | Moyenne | σ | Écarts appariés |
|---|---|---|---|---|---|---|
| **TÉMOIN** | 2 | 3 | 3 | **2,67** | 0,47 | — |
| chimie coupée | 5 | 1 | 1 | 2,33 | 1,89 | +3, −2, −2 |
| **toucher coupé** | 0 | 1 | 1 | **0,67** | 0,47 | **−2, −2, −2** |
| mémoire coupée | 2 | 0 | 4 | 2,00 | 1,63 | 0, −3, +1 |

**Le toucher est le seul sens démontré nécessaire** : −2 victoires sur **3 graines sur 3**,
σ identique au témoin. C'est le premier effet reproductible de toute l'investigation. Il
porte `objet_en_main` — sur DoorKey, *savoir qu'on tient la clé* est l'information la plus
décisive, et c'est la seule que la vue ne donne pas.

**La chimie ne sert à rien** (écart 0,33, signes incohérents) : le sens n'est pas cassé —
l'odorat topologique v32.0 calcule correctement — il est **inutile dans ce monde**. L'agent
voit déjà ce qu'il sent.

**Mémoire : non concluant** (signe variable selon la graine).

**Critère de conception qui en découle** : *un sens n'est utile que s'il apporte une
information qu'aucun autre canal ne donne*. Rendre un sens obligatoire ne se décrète pas
dans le capteur — cela se construit dans le monde, en **retirant à la vue** ce qu'on veut
confier à l'odorat.

⚠️ Coupure faite à la **valeur neutre, jamais à zéro** : clinotaxie → 0.5 (invariant v32.0
(3)), rappel marquant → [0.5, 0.0] (invariant v36.0 (5)). Mettre zéro aurait mesuré un
agent *craintif*, pas *indifférent*.

| Fichier modifié | Changement |
|-----------------|------------|
| `docs/recherche/recherche_bug_or_not_bug.md` | H15, protocole et résultats d'ablation |
| `docs/fonctionnement/CHANGELOG.md` | cette entrée |

---

## [recherche] - 2026-08-12 (nuit)

### 🔬 La variance est la découverte — les 5 leviers tombent, l'agent franchit quand même

| Type | Details |
|------|---------|
| **Commit** | `89ac5ad` |
| **Catégorie** | docs (recherche expérimentale) |
| **Impact** | **Documentation** — annule la conclusion des deux entrées précédentes |

Le verrouillage de la patience ∝ √surface (3 graines + 3 témoins appariés) **échoue** :
écarts appariés **+2, −1, +1**. Le levier gagne une fois, perd une fois.

Et surtout, **la même condition ne se reproduit pas elle-même** : 6 runs à réglages
strictement identiques donnent 5, 5, 5, 4, 4, 5. L'écart-type nul des trois premiers, que
l'entrée précédente présentait comme la marque d'un effet robuste, était **un accident de
trois graines**.

**Aucun des 5 leviers testés le 12/08 ne produit d'effet reproductible** (patience, grâce
mnésique, entrelacement, C2 profond, promotion hybride).

**Le bémol de l'utilisateur, mesuré** — *« l'agent ne reproduit pas le même comportement de
départ, qui s'amplifie avec le temps ? »* :

| Affirmation | Verdict |
|---|---|
| le départ n'est pas reproductible | ✅ **confirmé** — à j.50 : 0,0,0,1,2,2 |
| ça s'amplifie avec le temps | ❌ **réfuté** — c'est l'inverse |

σ passe de 0,76 (j.50) à **1,11** (j.400-600) puis retombe à **0,47** (j.1200). **Les
trajectoires divergent, l'état final converge** — bon signe pour l'architecture : l'agent
apprend quelque chose de stable au lieu de subir son tirage initial.

⚠️ **Conséquence de méthode : la mauvaise variable était mesurée.** Comparer des *totaux de
victoires* sur des courbes qui reconvergent revient à comparer les points d'arrivée d'un
processus qui les égalise. Il faut comparer des **vitesses** (jour de première promotion,
pente), dans la fenêtre j.400-600 où σ est maximal, et sur **≥8 graines** — 3 ne suffisent
pas.

**🎯 Ce qui reste debout** : l'agent franchit le cursus de 6 paliers dans **11 runs sur 12**,
toutes conditions confondues. Le blocage historique (« niveau 2/15 depuis 678 jours »)
n'apparaît dans **aucun** de ces runs. Ce qui a changé n'est aucun levier testé, mais ce qui
leur est **commun** : les correctifs **v37** (érosion, myéline, plancher vital) et un
**cursus DoorKey progressif à 6 paliers** au lieu de 15 niveaux hétérogènes. C'est-à-dire la
réparation du cerveau et la cohérence du cursus — pas les raffinements d'apprentissage.

| Fichier modifié | Changement |
|-----------------|------------|
| `docs/recherche/recherche_bug_or_not_bug.md` | verrouillage, analyse de variance, bémol utilisateur mesuré |
| `docs/fonctionnement/CHANGELOG.md` | cette entrée |

---

## [recherche] - 2026-08-12 (soir) — ⛔ CONCLUSION RÉFUTÉE, voir l'entrée ci-dessus

### ⛔ Réfutation — la révision espacée ne se réplique pas ; le seul levier est la patience

| Type | Details |
|------|---------|
| **Commit** | `89ac5ad` |
| **Catégorie** | docs (recherche expérimentale) |
| **Impact** | **Documentation** — annule la conclusion de l'entrée précédente |

L'entrée ci-dessous (`7fb4c02`) annonçait « ×4,5 sur les victoires » pour H13+H14. **Ce
résultat est réfuté.** Rejoué sur 3 graines avec témoins appariés :

| | g101 | g202 | g303 | Moyenne | σ |
|---|---|---|---|---|---|
| **H13+H14** | 7 / 5 pal. | 2 / 2 | 1 / 1 | **3,3** | 2,62 |
| **Témoin** | 5 / 5 | 5 / 5 | 5 / 5 | **5,0** | **0,00** |

Le témoin fait **mieux** et franchit le cursus **3 fois sur 3**. Le ×4,5 était un artefact
d'un seul run — la graine 101 le reproduit (7 victoires), ce qui montre le piège : sur n=1
on ne voit pas qu'on a tiré la queue de la distribution.

**La grâce mnésique produit l'obsession au lieu de l'empêcher** : g303 finit à 63 repères /
427 confirmations, l'exact profil de H11. Protéger un repère neuf lui laisse le temps de se
re-confirmer, donc de devenir inévinçable *par le haut*. Le cliquet n'a pas été supprimé,
il a été **alimenté**.

**Le « plateau de 800 jours » tombe aussi** : les témoins franchissent tout sans plateau. Il
appartenait à la famille H13/H14, ce n'était pas une loi de maturation.

**🎯 Le seul levier qui survit — la patience ∝ √surface**, seul ingrédient commun aux 4 runs
qui franchissent le cursus complet (A3fix + 3 témoins) :

| Levier | Runs | Verdict |
|---|---|---|
| ~~**Patience ∝ √surface**~~ | ~~4/4~~ | ⛔ **réfuté le soir même** (+2/−1/+1 en apparié) |
| Grâce mnésique (H13) | 1/3 | ❌ non reproduit |
| Entrelacement (H14) | 1/3 | ❌ non reproduit |
| C2 profond (A1) | 0/1 | ❌ aucun effet |
| Promotion hybride (A2) | 0/1 | ❌ bloque tout |

**Le blocage n'était ni la mémoire, ni C2, ni le seuil de promotion : c'était le temps
d'exploration.** L'agent recevait le même budget de ticks sur 196 cases que sur 9 — il
n'échouait pas par incapacité, **il était coupé avant d'avoir fini**.

**Erreur de méthode à ne pas répéter** : « ×4,5 » a été annoncé comme solide en citant, dans
la même page, la règle qui l'interdisait (H10 : « aucun écart sous 4 victoires n'est
significatif »). Règle qui en découle : **toute condition annoncée comme un effet doit être
répliquée sur ≥3 graines avec témoins appariés, avant publication et non après.**

| Fichier modifié | Changement |
|-----------------|------------|
| `docs/recherche/recherche_bug_or_not_bug.md` | réfutation, sections barrées mais conservées, erreur de méthode |
| `docs/fonctionnement/CHANGELOG.md` | cette entrée |

---

## [recherche] - 2026-08-12 (matin) — ⛔ CONCLUSION RÉFUTÉE, voir l'entrée ci-dessus

### L'apprentissage plutôt que le cerveau — la révision espacée fait ×4,5 sur les victoires

| Type | Details |
|------|---------|
| **Commit** | `89ac5ad` |
| **Catégorie** | docs (recherche expérimentale) |
| **Impact** | **Documentation** — aucun changement de code |

Neuf runs de 1200 jours menés le 12/08, tous par **surcharge en mémoire** depuis le
scratchpad. `src/naulthene/` n'a reçu **aucune modification**.

**📋 Carnet complet** : [`recherche_bug_or_not_bug.md`](../recherche/recherche_bug_or_not_bug.md)

**🔬 Les 4 axes de conciliation (A1–A4)**

| Run | Repères | Conf. | Palier | Victoires |
|---|---|---|---|---|
| BASE | 739 | 54 | 3/3 ✅ | 3 |
| A1 (C2 profond) | 685 | 67 | 3/3 ✅ | 3 |
| **A3 (patience ∝ √surface)** | 586 | 27 | **5/5** ✅ | 5 |
| A1+A2+A3 | 25 | 3264 | 0/5 ❌ | 4 |

**A3 franchit un cursus de 6 paliers depuis la naissance.** Le seul changement par rapport
au run raté : la patience étirée sur `patience_jour` (le budget réel, `noyau.py:4856`) et
non `patience_base_jour` (la valeur *loguée*, `noyau.py:4139`). Sur une grande carte, **le
temps d'exploration est une ressource au même titre que la mémoire**.

**🔬 H12/H13/H14 — l'apprentissage (hypothèses utilisateur)**

| Run | Palier | Victoires | Repères | Conf. |
|---|---|---|---|---|
| Témoin | 2/5 | 2 | 131 | 294 |
| H13 grâce mnésique | 3/5 | 3 | 118 | 110 |
| H14 entrelacement | 4/5 | 4 | 383 | 47 |
| **H13 + H14** | **5/5** ✅ | **9** | **605** | **18** |
| H12 rotation forcée | 1/5 | 2 | 689 | 49 |

**Trois résultats structurants :**

1. **Les deux mécanismes se combinent** (+1 et +2 paliers séparément, **+3 paliers et ×4,5
   victoires** ensemble) — une première, la combinaison H11+H09 ayant échoué la veille.
   H14 produit la nouveauté, H13 l'empêche d'être effacée à la naissance.

2. **Le « moment de bascule »** : toutes les conditions gagnantes stagnent **700 à 900
   jours** avant de décoller. ⚠️ Ce plateau est **indiscernable de l'échec** diagnostiqué
   depuis le début du projet — le run de 600 jours fondateur aurait été coupé 200 jours
   avant le décollage. **Aucun run de moins de 1000 jours ne peut conclure à un blocage.**

3. **La largeur mnésique ne suffit pas** : H12 produit 689 repères (record du projet) et ne
   franchit rien. Ni la largeur ni la profondeur ne comptent — seule **la nouveauté qui
   revient sur du connu**.

**Cause mécanique identifiée** (`noyau.py:2389`) : l'éviction retire le repère au
`confirmations` **minimal**. Un repère neuf naît à 1, il est donc **toujours** le minimum,
donc évincé immédiatement. **L'oubli tue la nouveauté au profit de l'habitude.** La règle
v36.0 est juste sur le principe mais crée un cliquet — même défaut de forme que
`norme_naissance` (v34.0-fix2) et `reference_choc_dopamine` (v37.1-fix1) : *une référence
qui suit sa propre dérive ne borne plus rien.*

⚠️ **Rien n'est porté dans `src/`.** Les constantes (10 nuits de grâce, 20 % de révision)
sont de l'**inné arbitraire**, ce que [CLAUDE.md](../../CLAUDE.md) interdit. Elles ont répondu
à « l'effet existe-t-il ? » ; elles doivent maintenant **dériver du vécu** (plasticité du
moment pour la grâce, fragilité mesurée de la compétence pour la révision).

| Fichier modifié | Changement |
|-----------------|------------|
| `docs/recherche/recherche_bug_or_not_bug.md` | A1–A4, H12/H13/H14, le moment de bascule, la frontière inné/acquis |
| `docs/fonctionnement/CHANGELOG.md` | cette entrée |

---

## [recherche] - 2026-08-11

### Campagne d'investigation « bug or not bug » — 7 hypothèses testées, aucune ligne de `src/` modifiée

| Type | Details |
|------|---------|
| **Commit** | `89ac5ad` |
| **Catégorie** | docs (recherche expérimentale) |
| **Impact** | **Documentation** — aucun changement de code |

Après le run de 1300 jours (`ous47258`) établissant que l'agent plafonne au niveau 2/15 depuis
678 jours, sept expériences de 800 jours ont été menées pour trancher : **bug ou erreur
logique ?**

Toutes les constantes ont été **surchargées en mémoire** depuis un script isolé du scratchpad.
`src/naulthene/` n'a reçu aucune modification.

**📋 Carnet complet** : [`recherche_bug_or_not_bug.md`](../recherche/recherche_bug_or_not_bug.md) — 11
hypothèses, protocoles, mesures, et les erreurs de diagnostic commises.

**🔬 RÉSULTATS DES SEPT RUNS (800 jours chacun)**

| Run | Victoires | Confirmations mém. | Accord C1/C2 |
|---|---|---|---|
| Témoin (cursus officiel) | **12** | 42,7 | 0,874 |
| Variété d'abord | 2 | 75,7 | 0,205 |
| **Adaptatif (DoorKey)** | **7** | 534,7 | 0,358 |
| Quête auto rétablie | 5 | 564,3 | 0,493 |
| Indulgence ×0,1 | 3 | 1047 | 0,294 |
| Sans sanction | 5 | **1542** | **0,794** |
| Sévérité décroissante | 3 | 1087 | 0,291 |

**🟢 CE QUI EST ROBUSTE** (écart d'un ordre de grandeur, mesuré sur 3 runs indépendants)

- **Moins on sanctionne, plus le cerveau consolide** : 42,7 → 1542 confirmations par repère
  (**×36**), accord C1/C2 de 0,29 à 0,79 (**×3**). La sanction n'empêche pas de gagner —
  **elle empêche d'apprendre**.
- **Le cursus officiel s'éteint, le cursus DoorKey accélère** :
  ```
  TÉMOIN     6 6 0 0 0 0 0 0   ← 12 victoires en 200 j, puis MORT pendant 600 j
  ADAPTATIF  0 1 1 0 1 2 2 0   ← lent au départ, puis ACCÉLÈRE
  ```
  Sur 800 jours le témoin gagne ; **sur la tendance, c'est l'inverse**, et aucun run DoorKey
  n'avait fini de progresser à l'arrêt.
- **Les 3 premiers niveaux du cursus sont les plus pauvres du programme** : `Empty-5x5` et
  `Empty-8x8` produisent **1 seule configuration** sur 500 graines, contre 500 pour
  `GoToDoor`. Le cursus est construit à l'envers.

**❌ CE QUI EST RÉFUTÉ**

- **Donner de la variété d'abord** : 6× moins de victoires (2 contre 12). Quand le but change
  de place, les records de proximité tombent à **0,00/jour** — l'agent perd tout signal
  intermédiaire.
- **Le signal de progrès manquant** : `QUETE_AUTO_EN_MODE_LIBRE` activé (le code le décrit
  comme un instrument de diagnostic prévu pour ça). Santé interne améliorée, **mais moins de
  victoires**. Remis à `False`. La rareté du signal n'est pas la cause principale.
- **Enlever la notation** : 5 victoires contre 7. La consolidation explose, les victoires non.

**⚠️ VARIANCE MESURÉE — à garder en tête pour toute lecture de ce carnet**

Un run raté pour cause d'erreur de conception (sévérité ancrée sur le taux de maîtrise, resté
à 0 % — mécanisme **circulaire**) a servi de **second témoin involontaire** : mêmes conditions
que le run adaptatif, **3 victoires contre 7**.

**Aucun écart de moins de 4 victoires sur 800 jours n'est significatif.**

**📐 MESURES DE RÉFÉRENCE ÉTABLIES** (simulation directe, pas lecture de courbe)

| Mesure | Valeur |
|---|---|
| Configurations distinctes, `Empty-5x5` / `Empty-8x8` | **1** sur 500 graines |
| Observations distinctes en 300 ticks, `Empty-5x5` | **24** (contre 171 sur `GoToDoor`) |
| Optimal BFS `(x,y,dir)`, `Empty-8x8` | **11** actions (patience 120 → marge ×10,9) |
| Réussite d'une politique aléatoire, `Empty-8x8` | **3,8 %** (contre 38,2 % sur `Empty-6x6`) |
| Idem à patience 256 (natif MiniGrid) | **21,0 %** |
| Idem avec 3 actions utiles au lieu de 7 | **23,3 %** |
| Ratio sanction / récompense | **314× à 4,8 milliards ×** |

**🧬 CADRE BIOLOGIQUE APPORTÉ PAR L'UTILISATEUR**

Deux faits qui recadrent des conclusions antérieures :

1. **Surproduction puis élagage** — le cerveau humain crée jusqu'à 1 M de synapses/seconde et
   atteint 90 % de son volume adulte à 5 ans, **avant** d'élaguer (−1 à −2 %/an). Naulthène
   fait l'inverse : il naît à 16 dims et **élague sans avoir jamais foisonné**. Les 50-98 % de
   synapses mortes des runs pré-v34 ressemblaient à une pathologie ; l'élagage massif est
   pourtant le régime biologique normal. Ce qui manquait n'était pas moins d'élagage, mais
   **plus de matière au départ**.
2. **Décalage maturatif** — le système limbique mûrit à l'adolescence, le cortex préfrontal
   seulement à 25 ans. Chez Naulthène, `cortex_prefrontal` fait **64 paramètres sur 55 232**
   (0,1 % du réseau), et couper C2 double le taux de succès. La conclusion « C2 nuit »
   pourrait simplement signifier « **C2 n'a pas fini de mûrir** ».

**🌙 RUNS DE 1200 JOURS EN COURS** (lancés dans la nuit du 11 au 12 août)

| Run | Bus de naissance | Promotion | Hypothèse |
|---|---|---|---|
| H11 | **64** (au lieu de 16) | 60 % / 2 vict. | Surproduction initiale |
| H09 | 16 | **25 % / 1 vict.** | Seuil adapté au monde riche |
| H11+H09 | **64** | **25 % / 1 vict.** | Les deux combinées |

---

## [37.1-fix1-experimental] - 2026-08-08

### Le Cliquet de la Référence — la barre monte vite, elle ne redescend presque plus

| Type | Details |
|------|---------|
| **Commit** | `b088416` |
| **Catégorie** | fix critique (distillation sélective, expérimental — `noyau.py`) |
| **Impact** | **Critique** — la v37.1 rendait l'agent *de plus en plus facile à impressionner*, l'inverse exact du principe visé |

**🔴 LE BUG** (mesuré sur le run `8wequiqg`, 600 jours, `070820261634_V371_600_RMD.brain`)

`reference_choc_dopamine` utilisait une moyenne glissante **symétrique**. Quand l'agent cesse
de gagner, il ne reste que des micro-chocs — la référence descend donc **vers eux** :

| Période | Référence | Crédit moyen |
|---|---|---|
| jours 0-50 | 0,2149 | 10,0 % |
| jours 300-350 | 0,2182 | 21,1 % |
| jours 450-500 | 0,1348 | 52,6 % |
| jours 550-600 | **0,0932** (−57 %) | **69,3 %** (×7) |

Le crédit valant `choc / référence`, une référence qui s'effondre fait qu'un **même événement
médiocre crédite de plus en plus**. Une boucle s'installait : moins de victoires → référence
plus basse → tout paraît marquant → C1 distille 70 % de bruit → encore moins de victoires.

La protection « une journée stérile ne distille rien » n'y pouvait rien : la journée n'était
jamais *stérile*, elle était **médiocre**, et la référence s'adaptait à la médiocrité.

**C'est exactement le défaut de `norme_naissance` corrigé en v34.0-fix2** : une référence qui
suit la décroissance ne borne plus rien. Même remède — un cliquet.

**✅ LE CORRECTIF**

L'inertie devient **asymétrique** : montée rapide (`INERTIE_REFERENCE_CHOC = 0.99`, inchangée),
descente ~50× plus lente (`INERTIE_OUBLI_REFERENCE_CHOC = 0.9998`). Découvrir qu'on peut vivre
mieux relève la barre sans tarder ; traverser une mauvaise passe ne fait pas réviser à la
baisse ce qu'on sait être un bon jour.

La descente reste **non nulle** : un monde durablement plus pauvre (nouveau niveau, ressources
plus rares) doit pouvoir recalibrer — mais sur des centaines de nuits, jamais sur une saison
creuse.

| Fichier | Changement |
|---|---|
| `src/naulthene/cerveau/noyau.py` | `_ponderer_distillation` — inertie asymétrique selon le sens de variation ; `INERTIE_OUBLI_REFERENCE_CHOC` |

**📊 VÉRIFIÉ** — simulation du scénario exact du run raté (300 j avec victoires, puis 300 j sans) :

| | Dérive de la référence | Crédit final |
|---|---|---|
| v37.1 (symétrique) | **−71,3 %** | **87,2 %** |
| v37.1-fix1 (cliquet) | **−4,4 %** | **26,1 %** |

Non-régressions confirmées : le principe débutant/expert tient (référence ×8,8, un même choc
**8,8× moins marquant** pour l'expert) ; la coupure aux frontières d'épisode est intacte ; le
recalibrage reste possible (−29 % après 2000 jours de monde pauvre — soit bien au-delà d'un run).

> ⚠️ Un `.brain` produit par la v37.1 garde sa référence **déjà effondrée** : le cliquet la gèle
> au lieu de la réparer (on n'invente pas un vécu). Relancer sur un cerveau neuf pour mesurer
> l'effet réel du correctif.

**📉 CE QUE LE RUN A AUSSI MONTRÉ** (indépendant de ce bug, non corrigé à ce stade)

- **Niveau 2/15 au jour 600**, contre 3/15 pour le run V36 — et **aucune victoire après le
  jour 288** (312 jours), guidage saturé à ×3,0 depuis le jour ~387.
- L'accord C1/C2 **oscille** (50 % → 75 % → 29 %) au lieu de converger : l'équilibre v37.0 tient
  (le ratio reste entre 0,57 et 1,09, jamais les 22× d'avant), mais les deux modules ne
  s'accordent pas durablement. Le pic à 100 % observé en cours de run était une oscillation, pas
  une tendance.
- ~~**Le rêve est quasi inexistant** : `Pourcentage_Reve` à 0,1 % sur les 600 jours~~
  ❌ **AFFIRMATION FAUSSE, corrigée le 2026-08-08** (voir [dia_Aout_2026.md](../recherche/dia_Aout_2026.md) §2.2).
  `Pourcentage_Reve` est logué comme une **fraction** (`0,177`) mais affiché suivi d'un `%` — la
  valeur réelle est **17,7 %**, pas 0,177 %. Vérifié : `Nb_Reves / Pourcentage_Reve = 398 ≈
  len(memoire_moyen_terme)` sur 400 ticks. **Le rêve rejoue 15-18 % de la journée et fonctionne.**
  Les 75 nuits sans rêve des 100 premiers jours sont réelles (plasticité basse chez un cerveau
  neuf) mais disparaissent totalement après le jour 400.

---

## [37.1-experimental] - 2026-08-07

### La Distillation Sélective — C1 n'automatise que ce qui a marché

| Type | Details |
|------|---------|
| **Commit** | `9502f26` |
| **Catégorie** | feat (apprentissage du réflexe, expérimental — `noyau.py` + `persistance.py`) |
| **Impact** | **Fonctionnel** — la distillation v37.0 passe de plate à pondérée |

Issu d'une remarque de l'utilisateur sur la v37.0. Détail :
[`CHANTIER_v37_equilibre_c1_c2.md §5bis`](../ameliorations_appliquees/CHANTIER_v37_equilibre_c1_c2.md).

**🔴 LE DÉFAUT**

La distillation v37.0 était **plate** : C1 imitait C2 à chaque tick, au même poids, que C2
ait eu raison ou tort. Sur un C2 médiocre (amplitude constante, argmax figé sur une seule
action), cela revient à **faire apprendre à C1 les erreurs de C2**.

**🧠 LE MODÈLE** — on n'automatise pas tous ses gestes, on automatise ceux qui ont marché.

Un tick est crédité si un choc dopaminergique le **suit**, avec une décroissance
exponentielle vers le passé (patron de `trace_activation`, LTP v20.0). La propagation
**s'arrête aux frontières d'épisode** — créditer un tick de l'épisode précédent pour une
réussite du suivant serait une superstition, l'agent ayant été téléporté entre les deux.

```
chocs : [0, 0, 0, 0, 0, 0.8, 0, 0, | 0, 0, 0.4, 0]      (| = fin d'épisode)
poids : [.66,.72,.78,.85,.92, 1.0, 0., 0., .56,.61,.67, 0.]
                                    └──┬──┘
                              crédit coupé net
```

**⚖️ RIEN N'EST EN DUR — un NIVEAU, pas un SEUIL**

Il n'existe aucune règle « si choc > X, imiter » : le crédit est **continu** et proportionnel
au choc. Et l'échelle à laquelle un choc est jugé fort n'est pas une constante — c'est
`reference_choc_dopamine`, moyenne glissante de ce que **cet agent** a lui-même vécu,
sérialisée dans le `.brain`.

| Agent | Référence apprise | Crédit accordé à un choc de 0,1 |
|---|---|---|
| **Débutant** (n'a connu que des micro-progrès) | 0,100 | **100 %** |
| **Le même, expert** (200 j de victoires) | 0,879 | **11,5 %** |

Le même événement est **8,7× moins marquant** pour l'expert. Le niveau évolue avec l'âge et
les habitudes, exactement comme la faim ou la soif.

Les deux constantes ajoutées sont des **dynamiques** (vitesse d'effacement d'un crédit,
vitesse de suivi de la référence), jamais des seuils de décision.

| Fichier | Changement |
|---|---|
| `src/naulthene/cerveau/noyau.py` | `_ponderer_distillation()` — crédit rétrograde borné aux épisodes ; moyenne **pondérée** dans `apprendre_journee` (une journée stérile ne distille plus rien, au lieu de distiller du bruit) |
| `src/naulthene/cerveau/noyau.py` | `chocs_dopamine_journee` — buffer journalier, remis à zéro dans `_reinitialiser_buffers_journee` |
| `src/naulthene/cerveau/noyau.py` | `reference_choc_dopamine` — le niveau adaptatif ; `DECROISSANCE_CREDIT_DISTILLATION`, `INERTIE_REFERENCE_CHOC` |
| `src/naulthene/cerveau/noyau.py` | Télémétrie : `Distillation_Credit_Moyen`, `Distillation_Reference_Choc` + bilan console |
| `src/naulthene/cerveau/persistance.py` | `reference_choc_dopamine` sérialisée (`.get()` → rétrocompatible, aucune greffe) |

**📊 EFFET MESURÉ**

| | v37.0 (plate) | v37.1 (sélective) |
|---|---|---|
| Part de la journée distillée | 100 % | **~25-35 %** |
| Gradient reçu par `tete_motrice` | 0,01117 | 0,00912 (**−18 %**) |

**⚠️ DEUX LEVIERS ÉCARTÉS** (proposés, mesurés, refusés)

- **`f_planif` piloté par l'entropie de C1 / l'erreur JEPA** : le signal n'existe pas —
  `indecision_c2` varie de **1,00×** entre min et max sur 300 ticks. Et c'est un
  déclenchement sur seuil déguisé en formule continue (refusé v28/v29/v30). Le ratio est
  déjà passé de 22× à 0,6× **sans aucun pilotage**, par la seule maturation synaptique.
- **C2 réinjecté comme canal continu dans `integrateur_bio`** : crée une boucle, C2 étant
  calculé à partir de `pensee_bio` qui sort d'`integrateur_bio`.

---

## [37.0-experimental] - 2026-08-07

### L'Équilibre C1 / C2 — le réflexe cesse d'être inaudible, et les têtes de décision peuvent enfin apprendre

| Type | Details |
|------|---------|
| **Commit** | `766239c` |
| **Catégorie** | feat + fix critique (arbitrage cognitif & plasticité, expérimental — `noyau.py` + `persistance.py`) |
| **Impact** | **Critique** — trois bugs rendaient l'apprentissage des deux têtes de décision *mathématiquement impossible* |

Chantier complet et traçabilité des options écartées :
[`CHANTIER_v37_equilibre_c1_c2.md`](../ameliorations_appliquees/CHANTIER_v37_equilibre_c1_c2.md).

**🔴 CE QUI ÉTAIT CASSÉ** (mesuré sur `070820261310_V36_600_RMD.brain`, 600 jours)

Trois cerveaux successifs (V34-fix1 900 j, V35 2700 j, V36 600 j) se sont arrêtés au **même
niveau** du cursus (`SimpleCrossingS9N1`, index 3/15). L'hypothèse « le niveau est mal placé »
a été **écartée par la mesure** : le blocage est architectural.

| Environnement | Ampl. C1 | Ampl. C2 | Ratio | Accord argmax |
|---|---|---|---|---|
| `Empty-5x5` (maîtrisé) | 0,217 | 2,138 | 9,9× | **0 %** |
| `Empty-8x8` (maîtrisé) | 0,168 | 2,125 | 12,7× | **0 %** |
| `SimpleCrossingS9N1` (bloqué) | 0,095 | 2,105 | 22,1× | **0 %** |

`argmax(C1) = 3` sur 400 ticks / 400 ; `argmax(C2) = 0` sur 400 / 400. Chaque module votait une
action **constante**, différente de l'autre, indépendamment de l'observation — **y compris sur
les niveaux déjà maîtrisés**. Les 21 victoires du run V36 (taux de vie 3,5 %) sont attribuables
à la marche aléatoire du `multinomial`, pas à une politique apprise.

**🔬 LES QUATRE CAUSES, EMPILÉES**

| # | Cause | Preuve |
|---|---|---|
| 1 | **Le plancher vital était devenu un plafond.** La v34.0 renormalisait à *exactement* 10 % de la naissance depuis la norme post-érosion : tout ce que le gradient consolidait était effacé chaque nuit. | `tete_motrice` : 0,319490 avant la journée, annexe consolidée +0,0139, norme après sommeil **0,319490** — au millionième près |
| 2 | **La myéline ne voyait jamais l'apprentissage du jour.** Calculée uniquement dans `forward()`, donc pendant la journée, alors que `annexe_weight` ne prend sa valeur qu'au `optimizer.step()` du soir. Aucun `forward` n'a lieu entre le dernier pas et `cycle_sommeil`. | myéline de `tete_motrice` et `cortex_prefrontal` : **0,000000 exact** après 600 jours |
| 3 | **`q_ref = 1.0` : échelle 500× trop grande.** Paramètre jamais passé par aucun appelant depuis l'origine. Suppose une myéline d'ordre 1 ; la mesure dit ~0,002. `myeline_norm` restait donc collée à 0 et **toute** couche s'érodait au taux plein. | Même défaut que `SEUIL_CRISTAL = 0.80` face à une myéline réelle de 0,0038 — la Cristallisation Souple n'a jamais pu s'exercer |
| 4 | **C2 normalisé, C1 non.** `valeur_cumulee` sort d'un z-score, donc écart-type 1 **par construction** ; C1 garde son échelle brute, érodée au plancher. La fusion additionnait 0,1 et 1,8. | Amplitude C2 = 2,10 ± 0,02 **identique** sur trois cartes de difficultés très différentes |

> **C2 n'écrasait pas C1 parce qu'il était meilleur. Il l'écrasait parce qu'il était le seul des
> deux à avoir une échelle garantie par construction.**

**✅ CE QUI A ÉTÉ LIVRÉ**

| Fichier | Changement |
|---|---|
| `src/naulthene/cerveau/noyau.py` | **Correctif plancher** : `torch.clamp(norme_plancher / norme_apres, min=1.0)` — ne remonte que ce qui manque, ne redescend jamais |
| `src/naulthene/cerveau/noyau.py` | **Correctif myéline** : rafraîchie en tête de `cycle_sommeil`, seul point qui voit l'état final de `annexe_weight`. L'invariant tient — la myéline vient toujours **uniquement** du gradient, seul le *moment* de la lecture change |
| `src/naulthene/cerveau/noyau.py` | **Échelle de myéline relative** : 3ᵉ quartile de `myeline_M` de la couche (`QUANTILE_ECHELLE_MYELINE`), au lieu de `q_ref=1.0`. Le quantile et non le max : normaliser par le max fait porter l'échelle par une seule synapse (p50 = 0,027 mais p99 = 1,000) |
| `src/naulthene/cerveau/noyau.py` | **Mesure 2 — gain de C1 à double sens** : facteur scalaire ramenant l'amplitude vers `VIGUEUR_MIN_C1`, borné par `GAIN_C1_MIN/MAX`. L'opinion de C1 est intacte, seul son volume est réglé |
| `src/naulthene/cerveau/noyau.py` | **Mesure 3 — auto-distillation C2 → C1** (`TAUX_DISTILLATION_C1`) : le réflexe reçoit un gradient qui ne dépend d'aucune victoire. Cible `.detach()`ée — vérifié : `cortex_prefrontal` reçoit 0,00000000 par ce canal, C2 n'apprend donc pas à se rendre prévisible |
| `src/naulthene/cerveau/noyau.py` | **Normalisation de C2 inconditionnelle** : l'ancien `if std > 1e-6` laissait C2 à son échelle brute (~1e-7) sous le seuil — un module **numériquement éteint**, sans aucun signal. Observé : des journées entières à `C2=0.000` |
| `src/naulthene/cerveau/noyau.py` | **Télémétrie** (v29.1) : `Arbitrage_Ratio_C2C1`, `Arbitrage_Accord`, `Arbitrage_Amplitude_C1/C2`, `Arbitrage_Gain_C1`, `Distillation_C2_vers_C1` + ligne de bilan console. Conditionnelles — un jour sans tick moteur ne logge pas de zéros |
| `src/naulthene/cerveau/persistance.py` | `echelle_myeline` exclu de la détection de greffe (même cas que `norme_naissance` v34.0-fix1 : buffer scalaire ajouté aux 12 couches, il aurait déclenché une fausse greffe massive et réinitialisé Adam à chaque chargement) |
| `src/naulthene/instruments/sonde_c1_c2.py` | **NOUVEAU** — rapport de force C1/C2 sur un `.brain`, en lecture seule. Politique **stochastique** (`multinomial`), jamais `argmax` : un agent REINFORCE n'a jamais expérimenté son mode déterministe |
| `src/naulthene/instruments/sonde_poids.py` | **NOUVEAU** — santé synaptique couche par couche, signale les couches collées au plancher vital |

**⚠️ UNE MESURE ESSAYÉE PUIS RETIRÉE**

« L'échelle de C2 porte sa confiance » (réinjecter `indecision_c2` après la normalisation) a été
implémentée **deux fois**, mesurée **deux fois**, et retirée :

| Tentative | Résultat | Cause |
|---|---|---|
| Échelle **absolue** | **Éteint C2** (ratio 0,01×) | Le std brut vaut 0,0008 et ne varie que de **1,00×** entre min et max sur 300 ticks |
| Échelle **relative** (moyenne glissante) | **Sature** (`confiance = 2.0000` constante) | La moyenne glissante décroît plus vite que le signal — effet net : un facteur constant |

Tant que `cortex_prefrontal` est au plancher, C2 n'a **aucune confiance variable à exprimer**.
La trace est conservée dans `simuler_futur_et_planifier`, à l'endroit exact où le code aurait
vécu, pour que l'idée ne soit pas réintroduite sans ces deux mesures.

**📊 RÉSULTATS (run de validation, 40 jours)**

| Critère | Avant | Après |
|---|---|---|
| Ratio C2/C1 | 9,9× à 22,1×, **dérivant** selon la carte | **1,48-1,59×**, stable |
| Accord C1/C2 | 0 % | **0 %** — ❌ inchangé |
| Couches au plancher vital | 5 / 12 | **3 / 12** |
| Myéline `tete_motrice` | 0,000000 | 0,0033 |
| Protection moyenne contre l'érosion | ~0 % | **45,9 %** (érosion effective 0,050 → 0,027) |

**Une régression a été rencontrée et corrigée en cours de route** : une fois les têtes
débloquées, la distillation a renforcé C1 plus vite que C2 et le ratio s'est **inversé à 0,21×**
— exactement le mode d'échec que le chantier s'était engagé à surveiller. D'où le gain à double
sens (borne haute `GAIN_C1_MAX`).

**Sur `tete_motrice`, restée à 10,00 %** : sa consolidation nocturne fait *baisser* la norme
(0,31949 → 0,31823) — le gradient pointe en sens opposé aux poids existants, **il les corrige,
il ne les grossit pas**. Vérifié sur 5 nuits : cosinus 0,9972, **7,43 % des poids modifiés**.
La couche se remodèle à norme constante ; la norme seule est un mauvais indicateur d'apprentissage.

**🚧 CE QUI RESTE OUVERT**

- **L'accord C1/C2 est toujours à 0 %.** Les deux voix sont désormais comparables, elles ne
  convergent pas pour autant. Trop tôt pour dire si l'auto-distillation les rapprochera.
- **Rien ne prouve encore que la v37 débloque le niveau 3** — 40 jours ne suffisent pas.
  C'est ce que le run long doit trancher.

---

## [36.0-experimental] - 2026-08-07

### Le Flux Enrichi & l'Abstraction par Récurrence — la mémoire cesse d'être affamée

| Type | Details |
|------|---------|
| **Commit** | `e2a134e` |
| **Catégorie** | feat (mécanique mnésique, expérimental — `noyau.py` + `persistance.py`) |
| **Impact** | **Fonctionnel** — `DIM_VECTEUR_BIO` passe de 34 à 36 |

**🔴 CE QUI ÉTAIT CASSÉ** (mesuré, run `58ssyw19`, 600 jours)

| Fait | Valeur |
|---|---|
| Types d'événements que la mémoire spatiale pouvait recevoir | **2** (`FOOD`, `WATER`) — deux sites d'appel dans tout le code |
| Part du flux **rejetée** par déduplication | **98,6 %** (869 doublons pour 12 repères) |
| Ne pouvaient **jamais** entrer | la clé, la porte, le but, **la lave**, un mur percuté, un échec |

Ce n'était pas un mauvais filtre : **c'était un filtre privé de matière**. Une mémoire ne
peut pas trier ce qu'on ne lui donne jamais. Et l'agent bloquait 338 jours sur `LavaGapS5`
— une carte où mourir est l'information principale, et où mourir ne laissait aucune trace.

**🧠 LE MODÈLE** (décision utilisateur)

> 1. *« Il devrait absolument tout mémoriser, mais avec des filtres de pondération selon :
>    nouveau, récurrent, etc. »*
> 2. *« La récurrence devient des abstractions dans le cerveau. »*
> 3. *« Le routage est un lien intrinsèque écrit dans l'ADN. »*
> 4. *« L'oubli est un moyen de dire : l'abstraction est faite, on met en archive
>    dégradable avec le temps. »*
> 5. *« Rien ne doit être expliqué en dur — le cerveau ne sait pas ce qu'est une pomme ou
>    une clé, c'est lié à l'apprentissage. »*

⚠️ **Option écartée : le routeur centralisé.** Une première proposition plaçait un
aiguilleur unique en amont des mémoires. Écartée sur correction de l'utilisateur : ce serait
un **goulot** et un point de défaillance unique. Les mémoires ne sont pas des destinations
qu'on choisit — **elles SONT les filtres**, en parallèle, chacune puisant dans un flux
commun. On ne centralise pas : on cesse d'affamer.

**✅ CE QUI A ÉTÉ LIVRÉ**

**1. Le flux enrichi** — `_memoriser_si_saillant()` remplace les deux appels codés en dur.
Tout tick dont la charge dépasse `SEUIL_SAILLANCE_MEMOIRE` laisse une trace, quelle que
soit sa nature. L'étiquette est **dérivée de l'API MiniGrid** (`objet.type`) et reste une
chaîne **opaque** : aucune table `lave = danger` n'existe ni ne doit exister.

**2. L'abstraction par récurrence** — un doublon n'est plus jeté, il **confirme** :

```python
souvenir['confirmations'] += 1
souvenir['valence'] = moyenne glissante des chocs vécus ici
```

La valence est **apprise**, jamais déclarée. C'est le seul canal par lequel un danger peut
devenir évitable sans qu'aucune ligne ne mentionne « lave ».

**3. L'oubli comme archivage** — l'éviction ne jette plus le plus ancien mais **le moins
abstrait** (`min(confirmations, tick)`). Un repère confirmé cent fois est une régularité du
monde ; un repère vu une fois est peut-être un accident.

**4. Le rappel agnostique** — `rappel_le_plus_marquant()` ne demande **aucun type** : il
balaie tous les repères et rend `(valence, confiance)` du plus pesant. L'agent ne cherche
pas « de la nourriture », il perçoit « ici, il s'est passé quelque chose ».

`DIM_RAPPEL_MARQUANT = 2` en **queue** du `vecteur_bio` (contrat append-only). Neutre
**`[0.5, 0.0]`** — jamais `0.0` pour la valence, qui signifierait « le pire souvenir
possible » et rendrait l'agent craintif partout où il n'a rien vécu (même discipline que la
clinotaxie v32.0).

**🧪 VALIDATION**

Cerveau neuf, 40 jours :

| Mesure | Avant v36 | Après |
|---|---|---|
| Types appris | 2 (câblés) | **4** (`FOOD`, `WATER`, `porte_ball`, `sol`) — dérivés |
| Confirmations / repère | 1 (doublons jetés) | **4,65** |
| Rappel marquant actif | — | **26-100 %** des ticks |

Rétrocompatibilité, **nuit complète incluse** (test exigé par `CLAUDE.md`) :

```
👃 integrateur_bio greffé de 114 à 116 dims (+2 : rappel marquant (v36.0))
   — acquis existants préservés.
```

Vérifié sur deux `.brain` réels ; tous deux apprennent immédiatement de nouveaux types
(`porte_key`, `door`) qu'ils ne pouvaient pas mémoriser avant.

**📊 TÉLÉMÉTRIE** — 5 clés `Memoire_*` + ligne console. `Memoire_Confirmations_Moy` est LA
métrique de l'abstraction : > 1 signifie que la récurrence se convertit en repères solides
au lieu d'être jetée. `Memoire_Rappels_Ratio` à 0 signifierait un canal mort.

| Fichier modifié | Changement |
|-----------------|------------|
| `src/naulthene/cerveau/noyau.py` | `_memoriser_si_saillant()`, `rappel_le_plus_marquant()`, `enregistrer_evenement(intensite=)` avec confirmations/valence, éviction par abstraction, `DIM_RAPPEL_MARQUANT`, 2 bornes, 5 clés W&B + ligne console |
| `src/naulthene/cerveau/persistance.py` | libellé de greffe v36.0, import `DIM_ODORAT_DELTA` |

⚠️ **`noyau.py` uniquement** (terrain d'essai, gitignoré).

---

## [35.1-experimental] - 2026-08-07

### Le Guidage Dégressif & le Filet de Sécurité — « plus il comprend, moins on l'aide »

| Type | Details |
|------|---------|
| **Commit** | `991c0ab` |
| **Catégorie** | feat (mécanique de cursus, expérimental — `noyau.py` uniquement) |
| **Impact** | **Fonctionnel** — ferme les deux chantiers laissés ouverts par la v35.0 |

**🎯 LA DÉCISION UTILISATEUR**

> *« Le guidage dégressif : à chaque victoire, jusqu'à 85-100 % de réussite, on fait de
> façon à moins répéter — comme un enfant : plus il comprend, moins on l'aide, jusqu'à lui
> laisser assez d'autonomie pour qu'il comprenne. »*
>
> *« La redescente de palier : non, il ne peut pas aller faire un palier impossible — et
> quand il bloque, on l'aide un peu. »*

**📉 LE SEVRAGE — le guidage suit la maîtrise, plus le numéro de palier**

Ce que ça remplace : le guidage était coupé d'un **seul coup** au palier 5 (Mode Libre),
c'est-à-dire au moment précis où la tâche devient la plus dure. Mesuré sur 2000 jours :
**0,00 record de proximité par jour**. Une falaise, là où il fallait une pente.

| Maîtrise | Guidage |
|---|---|
| non mesurable (< 10 épisodes) | **1,00** — un débutant reste un débutant |
| ≤ 60 % (`SEUIL_DEBUT_SEVRAGE`) | 1,00 |
| 70 % | 0,67 |
| 80 % | 0,33 |
| ≥ 90 % (`SEUIL_FIN_SEVRAGE`) | **0,00** — autonomie complète |

Le curseur pilote **les deux** sources d'aide en un seul point — `RECOMPENSE_APPROCHE_BUT`
(DoorKey) et les records de proximité (générique) — au lieu de deux mécaniques qui
s'éteignaient selon des règles différentes.

**🛟 LE FILET — « quand il bloque, on l'aide un peu »**

La redescente de palier est **écartée** (elle contredirait « ce qui ne régresse jamais »).
À la place : un agent qui stagne reçoit un **surplus** d'aide, progressif.

| Jours sans victoire | Renfort |
|---|---|
| ≤ 30 (`JOURS_AVANT_RENFORT`) | ×1,0 — un échec est normal, pas un blocage |
| 45 | ×1,5 |
| 60 | ×2,0 |
| ≥ 90 | **×3,0** (`RENFORT_AIDE_MAX`) |

Le renfort se replie **dès la première victoire** : c'est une bouée, pas une rente. Il ne
touche que le guidage, **jamais la récompense terminale** — on aide à trouver le chemin, on
n'offre jamais la victoire.

Les deux forces ne peuvent pas se contredire : un agent qui stagne a par construction une
maîtrise basse (donc un sevrage à 1,0 que le renfort amplifie), et un agent qui maîtrise n'a
aucun jour de stagnation. Vérifié : maîtrise 100 % + 200 jours de stagnation ⇒ guidage 0,00.

**🧪 VALIDATION — le filet a réellement débloqué l'agent**

Cerveau neuf, 100 jours, graine fixée. L'agent cale à `Maternelle` après 3 promotions :

```
 jour  niv  nom                          maîtrise  guidage  stagn  vict
    5    2  Maternelle (Longue distance)     —      1.00      0      4
   20    2  Maternelle                      0.00    1.00     15      4
   40    2  Maternelle                      0.00    1.13     35      4     ← le filet s'arme
   60    2  Maternelle                      0.00    1.80     55      4
   80    2  Maternelle                      0.00    2.47     75      4
  100    2  Maternelle                      0.05    1.00      5      7     ← VICTOIRES, filet replié
```

Sans filet, ce cerveau serait resté à 4 victoires — c'est exactement le scénario des 2000
jours de blocage au Collège. Le run de référence (v35.0 sans filet) calait à **0 % pendant
79 jours** sur `SimpleCrossingS9N1`.

**📊 TÉLÉMÉTRIE**

`Cursus_Facteur_Guidage` est LA métrique de ce cycle : < 1,0 = le sevrage mord, > 1,0 = le
filet est déployé, 1,0 constant = ni l'un ni l'autre ne sert. Plus
`Cursus_Jours_Stagnation`, et une ligne console lisible d'un coup d'œil
(`🤝 aide pleine` / `📉 sevrage 67%` / `🛟 filet ×2.5` / `🕊️ autonome`).

| Fichier modifié | Changement |
|-----------------|------------|
| `src/naulthene/cerveau/noyau.py` | `facteur_guidage()`, 5 bornes (`SEUIL_*_SEVRAGE`, `JOURS_AVANT_RENFORT`, `RENFORT_AIDE_MAX`, `PENTE_RENFORT`), `jours_stagnation_niveau`, application en un point unique, 2 clés W&B + ligne console |
| `src/naulthene/cerveau/persistance.py` | sauvegarde/restauration de `jours_stagnation_niveau` |
| `docs/fonctionnement/Parcourt_readme.md` | §6ter — le sevrage et le filet ; §6bis (b) et (c) marqués livrés |

⚠️ **`noyau.py` uniquement** (terrain d'essai, gitignoré).

---

## [35.0-experimental] - 2026-08-07

### Le Cursus Progressif — 15 niveaux au lieu de 5, promotion par maîtrise

| Type | Details |
|------|---------|
| **Commit** | `9a9eb73` |
| **Catégorie** | feat (nouvelle mécanique de cursus, expérimental — `noyau.py` uniquement) |
| **Impact** | **Fonctionnel** — change la progression de tous les parcours |

**🎓 LE PROGRAMME PASSE DE 5 À 15 NIVEAUX**

Principe : **entre deux paliers voisins, une seule chose change.**

| # | Environnement | Nom | Nouveauté |
|---|---|---|---|
| 0-2 | `Empty-5x5` · `Empty-Random-6x6` · `Empty-8x8` | Nourrisson → Maternelle | bouger · départ variable · distance |
| 3-5 | `SimpleCrossingS9N1` · `LavaGapS5` · `Fetch-5x5-N2` | Primaire 1-3 | contourner · danger · **ramasser** |
| 6-8 | `GoToDoor-6x6` · `DoorKey-5x5` · `DoorKey-6x6` | Collège 1-3 | viser une porte · **clé+porte** · échelle |
| 9-11 | `DoorKey-8x8` · `Unlock` · `UnlockPickup` | Lycée 1-3 | distance · sans but visible · + objet |
| 12-14 | `MemoryS7` · `MultiRoom-N2-S4` · `MultiRoom-N4-S5` | Université → Doctorat | mémoire · 2 salles · 4 salles |

`DoorKey-5x5 → 6x6 → 8x8` est la **même tâche à trois échelles** : l'agent consolide au lieu
de tout réapprendre. MiniGrid expose 58 environnements ; le projet n'en utilisait que 5.

**📏 CORRECTION D'UN DIAGNOSTIC ERRONÉ — le Doctorat EST faisable**

L'entrée `[34.0-diag-cursus]` concluait que `MultiRoom-N4-S5` était « infaisable » avec
`max_steps=120`. **C'est faux.** Mesure par BFS sur `(x, y, direction)` — coût réel en
ACTIONS (rotations + avances + `toggle`), 30 graines par niveau :

| Niveau | `max_steps` | Coût optimal (moy / max) | **Marge** |
|---|---|---|---|
| `DoorKey-6x6` | 360 | 9,7 / 15 | **37,0×** |
| `Empty-8x8` | 256 | 11,0 / 11 | **23,3×** |
| `MultiRoom-N2-S4` | 40 | 7,3 / 10 | 5,5× |
| **`MultiRoom-N4-S5`** | **120** | **33,7 / 43** | **3,6×** |

Le but est atteignable — la marge reste positive. Le vrai problème est **le saut
d'exigence** : l'agent passe d'un droit à l'erreur de ×37 à ×3,6 en un seul niveau, sans
étape intermédiaire. `MultiRoom-N2-S4` (×5,5) est précisément cette étape.

**🏆 PROMOTION : DEUX VOIES EN « OU »**

| Voie | Critère | Caractère |
|---|---|---|
| **Série** (historique) | 2 victoires consécutives | rapide, mais une défaite remet à zéro |
| **Maîtrise** (nouveau) | 60 % sur les 20 derniers épisodes | lent à établir, robuste |

Les deux coexistent : la seconde **ajoute** une porte sans fermer la première, donc aucun
cerveau existant ne régresse en vitesse de promotion. Un agent à 80 % de réussite qui perdait
un épisode sur cinq restait bloqué à vie avec l'ancien critère seul.

Trois garde-fous : le taux n'est calculé qu'à partir de **10 épisodes** (avant, il vaut
`None` — « pas encore mesurable » ≠ « mesuré à zéro ») ; la fenêtre est **vidée à chaque
promotion** (sinon un taux hérité d'un niveau facile promouvrait en chaîne) ; et la réussite
se juge sur **`recompense_env > 0`**, jamais sur `termine` seul — sur `LavaGap`, `termine`
vaut aussi True quand l'agent meurt.

**🔀 RÉTROCOMPATIBILITÉ — le remappage par `env_id`**

`niveau_actuel` est un **INDEX**. Un `.brain` au niveau 4 (ex-Doctorat) se serait retrouvé à
l'index 4 du nouveau programme (`LavaGapS5`) — **rétrogradé de dix crans**. La persistance
remappe donc par `env_id`, seule donnée non ambiguë :

```
🔀 Niveau remappé : index 4 → 14 (Doctorat) — le PROGRAMME a changé de taille (v35.0),
   aucune progression n'est perdue.
```

Vérifié sur deux `.brain` réels, **nuit complète incluse** (test exigé par `CLAUDE.md`) :
Collège 1 → 8, Doctorat 4 → 14.

**🧪 VALIDATION**

Cerveau neuf, 60 jours : 4 promotions en 40 jours (`Nourrisson` → `Primaire 2`), fenêtre de
maîtrise correctement remplie et remise à zéro à chaque passage.

**📊 TÉLÉMÉTRIE** (obligatoire dans le même commit)

Ligne console `Cursus` + 4 clés W&B : `Cursus_Niveau_Index`, `Cursus_Niveau_Total`,
`Cursus_Episodes_Fenetre`, `Cursus_Taux_Maitrise_Niveau` (à **−1.0** tant que la fenêtre
n'est pas significative — un 0.0 laisserait croire à un échec mesuré).

| Fichier modifié | Changement |
|-----------------|------------|
| `src/naulthene/cerveau/noyau.py` | `PROGRAMME` 5→15, `FENETRE_PROMOTION`/`TAUX_PROMOTION`/`MIN_EPISODES_PROMOTION`, `_enregistrer_episode_niveau()`, `_taux_maitrise_niveau()`, double voie de promotion, ligne console + 4 clés W&B |
| `src/naulthene/cerveau/persistance.py` | remappage du niveau par `env_id`, sauvegarde/restauration de `historique_episodes_niveau` |
| `CLAUDE.md` | nouvel invariant « `PROGRAMME` du cursus » (4 points) + invariant « érosion nocturne » (v34) |
| `docs/fonctionnement/Parcourt_readme.md` | §6 réécrit (15 niveaux, 2 voies, remappage), §6bis marqué livré |
| `readme_fr.md` | mention du cursus à 15 niveaux |

⚠️ **`noyau.py` uniquement** (terrain d'essai, gitignoré) — `colab.py` garde ses 5 niveaux.

---

## [34.0-diag-cursus] - 2026-08-07

### Le cursus est trop court et trop brutal — diagnostic sur 2700 jours sains

| Type | Details |
|------|---------|
| **Commit** | `05a28ae` |
| **Catégorie** | docs (diagnostic + refonte proposée, aucun code) |
| **Impact** | Documentation — le `PROGRAMME` actuel est inchangé |

**✅ D'ABORD : LE CORRECTIF D'EXTINCTION TIENT SUR 2700 JOURS**

| Couche | j700 | **j2700** |
|---|---|---|
| `porte_visuelle` | 11,0 % | **21,3 %** ↗ |
| `hippocampe` | 24,8 % | **33,1 %** ↗ |
| `fusion_memoire` | 23,5 % | **30,5 %** ↗ |
| Couches mortes | 0 / 11 | **0 / 11** |

Deux couches **remontent** : le cerveau regagne plus qu'il ne perd. À comparer aux 8 couches
sur 11 à zéro avant le correctif.

**🔴 MAIS L'AGENT NE PROGRESSE PLUS — et ce n'est plus la vue**

| Mesure sur 2000 jours | Valeur |
|---|---|
| Jours au **Collège** | **2000**, sans jamais en sortir |
| Palier | **7** (dernier) atteint dès le jour 701 |
| Victoires | 22, **tendance 1,08 → stationnaire** |
| Δt1 (atteindre la clé) | **JAMAIS ATTEINT** |
| Contact avec les murs | **82 %** des ticks |
| Records de proximité | **0,00 / jour** |

L'agent porte la clé 58 % du temps mais n'atteint jamais la porte. Optimum local stable.

**📊 L'ÉCONOMIE S'EST AMÉLIORÉE SEULE** (sonde de récompense, même protocole)

| | Cerveau mourant | **Cerveau sain (2700 j)** |
|---|---|---|
| Solde | −7,54 | **−3,30** (÷2,3) |
| Total positif | +1,12 | **+5,18** (×4,6) |
| `sous_objectif_intrinseque` | 0,00 | **+3,60** (69 % du positif) |
| `dopamine_curiosite` | +0,76 | +1,22 |

**La curiosité JEPA s'est réveillée** : 90 sous-quêtes/jour contre zéro avant. Conséquence
directe du bus vivant — le JEPA fonctionne (0,0038), donc il génère des sous-objectifs.

Deux coûts restent anormaux : `penalite_stagnation` −4,35 (95,8 % des ticks, 51 % du
déficit) et `MALUS_DOULEUR` −2,85 (**71,2 % des ticks**, 34 %).

**🎓 LES TROIS DÉFAUTS DU CURSUS** (documentés dans `Parcourt_readme.md` §6bis)

1. **Le saut Primaire → Collège demande 5 compétences d'un coup.** `Empty-8x8` a 1 objet,
   `DoorKey-6x6` en a 3 et exige repérer + ramasser + porter + viser + ouvrir. Deux
   victoires sur une salle vide suffisent à y accéder.
2. **Le guidage est coupé au pire moment.** Au Palier 5, `RECOMPENSE_APPROCHE_BUT` tombe à 0
   d'un coup — mesuré : **0,00 record de proximité/jour** pendant 2000 jours.
3. **Le dernier niveau a le budget le plus serré.** Vérifié via `env.max_steps` :

   | Niveau | Grille | `max_steps` | Objets |
   |---|---|---|---|
   | Collège | 6×6 | 360 | 3 |
   | **Doctorat** | **25×25** | **120** ⚠️ | **6** (5 portes) |

   **2× moins de temps pour une carte 17× plus grande.** Pas difficile — infaisable.

**💡 LA REFONTE PROPOSÉE : 14 paliers au lieu de 5**

MiniGrid expose **58 environnements**, le projet en utilise 5. Le programme proposé n'ajoute
**qu'une compétence par étape** : `Empty-5x5` → `Empty-Random-6x6` → `Empty-8x8` →
`SimpleCrossing` (contourner) → `LavaGap` (danger) → `Fetch` (ramasser) → `GoToDoor` →
`DoorKey-5x5/6x6/8x8` (même tâche, 3 échelles) → `Unlock` → `UnlockPickup` → `MemoryS7` →
`MultiRoom-N2` → `MultiRoom-N4`.

Plus trois changements d'accompagnement, **tous touchant des invariants** donc soumis à
décision utilisateur : promotion sur taux glissant (au lieu de 2 victoires consécutives),
guidage dégressif (au lieu d'une coupure nette), et **redescente possible** de palier.

| Fichier modifié | Changement |
|-----------------|------------|
| `docs/fonctionnement/Parcourt_readme.md` | **§6bis** — diagnostic chiffré, les 3 défauts, la refonte à 14 paliers, ce qu'il faut mesurer d'abord ; en-tête et TdM mis à jour |

---

## [34.0-fix2-experimental] - 2026-08-06

### La référence du plancher ne doit jamais rétrécir + validation en conditions réelles

| Type | Details |
|------|---------|
| **Commit** | `9a4659e` |
| **Catégorie** | fix (critique, complète le fix1) |
| **Impact** | **Critique** — sans ce correctif, chaque neurogenèse divisait la protection |

**✅ D'ABORD : LE FIX1 EST VALIDÉ EN CONDITIONS RÉELLES**

Trois runs successifs sur cerveaux neufs, avec le correctif :

| Run | Jours | Couches mortes | `porte_visuelle` | Victoires |
|---|---|---|---|---|
| 1 | 100 | **0 / 11** | 23,7 % | 4 |
| 2 | **200** | **0 / 11** | 24,6 % | 5 |
| 3 | **700** | **0 / 11** | 11,0 % | **8** |

Le run à 200 jours dépasse les **121 nuits** où l'ancien code commençait à effacer. À
comparer au run `060820260038_V34_1500_RMD` (avant correctif) : **8 couches sur 11 à
zéro**.

Les victoires progressent (4 → 5 → 8) : avec un bus vivant, l'agent apprend enfin.

⚠️ **Le plancher mord fort** : à j700, **6 couches sur 11 sont collées à 10,0 %** — sans
lui elles seraient mortes ou mourantes. Ce n'est pas un garde-fou dormant, c'est lui qui
maintient activement le cerveau en vie chaque nuit. Le déséquilibre de fond (érosion >
apprentissage) subsiste ; le plancher empêche la mort, il ne rétablit pas l'équilibre.

**🔴 LE BUG DÉCOUVERT PAR LE TEST 2 : la neurogenèse affaiblissait la protection**

`agrandir()` recopie les poids anciens (déjà érodés, parfois au plancher) et n'initialise à
neuf que les dimensions ajoutées. La norme du tenseur agrandi peut donc être **bien plus
petite** que la norme d'origine. Mesuré :

```
naissance            : norme_naissance = 5.31290  → plancher 0.53129
après 200 nuits      : norme réelle    = 0.53129  (au plancher)
après neurogenèse    : norme_naissance = 0.73749  → plancher 0.07375   ⚠️ ÷7
```

**Chaque neurogenèse divisait le garde-fou par ~7.** Un cerveau qui grandit beaucoup aurait
fini sans protection — le fix1 se serait auto-annulé sur la durée.

**✅ LE CORRECTIF**

`norme_naissance = max(ancienne_référence, nouvelle_norme)` : la protection ne peut que
**croître avec le substrat**, jamais décroître avec l'usure.

Vérifié sur 4 neurogenèses en cascade (16 → 80 dims, 200 nuits d'érosion entre chacune) :

```
dim_bus  16 →  32 →  48 →  64 →  80
norme_naissance : 5.31290 (STABLE sur les 5 étapes)
plancher        : 0.53129 (STABLE)
synapses        : 4704/4704 → 7056/7056 → 9408/9408 → 11760/11760  (toutes vivantes)
```

**🧪 LES TROIS TESTS**

| Test | Résultat |
|---|---|
| **1. L'oubli reste-t-il gradué ?** | ✅ à 50 nuits : 10 % (m=0) / 28 % (m=0,5) / 78 % (m=0,9). Sur le long terme toute myéline < 0,85 atteint le plancher — c'est la nature géométrique de l'érosion, le plancher **borne** sans moduler |
| **2. Neurogenèse** | 🔴 bug trouvé → corrigé (ci-dessus) |
| **3. Reprise de `.brain` réels** (300 nuits + nuit complète) | ✅ `V34fix1_900` : 11 760 nz conservés · `V33_5000j` : 1 728 nz, norme **remontée** 0,458 → 1,014 (il était **sous** le plancher) · `V34_1500` : reste mort (0 × k = 0, attendu) |

| Fichier modifié | Changement |
|-----------------|------------|
| `src/naulthene/cerveau/noyau.py` | `agrandir()` : `norme_naissance` prend le **maximum** au lieu d'écraser |

**🗂️ ARCHIVAGE**

Tous les `.brain` antérieurs déplacés dans `brains/old_testV30-V34/` (13 fichiers, v30 →
v34). Seul `060820262236_V34fix1_900_RMD.brain` reste actif — le premier cerveau vivant et
gagnant depuis le début de ce diagnostic.

---

## [34.0-fix1-experimental] - 2026-08-06

### 🔴 CRITIQUE — L'EXTINCTION SYNAPTIQUE : le cerveau devenait aveugle et sourd

| Type | Details |
|------|---------|
| **Commit** | `15e3aa9` |
| **Catégorie** | fix (critique) |
| **Impact** | **Critique** — rendait tout entraînement long depuis zéro structurellement impossible |

**🩺 LE SYMPTÔME**

Le cerveau `060820260038_V34_1500_RMD` (neuf, 1500 jours) mesuré après son run :

| Couche | base_weight non nuls |
|---|---|
| `porte_visuelle` | **0 / 11 760** ☠️ |
| `porte_auditive` | **0 / 10 400** ☠️ |
| `hippocampe` | **0 / 12 800** ☠️ |
| `fusion_memoire` | **0 / 12 800** ☠️ |
| `analyseur` | **0 / 6 400** ☠️ |
| `generateur_attente` | **0 / 7 040** ☠️ |
| `generateur_attente_audio` | **0 / 7 040** ☠️ |
| `tete_requete` | **0 / 400** ☠️ |
| `integrateur_bio` | 1 032 / 9 120 |
| `tete_motrice` | 307 / 640 |

**8 couches sur 11 entièrement à zéro.** L'agent était littéralement aveugle et sourd :
`bus_latent` nul ⇒ JEPA nul (`Erreur JEPA moy: 0.0000`) ⇒ C2 = `[0,0,0,0,0,0,0]` ⇒
politique réduite au **hasard uniforme** (entropie 1.94587 pour un maximum ln(7)=1.94591).

**🔬 LA MÉCANIQUE, EN TROIS MAILLONS**

1. `myeline_M = max(myeline_M, |annexe_weight|)` — la myéline ne peut venir **que** du
   gradient. Un agent sans récompense a des gradients infimes ⇒ myéline ≈ 0.
2. L'érosion vaut alors `base *= (1 − λ)` à **taux plein** chaque nuit. Avec λ=0.05, un
   poids de 0.05 tombe sous le seuil de pruning (1e-4) en **121 nuits**.
3. L'Étape 4 met à `0.0` tout ce qui passe sous 1e-4 — **définitivement** (base ET
   `myeline_M`, donc sans retour possible).

Boucle auto-renforçante : pas de récompense → pas de myéline → érosion → moins de
perception → encore moins de récompense.

**⚠️ POURQUOI LA PROTECTION EXISTANTE N'A JAMAIS FONCTIONNÉ**

`SEUIL_CRISTAL = 0.80` alors que la myéline maximale **mesurée** sur les cerveaux du dépôt
est de **0.0038** — un seuil **210× trop haut**. Compteur `cristallisee` :

```
5000j    : 0 / 11 760 synapses cristallisées
700j     : 0 / 11 760
V34_1500 : 0 / 11 760
```

**La Cristallisation Souple de la v26.0 ne s'est jamais enclenchée une seule fois, sur
aucun cerveau.** Ce n'était pas un réglage à ajuster : une échelle qui ne correspondait à
rien de réel.

Le précédent était pourtant connu : `ATTENUATION_EROSION_AUDIO_DEBUT` (v24.0-fix1)
corrigeait déjà « zéro exact après 1000 nuits d'érosion non amortie » — mais **uniquement
sur les 3 couches audio**, et par un facteur daté au palier vocal.

**✅ LE CORRECTIF — le Plancher Vital**

Deux garde-fous qui ne dépendent d'**aucun seuil absolu de myéline** :

| Garde-fou | Effet |
|---|---|
| `PLANCHER_POIDS_VITAL = 1e-3` | une synapse déjà faible mais vivante n'est **plus érodée** |
| `FRACTION_NORME_MIN_COUCHE = 0.10` | la couche conserve ≥ 10 % de sa **norme de naissance** |

Ce sont des **bornes**, pas des valeurs de fonctionnement (doctrine du projet) : la
quantité réellement érodée reste émergente, seul son plafond est fixé. L'oubli reste
possible — l'**extinction** ne l'est plus.

Nouveau buffer `norme_naissance` par couche (référence **absolue**). Le pruning de
l'Étape 4 passe de `1e-4` à `1e-12` : il ne nettoie plus que ce qui est déjà mort.

⚠️ **Erreur commise et corrigée en cours de route** : la première version bornait la norme
relativement à la **nuit précédente**. Ça ne borne rien cumulativement (0.95 × N_veille
décroît indéfiniment) — simulation à l'appui, la norme tombait quand même à 1 %. D'où la
référence absolue à la naissance.

**🧪 VALIDATION**

| Test | Avant | Après |
|---|---|---|
| 3000 nuits sans myéline (λ=0.05) | extinction totale | **11 760 vivantes, norme stable à 10 %** |
| 3000 nuits (λ=0.025) | extinction totale | **11 760 vivantes, 10 %** |
| Oubli toujours actif ? (myéline=1.0) | — | **100 % conservé** ✅ |
| Cerveau neuf, 150 jours | — | **9 408 vivantes, bus vivant, C2 actif, 5 victoires** |
| Rétrocompat `.brain` (5000j/700j/V34) | — | **acquis intacts** (1728 nz, norme 0.45838) |
| **Nuit complète post-chargement** | — | **passe** (test exigé par `CLAUDE.md`) |

**🐛 BUG CONNEXE CORRIGÉ — fausse détection de greffe**

Le nouveau buffer `norme_naissance`, absent de tout `.brain` antérieur, apparaissait dans
`missing_keys` sur les 12 couches — faisant croire à une greffe massive et
**réinitialisant Adam sans raison à chaque chargement**. Exclu de la détection : il ne
participe à aucun calcul de forme, et sa valeur par défaut est correcte pour un cerveau
déjà entraîné.

| Fichier modifié | Changement |
|-----------------|------------|
| `src/naulthene/cerveau/noyau.py` | `PLANCHER_POIDS_VITAL`, `FRACTION_NORME_MIN_COUCHE`, buffer `norme_naissance` (+ mise à jour dans `agrandir`), plancher vital dans `cycle_sommeil`, pruning 1e-4 → 1e-12 |
| `src/naulthene/cerveau/persistance.py` | `norme_naissance` exclu de `greffe_detectee` |

**📌 CONSÉQUENCE POUR LES CERVEAUX EXISTANTS**

`060820260038_V34_1500_RMD` est **irrécupérable** : ses poids sont à zéro exact, le
plancher ne peut pas ressusciter ce qui n'existe plus (0 × k = 0). Les cerveaux `5000j` et
`700j` sont sauvés — le premier était d'ailleurs **sous le plancher** (norme 0.458 contre
un plancher de 1.018) et remonte dès la première nuit.

---

## [34.0-etape0-experimental] - 2026-08-06

### Télémétrie de calibrage Fatigue/Mortalité/Soin — et le fait qui bloque le chantier

| Type | Details |
|------|---------|
| **Commit** | `3f4157d` |
| **Catégorie** | feat (télémétrie pure, expérimental) |
| **Impact** | **Aucun sur le comportement** — invariance validée par empreinte MD5 |

**🔒 INVARIANCE PROUVÉE**

Empreinte `efb6ff6506e852ed` **identique** avec et sans les appels de télémétrie
(neutralisation différentielle à graine fixée, 400 ticks, protocole v33). Aucune valeur
mesurée n'est lue par `penser()`, le gradient ou la dopamine.

**📊 CE QUI A ÉTÉ MESURÉ** (`REFERENCE_5000j`, 2 j × 400 ticks, 5 niveaux)

| Niveau | Ressources | **Autonomie** | Ticks critiques | Déficit moy / max |
|---|---|---|---|---|
| Primaire | 8 | **0,0 %** | **100 %** | 2,49 / 2,95 |
| Collège | 8 | **0,0 %** | **100 %** | 2,93 / 3,00 |
| Lycée | 8 | **0,0 %** | **100 %** | 2,94 / 3,00 |
| Université | 10 | **0,0 %** | **100 %** | 2,98 / 3,00 |
| Doctorat | 16 | **0,0 %** | **100 %** | 2,99 / 3,00 |

**🔴 LE FAIT QUI CHANGE LE PLAN : l'agent est déjà mort.**

`Autonomie_Jauges = 0,0 %` sur les 5 niveaux : à **aucun tick** l'agent ne maintient ses
trois jauges au-dessus du seuil critique. Déficit à **2,99 sur 3,00** — satiété,
hydratation et stimulation sont à **0,00** en permanence.

Conséquence : **l'Étape 3 (la mort) est déjà satisfaite par l'état actuel.** Un seuil létal
tuerait l'agent au premier tick, sur tous les niveaux, quelle que soit sa compétence.

**🟢 LE BLOCAGE §7.4 EST LEVÉ**

Les cartes contiennent **8 à 16 sources** de nourriture/eau, **y compris au Doctorat**.
L'odorat à 0,0 % du run de 5000 jours n'était pas une absence de ressources, mais la
conséquence d'un agent qui ne les atteint jamais. Peupler l'environnement n'est plus un
préalable.

**🟠 LE RISQUE §4 EST CONFIRMÉ ET CHIFFRÉ**

Avancer coûte **0,510**, tourner **0,270** — un facteur **1,9** — et l'agent avance
**6,5 %** du temps. Une fatigue branchée naïvement sur `calculer_effort_metabolique`
renforcerait ce biais.

| Fichier modifié | Changement |
|-----------------|------------|
| `src/naulthene/cerveau/noyau.py` | 14 compteurs dans `_reinitialiser_buffers_journee`, accumulation en lecture seule dans `traiter_tick`, `_compter_ressources_grille()` (1×/épisode), ligne console `Calibrage v34`, 14 clés `Calibrage_*` inconditionnelles |
| `docs/ameliorations/CONCEPTION_v34_fatigue_mortalite.md` | cadrage complet + section « Étape 0 livrée » avec les mesures |

---

## [33.1-experimental] - 2026-08-05

### Le Banc d'Ablation — la lobotomie contrôlée

| Type | Details |
|------|---------|
| **Commit** | `3f4157d` |
| **Catégorie** | feat (instrument de diagnostic, expérimental) |
| **Impact** | Fonctionnel (**instrument en lecture seule** — ne modifie aucun `.brain`, n'entraîne rien) |

**🔬 POURQUOI — le run de 5000 jours a dit « non »**

Le run `az794yzw` (jours 5001→10000, cerveau `040820262343_V33_5000_RMD`) répond sans
ambiguïté à la question « évolution ou non » :

| Indicateur | j5001-6000 | j9001-10000 | Verdict |
|---|---|---|---|
| **Victoires cumulées** | **69** | **69** | **0 en 5000 jours** |
| Portes / jour | 0,77 | 0,81 | plat |
| Records / jour | 8,96 | 9,11 | plat |
| Erreur JEPA | 0,00067 | 0,00064 | plat |
| Dopamine | 6,20 | 6,43 | plat |
| Neurogenèse | 80 dims | 80 dims | **aucune** |
| Sursauts de Volonté | — | — | **0 sur 5000 jours** |

Dernière victoire : **jour 3510**, soit 6490 jours avant la fin du run. L'agent a
**convergé** — il n'apprend plus, ne régresse pas. Le temps seul ne débloque plus rien.

Une ablation, elle, répond **en binaire, par composant** : ce qui ne dégrade rien quand on
le coupe ne portait rien.

**🧠 CE QUE LE BANC A DÉJÀ MESURÉ — C2 est nuisible au Primaire**

Reproduit sur **3 graines indépendantes** (`Empty-8x8`, le niveau le plus simple, franchi
au jour 66) :

| Graine | Témoin | `c2_coupe` | Δ |
|---|---|---|---|
| 1789 | **0,0 %** | **35,0 %** | **+35 pp** |
| 7 | **0,0 %** | **20,0 %** | **+20 pp** |
| 424242 | **0,0 %** | **33,3 %** | **+33 pp** |

Le diagnostic explique le mécanisme :

| Mesure | Témoin | `c2_coupe` | Lecture |
|---|---|---|---|
| **accord C1↔C2** | **0,000** | 1,000 | C2 contredit le réflexe à **100 %** des ticks |
| **sur-place** | **0,956** | 0,897 | l'agent ne change pas de case 95,6 % du temps |
| **couverture** | **0,033** | 0,068 | ×2 de cases explorées sans C2 |
| dist. min. au But | 4,9 | **2,1** | il s'approche physiquement plus près |

`accord_c1_c2 = 0,000` est le chiffre décisif : **C1 et C2 ne sont jamais d'accord**, pas
une seule fois sur 16 épisodes. Combiné à des logits d'instinct ~30× plus faibles que
l'arbitrage (±0,03 contre ±0,74), cela signifie que `logits_instinct + valeurs_simulees ×
force` est **entièrement dominé par C2**, et que le réflexe n'a aucun pouvoir correcteur.

⚠️ Mesuré **au Primaire seulement**. C2 pourrait être utile au Doctorat, où la
planification longue a un sens — c'est ce que le banc complet (65 cellules) doit trancher.

**⚙️ CE QUI A ÉTÉ CONSTRUIT**

| Fichier | Changement |
|---|---|
| `src/naulthene/instruments/banc_ablation.py` | **nouveau** — 13 lésions × 5 niveaux, copie par cellule, diagnostic C1/C2, publication W&B |
| `docs/fonctionnement/LANCEMENT.md` | **§15** — lancement, catalogue des lésions, grille de lecture |
| `docs/ameliorations/les_sens_combinatoire.md` | **§9 bis** — disponibilité réelle des sens mesurée sur ce run |

Treize lésions, en deux familles : **sens** (vue, ouïe, toucher, odorat, goût, Exo-Sens,
vecteur bio entier) et **cognition** (C2 coupé, C2 myope, épisodique, spatiale,
hippocampe).

**🐛 ERREUR DE CONCEPTION CORRIGÉE — la politique gloutonne**

La première version du banc utilisait `argmax` pour « supprimer le hasard », présenté comme
une garantie de rigueur. **C'était faux, et mesurable** : en argmax, l'agent joue l'action 0
(tourner à gauche) **en boucle infinie** et échoue même sur `Empty-8x8`.

La cause : un agent entraîné par **REINFORCE apprend une politique stochastique**. Son mode
déterministe n'est pas « sa meilleure version », c'est un régime qu'il n'a **jamais connu**
pendant l'entraînement. Mesurer l'argmax, c'est mesurer un agent qui n'existe pas.

Corrigé par un `multinomial` identique à `traiter_tick`, avec un générateur à graine fixée :
**la reproductibilité vient de la graine, jamais de la suppression du hasard.** Le premier
run a été tué avant de produire 65 cellules de résultats faux.

**🔒 LES CINQ GARANTIES**

1. Le cerveau de référence n'est **jamais** touché — une copie par cellule, supprimée après
2. **Aucun apprentissage** — `torch.no_grad()`, ni `apprendre_journee`, ni `executer_nuit`,
   ni `sauvegarder` : un cerveau qui apprendrait mesurerait l'apprentissage, pas la lésion
3. **Graine identique** pour toutes les cellules — mêmes cartes, même ordre
4. **Politique stochastique**, jamais gloutonne (voir ci-dessus)
5. **Masques, jamais d'amputation de poids** — supprimer une couche déclencherait une greffe,
   et on mesurerait la greffe

Le seuil de verdict est l'**intervalle de confiance à 95 %** de chaque cellule, jamais un
chiffre fixe : un écart sous la marge d'erreur est déclaré `inerte`, pas « petit effet ».

---

## [33.0-etape0.5-experimental] - 2026-08-04

### Le Test d'Ablation Inversée — la quête auto en Mode Libre + LECTURE DU RUN DE 700 JOURS

| Type | Details |
|------|---------|
| **Commit** | `4ccdffc` |
| **Catégorie** | feat (instrument de diagnostic, expérimental) |
| **Impact** | Fonctionnel (**inactif par défaut** — `QUETE_AUTO_EN_MODE_LIBRE = False` ⇒ comportement bit-identique à la v32.0) |

**🔬 LA MESURE D'ABORD — ce que le run de 700 jours a révélé**

Un run complet (`50ac6kz0`, cerveau neuf, v32.0, 700 jours) a été analysé **avant** d'écrire
cette version. Il tranche le débat ouvert par la v33.0-etape0 :

| Fait mesuré | Valeur |
|---|---|
| Arrivée au Palier 7 | **jour 94** |
| Jours passés au Palier 7 | **607** |
| Réussites du Palier 7 | **1** — le jour 94 lui-même |
| Jours avec récompense terminale > 0 | **0** |
| Portage (clé en main) après J94 | **51,4 %** des ticks |
| Portes franchies après J94 | **42 jours sur 607** |
| Sorties après J94 | **0** |
| Sursauts de Volonté | 101, dont **0 % de victoires** |
| Ressources consommées | **1,4 / jour** |

**Trois conclusions, dont une qui INFIRME une hypothèse de travail :**

1. **Δt1 et Δt2 fonctionnent.** 51,4 % de portage et 42 franchissements de porte : l'agent
   prend la clé, la transporte, déverrouille et franchit. Ce n'est pas un agent perdu.
2. **Δt3 est un mur absolu.** 42 franchissements pour **zéro** sortie. Pas « lent » :
   **jamais** — exactement la distinction que `extraire_deltas` encode avec `None` plutôt
   qu'avec `0`.
3. **❌ L'hypothèse du conflit viscéral est INFIRMÉE.** 1,4 ressource par jour : l'agent
   ne « broute » pas en portant la clé. Cette piste, envisagée dans le cadrage v33, est
   donc écartée par la mesure — comme la v31.1 avait écarté « le rêve cristallise des
   réflexes d'échec ».

**🎯 Le détail qui établit la causalité** : la **seule** victoire est le **jour 94**, celui
de la promotion — donc le dernier jour où l'agent travaillait encore sous guidage. Dès le
décrochage de `RECOMPENSE_APPROCHE_BUT`, plus jamais aucune sortie en 606 jours. La victoire
s'est produite précisément quand la béquille était là.

*(Note : les franchissements de porte s'accélèrent nettement en fin de run — jours 600-697.
L'agent **apprenait encore** à atteindre la porte ; ce progrès ne pouvait simplement
déboucher sur rien.)*

**L'instrument — rendre au dernier segment le gradient qui lui manque**

`DetecteurProgresPersonnel` (3b, « ai-je battu mon record de proximité au But ? ») est
historiquement **inactif sur DoorKey**, pour éviter un double guidage avec
`RECOMPENSE_APPROCHE_BUT`. **Cette exclusion est caduque en Mode Libre** :
`recompense_continue` n'est ajoutée à `recompense_interne` que si `not etat.mode_libre`.
Dès le Palier 5, la béquille DoorKey est déjà coupée — il n'y a plus de double guidage à
craindre, seulement un segment porte→but dépourvu de tout signal.

Nouveau drapeau `QUETE_AUTO_EN_MODE_LIBRE` (**`False` par défaut**). À `True`, la quête auto
s'active sur DoorKey **en Mode Libre uniquement** — jamais en Mode Guidé, où les deux
guidages coexisteraient réellement.

⚠️ **C'est un INSTRUMENT DE DIAGNOSTIC, pas une mécanique cognitive.** S'il débloque le
Palier 7, la nature du blocage est prouvée (rareté du signal) et il doit être **remis à
`False`** : la vraie solution doit émerger de la mémoire (valence + replay orienté), jamais
d'une béquille permanente.

**Une décision de conception : une seule source de vérité**

Cinq sites lisaient `not etat.doorkey_actif` en parallèle (init d'épisode ×2, évaluation du
tick, bilan de nuit). `_quete_auto_active(etat)` les centralise. Motif : les laisser diverger
produirait ici le pire bug possible — un détecteur qui **évalue sans avoir été
réinitialisé** compare la distance courante au record d'un épisode précédent, donc sur une
carte régénérée dont le But a bougé.

| Fichier modifié | Changement |
|-----------------|------------|
| `src/naulthene/cerveau/noyau.py` | Constante `QUETE_AUTO_EN_MODE_LIBRE` (section 4) documentée par la mesure ci-dessus ; helper `_quete_auto_active()` ; 4 sites de lecture unifiés (2 × `reinitialiser_episode`, `evaluer_tick`, bilan de nuit) ; suffixe `[ABLATION INVERSÉE]` sur la ligne « Quête Auto » ; clé W&B `Jalon_Quete_Auto_Ablation` |

**Validation** :
- **Non-régression PROUVÉE** : à `False`, l'empreinte MD5 des 400 actions à graine fixée est
  **identique** (`6573f2fd045d`) à la v33.0-etape0 — le drapeau au repos ne change rien.
- **Table de vérité complète, 6/6 cas** : hors DoorKey → toujours actif (historique) ;
  DoorKey **Guidé** → jamais actif, quel que soit le drapeau (le double guidage reste
  interdit) ; DoorKey **Libre** → actif si et seulement si le drapeau est levé.
- **Effet réel vérifié sur DoorKey-6x6 en Mode Libre** (800 ticks + nuit) : drapeau `False`
  → **0** record de proximité et clé W&B à 0 ; drapeau `True` → **5** micro-récompenses de
  proximité et clé W&B à 1. Le gradient manquant est bien rétabli, et le détecteur est
  **réinitialisé** (pas seulement évalué).
- Ligne de bilan vérifiée : `🧭 5 nouveaux records de proximité au But [ABLATION INVERSÉE — Mode Libre DoorKey]`.

⚠️ **Ce que cette version ne prouve PAS.** Elle livre l'instrument, elle ne rend aucun
verdict : le test doit tourner sur un cerveau **déjà au Palier 7**. Et même si l'ablation
débloque la sortie, les 42 franchissements ne représentent que **7 %** des jours — le désert
Δt3 est le blocage **principal**, pas nécessairement le seul.

---

## [33.0-conclusion] - 2026-08-05

### Le cursus est terminé — le blocage n'existait pas, la v33 est close sans être ouverte

| Type | Details |
|------|---------|
| **Commit** | `6945e24` |
| **Catégorie** | docs (clôture de cycle) + archivage |
| **Impact** | Documentation — **aucun code modifié** |

**Run de 5000 jours (`8q37yinf`, cerveau neuf, v33 instrumentée). L'agent a franchi les CINQ niveaux du `PROGRAMME` et atteint le Doctorat.**

| Jour | Promotion |
|---|---|
| 66 | Primaire → Collège |
| **3335** | Collège → **Lycée** ← le déblocage |
| 3465 | Lycée → Université |
| 3509 | Université → **Doctorat** |

**69 victoires** au total, contre 9 sur le run de 700 jours.

**La tendance, mesurée sur 45 intervalles (Collège / DoorKey)**

| | Moyenne |
|---|---|
| 1ʳᵉ moitié | 88,3 j |
| 2ᵉ moitié | 57,7 j |
| **Ratio** | **0,65 ↘️ se rapprochent** |

Par quart : **126 → 50 → 65 → 51** jours. Cadence : 4 victoires par tranche de 500 jours au
début, **13** sur la tranche 2500-2999. Avec 45 intervalles, le résultat est solide — plus
rien à voir avec les 4 points du run précédent. **L'agent apprend réellement, très lentement.**

**Trois diagnostics successifs, tous INFIRMÉS par un run plus long**

| Conclusion tirée | Fondée sur | Verdict du run de 5000 jours |
|---|---|---|
| « Δt3 est un **mur absolu**, l'agent ne sort jamais » | run 700 j, 1 victoire | **Faux** — 69 victoires, cursus complet |
| « Les victoires sont du **bruit stationnaire**, il ne retient rien » | 6 intervalles lus à la main | **Faux** — ratio 0,65, tendance nette |
| « La promotion est **mathématiquement inatteignable** (2 victoires consécutives exigées, 17 j d'écart minimum) » | run 700 j | **Faux** — 3 enchaînements à 2 jours d'écart (j1083→1085, j1839→1841, j2769→2771) |

**La leçon méthodologique — et c'est le vrai résultat de ce cycle**

Le projet a une doctrine explicite depuis la v30.1 : *instrumenter d'abord, calibrer ensuite*.
Ce cycle en révèle le corollaire manquant : **une mesure juste sur un échantillon trop court
produit une conclusion fausse**. Les trois diagnostics ci-dessus étaient rigoureux, chiffrés,
reproductibles — et faux, parce que 700 jours ne suffisaient pas à observer un apprentissage
dont la constante de temps est de l'ordre du millier de jours.

Le chantier Valence & Replay Orienté aurait traité un problème **qui n'existe pas**.

**État actuel — le Doctorat est une phase lente, pas un mur**

Depuis le jour 3510 : une seule victoire, puis 1490 jours sans. Mais les indicateurs montent :

| Tranche de 300 j | Records de proximité au But / jour |
|---|---|
| 3510-3809 | 7,68 |
| 4110-4409 | 8,09 |
| 4710-5009 | **9,14** |

**+19 %**, et l'erreur JEPA continue de descendre (0,00093 → 0,00068) : l'agent modélise
`MultiRoom` de plus en plus finement et s'approche du but de mieux en mieux. C'est
**exactement** le motif observé au Collège (3269 jours de montée avant la percée du j3335) —
et le Doctorat n'a que 1490 jours derrière lui.

| Fichier modifié | Changement |
|-----------------|------------|
| `docs/ameliorations/CONCEPTION_v33_memoire_emotionnelle.md` | **Archivé** (`git mv`), bandeau expliquant que la prémisse est infirmée et ce qui reste valable (le `abs()` qui détruit la valence, les options écartées, les risques) ; 4 liens entrants corrigés |
| `docs/Old_Archive_rmd/README.md` | Entrée d'index avec statut « jamais ouverte — prémisse infirmée » |
| `docs/fonctionnement/CHANGELOG.md`, `readme_fr.md`, `docs/fonctionnement/LANCEMENT.md` | Cette entrée + résultats du run |

**Ce qui reste acquis de ce cycle** : trois instruments de mesure livrés et validés
(`ChronometreJalonsDoorKey`, `QUETE_AUTO_EN_MODE_LIBRE`, chronologie des victoires), tous
**purement observationnels** — empreinte MD5 des 400 actions inchangée (`6573f2fd045d`) à
travers les quatre étapes. Ce sont eux qui ont permis de trancher, et ils resteront utiles
pour juger toute mécanique future.

⚠️ **Point de vigilance pour la suite** : le bus est à **80 dims**, le plafond
`DIM_BUS_MAX` est à **96**. La neurogenèse va bientôt s'arrêter. Si l'agent stagne au
Doctorat **après** avoir atteint 96 dims, ce sera un signal de nature différente — un manque
de **capacité**, non de temps — et cette fois un motif légitime d'intervention.

---

## [33.0-etape0.6-fix1-experimental] - 2026-08-04

### La tendance était fausse — segmentation des intervalles par contexte

| Type | Details |
|------|---------|
| **Commit** | `625bd81` |
| **Catégorie** | fix (correctif d'un défaut de conception de la v33.0-etape0.6) |
| **Impact** | Fonctionnel (lisibilité d'une métrique de diagnostic — aucun impact sur la décision) |

**Bug diagnostiqué sur le run `78859bgs` (700 jours) : la métrique affichait l'INVERSE de la réalité.**

Le bilan annonçait `tendance 34.89 ↗️ s'espacent` — donc un agent qui **régresse** — alors
que la lecture manuelle des logs montrait qu'il **s'améliorait** en fin de run.

**La cause : un ratio calculé sur des tâches sans commune mesure.**

Les 9 victoires du run n'étaient pas de même nature :

| Jours | Contexte | Nature |
|---|---|---|
| 49, 52, 64, 66 | Primaire (`Empty-8x8`) | victoires **faciles**, avant que le Palier 7 existe |
| 67 | bascule Collège | transition |
| 115, 583, 623, 695 | Collège, **Palier 7** | les seules victoires qui nous intéressent |

Le ratio comparait donc la première moitié (« Primaire », intervalles de 1 à 12 jours) à la
seconde (« Palier 7 », intervalles de 40 à 468 jours). Le `34.89` ne mesurait pas une
régression de l'agent : il mesurait **l'écart de difficulté entre deux niveaux du cursus**.

C'est un défaut de conception de la v33.0-etape0.6, pas un défaut du cerveau — et il aurait
conduit à trancher le chantier v33 sur un chiffre faux.

**Le correctif : un intervalle n'a de sens qu'à difficulté constante**

La série d'intervalles est désormais **segmentée par contexte** `(niveau_actuel, palier_cible)`.
Dès que le contexte change, la série est archivée (`intervalles_contexte_prec`, lisible en
télémétrie) et repart à zéro — exactement comme
`memoire_episodique_spatiale.reinitialiser_niveau()` efface des coordonnées qui n'ont plus
de sens sur une autre carte.

Trois points de conception :

1. **`victoires_totales` et `jour_derniere_victoire` ne sont JAMAIS remis à zéro** : ils
   comptent une vie entière. Seule la série d'intervalles — le support du ratio — est
   contextuelle.
2. **`jour_derniere_victoire` est délibérément CONSERVÉ** au changement de contexte : le
   premier intervalle de la nouvelle série mesure ainsi le temps qu'il a fallu pour
   **regagner à la nouvelle difficulté**, ce qui est une information utile, pas un artefact.
3. **Le contexte est affiché avec le chiffre** (`[P7] intervalle moyen 81 j (n=4)`). Sans
   lui, un « intervalle moyen » ne dit pas s'il parle de Primaire ou du Palier 7 — c'est
   précisément l'ambiguïté qui a produit le bug. Le `(n=…)` rappelle en outre combien de
   victoires soutiennent réellement la tendance.

**Effet mesuré sur le run réel** (calendrier `78859bgs` rejoué) :

| | Intervalles | Verdict |
|---|---|---|
| **Avant** | `[3, 12, 2, 1, 48, 468, 40, 72]` | `34.89 ↗️ s'espacent` ❌ |
| **Après** | `[48, 468, 40, 72]` (Palier 7 seul) | `0.22 ↘️ se rapprochent` ✅ |

**Le verdict est inversé**, et le nouveau est conforme à la lecture manuelle : après un trou
de 468 jours, les victoires reviennent tous les 40-72 jours.

| Fichier modifié | Changement |
|-----------------|------------|
| `src/naulthene/cerveau/noyau.py` | `contexte_victoires` + `intervalles_contexte_prec` dans `EtatCognitif` ; détection du changement de contexte dans `executer_nuit` (lue chaque nuit, pas seulement les jours de victoire) ; contexte et effectif affichés au bilan ; clé `Victoire_Serie_Contexte_N` |
| `src/naulthene/cerveau/persistance.py` | 2 clés supplémentaires, rechargement défensif par `.get` |

**Validation** :
- **Calendrier RÉEL rejoué** : `34.89 ↗️` → `0.22 ↘️`, verdict inversé et conforme à la
  lecture manuelle des logs.
- **Coupure de contexte** vérifiée en intégration (bascule `Empty` → `DoorKey`) : série
  remise à zéro, ancienne série archivée, `victoires_totales` et `jour_derniere_victoire`
  **conservés**.
- **Non-régression de la détection** : sur une série homogène à contexte unique, un vrai
  apprentissage reste détecté (`0.23 ↘️`).
- **Persistance** des 2 nouveaux champs vérifiée (sauvegarde + rechargement).
- **Invariance comportementale** : empreinte MD5 des 400 actions inchangée (`6573f2fd045d`).

⚠️ **Conséquence sur le diagnostic v33.** Le run `78859bgs`, correctement lu, suggère un
**apprentissage réel mais très lent** au Palier 7 (468 → 40 → 72 jours), et non le processus
purement stationnaire supposé jusqu'ici. Cela **affaiblit** l'argument « l'agent ne retient
rien » qui justifiait le Replay Orienté. À confirmer : la série ne compte que 4 intervalles,
et le trou de 468 jours pèse lourd dans le ratio. Un run long sur cette métrique corrigée
doit trancher **avant** d'ouvrir le chantier Valence & Replay.

---

## [33.0-etape0.6-experimental] - 2026-08-04

### Chronologie des Victoires — hasard stationnaire ou apprentissage lent ?

| Type | Details |
|------|---------|
| **Commit** | `26e1e50` |
| **Catégorie** | feat (télémétrie, expérimentale) |
| **Impact** | Fonctionnel (observabilité — **aucun** impact sur la décision, le gradient ou la dopamine) |

**Demande utilisateur, avant tout correctif : « ajouter une métrique (temps depuis la dernière victoire) pour voir si c'est 100 % aléatoire ou s'il réussit de mieux en mieux. Il faut un maximum de données pour tirer des conclusions. »**

**La question que cette métrique tranche — et pourquoi elle décide du sort de la v33**

L'analyse du run de 700 jours (`icfhotie`) a relevé **7 victoires** au Palier 7, aux jours
93, 153, 191, 281, 298, 407 et 624 — soit des intervalles de **60, 38, 90, 17, 109, 217**
jours. Ces chiffres suggèrent un processus **stationnaire** (l'agent gagne au hasard, à
taux constant, sans jamais retenir), ce qui justifierait le Replay Orienté.

Mais ce constat a trois faiblesses qui interdisent d'en tirer une conclusion :

1. il a été obtenu **à la main**, par `grep` a posteriori sur des logs console ;
2. il repose sur **7 points** — dont 6 intervalles seulement ;
3. il **ne survivrait pas** à une reprise de run : rien n'était persisté.

Deux lectures restent ouvertes, et elles n'appellent pas le même correctif :

| Régime | Signature | Conséquence pour la v33 |
|---|---|---|
| **Stationnaire** | intervalles stables | l'agent ne retient rien → le Replay Orienté est le bon chantier |
| **Convergent** | intervalles qui se resserrent | il apprend déjà, lentement → c'est la **vitesse** qu'il faut traiter, pas la mémoire |

**La mesure**

Quatre champs d'état, **délibérément hors de `_reinitialiser_buffers_journee`** : ce sont
des compteurs de **vie**, pas de journée. Les y placer les remettrait à zéro chaque matin
et détruirait la mesure — piège **inverse** de celui de `score_vocal_jour` (v27.0), où un
compteur journalier cumulait depuis la naissance. Ici, c'est bien le cumul de toute une
vie qui est voulu.

| Clé W&B | Mesure |
|---------|--------|
| `Victoire_Jours_Depuis_Derniere` | fraîcheur du dernier succès (= l'âge de l'agent s'il n'a jamais gagné) |
| `Victoire_Total_Vie` / `Victoire_Taux_Vie` | numérateur brut et taux depuis la naissance |
| `Victoire_Intervalle_Dernier` / `_Moyen` | écarts inter-victoires |
| **`Victoire_Tendance_Ratio`** | **la métrique décisive** — moyenne de la 2ᵉ moitié des intervalles ÷ 1ʳᵉ moitié |

Lecture du ratio : **< 0.8** les victoires se rapprochent (apprentissage) ; **≈ 1.0**
stationnaire (hasard) ; **> 1.25** elles s'espacent (régression). Le bilan console traduit
le chiffre en clair (`↘️ se rapprochent` / `➡️ stationnaire` / `↗️ s'espacent`).

**Deux décisions de conception**

1. **Aucun ratio n'est publié sous 4 intervalles.** En dessous, une seule victoire
   chanceuse ferait basculer le résultat du simple au double : mieux vaut une clé absente
   qu'un chiffre trompeur (règle v29.1).
2. **La première victoire ne crée pas d'intervalle.** Compter « jour 93 » comme un écart
   de 93 jours mélangerait le temps d'apprentissage initial avec les intervalles
   inter-victoires, qui sont la seule vraie mesure.

**Persistance — sans quoi la métrique ne vaudrait rien**

Les quatre champs entrent dans le `.brain`. Sans cela, toute reprise de run repartirait
d'une chronologie vierge, et la question resterait sans réponse précisément sur les
cerveaux qui ont **le plus de vécu**. Lecture **défensive** (`.get`) au chargement : les
`.brain` antérieurs n'ont aucune de ces clés et repartent d'une chronologie vide plutôt
que de faire échouer la résurrection — cohérent avec « greffe par recopie, jamais par
exclusion ».

| Fichier modifié | Changement |
|-----------------|------------|
| `src/naulthene/cerveau/noyau.py` | 4 champs de vie dans `EtatCognitif` (hors `_reinitialiser_buffers_journee`) ; mise à jour dans `executer_nuit` après `victoires_consecutives` ; ligne de bilan « Chrono Victoire » ; **6 clés W&B** |
| `src/naulthene/cerveau/persistance.py` | 4 clés sauvegardées ; rechargement défensif par `.get` |

**Validation** :
- **Calendrier RÉEL rejoué** (jours 93/153/191/281/298/407/624 du run `icfhotie`) →
  intervalles `[60, 38, 90, 17, 109, 217]` exactement reproduits, `jours_depuis_victoire`
  = 76 au jour 700, et la première victoire ne crée bien **aucun** intervalle.
- **Les 3 régimes sont discriminés** sur calendriers synthétiques : convergent → ratio
  `0.19` ; stationnaire → `1.00` ; divergent → `4.83`.
- **Cas limites** : jamais gagné sur 300 jours → compteur = 300, aucun intervalle ; une
  seule victoire → aucun intervalle ; 3 intervalles → **aucun ratio publié**.
- **Persistance** : sauvegarde puis rechargement d'un état à 5 victoires et 4 intervalles
  → valeurs intactes.
- **Rétrocompatibilité sur `.brain` RÉEL** (`020820262017_V31_700_RMD`, 700 jours, bus 48,
  aucune clé v33) : chargement propre, defaults à zéro, puis journée + **nuit complète**
  (69 clés) — leçon v32.0, jamais valider une persistance sur des ticks seuls.
- **Invariance comportementale** : empreinte MD5 des 400 actions à graine fixée inchangée
  (`6573f2fd045d`) — la métrique ne touche ni la décision, ni le gradient, ni la dopamine.

⚠️ **Ce que cette version ne prouve PAS.** Elle rend la question **mesurable**, elle n'y
répond pas : les intervalles du run `icfhotie` ont été rejoués en simulation, jamais
produits par un cerveau instrumenté. Seul un run long avec ces clés dira si
`Victoire_Tendance_Ratio` se stabilise autour de 1.0 (hasard) ou descend (apprentissage) —
et c'est **cette lecture, et elle seule**, qui doit valider ou invalider le chantier
Valence & Replay Orienté.

⚠️ **Un second verrou, indépendant, reste ouvert** (découvert pendant cette analyse) :
`VICTOIRES_REQUISES = 2` exige deux victoires sur des jours **consécutifs**
(`victoires_consecutives` retombe à 0 dès un jour sans victoire), alors que l'écart minimum
observé est de **17 jours**. La promotion de niveau est donc aujourd'hui **mathématiquement
inatteignable** au Palier 7, quel que soit le gain apporté par la v33. Aucun correctif n'est
appliqué ici — arbitrage utilisateur en attente : assouplir la règle (fenêtre glissante) ou
juger la v33 sur `Jalon_Taux_Atteinte_Sortie` sans attendre de promotion.

---

## [33.0-etape0-experimental] - 2026-08-04

### Chronométrie des Jalons DoorKey — mesurer AVANT de refondre la mémoire

| Type | Details |
|------|---------|
| **Commit** | `4ccdffc` |
| **Catégorie** | feat (télémétrie, expérimentale) |
| **Impact** | Fonctionnel (observabilité — **aucun** impact sur la décision, le gradient ou la dopamine) |

**Arbitrage utilisateur : viser la mémoire humaine, mais utiliser le Palier 7 comme juge de paix. Séquencement strict imposé — Étape 0 (télémétrie) « non négociable » AVANT tout chantier de Mémoire Émotionnelle. Voir [CONCEPTION_v33_memoire_emotionnelle.md](../ameliorations/CONCEPTION_v33_memoire_emotionnelle.md) pour le cadrage complet et les options écartées.**

**Le problème : un diagnostic non mesuré.**

Trois analyses successives ont conclu que l'agent bloque au Palier 7 parce que le segment
**porte déverrouillée → sortie** est un « désert de signal » : ni récompense intermédiaire
(`RECOMPENSE_APPROCHE_BUT` est coupée en Mode Libre), ni gradient olfactif (l'odorat ne
porte que sur FOOD/WATER), ni repère spatial (seuls FOOD/WATER sont enregistrés).

**Mais ce diagnostic est une DÉDUCTION DE LECTURE DE CODE, jamais une mesure.** La v31.1
a déjà démontré qu'une intuition forte peut être infirmée par l'instrumentation (« le rêve
cristallise des réflexes d'échec » : faux, `rever()` ne calcule que `perte_jepa`). Refonder
la mémoire sur une hypothèse non chiffrée reproduirait exactement l'erreur que la méthode
v30.1 interdit.

**La mesure — trois deltas et un conflit**

`ChronometreJalonsDoorKey` (nouvelle section **3h**) découpe chaque épisode :

| Delta | Segment | Ce que sa domination signifierait |
|---|---|---|
| **Δt1** | reset → prise de la clé | le problème est en amont, bien avant le Palier 7 |
| **Δt2** | clé → déverrouillage | le goulot est le **transport** (conflit viscéral) → la priorité de la v33 change |
| **Δt3** | déverrouillage → sortie | le **désert de récompense** est confirmé → la conception v33 s'applique telle quelle |

Plus une mesure directe du **conflit viscéral** : `ressources_post_cle` compte les
consommations FOOD/WATER survenues **clé en main**. Si « l'agent erre avec la clé en
cherchant à manger » est vrai, ce compteur le prouve en une courbe.

**La décision de conception qui fonde la métrique : `None` n'est pas `0`.**

Un segment jamais atteint retourne `None`, jamais `0`, et n'entre **ni au numérateur ni au
dénominateur**. Chaque delta porte donc son propre effectif. Sans cette séparation,
« le segment est lent » et « le segment n'est jamais atteint » — deux diagnostics
**opposés** — deviendraient indiscernables dans une moyenne commune. C'est aussi pourquoi
trois **taux d'atteinte** sont loggés à part : un Δt3 rapide sur n=1 et sur n=200 racontent
l'inverse l'un de l'autre.

Le bilan console affiche explicitement `JAMAIS ATTEINT (n=0)` plutôt qu'un `0.0` trompeur.

**Contrat de l'étape 0 — observation pure**

Contrairement à tous les détecteurs de 3a/3b, cette classe ne retourne **aucune récompense
et aucun poids de choc** : elle n'entre ni dans `recompense_interne`, ni dans
`poids_evenement`, ni dans le gradient. Un jalon n'est daté qu'**une fois par épisode**
(sinon un aller-retour devant la porte réécrirait la mesure), et le déverrouillage se lit
sur la **transition** verrouillée→ouverte, jamais sur l'état courant seul (une porte déjà
ouverte au reset ne doit pas être datée au tick 0).

| Fichier modifié | Changement |
|-----------------|------------|
| `src/naulthene/cerveau/noyau.py` | Nouvelle section **3h** `ChronometreJalonsDoorKey` ; instanciation dans `EtatCognitif` ; 8 compteurs journaliers dans `_reinitialiser_buffers_journee` ; appels dans `traiter_tick` (observation + 2 sites de consommation) ; récolte des deltas avant le `reset()` de fin d'épisode ; réinitialisation dans `demarrer_journee` et en fin d'épisode ; ligne de bilan « Jalons DoorKey » ; **6 clés W&B conditionnelles** |
| `docs/ameliorations/CONCEPTION_v33_memoire_emotionnelle.md` | **Nouveau.** Cadrage complet de la v33 : valence, replay orienté, liage multimodal — avec les options **écartées** et leurs raisons |

**Validation** :
- **Invariance comportementale PROUVÉE par différentiel** : l'empreinte MD5 des 400 actions
  à graine fixée est **identique** (`6573f2fd045d`) avec et sans les appels du chronomètre
  (vérifié en neutralisant les 3 sites d'appel puis en comparant) — la télémétrie ne touche
  ni la décision, ni le gradient, ni la dopamine. Test lui-même vérifié déterministe
  (2 exécutions identiques).
- **Ordre et unicité des jalons** (test unitaire) : épisode vierge → 3 `None` ; clé au
  tick 12 → Δt1=12, Δt2/Δt3 restent `None` ; porte au tick 40 → Δt2=28 ; sortie au tick 55
  → Δt3=15. `None` jamais confondu avec 0.
- **Conflit viscéral** : une consommation avant la prise de clé est **ignorée**, deux
  consommations clé en main sont **comptées**, une consommation après la sortie est
  **ignorée**.
- **Run réel DoorKey-6x6 (600 ticks) + NUIT COMPLÈTE** (leçon v32.0 : une mécanique ne se
  valide jamais sur des ticks seuls) — 74 clés W&B dont 6 de jalons ; bilan console correct,
  affichant `Δt2 porte JAMAIS ATTEINT (n=0)` sur un cerveau neuf.
- **Remise à zéro vérifiée** après `demarrer_journee` (piège `score_vocal_jour` v27.0 : un
  compteur journalier jamais vidé cumule depuis la naissance).

⚠️ **Ce que cette version ne prouve PAS.** Les chiffres du run de validation (Δt1 = 28 ticks
sur n=1, Δt2/Δt3 jamais atteints) proviennent d'un **cerveau neuf de 600 ticks au Palier 1** :
ils démontrent que la métrique **fonctionne**, ils ne disent rien du blocage au Palier 7.
Seul un run de diagnostic sur un cerveau **déjà arrivé au Palier 7** peut trancher entre Δt2
et Δt3 — et c'est cette lecture, et elle seule, qui doit décider du plan de la v33.

⚠️ **Aucune mécanique de la Mémoire Émotionnelle n'est écrite** : ni valence, ni replay
orienté, ni liage multimodal. La v33.0-etape0 ne fait que rendre mesurable ce qui devra
être décidé. `abs(recompense_interne)` reste en place dans le calcul d'`importance`.

---

## [32.0-experimental] - 2026-08-03

### L'Odorat Topologique & la Clinotaxie

| Type | Details |
|------|---------|
| **Commit** | `1291323` |
| **Catégorie** | feat (nouvelle mécanique cognitive, expérimentale) + fix (persistance) |
| **Impact** | Critique (architecture du réseau, persistance, signal olfactif) |

**Arbitrages utilisateur, tranchés avant implémentation : (1) le BFS plutôt que la pénalité `d_géo + p × N_obstacles`, dont le `N_obstacles` est mal défini dans un labyrinthe ; (2) porte fermée « qui fuit » (surcoût de +4 cases) plutôt que bloquante, pour que l'odorat garde son rôle de guidage AVANT que la porte ne soit ouverte ; (3) λ adaptatif DIFFÉRÉ et habituation au capteur ÉCARTÉE.**

**1. L'odorat cesse de traverser les murs**

`lire_chimie` calculait une distance de Manhattan pure, sans jamais consulter la grille entre l'agent et la source. Le problème n'était pas une imprécision mais un **gradient TROMPEUR** : l'agent qui suit une odeur à travers une cloison s'englue contre la paroi. Un gradient faux est pire que pas de gradient, puisque `integrateur_bio` ne peut pas apprendre à ignorer un signal qui n'est faux qu'une partie du temps.

La distance devient celle d'un parcours en largeur **multi-sources** (`_distances_topologiques` + `_bfs_vers_agent`), propagé depuis toutes les sources d'un type à la fois. Coût en O(V+E) sur 36 à 169 cases — **moins** que la double boucle de scan qu'il remplace. Murs et lave infranchissables ; porte fermée franchissable avec `SURCOUT_PORTE_FERMEE = 4`.

| Cas testé | Distance obtenue | Attendu |
|---|---|---|
| Mur plein entre agent et source | `None` (inodore) | `None` |
| Porte **fermée** sur le chemin | 10 | 6 + 4 |
| Porte **ouverte** | 6 | 6 |
| Aucun obstacle | 6 | 6 = Manhattan |

Le dernier cas garantit l'absence de régression sur carte ouverte : sans obstacle, le BFS retombe exactement sur l'ancien calcul.

**2. La clinotaxie — `DIM_VECTEUR_BIO` 32 → 34**

`integrateur_bio` ne recevait que l'intensité instantanée `S_t`, **sans aucun état interne** lui permettant d'en dériver quoi que ce soit : le réseau était structurellement **aveugle au mouvement**, incapable de savoir si son dernier pas l'avait rapproché d'une ressource. Deux dims de variation `ΔS = S_t − S_{t−1}` sont ajoutées **en queue** (contrat append-only), normalisées par `(ΔS+1)/2` — **neutre = 0.5**, au-dessus « je me rapproche », en dessous « je m'éloigne ».

C'est décisif là où le diagnostic v29.1 avait montré que l'odorat ne servait à rien : sur `DoorKey-6x6`, `S_t` varie peu d'une case à l'autre, mais le **signe** de ΔS bascule proprement à chaque pas. Le gradient existe dans le monde depuis la v30.0 ; ces 2 dims le rendent enfin **lisible**.

⚠️ **Le piège du respawn**, traité : au `reset()`, l'agent est téléporté et les sources régénérées ailleurs. Comparer la première odeur du nouvel épisode à la dernière de l'ancien produirait un ΔS énorme et **fictif**, lu par C1 comme un violent rapprochement. `reinitialiser_episode` efface donc la mémoire olfactive — le premier tick d'un épisode n'a rien à quoi se comparer (vérifié : 0.5 exact après un reset près d'une source).

**3. 🐛 Bug de persistance découvert et corrigé — la première nuit d'un cerveau greffé plantait**

Découvert en validant la greffe sur un `.brain` réel de 280 000 ticks. `greffe_detectee` ne se basait que sur `missing_keys`, qui ne signale que les couches **entièrement absentes**. Or une greffe **par recopie** — la règle même du projet — n'en produit aucune : la couche existe, seule sa forme change. Les moments Adam restaient donc chargés à l'ancienne largeur :

```
RuntimeError: The size of tensor a (80) must match the size of tensor b (82)
```

Ce crash ne survenait **ni au chargement, ni pendant la journée, mais à la première `executer_nuit`** — invisible à toute vérification courte de type « 30 ticks post-résurrection », qui était le protocole des v29/v30. Le bug était **latent depuis la v29.0** ; il ne s'était jamais manifesté parce que ces versions changeaient `dim_bus` en parallèle, ce qui déclenchait `missing_keys` par un autre chemin. Correctif : se fier au drapeau `bio_greffe` retourné par la greffe elle-même.

Le libellé de greffe est par ailleurs rendu **cumulatif** (`_greffer_vecteur_bio_etendu` annonçait « Exo-Sens (v30.0) » pour une greffe de clinotaxie) : un `.brain` pré-v29 chargé par un binaire v32 annonce désormais les trois blocs acquis.

| Fichier modifié | Changement |
|-----------------|------------|
| `src/naulthene/cerveau/bus_sensoriel.py` | `SURCOUT_PORTE_FERMEE`, `TYPES_BLOQUANTS_ODORAT`, `DIM_ODORAT_DELTA=2` ; `_distances_topologiques()` + `_bfs_vers_agent()` (BFS à seaux) ; `_calculer_deltas_odorat()` ; `_odeurs_precedentes` remis à zéro dans `reinitialiser_episode` ; `interpreter()` → 18 dims (deltas en queue, après l'Exo-Sens) ; `hierarchie_sensorielle` enrichie |
| `src/naulthene/cerveau/noyau.py` | `DIM_VECTEUR_BIO` 32 → 34 ; neutre **0.5** (et non 0.0) pour la clinotaxie hors MiniGrid dans `obtenir_vecteur_bio` ; **borne haute** sur `vecteur_exo` (sans elle les 2 deltas auraient faussé `Sens_Exo_*`) ; 4 compteurs journaliers ; ligne « Clinotaxie » au bilan ; 5 clés W&B |
| `src/naulthene/cerveau/persistance.py` | **Fix** : `greffe_detectee` s'appuie sur `bio_greffe` et non sur `missing_keys` seul ; libellé de greffe cumulatif |

**Validation** :
- **BFS** : 4 cas ci-dessus, dont le repli exact sur Manhattan sans obstacle.
- **Clinotaxie** : approche progressive vers une source → ΔS > 0.5 sur 4 ticks consécutifs (0.5204 → 0.6237) ; demi-tour → ΔS < 0.5 sur 3 ticks (0.3763 → 0.4750). Signe correct dans les deux sens.
- **Respawn** : 0.5 exact au premier tick après `reinitialiser_episode`, malgré une téléportation à 1 case de la source.
- **`.brain` RÉEL** (`020820262137_V31_700_RMD`, 280 000 ticks) : greffé 80 → 82, **80 colonnes historiques recopiées au bit près** (`torch.allclose`), palier vocal 19 et 280 000 ticks préservés. Cycle complet vérifié : greffe → journée → **nuit** → sauvegarde → rechargement (sans greffe) → **2ᵉ nuit**.
- **Neurogenèse** : `integrateur_bio` (16,50) → (32,66), segment bio **fixe à 34** pendant que `dim_bus` double.
- **Vocal isolé** : vecteur bio à 34 dims, 2 dernières à `[0.5, 0.5]` (neutre, pas une fuite olfactive fictive).
- Run 400 ticks + nuit (56 clés) ; 12/12 modules importent.

⚠️ **Ce que cette version ne prouve PAS.** `Sens_Odorat_Taux_Approche` vaut 70,4 % sur le run de validation, mais sur **27 ticks de variation seulement** — un nouveau-né ne change de case que 23 fois en 400 ticks (`Contact 53 %` : il tourne sur lui-même et se cogne). Ce chiffre n'est **pas** un résultat : il dit seulement que la métrique fonctionne. La clinotaxie est un apprentissage de `integrateur_bio`, pas un câblage — seul un run long, sur un cerveau qui se déplace vraiment, dira si l'agent **suit** le gradient (≫ 50 %) ou le monte et le descend au hasard (≈ 50 %, auquel cas ces 2 dims seraient à remettre en cause comme l'ont été les 182 doublons de la v31.1).

⚠️ **`λ` reste à 0.8 et aucune formule adaptative n'est écrite** — conformément à la méthode posée en v30.1. Le BFS augmentant mécaniquement les distances dans les labyrinthes, l'hypothèse est qu'il corrige à lui seul l'extinction trop rapide au Doctorat ; à vérifier sur `Sens_Odorat_Moyen` lors d'un run `MultiRoom` **avant** de toucher à λ.

---

## [31.1-docs] - 2026-08-02

### Archivage d'EXPLICATIONS_v29_sens.md & §15 d'explications_readme.md rendu autoportant

| Type | Details |
|------|---------|
| **Commit** | `e4e6c8d` |
| **Catégorie** | docs |
| **Impact** | Documentation |

**Demande utilisateur : archiver `EXPLICATIONS_v29_sens.md` et mettre à jour `explications_readme.md`.**

Ce document était la référence détaillée des 5 sens, mais ses chiffres avaient été **dépassés par
les v30/v31** : vecteur bio à 24 dims (il est à 32 depuis l'Exo-Sens), odorat linéaire à portée
fixe (exponentiel depuis la v30.0), aucune mention de la mémoire proportionnelle. Le laisser dans
`docs/` en faisait une source de confusion — un lecteur pouvait y prendre des valeurs fausses.

⚠️ **Le risque de l'archivage : perdre ce qu'il documentait seul.** Ce fichier portait des
explications **toujours en vigueur** (pourquoi les sens faibles restent hors de la cible JEPA, les
deux options écartées et leurs raisons). `explications_readme.md` §15 a donc été **enrichi pour
devenir autoportant** avant le déplacement :

- Tableau des sens complété par l'**Exo-Sens** (il s'arrêtait au goût) ;
- Odorat corrigé : **exponentiel** `exp(-0.8·d)` et non plus « linéaire sur 4 cases » ;
- `DIM_VECTEUR_BIO` **24 → 32**, avec la composition complète du vecteur bloc par bloc et le
  rappel que toute insertion **au milieu** décalerait silencieusement les acquis d'un `.brain` ;
- Nouvelle **§15.6bis « Deux options volontairement ÉCARTÉES »** — le court-circuit conditionnel
  de C2 et la porte tactile dans `bus_latent`, avec leurs raisons. Ce contenu n'existait que dans
  le document archivé ; il fait jurisprudence (la v30.0 a écarté un **troisième** seuil sur le
  même argument).

Le document archivé reçoit un bandeau explicite listant ce qui y est dépassé et renvoyant vers
`explications_readme.md` §15 pour l'état courant.

| Fichier modifié | Changement |
|-----------------|------------|
| `docs/ameliorations_appliquees/EXPLICATIONS_v29_sens.md` | Déplacé (`git mv`), bandeau « ARCHIVÉ », liens sortants recalculés d'un cran |
| `docs/fonctionnement/explications_readme.md` | §15 rendu autoportant (voir ci-dessus) + §15.6bis |
| `readme_fr.md`, `CLAUDE.md`, `docs/fonctionnement/LANCEMENT.md`, `docs/fonctionnement/Parcourt_readme.md`, `docs/fonctionnement/CHANGELOG.md`, `docs/Old_Archive_rmd/{README,CONCEPTION_v30_exo_sens}.md` | 7 références entrantes corrigées ; `docs/` ne compte plus que **4 documents vivants** |

**Validation** : 100 % des liens markdown du dépôt résolvent (4 vivants + 7 archivés) ; sanity run
120 ticks + nuit OK (52 clés) ; aucun code touché.

---

## [31.1-experimental] - 2026-08-02

### La Déduplication Mnésique & le Cap de Densité Spatiale

| Type | Details |
|------|---------|
| **Commit** | `11cc1a6` |
| **Catégorie** | fix (correctif d'un effet de bord de la v31.0) |
| **Impact** | Fonctionnel (contenu réel de la mémoire spatiale) |

**Analyse utilisateur d'un run de 700 jours sous v31.0. Quatre observations, dont une confirmée par la mesure et une infirmée par la lecture du code.**

**✅ Confirmé — la dilution spatiale (observation n°4).** La capacité proportionnelle de la v31.0 supprimait la saturation, mais ignorait une contrainte évidente : la taille du **monde**. À `dim_bus=48` (capacité 576) :

| Carte | cases | souvenirs/case |
|---|---|---|
| `DoorKey-6x6` | 16 intérieures | **36** |
| `Empty-8x8` | 36 | 16 |
| `MultiRoom-N4-S5` | 169 | 3,4 |

Retenir 36 repères pour une seule case n'a aucun sens. Pire, un effet de bord non anticipé : `recuperer_contexte` sélectionne par `min(distance)` et ne lit la fraîcheur **qu'après** — avec des doublons, un souvenir périmé pouvait être retenu à la place d'un souvenir récent situé à la même distance. **Le rappel devenait moins fiable à mesure que la mémoire grossissait.**

**❌ Infirmé — « le rêve cristallise des réflexes d'échec ».** Vérification faite dans `rever()` : il ne calcule **que `perte_jepa`**. Aucune perte acteur, aucune perte critique — c'est le comportement documenté depuis la v8.0 (`explications_readme.md` §10.2 : *« le rêve consolide le modèle du monde, la politique motrice en bénéficie seulement indirectement via le tronc partagé »*). Rejouer une trajectoire non gagnante apprend « voilà comment le monde évolue si je vais à gauche », **jamais** « aller à gauche était bien ». Il n'y a donc pas d'ancrage de choix moteurs d'échec à corriger, et le Prioritized Experience Replay envisagé supposerait une `Erreur_TD_RL` qui n'existe pas dans le rêve (le critique n'y est jamais évalué). ⚠️ Le « 0 % de victoires » du Sursaut est par ailleurs une métrique **introduite en v30.1** : sans point de comparaison antérieur, rien ne permet de l'attribuer à la v31.0.

**LA DÉCOUVERTE — 91 % de la mémoire était de la redondance**

En instrumentant, un fait bien plus déterminant est apparu sur un `.brain` réel :

```
naulthene_parole (480 000 ticks) : 200 souvenirs pour 18 repères DISTINCTS
                                   → 182 doublons (91 %)
```

La « saturation à 200/200 » n'était donc **pas un manque de place** : c'était le même lieu enregistré des dizaines de fois. Un souvenir n'est pas un journal d'événements, c'est un **repère** — « il y a de la nourriture ici ». Deux repères identiques n'apportent rien.

**Les trois correctifs**

1. **Déduplication à l'écriture** — `enregistrer_evenement` rafraîchit le tick d'un repère existant `(pos, type)` au lieu d'empiler, et le remet en fin de liste (la FIFO évince donc les lieux les plus anciennement **confirmés**, jamais un lieu encore visité). Corrige au passage le biais de sélection ci-dessus : un lieu connu reste toujours à sa fraîcheur la plus récente.
2. **Compactage au chargement** — `dedupliquer()`, appelée par `charger_ou_naitre`, fusionne les doublons **historiques** d'un `.brain` antérieur (la déduplication ne vaut que pour les nouveaux souvenirs). Conserve le tick le plus récent de chaque repère : **aucune information perdue**, seules les répétitions disparaissent.
3. **Cap de densité spatiale** — `capacite = min(dim_bus × 12 × (1+déficit), cases_grille × DENSITE_MAX)` avec `DENSITE_MAX = 3`. La mémoire cesse d'être absurdement plus grande que son monde. Le plancher (200) reste prioritaire ; `cases_grille=None` (mode vocal isolé, API absente) désactive le cap — comportement v31.0 inchangé.

| Fichier modifié | Changement |
|-----------------|------------|
| `src/naulthene/cerveau/noyau.py` | Déduplication dans `enregistrer_evenement` ; nouvelle `dedupliquer()` ; `DENSITE_MAX_PAR_CASE` + paramètre `cases_grille` dans `ajuster_capacite` ; lecture défensive de la grille dans `executer_nuit` ; 3 clés W&B (`Memoire_Doublons_Evites`, `Memoire_Cap_Densite_Actif`, `Memoire_Densite_Par_Case`) ; ligne de bilan enrichie |
| `src/naulthene/cerveau/persistance.py` | Appel de `dedupliquer()` au chargement + message `🧹 Mémoire spatiale compactée` |

**Validation** :
- **Effet sur les `.brain` RÉELS** : `naulthene_parole` passe de **200/200 saturé (rappel 100 %)** à **18/200 (9 %, rappel toujours 100 %)** — 182 doublons fusionnés sans aucune perte de qualité de rappel, ce qui **prouve** que ces doublons ne servaient à rien. `naulthene_cursus` : 73 doublons fusionnés → 16 repères.
- **Déduplication unitaire** : 100 événements au même endroit → **1 souvenir**, tick conservé = le plus récent (99). 50 événements sur 15 positions → 15 souvenirs.
- **Cap de densité** : `DoorKey-6x6` 576 → 200 (plancher), `MultiRoom` inchangé à 576 (le cap ne bride que là où c'est absurde).
- **Non-régression diurne prouvée** : empreinte MD5 des 400 actions à graine fixée **identique** (`e5ce5f49e406`) depuis la v30.1.
- Nuit + neurogenèse + `vocal_isole` ; tous les modules importent.

---

## [31.0-experimental] - 2026-08-02

### La Mémoire Proportionnelle & le Rêve Invariant d'Échelle

| Type | Details |
|------|---------|
| **Commit** | `6c9121e` |
| **Catégorie** | feat (nouvelle mécanique cognitive, expérimentale) |
| **Impact** | Fonctionnel (capacité mnésique et volume de consolidation nocturne) |

**Constat utilisateur : « la mémoire spatiale est saturée à 200/200, le rêve rejoue moins de 2 % de la journée et ne libère pas d'espace ». Les DEUX symptômes sont réels — mais l'enquête montre qu'ils sont INDÉPENDANTS, et que le lien de cause à effet supposé n'existe pas.**

**Diagnostic — deux mémoires distinctes, souvent confondues**

| Mémoire | Rôle | Saturation ? |
|---|---|---|
| `memoire_moyen_terme` | Ce que le rêve rejoue — **vidée chaque nuit** (`clear()`) | ❌ jamais |
| `memoire_episodique_spatiale` | Le « où/quand/quoi » des ressources — FIFO à 200 | ✅ oui |

Le rêve n'a donc **jamais** géré la mémoire spatiale : il ne peut pas « libérer » un espace qu'il ne touche pas. Corriger le rêve n'aurait rien changé à la saturation, et augmenter la capacité n'aurait rien changé au volume de rêve. Deux correctifs distincts étaient nécessaires.

**1. La cause réelle des 2 % de rêve — un biais d'échelle**

`importance` est multipliée par `empreinte_enfance = BUS_REFERENCE_INITIAL / dim_bus` : à `dim_bus=96`, tout souvenir vaut **6× moins** qu'à la naissance. Or `facteur_richesse` comparait cette importance à une référence **constante** (`IMPORTANCE_REFERENCE_REVE = 0.5`). Le pourcentage de rêve s'effondrait donc mécaniquement à mesure que le cerveau grandissait :

| `dim_bus` | % de rêve AVANT | % de rêve APRÈS |
|---|---|---|
| 16 | 60,0 % | 60,0 % |
| 32 | 46,2 % | **60,0 %** |
| 48 | 30,8 % | **60,0 %** |
| 96 | 15,4 % | **60,0 %** |

*(à erreur JEPA constante, pour isoler l'effet du correctif)*

**Un cerveau plus grand rêvait de moins en moins** — exactement l'inverse de ce que la consolidation nocturne devrait faire. Correctif : la référence suit la même échelle que ce qu'elle mesure (`IMPORTANCE_REFERENCE_REVE × empreinte_enfance`). Le rapport redevient invariant à la taille du cerveau ; `%_reve` continue d'émerger de la plasticité × richesse **réelle**, on retire seulement un biais parasite.

> ⚠️ **Nuance importante, mesurée et assumée** : une part du « peu de rêve » sur un cerveau mature est **saine** et n'est PAS corrigée. L'erreur JEPA moyenne chute de 0,227 (dim_bus=16) à 0,019 (dim_bus=96) — le cerveau **comprend mieux son monde**, donc a objectivement moins à consolider. `importance = (|r| + 2·JEPA + ε) × boost × empreinte` : la composante JEPA baisse pour une bonne raison. Ce correctif ne retire que le biais d'échelle, jamais le signal réel.

**2. La capacité mnésique devient proportionnelle**

`capacite_max = 200` était une constante arbitraire, jamais calibrée. Elle émerge désormais de deux facteurs biologiquement défendables :

$$\text{capacité} = \underbrace{\text{dim\_bus}}_{\text{substrat neural}} \times \underbrace{12}_{\text{densité}} \times \underbrace{(1 + \text{déficit\_bio})}_{\text{le BESOIN}}$$

| `dim_bus` | repu | déficit moyen | épuisé |
|---|---|---|---|
| 16 (naissance) | **200** | 288 | 384 |
| 48 | 576 | 864 | 1152 |
| 96 | 1152 | 1728 | 2304 |

`SOUVENIRS_PAR_DIM = 12` est calibré pour que la naissance donne 192 → ramené à **200 par le plancher**, soit exactement la valeur historique : aucune rupture au démarrage, la capacité cesse seulement d'être un plafond dur quand le cerveau grandit. Le `deficit_bio` (déjà calculé par `BiologicalHomeostasisEngine`) est le facteur « besoins » : un agent affamé a un usage réel du souvenir des ressources, un agent repu non. Il est **borné à 1.0** — un agent épuisé double sa capacité, jamais plus.

Recalculée **une fois par nuit** (jamais par tick : une capacité fluctuante rendrait la FIFO illisible), au moment où le cerveau grandit déjà. Ne descend jamais sous le plancher de 200 ; si elle rétrécit, la troncature se fait **par l'avant** (les plus anciens partent), jamais par la fin qui jetterait les souvenirs les plus frais.

| Fichier modifié | Changement |
|-----------------|------------|
| `src/naulthene/cerveau/noyau.py` | `MemoireEpisodiqueSpatiale.SOUVENIRS_PAR_DIM` + `ajuster_capacite(dim_bus, deficit_bio)` + `capacite_plancher` ; appel dans `executer_nuit` ; `reference_richesse` normalisée par `empreinte_enfance` ; 3 clés W&B (`Memoire_Capacite_Courante`, `Reve_Facteur_Richesse`, `Reve_Empreinte_Enfance`) ; ligne de bilan enrichie de l'origine de la capacité |

**Validation** :
- **Effet sur un `.brain` RÉEL** : `naulthene_parole` (480 000 ticks, `dim_bus=48`) passe de **200/200 saturé** à **200/1152 (17 %)** — la FIFO cesse de jeter. Acquis intégralement préservés (greffes v28/v29/v30 appliquées au chargement).
- **Correctif du rêve** vérifié à erreur JEPA constante : 15,4 % → 60,0 % à `dim_bus=96` (tableau ci-dessus).
- **Non-régression diurne prouvée** : empreinte MD5 de la séquence des 400 actions à graine fixée **identique** à la v30.1 (`e5ce5f49e406`) — les deux mécaniques n'agissent que la nuit.
- Plancher (200 mini), croissance avec `dim_bus`, modulation par le déficit, et **troncature FIFO par l'avant** vérifiés unitairement (500 souvenirs → 200, le plus ancien conservé est bien le n°300).
- Nuit + neurogenèse + `vocal_isole` ; les deux `.brain` réels du dépôt ; tous les modules importent.

---

## [30.1-docs] - 2026-08-02

### Archivage documentaire (`docs/Old_Archive_rmd/`) & harmonisation de toute la doc sur la v30

| Type | Details |
|------|---------|
| **Commit** | `cc73be4` |
| **Catégorie** | docs |
| **Impact** | Documentation |

**Demande utilisateur : ranger les documents « plus à jour » dans un dossier d'archive
`docs/Old_Archive_rmd/`, et mettre à jour toute la documentation restante.**

`docs/` ne contient désormais que **5 documents vivants** : `CHANGELOG.md` (la référence
factuelle), `LANCEMENT.md` (commandes et dépannage), `Parcourt_readme.md` (guide vulgarisé),
`explications_readme.md` (détail algorithmique) et `EXPLICATIONS_v29_sens.md` (toujours la
référence des 5 sens).

**Critère d'archivage retenu** : un document rejoint l'archive quand sa mécanique est **livrée et
documentée ailleurs**, jamais parce qu'il est simplement « vieux ». Ces documents restent
précieux — ils gardent la trace des options **écartées** et de leurs raisons, ce qu'aucun document
à jour ne raconte, et c'est ce qui évite qu'une idée déjà évaluée soit réintroduite plus tard sans
connaître l'argument qui l'avait rejetée.

| Archivé | Statut de la mécanique |
|---|---|
| `CONCEPTION_v22_audio.md` | ✅ Livrée (v22.0/v22.1, étendue jusqu'en v27.6) |
| `CONCEPTION_v30_exo_sens.md` | ✅ Livrée (v30.0) |
| `Maj_V29_readme.md` | ✅ Livrée (v29.0/v29.1) |
| `AMELIORATION_V1.md` | 🟡 Partiellement réalisée (§A.5 Cristallisation Souple seule) |
| `1440_JOURS_NAULTHENE_V1.md` | 📊 Analyse de run |

⚠️ **Piège traité** : ces documents étaient référencés depuis `readme_fr.md`, `CLAUDE.md`, les autres
docs **et sept modules du code source** (docstrings de `bus_sensoriel.py`, `hemisphere_audio.py`,
`professeur_gemma.py`, `lecons_vocales.py`, `client_professeur.py`, `daemon_cerveau.py`,
`irm_cerveau.py`). Déplacement par `git mv` (historique préservé, visible en `R` dans le statut),
puis correction des liens **entrants** (11 fichiers) **et sortants** (les documents archivés
pointaient vers `docs/`, désormais un cran au-dessus). Vérification finale : **100 % des liens
markdown internes du dépôt résolvent**.

**Mises à jour de fond** (au-delà de l'archivage) :

| Fichier | Changement |
|-----------------|------------|
| `docs/Old_Archive_rmd/README.md` | **Nouveau.** Explique le critère d'archivage, liste le contenu avec le statut de chaque mécanique, rappelle où trouver l'état courant, et documente la procédure (`git mv` + correction des liens, y compris dans le code) |
| `docs/fonctionnement/LANCEMENT.md` | En-tête V21-V29 → **V21-V30** (l'Exo-Sens §10 et les métriques de calibrage §11 manquaient) ; §9a : la légende de l'odorat décrivait encore la rampe linéaire à 4 cases, remplacée par l'atténuation exponentielle ; **2 lignes de dépannage** citaient `PORTEE_ODORAT=4` comme comportement actuel — corrigées |
| `readme_fr.md` | Nouvelle section **v30.1** (elle manquait alors que la version est livrée) + entrée de table des matières ; encadré « État du dépôt » étendu à la v30.1 |
| `docs/fonctionnement/explications_readme.md` | §12 « v7 → v29 » → **« v7 → v30 »** (le titre était déjà en retard sur sa propre table) + 2 lignes d'évolutions (v30.0, v30.1) ; **§15.7** (Odorat Dynamique & Exo-Sens) et **§15.8** (instrumentation) ; glossaire : `PORTEE_ODORAT` marquée « plus utilisée », ajout de `LAMBDA_ODORAT`, `SEUIL_COUPURE_ODORAT`, `DIM_EXO`, `PERIODE_PERCEPTION_EXO` |
| `CLAUDE.md` | Arborescence `docs/` refaite (vivants vs archive) ; nouvelle section **« Archivage documentaire »** dans *Maintenance du Changelog*, avec l'avertissement que le code source référence ces documents |

**Validation** : 100 % des liens markdown résolvent (vérifié sur les 4 fichiers racine/docs **et**
les 6 documents archivés) ; aucune référence obsolète `docs/<archive>.md` restante ; régression
150 ticks + nuit OK (46 clés, `DIM_VECTEUR_BIO=32`) ; tous les modules importent.

---

## [30.1-experimental] - 2026-08-02

### Instrumentation avant calibrage — mémoire épisodique & Sursaut de Volonté

| Type | Details |
|------|---------|
| **Commit** | `7ec4475` |
| **Catégorie** | feat (télémétrie, expérimentale) |
| **Impact** | Fonctionnel (observabilité — **aucun** impact sur la décision ni le gradient) |

**Contexte utilisateur : deux constantes arbitraires subsistent dans le projet — `capacite_max = 200` (mémoire épisodique spatiale) et `EXTENSION_PATIENCE_SURSAUT = 50` (Sursaut de Volonté). L'utilisateur souhaite les rendre ADAPTATIVES, indexées sur la capacité réelle du cerveau (`dim_bus`, neurogenèse) et sur les besoins, dans l'esprit du rêve adaptatif (`pourcentage_reve` émerge de la plasticité × richesse, jamais d'un batch fixe). Décision commune : **instrumenter d'abord, calibrer ensuite** — passer directement à une formule adaptative reviendrait à remplacer un chiffre arbitraire par une formule arbitraire, tout aussi peu validée. C'est la leçon explicite de la v29.1 (5 sens livrés sans télémétrie, écart corrigé après coup).**

**Les deux questions auxquelles ces mesures doivent répondre :**

1. **La saturation mémoire coûte-t-elle quelque chose ?** `naulthene_parole` affichait exactement 200 souvenirs après 480 000 ticks — le plafond, donc une FIFO qui jette en continu. Mais un rappel qui reste proche et frais à saturation prouverait que la capacité **n'est pas** le facteur limitant, et qu'une capacité adaptative serait une fausse bonne idée.
2. **Dans quel sens doit varier une extension de sursaut adaptative ?** Deux lectures opposées, toutes deux défendables : « muscle » (un sursaut qui gagne souvent se renforce — cohérent avec `augmenter_patience_de_base_definitivement`, déjà présent) ou « habituation » (un stimulant répété perd son effet). Le projet comptait déjà **combien** de sursauts (`sursauts_jour`) mais jamais s'ils **servaient** à quelque chose.

**Métriques ajoutées** (toutes conditionnelles, absentes du log quand la mécanique est inactive) :

| Clé W&B | Mesure |
|---------|--------|
| `Memoire_Taux_Saturation` | Remplissage rapporté à `capacite_max` — 1.0 = FIFO en train de jeter |
| `Memoire_Age_Plus_Vieux_Souvenir` | Profondeur temporelle réellement accessible (en ticks) |
| `Memoire_Taux_Rappel_Reussi` | Part des quêtes de survie trouvant un souvenir du bon type |
| `Memoire_Proximite_Moyenne` | Qualité spatiale du rappel (1.0 = souvenir sur place) |
| `Memoire_Fraicheur_Moyenne` | Qualité temporelle du rappel |
| `Sursaut_Taux_Victoire` | **La métrique décisive** — part des sursauts suivis d'une victoire |
| `Sursaut_Victoires_Jour` / `Sursaut_Echecs_Jour` | Numérateur et dénominateur bruts |

Plus deux lignes de bilan de nuit enrichies : `Mémoire Épiso.` affiche désormais `N/200` avec un
suffixe `⚠️ SATURÉE` au plafond et la qualité du rappel ; `Potentiomètre` affiche
`N Sursaut(s) → X% de victoires` dès qu'un sursaut a été jugé.

| Fichier modifié | Changement |
|-----------------|------------|
| `src/naulthene/cerveau/noyau.py` | 6 compteurs journaliers dans `_reinitialiser_buffers_journee` ; accumulation du rappel dans `traiter_tick` (au site d'appel de `recuperer_contexte`) et de l'issue du sursaut en fin d'épisode ; 2 lignes de bilan enrichies ; 8 clés W&B |

**Validation** :
- **Invariance comportementale prouvée** : à graine fixée (42), l'empreinte MD5 de la séquence des 400 actions d'une journée est **identique** avant et après (`e5ce5f49e406`) — la télémétrie ne touche ni la décision, ni le gradient, ni la dopamine.
- Métriques mémoire vérifiées sur run réel (taux de rappel 65 %, proximité 0.27, fraîcheur 0.96, âge du plus vieux souvenir 229 ticks).
- Métriques sursaut vérifiées en Mode Libre forcé (3 victoires / 7 échecs → `Sursaut_Taux_Victoire = 0.3`, ligne console `10 Sursaut(s) → 30% de victoires`).
- Absence correcte des clés quand la mécanique est inactive (aucun sursaut, aucune quête de survie).
- Non-régression : 200 ticks + nuit + neurogenèse + `vocal_isole` ; tous les modules importent.

⚠️ **Aucune formule adaptative n'est encore écrite.** `capacite_max` reste à 200 et
`EXTENSION_PATIENCE_SURSAUT` à 50 — la v30.1 ne fait que rendre mesurable ce qui devra être
calibré. Le passage à l'adaptatif attend les courbes du run de 700 jours en cours.

---

## [30.0-experimental] - 2026-08-02

### L'Unification & l'Extensibilité — l'Odorat Dynamique & l'Exo-Sens (C3 devient le 6ᵉ sens)

| Type | Details |
|------|---------|
| **Commit** | `c5d23dc` |
| **Catégorie** | feat (nouvelle mécanique cognitive majeure, expérimentale) |
| **Impact** | Critique (architecture du réseau, persistance, contrat des plugs) |

**Arbitrages utilisateur, tranchés avant implémentation (voir `docs/ameliorations_appliquees/CONCEPTION_v30_exo_sens.md`) : (1) l'odorat passe d'une rampe linéaire à une atténuation exponentielle `exp(-0.8·d)`, un gradient de diffusion chimique plutôt qu'un cercle à bord net ; (2) C3 cesse d'être un « 3ᵉ cerveau » interrogé par une action apprise pour devenir un 6ᵉ sens perçu en continu, SANS aucun seuil de déclenchement — l'attention à ce canal doit émerger de la myélinisation de `integrateur_bio`, pas d'un `if` ; (3) `num_actions` reste à 8 avec `ACTION_DEMANDER` masquée en permanence, pour ne jamais amputer les `.brain` existants.**

**1. Chantier 1 — l'Odorat Dynamique (atténuation exponentielle)**

La v29.1 avait diagnostiqué la saturation de l'odorat (97,6 % de couverture sur `Empty-8x8`, 100 % sur `DoorKey-6x6`). Une portée relative à la géométrie (`min(W,H)/3`) avait été envisagée puis **écartée** : elle ne corrigeait pas les cartes 4×4 et *aggravait* le Doctorat (portée 4→5). Le problème n'était pas la portée mais la **forme** de la décroissance.

$$S(d) = \exp(-\lambda \cdot d), \qquad \lambda = \text{LAMBDA\_ODORAT} = 0.8$$

| d | 0 | 1 | 2 | 3 | 4 |
|---|---|---|---|---|---|
| S(d) | 1.000 | 0.449 | 0.202 | 0.091 | 0.041 |

Le critère retenu pour juger n'est **pas la couverture mais le GRADIENT** (écart de signal entre cases voisines) — c'est lui qui permet à l'agent de savoir vers où aller. Mesuré sur 600 placements aléatoires de 4 sources :

| Carte | linéaire portée 4 | exponentiel λ=0.8 |
|---|---|---|
| `Empty-8x8` | 0.208 | **0.221** |
| `DoorKey-6x6` | 0.196 | **0.305** (+56 %) |
| `MemoryS7` | 0.207 | **0.259** |
| `MultiRoom` | 0.118 | 0.084 |

Sur un run réel de 400 ticks (`Empty-8x8`), l'intensité moyenne passe de ~0.54 à **0.316**, et l'odeur forte (> 0.45) ne survient plus que **29,8 %** du temps au lieu d'être quasi permanente : le sens redevient une boussole de proximité. **Contrepartie assumée et documentée** : `MultiRoom` (Doctorat) perd du gradient, l'exponentielle portant moins loin qu'une rampe à 4 cases — cohérent avec le rôle voulu (proximité, pas cartographie longue distance), mais à surveiller via `Sens_Odorat_*` sur un run au Doctorat.

**2. Chantier 2 — l'Exo-Sens : C3 devient le 6ᵉ sens**

`DIM_VECTEUR_BIO` passe de **24 à 32** dims (8 dims d'Exo-Sens **en queue**, contrat append-only). Le pivot conceptuel complet :

| | v28/v29 (C3 = 3ᵉ cerveau) | v30 (C3 = 6ᵉ sens) |
|---|---|---|
| Nature | Action apprise (`ACTION_DEMANDER`) | Entrée perceptive continue |
| Déclenchement | L'agent **décide** d'interroger | L'agent **perçoit**, sans décider |
| Sortie du plug | `ReponseC3.preferences` (avis sur les actions) | `ReponseC3.perception` (vecteur 8 dims) |
| Chemin | `tete_motrice` → `env.step` | `bus_sensoriel` → `integrateur_bio` |
| Attention | — | Émerge de la myélinisation, **aucun `if`** |

C'est l'option « perception continue » retenue par l'utilisateur contre le déclenchement sur erreur JEPA : un seuil codé en dur dans le chemin de décision aurait violé la règle déjà défendue deux fois (v28 pour l'appel à C3, v29 pour le court-circuit C1→C2). Si le plug envoie du bruit, `integrateur_bio` fera tomber ces poids vers 0 ; s'il envoie de l'information utile, il les renforcera.

**Latence — le garde-fou pratique** : un plug HTTP coûte de 100 ms à 30 s par appel. L'interroger à chaque tick rendrait impraticable un run de 120 000 ticks. La perception est donc **rafraîchie tous les `PERIODE_PERCEPTION_EXO = 20` ticks et mise en cache** (mesuré : 20 rafraîchissements pour 400 ticks). C'est une fréquence d'échantillonnage de capteur, pas une règle de décision — le cerveau perçoit bien quelque chose à chaque tick.

**3. La 8ᵉ action : masquée en permanence, jamais amputée**

`ACTION_DEMANDER` n'a plus de rôle (C3 n'est plus interrogé) mais **reste dans le réseau**, masquée à `-inf` quelle que soit la disponibilité du bus. Motif : 4 des `.brain` du dépôt sont déjà à 8 actions, dont `naulthene_cursus.brain` (cerveau actif, bus 48). Revenir à `num_actions = 7` aurait imposé une greffe **inverse** jetant des poids appris — première violation de la règle « greffe par recopie, jamais par exclusion ». La colonne 8 devient dormante, conservée, réactivable sans nouvelle greffe.

**4. Contrat `PlugC3` — perceptif et décisionnel coexistent**

`ReponseC3` porte désormais deux champs optionnels : `perception` (v30, 8 dims) et `preferences` (v28, conservé). `PortC3.agreger` agrège les deux **indépendamment**, en ignorant les plugs qui ne fournissent pas l'un ou l'autre — un bus mélangeant un plug v28 et un plug v30 fonctionne sans qu'aucun ne plante sur le `None` de l'autre. Les 3 plugs existants sont inchangés et continuent de fonctionner.

Nouveau **`PlugMemoireAugmentee`** : le premier plug perceptif, 100 % local et déterministe (résumé de la mémoire épisodique spatiale de l'agent), pour valider que C1/C2 digèrent un signal exogène avant d'introduire la latence d'un vrai service. Le contrat générique reste inchangé, donc un `PlugRAG`/`PlugOllama` se branche par simple configuration de `PlugHTTP`.

| Fichier modifié | Changement |
|-----------------|------------|
| `src/naulthene/cerveau/bus_sensoriel.py` | `LAMBDA_ODORAT`/`SEUIL_COUPURE_ODORAT` (atténuation exponentielle) ; `DIM_EXO=8` ; `percevoir_exogene()` (transducteur du 6ᵉ sens, clip défensif, avertissement isolé) ; `interpreter(..., reponse_c3=None)` → 16 dims ; `hierarchie_sensorielle()` étendue à `exo_sens` |
| `src/naulthene/cerveau/noyau.py` | `DIM_VECTEUR_BIO` 24 → 32 ; `PERIODE_PERCEPTION_EXO` ; `_rafraichir_perception_exogene()` (cache + diffusion `1_X`) ; masquage **permanent** de `ACTION_DEMANDER` ; 4 compteurs journaliers + ligne « Exo-Sens (C3) » au bilan + 4 clés `Sens_Exo_*` |
| `src/naulthene/exocortex/port_c3.py` | `ReponseC3.perception` (v30) ; `preferences` devient optionnel ; `agreger` réécrite via `_moyenne_ponderee`, tolérante aux champs absents |
| `src/naulthene/exocortex/plugs/plug_memoire_augmentee.py` | **Nouveau.** Premier plug perceptif + `source_depuis_memoire_spatiale()` (closure d'injection, garde `exocortex/` indépendant de `cerveau/`) |
| `src/naulthene/cerveau/persistance.py` | Libellé de greffe déduit de la **largeur bio réelle** du checkpoint (et non du nombre de dims ajoutées, ambigu : `DIM_TOUCHER+DIM_CHIMIE` et `DIM_EXO` valent tous deux 8) |

**Validation** (aucun test automatisé dans ce projet — vérifications manuelles) :
- **Invariance sans plug** : 400 ticks, `ACTION_DEMANDER` jamais jouée, 8 dims d'Exo-Sens nulles, **aucune clé `Sens_Exo_*` loggée**, bilan de nuit identique à la v29.1.
- **Odorat** : sur run réel, moyenne 0.316 (vs ~0.54), écart-type 0.256, odeur forte 29,8 % des ticks — le signal a changé de nature, pas seulement d'échelle.
- **Avec `PlugMemoireAugmentee`** : perception continue sur 95 % des ticks, **20 rafraîchissements pour 400 ticks** (le cache tient), ligne « Exo-Sens (C3) » et 4 clés `Sens_Exo_*` présentes.
- **Robustesse (4 cas)** : plug en panne en vol → aucune exception ; vecteur malformé (2 dims au lieu de 8) → Exo-Sens neutre, **les 5 sens physiques non affectés** ; bus mixte v28+v30 → agrégation correcte des deux canaux ; valeurs à 999 → clippées à 1.0.
- **Nuit + neurogenèse** : `integrateur_bio` (16,48) → (32,64), segment bio fixe à 32 pendant que `dim_bus` double.
- **Round-trip** persistance identique ; 30 ticks après résurrection.
- **`.brain` RÉELS du dépôt** : `naulthene_parole` (pré-v29, 7 actions) greffé 64→80 dims + 7→8 actions, **480 000 ticks et palier vocal 19/19 préservés** ; `naulthene_cursus` (v29, 8 actions) greffé 72→80, 120 000 ticks préservés. 30 ticks OK sur chacun.
- Chemins `vocal_isole` et MiniGrid+audio ; tous les modules importent.

---

## [master] - 2026-08-02 — Intégration des v28.0 et v29.0/v29.1

### Merge de `feat/v28-exocortex-c3` dans `master` + ouverture de la branche v30

| Type | Details |
|------|---------|
| **Commit** | `3582ade` (merge `--no-ff`) |
| **Catégorie** | chore (intégration) |
| **Impact** | Organisation du dépôt — aucun changement de code |

**`master` portait encore la v27.6.** Les trois versions suivantes vivaient sur la branche
`feat/v28-exocortex-c3`. Merge `--no-ff` (et non fast-forward) pour garder une trace lisible de
l'intégration dans l'historique.

`master` contient désormais :

| Version | Apport |
|---------|--------|
| **v28.0** | La Cascade C1→C2→C3 & le Port Exocortex — 8ᵉ action apprise, `PortC3` multiplexeur, plugs interchangeables, greffe 7→8 actions |
| **v29.0** | Le Bus Sensoriel Multimodal & l'identité C1/C2 explicite — les 5 sens, `DIM_VECTEUR_BIO` 16→24, greffe du vecteur bio |
| **v29.1** | Télémétrie des 5 sens — 7 clés W&B `Sens_*`, ligne au bilan de nuit, diagnostic de saturation de l'odorat |

La branche `feat/v30-exo-sens` a été **rebasée sur ce `master`** — elle ne contient pour l'instant
que le document de cadrage `docs/ameliorations_appliquees/CONCEPTION_v30_exo_sens.md` (aucun code livré).

| Fichier modifié | Changement |
|-----------------|------------|
| `readme_fr.md` | Encadré « État du dépôt » ; nouvelle section v29.1 (absente jusqu'ici) ; section v30.0 explicitement marquée **en cours de conception** ; 2 entrées de table des matières |
| `CLAUDE.md` | Nouvelle sous-section « État des branches » dans *Git Workflow* ; `docs/ameliorations_appliquees/CONCEPTION_v30_exo_sens.md` ajouté à l'arborescence |
| `docs/fonctionnement/CHANGELOG.md` | Cette entrée |
| `docs/fonctionnement/LANCEMENT.md`, `docs/fonctionnement/Parcourt_readme.md`, `docs/fonctionnement/explications_readme.md` | Références de version harmonisées (v29.1) et renvoi vers le cadrage v30 |

⚠️ **La v30.0 n'existe pas encore.** Toute la documentation la présente comme une cible, jamais
comme un état livré — deux points de sa spécification restent d'ailleurs ouverts (voir le document
de cadrage) : la formule d'odorat dynamique ne corrige pas les cartes 4×4 et aggrave le Doctorat,
et la boucle d'attention exogène réintroduirait un seuil codé en dur dans le chemin de décision.

---

## [29.1-experimental] - 2026-08-02

### Télémétrie des 5 Sens — les rendre observables, et un diagnostic de saturation de l'odorat

| Type | Details |
|------|---------|
| **Commit** | `6368e02` |
| **Catégorie** | feat (télémétrie, expérimentale) |
| **Impact** | Fonctionnel (observabilité — aucun impact sur la décision ni le gradient) |

**Constat utilisateur : « dans les tests tu as implémenté tous les sens et mis dans chaque jour pour suivre entièrement tous les éléments ? » — non. La v29.0 câblait bien les 5 sens dans la décision (l'agent les utilise réellement), mais AUCUN des 3 sens ajoutés n'était instrumenté : zéro clé W&B, zéro ligne au bilan de nuit, zéro compteur journalier. Les validations v29.0 étaient des tests PONCTUELS (lecture des signaux à un instant T), pas du suivi. Conséquence concrète : sur un run de 300 jours, il aurait été impossible de répondre à « l'odorat a-t-il jamais servi ? », et une désactivation silencieuse du bus (dégradation gracieuse) n'aurait laissé qu'un unique avertissement console, noyé dans les logs.**

**Audit préalable** : comparaison systématique des 21 compteurs `*_jour` de `EtatCognitif` avec ce qui est réellement loggé. Résultat — **tous les compteurs pré-v29 sont correctement instrumentés** (y compris la télémétrie C3 de la v28.0). L'écart était strictement limité à la v29.0.

**Les 7 nouvelles clés W&B** (préfixe `Sens_`, absentes du log si aucun tick sensoriel n'a été vécu — même logique conditionnelle que le bloc C3) :

| Clé | Ce qu'elle mesure |
|-----|-------------------|
| `Sens_Bus_Actif` | **Métrique de santé** : 0 si le bus s'est désactivé en vol (API minigrid incompatible) |
| `Sens_Toucher_Contact_Ratio` | Part des ticks au contact d'un obstacle (proxy de blocage) |
| `Sens_Toucher_Portage_Ratio` | Part des ticks avec un objet en main — très parlant sur DoorKey (la clé) |
| `Sens_Odorat_Moyen` | Intensité moyenne (nourriture + eau) sur la journée |
| `Sens_Odorat_Max` | Pic d'intensité de la journée |
| `Sens_Odorat_Ticks_Actifs_Ratio` | Part des ticks où au moins une odeur est perçue |
| `Sens_Gout_Ticks_Actifs` | Nombre de ticks avec une trace gustative rémanente |

Plus une ligne au bilan de nuit console, dans le style des lignes existantes, affichée uniquement si des ticks sensoriels ont eu lieu :

```
  ├─ Les 5 Sens     : ✋ Contact 28.5% | 🔑 Portage 20.5% | 👃 Odorat 96.0% des ticks (max 1.50) | 👅 Goût 75 tick(s)
```

Le suffixe `⚠️ BUS DÉSACTIVÉ` s'ajoute si le bus est tombé — l'alerte devient visible à chaque nuit au lieu d'un unique message au moment de la panne.

**⚠️ Diagnostic immédiat livré par cette télémétrie : l'odorat sature sur les petites cartes.** Dès le premier jour instrumenté, `Sens_Odorat_Ticks_Actifs_Ratio = 0.96` et `Sens_Odorat_Max = 1.50` (sur un maximum théorique de 2.0). Vérification par calcul de couverture (4 sources, portée de Manhattan) :

| Carte | `PORTEE_ODORAT=4` (actuelle) | portée 2 | portée 1 |
|-------|------------------------------|----------|----------|
| `Empty-8x8` (intérieur 6×6) | **97.6 %** | 73.3 % | 41.6 % |
| `DoorKey-6x6` (intérieur 4×4) | **100.0 %** | 94.9 % | 71.8 % |
| `MultiRoom-N4-S5` (~13×13) | 56.7 % | 24.5 % | 10.7 % |

Sur les 4 premiers niveaux du `PROGRAMME` (les plus petits), l'odorat est donc **quasi constamment saturé** : un signal presque toujours actif porte très peu d'information, et l'agent ne peut pas s'en servir pour s'orienter. Il ne redevient discriminant qu'au Doctorat (`MultiRoom`).

**Aucune valeur n'a été modifiée** — `PORTEE_ODORAT` reste à 4.0. C'est un constat livré à l'utilisateur, pas un correctif appliqué unilatéralement : le bon réglage dépend de l'intention (un odorat « ambiance de proximité » saturé est un choix valide ; un odorat « boussole vers la ressource » demanderait une portée 1-2, ou une normalisation par la taille de la carte). La télémétrie est désormais en place pour trancher sur données réelles.

| Fichier modifié | Changement |
|-----------------|------------|
| `src/naulthene/cerveau/noyau.py` | 7 compteurs journaliers dans `_reinitialiser_buffers_journee` ; accumulation dans `traiter_tick` juste après la lecture du bus (indices figés par le contrat de `BusSensoriel.interpreter`) ; ligne « Les 5 Sens » au bilan de nuit ; bloc de 7 clés `Sens_*` dans `log_wandb`. |

**Validation** :
- **400 ticks + nuit** : compteurs cohérents (400 ticks sensoriels, contact 114, portage 82, goût 75) et 7 clés `Sens_*` présentes dans le dict retourné par `executer_nuit`.
- **Remise à zéro** confirmée au `demarrer_journee` suivant (pas de cumul depuis la naissance — le piège exact du bug `score_vocal_jour` de la v27.0).
- **Mode `vocal_isole` pur** (aucun env MiniGrid) : `ticks_sensoriels_jour = 0` et clés `Sens_*` **absentes** du log — pas de ligne trompeuse ni de division par zéro.
- **Désactivation du bus en vol** : `Sens_Bus_Actif = 0` et `⚠️ BUS DÉSACTIVÉ` affiché au bilan.
- **Non-régression** : 400 ticks + nuit + neurogenèse + plug C3 + 200 ticks + nuit ; 44 puis 47 clés loggées, les 7 `Sens_*` présentes les deux nuits ; tous les modules importent.
- Les 4 points d'entrée (`cursus_developpemental`, `cursus_bebe`, `cursus_parole`, `daemon_cerveau`) loggent le dict retourné par `executer_nuit` — **les nouvelles clés y remontent automatiquement**, sans modification de ces scripts.

---

## [29.0-experimental] - 2026-08-02

### Le Bus Sensoriel Multimodal & l'Identité C1/C2 explicite — les 5 sens, et une frontière nommée entre le réflexe et le néo-cortex

| Type | Details |
|------|---------|
| **Commit** | `6fbe3df` |
| **Catégorie** | feat (nouvelle mécanique cognitive majeure, expérimentale) |
| **Impact** | Critique (architecture du réseau, persistance) |

**Contexte utilisateur (voir `docs/ameliorations_appliquees/Maj_V29_readme.md`) : trois idées à intégrer au dépôt existant sans casser ce qui fonctionne. (1) La hiérarchie des 5 sens — tous les sens ne coûtent pas le même prix en calcul, mais c'est la combinaison de leur diversité qui fait émerger une compréhension du monde ; jusqu'en v28.0 Naulthène n'avait que ses deux sens gourmands (vue, ouïe), les trois sens faibles à moyens n'existaient nulle part. (2) L'identité C1/C2 explicite — la distinction réflexe/néo-cortex existait déjà dans le code (`tete_motrice` d'un côté, `simuler_futur_et_planifier` de l'autre) mais restait implicite, entrelacée dans le corps de `penser()`. (3) La boucle de distillation C2 → C1 — qui, contrairement au reste, n'avait PAS besoin d'être écrite : elle est déjà réalisée par le cycle jour/nuit existant (`annexe_weight` → `base_weight` → Cristallisation Souple v26.0), et l'audit de cette version l'a confirmée plutôt que de la réimplémenter en double.**

**Deux décisions structurantes prises par l'utilisateur à la conception :**
- **Câblage des nouveaux sens** : `DIM_VECTEUR_BIO` passe de 16 à 24 dims — le toucher et la chimie entrent par la **queue du vecteur bio** (donc par `integrateur_bio`, juste avant la décision), **pas** par une nouvelle porte synaptique sommée dans le bus latent. Conséquence voulue : les sens faibles ne polluent jamais la cible JEPA (`perte_jepa` compare toujours le bus prédit au bus réel de la **vision seule**), et un cerveau entraîné sur 300+ jours ne voit pas son modèle du monde perturbé.
- **Portée du refactor C1/C2** : **restructuration pure, zéro changement de comportement**. C2 continue d'être sollicité à chaque tick. L'alternative (C1 court-circuite C2 quand il est confiant) a été explicitement écartée : elle aurait introduit un déclenchement sur seuil codé en dur dans le chemin de décision — exactement de la même nature que ce que `CLAUDE.md` interdit déjà pour l'appel à C3.

**1. Le Bus Sensoriel — l'Interpréteur des 5 Sens (`bus_sensoriel.py`, nouveau)**

Module **pur numpy**, qui n'importe jamais `noyau.py` (même discipline que `exocortex/port_c3.py` : aucun cycle d'import, aucune dépendance au réseau). Il ne fait que traduire l'environnement en signaux normalisés. La hiérarchie de gourmandise énergétique implémentée suit exactement le document de conception :

| Sens | Gourmandise | Dims | Chemin dans le cerveau | Dans la cible JEPA ? |
|------|-------------|------|------------------------|----------------------|
| **Vue** | Extrême | 147 | `porte_visuelle` → `bus_latent` | ✅ oui |
| **Ouïe** | Élevée | 130 | `porte_auditive` → `bus_latent` | ✅ oui (tête séparée) |
| **Toucher** | Moyenne | 4 | `vecteur_bio` → `integrateur_bio` | ❌ non |
| **Odorat** | Faible | 2 | `vecteur_bio` → `integrateur_bio` | ❌ non |
| **Goût** | Faible | 2 | `vecteur_bio` → `integrateur_bio` | ❌ non |

- **Le toucher (`DIM_TOUCHER=4`)** : contact frontal (via l'API native `can_overlap()`, plus fiable qu'une liste de types codée en dur), objet en main (`carrying` — en v28.0 l'agent ne savait qu'il tenait la clé qu'indirectement, par la vue), et orientation encodée **sur le cercle** (cos, sin) plutôt qu'en entier 0-3, pour éviter la discontinuité artificielle entre les directions 3 et 0 qui sont voisines dans le monde réel.
- **L'odorat (2 dims)** : intensité de la source de Nourriture/Eau la plus proche, décroissant linéairement sur `PORTEE_ODORAT=4` cases (distance de Manhattan, cohérente avec `DetecteurJalonsDoorKey._distance`). Réutilise la convention déjà posée par `DetecteurRessourcesBiologiques` (Ball rouge = Nourriture, Ball bleue = Eau). Portée volontairement courte : c'est un signal de survie grossier qui oriente, pas une carte — la cartographie précise reste le travail de la vue et de `MemoireEpisodiqueSpatiale`.
- **Le goût (2 dims)** : trace **rémanente** de la dernière ressource réellement consommée, décroissant à `DECROISSANCE_GOUT=0.85`/tick (~10 ticks de persistance). C'est le seul état inter-tick du bus, remis à zéro à chaque épisode — un goût est une sensation immédiate liée à une bouchée, pas un état vital continu comme les jauges du `BiologicalHomeostasisEngine`.
- **Dégradation** : identique aux détecteurs génériques §3b — `_MINIGRID_OK` faux ou toute exception d'API désactive le bus définitivement après **un** avertissement et renvoie des zéros. Jamais de crash, jamais de changement du chemin de gradient.

**2. L'identité C1/C2 explicite (`noyau.py` §2, renommée)**

La section 2 devient « LE CERVEAU C1 (RÉFLEXE) & C2 (NÉO-CORTEX) ». Le corps de `penser()` est désormais l'**arbitrage seul**, et la frontière est encapsulée dans deux méthodes nommées :

- **`_executer_c1_reflexe()`** — tout ce qui coûte quasi rien : compression du flux des 5 sens (`_tronc_cerebral` pour les deux sens gourmands, queue du `vecteur_bio` pour les trois autres), contexte épisodique, intégration viscérale, et le réflexe moteur immédiat (`tete_motrice`) en latence zéro.
- **`_solliciter_c2_neocortex()`** — le moteur analytique lourd (`simuler_futur_et_planifier` + JEPA). Il ne reçoit **que** `pensee_bio`, l'état déjà compressé par C1 : jamais les pixels, jamais le MFCC brut, jamais l'environnement — exactement le schéma de `docs/ameliorations_appliquees/Maj_V29_readme.md`.

La fusion `logits_instinct + valeurs_simulees * force_planification` reste **strictement inchangée** depuis la v13.0.

**3. La distillation C2 → C1 : auditée, pas réimplémentée**

Le document de conception présente la distillation comme « la pièce maîtresse ». L'audit de cette version confirme qu'elle est **déjà entièrement réalisée** par le cycle de vie existant de `NaultheneLinearSynaptique` : `annexe_weight` accumule le gradient diurne (C2 guide l'expérience) → `cycle_sommeil()` le consolide dans `base_weight` (C2 → C1) → la Cristallisation Souple (v26.0) fige définitivement les synapses les plus myélinisées. Aucun code ajouté ; la boucle est documentée dans `readme_fr.md` plutôt que dupliquée.

**4. Rétrocompatibilité des `.brain` — greffe par recopie, jamais par exclusion**

`DIM_VECTEUR_BIO` 16 → 24 change la **forme** de `integrateur_bio` (entrée `dim_bus + 16` → `dim_bus + 24`). Le filtre historique de `charger_ou_naitre` traitait ce cas en **excluant** la couche, qui renaissait à neuf — c'est le symptôme exact du bug v24.0-fix4 (bouche silencieuse dans l'Arène). Inacceptable sur un `.brain` portant 1000 jours de vécu.

Nouvelle fonction `_greffer_vecteur_bio_etendu`, appelée **en amont** du filtre : les `dim_bus + 16` premières colonnes gardent leurs poids appris, les 8 dernières conservent leur initialisation Xavier atténuée (même sémantique que `NaultheneLinearSynaptique.agrandir()`). L'agent se réveille avec tous ses acquis et découvre simplement qu'il a désormais un toucher, un odorat et un goût, encore muets. Le filtre d'exclusion reste en place derrière, comme trappe de secours pour tout autre mismatch qu'on ne sait pas greffer.

| Fichier modifié | Changement |
|-----------------|------------|
| `src/naulthene/cerveau/bus_sensoriel.py` | **Nouveau.** `BusSensoriel` (toucher, odorat, goût), constantes `DIM_TOUCHER`/`DIM_CHIMIE`/`PORTEE_ODORAT`/`DECROISSANCE_GOUT`, et `hierarchie_sensorielle()` (description déclarative des 5 sens, lecture seule, pour la doc/télémétrie). Pur numpy, aucun import de `noyau`. |
| `src/naulthene/cerveau/noyau.py` | Version 28 → 29. §2 renommée « LE CERVEAU C1 (RÉFLEXE) & C2 (NÉO-CORTEX) » + note de restructuration. Ajout de `_executer_c1_reflexe()` et `_solliciter_c2_neocortex()` ; `penser()` réduit à l'arbitrage. `DIM_VECTEUR_BIO` 16 → 24. `obtenir_vecteur_bio(..., signaux_sensoriels=None)`. `EtatCognitif.bus_sensoriel`, lecture des sens dans `traiter_tick` avant `penser()`, signal de goût sur consommation FOOD/WATER, reset de la trace de goût aux 2 sites de fin d'épisode. |
| `src/naulthene/cerveau/persistance.py` | Nouvelle `_greffer_vecteur_bio_etendu()` (recopie partielle de `integrateur_bio`, 16 → 24 dims bio), câblée en amont du filtre d'exclusion existant, qui devient une trappe de secours. Import de `DIM_VECTEUR_BIO`. |
| `docs/ameliorations_appliquees/EXPLICATIONS_v29_sens.md` | **Nouveau.** Document explicatif dédié en 11 sections : le problème résolu, la hiérarchie des 5 sens, le détail du Bus Sensoriel (formules du toucher/odorat/goût), pourquoi les sens faibles restent hors de la cible JEPA, l'identité C1/C2, la boucle de distillation (avec table de correspondance note de conception ↔ code existant), JEPA comme Intuition globale, la greffe des `.brain`, les 2 options **volontairement écartées** et pourquoi, la table des 13 validations, le glossaire des constantes. |
| `docs/fonctionnement/explications_readme.md` | Nouvelle §15 (résumé algorithmique en 5 sous-sections, renvoi vers le document dédié) + entrée dans la table des matières + pied de page mis à jour (v28.0 → v29.0). |
| `docs/fonctionnement/LANCEMENT.md` | En-tête V21-V28 → V21-V29 + encadré « rien à configurer ». Note de greffe `👃` en §1. Nouvelle **§9** (observer les 5 sens en direct, vérifier la hiérarchie, tester la greffe sur une copie de `.brain`, ce que la v29.0 ne change pas). 4 nouvelles lignes de dépannage. |
| `readme_fr.md` | Section « Nouveautés v29.0 » + entrée `3s.` dans la table des matières + diagramme d'architecture cognitico-biologique refait (les 5 sens en entrée, blocs C1/C2 nommés, flèche de distillation) + 3 nouvelles sous-sections d'architecture (Bus Sensoriel & hiérarchie, JEPA comme Intuition, boucle de distillation). |
| `CLAUDE.md` | `bus_sensoriel.py` et `EXPLICATIONS_v29_sens.md` ajoutés à l'arborescence ; §2 renommée « C1 (Réflexe) & C2 (Néo-Cortex) » ; 2 puces d'aperçu (C1/C2 nommés, Bus Sensoriel) ; **3 nouveaux garde-fous** dans *Before Modifying Code* (invariants du Bus Sensoriel/vecteur bio, frontière C1/C2 sans court-circuit, greffe par recopie jamais par exclusion) ; version expérimentale de référence 28.0 → 29.0. |

**Validation** (aucun test automatisé dans ce projet — vérifications manuelles exécutées avant livraison) :
- `DIM_VECTEUR_BIO = 24`, `integrateur_bio` en `(16, 40)` sur un cerveau neuf ; `penser()` renvoie 8 logits, `ACTION_DEMANDER` toujours masquée à `-inf` sans plug (**invariant v28.0 préservé**).
- **Greffe d'un `.brain` simulé pré-v29.0** : les 32 premières colonnes recopiées **bit à bit** (`torch.equal` = True) sur tous les buffers (y compris `cristallisee`, booléen), `annexe_weight` remis à zéro, 8 nouvelles colonnes non nulles ; `load_state_dict` sans clé manquante ni inattendue. Un `.brain` déjà v29.0 traverse la fonction **sans modification**.
- **400 ticks** consécutifs sur `MiniGrid-DoorKey-5x5-v0` : signaux sensoriels cohérents (contact frontal = 1.0 face à un mur, odorat = 0.25 pour une source d'eau à 3 cases, goût décroissant de 1.0 → 0.142 en 12 ticks).
- **Nuit complète** puis **neurogenèse** : `integrateur_bio` passe de `(16, 40)` à `(32, 56)` — le segment bio reste fixe à 24 dims pendant que `dim_bus` double (**invariant `segments_in` respecté**) ; 60 ticks post-neurogenèse OK.
- **Round-trip complet** `PersistanceAnatomique.sauvegarder()` → `charger_ou_naitre()` : `integrateur_bio` identique (`torch.equal` = True), 30 ticks après résurrection OK.
- Chemins **`mode_perception="vocal_isole"`** (sans env MiniGrid, 8 nouvelles dims neutres) et **MiniGrid + audio** testés ; tous les modules de la Cuve, des salles de classe et des instruments importent sans erreur.

---

## [28.0-docs2] - 2026-07-30

### Parcourt_readme.md déplacé de la racine vers docs/

| Type | Details |
|------|---------|
| **Commit** | `c5d23dc` |
| **Catégorie** | docs |
| **Impact** | Documentation |

**Demande utilisateur : ranger `Parcourt_readme.md` dans `docs/` plutôt qu'à la racine.**

`git mv Parcourt_readme.md docs/fonctionnement/Parcourt_readme.md` (historique préservé). Tous les liens
relatifs internes au fichier corrigés (`../readme.md` pour remonter à la racine, chemins courts
vers `CHANGELOG.md`/`LANCEMENT.md`/`explications_readme.md` désormais dans le même dossier).
`readme_fr.md` et `CLAUDE.md` mis à jour pour pointer vers `docs/fonctionnement/Parcourt_readme.md`.

| Fichier modifié | Changement |
|-----------------|------------|
| `docs/fonctionnement/Parcourt_readme.md` | Déplacé depuis la racine (`git mv`), liens internes corrigés pour le nouvel emplacement. |
| `readme_fr.md` | Liens mis à jour : `Parcourt_readme.md` → `docs/fonctionnement/Parcourt_readme.md`. |
| `CLAUDE.md` | Entrée déplacée de la liste des fichiers racine vers la description du dossier `docs/`. |

---

## [28.0-docs] - 2026-07-30

### Parcourt_readme.md — guide pratique complet du système de cursus (commandes, jours/ticks, paliers, FAQ)

| Type | Details |
|------|---------|
| **Commit** | `c5d23dc` |
| **Catégorie** | docs |
| **Impact** | Documentation |

**Demande utilisateur : un document unique, à la racine, qui explique de façon vulgarisée et exhaustive TOUT le fonctionnement des 4 parcours d'entraînement (Cursus par Ères, Cerveau Bébé, Cursus de la Parole, la Cuve) — commandes de lancement copier-collables, durée en jours et en ticks/jour de chacun, détail complet des 5 niveaux MiniGrid, des 7 paliers DoorKey, des 19 paliers vocaux, Mode Guidé/Libre, patience adaptative, et un rappel explicite qu'aucune progression ne régresse actuellement. Rédigé à partir d'une lecture directe du code (`noyau.py`, les 3 scripts de `salles_de_classe/`), pas de mémoire — toutes les valeurs (ticks/jour, seuils, poids de choc) vérifiées contre les constantes réelles.**

Nouveau fichier `Parcourt_readme.md`, à la racine du dépôt (comme `readme_fr.md`) plutôt que dans
`docs/` — c'est un guide pratique de premier niveau ("je veux lancer un run"), complémentaire à
`docs/fonctionnement/LANCEMENT.md` (guide opérationnel technique, options CLI complètes) et
`docs/fonctionnement/explications_readme.md` (détail algorithmique/mathématique). Référencé depuis `readme_fr.md`
(table des matières + lien en tête de la Vue d'Ensemble) et `CLAUDE.md` (arborescence).

| Fichier modifié | Changement |
|-----------------|------------|
| `Parcourt_readme.md` | **Nouveau.** 14 sections : vue d'ensemble des 4 parcours, détail par cursus (commande, rythme ticks/jour, phases/ères), les 5 niveaux MiniGrid, les 7 paliers DoorKey, les 19 paliers vocaux, Mode Guidé/Libre, patience adaptative, absence de régression, emplacement des `.brain`, lecture annotée d'un bilan de nuit, FAQ. |
| `readme_fr.md` | Entrée `3t.` dans la table des matières pointant vers `Parcourt_readme.md` ; lien de renvoi ajouté juste après le tableau des 5 niveaux dans la Vue d'Ensemble. |
| `CLAUDE.md` | `Parcourt_readme.md` ajouté à l'arborescence *Architecture* (fichiers racine). |

**Validation** : toutes les valeurs numériques du document (ticks/jour par cursus : 400/3600/800 ; seuils DoorKey 2+2 ; seuils vocaux 0.15→0.45 ; `PATIENCE_MIN/MAX` 50/350 ; `FORCE_PLANIFICATION_GUIDE/LIBRE` 0.5/0.85 ; `SEUIL_PALIER_MODE_LIBRE=5` ; `JOUR_FIN_MASQUAGE_EXTERNE=240`) vérifiées par grep direct sur `noyau.py` et les 3 scripts de cursus avant rédaction, aucune valeur inventée ou approximée.

---

## [28.0-experimental] - 2026-07-30

### La Cascade C1 → C2 → C3 & le Port Exocortex — un troisième cerveau optionnel, jamais dans le chemin de gradient

| Type | Details |
|------|---------|
| **Commit** | `c5d23dc` |
| **Catégorie** | feat (nouvelle mécanique cognitive majeure, expérimentale) |
| **Impact** | Critique (architecture du réseau, persistance) |

**Contexte utilisateur : ouvrir Naulthène à un greffon externe optionnel (Exocortex C3 — LLM lourd, RAG, recherche web, ou un autre cerveau Naulthène) sans jamais compromettre l'autonomie biologique du Cœur Organique [C1 (réflexe) + C2 (raison/JEPA)]. Principe non négociable posé par l'utilisateur : couper le courant de C3 ne doit ni planter, ni renvoyer d'erreur, ni changer le comportement d'un cerveau existant — l'agent bascule silencieusement sur sa curiosité intrinsèque déjà présente. Décision structurante : "interroger C3" n'est PAS un déclenchement sur seuil d'incertitude, c'est un CHOIX APPRIS par REINFORCE (une 8ème action, "tendre la main"), au même titre que les 7 actions MiniGrid — l'agent apprend lui-même quand demander de l'aide, jamais un `if erreur > seuil`. C3 est conçu comme un Port Multiplexeur (bus) sur lequel des "Plugs" interchangeables s'enregistrent (BrainToBrain, Ollama, VectorDB, Web...), plutôt qu'un appel figé vers un service unique.**

**Chantier 1 — Le Port Multiplexeur** (nouveau sous-package versionné `src/naulthene/exocortex/`) : `PortC3` (le bus), `RequeteC3`/`ReponseC3` (le contrat neutre — uniquement des vecteurs numpy et des scalaires, jamais un tenseur PyTorch, jamais l'agent lui-même), `PlugC3` (classe de base abstraite). Isolation totale : `canal_emission` capture TOUTE exception d'un plug (jamais de fuite vers le noyau) et met le plug fautif en cooldown (`COOLDOWN_PLUG_ECHEC=200` ticks) plutôt que de repayer un timeout complet à chaque tick — la leçon retenue du seul précédent d'appel externe du projet (`professeur_gemma.py`, aucun health-check, jusqu'à 60s de timeout par appel). Trois plugs livrés : `PlugNul` (toujours absent, mode nominal), `PlugSimule` (déterministe, flag `panne` activable en vol pour les crash-tests), `PlugHTTP` (backend générique JSON/HTTP, choix explicite de l'utilisateur plutôt qu'un fournisseur figé).

**Chantier 2 — Le choix appris.** `num_actions` passe de 7 (`NUM_ACTIONS_BASE`) à 8 (`NUM_ACTIONS_AVEC_C3`) : la 8ème action, `ACTION_DEMANDER`, est masquée à `-inf` dans les logits tant qu'aucun plug n'est disponible (`penser()`) — comportement bit-identique à la v27.6 sans plug branché. Nouvelle couche `tete_requete` (tête de routage : vers quel plug émettre, ou diffusion `1_X`), ajoutée aux 4 points de synchronisation (`__init__`, `fortifier_synapses`, `cycle_sommeil_global`, `declencher_neurogenese` — les 4, pas 3, contrairement à la formulation générique de CLAUDE.md). Le rollout mental (`simuler_futur_et_planifier`) remonte désormais aussi `indecision_c2` (l'écart-type brut du rollout, calculé puis jeté depuis la v10.0) — un simple CONTEXTE transmis dans `RequeteC3`, jamais un déclencheur (décision utilisateur explicite). L'action `ACTION_DEMANDER` substitue l'action MiniGrid "done" (6, seule action réellement neutre) à `env.step()` — jamais un pas d'environnement inventé — et coûte `COUT_REQUETE_C3=0.01` en `recompense_interne` (sans quoi REINFORCE apprendrait à spammer le bus gratuitement).

**Chantier 3 — La trappe de secours.** Purement structurelle, aucun code nouveau : sans plug, le masquage rend l'action inexistante ; un plug qui échoue en vol part en cooldown et la curiosité intrinsèque (`DetecteurCuriositeJEPA`) et le Sursaut de Volonté restent actifs en permanence, jamais conditionnés à C3.

**Chantier 4 — Registre d'Assimilation.** Une réponse C3 est mise en attente (`reponse_c3_en_attente`) et appliquée au tick SUIVANT (le bus répond après coup, jamais dans le même pas que l'émission) : sous `SEUIL_OVERRIDE_C3=0.85` de confiance, elle biaise les logits (`+= FORCE_C3 * préférences`, même forme que l'arbitrage C2) ; au-dessus, elle impose l'action (le `log_prob` reste alors celui de l'action réellement jouée sous la distribution courante, pour ne pas invalider REINFORCE). Un conseil C3 suivi d'un succès devient un 3ème canal du "OU doux" v27.0 (`POIDS_DOPAMINE_C3=0.5`, formule étendue à 3 facteurs, toujours bornée dans [0,1] et rétrocompatible à l'identique si `poids_c3=0`) — le LTP (`fortifier_synapses`) et l'importance majorée du souvenir (`micro_boost_ancrage`, déjà existant) font le reste : la trace est rejouée en priorité la nuit, sans réintroduire de distillation supervisée dans la politique (hors du chemin de gradient, cohérent avec la contrainte "pas de Transformer" de `docs/ameliorations/AMELIORATION_V1.md`).

**Le risque n°1 : rétrocompatibilité des `.brain` existants.** `load_state_dict(strict=False)` gère les clés absentes mais PAS un mismatch de forme sur une clé présente des deux côtés — passer à 8 actions change la forme de `tete_motrice`/`generateur_attente`/`generateur_attente_audio`/`actions_eye`. Nouvelle fonction `_greffer_action_supplementaire` (généralise le patron du filtre `integrateur_bio` déjà existant, mais par RECOPIE plutôt que par exclusion) : chaque bloc `[:7]` existant est recopié dans le nouveau tenseur `[:8]`, la 8ème ligne/colonne restant à son initialisation Xavier atténuée — même sémantique que `NaultheneLinearSynaptique.agrandir()`.

| Fichier modifié | Changement |
|-----------------|------------|
| `src/naulthene/exocortex/__init__.py`, `port_c3.py`, `plugs/{__init__,plug_nul,plug_simule,plug_http}.py` | **Nouveaux**, versionnés — le Port Multiplexeur et 3 plugs. |
| `src/naulthene/cerveau/noyau.py` | Nouvelle section `# --- 3h. LE PORT EXOCORTEX C3 ---` (constantes) ; `num_actions=8` par défaut ; couche `tete_requete` (4 points de sync) ; `port_c3` sur `AGI_Naulthene` ; `penser()` masque l'action 7 et retourne `logits_routage`/`indecision_c2` en plus ; `simuler_futur_et_planifier` remonte `indecision_c2` ; `traiter_tick` : émission/réception C3, coût, dopamine 3ème canal, override/biais de la réponse en attente, télémétrie W&B (`Dopamine_Poids_C3_Moyen`, `Requetes_C3_Jour`, `Reponses_C3_Jour`, `Taux_Reponse_C3`). |
| `src/naulthene/cerveau/persistance.py` | Nouvelle fonction `_greffer_action_supplementaire` (greffe par recopie 7→8) appelée dans `charger_ou_naitre` avant `load_state_dict`. |

**Validation** : import de tous les modules du package sans erreur (`noyau`, `persistance`, `daemon_cerveau`, `client_corps`, `lancer_arene`, `irm_cerveau`, `evaluer_cerveau`) ; test d'invariance (300 ticks sans plug, `ACTION_DEMANDER` jamais échantillonnée, seules les 7 actions historiques apparaissent) ; test de rétrocompatibilité sur les 3 vrais `.brain` existants (`naulthene_parole.brain` 300j palier vocal 19/19, `naulthene_cursus.brain`, `naulthene_bb.brain`) chargés sans exception, poids des 7 actions existantes préservés au bit près (vérifié par égalité tensorielle exacte) ; test de déconnexion en vol (`PlugSimule.panne` basculé en cours d'épisode) : aucune exception ne remonte, le plug part en cooldown, l'action redevient masquée au tick suivant ; test des 4 points de synchronisation (`tete_requete` correctement traitée par `cycle_sommeil_global`/`fortifier_synapses`/`declencher_neurogenese`) ; runs réels de 2 jours subjectifs sur les 3 cursus (`cursus_developpemental.py`, `cursus_bebe.py`, `cursus_parole.py`, cerveaux neufs isolés) sans aucune erreur, y compris une neurogenèse réelle traversant `tete_requete`. Les `.brain` réels du dépôt vérifiés strictement inchangés (comparaison octet à octet) après tous les tests.

---

## [27.6-experimental] - 2026-07-27

### Gradient vocal étendu aux 8 paramètres — la voix intègre f0/F3/durée/amplitude, dynamiquement, jamais en dur

| Type | Details |
|------|---------|
| **Commit** | `c5d23dc` |
| **Catégorie** | feat (correctif de conception majeur, mécanique expérimentale) |
| **Impact** | Critique (apprentissage vocal) |

**Décision utilisateur : "le cerveau doit intégrer le son peu importe la forme, en même temps que la vue, et être capable de le restituer — rien ne doit être écrit en dur, tout doit être dynamique." Diagnostic sur un cerveau réel de 300 jours (`naulthene_parole.brain`, palier vocal 19/19) : 6 des 8 paramètres physiques de `tete_vocale` (f0, F3, F1_bw, F2_bw, durée, amplitude) étaient restés figés à leur valeur de naissance au dixième près, quel que soit le nombre de jours d'entraînement — seuls F1/F2 (la "voyelle") recevaient jamais de gradient MSE dirigé (`indices_contraints = [1, 2]`, en dur depuis v22.1). L'agent produisait donc toujours le même timbre/hauteur/durée de voix, même après une longue exposition à une voix réelle riche. La question complémentaire de l'utilisateur ("le cerveau écoute-t-il précisément le temps du mot ?") a confirmé que l'entrée auditive (MFCC figé) était déjà correcte — le problème était uniquement du côté de l'APPRENTISSAGE de la sortie, pas de la perception.**

**Correctif en trois volets, tous DYNAMIQUES (aucune valeur écrite en dur) :** (1) `hemisphere_audio.py` gagne `estimer_pitch_f0` (autocorrélation, technique standard de pitch-tracking — aucune constante, la fréquence est cherchée dans la plage physique `BORNES_F0`), `estimer_duree_amplitude` (mesures directes du signal : longueur réelle, crête absolue), et l'extraction de F3 est ajoutée à `estimer_formants_lpc` (3e racine LPC triée, déjà calculée mais jusqu'ici ignorée). `estimer_parametres_vocaux_complets`/`_agreges` combinent les trois pour produire les 8 paramètres à partir d'UN enregistrement réel (F1_bw/F2_bw n'ont pas d'équivalent mesurable simplement par LPC — repli sur le centre de leur plage de synthèse, pas une valeur de voix théorique). (2) `lecons_vocales.CacheReferencesVocales` retourne désormais ce dict à 8 dimensions — dérivé de la banque personnelle si elle existe, SINON de la référence `say` elle-même (déjà générée dans ce chemin) : même le repli `say` devient une estimation acoustique dynamique, plus une table théorique figée (`VOYELLES_CIBLES` et `_voyelle_dominante`, devenues mortes, retirées). (3) `noyau._construire_cible_vocale` normalise chaque dimension EFFECTIVEMENT présente dans `formants_cibles` (au lieu de F1/F2 systématiquement) ; `_evaluer_production_vocale` calcule `indices_contraints` à partir des clés réellement fournies — un appelant qui ne donne encore que F1/F2 (`client_professeur.py`) reste contraint à `[1, 2]`, rétrocompatibilité stricte ; un appelant qui fournit les 8 clés (les 3 cursus, l'Arène, via `CacheReferencesVocales`) contraint désormais les 8 dimensions.**

| Fichier modifié | Changement |
|-----------------|------------|
| `src/naulthene/audio/hemisphere_audio.py` | `estimer_formants_lpc` retourne aussi `F3` (3e candidat trié des racines LPC déjà calculées). Nouvelles `estimer_pitch_f0` (autocorrélation), `estimer_duree_amplitude` (mesure directe), `estimer_parametres_vocaux_complets`/`_agreges` (les 8 paramètres, combinant les trois). |
| `src/naulthene/audio/lecons_vocales.py` | `_generer_si_absent` utilise `estimer_parametres_vocaux_agreges`(banque)/`estimer_parametres_vocaux_complets`(repli `say`) au lieu de `estimer_formants_agrege`(2 dims)/`VOYELLES_CIBLES` théorique. `_mot_cible_du_palier` simplifiée (ne retourne plus de formants théoriques, devenus inutiles). `_voyelle_dominante` retirée (plus aucun appelant). |
| `src/naulthene/cerveau/noyau.py` | Import étendu (`BORNES_F0/F3/BW/DUREE/AMPLITUDE`). `_construire_cible_vocale` : boucle sur les 8 dimensions (clé présente → normalisée, absente → neutre 0.5) au lieu de F1/F2 en dur. `_evaluer_production_vocale` : `indices_contraints` calculés dynamiquement depuis les clés présentes dans `formants_cibles`, plus `[1, 2]` fixe. |

**Validation** : `estimer_pitch_f0`/`estimer_duree_amplitude`/`estimer_parametres_vocaux_complets` testés sur les 5 voyelles + "porte" via `say` (f0 dans une plage plausible 135-207Hz, durée/amplitude cohérentes avec le signal réel, valeurs clampées correctement) ; agrégation multi-prises et repli sur liste vide vérifiés ; `_construire_cible_vocale` testée avec dict complet (8 dims normalisées) et partiel (F1/F2 seuls, reste neutre) ; indices contraints vérifiés dynamiques dans les deux cas (`[0..7]` complet, `[1,2]` partiel = rétrocompatibilité stricte avec `client_professeur.py`) ; run réel de 2 jours sur `naulthene_parole.brain` (cerveau de 300 jours, palier 19/19) confirmant le déblocage effectif : `f0` 190.0→187-189 (mouvement vers la cible 114.7), `F3` 2750.0 (figé depuis 300 jours)→2730-2744 (mouvement vers la cible 2502.1), `durée` 0.3→0.4 (vers la cible 0.6), en seulement 2 jours d'entraînement supplémentaires ; non-régression confirmée sur `cursus_developpemental.py` (2 jours, aucune erreur) ; les 4 points de synchronisation des couches vérifiés intacts ; tous les modules consommateurs importés sans erreur. Les deux cerveaux de test restaurés à leur état pré-vérification après validation.

---

## [27.5-experimental] - 2026-07-27

### Dopamine vocale proportionnelle à la méconnaissance — corrige la "boucle infinie de promotion vocale"

| Type | Details |
|------|---------|
| **Commit** | `c5d23dc` |
| **Catégorie** | fix (défaut de conception, mécanique expérimentale) |
| **Impact** | Critique (réservoir dopaminergique) |

**Diagnostic détaillé de l'utilisateur, confirmé par lecture du code : une fois le dernier palier du curriculum vocal (19) atteint, `promouvoir_palier_vocal_si_merite` continuait d'enregistrer des succès et d'afficher `🎓 [PROMOTION VOCALE]` tous les ~2 jours (bug de log — la garde existante empêchait bien le dépassement du palier 19, mais pas l'affichage du message ni l'accumulation de "succès fantômes" dans le gestionnaire). Plus important : `poids_vocal` (le score de prononciation du tick) alimentait la dopamine (`POIDS_DOPAMINE_VOCAL * poids_vocal`), le LTP hebbien et la micro-récompense RL SANS AUCUNE décroissance liée à la maîtrise déjà acquise — un agent qui maîtrise parfaitement le curriculum vocal depuis longtemps recevait le même choc dopaminergique qu'un débutant qui vient de réussir sa première voyelle. Sur un cerveau resté bloqué sur MiniGrid (Collège, palier DoorKey 7), ce shoot quotidien maintenait `teneur_dopamine`/`plasticite_base` artificiellement hauts, sans la tension motivationnelle nécessaire pour progresser sur le reste du cursus — exactement le mécanisme décrit par l'utilisateur ("moins il sait, plus l'effet est fort ; plus il sait, moins les effets sont forts").**

**Correctif en deux volets.** (1) Nouvelle fonction `facteur_nouveaute_vocale(etat)` : décroissance LINÉAIRE de 1.0 (palier 1) à `FACTEUR_NOUVEAUTE_VOCALE_MIN=0.1` (palier 19, jamais 0 — cohérent avec `TAUX_FRICTION`, rien dans ce moteur ne tombe à un plancher dur exactement nul), appliquée à `poids_vocal` **uniquement** pour la dopamine/le LTP/la micro-récompense — **jamais** pour la perte MSE supervisée (l'agent doit continuer à s'entraîner à plein régime, sinon il désapprendrait) ni pour `score_vocal_jour`/la logique de promotion (sinon le mécanisme de promotion s'auto-invaliderait). Le Module Parent ("Oui !"/"Non !") continue de juger le score BRUT, pas le score pondéré, pour ne jamais fausser sa décision. (2) `promouvoir_palier_vocal_si_merite` court-circuite dès `etat.palier_vocal >= len(CURRICULUM_VOCAL)`, avec un unique message `🏆 [MAÎTRISE VOCALE]` affiché une seule fois à la transition finale plutôt qu'un `🎓 [PROMOTION VOCALE]` répété indéfiniment.

**Question complémentaire de l'utilisateur, clarifiée** : le système n'écoute PAS "pendant X secondes le temps du mot" en fonction de ce que l'agent regarde — `obs_auditive` est un vecteur MFCC statique (un instantané figé, pas un flux temporel), envoyé identique à chaque tick tant que la cible ne change pas. Le mécanisme de stabilité de la case frontale (v27.4, `SEUIL_STABILITE_SYNESTHESIE`) contrôle QUAND la cible peut changer, pas combien de temps l'oreille "écoute" — ce sont deux mécanismes distincts, et aucun des deux ne modélise une vraie durée d'écoute.

| Fichier modifié | Changement |
|-----------------|------------|
| `src/naulthene/cerveau/noyau.py` | Nouvelle constante `FACTEUR_NOUVEAUTE_VOCALE_MIN=0.1`. Nouvelle fonction `facteur_nouveaute_vocale(etat) -> float`. `_traiter_tick_vocal_isole` : `poids_vocal_dopamine = poids_vocal * facteur_nouveaute_vocale(etat)` utilisé dans `poids_evenement`, `poids_vocal` brut conservé pour `_appliquer_feedback_parent_vocal`. `traiter_tick` : même principe, plus `micro_recompense_vocale` également pondérée avant d'entrer dans `recompense_interne`. `promouvoir_palier_vocal_si_merite` : court-circuit au dernier palier + message `🏆 [MAÎTRISE VOCALE]` unique. |

**Validation** : `facteur_nouveaute_vocale` testée sur plusieurs paliers (1→1.0, 5→0.8, 10→0.55, 15→0.3, 19→0.1, clamp au-delà de 19) ; comparaison directe de la contribution dopaminergique pour un même score de prononciation (0.9) : 0.630 au palier 1 vs 0.063 au palier 19 (facteur 10 de réduction) ; court-circuit du message de fausse promotion vérifié (aucun affichage à `palier_vocal=19` avec un score parfait sur 100 ticks) ; transition réelle 18→19 vérifiée (4 appels simulant les 4 succès requis, message de maîtrise affiché une seule fois, silence confirmé sur 5 appels suivants) ; run réel de 2 jours sur un cerveau neuf `naulthene_parole.brain` (phase 1, synesthésie active) sans erreur ni message de fausse promotion.

---

## [27.4-experimental] - 2026-07-27

### Cible synesthésique stabilisée — la cible vocale n'est publiée qu'après une exposition continue

| Type | Details |
|------|---------|
| **Commit** | `c5d23dc` |
| **Catégorie** | fix (défaut de conception, mécanique expérimentale) |
| **Impact** | Fonctionnel (mécanisme d'apprentissage vocal, phases 1-2 du Cursus de la Parole) |

**Diagnostic de l'utilisateur, confirmé par lecture du code : en phases 1-2 (synesthésie active), `LecteurCaseFrontale.lire`/`lire_syntagme` sont relues à CHAQUE tick, donc la cible vocale changeait aussi vite que le regard de l'agent — jusqu'à 10×/seconde dans l'Arène, sans aucune notion de "temps nécessaire pour apprendre un mot". Un agent qui tournait sur lui-même voyait sa cible passer de "mur" à "vide" à "porte" en 2-3 ticks, sans jamais laisser à `porte_auditive`/`tete_vocale` le temps d'associer le son au bon objet. Nouvelle méthode `LecteurCaseFrontale.lire_stable` : la cible publiée ne change que si l'agent a regardé LE MÊME mot pendant au moins `SEUIL_STABILITE_SYNESTHESIE=20` ticks CONSÉCUTIFS (un aller-retour du regard remet le compteur à zéro, sans tolérance) ; tant qu'aucune cible n'a jamais été stabilisée, aucune correction n'est appliquée (`formants_cibles=None`) plutôt que de risquer une fausse association. `cursus_parole._cible_synesthesique` retourne désormais un booléen `notable` en plus de `(mot, mfcc, formants)`, consommé par `_perception_du_tick_parole` pour désactiver la correction/le score spectral tant que la cible n'est pas stabilisée.**

| Fichier modifié | Changement |
|-----------------|------------|
| `src/naulthene/cerveau/noyau.py` | Nouvelle constante `SEUIL_STABILITE_SYNESTHESIE=20`. `LecteurCaseFrontale.__init__` gagne un état de stabilisation (`_mot_brut_courant`, `_ticks_stables`, `_cible_stabilisee`). Nouvelle méthode `lire_stable(env, seuil_stabilite, syntagme) -> (mot, type_objet, couleur, stable_ce_tick)`. |
| `src/naulthene/salles_de_classe/cursus_parole.py` | `_cible_synesthesique` utilise `lire_stable` au lieu de `lire`/`lire_syntagme` bruts, retourne `(mot, mfcc, formants, notable)`. `_perception_du_tick_parole` (phase 1 matin, phase 2) : `formants_cibles`/`mfcc_references` conditionnés par `guide AND notable` au lieu de `guide` seul. |

**Validation** : test sur `MiniGrid-DoorKey-6x6-v0` réel — agent qui tourne en boucle (action "left" en continu) ne stabilise jamais aucune cible sur 60 ticks (comportement voulu : jamais de fausse association) ; agent immobile (action "done" en boucle) stabilise sa cible exactement au tick `SEUIL_STABILITE_SYNESTHESIE` puis la conserve. Run réel de 3 jours sur `naulthene_parole.brain` traversant la transition phase 0→phase 1 (jour 300, `lire_stable` exercée en conditions réelles) : aucune erreur, promotion de palier vocal validée normalement.

---

## [27.3-experimental] - 2026-07-27

### Rythme de lecture vocale ralenti dans l'Arène — corrige l'effet "métronome" (TUT TUT TUT)

| Type | Details |
|------|---------|
| **Commit** | `c5d23dc` |
| **Catégorie** | fix (mécanique expérimentale) |
| **Impact** | Fonctionnel (qualité de la démo audio, aucune conséquence sur l'entraînement) |

**Second correctif signalé par l'utilisateur après [27.2] : les micro-coupures avaient disparu, mais le résultat sonnait comme un martèlement régulier ("TUT TUT TUT") plutôt qu'un rythme de parole — `PERIODE_LECTURE_VOCALE=5` (0.5s) laissait le son finir mais enchaînait quasi immédiatement le suivant, sans silence perceptible. Remonté à 18 ticks (≈1.8s à `FPS_ARENE=10`), plus proche du rythme naturel d'un mot prononcé toutes les 1.5-2s. `hemisphere_audio.BORNES_DUREE` (0.1-0.6s, la plage physique que `tete_vocale` apprend à viser sur TOUS les cursus) n'est volontairement PAS touchée — ce n'est qu'un problème de cadence d'AFFICHAGE dans l'Arène, la faire bouger perturberait l'apprentissage en cours sur les autres cursus pour un problème qui n'existe que dans un outil d'observation.**

**Diagnostic complémentaire (échantillonnage réel sur `naulthene_parole.brain`, jour 20/300)** : le "bip" répété plutôt qu'une syllabe qui varie est cohérent avec l'état d'apprentissage — sur 6 ticks consécutifs, `tete_vocale` produit des paramètres vocaux quasi identiques (`f0≈190Hz`, `F1_bw`/`F2_bw`/`durée`/`amplitude` figés sur des valeurs rondes, F1/F2 ne variant que de quelques Hz). Seuls F1/F2 reçoivent un vrai gradient supervisé (voir `noyau._evaluer_production_vocale`) ; les 6 autres paramètres n'évoluent qu'indirectement (LTP/rêve) et n'ont pas encore développé de variation temporelle notable à ce stade — pas un bug, un cerveau encore jeune sur le plan vocal.

| Fichier modifié | Changement |
|-----------------|------------|
| `src/naulthene/instruments/lancer_arene.py` | `PERIODE_LECTURE_VOCALE` 5 → 18 (≈0.5s → ≈1.8s). |

**Validation** : import du module vérifié sans erreur ; échantillonnage direct des paramètres vocaux produits par `naulthene_parole.brain` sur 6 ticks réels (`traiter_tick`) pour confirmer que le manque de variation vient de l'état d'apprentissage, pas d'un défaut de synthèse.

---

## [27.2-experimental] - 2026-07-27

### Lecture vocale espacée dans l'Arène — corrige les micro-coupures audio permanentes

| Type | Details |
|------|---------|
| **Commit** | `c5d23dc` |
| **Catégorie** | fix (mécanique expérimentale) |
| **Impact** | Fonctionnel (qualité de la démo audio, aucune conséquence sur l'entraînement) |

**Signalé par l'utilisateur : le babil de l'agent joué par l'Arène (`lancer_arene.py`) sonnait comme une suite ininterrompue de micro-coupures/craquements. Cause : `jouer_son_temps_reel` était appelée à CHAQUE tick (10/s, `FPS_ARENE`) en mode non-bloquant (`sd.play(..., bloquant=False)`) — un son synthétisé dure entre 0.1 et 0.6s (`hemisphere_audio.BORNES_DUREE`), donc un nouveau `sd.play()` coupait quasi systématiquement le son précédent en plein milieu, indépendamment du niveau réel d'apprentissage vocal du cerveau observé. La lecture (pas le calcul du score) est désormais espacée : un seul son émis toutes les `PERIODE_LECTURE_VOCALE=5` ticks (0.5s, au-dessus de la durée maximale d'un son), laissant chaque vocalisation se terminer avant la suivante. Le score de formants et la télémétrie continuent d'être recalculés à CHAQUE tick — seule l'émission sonore est ralentie.**

| Fichier modifié | Changement |
|-----------------|------------|
| `src/naulthene/instruments/lancer_arene.py` | Nouvelle constante `PERIODE_LECTURE_VOCALE=5`. L'appel à `synth.synthetiser`/`jouer_son_temps_reel` est conditionné à `ticks_journee_observation % PERIODE_LECTURE_VOCALE == 0` ; le calcul de `formants_produits`/`score_vocal` (télémétrie) reste hors de cette condition, à chaque tick. |

**Validation** : import du module vérifié sans erreur ; la garantie de non-altération du `.brain` (aucun `executer_nuit`/`apprendre_journee`/`rever` appelé) est inchangée par ce correctif, qui ne touche qu'à la cadence de lecture audio.

---

## [27.1-experimental] - 2026-07-27

### Tirage aléatoire d'une prise vocale à chaque appel — variation naturelle plutôt qu'un gabarit moyenné figé

| Type | Details |
|------|---------|
| **Commit** | `18e8c7a` |
| **Catégorie** | feat (correctif de conception, mécanique expérimentale) |
| **Impact** | Fonctionnel (mécanisme d'apprentissage vocal) |

**Décision utilisateur : quand plusieurs prises existent pour un mot (`voix/<mot>/<mot>_01.wav`, `_02.wav`, `_03.wav`...), l'oreille de l'agent (`porte_auditive`) ne doit jamais entendre un seul gabarit artificiel figé, mais la vraie variation naturelle d'une voix humaine — pour forcer l'agent à généraliser (reconnaître "mur" malgré le bruit inter-prise) plutôt qu'à mémoriser un son qui n'existe pas en dehors du cache. Jusqu'ici, `CacheReferencesVocales.obtenir_pour_palier` — la méthode appelée à chaque tick par les 3 cursus et l'Arène — renvoyait la MOYENNE des MFCC de toutes les prises d'un mot, calculée une fois et mise en cache : un seul son moyenné et identique du premier au dernier tick d'un run. Elle tire désormais UNE prise au hasard, uniformément, À CHAQUE APPEL (donc potentiellement à chaque tick) — vérifié sur 300 tirages avec 3 prises synthétiques distinctes : les 3 reviennent, en proportions proches de l'uniforme (83/94/123). Avec 0 ou 1 prise (repli `say` ou banque incomplète), le tirage se réduit trivialement à cette unique prise — comportement strictement inchangé.**

| Fichier modifié | Changement |
|-----------------|------------|
| `src/naulthene/audio/lecons_vocales.py` | `_generer_si_absent` : condition de présence en cache basée sur `_cache_mfcc_prises` (liste des prises individuelles) au lieu de `_cache_mfcc` (moyenne) — la moyenne (`_cache_mfcc`) est conservée pour diagnostic/repli `say` mais n'est plus lue par `obtenir_pour_palier`. `obtenir_pour_palier` : tire `prises[np.random.randint(len(prises))]` à chaque appel au lieu de renvoyer la moyenne mise en cache. `obtenir_mfcc_prises` (canal spectral, `recompense_vocale_mixte`) inchangée — continue de comparer au score MAX sur TOUTES les prises, indépendamment de celle tirée pour l'audition ce tick-là. |

**Validation** : fixture de test à 3 prises synthétiques acoustiquement distinctes (tonalités 400/600/800 Hz) — 300 tirages donnent bien 3 signatures MFCC distinctes, aucune ne domine anormalement ; repli `say`/1-prise vérifié strictement stable (10 tirages consécutifs → 1 seule signature) ; tous les modules consommateurs (`cursus_parole.py`, `cursus_bebe.py`, `cursus_developpemental.py`, `lancer_arene.py`) réimportés sans erreur après le changement.

---

## [27.0-experimental] - 2026-07-27

### L'École de la Parole & Synesthésie — voix réelle de l'utilisateur, synesthésie ancrée dans la vision, dopamine unifiée

| Type | Details |
|------|---------|
| **Commit** | N/A — `src/naulthene/cerveau/noyau.py` est gitignored (terrain d'essai expérimental), aucun commit ne le modifie ; voir la table ci-dessous pour les fichiers packagés réellement commités |
| **Catégorie** | feat (nouvelle mécanique cognitive majeure) |
| **Impact** | Critique (mécanisme de récompense/dopamine) + Fonctionnel (local uniquement) |

**Trois décisions structurantes referment les trois plus gros écarts entre l'hémisphère audio (v22.0-v26.0) et une vraie acquisition du langage ancrée dans le monde. (1) La cible vocale n'est plus une table théorique (`VOYELLES_CIBLES`) mais la voix RÉELLE de l'utilisateur : une banque d'enregistrements disque (`voix/<mot>/<mot>_NN.wav`, `instruments/enregistreur_voix.py`, recadrage de silence via `librosa.effects.trim`) alimente un estimateur de formants par analyse LPC (`hemisphere_audio.estimer_formants_lpc`, filtre inverse du modèle source-filtre du synthétiseur, clampé aux bornes physiques de `tete_vocale` pour rester atteignable), et une distance/récompense spectrale MFCC↔MFCC (`distance_spectrale`/`recompense_spectrale`) note l'agent sur le son RÉELLEMENT synthétisé et pas seulement sur deux nombres — `recompense_vocale_mixte` combine les deux (0.6 formants / 0.4 spectral, F1/F2 restant dominants car ce sont les seules dimensions sur lesquelles `tete_vocale` reçoit un gradient MSE dirigé), avec repli exact sur `recompense_formants` seule quand aucune prise n'existe (rétrocompatibilité stricte). (2) La synesthésie devient réelle : un nouveau lecteur générique (`LecteurCaseFrontale`, section 3g, `env.unwrapped.front_pos`) lit le mot à nommer directement dans la case devant l'agent — mur/porte/clé/but/vide, puis des syntagmes couleur+objet ("porte jaune") — au lieu d'un curriculum vocal déroulé indépendamment de ce que l'agent regarde ; 5 nouveaux paliers (15-19) étendent `CURRICULUM_VOCAL` en conséquence. (3) La dopamine devient unifiée entre les deux modalités : le `max(canaux visuels…, canal vocal)` pré-v27.0, qui laissait un agent recevoir la même dopamine qu'il ait fait UNE chose bien ou DEUX à la fois, est remplacé par une agrégation probabiliste "OU doux" (`1 - (1 - w_v·visuel)·(1 - w_a·vocal)`, `POIDS_DOPAMINE_VISUEL=1.0`, `POIDS_DOPAMINE_VOCAL=0.7`), bornée dans [0,1] par construction et rétrocompatible au bit près quand `poids_vocal=0`. En plus : la consolidation nocturne rejoue désormais l'audio pendant le rêve (`AGI_Naulthene.rever` gagne `coeff_jepa_audio`, `memoire_moyen_terme` stocke `obs_auditive`) — jusqu'ici tout l'apprentissage vocal du jour s'érodait la nuit sans jamais être consolidé ; le synthétiseur de formants est vectorisé (`scipy.signal.lfilter`, ~100× plus rapide, sortie numériquement identique) pour absorber le coût du canal spectral ; deux bugs bloquants sont corrigés (`score_vocal_jour`/`ticks_vocaux_jour` jamais remis à zéro → promotion vocale figée après quelques centaines de jours ; standardisation MFCC par constantes calibrées sur `say` → risque de re-saturer la sigmoid face à une vraie voix, remplacée par une standardisation par échantillon) ; un bug latent est corrigé (`"clé"` ne contenait aucune voyelle de `VOYELLES_CIBLES` avant dépliage NFD des accents). Nouveau troisième cursus développemental, `salles_de_classe/cursus_parole.py` (`naulthene_parole.brain`, dédié, jamais partagé), 900 jours × 800 ticks en 3 phases pédagogiques : Imprégnation totale (guidage=1.0 constant, correction même quand l'agent a bon) → Autonomie guidée (matin synesthésie/après-midi curriculum, guidage 1.0→0.4) → Émancipation (synesthésie + syntagmes toute la journée, guidage 0.4→0.1, Gemma en jugement qualitatif de fin de journée uniquement).**

| Fichier modifié | Changement |
|-----------------|------------|
| `src/naulthene/cerveau/noyau.py` | En-tête corrigé (v20→v27). Import module-level de `hemisphere_audio` (pur numpy, sans risque de cycle). Nouveaux helpers §4b factorisés (`_construire_cible_vocale`, `_evaluer_production_vocale`, `promouvoir_palier_vocal_si_merite`) remplaçant 2 paires de blocs dupliqués entre `traiter_tick`/`_traiter_tick_vocal_isole`. Nouvelle section 3g `LecteurCaseFrontale` (générique, sans état inter-tick). Dopamine unifiée (`POIDS_DOPAMINE_VISUEL`/`POIDS_DOPAMINE_VOCAL`, formule "OU doux") dans les deux chemins de tick. `_reinitialiser_buffers_journee` : reset de `score_vocal_jour`/`ticks_vocaux_jour` + nouveaux accumulateurs de télémétrie (`score_formants_jour`, `score_spectral_jour`, `dopamine_poids_*_jour`) + cache du canal spectral (`_tick_dernier_spectral`). `AGI_Naulthene.rever` : nouveau paramètre `coeff_jepa_audio`, reconstruit le batch audio seulement si tous les souvenirs tirés en ont un. `traiter_tick`/`_traiter_tick_vocal_isole` gagnent `mfcc_references` (par défaut `None`, inerte). `NB_PALIERS_VOCAUX` 14→19. Nouvelles constantes/helpers du Cursus de la Parole (`TICKS_PAR_JOUR_PAROLE=800`, `BORNES_PHASES_PAROLE=(300,600)`, `taux_guidage_parole`, `phase_parole`). Nom de run W&B du mode standalone mis à jour. |
| `src/naulthene/audio/hemisphere_audio.py` | `SynthetiseurFormants._resonateur` vectorisé via `scipy.signal.lfilter` (repli sur la boucle Python si scipy absent). `extraire_mfcc` gagne `standardisation="echantillon"` (CMVN par échantillon, remplace les constantes `MFCC_MOYENNE_EMPIRIQUE`/`MFCC_ECART_TYPE_EMPIRIQUE` calibrées sur `say` ; mode `"constantes"` conservé pour A/B). Nouvelle section « Analyse acoustique de références réelles » : `estimer_formants_lpc` (LPC de Burg, pré-accentuation, filtrage par bande passante, clamp aux bornes physiques du synthétiseur), `estimer_formants_agrege` (médiane inter-prises), `distance_spectrale`/`recompense_spectrale` (cosinus sur MFCC), `recompense_vocale_mixte` (score pondéré 0.6/0.4, repli exact sur `recompense_formants` sans banque). |
| `src/naulthene/audio/lecons_vocales.py` | `CacheReferencesVocales` lit d'abord `voix/<mot>/<mot>_NN.wav` (nouvelle `_references_depuis_banque`), replie sur `say` si aucune prise — interface `obtenir_pour_palier` inchangée. Nouveau `obtenir_mfcc_prises` (MFCC individuels, pour le canal spectral) et `resume_banque()`. `_voyelle_dominante` (nouveau, dépliage NFD) corrige le bug `"clé"` ; `_mot_cible_du_palier` mis à jour. |
| `src/naulthene/audio/professeur_gemma.py` | `CURRICULUM_VOCAL` étendu 14→19 paliers (15 mur, 16 clé, 17 but, 18 vide, 19 "porte jaune"). |
| `src/naulthene/instruments/enregistreur_voix.py` (nouveau) | CLI d'enregistrement de la banque vocale : capture micro + recadrage de silence (`librosa.effects.trim`) + relecture/validation interactive, convention `voix/<mot>/<mot>_NN.wav`, jamais d'écrasement d'une prise existante. Ne modifie jamais un `.brain`. |
| `src/naulthene/salles_de_classe/cursus_parole.py` (nouveau) | Troisième cursus développemental, calqué sur `cursus_bebe.py`/`cursus_developpemental.py` : 900 jours × 800 ticks, 3 phases (Imprégnation/Autonomie guidée/Émancipation), `_cible_synesthesique` relie `LecteurCaseFrontale` au curriculum vocal, `_perception_du_tick_parole` orchestre mode/guidage par phase. Cerveau dédié `naulthene_parole.brain`. |
| `.gitignore` | Nouvelle entrée `voix/*` (+ `!voix/.gitkeep` tracké) — banque vocale personnelle, données binaires lourdes, même raisonnement que `brains/*.brain`. |

**Changements de dynamique à surveiller sur les runs existants** (non-régression structurelle garantie par ailleurs — tous les nouveaux paramètres ont une valeur par défaut inerte) :
- **Dopamine vocale −30% en mode `vocal_isole`** : `POIDS_DOPAMINE_VOCAL=0.7` réduit le choc dopaminergique de tous les ticks vocaux isolés des cursus existants (`cursus_developpemental.py`, `cursus_bebe.py`) par rapport au comportement pré-v27.0 (poids plein) — effet en cascade possible sur `plasticite_base` → pourcentage de rêve → neurogenèse. En mode `"minigrid"` avec `poids_vocal=0` (aucune leçon active), le comportement reste identique au bit près.
- **Seuils de promotion vocale abaissés** : `NB_PALIERS_VOCAUX` 14→19 abaisse mécaniquement le seuil de chaque palier intermédiaire déjà atteint (interpolation sur une plage plus longue) — assouplissement, aucun risque de blocage.
- **Cascade de promotions possible sur les `.brain` anciens** : le correctif de reset quotidien débloque d'un coup une moyenne qui était figée depuis la naissance du cerveau — comportement correct (rattrapage d'une dette), pas un bug.

**Validation** : non-régression numérique de la vectorisation du synthétiseur (`np.allclose` boucle Python vs `lfilter`, écart max nul) ; estimateur LPC testé sur les 5 voyelles théoriques via `say` (F1/F2 dans la bonne topologie relative, garde-fou du percentile d'énergie de trame validé empiriquement contre l'inversion F1/F2 sur les trames d'attaque/chute) ; invariants de `recompense_vocale_mixte` vérifiés (rétrocompatibilité stricte sans banque, bornes [0,1] avec banque) ; `LecteurCaseFrontale` testé sur 300 pas aléatoires réels (`MiniGrid-DoorKey-6x6-v0`) — mur/porte/clé/vide et syntagmes couleur+objet tous détectés, aucune `AssertionError` de `Grid.get` ; les 19 paliers du curriculum vérifiés individuellement résolubles vers une cible de voyelle valide ; `rever()` testé avec et sans audio dans le lot (rétrocompatibilité + nouveau chemin, tous deux sans erreur) ; run réel bout-en-bout d'1 jour de `cursus_parole.py` sur cerveau neuf (préchauffage, 800 ticks, dream, cristallisation, sans crash) ; les 3 phases pédagogiques testées individuellement en forçant `etat.jour` (imprégnation, autonomie guidée avec bascule matin/après-midi synesthésie/curriculum, émancipation avec syntagmes) ; non-régression confirmée sur `cursus_developpemental.py` (2 jours sur le cerveau existant `naulthene_cursus.brain`, resurrection/palier/sursaut/rêve/cristallisation fonctionnels, aucune exception) ; les 4 points de synchronisation des couches `NaultheneLinearSynaptique` vérifiés intacts (`fortifier_synapses`/`cycle_sommeil_global`/`declencher_neurogenese`) ; tous les modules consommateurs (`cursus_bebe.py`, `cursus_developpemental.py`, `lancer_arene.py`, `client_professeur.py`, `daemon_cerveau.py`) importés sans erreur.

---

## [26.0-experimental] - 2026-07-27

### L'Arène augmentée — mini-IRM en pygame et télémétrie complète en direct

| Type | Details |
|------|---------|
| **Commit** | `47bfa2e` |
| **Catégorie** | feat |
| **Impact** | Fonctionnel (instrumentation d'observation) |

**L'Arène (`lancer_arene.py`/`arene_visuelle.py`) fusionne désormais en une seule fenêtre pygame ce qui vivait jusqu'ici dans deux outils séparés : voir l'agent bouger dans MiniGrid ET observer les activations de son cerveau, sur le MÊME agent en mémoire (pas un second `charger_ou_naitre()` qui aurait divergé). Une bande "mini-IRM" sous l'image affiche en direct les barres d'activation du bus latent aux 3 étapes du tronc cérébral (vision/mémoire/pensée) — le pendant temps-réel du panneau 1 de `irm_cerveau.py`, mais rendu avec des primitives `pygame.draw` plutôt qu'en matplotlib (mélanger les deux frameworks GUI dans le même thread est fragile sur macOS, SDL et le backend GUI de matplotlib se disputant la boucle d'événements native Cocoa). Le panneau de télémétrie de droite est étendu à la parité complète avec le bilan de nuit console (13 lignes : état mental, plasticité, jalons DoorKey, abnégation, mode décision, portes, potentiomètre, curiosité JEPA, viscéral, métabolisme, mémoire épisodique, erreur JEPA/thermostat) — les trois métriques qui n'existent QUE après une vraie nuit (plasticité base, souvenirs rejoués, thermostat de neurogenèse) sont remplacées par des proxys recalculés en continu avec la même formule, explicitement marqués comme estimés plutôt que présentés comme un vrai bilan nocturne. Un bandeau d'événement temporaire signale un changement de palier DoorKey observé en direct ; une note affichée au démarrage documente explicitement qu'une promotion de NIVEAU MiniGrid ne peut structurellement jamais se produire dans l'Arène (décidée uniquement par `executer_nuit`, jamais appelée ici — garantie de non-altération inchangée).**

| Fichier modifié | Changement |
|-----------------|------------|
| `src/naulthene/instruments/arene_visuelle.py` | Fenêtre élargie (1032×652) ; nouvelle bande mini-IRM (`_dessiner_panneau_bus`) ; panneau de télémétrie réécrit pour les 13 lignes de parité avec le bilan de nuit ; nouveau bandeau d'événement (`_dessiner_bandeau_evenement`) ; `dessiner_frame` accepte `activations`/`evenement` optionnels |
| `src/naulthene/instruments/lancer_arene.py` | Recalcul en lecture seule du tronc cérébral (`_tronc_cerebral` sous `torch.no_grad()`) avant chaque `traiter_tick`, pour alimenter le mini-IRM sur l'observation du tick courant ; `_construire_telemetrie` étendu avec les proxys continus (plasticité base, erreur JEPA/récompense moyenne, thermostat simplifié) ; détection de changement de palier DoorKey par diff entre deux ticks pour déclencher le bandeau |

**Validation** : script de vérification manuel (pas de suite de tests automatisée) — panneau testé en headless (`SDL_VIDEODRIVER=dummy`) sur toutes les combinaisons de clés manquantes/DoorKey actif ou non/bandeau présent ou non, sans crash ; run réel bout-en-bout sur `brains/naulthene_bb.brain` (niveau Doctorat) confirmant des valeurs de télémétrie cohérentes tick par tick ; test synthétique forçant un changement de palier DoorKey sur `brains/naulthene_cursus.brain` confirmant le déclenchement et l'extinction du bandeau ; aucune altération constatée sur les fichiers `.brain` sur disque après les runs de test.

---

## [26.0-experimental] - 2026-07-27

### Cristallisation Souple — protection ciblée des synapses matures contre l'érosion nocturne (falaise sigmoïde)

| Type | Details |
|------|---------|
| **Commit** | N/A — `src/naulthene/cerveau/noyau.py` est gitignored (terrain d'essai expérimental), aucun commit ne le modifie |
| **Catégorie** | feat (mécanique expérimentale) |
| **Impact** | Fonctionnel (plasticité structurelle) — `agi_local_test.py`/`noyau.py` uniquement |

**Implémente le chantier §A.5 du plan v26.0 « Le Parent remplace le Programme » ([docs/ameliorations/AMELIORATION_V1.md](../ameliorations/AMELIORATION_V1.md)) : les synapses `NaultheneLinearSynaptique` sollicitées fortement et régulièrement sur plusieurs nuits deviennent quasi indestructibles à l'érosion nocturne, sans jamais geler leur apprentissage diurne. Une seconde trace `myeline_cumul` accumule la myélinisation consolidée nuit après nuit (même patron de relaxation exponentielle que partout dans le projet, `ALPHA_CRISTAL = 0.95`) ; au-delà de `SEUIL_CRISTAL = 0.80`, la synapse devient `cristallisee` — un cliquet à sens unique, jamais réversible. Correctif appliqué en cours d'implémentation : le plancher d'érosion initialement prévu comme une constante rigide (`MYELINE_MIN_CRISTAL = 0.50`, tout-ou-rien) a été remplacé par une falaise continue — une sigmoïde de `myeline_cumul` centrée sur le seuil (`K_RAIDEUR_CRISTAL = 10.0`) — plus fidèle au principe du projet de régulation dynamique sans règle en dur : une synapse cristallisée voit son érosion tendre vers zéro à mesure qu'elle s'éloigne du seuil, tandis qu'une synapse jamais cristallisée s'érode normalement et finit élaguée en temps fini (zéro synapse fantôme).**

| Fichier modifié | Changement |
|-----------------|------------|
| `src/naulthene/cerveau/noyau.py` | `NaultheneLinearSynaptique.__init__` : 2 nouveaux buffers (`myeline_cumul`, `cristallisee`). `cycle_sommeil()` : nouvelle Étape 3.5 (accumulation inter-nuits + cliquet de cristallisation) et érosion (Étape 3) plancher-protégée par une falaise sigmoïde plutôt qu'un plancher rigide. `agrandir()` : les 2 nouveaux buffers suivent le même triptyque resize/copie-par-segment que `myeline_M`/`trace_activation` (nouvelles dimensions nées à `0`/`False`). 3 nouvelles constantes module (`ALPHA_CRISTAL`, `SEUIL_CRISTAL`, `K_RAIDEUR_CRISTAL`). `forward()` et `fortification_dopaminergique()` inchangées — garantit par construction la règle dissymétrique (le gradient diurne sur `annexe_weight` reste identique, cristallisée ou non). |
| `docs/ameliorations/AMELIORATION_V1.md` | §A.5 mis à jour pour refléter la falaise sigmoïde implémentée (remplace le plancher rigide de la proposition initiale) ; glossaire §G : `MYELINE_MIN_CRISTAL` remplacé par `K_RAIDEUR_CRISTAL = 10.0` |
| `docs/fonctionnement/explications_readme.md` | Nouvelle section §8.5 « Cristallisation Souple » (formules exactes, extrait de code, règle dissymétrique) ; table §12 et glossaire §13 mis à jour (v26.0, `ALPHA_CRISTAL`/`SEUIL_CRISTAL`/`K_RAIDEUR_CRISTAL`) |
| `readme_fr.md` | Nouvelle entrée « Nouveautés v26.0 (expérimental, §A.5 seul) » en tête du Journal des Mises à Jour + entrée table des matières `3x` |

**Validation** : script de vérification manuel isolé (pas de suite de tests automatisée dans ce projet) — cristallisation asymétrique confirmée (la synapse sollicitée bascule `cristallisee=True` vers la nuit 40 sur 80 simulées, l'inactive reste `False`), falaise sigmoïde confirmée (une synapse cristallisée résiste nettement mieux à l'érosion qu'une synapse juste sous le seuil, 0.987 vs 0.950 de rétention sur un cycle), zéro synapse fantôme confirmé (une synapse jamais cristallisée est élaguée en 89 nuits, temps fini), règle dissymétrique confirmée (`backward()` produit un gradient non nul sur `annexe_weight` même aux positions cristallisées), `agrandir()` confirmé préservant l'historique sans hallucination de cristallisation sur les nouvelles dimensions.

---

## [25.0-docs] - 2026-07-26

### Réorganisation en package Python + renforcement de l'attribution (NOTICE)

| Type | Details |
|------|---------|
| **Commit** | `c5d23dc` |
| **Catégorie** | refactor + docs |
| **Impact** | Fonctionnel (imports, arborescence) + Documentation/Légal |

**Le projet passe d'un ensemble de scripts plats à la racine à un vrai package Python `src/naulthene/`, organisé en sous-modules thématiques suivant le vocabulaire du projet : `cerveau/` (noyau.py ex-`agi_local_test.py`, colab.py ex-`agi_google_colab.py`, persistance.py), `salles_de_classe/` (cursus_bebe.py, cursus_developpemental.py), `cuve/` (daemon_cerveau.py, client_corps.py, client_professeur.py), `audio/` (hemisphere_audio.py, lecons_vocales.py, professeur_gemma.py), `instruments/` (arene_visuelle.py, lancer_arene.py, irm_cerveau.py). Tous les imports inter-modules sont passés en chemins de package absolus (`from naulthene.cerveau.noyau import ...`). Les cerveaux cristallisés (`*.brain`) sont rangés dans `brains/`, la documentation complémentaire dans `docs/` — `readme_fr.md` reste à la racine (aux côtés de `LICENSE`/`NOTICE`/`CLAUDE.md`) pour rester immédiatement visible. En parallèle, le fichier `NOTICE` est renforcé : au-delà de la simple demande d'attribution, il précise explicitement (en s'appuyant sur la Section 4(d) de la licence Apache 2.0) qu'Adrien Nault doit être crédité comme auteur original du concept et de l'architecture Naulthène AGI dans toute redistribution, usage public, publication ou œuvre dérivée — pas seulement dans le code source.**

| Fichier modifié | Changement |
|-----------------|------------|
| `src/naulthene/**/*.py` (tous) | Déplacement en package (`git mv`), réécriture de tous les imports locaux en chemins de package absolus, chemins `.brain` par défaut pointant vers `brains/` |
| `.gitignore` | Chemins mis à jour vers `brains/*.brain` et `src/naulthene/cerveau/noyau.py` |
| `readme_fr.md` | Reste à la racine du dépôt ; formulation d'attribution durcie en tête de document |
| `docs/fonctionnement/CHANGELOG.md`, `docs/fonctionnement/explications_readme.md`, `docs/fonctionnement/LANCEMENT.md`, `docs/ameliorations/AMELIORATION_V1.md` | Liens relatifs corrigés vers la nouvelle arborescence (`../readme.md`, `../CLAUDE.md`, `../LICENSE`, `../NOTICE`) |
| `CLAUDE.md` | Section Architecture réécrite pour décrire le package ; commandes de lancement mises à jour (`PYTHONPATH=src python -m naulthene....`) |
| `NOTICE` | Attribution renforcée : exigence explicite de citer Adrien Nault comme auteur du concept/architecture original, dans tout usage public (pas seulement redistribution de code), avec référence à la Section 4(d) de la licence |
| `LICENSE` | Texte légal Apache 2.0 inchangé (Sections 1-9) ; ajout d'un renvoi explicite vers `NOTICE` en fin de fichier |

**Validation** : les 12 modules du package s'importent sans erreur (`python -c "import naulthene...."` pour chaque sous-module) ; run réel d'1 jour de `cursus_bebe` exécuté de bout en bout, confirmant la résolution correcte de `brains/naulthene_bb.brain` en lecture et en écriture (reprise du jour 1440 → 1441 sans perte de progression) ; `git status` confirme la préservation de l'historique (renommages `R`/`RM`, pas de suppression/ajout).

---

## [25.0-experimental] - 2026-07-24

### Le Cerveau Bébé Développemental — 4 ans, masquage de récompense externe & Module Parent (expérimental, non porté sur le script de référence)

| Type | Details |
|------|---------|
| **Commit** | `c5d23dc` |
| **Catégorie** | feat (nouvelle mécanique cognitive majeure) |
| **Impact** | Fonctionnel (local uniquement) |

**Nouveau paradigme développemental bio-inspiré (Piaget / Dehaene, décision utilisateur) qui pousse plus loin le Cursus Développemental par Ères (v23.0) : au lieu du RL classique (qui force l'agent à "tricher" pour maximiser une récompense), le bébé traverse 4 ans (1440 jours × 3600 ticks) découpés en 5 phases d'âge, avec la récompense externe VERROUILLÉE à zéro pendant les 8 premiers mois (jour < 240) — l'agent "n'a aucune idée s'il fait bien ou mal", seuls le JEPA, l'homéostasie et la curiosité pilotent l'apprentissage — puis un Module "Parent" qui réintroduit un feedback social vocal déterministe ("Oui !"/"Non !"). Le cerveau vit dans un fichier dédié `naulthene_bb.brain`, distinct de `naulthene_cursus.brain` (Cursus par Ères) et `naulthene_v21.brain` (Cuve/daemon) — les trois écosystèmes ne partagent jamais le même cerveau. Le Cursus par Ères existant reste intact et utilisable tel quel.**

| Fichier modifié | Changement |
|-----------------|------------|
| `agi_local_test.py` | Ajout des constantes/helpers du paradigme (`TICKS_PAR_JOUR_BEBE=3600`, `TICKS_MATIN_BEBE=1800`, `JOURS_TOTAUX_BEBE=1440`, `BORNES_PHASES_BEBE=(90,180,360,720)`, `JOUR_FIN_MASQUAGE_EXTERNE=240`, `PLAFOND_REVE_PAR_PHASE=(0.70,0.60,0.50,0.40,0.35)`, `SEUIL_PARENT_OUI=0.45`, `SEUIL_PARENT_NON=0.15`, `TAUX_CORTISOL_PARENT=0.5`, helpers `phase_bebe()`/`plafond_reve_bebe()`). `traiter_tick()` gagne deux paramètres optionnels **par défaut inertes** : `masquer_recompense_externe=False` (gèle `recompense_env` à 0.0 juste après `env.step`, neutralisant à la fois sa contribution à `recompense_interne` ET à `poids_evenement` — donc plus de choc dopaminergique "victoire", plus de `victoire_aujourdhui`, plus de promotion de niveau MiniGrid tant que le masquage est actif) et `parent_actif=False` (déclenche le nouveau Module Parent). `_traiter_tick_vocal_isole()` gagne le même `parent_actif`. Nouveau helper `_appliquer_feedback_parent_vocal()` : "Oui !" (score de formants ≥ `SEUIL_PARENT_OUI`) renforce le choc dopaminergique déjà existant ; "Non !" (score < `SEUIL_PARENT_NON`) pousse activement la dopamine vers `DOPAMINE_MIN` via un nouveau canal "cortisol" (`TAUX_CORTISOL_PARENT`), toujours reclippé dans `[DOPAMINE_MIN, DOPAMINE_MAX]`. Un second canal "Oui !" se déclenche quand une ressource bio est atteinte pendant une quête de survie active (`poids_ressource_bio > 0`). Nouveau compteur de journée `feedback_parent_jour` (net Oui − Non), loggé sur W&B. `executer_nuit()` gagne `plafond_reve=None` : quand fourni, remplace `PLAGE_REVE_MAX` dans le calcul de `pourcentage_reve` — le pourcentage rejoué reste émergent (plasticité × richesse), seul son plafond suit le "% Dodo" de la phase d'âge (aucune taille de batch fixe réintroduite). Normalisations `erreur_moyenne`/`rec_moy`/`effort_moyen_jour` corrigées pour utiliser le nombre RÉEL de ticks de la journée (`len(etat.jepa_losses)`) plutôt que la constante globale `ticks_par_jour` (400) — nécessaire car `cursus_bebe.py` tourne sur 3600 ticks/jour, sans effet sur le Cursus par Ères/mode standalone (résultat identique dans ce cas). `NB_PALIERS_VOCAUX` passe de 11 à 14 (paliers "porte" + combinatoire ajoutés, voir ci-dessous) |
| `professeur_gemma.py` | `CURRICULUM_VOCAL` étendu de 11 à 14 paliers : palier 12 (mot "porte"), paliers 13-14 (combinatoire minimale "ouvre porte" / "prends clé") — couvre la roadmap "mots papa/maman/porte" puis "combinatoire Action+Objet" du concept. Chaque nouveau mot est géré automatiquement par `CacheReferencesVocales` (référence `say`) ; sa voyelle dominante ("porte"→"o", "ouvre"→"o", "prends"→"e") est déjà une clé connue de `hemisphere_audio.VOYELLES_CIBLES` via le fallback existant de `_mot_cible_du_palier` — aucune modification requise dans `hemisphere_audio.py` |
| `cursus_bebe.py` (nouveau) | Orchestrateur calqué sur `cursus_developpemental.py` : boucle sur `JOURS_TOTAUX_BEBE` (1440) jours × `TICKS_PAR_JOUR_BEBE` (3600) ticks, `_perception_du_tick_bebe()` mappe les 5 phases d'âge au curriculum vocal et au mode de perception (vocal isolé pour les phases 0-1, multimodal matin dès la phase 2, verbalisation de l'action aux phases 3-4 — même principe que l'Ère Intégration du Cursus par Ères), câble `masquer_recompense_externe`/`parent_actif` sur `JOUR_FIN_MASQUAGE_EXTERNE` et `plafond_reve_bebe(jour)` sur `executer_nuit`. Réutilise le même garde-fou "École de Rattrapage Vocal" (compteur de session local, pas `etat.jour` cumulatif) et le même mécanisme de promotion vocale 2+2 succès que le Cursus par Ères. Persistance dédiée : `PersistanceAnatomique(fichier="naulthene_bb.brain")`, sauvegarde après chaque nuit, reprise automatique, sauvegarde d'urgence sur `KeyboardInterrupt` |

**Validation** : non-régression structurelle garantie — les trois nouveaux paramètres (`masquer_recompense_externe`, `parent_actif`, `plafond_reve`) ont tous une valeur par défaut inerte, et tous les appelants existants (`__main__` standalone, `cursus_developpemental.py`, `lancer_arene.py`, `daemon_cerveau.py`) appellent `traiter_tick`/`executer_nuit` sans ces arguments — vérifié par grep sur tous les call sites. Testé bout-en-bout : (1) `cursus_bebe.py` exécuté sur cerveau neuf (3 jours, ticks réduits pour la vitesse du test) sans crash, phases/persistance/rêve/neurogenèse fonctionnels ; (2) masquage vérifié directement — un `recompense_env` forcé à 1.0 avec `masquer_recompense_externe=True` laisse `victoire_aujourdhui=False` et n'entre pas dans `recompense_interne`, alors que `masquer_recompense_externe=False` sur le même signal déclenche bien la victoire et la contribution ; (3) plafond de rêve vérifié — `plasticite_base` forcée à 1.0 (qui pousserait normalement `pourcentage_reve` vers 0.60) reste bornée à `plafond_reve=0.35` passé en paramètre ; (4) Module Parent testé en isolation — score ≥ 0.45 incrémente `feedback_parent_jour` sans toucher la dopamine (le choc positif est déjà géré par l'appelant), score < 0.15 la décrémente et pousse la dopamine vers `DOPAMINE_MIN` en respectant le clip, score intermédiaire neutre ; `parent_actif=False` laisse `feedback_parent_jour` totalement inchangé ; (5) non-régression confirmée sur `cursus_developpemental.py` (2 jours, inchangé, exécution normale).

---

## [24.0-fix5-experimental] - 2026-07-23

### L'Arène injecte enfin une cible vocale — fin du "(silence)" systématique (expérimental, non porté sur le script de référence)

| Type | Details |
|------|---------|
| **Commit** | N/A — vit dans `lancer_arene.py` |
| **Catégorie** | fix (bug bloquant, signalé par l'utilisateur avec une hypothèse de seuil à corriger) |
| **Impact** | Fonctionnel (local uniquement) |

**L'hypothèse initiale (un seuil de décodage type `if score_similarite < 0.55` masquant les scores 0.45-0.55 observés dans le cursus) ne correspondait pas au code réel : aucun seuil de ce type n'existe. Le vrai bug, plus simple : `lancer_arene.py` appelait `traiter_tick(etat)` SANS jamais passer `obs_auditive`/`formants_cibles` — `score_vocal` restait donc toujours `None` par construction, quel que soit le niveau réel de l'agent. L'Arène affichait "Palier vocal : Mot 'maman'" dans le panneau tout en ne présentant jamais ce mot à répéter au cerveau.**

| Fichier modifié | Changement |
|-----------------|------------|
| `lancer_arene.py` | Instancie `lecons_vocales.CacheReferencesVocales` (même mécanisme que `cursus_developpemental.py`) et injecte à CHAQUE tick le MFCC + les formants cibles du `etat.palier_vocal` courant dans `traiter_tick`. Le score est ensuite calculé via `hemisphere_audio.recompense_formants` sur les formants réellement produits, au lieu de rester `None` |

**Validation** : testé avec un `.brain` forcé au palier 11 ("maman") — confirmé que `score_vocal` n'est plus jamais `None` sur 10 ticks consécutifs (il se calcule à chaque fois, la valeur numérique dépendant ensuite du niveau réel de l'agent testé).

---

## [24.0-fix4-experimental] - 2026-07-23

### L'exclusion d'integrateur_bio devient conditionnelle à la forme réelle (expérimental, non porté sur le script de référence)

| Type | Details |
|------|---------|
| **Commit** | N/A — vit dans `persistance.py` |
| **Catégorie** | fix (bug bloquant, signalé par l'utilisateur) |
| **Impact** | Critique (local uniquement) — expliquait le silence de l'Arène |

**Le filtre `integrateur_bio` introduit en v22.1 pour gérer le changement DIM_VECTEUR_BIO 8→16 était INCONDITIONNEL : il testait seulement `startswith('integrateur_bio.')`, sans jamais comparer la forme réelle du checkpoint à la forme attendue. Conséquence : tout `.brain` sauvegardé depuis la v22.1 (donc avec `integrateur_bio` déjà à la bonne taille et correctement appris) se faisait quand même amputer de cette couche à CHAQUE rechargement — remplacée par des poids aléatoires. Comme `integrateur_bio` réinjecte justement la quête vocale vers `tete_vocale`, cette réinitialisation systématique produisait une bouche silencieuse dans l'Arène (amplitude prédite sous le seuil d'audibilité en mode `eval()`).**

| Fichier modifié | Changement |
|-----------------|------------|
| `persistance.py` | `charger_ou_naitre` compare désormais la shape réelle de `checkpoint['state_dict']['integrateur_bio.base_weight']` à la shape attendue par l'agent fraîchement recréé (`agent.integrateur_bio.base_weight.shape`). L'exclusion ne se déclenche que si les deux diffèrent (vieux `.brain` pré-v22.1) ; un checkpoint déjà à la bonne forme charge `integrateur_bio` intégralement, sans perte |

**Validation** : deux cas testés directement. (1) Un `.brain` simulé à l'ancienne forme (8 dims, `integrateur_bio` en `(16,24)`) déclenche toujours correctement l'exclusion, avec un message affichant la comparaison exacte des formes. (2) Un `.brain` à la forme actuelle (16 dims) avec des poids `integrateur_bio` marqués (valeur repère `0.777`) est rechargé avec ces poids **strictement préservés** — aucune exclusion, aucune réinitialisation. C'est ce second cas qui corrige le silence observé dans l'Arène sur `naulthene_cursus.brain`.

---

## [24.0-fix3-experimental] - 2026-07-23

### Correction du compteur du garde-fou vocal (expérimental, non porté sur le script de référence)

| Type | Details |
|------|---------|
| **Commit** | N/A — vit dans `cursus_developpemental.py` |
| **Catégorie** | fix (bug bloquant sur le garde-fou introduit en fix2) |
| **Impact** | Fonctionnel (local uniquement) |

**Le garde-fou de l'École de Rattrapage (v24.0-fix2) comparait `etat.jour` — cumulatif depuis la naissance du cerveau — au seuil de 100 jours. Sur un cerveau qui avait déjà vécu 970 jours AVANT le correctif de seuil (v24.0-fix1), la reprise après application du fix1 s'est vue couper la parole dès le premier jour de la nouvelle tentative (970 ≥ 100), sans laisser au nouveau seuil la moindre chance de prouver qu'il fonctionne réellement.**

| Fichier modifié | Changement |
|-----------------|------------|
| `cursus_developpemental.py` | Nouveau compteur local `jours_ecoules_session` (incrémenté à chaque itération de `lancer_cursus`, remis à zéro à chaque nouveau lancement du script) — le garde-fou compare désormais ce compteur au seuil, pas `etat.jour`. Une reprise sur un vieux cerveau obtient une vraie fenêtre de `JOURS_MAX_SANS_PREMIERE_LETTRE` jours depuis CETTE tentative, indépendamment de son passé |

**Validation** : testé avec un cerveau simulé à `etat.jour=970`/`palier_vocal=1` (reproduisant exactement le cas réel signalé) — un run de 5 jours (`jours_totaux=5`, sous le seuil de 100) se termine désormais normalement au lieu de déclencher le garde-fou dès le premier jour.

---

## [24.0-fix2-experimental] - 2026-07-23

### Garde-fou de l'École de Rattrapage Vocal (expérimental, non porté sur le script de référence)

| Type | Details |
|------|---------|
| **Commit** | N/A — vit dans `cursus_developpemental.py` |
| **Catégorie** | fix (garde-fou, détection précoce d'un blocage) |
| **Impact** | Fonctionnel (local uniquement) |

**Le run de 1000 jours qui a révélé le blocage du seuil de promotion (v24.0-fix1) a tourné intégralement à vide côté vocal sans qu'aucun signal ne le signale — il a fallu inspecter le `.brain` à la main après coup. Ajout d'un garde-fou : si après `JOURS_MAX_SANS_PREMIERE_LETTRE` (100) jours subjectifs cumulés le palier vocal n'a jamais quitté le palier 1 (aucune voyelle validée), le cursus s'arrête proprement — sauvegarde incluse — au lieu de tourner jusqu'au bout des jours demandés.**

| Fichier modifié | Changement |
|-----------------|------------|
| `cursus_developpemental.py` | Nouvelle constante `JOURS_MAX_SANS_PREMIERE_LETTRE = 100`. Dans `lancer_cursus`, après chaque sauvegarde nocturne, vérifie `etat.palier_vocal == 1 and etat.jour >= JOURS_MAX_SANS_PREMIERE_LETTRE` — si vrai, arrête la boucle (`break`) avec un message dédié. Ne se déclenche qu'une fois avant la toute première promotion (`GestionnaireCursusAbnegation` n'a aucun mécanisme de rétrogradation, donc `palier_vocal` ne peut jamais redescendre à 1 une fois monté) |

**Validation** : testé avec un seuil de promotion vocale rendu volontairement inatteignable (99.0) — arrêt confirmé exactement au jour du seuil (testé à 5 jours), `.brain` bien sauvegardé avant l'arrêt. Testé aussi le cas négatif (moins de jours que le seuil, promotion possible) — aucun faux déclenchement, le cursus se termine normalement.

---

## [24.0-fix1-experimental] - 2026-07-23

### École de Rattrapage Vocal — débloquer l'apprentissage vocal (expérimental, non porté sur le script de référence)

| Type | Details |
|------|---------|
| **Commit** | N/A — vit dans `agi_local_test.py` (seuil progressif + atténuation d'érosion) et `cursus_developpemental.py` (appel du nouveau seuil) |
| **Catégorie** | fix (critique — bloquait tout apprentissage vocal du Cursus) |
| **Impact** | Critique (local uniquement) |

**Diagnostic sur un vrai run de 1000 jours (`naulthene_cursus.brain`) : avec le seuil de promotion vocale fixe introduit en v23.0 (0.5), `gestionnaire_cursus_vocal_succes_courant` est resté à 0 du premier au dernier jour — aucune promotion vocale en 1000 jours, et `porte_auditive.base_weight` a fini à norme EXACTEMENT ZÉRO (l'oreille n'a strictement rien appris). Cause racine identifiée : sans un premier succès pour amorcer la myélinisation, le peu de gradient accumulé par jour se fait entièrement raser par l'érosion nocturne (`cycle_sommeil`) avant d'avoir pu s'accumuler — un cercle vicieux qui ne se débloque jamais tout seul.**

| Fichier modifié | Changement |
|-----------------|------------|
| `agi_local_test.py` | Remplace la constante `SEUIL_JOUR_VOCAL_REUSSI` (0.5 fixe) par `seuil_jour_vocal_reussi(palier_vocal)`, une interpolation progressive de `SEUIL_VOCAL_PALIER_DEBUTANT=0.15` (palier 1) à `SEUIL_VOCAL_PALIER_AVANCE=0.45` (palier 11) — jamais 0.5, pour ne jamais retomber dans le blocage diagnostiqué. Second volet : `AGI_Naulthene.cycle_sommeil_global` gagne un paramètre `attenuation_erosion_audio` appliqué uniquement à `porte_auditive`/`tete_vocale`/`generateur_attente_audio`, réduit à 10% (`ATTENUATION_EROSION_AUDIO_DEBUT`) tant que `palier_vocal <= PALIER_VOCAL_FIN_PROTECTION` (3) — laisse au tout premier apprentissage le temps de survivre à plusieurs nuits avant d'être soumis à l'érosion standard |
| `cursus_developpemental.py` | `_promouvoir_palier_vocal_si_merite` utilise le nouveau seuil progressif au lieu de la constante fixe |

**Validation** : non-régression MiniGrid confirmée byte-identique (le fix n'affecte le comportement que via `palier_vocal`/`attenuation_erosion_audio`, neutres par défaut). Test dédié bout-en-bout sur cerveau neuf (seed fixe, curriculum réel via `professeur_gemma.choisir_lecon` + `_promouvoir_palier_vocal_si_merite`) : **3 promotions vocales obtenues en 60 jours** (palier 1→2→3, voyelles a→a→e), score de formants monté jusqu'à 0.53 — alors que le seuil fixe précédent n'avait produit AUCUNE promotion en 1000 jours sur un vrai run.

---

## [24.0-experimental] - 2026-07-23

### L'Arène & Démo Live — observer un cerveau entraîné en action (expérimental, non porté sur le script de référence)

| Type | Details |
|------|---------|
| **Commit** | N/A — vit dans `agi_local_test.py` (`creer_env` render_mode), `persistance.py`, `cursus_developpemental.py` (modifiés) + `arene_visuelle.py`, `lancer_arene.py` (nouveaux fichiers) |
| **Catégorie** | feat (Phase 2 du plan à 3 phases : Cursus → Arène → boucle méta) |
| **Impact** | Fonctionnel (local uniquement) |

**Ajoute une fenêtre graphique temps réel (image MiniGrid + panneau de télémétrie composés dans une seule fenêtre pygame) et le son joué en direct, pour observer un agent entraîné en action — sans jamais l'altérer. Préalable indispensable résolu au passage : le Cursus Développemental (v23.0) ne sauvegardait jamais son état ; il persiste désormais chaque nuit dans un fichier dédié, avec reprise automatique d'un run interrompu.**

| Fichier modifié | Changement |
|-----------------|------------|
| `persistance.py` | Ajout de `palier_vocal` et de l'état de `gestionnaire_cursus_vocal` (instance séparée de celle de DoorKey) au checkpoint sauvegardé/restauré — absents jusqu'ici, une reprise perdait la progression vocale. Rétrocompatible (`.get(..., défaut)`) pour les vieux `.brain` |
| `cursus_developpemental.py` | `lancer_cursus` charge désormais un cerveau existant via `PersistanceAnatomique` (fichier dédié `naulthene_cursus.brain`, distinct de `naulthene_v21.brain` de la Cuve) au lieu de toujours faire naître un cerveau neuf, et sauvegarde après CHAQUE nuit. `try/except KeyboardInterrupt` avec sauvegarde d'urgence — un cursus interrompu ne perd au plus que la journée en cours |
| `agi_local_test.py` | `creer_env` gagne un paramètre optionnel `render_mode=None` (rétrocompatible, tous les appels existants inchangés), passé à `gym.make()` — permet `render_mode="rgb_array"` pour récupérer une image numpy de la grille |
| `arene_visuelle.py` (nouveau) | `FenetreArene` : rendu pygame pur (aucune dépendance au réseau de neurones) — image MiniGrid à gauche, panneau de télémétrie à droite (jauges dopamine/satiété/hydratation/stimulation, curriculum MiniGrid + DoorKey, ère + curriculum vocal, score de formants). Gère aussi `pygame.QUIT` pour une fermeture par clic sur la croix |
| `lancer_arene.py` (nouveau) | Orchestrateur : charge un `.brain`, recrée l'env avec rendu activé, boucle `traiter_tick` (mode `"minigrid"` normal) en lisant `EtatCognitif` directement pour la télémétrie (`traiter_tick` ne retourne que peu d'infos, mais `EtatCognitif` est accessible sans encapsulation). `agent.eval()` après le chargement, `executer_nuit`/`apprendre_journee` jamais appelés — garantie explicite de non-altération du cerveau observé |

**Validation** : non-régression confirmée (`creer_env` avec `render_mode=None` par défaut, logs byte-identiques). Cycle complet de persistance du cursus testé (naissance → sauvegarde chaque nuit → reprise exacte au bon jour, `tick_absolu` et `palier_vocal` restaurés) ; robustesse confirmée même sur arrêt brutal (`kill -9`, écriture atomique intacte). Arène testée en conditions réelles sur un `.brain` produit par le cursus : 20 ticks avec rendu d'image (256×256×3) et télémétrie complète sans crash, `agent.training=False` confirmé. **Non-altération du cerveau prouvée directement** : comparaison `torch.equal` de tous les tenseurs du `state_dict` avant/après 50 ticks d'observation — strictement identiques.

---

## [23.0-experimental] - 2026-07-23

### Le Cursus Développemental par Ères — 1000 jours d'apprentissage autonome (expérimental, non porté sur le script de référence)

| Type | Details |
|------|---------|
| **Commit** | N/A — vit dans `agi_local_test.py` (mode `vocal_isole` + constantes d'ères) + `lecons_vocales.py`, `cursus_developpemental.py` (nouveaux fichiers) |
| **Catégorie** | feat (nouvelle mécanique cognitive majeure) |
| **Impact** | Fonctionnel (local uniquement) |

**Fait passer l'apprentissage vocal du statut de leçon manuelle ponctuelle (`client_professeur.py --palier N`) à celui de programme de développement autonome sur 1000 jours subjectifs, organisé en 3 ères de difficulté croissante — Alternance (matin MiniGrid / après-midi vocal isolé), Synesthésie (multimodal simultané le matin, syllabes/mots l'après-midi), Intégration (verbalisation de l'action toute la journée). Le curriculum MiniGrid et le curriculum vocal progressent en parallèle, chacun par son propre mécanisme de promotion — les ères orchestrent QUAND chaque apprentissage est actif, sans remplacer ni l'un ni l'autre.**

| Fichier modifié | Changement |
|-----------------|------------|
| `agi_local_test.py` | Nouveau paramètre `mode_perception="minigrid"` (défaut, non-régression validée byte-identique) ou `"vocal_isole"` sur `traiter_tick` — en `vocal_isole`, AUCUN `env.step` n'est appelé (l'environnement MiniGrid est en pause, validé par un test espionnant explicitement les appels) et la vision est un tenseur de zéros ; seuls la pensée multimodale, le JEPA, la perte vocale supervisée et la dopamine sur le score de formants s'exécutent, via une nouvelle fonction `_traiter_tick_vocal_isole` qui ne touche jamais aux buffers acteur-critique (`log_probs_journee`/`entropies_journee`/`valeurs_journee`/`recompenses_journee`/`dones_journee`) pour ne jamais les désynchroniser. Ajout des constantes `DUREE_ERE`, `TICKS_MATIN`, `BORNES_ERES`, `SEUIL_JOUR_VOCAL_REUSSI` et du helper `ere_courante(jour)`. `EtatCognitif` gagne `palier_vocal` et `gestionnaire_cursus_vocal` (instance séparée de `GestionnaireCursusAbnegation`, indépendante de celle des 7 paliers DoorKey) |
| `lecons_vocales.py` (nouveau) | `CacheReferencesVocales` : génère les références audio (`say` → MFCC) des voyelles UNE SEULE FOIS au démarrage du cursus et les met en cache mémoire, dédupliquées par mot cible — évite de ré-invoquer `say`/`afconvert` à chaque tick sur un run de centaines de milliers de ticks vocaux |
| `cursus_developpemental.py` (nouveau) | Script standalone autonome (sans client réseau, décision utilisateur) qui pilote la boucle des 1000 jours, réutilisant à l'identique `demarrer_journee`/`traiter_tick`/`executer_nuit` — seule la logique de *quoi* passer à `traiter_tick` change selon l'ère et le moment de la journée (`_perception_du_tick`). La promotion du palier vocal (`_promouvoir_palier_vocal_si_merite`) réutilise le mécanisme 2+2 succès de `GestionnaireCursusAbnegation` sur le score de formants moyen du jour |

**Validation** : non-régression MiniGrid byte-identique (`mode_perception="minigrid"` par défaut, seed=42). Mode `vocal_isole` validé par espionnage explicite de `env.step` (0 appel sur 120 ticks de test) et par une progression réelle du score de formants (0.17→0.19 sur 3 jours de test dédié). Journée mixte matin/après-midi validée sans crash malgré des buffers de longueurs différentes (`log_probs_journee` 20 entrées vs `jepa_losses` 40). Promotion vocale validée par simulation (4 jours réussis → palier a→e). Cache de références validé (déduplication : 10 appels `say` pour 11 paliers). Run complet de 2 jours du cursus exécuté de bout en bout sans erreur (préchauffage, matin, après-midi, nuit, neurogenèse).

---

## [22.1-experimental] - 2026-07-23

### Correction de l'Hémisphère Audio — un vrai signal d'apprentissage pour la bouche (expérimental, non porté sur le script de référence)

| Type | Details |
|------|---------|
| **Commit** | N/A — vit dans `agi_local_test.py`, `persistance.py`, `daemon_cerveau.py`, `client_professeur.py` |
| **Catégorie** | fix (correctif de conception majeur) |
| **Impact** | Critique (local uniquement) |

**Corrige trois défauts de conception détectés à la revue de la v22.0, dont un critique confirmé par l'exploration du code réel : la bouche (`tete_vocale`) ne recevait aucun gradient d'apprentissage dirigé (sortie détachée avant tout calcul) — elle produisait des formants sans jamais apprendre à viser la cible. Les trois corrections ont été validées expérimentalement : le score de formants progresse désormais de 0.0045 à 0.1111 sur 5 jours de leçon (×24), la preuve directe que la bouche apprend enfin.**

| Fichier modifié | Changement |
|-----------------|------------|
| `agi_local_test.py` | **Défaut 1 (CRITIQUE, "membre fantôme")** : `tete_vocale` recevait un score de récompense mais aucun gradient dirigé (`.detach()` avant tout calcul). Ajout d'une perte MSE supervisée (`etat.pertes_vocales`, nouveau 6e buffer de journée) calculée sur le tenseur `parametres_vocaux` non détaché, restreinte aux dimensions F1/F2 réellement contraintes par la leçon, sommée à `perte_totale` dans `apprendre_journee` (`COEFF_PERTE_VOCALE`). **Défaut 2 ("court-circuit de la double entrée")** : `porte_auditive` ne reçoit plus l'embedding sémantique du mot (qui aurait fait ignorer le son réel par le réseau) — `DIM_AUDIO_ENTREE` passe de 162 à 130 (MFCC seul). Le concept-cible devient une "quête vocale" de 8 dims dans `vecteur_bio` (`DIM_VECTEUR_BIO` 8→16), au même titre que les quêtes SURVIVAL_FOOD/WATER. **Défaut 3 ("empoisonnement du JEPA")** : nouvelle tête prédictive séparée `generateur_attente_audio` (4 points de synchro respectés), pondérée par un coefficient `coeff_jepa_audio` monté progressivement de 0 à `COEFF_JEPA_AUDIO_MAX` sur `RAMPE_JEPA_AUDIO` ticks audio reçus — protège le JEPA visuel (physique MiniGrid) d'une perturbation par un signal audio bruyant dès le premier tick |
| `persistance.py` | Bug détecté et corrigé pendant les tests : le passage `DIM_VECTEUR_BIO` 8→16 change la *forme* de `integrateur_bio` (pas seulement des clés manquantes) — `load_state_dict(strict=False)` seul ne suffit pas, une `RuntimeError` de mismatch de shape a été confirmée sur le vrai `.brain`. `integrateur_bio` est désormais explicitement exclu du chargement et renaît à neuf (décision assumée : cette couche a une `base_weight` quasi vide, <3% de poids non-nuls, après 481 jours — l'acquis perdu est négligeable) |
| `client_professeur.py` | Cesse d'envoyer l'embedding sémantique dans `perception['audio']` (n'envoie plus que le MFCC), cohérent avec le défaut 2 |
| `daemon_cerveau.py` | Commentaires mis à jour pour refléter le nouveau format du canal audio |

**Validation** : score de formants prouvé en progression réelle (0.0045→0.1111 sur 5 jours×24 ticks, seed fixe) — la preuve clé que le défaut 1 est corrigé. Les 4 points de synchro de `generateur_attente_audio` validés par exécution (neurogenèse préserve les poids, optimiseur resynchronisé). Rampe `coeff_jepa_audio` confirmée quasi nulle au démarrage (0.00015 au premier tick). Non-régression MiniGrid sans audio confirmée cohérente (les logs changent légèrement par rapport à la v22.0 à cause du changement dimensionnel `DIM_VECTEUR_BIO`, effet attendu et documenté, pas un bug). Résurrection du vrai `.brain` (481 jours, testée sur copie) validée de bout en bout : acquis intacts, `integrateur_bio` renaît proprement, 10 ticks MiniGrid post-greffe exécutés sans erreur.

---

## [22.0-experimental] - 2026-07-23

### L'Hémisphère Auditif & Vocal — Naulthène apprend à parler (expérimental, non porté sur le script de référence)

| Type | Details |
|------|---------|
| **Commit** | N/A — vit dans `agi_local_test.py` (greffe des 2 nouvelles couches) + `persistance.py`, `daemon_cerveau.py` (modifiés) + `hemisphere_audio.py`, `professeur_gemma.py`, `client_professeur.py` (nouveaux fichiers) |
| **Catégorie** | feat (expérimental) |
| **Impact** | Architectural (local uniquement) |

**Greffe un véritable hémisphère audio dans le cerveau `AGI_Naulthene` — une oreille (`porte_auditive`, miroir de `porte_visuelle`) et une bouche (`tete_vocale`, miroir de `tete_motrice`) — plutôt qu'un module de traitement audio bricolé à côté. Décision structurante : cerveau 100% multimodal unifié, vision et audio fusionnés dans le même bus latent (pas de "mode" audio isolé) ; l'agent voit et entend, bouge et vocalise, au même tick. Le cortex auditif est prédictif dès le départ (JEPA étendu au son, pas seulement à l'image). La récompense par tick est une distance de formants déterministe (Gemma via Ollama met ~8-30s par réponse, mesuré, incompatible avec le RL par tick) ; Gemma intervient en professeur périodique (curriculum vocal + jugement qualitatif de fin de leçon). Le babil de l'agent est synthétisé et joué en temps réel dans les haut-parleurs, dès qu'il est produit.**

| Fichier modifié | Changement |
|-----------------|------------|
| `agi_local_test.py` | Ajout de `porte_auditive` (double entrée MFCC⊕embedding sémantique, `DIM_AUDIO_ENTREE=162`) et `tete_vocale` (sortie `DIM_VOCALE=8`, paramètres de formants) aux 4 points de synchro obligatoires (`__init__`, `fortifier_synapses`, `cycle_sommeil_global`, `declencher_neurogenese`) ; `_tronc_cerebral` fusionne vision et audio par somme dans le même bus (silence = comportement identique à avant v22.0, non-régression validée sur run déterministe) ; `penser()` retourne désormais 6 valeurs (ajout de `parametres_vocaux`) ; `perte_jepa` étendue pour prédire aussi le son (cortex auditif prédictif) ; `traiter_tick` accepte `obs_auditive`/`formants_cibles` optionnels et remonte `parametres_vocaux` dans `infos_internes` à chaque tick |
| `hemisphere_audio.py` (nouveau) | Pur traitement du signal, sans dépendance au réseau : `SynthetiseurFormants` (synthèse source-filtre, cascade de 3 résonateurs biquad, validée à l'oreille sur les 5 voyelles a/e/i/o/u), `extraire_mfcc`, `distance_formants`/`recompense_formants` (récompense continue, pas binaire), `capture_micro`/`transcrire_whisper` |
| `professeur_gemma.py` (nouveau) | Client Ollama isolé (API HTTP, testable sans réseau de neurones) : `choisir_lecon` (curriculum vocal à 11 paliers, déterministe), `embedding_semantique` (réduction 384→32 dims), `juger_qualitatif` (jugement périodique, repli propre sur le score de formants si Ollama indisponible) |
| `persistance.py` | `charger_ou_naitre` passe en `load_state_dict(strict=False)` pour la rétrocompatibilité des vieux `.brain` (sans couches audio) — greffe les hémisphères en initialisation aléatoire tout en préservant les acquis existants ; bug découvert et corrigé pendant les tests : l'ancien optimiseur (moins de groupes de paramètres) plantait sur `load_state_dict` après une greffe — un optimiseur frais est désormais recréé dans ce cas précis |
| `daemon_cerveau.py` | `_vivre_connexion` décode `perception['audio']`/`perception['formants_cibles']` du paquet client et les transmet à `traiter_tick` — ouvre le verrou qui empêchait jusqu'ici tout canal de perception réel d'atteindre le cerveau (le paquet JSON était reçu mais entièrement ignoré, voir limite assumée v21.0) |
| `client_professeur.py` (nouveau) | Boucle de leçon de parole : Gemma annonce la cible du palier → référence audio via `say` (ou micro) → encodée et envoyée à la Cuve à chaque tick → `parametres_vocaux` reçus synthétisés et **joués immédiatement** (temps réel) → récompense de formants affichée → jugement Gemma périodique en fin de leçon |

**Validation** : tests exécutés (pas de suite automatisée dans ce projet) — non-régression MiniGrid byte-identique (seed fixe, `obs_auditive=None`) ; les 4 points de synchro vérifiés par exécution réelle (neurogenèse préserve les poids audio existants, LTP touche bien les 2 nouvelles couches, `cycle_sommeil_global` s'exécute sans crash) ; JEPA audio validé par `backward()` réel (gradient confirmé sur `porte_auditive`) ; greffe rétrocompatible testée sur un scénario reproduisant fidèlement un vieux `.brain` (state_dict + optimizer sans couches audio) ; flux bout-en-bout validé (daemon de test + `client_professeur.py`, son synthétisé et joué en temps réel, jugement Gemma reçu).

---

## [21.0-experimental] - 2026-07-23

### Le Cerveau Persistant en Cuve — Architecture Client-Serveur (expérimental, non porté sur le script de référence)

| Type | Details |
|------|---------|
| **Commit** | N/A — vit dans `agi_local_test.py` (refactor) + `persistance.py`, `daemon_cerveau.py`, `client_corps.py` (nouveaux fichiers) |
| **Catégorie** | feat (expérimental) |
| **Impact** | Architectural (local uniquement) |

**Sépare définitivement la Conscience (le réseau + son état biologique, hébergé par un daemon persistant) du Corps (l'environnement MiniGrid, jetable), via une architecture Client-Serveur en sockets TCP/IP. L'agent traverse désormais les redémarrages de process : dopamine, satiété, mémoire épisodique, dimension du bus et progression de cursus survivent à l'arrêt/relance du daemon.**

| Fichier modifié | Changement |
|-----------------|------------|
| `agi_local_test.py` | Refactor pur (aucun changement de comportement, validé par comparaison de logs avant/après sur run déterministe) : extraction de la boucle principale (~500 lignes, jusque-là au niveau module) en un conteneur d'état `EtatCognitif` et quatre fonctions réutilisables — `initialiser_etat_cognitif()`, `demarrer_journee(etat)`, `traiter_tick(etat)`, `executer_nuit(etat)`. Le mode standalone (`if __name__ == "__main__":`) et la Cuve du daemon consomment désormais les mêmes fonctions — zéro duplication de la logique dopamine/détecteurs/curriculum/rêve adaptatif |
| `persistance.py` (nouveau) | `PersistanceAnatomique` : cristallise/ressuscite l'état complet d'un `EtatCognitif` dans un fichier `.brain` (`torch.save`/`torch.load`, écriture atomique via fichier temporaire + `os.replace`) — dimension du bus (pour reconstruire l'agent à la bonne taille AVANT `load_state_dict`), poids + traces de myéline/éligibilité, état de l'optimiseur Adam, chimie viscérale (dopamine, jauges biologiques, quête active), mémoire épisodique spatiale, curriculum (niveau, palier, victoires), thermostat de neurogenèse, compteurs de temps |
| `daemon_cerveau.py` (nouveau) | `CuveDeMaintien` : serveur socket TCP qui héberge le cerveau en continu. Cryostase (`socket.accept()` bloquant, CPU ~0%) tant qu'aucun corps n'est connecté. Modèle de temps hybride (décision utilisateur) : une nuit complète (apprentissage + rêve adaptatif + ressort dopaminergique + thermostat de neurogenèse + `cycle_sommeil_global`) se déclenche soit **in-session** dès qu'une journée subjective (`ticks_par_jour`) est accumulée, soit **à la déconnexion** si assez de ticks se sont écoulés depuis la dernière nuit ; sinon une simple **micro-sieste** (cristallisation sans érosion ni rêve) préserve le cerveau — protection explicite contre l'« Alzheimer numérique » d'une nuit relancée à vide sur des sessions courtes et répétées |
| `client_corps.py` (nouveau) | Pilote de session jetable : ouvre/maintient/ferme une connexion vers la Cuve selon le protocole JSON prévu par le design. Limite assumée de cette itération (documentée dans le fichier et dans `daemon_cerveau.py`) : l'environnement MiniGrid réel tourne côté serveur (les détecteurs biologiques/spatiaux lisent les internes MiniGrid, intransmissibles par un simple flux pixels+action) — le découplage total est une évolution future, pas un correctif oublié |
| `.gitignore` | Ajout de `*.brain` (cerveaux cristallisés, données binaires lourdes) ; les 3 nouveaux fichiers `.py` restent trackés |

**Validation** : run de non-régression déterministe (seed fixe) comparant les logs console avant/après le refactor de l'Étape 1 — coïncidence exacte. Test end-to-end de persistance à travers un redémarrage complet du process daemon (résurrection avec `tick_absolu`, dopamine, niveau et dimension du bus fidèles à l'état sauvegardé, y compris après neurogenèse 16→32 dims). Test dédié par assertions du régime micro-sieste vs nuit complète (seuil de ticks).

---

## [20.0-experimental] - 2026-07-23

### Mémoire Épisodique Spatiale & LTP Hebbien (expérimental, non porté sur le script de référence)

| Type | Details |
|------|---------|
| **Commit** | N/A — vit uniquement dans `agi_local_test.py`, non tracké par git |
| **Catégorie** | feat (expérimental) |
| **Impact** | Fonctionnel (local uniquement) |

**Ajoute une mémoire épisodique spatiale (où/quand/quoi) persistante dans la journée, consommée par le vecteur bio existant, et une Potentiation à Long Terme (LTP) hebbienne pilotée par les pics de dopamine par tick.**

| Fichier modifié | Changement |
|-----------------|------------|
| `agi_local_test.py` | Ajout de `MemoireEpisodiqueSpatiale` : enregistre position/type/tick des ressources trouvées, persiste à travers les épisodes d'une même journée, vidée uniquement au changement de niveau (`reinitialiser_niveau`) |
| `agi_local_test.py` | `BiologicalHomeostasisEngine.obtenir_vecteur_bio()` accepte un `rappel_spatial` (distance normalisée + fraîcheur) ; `DIM_VECTEUR_BIO` passe de 6 à 8 dims |
| `agi_local_test.py` | Boucle principale : récupération de contexte avant construction du vecteur bio (si une quête de survie est active), enregistrement d'événement à la consommation d'une ressource, compteur `tick_absolu` global |
| `agi_local_test.py` | `NaultheneLinearSynaptique` : ajout de `trace_activation` (trace d'éligibilité, accumulation exponentielle à chaque tick) et de `fortification_dopaminergique()` (LTP : grave les synapses actives dans `base_weight` proportionnellement au pic de dopamine) ; `agrandir()` étend `trace_activation` comme `myeline_M` ; `cycle_sommeil()` la remet à zéro |
| `agi_local_test.py` | `AGI_Naulthene.fortifier_synapses()` : nouvelle méthode appelant `fortification_dopaminergique()` sur toutes les couches plastiques, appelée depuis la boucle principale sur `poids_evenement` (par tick, pas une seule fois par jour sur la moyenne des récompenses comme le pseudo-code initial — évite de diluer un événement isolé) |
| `agi_local_test.py` | Nouvelle métrique W&B : `Memoire_Episodique_Taille` |

---

## [19.0-experimental] - 2026-07-22

### Métabolisme 20/80 & Forage 80/20 (expérimental, non porté sur le script de référence)

| Type | Details |
|------|---------|
| **Commit** | N/A — vit uniquement dans `agi_local_test.py`, non tracké par git |
| **Catégorie** | feat (expérimental) |
| **Impact** | Fonctionnel (local uniquement) |

**Remplace le coût énergétique fixe de la v18.0 par un calcul dynamique 20% Cerveau / 80% Corps, et introduit un cycle de forage (respawn) 80% Nid / 20% Dispersion pour la Nourriture.**

| Fichier modifié | Changement |
|-----------------|------------|
| `agi_local_test.py` | `BiologicalHomeostasisEngine.calculer_effort_metabolique()` : nouvelle méthode fusionnant coût corporel (80%, dépend du type d'action MiniGrid réelle — tourner/avancer/manipuler) et coût cognitif (20%, dérivé de `force_planification` et de la somme des `HORIZONS_PLANIFICATION`) ; remplace la constante fixe `COUT_ACTION_METABOLIQUE` (supprimée) |
| `agi_local_test.py` | `DetecteurRessourcesBiologiques` : ajout d'un `nid_position` (dérivé de la carte courante à l'initialisation de l'épisode, jamais une coordonnée fixe codée en dur) et de `_faire_repousser_food()` — la Nourriture consommée réapparaît immédiatement (80% près du nid ±1 case, 20% dispersée aléatoirement) ; l'Eau ne respawn pas |
| `agi_local_test.py` | Boucle principale : câblage de `calculer_effort_metabolique()` avant `step_metabolisme()`, nouveau compteur `effort_metabolique_jour` |
| `agi_local_test.py` | Nouvelle métrique W&B : `Bio_Effort_Metabolique_Moyen` |

---

## [18.0-experimental] - 2026-07-22

### Architecture Homéostatique Biologique (expérimental, non porté sur le script de référence)

| Type | Details |
|------|---------|
| **Commit** | N/A — vit uniquement dans `agi_local_test.py`, non tracké par git |
| **Catégorie** | feat (expérimental) |
| **Impact** | Fonctionnel (local uniquement) |

**Trois jauges vitales (satiété, hydratation, stimulation) régies par la Théorie de la Réduction du Drive (Hull), avec génération procédurale de ressources et quêtes de survie autonomes. Existe uniquement dans `agi_local_test.py` en attendant validation sur un run local suffisamment long avant portage sur `agi_google_colab.py`.**

| Fichier modifié | Changement |
|-----------------|------------|
| `agi_local_test.py` | Ajout de `BiologicalHomeostasisEngine` : jauges satiété/hydratation/stimulation dégradées à chaque tick, déficit homéostatique $D(t)$, récompense `r_bio` = réduction du déficit, injectée dans `TENEUR_DOPAMINE` existant (pas de second réservoir de dopamine parallèle, contrairement au pseudo-code initial) |
| `agi_local_test.py` | Ajout de `DetecteurRessourcesBiologiques` : génération procédurale de sources Nourriture/Eau via `Ball` colorées (rouge/bleu) placées sur des cases vides aléatoires par épisode, consommées et retirées de la grille au contact |
| `agi_local_test.py` | Génération autonome de quêtes de survie (`SURVIVAL_FOOD` > `SURVIVAL_WATER` > `EXPLORATION_STIM`) dès qu'une jauge passe sous 0.35 |
| `agi_local_test.py` | Ajout de la couche `integrateur_bio` (`NaultheneLinearSynaptique`, `dim_bus + 6 → dim_bus`) dans `AGI_Naulthene` : fusionne la pensée avec le vecteur bio (jauges + quête) avant la tête motrice et le rollout mental — intégré à l'architecture existante plutôt que de dupliquer un agent/encodeur parallèle (`V18BiologicalAgent` du pseudo-code initial) |
| `agi_local_test.py` | `declencher_neurogenese`/`cycle_sommeil_global` mis à jour pour couvrir `integrateur_bio` ; le vecteur bio (6 dims) ne grandit jamais avec la neurogenèse |
| `agi_local_test.py` | Nouvelles métriques W&B : `Bio_Satiete`, `Bio_Hydratation`, `Bio_Stimulation`, `Bio_Deficit`, `Bio_R_Bio_Jour`, `Bio_Food_Consommes_Jour`, `Bio_Water_Consommes_Jour`, `Bio_Quete_Active` |

---

## [17.0] - 2026-07-22

### Volonté Émergente & Sous-Objectifs Intrinsèques

| Type | Details |
|------|---------|
| **Commit** | `a0aa9e0` |
| **Catégorie** | feat |
| **Impact** | Fonctionnel |

**Décrochage précoce du Mode Libre (Palier 5 au lieu de 7), génération de sous-quêtes intrinsèques par curiosité JEPA, et Sursaut de Volonté qui étire la patience à 95% du seuil plutôt que de laisser l'agent abandonner.**

| Fichier modifié | Changement |
|-----------------|------------|
| `agi_google_colab.py` | `SEUIL_PALIER_MODE_LIBRE = 5` : le guidage artificiel (`RECOMPENSE_APPROCHE_BUT`) se désactive dès le Palier 5 (Viser la Porte) au lieu du Palier 7 |
| `agi_google_colab.py` | Ajout de `DetecteurCuriositeJEPA` : génère une micro-récompense de sous-quête quand l'erreur JEPA du tick dépasse 1.5x la moyenne récente (surprise du World Model), actif uniquement en Mode Libre — distinct de `dopamine_curiosite` existant (scaling continu, pas un signal de sous-quête) |
| `agi_google_colab.py` | Ajout de `ModuleSursautVolonte` : à 95% de la patience du jour, déclenche un boost dopaminergique ponctuel (`BOOST_SECOND_SOUFFLE`) et étire la patience de l'épisode (+50 ticks, plafonnée), un seul sursaut par épisode — actif uniquement en Mode Libre |
| `agi_google_colab.py` | `ModuleAcceptationAbnegation.augmenter_patience_de_base_definitivement()` : une victoire réelle obtenue après un Sursaut de Volonté augmente durablement `patience_min` (apprentissage de la récurrence) |
| `agi_google_colab.py` | Nouvelles métriques W&B : `Sursauts_Volonte_Jour`, `Patience_Min_Actuelle`, `Sous_Objectifs_Curiosite_Jour` |
| `agi_google_colab.py` | Omission assumée par rapport à la spécification initiale : le "chuchotement d'indice visuel" (illumination du chemin) n'est pas implémenté — nécessiterait de modifier l'observation renvoyée par MiniGrid, hors de portée sans toucher au moteur de rendu de l'environnement |

---

## [16.0] - 2026-07-22

### Thermostat Multimodal & Patience par Abnégation

| Type | Details |
|------|---------|
| **Commit** | `65d70d2` |
| **Catégorie** | feat |
| **Impact** | Fonctionnel |

**Pression cinétique modulée par le contexte perception-action (multimodalité) et promotion de palier DoorKey remplacée par un compteur cumulatif à 4 succès (2 sous-seuils), avec patience étirée sur le sous-seuil le plus exigeant.**

| Fichier modifié | Changement |
|-----------------|------------|
| `agi_google_colab.py` | `ThermostatCinetique` renommé `ThermostatCinetiqueMultimodal` : la pénalité brute de stagnation (inchangée) est désormais atténuée selon le contexte du tick — déplacement libre ($\times 1.00$), objet transporté (`carrying`, $\times 0.30$), interaction face à `Key`/`Door`/`Goal` avec `pickup`/`toggle` ($\times 0.05$) |
| `agi_google_colab.py` | `ModuleAcceptationAdaptative` renommé `ModuleAcceptationAbnegation` : `obtenir_seuil_patience()` accepte désormais un `facteur_complexite_sous_seuil` qui étire la patience de base |
| `agi_google_colab.py` | Ajout de `GestionnaireCursusAbnegation` : remplace la promotion de palier DoorKey par taux de réussite journalier (`SEUIL_MAITRISE_PALIER`, supprimé) par un compteur cumulatif de 4 succès répartis en 2 sous-seuils (Amorçage ×2, Consolidation/Abnégation ×2 sous patience `× COEFF_ABNEGATION_SOUS_SEUIL_2 = 1.6`) |
| `agi_google_colab.py` | Boucle principale : câblage du facteur de complexité par jour, appel du gestionnaire de cursus à chaque fin d'épisode (au lieu du calcul de taux en fin de journée), nouvelles constantes `FACTEUR_ATTENUATION_*`, `SUCCES_PAR_SOUS_SEUIL`, `COEFF_ABNEGATION_SOUS_SEUIL_2` |
| `agi_google_colab.py` | Nouvelles métriques W&B : `Sous_Seuil_Abnegation`, `Succes_Sous_Seuil_Courant`, `Facteur_Complexite` |

---

## [15.0] - 2026-07-22

### Planification Non-Linéaire, Pression Cinétique & Patience Adaptative

| Type | Details |
|------|---------|
| **Commit** | `c5d23dc` |
| **Catégorie** | feat |
| **Impact** | Fonctionnel |

**Système 2 étendu à un rollout multi-échelle à sauts temporels, ajout d'un coût de stagnation générique et d'un seuil de patience adaptatif remplaçant le plafond de ticks fixe.**

| Fichier modifié | Changement |
|-----------------|------------|
| `agi_google_colab.py` | `simuler_futur_et_planifier` : remplacement du rollout pas-à-pas ($t+1 \to t+2 \to t+3$) par un rollout à sauts exponentiels sur des horizons `(1, 3, 7)` — le premier horizon branche sur les 7 actions réelles, les suivants comblent l'écart en suivant le réflexe glouton de la politique, évalués à chaque point d'arrivée et sommés avec actualisation $\gamma^{\text{horizon}}$ |
| `agi_google_colab.py` | `penser()` : paramètre `horizon_planification` (entier) remplacé par `horizons_planification` (tuple) ; `HORIZONS_PLANIFICATION = (1, 3, 7)` dans la config d'exécution |
| `agi_google_colab.py` | Ajout de `ThermostatCinetique` : détecteur générique de pression cinétique, pénalise l'immobilité stricte et le piétinement (positions répétées dans une fenêtre glissante) — actif sur tous les niveaux du `PROGRAMME` |
| `agi_google_colab.py` | Ajout de `ModuleAcceptationAdaptative` : calcule un seuil de patience par épisode (`obtenir_seuil_patience()`) à partir du taux de succès et de la vitesse des succès sur les 20 derniers épisodes ; déclenche une troncature volontaire (`abandon_par_patience`) si l'épisode dépasse ce seuil sans conclusion naturelle, avec une friction dopaminergique douce dédiée (`TAUX_FRICTION_DOUCE_ABANDON`) plutôt qu'un choc négatif |
| `agi_google_colab.py` | Nouvelles métriques W&B : `Patience_Max_Episode`, `Abandons_Patience_Jour`, `Penalite_Stagnation` |

---

## [14.0] - 2026-07-22

### Rêves Adaptatifs & Planification Étendue à 3 Pas

| Type | Details |
|------|---------|
| **Commit** | `2247f2b` (commit initial groupé) |
| **Catégorie** | feat |
| **Impact** | Fonctionnel |

**Consolidation nocturne à porosité adaptative et Système 2 étendu à un horizon de 3 pas.**

| Fichier modifié | Changement |
|-----------------|------------|
| `agi_google_colab.py` | Suppression de la taille de batch de rêve fixe (64) au profit d'un pourcentage adaptatif dérivé de la plasticité base et de la richesse moyenne de la journée |
| `agi_google_colab.py` | `simuler_futur_et_planifier` poussé à un horizon de 3 pas (pas 1 = 7 actions réelles, pas 2/3 = réflexe glouton de la politique, pour éviter l'explosion combinatoire $7^3$) |
| `agi_google_colab.py` | Ajout de `DetecteurFranchissementPortes` (micro-récompense au franchissement d'une porte ouverte) |
| `agi_google_colab.py` | Ajout de `DetecteurProgresPersonnel` (quêtes auto-générées sur les records de proximité au but) |

---

## [13.0] - 2026-07-22

### Décision Autonome & Mode Libre

| Type | Details |
|------|---------|
| **Commit** | `2247f2b` (commit initial groupé) |
| **Catégorie** | feat |
| **Impact** | Fonctionnel |

**Retrait du guidage artificiel une fois le Palier 7 validé, avec relais méta-cognitif renforcé.**

| Fichier modifié | Changement |
|-----------------|------------|
| `agi_google_colab.py` | `Mode_Libre` : désactivation de la récompense de guidage vers l'objectif dès la première validation du Palier 7 |
| `agi_google_colab.py` | `force_planification` monte à 0.85 et `coeff_entropie` à 0.06 en Mode Libre, pour maintenir une exploration active sans béquille |

---

## [12.0] - 2026-07-22

### Cursus à 7 Paliers & Correctif d'Épisodes

| Type | Details |
|------|---------|
| **Commit** | `2247f2b` (commit initial groupé) |
| **Catégorie** | feat |
| **Impact** | Fonctionnel |

**Décomposition du cursus DoorKey en 7 paliers cognitifs et correction du bug des épisodes tronqués.**

| Fichier modifié | Changement |
|-----------------|------------|
| `agi_google_colab.py` | `DetecteurJalonsDoorKey` : division de la tâche `DoorKey` en 7 paliers (Regarder → S'approcher → Toucher/Prendre → Transporter → Viser la Porte → Déverrouiller → Franchir & Sortir) |
| `agi_google_colab.py` | Correction du bug `0/0 épisodes (maîtrise: N/A)` causé par la fin de journée à t=250 ; durée de journée augmentée à 400 ticks |

---

## [11.0] - 2026-07-22

### Réservoir Dopaminergique V3

| Type | Details |
|------|---------|
| **Commit** | `2247f2b` (commit initial groupé) |
| **Catégorie** | feat |
| **Impact** | Fonctionnel |

**Remplacement du tonus dopaminergique fixe par un réservoir homéostatique dynamique.**

| Fichier modifié | Changement |
|-----------------|------------|
| `agi_google_colab.py` | Réservoir `TENEUR_DOPAMINE` (0.001 à 10.0) régi par Friction (décroissance quotidienne), Choc (succès) et Ressort (reset nocturne vers 5.0) |
| `agi_google_colab.py` | `EMPREINTE_ENFANCE` : modulation de l'intensité d'apprentissage par la taille du bus visuel initial |

---

## [10.0-fix1] - 2026-07-22

### Correctif de Stabilité JEPA & Thermostat

| Type | Details |
|------|---------|
| **Commit** | `2247f2b` (commit initial groupé) |
| **Catégorie** | fix |
| **Impact** | Critique |

**Correctif de stabilité sur le modèle du monde JEPA et le thermostat de neurogenèse.**

| Fichier modifié | Changement |
|-----------------|------------|
| `agi_google_colab.py` | Stabilisation de la perte JEPA et du déclenchement du thermostat de mutation |

---

## [10.0] - 2026-07-22

### Système 2 & Rollout Mental Vectorisé

| Type | Details |
|------|---------|
| **Commit** | `2247f2b` (commit initial groupé) |
| **Catégorie** | feat |
| **Impact** | Fonctionnel |

**Introduction du Système 2 délibératif via un rollout mental vectorisé.**

| Fichier modifié | Changement |
|-----------------|------------|
| `agi_google_colab.py` | `simuler_futur_et_planifier` : simulation mentale vectorisée des conséquences des actions, arbitrage avec le Système 1 instinctif via `force_planification` |

---

## [9.1] - 2026-07-22

### Intégration du Tampon Épisodique (Université)

| Type | Details |
|------|---------|
| **Commit** | `2247f2b` (commit initial groupé) |
| **Catégorie** | feat |
| **Impact** | Fonctionnel |

**Ajout de la mémoire épisodique de contexte pour la rétention d'informations temporelles.**

| Fichier modifié | Changement |
|-----------------|------------|
| `agi_google_colab.py` | `vecteurs_episodiques` / `lecture_episodique` : moyenne glissante des états latents récents de l'épisode, utile pour `MemoryS7` (Université) |

---

## [9.0-fix1] - 2026-07-22

### Correctif de la Neurogenèse Bloc par Bloc

| Type | Details |
|------|---------|
| **Commit** | `2247f2b` (commit initial groupé) |
| **Catégorie** | fix |
| **Impact** | Critique |

**Correction de la segmentation des dimensions lors de l'agrandissement des couches.**

| Fichier modifié | Changement |
|-----------------|------------|
| `agi_google_colab.py` | `NaultheneLinearSynaptique.agrandir()` : correction de la reconstruction bloc par bloc des poids existants lors de la neurogenèse |

---

## [9.0] - 2026-07-22

### Cursus Académique Progressif (Primaire à Doctorat)

| Type | Details |
|------|---------|
| **Commit** | `2247f2b` (commit initial groupé) |
| **Catégorie** | feat |
| **Impact** | Fonctionnel |

**Mise en place du programme complet des 5 niveaux MiniGrid.**

| Fichier modifié | Changement |
|-----------------|------------|
| `agi_google_colab.py` | `PROGRAMME` : Primaire (`Empty-8x8`) → Collège (`DoorKey-6x6`) → Lycée (`Unlock-5x5`) → Université (`MemoryS7`) → Doctorat (`MultiRoom-N4-S5`), promotion après 2 victoires consécutives |

---

## [8.0] - 2026-07-22

### Alignement Graph-Gradient RL & Rêve Nocturne

| Type | Details |
|------|---------|
| **Commit** | `2247f2b` (commit initial groupé) |
| **Catégorie** | feat |
| **Impact** | Fonctionnel |

**Introduction du mécanisme de rêve nocturne (replay) et alignement des gradients RL/JEPA.**

| Fichier modifié | Changement |
|-----------------|------------|
| `agi_google_colab.py` | `rever()` : rejeu d'un lot de souvenirs pondéré par importance pendant la phase de sommeil |
| `agi_google_colab.py` | Alignement du graphe de calcul entre la perte Acteur-Critique et la perte JEPA pour un unique `backward()` cohérent |

---

## [7.0] - 2026-07-22

### Phase 7 Initiale (Architecture Hybride Duale)

| Type | Details |
|------|---------|
| **Commit** | `2247f2b` (commit initial groupé) |
| **Catégorie** | feat |
| **Impact** | Fonctionnel |

**Première version documentée de l'architecture hybride RL + JEPA.**

| Fichier modifié | Changement |
|-----------------|------------|
| `agi_google_colab.py` | Socle initial : `AGI_Naulthene`, tronc cérébral commun, tête motrice Acteur-Critique, modèle du monde JEPA |

---

*Note : les entrées v7.0 à v14.0 ont été reconstituées à partir du journal narratif de [readme.md](../../readme_fr.md) lors de la mise en place initiale de ce changelog (2026-07-22) — les hash de commit réels n'étaient pas disponibles rétroactivement (dépôt git non initialisé jusqu'à cette date). Toute nouvelle entrée à partir de maintenant doit renseigner un hash réel.*
