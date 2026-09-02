# Naulthène AGI

**A cognitive agent where every parameter lives in one unified vector space — no task-specific modules, no separate heads per skill, no orchestration layer.**

Vision, hearing, touch, smell, taste, motor control, a world model, episodic memory and speech
all read from and write to a **single latent bus**. Adding a sense means appending dimensions to
one vector, not bolting on a subsystem.

**7,760 parameters at birth. 55,616 once grown to `dim_bus = 64`.** One `nn.Module`, twelve
layers, twelve hundred simulated days of continuous life. 🔴 **Corrected 30 Aug 2026**: this
line read "55,616 at birth" for months, and that was wrong — a brain is born at
`BUS_REFERENCE_INITIAL = 16`, which is **7,760 parameters**; 55,616 is the same brain four
neurogenesis events later. Measured, never estimated. Growth does not stop there: a brain at
1500 days averages **1,241,790 parameters — 160×** its true birth size (35 brains, see below).

### What this is meant to become

**A complete brain, waiting for a body.**

Naulthène is not a MiniGrid solver. MiniGrid is a *crib* — a cheap, fast world in which a brain
can be grown, broken and measured. What is being built is the organ itself: senses that all feed
one space, a metabolism that gets hungry, a reflex layer and a deliberative layer, memory that
abstracts by repetition, and a day/night cycle that consolidates or forgets. Swap the crib for a
camera, a microphone and a motor bus, and the same `nn.Module` should keep running.

⚠️ **Precisely stated** (an earlier version of this line overclaimed): the decision path
contains **no triggering threshold**, and learning quantities are **derived from what the
agent has lived**, not tuned — the same reward is worth 100 % to a beginner and 11 % to
the same agent once expert. What remains hardcoded, and is documented rather than hidden:
**three posed rewards** (down from four — `MALUS_DOULEUR` was removed from the reward path
in v41.27), ~25 calibration constants, and **food/water identified by colour**
(`"red"`/`"blue"`) inside the core.

🔴 **And a second audit, 30 Aug 2026, measured what those constants are actually worth.**
Over 2,400 ticks on a trained brain across three levels, **95.6 % of the agent's learning
signal comes from posed constants and 4.4 % from the world**. On the very level where it
plateaus, MiniGrid pays it **exactly `0.0000` over 800 ticks**: half of everything it wants
is curiosity (`PLAFOND_ERREUR_DOPAMINE`), and its only cost is a posed stagnation penalty
firing on 93 % of ticks. **The agent is not failing at the task — it is succeeding at a
scoring scheme.** Audits:
[dogma](docs/etat_des_lieux/18082026_revue_dogme_avant_publication.md) ·
[genome](docs/etat_des_lieux/30082026_le_genome_audit_des_constantes.md).

🔴 **And the causal hypothesis that followed from it died the next hour — seventeenth
refutation.** Replicated across **40 brains** (no run launched; the AB3 cohort already
existed): the descriptive finding holds, but "listening to the world predicts success" is a
**tautology**. MiniGrid pays only on a win, so `part_world > 0` *means* "this brain won",
and mastery *is* a win rate — the two count the same thing. Conditioned on having won at
all, the signal falls below Bonferroni (`t = +2.34` against 2.39, n = 36). Curiosity
predicts nothing and **its sign flips between the two arms** (+0.23 / −0.26). Same trap as
the C2/C1 ratio in v41.32: a metric derived from the reward cannot predict success, because
the reward *is* success. **The suspect list stays empty** —
[cohort](docs/recherche/campagnes/COHORTE_30082026_le_bareme_ne_predit_rien.md).

**⚠️ It does not work yet.** The agent plateaus at **level 4 of 15**, and **twenty-one**
successive explanations for that plateau have been measured and refuted — thrashing, credit
assignment, proprioception, top-down attention, representational drift, and, on 1-2 Sep
2026, two mechanics *shipped and then refuted at n = 20* (mechanical yield, kinematic
anchoring — [rendement](docs/recherche/campagnes/RENDEMENT_01092026_le_gradient_assaini_ne_change_rien.md) ·
[élan](docs/recherche/campagnes/ELAN_02092026_l_information_est_la_et_ne_sert_a_rien.md)).
Those last two converge on one sentence: *the information is there, and the network does
not use it*. The only levers that ever worked are properties of the *world*, not of the brain.
🔴 **And on 29 Aug 2026 the last one fell too**: `mastery ~ energy`, long quoted here as
`r = +0.710` (`t = +2.85`), was measured at **n = 10**. Recomputed on **20 seeds** it reads
**r = −0.0588 (`t = −0.25`)** — the sign flips and the signal vanishes, jackknife confirming
it was never carried by one outlier. **The suspect list is now empty**, and that is the most
useful thing this repository can say.

**⚠️ And the benchmark itself was biased.** A code review on 13-14 August found that up to
**one map in two** was solvable without the key — the agent was passing a rigged exam. Fixed;
the task then became **50× harder** (random-policy success on `8x8`: 15.3 % → 0.3 %), so
prior results are **not comparable** to future ones. Full account:
[code review](docs/recherche/REVUE_CODE_v39_aout_2026.md).

Read this as a research log, not a released system. Everything broken is written down,
including [every diagnostic mistake](docs/recherche/recherche_bug_or_not_bug.md) — 18 of them so far,
three of which were caught and retracted in the last week alone.

*Long-term direction: a generalist intelligence that runs on a single Apple Silicon chip, with no
datacenter.*

