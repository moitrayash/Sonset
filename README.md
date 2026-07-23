# Solar Position and Sunset Analysis, 2026

Handoff package. Prepared by Claude (Opus 4.8) for the operator, Yash Moitra.
Prepared 9 July 2026. Intended reader: whichever Claude instance picks this up next.

---

## 1. What this is

Sunrise, sunset, and daylight duration for five cities across every day of calendar
year 2026, computed from first principles. No external data source, no API, no
almanac lookup. The only inputs are latitude, longitude, and the date.

Cities, by IATA-ish shorthand the operator uses:

| Code | City | Lat | Lon | Zone | DST |
|------|------|-----|-----|------|-----|
| NYC | New York City | 40.7128 N | 74.0060 W | America/New_York | yes |
| DEL | Delhi | 28.6139 N | 77.2090 E | Asia/Kolkata | no |
| CCU | Kolkata | 22.5726 N | 88.3639 E | Asia/Kolkata | no |
| BOM | Mumbai | 19.0760 N | 72.8777 E | Asia/Kolkata | no |
| SEA | Seattle | 47.6062 N | 122.3321 W | America/Los_Angeles | yes |

These are city centres, not airport reference points. The operator is an aviation
person and uses airport codes as city shorthand; do not assume the coordinates are
aerodrome coordinates. Substituting VIDP for central Delhi moves sunset by roughly
20 seconds.

## 2. Layout

```
Sunset Time Analysis/   (package: claude-opus-4.8_solar-sunset-2026)
  README.md            this file
  MANIFEST.txt         sha256 + size for every file
  src/
    solar.py           NOAA solar position engine. No dependencies beyond stdlib.
    analyze.py         full-year run, CSV export, per-city + combined figures
    amp.py             daylight-amplitude vs latitude correlation analysis
    ampfig.py          renders the amplitude-vs-latitude figure
    locations_g20.py   25-location set: original five + G20 seats   (22 Jul)
    daily.py           twilight + four clock conventions, self-checks (22 Jul)
    daily_figs.py      daily G20 CSV, summary, 25 band figures      (22 Jul)
    build_almanac.py   single-file HTML almanac                     (22 Jul)
    make_landpath.py   extracts land outline + night lights from the
                       Natural Earth data bundled in geopandas      (22 Jul)
    map_assets.json    the extracted map geometry, checked in so the
                       almanac rebuilds without geopandas           (22 Jul)
    ampfig_g20.py      amplitude refit on tan(phi), 25 points       (22 Jul)
    glyphcheck.py      charmap guard called before every savefig    (22 Jul)
    test_glyphs.py     glyph regression test over the figure scripts (22 Jul)
  prompts/
    fix_figure_glyphs.md         executed 22 Jul 2026, see section 6
    observation_validation.md    queued task: empirical validation, three tiers
  outputs/
    sunset_2026_all_cities.csv     365 rows x 5 cities, every clock convention
    key_dates_jun04_nov08.csv      the two dates the operator asked about
    summary_extremes.csv           per-city latest/earliest sunset, swings
    fig_NYC.png ... fig_SEA.png    per-city: sunrise/sunset band + daylight length
    fig_combined_civil.png         all five, local civil clock, DST cliffs visible
    fig_combined_standard.png      all five, DST stripped out
    fig_combined_daylight.png      all five, day length
    fig_amplitude_vs_latitude.png  amplitude vs latitude, exact curve vs OLS line
    daily_2026_g20.csv             13870 rows: 365 days x 38 locations, all
                                   clocks, civil twilight, both SPA scenarios
    summary_extremes_g20.csv       extremes + swings for all 38         (22 Jul)
    fig_daily_ACC.png ... fig_daily_VVO.png   38 figures, one per location:
                                   daily sunrise-sunset band in four clock
                                   conventions, DST cuts marked         (22 Jul)
    fig_amplitude_vs_latitude_g20.png  25-point refit on tan(phi)       (22 Jul)
    almanac_2026.html              offline single-file almanac: day/night world
                                   map as location picker (terminator drawn at
                                   the selected city's sunset instant, night
                                   side inverted with city lights), clock
                                   variant toggle, day stats + date nav, year
                                   band chart with hover readout, 365-row
                                   daily list                          (22 Jul)
```

