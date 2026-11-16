# Nine pairwise intersecting pseudo-disks can always be pierced by three points: supplementary material

Status: complete. All 584 canonical cubes of the n = 9 formula are unsatisfiable, and each was
certified by an LRAT proof checked with `lrat-check`.

- `code/`: the exact arrangement checker, the enumeration of 3- and 4-types (`t4.pkl`), the SAT
  encoding, the CNF generator (`gen_cnf.py`), the certification scripts and the tests.
  See `code/README.md`.
- `certificates/`
  - `certified_w0.txt` ... `certified_w5.txt`, `certified_test.txt`: one line per cube (584 in
    total; cube 350 is in `certified_test.txt`). Each line records that `lrat-check` verified the
    LRAT proof, the solving and checking times (s), the proof size (bytes), and the first 64 bits
    (16 hex digits) of the SHA-256 of the CNF file. The CNF files were written on Windows, so they
    have CRLF line endings.
  - `cnf_sha256.tsv`: full SHA-256 of every regenerated CNF, for CRLF and for LF line endings.
  - The proofs (762 GB in total) were deleted after checking and are not included. Any of them can
    be regenerated and checked; see `code/README.md`.
- `logs/`: logs of the incremental search (305 cubes in `done_pseudo.txt`, 279 in `log_*.txt`).
  This search is not part of the proof; the proof rests on the certified standalone runs.
- `examples/`: vertex coordinates of the ten convex pseudo-disks that need four points, and
  `exact_check_convex10.py`, which verifies all stated properties in exact rational arithmetic.
  Run it from inside `examples/`.

Quick check of the records against the supplied hashes (plain Python 3, a second):
```
cd code
python3 check_certified.py ../certificates/cnf_sha256.tsv ../certificates/certified_*.txt
```
To recompute the hashes from the code instead, see `code/README.md` (needs `python-sat`).
