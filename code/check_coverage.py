"""Report progress of the n=9 pseudo-disk cube run.

usage: python3 check_coverage.py done_pseudo.txt log_*.txt
  - counts canonical cubes proven UNSAT (union over all given logs)
  - lists the cubes still missing
  - reports any SAT cube and re-verifies its witness exactly
"""
import sys, re, glob, itertools, pickle, os

vecs = list(itertools.product((1, 0), repeat=3))
cubes = list(itertools.combinations_with_replacement(range(8), 6))


def rot(c):
    return tuple(sorted(vecs.index((vecs[v][1], vecs[v][2], vecs[v][0])) for v in c))


canon = [ci for ci, c in enumerate(cubes) if c <= rot(c) and c <= rot(rot(c))]
assert len(canon) == 584

files = [g for a in sys.argv[1:] for g in glob.glob(a)]
done, sat = set(), set()
for f in files:
    for line in open(f):
        m = re.match(r'cube (\d+) .* UNSAT', line)
        if m:
            done.add(int(m.group(1)))
        m = re.match(r'SAT cube (\d+)', line)
        if m:
            sat.add(int(m.group(1)))

missing = [ci for ci in canon if ci not in done and ci not in sat]
print(f'canonical cubes: 584   UNSAT: {len(done & set(canon))}   SAT: {len(sat)}   missing: {len(missing)}')
if missing:
    print('missing cube indices:', missing)
if sat:
    from arr import valid, helly
    from run import three_pierceable
    for ci in sorted(sat):
        fn = f'witness_pseudo_cube{ci}.pkl'
        if os.path.exists(fn):
            seq = pickle.load(open(fn, 'rb'))
            print(f'SAT cube {ci}: witness realizable={valid(seq)}, 3-pierceable={three_pierceable(seq, 9) is not None}')
        else:
            print(f'SAT cube {ci}: witness file {fn} not found')
if not missing and not sat:
    print('ALL 584 CANONICAL CUBES UNSAT')
