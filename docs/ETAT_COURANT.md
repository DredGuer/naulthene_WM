# État courant — Naulthène AGI

> **Un seul instantané factuel de l'état du projet** — réécrit, jamais accumulé, après chaque
> résultat majeur (règle DOC-01, point général du 07/09/2026). Ce fichier porte **l'état** ;
> l'histoire, les rétractations et les mesures détaillées vivent dans le CHANGELOG et les
> carnets de campagne. Les README EN/FR restent la vitrine publique (miroir strict).
> Dernière mise à jour : **12/09/2026** (v41.78-mesure) — **SCI-01 terminée et dépouillée à
> n=20** (120 runs, 0 échec), **REP-01 clos** : la Phase A du registre est entièrement soldée.

---

## En une ligne

Naulthène est un **cerveau complet en attente d'un corps** (un seul `nn.Module`, bus latent
unifié, C1 réflexe + C2 néo-cortex, mémoire à flux enrichi, homéostasie dopaminergique,
jour/nuit). MiniGrid (cursus de **15 niveaux**) est son **berceau** d'entraînement — pas sa
finalité. Il est **toujours en cours de développement** : ce n'est ni un solveur MiniGrid, ni
un système livré.

## Le mur réel (au 08/09/2026)

Le log affiche `niveau_actuel + 1` — convention corrigée le 07/09 (off-by-one) : toute
mention de niveau porte désormais le couple `niveau N/15 (env_id)`.

| Réel (index) | Affiché | Carte | Statut |
|---|---|---|---|
| 0 → 2 | 1/15 → 3/15 | `Empty-5x5` → `Empty-Random-6x6` → `Empty-8x8` | ✅ franchis par tous |
| **3** | **4/15** | **`SimpleCrossingS9N1`** | 🔴 **LE MUR** — régime témoin historique : 40/40 s'y arrêtent ; sous K8 (07/09), 15/20 y restent encore |
| 4 | 5/15 | `LavaGapS5` | 🟡 franchi par **5/20** sous `--epoques-nuit 8` (07/09, jamais auparavant) — **suggestif, pas Bonferroni** (`p` = 0,024 vs 0,0167) |
| 5 → 14 | 6/15 → 15/15 | `Fetch` → DoorKey → Unlock → Memory → MultiRoom | ⛔ **jamais atteint par aucun cerveau** |

**23 explications du plafond ont été mesurées et réfutées** (17ᵉ barème 30/08 · 20ᵉ rendement
01/09 · 21ᵉ ancrage cinématique 02/09 · 22ᵉ rebond d'entropie 04/09 · 23ᵉ voix libre en
cursus 04/09). 🔴 **Le mur n'est pas la carte** : un PPO résout `LavaGapS5` — l'étage
**au-delà** du mur — à **97,27 %**, mais cette mesure du 06/09 croyait tester le mur et a été
prise **une carte trop loin** (off-by-one, requalifiée) ; `SimpleCrossingS9N1` lui-même n'a
pas encore de mesure PPO directe. Le blocage est une **pathologie de l'architecture** : la
politique ne reçoit qu'**un pas de gradient par journée** de ~400 ticks (**63× moins par tick
vécu** qu'un PPO sur le même banc).

## Croissance réelle (mesurée, jamais estimée)

| | Total paramètres (appris + buffers `base_weight`) |
|---|---|
| **Naissance** (`dim_bus = 16`) | **46 840** (7 792 appris + 39 048 buffers) |
| **1500 jours** (médiane, n = 44, 07/09) | **1 321 618** — soit **×28,2** |
| plus petit / plus gros | 377 242 / 1 521 418 |

La neurogenèse étend `dim_bus` (16 → 145 médian, **×9**) quand l'erreur JEPA le demande.
⚠️ La croissance mesure surtout la **survie**, pas la compétence (`r(dim_bus, victoires) =
+0,678` contre `+0,499` pour la maîtrise), et **56 % des neurones de `pensee_bio` sont morts**
(40/40 cerveaux) sans lien établi avec le plafond.

## Leviers mesurés (tous des corrections de l'APPRENANT — aucun organe ajouté n'a d'effet)

