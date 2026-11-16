"""Write a standalone DIMACS CNF for one canonical cube of the n = 9 formula (C1)-(C8).

usage: python3 gen_cnf.py CUBE_INDEX OUT.cnf [--no-cache]
       python3 gen_cnf.py --list                 # print the 584 canonical cube indices

The CNF is the base formula (orders, 3- and 4-type tables, Helly variables, not-3-pierceable,
vertex-Helly, corner clauses, symmetry breaking) plus 18 unit clauses fixing the cube's Helly
bits. No CEGAR clauses are included.

The base formula is cached in base_pseudo.pkl. The cache stores the SHA-256 of every source file
it depends on and is rebuilt automatically if any of them changed; --no-cache ignores it.

Line endings: the file is written in text mode, so it has CRLF line endings on Windows and LF on
Linux. The certified hashes were computed on Windows (CRLF); see hash_manifest.py.
"""
import sys, itertools, pickle, os, hashlib
here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, here)

vecs = list(itertools.product((1, 0), repeat=3))
cubes = list(itertools.combinations_with_replacement(range(8), 6))


def rot(c):
    return tuple(sorted(vecs.index((vecs[v][1], vecs[v][2], vecs[v][0])) for v in c))


canon = [ci for ci, c in enumerate(cubes) if c <= rot(c) and c <= rot(rot(c))]
assert len(canon) == 584

SOURCES = ['encode.py', 'run_sb.py', 'run.py', 'arr.py', 'enumtypes.py', 't4.pkl', 'gen_cnf.py']


def source_key():
    h = hashlib.sha256()
    for f in SOURCES:
        h.update(f.encode() + b'\0')
        h.update(open(os.path.join(here, f), 'rb').read())
    return h.hexdigest()


def build_base():
    from encode import Enc, add_vertex_helly, add_k1
    from run_sb import sb
    E = Enc(9)
    sb(E)                 # (C3) 4-type table and (C8) symmetry breaking
    add_vertex_helly(E)   # (C6)
    add_k1(E)             # (C7) corner clauses
    hb = {i: [E.H[(0, 1, i)], E.H[(0, 2, i)], E.H[(1, 2, i)]] for i in range(3, 9)}
    return (E.pool.top, E.cl, hb)


def base_formula(use_cache=True):
    cache = os.path.join(here, 'base_pseudo.pkl')
    key = source_key()
    if use_cache and os.path.exists(cache):
        stored = pickle.load(open(cache, 'rb'))
        if isinstance(stored, dict) and stored.get('key') == key:
            return stored['data']
    data = build_base()
    if use_cache:
        pickle.dump({'key': key, 'data': data}, open(cache, 'wb'), protocol=pickle.HIGHEST_PROTOCOL)
    return data


_body = None


def base_body(use_cache=True):
    """The base clauses as DIMACS text (LF line endings), built once per process."""
    global _body
    if _body is None:
        nv, cls, hb = base_formula(use_cache)
        _body = (nv, len(cls), hb, ''.join(' '.join(map(str, cl)) + ' 0\n' for cl in cls))
    return _body


def cube_parts(ci, use_cache=True):
    """(head, body, tail) of the DIMACS text of cube ci, with LF line endings."""
    nv, ncl, hb, body = base_body(use_cache)
    c = cubes[ci]
    units = []
    for k, vi in enumerate(c):
        for x, b in zip(hb[3 + k], vecs[vi]):
            units.append(x if b else -x)
    head = f'c n=9 pseudo-disk track, canonical cube {ci} {c}\n' + f'p cnf {nv} {ncl + len(units)}\n'
    tail = ''.join(f'{u} 0\n' for u in units)
    return head, body, tail


def write_cube(ci, out, use_cache=True):
    head, body, tail = cube_parts(ci, use_cache)
    with open(out, 'w') as f:      # text mode: CRLF on Windows, LF elsewhere
        f.write(head)
        f.write(body)
        f.write(tail)


if __name__ == '__main__':
    if sys.argv[1] == '--list':
        print('\n'.join(map(str, canon)))
    else:
        ci = int(sys.argv[1])
        assert ci in canon, 'not a canonical cube index'
        write_cube(ci, sys.argv[2], use_cache='--no-cache' not in sys.argv)
