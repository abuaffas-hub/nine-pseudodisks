"""Exact combinatorial checker for arrangements of pairwise-crossing pseudo-circles.

Representation (all circles oriented counterclockwise, disk = left side):
  seq[i] = cyclic list of labels (j, s) for j != i, s in {0,1}:
     (j,0) on circle i = point where i ENTERS disk j  (start of arc I_i(j) = dD_i ∩ D_j)
     (j,1) on circle i = point where i EXITS  disk j  (end of that arc)
  Vertex X(i,j) = "i enters j" = (j,0) on i = (i,1) on j.
  At a vertex where q enters disk p the ccw rotation is (p_fwd, q_fwd, p_back, q_back).

valid(seq) is True iff seq is the rotation system of an arrangement of closed curves in
the plane, each pair crossing exactly twice (transversally), with disks = bounded sides:
  * the induced combinatorial map has genus 0 (V - E + F = 2; graph is connected),
  * every face gets a consistent inside/outside vector,
  * some face is outside all disks (it becomes the unbounded face).
"""
from itertools import combinations


def restrict(seq, S):
    S = set(S)
    return {i: [p for p in seq[i] if p[0] in S] for i in S}


def analyse(seq):
    """Return (ok, info). info has faces with their in/out vectors."""
    C = sorted(seq)
    # darts: (i, t, d) circle i, edge t (from point t to t+1), d=+1 forward / -1 backward
    pos = {}
    for i in C:
        for t, p in enumerate(seq[i]):
            pos[(i, p)] = t
    m = {i: len(seq[i]) for i in C}

    def vertex_of(i, p):
        j, s = p
        return (i, j) if s == 0 else (j, i)   # X(a,b): a enters b

    # inside-ness of edge t on circle i w.r.t. j: edge after point t
    inside = {}
    for i in C:
        L = seq[i]
        state = {}
        # find state at start: walk once around to settle
        cur = {}
        for p in L + L:
            j, s = p
            cur[j] = (s == 0)
        for t, p in enumerate(L):
            j, s = p
            cur[j] = (s == 0)
            inside[(i, t)] = frozenset(k for k, v in cur.items() if v)
    # rotation at each vertex
    # dart out of vertex: (i, t, +1) leaves point t forward; (i, t-1, -1) leaves point t backward
    rot = {}
    for i in C:
        for t, p in enumerate(seq[i]):
            v = vertex_of(i, p)
            rot.setdefault(v, {})[i] = ((i, t, +1), (i, (t - 1) % m[i], -1))
    succ = {}
    for v, d in rot.items():
        a, b = v  # a enters b ; p=b, q=a
        pf, pb = d[b]
        qf, qb = d[a]
        cyc = [pf, qf, pb, qb]
        for k in range(4):
            succ[cyc[k]] = cyc[(k + 1) % 4]
    pred = {y: x for x, y in succ.items()}

    def head(d):
        i, t, s = d
        tt = (t + 1) % m[i] if s == 1 else t
        return vertex_of(i, seq[i][tt]), (i, t, -s)  # reverse dart leaves head

    def left_label(d):
        i, t, s = d
        ins = set(inside[(i, t)])
        if s == 1:
            ins.add(i)
        return frozenset(ins)

    seen = set()
    faces = []
    for d0 in succ:
        if d0 in seen:
            continue
        f = []
        d = d0
        while d not in seen:
            seen.add(d)
            f.append(d)
            _, rev = head(d)
            d = pred[rev]
        faces.append(f)
    V = len(rot)
    E = sum(m.values())
    F = len(faces)
    labels = []
    ok = True
    for f in faces:
        labs = {left_label(d) for d in f}
        if len(labs) != 1:
            ok = False
        labels.append(labs)
    euler = V - E + F
    outer = any(len(l) == 1 and len(next(iter(l))) == 0 for l in labels)
    ok = ok and euler == 2 and outer
    return ok, dict(V=V, E=E, F=F, euler=euler, outer=outer, faces=faces, labels=labels)


def valid(seq):
    if len(seq) <= 1:
        return True
    return analyse(seq)[0]


def helly(seq, t):
    """Triple t has a common point iff on some circle of t the two arcs overlap."""
    for i in t:
        a, b = [x for x in t if x != i]
        L = seq[i]
        # walk around: is there a position inside both I_i(a) and I_i(b)?
        cur = {}
        for p in L + L:
            cur[p[0]] = (p[1] == 0)
        for p in L:
            cur[p[0]] = (p[1] == 0)
            if cur.get(a) and cur.get(b):
                return True
    return False


def faces_depth(seq):
    """Return list of label sets of faces (sets of disks containing the face)."""
    ok, info = analyse(seq)
    return [next(iter(l)) for l in info['labels']]


def minimal_invalid(seq):
    """Deletion-minimal subset of circles whose restriction is invalid."""
    S = sorted(seq)
    assert not valid(seq)
    changed = True
    while changed:
        changed = False
        for i in list(S):
            T = [x for x in S if x != i]
            if len(T) >= 2 and not valid(restrict(seq, T)):
                S = T
                changed = True
                break
    return S


def from_disks(D, eps=0.0):
    """Rotation system of real disks D = [(x,y,r)], assumed pairwise crossing."""
    import math
    n = len(D)
    seq = {}
    for i in range(n):
        xi, yi, ri = D[i]
        pts = []
        for j in range(n):
            if j == i:
                continue
            xj, yj, rj = D[j]
            dx, dy = xj - xi, yj - yi
            d = math.hypot(dx, dy)
            assert abs(ri - rj) < d < ri + rj, (i, j)
            base = math.atan2(dy, dx)
            c = (ri * ri + d * d - rj * rj) / (2 * ri * d)
            h = math.acos(c)
            # arc of circle i inside disk j: angles base-h .. base+h (ccw)
            pts.append(((base - h) % (2 * math.pi), (j, 0)))
            pts.append(((base + h) % (2 * math.pi), (j, 1)))
        pts.sort()
        seq[i] = [p for _, p in pts]
    return seq
