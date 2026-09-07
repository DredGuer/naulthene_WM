# Registre des problèmes à corriger — Naulthène AGI

> **Créé le 8 septembre 2026** à partir de `readme.md`, du début de
> `docs/fonctionnement/CHANGELOG.md`, de l'index documentaire, des carnets récents et d'une
> inspection statique ciblée du code.
>
> **Nature du document : registre opérationnel, non normatif.** La référence factuelle reste
> `docs/fonctionnement/CHANGELOG.md`. Ce fichier sert à préparer les corrections et doit être
> mis à jour lorsqu'un problème est vérifié, corrigé, réfuté ou requalifié.
>
> ⚠️ Aucun entraînement ni test dynamique n'a été exécuté pour l'audit initial. Une inspection
> statique établit un écart de code ou de documentation ; elle ne démontre pas à elle seule son
> effet causal sur les performances.

---

## 1. Mode d'emploi

### Statuts

| Statut | Sens |
|---|---|
| 🔴 **Ouvert** | problème confirmé ou protection insuffisante ; correction à concevoir |
| 🟠 **À reproduire** | écart confirmé statiquement, effet dynamique non mesuré |
| 🟡 **À décider** | choix de méthode, d'architecture ou de gouvernance |
| 🔵 **À mesurer** | hypothèse scientifique ou optimisation nécessitant un protocole |
| ✅ **Clos** | correction vérifiée avec preuve et référence au CHANGELOG |
| ❌ **Réfuté** | hypothèse testée et écartée ; conserver la raison pour ne pas la rouvrir |

### Niveaux de priorité

- **P0 — avant toute nouvelle campagne concernée** : risque d'invalider l'expérience ou son
  interprétation.
- **P1 — prochain cycle de fiabilisation** : risque récurrent important, sans invalider
  automatiquement les résultats existants.
- **P2 — amélioration structurante** : reproductibilité, maintenance, performance ou clarté.
- **P3 — recherche ultérieure** : chantier scientifique conditionné par les corrections P0/P1.

### Règle de clôture

Un problème ne passe à `✅ Clos` que si les quatre éléments suivants sont consignés :

1. cause ou décision explicitée ;
2. correction ou changement documentaire référencé ;
3. vérification fraîche reproduisant le contrat attendu ;
4. entrée CHANGELOG ou carnet donnant la portée et les limites du résultat.

---

## 2. Vue d'ensemble priorisée

| ID | Priorité | Statut | Problème | Action immédiate |
|---|---:|---|---|---|
| APP-01 | P0 | ✅ Clos | La politique rejouée la nuit n'est pas la politique ayant collecté les actions | Corrigé v41.64 (`6d6bcaa`) — rejeu sur politique complète |
| APP-02 | P0 | ✅ Clos | `--detach-c2` n'est pas conservé dans les époques supplémentaires | Corrigé v41.64 (`6d6bcaa`) — detach sur chaque passe |
| MES-01 | P0 | ✅ Clos | Le dépouillement peut publier sur une cohorte incomplète ou un garde-fou échoué | Corrigé v41.65 (`54c1867`) — primitive stricte + manifestes, 6 scripts migrés |
| MES-02 | P0 | ✅ Clos | La sonde du rollout réimplémente encore le noyau | Corrigé v41.66 (`48aa8a6`) — trace `trace_rollout` + sonde canonique |
| APP-03 | P1 | 🔴 Ouvert | Deux identités/configurations du module `noyau` | Point d'entrée léger et configuration unique |
| API-01 | P1 | 🔴 Ouvert | Le tuple positionnel de `penser()` est fragile | Sortie nommée et validations de forme |
| MES-03 | P1 | 🔴 Ouvert | Des dispersions de récompense sont présentées comme parts du gradient | Corriger le vocabulaire et mesurer séparément |
| MES-04 | P1 | 🟡 À décider | Le seuil `2,86` appliqué contredit la famille de 3 métriques déclarée (2,625) | Trancher : famille de 3, ou α = 0,01 assumé |
| QUA-01 | P1 | 🟠 Amorcé | Absence de petite suite automatisée et de CI | `tests/` livré en v41.65 (40 tests) ; reste `penser()` et la CI |
| EVA-01 | P1 | 🔵 À mesurer | Le juge principal est bruité et dépend du palier atteint | Banc final standard sur cartes fixes |
| DOC-01 | P1 | 🔴 Ouvert | L'état courant et l'historique se contredisent dans la documentation | État courant unique + miroir EN/FR |
| PER-01 | P1 | 🟠 À reproduire | Le chargement permissif peut masquer une anomalie comme migration | Migrations explicites, strictes hors cas connus |
| REP-01 | P2 | 🔴 Ouvert | Installation et versions non verrouillées | `pyproject`/contraintes et manifeste de run |
| PER-02 | P2 | 🟠 À reproduire | Deux écrivains peuvent partager le même fichier temporaire de checkpoint | Temporaire unique, verrou, test d'incident |
| SCI-01 | P2 | 🔵 À mesurer | K=8 est un point favorable, pas un optimum ni une valeur dérivée | Balayage K et politique d'arrêt |
| SCI-02 | P2 | 🔵 À mesurer | Le benchmark PPO n'est pas égalisé selon tous les budgets | Comparaisons séparées interactions/calcul/mémoire |
| SCI-03 | P2 | 🔵 À mesurer | La neurogenèse globale produit beaucoup de capacité inactive | Trajectoire des activations puis témoin à taille fixe |
| SCI-04 | P2 | 🔵 À mesurer | Le ratio Bio/Env est non tranché et mal nommé « gradient » | Mesure causale avec échelle dérivée |
| SCI-05 | P3 | 🟡 À décider | La tête d'intention C2 serait construite avant validation complète de ses entrées | Reporter après fidélité du rollout et ablations |
| ARC-01 | P2 | 🟡 À décider | `colab.py` reste nommé référence alors que le développement réel vit dans `noyau.py` | Décider et documenter la source de vérité |

