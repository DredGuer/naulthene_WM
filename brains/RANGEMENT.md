# Rangement des cerveaux (`brains/`)

> ⚠️ **Règle du projet : toujours ARCHIVER, jamais SUPPRIMER.** Un `.brain` représente
> des centaines de jours de run. Aucun fichier de ce dossier n'a jamais été effacé.
>
> `brains/**/*.brain` est gitignoré (sous-dossiers compris) — vérifier avec
> `git check-ignore -v <chemin>` après avoir créé un nouveau sous-dossier.

> 🔴 **UNE CAMPAGNE ÉCRIT DIRECTEMENT DANS `brains/`, JAMAIS DANS UN SCRATCHPAD.**
> Règle posée le 22/08/2026 après la perte des **40 `.brain` et 40 `.log`** de la campagne
> v41.31-cursus (20 graines × 2 bras × 1500 jours) : les runs avaient été écrits dans un
> répertoire temporaire de session, **purgé quelques minutes après la fin de la campagne**.
> Les chiffres avaient été extraits à temps et sont exacts, mais **aucune réanalyse n'est
> plus possible** et personne ne peut re-vérifier les calculs.
>
> Le `--brain` d'un lancement de campagne pointe donc **toujours** sur
> `brains/<nom_campagne>/`, dès le premier run — pas « on rangera à la fin ». Un dossier de
> campagne se crée **avant** le lancement, pas après.

## Organisation (rangé le 15/08/2026)

