#!/bin/zsh
# ⚠️ TOURNE SUR LE WORKTREE v41.47 (commit 2d69b40) : DIM_VECTEUR_BIO = 42, donc AUCUNE
# greffe des cerveaux historiques, et memoire de travail deja corrigee en penser()[4].
# C'est la SEULE combinaison qui isole la correction d'instrument de tout le reste.
cd /tmp/naulthene_v4147
R="/Users/dredguer/Documents/1. Dossier personnel important/1. Adrien/21. AGI"
D="$R/brains/02092026_rejeu_banc_corrige"
S="$R/brains/26082026_v4132_AB3_cursus"
for c in A_g155 A_g122 A_g166 A_g66 A_g11 A_g111 A_g133 A_g144 A_g177 A_g188 \
         A_g222 A_g33 A_g44 A_g77 B_g11 B_g122 B_g144 B_g188 B_g211 B_g44; do
  [ -f "$D/banc_$c.json" ] && continue
  WANDB_MODE=offline PYTHONPATH=src python -m naulthene.instruments.sonde_plancher_geometrique \
      --brain "$S/$c.brain" --episodes 300 --json "$D/banc_$c.json" > /dev/null 2>&1
  echo "rejoue $c"
done
echo "REJEU TERMINE"
