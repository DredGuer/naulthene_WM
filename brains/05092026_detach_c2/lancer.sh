#!/bin/zsh
cd "$(dirname "$0")/../.."
D=brains/05092026_detach_c2; PAR=6
: > "$D/.taches"
for g in 11 22 33 44 55 66 77 88 99 111 122 133 144 155 166 177 188 199 211 222; do
  echo "$g LIBRE_DETACH" >> "$D/.taches"
done
echo "$(wc -l < "$D/.taches") runs, $PAR en parallele"
cat "$D/.taches" | xargs -P $PAR -L1 zsh "$D/run_un.sh"
