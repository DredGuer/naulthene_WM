# CLAUDE.md

Instructions de travail pour Claude Code sur le projet **Naulthène AGI** — agent cognitif
autonome hybride (RL + JEPA + mémoire épisodique + homéostasie neuro-mimétique), entraîné sur
un cursus scolaire d'environnements MiniGrid à complexité croissante.

> 🔴 **Ce fichier est un fichier de RÈGLES ET DE LIENS, pas une encyclopédie** (réduction
> DOC-01 + ARC-01, 08/09/2026). Il ne raconte pas l'histoire du projet :
>
> - **L'état courant** (murs, croissance, leviers, verrous, campagne en cours) →
>   [`docs/ETAT_COURANT.md`](docs/ETAT_COURANT.md) — l'instantané unique, réécrit après
>   chaque résultat majeur.
> - **L'histoire, version par version, rétractations comprises** →
>   [`docs/fonctionnement/CHANGELOG.md`](docs/fonctionnement/CHANGELOG.md) ; la carte de tout
>   le dépôt → [`docs/INDEX.md`](docs/INDEX.md) ; la feuille de route (registre) →
>   [`docs/ameliorations/REGISTRE_PROBLEMES_A_CORRIGER.md`](docs/ameliorations/REGISTRE_PROBLEMES_A_CORRIGER.md).
> - Les **récits mesurés** des 23 réfutations et des chantiers vivent dans les carnets de
>   `docs/recherche/` et `docs/ameliorations_appliquees/` — consultés avant toute idée neuve,
>   jamais résumés ici.

---

## 1. Source de vérité (ARC-01, décidé le 08/09/2026)

**`src/naulthene/cerveau/noyau.py` est la source de vérité opérationnelle UNIQUE du projet**
(en-tête : `#Version actuelle 41.68`). Toute mécanique, tout correctif, toute campagne vivent
dans `noyau.py`.

**`src/naulthene/cerveau/colab.py` est une ARCHIVE HISTORIQUE** (en-tête `#Version actuelle
17.`), figée telle quelle :

- ne jamais y écrire de mécanique, ne jamais le citer comme « script de référence » ;
- aucun portage noyau → colab n'est attendu ; aucun test de parité noyau/colab ;
- sa liste de mécaniques manquantes (v18 → v41.x) est le CHANGELOG, pas ce fichier.

La version de `noyau.py` suit le CHANGELOG (une entrée par version). Incréments :
`feat` +1.0 · `fix` critique +0.1 (`-fix1`) · `fix` mineur/`refactor`/`docs` même version ·
`chore`/`style` rien. Une mécanique non portée ailleurs reste marquée de son versionnage
normal, sans suffixe `-experimental` (plus de cible de portage depuis ARC-01).

---

## 2. Projet Overview (le minimum pour ne pas se tromper de projet)

Naulthène n'est **pas un solveur MiniGrid** : c'est un **cerveau complet en attente d'un
corps**, élevé dans un berceau MiniGrid (15 niveaux, du Nourrisson `Empty-5x5` au Doctorat
`MultiRoom-N4-S5`) pour être cassé et mesuré. L'agent (`AGI_Naulthene`, un seul `nn.Module`)
combine :

- **JEPA** — modèle du monde latent (`generateur_attente`, `perte_jepa`) ;
- **C1 réflexe + C2 néo-cortex** — arbitrage `logits_instinct + valeurs_simulees ×
  force_planification` (fusion inchangée depuis v13.0), C2 ne recevant que l'état déjà
  compressé par C1 ;
- **mémoire à flux enrichi** (v36.0) — repères spatiaux, récurrence → abstraction
  (`confirmations`, `valence` apprise), oubli = retirer le moins abstrait ;
- **Bus Sensoriel** (`bus_sensoriel.py`) — 5 sens hiérarchisés + Exo-Sens (6ᵉ, perception
  continue du monde numérique, jamais « interrogé » par une action) ;
- **homéostasie** — réservoir dopaminergique, plasticité structurelle
  (`NaultheneLinearSynaptique`, base figée + annexe apprise, myéline, neurogenèse sur
  thermostat JEPA), rêve adaptatif (porosité = plasticité × richesse, jamais un batch fixe),
  jour/nuit.

**Promotion** (v40.2+) : par **maturité composée** `_maturite_niveau` = régularité ×
consolidation × autonomie ≥ `SEUIL_MATURITE`. Les « 2 victoires consécutives OU 60 % sur 20
épisodes » sont les voies historiques (v35), pas la mécanique actuelle.

⚠️ **Communication** : ne jamais présenter le projet comme livré ni comme solveur MiniGrid ;
ne jamais masquer l'état réel ; ne jamais écrire une supériorité non mesurée. « Le cœur ne
nomme presque rien du monde » — mais `COULEUR_FOOD`/`COULEUR_WATER` et un test de type
subsistent dans `noyau.py` (audit 18/08) : toujours nuancer, et ne jamais dire « rien en dur »
sans vérifier.

