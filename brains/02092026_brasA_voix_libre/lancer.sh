#!/bin/zsh
# BRAS A — voix libre (v41.50). 20 graines appariées × 2 bras × 100 jours, banc forcé.
# ⚠️ Ne lancer QU'APRÈS la fin du rejeu (brains/02092026_rejeu_banc_corrige/, 20/20).
cd "/Users/dredguer/Documents/1. Dossier personnel important/1. Adrien/21. AGI"
source venv/bin/activate
D=brains/02092026_brasA_voix_libre
for g in 11 22 33 44 55 66 77 88 99 111 122 133 144 155 166 177 188 199 211 222; do
  for bras in LIBRE TEMOIN; do
    [ -f "$D/${bras}_g${g}.brain" ] && continue
    FLAG=""; [ "$bras" = "LIBRE" ] && FLAG="--gain-c1-libre"
    WANDB_MODE=offline PYTHONPATH=src python -m naulthene.cerveau.noyau \
        --graine $g --jours 100 --env-force MiniGrid-SimpleCrossingS9N1-v0 $FLAG \
        --brain "$D/${bras}_g${g}.brain" > "$D/${bras}_g${g}.log" 2>&1
    # le drapeau doit avoir atteint le module ET l'individu — sinon la campagne est invalide
    if [ "$bras" = "LIBRE" ]; then
      grep -q '\[BRAS A\] voix libre v41.50' "$D/${bras}_g${g}.log" || { echo "❌ drapeau absent ${bras}_g${g}"; exit 1; }
    else
      grep -q 'voix libre' "$D/${bras}_g${g}.log" && { echo "❌ témoin contaminé ${bras}_g${g}"; exit 1; }
    fi
    echo "fait ${bras}_g${g}"
  done
done
echo "BRAS A TERMINE"
