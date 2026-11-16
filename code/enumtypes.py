import itertools, pickle, sys
from arr import valid, helly
def cyc_orders(labels):
    a=labels[0]
    for perm in itertools.permutations(labels[1:]):
        yield [a]+list(perm)
def enum(k):
    C=list(range(k))
    per=[list(cyc_orders([(j,s) for j in C if j!=i for s in (0,1)])) for i in C]
    out=[]
    if k==3:
        for combo in itertools.product(*per):
            seq=dict(zip(C,combo))
            if valid(seq): out.append(seq)
        return out
    # k=4: prune by triples
    tri=enum(3)
    def key3(seq,T):
        # canonical relabel to 0..2 keeping order
        mp={x:r for r,x in enumerate(T)}
        res=[]
        for i in T:
            L=[(mp[j],s) for j,s in seq[i] if j in mp]
            # rotate so first is (smallest other,0)
            a=min(mp[j] for j in T if j!=i); 
            st=L.index((a,0)); L=L[st:]+L[:st]
            res.append(tuple(L))
        return tuple(res)
    good3={key3(s,(0,1,2)) for s in tri}
    for combo in itertools.product(*per):
        seq=dict(zip(C,combo))
        if all(key3(seq,T) in good3 for T in itertools.combinations(C,3)):
            if valid(seq): out.append(seq)
    return out
if __name__=="__main__":
  t3=enum(3); print('valid 3-configs (labelled):',len(t3))
  print('Helly patterns:',sorted(set(helly(s,(0,1,2)) for s in t3)))
  from collections import Counter
  print(Counter(helly(s,(0,1,2)) for s in t3))
  pickle.dump(t3,open('t3.pkl','wb'))
