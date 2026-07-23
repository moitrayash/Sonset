import os, math, csv, datetime as dt
from zoneinfo import ZoneInfo
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter, MultipleLocator
from solar import CITIES, solar_events, utc_dt
from glyphcheck import check_figure

YEAR = 2026
OUT = os.environ.get("SOLAR_OUT", "/mnt/user-data/outputs")

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["cmr10", "CMU Serif", "DejaVu Serif"],
    "font.sans-serif": ["cmss10", "CMU Sans Serif", "DejaVu Sans"],
    "mathtext.fontset": "cm",
    "axes.formatter.use_mathtext": True,
    "axes.unicode_minus": False,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "savefig.facecolor": "white",
    "axes.edgecolor": "#333333",
    "axes.linewidth": 0.8,
    "grid.color": "#cccccc",
    "grid.linewidth": 0.5,
    "font.size": 10,
    "axes.titlesize": 12,
    "legend.frameon": False,
})

COLORS = {"NYC": "#1b3a6b", "DEL": "#a03020", "CCU": "#2e6b3a",
          "BOM": "#7a4b8f", "SEA": "#b5852a"}

def hhmm(minutes_after_midnight):
    m = minutes_after_midnight % 1440
    return f"{int(m//60):02d}:{int(round(m%60)):02d}"

def fmt_clock(x, pos=None):
    return hhmm(x)

# ---------------------------------------------------------------- compute
days = [dt.date(YEAR,1,1) + dt.timedelta(days=i)
        for i in range((dt.date(YEAR+1,1,1) - dt.date(YEAR,1,1)).days)]

data = {}
for code, c in CITIES.items():
    tz = ZoneInfo(c["tz"])
    rec = dict(dates=[], set_utc=[], set_std=[], set_civ=[], set_lmt=[],
               rise_civ=[], daylight=[], dst=[])
    for d in days:
        sr, ss, noon, decl, eq = solar_events(d, c["lat"], c["lon"])
        ss_utc_dt = utc_dt(d, ss)
        sr_utc_dt = utc_dt(d, sr)
        civ = ss_utc_dt.astimezone(tz)
        civr = sr_utc_dt.astimezone(tz)
        off_civ = civ.utcoffset().total_seconds()/3600.0

        rec["dates"].append(d)
        rec["set_utc"].append(ss % 1440)
        rec["set_std"].append((ss + c["std"]*60) % 1440)
        rec["set_civ"].append((ss + off_civ*60) % 1440)
        rec["set_lmt"].append((ss + c["lon"]/15.0*60) % 1440)
        rec["rise_civ"].append((sr + off_civ*60) % 1440)
        rec["daylight"].append((ss - sr)/60.0)
        rec["dst"].append(abs(off_civ - c["std"]) > 1e-6)
    data[code] = rec

# ---------------------------------------------------------------- CSV
with open(f"{OUT}/sunset_{YEAR}_all_cities.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["date","city_code","city","lat","lon","dst_in_effect",
                "sunrise_local_civil","sunset_utc","sunset_local_standard",
                "sunset_local_civil","sunset_local_mean_solar","daylight_hours"])
    for code, c in CITIES.items():
        r = data[code]
        for i, d in enumerate(r["dates"]):
            w.writerow([d, code, c["name"], c["lat"], c["lon"], int(r["dst"][i]),
                        hhmm(r["rise_civ"][i]), hhmm(r["set_utc"][i]),
                        hhmm(r["set_std"][i]), hhmm(r["set_civ"][i]),
                        hhmm(r["set_lmt"][i]), round(r["daylight"][i], 4)])

# ---------------------------------------------------------------- key dates table
KEY = [dt.date(YEAR,6,4), dt.date(YEAR,11,8)]
rows = []
for code, c in CITIES.items():
    r = data[code]
    for kd in KEY:
        i = r["dates"].index(kd)
        rows.append([code, c["name"], kd.isoformat(),
                     hhmm(r["set_utc"][i]), hhmm(r["set_std"][i]),
                     hhmm(r["set_civ"][i]), hhmm(r["set_lmt"][i]),
                     "yes" if r["dst"][i] else "no",
                     f"{r['daylight'][i]:.2f}"])
with open(f"{OUT}/key_dates_jun04_nov08.csv","w",newline="") as f:
    w = csv.writer(f)
    w.writerow(["code","city","date","sunset_utc","sunset_local_std",
                "sunset_local_civil","sunset_lmt","dst","daylight_h"])
    w.writerows(rows)

