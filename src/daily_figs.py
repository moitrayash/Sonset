"""Daily almanac, static outputs: one CSV, one summary, 25 band figures.

Per-city figure: four columns sharing the date axis (1 Jan at top, matching
the phone app's list order), clock time of day on x. The filled band runs
sunrise to sunset; the pale fringe extends to civil twilight. Columns are the
four clock conventions from daily.py. DST cuts show as steps in the band and
are marked with dashed rules.

Figures are the daily, per-location translation of the iOS Weather "Sunrise
and Sunset Averages" list: 365 rows instead of 12, drawn as a band because a
one-day-per-text-row list belongs in the HTML almanac, not a PNG.

Usage:
  SOLAR_OUT=/some/dir python3 daily_figs.py            # CSV + summary + all figs
  SOLAR_OUT=/some/dir SOLAR_CODES=NYC,PAR python3 daily_figs.py   # subset figs
  SOLAR_OUT=/some/dir SOLAR_SKIP_CSV=1 python3 daily_figs.py      # figs only
"""

import os, csv, datetime as dt
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter, MultipleLocator

from locations_g20 import LOCATIONS, ORDER
from daily import YEAR, SPA_CUT, DAYS, compute_all, hhmm
from glyphcheck import check_figure

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

INK = "#1b3a6b"          # one sober ink for all cities; colour was only ever
CUT = "#a03020"          # needed to separate overlaid lines in combined figs
GREY = "#666666"

VAR_TITLES = [
    ("off_std",  "standard time",  "DST ignored"),
    ("off_civ",  "civil clock",    "as lived"),
    ("off_spaA", "SPA, as-lived",  "no 1 Nov fall-back"),
    ("off_spaS", "SPA, steady",    "permanent DST"),
]


def fmt_clock(x, pos=None):
    return hhmm(x)


def moves_in(offsets):
    return [(DAYS[i], (offsets[i] - offsets[i - 1]) / 60.0)
            for i in range(1, len(DAYS)) if offsets[i] != offsets[i - 1]]


def coord_label(c):
    ns = "N" if c["lat"] >= 0 else "S"
    ew = "E" if c["lon"] > 0 else "W"
    return (f"{abs(c['lat']):.2f}$^\\circ${ns}, "
            f"{abs(c['lon']):.2f}$^\\circ${ew}")


def render_city(code, r):
    c = LOCATIONS[code]
    fig, axes = plt.subplots(1, 4, figsize=(12.8, 8.4), sharey=True)
    fig.subplots_adjust(left=0.065, right=0.985, top=0.885, bottom=0.075,
                        wspace=0.10)

    for k, (offkey, t1, t2) in enumerate(VAR_TITLES):
        ax = axes[k]
        off = r[offkey]
        dawn = [r["dawn_utc"][i] + off[i] for i in range(len(DAYS))]
        rise = [r["rise_utc"][i] + off[i] for i in range(len(DAYS))]
        sets = [r["set_utc"][i] + off[i] for i in range(len(DAYS))]
        dusk = [r["dusk_utc"][i] + off[i] for i in range(len(DAYS))]

        ax.fill_betweenx(DAYS, dawn, rise, color=INK, alpha=0.13, lw=0)
        ax.fill_betweenx(DAYS, rise, sets, color=INK, alpha=0.42, lw=0)
        ax.fill_betweenx(DAYS, sets, dusk, color=INK, alpha=0.13, lw=0)

        subtitle = t2
        if k >= 2 and not c["us"]:
            subtitle = "(unchanged)"
        ax.set_title(f"{t1}\n{subtitle}", fontsize=9.5,
                     color="#222222" if not (k >= 2 and not c["us"]) else GREY)

        for d, jump in moves_in(off):
            ax.axhline(d, color=CUT, lw=0.7, ls="--", zorder=4)
            ax.text(15, mdates.date2num(d) - 2.2, f"{d:%-d %b} {jump:+.0f} h",
                    fontsize=6.5, color=CUT, ha="left", va="bottom")
        if offkey == "off_spaA" and c["us"]:
            ax.axhline(SPA_CUT, color=GREY, lw=0.7, ls=":", zorder=4)
            ax.text(15, mdates.date2num(SPA_CUT) + 3.5,
                    f"{SPA_CUT:%-d %b} fall-back\ncancelled",
                    fontsize=6.5, color=GREY, ha="left", va="top")
        if offkey == "off_spaS" and c["us"]:
            ax.text(15, mdates.date2num(dt.date(YEAR, 11, 1)) + 3.5,
                    "no transitions\nall year", fontsize=6.5, color=GREY,
                    ha="left", va="top")

        if offkey == "off_civ":
            # monthly anchor times, the surviving skeleton of the app's list
            for mth in range(1, 13):
                d15 = dt.date(YEAR, mth, 15)
                i = DAYS.index(d15)
                ax.text(rise[i] - 18, d15, hhmm(rise[i]), fontsize=6,
                        color="#555555", ha="right", va="center")
                ax.text(sets[i] + 18, d15, hhmm(sets[i]), fontsize=6,
                        color="#555555", ha="left", va="center")
            i_late = sets.index(max(sets))
            i_early = sets.index(min(sets))
            for i, lab in ((i_late, "latest"), (i_early, "earliest")):
                ax.plot([sets[i]], [DAYS[i]], marker="o", ms=3, color="black",
                        zorder=5)
                ax.text(sets[i] - 16, mdates.date2num(DAYS[i]),
                        f"{lab} sunset {hhmm(sets[i])}, {DAYS[i]:%-d %b}",
                        fontsize=6.5, ha="right", va="center", color="#111111",
                        zorder=6)

        ax.set_xlim(0, 1440)
        ticks = [0, 360, 720, 1080] + ([1440] if k == 3 else [])
        ax.set_xticks(ticks)
        ax.xaxis.set_minor_locator(MultipleLocator(120))
        ax.xaxis.set_major_formatter(
            FuncFormatter(lambda x, pos: "24:00" if x >= 1440 else hhmm(x)))
        ax.tick_params(axis="x", labelsize=7.5)
        ax.grid(True, axis="x", alpha=0.55)
        ax.grid(True, axis="y", alpha=0.35)

    ax0 = axes[0]
    ax0.set_ylim(DAYS[-1], DAYS[0])                 # 1 Jan at top, app order
    ax0.yaxis.set_major_locator(mdates.MonthLocator())
    ax0.yaxis.set_major_formatter(mdates.DateFormatter("%b"))
    for ax in axes:
        ax.tick_params(axis="y", length=3)

    fig.suptitle(f"{c['name']} ({code}) $\\cdot$ {coord_label(c)} $\\cdot$ "
                 f"daily sunrise to sunset, {YEAR}", fontsize=12.5, y=0.975)

    foot = ("Band: sunrise to sunset. Fringe: civil twilight (sun within "
            "6$^\\circ$ below horizon). SPA columns assume the Sunshine "
            "Protection Act (House 308-117, 14 Jul 2026) is enacted before "
            "1 Nov 2026, no state opt-outs.")
    if not c["us"]:
        foot += " The bill moves no clock here; those columns repeat the civil clock."
    fig.text(0.5, 0.012, foot, ha="center", fontsize=7, color=GREY)

    check_figure(fig)
    fig.savefig(f"{OUT}/fig_daily_{code}.png", dpi=200)
    plt.close(fig)


