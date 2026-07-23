# Task: empirical validation of the solar model against reality

Project: `Sunset Time Analysis` (solar sunset 2026 package). Read `README.md` first,
especially sections 4 to 8. Verify `MANIFEST.txt` before trusting any file.

## Why this task exists

README section 6 ends with the most important caveat in the package: "Nothing here
is empirical. It is a model. It has never been checked against a photometer." Your
job is to retire, weaken, or precisely quantify that caveat. This is the painful
work the original pass skipped, and it is painful because most things that look like
observations are other models wearing a costume. Be ruthless about the distinction.

## Ground rules before anything else

- A published almanac, timeanddate.com, USNO tables, and Skyfield outputs are all
  **models**. Comparing against them bounds algorithmic error. It is not empirical
  validation and must never be described as such.
- An **observation** is a timestamped record of the sun actually crossing the
  apparent horizon at a known location: photometer data, timestamped webcam or
  all-sky camera frames, citizen-science sunset reports with stated methodology, or
  the operator timing it himself with a defined protocol.
- If a tier below yields nothing usable, report that plainly and move on. An honest
  "no usable observations could be obtained for BOM" is a valid result. A fabricated
  or laundered one is a firing offence; the no-fabrication rule (README section 7)
  is standing and absolute.

## Tier 1: bound the algorithmic error (model vs better model)

Compare `src/solar.py` against a rigorous ephemeris (Skyfield with a JPL DE
ephemeris, e.g. DE440s, is the practical choice; `pip install skyfield` and let it
fetch the ephemeris file). Compute sunset for all 365 days for all five cities with
both. Deliver the error distribution: mean, max, sign structure, seasonal shape.
Expected result is agreement within about a minute; if you see worse, find out why
before proceeding. Label every artifact from this tier "model vs ephemeris", not
"validation".

## Tier 2: quantify the terrain term (the known missing physics)

The model assumes a sea-level astronomical horizon. Real horizons have elevation.
Using a public DEM (SRTM 30 m or similar), compute the horizon elevation profile
along the sunset azimuth range for each city centre across the year (sunset azimuth
swings roughly 55 degrees over the year at these latitudes; compute the actual range
per city from the declination). Convert horizon elevation into minutes of sunset
advance. Cities where this should matter: SEA (Olympic Mountains to the west), BOM
(README claims the Western Ghats affect it; the Ghats lie mostly east of the city,
so test that claim rather than repeating it, and check the marine horizon case too).
Deliver a per-city table: typical and worst-case sunset shift in minutes, with the
azimuth and obstruction responsible.

## Tier 3: actual observations (the painful part)

Define the observable first, in writing: sunset is last contact of the upper limb
with the apparent horizon as seen from the stated coordinates at eye level, or a
stated alternative if the data source forces one. Then hunt, in rough order of
plausibility:

1. Timestamped public webcam or all-sky camera archives with a western horizon view
   in or near any of the five cities (port authority cams, airport cams, university
   meteorology cams). Frame timestamps give sunset to within the frame interval.
2. Citizen or academic sunset/green-flash observation datasets with methodology.
3. The operator himself. He is an aviation person; propose a simple protocol he can
   run (location, eye height, what to time, how many evenings) and hand it to him as
   a one-page appendix. His future data can close the loop even if nothing else does.

For every observation obtained, record: source, timestamp provenance (NTP-synced or
unknown), observer location and eye height, obstruction description, and the model
residual in minutes with the Tier 2 terrain correction applied and not applied.
Small n is fine. State n everywhere. Draw no inferential conclusions from n < 10;
present residuals as anecdata with error bars from the timestamp uncertainty.

## Deliverables

- `outputs/validation_tier1_ephemeris.csv`, `outputs/validation_tier2_terrain.csv`,
  and, if anything is obtained, `outputs/validation_tier3_observed.csv`.
- One figure per tier in the house style (white background, Computer Modern, sober;
  run `src/test_glyphs.py` if it exists by the time you work).
- `VALIDATION.md` at the package root: methods, results, and an explicit verdict on
  how README section 6's final caveat should now read. Propose the new wording.
- Regenerated `MANIFEST.txt` covering the new files.

## Conventions (README section 7, binding)

Standard capitalisation. No em dashes except parenthetically. Every document with
caveats ends with a `## Notes` header and bullets, limitations stated plainly. Show
derivations. Ask for every permission you might plausibly need at the very start:
network access for ephemeris and DEM downloads, webcam archive access, and package
installation are all foreseeable; list them in your first message.