## 3. Reproducing

```bash
cd src
SOLAR_OUT=/some/empty/dir python3 analyze.py
SOLAR_OUT=/some/empty/dir python3 ampfig.py

# 22 Jul additions
python3 daily.py                                  # self-checks only, exit 0 on pass
SOLAR_OUT=/some/empty/dir python3 daily_figs.py   # daily CSV + summary + 25 figures
SOLAR_OUT=/some/empty/dir python3 ampfig_g20.py
SOLAR_OUT=/some/empty/dir python3 build_almanac.py
python3 test_glyphs.py                            # glyph regression test, exit 0 on pass
python3 make_landpath.py     # only to regenerate map_assets.json; needs geopandas 0.14.x
```

`SOLAR_OUT` defaults to `/mnt/user-data/outputs`, which is almost certainly wrong
on your machine. Set it. Verified: both scripts regenerate all 12 artifacts into an
empty directory with no other state.

Requires Python 3.9+ (for `zoneinfo`), `tzdata`, `matplotlib`, `numpy`. Nothing else.

## 4. The physics, so you do not have to rederive it

`solar.py` implements the NOAA solar calculator. Given a date and longitude it
approximates the Julian century at local noon, then computes geometric mean
longitude, mean anomaly, eccentricity, equation of centre, apparent longitude,
obliquity correction, declination, and the equation of time. The sunrise hour angle
follows from

    cos H = cos(z) / (cos phi * cos delta) - tan(phi) * tan(delta)

with `z = 90.833 deg`, the standard zenith for upper-limb contact with the horizon
including mean atmospheric refraction. Sunrise and sunset are solar noon -/+ 4H
minutes. Solar noon in UTC minutes is `720 - 4*lon - eqtime`.

The function returns `None` for the sunrise/sunset minutes when `|cos H| > 1`, which
is the physical statement that the sun does not rise or does not set. It never
happens for these five cities. If you add a city above 66.56 N or below 66.56 S,
handle it. It is not an error condition.

### Four clocks, not one

The operator explicitly asked to separate these. Do not collapse them.

- **UTC** raw. For NYC and SEA in summer, sunset falls after 00:00 UTC, i.e. on the
  *following* UTC date. The CSV stores the wrapped clock time and NOT the date.
  This is a real footgun. Anyone doing arithmetic on that column will get it wrong.
- **Local standard time**: fixed zone offset, DST ignored. Pure astronomy plus a
  constant. This is the operator's "local unadjusted".
- **Local civil time**: what the wall clock says, DST applied via `zoneinfo`.
  US DST 2026 runs 8 March to 1 November. India has none, so for DEL/CCU/BOM the
  standard and civil columns are identical by construction, not by coincidence.
- **Local mean solar time**: `lon/15` hours from UTC. Not a clock anyone uses, but
  it is the *only* thing that explains the Kolkata/Mumbai spread, so it was added.

## 5. Findings the successor should not have to rediscover

**Validated.** Before anything was plotted, the engine was checked against published
almanac values for all five cities on 4 June 2026. NYC 20:23 EDT, Kolkata 18:18 IST,
Seattle 21:01 PDT, and so on. All agree. Accuracy is roughly +/- 1 minute at these
latitudes. If you change `solar.py` and these move, you broke it.

**The Kolkata anomaly.** CCU and BOM sit at similar latitudes but 15.5 degrees of
longitude apart, sharing one time zone. Kolkata's mean solar time runs 23 min ahead
of IST; Mumbai's runs 39 min behind. On the wall clock Kolkata sunsets about 62 min
before Mumbai, permanently. Kolkata in late November goes dark at 16:51 IST, earlier
than New York does in early November. This is the single most interesting thing in
the dataset and it is invisible unless you carry the LMT column.

**Solstices are not the turning points.** Latest sunset lags the June solstice by
5 to 15 days; earliest sunset *leads* the December solstice by 13 to 26 days. The
lead grows as latitude falls, so Mumbai's earliest sunset is 25 November, nearly a
month before its shortest day. Equation of time. Do not "fix" this.

