# Naulthène AGI

**A cognitive agent where every parameter lives in one unified vector space — no task-specific modules, no separate heads per skill, no orchestration layer.**

Vision, hearing, touch, smell, taste, motor control, a world model, episodic memory and speech
all read from and write to a **single latent bus**. Adding a sense means appending dimensions to
one vector, not bolting on a subsystem.

**55,552 parameters. 0.21 MB.** One `nn.Module`, twelve layers, twelve hundred simulated days of
continuous life.

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
**four posed rewards**, ~25 calibration constants, and **food/water identified by colour**
(`"red"`/`"blue"`) inside the core. Full audit:
[dogma review](docs/etat_des_lieux/18082026_revue_dogme_avant_publication.md).

**⚠️ It does not work yet.** The agent clears 1 to 5 levels out of 6 depending on the random
seed — a **×69 variance between two identical runs**. Eight cognitive mechanisms have been
tested; eight failed. The only two levers that ever worked are properties of the *world*, not
of the brain.

**⚠️ And the benchmark itself was biased.** A code review on 13-14 August found that up to
**one map in two** was solvable without the key — the agent was passing a rigged exam. Fixed;
the task then became **50× harder** (random-policy success on `8x8`: 15.3 % → 0.3 %), so
prior results are **not comparable** to future ones. Full account:
[code review](docs/recherche/REVUE_CODE_v39_aout_2026.md).

Read this as a research log, not a released system. Everything broken is written down,
including [every diagnostic mistake](docs/recherche/recherche_bug_or_not_bug.md) — 15 of them so far.

*Long-term direction: a generalist intelligence that runs on a single Apple Silicon chip, with no
datacenter.*

