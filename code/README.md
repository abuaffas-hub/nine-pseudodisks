# Code

Requirements: Python 3 with `python-sat` (`pip install python-sat`; tested with 1.9.dev22).
For certification: CaDiCaL 3.0.1 and `lrat-check` (see below).

## Files

| file | role |
|---|---|
| `arr.py` | exact checker: rotation system -> combinatorial map; (R1)-(R3); Helly test (Lemma 10) |
| `enumtypes.py`, `enum4.py` | exhaustive enumeration of the 9 valid 3-types and 1,028 valid 4-types |
| `t4.pkl` | the 1,028 labelled 4-types (regenerate with `python3 enum4.py`, a few minutes) |
| `encode.py` | the clauses (C1)-(C7) |
| `run_sb.py` | (C3) and the symmetry breaking (C8) |
| `gen_cnf.py` | standalone DIMACS file for one canonical cube: (C1)-(C8) plus 18 unit clauses |
| `hash_manifest.py` | full SHA-256 of all 584 CNF files (CRLF and LF), without writing them |
| `check_certified.py` | validates the certification records against the 584 canonical cubes and the hashes |
| `certify.sh`, `certify.ps1` | certify all cubes (Linux / Windows); `cert_status.sh` shows progress |
| `build_tools.sh` | builds the pinned versions of CaDiCaL and lrat-check (Linux / WSL) |
| `test_encoding.py` | the tests of Appendix A of the paper |
| `run.py`, `cube2.py`, `run_all.sh`, `check_coverage.py` | the incremental search (not needed for the proof) |

`gen_cnf.py` caches the base formula in `base_pseudo.pkl`. The cache records the SHA-256 of every
source file it depends on and is rebuilt automatically when one of them changes; `--no-cache`
ignores it.

## Checking the records

```
python3 hash_manifest.py manifest.tsv          # about 30 s; should equal ../certificates/cnf_sha256.tsv
python3 check_certified.py manifest.tsv ../certificates/certified_*.txt
```
The last line should read `ALL 584 CANONICAL CUBES CERTIFIED`.

## Re-certifying cubes

Tools, at the versions used for the certificates:
- CaDiCaL 3.0.1: tag `rel-3.0.1`, commit `c60730422e758ef1cebe7aeddf2dda31c996bf04`
  (https://github.com/arminbiere/cadical);
- `lrat-check` from drat-trim commit `2e3b2dc0ecf938addbd779d42877b6ed69d9a985`
  (https://github.com/marijnheule/drat-trim).

On Linux / WSL, `./build_tools.sh` builds both. On Windows they were built with gcc; CaDiCaL needed
`-DNUNLOCKED` there.

One cube by hand:
```
python3 gen_cnf.py 350 cube.cnf
cadical --lrat=1 --binary=0 cube.cnf proof.lrat     # exit code 20, prints "s UNSATISFIABLE"
lrat-check cube.cnf proof.lrat                       # exit code 0, prints "c VERIFIED"
```
All cubes:
```
./certify.sh test        # one easy cube (350), shows all output
./certify.sh 4           # all 584 cubes with 4 workers (resumable)
./cert_status.sh
```
On Windows: `powershell -ExecutionPolicy Bypass -File certify.ps1 -Test`, then `-Workers 4`, then
`-Status` (tools in `$HOME\nine_tools`, or pass `-Tools DIR`).

A cube counts as certified only if CaDiCaL exits with code 20 and reports UNSAT, and `lrat-check`
exits with code 0 and prints `VERIFIED`. The scripts write one line per cube to `certified*.txt`,
now with the full SHA-256 of the CNF, and keep the solver and checker output in `checklogs/`. Proofs
are deleted after a successful check unless `KEEP=1` (`-Keep` on Windows); they can reach several GB
per cube (762 GB for all cubes).

The original certificates were made with an earlier version of these scripts, which recorded only
the first 16 hex digits of the SHA-256, did not test exit codes (only the printed results), and
deleted the solver and checker output after success.

## Tests

```
python3 test_encoding.py      # a few minutes
```
See the docstring of `test_encoding.py` and Appendix A of the paper.

## Note on the incremental search

`run.py` and `cube2.py` refine with CEGAR blocking clauses when a model is not realizable. A blocking
clause can introduce new `cyc` variables; earlier versions added only the blocking clause to the
solver, not the definitions of these variables. This could only weaken the formula and never
produce a wrong UNSAT, and the completed runs needed no refinements (`ref=0` in all logs). It is
fixed in this version. The formulas of `gen_cnf.py` contain no CEGAR clauses.
