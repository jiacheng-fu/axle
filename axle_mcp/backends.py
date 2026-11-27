"""Where the MCP server gets its data.

HttpBackend   - calls a deployed Axle API (set AXLE_API_URL). Live dealer inventory.
LocalBackend  - imports Axle's own backend in-process and runs the same ranking
                engine over the bundled demo inventory (162 real listings across
                seed dealers). No network, no API keys, nothing spent upstream.

Both backends send Axle a STRUCTURED preference dict. The agent calling the tool
is already a language model, so it does the "plain English -> filters" step itself
and Axle's own LLM extraction step is skipped entirely: a search costs no model
calls, only (cached) inventory lookups.
"""

import contextlib
import os
import sys
from pathlib import Path

import httpx

BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"


@contextlib.contextmanager
def stdout_to_stderr():
    """Axle's backend logs with print(). On a stdio MCP server, stdout IS the
    protocol channel, so any stray print would corrupt the JSON-RPC stream."""
    with contextlib.redirect_stdout(sys.stderr):
        yield


_axle_core = None


def load_axle_core():
    """Import Axle's backend (main.py) once, pinned to the bundled seed data unless
    AXLE_LOCAL_DATA_SOURCE=autodev is set explicitly - so running the MCP server
    locally can never spend the live 1,000-call/month listings quota by accident."""
    global _axle_core
    if _axle_core is not None:
        return _axle_core
    if os.environ.get("AXLE_LOCAL_DATA_SOURCE", "seed").lower() != "autodev":
        # Set before import: repository.py reads it at import time, and
        # load_dotenv() never overrides a variable that is already set.
        os.environ["CARSCOUT_DATA_SOURCE"] = "seed"
    if str(BACKEND_DIR) not in sys.path:
        sys.path.insert(0, str(BACKEND_DIR))
    with stdout_to_stderr():
        import main as axle_main
    _axle_core = axle_main
    return _axle_core


class LocalBackend:
    source = "axle-demo-inventory"

    def __init__(self):
        self.core = load_axle_core()

    def find_dealers(self, zip_code, radius_miles):
        with stdout_to_stderr():
            normalized = self.core.geo.normalize_zip(zip_code)
            if normalized is None or self.core.geo.lookup(normalized) is None:
                raise LookupError("Axle does not recognise zip code " + zip_code + ".")
            return self.core.get_dealers_near(normalized, radius_miles)

    def search(self, zip_code, radius_miles, prefs, dealer_ids):
        with stdout_to_stderr():
            candidates = self.core.get_listings_for_dealers(zip_code, radius_miles, dealer_ids)
            # rank_listings may write into prefs (financing), so hand it a copy.
            return self.core.rank_listings(dict(prefs), candidates)


class HttpBackend:
    source = "axle-live"

    def __init__(self, base_url, timeout_seconds=30.0, transport=None):
        if not base_url.startswith("https://") and not base_url.startswith("http://localhost"):
            raise ValueError("AXLE_API_URL must be an https:// URL (or http://localhost for development).")
        self.base_url = base_url.rstrip("/")
        self.client = httpx.Client(timeout=timeout_seconds, transport=transport)

    def find_dealers(self, zip_code, radius_miles):
        params = {"zip": zip_code, "radius": radius_miles}
        response = self.client.get(self.base_url + "/dealers", params=params)
        response.raise_for_status()
        data = response.json()
        if not data.get("valid"):
            raise LookupError(data.get("error") or "Axle rejected that zip code.")
        return data.get("dealers") or []

    def search(self, zip_code, radius_miles, prefs, dealer_ids):
        # stage "done" + text "show_results" is the API path that ranks the given
        # state as-is, without asking Axle's model to re-read any text.
        payload = {
            "text": "show_results",
            "stage": "done",
            "zip": zip_code,
            "radius": radius_miles,
            "state": prefs,
            "dealer_ids": dealer_ids,
        }
        response = self.client.post(self.base_url + "/preferences", json=payload)
        response.raise_for_status()
        data = response.json()
        return data.get("results") or []


def backend_from_environment():
    url = os.environ.get("AXLE_API_URL", "").strip()
    if url:
        return HttpBackend(url)
    return LocalBackend()
