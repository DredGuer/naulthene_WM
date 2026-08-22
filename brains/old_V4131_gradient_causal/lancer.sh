#!/bin/bash
# v41.31 — GRADIENT CAUSAL, banc force sur SimpleCrossingS9N1 (le mur du niveau 4).
# Juge de paix : taux de franchissement du niveau 4 (reference 7,5% = 3/40 sur v41.30).
# L'axe 2 (tube digestif) a ete RETIRE : seuls les axes 1 (gradient) et 3 (detecteur)
# sont testes, pour que le signal reste pur.
S="/private/tmp/claude-501/-Users-dredguer-Documents-1--Dossier-personnel-important-1--Adrien-21--AGI/aff01131-0ff1-45ac-9909-eb2880a09fcb/scratchpad/v4131camp"
cd "/Users/dredguer/Documents/1. Dossier personnel important/1. Adrien/21. AGI"
JOURS=400; PAR=10; ENV="MiniGrid-SimpleCrossingS9N1-v0"
for g in $(seq 1 20); do
  for bras in CAUSAL TEMOIN; do
    while [ "$(jobs -rp | wc -l)" -ge $PAR ]; do sleep 15; done
    if [ "$bras" = "CAUSAL" ]; then
      WANDB_MODE=offline PYTHONPATH=src python3 -m naulthene.cerveau.noyau \
        --jours $JOURS --graine $g --no-wandb --env-force "$ENV" \
        --brain "$S/${bras}_g${g}.brain" > "$S/${bras}_g${g}.log" 2>&1 &
    else
      WANDB_MODE=offline PYTHONPATH=src python3 -m naulthene.cerveau.noyau \
        --jours $JOURS --graine $g --no-wandb --env-force "$ENV" \
        --gradient-non-filtre --detecteur-observation \
        --brain "$S/${bras}_g${g}.brain" > "$S/${bras}_g${g}.log" 2>&1 &
    fi
  done
done
wait; echo FINI > "$S/FINI.txt"
