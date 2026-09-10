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
| API-01 | P1 | ✅ Clos | Le tuple positionnel de `penser()` est fragile | Corrigé v41.67 (`87b8967`) — `SortiePenser` (NamedTuple) |
| MES-03 | P1 | 🔴 Ouvert | Des dispersions de récompense sont présentées comme parts du gradient | Corriger le vocabulaire et mesurer séparément |
| MES-04 | P1 | ✅ Clos | Le seuil `2,86` appliqué contredisait la famille de 3 métriques déclarée (2,625) | Décidé 08/09 : famille de 3, α = 0,05 ⇒ `t` = 2,625 (n=20) / 2,694 (n=16) |
| QUA-01 | P1 | ✅ Clos | Absence de petite suite automatisée (CI : en attente d'infra) | Clos v41.70 — **44 tests CPU** (`test_contrats_cognitifs.py`) : API-01, APP-01, APP-02, MES-02 + 40 MES-01 ; commande unique documentée |
| EVA-01 | P1 | 🔵 À mesurer | Le juge principal est bruité et dépend du palier atteint | Banc final standard sur cartes fixes |
| DOC-01 | P1 | ✅ Clos | L'état courant et l'historique se contredisent dans la documentation | Clos v41.71 — `ETAT_COURANT.md` unique + INDEX nettoyé + miroir EN/FR vérifié |
| PER-01 | P1 | 🟠 À reproduire | Le chargement permissif peut masquer une anomalie comme migration | Migrations explicites, strictes hors cas connus |
| REP-01 | P2 | 🔴 Ouvert | Installation et versions non verrouillées | v41.73 + v41.75 — pyproject + lock + spec + script `verifier_environnement.sh` prêts ; clôture = exécution env vierge (après SCI-01 Wave 2) |
| PER-02 | P2 | 🟠 À reproduire | Deux écrivains peuvent partager le même fichier temporaire de checkpoint | Temporaire unique, verrou, test d'incident |
| SCI-01 | P2 | 🔵 À mesurer | K=8 est un point favorable, pas un optimum ni une valeur dérivée | Wave 1 dépouillée (09/09) : cloche 0/0/8/10/3, optimum K=8, clip inerte ; Wave 2 (n=20) pour le verdict |
| SCI-02 | P2 | 🔵 À mesurer | Le benchmark PPO n'est pas égalisé selon tous les budgets | Comparaisons séparées interactions/calcul/mémoire |
| SCI-03 | P2 | 🔵 À mesurer | La neurogenèse globale produit beaucoup de capacité inactive | Trajectoire des activations puis témoin à taille fixe |
| SCI-04 | P2 | 🔵 À mesurer | Le ratio Bio/Env est non tranché et mal nommé « gradient » | Mesure causale avec échelle dérivée |
| SCI-05 | P3 | 🟡 À décider | La tête d'intention C2 serait construite avant validation complète de ses entrées | Reporter après fidélité du rollout et ablations |
| ARC-01 | P2 | ✅ Clos | `colab.py` reste nommé référence alors que le développement réel vit dans `noyau.py` | Décidé 08/09 (v41.72) : `noyau.py` source de vérité unique, `colab.py` = archive v17 |
| VIS-01 | P3 | ✅ Clos | Le cerveau n'est observable qu'à plat (courbes, barres, heatmap) : sa structure spatiale, sa croissance et ses neurones morts ne se voient pas | **Livré le 10/09/2026** — IRM 3D vivante (`cerveau_3d`) + drapeau `--telemetrie-3d` dans `noyau.py`, documentés dans [`LANCEMENT.md` §7bis](../fonctionnement/LANCEMENT.md). Preuves : run **bit-identique** sans le drapeau (A/A 5 j + 3 paires de 50 j), empreinte SHA-256 du `.brain` **inchangée** après 5 579 ticks observés, **surcoût mesuré à +7,87 % de temps / −7,30 % de débit**, et **étape 2 vérifiée de bout en bout** (tâche 11 : `/structure` = **12 couches, `dim_bus` 68, `sequence_structure` 6** — `brains/VIS01_etape2_fichier_10092026/`). ⚠️ Cette ligne annonçait « 🟠 Livré en partie » et « **Reste** : le serveur ne relit pas `<brain>.vis01_structure.json` ⇒ la page attend la structure en `--serveur-seul` » : **fait** le 10/09/2026 (`--structure-fichier`, tâche 11) — ancien énoncé consigné dans la rétractation §VIS-01 |
| DOC-02 | P2 | 🟠 Corrigé (clôture suspendue) | La garantie « ne modifie aucun poids » de `irm_cerveau.py` et `lancer_arene.py` est **inexacte** : `fortifier_synapses` écrit sous `no_grad`, sans `backward()` | Docstrings corrigées 10/09 (mesure : trace nulle ⇒ écriture nulle) ; **entrée CHANGELOG en attente** de la décision de version (voir la section DOC-02) |
| DOC-03 | P2 | 🟠 Corrigé en partie | L'en-tête de version de `noyau.py` retardait de 7 versions, la tête du CHANGELOG n'était pas dans l'ordre décroissant, et **deux entrées distinctes portent le même numéro v41.71** (v41.70 manquant) | Décision de l'auteur (10/09) : **le CHANGELOG fait foi** → en-tête porté à **41.75**, tête du CHANGELOG remise en ordre décroissant ; reste à trancher le titre de l'entrée QUA-01 (voir la section DOC-03) |

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

## MES-04 — Le seuil appliqué contredisait la famille de tests déclarée — ✅ CLOS (décision 08/09/2026)

- **Priorité / statut** : **P1 — ✅ Clos (décision)** — famille déclarée de **3** métriques,
  α = 0,05 ⇒ `t` = **2,625** (n=20, df=19) et **2,694** (n=16 après retrait des extrêmes).
  Le résidu conservateur 2,861 (α = 0,01) est abandonné : ce n'était pas une convention,
  c'était un écart non documenté.

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

### La décision (prise le 08/09/2026 — option A)

**Famille de 3 assumée, α = 0,05** : seuils `t` = **2,625** (n = 20) et **2,694** (n = 16),
dérivés par `depouillement.seuil_t` (v41.65). C'est la valeur exacte de la règle déclarée
dans les LISEZ_MOI. Le résidu conservateur 2,861 (α = 0,01, famille de 5) est **abandonné** :
ce n'était pas une convention, c'était un écart non documenté — conserver l'écart parce qu'il
est conservateur reviendrait à documenter une faute de frappe comme une politique.

**Conséquences** : aucun verdict publié ne bascule (aucun `t` dans la bande litigieuse — le
plus proche, le juge 2 de K8, vaut +2,52 < 2,625, toujours NS). Les manifestes transcrivent
déjà la famille 3 (v41.65) et les dépouillements affichent déjà les seuils dérivés 2,63/2,69.

### Critères de clôture — vérifiés

- Option choisie, écrite une seule fois, reportée dans les manifestes : ✅ (manifestes v41.65,
  familles `comparaisons_prevues` = 3, α = 0,05).
- Aucun verdict publié ne bascule sous l'option retenue : ✅ vérifié (aucun `t` dans la bande
  [2,625 ; 2,861)).

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

