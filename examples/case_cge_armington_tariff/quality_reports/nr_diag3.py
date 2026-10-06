import sys, numpy as np
sys.path.insert(0,'model/03_solve/armington_tariff')
import solve as S
from scipy.optimize import minimize_scalar
b=S.load_base(); N=3; ones=np.ones_like(b.X); D=np.zeros(N)
def W(t,base=b):
    tp=base.t.copy(); tp[1,0,0]=t
    w,_=S.solve_levels(base,tp,D); return S.solve_levels(base,tp,D)[1][0]-1
for t in [0.09,0.10,0.11,0.12]: print(t,"levels W_A %",100*W(t))
r=minimize_scalar(lambda t:-W(t),bounds=(0,0.6),method='bounded',options={'xatol':1e-8}); print("continuous opt t*",r.x,100*-r.fun)
# exposure shares
print("B->A MAN share of A MAN spend",b.lam[1,0,0],"share of B sales",b.X[1,0,0]/b.Y[1])
# closed-form-ish: small-exposure intuition; eps dependence of t*
raw=S.load_base(flows_file="trade_flows.csv")
for e in [2,4,8]:
    p=S.purge_deficits(S.Base(raw.regions,raw.sectors,raw.X,raw.t,np.array([e,4.0])))
    r=minimize_scalar(lambda t:-W(t,p),bounds=(0,0.6),method='bounded',options={'xatol':1e-7}); print("eps_MAN",e,"t*",r.x)
# grid csv vs levels at a few points, and zero-welfare crossing
import csv
rows=list(csv.DictReader(open('output/tables/armington_tariff_optimal_tariff_grid.csv')))
mx=max(abs(float(r['A_welfare_pct'])-100*W(float(r['tariff_A_on_B_MAN']))) for r in rows[::5]); print("grid vs levels max diff pct pts",mx)