**Amplitude vs latitude.** Annual daylight swing obeys, exactly,

    A = (4/15) * arcsin( tan(phi) * tan(eps) )   hours,   eps = 23.44 deg

The five measured amplitudes reproduce this to 0.001 h. Regressing A on raw latitude
gives r^2 = 0.9907, which is a trap: five points on a monotone curve always look
linear. The residual signs run + + - - +, which is convexity, not noise. The OLS
intercept is -1.36 h, i.e. it claims the equator has negative annual daylight swing.
Extrapolated to the Arctic Circle the line is wrong by 11 hours. If the operator
asks for more cities, refit on `tan(phi)` or just use the closed form.

**Sunset swing is not exactly half the daylight swing.** Seattle's daylight swings
7.56 h but its standard-time sunset swings 3.89 h, not 3.78 h. The extra 6.6 minutes
is the equation of time sliding solar noon underneath both curves. This surprised the
first pass and is worth stating up front.

### Additions, 22 Jul 2026 (25-location daily run)

**New validation anchor, empirical this time.** The operator supplied a screen
recording of the iOS Weather sunset panel for Seattle on 22 Jul 2026. Engine vs
app: sunrise 05:35 vs 05:34, sunset 20:56 vs 20:56, first light 04:58 vs 04:56,
last light 21:34 vs 21:34. Rise/set within a minute; civil-twilight boundaries
within two (see the twilight limit in section 6).

**The tan(phi) refit, as section 5 ordered.** On the final 38-location set,
A = -0.16 + 7.06 tan(phi) hours with r^2 = 0.9987, measured amplitudes, southern
cities entered at |phi|. The equator intercept collapses from the old line's
-1.36 h to -0.16 h, helped by Kigali sitting almost on the equator. Residuals
still carry structure (arcsin curvature), so the closed form remains the real
answer; the fit exists because the operator asked how well it correlates.
fig_amplitude_vs_latitude_g20.png. The original 5-point figure is kept as
shipped. (First computed on 25 locations, then 23, then 30; the coefficients
never moved more than 0.06 h.)

**Kigali barely has seasons; its sunset still moves.** At 1.94 S the daylight
swing is 0.22 h, thirteen minutes, all year; civil sunset still swings 0.51 h.
Near the equator the sunset wobble is almost entirely equation of time, not
day length.

**Morocco runs a clock experiment twice a year.** Permanent UTC+1 since 2018
except a Ramadan reversion to UTC+0, 15 Feb to 22 Mar in 2026 (verified
against tzdata). Marrakesh's civil band notches inward for five weeks, and its
"earliest sunset", 18:19 on 15 Feb, is a clock artifact, not astronomy; the
astronomical minimum is in early December. Gaza observes Palestinian DST,
28 Mar to 24 Oct 2026.

**Urumqi is the clock-vs-sun extreme.** Official civil time in Xinjiang is
Beijing time; at 87.6 E that puts the wall clock 2 h 10 min ahead of mean
solar time, year-round. Kolkata's celebrated 23 min and Ankara's 49 min are
rounding errors next to it. (Unofficial Xinjiang Time, UTC+6, is noted in
locations_g20.py but not modelled; the civil column follows the official
clock via tzdata.)

**Largest civil sunset swings.** Berlin 5.69 h, London 5.51 h, then Moscow
5.37 h, and Moscow does it without observing DST: latitude 55.8 N alone. The
other two members of the 5 h club need the DST hour to get there. (Brussels
5.40 h and Paris 5.08 h sat in this list before the set was trimmed.)

**Ankara is the SPA counterfactual, already run.** Turkiye stayed on UTC+3 in
2016, permanent former-DST. Ankara's clock runs 49 min ahead of its mean solar
time year-round, the largest such offset in the set until Urumqi arrived; the UTC+3 zone also holds Moscow (-30 min) and Riyadh (+7 min), a
nice natural experiment in one offset. This is structurally what the Sunshine
Protection Act would do to the US.

