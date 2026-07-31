"""Inventory + dealer data-access layer (the "repository" seam).

Primary source: **Auto.dev Vehicle Listings API** (real nationwide dealers +
inventory by zip + radius) when ``AUTODEV_API_KEY`` is set — see ``autodev.py``.

Fallback (no key / API error / no results): a **seed dealer set**
(``data/dealers.json``, real geography) with the bundled demo inventory
(``data/carData.json``, 162 real scraped listings) deterministically distributed
across those dealers so the zip → radius → dealer → browse flow works anywhere.

Callers in ``main.py`` only use the public functions here; swapping the source
(Auto.dev today, Supabase later) doesn't change them.
"""

import hashlib
import json
import os

import autodev
import geo

# Which data source backs dealers + inventory:
#   "autodev" — Auto.dev Vehicle Listings API (default; results are disk-cached).
#   "seed"    — bundled demo inventory only (no network / no API calls).
DATA_SOURCE = os.getenv("CARSCOUT_DATA_SOURCE", "autodev").lower()

# Fetches use the user's chosen radius and are cached per (zip, radius) on disk,
# so re-running the SAME zip + radius costs zero API calls. Fetching AT the radius
# (not a fixed 250) concentrates listings in range -> plenty of in-radius cars.
MAX_RADIUS_MILES = 250

# Same resolution problem as geo.py: ../data/ is correct from backend/ in the repo
# but points outside the bundle once Lambda flattens backend/ to the package root.
def _find_data_dir() -> str:
    here = os.path.dirname(__file__)
    for rel in (("..", "data"), ("data",)):
        cand = os.path.abspath(os.path.join(here, *rel))
        if os.path.isdir(cand):
            return cand
    return os.path.abspath(os.path.join(here, "..", "data"))


_DATA_DIR = _find_data_dir()
_CARDATA_PATH = os.path.join(_DATA_DIR, "carData.json")
_DEALERS_PATH = os.path.join(_DATA_DIR, "dealers.json")

_seed_dealers: list | None = None        # [{id,name,city,state,zip,phone,hours,lat,lng}]
_demo_listings: list | None = None        # carData listings, each tagged with _dealer
_demo_counts: dict[str, int] = {}         # dealer id -> assigned listing count


# ---------------------------------------------------------------- loaders

def _load_seed_dealers() -> list:
    global _seed_dealers
    if _seed_dealers is not None:
        return _seed_dealers
    dealers = []
    try:
        with open(_DEALERS_PATH, "r", encoding="utf-8") as f:
            raw = json.load(f).get("dealers", [])
    except Exception as exc:  # noqa: BLE001
        print(f"[repository] failed to load dealers.json: {exc}", flush=True)
        raw = []
    for d in raw:
        pt = geo.lookup(d.get("zip"))
        if not pt:
            continue  # can't place it on the map — skip
        dealers.append({
            "id": d["id"],
            "name": d["name"],
            "address": f"{d.get('city', '')}, {d.get('state', '')} {d.get('zip', '')}".strip(", "),
            "city": d.get("city"),
            "state": d.get("state"),
            "zip": d.get("zip"),
            "phone": d.get("phone", ""),
            "hours": d.get("hours", ""),
            "website": d.get("website"),
            "lat": pt[0],
            "lng": pt[1],
        })
    _seed_dealers = dealers
    print(f"[repository] seed dealers placed: {len(dealers)}", flush=True)
    return dealers


def _raw_cardata() -> list:
    if not os.path.exists(_CARDATA_PATH):
        print(f"[repository] carData.json not found at {_CARDATA_PATH}", flush=True)
        return []
    try:
        with open(_CARDATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f).get("listings", [])
    except Exception as exc:  # noqa: BLE001
        print(f"[repository] failed to load carData: {exc}", flush=True)
        return []


def _load_demo_listings() -> list:
    """carData listings, each deterministically attributed to a seed dealer."""
    global _demo_listings, _demo_counts
    if _demo_listings is not None:
        return _demo_listings
    dealers = _load_seed_dealers()
    listings = _raw_cardata()
    if not dealers:
        _demo_listings = listings
        return listings
    counts: dict[str, int] = {}
    for lst in listings:
        key = str(lst.get("id", "")).encode("utf-8")
        idx = int(hashlib.md5(key).hexdigest(), 16) % len(dealers)
        dealer = dealers[idx]
        lst["_dealer"] = {
            "id": dealer["id"], "name": dealer["name"], "address": dealer["address"],
            "city": dealer["city"], "state": dealer["state"], "zip": dealer["zip"],
        }
        counts[dealer["id"]] = counts.get(dealer["id"], 0) + 1
    _demo_listings = listings
    _demo_counts = counts
    return listings


# ---------------------------------------------------------------- seed fallback

def _seed_dealers_near(zip_code: str, radius_miles: int) -> list:
    _load_demo_listings()  # ensures _demo_counts is populated
    origin = geo.lookup(zip_code)
    if not origin:
        return []
    out = []
    for d in _load_seed_dealers():
        dist = geo.haversine_miles(origin[0], origin[1], d["lat"], d["lng"])
        if dist > radius_miles:
            continue
        out.append({
            "id": d["id"], "name": d["name"], "address": d["address"],
            "city": d["city"], "state": d["state"], "zip": d["zip"],
            "phone": d["phone"], "hours": d["hours"],
            "lat": d["lat"], "lng": d["lng"],
            "distance": geo.format_distance(dist),
            "inventory_count": _demo_counts.get(d["id"], 0),
            "_distance_mi": dist,
        })
    out.sort(key=lambda x: x["_distance_mi"])
    for d in out:
        d.pop("_distance_mi", None)
    return out


def _seed_listings_for_dealers(dealer_ids: set) -> list:
    listings = _load_demo_listings()
    if not dealer_ids:
        return list(listings)
    return [l for l in listings if (l.get("_dealer") or {}).get("id") in dealer_ids]


# ---------------------------------------------------------------- public API

def get_dealers_near(zip_code: str, radius_miles: int = MAX_RADIUS_MILES) -> list:
    """Dealers within ``radius_miles`` of the zip, sorted nearest-first."""
    if DATA_SOURCE != "seed" and autodev.is_enabled():
        listings = autodev.fetch_area(zip_code, radius_miles)
        if listings:
            return autodev.dealers_from_listings(listings, radius_miles)
        print("[repository] Auto.dev returned nothing — using seed dealers", flush=True)
    return _seed_dealers_near(zip_code, radius_miles)


def get_listings_for_dealers(zip_code: str, radius_miles: int = MAX_RADIUS_MILES,
                             dealer_ids=None) -> list:
    """Candidate listings for the area, restricted to the selected dealers.

    Returns CarScout-canonical listing dicts (``vehicle`` sub-dict, ``image_urls``,
    ``highlighted_features_raw``, ``_dealer`` …) ready for the scorer.
    """
    ids = set(dealer_ids or [])
    if DATA_SOURCE != "seed" and autodev.is_enabled():
        listings = autodev.fetch_area(zip_code, radius_miles)
        if listings:
            return [l for l in listings if not ids or (l.get("_dealer") or {}).get("id") in ids]
    return _seed_listings_for_dealers(ids)


def get_listings():
    """Back-compat: all bundled demo listings (no dealer filter)."""
    return _load_demo_listings()
