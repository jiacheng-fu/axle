"""Auto.dev Vehicle Listings API client.

Primary live data source for dealers + inventory (nationwide, by zip + radius).
Docs: https://docs.auto.dev/v2/products/vehicle-listings
  GET https://api.auto.dev/listings?zip=&distance=   (Authorization: Bearer <key>)
  -> { "data": [ { vin, location, vehicle:{year,make,model,trim},
                   retailListing:{price,...} } ], "total": N }

The public docs don't enumerate every field name (dealer/photos/mileage), so the
normalizer below probes several candidate paths and degrades gracefully. On the
first successful call it logs the raw field names of one listing so the mapping
can be tightened against the real response.

No key set -> ``is_enabled()`` returns False and callers fall back to the seed
layer in ``repository.py``. Results are cached in-process (TTL) to respect the
free tier's 1,000 calls/month cap.
"""

import json
import os
import time

import geo
import dynamo_cache

API_BASE = "https://api.auto.dev"
_TTL_SECONDS = 900  # in-memory cache (per process)
_PAGE_LIMIT = int(os.getenv("AUTODEV_LIMIT", "100"))
_MAX_PAGES = int(os.getenv("AUTODEV_PAGES", "5"))  # pages to pull per area (dealer coverage)

# Persistent on-disk cache: re-running the SAME zip across app restarts reuses the
# saved results and makes ZERO API calls (protects the free-tier monthly quota).
# Long default TTL so re-recording a demo over days/weeks still hits the cache.
# Delete backend/.cache/autodev/ to force fresh data.
# On Lambda the whole filesystem is read-only except /tmp, so writing beside the
# source would fail on every request. /tmp is also per-instance and wiped on cold
# start, which is precisely why the DynamoDB tier above it exists.
_ON_LAMBDA = bool(os.getenv("AWS_LAMBDA_FUNCTION_NAME"))
_CACHE_DIR = (os.path.join("/tmp", "autodev-cache") if _ON_LAMBDA
              else os.path.join(os.path.dirname(__file__), ".cache", "autodev"))
_DISK_TTL = int(os.getenv("AUTODEV_CACHE_TTL", str(30 * 24 * 3600)))  # 30 days

# (zip, distance) -> (fetched_at, [normalized listing, ...])
_CACHE: dict[tuple[str, int], tuple[float, list]] = {}
_logged_shape = False


def _disk_path(z: str, distance: int) -> str:
    return os.path.join(_CACHE_DIR, f"{z}_{distance}.json")


def _disk_read(z: str, distance: int):
    path = _disk_path(z, distance)
    try:
        if os.path.exists(path) and (time.time() - os.path.getmtime(path)) < _DISK_TTL:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as exc:  # noqa: BLE001
        print(f"[autodev] disk cache read failed: {exc}", flush=True)
    return None


def _disk_write(z: str, distance: int, listings: list) -> None:
    try:
        os.makedirs(_CACHE_DIR, exist_ok=True)
        with open(_disk_path(z, distance), "w", encoding="utf-8") as f:
            json.dump(listings, f)
    except Exception as exc:  # noqa: BLE001
        print(f"[autodev] disk cache write failed: {exc}", flush=True)


def api_key() -> str | None:
    key = os.getenv("AUTODEV_API_KEY")
    return key.strip() if key and key.strip() else None


def is_enabled() -> bool:
    return api_key() is not None


# ---------------------------------------------------------------- helpers

def _dig(obj, path: str):
    """Traverse a dotted path through nested dicts; return None on any miss."""
    cur = obj
    for part in path.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return None
    return cur


def _first(obj, *paths, default=None):
    """First non-empty value among several candidate dotted paths."""
    for p in paths:
        val = _dig(obj, p)
        if val not in (None, "", [], {}):
            return val
    return default


def _num(val):
    """Coerce '$24,995' / '24995' / 24995.0 -> int, else None."""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return int(val)
    s = "".join(ch for ch in str(val) if ch.isdigit() or ch == ".")
    if not s:
        return None
    try:
        return int(float(s))
    except ValueError:
        return None


def _photos(item) -> list:
    val = _first(
        item, "photoUrls", "photos", "images", "media.photoUrls",
        "media.images", "retailListing.photoUrls", "vehicle.photoUrls",
        default=[],
    )
    if isinstance(val, str):
        return [val]
    if isinstance(val, list):
        out = []
        for p in val:
            if isinstance(p, str):
                out.append(p)
            elif isinstance(p, dict):
                u = _first(p, "url", "src", "href")
                if u:
                    out.append(u)
        return out
    return []


