"""Offline geography helpers — no API key, no runtime network.

Zip-code centroids come from a committed public-domain dataset
(``data/zip_centroids.csv``: ``ZIP,LAT,LNG`` from 2013 US government data).
Used to validate US zips, place dealers on a map, and compute real
straight-line distances for radius filtering.
"""

import csv
import math
import os

# Resolved against several candidate roots. In the repo this file sits in backend/
# and the data lives at ../data/, but the Lambda bundle flattens backend/ to the
# package root, where ../data/ points outside the deployment package entirely.
# Checking both keeps one code path for local and Lambda.
def _find_csv() -> str:
    here = os.path.dirname(__file__)
    for rel in (("..", "data"), ("data",), (".",)):
        cand = os.path.abspath(os.path.join(here, *rel, "zip_centroids.csv"))
        if os.path.exists(cand):
            return cand
    return os.path.abspath(os.path.join(here, "..", "data", "zip_centroids.csv"))


_CSV_PATH = _find_csv()

# zip (5-digit str) -> (lat, lng)
_CENTROIDS: dict[str, tuple[float, float]] = {}
_LOADED = False


def _load() -> None:
    global _LOADED
    if _LOADED:
        return
    _LOADED = True  # set first so a bad file doesn't retry every call
    if not os.path.exists(_CSV_PATH):
        print(f"[geo] zip_centroids.csv not found at {_CSV_PATH}", flush=True)
        return
    try:
        with open(_CSV_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                z = (row.get("ZIP") or "").strip().zfill(5)
                try:
                    lat = float(row["LAT"])
                    lng = float(row["LNG"])
                except (KeyError, TypeError, ValueError):
                    continue
                if z:
                    _CENTROIDS[z] = (lat, lng)
        print(f"[geo] loaded {len(_CENTROIDS)} zip centroids", flush=True)
    except Exception as exc:  # noqa: BLE001 — best-effort load
        print(f"[geo] failed to load centroids: {exc}", flush=True)


def normalize_zip(zip_code) -> str | None:
    """Return a clean 5-digit zip string, or None if not a valid US zip format."""
    if zip_code is None:
        return None
    z = str(zip_code).strip()
    if len(z) >= 5 and z[:5].isdigit():
        return z[:5]
    if z.isdigit():
        return z.zfill(5)
    return None


def lookup(zip_code) -> tuple[float, float] | None:
    """Return (lat, lng) for a US zip, or None if unknown/invalid."""
    _load()
    z = normalize_zip(zip_code)
    if not z:
        return None
    return _CENTROIDS.get(z)


def haversine_miles(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance between two lat/lng points, in statute miles."""
    r = 3958.7613  # Earth radius (miles)
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.asin(min(1.0, math.sqrt(a)))


def distance_between_zips(zip_a, zip_b) -> float | None:
    """Miles between two zip centroids, or None if either is unknown."""
    a = lookup(zip_a)
    b = lookup(zip_b)
    if not a or not b:
        return None
    return haversine_miles(a[0], a[1], b[0], b[1])


def format_distance(miles: float | None) -> str:
    """Human distance label, e.g. '12.3 miles'."""
    if miles is None:
        return ""
    if miles < 10:
        return f"{miles:.1f} miles"
    return f"{round(miles)} miles"
