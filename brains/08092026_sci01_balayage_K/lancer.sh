#!/bin/bash
# SCI-01 — lance la campagne (vagues de 6 en parallèle), puis signale la fin.
# ⚠️ bash pour run_un.sh (découpage de $EXTRA en mots).
cd "/Users/dredguer/Documents/1. Dossier personnel important/1. Adrien/21. AGI"
D=brains/08092026_sci01_balayage_K
ARMS="K1_TEMOIN K2_NU K4_NU K8_NU K16_NU K8_CLIP_e02"
SEEDS="11 22 33 44 55 66 77 88 99 111 122 133 144 155 166 177 188 199 211 222"
[ -f "$D/campagne.log" ] && rm -f "$D/campagne.log"
for ARM in $ARMS; do for G in $SEEDS; do echo "$ARM $G"; done; done \
  | xargs -P 6 -n 2 bash "$D/run_un.sh"
echo "CAMPAGNE TERMINEE" >> "$D/campagne.log"