def _coords(item) -> tuple[float, float] | None:
    """Auto.dev returns location as a [lng, lat] array; also tolerate a dict."""
    loc = item.get("location")
    if isinstance(loc, (list, tuple)) and len(loc) >= 2:
        try:
            return (float(loc[1]), float(loc[0]))  # (lat, lng)
        except (TypeError, ValueError):
            return None
    if isinstance(loc, dict):
        la = _first(loc, "lat", "latitude")
        ln = _first(loc, "lng", "lon", "longitude")
        try:
            if la is not None and ln is not None:
                return (float(la), float(ln))
        except (TypeError, ValueError):
            return None
    return None


def _normalize(item, origin: tuple[float, float] | None) -> dict | None:
    """Map one Auto.dev listing into CarScout's canonical listing shape.

    Targets the real Auto.dev schema (vehicle.*, retailListing.*, location=[lng,lat]),
    with light fallbacks in case other listings vary.
    """
    vin = _first(item, "vin", "vehicle.vin")
    v = item.get("vehicle") or {}
    r = item.get("retailListing") or {}

    dealer_pt = _coords(item)
    dealer_name = _first(item, "retailListing.dealer", "location.dealerName",
                         "dealer.name", default="Dealer")
    d_city = _first(item, "retailListing.city", "location.city")
    d_state = _first(item, "retailListing.state", "location.state", "vehicle.state")

    distance = None
    if origin and dealer_pt:
        distance = geo.haversine_miles(origin[0], origin[1], dealer_pt[0], dealer_pt[1])

    address = ", ".join([b for b in [d_city, d_state] if b])
    did_base = f"{(dealer_name or 'dealer').strip().lower()}|{(d_city or '').lower()}|{(d_state or '').lower()}"
    dealer_id = "autodev-" + "".join(c if c.isalnum() else "-" for c in did_base)[:70]

    dealer = {
        "id": dealer_id,
        "name": dealer_name,
        "address": address,
        "city": d_city,
        "state": d_state,
        "zip": geo.normalize_zip(_first(item, "retailListing.zip", "location.zip")),
        "phone": _first(item, "retailListing.phone", "location.phone", default=""),
        "hours": "",
        "lat": dealer_pt[0] if dealer_pt else None,
        "lng": dealer_pt[1] if dealer_pt else None,
        "distance": geo.format_distance(distance) if distance is not None else "",
        "_distance_mi": distance,
    }

    model = v.get("model")
    if model is not None:
        model = str(model)  # Auto.dev sometimes returns numeric models (e.g. 1500)

    vehicle = {
        "make": v.get("make"),
        "model": model,
        "year": _num(v.get("year")),
        "trim": v.get("trim"),
        "price_usd": _num(_first(item, "retailListing.price", "price")),
        "odometer_miles": _num(_first(item, "retailListing.miles", "retailListing.mileage")),
        "exterior_color": _first(item, "vehicle.exteriorColor", "retailListing.exteriorColor"),
        "interior_color": _first(item, "vehicle.interiorColor", "retailListing.interiorColor"),
        "body_style": _first(item, "vehicle.bodyStyle", "vehicle.type", "vehicle.bodyType"),
        "normal_body_style": _first(item, "vehicle.bodyStyle", "vehicle.type"),
        "drivetrain": _first(item, "vehicle.drivetrain", "vehicle.driveType"),
        "horsepower_hp": _num(_first(item, "vehicle.horsepower", "vehicle.engineHorsepower")),
        "torque_lbft": _num(_first(item, "vehicle.torque")),
        "engine_type": _first(item, "vehicle.engine", "vehicle.engineType"),
        "transmission": _first(item, "vehicle.transmission"),
        "fuel_type": _first(item, "vehicle.fuel", "vehicle.fuelType"),
        "mpg_city": _num(_first(item, "vehicle.mpgCity", "vehicle.cityMpg")),
        "mpg_highway": _num(_first(item, "vehicle.mpgHighway", "vehicle.highwayMpg")),
        "seating_capacity": _num(_first(item, "vehicle.seats", "vehicle.seatingCapacity")),
    }

    if not vehicle["make"] and not vin:
        return None  # not a usable listing

    primary = _first(item, "retailListing.primaryImage", "primaryImage")
    images = [primary] if isinstance(primary, str) and primary else _photos(item)

    return {
        "id": vin or item.get("@id") or f"{dealer_id}-{len(_CACHE)}",
        "source_url": _first(item, "retailListing.vdp", "retailListing.vdpUrl",
                             "retailListing.clickoffUrl", default=""),
        "scraped_at": None,
        "vehicle": vehicle,
        "highlighted_features_raw": _first(item, "vehicle.features", "features", default=[]) or [],
        "image_urls": images,
        "dealer_notes": _first(item, "retailListing.sellerComments", "vehicle.series",
                               default="") or "",
        "spec_sections": {},
        "_dealer": dealer,
    }


