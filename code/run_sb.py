import sys, itertools, pickle
from run import cegar
from encode import add_four_table
def sb(E):
    add_four_table(E)
    n=E.n
    E.cl.append([-E.H[(0,1,2)]])
    def bits(i): return [E.H[(0,1,i)],E.H[(0,2,i)],E.H[(1,2,i)]]
    for i in range(3,n-1):
        a,b=bits(i),bits(i+1)
        for u in itertools.product((0,1),repeat=3):
            for v in itertools.product((0,1),repeat=3):
                if u<v:  # forbid b(i)=u, b(i+1)=v  (require non-increasing)
                    E.cl.append([(-x if ub else x) for x,ub in zip(a,u)]+[(-y if vb else y) for y,vb in zip(b,v)])
if __name__=="__main__":
  n=int(sys.argv[1]); solver=sys.argv[2] if len(sys.argv)>2 else 'cadical195'
  res,E,seq=cegar(n,solver=solver,extra=sb,log_every=500)
  if seq is not None: pickle.dump(seq,open(f'witness_sb_{n}.pkl','wb'))
