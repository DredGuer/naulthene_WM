#!/bin/bash
# Campagne A/B v41.10 — la mémoire par carte sert-elle à quelque chose ?
#
#   bras A (témoin)   : --sans-memoire-cartes  → la bascule EFFACE (v41.9)
#   bras B (variante) : par défaut             → la bascule ARCHIVE (v41.10)
#
# 20 graines par bras (règle de mesure : jamais de conclusion sous 20), mêmes graines des
# deux côtés donc MÊMES MONDES (reproductibilité v41.9, contrôlée par un test A/A).
#
# Lancé depuis la racine du dépôt.
set -u
RACINE="$(pwd)"
SORTIE="${1:-/tmp/campagne_v4110}"
JOURS="${2:-2500}"
PARALLELE="${3:-5}"
mkdir -p "$SORTIE/logs" "$SORTIE/brains"

lancer() {
    local graine="$1" bras="$2" flag="$3"
    WANDB_MODE=offline PYTHONPATH=src python -m naulthene.cerveau.noyau \
        --jours "$JOURS" --graine "$graine" $flag \
        --brain "$SORTIE/brains/${bras}_g${graine}.brain" \
        > "$SORTIE/logs/${bras}_g${graine}.log" 2>&1
}

echo "Campagne v41.10 — $JOURS jours × 20 graines × 2 bras → $SORTIE"
for graine in $(seq 1 20); do
    lancer "$graine" "temoin"   "--sans-memoire-cartes" &
    lancer "$graine" "variante" ""                      &
    while [ "$(jobs -rp | wc -l)" -ge "$PARALLELE" ]; do sleep 5; done
done
wait
echo "TERMINE $(date '+%H:%M:%S')"
