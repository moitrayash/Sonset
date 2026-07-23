"""Charmap guard for figure text, per prompts/fix_figure_glyphs.md.

cmr10 fails on some Unicode two ways: missing glyph with a warning (U+00B7)
and wrong glyph with no warning at all (U+00B0). Warnings alone are therefore
not a sufficient check. This walks every Text object in a figure and verifies
each character outside $...$ math segments against the resolved font's actual
charmap. Figure scripts call check_figure(fig) immediately before savefig.
"""

import os
import matplotlib.text
from matplotlib import font_manager
from matplotlib.ft2font import FT2Font

_font_cache = {}
_WHITESPACE = set(" \n\t")   # laid out by the engine, not drawn as glyphs

# Empirical finding, 22 Jul 2026: cmr10.ttf's cmap DOES contain U+00B0, mapped
# to glyph 52 (the wrong mark). Charmap membership alone therefore cannot catch
# the degree-sign defect described in prompts/fix_figure_glyphs.md. For the TeX
# cm* fonts the cmap above ASCII is legacy-encoded and untrustworthy, so any
# codepoint > 0x7E is rejected outright. A few ASCII slots are also re-encoded
# in OT1 text fonts (e.g. '<' draws an inverted exclamation mark); those are
# denylisted too.
_OT1_ASCII_TRAPS = set("<>\\{}|_^~\"")


def _is_tex_cm(fname):
    return os.path.basename(fname).startswith("cm")


def _charmap(prop):
    fname = font_manager.findfont(prop)
    if fname not in _font_cache:
        _font_cache[fname] = (set(FT2Font(fname).get_charmap().keys()), fname)
    return _font_cache[fname]


def check_figure(fig):
    """Raise RuntimeError if any non-math character lacks a real glyph."""
    for t in fig.findobj(matplotlib.text.Text):
        s = t.get_text()
        if not s:
            continue
        non_math = "".join(s.split("$")[0::2])   # even segments are outside $...$
        if not non_math:
            continue
        charmap, fname = _charmap(t.get_fontproperties())
        tex_cm = _is_tex_cm(fname)
        for ch in non_math:
            if ch in _WHITESPACE:
                continue
            if ord(ch) not in charmap:
                raise RuntimeError(
                    f"glyph U+{ord(ch):04X} ({ch!r}) not in {fname} "
                    f"for text {s!r}")
            if tex_cm and (ord(ch) > 0x7E or ch in _OT1_ASCII_TRAPS):
                raise RuntimeError(
                    f"U+{ord(ch):04X} ({ch!r}) is unreliable in OT1-encoded "
                    f"{os.path.basename(fname)} (mapped, but possibly to the "
                    f"wrong glyph) for text {s!r}; route it through mathtext")


if __name__ == "__main__":
    # demonstrate both directions on cmr10
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family": "serif", "font.serif": ["cmr10"]})
    fig = plt.figure()
    fig.text(0.5, 0.5, "clean ascii $\\cdot$ $^\\circ$ text")
    check_figure(fig)
    print("clean text passes")
    for bad in ("bad · dot", "bad 40.7° degree"):
        fig2 = plt.figure()
        fig2.text(0.5, 0.3, bad)
        try:
            check_figure(fig2)
            print(f"ERROR: defect not caught in {bad!r}")
            raise SystemExit(1)
        except RuntimeError as e:
            print(f"defect caught: {e}")
