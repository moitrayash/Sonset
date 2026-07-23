"""Daily solar data for the 25-location set, four clock conventions.

Reuses the validated NOAA engine in solar.py unchanged. Adds civil twilight
(zenith 96 deg, geometric, no refraction term: refraction is already tiny at
-6 deg solar altitude) and the two Sunshine Protection Act scenario clocks.

Clock conventions carried per day (offsets in minutes added to UTC event time):
  std   fixed standard offset, DST ignored (the operator's "local unadjusted")
  civ   wall clock via zoneinfo; jagged where DST or "whatnot" applies
  spaA  scenario, 2026 as-lived: identical to civ through 31 Oct, then the
        1 Nov fall-back is cancelled and the clock stays on std+1h. US only.
  spaS  scenario, steady state: permanent DST (std+1h) all 365 days. US only.
For non-US locations spaA == spaS == civ by construction.

The House passed the Sunshine Protection Act 308-117 on 14 Jul 2026; the text
carries no effective date, so the as-lived variant assumes enactment before
1 Nov 2026 and no state opt-outs. That assumption is the scenario, not a fact.

Offset choice on transition days: one offset per day, evaluated at the sunset
instant, matching analyze.py. Every DST transition in this set happens at
01:00-03:00 local, hours before dawn, so sunrise and sunset always share an
offset and the simplification is exact for these events.
"""

import math, datetime as dt
from zoneinfo import ZoneInfo
from solar import solar_events, utc_dt
from locations_g20 import LOCATIONS, ORDER

YEAR = 2026
SPA_CUT = dt.date(YEAR, 11, 1)          # the fall-back the scenario cancels
DAYS = [dt.date(YEAR, 1, 1) + dt.timedelta(days=i)
        for i in range((dt.date(YEAR + 1, 1, 1) - dt.date(YEAR, 1, 1)).days)]

R, D = math.radians, math.degrees


def hour_angle(lat, decl, zenith):
    cosH = (math.cos(R(zenith)) / (math.cos(R(lat)) * math.cos(R(decl)))
            - math.tan(R(lat)) * math.tan(R(decl)))
    if abs(cosH) > 1:
        return None                      # sun never reaches this zenith today
    return D(math.acos(cosH))


def compute(code):
    """Per-day record lists for one location. All event times are raw UTC
    minutes from local midnight of the UTC date (may exceed 1440 or go
    negative; wrap only at the formatting boundary, per README section 4)."""
    c = LOCATIONS[code]
    tz = ZoneInfo(c["tz"])
    rec = dict(dates=DAYS, rise_utc=[], set_utc=[], dawn_utc=[], dusk_utc=[],
               off_std=[], off_civ=[], off_spaA=[], off_spaS=[],
               daylight=[], dst=[])
    std_min = c["std"] * 60.0
    for d in DAYS:
        sr, ss, noon, decl, eq = solar_events(d, c["lat"], c["lon"])
        if sr is None:
            raise ValueError(f"{code} {d}: polar day/night; set is not built for this")
        H96 = hour_angle(c["lat"], decl, 96.0)
        if H96 is None:
            raise ValueError(f"{code} {d}: no civil twilight boundary")
        off_civ = utc_dt(d, ss).astimezone(tz).utcoffset().total_seconds() / 60.0
        if c["us"]:
            off_spaA = off_civ if d < SPA_CUT else std_min + 60.0
            off_spaS = std_min + 60.0
        else:
            off_spaA = off_spaS = off_civ
        rec["rise_utc"].append(sr)
        rec["set_utc"].append(ss)
        rec["dawn_utc"].append(noon - 4.0 * H96)
        rec["dusk_utc"].append(noon + 4.0 * H96)
        rec["off_std"].append(std_min)
        rec["off_civ"].append(off_civ)
        rec["off_spaA"].append(off_spaA)
        rec["off_spaS"].append(off_spaS)
        rec["daylight"].append((ss - sr) / 60.0)
        rec["dst"].append(abs(off_civ - std_min) > 1e-6)
    return rec


def compute_all():
    return {code: compute(code) for code in ORDER}


def hhmm(m):
    m = m % 1440
    return f"{int(m // 60):02d}:{int(round(m % 60)) % 60:02d}"


VARIANTS = [("std", "off_std"), ("civ", "off_civ"),
            ("spaA", "off_spaA"), ("spaS", "off_spaS")]


