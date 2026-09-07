#!/bin/zsh
cd "/Users/dredguer/Documents/1. Dossier personnel important/1. Adrien/21. AGI"
D=brains/07092026_branches_persistantes
for g in 11 22 33 44 55 66 77 88 99 111 122 133 144 155 166 177 188 199 211 222; do echo "$g"; done \
  | xargs -P 6 -n 1 zsh "$D/run_un.sh"
echo "CAMPAGNE TERMINEE"
