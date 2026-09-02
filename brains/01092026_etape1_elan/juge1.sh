#!/bin/zsh
cd "/Users/dredguer/Documents/1. Dossier personnel important/1. Adrien/21. AGI"
D=brains/01092026_etape1_elan
for g in 11 22 33 44 55 66 77 88 99 111 122 133 144 155 166 177 188 199 211 222; do
  for bras in ACTIF TEMOIN; do
    J="$D/autocorr_${bras}_g${g}.json"
    [ -f "$J" ] && continue
    WANDB_MODE=offline PYTHONPATH=src python -m naulthene.instruments.sonde_autocorrelation_motrice \
        --brain "$D/${bras}_g${g}.brain" --episodes 40 --json "$J" 2>&1 | grep "ticks="
  done
done
echo "JUGE1 TERMINE"
