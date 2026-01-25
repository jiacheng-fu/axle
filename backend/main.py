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
    # Connectivity & Phone
    "apple carplay": "wireless phone connectivity: bluetooth",
    "carplay": "wireless phone connectivity: bluetooth",
    "android auto": "wireless phone connectivity: bluetooth",
    "bluetooth": "wireless phone connectivity: bluetooth",
    "phone": "wireless phone connectivity: bluetooth",
    "wireless": "wireless phone connectivity: bluetooth",
    "hands free": "wireless phone connectivity: bluetooth",
    "handsfree": "wireless phone connectivity: bluetooth",

    # Seats & Interior - Leather
    "leather": "leather upholstery",
    "leather interior": "leather upholstery",
    "leather seats": "leather upholstery",
    "leather seat": "leather upholstery",

    # Seats - Heated/Cooled
    "heated seats": "heated front seats",
    "heated seat": "heated front seats",
    "seat warmers": "heated front seats",
    "warm seats": "heated front seats",
    "cooled seats": "ventilated front seats",
    "ventilated seats": "ventilated front seats",
    "air conditioned seats": "ventilated front seats",
    "ac seats": "ventilated front seats",

    # Seats - Power/Memory
    "power seats": "power driver seat",
    "power seat": "power driver seat",
    "electric seats": "power driver seat",
    "memory seats": "memory seat",
    "memory seat": "memory seat",

    # Camera & Sensors - Backup Camera
    "backup camera": "exterior parking camera rear",
    "rear camera": "exterior parking camera rear",
    "reverse camera": "exterior parking camera rear",
    "rearview camera": "exterior parking camera rear",
    "rear view camera": "exterior parking camera rear",
    "parking camera": "exterior parking camera rear",
    "camera": "exterior parking camera rear",
    "back up camera": "exterior parking camera rear",
    "rear cam": "exterior parking camera rear",

    # Blind Spot
    "blind spot": "blind spot sensor: warning",
    "blind spot monitoring": "blind spot sensor: warning",
    "blind spot monitor": "blind spot sensor: warning",
    "bsm": "blind spot sensor: warning",
    "blind spot warning": "blind spot sensor: warning",

    # Parking Sensors
    "parking sensors": "parking sensors: front and rear w/rear camera",
    "parking sensor": "parking sensors: front and rear w/rear camera",
    "park assist": "parking sensors: front and rear w/rear camera",
    "parking assist": "parking sensors: front and rear w/rear camera",

    # Roof - Sunroof/Moonroof
    "sunroof": "power moonroof",
    "moonroof": "power moonroof",
    "panoramic roof": "power moonroof",
    "panoramic sunroof": "power moonroof",
    "pano roof": "power moonroof",
    "sun roof": "power moonroof",
    "moon roof": "power moonroof",

    # Navigation & Entertainment
    "navigation": "navigation system",
    "nav": "navigation system",
    "gps": "navigation system",
    "navigation system": "navigation system",
    "maps": "navigation system",
    "entertainment": "entertainment system",
    "entertainment system": "entertainment system",

    # Climate Control
    "climate control": "automatic temperature control",
    "automatic climate": "automatic temperature control",
    "auto climate": "automatic temperature control",
    "temp control": "automatic temperature control",
    "dual zone": "front dual zone a/c",
    "dual zone ac": "front dual zone a/c",
    "dual zone climate": "front dual zone a/c",
    "rear ac": "rear air conditioning",
    "rear climate": "rear air conditioning",
    "rear air": "rear air conditioning",

    # Drivetrain
    "awd": "all wheel drive",
    "all wheel drive": "all wheel drive",
    "4wd": "four wheel drive",
    "four wheel drive": "four wheel drive",
    "fwd": "front wheel drive",
    "front wheel drive": "front wheel drive",

    # Safety & Cruise Control
    "cruise control": "distance pacing cruise control",
    "cruise": "distance pacing cruise control",
    "adaptive cruise": "distance pacing cruise control",
    "adaptive cruise control": "distance pacing cruise control",
    "acc": "distance pacing cruise control",
    "radar cruise": "distance pacing cruise control",

    # Wheels & Exterior
    "alloy wheels": "alloy wheels",
    "alloys": "alloy wheels",
    "aluminum wheels": "alloy wheels",
    "spoiler": "spoiler",
    "rear spoiler": "spoiler",
    "roof rack": "roof rack",
    "roof rails": "roof rack",

    # Keys & Entry
    "keyless entry": "remote keyless entry",
    "keyless": "remote keyless entry",
    "remote entry": "remote keyless entry",
    "remote start": "remote keyless entry",
    "push button start": "remote keyless entry",
    "push start": "remote keyless entry",

    # Seating Capacity
    "third row": "3rd row seats: split-bench",
    "3rd row": "3rd row seats: split-bench",
    "third row seats": "3rd row seats: split-bench",
    "7 seater": "3rd row seats: split-bench",
    "7 passenger": "3rd row seats: split-bench",
    "8 seater": "3rd row seats: split-bench",
    "seven seater": "3rd row seats: split-bench",

    # Mirrors
    "auto dimming mirror": "auto-dimming rearview mirror",
    "auto-dimming mirror": "auto-dimming rearview mirror",
    "dimming mirror": "auto-dimming rearview mirror",
    "heated mirrors": "heated door mirrors",
    "heated side mirrors": "heated door mirrors",

    # Lights
    "automatic headlights": "fully automatic headlights",
    "auto headlights": "fully automatic headlights",
    "auto lights": "fully automatic headlights",

    # Audio Controls
    "steering wheel controls": "steering wheel mounted audio controls",
    "wheel controls": "steering wheel mounted audio controls",

    # Towing
    "tow hitch": "trailer hitch receiver",
    "trailer hitch": "trailer hitch receiver",
    "towing": "trailer hitch receiver",
    "hitch": "trailer hitch receiver",

    # Adaptive Suspension
    "adaptive suspension": "adaptive suspension",
    "air suspension": "adaptive suspension",
}