> 🗂️ **[Documentation index →](docs/INDEX.md)** — which question leads to which document
> 🇫🇷 **[Miroir français complet →](readme_fr.md)** (architecture, formules, changelog v7 → v39)
> 🩺 **[System diagnostic, August 2026 →](docs/recherche/dia_Aout_2026.md)** (1300-day run: what works,
> what is blocked, what remains unknown)
> 📊 **[Live experiments on Weights & Biases →](https://wandb.ai/naultadrien123-nvnc/Naulthene-AGI)**
> (every run, every curve, including the failures)

**Author**: Adrien Nault ([@DredGuer](https://github.com/DredGuer)) — [Apache 2.0](LICENSE).
Any reuse, redistribution or derivative work building on this concept or architecture **must
credit Adrien Nault as the original author of Naulthène AGI** — see [NOTICE](NOTICE).

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

| Component | Parameters |
|---|---|
| `porte_visuelle` (147 → 64) | 9,408 |
| `porte_auditive` (130 → 64) | 8,320 |
| `hippocampe` (128 → 64) | 8,192 |
| `fusion_memoire` (128 → 64) | 8,192 |
| `integrateur_bio` (105 → 64) — 5 senses + homeostasis | 6,720 |
| `generateur_attente` (72 → 64) — JEPA world model | 4,608 |
| `generateur_attente_audio` (72 → 64) | 4,608 |
| `analyseur` (64 → 64) | 4,096 |
| `tete_motrice` (64 → 8) — C1 | 512 |
| `tete_vocale` (64 → 8) | 512 |
| `tete_requete` (64 → 5) — C3 routing ⚠️ **dead at runtime** | 320 |
| `cortex_prefrontal` (64 → 1) — C2 | 64 |
| **Total** | **55,552** (0.21 MB fp32) |

> ⚠️ **Corrected 21 Aug 2026.** This table previously read **55,232** with `integrateur_bio`
> at 100→64. Thermoception (v41.11) had grown the bio vector from 36 to **41** dimensions, so
> the layer is **105→64** and the total is **+320**. The count had not been re-measured since.
> Recounted with `sum(p.numel() for p in agent.parameters())`, never estimated. Full teardown:
> [anatomy of the core](docs/etat_des_lieux/21082026_anatomie_du_noyau.md).
>
> **What the split reveals**: **C2 — the deliberative system — is 64 parameters out of 55,552,
> i.e. 0.1 % of the brain.** All of deliberation is one 64→1 projection. Worth holding next to
> the ablation result ("severing C2 changes the score by 0.0 points"): perhaps C2 is not
> useless, it is *tiny*. Meanwhile the audio hemisphere weighs **13,440 parameters (24 %)** for
> a faculty no MiniGrid level exercises.

### Versus MiniGrid baselines — **the thesis does not yet hold on size**

| Architecture | Parameters | Ratio |
|---|---|---|
| `rl-starter-files` CNN actor-critic | 19,384 | Naulthène is **2.87× larger** |
| PPO `MlpPolicy` (SB3 default) | 27,784 | Naulthène is **2.00× larger** |
| `rl-starter-files` CNN + LSTM | 52,664 | Naulthène is **1.05×** — parity |

**Naulthène is not smaller than a standard RL baseline.** Stated plainly, because the numbers are
one `grep` away for any reader.

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
| Learned valence of lava | **+0.072 — POSITIVE**, barely distinct from water (+0.069). Nociception (v41.25) flips it to **−0.761 on 20/20 seeds** — but survival **drops** 8.6 % → 6.7 %, because pain was **non-zero everywhere** (77 % of cells) and the agent fled its own food supply (**−25 % harvest**, two maps). Graded pain (v41.26) under test |
| Cognitive mechanisms that improved anything | **1 out of 14 tested** — brain-sparing. Three pain models (v41.25/26/27) changed behaviour by **0 pt** (`t = −1.51`, n=20) |
| Navigation on an empty 5×5 room | **54.4 %** after 300 days vs **39.2 %** for a random policy *over the same 7 actions* — the agent **beats chance by 15 pts** |
| Ticks spent on gestures that change nothing (`Empty-5x5`) | **57.2 %** — because a sterile gesture cost **1.09** against **4.00** for the one gesture that moves toward the goal. **v41.28** charges the work *attempted*: pushing a wall now costs a full step. **Measured (n=20): −2.5 pts, `t = −1.71`, not significant** — the cost was not the lever |
| Effect of growing the brain (96 → 160 → 512 dims) | **none** across 3 campaigns — and energy drops 11× |
| **Why it plateaus at level 4** | **Not cognitive — metabolic.** `mastery ~ mean energy`: **r = +0.710**, `t = +2.85` (SIG, n=10). Three **posed constants** calibrate the metabolic rhythm for a *newborn* agent: the code assumes **4 episodes/day**, the agent plays **1.55**, and the gap **widens** over the run (×1.68 → ×2.58). **9 seeds out of 10 sit at the exact `PATIENCE_MAX = 350` ceiling** |
| **First cognitive effect that works** | **v41.31 — the causal gradient.** Masking the actor's gradient on non-transitions (`Σ m_t` denominator, critic/entropy/JEPA untouched): mastery **+2.57 pts** (`t = +2.68`), wins **+48 %** (55.0 vs 37.3), n=20 on a forced `SimpleCrossing` bench. **Falsification arm rejected**: amplifying the actor's gradient ×2.70 *without* filtering gives **nothing** (`p = 0.502`) — it is the **filtering**, not the gain. ⚠️ Sterile gestures do **not** drop, and **0/20** seeds reach the 60 % gate |
| Levers that did work | **3 — two properties of the world, one of the decision** |

A standard PPO solves `Empty-8x8` in a few thousand episodes. **Naulthène currently does not.**

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

> ⚠️ **Every paired comparison predating v41.9 is inconclusive — including the "0 out of 9"
> line above.** `env.reset()` was never seeded: MiniGrid draws its layouts from its own RNG,
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
[campaign notebook](docs/recherche/CAMPAGNE_v41_population_et_ablation_aout_2026.md).

### 2. Memory footprint — ✅ **measured for Naulthène**, baseline pending

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

### 3. Parameter efficiency at equal performance — ⏳ **not run**

This is the table that would decide whether the architecture is *efficient* or merely
*different*. It requires training PPO baselines on the same levels — not yet done.

| Agent | Params | `Empty-5x5` success | `DoorKey-5x5` success | Episodes to 80 % |
|---|---|---|---|---|
| PPO CNN (`rl-starter-files`) | 19,384 | — | — | — |
| PPO + LSTM | 52,664 | — | — | — |
| **Naulthène** | **55,552** | **44.7 %** (v41 bench, 300 ep.) | — | **never reached** |

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

> Naulthène's own numbers are filled in. Until the baseline row is too, the comparison proves
> nothing — a reader still cannot tell an elegant architecture from an underperforming one.

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
| `Cursus_Niveau_Index` | Curriculum progress — flat at 2 since day 274 |
| `Victoire_Taux_Vie` | Lifetime win rate — 1.69 % |
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

**Now — make the thesis falsifiable.** Run the three benchmark tables above. Without them, a
reader cannot distinguish "elegant and efficient" from "different and worse".

**Next — unblock the curriculum.** Five measured blockers, none cognitive. The best-measured
lever is patience: 120 → 256 ticks moves reachable success from 4.7 % to 21.0 %.

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
  help — the "it just needs more days" hypothesis is contradicted by 700 days of data. And
  the cause is **not cognitive**: `mastery ~ mean energy` gives **r = +0.710** (`t = +2.85`,
  SIG). The seeds that eat are the seeds that master. Resource density is *not* the culprit
  either — it is constant per cell across levels (0.286 → 0.293).
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
- **Nine cognitive mechanics tested, nine without demonstrated benefit** — but see the bench
  caveat above. The only two levers that ever worked were properties of the *world*, not of
  the brain.
- The **v34–v39 mechanics are now in this repository** (`noyau.py` was versioned on 14 Aug 2026,
  closing the project's #1 structural risk).
- Two of three benchmark tables are filled; the one that matters most (equal-budget comparison
  against PPO) **has not been run**.
- The thesis defended here is **unification**, which is measured. Lightness is *not* yet
  demonstrated — Naulthène is currently 2.87× heavier than a PPO CNN baseline, and this README
  says so.

Everything that is broken is written down, including the diagnostic errors made along the way.
[**Read the diagnostic**](docs/recherche/dia_Aout_2026.md) — it is more useful than this README.