def write_csv(data):
    with open(f"{OUT}/daily_{YEAR}_g20.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", "city_code", "city", "lat", "lon", "tz",
                    "dst_in_effect",
                    "first_light_utc", "sunrise_utc", "sunset_utc", "last_light_utc",
                    "sunrise_std", "sunset_std",
                    "sunrise_civil", "sunset_civil",
                    "sunset_mean_solar",
                    "sunrise_spa_aslived", "sunset_spa_aslived",
                    "sunrise_spa_steady", "sunset_spa_steady",
                    "first_light_civil", "last_light_civil",
                    "daylight_hours"])
        for code in ORDER:
            c, r = LOCATIONS[code], data[code]
            lmt = c["lon"] / 15.0 * 60.0
            for i, d in enumerate(DAYS):
                def L(ev, offkey):
                    return hhmm(r[ev][i] + r[offkey][i])
                w.writerow([
                    d, code, c["name"], c["lat"], c["lon"], c["tz"],
                    int(r["dst"][i]),
                    hhmm(r["dawn_utc"][i]), hhmm(r["rise_utc"][i]),
                    hhmm(r["set_utc"][i]), hhmm(r["dusk_utc"][i]),
                    L("rise_utc", "off_std"), L("set_utc", "off_std"),
                    L("rise_utc", "off_civ"), L("set_utc", "off_civ"),
                    hhmm(r["set_utc"][i] + lmt),
                    L("rise_utc", "off_spaA"), L("set_utc", "off_spaA"),
                    L("rise_utc", "off_spaS"), L("set_utc", "off_spaS"),
                    L("dawn_utc", "off_civ"), L("dusk_utc", "off_civ"),
                    round(r["daylight"][i], 4)])


def write_summary(data):
    with open(f"{OUT}/summary_extremes_g20.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["code", "city", "lat", "lon",
                    "latest_sunset_civil_date", "latest_sunset_civil",
                    "earliest_sunset_civil_date", "earliest_sunset_civil",
                    "civil_swing_hours", "standard_swing_hours",
                    "spa_aslived_swing_hours",
                    "longest_day_h", "shortest_day_h", "daylight_swing_h"])
        for code in ORDER:
            c, r = LOCATIONS[code], data[code]
            civ = [r["set_utc"][i] + r["off_civ"][i] for i in range(len(DAYS))]
            std = [r["set_utc"][i] + r["off_std"][i] for i in range(len(DAYS))]
            spa = [r["set_utc"][i] + r["off_spaA"][i] for i in range(len(DAYS))]
            il, ie = civ.index(max(civ)), civ.index(min(civ))
            w.writerow([code, c["name"], c["lat"], c["lon"],
                        DAYS[il], hhmm(civ[il]), DAYS[ie], hhmm(civ[ie]),
                        round((max(civ) - min(civ)) / 60.0, 2),
                        round((max(std) - min(std)) / 60.0, 2),
                        round((max(spa) - min(spa)) / 60.0, 2),
                        round(max(r["daylight"]), 2),
                        round(min(r["daylight"]), 2),
                        round(max(r["daylight"]) - min(r["daylight"]), 2)])


if __name__ == "__main__":
    data = compute_all()
    if not os.environ.get("SOLAR_SKIP_CSV"):
        write_csv(data)
        write_summary(data)
        print(f"wrote daily_{YEAR}_g20.csv ({len(ORDER) * len(DAYS)} rows) "
              f"and summary_extremes_g20.csv")
    codes = os.environ.get("SOLAR_CODES")
    codes = codes.split(",") if codes else ORDER
    for code in codes:
        render_city(code, data[code])
        print(f"fig_daily_{code}.png", flush=True)
