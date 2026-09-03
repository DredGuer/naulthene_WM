#!/bin/zsh
# BRAS A à 200 JOURS — reprise des cerveaux de 02092026_brasA_voix_libre (déjà copiés ici).
# `--jours 100` sur un cerveau à j100 est ADDITIF : il le mène à j200.
# ⚠️ Vérifier qu'aucun lanceur ne tourne déjà (ps aux | grep lancer.sh) — collision du 02/09.
cd "/Users/dredguer/Documents/1. Dossier personnel important/1. Adrien/21. AGI"
source venv/bin/activate
D=brains/03092026_brasA_200j
for g in 11 22 33 44 55 66 77 88 99 111 122 133 144 155 166 177 188 199 211 222; do
  for bras in LIBRE TEMOIN; do
    B="$D/${bras}_g${g}.brain"
    [ -f "$B" ] || { echo "❌ cerveau absent ${bras}_g${g} — la copie a échoué"; exit 1; }
    # idempotence : un run terminé a écrit sa marque de fin dans son log
    [ -f "$D/${bras}_g${g}.log" ] && grep -q "jour 200" "$D/${bras}_g${g}.log" && continue
    FLAG=""; [ "$bras" = "LIBRE" ] && FLAG="--gain-c1-libre"
    WANDB_MODE=offline PYTHONPATH=src python -m naulthene.cerveau.noyau \
        --graine $g --jours 100 --env-force MiniGrid-SimpleCrossingS9N1-v0 $FLAG \
        --brain "$B" > "$D/${bras}_g${g}.log" 2>&1
    # le drapeau doit avoir atteint le module ET l'individu — sinon la campagne est invalide
    if [ "$bras" = "LIBRE" ]; then
      grep -q '\[BRAS A\] voix libre v41.50' "$D/${bras}_g${g}.log" || { echo "❌ drapeau absent ${bras}_g${g}"; exit 1; }
    else
      grep -q 'voix libre' "$D/${bras}_g${g}.log" && { echo "❌ témoin contaminé ${bras}_g${g}"; exit 1; }
    fi
    echo "fait ${bras}_g${g}"
  done
done
echo "BRAS A 200 JOURS TERMINE"
