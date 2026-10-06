# Independent spot-check (verifier). Does NOT import/copy solve.py.
# Own Rouwenhorst, own EGM (n_a=250, power-3 grid, a_max=80), own Young-lottery stationary dist via power iteration.
import numpy as np
from scipy.optimize import brentq
beta,mu,alpha,delta,rho,sig,nz=0.96,3.0,0.36,0.08,0.9,0.2,7

def rouw(n,rho,s):
    p=(1+rho)/2; P=np.array([[p,1-p],[1-p,p]])
    for k in range(3,n+1):
        Q=np.zeros((k,k)); Q[:-1,:-1]+=p*P; Q[:-1,1:]+=(1-p)*P; Q[1:,:-1]+=(1-p)*P; Q[1:,1:]+=p*P
        Q[1:-1]/=2; P=Q
    return np.linspace(-np.sqrt(n-1)*s,np.sqrt(n-1)*s,n),P
x,P=rouw(nz,rho,sig)
# stationary dist of z (binomial)
pz=np.ones(nz)/nz
for _ in range(5000): pz=pz@P
z=np.exp(x); z=z/(z@pz)

def wage(r):
    K=(alpha/(r+delta))**(1/(1-alpha)); return (1-alpha)*K**alpha, K

def Ks(r,b,na=250,amax=80.0):
    w,Kd=wage(r)
    phi=b if r<=0 else min(b,w*z.min()/r)
    a=-phi+(amax+phi)*np.linspace(0,1,na)**3   # grid on [-phi,amax]
    up=lambda c:c**(-mu); iup=lambda m:m**(-1/mu)
    c=np.maximum(r*a[:,None]+w*z[None,:],1e-3)   # initial guess
    for it in range(5000):
        m=beta*(1+r)*(up(c)@P.T)            # E[u'(c')] at a' grid, by current z
        cend=iup(m)                          # c today for a' = a[i]
        aend=(cend+a[:,None]-w*z[None,:])/(1+r)  # beginning-of-period assets
        cn=np.empty_like(c)
        for j in range(nz):
            cn[:,j]=np.interp(a,aend[:,j],cend[:,j])
            low=a<aend[0,j]
            cn[low,j]=(1+r)*a[low]+w*z[j]+phi   # constrained: a'=-phi
        if np.max(np.abs(cn-c))<1e-9: c=cn; break
        c=cn
    ap=(1+r)*a[:,None]+w*z[None,:]-c
    ap=np.clip(ap,-phi,amax)
    # Young lottery
    idx=np.clip(np.searchsorted(a,ap,side='right')-1,0,na-2)
    wt=np.clip((a[idx+1]-ap)/(a[idx+1]-a[idx]),0,1)
    D=np.ones((na,nz))/(na*nz)
    for it in range(20000):
        Dn=np.zeros_like(D)
        for j in range(nz):
            np.add.at(Dn,(idx[:,j],j),D[:,j]*wt[:,j])
            np.add.at(Dn,(idx[:,j]+1,j),D[:,j]*(1-wt[:,j]))
        Dn=Dn@P
        if np.abs(Dn-D).max()<1e-13: D=Dn; break
        D=Dn
    return (D*a[:,None]).sum()-Kd

def eq(b):
    f=lambda r:Ks(r,b)
    r=brentq(f,-delta+0.02,1/beta-1-1e-4,xtol=1e-10)
    w,K=wage(r); Y=K**alpha
    return r,delta*K/Y,K/Y

for b in (0.0,8.0):
    r,s,ky=eq(b)
    print(f"b={b}: r={100*r:.4f}%  saving rate={100*s:.3f}%  K/Y={ky:.4f}")