> 🗂️ **[Documentation index →](docs/INDEX.md)** — which question leads to which document
> 🇫🇷 **[Miroir français complet →](readme_fr.md)** (architecture, formules, changelog v7 → v41)
> 🩺 **[System diagnostic, August 2026 →](docs/recherche/dia_Aout_2026.md)** (1300-day run: what works,
> what is blocked, what remains unknown)
> 📊 **[Live experiments on Weights & Biases →](https://wandb.ai/naultadrien123-nvnc/Naulthene-AGI)**
> (every run, every curve, including the failures)

**Author**: Adrien Nault ([@DredGuer](https://github.com/DredGuer)) —
**[AGPL-3.0-or-later](LICENSE)** (relicensed from Apache 2.0 on 2026-08-27).

The AGPL keeps this work open to peers and contributors while making sure it cannot be taken
and closed behind a proprietary black box. **Section 13 matters here**: if you run a modified
version of Naulthène as a network service — an API, a hosted agent, a demo — you must offer
its source to the users of that service. Any reuse, redistribution or derivative work building
on this concept or architecture **must credit Adrien Nault as the original author of Naulthène
AGI** — see [NOTICE](NOTICE).

---

## The thesis

Most cognitive architectures grow by **addition**: a vision module, a memory module, a planner, a
router that arbitrates between them. Each addition brings its own parameters, its own interface,
and its own failure mode.

Naulthène grows by **compression**. A single latent bus (currently 64 dimensions) carries
everything. Every faculty is a projection into or out of that bus:

```
    vision ─┐                                    ┌─ motor (C1 reflex)
   hearing ─┤                                    ├─ value  (C2 neocortex)
     touch ─┼──►  LATENT BUS (64 dims)  ────────►┼─ world model (JEPA)
     smell ─┤     one vector, one space          ├─ voice
     taste ─┘                                    └─ exocortex port
```

Three consequences that make this testable:

| Claim | Why it follows | Status |
|---|---|---|
| **Sensory substitution is free** | Losing a sense zeroes some bus inputs; the others still project into the same space. No fallback code path exists — or is needed. | Architecturally true, **not yet measured** |
| **Adding a sense is additive, not structural** | Smell (v32) and the exocortex sense (v30) were added by appending dimensions. No router, no new subsystem. | ✅ Done twice |
| **Everything shares one plasticity rule** | One `NaultheneLinearSynaptique` class governs all twelve layers: day/night cycle, myelin, erosion, neurogenesis. | ✅ Verified over 1300 nights |

---

## Honest numbers

This section exists because the thesis above is only worth stating if it can be falsified.

### Parameter count — measured

**Read the header carefully**: this table describes a brain at **`dim_bus = 64`**, i.e. one
that has already grown. A *newborn* brain runs at `dim_bus = 16` and totals **7,760**
parameters — see the [genome audit](docs/etat_des_lieux/30082026_le_genome_audit_des_constantes.md).

| Component (at `dim_bus = 64`) | Parameters | At birth (`dim_bus = 16`) |
|---|---|---|
| `porte_visuelle` (147 → bus) | 9,408 | 2,352 |
| `porte_auditive` (130 → bus) | 8,320 | 2,080 |
| `hippocampe` (2·bus → bus) | 8,192 | 512 |
| `fusion_memoire` (2·bus → bus) | 8,192 | 512 |
| `integrateur_bio` (bus+42 → bus) — 5 senses + homeostasis + proprioception | 6,784 | 928 |
| `generateur_attente` (8+bus → bus) — JEPA world model | 4,608 | 384 |
| `generateur_attente_audio` (8+bus → bus) | 4,608 | 384 |
| `analyseur` (bus → bus) | 4,096 | 256 |
| `tete_motrice` (bus → 8) — C1 | 512 | 128 |
| `tete_vocale` (bus → 8) | 512 | 128 |
| `tete_requete` (bus → 5) — C3 routing ⚠️ **dead at runtime** | 320 | 80 |
| `cortex_prefrontal` (bus → 1) — C2 | 64 | 16 |
| **Total** | **55,616** (0.212 MB fp32) | **7,760** |

> ⚠️ **Recounted 27 Aug 2026.** v41.33 adds a **proprioceptive bit** (does the agent carry
> something?) in queue of the bio vector, taking it from 41 to **42** dimensions, so
> `integrateur_bio` is **106→64** and the total **55,616**. Measured with
> `sum(p.numel() for p in agent.parameters())`, never estimated — the same discipline that
> caught the earlier **55,232** figure, stale by two versions. Full teardown:
> [anatomy of the core](docs/etat_des_lieux/21082026_anatomie_du_noyau.md).
>
> **What the split reveals**: **C2 — the deliberative system — is 64 parameters out of 55,616,
> i.e. 0.1 % of the brain.** All of deliberation is one 64→1 projection. Worth holding next to
> the ablation result ("severing C2 changes the score by 0.0 points"): perhaps C2 is not
> useless, it is *tiny*. Meanwhile the audio hemisphere weighs **13,440 parameters (24 %)** for
> a faculty no MiniGrid level exercises.
>
> 🔴 **And neurogenesis makes it worse — structurally.** Measured over 35 brains at 1500 days:
> C2 *is* multiplied by 13 (64 → 833), yet its **share falls from 0.115 % to 0.067 %** because
> the trunk grows **2.2× faster**. The cause is geometry, not a tunable: when `dim_bus` goes
> 16 → 154, a `bus→bus` layer grows as **N²** while a `bus→1` head grows as **N**
> (`hippocampe` ×28.9 vs `cortex_prefrontal` ×13.0). **Every neurogenesis event dilutes C2.**
> There is no constant to fix.
>
> 🔴 **And non-uniform growth would not fix it either — measured 2026-08-23.** The obvious
> remedy (distribute new neurons by per-layer stress) fails twice. It is *structurally
> impossible* as stated — the growth step `a` is both the input **and** the output widening,
> and eight layers are chained on the same bus, so a per-layer `a` breaks the chain at the
> first forward. And its goal is out of reach anyway: on a real 384,808-parameter brain,
> `cortex_prefrontal` weighs **422 params (0.110 %)** *because it has a single output*. Even
> given **100 % of the budget** it would gain **96** parameters where `hippocampe` gains
> **29,952** (**×312**). The lever is not how many dimensions C2 receives — it is that C2
> has **one output**.

### Versus MiniGrid baselines — **lighter at birth, far heavier once grown**

| Architecture | Parameters | vs birth (7,760) | vs `dim_bus=64` (55,616) | vs 1500 d (1,241,790) |
|---|---|---|---|---|
| `rl-starter-files` CNN actor-critic | 19,384 | **0.40×** | 2.87× | **64.1×** |
| PPO `MlpPolicy` (SB3 default) | 27,784 | **0.28×** | 2.00× | **44.7×** |
| `rl-starter-files` CNN + LSTM | 52,664 | **0.15×** | 1.06× | **23.6×** |

> 🔴 **This table was wrong until 30 Aug 2026** and the error cut *against* the project: the
> column labelled "at birth" held ratios computed at `dim_bus = 64`, a brain four neurogenesis
> events old. At its **real** birth size (7,760) Naulthène is **2.5× lighter** than a PPO CNN,
> not 2.87× heavier. Corrected here rather than quietly dropped —
> [genome audit](docs/etat_des_lieux/30082026_le_genome_audit_des_constantes.md).

**But that does not rescue the size claim, because the agent does not stay newborn.** Measured
22 Aug 2026 over **35 brains at 1500 days**: `dim_bus` grows from **16 to 139** on average (max
160) and the total reaches **1,241,790 parameters — 160×** its true birth size. An RL baseline
keeps the size it was given. **The honest comparison on a trained agent is 64×**, and it comes
with a hard block at level 4/15. Naulthène starts smaller and ends far larger.
>
> The cost buys nothing measurable: the heaviest brain in the campaign (1,570,648) and the
> lightest (402,712) both end at **the same level**, size correlates with level at
> **r = −0.17 (t = −1.01, n = 35, not significant)**, and neurogenesis has been extinct for
> **882 days on average**.

Two caveats, both measurable rather than rhetorical:

1. **The comparison is not like-for-like.** 25,088 of those parameters (45 %) buy things no
   MiniGrid baseline has: an audio/vocal hemisphere (13,440), a JEPA world model (4,608), a
   5-sense biological integrator (6,720), an exocortex port (320). The **strictly comparable RL
   core is 30,464 parameters** — 1.57× a CNN baseline, 0.58× a CNN+LSTM.
2. **Efficiency claims require equal-budget comparison**, and that experiment has not been run.

### Task performance — **currently blocked**

| Metric | Value |
|---|---|
| Level reached | **4 out of 15** — 100 % of seeds (n = 20 × 1500 days, v41.23), **reproduced on v41.29**: 10/10 seeds reach level 4, 2/10 reach level 5 (n=10, full curriculum) |
| Level 5 | **4 seeds out of 20** — 20 % [8–42], and the level is **held** (up to 1078 nights on it) |
| What unlocked level 4 | **brain-sparing**: 0 % [0–16] → 80 % [58–92], 18 wins / 0 losses (p < 0.001) |
| Effect of severing C2 on the score | **0.0 points across all 6 levels** (78 cells) — and on `LavaGap`, severing it **triples** the success rate |
| Learned valence of **water** | **+0.017 — below bare floor (+0.125)**, over ~7,800 confirmations, 10/10 brains. The agent drinks constantly and learns **nothing** from it. Same signature as the v41.7 bug (food valence stuck at zero over 4,004 meals): a suspiciously clean result on a high-volume channel. **Possibly a severed channel — unverified** |
| Nights spent at **exactly zero satiety** | **82–87 %** in this campaign, and **78–100 % across every campaign in the repo**, all arms, all versions. ~38 % of ticks in the critical zone, `reserve = 0.000` on every brain measured. Yet surplus is arithmetically reachable (**+0.0025**/tick on a full stomach) — the stomach simply never stays full. ⚠️ The `mastery ~ energy` link once quoted here (**r = +0.710**, n=10) **does not survive n=20** (−0.0588) |
| Learned valence of lava | **+0.072 — POSITIVE**, barely distinct from water (+0.069). Nociception (v41.25) flips it to **−0.761 on 20/20 seeds** — but survival **drops** 8.6 % → 6.7 %, because pain was **non-zero everywhere** (77 % of cells) and the agent fled its own food supply (**−25 % harvest**, two maps). Graded pain (v41.26) under test |
| Cognitive mechanisms that improved anything | **1 out of 19 tested** — brain-sparing. Three pain models (v41.25/26/27) changed behaviour by **0 pt** (`t = −1.51`, n=20); the five mechanisms of the 26-29 Aug series (asymmetric detach, carry bit, connected trunk, drift, metabolism) each measured at **zero effect or below significance** |
| **Is the plateau a geometric floor?** | ✅ **No — measured 30 Aug 2026.** On `SimpleCrossingS9N1` a random walker scores **5.67 %** (600 episodes: 4.50 %, CI95 [3.1 ; 6.5]) while trained brains reach **25.83 %** aggregated (`z = +13.56`), one of them **37.33 %** — inside PPO's own range (27–40 %). **The competence is real.** ⚠️ But the wins stay **Brownian**: 14.2×–18.1× the shortest path (median optimal route **12 steps**, budget 324 ticks), and `r(success, directedness) = −0.92`. The agent wins far more often than chance without ever walking a directed trajectory. 🔴 **Extended to n = 20 on 31 Aug 2026, and it found the first significant predictor in this repository**: **directedness** — path length over the true shortest path — predicts success at **`r = −0.8225`** (`t = −5.96`, n=19), **68 % of the variance**, against 16 % for in-run mastery. Three checks passed: no budget saturation (ceiling 27.0×, worst brain 22.83×), no tautology (`B_g122` scores 0.00 % with *no* directedness defined), and it survives dropping the four extremes (`r = −0.78`, `t = −3.27`). **What separates a 3 % brain from a 37 % one is its spatial diffusion coefficient** — not perception, not size, not metabolism, not the reward mix. ⚠️ **A retraction**: an earlier version of this line reported an *inversion* (`r = −0.89`) between mastery and bench score — that was a **selection bias of mine**, four brains all drawn from the top of the distribution. At n=20 the correlation is **+0.3961** (NS). Mastery is not inverted, it is **noisy**: it explains 16 % of the variance, and at equal mastery two brains range from 3.00 % to 28.67 %. 🔴 **RE-RUN ON THE CORRECTED BENCH (2 Sep 2026, 20/20) — and the figure is REQUALIFIED.** Those bench numbers came from a probe reading working memory at the wrong index; the agent played with **no working memory and no episodic context**. Re-measured on the full cohort, directedness **survives but weakens**: `r = −0.6794` (`t = −3.93`, n=20), **46 % of the variance** — and it **no longer survives dropping the four extremes** (`r = −0.478`, `t = −2.04`, **NS**), which was one of the three checks that established the result on 31 Aug. The correlation is **carried by its extremes**: it separates very directed brains from very Brownian ones, and discriminates poorly in the middle. ⚠️ This was written down **at n=15, before the campaign ended**, not discovered afterwards. Checks that do pass: random control **5.67 % on 20/20**, no budget saturation (worst 26.25× against a 27.0× ceiling), no brain at zero wins. And **working memory is a source of variance, not a lever**: δ success **+0.63 pt** (`t = +0.40`, 10/20) on average, but **A_g111 +17.0 pt**, **B_g11 +17.3**, **A_g166 −10.7** individually — every ranking of brains based on the 30-31 Aug figures is void ([re-run](docs/recherche/campagnes/REJEU_02092026_la_directivite_survit_affaiblie.md)) |
| Navigation on an empty 5×5 room | **54.4 %** after 300 days vs **39.2 %** for a random policy *over the same 7 actions* — the agent **beats chance by 15 pts** |
| Ticks spent on gestures that change nothing (`Empty-5x5`) | **57.2 %** — because a sterile gesture cost **1.09** against **4.00** for the one gesture that moves toward the goal. **v41.28** charges the work *attempted*: pushing a wall now costs a full step. **Measured (n=20): −2.5 pts, `t = −1.71`, not significant** — the cost was not the lever |
| Effect of growing the brain (96 → 160 → 512 dims) | **none** across 3 campaigns — and energy drops 11× |
| **Why it plateaus at level 4** | 🔴 **UNKNOWN — and the metabolic answer was retracted on 29 Aug 2026.** `mastery ~ mean energy` was quoted for nine days as **r = +0.710** (`t = +2.85`) — measured at **n = 10**. At **n = 20** it is **r = −0.0588 (`t = −0.25`)**: the sign flips, the signal disappears, and a jackknife shows it was never carried by a single seed (r stays within [−0.168, +0.055]). g77 has the 2nd-best energy and 17.3 % mastery; g144 has the 2nd-worst and 22.5 %. **Eighteen explanations measured, eighteen refuted.** Three fell on 30 Aug 2026: the *sparse reward* framing (the premise is false — **86 % of the signal is dense**, and normalising per episode measures **worse**, 60 draws out of 60), **curiosity** (a confirmed permanent rent at 40 % of the signal, yet mastery is **15.0 % vs 15.0 %** between low- and high-curiosity brains), and the **scoring scheme** itself, which turned out to be a tautology. What remains true and unexplained: three **posed constants** still calibrate the metabolic rhythm for a *newborn* agent (4 episodes/day assumed, 1.55 played), and **9 seeds out of 10 sit at the exact `PATIENCE_MAX = 350` ceiling** |
| **v41.31 — the causal gradient** | Masking the actor's gradient on non-transitions gave mastery **+2.57 pts** (`t = +2.68`) on a **forced** `SimpleCrossing` bench, n=20. 🔴 **It does not survive the full curriculum.** 20 paired seeds × 1500 days, free curriculum (40 runs): level **+0.05 (`t = +0.37`)**, mastery **+1.09 (`t = +0.39`)**, energy **+0.001 (`t = +0.07`)** — all NS, and **0 of 40 runs pass level 5**. A forced bench proves a mechanic works *where it applies*, never that it helps elsewhere |
| **v41.32 — asymmetric detach (AB3)** | Cutting C2's gradient into the shared trunk cleans the gradient (+25 % alignment on the bench) and **changes nothing**: 20 paired seeds × 1440 days, level **−0.10 (`t = −0.70`)**, mastery **−6.09 (`t = −1.93`)**. The one significant metric (C2/C1 ratio, `t = +3.82`) is a **tautology** — decomposition shows C1's amplitude *falling* 27 % (`t = −3.57`) while C2 does not move (`t = +1.70`, NS). **Tenth refutation** |
| **v41.33 — the carry bit** | The critic separates *object ahead* from *wall ahead* very well (Cohen's **d = +0.65 to +1.21**) but **could not tell it was carrying something** (d ≈ **0.1**, sign unstable) — of the 41 bio dimensions, **zero** encoded the inventory. Adding a 42nd dimension **lifts the blindness**: d goes **−0.012 → +1.428**, 18/20 seeds, 40 runs. 🔴 **And it changes nothing.** The credit stays flat (`\|A\| useful / \|A\| neutral` **1.11× → 1.18×**, `t = +1.97`, NS) and no behavioural metric moves. **Twelfth refutation** |
| **v41.34 — the historical `.detach()`** | The actor and critic send **exactly 0.000000** gradient to the four perceptual layers; only the JEPA (0.033868) shapes what the agent learns to see — a line present in `colab.py` **since the project's origin**, never commented, never justified. Connecting it was expected to *reduce* perceptual noise. It **raises it 48 %** (`t = +2.71`, 14/20, 40 runs), with σ(V) +52 % — the trunk is *agitated*, not oriented. Level: **δ = 0.00 exactly**. The `.detach()` is not technical debt; it **protects the stability of the perceptual map**. **Fourteenth refutation** |
| **v41.35 — a geometric ceiling, and a retracted diagnosis** | Bound: `\|logit_r − logit_m\| ≤ ‖W‖·‖x_r − x_w‖` caps the favoured action at **14.56 %–18.00 %** against **14.29 %** for chance — the 15.00 % measured in play is **not apathy**. ⚠️ **The accompanying claim that "the network destroys the information" was WRONG and is retracted**: cosine **saturates** post-`relu` (two clearly separated clouds, d' = 2.93, still read cos = 0.971). Re-measured with d-prime where the agent actually plateaus, the network **amplifies** the decisive feature — *is the goal visible?* — by **3.5× to 4.4×** (d' 0.824 → 2.891/3.613/3.017). The JEPA is doing its job; the bottleneck is what `tete_motrice` **does** with a clean input, and that has never been measured |
| **v41.36 — the head chases a target that outruns it** | Everything upstream works: the trunk **amplifies** the decisive feature, the gradient arrives, **g22 is never clipped** (0/5 nights), Adam takes its full step, the night does not erode (norm at **90–98 %** of birth), and the steps are **directed** and **additive** (temporal alignment **0.969** vs 0.316 for a random walk). But the informative axis — trained *at the same time* — **rotates 0.4203°/night** while `W` turns at 0.0359°/night (**×11.7**), and over 200 nights the alignment **regresses** (0.1051 → 0.0917). The two are **coupled**: when the target slows to 0.101°, `W` slows to 0.012° with it. ⚠️ An earlier ×46 figure was **retracted** — its prey was measured without a fixed seed, its pursuer derived from a formula rather than measured |
| 🔴 **v41.37 — and the drift predicts nothing** | The missing link, refused as an assumption for two days, does not hold. Drift speed measured on all **20 paired brains** of the v41.34 cohort, correlated against performance already logged: **r(drift, mastery) = +0.1386** (`t = +0.59`), r(drift, energy) = −0.1059, r(drift, level) = −0.0506 — **none approaches the Bonferroni threshold** (3.38 over 3 metrics), and the first sign is *positive*, the opposite of the prediction. **g111 drifts 4.6× more than g211 and masters 3.1× better.** The drift is real; it does not explain the plateau. **Fifteenth refutation** — and it cost 20 minutes instead of a 40-run campaign, because a correlation is falsifiable in both directions while a finer description of the phenomenon is not |
| 🔴 **v41.39 — confident in the wrong answer** | ⚠️ **A correction first**: the policy actually played is `voix_c1 + voix_c2`, not the raw head logits. The **15.00 %** published two days earlier was C1 alone; the real policy sits at **23.89 %** and **1.8631** entropy — C2 adds **+8 points of decision**, and the "18 % geometric ceiling" applies to C1 only, never to the agent. `coeff_entropie` is **acquitted** (its gradient is **0.44–1.05 %** of the advantage's). The gain clip saturates 99.8 % of ticks on one brain, and correlates with mastery at `r = −0.4519` — **the strongest signal in weeks, and still short of Bonferroni** (`t = −2.15` against 3.61). ⚠️ Two findings break the causal chain: clipping **does not touch entropy** (`r = −0.0192`), and **P(favoured action) correlates NEGATIVELY with mastery** (`r = −0.2868`). The agent is not frozen by doubt — when it commits, it often commits to the wrong action. Against PPO the distributions are close (1.83/25 % vs 1.68/35 %) for 16 % vs 40 % success: **the failure is qualitative, not quantitative** |
| Levers that did work | **3 — two properties of the world, one of the decision** |

> 🔴 **The gradient was not the cause — nine refutations, then a twist (26-27 Aug 2026).**
> A week of gradient diagnostics converged on *thrashing*: the actor's daily gradients cancel
> out (alignment 0.3966 against 0.3536 for a random walk). Cutting C2's gradient out of the
> shared trunk repairs it — and the full-curriculum campaign (**40 runs, all complete**) finds
> **nothing**. A clean gradient with nothing worth optimising produces no intelligence.
>
> **What the probes then found is structural.** The actor and the critic send **exactly
> 0.000000** gradient to `porte_visuelle`, `hippocampe`, `analyseur` and `fusion_memoire` — a
> `.detach()` cuts the perceptual trunk from both heads, so **only the JEPA shapes perception**
> (0.033868). No amount of incentive can sculpt what the agent learns to see. And the *credit*
> is flat where it should peak: a useful grab earns, within ±13 %, what a quarter-turn on the
> spot earns.
>
> 🔴 **And giving the agent the missing information was not enough either (27 Aug 2026).**
> The critic was found blind to its own hands: of 41 bio dimensions, **zero** encoded whether
> it was carrying anything. Adding one dimension **fixes exactly that** — Cohen's d goes from
> −0.012 (control) to **+1.428**, on 18 of 20 paired seeds, 40 runs. The chain's first link
> held: a variable absent from the input cannot be learned.
> **The second link does not.** A critic that sees better does not produce a sharper advantage:
> the useful-gesture credit moves 1.11× → **1.18×** (`t = +1.97`, NS against a Bonferroni
> threshold of 3.53 over 10 metrics), and every behavioural metric stays put — with the
> non-zero trends running *against* the bit. **Twelfth refutation.** The bit stays in the code:
> it lifts a real, measured blindness for one dimension, and its null effect is a result, not
> a defect.
>
> ⚠️ **One campaign had to be killed mid-flight.** The carry bit was validated on `DoorKey-6x6`
> (a level-9 environment) then launched on the full curriculum, where the agent plateaus at
> level 4 — the first graspable object appears at level 6. `🔑 Carry 0.0%` over 400 days, both
> arms bit-identical: an **empty ablation, not a negative one**, the exact trap §4 of the
> measurement rules describes. 16 runs discarded, and a new mandatory step added: *verify the
> independent variable actually varies before launching*.
> [Conditioning](docs/recherche/enquetes_closes/CONDITIONNEMENT_27082026_le_signal_arrive_et_ne_sert_a_rien.md) ·
> [Credit](docs/recherche/enquetes_closes/CREDIT_27082026_l_arrosage_confirme_et_la_vue_orpheline.md)

A standard PPO solves `Empty-8x8` in a few thousand episodes. **Naulthène currently does not.**

> 🔴 **The causal gradient falsified on the full curriculum (22 Aug 2026).** 20 paired seeds
> × 1500 days, free 15-level curriculum, **40 runs all complete**. Level: **4.10 vs 4.05**
> (`t = +0.37`, 4 wins / 13 ties / 3 losses). Mastery: **+1.09** (`t = +0.39`, 9/20 seeds).
> Energy: **+0.001**. **Not one run out of 40 passes level 5.**
>
> ✅ **The "never report a `t` on a running job" rule paid off.** At 5 seeds mid-campaign the
> mastery gap read **+4.95**; at 20 seeds it is **+1.09** — divided by 4.5. The figure was
> never published, so nothing had to be retracted. Same shape as the C2/C1 ratio
> (`t = +3.68` mid-run → `t = +0.63` final).
>
> The one metric above `t = 2` — minimum satiety, `Δ = +0.032`, `t = +2.17` — **fails
> Bonferroni** across the 3 metrics tested (threshold `t ≈ 2.86`; corrected p ≈ 0.13).
> [Full write-up](docs/etat_des_lieux/22082026_campagne_v41.31_cursus_complet.md).

> 🔴 **The clearest measurement in this repository (20 Aug 2026).** On `Empty-5x5` — an
> empty room, no hazard, goal 4 cells away — the agent **does learn**: mastery climbs
> 13.8 % → 26.7 % → 43.8 % → **54.4 %** over 300 days, on **10 seeds out of 10**, and the
> gap between wins shrinks from 5.4 to 1.4 days. Against a random policy drawing from the
> **same 7 actions** (39.2 %), it is **15 points ahead**.
>
> ⚠️ **An earlier version of this block claimed the opposite** — "21 points below chance" —
> by comparing a 7-action agent to a 3-action random baseline. That was not the same task,
> and the conclusion was wrong. Corrected here rather than quietly deleted.
>
> **What the measurement does show** is a misaligned incentive: **57.2 % of ticks** go to
> gestures that change nothing on this map, because the physical-work cost model (v41.20)
> charges **4.00** for the one gesture that approaches the goal and **1.09** for doing
> nothing. The agent is not irrational — it is optimising exactly what it was asked to.
> [Full measurement](docs/recherche/NAVIGATION_20082026_le_vrai_blocage.md) ·
> [why](docs/recherche/POURQUOI_20082026_l_agent_economise.md).

> ⚠️ **Every paired comparison predating v41.9 is inconclusive.** (An earlier version of
> this page still carried a "0 out of 9 seeds" line; it was one of them.) `env.reset()` was never seeded: MiniGrid draws its layouts from its own RNG,
> which `torch.manual_seed` does not reach. Two runs of the same `--graine` therefore saw
> **different worlds**. Those results are not wrong; they establish nothing. The figures in the
> first two rows are the first measured on a **reproducible bench**, verified by an A/A test.

The [diagnostic](docs/recherche/dia_Aout_2026.md) isolates why, and none of the five blockers is cognitive:
patience capped at 120 ticks against MiniGrid's own 256 (reachable success rate 4.7 % vs 21.0 %),
a ×10 difficulty jump at level 2, an episode expected value of **−1.06**, four of seven actions
inert on empty rooms, and a curriculum era that doubles losing episodes.

---

## Benchmarks

### 1. Sensory ablation — the unification test ✅ **measured**

The central prediction of a unified vector space: removing a sense should degrade performance
*gracefully*, with **no code path change and no fallback logic**. Measured with
[`banc_ablation.py`](src/naulthene/instruments/banc_ablation.py) — **78 cells** (13 lesions × 3
levels × 2 brains), 300 episodes per cell, on two v41 brains at 2000 days.

> **Protocol note.** Each brain is ablated **on its own levels** — g11 on levels 0/1/2, g22 on
> 3/4/5. An earlier bench measured a **0 % control**, which measures nothing: no lesion can lower
> a score already at the floor. Controls here: 44.7 / 46.7 / 27.0 % (g11) and 8.7 / 8.7 / 45.7 %
> (g22). On the two g22 levels sitting at 8.7 %, differences of ±1–2 pts are noise; **exact zeros
> remain readable**.

Δ per level, in points vs the control of that level:

| Lesion | g11: L0 / L1 / L2 | g22: L3 / L4 / L5 | Verdict |
|---|---|---|---|
| **C2 severed** (`planning_force = 0`) | **0.0 / 0.0 / 0.0** | **0.0 / 0.0 / 0.0** | **no effect** |
| **C2 myopic** (horizon 1) | **0.0 / 0.0 / 0.0** | **0.0 / 0.0 / 0.0** | **no effect** |
| Hearing removed | 0.0 / 0.0 / 0.0 | 0.0 / 0.0 / 0.0 | no effect |
| Taste removed | 0.0 / 0.0 / 0.0 | 0.0 / 0.0 / 0.0 | no effect |
| Exo-sense removed | 0.0 / 0.0 / 0.0 | 0.0 / 0.0 / 0.0 | no effect |
| Smell removed (+ klinotaxis) | 0.0 / 0.0 / 0.0 | 0.0 / 0.0 / −0.7 | no effect |
| Touch removed | −4.4 / −5.4 / **−6.7** | −5.0 / −1.7 / +3.3 | **costs** |
| Bio vector zeroed | −4.4 / −3.4 / **−8.0** | −3.4 / −0.7 / +1.0 | **costs** |
| Vision removed | −3.4 / **+3.0** / −3.3 | −2.7 / +1.0 / +1.6 | unstable |
| Spatial memory cleared | **+3.6** / −2.0 / −1.3 | −1.4 / +1.0 / **−7.4** | mixed |
| Episodic context zeroed | +1.3 / +1.6 / +0.3 | −2.4 / **+2.3** / +2.0 | **helps** |
| Working memory frozen | +2.0 / +1.6 / **+4.7** | −3.0 / **+2.6** / −2.7 | **helps** |

**What this supports.** Graceful degradation is real: no lesion causes a crash or a collapse.
Every sense can be removed and the agent keeps running through the same code path — that is the
unification claim, and it holds.

**What this contradicts.** Three results cut against the architecture as it stands:

- **Severing C2 changes nothing — 0.0 points across all six levels.** Twelve measurements
  (severed + myopic × 6 levels), two independent brains, 300 episodes per cell, twelve exact
  zeros. This supersedes an earlier claim on this page that severing C2 *doubled* the success
  rate: that figure came from a bench whose control sat at 4.50 %. The deliberative system is not
  harmful and not helpful — it is **causally disconnected from behaviour**. Corroborated
  independently by C1/C2 agreement decaying from 37 % (day 500) to **0.5 %** (day 2000) across
  10 seeds.
- **Six lesions out of thirteen have no measurable effect.** Hearing, taste, smell and the
  exo-sense — four of the six senses — can be severed without consequence. Only **touch** and the
  **bio vector** carry weight, and their cost grows with difficulty (bio: −4.4 on `Empty-5x5` →
  **−8.0** on long-distance navigation).
- **The three memory systems are mostly harmful.** Freezing working memory *improves* the score
  on 4 levels out of 6 (up to **+4.7**); zeroing episodic context improves it on 4 of 6. One
  clear exception: spatial memory earns its keep on `Primaire 3 (Pick up)`, where clearing it
  costs **−7.4**.

All three are consistent with the [diagnostic](docs/recherche/dia_Aout_2026.md): the agent has not yet learned a
policy worth planning over. Full protocol and matrix:
[campaign notebook](docs/recherche/campagnes/CAMPAGNE_v41_population_et_ablation_aout_2026.md).

### 2. Memory footprint — ✅ **measured for Naulthène**, baseline still pending

| Component | Size |
|---|---|
| Weights (fp32) | **0.211 MB** |
| Adam optimizer state | 0.419 MB |
| Plasticity buffers (myelin, traces, birth norms) | 1.054 MB |
| **Total in memory (training)** | **1.683 MB** |
| Checkpoint on disk | 1.58 MB |

Runs on `mps` (Apple Silicon) today. The plasticity buffers cost **5× the weights themselves** —
the price of the day/night cycle, and a real target for optimization.

| Agent | Training peak | Inference | Checkpoint |
|---|---|---|---|
| PPO CNN (`rl-starter-files`) | — | — | — |
| **Naulthène** | **1.683 MB** | **0.211 MB** | **1.58 MB** |

### 3. Against a PPO baseline — ✅ **measured 29 Aug 2026, 60 runs**

The table that had been empty since this repository was created. **δ_A/A = 0.000000** on all
five metrics (two identical runs, 152,043 steps): the bench is strictly deterministic, so
every gap below is real.

Same task (`SimpleCrossingS9N1`, the level where Naulthène plateaus), same **flattened 7×7×3
observation** and `MlpPolicy` — never `CnnPolicy`, since `porte_visuelle` is a **linear**
layer with no convolution — same **7 actions** (Naulthène masks the 8th to `-inf`
permanently), same **152,043 environment steps** (🔴 *measured* in a real brain's
`tick_absolu` at 400 days, not the nominal 400×400 = 160,000, which is wrong), and MiniGrid's
**raw sparse reward**, no shaping.

| Agent | Params | Success | P(favoured action) | Entropy | d' |
|---|---|---|---|---|---|
| PPO `[37,37]` | 14,068 | **36.2 % ±13.3** | **35.45 % ±5.33** | 1.667 | 0.697 |
| PPO `[69,69]` | 30,644 | **39.8 % ±11.7** | **35.13 % ±5.08** | 1.681 | 0.647 |
| PPO `[107,107]` | 55,648 | **27.1 % ±10.8** | **34.73 % ±3.88** | 1.704 | 0.644 |
| **Naulthène** | **55,616** | **~16 %** | **15.00 %** | **1.930** | **2.891–3.613** |

*(Naulthène's geometric ceiling: 18.00 % · maximum entropy ln(7) = 1.9459)*

> **Three arms, not one, and deliberately.** Matching PPO to the 55,616 total would have handed
> it **1.8× Naulthène's real decision budget** — 45 % of those parameters buy an audio
> hemisphere, a JEPA world model, a biological integrator and an exocortex port that no
> baseline has. The strictly comparable RL core is **30,464**.

🔴 **The informational wall does not exist.** PPO reaches **34.7–35.5 %** on the favoured
action — nearly **double the 18.00 % ceiling** Naulthène's own geometry allows — and all three
architectures sit within **0.7 points** of each other. The plateau is a pathology of
Naulthène, not a property of MiniGrid.

🔴 **Capacity is not the cause.** `r(params, success) = −0.1519` (`t = −1.17`, NS). A PPO of
**14,068 parameters — 4× lighter than Naulthène's RL core — succeeds 2.3× better**, and the
largest arm is the worst of the three.

🔴 **And representation quality buys nothing.** `r(d', success) = −0.0368` (`t = −0.28`).
PPO succeeds **2.3× better with a d' 4.5× lower**. This **reverses two days of readings**:
Naulthène's clean latent space (d' ≈ 3.0) had been taken as a sign of health — it is
decorative. A geometrically clean representation is not a prerequisite for a good policy.
`r(drift, success) = −0.2066` (NS) likewise confirms the fifteenth refutation on a **second,
independent architecture**.

**What is left is the entropy.** PPO converges to **1.667–1.704** (86–88 % of maximum);
Naulthène sits at **1.930 — 99.2 % of white noise** after 400 days. That is now the sharpest
measured difference between the two, and the next thing to investigate.
[Full write-up](docs/recherche/campagnes/BASELINE_PPO_29082026_le_mur_n_existe_pas.md).

Across **20 seeds × 1500 simulated days** on a reproducible bench, **100 % [84–100]** of
agents reach level 4 of the 15-level curriculum, and **20 % [8–42]** now hold level 5 — up
to 1078 nights on it. Before the v41.16 fix, level 4 was reached by **0 % [0–16]**.
**Reproduced on v41.29** (10 seeds × 1500 days, full curriculum, no forced env): 10/10 reach
level 4, 2/10 reach level 5 — so the earlier "natal lottery" reading of a single lucky seed
was wrong. ⚠️ **But nothing is learned on the level reached**: the mastery trend over ~700
days is **never positive** (−0.44 pt `t=−0.26`; −4.57 `t=−2.85` SIG; −4.78 `t=−1.95`), and
both level-5 crossings came through the "2 consecutive wins" route, never through the 60 %
mastery gate. n=10, below the project's 20-seed bar — a tendency, not a conclusion.
⚠️ They hold `LavaGap` **without having learned what lava is**: its learned valence stays
**positive** (+0.07), indistinguishable from water. `SimpleCrossing`
and everything beyond remain unsolved.
⚠️ v41.25 closes the loop that made this *structurally* impossible: heat now enters the
homeostatic deficit as `+T²`, so walking into lava costs **r_bio = −0.791** instead of
MiniGrid's `0.0` (measured by the engine itself; an earlier `−1.000` figure was a
measurement error — the pain was cancelling itself out, fixed in v41.25-fix1). Whether that actually teaches avoidance is **being measured** (20 seeds
× 2 arms, forced `LavaGap` bench) — at 5 days the deficit differs but behaviour does not.

> ✅ **This block used to read "until the baseline row is filled, the comparison proves
> nothing".** It is filled now — see the table above. The reader can finally tell an elegant
> architecture from an underperforming one, and on this task the answer is unflattering.

---

## Architecture

### Two decision systems, one shared state

**C1 (reflex)** compresses all senses into `pensee_bio` and emits motor logits at near-zero cost.
**C2 (neocortex)** runs a multi-horizon mental rollout through the JEPA world model — and only
ever sees the state C1 already compressed. Never raw pixels, never the environment.

```python
logits_final = (c1_logits × gain_c1) + (c2_values × planning_force)
```

C2 is consulted **every tick**. There is no confidence threshold, no short-circuit — a design
constraint the project has refused four times, because a threshold in the decision path is a
hard-coded rule masquerading as a mechanism.

### Nothing is hard-coded — levels, not thresholds

The recurring principle: **constants are bounds; values are derived from what the agent has
lived.**

The clearest example is `reference_choc_dopamine`, the scale against which an event is judged
significant. It is not a threshold — it is a running level, ratcheted (fast up, ~50× slower
down), persisted in the brain file:

| Agent | Its reference | Credit given to a 0.1 shock |
|---|---|---|
| Beginner (has only known micro-progress) | 0.100 | **100 %** |
| Same agent, after 200 days of wins | 0.879 | **11.4 %** |

The same event is **8.8× less remarkable** to the expert. No rule says so; the level moved.

The memory works the same way: the brain never learns that "key" or "lava" exist. Labels stay
**opaque**, derived from the environment API, and a location's value is *learned* from
accumulated dopamine shocks — never declared.

### A body that gets hungry — the two-stage metabolism (v41.2, experimental)

**Satiety is a *stock*; energy is the *flow*.** Only energy is spent to act; food and water
merely replenish it, through a digestion whose throughput is capped. This decoupling makes two
states representable that a single gauge cannot: a full stomach with low energy, and hunger with
energy still to spare.

Death follows from **insolvency**, never from a threshold test:

```python
mobilisable_reserve = satiety × conversion_yield
```

Resting lowers expenditure but **creates no matter**. An empty stomach means nothing to mobilise,
so energy keeps falling whatever the agent does. There is no `if resting and starving then die`
anywhere — measured: resting without eating dies at tick 411, full activity at tick 319. **Rest
delays death without preventing it.**

Energy modulates the whole decision path through one derived quantity, `vigour = energy ** κ` —
a power, not a threshold, so degradation is continuous but *accelerating*:

| Energy | Vigour | C1's voice | C2's voice |
|---|---|---|---|
| 1.00 | 1.000 | 100 % | 100 % |
| **0.50** | **0.250** | **25 %** | **6 %** |
| 0.00 | **0.150** (floor) | 15 % | 2 % |

**Deliberation dies before reflex does** — an exhausted organism stops simulating the future long
before it stops walking. The floor is not decorative: without it, vigour → 0 zeroes *both* voices,
all logits become null and the action turns **random**. A dying agent must stay coherent.

Eating is an **act**, not a side effect of walking: it costs the most expensive action in the
budget, and the relief it brings is credited to the gesture that produced it.

| State | Eating yields |
|---|---|
| **Starving** | **+0.7945** |
| Moderate | +0.1267 |
| **Sated** | **−0.0227** |

Eating when full is *punished* — the gain is nil and the gesture costs. No rule forbids it; the
body handles it. Surplus above the ceiling becomes **fat**, remobilised in lean times: an agent
that stocked for 6 good days survives a fast **twice as long** as one living day to day.

⚠️ **Not yet working**: the agent plays the eating gesture 58 times a day (17 % of its ticks) at
~12 % accuracy, flat over 65 days. Its expected value (**+0.033**) sits at the same order as the
tick's own noise — and missing costs almost nothing, so spraying the gesture is *rational*.

### Day/night synaptic plasticity

Each layer holds a frozen `base_weight` and a daytime `annexe_weight`. Every night: consolidate,
erode geometrically (protected by myelin, which can come **only** from gradient), prune, and
occasionally grow.

```python
myeline_M   = max(myeline_M, |annexe_weight|)        # refreshed before use (v37.0-fix)
base       += annexe                                  # consolidation
scale       = max(historical, quantile(myeline_M, .75))   # relative, not absolute (v37.0-fix)
base       *= 1 − λ(1 − clamp(myeline_M / scale, 0, 1))   # erosion
base       *= clamp(birth_norm × 0.10 / ‖base‖, min=1.0)  # vital floor, never a ceiling
```

Each of those three `v37.0-fix` markers is a bug that made learning **mathematically impossible**
and went undetected for hundreds of simulated days. See the [diagnostic](docs/recherche/dia_Aout_2026.md)
§9 for the full list of diagnostic errors, measured and corrected.

### Repository layout

```
src/naulthene/
├── cerveau/        core: colab.py (reference), persistance.py, bus_sensoriel.py
├── salles_de_classe/  training curricula (15 MiniGrid levels + vocal)
├── cuve/           client/server: a persistent brain in "cryostasis"
├── audio/          formants, MFCC, synthesis, Whisper
├── exocortex/      C3 port — ⚠️ DEAD at runtime: no plug is ever registered, so
│                   ACTION_DEMANDER stays masked to -inf and action 7 appears in
│                   zero run logs. Kept only because DIM_EXO (8) and num_actions (8)
│                   are baked into the weight shapes — removing them would break
│                   every existing .brain. Costs 8 null input dims, nothing else.
└── instruments/    read-only probes: ablation bench, C1/C2, weights, gradients, reward
```

> ✅ **Since v39 (14 Aug 2026), `src/naulthene/cerveau/noyau.py` is versioned.** It carries every
> mechanic from v34 to v39 and used to be gitignored — four months of work in a single copy on a
> single disk. It remains the *experimental* core (`colab.py` is still the reference script), but
> an accident no longer erases it.

---

## Running it

```bash
pip install torch gymnasium minigrid wandb numpy

# Main curriculum (1300 days ≈ 520k ticks)
WANDB_MODE=offline PYTHONPATH=src python -m naulthene.salles_de_classe.cursus_developpemental \
    --jours 1300 --brain "brains/$(date +%d%m%Y%H%M)_V37_1300_RMD.brain"

# Read-only diagnostics on a trained brain
PYTHONPATH=src python -m naulthene.instruments.sonde_c1_c2 <brain> <env_id>
PYTHONPATH=src python -m naulthene.instruments.sonde_poids <brain>
```

Full command reference and troubleshooting: [docs/fonctionnement/LANCEMENT.md](docs/fonctionnement/LANCEMENT.md).

### Following the experiments

Every run is logged to **[Weights & Biases → `Naulthene-AGI`](https://wandb.ai/naultadrien123-nvnc/Naulthene-AGI)**,
public and unfiltered — the failed runs are there too, because they are where the diagnostics
came from.

Roughly 90 metrics per simulated night. The ones worth watching:

| Metric | What it tells you |
|---|---|
| `Cursus_Niveau_Index` | Curriculum progress — plateaus at **4** on 100 % of seeds since v41.16; the only question a run can answer is whether it crosses to 5 |
| `Victoire_Taux_Vie` | Lifetime win rate — ⚠️ **noisy**: in-run mastery explains only 16 % of the variance of bench competence (v41.45); never read it alone, always next to a forced-bench score |
| `Arbitrage_Ratio_C2C1` / `Arbitrage_Accord` | Balance and agreement between the reflex and the neocortex |
| `Distillation_Reference_Choc` | The agent's own bar for what counts as remarkable — should rise with maturity |
| `Memoire_Confirmations_Moy` | Abstraction by recurrence — 108 confirmations per landmark |
| `Erreur_JEPA` | World-model prediction error |
| `Teneur_Dopamine`, `Bio_Deficit` | Motivation reservoir and metabolic state |
| `Sens_Odorat_Taux_Approche` | Does the agent actually follow smell gradients? (63.4 %, chance = 50 %) |
| `Synapses_Mortes`, `Taille_Thalamus` | Synaptic death count and neurogenesis |

---

## What actually works — measured over 1300 days

| Mechanism | Evidence |
|---|---|
| Synaptic plasticity (v37) | Layers at vital floor: **5/12 → 1/12**; **zero** dead synapses |
| Adaptive dreaming | **15–18 %** of each day replayed, 70 replays/night |
| C1/C2 balance (v37.0) | Amplitude ratio **0.58–1.12**, down from 9.9–22.1× |
| Memory abstraction (v36.0) | **108** confirmations per landmark, **73 %** recall rate |
| Topological smell (v32.0) | **63.4 %** approach rate (chance = 50 %) |
| Neurogenesis | Bus grew 16 → 64 dimensions |
| Vocal curriculum | Stage **19** — the only curriculum still progressing |

---

## Roadmap

**Done — the thesis is falsifiable.** The three benchmark tables above are filled
(29 Aug 2026), and the verdict is unflattering: a PPO 4× lighter succeeds 2.3× better.
⚠️ *An earlier version of this line still asked for those tables to be run.*

**Now — re-run the bench with the corrected instrument.** Every bench figure from 30-31 Aug
was measured with the working memory silently disconnected (v41.47). The 20-brain replay is
in progress (`brains/02092026_rejeu_banc_corrige/`); until it lands, `r(directedness,
success) = −0.82` is **not established**.

**Next — the conversion problem, not the signal problem.** Twenty-one refutations say the
learning signal and the available information are not the bottleneck; what fails is turning
information into a policy (entropy 1.93 vs 1.67 for PPO). Whatever comes next must act on
*how the motor head decides*, and must be measured against the `≤ 6×` directedness target
fixed before the run. ⚠️ *The patience lever once listed here (120 → 256 ticks) is obsolete:
v41.30 removed `PATIENCE_MAX` and derived patience from the world's own `max_steps`.*

**Then — cross-modal binding.** All senses already enter the same bus simultaneously, including
inactive ones. The design document
([`docs/ameliorations/les_sens_combinatoire.md`](docs/ameliorations/les_sens_combinatoire.md)) covers the ten sensory pairs
and the hard constraint: **the system must keep working with a single sense**, accepting that
survival odds drop with each one lost.

**Long term — Apple Silicon.** A generalist intelligence on one chip, no datacenter. The current
artifact is 0.21 MB and runs on `mps` today; the distance from here to that goal is enormous, and
this line is a direction, not a promise.

---

## Status — work in progress, openly

Exploratory research, single author, **actively under development**. No test suite, no CI —
validation is by W&B curves, console logs and read-only probes.

What that means concretely:

- The agent now reaches **level 4 of 15** on **100 %** of seeds [84–100] and **holds level
  5** on 20 % [8–42] (20 seeds × 1500 simulated days). Before the v41.16 brain-sparing fix,
  level 4 was reached by **0 %** [0–16]. **Reproduced 20 Aug 2026** on the full curriculum
  (10 seeds × 1500 days): **10/10 reach level 4**, 2/10 reach level 5.
- **⚠️ The blockage did not disappear — it MOVED to level 4, and its cause is now measured.**
  Nothing is learned on the level reached: the mastery trend over ~700 days is **never
  positive** (−0.44 pt `t=−0.26`; −4.57 `t=−2.85` SIG; −4.78 `t=−1.95`). More time does not
  help — the "it just needs more days" hypothesis is contradicted by 700 days of data.
  ⚠️ **This bullet used to continue "and the cause is not cognitive — `mastery ~ mean energy`
  gives r = +0.710 (SIG)". That claim is RETRACTED (29 Aug 2026):** it was measured at n=10;
  at **n=20** the correlation is **−0.0588 (`t = −0.25`)**. The seeds that eat are *not* the
  seeds that master. Resource density is not the culprit either — it is constant per cell
  across levels (0.286 → 0.293). **No measured cause survives.**
- **⚠️ Three posed constants describe the same August-2026 agent, and must go.**
  `EPISODES_PAR_JOURNEE_REFERENCE = 4.0` sets the entire metabolic rhythm; it equals
  `400 ticks / patience ~95`, the patience of a **newborn** agent. Measured today: real
  patience is **258 ticks** (`t = +9.55`), the agent plays **1.55 episodes/day** against the
  4.0 assumed, and the gap **widens** over a run (×1.68 → ×2.58) because patience ratchets up
  and never comes back down. Worse, **9 seeds out of 10 sit at the exact `PATIENCE_MAX = 350`
  ceiling**: the current mechanism grants a **constant** +10 per willpower-win until the wall,
  then **nothing** — 30 wins saturate it, and 1200 days change nothing after that.
- **v41.30 removes all three.** Patience becomes a **trait of the agent's whole life**:
  `patience = patience_min × exp(capital)`, each gain adding `contrast / (1 + capital)` —
  **unbounded, with a decaying return** (measured: +1.00 → +0.50 → +0.40 → +0.34 → +0.31).
  The gain no longer counts *events* (+10 per win regardless of difficulty) but measures the
  **gap between how long success takes and how long the agent waits before quitting**: succeed
  in 80 ticks while quitting at 100 and more patience buys nothing, so nothing is granted. The
  ceiling is not another number — it comes from the **world** (`max_steps`, which MiniGrid
  enforces anyway; the patiences observed in v41.29 — 100 · 144 · 256 · 324 — *are* those
  `max_steps`). The metabolic need now reads `episodes_jour`, a quantity the code already
  measured and logged. The life-long EMA is **never reset on promotion**: verified, clearing
  the sliding window leaves patience unchanged (471.9 → 471.9).
- **🔴 The first measurement was unfavourable — and it found a real design fault.** A 3-seed ×
  3-arm × 10-day isolation bench, run immediately: energy **0.1968 derived vs 0.2651 fossil**
  (−0.068). Cutting the new patience changed **literally nothing** (bit-identical runs), so the
  whole gap came from the **metabolic rhythm** — which is exactly what keeping the two ablation
  flags separate was for.
- **The fault: the WORLD had been indexed on the agent's METABOLISM.** Two corrections.
  **(fix1)** Resource density was derived from the need, so a slower agent made food
  *physically vanish* from the grid — 2 sources instead of 6 from day one. Early on the policy
  is near-random, so survival depends on **spatial density**, not nutritional value: quadrupling
  what an apple is worth compensates nothing if you are less likely to step on one. Density now
  derives from **surface area** alone (measured per cell: 0.286 · 0.324 · 0.341 across levels),
  and both arms place identical resources. **(fix2)** The portion itself derived from the
  rhythm — but satiety is capped at 1.0 and the overflow **discarded**, while digestion is
  charged on the **whole** portion: at rhythm 1.0 a meal was 3.175, of which **2.175 was thrown
  away** for a **×4 digestive cost** (0.476 vs 0.119). A portion is a property of the *resource*,
  not of the agent's schedule; it now derives from stomach capacity (waste: **0.000**). The
  lived rhythm was meant to set only what remains physiological — the **drain rate**.
  ⚠️ **It does not: `taux_satiete` is a dead variable.** Nothing subtracts it — v41.2 replaced
  it with digestion and left it without a consumer (verified: a fasting agent loses 0.083333
  of satiety over 10 ticks, exactly `debit_digestif / RENDEMENT_CONVERSION`, not the 0.017500
  that rate would produce). The real regulator is **`DEBIT_DIGESTIF_JOUR`**, forcing a drain of
  **3.333 stomachs/day identical in both arms** — which fully explains why energy does not move
  (`t = +1.40`, NS). The agent eats **5.4 times a day** and still sits at 0.22 energy: its gut
  is calibrated for a hyper-expensive life it no longer leads.
  [Investigation](docs/recherche/METABOLISME_20082026_la_variable_morte.md).
- **After both fixes the sign flips: +0.0567** (0.3567 derived vs 0.3000 fossil), **3 seeds out
  of 3** favourable. ⚠️ **`t = +1.64` at n=3 is NOT significant** (threshold 4.30).
- **The full campaign found nothing — n=20, 40 runs × 1500 days.** The project's first
  measurement actually at its own 20-seed bar: energy **+0.011 (`t = +1.04`)**, vigour
  **+0.003**, mastery **+0.33**, C2/C1 ratio **+0.088 (`t = +0.63`, 9/20 seeds)**. All NS.
- **And the conditional analysis unmasked an artefact.** Splitting pairs by whether both arms
  reached the *same* level: **at equal regime (16 pairs) the effect vanishes and turns slightly
  negative — −0.065, `t = −0.44`, 5/16 favourable**. The four divergent pairs carry the entire
  positive gap. **Proof by sign**: in 3 of those 4, it is FOSSIL that holds the higher level,
  and the gap stays positive anyway — if the effect came from the arm, the sign would flip. It
  never does. What raises the C2/C1 ratio is being on a *different level from your twin*, not
  being in the derived arm. Level-4 crossing: **1/20 vs 2/20**, Fisher exact **p = 1.000**, and
  **no run out of 40 ever passed level 5**.
  ⚠️ At day 1046 on 5 seeds this same ratio showed `t = +3.68` on 5/5 and was reported as
  significant. It did not hold. **A `t` computed on a running job is a snapshot, not a
  measurement** — corrected here rather than quietly dropped.
  [Design note](docs/ameliorations/EPISODES_REFERENCE_20082026_la_derniere_constante_posee.md).
- **But it has not learned danger.** On the four level-5 brains, the learned valence of
  lava is **positive** (+0.068 to +0.081) and indistinguishable from water (+0.060 to
  +0.088), after up to 1078 nights spent on `LavaGap`. MiniGrid punishes death with exactly
  `0.0`, so no negative valence could ever form. The level is crossed by speed, not by
  understanding. **v41.25 removes that structural impossibility** — heat now enters the
  homeostatic deficit (`+T²`), making a step into lava cost `r_bio = −0.791`. Measured over
  **20 seeds × 2 arms**: the learned valence of lava flips to **−0.761 on 20/20 seeds**
  (control: +0.062 on 0/20, `t = −1066`), and the agent approaches danger **5.6 points
  less**. **But survival drops** — 8.57 % [8.19–8.96] → 6.71 % [6.19–7.27], non-overlapping
  intervals. The agent dies **2.4× less** and wins **2.9× less**: on `LavaGap` the goal sits
  *behind* the lava, so fleeing danger means fleeing the objective. **Fear alone does not
  produce competence.**
  ⚠️ A first version of this fix was **entirely inoperative** — the pain appeared on both
  sides of a subtraction and cancelled to exactly `0.000000`.
- **Why fear cost performance — measured, not assumed.** `pain = T²` is continuous and
  **never zero**: 100 % of free cells carry heat > 0.10, 77 % carry > 0.25. The agent had
  **no place to rest**, so it fled permanently — and on these maps food sits ~1.2 cells
  from the lava. Result: **−25 % food harvested**, on two maps with nothing in common
  (`LavaGap` −26 %, `LavaCrossing` −25 %), hence low energy, vigour at its floor, C2
  silenced. The cause is **behavioural, not metabolic**: heat never touches energy,
  satiety or expenditure. **v41.26** replaces `T²` with a graded pain — a perception
  threshold derived from the agent's own habituation (a true zero, not an epsilon), a
  cubic rise, and a burn that **accumulates while you stay and dissipates when you
  leave**. **Measured: it failed** — the burn saturated at `peak/decay` (×6.67), so pain
  reached 0.24 in real runs against 0.087 on the bench, and harvest stayed at −22.8 %.
- **v41.27 rebuilds pain as a single body state.** There were two unrelated pains: a
  hardcoded `−0.01` for walls (in the reward) and `heat²` for fire (in the deficit). Now
  one state, fed by (peak, half-life) couples the *senses* supply — burn recovers over
  60 ticks, a wall impact over 5, and impact pain scales with **speed**. The core receives
  two numbers and never learns what hurt it. The hardcoded `−0.01` — one of the four posed
  rewards flagged by the dogma audit, and the one that made *dying cheaper than bumping
  into a wall* — **is gone**. Heat is now a **state maintained by the source**: the body
  evacuates it and only burns above its capacity, so distance sets the *equilibrium* pain
  (d≥2 → 0.000, d=1 → 0.166, inside → 0.806) instead of a permanent ache everywhere.
  Under test on three arms.
- **Growing the brain changes nothing**: across three campaigns (96 → 160 → 512 dims) the
  level reached is identical, while energy drops 11× and effort triples.
- **The bench itself was broken until v41.9.** `env.reset()` was never seeded, so two runs of
  the same seed saw different worlds. **Every paired comparison in this project's history is
  therefore inconclusive** — they are not wrong, they establish nothing. Fixed and verified by
  an A/A test (bit-identical runs).
- **C2, the deliberative system, is causally disconnected**: severing it changes the score by
  **0.0 points on all six levels** (78-cell ablation), and C1/C2 agreement decays to 0.5 %.
  A scan of 20 brains found C2 is **36 % larger in the agents that fail**.
- **Nineteen cognitive mechanics tested, eighteen without demonstrated benefit.** The only
  levers that ever worked were properties of the *world*, not of the brain.
- 🔴 **The suspect list is empty (29 Aug 2026).** The last standing hypothesis —
  `mastery ~ energy`, `r = +0.710` at n=10 — collapses to **r = −0.0588 (`t = −0.25`)** at
  n=20. Nothing in this repository currently predicts why the agent plateaus at level 4.
  That is a worse position to be in, and a more honest one.
- The **v34–v39 mechanics are now in this repository** (`noyau.py` was versioned on 14 Aug 2026,
  closing the project's #1 structural risk).
- ✅ **All three benchmark tables are now filled** (29 Aug 2026). The one that mattered most —
  the PPO comparison — took 60 runs and a deterministic bench (δ_A/A = 0.000000). Its verdict:
  a PPO **4× lighter** than Naulthène's RL core succeeds **2.3× better**, so the plateau is a
  pathology of this architecture, not a wall in MiniGrid.
- The thesis defended here is **unification**, which is measured. Lightness is *not* yet
  demonstrated — Naulthène is currently 2.87× heavier than a PPO CNN baseline, and this README
  says so.

Everything that is broken is written down, including the diagnostic errors made along the way.
[**Read the diagnostic**](docs/recherche/dia_Aout_2026.md) — it is more useful than this README.
