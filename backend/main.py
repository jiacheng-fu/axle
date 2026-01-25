import json
import os
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from pydantic import BaseModel

# set up the semantic chatbot client
load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)

DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "carData.json"))

SYSTEM_PROMPT = """
You extract structured car preferences from a single user sentence.

Output ONLY valid JSON.
Do NOT explain.
Do NOT include fields not mentioned.
Do NOT guess missing values.

Allowed keys:
- brand (array of strings)
- model (array of strings)
- min_year (number)
- max_year (number)
- max_price (number)
- max_mileage (number)
- exterior_color (string),
- body_type (string),
- seating_capacity (number),
- horsepower (number),
- interior_color (string),
- features (array of strings)

Rules:
- Normalize brands and models to proper capitalization.
- Normalize features to lowercase canonical labels.
- If nothing relevant is mentioned, output {}.

Allowed feature strings:
    "Automatic temperature control",
    "Wireless phone connectivity: Bluetooth",
    "Front dual zone A/C",
    "Auto-dimming rearview mirror",
    "Split folding rear seat",
    "Perimeter/approach lights",
    "Remote keyless entry",
    "Steering wheel mounted audio controls",
    "Rear window wiper",
    "Fully automatic headlights",
    "Power driver seat",
    "Alloy wheels",
    "Heated door mirrors",
    "Spoiler",
    "Navigation system",
    "Entertainment system",
    "Blind spot sensor: warning",
    "Distance pacing cruise control",
    "Leather upholstery",
    "Power moonroof",
    "Parking sensors: front and rear w/rear camera",
    "Headlight cleaning",
    "3rd row seats: split-bench",
    "2nd row LCD monitors: 1",
    "Memory seat",
    "Heated front seats",
    "Ventilated front seats",
    "Rear air conditioning",
    "Auto tilt-away steering wheel",
    "Adaptive suspension",
    "Auto-leveling suspension",
    "Steering wheel mounted A/C controls",
    "Heated rear seats",
    "Headphones",
    "Sun blinds",
    "Security system",
    "Steering wheel memory",
    "Power passenger seat",
    "Auto-dimming door mirrors",
    "Roof rack",
    "Trailer hitch receiver",
    "Trailer sway control",
    "Exterior parking camera rear"
"""

FEATURE_ALIASES = {
    "apple carplay": "carplay",
    "carplay": "carplay",
    "android auto": "android auto",
    "leather": "leather seats",
    "leather interior": "leather seats",
    "leather seats": "leather seats",
    "awd": "awd",
    "all wheel drive": "awd",
    "backup camera": "backup camera",
}

SCHEMA = {
    "brand": list,
    "model": list,
    "min_year": int,
    "max_year": int,
    "max_price": int,
    "max_mileage": int,
    "exterior_color": str,
    "body_type": str,
    "seating_capacity":int,
    "horsepower": int,
    "interior_color": str,
    "features": list
}

def load_listings():
    if not os.path.exists(DATA_PATH):
        print(f"[data] carData.json not found at {DATA_PATH}", flush=True)
        return []
    try:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("listings", [])
    except Exception as exc:
        print(f"[data] failed to load listings: {exc}", flush=True)
        return []

def normalize_text(value: str) -> str:
    return value.strip().lower()

def normalize_list(items):
    return [normalize_text(item) for item in items if isinstance(item, str)]

def score_listing(listing: dict, prefs: dict) -> int:
    score = 0
    vehicle = listing.get("vehicle", {})
    features_raw = listing.get("highlighted_features_raw", []) or []

    make = normalize_text(vehicle.get("make", "")) if vehicle.get("make") else ""
    model = normalize_text(vehicle.get("model", "")) if vehicle.get("model") else ""
    year = vehicle.get("year")
    price = vehicle.get("price_usd")
    mileage = vehicle.get("odometer_miles")

    pref_brands = normalize_list(prefs.get("brand", []))
    pref_models = normalize_list(prefs.get("model", []))
    pref_features = normalize_list(prefs.get("features", []))
    listing_features = normalize_list(features_raw)

    if pref_brands:
        score += 5 if make in pref_brands else -2
    if pref_models:
        score += 3 if model in pref_models else -1

    min_year = prefs.get("min_year")
    max_year = prefs.get("max_year")
    if isinstance(min_year, int) and isinstance(year, int):
        score += 2 if year >= min_year else -4
    if isinstance(max_year, int) and isinstance(year, int):
        score += 2 if year <= max_year else -4

    max_price = prefs.get("max_price")
    if isinstance(max_price, int) and isinstance(price, (int, float)):
        score += 2 if price <= max_price else -3

    max_mileage = prefs.get("max_mileage")
    if isinstance(max_mileage, int) and isinstance(mileage, (int, float)):
        score += 2 if mileage <= max_mileage else -2

    if pref_features:
        match_count = len(set(pref_features) & set(listing_features))
        score += 2 * match_count

    return score

