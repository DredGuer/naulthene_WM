#!/bin/zsh
# Campagne PPO — 3 architectures x 20 graines = 60 runs.
# Vagues de 6 (leçon du 25/08 : trop de processus torch simultanes font echouer libtorch).
cd "$(dirname "$0")/../.."
C=brains/29082026_baseline_ppo
GRAINES="11 22 33 44 55 66 77 88 99 111 122 133 144 155 166 177 188 199 211 222"
i=0
for arch in 37 69 107; do
  for g in ${=GRAINES}; do
    PYTHONPATH=src nohup venv/bin/python -m naulthene.instruments.banc_ppo \
        --arch $arch --graine $g --pas 152043 \
        --sortie "$C/ppo_a${arch}_g${g}.json" > "$C/ppo_a${arch}_g${g}.log" 2>&1 &
    i=$((i+1))
    if [ $((i % 6)) -eq 0 ]; then wait; fi
  done
done
wait
echo "CAMPAGNE PPO TERMINEE : $i runs"
