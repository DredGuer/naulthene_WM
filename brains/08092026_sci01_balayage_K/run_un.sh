#!/bin/zsh
# SCI-01 — un run par (bras, graine). Vagues de 6 en parallèle.
# Usage : zsh run_un.sh <BRAS> <GRAINE>
cd "/Users/dredguer/Documents/1. Dossier personnel important/1. Adrien/21. AGI"
D=brains/08092026_sci01_balayage_K
ARM="$1"; G="$2"
mkdir -p "$D/$ARM"
LOG="$D/$ARM/${ARM}_g${G}.log"; BR="$D/$ARM/${ARM}_g${G}.brain"
if [ -f "$LOG" ] && grep -q "Jour 1500" "$LOG"; then echo "SKIP $ARM g$G"; exit 0; fi

case "$ARM" in
  K1_TEMOIN)  EXTRA="--epoques-nuit 1" ;;
  K2_NU)      EXTRA="--epoques-nuit 2" ;;
  K4_NU)      EXTRA="--epoques-nuit 4" ;;
  K8_NU)      EXTRA="--epoques-nuit 8" ;;
  K16_NU)     EXTRA="--epoques-nuit 16" ;;
  K8_CLIP_e02) EXTRA="--epoques-nuit 8 --ratio-clippe" ;;
  *) echo "BRAS INCONNU: $ARM"; exit 2 ;;
esac

WANDB_MODE=offline PYTHONPATH=src venv/bin/python3 -m naulthene.cerveau.noyau \
    --graine "$G" --jours 1500 --gain-c1-libre --detach-c2 $EXTRA \
    --brain "$BR" > "$LOG" 2>&1
echo "OK $ARM g$G" >> "$D/campagne.log"