## VIS-01 — Le cerveau n'est observable qu'à plat (chantier d'instrument)

- **Priorité / statut** : **P3 — ✅ Clos** (10/09/2026). Les tâches du plan sont closes, et la
  **dernière** — la relecture du fichier de structure par le serveur du spectateur — a été livrée
  par la tâche 11 (`2fad056` + `433cc14`) : l'étape 2 est **vérifiée de bout en bout**. ⚠️ Clôture
  **sans** entrée CHANGELOG : la tâche 11 ne touche pas `noyau.py` (fichiers livrés :
  `cerveau_3d/serveur.py`, `cerveau_3d/__main__.py`, `tests/test_cerveau_3d.py`) — la portée et les
  limites du résultat vivent donc dans le carnet de campagne
  (`brains/VIS01_etape2_fichier_10092026/LISEZ_MOI.md`), ce qu'admet l'élément 4 de la règle de
  clôture (« entrée CHANGELOG **ou** carnet »).
- **Nature** : capacité manquante, pas un défaut. Enregistré ici parce que la spec portait **deux
  découvertes** qui, elles, étaient des défauts (voir « Découvertes » ci-dessous — les deux sont
  désormais traitées sous `DOC-02` et `DOC-03`).

### Constat

Le cerveau dispose de deux instruments de rendu, tous deux **à plat** : `arene_visuelle.py`
(image MiniGrid + jauges + bande d'activations) et `irm_cerveau.py` (activations, myéline,
variance du bus). Aucun ne montre la **structure** : 12 couches, 220 255 synapses, croissance par
neurogenèse, neurones fonctionnellement morts (**56 %** de `pensee_bio`, mesuré sur 40/40
cerveaux). Aucun ne peut être branché sur un **run en cours** : la télémétrie par tick ne contient
que `dopamine`, `faim` et `parametres_vocaux`.

### Ce qui a été livré (10/09/2026)

Chantier **VIS-01** ([`CHANTIER_VIS-01_cerveau_3d_irm_vivante.md`](CHANTIER_VIS-01_cerveau_3d_irm_vivante.md)) : IRM 3D vivante
rendue en **three.js vendorisé**, alimentée par un **rapporteur par forward hooks** en lecture
seule (discipline MES-02), servie par un **serveur stdlib** (aucune dépendance ajoutée).
Commandes d'usage : [`LANCEMENT.md` §7bis](../fonctionnement/LANCEMENT.md).

| Étape | Contenu | Impact sur `noyau.py` | État |
|---|---|---|---|
| 0 | démonstration, source factice | aucun | ✅ `--source factice` |
| 1 | spectateur-pilote sur un vrai `.brain`, lecture seule | aucun | ✅ `--source cerveau --brain …`, empreinte SHA-256 imprimée à l'arrêt |
| 2 | passerelle UDP + fichier de structure + drapeau `--telemetrie-3d` | **oui** — additif, éteint par défaut, test bit-identique exigé | ✅ **COMPLET** (tâche 11) : le run émet (activité + événements, **0 perdu**) **et** écrit sa structure, que le serveur **relit** (`--structure-fichier`) — `/structure` rend **12 couches, `dim_bus` 68**, `sequence_structure` **6**. ⚠️ Cette ligne disait « 🟠 **EN PARTIE** : le run émet (activité + événements, **0 perdu**) et écrit sa structure ; **le serveur ne relit pas le fichier de structure** » — ancien énoncé consigné dans la rétractation ci-dessous |

### Les quatre éléments de la règle de clôture

1. **Cause / décision explicitée** : le cerveau n'était observable qu'à plat — aucune capacité de
   rendu **structurel**. Décisions de cadrage du 10/09 : rendu Web/three.js vendorisé, sujet =
   activité tick par tick, disposition = plaques stratifiées + colonne du bus, spectateur
   **strictement en lecture seule**, aucun mode « vivre ».
