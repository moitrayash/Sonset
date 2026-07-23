# Task: fix broken glyphs in all figures, then make it impossible to regress

Project: `Sunset Time Analysis` (solar sunset 2026 package). Read `README.md` first,
especially sections 7 and 8. Verify `MANIFEST.txt` before trusting any file.

## The defect

Figure text is set in `cmr10`, a TeX font with OT1 encoding, but the scripts pass it
raw Unicode it cannot represent. Two distinct failure modes, and only one of them warns:

1. **U+00B7 MIDDLE DOT (`·`)** has no glyph in `cmr10`. Matplotlib emits
   `UserWarning: Glyph 183 missing from font(s) cmr10` and draws a tofu box.
   Present in every title built in `src/analyze.py` (the per-city title around line
   177 and the three combined-figure titles around lines 216, 232, 250).
2. **U+00B0 DEGREE SIGN (`°`)** maps to the *wrong glyph* in `cmr10` (it renders as
   an fl-ligature-like mark) and emits **no warning at all**. Present in the per-city
   titles (`°N`, `°E/W`), the daylight-figure legend labels (`°N`) in `analyze.py`,
   and the x-axis label `Latitude (°N)` in `src/ampfig.py` around line 56.

Confirmed by rendering `outputs/fig_NYC.png`: the title reads
`New York City (NYC) ☐ 40.71flN, 74.01flW ☐ daylight through 2026`.
This defect exists in the originally shipped figures too (byte sizes match the
original manifest), so it is inherited, not a regression from regeneration.

## The fix

Route the offending characters through mathtext, which uses the `cm` fontset and
renders both correctly: replace `·` with `$\cdot$` and `°` with `$^\circ$` in every
affected string. Do not switch fonts, do not add a Unicode fallback font, do not
change any other aspect of the figures. The house style (white background, Computer
Modern, sober) stays exactly as it is.

## The regression test

Create `src/test_glyphs.py`. It must catch **both** failure modes, because warnings
alone miss the degree-sign case:

1. Run both figure scripts into a temporary directory with
   `warnings.catch_warnings(record=True)` and fail if any warning message contains
   `missing from font`.
2. Before each `savefig`, walk every text object in the figure
   (`fig.findobj(matplotlib.text.Text)`) and, for each one, check every character
   outside `$...$` math segments against the resolved font's actual charmap (load
   the font file via `matplotlib.font_manager.findfont` + `matplotlib.ft2font.FT2Font`
   and test `ord(ch) in font.get_charmap()`). Fail on any character the font cannot
   represent. This is the check that catches `°`, which renders without warning.

   The cleanest hook is a small helper the figure scripts call before saving, or a
   test that imports and re-runs them with a monkeypatched `savefig`. Your choice,
   but the test must exercise the *actual* figure scripts, not a copy of their strings.

The test must run with plain `python3 src/test_glyphs.py` (exit 0 pass, nonzero fail)
so it needs no test framework. Document the invocation in README section 3.

## Acceptance criteria, all mandatory

- `python3 src/test_glyphs.py` fails on the current code, passes after the fix.
  Demonstrate both states; a test never seen failing proves nothing.
- All 9 PNGs regenerated. Visually inspect at least `fig_NYC.png` and
  `fig_amplitude_vs_latitude.png` (Read the files, look at the titles and axis
  labels) and confirm no tofu and a correct degree sign.
- The three CSVs remain **byte-identical** (compare sha256 before and after). This
  fix touches text rendering only; if a CSV hash moves, you broke something else.
- Regenerate `MANIFEST.txt` in the existing format, including the new test file.
- Add one line to README section 6 noting the glyph fix and the test.

## Conventions (README section 7, binding)

Standard capitalisation. No em dashes except parenthetically. Any response with
caveats ends with a `## Notes` header and bullets. Do not fabricate anything. Ask
for every permission you might plausibly need at the very start.
