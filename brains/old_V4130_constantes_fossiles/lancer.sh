#!/bin/bash
# v41.30 — CAMPAGNE 20 GRAINES x 2 BRAS, cursus complet 1500 jours.
# Question : les trois constantes fossiles supprimees debloquent-elles la vigueur,
# donc C2, donc le franchissement du niveau 4 ?
S="/private/tmp/claude-501/-Users-dredguer-Documents-1--Dossier-personnel-important-1--Adrien-21--AGI/aff01131-0ff1-45ac-9909-eb2880a09fcb/scratchpad/v4130camp"
cd "/Users/dredguer/Documents/1. Dossier personnel important/1. Adrien/21. AGI"
JOURS=1500; PAR=10
for g in $(seq 1 20); do
  for bras in DERIVE FOSSILE; do
    while [ "$(jobs -rp | wc -l)" -ge $PAR ]; do sleep 15; done
    if [ "$bras" = "DERIVE" ]; then
      WANDB_MODE=offline PYTHONPATH=src python3 -m naulthene.cerveau.noyau \
        --jours $JOURS --graine $g --no-wandb \
        --brain "$S/${bras}_g${g}.brain" > "$S/${bras}_g${g}.log" 2>&1 &
    else
      WANDB_MODE=offline PYTHONPATH=src python3 -m naulthene.cerveau.noyau \
        --jours $JOURS --graine $g --no-wandb --patience-fossile --rythme-fossile \
        --brain "$S/${bras}_g${g}.brain" > "$S/${bras}_g${g}.log" 2>&1 &
    fi
  done
done
wait; echo FINI > "$S/FINI.txt"