2. **Correction / changement documentaire référencé** : commits `8eb7830` → `3281f3e` (page,
   serveur, rapporteur, spectateur-pilote, source factice, drapeau dans `noyau.py`) puis la clôture
   documentaire ; **tâche 11 (`2fad056` code + tests, `433cc14` traces)** : le serveur **relit**
   `<brain>.vis01_structure.json` (`--structure-fichier`, veilleur dédié) ; spec à jour avec ses
   **avenants** (transport de `structure`, relecture livrée, bornes comptées) ; usage documenté dans
   `LANCEMENT.md` §7bis. ⚠️ **`INDEX.md` n'est PAS à jour** : sa ligne VIS-01 (l. 158) affirme
   encore « un fichier que **le serveur ne relit pas encore** (étape 2 partielle) » — **hors des
   trois fichiers autorisés** de ce tour de correction documentaire, donc **signalé ici plutôt que
   corrigé en silence** (à reprendre au prochain passage sur `INDEX.md`).
3. **Vérification fraîche (reproduite le 10/09/2026)** :
   - **Le drapeau ne change rien au run** : `diff` des niveaux promus **vide** sur l'A/A (5 jours,
     `brains/VIS01_preuve/LISEZ_MOI.md`), **re-mesuré par la clôture sur 3 paires de 50 jours**
     (20 000 ticks) — `diff` vide, **`dim_bus` final identique (71)**.
   - **Empreinte** : le `.brain` observé n'est jamais ouvert en écriture (SHA-256 avant/après en
     mode spectateur ; `sha256 74553e6e…` inchangée après 5 579 ticks) ; les deux `.brain` de l'A/A
     sont identiques au contenu (97 tenseurs `torch.equal`, archive au même SHA-256).
   - **Surcoût du rapporteur, chiffré** (jamais estimé) : **364,0 ticks/s sans le drapeau contre
     337,4 avec**, soit **+7,87 % de temps de boucle / −7,30 % de débit** — 3 paires entrelacées de
     50 jours partant du même cerveau copié à la même graine, dispersion intra-bras 0,47–1,55 %
     (`brains/VIS01_surcout_10092026/LISEZ_MOI.md`). **Minorant** : mesuré à `bus = 32 → 71`.
   - **Le canal tient la cadence** : avec un serveur réel, **81 datagrammes envoyés / 0 perdu**,
     **13 trames d'activité + 68 événements reçus**, page servie en HTTP 200.
   - **Étape 2 de bout en bout (tâche 11, `brains/VIS01_etape2_fichier_10092026/`)** : serveur
     lancé **avant** le run (fichier **absent** au démarrage), run réel de 60 jours à la graine 11,
     une interrogation par seconde (`poll_structure.txt`, 111 lignes) — `/structure` passe de `{}`
     à **12 couches**, `dim_bus` **16 → 68**, `sequence_structure` **0 → 6**, compteurs
     `illisibles 0`, `invalides 0` ; **4 trames `structure`** poussées sur le flux SSE, **en tête de
     flux**, sans redémarrer le serveur. Le run écrit **11** structures, le serveur en publie **6**
     (deux neurogenèses dans la même seconde ⇒ la dernière seule) : **limite écrite d'avance**, pas
     découverte après coup.
   - **Suite de tests** : **147 tests OK** (138 + 9) —
     `NAULTHENE_DEVICE=cpu PYTHONPATH=src venv/bin/python3 -m unittest discover -s tests`, 28–30 s ;
     aucun test existant modifié (`+429 / −0` dans `tests/test_cerveau_3d.py`).
4. **Entrée CHANGELOG** : `[v41.76] - 2026-09-10 — VIS-01 tâche 9 : la passerelle
   --telemetrie-3d` (portée, preuves, et limite : le surcoût n'était alors pas mesuré). Le journal
   des runs porte les **trois** campagnes : `VIS01_preuve` (A/A), `VIS01_surcout_10092026` et
   `VIS01_etape2_fichier_10092026`. ⚠️ **La tâche 11 n'a PAS d'entrée CHANGELOG propre** : elle ne
   touche pas `noyau.py` — la portée et les limites du résultat vivent dans le carnet
   `brains/VIS01_etape2_fichier_10092026/LISEZ_MOI.md` (§4 limites écrites d'avance, §5 chiffres
   bruts, §6 ce que cela ferme), ce qu'admet l'alternative « **ou carnet** » de cet élément.

### 🔴 Rétractation du 10/09/2026 — ce qui était écrit ci-dessus a été démenti par le code livré

*(tâche 11 ; ancien énoncé en regard, dogme « rien sans écrit »)*

| Énoncé publié dans ce registre | ❌ FAUX — re-mesuré le 10/09/2026 (tâche 11) | Corrigé en |
|---|---|---|
| « 🔴 **Le lien manquant de l'étape 2** : … **aucun code ne le relit** (`grep -rn "vis01_structure" src/` ne rend que `noyau.py`) » | `grep -rn "vis01_structure" src/` rend désormais **`noyau.py`** (l'émetteur), **`cerveau_3d/serveur.py`** (`VeilleurStructureFichier`) et **`cerveau_3d/__main__.py`** (`--structure-fichier`). Le fichier est relu **au démarrage** puis **à chaque changement** | « le serveur relit le fichier de structure » |
| « En `--serveur-seul`, `/structure` rend `{}` et `sequence_structure` reste `0` — mesuré » | Vrai **sans** l'option, faux **avec** : mesuré `{}` → **12 couches** et `0` → **6** pendant un run vivant (`poll_structure.txt`) | « `/structure` rend 12 couches, `dim_bus` 68, `sequence_structure` 6 » |
| « Il manque un chemin de lecture … `cerveau_3d/serveur.py` + `cerveau_3d/__main__.py`, **hors des fichiers autorisés de la clôture** » | Ces deux fichiers ont été livrés (+ 9 tests) — le « manque » était une limite de **périmètre** (liste de fichiers close), pas une impossibilité technique | « livré : `serveur.py` + `__main__.py` + 9 tests » |
| Vue d'ensemble (l. 74) : « VIS-01 … 🟠 **Livré en partie** … **Reste** : le serveur ne relit pas `<brain>.vis01_structure.json` ⇒ la page attend la structure en `--serveur-seul` » | L'étape 2 est **complète** ; le statut est passé à **✅ Clos** | « ✅ Clos — étape 2 vérifiée de bout en bout » |

