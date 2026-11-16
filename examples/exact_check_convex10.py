# Exact verification (rational arithmetic) for convex polygons:
# a family of convex polygons has a common point iff (Helly) every triple does; a triple (or pair) of
# convex polygons has a common point iff some candidate point - a vertex, or an intersection point of two
# edges - lies in all of them.
import json, itertools, sys
from fractions import Fraction as F
sys.path.insert(0,'../code')
from encode import set_partitions3
D=json.load(open('convex10_coordinates.json'))
polys=[]
for d in D:
    P=[(F(str(x)),F(str(y))) for x,y in d['pts']]
    a=sum(P[i][0]*P[(i+1)%len(P)][1]-P[(i+1)%len(P)][0]*P[i][1] for i in range(len(P)))
    if a<0: P=P[::-1]
    polys.append(P)
def cr(o,a,b): return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
def strictly_convex(P):
    # global test: every vertex not on an edge lies strictly to the left of that edge's line
    # (this also excludes self-intersecting polygons whose consecutive turns are all left turns)
    m=len(P)
    return all(cr(P[i],P[(i+1)%m],P[k])>0 for i in range(m) for k in range(m) if k not in (i,(i+1)%m))
def inside(P,q): return all(cr(P[i],P[(i+1)%len(P)],q)>=0 for i in range(len(P)))
def edges(P): return [(P[i],P[(i+1)%len(P)]) for i in range(len(P))]
def seg_inter(e,f):
    (p,p2),(q,q2)=e,f
    r=(p2[0]-p[0],p2[1]-p[1]); s=(q2[0]-q[0],q2[1]-q[1]); den=r[0]*s[1]-r[1]*s[0]
    if den==0: return None
    t=((q[0]-p[0])*s[1]-(q[1]-p[1])*s[0])/den; u=((q[0]-p[0])*r[1]-(q[1]-p[1])*r[0])/den
    return (p[0]+t*r[0],p[1]+t*r[1]) if 0<=t<=1 and 0<=u<=1 else None
def common(idx):
    cands=[v for i in idx for v in polys[i]]
    for i,j in itertools.combinations(idx,2):
        for e in edges(polys[i]):
            for f in edges(polys[j]):
                x=seg_inter(e,f)
                if x: cands.append(x)
    return any(all(inside(polys[k],q) for k in idx) for q in cands)
n=len(polys)
print('strictly convex:',all(strictly_convex(P) for P in polys))
print('pairwise intersecting:',all(common((i,j)) for i,j in itertools.combinations(range(n),2)))
# boundary crossing counts (exact): edges in general position -> count proper crossings
def crossings(i,j):
    c=0
    for e in edges(polys[i]):
        for f in edges(polys[j]):
            x=seg_inter(e,f)
            if x:
                assert x not in (e[0],e[1],f[0],f[1]), 'crossing at a vertex'
                c+=1
    return c
print('boundary crossings per pair:',sorted(set(crossings(i,j) for i,j in itertools.combinations(range(n),2))))
def on_boundary(P,q):
    return any(cr(a,b,q)==0 and min(a[0],b[0])<=q[0]<=max(a[0],b[0]) and min(a[1],b[1])<=q[1]<=max(a[1],b[1])
               for a,b in edges(P))
def no_triple_boundary_points():
    # every boundary crossing of two polygons lies on no third boundary (general position)
    for i,j in itertools.combinations(range(n),2):
        for e in edges(polys[i]):
            for f in edges(polys[j]):
                x=seg_inter(e,f)
                if x and any(on_boundary(polys[k],x) for k in range(n) if k not in (i,j)): return False
    return True
print('no point on three boundaries:',no_triple_boundary_points())
H={t for t in itertools.combinations(range(n),3) if common(t)}
def pierceable(idx):
    m=len(idx)
    for Pt in set_partitions3(m):
        if all(tuple(idx[k] for k in t) in H for B in Pt for t in itertools.combinations(sorted(B),3)): return True
    return False
print('Helly triples:',len(H))
print('3-pierceable:',pierceable(list(range(n))))
print('all 9-subfamilies 3-pierceable:',all(pierceable([k for k in range(n) if k!=r]) for r in range(n)))
