#!/bin/zsh
# Campagne AB3 — 20 graines appariées x 1440 jours x 2 bras = 40 runs.
# Lance par vagues de 8 pour ne pas saturer la machine (leçon du 25/08 : 9 processus
# simultanés faisaient échouer le chargement de libtorch).
cd "$(dirname "$0")/../.."
C=brains/26082026_v4132_AB3_cursus
GRAINES="11 22 33 44 55 66 77 88 99 111 122 133 144 155 166 177 188 199 211 222"
i=0
for g in ${=GRAINES}; do
  for bras in A B; do
    if [ "$bras" = "A" ]; then FLAG=""; else FLAG="--detach-c2"; fi
    WANDB_MODE=offline PYTHONPATH=src nohup python -m naulthene.cerveau.noyau \
        --graine $g --jours 1440 $FLAG \
        --brain "$C/${bras}_g${g}.brain" > "$C/${bras}_g${g}.log" 2>&1 &
    i=$((i+1))
    if [ $((i % 8)) -eq 0 ]; then wait; fi
  done
done
wait
echo "CAMPAGNE TERMINEE : $i runs"