Le reste de ces constats n'est **pas** touché : le run était bien bit-identique sans le drapeau, le
surcoût bien de **+7,87 %** (minorant, `bus = 32 → 71`), et les limites de mesure ci-dessous restent
vraies.

### Ce qui reste ouvert (pour ne pas clore à tort)

- ✅ **Le lien manquant de l'étape 2 — FAIT (10/09/2026, tâche 11)** : le run écrit
  `<brain>.vis01_structure.json` et le serveur le **relit** (`--structure-fichier`, qui exige
  `--serveur-seul`), au démarrage puis à chaque changement. Ancien énoncé conservé dans la
  rétractation ci-dessus (« aucun code ne le relit »).
- Le surcoût n'est **pas** mesuré à `dim_bus = 145` (c'est l'encodage des trames qui grossit avec le
  bus), ni sous charge machine, ni avec un navigateur connecté. Idem pour le **coût de la veille du
  fichier** : obtenu **par construction** (fil séparé, 1 `stat`/s, aucun accès disque sur la voie
  chaude) et **témoigné** par l'e2e, jamais chiffré en % de CPU.
- **Le rendu three.js réel n'est pas prouvé** (aucun navigateur ouvert) : ce qui est vérifié est le
  **transport** (SSE, HTTP 200), pas l'image.
- **Quatre écarts de revue (M-1 à M-6 de la tâche 9)** restent ouverts : canal `evenement` absent
  du chemin `vocal_isole`, clé `action` ajoutée au fichier de structure selon le chemin d'écriture,
  etc. — ils n'ont pas été traités par la clôture (liste de fichiers close).

### Découvertes faites au cadrage (hors périmètre VIS-01) — traitées

1. 🔴 **La garantie « ne modifie aucun poids » est inexacte** dans les docstrings
   d'`irm_cerveau.py` (l. 35-38) et de `lancer_arene.py` (l. 39-42). `traiter_tick` →
   `fortifier_synapses` (~10430) → `fortification_dopaminergique` (~176-189) **écrit en place,
   sous `no_grad`, dans `base_weight` et `myeline_M` — sans aucun `backward()`**. Mesuré sur
   `K4_NU_g11.brain` : `|trace_activation|max = 0,000e+00` sur les 12 couches, donc l'écriture est
   **numériquement nulle** pour tout `.brain` sauvegardé après une nuit (`cycle_sommeil` remet la
   trace à zéro, ~364). ⚠️ Elle **ne l'est pas** pour un `.brain` sauvegardé en pleine journée —
   cas réel : la **micro-sieste de la Cuve**. Le **fichier** n'est jamais modifié dans les deux cas.
   → suivi sous `DOC-02` (docstrings corrigées ; entrée CHANGELOG en attente).
2. 🟡 **Écart de version** : `noyau.py` déclarait `#Version actuelle 41.68` quand le CHANGELOG
   portait **v41.75** et `ETAT_COURANT.md` **v41.72** ; et la tête du CHANGELOG n'était pas dans
   l'ordre décroissant. → **tranché le 10/09** (`DOC-03`) : **le CHANGELOG fait foi**, l'en-tête de
   `noyau.py` est passé à **41.76** avec l'entrée `[v41.76]`.

### Critères de clôture (énoncés au cadrage — état)

- ✅ Étapes 0 et 1 livrées, empreinte du `.brain` observé **identique** avant/après, surcoût du
  rapporteur **mesuré et reporté**.
- ✅ Étape 2 : run **bit-identique sans le drapeau** (deux runs même graine, `diff` des promotions
  — et 3 paires de 50 jours à la clôture).
- ✅ Tests ajoutés et verts avec la commande unique existante (**147 OK** = 138 + 9) ; `LANCEMENT.md`
  documente l'instrument **et** les commandes copiables de l'étape 2 (`--structure-fichier`).
  ⚠️ Cette ligne disait « **fait**, mais l'étape 2 reste **partielle** (structure non relue par le
  serveur) » : l'étape 2 est **complète** depuis la tâche 11.

---

# 5. API, tests et persistance

## API-01 — Le contrat positionnel de `penser()` est fragile — ✅ CLOS (08/09/2026)

- **Priorité / statut** : **P1 — ✅ Clos** (v41.67, commit `87b8967`)

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

### Clôture (08/09/2026, commit `87b8967`)

1. **Cause** : tuple positionnel de 8 sorties, muet sur la sémantique de chaque position —
   confusion historique `[1]` (valeur) vs `[4]` (mémoire de travail), `INSTRUMENT_01092026`.
2. **Correction** : `SortiePenser(NamedTuple)` (v41.67) — ordre **inchangé**, accès numérique
   rétrocompatible, accès par nom (`out.memoire_actuelle`, `out.valeur_etat_courant`…)
   impossible à confondre à la racine.
