#!/bin/zsh
# Un run. Args: <graine> <bras>   ⚠️ zsh : FLAGS doit etre un TABLEAU (pas de word-splitting)
cd "$(dirname "$0")/../.."
g=$1; bras=$2; D=brains/05092026_detach_c2
L="$D/${bras}_g${g}.log"; B="$D/${bras}_g${g}.brain"
if [ -f "$L" ] && grep -q "Jour 1500" "$L" 2>/dev/null; then echo "SKIP ${bras}_g${g}"; exit 0; fi
case "$bras" in
  LIBRE_DETACH) FLAGS=(--gain-c1-libre --detach-c2) ;;
  *) echo "!! bras inconnu: $bras"; exit 2 ;;
esac
WANDB_MODE=offline PYTHONPATH=src python -m naulthene.cerveau.noyau \
  --graine $g --jours 1500 "${FLAGS[@]}" --no-wandb --brain "$B" > "$L" 2>&1
grep -q "Jour 1500" "$L" || { echo "!! ${bras}_g${g} : run INCOMPLET"; exit 6; }
grep -q "VARIANTE\] detach asym" "$L" || { echo "!! ${bras}_g${g} : detach NON atteint"; exit 3; }
grep -q "BRAS A\] voix libre" "$L" || { echo "!! ${bras}_g${g} : voix libre NON atteinte"; exit 4; }
echo "OK ${bras}_g${g}"
