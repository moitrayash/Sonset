"""Generate src/map_assets.json for the almanac's day/night picker map.

Land outline: Natural Earth 110m via the shapefile bundled inside
geopandas 0.14.x (no runtime download), dissolved, simplified to 0.4 deg,
Antarctica dropped, islands under 1.2 sq deg dropped, emitted as one SVG
path (fill-rule evenodd so the Caspian reads as water). Night lights:
Natural Earth 110m populated places, coordinates only, purely to dress the
night side; they are real city positions, not radiance data.

The JSON is checked into src/ so rebuilding the almanac needs no geopandas.

  python3 make_landpath.py
"""

import json, os, warnings
warnings.filterwarnings("ignore")
import geopandas as gpd
from shapely.ops import unary_union
from shapely.geometry import MultiPolygon, Polygon

HERE = os.path.dirname(os.path.abspath(__file__))

world = gpd.read_file(gpd.datasets.get_path("naturalearth_lowres"))
world = world[world["continent"] != "Antarctica"]
land = unary_union(world.geometry).simplify(0.4, preserve_topology=True)
polys = list(land.geoms) if isinstance(land, MultiPolygon) else [land]


def ring(coords):
    return "M" + "L".join(f"{x:.1f} {-y:.1f}" for x, y in coords) + "Z"


parts = []
kept = 0
for p in polys:
    if p.area < 1.2:
        continue
    kept += 1
    parts.append(ring(p.exterior.coords))
    for hole in p.interiors:
        if Polygon(hole).area >= 1.2:
            parts.append(ring(hole.coords))

cities = gpd.read_file(gpd.datasets.get_path("naturalearth_cities"))
lights = [[round(pt.x, 1), round(pt.y, 1)] for pt in cities.geometry]

assets = dict(land="".join(parts), lights=lights)
out = os.path.join(HERE, "map_assets.json")
with open(out, "w") as f:
    json.dump(assets, f, separators=(",", ":"))
print(f"{kept} land polygons, {len(lights)} lights, "
      f"{os.path.getsize(out)/1024:.0f} KB -> map_assets.json")