3. **Vérification fraîche (CPU)** : type `SortiePenser` ; `index == nom` sur les **8** champs ;
   déballage 8-tuple OK ; `out[4] == out.memoire_actuelle`, `out[1] ==
   out.valeur_etat_courant`. Les instruments existants qui lisent par index restent valides
   (rétrocompatibilité) ; migration aux noms au fil de l'eau (QUA/DOC).
4. **Entrée CHANGELOG** : [v41.67].

---

## QUA-01 — Pas de petite suite de tests automatisés ni de CI — ✅ CLOS (08/09/2026)

- **Priorité / statut** : **P1 — ✅ Clos** (v41.70) — CI : dépend de l'infra, hors périmètre
  de cette clôture (pas d'hébergeur CI sur le dépôt ; la commande locale unique est livrée).

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

### Clôture (08/09/2026, v41.70)

1. **Cause** : aucune petite suite de contrats automatisée ; validation par pré-vols manuels.
2. **Correction** : `tests/test_contrats_cognitifs.py` (agent neuf CPU partagé par classe) —
   **API-01** : index == nom == déballage sur les 8 champs de `SortiePenser` ; **APP-01** :
   parité `penser()` vs `_logits_politique_complete_rejouee` sur **16 régimes** (SANS_C2 ×
   brain-sparing × corps-rollout × voix libre, force/vigueur variés, masque 8ᵉ vérifié) ;
   **APP-02** : gradient du critique vers `integrateur_bio` > 0 sans detach, **exactement
   0,000** avec `DETACH_C2_ASYMETRIQUE` ; **MES-02** : trace `None` = simulation inchangée,
   collecteur actif = horizons 1/3/7 capturés sans modifier le retour.
3. **Vérification fraîche (CPU)** : **44 tests OK en 2,1 s** (40 MES-01 + 4 nouveaux) —
   `NAULTHENE_DEVICE=cpu venv/bin/python -m unittest discover -s tests`.
4. **CI** : non installée (pas d'hébergeur sur le dépôt) — point d'infra, hors clôture.

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

## DOC-01 — L'état courant est noyé dans l'historique et contient des contradictions — ✅ CLOS (08/09/2026)

- **Priorité / statut** : **P1 — ✅ Clos** (v41.69 `4e5410a` + miroir `6d9ae57` + clôture v41.71)

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

### Clôture (08/09/2026, commits `4e5410a` + `6d9ae57` + v41.71)

1. **Cause** : l'état courant était dispersé entre README, CHANGELOG et CLAUDE.md, avec des
   blocs datés (02/09) qui contredisaient les résultats récents (23 réfutations, leviers de
   l'apprenant) — la « piste en cours » de l'INDEX était dépassée depuis le 04/09.
2. **Correction documentaire** :
   - v41.69 (`4e5410a`) : ratio **×28,2** (46 840 → 1 321 618) partout, maturité composée,
     `(env_id)` sur les niveaux, leviers de l'apprenant, entrée CHANGELOG v41.68 manquante ;
   - `6d9ae57` : miroir FR du ratio + CLAUDE (protocole A dépouillé, plus « préparé ») ;
   - **v41.71** : `docs/ETAT_COURANT.md` créé (instantané unique, réécrit après chaque
     résultat majeur), `docs/INDEX.md` nettoyé (bloc « À lire en premier » → ETAT_COURANT,
     carnets 07/09 ajoutés, comptages corrigés).
3. **Vérification fraîche** : audit croisé des deux vitrines — `28,2×`/`~28,2` présent dans
   l'intro et le bloc de mesure des deux README ; `1,01`/`1,01`, `18,76`/`18,76` et
   `0,0073`/`0,0073` (requalification MES-02) présents des deux côtés ; résidus « ~24 » et
   « 2,86 » **uniquement** dans les blocs historiques datés (v41.31) — conforme à la règle de
   trace, aucune archive réécrite. Tous les liens de l'INDEX et d'ETAT_COURANT pointent vers
   des fichiers existants (vérifié).
4. **Entrée CHANGELOG** : [v41.71]. ⚠️ Restent hors périmètre DOC-01 : `ARC-01` (décision
   `noyau.py`/`colab.py`, à trancher séparément) et la réduction de CLAUDE.md aux règles +
   liens (dette documentaire, point général 07/09).

---

## REP-01 — Environnement d'installation insuffisamment verrouillé

- **Priorité / statut** : **P2 — 🔴 Ouvert** (livraison à froid faite le 08/09/2026 — clôture
  en attente de la vérification en environnement vierge, différée pour ne pas concurrencer
  SCI-01 Wave 1)

### Constat

Le README propose des installations `pip` sans versions et le lancement via `PYTHONPATH=src`.
L'audit ciblé n'a pas trouvé de `pyproject.toml` à la racine. Aucun échec d'installation vierge
n'a toutefois été reproduit.

### Correction proposée

- Définir la version Python supportée et les dépendances du cœur.
- Ajouter des extras pour audio, visualisation, serveur et instruments.
- Fournir un fichier de contraintes ou lock de référence.
- Enregistrer avec chaque campagne : commit, Python, Torch, MiniGrid, Gymnasium, device et flags.

### Avancement (08/09/2026, v41.73 — zéro run, machine laissée à SCI-01)

1. **`pyproject.toml` créé** — Python ≥ 3.12, dépendances cœur en **planchers larges**
   (numpy/torch/gymnasium/minigrid/wandb), extras découpés par imports réels (audio · arene ·
   irm · professeur · plug-http · baseline-ppo · visualisation · exocortex · tout).
2. **`constraints-lock.txt` créé** — lock de référence figé sur le venv **mesuré**
   (`pip freeze`, 66 paquets, versions exactes ; Python 3.12.12, torch MPS).
3. **`docs/fonctionnement/ENVIRONNEMENT.md`** — spécification normative : installation
   reproductible, enregistrement d'environnement par campagne (bloc du `LISEZ_MOI.md`),
   procédure de mise à jour, critères de clôture.
4. ⚠️ **Décision de forme** : l'environnement de campagne va dans le `LISEZ_MOI.md`, **pas**
   dans `manifeste.json` — le schéma MES-01 est strict (clé inconnue → échec de
   `depouillement.py`, vérifié). L'environnement est une trace de campagne, pas une contrainte
   de dépouillement.

### Critères de clôture

- Installation dans un environnement vierge.
- Import minimal et test CPU réussis.
- Manifeste d'environnement joint aux nouvelles campagnes.

*(À exécuter après la fin de SCI-01 Wave 1 : §6 d'ENVIRONNEMENT.md.)*

---

## ARC-01 — La source de vérité `noyau.py` / `colab.py` n'est pas décidée — ✅ CLOS (08/09/2026)

- **Priorité / statut** : **P2 — ✅ Clos** (v41.72 — option 1 actée)

### Constat

La documentation nommait encore `colab.py` script de référence alors que l'essentiel de
l'évolution et des campagnes récentes vit dans `noyau.py` (figé en v17 contre v41.68, ~24
versions d'écart). Une référence très en retard n'est plus une référence reproductible.

### Options

1. **Recommandée** : déclarer `noyau.py` source de vérité ; `colab.py` devient une archive datée
   ou un simple point d'entrée compatible Colab.
2. Porter régulièrement le noyau vers Colab avec un test de parité obligatoire.
3. Extraire un cœur partagé et garder deux points d'entrée minces.

### Critères de clôture

- Décision écrite dans la documentation normative.
- Une seule implémentation cognitive active, ou test automatique de parité.
- Commandes de lancement mises à jour.

### Clôture (08/09/2026, v41.72)

1. **Décision** : option 1 actée — **`noyau.py` est la source de vérité opérationnelle
   unique** ; `colab.py` (v17) est **classé archive historique**, conservé tel quel, plus
   jamais « script de référence ». Aucun portage colab → noyau n'est plus attendu ; aucune
   mécanique ne doit être écrite pour colab.
2. **Correction documentaire** : en-tête `colab.py` marqué archive (commentaires, zéro
   changement de code) · en-tête `noyau.py` mis à jour (« source de vérité », colab archive) ·
   CHANGELOG [v41.72] · CLAUDE.md dégraissé (section « Variante locale » réécrite : colab
   n'est plus la référence).
3. **Vérification fraîche** : `colab.py` ne porte plus AUCUNE auto-désignation comme
   « script de référence » — le seul emploi du terme est l'interdiction posée par le bandeau
   d'archive (vérifié : 1 occurrence, dans la phrase « ne pas le présenter comme script de
   référence » ajoutée par cette clôture) ; colab.py inchangé fonctionnellement (aucune ligne
   de code modifiée) ; commandes de lancement des runs actuels (SCI-01) toutes sur
   `noyau.py` — déjà le cas.
4. **Entrée CHANGELOG** : [v41.72].

---

## DOC-02 — La garantie « ne modifie aucun poids » de deux instruments est inexacte — 🟠 CORRIGÉ (10/09/2026), clôture suspendue

- **Priorité / statut** : **P2 — 🟠 Corrigé, `✅ Clos` en attente** (critère 4 de la règle de
  clôture : l'entrée CHANGELOG dépend de la décision de version, voir D2 ci-dessous).
- **Nature** : garantie fausse dans sa **mécanique**, vraie dans sa **portée pratique** — la
  distinction compte, donc elle est écrite plutôt que corrigée en silence.
- **Depuis quand** : depuis la rédaction des deux fichiers (en-têtes `irm_cerveau.py` **V25.x**,
  `lancer_arene.py` **V24.0**) ; dernier commit les touchant : `bd2af14`, **27/08/2026** (v41.33).
  ⚠️ `git blame -S` est inexploitable dans cet environnement (« échec de mmap »), la date exacte
  d'introduction de la phrase n'a donc **pas** été établie.

### Preuves (lecture du code + une mesure)

Ce qu'affirmaient les docstrings (l. 35-38 d'`irm_cerveau.py`, l. 39-42 de `lancer_arene.py`) :
`traiter_tick` « ne modifie aucun poids hors d'un `backward()` explicite ». **Faux** :

1. `traiter_tick` appelle `fortifier_synapses` sur tout événement marquant
   (`noyau.py` ~10430-10434) ;
2. `fortifier_synapses` (~2284-2298) appelle `fortification_dopaminergique` sur **les 12 couches** ;
3. celle-ci écrit **en place**, sous `no_grad`, dans `base_weight` **et** `myeline_M`
   (~176-189) — **sans `backward()`**, et **sans être arrêtée par `eval()`**
   (`fortification_dopaminergique` n'est pas conditionnée par `self.training`).

**Mesure** (10/09/2026, lecture seule de `brains/08092026_sci01_balayage_K/K4_NU/K4_NU_g11.brain`) :
`|trace_activation|max = 0,000e+00` sur **les 12 couches**. La fonction grave
`ancrage = trace_activation × pic` : trace nulle ⇒ **écriture numériquement nulle**. Ce n'est pas
un hasard, `cycle_sommeil` remet la trace à zéro (`noyau.py` ~364), donc **tout `.brain`
sauvegardé après une nuit** porte une trace nulle.

⚠️ **Le cas qui n'est pas couvert** : un `.brain` sauvegardé **en pleine journée** — cas réel, la
**micro-sieste de la Cuve** (`daemon_cerveau.py`, `_processus_nocturne`, qui sauvegarde sans nuit)
— conserve une trace non nulle, et le premier pic dopaminergique d'une session d'observation y
écrirait de **vraies** valeurs. **En mémoire uniquement** : ni l'IRM ni l'Arène n'appellent
`persistance.sauvegarder`, donc **le fichier `.brain` n'est jamais modifié** — c'est la garantie
qui compte pour l'utilisateur, et elle est intacte.

### Correction livrée (10/09/2026)

- `irm_cerveau.py` : la garantie est réécrite, avec la mécanique exacte, le cas de la
  micro-sieste et la portée mesurée (bloc « Formulation corrigée le 10/09/2026 »).
- `lancer_arene.py` : même correctif, renvoyant à `irm_cerveau.py` pour le détail.
- **Zéro ligne de code exécutable modifiée** (docstrings seulement).

### Vérifications passées

- Les deux modules **compilent** (`py_compile`) et leur docstring de module reste bien formée
  (vérifié par `ast.get_docstring`) ;
- suite de contrats **44 tests CPU : `OK` (1,66 s)** — aucune régression.

### Reste à faire pour clore

- **Entrée CHANGELOG** — la décision D2 est **prise** (10/09 : « le CHANGELOG fait foi »,
  en-tête `noyau.py` porté à **41.75**, voir DOC-03) : la référence de version n'est donc plus un
  obstacle. Le précédent du dépôt (ARC-01, v41.72 : commentaires seuls ⇒ **entrée CHANGELOG quand
  même**) plaide pour une entrée, à écrire dans le même passage que la clôture de DOC-03.

---

## DOC-03 — L'en-tête de version, l'ordre du CHANGELOG et une collision de numéro — 🟠 CORRIGÉ EN PARTIE (10/09/2026)

- **Priorité / statut** : **P2 — 🟠 Corrigé en partie** (le titre de l'entrée QUA-01 reste à
  trancher par l'auteur).
- **Décision de l'auteur (10/09/2026)** : *« l'en-tête est en retard — le CHANGELOG fait foi »*.

### Les trois faits, mesurés

1. **L'en-tête de `noyau.py` retardait de 7 versions** : il portait `#Version actuelle 41.68`
   alors que la dernière entrée du CHANGELOG est **v41.75** (`docs/ETAT_COURANT.md` parle de
   v41.72/ARC-01). C'est exactement le piège que CLAUDE.md signale (« l'en-tête est resté périmé
   de 20 versions une fois »).
2. **La tête du CHANGELOG n'était pas dans l'ordre décroissant** : `## [v41.71]` était en ligne 7,
   et les entrées **plus récentes** `v41.75`, `v41.74-mesure`, `v41.73`, `v41.72` se trouvaient
   **plus bas** (lignes 46 à 160), contrairement à CLAUDE.md §13 (« entrée la plus récente en
   haut »).
3. 🔴 **Deux entrées distinctes portent le même numéro `v41.71`**, et **`v41.70` est absent de la
   série** :

   | Position | Titre | Corps réel |
   |---|---|---|
   | ligne 7 (avant correction) | `v41.71 — DOC-01 : ETAT_COURANT.md créé…` | DOC-01 (`Catégorie : docs`, registre DOC-01) |
   | ligne 161 | `v41.71 — DOC-01 : ETAT_COURANT.md créé…` | **QUA-01** (`Catégorie : tests`, registre QUA-01, `tests/test_contrats_cognitifs.py`, 44 tests) |

   Le **titre** de la seconde entrée contredit son **corps**, cinq lignes plus bas. Un
   copier-coller du titre DOC-01 lors de l'ajout de l'entrée v41.71 est l'explication la plus
   simple ; la série des versions montre d'ailleurs que **v41.70 manque** à l'appel, et que
   l'entrée QUA-01 est précisément placée entre v41.71 et v41.69.

### Corrections livrées (10/09/2026)

- `noyau.py` : `#Version actuelle` porté de **41.68** à **41.75**, avec la raison écrite dans
  l'en-tête (et le rappel que ce marqueur a déjà dérivé une fois) ;
- `CHANGELOG.md` : les **115 lignes** des entrées v41.75 → v41.72 remontées **au-dessus** de
  l'entrée v41.71, sans qu'**aucune ligne ne soit ajoutée, supprimée ou réécrite** — vérifié en
  comparant la **liste triée des lignes** avant/après (`sorted()` identique) ;
- l'entrée la plus récente est désormais en tête, comme §13 l'exige.

### Ce qui reste à trancher (par l'auteur)

🔴 **Le titre de l'entrée QUA-01 n'a PAS été réécrit** : le faire suppose de choisir son numéro
(`v41.70`, qui comblerait le trou de la série, ou `v41.71` partagé), et ce choix touche
l'histoire du projet. Deux options, à décider :

1. **Retitrer en QUA-01 avec le numéro `v41.70`** — comble le trou de la série et rend chaque
   entrée unique (hypothèse la plus probable, mais c'est une **reconstruction**, pas une preuve) ;
2. **Retitrer en QUA-01 en gardant `v41.71`** — ne suppose rien sur le numéro, au prix d'un
   numéro partagé par deux entrées.

Dans les deux cas, la règle de trace demande de **garder l'ancien titre en regard** (un chiffre
publié corrigé se consigne avec l'ancien, jamais en silence).

### Critères de clôture

- Le titre de l'entrée QUA-01 correspond à son corps, avec l'ancien titre en regard.
- Une entrée CHANGELOG consigne la correction (elle sera prise dans le même passage que DOC-02,
  quand le numéro de version sera fixé).

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
5. ✅ MES-04 : décision — famille de 3, α = 0,05 ⇒ `t` = 2,625 / 2,694. *(08/09/2026)*
6. ✅ API-01 : `SortiePenser` nommée pour `penser()`. *(v41.67, `87b8967`)*
7. ✅ QUA-01 : contrats noyau posés — **44 tests CPU** (v41.70). *(CI : en attente d'infra)*
8. ✅ DOC-01 : corriger l'état courant et les termes statistiques. *(v41.69 + v41.71 — `ETAT_COURANT.md` unique + INDEX + miroir EN/FR)*

## Phase B — fiabilisation structurelle

7. APP-03 : module/configuration uniques.
8. PER-01/PER-02 : migrations et sauvegardes.
9. ✅ ARC-01 : source de vérité — `noyau.py`, colab archive. *(v41.72)* · REP-01 : environnement (ouvert).
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
| 2026-09-08 | MES-04 | ✅ Clos (décision) | CHANGELOG [v41.67] | — | Option A : famille de 3, α = 0,05 ⇒ `t` = 2,625 (n=20) / 2,694 (n=16) ; aucun `t` dans la bande litigieuse, aucun verdict basculé |
| 2026-09-08 | API-01 | ✅ Clos | `87b8967` · CHANGELOG [v41.67] | CPU : type `SortiePenser`, index == noms sur 8/8 champs, déballage OK, `out[4] == out.memoire_actuelle` | Sortie nommée de `penser()` (NamedTuple, accès numérique rétrocompatible) |
| 2026-09-08 | QUA-01 | ✅ Clos | v41.70 · CHANGELOG [v41.70] | **44 tests OK en 2,1 s** (CPU) : API-01 / APP-01 (16 régimes) / APP-02 / MES-02 + 40 MES-01 | `tests/test_contrats_cognitifs.py` ; commande `NAULTHENE_DEVICE=cpu venv/bin/python -m unittest discover -s tests` ; CI = point d'infra |
| 2026-09-08 | DOC-01 | ✅ Clos | `4e5410a` · `6d9ae57` · v41.71 · CHANGELOG [v41.69] + [v41.71] | Audit croisé EN/FR : 28,2×/1,01/18,76/0,0073 présents des deux côtés, résidus historiques datés uniquement ; liens INDEX/ETAT_COURANT vérifiés | `ETAT_COURANT.md` créé (instantané unique) + INDEX nettoyé (bloc 02/09 remplacé, carnets 07/09 ajoutés) ; ARC-01 et réduction CLAUDE hors périmètre |
| 2026-09-08 | ARC-01 | ✅ Clos | v41.72 · CHANGELOG [v41.72] | `colab.py` : aucune auto-désignation « script de référence » hors le bandeau d'interdiction (1 occurrence ajoutée par la clôture) ; zéro ligne de code modifiée ; runs actuels tous sur `noyau.py` | Option 1 : `noyau.py` source de vérité unique, `colab.py` classé archive v17 ; en-têtes mis à jour (commentaires seuls) |
| 2026-09-08 | REP-01 | 🔴 Ouvert (livraison à froid) | v41.73 · CHANGELOG [v41.73] | zéro run — inventaire du venv mesuré (Python 3.12.12, 66 paquets, torch MPS) ; syntaxe/liens vérifiés | `pyproject.toml` (planchers + extras) · `constraints-lock.txt` (lock mesuré) · spec `ENVIRONNEMENT.md` ; clôture = env vierge + 44 tests, différée après SCI-01 |
| 2026-09-09 | SCI-01 | 🔵 À mesurer (Wave 1 faite) | v41.74-mesure · CHANGELOG [v41.74-mesure] | Dépouillement strict : 60/60 couverts, gardes gain_c1 = 1,0000, aucun `t` ne passe Bonferroni (n=10) | Wave 1 : cloche 0/0/8/10/3 (optimum K=8), clip inerte (fraction ~8 %) ; carnet `SCI01_WAVE1_09092026` ; Wave 2 (n=20) pour le verdict |
| 2026-09-09 | REP-01 | 🔴 Ouvert (script prêt) | v41.75 · CHANGELOG [v41.75] | zéro run — syntaxe bash OK ; garde anti-contention testée (refuse si noyau.py actif) | `scripts/verifier_environnement.sh` créé (venv vierge /tmp + import + 44 tests + rapport versions) ; exécution différée après SCI-01 Wave 2 |
| 2026-09-10 | VIS-01 | 🟠 Livré en partie → **✅ Clos** | `2fad056` + `433cc14` · **aucune entrée CHANGELOG** (tâche 11 : pas de `noyau.py`) ; carnet `VIS01_etape2_fichier_10092026/LISEZ_MOI.md` | e2e serveur+run réels : `/structure` `{}` → **12 couches**, `dim_bus` **16 → 68**, `sequence_structure` **0 → 6** (`poll_structure.txt`, 111 lignes à 1 Hz) ; **147 tests OK** (138 + 9, `+429 / −0`) ; empreinte `.brain` bit-identique ; A/A `diff` vide ; surcoût **+7,87 %** | Étape 2 complète : `--structure-fichier` (serveur `--serveur-seul`) relit `<brain>.vis01_structure.json` ; rétractation en §VIS-01 (ancien énoncé « aucun code ne le relit ») ; limites restantes : dernier état publié, coût de veille non chiffré, rendu navigateur non prouvé ; ⚠️ **`INDEX.md` l. 158 reste à corriger** (« le serveur ne relit pas encore ») — hors des trois fichiers autorisés de ce tour |

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
