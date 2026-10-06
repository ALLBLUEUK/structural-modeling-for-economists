import sys, json, numpy as np
sys.path.insert(0,'model/03_solve/armington_tariff')
import solve as S
from scipy.optimize import root
np.set_printoptions(precision=6, linewidth=160)
raw = S.load_base(flows_file="trade_flows.csv")
pur = S.load_base(flows_file="trade_flows_purged.csv")
N=3
print("raw D",raw.D,"alpha rows sum",raw.alpha.sum(1))
# 1 repurge
rp = S.purge_deficits(raw)
print("repurge vs csv max abs diff", np.abs(rp.X-pur.X).max())
print("purged D after csv reload", pur.D, "Y",pur.Y, "sumD",pur.D.sum())
print("purged min flow", pur.X.min(), "trade balance purged", (pur.X.sum(axis=(1,2)) - pur.gross.sum(axis=(0,2))))
# idempotent
pp = S.purge_deficits(pur); print("purge idempotence diff", np.abs(pp.X-pur.X).max())
# purge on raw: wage changes and cond
tp=raw.t; dh=np.ones_like(raw.X)
w,_=S.solve_hybr(raw,tp,dh,np.zeros(N)); print("purge what",w)
# raw zero-shock with D
w0,_=S.solve_hybr(raw,tp,dh,raw.D); print("raw zero shock w dev",np.abs(w0-1).max())
# jacobian cond at S1 solution
tpS1=S.load_scenario(pur,"S1")
w1,_=S.solve_hybr(pur,tpS1,dh,np.zeros(N))
def F(x):
    r,_=S.clearing_residuals(pur,x,tpS1,dh,np.zeros(N)); return r/pur.Y.sum()
def jac(f,x,h=1e-6):
    J=np.zeros((N,N))
    for k in range(N):
        e=np.zeros(N);e[k]=h; J[:,k]=(f(x+e)-f(x-e))/(2*h)
    return J
J=jac(F,w1); print("Jac full\n",J,"\nsv",np.linalg.svd(J)[1])
def Fr(x):
    r=F(x); r[2]=(x*pur.Y).sum()/pur.Y.sum()-1; return r
Jr=jac(Fr,w1); print("cond reduced Jac", np.linalg.cond(Jr))
# Walras identity off-equilibrium
for _ in range(3):
    x=np.exp(np.random.randn(N)*0.3); print("sum resid off-eq (should be 0):",F(x).sum(), "resid",F(x))
# multi-start
sols=[]
for _ in range(30):
    x0=np.exp(np.random.randn(N)*0.5)
    s=root(Fr,x0,method='hybr',tol=1e-13); 
    if np.abs(Fr(s.x)).max()<1e-12: sols.append(s.x/ (s.x*pur.Y).sum()*pur.Y.sum())
print("multistart converged",len(sols),"/30 max dev",np.abs(np.array(sols)-w1).max())
# ACR tautology: arbitrary w
Xs=pur.X.sum(axis=2,keepdims=True)
b1=S.Base(pur.regions,["ALL"],Xs,np.zeros_like(Xs),np.array([4.0])); b1=S.purge_deficits(b1)
dh1=np.ones_like(b1.X); dh1[0,1,0]=1.25; dh1[2,0,0]=0.9
for wtest in [np.array([1.0,1.0,1.0]),np.array([1.3,0.7,1.1])]:
    o=S.outcomes(b1,wtest,b1.t,dh1,np.zeros(N))
    lj=np.array([o["lamp"][j,j,0]/b1.lam[j,j,0] for j in range(N)])
    print("ACR diff at NON-equilibrium w",wtest,np.abs(o["What"]-lj**(-0.25)).max(), "clear resid",o["clearing_residuals"]/b1.Y.sum())
# ACR nontrivial: does the shock matter? What values
wa,_=S.solve_hybr(b1,b1.t,dh1,np.zeros(N)); oa=S.outcomes(b1,wa,b1.t,dh1,np.zeros(N)); print("ACR eq What",oa["What"],"w",wa)
# ACR with ε in the check = base.eps.mean (ok)  ; ACR with tariff would break
# numeraire neutrality incl. w scaling
tp2=pur.t.copy(); tp2[0,1,0]+=0.1
a,_=S.solve_hybr(pur,tp2,dh,np.zeros(N)); b,_=S.solve_hybr(pur,tp2,dh,np.zeros(N),numeraire=0)
print("w ratio invariance",np.abs(a/a[0]-b).max(), "scale",a[0])
oa=S.outcomes(pur,a,tp2,dh,np.zeros(N)); ob=S.outcomes(pur,b,tp2,dh,np.zeros(N)); print("What diff",np.abs(oa["What"]-ob["What"]).max())
# numeraire failure with raw D!=0
a,_=S.solve_hybr(raw,tp2,dh,raw.D); b,_=S.solve_hybr(raw,tp2,dh,raw.D,numeraire=0)
oa=S.outcomes(raw,a,tp2,dh,raw.D); ob=S.outcomes(raw,b,tp2,dh,raw.D); print("RAW (D!=0) What diff (expected nonzero)",np.abs(oa["What"]-ob["What"]).max())
# two solver independence: iterate vs hybr on S2, damp variants
tpS2=S.load_scenario(pur,"S2")
wh,_=S.solve_hybr(pur,tpS2,dh,np.zeros(N)); wi,it=S.solve_iterate(pur,tpS2,dh,np.zeros(N)); print("S2 two solver",np.abs(wh-wi).max(),it)
for e in [2,8]:
    p2=S.Base(pur.regions,pur.sectors,pur.X,pur.t,np.array([e,e],float)); p2=S.purge_deficits(p2)
    ww,_=S.solve_hybr(p2,tpS1,dh,np.zeros(N)); print("eps",e,"w",ww)
# eps_MAN sweep boundary exactness: rounding of purged csv effects
print("sector emp checks S1", json.load(open('output/checkpoints/armington_tariff_S1.json'))['diagnostics'])
# sensitivity of results to csv 10-decimal rounding: relative size
print("csv rounding D", np.abs(pur.D).max())
# iterate solver stopping tol 1e-13 on w: residual
print("resid at iter sol", np.abs(F(wi)).max() if False else np.abs(Fr(S.solve_iterate(pur,tpS1,dh,np.zeros(N))[0])).max())
# welfare numbers magnitude vs tolerance
print("S1 welfare dev sizes ~1e-4; tolerances 1e-9 relative to effects:",1e-9/2e-4)