# ---------------------------------------------------------------- extremes summary
summary = []
for code, c in CITIES.items():
    r = data[code]
    civ = r["set_civ"]; std = r["set_std"]; dl = r["daylight"]
    i_late, i_early = civ.index(max(civ)), civ.index(min(civ))
    j_late, j_early = std.index(max(std)), std.index(min(std))
    summary.append(dict(
        code=code, name=c["name"], lat=c["lat"], lon=c["lon"],
        civ_late=(r["dates"][i_late], civ[i_late]),
        civ_early=(r["dates"][i_early], civ[i_early]),
        civ_amp=(max(civ)-min(civ))/60.0,
        std_late=(r["dates"][j_late], std[j_late]),
        std_early=(r["dates"][j_early], std[j_early]),
        std_amp=(max(std)-min(std))/60.0,
        dl_max=max(dl), dl_min=min(dl), dl_amp=max(dl)-min(dl)))

with open(f"{OUT}/summary_extremes.csv","w",newline="") as f:
    w = csv.writer(f)
    w.writerow(["code","city","lat","lon",
                "latest_sunset_civil_date","latest_sunset_civil",
                "earliest_sunset_civil_date","earliest_sunset_civil",
                "civil_swing_hours","standard_time_swing_hours",
                "longest_day_h","shortest_day_h","daylight_swing_h"])
    for s in summary:
        w.writerow([s["code"], s["name"], s["lat"], s["lon"],
                    s["civ_late"][0], hhmm(s["civ_late"][1]),
                    s["civ_early"][0], hhmm(s["civ_early"][1]),
                    round(s["civ_amp"],2), round(s["std_amp"],2),
                    round(s["dl_max"],2), round(s["dl_min"],2), round(s["dl_amp"],2)])

# ---------------------------------------------------------------- helpers
def month_axis(ax):
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b"))
    ax.set_xlim(dt.date(YEAR,1,1), dt.date(YEAR,12,31))
    ax.tick_params(axis="x", length=3)

def clock_axis(ax, step=30):
    ax.yaxis.set_major_formatter(FuncFormatter(fmt_clock))
    ax.yaxis.set_major_locator(MultipleLocator(step))