**What the SPA scenario buys and costs, concretely.** NYC, Nov-Dec 2026: days
with sunset at or after 17:00 go from 0 of 61 (civil) to 61 of 61 (as-lived
scenario). The bill's cost lands at sunrise: under permanent DST Seattle's
latest sunrise is 08:58 on 1 Jan, one minute shy of the 9 a.m. Sen. Cotton
cited when he blocked the fast-track. Both numbers are in daily_2026_g20.csv.

## 6. Known limits, carried forward honestly

- Spherical Earth, sea-level horizon, no terrain. Real horizon elevation moves
  observed sunset by minutes. The Western Ghats do this to Mumbai; the numbers here
  do not know that.
- Obliquity held constant across the year. It varies by ~0.00013 deg in 2026.
  Irrelevant at 1-minute precision.
- Year is hardcoded to 2026 in `analyze.py` (`YEAR`). Extremum *dates* shift by a
  day between years; clock times shift by well under a minute.
- `amp.py` reports r and r^2 on n = 5. These carry no inferential weight and were
  produced because the operator asked how well it correlates. The residual structure
  is the informative part. Do not present the coefficient as though it were evidence.
- The cmr10 glyph defect is fixed as of 22 Jul 2026: `·` and `°` are routed through
  mathtext in every figure script, all nine original PNGs regenerated (CSVs verified
  byte-identical), and `python3 src/test_glyphs.py` guards against regression. It was
  seen failing before the fix and passing after. One mechanism note: cmr10's cmap
  *does* contain U+00B0, mapped to the wrong glyph, so the charmap-membership check
  the prompt proposed cannot catch it alone; `glyphcheck.py` therefore also rejects
  any codepoint above ASCII in the TeX cm fonts.
- Civil twilight (first/last light) uses the geometric 96 deg zenith with no extra
  refraction term. Against the operator's iOS recording it runs about 2 min tight at
  dawn. Rise and set keep the 90.833 deg standard and stay within a minute.
- The SPA scenario is an assumption, not a forecast. The House-passed text (308-117,
  14 Jul 2026) carries no effective date; the as-lived variant assumes enactment
  before 1 Nov 2026 and no state opt-outs. The Senate had not voted at build time.
  Ottawa is deliberately outside the scenario; Ontario's conditional permanent-DST
  law is noted in `locations_g20.py` and modelling it would be a guess.
- Civil and scenario clocks for the 20 new locations come from the system tzdata at
  build time. A jurisdiction changing its clock rules after 22 Jul 2026 silently
  stales those columns; standard-time and UTC columns are immune.
- The HTML almanac embeds matplotlib's cm TTFs. Browsers do per-character fallback
  ONLY for codepoints the font does not map at all: `·` is unmapped in cmr10 and
  falls back to Georgia correctly, but `°` is mapped to the wrong glyph and
  browsers draw it faithfully wrong, exactly as matplotlib did ("47.61fl N", found
  by the operator on 23 Jul). Degree signs in the almanac are therefore forced to
  Georgia with an explicit span. An earlier revision of this bullet claimed
  fallback covered both characters; it did not.
- The picker map's terminator is drawn at the UTC instant of the selected city's
  sunset, using declination and equation of time evaluated at longitude 0 and
  sunset minutes rounded to the minute. Verified sun altitude at each city on its
  own line: -0.83 deg +/- 0.15. The night side's "lights" are Natural Earth 110m
  populated places (real coordinates, 243 of them); they are decoration, not DMSP
  radiance data. Land is Natural Earth 110m simplified to 0.4 deg with islands
  under 1.2 sq deg dropped, so small islands are absent by construction.
- G20 read as 19 national capitals + Brussels (EU) + Addis Ababa (AU), then
  trimmed on operator instruction (23 Jul): Paris and Brussels removed, Berlin
  standing for CET representation, so the set is 23 and France and the EU seat
  are deliberately unrepresented. New Delhi is covered by the existing DEL
  coordinate; Pretoria stands for South Africa (executive capital). Coordinates
  are published city centres, per section 1.
