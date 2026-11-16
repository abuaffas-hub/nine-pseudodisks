#!/usr/bin/env bash
# Build CaDiCaL (solver with LRAT output) and lrat-check (independent checker) at the exact
# versions used for the certificates:
#   CaDiCaL   3.0.1   tag rel-3.0.1, commit c60730422e758ef1cebe7aeddf2dda31c996bf04
#   drat-trim         commit 2e3b2dc0ecf938addbd779d42877b6ed69d9a985 (contains lrat-check.c)
# Run once on Linux / WSL:  ./build_tools.sh
set -e
cd "$(dirname "$0")"
CADICAL_COMMIT=c60730422e758ef1cebe7aeddf2dda31c996bf04
DRATTRIM_COMMIT=2e3b2dc0ecf938addbd779d42877b6ed69d9a985
command -v git >/dev/null && command -v make >/dev/null || {
  sudo apt-get update -y && sudo apt-get install -y git build-essential; }
mkdir -p tools && cd tools
[ -d cadical ]   || git clone https://github.com/arminbiere/cadical.git
[ -d drat-trim ] || git clone https://github.com/marijnheule/drat-trim.git
git -C cadical   -c advice.detachedHead=false checkout "$CADICAL_COMMIT"
git -C drat-trim -c advice.detachedHead=false checkout "$DRATTRIM_COMMIT"
[ "$(git -C cadical rev-parse HEAD)" = "$CADICAL_COMMIT" ]
[ "$(git -C drat-trim rev-parse HEAD)" = "$DRATTRIM_COMMIT" ]
( cd cadical && ./configure && make -j"$(nproc)" )
( cd drat-trim && make )
echo
./cadical/build/cadical --version
ls -l drat-trim/lrat-check
echo "tools built OK (pinned commits)"
