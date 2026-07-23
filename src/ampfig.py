import os, math, numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
OUT = os.environ.get("SOLAR_OUT", "/mnt/user-data/outputs")
from solar import CITIES
from amp import amp_theory, amp_clean, rows
from glyphcheck import check_figure

plt.rcParams.update({
    "font.family":"serif","font.serif":["cmr10","DejaVu Serif"],
    "mathtext.fontset":"cm","axes.formatter.use_mathtext":True,
    "axes.unicode_minus":False,"figure.facecolor":"white","axes.facecolor":"white",
    "savefig.facecolor":"white","axes.edgecolor":"#333333","axes.linewidth":0.8,
    "grid.color":"#cccccc","grid.linewidth":0.5,"font.size":10,
    "axes.titlesize":12,"legend.frameon":False,
})
COL={"NYC":"#1b3a6b","DEL":"#a03020","CCU":"#2e6b3a","BOM":"#7a4b8f","SEA":"#b5852a"}

lat=np.array([r[2] for r in rows]); A=np.array([r[3] for r in rows])
b,a0=np.polyfit(lat,A,1)
grid=np.linspace(0,66.4,600)
truth=np.array([amp_theory(L) for L in grid])

fig,axes=plt.subplots(2,1,figsize=(9,7.6),sharex=True,
                      gridspec_kw=dict(height_ratios=[2.4,1],hspace=0.10))
ax,ax2=axes

ax.plot(grid,truth,color="#333333",lw=1.4,
        label=r"exact: $A=\frac{4}{15}\arcsin(\tan\phi\,\tan\varepsilon)$")
ax.plot(grid,b*grid+a0,color="#999999",lw=1.1,ls="--",
        label=f"OLS line through the 5 cities ($r^2$ = 0.9907)")
for r in rows:
    ax.plot([r[2]],[r[3]],"o",ms=6,color=COL[r[0]],zorder=5)
    ax.annotate(f"{r[0]}", (r[2],r[3]), textcoords="offset points",
                xytext=(7,-3), fontsize=9, color=COL[r[0]])
ax.axvline(66.56,color="#bbbbbb",lw=0.7,ls=":")
ax.annotate("Arctic Circle\n$A\\to 24$ h",(66.0,17),ha="right",fontsize=8,color="#666666")
ax.axvspan(19.0,47.7,color="#f3f3f3",zorder=0,lw=0)
ax.annotate("range spanned by your 5 cities",(33,0.6),ha="center",fontsize=8,color="#666666")
ax.set_ylim(0,24)
ax.yaxis.set_major_locator(MultipleLocator(3))
ax.grid(True,alpha=0.6)
ax.set_ylabel("Daylight amplitude, $A$ (hours)")
ax.set_title("Annual daylight swing against latitude, 2026")
ax.legend(loc="upper left",fontsize=9)

resid=A-(b*lat+a0)
ax2.axhline(0,color="#999999",lw=0.7)
ax2.plot(grid,truth-(b*grid+a0),color="#333333",lw=1.0,alpha=0.5)
for i,r in enumerate(rows):
    ax2.plot([r[2]],[resid[i]],"o",ms=6,color=COL[r[0]],zorder=5)
    ax2.vlines(r[2],0,resid[i],color=COL[r[0]],lw=1.0)
ax2.set_ylim(-3,1.5)
ax2.grid(True,alpha=0.6)
ax2.set_ylabel("Residual (h)")
ax2.set_xlabel("Latitude ($^\\circ$N)")
ax2.set_xlim(0,70)
ax2.xaxis.set_major_locator(MultipleLocator(10))
ax2.annotate("linear fit residuals: $+\\;+\\;-\\;-\\;+$  (convexity, not noise)",
             (2,-2.6),fontsize=8.5,color="#444444")

check_figure(fig)
fig.savefig(f"{OUT}/fig_amplitude_vs_latitude.png",dpi=200,bbox_inches="tight")
print("ok")
