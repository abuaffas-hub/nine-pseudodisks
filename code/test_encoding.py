"""Tests of the implementation against real disk families (Appendix A of the paper).

usage: python3 test_encoding.py

Part 1 (realizability check, Lemma 9 and Lemma 10): for random crossing families of 3-7 disks,
  the rotation system computed from the circles passes (R1)-(R3), and the combinatorial Helly test
  agrees with geometry on every triple. Random shuffles of the cyclic orders are rejected.
Part 2 (the formula): for random crossing families of 9 disks with a non-Helly triple, relabelled
  as in (C8), the rotation system satisfies exactly the clauses used in gen_cnf.py except (C5) and
  (C7), which hold only for families that cannot be pierced by three points. The model's Helly
  variables and its literals for "crossing point X(a,b) lies in D_d" agree with geometry, so the
  family lies in the cube given by its Helly bits.

Geometry: in a crossing family of disks, three disks have a common point iff some crossing point
of two of them lies in the third (otherwise the boundary of the intersection would be a whole
circle, i.e. two members would be nested).
"""
import itertools, math, random, sys
import numpy as np
from pysat.solvers import Solver
from arr import from_disks, analyse, valid, helly
from encode import Enc, add_vertex_helly, contains_vertex
from run_sb import sb

rng = np.random.default_rng(2026)
random.seed(2026)
MARGIN = 1e-6


def rand_family(n):
    """n disks, any two boundaries crossing, with margins (general position)."""
    while True:
        D = [(rng.normal(), rng.normal(), abs(rng.normal()) + 0.3) for _ in range(n)]
        if all(abs(D[i][2] - D[j][2]) + 1e-3 < math.dist(D[i][:2], D[j][:2]) < D[i][2] + D[j][2] - 1e-3
               for i, j in itertools.combinations(range(n), 2)):
            return D


def crossing(D, a, b):
    """X(a,b): the crossing point where the ccw boundary of D_a enters D_b."""
    (xa, ya, ra), (xb, yb, rb) = D[a], D[b]
    d = math.dist((xa, ya), (xb, yb))
    base = math.atan2(yb - ya, xb - xa)
    h = math.acos((ra * ra + d * d - rb * rb) / (2 * ra * d))
    return (xa + ra * math.cos(base - h), ya + ra * math.sin(base - h))


def inside(D, d, p):
    dist = math.dist(p, D[d][:2])
    assert abs(dist - D[d][2]) > MARGIN, 'degenerate: crossing point on a third circle'
    return dist < D[d][2]


def geo_helly(D, t):
    return any(inside(D, c, crossing(D, a, b)) for a, b in itertools.permutations(t, 2)
               for c in t if c not in (a, b))


# ---------------- Part 1 ----------------
bad = mism = 0
for trial in range(300):
    n = random.randint(3, 7)
    D = rand_family(n)
    s = from_disks(D)
    ok, _ = analyse(s)
    bad += not ok
    mism += sum(helly(s, t) != geo_helly(D, t) for t in itertools.combinations(range(n), 3))
print(f'part 1: 300 random families of 3-7 disks: rejected {bad}, Helly mismatches {mism}')
assert bad == 0 and mism == 0

shuffled_valid = 0
for trial in range(300):
    s = from_disks(rand_family(5))
    s2 = {i: random.sample(s[i], len(s[i])) for i in s}
    cyc_equal = lambda A, B: any(A[k:] + A[:k] == B for k in range(len(A)))
    if not all(cyc_equal(s2[i], s[i]) for i in s) and valid(s2):
        shuffled_valid += 1
print(f'part 1: 300 shuffled rotation systems of 5 disks: accepted {shuffled_valid}')

types3 = set()
for trial in range(2000):
    s = from_disks(rand_family(3))
    norm = []
    for i in range(3):
        L = s[i]; a = (min(j for j in range(3) if j != i), 0); k = L.index(a)
        norm.append(tuple(L[k:] + L[:k]))
    types3.add(tuple(norm))
print(f'part 1: labelled 3-types realized by random circles: {len(types3)} of 9')

# ---------------- Part 2 ----------------
n = 9
E = Enc(n, pierce=False)   # (C1), (C2), (C4)
sb(E)                      # (C3) and (C8)
add_vertex_helly(E)        # (C6)
S = Solver(name='cadical195', bootstrap_with=E.cl)
tested = skipped = 0
while tested < 100:
    D = rand_family(n)
    nh = [t for t in itertools.combinations(range(n), 3) if not geo_helly(D, t)]
    if not nh:
        skipped += 1
        continue
    T = list(random.choice(nh))
    rest = [d for d in range(n) if d not in T]
    vec = lambda d: (geo_helly(D, (T[0], T[1], d)), geo_helly(D, (T[0], T[2], d)), geo_helly(D, (T[1], T[2], d)))
    rest.sort(key=vec, reverse=True)           # (C8): vectors non-increasing
    D2 = [D[i] for i in T + rest]
    s = from_disks(D2)
    assum = []
    for i in range(n):
        assum += E.pattern_lits(i, s[i])
    for cl in E.cl[S.nof_clauses():]:
        S.add_clause(cl)                       # definitions of cyc variables created on demand
    assert S.solve(assumptions=assum), 'a real family violates the encoding'
    M = set(S.get_model())
    for t, v in E.H.items():
        assert (v in M) == geo_helly(D2, t), ('Helly variable', t)
    for a, b in itertools.permutations(range(n), 2):
        p = crossing(D2, a, b)
        for d in range(n):
            if d not in (a, b):
                lit = contains_vertex(E, d, a, b)
                for cl in E.cl[S.nof_clauses():]:
                    S.add_clause(cl)
                assert (lit in M) == inside(D2, d, p), ('containment literal', a, b, d)
    tested += 1
print(f'part 2: 100 relabelled random families of 9 disks satisfy (C1)-(C4), (C6), (C8); '
      f'Helly variables and containment literals agree with geometry ({skipped} families with no '
      f'non-Helly triple skipped)')
print('ALL TESTS PASSED')
