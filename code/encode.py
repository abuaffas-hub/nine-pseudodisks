"""SAT encoding: n pairwise-crossing pseudo-disks (each pair of boundaries crosses exactly twice)
that cannot be pierced by 3 points.  Only necessary conditions are encoded (sound for UNSAT);
SAT witnesses are checked exactly with arr.valid and refined by CEGAR.

Variables
  lin[i][(p,q)]  (p<q, non-anchor points of circle i): p precedes q on circle i, linear order
                 starting at the anchor point (a_i, 0), a_i = min(j != i).
  cyc_i(p,q,r)   derived: p -> q -> r in ccw cyclic order on circle i.
  H[t]           triple t has a common point.
Constraints
  (1) each lin[i] is a strict total order (transitivity).
  (2) every 3-subarrangement is one of the 9 valid labelled types (exhaustive enumeration).
  (3) H[t] <-> some circle of t has overlapping arcs  (exact for pseudo-disks).
  (4) not 3-pierceable: for each partition into 3 blocks, some block contains a non-Helly triple
      (Helly number of pseudo-disks is 3, so a block has a common point iff all its triples are Helly).
  (5) CEGAR: forbid the cyclic-order pattern of every deletion-minimal unrealizable subset found.
"""
import itertools
import os
from pysat.formula import IDPool
from arr import valid, restrict, minimal_invalid, helly
from enumtypes import enum


def set_partitions3(n):
    # all partitions of range(n) into exactly 3 nonempty blocks (unordered)
    def rec(k, blocks):
        if k == n:
            if len(blocks) == 3:
                yield [list(b) for b in blocks]
            return
        for b in blocks:
            b.append(k)
            yield from rec(k + 1, blocks)
            b.pop()
        if len(blocks) < 3:
            blocks.append([k])
            yield from rec(k + 1, blocks)
            blocks.pop()
    yield from rec(0, [])


class Enc:
    def __init__(self, n, pierce=True):
        self.n = n
        self.pool = IDPool()
        self.cl = []
        self.TRUE = self.pool.id('TRUE')
        self.cl.append([self.TRUE])
        self.pts = {i: [(j, s) for j in range(n) if j != i for s in (0, 1)] for i in range(n)}
        self.anchor = {i: (min(j for j in range(n) if j != i), 0) for i in range(n)}
        self._cyc = {}
        self.build_orders()
        self.build_triples()
        self.H = {}
        for t in itertools.combinations(range(n), 3):
            self.H[t] = self.helly_var(t)
        if pierce:
            for P in set_partitions3(n):
                c = []
                for B in P:
                    for t in itertools.combinations(sorted(B), 3):
                        c.append(-self.H[t])
                self.cl.append(c)

    # ---- order on circles
    def before(self, i, p, q):
        a = self.anchor[i]
        if p == q:
            raise ValueError
        if p == a:
            return self.TRUE
        if q == a:
            return -self.TRUE
        if p < q:
            return self.pool.id(('lin', i, p, q))
        return -self.pool.id(('lin', i, q, p))

    def build_orders(self):
        for i in range(self.n):
            P = [p for p in self.pts[i] if p != self.anchor[i]]
            for p, q, r in itertools.permutations(P, 3):
                if p < q and p < r:  # each unordered triple, all 6 orientations below
                    pass
            for x, y, z in itertools.permutations(P, 3):
                # x<y and y<z -> x<z
                self.cl.append([-self.before(i, x, y), -self.before(i, y, z), self.before(i, x, z)])

    def cyc(self, i, p, q, r):
        # canonical rotation
        trip = (p, q, r)
        k = trip.index(min(trip))
        p, q, r = trip[k:] + trip[:k]
        if q > r:  # (p,r,q) is the canonical; cyc(p,q,r) = not cyc(p,r,q)
            return -self.cyc(i, p, r, q)
        key = (i, p, q, r)
        if key not in self._cyc:
            v = self.pool.id(('cyc',) + key)
            x, y, z = self.before(i, p, q), self.before(i, q, r), self.before(i, r, p)
            for a, b in ((x, y), (y, z), (x, z)):
                self.cl.append([-v, a, b])
                self.cl.append([v, -a, -b])
            self._cyc[key] = v
        return self._cyc[key]

    def pattern_lits(self, i, L):
        """literals asserting the cyclic order on circle i restricted to points L is L."""
        return [self.cyc(i, L[0], L[t], L[t + 1]) for t in range(1, len(L) - 1)]

    def forbid(self, seq, S):
        """forbid the restriction of rotation system seq to circles S."""
        sub = restrict(seq, S)
        c = []
        for i in S:
            c += [-l for l in self.pattern_lits(i, sub[i])]
        self.cl.append(c)
        return c

    def build_triples(self):
        t3 = enum(3)
        good = set()
        for s in t3:
            good.add(tuple(self._canon(s, i, (0, 1, 2)) for i in range(3)))
        # all 216 combos; forbid the invalid ones for each triple
        orders = {}
        for i in range(3):
            o = [j for j in range(3) if j != i]
            a = (o[0], 0)
            rest = [(o[0], 1), (o[1], 0), (o[1], 1)]
            orders[i] = [tuple([a] + list(p)) for p in itertools.permutations(rest)]
        bad = [c for c in itertools.product(orders[0], orders[1], orders[2]) if c not in good]
        self.n_bad3 = len(bad)
        for T in itertools.combinations(range(self.n), 3):
            mp = dict(zip((0, 1, 2), T))
            for c in bad:
                clause = []
                for i in range(3):
                    L = [(mp[j], s) for j, s in c[i]]
                    clause += [-l for l in self.pattern_lits(mp[i], L)]
                self.cl.append(clause)

    @staticmethod
    def _canon(s, i, T):
        L = [p for p in s[i] if p[0] in T]
        a = (min(j for j in T if j != i), 0)
        k = L.index(a)
        return tuple(L[k:] + L[:k])

    def helly_var(self, t):
        v = self.pool.id(('H',) + t)
        ov = []
        for i in t:
            a, b = [x for x in t if x != i]
            # arcs disjoint on circle i  <->  cyclic order a0 a1 b0 b1
            d = self.pool.id(('disj', i, a, b))
            lits = self.pattern_lits(i, [(a, 0), (a, 1), (b, 0), (b, 1)])
            for l in lits:
                self.cl.append([-d, l])
            self.cl.append([d] + [-l for l in lits])
            ov.append(-d)
        # H <-> OR(ov)
        self.cl.append([-v] + ov)
        for o in ov:
            self.cl.append([v, -o])
        return v

    def decode(self, model):
        M = set(l for l in model if l > 0)
        seq = {}
        for i in range(self.n):
            P = self.pts[i]
            def lt(p, q):
                l = self.before(i, p, q)
                return (l in M) if l > 0 else (-l not in M)
            import functools
            key = functools.cmp_to_key(lambda p, q: -1 if lt(p, q) else 1)
            seq[i] = sorted(P, key=key)
        return seq


