#!/bin/zsh
# Un run. Args: <graine> <bras>
cd "$(dirname "$0")/../.."
g=$1; bras=$2; D=brains/05092026_ablation_c2
L="$D/${bras}_g${g}.log"; B="$D/${bras}_g${g}.brain"
# Idempotence : ne pas refaire un run deja termine
if [ -f "$L" ] && grep -q "Jour 1500" "$L" 2>/dev/null; then echo "SKIP ${bras}_g${g}"; exit 0; fi
case "$bras" in
  LIBRE_SANS_C2)  FLAGS="--gain-c1-libre --sans-c2" ;;
  TEMOIN_SANS_C2) FLAGS="--sans-c2" ;;
  *) echo "bras inconnu: $bras"; exit 2 ;;
esac
WANDB_MODE=offline PYTHONPATH=src python -m naulthene.cerveau.noyau \
  --graine $g --jours 1500 $FLAGS --no-wandb --brain "$B" > "$L" 2>&1
# Verification post-run : le drapeau a atteint l'individu
grep -q "ABLATION\] C2 MUET" "$L" || { echo "!! ${bras}_g${g} : ablation NON atteinte"; exit 3; }
if [ "$bras" = "LIBRE_SANS_C2" ]; then
  grep -q "BRAS A\] voix libre" "$L" || { echo "!! ${bras}_g${g} : voix libre NON atteinte"; exit 4; }
else
  grep -q "BRAS A\] voix libre" "$L" && { echo "!! ${bras}_g${g} : CONTAMINE par la voix libre"; exit 5; }
fi
echo "OK ${bras}_g${g}"
