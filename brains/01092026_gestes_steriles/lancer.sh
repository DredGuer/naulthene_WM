#!/bin/zsh
cd "/Users/dredguer/Documents/1. Dossier personnel important/1. Adrien/21. AGI"
D=brains/01092026_gestes_steriles
for c in A_g155 A_g122 A_g166 A_g66 A_g11 A_g111 A_g133 A_g144 A_g177 A_g188 A_g222 A_g33 A_g44 A_g77 B_g11 B_g122 B_g144 B_g188 B_g211 B_g44; do
  [ -f "$D/res_$c.json" ] && continue
  PYTHONPATH=src WANDB_MODE=offline python -m naulthene.instruments.sonde_gestes_steriles \
     --brain "brains/26082026_v4132_AB3_cursus/$c.brain" --episodes 60 \
     --json "$D/res_$c.json" 2>&1 | grep -v "^   \|^🚀\|^🧬"
done
echo "COHORTE TERMINEE"
