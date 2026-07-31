"""DynamoDB listing cache — the tier that survives serverless.

Why this exists on top of the existing disk cache: ``autodev._disk_write`` writes
under ``backend/.cache/autodev/``, which works fine on one long-lived machine and
stops working the moment the backend runs anywhere elastic. On Lambda the
filesystem is ephemeral and per-instance, so a cold start starts from zero and
two warm instances never share a hit. Every miss is an Auto.dev call, and the
free tier is 1,000 calls/month, so a cache that silently stops working is a quota
problem, not just a latency one.

DynamoDB gives one shared cache across every instance and deploy, with expiry
handled by the table itself rather than by mtime checks.

Layout:
    partition key   cache_key   "78750#50"     (zip # distance_miles)
    attribute       listings    JSON string
    attribute       expires_at  epoch seconds  <- native DynamoDB TTL

Using the table's TTL rather than filtering on read means expired rows are
removed by DynamoDB and stop costing storage. TTL deletion is best-effort and can
lag by ~48h, so reads still check ``expires_at`` themselves.

Disabled unless CARSCOUT_DYNAMO_TABLE is set AND boto3 can find credentials.
When disabled every function is a no-op and callers fall through to the disk
tier, so this is safe to import with no AWS account at all.
"""

import json
import os
import time

TABLE_ENV = "CARSCOUT_DYNAMO_TABLE"
REGION_ENV = "AWS_REGION"
_DEFAULT_TTL = int(os.getenv("AUTODEV_CACHE_TTL", str(30 * 24 * 3600)))  # match the disk tier

_table = None
_checked = False
_disabled_reason: str | None = None


def table_name() -> str | None:
    name = os.getenv(TABLE_ENV)
    return name.strip() if name and name.strip() else None


def _get_table():
    """Resolve the table once. Any failure disables the tier permanently."""
    global _table, _checked, _disabled_reason
    if _checked:
        return _table
    _checked = True

    name = table_name()
    if not name:
        _disabled_reason = f"{TABLE_ENV} not set"
        return None
    try:
        import boto3  # imported lazily so the app runs without boto3 installed
    except ImportError:
        _disabled_reason = "boto3 not installed"
        return None
    try:
        region = os.getenv(REGION_ENV) or "us-east-1"
        res = boto3.resource("dynamodb", region_name=region)
        tbl = res.Table(name)
        tbl.load()  # raises if the table is missing or credentials are bad
        _table = tbl
        print(f"[dynamo] cache tier active: {name} ({region})", flush=True)
    except Exception as exc:  # noqa: BLE001 — never let cache setup break a request
        _disabled_reason = str(exc).split("\n")[0][:120]
        print(f"[dynamo] disabled: {_disabled_reason}", flush=True)
        _table = None
    return _table


def is_enabled() -> bool:
    return _get_table() is not None


def status() -> str:
    return "enabled" if is_enabled() else f"disabled ({_disabled_reason})"


def _key(z: str, distance: int) -> str:
    return f"{z}#{int(distance)}"


def read(z: str, distance: int):
    """Return cached listings, or None on miss/expiry/any failure."""
    tbl = _get_table()
    if tbl is None:
        return None
    try:
        resp = tbl.get_item(Key={"cache_key": _key(z, distance)})
    except Exception as exc:  # noqa: BLE001
        print(f"[dynamo] read failed: {exc}", flush=True)
        return None

    item = resp.get("Item")
    if not item:
        return None
    # TTL sweeps lag, so an expired row can still be returned by get_item.
    try:
        if int(item.get("expires_at", 0)) <= int(time.time()):
            return None
    except (TypeError, ValueError):
        return None
    try:
        return json.loads(item["listings"])
    except Exception as exc:  # noqa: BLE001
        print(f"[dynamo] corrupt cache row {_key(z, distance)}: {exc}", flush=True)
        return None


def write(z: str, distance: int, listings: list, ttl_seconds: int | None = None) -> bool:
    """Persist listings. Returns True on success; failures are logged, not raised."""
    tbl = _get_table()
    if tbl is None or not listings:
        return False
    ttl = int(ttl_seconds if ttl_seconds is not None else _DEFAULT_TTL)
    try:
        tbl.put_item(Item={
            "cache_key": _key(z, distance),
            "listings": json.dumps(listings),
            "expires_at": int(time.time()) + ttl,
            "count": len(listings),
        })
        return True
    except Exception as exc:  # noqa: BLE001
        # A 400KB item limit is the realistic failure here; the disk tier still has it.
        print(f"[dynamo] write failed ({len(listings)} listings): {exc}", flush=True)
        return False