# ---------------------------------------------------------------- API call

def fetch_area(zip_code: str, distance_miles: int) -> list:
    """Return normalized candidate listings within ``distance_miles`` of ``zip_code``.

    Pulls up to ``_MAX_PAGES`` pages so we surface enough listings to reveal the
    real set of dealers in range (one page of 100 badly under-counts dealers).
    Cached per (zip, distance) for TTL. Returns [] on any failure so callers can
    fall back to the seed layer.
    """
    global _logged_shape
    key = api_key()
    if not key:
        return []

    z = geo.normalize_zip(zip_code)
    if not z:
        return []

    cache_key = (z, int(distance_miles))
    hit = _CACHE.get(cache_key)
    if hit and (time.time() - hit[0]) < _TTL_SECONDS:
        return hit[1]

    # Shared cache: survives cold starts and is visible to every instance, which
    # the disk tier is not once this runs anywhere elastic. Checked before disk
    # because it is the tier that stays correct in deployment.
    shared = dynamo_cache.read(z, int(distance_miles))
    if shared is not None:
        print(f"[autodev] dynamo cache hit {z} d={distance_miles}: {len(shared)} listings (no API call)", flush=True)
        _CACHE[cache_key] = (time.time(), shared)
        return shared

    # Persistent cache: reuse a prior run's results — no API call.
    disk = _disk_read(z, int(distance_miles))
    if disk is not None:
        print(f"[autodev] disk cache hit {z} d={distance_miles}: {len(disk)} listings (no API call)", flush=True)
        _CACHE[cache_key] = (time.time(), disk)
        # Promote to the shared tier so other instances stop paying for this call.
        dynamo_cache.write(z, int(distance_miles), disk)
        return disk

    try:
        import httpx
    except ImportError:
        print("[autodev] httpx not installed; cannot call API", flush=True)
        return []

    origin = geo.lookup(z)
    headers = {"Authorization": f"Bearer {key}", "Accept": "application/json"}
    out: list = []
    pages = 0
    for page in range(1, _MAX_PAGES + 1):
        pages = page
        params = {"zip": z, "distance": int(distance_miles), "limit": _PAGE_LIMIT, "page": page}
        try:
            resp = httpx.get(f"{API_BASE}/listings", params=params, headers=headers, timeout=30.0)
            resp.raise_for_status()
            payload = resp.json()
        except Exception as exc:  # noqa: BLE001 — keep whatever we have, fall back if none
            print(f"[autodev] request failed (page {page}): {exc}", flush=True)
            break

        raw = payload.get("data") if isinstance(payload, dict) else payload
        if not isinstance(raw, list):
            print(f"[autodev] unexpected payload shape: {type(payload)}", flush=True)
            break

        if raw and not _logged_shape:
            _logged_shape = True
            sample = raw[0]
            print(f"[autodev] sample listing top-level keys: {list(sample.keys())}", flush=True)
            for sub in ("location", "vehicle", "retailListing"):
                if isinstance(sample.get(sub), dict):
                    print(f"[autodev]   {sub} keys: {list(sample[sub].keys())}", flush=True)

        out.extend(n for n in (_normalize(it, origin) for it in raw) if n)
        if len(raw) < _PAGE_LIMIT:
            break  # last page

    print(f"[autodev] {z} d={distance_miles}: {len(out)} normalized listings across {pages} page(s)", flush=True)
    _CACHE[cache_key] = (time.time(), out)
    if out:
        _disk_write(z, int(distance_miles), out)  # persist non-empty results only
        dynamo_cache.write(z, int(distance_miles), out)  # shared tier, survives cold starts
    return out


def dealers_from_listings(listings: list, radius_miles: int) -> list:
    """Collapse listings into unique dealers within radius, sorted by distance."""
    by_id: dict[str, dict] = {}
    for lst in listings:
        d = lst.get("_dealer") or {}
        did = d.get("id")
        if not did:
            continue
        dist = d.get("_distance_mi")
        if dist is not None and dist > radius_miles:
            continue
        entry = by_id.get(did)
        if entry is None:
            by_id[did] = {**{k: v for k, v in d.items() if not k.startswith("_")},
                          "_distance_mi": dist, "inventory_count": 1}
        else:
            entry["inventory_count"] += 1
            if dist is not None and (entry["_distance_mi"] is None or dist < entry["_distance_mi"]):
                entry["_distance_mi"] = dist
                entry["distance"] = d.get("distance")
    dealers = list(by_id.values())
    dealers.sort(key=lambda x: (x.get("_distance_mi") is None, x.get("_distance_mi") or 0))
    for d in dealers:
        d.pop("_distance_mi", None)
    return dealers