TOYOTA_SUBSTITUTES = {
    # Sedans (by size/price tier)
    "camry": ["avalon", "corolla", "camry hybrid"],
    "corolla": ["camry", "prius", "corolla hybrid"],
    "avalon": ["camry", "es 350"],
    "prius": ["corolla hybrid", "camry hybrid", "corolla"],

    # SUVs (by size)
    "rav4": ["highlander", "4runner", "venza", "rav4 prime", "rav4 hybrid"],
    "highlander": ["4runner", "rav4", "sequoia", "venza"],
    "4runner": ["highlander", "sequoia", "tacoma"],
    "venza": ["rav4", "highlander"],
    "sequoia": ["highlander", "4runner", "tundra"],

    # Trucks
    "tacoma": ["tundra", "4runner"],
    "tundra": ["tacoma", "sequoia"],

    # Compact/Crossover
    "c-hr": ["corolla", "rav4"],
    "yaris": ["corolla", "prius"],

    # Minivans
    "sienna": ["highlander", "sequoia"],
}

# Bryan/College Station area zip codes
BRYAN_CSTAT_ZIPS = {
    "77801", "77802", "77803", "77805", "77806", "77807", "77808",  # Bryan
    "77840", "77841", "77842", "77843", "77844", "77845"             # College Station
}