| Dossier | Contenu |
|---|---|
| `old_testV30-V34/` | générations d'essai v30 → v34 |
| `old_V30/` | tout ce qui précède la v30.0 |
| `old_V37/` | lignée v34 → v37 + `recherche_aout2026/` (campagne d'ablation du 11-12/08) |
| `old_V39/` | génération v39.0 |
| `old_V40/` | campagne v40 (3 graines × 2000 j) |
| `old_V41_campagne/` | **campagne v41** — 10 graines × 2000 j, celle du « 0 promotion » |
| `old_V414_campagne/` | campagne v41.4 — 300 j appariés + 2000 j héritage actif |
| `old_V414_temoin/` | témoins v41.4 `--sans-heritage` (comparaison appariée) |
| `old_V414_invalides/` | ⚠️ **campagne du 15/08 14h20 — INVALIDE**, l'ablation n'atteignait pas le module (voir CHANTIER_v41.4 §6.1). Conservés pour la traçabilité, **à ne pas exploiter** |
| `cas_isole_g22_v41/` | le cerveau de la « loterie natale » (niveau 4, non reproductible) |
| `ablations/` | résultats JSON du banc d'ablation |
| `old_V419_snapshots_intermediaires/` | ex-`doublons_icloud/`. ⚠️ **Le nom était faux : ce ne sont PAS des doublons.** Vérifié le 18/08 sur les 57 fichiers — **0 redondant, 57 uniques**, chacun portant un `tick_absolu`/`dim_bus` introuvable ailleurs. Le suffixe ` 2`, ` 3` marque un **état intermédiaire** du même run (ex. 2 400 / 5 600 / 400 000 ticks), pas une copie. **Ne pas supprimer** |
| `old_V4124_roi/` | **campagne ROI** (18/08) — 20 graines × 2000 j, plafond 512. Celle qui établit que **la taille du bus n'explique rien** (`r = +0,018`, IC95 [−0,45 ; +0,48]) |
| `old_V4125_nociception/` | **campagne nociception** (18/08) — 20 graines × 2 bras × 300 j, banc `LavaGapS5`. Valence de la lave **+0,062 → −0,761 sur 20/20** (`t = −1066`), mais survie **8,57 % → 6,71 %** |
| `old_V4126_graduee/` | **douleur graduée** (18/08) — 20 graines × 2 bras. ⚠️ **Échec mesuré** : la brûlure saturait à `pic/dissipation` (×6,67), récolte encore −22,8 % |
| `old_V4127_douleur_unique/` | **douleur unique, 3 bras** (19/08) — 20 graines × 3 × 300 j. A (douleur + mort coûteuse) / B (douleur seule) / C (témoin). Établit que **la douleur seule ne change rien** (`t = −1,51`) et que **le coût de la mort, si** (`t = −15,21`) |
| `old_V4128_navigation/` | **diagnostic navigation** (19-20/08) — 10 graines × 300 j sur `Empty-5x5`. Celle qui montre que **l'agent apprend** (13,8 % → 54,4 %, 10/10 graines) et **bat le hasard équitable** (39,2 %) |
| `old_V4128_travail_tente/` | **travail tenté** (20/08) — 20 graines × 2 bras. ⚠️ **Résultat négatif** : −2,52 pts de gestes stériles, `t = −1,71`, non significatif. Le coût n'était pas le levier |
| `old_V4131_gradient_causal/` | **le premier effet cognitif** (21/08) — 3 bras × 20 graines × 400 j sur banc forcé `SimpleCrossingS9N1`. **CAUSAL bat TEMOIN** : maîtrise +2,57 pts (`t=+2,68`), victoires +48 %. Et le bras **CTRL ×2,70 sans filtrage ne donne RIEN** (`p=0,502`) : l'artefact mathématique est réfuté, c'est bien le filtrage. ⚠️ Les gestes stériles ne baissent pas et 0/20 atteignent les 60 %. Logs + scripts inclus |
| `old_V4130_constantes_fossiles/` | **la campagne à n=20** (20-21/08) — 20 graines × 2 bras (DERIVE / FOSSILE) × 1500 jours, cursus complet. **Première mesure du projet réellement au seuil des 20 graines.** ⚠️ **Résultat NÉGATIF** : énergie +0,011 (`t=+1,04`), maîtrise +0,33, ratio C2/C1 +0,088 (`t=+0,63`, 9/20) — tout NS. L'analyse conditionnelle démasque un **artefact** : à régime égal (16 paires) l'effet devient **−0,065** (`t=−0,44`). Franchissement du niveau 4 : **1/20 vs 2/20**, Fisher `p=1,000` ; **aucun run sur 40 n'a dépassé le niveau 5**. Contient aussi la découverte de `taux_satiete` mort. Logs + script de lancement inclus |
| `old_V4129_cursus1500/` | **cursus complet 1500 jours** (20/08) — 10 graines × 2 bras (LIBRE/MORT), sans `--env-force`. **10/10 atteignent le niveau 4/15**, 2/10 le niveau 5 : le blocage au niveau 1 est levé et ce n'était PAS une loterie natale. ⚠️ Mais **rien n'est appris au palier** (tendance jamais positive) et la campagne a surtout servi à **découvrir les trois constantes posées** (`EPISODES_PAR_JOURNEE_REFERENCE`, `PATIENCE_MAX`, `BOOST_PATIENCE_MIN_PAR_RECURRENCE`) : 9 graines sur 10 au plafond exact de patience. Logs inclus |
| ⚠️ `old_V4131_cursus_complet/` | **VIDE — DONNÉES PERDUES.** La campagne de validation du gradient causal sur cursus complet (22/08) — 20 graines × 2 bras × 1500 jours, 40 runs tous complets — a été écrite dans un **scratchpad de session, purgé juste après**. Résultat conservé dans [le compte rendu](../docs/etat_des_lieux/22082026_campagne_v41.31_cursus_complet.md) : niveau `t=+0,37`, maîtrise `t=+0,39`, énergie `t=+0,07`, **0/40 au-delà du niveau 5** — le gradient causal ne survit pas au cursus. C'est l'incident qui a motivé la règle en tête de ce fichier |
| `nuit_18082026_V4123_optionB/` | les 4 cerveaux qui **tiennent le niveau 5** (jusqu'à 1078 nuits dessus) + 1 témoin niveau 4, campagne Option B 20×1500 j |

## Convention de nommage

```
DDMMYYYYHHMM_VXX_NMRTOUR_RMD.brain
└──────┬───┘ └┬┘ └───┬──┘ └┬┘
       │      │      │     └── identifiant du run
       │      │      └──────── nombre de jours demandé
       │      └─────────────── version de l'architecture AU LANCEMENT
       └────────────────────── date+heure de LANCEMENT (jamais mise à jour ensuite)
```

Le fichier est réécrit à chaque nuit, mais son nom garde la trace du **départ** du run.
`VXX` est la version de naissance, pas celle de l'état courant : un `.brain` v29 rechargé
par un binaire v30 est greffé automatiquement et **garde son nom d'origine**.

**Un `.brain` par run** — deux runs partageant le même fichier s'écrasent mutuellement.