---

# 3. Apprentissage et politique

## APP-01 — La politique rejouée n'est pas celle qui a collecté les actions — ✅ CLOS (07/09/2026)

- **Priorité / statut** : **P0 — ✅ Clos** (correction `6d6bcaa`, CHANGELOG [v41.64])
- **Nature** : écart structurel confirmé ; impact quantitatif non mesuré.

### Preuves

Dans `src/naulthene/cerveau/noyau.py` :

- les actions de la journée proviennent de `penser()`, puis de l'arbitrage C1+C2
  (`~1532-1538`, appel et collecte `~9423-9486`) ;
- les anciennes log-probabilités sont conservées pour les passes supplémentaires
  (`~1936`, reprises `~2014`) ;
- le rejeu recalcule C1 directement par `_executer_c1_reflexe`, puis construit la
  distribution sur ses logits (`~2018-2023`) ;
- le ratio est ensuite `exp(lp - lp_old)` (`~2026-2031`).

Le rejeu ne reconstruit donc pas explicitement l'arbitrage C1+C2 de la politique ayant produit
les actions. Selon le régime, il peut également ignorer certaines modulations appliquées autour
de `penser()` : vigueur, audio, ou réponse C3. Dans la campagne K8 publiée, la voix libre
neutralise toutefois la composante `gain_c1` et le chemin C3 est normalement dormant.

### Impact possible

- Un ratio peut différer de 1 avant même toute mise à jour de poids.
- Le bras nu et le bras clippé ne diffèrent pas seulement par le clamp : le bras nu utilise
  `-(lp * avantage)`, le bras clippé utilise le ratio d'importance.
- La conclusion empirique « les deux bras ont des performances différentes » reste une
  observation ; la conclusion générale « le clipping PPO nuit » n'est pas encore isolée.

### Correction proposée

1. Définir explicitement la politique cible des époques supplémentaires : politique complète
   déployée ou apprentissage volontaire de C1 à partir d'une politique comportementale distincte.
2. Centraliser la reconstruction des logits de la politique choisie.
3. Ajouter une assertion de parité avant le premier pas supplémentaire : mêmes poids + mêmes
   entrées ⇒ log-probabilités attendues selon le contrat choisi.
4. Logger distribution du ratio, moyenne, quantiles, fraction clippée et divergence KL.

### Critères de clôture

- Test CPU montrant le contrat de parité sur plusieurs états et régimes.
- Test couvrant C2 actif/inactif, voix libre, brain-sparing et action masquée.
- Nouvelle expérience isolant clairement ratio d'importance et clamp.
- Interprétation K8 requalifiée dans le CHANGELOG si nécessaire.

### Clôture (07/09/2026, commit `6d6bcaa`)

1. **Cause** : le rejeu nocturne reconstruisait `tete_motrice` nue ; la log-prob diurne
   (`lp_old`) vient des logits fusionnés C1+C2 → le ratio comparait deux politiques.
2. **Correction** : rejeu sur la politique COMPLÈTE reconstruite (helper
   `_logits_politique_complete_rejouee` : C1 + C2 re-rollout par état, fusion avec le
   contexte figé `k1`/`k2` stocké par tick, `.clone()` des états).
3. **Vérification fraîche (CPU, `experiences/prevol_app01_app02.py`) T1** : parité de
   formule sur 32 régimes × 2 (C2 actif/SANS_C2 · voix libre/renormalisation ·
   brain-sparing · corps-rollout · action masquée) → delta max **0,0** (≤ 1,5e-8) ;
   journées réelles K=8 (voix libre, detach, bras clippé) : **0 violation** du garde de
   forme échantillonné.
4. **Entrée CHANGELOG** : [v41.64]. ⚠️ Découverte clé consignée : le pas de politique du
   jour précède les époques, donc le ratio de la passe 0 ne doit PAS être 1 — le garde de
   parité porte sur la FORME (reconstruction ≡ `penser`), jamais sur l'égalité des
   log-probs après un pas d'optimiseur.

---

## APP-02 — Le détachement de C2 n'est pas conservé dans les passes supplémentaires — ✅ CLOS (07/09/2026)

- **Priorité / statut** : **P0 — ✅ Clos** (correction `6d6bcaa`, CHANGELOG [v41.64])
- **Nature** : graphe de gradient incohérent pour la combinaison K > 1 + detach.

### Preuves

- `penser()` applique `pensee_bio.detach()` quand `DETACH_C2_ASYMETRIQUE` est actif
  (`noyau.py ~1559-1563`).
