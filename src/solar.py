import math, datetime as dt
from zoneinfo import ZoneInfo

R = math.radians
D = math.degrees

CITIES = {
    "NYC": dict(name="New York City", lat=40.7128, lon=-74.0060, tz="America/New_York", std=-5.0),
    "DEL": dict(name="Delhi",         lat=28.6139, lon= 77.2090, tz="Asia/Kolkata",     std= 5.5),
    "CCU": dict(name="Kolkata",       lat=22.5726, lon= 88.3639, tz="Asia/Kolkata",     std= 5.5),
    "BOM": dict(name="Mumbai",        lat=19.0760, lon= 72.8777, tz="Asia/Kolkata",     std= 5.5),
    "SEA": dict(name="Seattle",       lat=47.6062, lon=-122.3321, tz="America/Los_Angeles", std=-8.0),
}

def julian_day(d):
    y, m = d.year, d.month
    if m <= 2:
        y -= 1; m += 12
    A = y // 100
    B = 2 - A + A // 4
    return math.floor(365.25*(y+4716)) + math.floor(30.6001*(m+1)) + d.day + B - 1524.5

def solar_events(d, lat, lon):
    """Return (sunrise_utc_minutes, sunset_utc_minutes, noon_utc_minutes, decl_deg, eqtime_min)."""
    jd = julian_day(d) + 0.5 - lon/360.0   # approx local noon
    jc = (jd - 2451545.0) / 36525.0

    L0 = (280.46646 + jc*(36000.76983 + jc*0.0003032)) % 360.0
    M  = 357.52911 + jc*(35999.05029 - 0.0001537*jc)
    e  = 0.016708634 - jc*(0.000042037 + 0.0000001267*jc)
    C  = (math.sin(R(M))*(1.914602 - jc*(0.004817 + 0.000014*jc))
          + math.sin(R(2*M))*(0.019993 - 0.000101*jc)
          + math.sin(R(3*M))*0.000289)
    true_long = L0 + C
    app_long  = true_long - 0.00569 - 0.00478*math.sin(R(125.04 - 1934.136*jc))
    mean_obl  = 23 + (26 + (21.448 - jc*(46.815 + jc*(0.00059 - jc*0.001813)))/60)/60
    obl_corr  = mean_obl + 0.00256*math.cos(R(125.04 - 1934.136*jc))
    decl = D(math.asin(math.sin(R(obl_corr))*math.sin(R(app_long))))

    vary = math.tan(R(obl_corr/2))**2
    eqtime = 4*D(vary*math.sin(2*R(L0)) - 2*e*math.sin(R(M))
                 + 4*e*vary*math.sin(R(M))*math.cos(2*R(L0))
                 - 0.5*vary*vary*math.sin(4*R(L0))
                 - 1.25*e*e*math.sin(2*R(M)))

    cosH = (math.cos(R(90.833))/(math.cos(R(lat))*math.cos(R(decl)))
            - math.tan(R(lat))*math.tan(R(decl)))
    if cosH > 1:  return (None, None, None, decl, eqtime)   # polar night
    if cosH < -1: return (None, None, None, decl, eqtime)   # midnight sun
    ha = D(math.acos(cosH))

    noon_utc = 720 - 4*lon - eqtime
    return (noon_utc - 4*ha, noon_utc + 4*ha, noon_utc, decl, eqtime)

def utc_dt(d, minutes):
    return dt.datetime.combine(d, dt.time(0), tzinfo=dt.timezone.utc) + dt.timedelta(minutes=minutes)

if __name__ == "__main__":
    checks = [("NYC", dt.date(2026,6,4)), ("NYC", dt.date(2026,11,8)),
              ("SEA", dt.date(2026,6,4)), ("DEL", dt.date(2026,6,4)),
              ("BOM", dt.date(2026,6,4)), ("CCU", dt.date(2026,6,4))]
    for code, d in checks:
        c = CITIES[code]
        sr, ss, *_ = solar_events(d, c["lat"], c["lon"])
        civ = utc_dt(d, ss).astimezone(ZoneInfo(c["tz"]))
        rise = utc_dt(d, sr).astimezone(ZoneInfo(c["tz"]))
        print(f"{code} {d}  rise {rise:%H:%M %Z}   set {civ:%H:%M %Z}")
