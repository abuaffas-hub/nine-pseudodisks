import sys, time, itertools, pickle
from pysat.solvers import Solver
from encode import Enc
from arr import valid, minimal_invalid, helly, restrict


def three_pierceable(seq, n):
    H = {t for t in itertools.combinations(range(n), 3) if helly(seq, t)}
    from encode import set_partitions3
    for P in set_partitions3(n):
        if all(t in H for B in P for t in itertools.combinations(sorted(B), 3)):
            return P
    return None


def cegar(n, solver='cadical153', max_iter=100000, log_every=50, extra=None, verbose=True):
    t0 = time.time()
    E = Enc(n)
    if extra:
        extra(E)
    S = Solver(name=solver, bootstrap_with=E.cl)
    nbase = len(E.cl)
    if verbose:
        print(f'n={n}: vars={E.pool.top} clauses={nbase} (bad 3-combos per triple={E.n_bad3})', flush=True)
    sizes = {}
    it = 0
    while True:
        it += 1
        if not S.solve():
            print(f'n={n}: UNSAT after {it-1} refinements, {time.time()-t0:.1f}s; blocked subset sizes {sizes}', flush=True)
            return 'UNSAT', E, None
        seq = E.decode(S.get_model())
        if valid(seq):
            assert three_pierceable(seq, n) is None
            print(f'n={n}: SAT with exactly realizable arrangement after {it-1} refinements, {time.time()-t0:.1f}s; blocked sizes {sizes}', flush=True)
            return 'SAT', E, seq
        Sm = minimal_invalid(seq)
        sizes[len(Sm)] = sizes.get(len(Sm), 0) + 1
        before = len(E.cl)
        E.forbid(seq, Sm)          # may also create new cyc variables with defining clauses
        for c in E.cl[before:]:    # add the definitions and the blocking clause
            S.add_clause(c)
        if verbose and it % log_every == 0:
            print(f'  iter {it}: blocked sizes {sizes}  {time.time()-t0:.1f}s', flush=True)
        if it >= max_iter:
            return 'UNKNOWN', E, None


if __name__ == '__main__':
    n = int(sys.argv[1])
    from encode import add_four_table
    res, E, seq = cegar(n, extra=add_four_table, log_every=500)
    if seq is not None:
        pickle.dump(seq, open(f'witness_{n}.pkl', 'wb'))