- `_epoques_supplementaires` appelle directement
  `self.cortex_prefrontal(pensee_bio)` (`~2024`), puis rétropropage sa MSE (`~2035-2043`).

Ainsi, le premier pas peut empêcher le critique de sculpter la représentation partagée, tandis
que les K−1 passes suivantes réouvrent ce chemin.

### Limite

La campagne K8 publiée n'activait pas `--detach-c2`. Cet écart ne constitue donc pas une
explication démontrée de ses résultats ; il concerne la combinaison future des deux leviers.

### Correction proposée

- Appliquer la même règle de détachement à toutes les passes.
- Vérifier également tout drapeau analogue, notamment `GRADIENT_C2_ACTIF`.
- Faire du contrat de gradient une fonction partagée, plutôt qu'une branche du seul `penser()`.

### Critères de clôture

- Test par hooks ou normes de gradient : gradient critique nul dans les couches protégées pour
  chaque passe, non nul dans le témoin.
- Test K=1 et K>1.
- Pré-vol de la première campagne combinée K + detach.

### Clôture (07/09/2026, commit `6d6bcaa`)

1. **Cause** : le rejeu appelait `cortex_prefrontal(pensee_bio)` sans le détachement que
   `penser()` applique (v41.32) → les K−1 passes réouvraient le chemin du critique vers le
   tronc partagé.
2. **Correction** : le rejeu applique la même règle sur **chaque** passe (`entree_critique =
   pensee_bio.detach() si DETACH_C2_ASYMETRIQUE`), exactement comme `penser`.
3. **Vérification fraîche (CPU, `experiences/prevol_app01_app02.py`) T2** : norme du
   gradient du critique sur `integrateur_bio` = **2,891** (sans detach) → **0,000** (avec),
   sur le graphe exact du rejeu ; journée réelle K=8 + `--detach-c2` : exit 0, 0 violation.
4. **Entrée CHANGELOG** : [v41.64].

---

## APP-03 — Deux identités et deux configurations du noyau

- **Priorité / statut** : **P1 — 🔴 Ouvert**
- **Nature** : fragilité de configuration confirmée ; aucun nouveau flag déclaré cassé.

### Preuves

`persistance.py ~32-37` importe `naulthene.cerveau.noyau`, tandis que le noyau peut être exécuté
comme `__main__`. `noyau.py ~12535-12565` synchronise donc explicitement `globals()` et
`_module_reel` pour plusieurs options.

Le CHANGELOG v41.62 consigne un pré-vol où K=1 et K=8 restaient initialement identiques parce
que la collecte et l'apprentissage lisaient deux copies différentes de la configuration.

### Correction proposée

- Transformer l'exécutable en point d'entrée léger important un noyau nommé unique.
- Porter les options dans un objet de configuration explicite transmis aux composants.
- Enregistrer dans chaque run la configuration effectivement consommée, pas seulement les
  arguments acceptés par `argparse`.

### Critères de clôture

- Une seule identité de classe et de constantes au runtime.
- Tests de propagation de tous les flags expérimentaux.
- Suppression des doubles affectations `globals()` / `_module_reel` devenue possible.
- Empreinte bit-identique du régime par défaut ou divergence explicitement documentée.

---

# 4. Instruments, dépouillement et statistiques

## MES-01 — Le dépouillement ne bloque pas toutes les campagnes invalides — ✅ CLOS (08/09/2026)

- **Priorité / statut** : **P0 — ✅ Clos** (v41.65, commit `54c1867`, CHANGELOG [v41.65])

### Preuves (audit initial, confirmé et étendu le 08/09)

Le registre citait `brains/06092026_epoques_nuit/depouiller.py`. L'audit a montré que le
défaut n'était pas dans **un** script mais dans **six**, copies successives les uns des
autres — `01092026_etape1_rendement`, `02092026_rejeu_banc_corrige`, `05092026_ablation_c2`,
`05092026_detach_c2`, `06092026_epoques_nuit`, `07092026_branches_persistantes` :

- les runs absents, vides ou inachevés sont exclus **en silence** (`for g in GRAINES if
  f'{bras}_g{g}' in E`), sans confronter le `n` réel au `n` prévu ;
- la couverture n'est qu'affichée ;
- le seuil `2.86` est fixe, y compris après retrait de quatre observations ;
- un garde-fou échoué affiche « CAMPAGNE INVALIDE » sans arrêter le script ;
- l'agrégat est écrit sans condition finale, code de sortie 0 ;
- `02092026` calcule deux vérifications pré-enregistrées (`temoin_aleatoire_conforme`,
  `saturation_budget`) **et les ignore** ;
- la fonction de lecture des journaux et ses expressions régulières sont recopiées dans
  quatre fichiers.

Cela ne démontre pas que l'agrégat publié était incomplet. Cela démontre que le script ne rend
pas cette situation impossible.

### Correction livrée

