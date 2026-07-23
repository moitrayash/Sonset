"""Regression test for figure-text glyph integrity. Plain python3, no framework.

    python3 src/test_glyphs.py     (from anywhere; exit 0 pass, nonzero fail)

Runs the actual figure scripts (analyze.py, ampfig.py, daily_figs.py for one
city, ampfig_g20.py) into a temporary directory with Figure.savefig
monkeypatched to first walk every Text object through glyphcheck.check_figure.
Two independent detections, because the two failure modes differ:

  1. recorded warnings containing "missing from font"  (catches U+00B7 tofu)
  2. per-character charmap + OT1-reliability walk       (catches U+00B0, which
     IS in cmr10's cmap, mapped to the wrong glyph, and never warns; membership
     alone cannot catch it, so glyphcheck also rejects any codepoint above
     ASCII in TeX cm* fonts)
"""

import os, sys, runpy, warnings, tempfile, traceback

SRC = os.path.dirname(os.path.abspath(__file__))
os.chdir(SRC)
sys.path.insert(0, SRC)

import matplotlib
matplotlib.use("Agg")
from matplotlib.figure import Figure
from glyphcheck import check_figure

failures = []
_real_savefig = Figure.savefig


def guarded_savefig(self, *a, **k):
    try:
        check_figure(self)
    except RuntimeError as e:
        failures.append(f"charmap: {e}")
    return _real_savefig(self, *a, **k)


SCRIPTS = [
    ("analyze.py", {}),
    ("ampfig.py", {}),
    ("daily_figs.py", {"SOLAR_CODES": "JFK", "SOLAR_SKIP_CSV": "1"}),
    ("ampfig_g20.py", {}),
]

Figure.savefig = guarded_savefig
try:
    for script, extra_env in SCRIPTS:
        if not os.path.exists(script):
            continue                      # ampfig_g20 may not exist yet
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["SOLAR_OUT"] = tmp
            saved = {k: os.environ.get(k) for k in extra_env}
            os.environ.update(extra_env)
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                try:
                    runpy.run_path(script, run_name="__main__")
                except SystemExit:
                    pass
                except Exception:
                    failures.append(f"{script} crashed:\n{traceback.format_exc()}")
            for w in caught:
                if "missing from font" in str(w.message):
                    failures.append(f"warning in {script}: {w.message}")
            for k, v in saved.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
        print(f"ran {script}")
finally:
    Figure.savefig = _real_savefig

if failures:
    print(f"\nFAIL, {len(failures)} problem(s):")
    seen = set()
    for f in failures:
        if f not in seen:
            print(" -", f)
            seen.add(f)
    raise SystemExit(1)
print("\nPASS: every figure character has a real glyph in its resolved font")