def local(rec, i, event, offkey):
    return rec[event][i] + rec[offkey][i]


# ------------------------------------------------------------- self checks
if __name__ == "__main__":
    data = compute_all()
    fails = []

    def check(label, got, want, tol_min=2.0):
        ok = abs(got - want) <= tol_min
        print(f"{'ok ' if ok else 'FAIL'} {label}: got {hhmm(got)} want {hhmm(want)}")
        if not ok:
            fails.append(label)

    def m(h, mm):
        return h * 60 + mm

    i0604 = DAYS.index(dt.date(YEAR, 6, 4))
    i0722 = DAYS.index(dt.date(YEAR, 7, 22))

    # README section 5 almanac anchors, must keep passing (JFK = the NYC row)
    check("JFK 4 Jun sunset EDT", local(data["JFK"], i0604, "set_utc", "off_civ"), m(20, 23))
    check("CCU 4 Jun sunset IST", local(data["CCU"], i0604, "set_utc", "off_civ"), m(18, 18))
    check("SEA 4 Jun sunset PDT", local(data["SEA"], i0604, "set_utc", "off_civ"), m(21, 1))

    # ground truth from the operator's 22 Jul screen recording (iOS Weather, Seattle)
    check("SEA 22 Jul sunrise", local(data["SEA"], i0722, "rise_utc", "off_civ"), m(5, 34))
    check("SEA 22 Jul sunset", local(data["SEA"], i0722, "set_utc", "off_civ"), m(20, 56))
    check("SEA 22 Jul first light", local(data["SEA"], i0722, "dawn_utc", "off_civ"), m(4, 56))
    check("SEA 22 Jul last light", local(data["SEA"], i0722, "dusk_utc", "off_civ"), m(21, 34))

    # scenario arithmetic, JFK Christmas: civil EST, both SPA clocks one hour later
    i1225 = DAYS.index(dt.date(YEAR, 12, 25))
    civ = local(data["JFK"], i1225, "set_utc", "off_civ")
    spa = local(data["JFK"], i1225, "set_utc", "off_spaA")
    sps = local(data["JFK"], i1225, "set_utc", "off_spaS")
    print(f"{'ok ' if abs(spa - civ - 60) < 1e-9 and abs(sps - spa) < 1e-9 else 'FAIL'} "
          f"JFK 25 Dec: civ {hhmm(civ)}, spaA {hhmm(spa)}, spaS {hhmm(sps)} (+60 both)")
    if not (abs(spa - civ - 60) < 1e-9 and abs(sps - spa) < 1e-9):
        fails.append("SPA offsets")

    # spaA equals civ strictly before 1 Nov, for a US city
    i1031 = DAYS.index(dt.date(YEAR, 10, 31))
    assert data["MIA"]["off_spaA"][i1031] == data["MIA"]["off_civ"][i1031]
    # non-US never diverges
    for code in ORDER:
        if not LOCATIONS[code]["us"]:
            assert data[code]["off_spaA"] == data[code]["off_civ"] == data[code]["off_spaS"], code

    # DST transition dates seen in the civil offsets
    print("\nDST transitions found (date, hours jump):")
    for code in ORDER:
        r = data[code]
        moves = [(DAYS[i], (r["off_civ"][i] - r["off_civ"][i - 1]) / 60.0)
                 for i in range(1, len(DAYS)) if r["off_civ"][i] != r["off_civ"][i - 1]]
        if moves:
            print(f"  {code}: " + ", ".join(f"{d:%d %b} {j:+.0f}h" for d, j in moves))

    # range sanity: no local event should wrap past midnight
    for code in ORDER:
        r = data[code]
        for _, offkey in VARIANTS:
            for ev in ("dawn_utc", "rise_utc", "set_utc", "dusk_utc"):
                vals = [r[ev][i] + r[offkey][i] for i in range(len(DAYS))]
                if min(vals) <= 0 or max(vals) >= 1440:
                    fails.append(f"wrap {code} {ev} {offkey}")
                    print(f"FAIL wrap: {code} {ev} {offkey} range "
                          f"{min(vals):.0f}..{max(vals):.0f}")

    print(f"\n{'ALL CHECKS PASS' if not fails else 'FAILURES: ' + str(fails)}")
    raise SystemExit(0 if not fails else 1)