def rank_listings(prefs: dict, limit: int = 10):
    listings = load_listings()
    scored = []
    for listing in listings:
        score = score_listing(listing, prefs)
        scored.append((score, listing))
    scored.sort(key=lambda item: item[0], reverse=True)
    top = []
    for score, listing in scored[:limit]:
        vehicle = listing.get("vehicle", {})
        image_urls = listing.get("image_urls", []) or []
        top.append({
            "year": vehicle.get("year"),
            "model": vehicle.get("model"),
            "trim": vehicle.get("trim"),
            "image_url": image_urls[0] if image_urls else None,
            "dealer_notes": listing.get("dealer_notes"),
            "score": score
        })
    return top


def extract_labels(user_text: str) -> dict:
    print(f"[extract_labels] input={user_text!r}", flush=True)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_text}
    ]

    print("[extract_labels] sending request to model...", flush=True)
    response = client.chat.completions.create(
        model="GPT-5.2",
        messages=messages,
        temperature=0
    )

    raw = response.choices[0].message.content.strip()
    print(f"[extract_labels] raw response={raw!r}", flush=True)
    data = json.loads(raw)
    print(f"[extract_labels] parsed data={data!r}", flush=True)

    cleaned = sanitize_output(data)
    print(f"[extract_labels] cleaned={cleaned!r}", flush=True)
    return cleaned

def sanitize_output(data: dict) -> dict:
    print(f"[sanitize_output] input={data!r}", flush=True)
    clean = {}

    for key, value in data.items():
        if key not in SCHEMA:
            print(f"[sanitize_output] skip unknown key={key!r}", flush=True)
            continue

        if value is None:
            print(f"[sanitize_output] skip None key={key!r}", flush=True)
            continue

        if isinstance(value, list) and len(value) == 0:
            print(f"[sanitize_output] skip empty list key={key!r}", flush=True)
            continue

        clean[key] = value

    if "features" in clean:
        print(f"[sanitize_output] normalizing features={clean['features']!r}", flush=True)
        clean["features"] = normalize_features(clean["features"])

    print(f"[sanitize_output] output={clean!r}", flush=True)
    return clean

def normalize_features(features):
    print(f"[normalize_features] input={features!r}", flush=True)
    normalized = set()

    for f in features:
        f = f.lower()
        mapped = FEATURE_ALIASES.get(f, f)
        print(f"[normalize_features] {f!r} -> {mapped!r}", flush=True)
        normalized.add(mapped)

    result = list(normalized)
    print(f"[normalize_features] output={result!r}", flush=True)
    return result

def merge_state(state: dict, update: dict) -> dict:
    print(f"[merge_state] state(before)={state!r}", flush=True)
    print(f"[merge_state] update={update!r}", flush=True)
    for key, value in update.items():
        if key in ["brand", "model"]:
            state[key] = value  # replace
        elif key == "features":
            state.setdefault("features", [])
            state["features"] = list(set(state["features"]) | set(value))
        else:
            state[key] = value  # last-write-wins

    print(f"[merge_state] state(after)={state!r}", flush=True)
    return state

app = FastAPI(title="Used Car Intelligence API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

state = {}


class PreferenceInput(BaseModel):
    text: str
    stage: Optional[str] = None
    zip: Optional[str] = None


@app.get("/")
def health():
    print("[health] ok", flush=True)
    return {"status": "ok"}


@app.post("/preferences")
def update_preferences(payload: PreferenceInput):
    global state
    print(f"[preferences] stage={payload.stage} zip={payload.zip} text={payload.text!r}", flush=True)

    if payload.stage == "zip":
        print("[preferences] resetting state for new zip", flush=True)
        state = {}
        if payload.zip:
            state["zip"] = payload.zip
        print(f"[preferences] state={state!r}", flush=True)
        return {"state": state}

    if payload.stage == "done":
        print(f"[preferences] done, state={state!r}", flush=True)
        results = rank_listings(state)
        print(f"[preferences] results_count={len(results)}", flush=True)
        return {"state": state, "results": results}

    try:
        update = extract_labels(payload.text)
    except Exception:
        print("[preferences] extract_labels failed, returning empty update", flush=True)
        update = {}

    state = merge_state(state, update)
    print(f"[preferences] state(final)={state!r}", flush=True)
    return {"state": state}