DEALERSHIP_INFO = {
    "name": "College Station Toyota",
    "address": "1701 University Dr E, College Station, TX 77840",
    "phone": "(979) 764-2886",
    "hours": "Mon-Sat 9:00 AM - 8:00 PM"
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

def validate_zip(zip_code: str) -> dict:
    """Validate zip code and return nearby dealerships"""
    print(f"[validate_zip] input={zip_code!r}", flush=True)

    # Strip whitespace and validate format
    zip_clean = zip_code.strip()

    # Check if it's a 5-digit number
    if not zip_clean.isdigit() or len(zip_clean) != 5:
        print(f"[validate_zip] invalid format", flush=True)
        return {
            "valid": False,
            "error": "Please enter a valid 5-digit zip code."
        }

    # For all valid zips, return the College Station dealership
    # (In a real app, this would search multiple dealerships by distance)
    print(f"[validate_zip] valid zip, returning nearby dealerships", flush=True)

    # Calculate mock distance based on zip
    if zip_clean in BRYAN_CSTAT_ZIPS:
        distance = "2.3 miles"
    else:
        # Mock distance for other zips (just for show)
        distance = "45.7 miles"

    dealership_with_distance = DEALERSHIP_INFO.copy()
    dealership_with_distance["distance"] = distance

    return {
        "valid": True,
        "dealerships": [dealership_with_distance],  # Always return just one for demo
        "message": f"I found 1 Toyota dealership near {zip_clean}."
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

def score_listing(listing: dict, prefs: dict) -> tuple:
    """Score listing and return (score, explanation)"""
    score = 100  # Start at perfect
    reasons = []
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

    # Brand matching
    if pref_brands:
        if make in pref_brands:
            score += 20
            reasons.append(f"✓ Matches brand: {vehicle.get('make', '')}")
        else:
            score -= 15
            reasons.append(f"⚠ Different brand: {vehicle.get('make', '')} (wanted {', '.join(prefs.get('brand', []))})")

    # Model matching
    if pref_models:
        if model in pref_models:
            score += 15
            reasons.append(f"✓ Matches model: {vehicle.get('model', '')}")
        else:
            score -= 10
            reasons.append(f"⚠ Different model: {vehicle.get('model', '')} (wanted {', '.join(prefs.get('model', []))})")

    # Year range
    min_year = prefs.get("min_year")
    max_year = prefs.get("max_year")
    if isinstance(min_year, int) and isinstance(year, int):
        if year >= min_year:
            score += 5
        else:
            score -= 20
            reasons.append(f"⚠ Older than {min_year} ({year})")

    if isinstance(max_year, int) and isinstance(year, int):
        if year <= max_year:
            score += 5
        else:
            score -= 20
            reasons.append(f"⚠ Newer than {max_year} ({year})")

    if isinstance(year, int) and not reasons[-1:]:
        reasons.append(f"✓ Year: {year}")

    # Price constraint (hard constraint)
    max_price = prefs.get("max_price")
    if isinstance(max_price, int) and isinstance(price, (int, float)):
        if price <= max_price:
            # Bonus for being cheaper within budget
            savings_ratio = 1 - (price / max_price)
            bonus = int(10 * savings_ratio)
            score += bonus
            reasons.append(f"✓ Within budget: ${int(price):,} (max ${max_price:,})")
        else:
            over_budget = price - max_price
            score -= 30
            reasons.append(f"⚠ Over budget by ${int(over_budget):,} (${int(price):,} vs ${max_price:,})")

    # Mileage constraint
    max_mileage = prefs.get("max_mileage")
    if isinstance(max_mileage, int) and isinstance(mileage, (int, float)):
        if mileage <= max_mileage:
            score += 5
            reasons.append(f"✓ Mileage: {int(mileage):,} miles")
        else:
            over_miles = mileage - max_mileage
            score -= 15
            reasons.append(f"⚠ {int(over_miles):,} miles over limit ({int(mileage):,} vs {max_mileage:,})")

    # Body type constraint (SUV, Sedan, Truck, etc.)
    pref_body_type = prefs.get("body_type")
    listing_body_type = normalize_text(vehicle.get("body_style", "")) if vehicle.get("body_style") else ""
    listing_normal_body = normalize_text(vehicle.get("normal_body_style", "")) if vehicle.get("normal_body_style") else ""
    if pref_body_type:
        pref_body_normalized = normalize_text(pref_body_type)
        # Check both body_style and normal_body_style fields
        if (listing_body_type and pref_body_normalized in listing_body_type) or \
           (listing_normal_body and pref_body_normalized in listing_normal_body):
            score += 15
            body_display = vehicle.get("body_style", "") or vehicle.get("normal_body_style", "")
            reasons.append(f"✓ Matches body type: {body_display}")
        else:
            score -= 20
            body_display = vehicle.get("body_style", "") or vehicle.get("normal_body_style", "") or "Unknown"
            reasons.append(f"⚠ Different body type: {body_display} (wanted {pref_body_type})")

    # Horsepower constraint (CRITICAL - hard requirement)
    min_horsepower = prefs.get("horsepower")
    listing_horsepower = vehicle.get("horsepower_hp")  # Fixed: use correct field name
    if isinstance(min_horsepower, int) and isinstance(listing_horsepower, (int, float)):
        if listing_horsepower >= min_horsepower:
            score += 15
            reasons.append(f"✓ Horsepower: {int(listing_horsepower)}hp (meets {min_horsepower}+ requirement)")
        else:
            deficit = min_horsepower - listing_horsepower
            score -= 25
            reasons.append(f"⚠ Underpowered: {int(listing_horsepower)}hp (need {min_horsepower}+, short by {int(deficit)}hp)")
    elif isinstance(min_horsepower, int) and not listing_horsepower:
        # If horsepower is required but not listed, penalize moderately
        score -= 15
        reasons.append(f"⚠ Horsepower not listed (need {min_horsepower}+)")

    # Feature matching (normalized by requested features)
    if pref_features:
        # Exact matches
        matched_features = set(pref_features) & set(listing_features)

        # Fuzzy matches for partial word overlap (e.g., "bluetooth" in "wireless phone connectivity")
        fuzzy_matched = 0
        for pref_feature in pref_features:
            if pref_feature in matched_features:
                continue  # Already counted as exact match

            # Check if any words from pref match any listing feature
            pref_words = set(pref_feature.split())
            for listing_feature in listing_features:
                listing_words = set(listing_feature.split())
                word_overlap = len(pref_words & listing_words)

                # If 50%+ words match, count as partial match
                if word_overlap > 0 and word_overlap >= len(pref_words) * 0.5:
                    fuzzy_matched += 0.5  # Partial credit
                    break

        total_matches = len(matched_features) + fuzzy_matched
        match_ratio = total_matches / len(pref_features)
        feature_score = int(30 * match_ratio)
        score += feature_score

        exact_count = len(matched_features)
        fuzzy_count = int(fuzzy_matched)

        if exact_count > 0 and fuzzy_count > 0:
            reasons.append(f"✓ Has {exact_count} exact + {fuzzy_count} partial feature matches (out of {len(pref_features)})")
        elif exact_count > 0:
            reasons.append(f"✓ Has {exact_count}/{len(pref_features)} requested features")
        elif fuzzy_count > 0:
            reasons.append(f"⚠ Has {fuzzy_count} partial feature matches (out of {len(pref_features)})")
        else:
            reasons.append(f"⚠ Missing all {len(pref_features)} requested features")

    # Clamp score to 0-100
    final_score = max(0, min(100, score))

    return (final_score, reasons)

def expand_models_with_substitutes(prefs: dict) -> dict:
    """Expand model preferences to include Toyota substitutes"""
    expanded_prefs = prefs.copy()
    original_models = prefs.get("model", [])

    if not original_models:
        return expanded_prefs

    expanded_models = set(normalize_list(original_models))

    for model in normalize_list(original_models):
        if model in TOYOTA_SUBSTITUTES:
            expanded_models.update(normalize_list(TOYOTA_SUBSTITUTES[model]))

    expanded_prefs["model"] = list(expanded_models)
    print(f"[expand_models] {original_models} → {list(expanded_models)}", flush=True)
    return expanded_prefs

def relax_constraints(prefs: dict, level: int) -> tuple:
    """Progressively relax constraints. Returns (relaxed_prefs, relaxations_applied)"""
    relaxed = prefs.copy()
    relaxations = []

    if level >= 1:
        # Level 1: Remove half of features (keep most important)
        features = relaxed.get("features", [])
        if len(features) > 3:
            keep_count = max(3, len(features) // 2)
            relaxed["features"] = features[:keep_count]
            relaxations.append(f"Kept only {keep_count} most important features")

    if level >= 2:
        # Level 2: Increase price by 20%
        max_price = relaxed.get("max_price")
        if max_price:
            new_price = int(max_price * 1.2)
            relaxed["max_price"] = new_price
            relaxations.append(f"Increased budget to ${new_price:,}")

    if level >= 3:
        # Level 3: Expand year range by ±2 years
        if "min_year" in relaxed:
            relaxed["min_year"] -= 2
            relaxations.append(f"Expanded min year to {relaxed['min_year']}")
        if "max_year" in relaxed:
            relaxed["max_year"] += 2
            relaxations.append(f"Expanded max year to {relaxed['max_year']}")

    if level >= 4:
        # Level 4: Increase mileage by 30k
        max_mileage = relaxed.get("max_mileage")
        if max_mileage:
            new_mileage = max_mileage + 30000
            relaxed["max_mileage"] = new_mileage
            relaxations.append(f"Increased mileage limit to {new_mileage:,}")

    if level >= 5:
        # Level 5: Expand to similar Toyota models
        expanded = expand_models_with_substitutes(relaxed)
        if expanded.get("model") != relaxed.get("model"):
            relaxed = expanded
            relaxations.append("Expanded to similar Toyota models")

    if level >= 6:
        # Level 6: Remove all features
        if relaxed.get("features"):
            relaxed["features"] = []
            relaxations.append("Removed all feature requirements")

    return (relaxed, relaxations)

def rank_listings(prefs: dict, limit: int = 10):
    """Rank listings with zero-match detection and constraint relaxation"""
    listings = load_listings()
    scored = []

    for listing in listings:
        score, reasons = score_listing(listing, prefs)
        scored.append((score, reasons, listing))

    scored.sort(key=lambda item: item[0], reverse=True)

    # Zero-match detection
    GOOD_MATCH_THRESHOLD = 50
    top_score = scored[0][0] if scored else 0

    if top_score < GOOD_MATCH_THRESHOLD:
        print(f"[rank_listings] Zero matches detected (top score: {top_score}). Trying constraint relaxation...", flush=True)

        # Try progressive relaxation
        for level in range(1, 7):
            relaxed_prefs, relaxations = relax_constraints(prefs, level)
            print(f"[rank_listings] Relaxation level {level}: {relaxations}", flush=True)

            # Re-score with relaxed constraints
            scored = []
            for listing in listings:
                score, reasons = score_listing(listing, relaxed_prefs)
                scored.append((score, reasons, listing))

            scored.sort(key=lambda item: item[0], reverse=True)
            top_score = scored[0][0] if scored else 0

            if top_score >= GOOD_MATCH_THRESHOLD:
                print(f"[rank_listings] Found good matches at level {level} (score: {top_score})", flush=True)
                # Return results with relaxation info
                return format_results(scored, limit, relaxations)

        # If still no good matches, return best available with all relaxations
        print(f"[rank_listings] No good matches even after full relaxation", flush=True)
        _, final_relaxations = relax_constraints(prefs, 6)
        return format_results(scored, limit, final_relaxations)

    # Good matches found, return normally
    return format_results(scored, limit, [])

def format_results(scored, limit, relaxations):
    """Format scored listings into result objects with diversity filter"""
    top = []
    seen_models = {}
    MAX_PER_MODEL = 3

    for score, reasons, listing in scored:
        if len(top) >= limit:
            break

        vehicle = listing.get("vehicle", {})
        model = vehicle.get("model", "Unknown")

        # Diversity filter: max 3 of same model
        if seen_models.get(model, 0) >= MAX_PER_MODEL:
            continue

        seen_models[model] = seen_models.get(model, 0) + 1

        image_urls = listing.get("image_urls", []) or []
        features = listing.get("highlighted_features_raw", []) or []

        top.append({
            "year": vehicle.get("year"),
            "make": vehicle.get("make"),
            "model": model,
            "trim": vehicle.get("trim"),
            "price": vehicle.get("price_usd"),
            "mileage": vehicle.get("odometer_miles"),
            "exterior_color": vehicle.get("exterior_color"),
            "interior_color": vehicle.get("interior_color"),
            "body_style": vehicle.get("body_style"),
            "drivetrain": vehicle.get("drivetrain"),
            "horsepower": vehicle.get("horsepower_hp"),
            "engine": vehicle.get("engine_type"),
            "features": features[:5],  # Top 5 features
            "image_url": image_urls[0] if image_urls else None,
            "dealer_notes": listing.get("dealer_notes"),
            "score": score,
            "match_score_percent": score,
            "match_reasons": reasons,
            "relaxations": relaxations if relaxations else None
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

def generate_bot_response(user_text: str, current_state: dict, stage: str) -> str:
    """Generate contextual, salesman-like bot response based on user input and current state"""
    print(f"[generate_bot_response] user_text={user_text!r}, stage={stage}, state={current_state!r}", flush=True)

    # Build context about what we know so far
    context_parts = []
    if current_state.get("brand"):
        context_parts.append(f"Brand preferences: {', '.join(current_state['brand'])}")
    if current_state.get("model"):
        context_parts.append(f"Model preferences: {', '.join(current_state['model'])}")
    if current_state.get("max_price"):
        context_parts.append(f"Budget: ${current_state['max_price']:,}")
    if current_state.get("max_mileage"):
        context_parts.append(f"Max mileage: {current_state['max_mileage']:,}")
    if current_state.get("min_year") or current_state.get("max_year"):
        year_str = ""
        if current_state.get("min_year"):
            year_str += f"{current_state['min_year']}+"
        if current_state.get("max_year"):
            year_str = f"{current_state.get('min_year', 'any')}-{current_state['max_year']}"
        context_parts.append(f"Year range: {year_str}")
    if current_state.get("features"):
        features_str = ', '.join(current_state['features'][:5])
        if len(current_state['features']) > 5:
            features_str += f" (+{len(current_state['features']) - 5} more)"
        context_parts.append(f"Features: {features_str}")

    context_summary = "\n".join(context_parts) if context_parts else "No preferences captured yet"

    BOT_RESPONSE_PROMPT = f"""You are an expert Toyota car salesman having a friendly conversation with a customer.

User just said: "{user_text}"

What we know about their preferences so far:
{context_summary}

Your task:
1. Acknowledge what they just mentioned SPECIFICALLY (don't be generic)
2. If appropriate, ask 1-2 intelligent follow-up questions to understand their needs better
3. Suggest related features or considerations they might not have thought of
4. Be conversational, friendly, and helpful - like a real salesperson building rapport
5. Keep it concise (1-3 sentences)

Guidelines:
- If they mentioned a budget, acknowledge it and ask about priorities within that range
- If they mentioned features, validate their choice and suggest complementary features
- If they mentioned a model, acknowledge it and ask about specific use cases
- If they mentioned family/kids, ask about seating, safety features
- If they mentioned commute/driving, ask about fuel efficiency, comfort features
- Be genuinely helpful, not pushy

Output ONLY your response text. No preamble, no "Here's my response:", just the conversational text."""

    messages = [
        {"role": "system", "content": BOT_RESPONSE_PROMPT},
        {"role": "user", "content": "Generate the response."}
    ]

    print("[generate_bot_response] sending request to model...", flush=True)
    response = client.chat.completions.create(
        model="GPT-5.2",
        messages=messages,
        temperature=0.7  # More creative for conversational responses
    )

    bot_text = response.choices[0].message.content.strip()
    print(f"[generate_bot_response] generated response={bot_text!r}", flush=True)
    return bot_text

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
        f = f.lower().strip()

        # First try exact alias match
        if f in FEATURE_ALIASES:
            mapped = FEATURE_ALIASES[f]
            print(f"[normalize_features] exact alias: {f!r} -> {mapped!r}", flush=True)
            normalized.add(mapped)
            continue

        # Try fuzzy matching for partial word matches
        fuzzy_match = fuzzy_match_feature(f)
        if fuzzy_match:
            print(f"[normalize_features] fuzzy match: {f!r} -> {fuzzy_match!r}", flush=True)
            normalized.add(fuzzy_match)
        else:
            # Keep original if no match found
            print(f"[normalize_features] no match, keeping: {f!r}", flush=True)
            normalized.add(f)

    result = list(normalized)
    print(f"[normalize_features] output={result!r}", flush=True)
    return result

def fuzzy_match_feature(user_term: str) -> str:
    """Try to fuzzy match user input to known features using partial string matching"""
    user_words = set(user_term.lower().split())

    # Common feature patterns to match against
    FEATURE_PATTERNS = {
        "camera": "exterior parking camera rear",
        "bluetooth": "wireless phone connectivity: bluetooth",
        "leather": "leather upholstery",
        "heated": "heated front seats",
        "navigation": "navigation system",
        "moonroof": "power moonroof",
        "sunroof": "power moonroof",
        "cruise": "distance pacing cruise control",
        "blind": "blind spot sensor: warning",
        "parking": "parking sensors: front and rear w/rear camera",
        "keyless": "remote keyless entry",
        "spoiler": "spoiler",
        "alloy": "alloy wheels",
        "roof rack": "roof rack",
    }

    # Check if any pattern keyword is in the user term
    for keyword, canonical_feature in FEATURE_PATTERNS.items():
        if keyword in user_term:
            return canonical_feature

    # Check for word overlap with canonical feature names
    best_match = None
    best_score = 0

    # Check against all unique canonical features from aliases
    canonical_features = set(FEATURE_ALIASES.values())

    for canonical in canonical_features:
        canonical_words = set(canonical.lower().split())
        # Count word overlap
        overlap = len(user_words & canonical_words)

        if overlap > best_score:
            best_score = overlap
            best_match = canonical

    # Only return if we have at least 1 word overlap and user has 2+ words
    # (avoids false matches on single word inputs)
    if best_score > 0 and len(user_words) >= 2:
        return best_match

    return None

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

        # Validate zip code
        zip_validation = validate_zip(payload.text)

        if not zip_validation["valid"]:
            # Invalid zip - ask them to try again
            return {
                "state": state,
                "bot_response": zip_validation["error"],
                "error": True
            }

        # Valid zip - store it and return dealership list
        state["zip"] = payload.text.strip()

        print(f"[preferences] state={state!r}", flush=True)

        # Return dealership options for user to select
        bot_response = f"{zip_validation['message']} Please select which dealership you'd like to search inventory from."
        return {
            "state": state,
            "bot_response": bot_response,
            "dealerships": zip_validation["dealerships"]
        }

    if payload.stage == "select_dealership":
        print(f"[preferences] dealership selected", flush=True)
        # Store the selected dealership (for demo, we just store the only one)
        state["dealership"] = DEALERSHIP_INFO

        bot_response = f"Perfect! I'll search the inventory at {DEALERSHIP_INFO['name']}. Now, what kind of Toyota are you looking for? Tell me about your budget, preferred features, or any specific models you have in mind."
        return {"state": state, "bot_response": bot_response}

    if payload.stage == "done":
        print(f"[preferences] done, state={state!r}", flush=True)
        results = rank_listings(state)
        print(f"[preferences] results_count={len(results)}", flush=True)
        bot_response = f"Excellent! I've found {len(results)} great matches for you. Let me show you the best options that fit your preferences."
        return {"state": state, "results": results, "bot_response": bot_response}

    try:
        update = extract_labels(payload.text)
    except Exception:
        print("[preferences] extract_labels failed, returning empty update", flush=True)
        update = {}

    state = merge_state(state, update)
    print(f"[preferences] state(final)={state!r}", flush=True)

    # Generate contextual bot response
    try:
        bot_response = generate_bot_response(payload.text, state, payload.stage or "prefs")
    except Exception as e:
        print(f"[preferences] generate_bot_response failed: {e}, using fallback", flush=True)
        bot_response = "Got it! Is there anything else you'd like to add to help me find the perfect vehicle for you?"

    return {"state": state, "bot_response": bot_response}
