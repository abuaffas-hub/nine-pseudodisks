import itertools, pickle, time
from arr import valid
from enumtypes import enum
C=list(range(4))
def orders(i):
    labs=[(j,s) for j in C if j!=i for s in (0,1)]
    a=labs[0]
    return [tuple([a]+list(p)) for p in itertools.permutations(labs[1:])]
O={i:orders(i) for i in C}
def rkey(L,i,T):
    L=[p for p in L if p[0] in T]
    a=(min(j for j in T if j!=i),0); k=L.index(a); return tuple(L[k:]+L[:k])
# valid triple keys, for generic triple T=(a<b<c) relabelled
t3=enum(3)
good3=set(tuple(rkey(s[i],i,(0,1,2)) for i in range(3)) for s in t3)
def relab(key,T):
    inv={x:r for r,x in enumerate(T)}
    return tuple(tuple((inv[j],s) for j,s in L) for L in key)
def tri_ok(sel,T):
    k=tuple(rkey(sel[i],i,T) for i in T)
    return relab(k,T) in good3
t=time.time(); out=[]
for o0 in O[0]:
  for o1 in O[1]:
    for o2 in O[2]:
      sel={0:o0,1:o1,2:o2}
      if not tri_ok(sel,(0,1,2)): continue
      for o3 in O[3]:
        sel[3]=o3
        if tri_ok(sel,(0,1,3)) and tri_ok(sel,(0,2,3)) and tri_ok(sel,(1,2,3)):
          if valid(dict(sel)): out.append(dict(sel))
print(len(out),'valid labelled 4-configs',time.time()-t)
pickle.dump(out,open('t4.pkl','wb'))
