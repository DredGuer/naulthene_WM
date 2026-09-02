#!/bin/zsh
# Banc du bras A : 300 épisodes, force = acceptation() du cerveau (défaut v41.50).
cd "/Users/dredguer/Documents/1. Dossier personnel important/1. Adrien/21. AGI"
source venv/bin/activate
D=brains/02092026_brasA_voix_libre
for g in 11 22 33 44 55 66 77 88 99 111 122 133 144 155 166 177 188 199 211 222; do
  for bras in LIBRE TEMOIN; do
    B="$D/${bras}_g${g}.brain"; J="$D/banc_${bras}_g${g}.json"
    [ -f "$B" ] || continue
    [ -f "$J" ] && continue
    WANDB_MODE=offline PYTHONPATH=src python -m naulthene.instruments.sonde_plancher_geometrique \
        --brain "$B" --episodes 300 --json "$J" > "$D/banc_${bras}_g${g}.log" 2>&1
    echo "banc ${bras}_g${g}"
  done
done
echo "BANC TERMINE"
