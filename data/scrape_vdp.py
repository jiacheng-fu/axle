#!/usr/bin/env python3
import json
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup, Tag
from dotenv import load_dotenv
from openai import OpenAI

MASTER_FILE = Path(__file__).parent / "carData.json"
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)
REQUEST_TIMEOUT_S = 30
SCRAPE_TIMEOUT_SECONDS = 60  # Maximum time to spend scraping a single vehicle

# Load environment variables and initialize OpenAI client for intelligent field inference
load_dotenv()
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def normalize_drivetrain(drivetrain: Optional[str]) -> Optional[str]:
    """
    Normalize drivetrain to remove hyphens and standardize capitalization.

    Examples:
        "All-Wheel Drive" -> "All Wheel Drive"
        "Rear-Wheel Drive" -> "Rear Wheel Drive"
        "Front-Wheel Drive" -> "Front Wheel Drive"
        "Four-Wheel Drive" -> "Four Wheel Drive"
    """
    if not drivetrain:
        return None

    # Remove hyphens
    normalized = drivetrain.replace("-", " ").strip()

    # Capitalize first letter of each word
    normalized = " ".join(word.capitalize() for word in normalized.split())

    return normalized


def get_html_requests(url: str) -> str:
    r = requests.get(url, headers={"User-Agent": UA}, timeout=REQUEST_TIMEOUT_S)
    r.raise_for_status()
    return r.text


def soup_from_html(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "lxml")


def extract_vdp_heading_title(soup: BeautifulSoup) -> str:
    for tag in soup.select("h1, h2"):
        t = clean(tag.get_text(" ", strip=True))
        if re.search(r"\b(19\d{2}|20\d{2})\b", t) and len(t) <= 140:
            return t
    og = soup.select_one('meta[property="og:title"]')
    if og and og.get("content"):
        return clean(og["content"])
    return clean(soup.title.get_text()) if soup.title else ""


def parse_year_make_model_trim_from_heading(
    heading: str,
) -> Tuple[Optional[int], Optional[str], Optional[str], Optional[str]]:
    h = clean(heading)
    h = re.sub(r"^(#\s*)?(pre-owned|used|certified)\s+", "", h, flags=re.IGNORECASE).strip()
    h = re.sub(
        r"\s+(front-wheel drive|rear-wheel drive|all-wheel drive|four-wheel drive)\s*$",
        "",
        h,
        flags=re.IGNORECASE,
    ).strip()

    m = re.match(r"^(19\d{2}|20\d{2})\s+(\S+)\s+(\S+)\s*(.*)$", h)
    if not m:
        return None, None, None, None

    year = int(m.group(1))
    make = m.group(2)
    model = m.group(3)
    trim = clean(m.group(4)) or None
    return year, make, model, trim


def make_listing_id(url: str, vin: Optional[str], stock_number: Optional[str], uuid: Optional[str]) -> str:
    host = urlparse(url).netloc.replace(".", "_")
    if vin:
        return f"{host}_{vin}"
    if stock_number:
        return f"{host}_{stock_number}"
    if uuid:
        return f"{host}_{uuid}"
    slug = urlparse(url).path.strip("/").split("/")[-1].replace(".htm", "")
    return f"{host}_{slug}"


def append_to_master(blob: dict) -> None:
    data: Dict[str, Any] = {"listings": []}

    if MASTER_FILE.exists():
        try:
            raw = MASTER_FILE.read_text(encoding="utf-8").strip()
            if raw:
                loaded = json.loads(raw)
                if isinstance(loaded, dict):
                    data = loaded
                    if "listings" not in data or not isinstance(data["listings"], list):
                        data["listings"] = []
                elif isinstance(loaded, list):
                    data["listings"] = loaded
        except Exception:
            data = {"listings": []}

    data["listings"] = [
        x for x in data["listings"]
        if isinstance(x, dict) and x.get("id") != blob.get("id")
    ]
    data["listings"].append(blob)
    MASTER_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


