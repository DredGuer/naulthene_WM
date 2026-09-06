#!/bin/zsh
# 40 runs, 6 en parallele. xargs -P borne REELLEMENT le parallelisme (l'incident du
# 04/09 : un `while jobs -r` avait lance 41 runs simultanes au lieu de 6).
cd "/Users/dredguer/Documents/1. Dossier personnel important/1. Adrien/21. AGI"
D=brains/06092026_epoques_nuit
for g in 11 22 33 44 55 66 77 88 99 111 122 133 144 155 166 177 188 199 211 222; do
  echo "K8_NU:$g"; echo "K8_CLIP:$g"
done | xargs -P 6 -n 1 zsh "$D/run_un.sh"
echo "CAMPAGNE TERMINEE"
