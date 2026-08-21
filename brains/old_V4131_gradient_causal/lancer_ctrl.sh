#!/bin/bash
# v41.31 — BRAS DE FALSIFICATION. Gradient acteur x2.70 (le T/Sm median mesure)
# SANS filtrage. Meme graines, meme carte, meme duree que CAUSAL et TEMOIN.
# Si le score egale CAUSAL -> le filtrage n'y est pour rien.
S="/private/tmp/claude-501/-Users-dredguer-Documents-1--Dossier-personnel-important-1--Adrien-21--AGI/aff01131-0ff1-45ac-9909-eb2880a09fcb/scratchpad/v4131camp"
cd "/Users/dredguer/Documents/1. Dossier personnel important/1. Adrien/21. AGI"
for g in $(seq 1 20); do
  while [ "$(jobs -rp | wc -l)" -ge 10 ]; do sleep 15; done
  WANDB_MODE=offline PYTHONPATH=src python3 -m naulthene.cerveau.noyau \
    --jours 400 --graine $g --no-wandb --env-force MiniGrid-SimpleCrossingS9N1-v0 \
    --gradient-non-filtre --detecteur-observation --gain-acteur 2.70 \
    --brain "$S/CTRL_g${g}.brain" > "$S/CTRL_g${g}.log" 2>&1 &
done
wait; echo FINI > "$S/CTRL_FINI.txt"