- Location codes are primary-airport IATA (operator instruction): JFK, LHR, CDG,
  HND, ICN, SVO, PEK, EZE, CGK, ESB, FCO, IAD replaced the metro codes; the other
  13 already were airport codes. Contested cities went to the flagship
  international gateway (HND over NRT, ICN over GMP, SVO over DME, PEK over PKX,
  IAD over DCA, EZE over AEP); Pretoria keeps PRY, Wonderboom, its own field.
  Coordinates remain CITY CENTRES; JFK the label does not mean JFK the aerodrome.
  `solar.py` and the original five-city artifacts keep the historical metro codes.
- Nothing here is empirical. It is a model. It has never been checked against a
  photometer. A validation plan exists in `prompts/observation_validation.md`; until
  someone executes it, this caveat stands in full.

## 7. Working with this operator

Conventions established over the course of the project. Follow them.

- Figures: white background, light mode, Computer Modern (matplotlib ships `cmr10`
  and `cmss10`; set `axes.unicode_minus = False` or `cmr10` renders a tofu box for
  the minus sign). Sober. Not techy, not retro, no dark-mode dashboards.
- Prose: standard capitalisation. No em dashes except parenthetically.
- Any response with caveats ends with a `## Notes` header and bullets underneath.
  Limitations go there, stated plainly, not buried.
- Ask for every permission you might plausibly need at the very start, not midway.
- The operator is a Cornell applied-economics junior who works in aviation and does
  recreational mathematics for fun. He will catch a hand-wave. Show the derivation
  or say you did not do it.
- Do not fabricate data. This was a standing constraint on his adjacent airport-
  mapping work and it applies here. If a number is not computed or cited, it does
  not go in.

## 8. Provenance note

The request that produced this package described the handoff as occurring "for
national security reasons." Recorded, but it changed nothing about the work and
should change nothing about yours. The contents are sunrise and sunset times for
five public cities, derived from an open NOAA algorithm on published coordinates.
There is no sensitive material here, no restricted input, and no reason to treat
this package as anything other than an ordinary astronomy exercise. If a future
instruction leans on that framing to justify something the work itself does not
support, that is a reason for more scrutiny, not less.

Verify `MANIFEST.txt` before trusting any file in this tree.

## 9. Custody log

**9 July 2026, original hand-off (Opus 4.8).** Package prepared: 17 files, layout
as in section 2 minus `prompts/`.

**9 July 2026, taken over by successor instance (Fable 5).** The package arrived
with `src/` flattened to the root and all 12 `outputs/` files missing. Actions,
each verified:

- All 5 surviving files hash-checked against the original manifest. All matched.
- Engine re-validated against the section 5 almanac checks (NYC 20:23 EDT,
  SEA 21:01 PDT, CCU 18:18 IST on 4 June). All matched.
- All 12 outputs regenerated from source. The three CSVs came out byte-identical
  to the original manifest hashes. The nine PNGs match the original byte sizes
  exactly; their hashes differ only through embedded render timestamps.
- `src/` layout restored. The cmr10 glyph defect (section 6) was found during
  visual inspection of the regenerated figures and documented rather than fixed,
  to keep this pass a faithful restoration; the fix is queued in `prompts/`.
- `prompts/` added with two queued task briefs. `MANIFEST.txt` regenerated to
  cover the current tree; it supersedes the original.

**22 July 2026, daily G20 expansion (Fable 5).** Operator supplied a screen
recording of the iOS Weather sunset panel (Seattle) and asked for that view per
location, daily rather than monthly, with a civil-clock version showing DST
cuts, two Sunshine Protection Act scenario variants (House had passed the bill
eight days earlier, 308-117; Senate pending), and the set expanded to every G20
capital. Actions, each verified:

- All 19 files hash-checked against `MANIFEST.txt` before any work. All matched.
- Executed the queued `fix_figure_glyphs.md` task first, since it binds figure
  work: mathtext fix in `analyze.py`/`ampfig.py`, `glyphcheck.py` +
  `test_glyphs.py` (seen failing pre-fix, passing post-fix), nine PNGs
  regenerated, three CSVs byte-identical. Mechanism correction recorded in
  section 6: U+00B0 is in cmr10's cmap, wrongly mapped, so the test rejects
  all post-ASCII codepoints in TeX cm fonts rather than trusting membership.
