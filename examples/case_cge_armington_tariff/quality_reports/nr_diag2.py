import sys, numpy as np
sys.path.insert(0,'model/03_solve/armington_tariff')
import solve as S
from scipy.optimize import root
pur=S.load_base(flows_file="trade_flows_purged.csv"); N=3
dh=np.ones_like(pur.X); Dp=np.zeros(N)
def Fr(x,tp):
    r,_=S.clearing_residuals(pur,x,tp,dh,Dp); r=r/pur.Y.sum(); r[2]=(x*pur.Y).sum()/pur.Y.sum()-1; return r
for seed in range(3):
    x0=np.exp(np.random.RandomState(seed).randn(N)*0.3)
    s=root(Fr,x0,args=(pur.t,),method='hybr',tol=1e-13); print("zero-shock perturbed start dev",np.abs(s.x-1).max(), "nfev",s.nfev)
print("trade_balance after S1 using purged D:", np.abs(pur.D).max())
# S1 tariff on A->B in which direction: scenarios.csv S1 = exporter B importer A
tp=S.load_scenario(pur,"S1"); print("S1 tariff nonzero idx",np.argwhere(tp>0), "regions",pur.regions)
# convergence-tol sensitivity: solve with tol 1e-8 vs 1e-13 effect
s8=root(Fr,np.ones(N),args=(tp,),method='hybr',tol=1e-8); s13=root(Fr,np.ones(N),args=(tp,),method='hybr',tol=1e-13)
print("tol1e-8 vs 1e-13 dw",np.abs(s8.x-s13.x).max())
