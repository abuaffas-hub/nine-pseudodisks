#!/usr/bin/env bash
# Finish the n=9 pseudo-disk cube run.  usage: ./run_all.sh [NUM_WORKERS]   (default: number of cores)
# Skips every cube already logged UNSAT in done_pseudo.txt or in earlier log_*.txt files,
# so it is safe to rerun after an interruption.
set -e
cd "$(dirname "$0")"
W=${1:-$(nproc)}
cat done_pseudo.txt log_*.txt 2>/dev/null | grep 'UNSAT' > .skip.txt || true
STAMP=$(date +%Y%m%d_%H%M%S)
for ((k=0; k<W; k++)); do
  nohup python3 cube2.py --track pseudo --canon --skip .skip.txt --start $k --step $W \
      > log_${STAMP}_w$k.txt 2>&1 &
done
echo "started $W workers; logs: log_${STAMP}_w*.txt"
echo "progress: python3 check_coverage.py done_pseudo.txt 'log_*.txt'"
