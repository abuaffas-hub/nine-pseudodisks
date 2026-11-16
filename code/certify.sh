#!/usr/bin/env bash
# Certify the 584 canonical cubes: for each cube, write a standalone CNF, solve it with CaDiCaL
# producing a proof, check the proof with an independent checker, record the result, and delete
# the (large) temporary files unless KEEP=1.
#
#   ./certify.sh test            # certify one easy cube (350) and show all output
#   ./certify.sh [WORKERS]       # certify every cube not yet in certified.txt (resumable)
#
#   MODE=lrat (default): cadical --lrat  +  lrat-check   (fast checking, larger proof files)
#   MODE=drat          : cadical (DRAT)  +  drat-trim    (smaller proofs, slower checking)
#   KEEP=1             : keep CNF and proof files in proofs/
#
# The solver and checker output of every cube is kept in checklogs/ (also after success).
# A cube counts as certified only if CaDiCaL exits with code 20 and prints 's UNSATISFIABLE',
# and the checker exits with code 0 and prints 'VERIFIED' (not 'NOT VERIFIED').
set -u
cd "$(dirname "$0")"
MODE=${MODE:-lrat}
CADICAL=tools/cadical/build/cadical
LRATCHECK=tools/drat-trim/lrat-check
DRATTRIM=tools/drat-trim/drat-trim
mkdir -p proofs work checklogs
touch certified.txt

one() {   # one CUBE_INDEX  -> appends a line to certified.txt (or failures.txt)
  ci=$1; d=work/c$ci; mkdir -p "$d"
  cnf=$d/cube.cnf; prf=$d/proof.$MODE
  python3 gen_cnf.py "$ci" "$cnf" || { echo "cube $ci GEN_FAILED" >> failures.txt; return; }
  h=$(sha256sum "$cnf" | cut -c1-64)
  t0=$(date +%s)
  if [ "$MODE" = lrat ]; then
    "$CADICAL" -q --lrat --no-binary "$cnf" "$prf" > "$d/solve.log" 2>&1; src=$?
  else
    "$CADICAL" -q "$cnf" "$prf" > "$d/solve.log" 2>&1; src=$?
  fi
  t1=$(date +%s)
  cp "$d/solve.log" "checklogs/cube$ci.solve.log"
  if [ "$src" -ne 20 ] || ! grep -q '^s UNSATISFIABLE' "$d/solve.log"; then
    echo "cube $ci SOLVER_DID_NOT_REPORT_UNSAT $(tail -n3 "$d/solve.log" | tr '\n' ' ')" >> failures.txt; return
  fi
  psize=$(stat -c %s "$prf")
  if [ "$MODE" = lrat ]; then
    "$LRATCHECK" "$cnf" "$prf" > "$d/check.log" 2>&1; crc=$?
  else
    "$DRATTRIM" "$cnf" "$prf" -t 200000 > "$d/check.log" 2>&1; crc=$?
  fi
  t2=$(date +%s)
  cp "$d/check.log" "checklogs/cube$ci.check.log"
  if [ "$crc" -eq 0 ] && grep -q 'VERIFIED' "$d/check.log" && ! grep -q 'NOT VERIFIED' "$d/check.log"; then
    echo "cube $ci VERIFIED mode=$MODE solve=$((t1-t0))s check=$((t2-t1))s proof=${psize}B cnf_sha256=$h" >> certified.txt
    if [ "${KEEP:-0}" = 1 ]; then mv "$cnf" "proofs/cube$ci.cnf"; mv "$prf" "proofs/cube$ci.$MODE"; fi
    rm -rf "$d"
  else
    echo "cube $ci CHECK_FAILED $(tail -n3 "$d/check.log" | tr '\n' ' ')" >> failures.txt
  fi
}

if [ "${1:-}" = test ]; then
  ci=350; d=work/c$ci
  one $ci
  echo "--- certified.txt (last line):"; tail -n1 certified.txt
  [ -f failures.txt ] && { echo "--- failures.txt:"; cat failures.txt; }
  [ -d "$d" ] && { echo "--- solve.log:"; tail -n5 "$d/solve.log"; echo "--- check.log:"; tail -n5 "$d/check.log" 2>/dev/null; }
  exit 0
fi

W=${1:-$(nproc)}
python3 gen_cnf.py 350 /dev/null >/dev/null 2>&1 || true      # builds base_pseudo.pkl once
todo=$(python3 gen_cnf.py --list | while read ci; do grep -q "^cube $ci VERIFIED" certified.txt || echo "$ci"; done)
echo "$(echo "$todo" | grep -c .) cubes to certify with $W workers (MODE=$MODE)"
for ((k=0; k<W; k++)); do
  ( i=0; for ci in $todo; do
      [ $((i % W)) -eq $k ] && one "$ci"
      i=$((i+1))
    done ) > /dev/null 2>&1 &
done
echo "running in background; progress: ./cert_status.sh"
wait
