"""
Benchmark: reverse_geocoder vs geopy Nominatim vs geopandas+GADM
Test coordinates: Worcester, MA area  (42.246, -71.760)
Run from any directory.
"""
import time

LAT, LON = 42.246075, -71.76043055555556
N_WARM   = 5   # warm-call repetitions


def bench(label, fn):
    # Cold start
    t0 = time.perf_counter()
    result = fn()
    cold = time.perf_counter() - t0
    print(f"\n[{label}]")
    print(f"  Result   : {result}")
    print(f"  Cold start: {cold:.2f}s")

    # Warm calls
    times = []
    for _ in range(N_WARM):
        t0 = time.perf_counter()
        fn()
        times.append(time.perf_counter() - t0)
    avg = sum(times) / len(times)
    print(f"  Warm avg ({N_WARM}x): {avg:.3f}s")


# ── 1. reverse_geocoder ────────────────────────────────────────────────────────
def run_rg():
    import reverse_geocoder as rg
    r = rg.search((LAT, LON), verbose=False)
    return f"{r[0]['name']}, {r[0]['admin1']}"

# ── 2. geopy Nominatim ────────────────────────────────────────────────────────
def run_geopy():
    from geopy.geocoders import Nominatim
    geo = Nominatim(user_agent="pmo_benchmark")
    loc = geo.reverse(f"{LAT}, {LON}", language="en")
    addr = loc.raw['address']
    city = addr.get('city') or addr.get('town') or addr.get('village') or '?'
    state = addr.get('state', '')
    return f"{city}, {state}"

# ── 3. geopandas + GADM ───────────────────────────────────────────────────────
# Download USA level-2 from: https://gadm.org/download_country.html
# Place the .gpkg or .shp file path below.
GADM_PATH = r"D:\path\to\gadm41_USA_2.gpkg"   # <-- update this

def run_geopandas():
    import geopandas as gpd
    from shapely.geometry import Point
    gdf = gpd.read_file(GADM_PATH)
    pt  = Point(LON, LAT)
    hit = gdf[gdf.geometry.contains(pt)]
    if hit.empty:
        return "not found"
    return f"{hit.iloc[0]['NAME_2']}, {hit.iloc[0]['NAME_1']}"


if __name__ == '__main__':
    bench("reverse_geocoder", run_rg)
    bench("geopy Nominatim",  run_geopy)

    import os
    if os.path.exists(GADM_PATH):
        bench("geopandas + GADM", run_geopandas)
    else:
        print(f"\n[geopandas + GADM]  skipped — set GADM_PATH in script")
