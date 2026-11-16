#!/usr/bin/env bash
# Progress of the certification run.
cd "$(dirname "$0")"
v=$(grep -s -c ' VERIFIED' certified.txt); v=${v:-0}
f=$(cat failures.txt 2>/dev/null | wc -l)
echo "verified: $v / 584    failures: $f    in progress: $(ls work 2>/dev/null | wc -l)"
[ "$f" -gt 0 ] && tail -n5 failures.txt
[ "$v" -eq 584 ] && echo "ALL 584 CUBES CERTIFIED"
exit 0