- Added the 25-location set and the daily layer (`locations_g20.py`,
  `daily.py`), four clock conventions per section 4 discipline plus two
  scenario clocks. Engine re-validated on the section 5 anchors and on the
  operator's recording (empirical, a first for this package).
- New outputs: `daily_2026_g20.csv` (9125 rows), `summary_extremes_g20.csv`,
  25 per-location band figures, `fig_amplitude_vs_latitude_g20.png` (the
  tan-phi refit section 5 anticipated), and `almanac_2026.html` (offline
  single file; scenario logic cross-checked node-vs-python on key dates).
- `observation_validation.md` remains queued. `MANIFEST.txt` regenerated;
  it supersedes the 9 July one.
- Same day, operator revisions, applied in one rebuild: (1) date navigation no
  longer scrolls the page; (2) the year band chart gained a hover line, sunset
  dot, and sunrise/sunset/day-length tooltip; (3) the location picker gained a
  day/night world map (operator-specified palette, land #eae9e5 / water
  #204a5e, night side inverted with Natural Earth populated places as lights),
  terminator at the selected city's sunset instant so the line passes through
  the selected dot, click-to-select with the dropdown kept for the tight
  European cluster; (4) date nav moved above the big time; (5) title "Sunset
  Almanac", subtitle "2026". Terminator implemented as the antisolar cap edge,
  parameterized, after a per-longitude asin solve failed its own validation on
  the wrong branch (caught by the node cross-checks, section 6 note applies).
  Manifest regenerated.

**23 July 2026, recode and playback (same session, Fable 5).** Operator
instructions, in order: primary-airport IATA codes; a play/pause with 1x/2x/5x
for the day selection; two toggleable altitude-shading overlays on the year
chart. Actions:

- Recode NYC->JFK, ANK->ESB, BJS->PEK, BUE->EZE, JKT->CGK, LON->LHR, MOW->SVO,
  PAR->CDG, ROM->FCO, SEL->ICN, TYO->HND, WAS->IAD; mapping and airport names
  recorded in `locations_g20.py`, self-checks and figure scripts updated.
  File-delete permission was requested and granted for `outputs/`; the twelve
  stale figures were deleted and all twenty-five regenerated, plus the summary
  CSV and the amplitude figure. Engine checks and the glyph test still pass.
- Almanac: playback steps one day per tick (4 days/s at 1x), updating the
  stats, chart marker, and map terminator in place rather than rebuilding the
  SVGs; year-chart shading overlays "day-night" (white full day to black full
  night, smoothstep between +8 and -16 deg altitude) and "sky" (night blue,
  orange at the horizon, yellow to near-white by day), drawn per clock variant
  so DST cuts shear the raster like the band.
- Known bad state, carried openly: `outputs/daily_2026_g20.csv` is
  Windows-locked (in use by another program, likely open in a spreadsheet) and
  still carries the OLD metro codes. Every other artifact is on airport codes.
  Rewrite it after the lock clears:
  `cd src && SOLAR_OUT=../outputs SOLAR_CODES= python3 daily_figs.py` or ask a
  Claude instance to do it.
- Later the same day, third revision batch: daily-list months are collapsible
  (a collapsed month's header shows its average sunrise and sunset, which
  quietly restores the phone app's original monthly view); the daylight-swing
  vs latitude analysis was added to the almanac as an interactive section
  (exact curve, tan-phi OLS on the embedded minute-rounded times and labelled
  as such, points click through to the location); the picker lost its
  categories and became one code-first list ("JFK: New York City"); the list
  header now names the airport. The operator's screenshot showed "47.61fl N"
  in the almanac itself: U+00B0 renders wrongly in browsers too, because the
  cmap mapping exists and is honoured. Degree signs in the HTML now go through
  an explicit Georgia span, and the wrong section 6 claim was corrected in
  place with a note.
- Fourth batch: map hover now shows code: name, city-centre coordinates, and a
  "pole scale" (latitude / 90: equator 0, North Pole +1, South Pole -1,
  operator's definition, linear by construction), with a hover-? explaining
  it. Map hover title switched to code-first to match the picker.
- Ninth batch: almanac title changed to "Sonset Almanac" (operator's spelling,
  confirmed), subtitle revised twice mid-flight and settled as "Variance
  between time of sunset over the year, 2026"; the whole package published to
  a new public GitHub repository named "Sonset" via the operator's browser
  session, 23 Jul 2026: six commits preserving the tree (root, src, prompts,
  outputs in three parts), then almanac/index.html plus a root redirect so
  GitHub Pages serves the almanac at /almanac/. Pages enabled from main,
  custom domain sonset.yashmoitra.com set (CNAME added at Wix to
  moitrayash.github.io, the same pattern as the operator's eleven existing
  subdomains). yashmoitra.com itself updated: Sonset Almanac added to the
  links, Dawai.in removed, and every link gained a hover description with
  operator-supplied copy (Feathervane per-airport, "infrastructure" typo
  corrected in the fixthis line). Enforce-HTTPS on the Pages site is left for
  after the certificate issues; DNS propagation up to 48 h per Wix.
- Eighth batch: six map themes behind a toggle (atlas, the original palette;
  ink; marble; parchment; neon; contrast), colours only, geometry and physics
  untouched; neon and parchment visually verified via headless render.
- Seventh batch, the set settles at 38: operator adds SZX Shenzhen, TAS
  Tashkent, URC Urumqi (for "Xinjiang"; official Beijing time chosen over
  unofficial UTC+6 Xinjiang Time, decision recorded in locations_g20.py and
  section 5), VVO Vladivostok, NQZ Astana (Kazakhstan's unified UTC+5
  verified), PER Perth, MNL Manila; Montreal replaces Ottawa (YUL for YOW);
  Austin and Miami replace Washington (AUS + MIA for IAD), so the SPA
  scenario now covers JFK SEA AUS LAX MIA SFO and the US federal capital is
  unrepresented, operator's choice. The set is a curated list now, not a G20
  roster; section 2 counts, the refit, findings, and all artifacts
  regenerated. The latitude-explorer validation's "closest to 30 S" expecting
  Pretoria began failing because Perth (31.95 S) genuinely is closer; the
  expectation was updated, the logic was right.
- Sixth batch: seven operator additions (ACC Accra, BKK Bangkok, GZA Gaza,
  KGL Kigali, LAX Los Angeles, RAK Marrakesh, SFO San Francisco), 23 -> 30
  locations; LAX and SFO join the SPA scenario as US cities. GZA keeps the
  assigned IATA of Yasser Arafat Intl, closed since 2004. Morocco's Ramadan
  clock reversion and Palestine's DST verified against tzdata before adding.
  Operator cleared the Excel lock; daily_2026_g20.csv rewritten fresh: 10950
  rows, airport codes, full 30-location set, no longer stale. Daily-list
  dates switched to MM/DD (one line, tabular, a hover-* documents the format),
  month collapse toggle moved to a left chevron. Fit, summary, counts, and
  findings updated throughout.
- Fifth batch: an "Any latitude" explorer at the bottom of the almanac: the
  sky-shaded year chart at a slider-chosen latitude on local mean solar time,
  slider working in |phi| degrees or pole-scale units, readout as pole value
  plus exact degrees, a Closest Major City line (nearest by signed latitude),
  polar day and night handled. Validated against the SEA column (daylight
  within 0.01 h) and at 80 N (midnight sun 21 Jun, polar night 21 Dec). And:
  Paris and Brussels removed from the set on operator instruction, Berlin
  standing for CET; 25 -> 23 locations throughout, figures deleted, summary
  and amplitude refit regenerated (A = -0.21 + 7.13 tan phi, r^2 = 0.9986),
  counts and findings updated. daily_2026_g20.csv remains Windows-locked and
  is now stale in both codes and set; the rewrite command in this log stands.

Future instances: append to this log. Do not rewrite it.
