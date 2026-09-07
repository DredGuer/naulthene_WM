#!/bin/zsh
cd "/Users/dredguer/Documents/1. Dossier personnel important/1. Adrien/21. AGI"
D=brains/07092026_branches_persistantes
G="$1"
LOG="$D/BP_g${G}.log"; BR="$D/BP_g${G}.brain"
if [ -f "$LOG" ] && grep -q "Jour 1500" "$LOG"; then echo "SKIP g$G"; exit 0; fi
WANDB_MODE=offline PYTHONPATH=src python3 -m naulthene.cerveau.noyau \
    --graine "$G" --jours 1500 --gain-c1-libre --epoques-nuit 8 --branches-persistantes \
    --brain "$BR" > "$LOG" 2>&1
echo "OK g$G"
