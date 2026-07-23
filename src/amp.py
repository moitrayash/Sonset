import math, datetime as dt, numpy as np
from solar import CITIES, solar_events

YEAR=2026
days=[dt.date(YEAR,1,1)+dt.timedelta(days=i) for i in range(365)]
EPS=23.4392  # obliquity

def amp_empirical(lat, lon):
    dl=[]
    for d in days:
        sr,ss,*_=solar_events(d,lat,lon)
        dl.append((ss-sr)/60)
    return max(dl)-min(dl), max(dl), min(dl)

def amp_theory(lat_deg, refraction=True):
    """Geometric solstice-to-solstice daylight amplitude, hours."""
    phi=math.radians(lat_deg); eps=math.radians(EPS)
    z=math.radians(90.833) if refraction else math.radians(90.0)
    def H(decl):
        c=(math.cos(z)/(math.cos(phi)*math.cos(decl)) - math.tan(phi)*math.tan(decl))
        c=max(-1,min(1,c)); return math.degrees(math.acos(c))
    return (2/15)*(H(eps)-H(-eps))

def amp_clean(lat_deg):
    """No-refraction closed form: (4/15)*arcsin(tan(phi)tan(eps)) in degrees."""
    x=math.tan(math.radians(lat_deg))*math.tan(math.radians(EPS))
    if abs(x)>=1: return float('nan')
    return (4/15)*math.degrees(math.asin(x))

rows=[]
for code,c in CITIES.items():
    a,mx,mn=amp_empirical(c["lat"],c["lon"])
    rows.append((code,c["name"],c["lat"],a,amp_theory(c["lat"]),amp_clean(c["lat"])))
rows.sort(key=lambda r:r[2])

if __name__ == "__main__":
    print(f"{'city':<6}{'lat':>7}{'A_emp':>9}{'A_theory':>10}{'A_norefr':>10}")
    for r in rows: print(f"{r[0]:<6}{r[2]:>7.2f}{r[3]:>9.3f}{r[4]:>10.3f}{r[5]:>10.3f}")

    lat=np.array([r[2] for r in rows]); A=np.array([r[3] for r in rows])
    tanphi=np.tan(np.radians(lat))
    phys=np.array([amp_clean(l) for l in lat])

    def stats(x,y,label):
        r=np.corrcoef(x,y)[0,1]
        b,a0=np.polyfit(x,y,1)
        pred=b*x+a0
        resid=y-pred
        ss=1-np.sum(resid**2)/np.sum((y-y.mean())**2)
        print(f"\n{label}: r={r:.6f}  r^2={r**2:.6f}  slope={b:.4f}  int={a0:.4f}")
        print(f"  max|resid| = {np.max(np.abs(resid)):.3f} h ({np.max(np.abs(resid))*60:.1f} min)")
        print("  residuals (h):", np.round(resid,3))
        return b,a0

    stats(lat,A,"A ~ latitude (deg)")
    stats(tanphi,A,"A ~ tan(latitude)")
    stats(phys,A,"A ~ physical model")

    # where does the linear fit break
    b,a0=np.polyfit(lat,A,1)
    print("\nExtrapolation check (linear fit on the 5 cities vs truth):")
    for L in [0,5,10,30,50,55,60,63,66.0,66.5]:
        t=amp_theory(L); lin=b*L+a0
        print(f"  lat {L:>5.1f}: truth {t:6.2f} h   linear {lin:6.2f} h   err {lin-t:+6.2f} h")
