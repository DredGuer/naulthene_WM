# Naulthène AGI

**A cognitive agent where every parameter lives in one unified vector space — no task-specific modules, no separate heads per skill, no orchestration layer.**

Vision, hearing, touch, smell, taste, motor control, a world model, episodic memory and speech
all read from and write to a **single latent bus**. Adding a sense means appending dimensions to
one vector, not bolting on a subsystem.

**55,232 parameters. 0.21 MB.** One `nn.Module`, twelve layers, twelve hundred simulated days of
continuous life.

*Long-term direction: a generalist intelligence that runs on a single Apple Silicon chip, with no
datacenter.*

> 🇫🇷 **[Documentation complète en français →](readme_fr.md)** (1500+ lines: architecture,
> formulas, full changelog v7 → v37)
> 🩺 **[System diagnostic, August 2026 →](docs/dia_Aout_2026.md)** (1300-day run: what works,
> what is blocked, what remains unknown)

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
| `integrateur_bio` (100 → 64) — 5 senses + homeostasis | 6,400 |
| `generateur_attente` (72 → 64) — JEPA world model | 4,608 |
| `generateur_attente_audio` (72 → 64) | 4,608 |
| `analyseur` (64 → 64) | 4,096 |
| `tete_motrice` (64 → 8) — C1 | 512 |
| `tete_vocale` (64 → 8) | 512 |
| `tete_requete` (64 → 5) — C3 routing | 320 |
| `cortex_prefrontal` (64 → 1) — C2 | 64 |
| **Total** | **55,232** (0.21 MB fp32) |

### Versus MiniGrid baselines — **the thesis does not yet hold on size**

| Architecture | Parameters | Ratio |
|---|---|---|
| `rl-starter-files` CNN actor-critic | 19,384 | Naulthène is **2.85× larger** |
| PPO `MlpPolicy` (SB3 default) | 27,784 | Naulthène is **1.99× larger** |
| `rl-starter-files` CNN + LSTM | 52,664 | Naulthène is **1.05×** — parity |

**Naulthène is not smaller than a standard RL baseline.** Stated plainly, because the numbers are
one `grep` away for any reader.

Two caveats, both measurable rather than rhetorical:

1. **The comparison is not like-for-like.** 24,768 of those parameters (45 %) buy things no
   MiniGrid baseline has: an audio/vocal hemisphere (13,440), a JEPA world model (4,608), a
   5-sense biological integrator (6,400), an exocortex port (320). The **strictly comparable RL
   core is 30,464 parameters** — 1.57× a CNN baseline, 0.58× a CNN+LSTM.
2. **Efficiency claims require equal-budget comparison**, and that experiment has not been run.

### Task performance — **currently blocked**

| Metric | Value (1300-day run) |
|---|---|
| Curriculum level reached | **2 / 15** (`Empty-8x8`) |
| Lifetime win rate | **1.69 %** |
| Days since last win | 678 |

A standard PPO solves `Empty-8x8` in a few thousand episodes. **Naulthène currently does not.**

The [diagnostic](docs/dia_Aout_2026.md) isolates why, and none of the five blockers is cognitive:
patience capped at 120 ticks against MiniGrid's own 256 (reachable success rate 4.7 % vs 21.0 %),
a ×10 difficulty jump at level 2, an episode expected value of **−1.06**, four of seven actions
inert on empty rooms, and a curriculum era that doubles losing episodes.

---

## What the benchmark must show

The three tables below are the ones that would turn the thesis into a result. **They are empty
because the experiments have not been run.**

### 1. Parameter efficiency at equal performance

| Agent | Params | `Empty-8x8` success | `DoorKey-5x5` success | Episodes to 80 % |
|---|---|---|---|---|
| PPO CNN (`rl-starter-files`) | 19,384 | — | — | — |
| PPO + LSTM | 52,664 | — | — | — |
| **Naulthène** | **55,232** | — | — | — |

### 2. Memory footprint

| Agent | Training peak | Inference | Checkpoint |
|---|---|---|---|
| PPO CNN | — | — | — |
| **Naulthène** | — | — | 1.58 MB |

### 3. Sensory ablation — the unification test

The claim is that removing a sense degrades performance gracefully, with no code path change.
[`banc_ablation.py`](src/naulthene/instruments/banc_ablation.py) already runs 13 lesions across 5
levels; the numbers below are what it should produce.

| Lesion | Success rate | Δ vs intact |
|---|---|---|
| Intact | — | — |
| No vision | — | — |
| No hearing | — | — |
| No smell | — | — |
| No C2 (planning) | — | — |

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
and went undetected for hundreds of simulated days. See the [diagnostic](docs/dia_Aout_2026.md)
§9 for the full list of diagnostic errors, measured and corrected.

### Repository layout

```
src/naulthene/
├── cerveau/        core: colab.py (reference), persistance.py, bus_sensoriel.py
├── salles_de_classe/  training curricula (15 MiniGrid levels + vocal)
├── cuve/           client/server: a persistent brain in "cryostasis"
├── audio/          formants, MFCC, synthesis, Whisper
├── exocortex/      C3 port — pluggable external senses (LLM/RAG, APIs, IoT)
└── instruments/    read-only probes: ablation bench, C1/C2, weights, gradients, reward
```

> ⚠️ `src/naulthene/cerveau/noyau.py` — the local experimental core carrying every mechanic from
> v34 to v37 — is **gitignored**. This repository holds the documentation, `persistance.py` and
> the instruments; **the v34–v37 mechanics themselves live only on the author's machine.**

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

Full command reference and troubleshooting: [docs/LANCEMENT.md](docs/LANCEMENT.md).

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
([`docs/les_sens_combinatoire.md`](docs/les_sens_combinatoire.md)) covers the ten sensory pairs
and the hard constraint: **the system must keep working with a single sense**, accepting that
survival odds drop with each one lost.

**Long term — Apple Silicon.** A generalist intelligence on one chip, no datacenter. The current
artifact is 0.21 MB and runs on `mps` today; the distance from here to that goal is enormous, and
this line is a direction, not a promise.

---

## Status

Exploratory research, single author. No test suite, no CI — validation is by W&B curves, console
logs and read-only probes. The agent is **blocked at level 2 of 15** and the reasons are
[documented in full](docs/dia_Aout_2026.md), including the diagnostic mistakes made along the way.

If you read one supporting document, read that one. It is more useful than this README.