Suivi expérimental : W&B public [`Naulthene-AGI`](https://wandb.ai/naultadrien123-nvnc/Naulthene-AGI),
~90 métriques par nuit. Pas de build ; validation par logs console + courbes W&B + carnets.

---

## 3. Les trois dogmes (ce qui ne se négocie jamais)

| Dogme | Gouverne | Règle |
|---|---|---|
| **« Rien en dur »** | la conception | toute grandeur qui devrait évoluer avec l'âge ou le monde est **dérivée du vécu** (jamais une constante posée a priori) — voir §9 « invariants », et l'échelle d'une grandeur dérivée se justifie par une mesure, jamais par une formule arbitraire |
| **« Rien sans témoin »** | les conclusions | aucune conclusion sans **témoin** (A/A d'abord, n ≥ 20, δ_A/A reporté, Bonferroni dès 2 métriques) — voir §7 « Règle de Mesure » |
| **« Rien sans écrit »** | ce qui survit | toute mesure, réfutation, correction d'instrument, run lancé est **écrit avant d'être commenté** — une mesure non consignée n'a pas eu lieu — voir §6 « Règle de Trace » |

---

## 4. Règle de miroir — `readme.md` (EN) ↔ `readme_fr.md` (FR)

`readme.md` est la page d'accueil GitHub, en **anglais** ; `readme_fr.md` en est le **miroir
français** : même thèse, mêmes chiffres, mêmes tableaux dans l'en-tête, avant la
documentation narrative longue (FR seulement).

**Toute modification de l'en-tête de l'un est répercutée dans l'autre, dans le même commit.**

| Bloc | Dans les deux |
|---|---|
| La thèse (espace vectoriel unifié) · « un cerveau complet en attente d'un corps » | ✅ |
| L'avertissement « cela ne fonctionne pas encore » | ✅ |
| Paramètres par couche + total · comparaison aux baselines RL et son verdict défavorable | ✅ |
| L'état du blocage · le tableau d'ablation sensorielle · l'empreinte mémoire | ✅ |
| Le lien W&B public | ✅ |
| Journal des versions, formules détaillées, paliers | ❌ français seulement |

Mettre ces blocs à jour seulement si : **(1)** le nombre de paramètres bouge — le **recompter**
(`sum(p.numel() for p in agent.parameters())` + buffers `base_weight`), jamais l'estimer ;
**(2)** l'état du blocage bouge ; **(3)** un tableau de benchmark a une mesure nouvelle.

⚠️ **Ne jamais écrire une supériorité non mesurée.** Les deux README affirment des chiffres
vérifiables en cinq minutes (2,85× plus lourd qu'un PPO CNN à la naissance, « ne résout pas
`Empty-8x8` », couper C2 ne change rien) : les enjoliver coûterait toute la crédibilité du
dépôt. Thèse défendable : **l'unification** (une règle de plasticité, un bus, des sens
additifs) — la légèreté reste à démontrer à budget égal.

---

## 5. Architecture (où trouver quoi)

```
21. AGI/                          racine du dépôt (CWD de lancement de tous les scripts)
├── readme.md · readme_fr.md      VITRINE publique — miroir strict (§4)
├── CLAUDE.md                     ce fichier : règles + liens
├── src/naulthene/
│   ├── cerveau/
│   │   ├── noyau.py              🔴 SOURCE DE VÉRITÉ UNIQUE (ARC-01) — ex-agi_local_test.py
│   │   ├── colab.py              🔒 ARCHIVE HISTORIQUE v17 (ne pas modifier)
│   │   ├── bus_sensoriel.py      sens faibles + Exo-Sens ; pur numpy, n'importe JAMAIS noyau
│   │   └── persistance.py        cristallisation/résurrection (.brain), greffes par recopie
│   ├── salles_de_classe/         cursus (bébé, développemental, parole)
│   ├── cuve/                     client-serveur (daemon, client_corps, client_professeur)
│   ├── audio/                    hémisphère audio/vocal
│   ├── exocortex/                Port C3 + plugs (greffon optionnel)
│   └── instruments/              sondes et bancs LECTURE SEULE (~35 fichiers) — cf. CHANGELOG
├── experiences/                  scripts d'expérience v38/v39, lancés à la main
├── brains/                       UNE CAMPAGNE = UN DOSSIER créé AVANT le premier run
│                                   (LISEZ_MOI.md + agrégat JSON versionnés, *.brain gitignorés)
└── docs/
    ├── ETAT_COURANT.md           🔴 l'instantané unique de l'état — à lire en premier
    ├── INDEX.md                  la carte : quelle question → quel document
    ├── fonctionnement/           NORMATIF (CHANGELOG, JOURNAL_DES_RUNS, LANCEMENT)
    ├── recherche/                ENQUÊTES (campagnes/ n≥20 · enquetes_closes/ pistes réfutées)
    ├── ameliorations/            idées proposées, non validées
    ├── ameliorations_appliquees/ livré + options ÉCARTÉES et leurs raisons
    └── etat_des_lieux/           photos datées, jamais réécrites
```

Tous les imports entre modules : **chemins absolus de package**
(`from naulthene.cerveau.noyau import ...`), jamais d'imports à plat. Tout script se lance de
la racine du dépôt avec `PYTHONPATH=src` et l'option `-m` (jamais `python fichier.py`).
Chemins `.brain` par défaut relatifs à la racine.

`noyau.py` reste volontairement monolithique : sections numérotées par
`# --- N. NOM DE LA SECTION ---` — c'est sa table des matières. Toute nouvelle section
respecte ce style. (`colab.py`, archive figée, n'en reçoit plus.)

---

## 6. La Règle de Trace — « rien sans écrit »

> Troisième dogme. Gouverne ce qui SURVIT (posé le 31/08/2026).

**Toute mesure est écrite AVANT d'être commentée. Une mesure non consignée n'a pas eu lieu.**

### Ce qui déclenche l'obligation

| Action | Trace obligatoire |
|---|---|
| Une **mesure** (banc, sonde, corrélation, ablation) | document + agrégat machine |
| Une **hypothèse réfutée** | carnet dans `recherche/enquetes_closes/` ou `campagnes/` |
| Un **chiffre publié corrigé** | la rétractation, **avec l'ancien chiffre en regard** |
| Un **instrument corrigé** | ce qu'il mesurait faux, et depuis quand |
| Un **artefact écarté** | le test qui l'a écarté, pas seulement la conclusion |
| Du code modifié | entrée CHANGELOG (règle préexistante) |
| **Un run lancé** | entrée [`JOURNAL_DES_RUNS.md`](docs/fonctionnement/JOURNAL_DES_RUNS.md) AU LANCEMENT (voir « Journal des runs » ci-dessous) |

⚠️ **L'échec compte autant que le succès** : une piste morte non écrite sera reprise — le
coût le plus cher du dépôt.

### Forme minimale d'un document de mesure

1. La **question posée**, telle qu'elle a été formulée (pas reconstruite après coup).
2. Le **protocole exact** : commande, `n`, graines, témoin, appariement.
3. Les **chiffres bruts**, en tableau, avant interprétation.
4. Les **vérifications** passées — tautologie, saturation, confondage, artefact — avec leur
   résultat, même nul.
5. Les **limites**, écrites par soi-même d'abord.
6. Ce que cela **ferme** et ce que cela **laisse ouvert**.

### Journal des runs (🔴 écrit AU LANCEMENT, avant le premier processus)

| Champ | Règle |
|---|---|
| Titre | nom de la campagne, jamais la conclusion espérée |
| Date de début | `date "+%Y-%m-%d %H:%M"` au lancement, jamais reconstruite |
| Fin estimée | dérivée du rythme **mesuré** (~30 min de run), jamais devinée |
| Fin réelle | remplie à la fin — **l'écart avec l'estimation est une information** |
| Pourquoi | la question posée, en une phrase, telle qu'elle a été formulée |
| Statut | 🟡 en cours · ✅ terminée · ❌ échouée/annulée |

Une campagne **annulée reste au journal, avec sa raison**. `LISEZ_MOI.md` de campagne porte
le protocole ; le journal porte le calendrier. Les deux sont obligatoires.

### Agrégat machine, à côté du texte

Un JSON par campagne, **régénéré après CHAQUE point** (jamais seulement à la fin). Vérifier
qu'il est complet avant de le citer — un agrégat périmé se lit exactement comme un agrégat à
jour (piège mesuré le 31/08 : resté à n=14 sur 16).

### Ce qui ne compte PAS comme trace

Un chiffre dans une conversation · un log dans `brains/**/*.log` (gitignoré) · un commentaire
de code pour une mesure · un message de commit seul (bon pour le « quoi », pas pour le
protocole).

**Corollaire** : ne jamais annoncer avant d'avoir écrit — un résultat transmis puis écrit
arrive déjà interprété (cas d'école : l'inversion `r = −0,89` annoncée sur 4 cerveaux choisis,
`r = +0,3961` à n=20).

---

## 7. La Règle de Mesure — « rien sans témoin »

> Règle jumelle de « rien en dur » (posée le 16/08/2026).

**Aucune conclusion sans avoir vérifié que le test pouvait la produire.**

### 1. A/A avant tout A/B — et δ_A/A est le vrai plancher

Deux runs identiques (même graine, même code). S'ils diffèrent autant que A et B, le test ne
mesure rien. C'est ce qui a découvert v41.9 : `env.reset()` jamais seedé → **toutes les
comparaisons appariées antérieures à v41.9 ne sont pas concluantes** (ni fausses, ni
probantes).

```bash
mkdir -p brains/AA_<sujet>_$(date +%d%m%Y)
for rep in 1 2; do
  WANDB_MODE=offline PYTHONPATH=src python -m naulthene.cerveau.noyau \
      --graine 11 --jours 60 \
      --brain "brains/AA_<sujet>_$(date +%d%m%Y)/AA_g11_rep${rep}.brain" \
      > "brains/AA_<sujet>_$(date +%d%m%Y)/AA_g11_rep${rep}.log" 2>&1
done
diff <(grep -o 'Niveau [0-9]*' AA_g11_rep1.log) <(grep -o 'Niveau [0-9]*' AA_g11_rep2.log)
```

Bit-identique → l'A/B peut mesurer (δ_A/A = 0) · diffèrent moins que l'effet attendu → bruit
résiduel à dépasser **et** passer le `t` · diffèrent autant que A/B → **le test ne mesure
rien**. **Toujours reporter `δ_A/A` à côté du résultat A/B** — un effet inférieur au bruit
A/A n'existe pas, quel que soit son `t`.

### 2. Ne jamais conclure sous 20 graines

À n=10, une corrélation ne vaut rien même avec un `t` « significatif » à seuil non corrigé
(cas d'école 29/08 : `r = +0,710, t = +2,85` à n=10 → `r = −0,0588` à n=20, signe inversé).

| Échantillon | IC95 du taux de base | Ce qu'on peut détecter |
|---|---|---|
| 6 graines | ± ~30 pts | rien |
| 20 graines | ± ~20 pts | un effet qui double le taux |
| 40 graines | ± ~14 pts | un effet de +50 % |

**Obligatoire** : intervalle de confiance à côté de chaque taux, jamais le taux seul.
**Interdit** : « cette version est meilleure » sous 20 graines.

### 3. Se méfier des résultats qui font plaisir

Un résultat **trop propre** est suspect (canal débranché, pas une découverte : v41.4 drapeau
absent du module, v41.7 valence à zéro sur 4004 repas). Un résultat **favorable** se vérifie
deux fois plus qu'un défavorable.

### 4. Trois natures de résultat

| Nature | Fiable ? |
|---|---|
| Mesure directe (lecture d'un `.brain`, statistique intra-run) | ✅ oui |
| Comparaison appariée (A vs B, mêmes graines) | 🟡 depuis v41.9 seulement, et n ≥ 20 |
| Anecdote (une graine, un run) | ❌ jamais |

Ablation **négative** (mesurée à 0) ≠ ablation **vide** (jamais activée) : une ablation dont
le témoin est à zéro ne mesure rien.

### 5. Forme obligatoire de l'A/B

1. **Appariement par graine** : la graine g11 du bras A voit le même monde que g11 du bras B.
2. **Un seul bras par mécanique** : deux drapeaux ensemble = ablation confondue (v41.30) ;
   deux mécaniques couplées ⇒ trois bras (A, A+m1, A+m2).
3. **Le témoin garde le SENS et ne coupe que la MÉCANIQUE** (`--sans-douleur` garde la
   thermoception, coupe la boucle nociceptive).
4. **Vérifier que le témoin est ATTEINT** : le drapeau doit être lu **dans le module** (bug
   v41.4 : accepté par argparse, jamais atteint).

⚠️ **Le run doit être TERMINÉ avant tout `t`** — un `t` sur un run en cours choisit
implicitement sa fenêtre (ratio C2/C1 : `t=+3,68` au jour 1046 → `t=+1,93` au jour 1479 ;
maîtrise à n=5 : +4,95 → à n=20 : +1,09).

⚠️ **Bonferroni dès plusieurs métriques** — convention MES-04 (décidée 08/09) : famille de 3,
α = 0,05 ⇒ `t` = **2,625** (n=20) / **2,694** (n=16). Annoncer le nombre de métriques avant
le `t`. (Le 2,861 = α 0,01 a été abandonné : erreur conservatrice sans résultat retiré.)

⚠️ **Un banc forcé (`--env-force`) ne prouve rien sur le cursus** (niveau = 1 par
construction) : il prouve qu'une mécanique marche là où elle s'applique, jamais qu'elle ne
nuit pas ailleurs. Toute mécanique validée au banc **doit** repasser en cursus complet.

### 6. Gestion des données — une campagne s'archive AVANT de tourner

Le dossier de campagne se crée **avant** le premier run (jamais après — 40 `.brain` perdus
dans un scratchpad purgé le 22/08). Écrire directement dans `brains/<campagne>/` (jamais
`/tmp`). `.log` compte autant que `.brain` (télémétrie console) : un fichier par run,
`> …log 2>&1`. Toujours archiver, jamais supprimer (`brains/old_VXX/`). Un `LISEZ_MOI.md` par
campagne (protocole versionné). Extraire les chiffres **au fil de l'eau** (résumé JSON après
chaque vague). Nommage apparié : `…_BRAS_g11.brain`, deux bras dans le même dossier.

### 7. Copies de cerveaux — ce qu'on a le droit de comparer

| Situation | Comparable ? |
|---|---|
| Deux bras, même graine, même version | ✅ appariement — le seul cas propre |
| Deux graines différentes, même version | 🟡 population seulement, n ≥ 20 |
| Deux versions d'architecture | ❌ jamais |
| Un `.brain` repris pour un nouveau run | ❌ **jamais sans copie** (écrasé chaque nuit) |

`cp ancien.brain brains/<campagne>/reprise_g11.brain` puis lancer sur la **copie**. Ne jamais
réutiliser un chemin générique (`naulthene_cursus.brain`) pour un run neuf. Un `.brain`
antérieur est greffé au chargement **par recopie** et garde son nom d'origine (le nom trace
sa naissance, pas son état) — lire la version dans le fichier.

---

## 8. Contrats de code verrouillés (à ne pas casser — v41.64 → v41.70)

Ces contrats sont **testés** par `tests/test_contrats_cognitifs.py` (44 tests CPU) — commande
unique : `NAULTHENE_DEVICE=cpu venv/bin/python -m unittest discover -s tests`.

- **`penser()` renvoie `SortiePenser`** (NamedTuple, API-01) : index == nom == déballage sur
  les 8 champs. Ne pas revenir à un tuple positionnel.
- **Le rejeu nocturne rejoue la politique COMPLÈTE** (APP-01) : helper
  `_logits_politique_complete_rejouee` (C1 + C2 re-rollout par état, fusion avec les
  contextes figés `k1`/`k2` stockés par tick, `.clone()` des états). Le pas du jour précède
  les époques : le ratio de la passe 0 ne doit PAS être 1 — le garde porte sur la FORME
  (reconstruction ≡ `penser`), tolérance 1e-4.
- **`--detach-c2` s'applique sur CHAQUE passe** (APP-02) : `entree_critique =
  pensee_bio.detach()` si `DETACH_C2_ASYMETRIQUE`, exactement comme dans `penser()`.
- **Les sondes observent le rollout réel, elles ne le réimplémentent pas** (MES-02) :
  `simuler_futur_et_planifier(..., trace_rollout=...)` (lecture seule) ; `trace_rollout=None`
  = simulation strictement inchangée ; sondes en `no_grad()`, elles ne modifient jamais le
  `.brain` (copier le fichier avant de charger si besoin).
- **Le dépouillement est strict** (MES-01) : primitive `depouillement.py` (manifeste requis,
  cohorte complète, garde-fous bloquants) — ne jamais publier sur une campagne incomplète.

---

## 9. Invariants d'ingénierie stricts — « Before Modifying Code »

> La règle générale : **greffe par recopie, jamais par exclusion** (v24.0-fix4) ; tout ajout
> de dimension au `vecteur_bio` se fait **EN QUEUE** ; les garde-fous de forme **crient**
> quand ils rejettent. Vérifier, avant chaque modification, si elle touche l'une des zones
> suivantes — la justification mesurée de chaque invariant est dans le CHANGELOG et le
> chantier cité.

### Réseau & apprentissage

- **Architecture du réseau** : toute nouvelle couche `NaultheneLinearSynaptique` s'ajoute à
  la fois dans `AGI_Naulthene.__init__`, `cycle_sommeil_global()` et
  `declencher_neurogenese()` — oublier l'un des trois casse silencieusement le sommeil ou la
  neurogenèse de cette couche. `agrandir()` : `segments_in` doit couvrir exactement
  `in_features` (`assert total_ancien == self.in_features`), dans l'ordre de la concaténation
  de `forward()`/`penser()`.
- **Rollout mental** (`simuler_futur_et_planifier`) : le premier pas branche sur les 7
  actions réelles (`self.actions_eye`), les suivants suivent l'argmax glouton — sinon
  complexité $7^{\text{horizon}}$ au lieu de linéaire.
- **Réservoir dopaminergique** : la teneur reste dans `[DOPAMINE_MIN, DOPAMINE_MAX]` via
  `np.clip` **après chaque** mise à jour.
- **Rêve adaptatif** : ne jamais réintroduire une taille de batch fixe — le % rejoué émerge
  de plasticité × richesse.
- **Constante → adaptative** : instrumenter et mesurer d'abord (méthode v30.1). Remplacer un
  chiffre arbitraire par une formule arbitraire ne vaut pas mieux. Encore en attente de
  données : `EXTENSION_PATIENCE_SURSAUT` (métriques `Sursaut_*`).
- **`PROGRAMME` du cursus** (v35.0) : `niveau_actuel` est un **INDEX** — changer taille/ordre
  rétrograde silencieusement les `.brain` ; `persistance` remappe par `env_id` (seule donnée
  non ambiguë, affiche `🔀 Niveau remappé`). Promotion : deux voies en OU, ne jamais supprimer
  la série de victoires. `historique_episodes_niveau` **vidé à chaque promotion**. Succès =
  `recompense_env > 0`, jamais `termine` seul (mort dans la lave). Une seule compétence
  change entre deux paliers voisins.
- **Détecteurs** : `DetecteurFranchissementPortes` et `DetecteurProgresPersonnel` restent
  **agnostiques de la carte** — jamais d'identifiant de niveau ou de position en dur. Le
  cursus des 7 paliers (`DetecteurJalonsDoorKey` : `NOMS`, ordre de validation) est
  spécifique à `DoorKey` — ne pas réutiliser cette classe pour un autre niveau du `PROGRAMME`.

### C1 / C2 (v29.0, v37.0, v37.1 — chantier `docs/ameliorations_appliquees/CHANTIER_v37_equilibre_c1_c2.md`)

- Découpage v29.0 = **restructuration pure** : C2 sollicité à chaque tick, arbitrage inchangé
  depuis v13.0. Pas de court-circuit conditionnel (« C1 saute C2 s'il est confiant »). C2 ne
  reçoit jamais que `pensee_bio` (l'état compressé par C1) — jamais l'observation brute,
  jamais l'environnement.
- (1) **`gain_c1` est un facteur SCALAIRE à double sens** (`GAIN_C1_MIN/MAX`) : il règle le
  VOLUME, jamais l'OPINION — les rapports entre les 7 logits restent intacts.
- (2) **`VIGUEUR_MIN_C1` est dérivée, jamais posée** :
  `(AMPLITUDE_C2_NORMALISEE × FORCE_PLANIFICATION_LIBRE) / RATIO_C1C2_VISE`.
- (3) **La normalisation de C2 est INCONDITIONNELLE** (pas de `if std > 1e-6`).
- (4) **La distillation C2 → C1 exige `.detach()` sur la cible**.
- v37.1 : distillation **sélective** (`_ponderer_distillation`). Le crédit s'arrête aux
  frontières d'épisode (`dones`) ; moyenne **pondérée** (journée stérile = rien) ;
  `reference_choc_dopamine` est un **NIVEAU, jamais un seuil**, et c'est un **cliquet**
  (`INERTIE_OUBLI_REFERENCE_CHOC`) : montée rapide, descente ~50× plus lente, jamais une
  moyenne glissante symétrique.
- ⚠️ Ne pas réintroduire « l'échelle de C2 porte sa confiance » (`indecision_c2`) sans lire
  §5.6 du chantier (échoué deux fois). ⚠️ Ne pas rendre `force_planification` fonction de
  l'incertitude sans un run long montrant `Arbitrage_Ratio_C2C1` stagnant — la décroissance
  de l'écoute de C2 avec la maturité doit **émerger**, jamais être formulée.

### Sens & monde (v29.0 → v32.0, v41.x)

- **Bus sensoriel** (`bus_sensoriel.py`) : pur numpy, n'importe **jamais** `noyau.py`
  (absence de cycle d'import). Nouvelle dimension → **EN QUEUE** (contrat partagé avec
  `BusSensoriel.interpreter` et `persistance._greffer_vecteur_bio_etendu`). Les sens faibles
  (toucher, odorat, goût) n'entrent **jamais** dans `bus_latent` (hors cible JEPA) — pas de
  porte synaptique sommée dans le tronc sans demande explicite.
- **Exo-Sens / Port C3** (v30.0) : **aucun plug enregistré ⇒ comportement bit-identique** ;
  `ACTION_DEMANDER` masquée à `-inf` en permanence, `num_actions` reste 8 ; perception
  **continue**, jamais un déclenchement sur seuil (refusé trois fois) ;
  `percevoir_exogene` clippe dans [0,1] et rejette une mauvaise taille ; bus interrogé un
  tick sur `PERIODE_PERCEPTION_EXO` avec cache ; `PortC3.canal_emission` capture TOUTE
  exception d'un plug.
- **Odorat / clinotaxie** (v32.0) : distance **topologique** (BFS ; sans obstacle = exactement
  Manhattan, test de non-régression) ; porte fermée **« fuit »** (surcoût +4), ne bloque pas ;
  neutre de clinotaxie **0.5** ; `_odeurs_precedentes` remis à `None` dans
  `reinitialiser_episode` ; pas d'habituation au capteur.
- **Thermoception** (v41.11) : le danger est un **champ continu**, jamais un malus
  conditionnel (`si mort → récompense -= X` interdit — seuil en dur sur un type nommé) ; la
  chaleur **rayonne** depuis les cases brûlantes mais les murs font **ombre thermique** ;
  neutre asymétrique (chaleur `0.0`, variation `0.5`) ; `_chaleur_precedente` à `None` au
  reset ; **toute tranche du vecteur sensoriel est bornée en HAUT** (pas de tranche ouverte) ;
  `lava` n'apparaît QUE dans `bus_sensoriel.py`, jamais dans `noyau.py`.
- **Douleur unique** (v41.27) : `encaisser_douleur(pic, demi_vie)` = point d'entrée unique ;
  le « type » de douleur est un couple de nombres, jamais un nom ; le temps **n'augmente pas
  la douleur aiguë, il allonge la récupération** (`dégradation = (1/demi_vie) ×
  exp(−(exposition + douleur))`) ; la chaleur est un **état maintenu par la source**
  (évacuation ≠ perception : seuil 0,12 vs capacité 0,40) ; `douleur`/`exposition` remis à
  zéro à chaque épisode ; tout banc de douleur teste le **régime permanent** (≥ 400 ticks) ;
  option `MORT_COUTE_LA_JOURNEE` = témoin `--mort-sans-cout` obligatoire.
- **Thermohoméostasie graduée** (v41.26) : coût de la douleur **comportemental**, jamais
  métabolique (ne rien brancher sur l'énergie) ; palier 1 = **zéro exact** (pas d'epsilon) ;
  seuil **relatif à l'habituation** (dérivé du vécu) ; habituation **lente**
  (`VITESSE_HABITUATION_MONTEE` ~0,02/tick) ; `brulure` = lésion locale remise à zéro par
  épisode, `chaleur_habituee` survit et se sérialise ; ne jamais mesurer sur `LavaGapS5` seul
  (aucune case à distance ≥ 3 de la lave).
- **Nociception thermique** (v41.25) : la douleur est un **déficit** (`+ chaleur**2` dans
  `calculer_deficit`), jamais une pénalité ; elle se facture **là où le corps est arrivé**
  (relecture post-`env.step` via `chaleur_seule()`, JAMAIS `lire_thermoception()` qui écrit
  `_chaleur_precedente` et diviserait la clinotaxie) ; mesurer avec `--env-force
  MiniGrid-LavaGapS5-v0` + `--sans-douleur`, jamais sur le cursus normal (terme nul dans
  99,7 % des ticks).
- **Travail tenté** (v41.28) : un geste stérile **n'est pas** un geste non fait — ne jamais
  remettre `travail = 0.0` sur un échec ; nature du geste lue sur l'API MiniGrid
  (`unwrapped.actions`), jamais une table de coûts par action ; ratio
  locomotion/manipulation (8×) **géométrique**, pas un réglage.
- **Douleur de stagnation** (v41.43) : n'est **pas** un doublon du métabolisme basal (basal =
  temps ; stagnation = redondance spatiale `1.5 ** occurrences`) ; échelle dérivée du MONDE
  (`GAIN_MINIMAL_VICTOIRE / max_steps`) ; recalculée à chaque carte, jamais par tick ;
  témoin `--stagnation-fossile` branché dans le module avec assertion runtime. ⚠️ Aucune
  mesure comportementale ne soutient ce correctif.
- **Silence auditif** (`obs_auditive is None`) : `porte_auditive` sans biais ⇒ `relu(zeros) =
  0 exact`, norme du bus identique avec/sans (6,3323, écart 0,0000). Ne pas répéter l'erreur
  du CHANGELOG v38 (« la norme change ») : c'est faux. Le défaut est qu'un silence parfait et
  une oreille absente sont indiscernables — la levée exige un **bit de présence** dans le
  vecteur bio (dimension en queue + greffe `persistance`), chantier à part entière, pas un
  bricolage dans la branche `else`.

### Mémoire & apprentissage nocturne

- **Capacité mnésique / richesse du rêve** (v31.0) : capacité recalculée **une fois par
  nuit**, jamais sous `capacite_plancher` (200), troncature par l'AVANT (`pop(0)`) ; souvenir
  spatial = repère dédupliqué sur `(pos, type)` (capacité bornée par `DENSITE_MAX_PAR_CASE`) ;
  `reference_richesse` proportionnelle à `empreinte_enfance` (ne pas sur-corriger la baisse
  saine de rêve d'un cerveau mature).
- **Flux mnésique** (v36.0) : **rien n'est expliqué en dur** (étiquettes opaques, valeur
  apprise dans `valence`) ; **pas de routeur centralisé** (les mémoires SONT les filtres, en
  parallèle) ; la récurrence produit l'abstraction (un doublon incrémente `confirmations` et
  affine `valence`, jamais jeté) ; l'oubli retire le repère le **moins confirmé** ; neutre du
  rappel marquant = `[0.5, 0.0]`.
- **Empreinte de type** (v39.0) : `reinitialiser_niveau` efface le OÙ, jamais le QUOI
  (`empreinte_types` survit) ; l'empreinte se nourrit à l'écriture ET à la confirmation ;
  rien n'y est déclaré ; sérialisée avec lecture défensive `.get(..., {})`.
- **Mémoire par carte** (v41.10) : quitter une carte **archive**, ne détruit pas ; une
  coordonnée n'est jamais lue hors de sa carte (test de fuite) ; `len(souvenirs)` ne compte
  que la carte courante → utiliser `total_souvenirs()` pour toute télémétrie ;
  `reinitialiser_niveau` conservée comme témoin d'ablation.
- **Érosion nocturne** (v34.0-fix1/fix2, v37.0) : érosion **géométrique**
  (`base *= 1 − λ(1 − myéline)`), myéline venant **que** du gradient ; plancher vital jamais
  retiré (6 couches sur 11 y sont collées) ; `norme_naissance` **ne rétrécit jamais**
  (`torch.maximum`) ; le plancher ne doit **jamais devenir un plafond**
  (`torch.clamp(norme_plancher / norme_apres, min=1.0)`) ; myéline rafraîchie **en tête de
  `cycle_sommeil`** ; échelle de myéline **relative à la couche** (`echelle_myeline`, 3ᵉ
  quartile de `myeline_M`, quantile pas max) ; ⚠️ la norme d'une couche est un mauvais
  indicateur d'apprentissage — vérifier la direction (cosinus), pas la magnitude.
- **Cristallisation** (v41.44) : seuil **relatif à la couche**
  (`echelle_myeline × FRACTION_SEUIL_CRISTAL`), jamais absolu ; `FRACTION_SEUIL_CRISTAL` > 1
  par construction (cristalliser doit rester exceptionnel, sinon l'érosion — l'oubli — cesse) ;
  cliquet à **sens unique** (`|=`) ; deux témoins (`--cristallisation-fossile`,
  `--sans-cristallisation`). ⚠️ Non mesuré en comportement.

### Noms du monde, persistance, style

- **Noms du monde dans le cœur** (v41.44, P8) : `COULEUR_FOOD`/`COULEUR_WATER`/`TYPE_RESSOURCE`
  sont des alias de `bus_sensoriel` (source unique, à la frontière corps/monde). ⚠️ Le cœur
  reste le **jardinier du monde** (il sème les ressources, donc dépend de « balle rouge =
  nourriture ») : ne jamais écrire « le cœur ne nomme rien » sans cette nuance. Les tables
  `MOT_PAR_OBJET_MINIGRID` restent dans `noyau.py` (l'apprentissage vocal nomme par
  fonction).
- **Persistance / greffes** (`persistance.py`) : `greffe_detectee` ne se fonde **jamais** sur
  `missing_keys` seul (une greffe par recopie ne produit aucune clé manquante — le bug Adam
  v32.0 ne crashait qu'à la première `executer_nuit`). **Toute validation d'une greffe inclut
  une nuit complète.** Modèle : `_greffer_action_supplementaire` (7→8) et
  `_greffer_vecteur_bio_etendu`.
- **Style** : sections `# --- N. NOM ---` · imports absolus · jamais de device supposé fixe
  (toujours `DEVICE` / `.to(DEVICE)`, `cuda`/`mps`/`cpu`).
- **Instrumentation obligatoire** (v29.1) : toute mécanique observable est instrumentée dans
  le même commit — compteur remis à zéro dans `_reinitialiser_buffers_journee`, accumulé dans
  `traiter_tick`, agrégé dans `executer_nuit` (bilan console **et** clé `log_wandb`) ; clés
  **conditionnelles** quand la mécanique peut être inactive ; jamais de compteur journalier
  créé par `getattr(etat, ..., 0)` sans l'ajout à `_reinitialiser_buffers_journee`.
- Après toute modification des hyperparamètres de la section 4 : vérifier la cohérence avec
  le README (tableau config narratif) et mettre à jour la doc si les valeurs divergent.

---

## 10. Essential Commands

Depuis la racine du dépôt, venv Python 3.12 (`venv/bin/python3` — jamais le python système,
sans dépendances) :

```bash
# Cœur — la source de vérité (ARC-01). Flags usuels :
# --graine G --jours N --gain-c1-libre --detach-c2 --epoques-nuit K [--ratio-clippe]
# --brain <chemin> [--no-wandb]   (+ NAULTHENE_DEVICE=cpu|mps, WANDB_MODE=offline si besoin)
PYTHONPATH=src venv/bin/python3 -m naulthene.cerveau.noyau --graine 11 --jours 700 \
    --brain "brains/$(date +%d%m%Y%H%M)_V41_700_RMD.brain"

# Tests (contrats verrouillés, CPU, ~2 s)
NAULTHENE_DEVICE=cpu PYTHONPATH=src venv/bin/python -m unittest discover -s tests

# Autres points d'entrée du même écosystème
PYTHONPATH=src python -m naulthene.cuve.daemon_cerveau --port 9999     # la Cuve (serveur)
PYTHONPATH=src python -m naulthene.cuve.client_corps --port 9999       # client MiniGrid
PYTHONPATH=src python -m naulthene.instruments.lancer_arene             # observer un cerveau
```

### Convention de nommage des cerveaux (depuis v30.0)

```
DDMMYYYYHHMM_VXX_NMRTOUR_RMD.brain   (horodatage du LANCEMENT, version VXX de
  l'architecture, jours demandés, identifiant du run — jamais mis à jour ensuite)
```

Campagne appariée : `…_BRAS_g11.brain` / `…_TEMOIN_g11.brain`, deux bras dans le même
dossier. Générer la date avec `date "+%d%m%Y%H%M"`. Archiver dans `brains/old_VXX/`, jamais
supprimer. `brains/**/*.brain` est gitignoré — vérifier avec `git check-ignore -v` après
création d'un sous-dossier. Le `LISEZ_MOI.md`, lui, est versionné.

---

## 11. Format de Rapport — 3 / 3 / 3

⚠️ **Uniquement sur déclencheur** (« bonne nuit », « à toute », « Acti.333 ») : compte rendu
de session **en autonomie**, jamais un gabarit de réponse ordinaire.

### ✅ 3 avancées — chiffrées. ### ⛔ 3 retards — y compris mes propres erreurs ; un rapport
sans retard est incomplet. ### 💡 3 améliorations — classées par ce que la mesure justifie,
pas par ce qui est le plus intéressant à coder ; distinguer arbitré / en attente de décision.

Si une catégorie est vide, le dire explicitement.

---

## 12. Git Workflow

- **Mono-branche** : le travail se fait sur `master` (seule branche locale depuis le
  02/09/2026). Une branche `feat/…` ne se crée que pour un chantier jetable. Vérifier l'état
  réel avec `git branch --merged master` et `git branch -r`, pas avec un tableau.
- Ne créer un commit que si l'utilisateur le demande explicitement.
- Toujours un **nouveau commit** plutôt qu'un `--amend`, sauf demande contraire.
- Jamais de `push --force`, `reset --hard` ni `--no-verify` sans autorisation explicite.
- Un commit qui modifie `noyau.py` de façon significative s'accompagne de l'entrée CHANGELOG
  et, si le changement est narrativement significatif, de la mise à jour du readme (règle de
  miroir §4).

---

## 13. Maintenance du Changelog et des docs

**OBLIGATOIRE** : à chaque commit modifiant `noyau.py` de façon significative, mettre à jour
les fichiers suivants.

### 1. `docs/fonctionnement/CHANGELOG.md`

Entrée **en haut du fichier** (après l'introduction) :

```markdown
## [X.X] - YYYY-MM-DD — titre court

| Type | Details |
|------|---------|
| **Catégorie** | feat/fix/perf/refactor/docs |
| **Impact** | Critique/Fonctionnel/Performance/Documentation |
| **Registre** | [REGISTRE_PROBLEMES_A_CORRIGER](../ameliorations/REGISTRE_PROBLEMES_A_CORRIGER.md) <ID> → … (si applicable) |

Description courte. | Fichier modifié | Changement |
```

Le CHANGELOG est la référence factuelle : une entrée par version, rétractations comprises
(ancien chiffre en regard). Le `#Version actuelle` de `noyau.py` suit la dernière entrée —
l'en-tête est resté périmé de 20 versions une fois (corrigé le 02/09) : ne pas reproduire.

### 2. README et miroir

- Ajouter une section « Nouveautés vX.X » en tête du journal des mises à jour du
  `readme_fr.md` si le changement est significatif ; mettre à jour la table des matières.
- Si l'**en-tête** de `readme_fr.md` change, appliquer la règle de miroir §4 (même commit).
- Ne pas toucher aux sections narratives pour des commits `docs`/`chore` mineurs.

### 3. Les dossiers de `docs/`

Point d'entrée : [`docs/INDEX.md`](docs/INDEX.md) — tout nouveau document y figure, sinon il
sera oublié. `docs/fonctionnement/` = normatif (CHANGELOG, journal des runs, LANCEMENT) ·
`docs/recherche/` = enquêtes non normatives (consulter avant de relancer une piste) ·
`docs/ameliorations/` = idées non validées · `docs/ameliorations_appliquees/` = livré +
options écartées · `docs/etat_des_lieux/` = photos datées jamais réécrites ·
**`docs/ETAT_COURANT.md` = l'état courant, réécrit après chaque résultat majeur**.

Déplacement : `git mv` et correction de **tous** les liens entrants (README FR et EN,
CLAUDE.md, docs, docstrings). Un document rejoint `ameliorations_appliquees/` quand sa
mécanique est livrée **et** documentée ailleurs.