- `src/naulthene/instruments/depouillement.py` — `Manifeste` (protocole transcrit en JSON),
  `Depouillement` (collecte de la cohorte **entière**, garde-fous bloquants cible±tolérance
  **et** plancher, `exiger()` pour les données annexes, refus de publier, code de sortie),
  `Resultat` (verdict avec seuil affiché), `seuil_t` (quantile de Student **dérivé** de `n` et
  de la famille, en pur `math` — `scipy.stats` met > 60 s à s'importer dans ce venv).
- `src/naulthene/instruments/journal_cursus.py` — lecture unique des journaux de run.
- Mode **exploratoire** séparé : calcule tout, ne prononce aucun verdict, et n'écrit jamais
  `agregat.json` (seulement `agregat_exploratoire.json`).
- Six manifestes + six scripts migrés.

### Critères de clôture — vérifiés

| Critère | Preuve |
|---|---|
| Tests avec run manquant, run inachevé, garde-fou faux, `n` réduit | `tests/test_depouillement.py` — 33 tests, dont couverture, plancher, cohorte explicite, retrait des extrêmes |
| Aucun agrégat final écrit dans ces cas | épreuves sur données réelles : rollout `BP_g44` retiré → exit 1 ; `K8_NU_g55.log` tronqué à 900/1500 → exit 1 et `agregat.json` **binairement inchangé** |
| Rapport lisible des exclusions et de leur justification | `Depouillement.rapport()` nomme chaque run écarté, son motif, et distingue « prévue au manifeste » de « NON PRÉVUE » |
| Non-régression | re-dépouillement strict des 6 campagnes : tous les `δ`/`t` identiques, aucun verdict changé ; parité champ à champ **0 divergence / 60 runs** sur K8 |

### Ce que le re-dépouillement a appris (et qui n'était pas cherché)

1. 🟡 **`2,86` n'est pas le seuil annoncé.** Les campagnes déclarent « Bonferroni 3
   métriques » ; le seuil correspondant à `n = 20` est **2,625**, et 2,861 est celui de
   α = 0,01 (famille de 5). Le dépôt a été **plus sévère que sa pré-enregistration** —
   erreur conservatrice, aucun résultat à retirer, mais un choix à trancher (voir MES-04).
2. ✅ **Aucune campagne publiée n'était incomplète** : 60/60, 40/40, 60/60, 40/40, 20/20,
   40/40. Le risque était réel, il ne s'était pas réalisé.
3. Une « médiane » de `01092026` était `sorted(v)[len(v)//2]` (valeur haute pour `n` pair) :
   19,50× affiché pour 19,25× réel. Le carnet publiait déjà **19,25×** — l'outil était faux,
   pas le carnet ; verdict inchangé.

---

## MES-02 — La sonde des branches réimplémente toujours le rollout — ✅ CLOS (08/09/2026)

- **Priorité / statut** : **P0 — ✅ Clos** (v41.66, commit `48aa8a6`, CHANGELOG [v41.66])

### Preuves

`src/naulthene/instruments/sonde_horizon_branches.py ~3-5` affirme réutiliser le noyau sans
réimplémentation, mais les lignes `~29-50` recopient la transition du rollout. La sonde utilise
bien les couches de l'agent et suit `BRANCHES_PERSISTANTES`, mais n'appelle pas le rollout réel.
Elle impose également un contexte et un vecteur bio nuls dans un environnement forcé.

### Correction proposée

- Ajouter une trace observationnelle optionnelle au rollout réel ; ou
- extraire une primitive de transition mentale commune au noyau et à la sonde.

La trace doit être en lecture seule et ne jamais changer l'algorithme, les actions, l'horizon,
les tirages aléatoires ou le graphe utile à l'apprentissage.

### Critères de clôture

- Test d'invariance avec trace activée/désactivée.
- Test d'égalité des états intermédiaires entre sonde et noyau.
- Couverture des branches persistantes, du corps dans le rollout et de plusieurs horizons.
- Correction de la promesse documentaire.

### Clôture (08/09/2026, commit `48aa8a6`)

1. **Cause** : la sonde recopiait la boucle de rollout (sauts/horizons/argmax/corps) et
   imposait contexte et vecteur bio **nuls** — tout écart futur noyau/instrument l'aurait
   fait mentir (maladie de l'INSTRUMENT_01092026).
2. **Correction (option retenue : trace lecture seule)** : `trace_rollout=None` ajouté à
   `simuler_futur_et_planifier` (dernier argument, `None` = zéro instruction exécutée) ;
   au terme de chaque horizon la trace reçoit `pensee_branche`/`mem_branche`/
   `valeur_horizon` **détachés sous `no_grad`**. La sonde est réécrite : états réels
   (env, mémoire, contexte épisodique, corps au repos), **un seul appel** à la méthode
   canonique, séparation calculée sur les tenseurs observés. **Zéro boucle de rollout
   dans l'instrument.**
3. **Vérifications fraîches (CPU)** : A — jour K=8 réel corrigé vs d'origine : payload
   sémantique **0 différence** ; B — trace on/off : retour strictement identique
   (δ 0,0), collecteur remplit h1/h3/h7 ; C′ — `BRANCHES_PERSISTANTES` on/off
   discriminant (1,177 vs 0,009) ; C — cohorte BP 20 : médiane **1,0137** vs témoin K8
   **0,0073**.
4. **Entrée CHANGELOG** : [v41.66]. 🔴 **Requalification** : l'ancien protocole biaisait
   les niveaux absolus (BP 1,28 → 1,01 ; K8 0,0118 → 0,0073) ; le juge 3 BP re-dépouillé
   est **renforcé** (`t` +10,55 → +18,76, 20/20, extrêmes +19,31), tous les autres juges
   inchangés. Documents citant les anciens niveaux requalifiés (carnet BP, vitrines,
   CLAUDE.md, journal des runs).

---

## MES-03 — Les « parts du gradient » sont des parts de dispersion du signal

- **Priorité / statut** : **P1 — 🔴 Ouvert**

### Preuves

`docs/recherche/enquetes_closes/MIXAGE_04092026_les_termes_morts_ne_sont_pas_du_code_mort.md`
nomme « Part du gradient » les proportions calculées depuis `n`, `Σx`, `Σx²` et les écarts-types
des composantes de récompense. Cela mesure leur dispersion relative, pas leur contribution au
gradient ni au déplacement Adam.

La sonde de mixage des pertes mesure d'autres normes de gradient — JEPA, acteur, critique,
entropie — mais pas une attribution Bio contre Env et pas leurs directions ou annulations.

### Correction proposée

- Renommer les colonnes et conclusions : « part de la somme des écarts-types » ou formulation
  équivalente précisément définie.
- Si une attribution causale est nécessaire, concevoir une mesure de gradient par composante de
  récompense, avec directions, cosinus et déplacement effectif de l'optimiseur.
- Ne pas normaliser automatiquement les récompenses par leur écart-type.

### Critères de clôture

- Vocabulaire corrigé dans les documents normatifs et vitrines ; archives datées annotées sans
  effacer l'ancien texte.
- Instrument et formule documentés si une vraie attribution du gradient est produite.

---

## MES-04 — Le seuil appliqué contredit la famille de tests déclarée

- **Priorité / statut** : **P1 — 🟡 À décider** (constaté le 08/09/2026 pendant MES-01)

### Le fait

Quatre campagnes (`05092026_ablation_c2`, `05092026_detach_c2`, `06092026_epoques_nuit`,
`07092026_branches_persistantes`) écrivent dans leur `LISEZ_MOI.md` :

> ⚠️ **Bonferroni 3 métriques** ⇒ seuil `t` = **2,86**.

Or, pour `n` = 20 (df = 19), le seuil bilatéral de Bonferroni à 3 comparaisons vaut
**2,625**. **2,861** est le seuil de α = 0,01, c'est-à-dire d'une famille de **5**. Les deux
phrases de la même ligne ne désignent pas le même test.

### Conséquences mesurées

- L'erreur est **conservatrice** : elle n'a jamais transformé un résultat nul en résultat
  significatif. Elle a pu masquer un effet réel.
- Après retrait des 4 extrêmes (`n` = 16), le seuil correct de la famille 3 est **2,694**,
  toujours en dessous de 2,861 : là aussi le dépôt a été plus sévère qu'annoncé.
- **Aucun `t` du dépôt ne tombe dans la bande litigieuse.** Le plus proche est le juge 2 de
  K8 (niveau, `t` = **+2,52**, contre un seuil de 2,625) : près du seuil, toujours NS.

### La décision à prendre

| Option | Effet |
|---|---|
| **A — famille de 3 assumée** (2,625 / 2,694) | cohérent avec les LISEZ_MOI ; desserre légèrement le critère des campagnes futures |
| **B — α = 0,01 assumé** (2,861 / 2,947) | conserve le comportement historique ; il faut alors corriger la phrase « Bonferroni 3 métriques » partout |

Les manifestes livrés en v41.65 transcrivent la famille **déclarée** (option A) parce qu'un
manifeste transcrit un protocole, il ne le réécrit pas. ⚠️ **Tant que ce point n'est pas
tranché, ne requalifier en « significatif » aucun résultat qui ne passait pas 2,86.**

### Critères de clôture

- Option choisie, écrite une seule fois, et reportée dans les manifestes.
- Vérification qu'aucun verdict publié ne bascule sous l'option retenue (déjà fait pour A).

---

## EVA-01 — L'évaluation principale est trop bruitée et dépend du cursus

- **Priorité / statut** : **P1 — 🔵 À mesurer**

### Constat

Le dépôt documente que la maîtrise sur une fenêtre de 20 épisodes est quantifiée par pas de 5 %,
que le niveau atteint peut saturer et que la compétence au banc varie fortement à maîtrise égale.
Une promotion change aussi la carte finale sur laquelle la maîtrise est lue.

### Amélioration proposée

À la fin de chaque campagne confirmatoire :

1. geler l'apprentissage ;
2. évaluer tous les cerveaux sur les mêmes cartes et les mêmes graines ;
3. inclure la carte du blocage et le palier suivant ;
4. reporter succès, retour, longueur normalisée et intervalles d'incertitude ;
5. conserver niveau et maîtrise comme mesures de développement, non comme seuls juges finaux.

### Critères de clôture

- Protocole standard versionné.
- Banc final obligatoire dans les nouvelles campagnes majeures.
- Séparation claire entre graines d'entraînement et d'évaluation.

---

# 5. API, tests et persistance

## API-01 — Le contrat positionnel de `penser()` est fragile

- **Priorité / statut** : **P1 — 🔴 Ouvert**

### Preuves

`noyau.py ~1617-1619` retourne un tuple de huit éléments. La valeur et la mémoire occupent des
positions différentes et un banc a historiquement lu `[1]` au lieu de `[4]`, retirant en silence
la mémoire de travail. Les consommateurs examinés utilisent aujourd'hui l'index corrigé : il ne
s'agit pas d'un bug actif démontré.

### Correction proposée

- Introduire une sortie nommée (`NamedTuple`, dataclass ou objet compatible avec le déballage
  historique).
- Migrer les consommateurs vers les noms.
- Faire échouer bruyamment toute forme ou dimension inattendue.

### Critères de clôture

- Test de compatibilité avec le déballage existant pendant la migration.
- Aucun nouvel accès numérique dans les instruments.
- Tests des champs et de leurs formes.

---

## QUA-01 — Pas de petite suite de tests automatisés ni de CI

- **Priorité / statut** : **P1 — 🔴 Ouvert**

### Constat

Le README déclare qu'il n'existe ni suite de tests ni CI. Le dépôt possède des expériences et
pré-vols utiles, mais ils ne remplacent pas des tests rapides des contrats logiciels.

### Première suite recommandée

Tests CPU, courts et sans entraînement long :

1. parité collecte/rejeu selon le contrat APP-01 ;
2. propagation et composition des flags ;
3. gradients detach K=1/K>1 ;
4. sorties et formes de `penser()` ;
5. invariance des traces instrumentales ;
6. promotion et remappage par `env_id` ;
7. sauvegarde/chargement d'un cerveau courant ;
8. fixtures de migrations historiques ;
9. greffe suivie d'une nuit complète ;
10. réinitialisation des compteurs aux frontières jour/épisode.

### Critères de clôture

- Commande unique documentée.
- Suite exécutée en CI sur CPU.
- Temps compatible avec chaque commit.
- Les campagnes longues restent nécessaires pour les hypothèses cognitives.

---

## PER-01 — Une migration permissive peut masquer une anomalie de checkpoint

- **Priorité / statut** : **P1 — 🟠 À reproduire**

### Preuves

`src/naulthene/cerveau/persistance.py` accepte des chargements `strict=False`, exclut certaines
couches incompatibles et peut réinitialiser l'optimiseur après une greffe. Cette flexibilité est
nécessaire aux anciens `.brain`, mais une incompatibilité non prévue peut devenir un cerveau
partiellement réinitialisé plutôt qu'une erreur bloquante.

Aucun checkpoint corrompu n'a été observé pendant cet audit.

### Correction proposée

- Registre explicite des migrations connues, version source → version cible.
- Chargement strict par défaut hors migration reconnue.
- Rapport structuré listant chaque tenseur recopié, greffé, rejeté ou réinitialisé.
- Option explicite pour accepter une migration destructive.

### Critères de clôture

- Fixtures représentatives d'anciens cerveaux.
- Test de rejet d'une incompatibilité inconnue.
- Test d'une migration connue jusqu'à une nuit complète.

---

## PER-02 — Écriture atomique, mais temporaire partagé entre écrivains

- **Priorité / statut** : **P2 — 🟠 À reproduire**

### Preuves

La persistance écrit dans `<brain>.tmp`, puis utilise `os.replace`. Le remplacement atomique
existe bien. Deux processus écrivant le même cerveau partageraient toutefois le même temporaire,
et le chemin examiné ne garantit pas une synchronisation disque complète.

Aucun incident de concurrence ou de coupure n'est établi.

### Correction proposée

- Temporaire unique par processus/opération.
- Verrou d'écriture sur un même checkpoint.
- `flush`/`fsync` si la durabilité après coupure est une exigence.
- Conservation vérifiée de la dernière version valide.

### Critères de clôture

- Tests de concurrence et d'injection de panne.
- Le checkpoint précédent reste chargeable après interruption simulée.

---

# 6. Documentation et reproductibilité

## DOC-01 — L'état courant est noyé dans l'historique et contient des contradictions

- **Priorité / statut** : **P1 — 🔴 Ouvert**

### Exemples à corriger ou requalifier

1. Certaines phrases du README affirment encore que seuls des leviers du monde ont fonctionné,
   malgré les résultats récents sur voix libre, detach C2 et K8.
2. Une roadmap mentionne encore comme en cours un rejeu documenté comme terminé.
3. Le ratio `1 321 618 / 46 840` vaut environ **28,2×**, pas ~24× ; le périmètre des paramètres
   appris et des buffers doit être explicité partout.
4. « Franchir le niveau 5 » est ambigu quand les cerveaux atteignent le niveau affiché 5 après
   avoir franchi le niveau 4.
5. Le noyau actuel promeut par une maturité composée
   (`_maturite_niveau`, puis `maturite >= SEUIL_MATURITE`), alors que certaines présentations de
   l'état courant reprennent encore l'ancienne règle « deux victoires OU 60 % ». Les sections
   historiques datées doivent rester historiques, pas être réécrites comme si elles avaient
   toujours été fausses.
6. Les numéros de niveau doivent toujours être accompagnés de l'`env_id`.

### Correction proposée

- Créer un `ETAT_COURANT.md` court, remplacé explicitement après chaque résultat majeur.
- Réserver le CHANGELOG et les carnets à l'histoire et aux rétractations.
- Garder les README EN/FR courts, factuels et strictement synchronisés.
- Réduire les instructions de travail aux invariants et liens.
- Employer partout `niveau N/15 (env_id)` et « atteint »/« résout » sans ambiguïté.

### Critères de clôture

- Audit croisé README EN/FR, CHANGELOG, INDEX et état courant.
- Recalcul automatique ou script versionné pour les nombres dérivés importants.
- Aucune archive historique effacée ; corrections annotées selon la règle de trace.

---

## REP-01 — Environnement d'installation insuffisamment verrouillé

- **Priorité / statut** : **P2 — 🔴 Ouvert**

### Constat

Le README propose des installations `pip` sans versions et le lancement via `PYTHONPATH=src`.
L'audit ciblé n'a pas trouvé de `pyproject.toml` à la racine. Aucun échec d'installation vierge
n'a toutefois été reproduit.

### Correction proposée

- Définir la version Python supportée et les dépendances du cœur.
- Ajouter des extras pour audio, visualisation, serveur et instruments.
- Fournir un fichier de contraintes ou lock de référence.
- Enregistrer avec chaque campagne : commit, Python, Torch, MiniGrid, Gymnasium, device et flags.

### Critères de clôture

- Installation dans un environnement vierge.
- Import minimal et test CPU réussis.
- Manifeste d'environnement joint aux nouvelles campagnes.

---

## ARC-01 — La source de vérité `noyau.py` / `colab.py` n'est pas décidée

- **Priorité / statut** : **P2 — 🟡 À décider**

### Constat

La documentation nomme encore `colab.py` script de référence alors que l'essentiel de
l'évolution et des campagnes récentes vit dans `noyau.py`. Une référence très en retard n'est
plus une référence reproductible.

### Options

1. **Recommandée** : déclarer `noyau.py` source de vérité ; `colab.py` devient une archive datée
   ou un simple point d'entrée compatible Colab.
2. Porter régulièrement le noyau vers Colab avec un test de parité obligatoire.
3. Extraire un cœur partagé et garder deux points d'entrée minces.

### Critères de clôture

- Décision écrite dans la documentation normative.
- Une seule implémentation cognitive active, ou test automatique de parité.
- Commandes de lancement mises à jour.

---

# 7. Chantiers scientifiques à programmer après les P0/P1

## SCI-01 — Déterminer la forme de l'effet du nombre d'époques

- **Priorité / statut** : **P2 — 🔵 À mesurer**

K=8 a amélioré la maîtrise dans une campagne documentée. Cela n'établit ni l'optimum, ni une loi
monotone, ni une valeur adaptée à chaque cerveau.

### Protocole recommandé

Après correction d'APP-01/APP-02 :

- mesurer plusieurs K autour de 8 ;
- suivre performance, KL, ratios, entropie, stabilité, temps et surapprentissage ;
- utiliser de nouvelles graines pour la validation finale ;
- dériver ensuite une règle adaptative seulement si la forme fixe est comprise.

### Clôture

Une règle de nombre de passes est soit dérivée d'une grandeur vécue et validée hors échantillon,
soit maintenue comme hyperparamètre expérimental explicitement posé.

---

## SCI-02 — Comparer Naulthène et PPO sous plusieurs budgets explicites

- **Priorité / statut** : **P2 — 🔵 À mesurer**

Aucun budget unique ne rend automatiquement les architectures comparables.

### Comparaisons à séparer

- même nombre d'interactions environnementales ;
- même temps mural sur matériel identique ;
- même mémoire maximale ;
- même budget de paramètres entraînables ;
- courbes échantillons-performance, pas seulement un point final.

Les organes supplémentaires de Naulthène doivent être comptés deux fois : comme coût total du
cerveau complet, et dans une ablation permettant d'estimer leur valeur marginale.

---

## SCI-03 — Diagnostiquer la neurogenèse globale et les activations mortes

- **Priorité / statut** : **P2 — 🔵 À mesurer**

Le dépôt rapporte une croissance forte, beaucoup d'activations toujours nulles et des couches
inactives qui grandissent malgré l'absence de gradient sur le cursus joué.

### Ordre recommandé

1. Déterminer si les unités sont nulles dès la naissance ou le deviennent.
2. Mesurer la fraction nulle après chaque nuit et chaque neurogenèse.
3. Distinguer ReLU inactive, érosion, données hors domaine et véritable absence d'usage.
4. Seulement ensuite tester un témoin à `dim_bus` fixe.

Ne pas conclure qu'une unité ReLU nulle est une « synapse morte » : poids, activation et utilité
causale sont trois grandeurs différentes.

---

## SCI-04 — Trancher le rôle causal du corps dans l'apprentissage de la tâche

- **Priorité / statut** : **P2 — 🔵 À mesurer**

Le ratio Bio/Env actuellement publié décrit des dispersions, pas une causalité. La corrélation
maîtrise-énergie a été réfutée, mais cela ne mesure pas l'effet d'une autre échelle du signal Bio.

### Protocole recommandé

- définir l'échelle candidate à partir d'une grandeur corporelle ou mondiale mesurable ;
- conserver un témoin fossile ;
- vérifier que l'ablation varie réellement sur la carte jouée ;
- mesurer performance de tâche **et** viabilité corporelle ;
- refuser une « amélioration » qui résout MiniGrid en supprimant simplement l'organisme.

---

## SCI-05 — Reporter la tête d'intention C2 jusqu'à validation de ses entrées

- **Priorité / statut** : **P3 — 🟡 À décider**

La tête d'intention reste cohérente avec la thèse du projet, mais elle dépend de futurs :

- distincts ;
- suffisamment fidèles au monde réel ;
- mieux classés que le hasard ;
- exploitables par l'apprenant corrigé.

### Conditions avant implémentation

1. MES-02 clos : mesure prise sur le vrai rollout. *(✅ clos 08/09/2026, `48aa8a6` — sonde sur trace)*
2. Fidélité multi-horizon mesurée, pas seulement séparation géométrique.
3. APP-01/APP-02 clos : politique et gradient cohérents.
4. Campagne de soustraction réalisée sous le meilleur apprenant connu.
5. Critère d'ablation propre de la future tête défini avant le code.

---

# 8. Ordre opérationnel recommandé

## Phase A — zéro campagne longue

1. ✅ APP-01 : test de parité collecte/rejeu et définition du contrat. *(v41.64)*
2. ✅ APP-02 : test de gradient K + detach. *(v41.64)*
3. ✅ MES-01 : rendre le dépouillement strict. *(v41.65)*
4. ✅ **MES-02 : supprimer la duplication instrument/noyau.** *(v41.66, `48aa8a6`)*
5. MES-04 : trancher la famille de tests (2,625 déclaré contre 2,861 appliqué).
6. API-01 et QUA-01 : installer la première suite de contrats — **amorcée** par `tests/`
   (40 tests stdlib) livré avec MES-01 ; reste à couvrir `penser()` et à installer la CI.
7. DOC-01 : corriger l'état courant et les termes statistiques.

## Phase B — fiabilisation structurelle

7. APP-03 : module/configuration uniques.
8. PER-01/PER-02 : migrations et sauvegardes.
9. REP-01/ARC-01 : environnement et source de vérité.
10. EVA-01 : banc final standardisé.

## Phase C — campagnes

11. SCI-01 : balayage des époques après correction du rejeu.
12. Combinaison voix libre + detach C2 + meilleur régime d'époques.
13. Campagne de soustraction : facultés complètes contre cœur minimal, sur un apprenant stabilisé.
14. SCI-03 et SCI-04 selon les résultats.
15. SCI-05 seulement si le rollout et l'utilité de C2 le justifient encore.

---

# 9. Tableau de suivi des corrections

À remplir sans supprimer les anciennes lignes :

| Date | ID | Nouveau statut | Commit / carnet | Vérification | Note |
|---|---|---|---|---|---|
| 2026-09-08 | Tous | Registre créé | — | Audit statique ciblé | Aucun effet dynamique nouvellement établi |
| 2026-09-07 | APP-01 | ✅ Clos | `6d6bcaa` · CHANGELOG [v41.64] | T1 CPU : parité de formule 32 régimes × 2 (delta ≤ 1,5e-8) ; K=8 réel 0 violation du garde de forme | Rejeu sur politique complète (C1+C2), contexte k1/k2 figé par tick |
| 2026-09-07 | APP-02 | ✅ Clos | `6d6bcaa` · CHANGELOG [v41.64] | T2 CPU : grad critique `integrateur_bio` 2,891 → 0,000 (detach) ; K=8 + detach réel exit 0 | Détachement du critique appliqué sur chaque passe |
| 2026-09-08 | MES-01 | ✅ Clos | `54c1867` · CHANGELOG [v41.65] | 40 tests `unittest` verts ; épreuves réelles : rollout retiré → exit 1, log tronqué 900/1500 → exit 1 et agrégat binairement inchangé ; re-dépouillement des 6 campagnes, 0 verdict changé, parité champ à champ 0/60 divergence | Primitive `depouillement.py` + `journal_cursus.py` + 6 manifestes ; 6 scripts migrés |
| 2026-09-08 | MES-02 | ✅ Clos | `48aa8a6` · CHANGELOG [v41.66] | A : payload sémantique 0 diff (K=8 réel) · B : trace on/off δ 0,0 · C′ : 1,177 vs 0,009 · C : BP médiane 1,0137 vs K8 0,0073 | Trace `trace_rollout` + sonde réécrite sans boucle ; **juge 3 BP requalifié** (t +10,55 → +18,76, autres juges inchangés) |
| 2026-09-08 | MES-04 | 🟡 À décider | — | Constatée pendant le re-dépouillement MES-01 | La famille déclarée (3 métriques ⇒ 2,625) contredit le seuil appliqué (2,861 = α 0,01) ; erreur conservatrice, aucun résultat retiré |

---

## 10. Résumé de décision

Le dépôt possède désormais des leviers d'apprentissage mesurés, mais leur combinaison et leur
interprétation dépendent encore de contrats logiciels qui ne sont pas automatisés. La meilleure
séquence n'est donc pas d'ajouter immédiatement un nouvel organe :

> **faire correspondre la politique collectée, la politique rejouée, les gradients, les sondes
> et les statistiques ; stabiliser ensuite l'apprenant ; enfin mesurer la valeur marginale de
> chaque faculté cognitive.**

Cette séquence ne réduit pas Naulthène à MiniGrid. Elle crée les conditions nécessaires pour
savoir si un organe cognitif aide réellement un cerveau capable d'apprendre.
