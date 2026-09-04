#!/bin/zsh
# Un seul run du cursus complet. Appele par lancer.sh via xargs -P (parallelisme borne).
# Usage : run_un.sh <graine> <LIBRE|TEMOIN>
cd "/Users/dredguer/Documents/1. Dossier personnel important/1. Adrien/21. AGI"
source venv/bin/activate
D=brains/04092026_cursus_complet
g=$1; bras=$2
B="$D/${bras}_g${g}.brain"; L="$D/${bras}_g${g}.log"

# idempotence : un run termine a ecrit son dernier jour
[ -f "$L" ] && grep -q "Jour 1500" "$L" && { echo "deja fait ${bras}_g${g}"; exit 0; }

FLAG=""; [ "$bras" = "LIBRE" ] && FLAG="--gain-c1-libre"
WANDB_MODE=offline PYTHONPATH=src python -m naulthene.cerveau.noyau \
    --graine $g --jours 1500 $FLAG --brain "$B" > "$L" 2>&1

# le drapeau doit avoir atteint l'individu — sinon la campagne est invalide
if [ "$bras" = "LIBRE" ]; then
  grep -q '\[BRAS A\] voix libre v41.50' "$L" || { echo "❌ drapeau absent ${bras}_g${g}"; exit 1; }
else
  grep -q 'voix libre' "$L" && { echo "❌ témoin contaminé ${bras}_g${g}"; exit 1; }
fi
echo "fait ${bras}_g${g} (jour $(grep -oE 'Jour [0-9]+' "$L" | tail -1 | grep -oE '[0-9]+'))"