def shade_dst(ax, code):
    r = data[code]
    on = [i for i,v in enumerate(r["dst"]) if v]
    if not on: return
    # contiguous run
    ax.axvspan(r["dates"][on[0]], r["dates"][on[-1]],
               color="#f1f1f1", zorder=0, lw=0)
    lo, hi = ax.get_ylim()
    ax.text(r["dates"][on[len(on)//2]], hi - 0.03*(hi-lo),
            "daylight saving in effect", ha="center", va="top",
            fontsize=8, color="#666666")

# ---------------------------------------------------------------- per-city figures
for code, c in CITIES.items():
    r = data[code]
    fig, axes = plt.subplots(2, 1, figsize=(9, 7.2), sharex=True,
                             gridspec_kw=dict(height_ratios=[2,1], hspace=0.12))
    ax, ax2 = axes

    ax.plot(r["dates"], r["set_civ"], color=COLORS[code], lw=1.6,
            label="Sunset, local civil time (clock on the wall)")
    ax.plot(r["dates"], r["set_std"], color=COLORS[code], lw=1.0, ls="--",
            label="Sunset, local standard time (DST ignored)")
    ax.plot(r["dates"], r["set_lmt"], color="#888888", lw=0.9, ls=":",
            label="Sunset, local mean solar time")
    ax.fill_between(r["dates"], r["rise_civ"], r["set_civ"],
                    color=COLORS[code], alpha=0.06, lw=0)
    ax.plot(r["dates"], r["rise_civ"], color=COLORS[code], lw=0.8, alpha=0.45,
            label="Sunrise, local civil time")

    ax.set_ylim(min(r["rise_civ"])-40, max(r["set_civ"])+75)
    clock_axis(ax, 60)
    ax.grid(True, axis="y", alpha=0.6)
    ax.set_ylabel("Time of day")
    ax.set_title(f"{c['name']} ({code})  $\\cdot$  {c['lat']:.2f}$^\\circ$N, "
                 f"{abs(c['lon']):.2f}$^\\circ$"
                 f"{'E' if c['lon']>0 else 'W'}  $\\cdot$  daylight through {YEAR}")
    shade_dst(ax, code)
    ax.legend(loc="center", ncol=2, fontsize=8.5)

    for kd, lab in zip(KEY, ["4 Jun", "8 Nov"]):
        i = r["dates"].index(kd)
        ax.plot([kd],[r["set_civ"][i]], marker="o", ms=4, color="black", zorder=5)
        ax.annotate(f"{lab}\n{hhmm(r['set_civ'][i])}", (kd, r["set_civ"][i]),
                    textcoords="offset points", xytext=(0,9),
                    ha="center", fontsize=8)

    ax2.plot(r["dates"], r["daylight"], color=COLORS[code], lw=1.4)
    ax2.set_ylabel("Daylight (hours)")
    ax2.grid(True, alpha=0.6)
    ax2.yaxis.set_major_locator(MultipleLocator(1))
    month_axis(ax2)
    ax2.set_xlabel(f"Date, {YEAR}")

    check_figure(fig)
    fig.savefig(f"{OUT}/fig_{code}.png", dpi=200, bbox_inches="tight")
    plt.close(fig)

# ---------------------------------------------------------------- combined: civil
fig, ax = plt.subplots(figsize=(10, 6))
for code, c in CITIES.items():
    r = data[code]
    ax.plot(r["dates"], r["set_civ"], color=COLORS[code], lw=1.6,
            label=f"{c['name']} ({code})")
for kd in KEY:
    ax.axvline(kd, color="#999999", lw=0.7, ls=":")
ax.annotate("4 Jun", (KEY[0], 1300), rotation=90, fontsize=8, color="#666666",
            ha="right", va="top")
ax.annotate("8 Nov", (KEY[1], 1300), rotation=90, fontsize=8, color="#666666",
            ha="right", va="top")
clock_axis(ax, 30)
month_axis(ax)
ax.grid(True, alpha=0.6)
ax.set_ylabel("Sunset, local civil time")
ax.set_xlabel(f"Date, {YEAR}")
ax.set_title(f"Sunset by local civil clock, {YEAR}  $\\cdot$  DST discontinuities included")
ax.legend(loc="upper left", fontsize=9)
check_figure(fig)
fig.savefig(f"{OUT}/fig_combined_civil.png", dpi=200, bbox_inches="tight")
plt.close(fig)

# ---------------------------------------------------------------- combined: standard
fig, ax = plt.subplots(figsize=(10, 6))
for code, c in CITIES.items():
    r = data[code]
    ax.plot(r["dates"], r["set_std"], color=COLORS[code], lw=1.6,
            label=f"{c['name']} ({code})")
clock_axis(ax, 30)
month_axis(ax)
ax.grid(True, alpha=0.6)
ax.set_ylabel("Sunset, local standard time")
ax.set_xlabel(f"Date, {YEAR}")
ax.set_title(f"Sunset with DST removed, {YEAR}  $\\cdot$  pure astronomy, no clock policy")
ax.legend(loc="upper left", fontsize=9)
check_figure(fig)
fig.savefig(f"{OUT}/fig_combined_standard.png", dpi=200, bbox_inches="tight")
plt.close(fig)

# ---------------------------------------------------------------- combined: daylight
fig, ax = plt.subplots(figsize=(10, 6))
for code, c in CITIES.items():
    r = data[code]
    ax.plot(r["dates"], r["daylight"], color=COLORS[code], lw=1.6,
            label=f"{c['name']} ({code}), {c['lat']:.1f}$^\\circ$N")
ax.axhline(12, color="#999999", lw=0.7, ls=":")
ax.annotate("12 h", (dt.date(YEAR,1,10), 12.05), fontsize=8, color="#666666")
month_axis(ax)
ax.yaxis.set_major_locator(MultipleLocator(1))
ax.grid(True, alpha=0.6)
ax.set_ylabel("Daylight (hours)")
ax.set_xlabel(f"Date, {YEAR}")
ax.set_title(f"Length of day, {YEAR}  $\\cdot$  amplitude scales with latitude")
ax.legend(loc="upper left", fontsize=9)
check_figure(fig)
fig.savefig(f"{OUT}/fig_combined_daylight.png", dpi=200, bbox_inches="tight")
plt.close(fig)

# ---------------------------------------------------------------- console
print(f"{'city':<10}{'date':<13}{'UTC':<8}{'std':<8}{'civil':<8}{'LMT':<8}{'DST':<6}{'daylight'}")
for row in rows:
    print(f"{row[1]:<10}{row[2]:<13}{row[3]:<8}{row[4]:<8}{row[5]:<8}{row[6]:<8}{row[7]:<6}{row[8]}")
print()
for s in summary:
    print(f"{s['name']:<10} civil: latest {hhmm(s['civ_late'][1])} on {s['civ_late'][0]:%d %b}, "
          f"earliest {hhmm(s['civ_early'][1])} on {s['civ_early'][0]:%d %b}, "
          f"swing {s['civ_amp']:.2f} h | std swing {s['std_amp']:.2f} h | "
          f"daylight {s['dl_min']:.2f}-{s['dl_max']:.2f} h (Δ{s['dl_amp']:.2f})")
