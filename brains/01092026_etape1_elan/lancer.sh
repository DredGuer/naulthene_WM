#!/bin/zsh
cd "/Users/dredguer/Documents/1. Dossier personnel important/1. Adrien/21. AGI"
D=brains/01092026_etape1_elan
for g in 11 22 33 44 55 66 77 88 99 111 122 133 144 155 166 177 188 199 211 222; do
  for bras in ACTIF TEMOIN; do
    [ -f "$D/${bras}_g${g}.brain" ] && continue
    FLAG=""; [ "$bras" = "TEMOIN" ] && FLAG="--sans-elan"
    WANDB_MODE=offline PYTHONPATH=src python -m naulthene.cerveau.noyau \
        --graine $g --jours 100 --env-force MiniGrid-SimpleCrossingS9N1-v0 $FLAG \
        --brain "$D/${bras}_g${g}.brain" > "$D/${bras}_g${g}.log" 2>&1
    echo "fait ${bras}_g${g}"
  done
done
echo "ETAPE1 ELAN TERMINEE"
