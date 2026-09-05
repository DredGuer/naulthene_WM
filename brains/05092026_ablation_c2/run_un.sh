#!/bin/zsh
# Un run. Args: <graine> <bras>
#
# ⚠️ zsh ne fait PAS de word-splitting sur l'expansion d'une variable (contrairement a bash) :
# `FLAGS="--a --b"` puis `python ... $FLAGS` passe UN SEUL argument "--a --b", qu'argparse
# rejette en listant pourtant les deux options comme valides. D'ou le TABLEAU ci-dessous.
cd "$(dirname "$0")/../.."
g=$1; bras=$2; D=brains/05092026_ablation_c2
L="$D/${bras}_g${g}.log"; B="$D/${bras}_g${g}.brain"
if [ -f "$L" ] && grep -q "Jour 1500" "$L" 2>/dev/null; then echo "SKIP ${bras}_g${g}"; exit 0; fi
case "$bras" in
  LIBRE_SANS_C2)  FLAGS=(--gain-c1-libre --sans-c2) ;;
  TEMOIN_SANS_C2) FLAGS=(--sans-c2) ;;
  *) echo "!! bras inconnu: $bras"; exit 2 ;;
esac
WANDB_MODE=offline PYTHONPATH=src python -m naulthene.cerveau.noyau \
  --graine $g --jours 1500 "${FLAGS[@]}" --no-wandb --brain "$B" > "$L" 2>&1
# Le run est-il alle au bout ?
grep -q "Jour 1500" "$L" || { echo "!! ${bras}_g${g} : run INCOMPLET"; exit 6; }
# Les drapeaux ont-ils atteint l'individu ? (leçon v41.4)
grep -q "ABLATION\] C2 MUET" "$L" || { echo "!! ${bras}_g${g} : ablation NON atteinte"; exit 3; }
if [ "$bras" = "LIBRE_SANS_C2" ]; then
  grep -q "BRAS A\] voix libre" "$L" || { echo "!! ${bras}_g${g} : voix libre NON atteinte"; exit 4; }
else
  grep -q "BRAS A\] voix libre" "$L" && { echo "!! ${bras}_g${g} : CONTAMINE par la voix libre"; exit 5; }
fi
echo "OK ${bras}_g${g}"
