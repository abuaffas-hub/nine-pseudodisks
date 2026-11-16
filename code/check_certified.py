"""Validate the certification records against the exact set of canonical cubes.

usage: python3 check_certified.py MANIFEST.tsv RECORD_FILE...
  e.g. python3 check_certified.py ../certificates/cnf_sha256.tsv ../certificates/certified_*.txt

Checks that
  - every record line has the expected format (mode=lrat, VERIFIED);
  - no cube is recorded twice, and no non-canonical cube occurs;
  - the recorded cubes are exactly the 584 canonical cubes;
  - each recorded hash (a 16-hex-digit prefix in the original records, or a full SHA-256)
    is a prefix of the cube's SHA-256 in the manifest (CRLF or LF version).
Then prints the totals from the unrounded per-cube measurements.
"""
import sys, re, statistics
from gen_cnf import canon

PAT = re.compile(r'^cube (\d+) VERIFIED mode=lrat solve=(\d+)s check=(\d+)s proof=(\d+)B '
                 r'cnf_sha256=([0-9A-Fa-f]{16}|[0-9A-Fa-f]{64})$')

man = {}
for line in open(sys.argv[1]):
    if line.startswith('cube'):
        continue
    ci, six, crlf, lf = line.split()
    man[int(ci)] = (crlf.lower(), lf.lower())
assert set(man) == set(canon), 'manifest does not cover exactly the canonical cubes'

rec, errors = {}, []
for f in sys.argv[2:]:
    for k, line in enumerate(open(f), 1):
        line = line.strip()
        if not line:
            continue
        m = PAT.match(line)
        if not m:
            errors.append(f'{f}:{k}: unexpected line: {line}')
            continue
        ci = int(m[1])
        if ci in rec:
            errors.append(f'{f}:{k}: cube {ci} recorded twice')
        rec[ci] = (int(m[2]), int(m[3]), int(m[4]), m[5].lower())

extra = sorted(set(rec) - set(canon))
missing = sorted(set(canon) - set(rec))
if extra:
    errors.append(f'non-canonical cubes recorded: {extra}')
if missing:
    errors.append(f'canonical cubes without a record: {missing}')
for ci, (_, _, _, h) in rec.items():
    if ci in man and not any(full.startswith(h) for full in man[ci]):
        errors.append(f'cube {ci}: recorded hash {h} matches neither manifest hash')

if errors:
    print('\n'.join(errors))
    print(f'FAILED: {len(errors)} problem(s)')
    sys.exit(1)

S = [v[0] for v in rec.values()]; C = [v[1] for v in rec.values()]; P = [v[2] for v in rec.values()]
crlf = sum(man[ci][0].startswith(v[3]) for ci, v in rec.items())
print(f'records: {len(rec)} = the 584 canonical cubes; hashes match the manifest '
      f'({crlf} CRLF, {len(rec) - crlf} LF)')
print(f'solving {sum(S) / 3600:.3f} h, checking {sum(C) / 3600:.3f} h, proofs {sum(P) / 1e9:.3f} GB, '
      f'largest proof {max(P) / 1e9:.3f} GB, longest check {max(C)} s, median check {statistics.median(C)} s')
print('ALL 584 CANONICAL CUBES CERTIFIED')