def add_four_table(E):
    """Every 4-subarrangement is one of the 1028 valid labelled types (exhaustive enumeration)."""
    import pickle
    t4 = pickle.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 't4.pkl'), 'rb'))
    for T in itertools.combinations(range(E.n), 4):
        mp = dict(zip(range(4), T))
        sel = []
        for k, s in enumerate(t4):
            x = E.pool.id(('T4', T, k))
            sel.append(x)
            for i in range(4):
                L = [(mp[j], b) for j, b in s[i]]
                for l in E.pattern_lits(mp[i], L):
                    E.cl.append([-x, l])
        E.cl.append(sel)


def add_four_table_support(E):
    """4-table with support clauses: every cyc literal of a 4-subset needs a live type."""
    import pickle
    t4 = pickle.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 't4.pkl'), 'rb'))
    for T in itertools.combinations(range(E.n), 4):
        mp = dict(zip(range(4), T))
        sel = []
        sup = {}
        for k, s in enumerate(t4):
            x = E.pool.id(('T4', T, k))
            sel.append(x)
            for i in range(4):
                L = [(mp[j], b) for j, b in s[i]]
                # all triples among the 6 points of circle mp[i]: full description of the order
                for p, q, r in itertools.combinations(L, 3):
                    l = E.cyc(mp[i], p, q, r)
                    E.cl.append([-x, l])
                    sup.setdefault(l, []).append(x)
        E.cl.append(sel)
        for l, xs in sup.items():
            E.cl.append([-l] + xs)


def contains_vertex(E, d, a, b):
    """literal: disk d contains vertex X(a,b) (a enters b) = point (b,0) on circle a."""
    if d in (a, b):
        return E.TRUE
    return E.cyc(a, (d, 0), (b, 0), (d, 1))


def add_vertex_helly(E):
    """(i) disks containing a common crossing vertex pairwise-triple-wise are Helly (pseudo-disks)."""
    n = E.n
    for a, b in itertools.permutations(range(n), 2):
        for t in itertools.combinations(range(n), 3):
            c = [-contains_vertex(E, d, a, b) for d in t]
            c = [l for l in c if l != -E.TRUE]
            E.cl.append(c + [E.H[t]])


def add_k1(E):
    """(ii) Prop k1: for a non-Helly triple and any points p_XY,p_YZ,p_ZX chosen among crossing
    vertices, at least two of the other n-3 disks contain none of them (else 3-pierceable).
    Valid for n = 9 (six other disks)."""
    n = E.n
    assert n == 9
    for T in itertools.combinations(range(n), 3):
        X, Y, Z = T
        others = [d for d in range(n) if d not in T]
        for (p1, p2, p3) in itertools.product([(X, Y), (Y, X)], [(Y, Z), (Z, Y)], [(Z, X), (X, Z)]):
            cf = {}
            for d in others:
                v = E.pool.id(('cf', T, p1, p2, p3, d))
                lits = [contains_vertex(E, d, *p) for p in (p1, p2, p3)]
                for l in lits:
                    E.cl.append([-v, -l])
                E.cl.append([v] + lits)
                cf[d] = v
            for Q in itertools.combinations(others, len(others) - 1):
                E.cl.append([E.H[T]] + [cf[d] for d in Q])


A_CORNERS = [(0, 1), (1, 2), (2, 0)]
A_ARC = {0: ((2, 1), (1, 0)), 1: ((0, 1), (2, 0)), 2: ((1, 1), (0, 0))}


def add_h1(E):
    """(iv) H1 (disks): {0,1,2} = max-area non-Helly triple, hole = triangle A (by reflection);
    every other disk meets the hole: contains an A-corner or crosses an A-arc."""
    E.cl.append([-E.H[(0, 1, 2)]])
    for d in range(3, E.n):
        c = [contains_vertex(E, d, a, b) for a, b in A_CORNERS]
        for a in range(3):
            p, q = A_ARC[a]
            c += [E.cyc(a, p, (d, 0), q), E.cyc(a, p, (d, 1), q)]
        E.cl.append(c)
