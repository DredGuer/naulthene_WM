#!/bin/zsh
# CURSUS COMPLET — 20 graines x 2 bras x 1500 jours, 15 niveaux, AUCUN --env-force.
# Parallelisme 6 (M3 Pro 12 coeurs, ~700 Mo/run mesure => ~4,2 Go sur 36).
#
# ⚠️ LE PARALLELISME EST BORNE PAR `xargs -P`, PAS PAR `jobs -r`.
#    Mesure du 04/09 : la boucle `while [ $(jobs -r | wc -l) -ge N ]` a lance
#    41 runs simultanes (12 Go) au lieu de 6 — `jobs` ne voit pas les jobs
#    d'un sous-shell de la meme facon selon le contexte d'execution.
#    xargs -P est le seul garde-fou verifie.
#
# ⚠️ Verifier qu'aucun lanceur ne tourne deja (ps aux | grep lancer.sh) — collision du 02/09.
cd "/Users/dredguer/Documents/1. Dossier personnel important/1. Adrien/21. AGI"
D=brains/04092026_cursus_complet
PAR=6

# un run = une ligne "graine bras", consommee par xargs
: > "$D/.taches"
for g in 11 22 33 44 55 66 77 88 99 111 122 133 144 155 166 177 188 199 211 222; do
  for bras in LIBRE TEMOIN; do
    echo "$g $bras" >> "$D/.taches"
  done
done

cat "$D/.taches" | xargs -P $PAR -L1 zsh "$D/run_un.sh"
echo "CURSUS COMPLET TERMINE"
