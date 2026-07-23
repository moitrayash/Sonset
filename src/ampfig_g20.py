"""Amplitude vs latitude, refitted on the 25-location set.

README section 5 anticipated this: with more cities, regress on tan(phi)
rather than raw latitude, or use the closed form outright. Both are shown.
Amplitudes are measured from the computed daily series (max minus min
daylight), not from the closed form, so the exact curve is a check, not an
input. Southern-hemisphere locations enter at |phi| (open markers).

  SOLAR_OUT=/some/dir python3 ampfig_g20.py
"""

import os, math, numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator

from locations_g20 import LOCATIONS, ORDER
from daily import compute_all
from glyphcheck import check_figure

OUT = os.environ.get("SOLAR_OUT", "/mnt/user-data/outputs")
EPS = 23.44

plt.rcParams.update({
    "font.family": "serif", "font.serif": ["cmr10", "DejaVu Serif"],
    "mathtext.fontset": "cm", "axes.formatter.use_mathtext": True,
    "axes.unicode_minus": False, "figure.facecolor": "white",
    "axes.facecolor": "white", "savefig.facecolor": "white",
    "axes.edgecolor": "#333333", "axes.linewidth": 0.8,
    "grid.color": "#cccccc", "grid.linewidth": 0.5, "font.size": 10,
    "axes.titlesize": 12, "legend.frameon": False,
})
INK = "#1b3a6b"


# the closed form, stated plainly: A hours = (4/15) * arcsin_deg(tan phi tan eps)
def A_exact(phi_deg):
    return (4.0 / 15.0) * math.degrees(
        math.asin(math.tan(math.radians(phi_deg)) * math.tan(math.radians(EPS))))


def main():
    data = compute_all()
    lat_abs, amp, south, codes = [], [], [], []
    for code in ORDER:
        r = data[code]
        lat_abs.append(abs(LOCATIONS[code]["lat"]))
        amp.append(max(r["daylight"]) - min(r["daylight"]))
        south.append(LOCATIONS[code]["lat"] < 0)
        codes.append(code)
    lat_abs, amp = np.array(lat_abs), np.array(amp)
    tphi = np.tan(np.radians(lat_abs))

    b, a0 = np.polyfit(tphi, amp, 1)
    pred = b * tphi + a0
    r2 = 1 - np.sum((amp - pred) ** 2) / np.sum((amp - amp.mean()) ** 2)

    grid = np.linspace(0.0, 66.4, 600)
    exact = np.array([A_exact(g) for g in grid])
    fitcrv = b * np.tan(np.radians(grid)) + a0

    fig, axes = plt.subplots(2, 1, figsize=(9, 7.6), sharex=True,
                             gridspec_kw=dict(height_ratios=[2.4, 1], hspace=0.10))
    ax, ax2 = axes

    ax.plot(grid, exact, color="#333333", lw=1.4,
            label=r"exact: $A=\frac{4}{15}\arcsin(\tan\phi\,\tan\varepsilon)$")
    ax.plot(grid, fitcrv, color="#999999", lw=1.1, ls="--",
            label=f"OLS on $\\tan\\phi$, {len(codes)} locations ($r^2$ = {r2:.4f}, "
                  f"intercept {a0:+.2f} h)")
    # explicit label dodges for near-equal |phi| pairs
    place = {"BOM": (-6, 5, "right"), "MEX": (5, -9, "left"),
             "RUH": (5, -9, "left"), "PRY": (-6, 5, "right"),
             "CBR": (5, -9, "left"), "EZE": (-6, 5, "right"),
             "ICN": (5, -9, "left"), "PEK": (-6, -9, "right"),
             "ESB": (-6, 5, "right"), "MIA": (5, -9, "left"),
             "AUS": (-6, -9, "right"), "NQZ": (5, -9, "left"),
             "CCU": (5, -9, "left"), "CGK": (-6, 5, "right"),
             "LHR": (-6, 5, "right"), "SEA": (-6, 5, "right"),
             "YUL": (5, -9, "left"), "LAX": (-6, -9, "right"),
             "GZA": (5, -9, "left"), "ACC": (5, -9, "left"),
             "SFO": (-6, 5, "right"), "SZX": (-6, 5, "right"),
             "TAS": (5, -9, "left"), "VVO": (5, -9, "left"),
             "PER": (-6, 5, "right"), "MNL": (5, -9, "left")}
    for i, code in enumerate(codes):
        mfc = "white" if south[i] else INK
        ax.plot([lat_abs[i]], [amp[i]], "o", ms=5, mfc=mfc, mec=INK,
                mew=1.0, zorder=5)
        dx, dy, ha = place.get(code, (5, 4, "left"))
        ax.annotate(code, (lat_abs[i], amp[i]), textcoords="offset points",
                    xytext=(dx, dy), ha=ha, fontsize=6.5, color="#444444")
    ax.plot([], [], "o", ms=5, mfc=INK, mec=INK, label="northern hemisphere")
    ax.plot([], [], "o", ms=5, mfc="white", mec=INK,
            label="southern hemisphere, at $|\\phi|$")
    ax.axvline(66.56, color="#bbbbbb", lw=0.7, ls=":")
    ax.annotate("Arctic Circle\n$A\\to 24$ h", (66.0, 15.5), ha="right",
                fontsize=8, color="#666666")
    ax.set_ylim(0, 18)
    ax.yaxis.set_major_locator(MultipleLocator(3))
    ax.grid(True, alpha=0.6)
    ax.set_ylabel("Daylight amplitude, $A$ (hours)")
    ax.set_title(f"Annual daylight swing against latitude, {len(codes)} locations, 2026")
    ax.legend(loc="upper left", fontsize=8.5)

    resid = amp - pred
    ax2.axhline(0, color="#999999", lw=0.7)
    for i in range(len(codes)):
        mfc = "white" if south[i] else INK
        ax2.plot([lat_abs[i]], [resid[i]], "o", ms=5, mfc=mfc, mec=INK, mew=1.0,
                 zorder=5)
        ax2.vlines(lat_abs[i], 0, resid[i], color=INK, lw=0.9, alpha=0.7)
    ax2.set_ylim(-0.32, 0.32)
    ax2.grid(True, alpha=0.6)
    ax2.set_ylabel("Residual (h)")
    ax2.set_xlabel("Latitude ($^\\circ$, absolute value)")
    ax2.set_xlim(0, 70)
    ax2.xaxis.set_major_locator(MultipleLocator(10))
    ax2.annotate("residuals of the $\\tan\\phi$ fit; compare the $-$1.36 h "
                 "equator intercept of the old raw-latitude line",
                 (2, -0.21), fontsize=8.5, color="#444444")

    check_figure(fig)
    fig.savefig(f"{OUT}/fig_amplitude_vs_latitude_g20.png", dpi=200,
                bbox_inches="tight")
    print(f"fit on tan(phi): A = {a0:+.3f} + {b:.3f} tan(phi) h, r2 = {r2:.5f}")


if __name__ == "__main__":
    main()
