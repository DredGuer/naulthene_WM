#!/usr/bin/env bash
# ============================================================================
# REP-01 — Vérification d'un environnement vierge (validation de clôture)
#
# Crée un venv PROPRE hors du dépôt, installe les dépendances depuis le lock de
# référence, puis exécute les trois vérifications de clôture REP-01 :
#   1. Import minimal du cœur (CPU)
#   2. Suite de contrats CPU (44 tests)
#   3. Rapport de versions installées vs lock (écart éventuel signalé)
#
# ⚠️ À exécuter UNIQUEMENT quand aucune campagne ne tourne : l'installation
# télécharge plusieurs Go (torch, scipy, librosa…) — la contention I/O fausserait
# les mesures de runs en cours. Voir docs/fonctionnement/ENVIRONNEMENT.md §6.
#
# Le venv cible est créé dans /tmp (hors dépôt, hors iCloud) — ne touche JAMAIS au
# venv de production de la campagne.
#
# Usage :  bash scripts/verifier_environnement.sh [chemin_venv]
#          défaut : /tmp/venv_rep01_validation
# Code de sortie : 0 = validation OK · ≠0 = échec (le détail est affiché).
# ============================================================================
set -u

REPO="$(cd "$(dirname "$0")/.." && pwd)"
LOCK="$REPO/constraints-lock.txt"
TARGET_VENV="${1:-/tmp/venv_rep01_validation}"
LOGFILE="${TARGET_VENV}_validation.log"

echo "=== REP-01 — validation d'environnement vierge ==="
echo "Dépôt     : $REPO"
echo "Lock      : $LOCK"
echo "Venv cible: $TARGET_VENV (hors dépôt, hors iCloud — /tmp)"
echo "Log       : $LOGFILE"
echo

# 0. Garde : aucune campagne ne doit tourner (un run noyau.py actif = refus).
if pgrep -f "naulthene.cerveau.noyau" >/dev/null 2>&1; then
    echo "⛔ Un processus noyau.py tourne — la validation perturberait la campagne."
    echo "   Attendre 'WAVE X TERMINEE' dans campagne.log avant de relancer."
    exit 2
fi

# 1. Création du venv vierge.
if [ -d "$TARGET_VENV" ]; then
    echo "⚠️ Le venv cible existe déjà — suppression pour repartir d'un état VRAIMENT vierge."
    rm -rf "$TARGET_VENV"
fi
echo "--- Création du venv (python3.12 requis) ---"
python3.12 -m venv "$TARGET_VENV" || { echo "⛔ échec création venv"; exit 3; }
"$TARGET_VENV/bin/pip" install --upgrade pip -q

# 2. Installation depuis le lock de référence.
echo "--- Installation : pip install -c constraints-lock.txt -e '.[tout]' ---"
echo "    (téléchargement de plusieurs Go — patience, c'est la phase lourde)"
if ! "$TARGET_VENV/bin/pip" install -c "$LOCK" -e "${REPO}[tout]" >"$LOGFILE" 2>&1; then
    echo "⛔ L'installation a échoué — voir $LOGFILE (dernières lignes) :"
    tail -20 "$LOGFILE"
    exit 4
fi
echo "✅ Installation terminée."

# 3. Vérification 1 — import minimal du cœur (CPU).
echo "--- Vérif 1 : import minimal (CPU) ---"
if ! NAULTHENE_DEVICE=cpu PYTHONPATH="$REPO/src" "$TARGET_VENV/bin/python" \
        -c "import naulthene.cerveau.noyau; print('✅ noyau importé')" >>"$LOGFILE" 2>&1; then
    echo "⛔ Import minimal en échec — voir $LOGFILE"
    tail -15 "$LOGFILE"
    exit 5
fi
echo "✅ Import minimal OK."

# 4. Vérification 2 — suite de contrats CPU (le nombre de tests ÉVOLUE : jamais figé ici).
echo "--- Vérif 2 : suite de contrats CPU ---"
if ! NAULTHENE_DEVICE=cpu PYTHONPATH="$REPO/src" "$TARGET_VENV/bin/python" \
        -m unittest discover -s "$REPO/tests" >>"$LOGFILE" 2>&1; then
    echo "⛔ Tests en échec — voir $LOGFILE (dernières lignes) :"
    tail -25 "$LOGFILE"
    exit 6
fi
# ⚠️ Le nombre de tests n'est PAS figé dans ce script : il a déjà menti une fois (« 44
# attendus » alors que le dépôt en comptait 156 le 12/09/2026). On lit ce que le log dit.
echo "✅ Tests CPU OK — $(grep -oE 'Ran [0-9]+ tests' "$LOGFILE" | tail -1)"

# 5. Vérification 3 — rapport de versions vs lock.
echo "--- Vérif 3 : versions installées vs lock ---"
"$TARGET_VENV/bin/pip" freeze > "${TARGET_VENV}_freeze.txt"
echo "Freeze écrit : ${TARGET_VENV}_freeze.txt"
# Signalement simple des écarts sur les paquets directs du cœur.
for PKG in numpy torch gymnasium minigrid wandb; do
    LOCKED=$(grep -i "^${PKG}==" "$LOCK" | head -1 | cut -d= -f3)
    GOT=$(grep -i "^${PKG}==" "${TARGET_VENV}_freeze.txt" | head -1 | cut -d= -f3)
    if [ -n "$LOCKED" ] && [ "$LOCKED" != "$GOT" ]; then
        echo "  ⚠️ $PKG : lock=$LOCKED installé=$GOT"
    else
        echo "  ✅ $PKG == ${GOT:-ABSENT}"
    fi
done

echo
echo "=== VALIDATION REP-01 TERMINÉE ==="
echo "Log complet : $LOGFILE"
echo "Freeze      : ${TARGET_VENV}_freeze.txt"
echo "Code retour : 0 (succès) — documenter le résultat dans ENVIRONNEMENT.md §6."
exit 0
