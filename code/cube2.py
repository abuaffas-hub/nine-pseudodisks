import sys, itertools, pickle, time, argparse
from pysat.solvers import Solver
from encode import Enc, add_four_table, add_vertex_helly, add_k1, add_h1
from run_sb import sb
from arr import valid, minimal_invalid
ap=argparse.ArgumentParser(); ap.add_argument('--start',type=int,default=0); ap.add_argument('--end',type=int,default=10**9)
ap.add_argument('--only',type=str,default=''); ap.add_argument('--track',default='disk'); ap.add_argument('--step',type=int,default=1); ap.add_argument('--canon',action='store_true'); ap.add_argument('--skip',default='')
a=ap.parse_args()
n=9; t0=time.time()
E=Enc(n); sb(E)                         # 3/4-tables, {0,1,2} non-Helly, lex sort of 3..8
add_vertex_helly(E); add_k1(E)          # pseudo-disk-valid
if a.track=='disk':
    for Q in itertools.combinations(range(n),4):   # Lemma 5.1 (disks)
        E.cl.append([-E.H[t] for t in itertools.combinations(Q,3)])
    add_h1(E)                                       # Theorem H1 (disks)
S=Solver(name='cadical195',bootstrap_with=E.cl)
print('built',a.track,E.pool.top,'vars',len(E.cl),'clauses',f'{time.time()-t0:.1f}s',flush=True)
vecs=list(itertools.product((1,0),repeat=3))
cubes=list(itertools.combinations_with_replacement(range(8),6))
def rot(c):
    # relabel 0->1->2->0 maps (b01,b02,b12) -> (b02,b12,b01); hole triangle A is invariant
    return tuple(sorted(vecs.index((vecs[v][1],vecs[v][2],vecs[v][0])) for v in c))
canon=[ci for ci,c in enumerate(cubes) if c<=rot(c) and c<=rot(rot(c))]
if a.canon: print('canonical cubes',len(canon),flush=True)
pool=canon if a.canon else list(range(len(cubes)))
import re, glob
skip=set()
for f in (a.skip.split(',') if a.skip else []):
    for g in glob.glob(f):
        for l in open(g):
            m=re.match(r'cube (\d+) .* UNSAT',l)
            if m: skip.add(int(m.group(1)))
pool=[ci for ci in pool if ci not in skip]
idx=[int(x) for x in a.only.split(',')] if a.only else pool[a.start:a.end:a.step]
for ci in idx:
    c=cubes[ci]; assum=[]
    for k,vi in enumerate(c):
        i=3+k
        for x,b in zip([E.H[(0,1,i)],E.H[(0,2,i)],E.H[(1,2,i)]],vecs[vi]): assum.append(x if b else -x)
    t=time.time(); ref=0
    while S.solve(assumptions=assum):
        seq=E.decode(S.get_model())
        if valid(seq):
            print('SAT cube',ci,c,flush=True); pickle.dump(seq,open(f'witness_{a.track}_cube{ci}.pkl','wb')); break
        Sm=minimal_invalid(seq); before=len(E.cl); E.forbid(seq,Sm)
        for cl in E.cl[before:]: S.add_clause(cl)   # new cyc definitions + blocking clause
        ref+=1
    else:
        print(f'cube {ci} {c} UNSAT {time.time()-t:.1f}s ref={ref} total {time.time()-t0:.0f}s',flush=True); continue
print('done',time.time()-t0,flush=True)