| Levier | Mesure (n=20 graines appariées × 1500 j, sauf mention) | Verdict |
|---|---|---|
| **`--detach-c2`** (06/09) | maîtrise 8,75 % → 14,00 % (δ **+5,25 pt**, `t` = **+4,97**, 16/20, survit aux extrêmes `t` = +4,57) | ✅ le premier levier réel en cursus complet |
| **`--epoques-nuit 8`** (07/09, **confirmé le 12/09 à n=20**) | le point K=8 du 07/09 était mesuré sur le **rejeu faussé** (APP-01). Re-mesuré proprement : franchissements du mur **0 · 1 · 13 · 18 · 4 sur 20** pour K=1/2/4/8/16 — **cloche, optimum K=8 (90 %)**, K=16 s'effondre (20 %) | ✅ **le levier tient**, et K=8 est le meilleur réglage — mais reste une **constante posée** (pas dérivée) |
| **Voix libre** `--gain-c1-libre` (04/09) | mur tenu (20/20 au niv. 4), effet apparié tombe aux extrêmes | 🟡 ne débloque pas, mais **stoppe l'hémorragie** : 9 témoins/20 à 0 % de maîtrise contre 1/20 en libre |
| **Clipping PPO (ε=0,2)** (07/09 → **requalifié 12/09**) | au 07/09 : −1,00 pt (« le clip nuit »). À n=20 sur le socle réparé : **K8_CLIP = 20/20 franchissements**, indiscernable de K8_NU (Fisher `p` = 0,49), **fraction clippée ~8 %** | 🟡 **INERTE, pas nuisible** — le « il nuit » du 07/09 était un artefact du rejeu faussé |

## Registre des problèmes (verrous)

- **✅ Phase A ENTIÈREMENT CLOSE** : APP-01 · APP-02 · MES-01 · MES-02 · MES-04 (famille de 3,
  α = 0,05 ⇒ `t` = 2,625) · API-01 · QUA-01 · DOC-01 · ARC-01 (v41.72 : `noyau.py` source de
  vérité unique) · **REP-01** (v41.77 : environnement verrouillé **et validé** en venv vierge —
  exit 0, 156 tests OK, versions conformes au lock).
- **🔴 Ouverts (P1/P2)** : APP-03 (deux identités du module) · MES-03 (vocabulaire dispersions) ·
  PER-01/PER-02 (migrations, écriture partagée — à reproduire).
- **🟡 À mesurer / décider** : EVA-01 (juge bruité) · **SCI-01 (n=20 dépouillé — cloche
  confirmée, reste à décider si K=8 devient un socle ou une règle dérivée)** · SCI-02 à SCI-05.

## Dernier résultat consolidé (SCI-01, 12/09/2026)

**Balayage K/ε sur l'apprenant réparé** (`brains/08092026_sci01_balayage_K`) : 20 graines
appariées × 6 bras × 1500 jours = **120 runs, 0 échec**, socle voix libre + `--detach-c2`,
dépouillement strict MES-01 (couverture 120/120, gardes `gain_c1` = 1,0000).

| K | 1 | 2 | 4 | 8 | 16 | 8 + clip |
|---|---|---|---|---|---|---|
| **Franchissements du mur** | 0/20 | 1/20 | 13/20 | **18/20** | 4/20 | **20/20** |

**Cloche confirmée, optimum K=8** ; à palier égal la maîtrise monte jusqu'à K=8
(15 → 20 → 25 → 27,5 %) puis K16 retombe (7,5 %). Le **clip est inerte** (~8 % de fraction
clippée). ⚠️ Aucun `t` de maîtrise n'est interprétable (confusion de palier) : **la cloche
repose sur des comptages, pas sur un test** — et K=8 reste une **constante posée**. Carnet :
[SCI01_N20](recherche/campagnes/SCI01_N20_12092026_le_verdict.md).

## Règles en vigueur

- Ne jamais écrire une supériorité non mesurée · recompter les paramètres, jamais les estimer
  · les niveaux portent `(env_id)` · toute nouvelle mécanique observable est instrumentée dans
  le même commit · un garde-fou de forme **crie** quand il rejette.

## Liens

| Sujet | Où |
|---|---|
| Vitrine publique (miroir EN/FR) | [`readme.md`](../readme.md) · [`readme_fr.md`](../readme_fr.md) |
| Histoire factuelle version par version | [`docs/fonctionnement/CHANGELOG.md`](fonctionnement/CHANGELOG.md) |
| Carte « quelle question → quel document » | [`docs/INDEX.md`](INDEX.md) |
| Registre des problèmes et des clôtures | [`docs/ameliorations/REGISTRE_PROBLEMES_A_CORRIGER.md`](ameliorations/REGISTRE_PROBLEMES_A_CORRIGER.md) |
| Journal des campagnes (normatif, écrit au lancement) | [`docs/fonctionnement/JOURNAL_DES_RUNS.md`](fonctionnement/JOURNAL_DES_RUNS.md) |
| Commandes et dépannage | [`docs/fonctionnement/LANCEMENT.md`](fonctionnement/LANCEMENT.md) |
| Règles de travail (invariants, mesures, trace) | [`CLAUDE.md`](../CLAUDE.md) |
