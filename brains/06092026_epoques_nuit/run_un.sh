#!/bin/zsh
# Un run de la campagne des epoques. Argument : "BRAS:GRAINE"
cd "/Users/dredguer/Documents/1. Dossier personnel important/1. Adrien/21. AGI"
D=brains/06092026_epoques_nuit
BRAS="${1%%:*}"; G="${1##*:}"
LOG="$D/${BRAS}_g${G}.log"; BR="$D/${BRAS}_g${G}.brain"
# garde de reprise : un run DEJA TERMINE n'est pas relance. On verifie l'ARRIVEE
# (Jour 1500), jamais la seule existence du log — un run mort en 2 s a un log lui aussi.
if [ -f "$LOG" ] && grep -q "Jour 1500" "$LOG"; then echo "SKIP $BRAS g$G"; exit 0; fi
# ⚠️ zsh ne decoupe PAS une variable en mots : un FLAGS="a b" passerait UN argument.
case "$BRAS" in
  K8_NU)   FLAGS=(--epoques-nuit 8) ;;
  K8_CLIP) FLAGS=(--epoques-nuit 8 --ratio-clippe) ;;
  *) echo "bras inconnu: $BRAS"; exit 1 ;;
esac
WANDB_MODE=offline PYTHONPATH=src python3 -m naulthene.cerveau.noyau \
    --graine "$G" --jours 1500 --gain-c1-libre "${FLAGS[@]}" \
    --brain "$BR" > "$LOG" 2>&1
echo "OK $BRAS g$G"