# ---------- DDC dataLayer extraction ----------

def _find_ddc_tracking_script_text(soup: BeautifulSoup) -> Optional[str]:
    node = soup.select_one("div.ddc-content.tracking-ddc-data-layer script[type='text/javascript']")
    if node:
        raw = node.get_text()
        if raw and "DDC.dataLayer" in raw and "vehicles" in raw:
            return raw

    node2 = soup.select_one("div.ddc-content.tracking-ddc-data-layer script")
    if node2:
        raw = node2.get_text()
        if raw and "DDC.dataLayer" in raw and "vehicles" in raw:
            return raw

    for s in soup.find_all("script"):
        raw = s.get_text()
        if raw and "DDC.dataLayer" in raw and (
            "DDC.dataLayer['vehicles']" in raw or 'DDC.dataLayer["vehicles"]' in raw
        ):
            return raw
    return None


def _extract_balanced(text: str, start_idx: int) -> Optional[str]:
    if not (0 <= start_idx < len(text)):
        return None
    opener = text[start_idx]
    if opener not in "[{":
        return None
    closer = "]" if opener == "[" else "}"

    depth = 0
    in_str = False
    esc = False
    quote = ""

    for i in range(start_idx, len(text)):
        ch = text[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == quote:
                in_str = False
        else:
            if ch in ("'", '"'):
                in_str = True
                quote = ch
            elif ch == opener:
                depth += 1
            elif ch == closer:
                depth -= 1
                if depth == 0:
                    return text[start_idx:i + 1]
    return None


def _js_objectish_to_jsonish(s: str) -> str:
    s = s.strip()
    s = re.sub(r",\s*([}\]])", r"\1", s)
    s = s.replace(r"\-", "-")
    s = re.sub(r'\\(?!["\\/bfnrtu])', "", s)
    return s


def extract_ddc_vehicle(soup: BeautifulSoup) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    raw = _find_ddc_tracking_script_text(soup)
    if not raw:
        return None, "ddc_script_not_found"

    m = re.search(r"DDC\.dataLayer\[\s*['\"]vehicles['\"]\s*\]\s*=\s*\[", raw)
    if not m:
        return None, "vehicles_assignment_not_found"

    start = m.end() - 1
    payload = _extract_balanced(raw, start)
    if not payload:
        return None, "vehicles_payload_not_extracted"

    jsonish = _js_objectish_to_jsonish(payload)

    try:
        vehicles = json.loads(jsonish)
    except Exception as e:
        Path("debug_vehicles_payload.txt").write_text(jsonish, encoding="utf-8")
        return None, f"json_load_failed: {type(e).__name__}: {e}"

    if not isinstance(vehicles, list) or not vehicles or not isinstance(vehicles[0], dict):
        return None, "vehicles_payload_not_list_or_empty"

    return vehicles[0], None


def features_from_ddc(vehicle: Dict[str, Any]) -> List[str]:
    feats: List[str] = []
    for f in (vehicle.get("features") or []):
        if not isinstance(f, dict):
            continue
        desc = clean(str(f.get("description") or ""))
        detail = clean(str(f.get("detail") or ""))
        if not desc:
            continue
        feats.append(f"{desc}: {detail}" if detail else desc)

    seen = set()
    out: List[str] = []
    for x in feats:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def images_from_ddc(vehicle: Dict[str, Any]) -> List[str]:
    urls: List[str] = []
    for img in (vehicle.get("images") or []):
        if isinstance(img, dict):
            uri = img.get("uri")
            if isinstance(uri, str) and uri:
                urls.append(uri)
    seen = set()
    out: List[str] = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


def images_from_dom(soup: BeautifulSoup) -> List[str]:
    urls = set()
    for img in soup.select("img"):
        for attr in ("src", "data-src", "data-lazy", "data-original", "srcset"):
            val = img.get(attr)
            if not val:
                continue
            for token in str(val).split(","):
                u = token.strip().split(" ")[0]
                if "pictures.dealer.com" in u:
                    urls.add(u)
    return sorted(urls)


# ---------- Dealer Notes + spec sections from visible DOM ----------

SECTION_TITLES = [
    "Detailed Specifications",
    "Convenience Features",
    "Suspension/Handling",
    "Entertainment Features",
    "Seats and Trim",
    "Powertrain",
    "Body Exterior",
    "Specs and Dimensions",
    "Lighting, Visibility and Instrumentation",
    "Safety and Security",
]


def _collect_bullets_in(container: Tag) -> List[str]:
    items: List[str] = []

    for li in container.select("li"):
        t = clean(li.get_text(" ", strip=True))
        if t:
            items.append(t)

    dts = container.select("dt")
    dds = container.select("dd")
    if dts and dds and len(dts) == len(dds):
        for dt, dd in zip(dts, dds):
            k = clean(dt.get_text(" ", strip=True))
            v = clean(dd.get_text(" ", strip=True))
            if k or v:
                items.append(f"{k}: {v}" if k else v)

    if not items:
        txt = clean(container.get_text("\n", strip=True))
        for line in [clean(x) for x in txt.split("\n")]:
            if line:
                items.append(line)

    seen = set()
    out = []
    for x in items:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def find_dealer_notes(soup: BeautifulSoup) -> Optional[str]:
    candidates = [
        "#dealer-notes",
        "[data-qa='dealer-notes']",
        ".dealer-notes",
        "#ws-dealernotes",
        "ws-dealernotes",
    ]
    for sel in candidates:
        node = soup.select_one(sel)
        if node:
            t = clean(node.get_text(" ", strip=True))
            if t and len(t) > 20:
                return t

    for tag in soup.find_all(["h2", "h3", "h4"]):
        if clean(tag.get_text()).lower() == "dealer notes":
            nxt = tag.find_next()
            if nxt:
                t = clean(nxt.get_text(" ", strip=True))
                if t and len(t) > 20:
                    return t
    return None


def scrape_sections_by_titles(soup: BeautifulSoup) -> Dict[str, List[str]]:
    out: Dict[str, List[str]] = {}

    headings: List[Tuple[str, Tag]] = []
    for tag in soup.find_all(["h2", "h3", "h4", "button"]):
        txt = clean(tag.get_text(" ", strip=True))
        for title in SECTION_TITLES:
            if txt.lower() == title.lower():
                headings.append((title, tag))
                break

    for title, head in headings:
        panel = None
        aria = head.get("aria-controls")
        if aria:
            panel = soup.find(id=aria)

        if panel is None:
            panel = head.find_parent(["section", "div"]) or head.find_next(["section", "div"])

        if panel is None:
            continue

        items = _collect_bullets_in(panel)

        filtered = []
        for x in items:
            if len(x) < 2:
                continue
            if re.search(r"^\(?\d{3}\)?\s*\d{3}-\d{4}$", x):
                continue
            filtered.append(x)

        if filtered:
            out[title] = filtered

    return out


def prune_spec_sections(spec_sections: Dict[str, Any]) -> Dict[str, List[str]]:
    pruned: Dict[str, List[str]] = {}
    for title, val in (spec_sections or {}).items():
        if not isinstance(val, list):
            continue
        norm = [clean(str(x)) for x in val if clean(str(x))]
        if not norm:
            continue
        only_titles = all(x.lower() == clean(title).lower() for x in norm)
        if only_titles:
            continue
        pruned[title] = norm
    return pruned


def parse_hp_torque_from_spec_lines(lines: List[str]) -> Tuple[Optional[int], Optional[int]]:
    hp = None
    tq = None
    for line in lines or []:
        s = clean(line)

        if hp is None and re.search(r"\bhorsepower\b", s, re.IGNORECASE):
            m = re.search(r"(\d{2,4})\s*hp\b", s, re.IGNORECASE)
            if m:
                hp = int(m.group(1))

        if tq is None and re.search(r"\btorque\b", s, re.IGNORECASE):
            m = re.search(r"(\d{2,4})\s*(lb\.?-?\s*ft|lb\s*ft|lb-ft|lb\.-ft\.)", s, re.IGNORECASE)
            if m:
                tq = int(m.group(1))

        if hp is not None and tq is not None:
            break
    return hp, tq


def extract_seating_capacity_from_vehicle_ddc(ddc_vehicle: Dict[str, Any]) -> Optional[int]:
    """
    Best-case: Dealer.com sometimes exposes a direct "maxSeatingCapacity"/"seatingCapacity" field.
    Otherwise, return None and we fall back to parsing spec lines.
    """
    if not isinstance(ddc_vehicle, dict):
        return None

    # Common-ish key guesses across Dealer.com payloads
    for k in ("maxSeatingCapacity", "seatingCapacity", "seats", "seatCount"):
        v = ddc_vehicle.get(k)
        if v is None:
            continue
        m = re.search(r"\d+", str(v))
        if m:
            n = int(m.group(0))
            if 1 <= n <= 20:
                return n
    return None


def parse_seating_capacity_from_spec_lines(lines: List[str]) -> Optional[int]:
    """
    Parse lines like:
      - "Max seating capacity: 5"
      - "Seating capacity: 7"
      - "Max seating capacity: 7 passengers"
    """
    for line in lines or []:
        s = clean(line)

        if re.search(r"\b(max\s+seating\s+capacity|seating\s+capacity)\b", s, re.IGNORECASE):
            m = re.search(r"(\d{1,2})", s)
            if m:
                n = int(m.group(1))
                if 1 <= n <= 20:
                    return n
    return None


def normalize_color_with_llm(
    technical_color: Optional[str],
    make: Optional[str] = None,
    model: Optional[str] = None,
    year: Optional[int] = None
) -> Optional[str]:
    """
    Use LLM to normalize technical/factory color names to common color names.

    Args:
        technical_color: The factory technical color name (e.g., "Blizzard Pearl", "Midnight Black Metallic")
        make: Vehicle make for context (e.g., "Toyota")
        model: Vehicle model for context (e.g., "Sequoia")
        year: Vehicle year for context (e.g., 2013)

    Returns:
        Common color name (e.g., "White", "Black", "Silver") or None if input is None/empty
    """
    if not technical_color:
        return None

    # Build context string
    context_parts = []
    if year:
        context_parts.append(str(year))
    if make:
        context_parts.append(make)
    if model:
        context_parts.append(model)

    context = " ".join(context_parts) if context_parts else "vehicle"

    prompt = f"""Given this factory/technical color name for a {context}: "{technical_color}"

What is the actual common color that people would use when searching for this car?

Respond with ONLY ONE of these standard colors (nothing else):
- White
- Black
- Silver
- Gray
- Blue
- Red
- Green
- Brown
- Orange
- Yellow
- Purple
- Gold
- Tan
- Beige

Just output the color name, nothing else."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=10
        )

        normalized = response.choices[0].message.content.strip()
        print(f"[normalize_color_with_llm] '{technical_color}' ({context}) → '{normalized}'", flush=True)
        return normalized
    except Exception as e:
        print(f"[normalize_color_with_llm] Error: {e}, returning original: '{technical_color}'", flush=True)
        return technical_color


def infer_missing_field_with_llm(
    field_name: str,
    vehicle_context: Dict[str, Any],
    url: str
) -> Optional[Any]:
    """
    Use LLM to intelligently infer a missing vehicle field based on available context.

    Args:
        field_name: The name of the missing field (e.g., "body_style", "seating_capacity")
        vehicle_context: Dict with available vehicle info (make, model, year, trim, etc.)
        url: Source URL for additional context

    Returns:
        Inferred value for the field, or None if unable to infer
    """
    # Build context string from available info
    context_parts = []
    for key in ["year", "make", "model", "trim"]:
        if vehicle_context.get(key):
            context_parts.append(str(vehicle_context[key]))

    context = " ".join(context_parts) if context_parts else "unknown vehicle"

    # Field-specific prompts
    if field_name == "body_style":
        prompt = f"""What is the body style of this vehicle: {context}?

Respond with ONLY ONE of these body styles (nothing else):
- Sedan
- SUV
- Truck
- Coupe
- Convertible
- Hatchback
- Wagon
- Van
- Minivan

Just output the body style, nothing else."""
        expected_type = str

    elif field_name == "seating_capacity":
        prompt = f"""What is the typical seating capacity (number of seats) for this vehicle: {context}?

Respond with ONLY the number (e.g., 5, 7, 8), nothing else."""
        expected_type = int

    elif field_name == "year":
        prompt = f"""Based on this vehicle URL: {url}

What year is this vehicle? Extract the year from the URL or context.

Respond with ONLY the 4-digit year (e.g., 2020), nothing else."""
        expected_type = int

    elif field_name == "make":
        prompt = f"""Based on this vehicle URL: {url}

What is the make/brand of this vehicle?

Respond with ONLY the make name (e.g., Toyota, Honda, Ford), nothing else."""
        expected_type = str

    elif field_name == "model":
        prompt = f"""Based on this vehicle context: {context}
URL: {url}

What is the model of this vehicle?

Respond with ONLY the model name (e.g., Camry, Accord, F-150), nothing else."""
        expected_type = str

    else:
        print(f"[infer_missing_field_with_llm] No LLM prompt defined for field: {field_name}", flush=True)
        return None

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=20
        )

        result_str = response.choices[0].message.content.strip()

        # Convert to expected type
        if expected_type == int:
            result = int(result_str)
        else:
            result = result_str

        print(f"[infer_missing_field_with_llm] {field_name} for '{context}' → '{result}'", flush=True)
        return result

    except Exception as e:
        print(f"[infer_missing_field_with_llm] Error inferring {field_name}: {e}", flush=True)
        return None


def scrape_vdp(url: str) -> dict:
    html = get_html_requests(url)
    soup = soup_from_html(html)

    ddc_vehicle, ddc_err = extract_ddc_vehicle(soup)

    page_text = clean(soup.get_text(" ", strip=True))
    heading = extract_vdp_heading_title(soup)
    year, make, model, trim = parse_year_make_model_trim_from_heading(heading)

    vin_match = re.search(r"\b[A-HJ-NPR-Z0-9]{17}\b", page_text)
    vin = vin_match.group(0) if vin_match else None

    stock = None
    price_usd = None
    odometer_miles = None
    exterior_color = None
    interior_color = None
    highlighted_features: List[str] = []
    image_urls: List[str] = []
    vehicle_uuid: Optional[str] = None

    # Body style must be present
    body_style: Optional[str] = None
    normal_body_style: Optional[str] = None

    # NEW: seating capacity (must be present)
    seating_capacity: Optional[int] = None

    drivetrain: Optional[str] = None
    drive_type: Optional[str] = None
    transmission: Optional[str] = None
    engine_type: Optional[str] = None
    engine_size: Optional[str] = None
    horsepower_hp: Optional[int] = None
    torque_lbft: Optional[int] = None

    if ddc_vehicle:
        if not vin and isinstance(ddc_vehicle.get("vin"), str):
            vin = clean(ddc_vehicle["vin"]) or vin
        if isinstance(ddc_vehicle.get("uuid"), str):
            vehicle_uuid = clean(ddc_vehicle["uuid"]) or None

        asking = ddc_vehicle.get("askingPrice") or ddc_vehicle.get("internetPrice") or ddc_vehicle.get("salePrice")
        if asking is not None:
            try:
                price_usd = int(float(str(asking).replace(",", "").strip()))
            except Exception:
                price_usd = None

        # Extract raw colors (will normalize later with vehicle context)
        raw_exterior = clean(ddc_vehicle.get("exteriorColor")) if isinstance(ddc_vehicle.get("exteriorColor"), str) else None
        raw_interior = clean(ddc_vehicle.get("interiorColor")) if isinstance(ddc_vehicle.get("interiorColor"), str) else None
        exterior_color = raw_exterior
        interior_color = raw_interior

        odo = ddc_vehicle.get("odometer") or ddc_vehicle.get("mileage") or ddc_vehicle.get("odometerReading")
        if odo is not None:
            try:
                odometer_miles = int(float(str(odo).replace(",", "").strip()))
            except Exception:
                odometer_miles = None

        stock = ddc_vehicle.get("stockNumber") or ddc_vehicle.get("stock")
        if isinstance(stock, (int, float)):
            stock = str(stock)
        stock = clean(stock) if isinstance(stock, str) and clean(stock) else None

        if not make and isinstance(ddc_vehicle.get("make"), str):
            make = clean(ddc_vehicle["make"])
        if not model and isinstance(ddc_vehicle.get("model"), str):
            model = clean(ddc_vehicle["model"])
        if not trim and isinstance(ddc_vehicle.get("trim"), str):
            trim = clean(ddc_vehicle["trim"])
        if not year:
            y = ddc_vehicle.get("modelYear") or ddc_vehicle.get("year")
            try:
                year = int(str(y).strip()) if y is not None else year
            except Exception:
                pass

        if isinstance(ddc_vehicle.get("bodyStyle"), str):
            body_style = clean(ddc_vehicle.get("bodyStyle"))
        if isinstance(ddc_vehicle.get("normalBodyStyle"), str):
            normal_body_style = clean(ddc_vehicle.get("normalBodyStyle"))

        # Try seating directly from DDC if present (varies by site)
        seating_capacity = extract_seating_capacity_from_vehicle_ddc(ddc_vehicle)

        drivetrain = clean(ddc_vehicle.get("driveLine")) if isinstance(ddc_vehicle.get("driveLine"), str) else None
        drive_type = clean(ddc_vehicle.get("driveType")) if isinstance(ddc_vehicle.get("driveType"), str) else None
        transmission = clean(ddc_vehicle.get("transmission")) if isinstance(ddc_vehicle.get("transmission"), str) else None
        engine_type = clean(ddc_vehicle.get("engine")) if isinstance(ddc_vehicle.get("engine"), str) else None
        engine_size = clean(ddc_vehicle.get("engineSize")) if isinstance(ddc_vehicle.get("engineSize"), str) else None

        def _parse_intish(v) -> Optional[int]:
            if v is None:
                return None
            m = re.search(r"(-?\d+)", str(v))
            return int(m.group(1)) if m else None

        horsepower_hp = _parse_intish(ddc_vehicle.get("horsepower"))
        torque_lbft = _parse_intish(ddc_vehicle.get("torque"))

        highlighted_features = features_from_ddc(ddc_vehicle)
        image_urls = images_from_ddc(ddc_vehicle)

    if odometer_miles is None:
        m = re.search(r"([\d,]+)\s*miles\b", page_text, re.IGNORECASE)
        if m:
            odometer_miles = int(m.group(1).replace(",", ""))

    if not image_urls:
        image_urls = images_from_dom(soup)

    dealer_notes = find_dealer_notes(soup)
    spec_sections_raw = scrape_sections_by_titles(soup)
    spec_sections = prune_spec_sections(spec_sections_raw)

    # Fill hp/torque from Detailed Specifications if missing
    if (horsepower_hp is None or torque_lbft is None):
        ds_lines = spec_sections.get("Detailed Specifications", [])
        hp2, tq2 = parse_hp_torque_from_spec_lines(ds_lines)
        if horsepower_hp is None:
            horsepower_hp = hp2
        if torque_lbft is None:
            torque_lbft = tq2

    # Fill seating capacity from Detailed Specifications if missing
    if seating_capacity is None:
        ds_lines = spec_sections.get("Detailed Specifications", [])
        seating_capacity = parse_seating_capacity_from_spec_lines(ds_lines)

    # Build vehicle context for LLM inference
    vehicle_context = {
        "year": year,
        "make": make,
        "model": model,
        "trim": trim,
        "vin": vin
    }

    # Use LLM to infer missing critical fields
    if year is None:
        print("\n⚠️  WARNING: year was not found in DDC payload or page heading. Using LLM to infer...", flush=True)
        year = infer_missing_field_with_llm("year", vehicle_context, url)
        vehicle_context["year"] = year

    if not make:
        print("\n⚠️  WARNING: make was not found in DDC payload or page heading. Using LLM to infer...", flush=True)
        make = infer_missing_field_with_llm("make", vehicle_context, url)
        vehicle_context["make"] = make

    if not model:
        print("\n⚠️  WARNING: model was not found in DDC payload or page heading. Using LLM to infer...", flush=True)
        model = infer_missing_field_with_llm("model", vehicle_context, url)
        vehicle_context["model"] = model

    if not body_style:
        if normal_body_style:
            body_style = normal_body_style
        else:
            print("\n⚠️  WARNING: body_style was not found in DDC payload. Using LLM to infer...", flush=True)
            body_style = infer_missing_field_with_llm("body_style", vehicle_context, url)

    if seating_capacity is None:
        print("\n⚠️  WARNING: seating_capacity was not found in DDC payload or spec sections. Using LLM to infer...", flush=True)
        seating_capacity = infer_missing_field_with_llm("seating_capacity", vehicle_context, url)

    # Normalize colors using LLM with vehicle context
    if exterior_color:
        exterior_color = normalize_color_with_llm(exterior_color, make, model, year)
    if interior_color:
        interior_color = normalize_color_with_llm(interior_color, make, model, year)

    # Normalize drivetrain to remove hyphens and standardize capitalization
    drivetrain = normalize_drivetrain(drivetrain)

    # Final validation - if critical fields are still None after LLM, raise error
    if year is None:
        raise ValueError("Could not determine vehicle year from scraping or LLM inference")
    if not make:
        raise ValueError("Could not determine vehicle make from scraping or LLM inference")
    if not model:
        raise ValueError("Could not determine vehicle model from scraping or LLM inference")
    if not body_style:
        raise ValueError("Could not determine vehicle body_style from scraping or LLM inference")
    if seating_capacity is None:
        raise ValueError("Could not determine seating_capacity from scraping or LLM inference")

    # Price and mileage can be optional for now (user can filter them out later)
    # But log warnings if missing
    if price_usd is None:
        print(f"\n⚠️  WARNING: price_usd is None for {year} {make} {model} - listing may be incomplete", flush=True)
    if odometer_miles is None:
        print(f"\n⚠️  WARNING: odometer_miles is None for {year} {make} {model} - listing may be incomplete", flush=True)

    listing_id = make_listing_id(url, vin, stock, vehicle_uuid)

    return {
        "id": listing_id,
        "source_url": url,
        "scraped_at": int(time.time()),
        "vehicle": {
            "year": year,
            "make": make,
            "model": model,
            "body_style": body_style,
            "normal_body_style": normal_body_style,
            "seating_capacity": seating_capacity,
            "trim": trim,
            "vin": vin,
            "stock_number": stock,
            "price_usd": price_usd,
            "odometer_miles": odometer_miles,
            "exterior_color": exterior_color,
            "interior_color": interior_color,
            "drivetrain": drivetrain,
            "drive_type": drive_type,
            "transmission": transmission,
            "engine_type": engine_type,
            "engine_size": engine_size,
            "horsepower_hp": horsepower_hp,
            "torque_lbft": torque_lbft,
        },
        "highlighted_features_raw": highlighted_features,
        "image_urls": image_urls,
        "dealer_notes": dealer_notes,
        "spec_sections": spec_sections,
    }


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python scrape_vdp.py <vehicle_detail_url_or_file>")
        print("Examples:")
        print("  python scrape_vdp.py https://www.example.com/used/vehicle.htm")
        print("  python scrape_vdp.py vdp_urls.txt")
        raise SystemExit(1)

    arg = sys.argv[1]

    # Check if argument is a file or URL
    is_file = Path(arg).exists() and Path(arg).is_file()

    if is_file:
        # Batch mode: read URLs from file
        print(f"[BATCH MODE] Reading URLs from {arg}", flush=True)
        urls_file = Path(arg)

        with urls_file.open("r", encoding="utf-8") as f:
            urls = [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]

        total = len(urls)
        print(f"[BATCH MODE] Found {total} URLs to scrape\n", flush=True)

        success_count = 0
        error_count = 0

        for idx, url in enumerate(urls, 1):
            print(f"\n{'='*80}", flush=True)
            print(f"[{idx}/{total}] Processing: {url}", flush=True)
            print(f"{'='*80}\n", flush=True)

            try:
                # Use ThreadPoolExecutor to enforce timeout
                with ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(scrape_vdp, url)
                    try:
                        blob = future.result(timeout=SCRAPE_TIMEOUT_SECONDS)
                        append_to_master(blob)

                        print(
                            f"\n[{idx}/{total}] SUCCESS: Appended {blob['id']} to {MASTER_FILE.name} | "
                            f"highlights={len(blob.get('highlighted_features_raw', []))} | "
                            f"sections={len(blob.get('spec_sections', {}))} | "
                            f"dealer_notes={bool(blob.get('dealer_notes'))} | "
                            f"hp={blob.get('vehicle', {}).get('horsepower_hp')} "
                            f"tq={blob.get('vehicle', {}).get('torque_lbft')} | "
                            f"body_style={blob.get('vehicle', {}).get('body_style')} | "
                            f"seats={blob.get('vehicle', {}).get('seating_capacity')}",
                            flush=True
                        )
                        success_count += 1

                    except FuturesTimeoutError:
                        print(f"\n[{idx}/{total}] TIMEOUT: Scraping exceeded {SCRAPE_TIMEOUT_SECONDS} seconds - skipping this vehicle", flush=True)
                        error_count += 1
                        # Continue to next URL

            except Exception as e:
                print(f"\n[{idx}/{total}] ERROR: Failed to scrape {url}", flush=True)
                print(f"Error details: {str(e)}", flush=True)
                error_count += 1
                # Continue to next URL instead of stopping

        # Print summary
        print(f"\n{'='*80}", flush=True)
        print(f"BATCH COMPLETE", flush=True)
        print(f"{'='*80}", flush=True)
        print(f"Total URLs: {total}", flush=True)
        print(f"Successful: {success_count}", flush=True)
        print(f"Failed: {error_count}", flush=True)
        print(f"Output file: {MASTER_FILE}", flush=True)

    else:
        # Single URL mode
        url = arg
        print(f"[SINGLE MODE] Scraping: {url}\n", flush=True)

        blob = scrape_vdp(url)
        append_to_master(blob)

        print(
            f"\nAppended {blob['id']} to {MASTER_FILE.name} | "
            f"highlights={len(blob.get('highlighted_features_raw', []))} | "
            f"sections={len(blob.get('spec_sections', {}))} | "
            f"dealer_notes={bool(blob.get('dealer_notes'))} | "
            f"hp={blob.get('vehicle', {}).get('horsepower_hp')} "
            f"tq={blob.get('vehicle', {}).get('torque_lbft')} | "
            f"body_style={blob.get('vehicle', {}).get('body_style')} | "
            f"seats={blob.get('vehicle', {}).get('seating_capacity')}"
        )
