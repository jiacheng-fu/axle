import json
import os
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from pydantic import BaseModel

from repository import get_listings

# set up the semantic chatbot client
load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)

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
- min_price (number)
- max_price (number)
- max_mileage (number)
- exterior_color (array of strings OR single string) - use array if user mentions multiple colors like "red or silver"
- body_type (array of strings OR single string) - use array if user mentions multiple types like "truck or SUV"
- seating_capacity (number)
- horsepower (number)
- interior_color (array of strings OR single string) - use array if user mentions multiple colors
- drivetrain (string) - values: "AWD", "4WD", "FWD", "RWD", "All Wheel Drive", "Four Wheel Drive", "Front Wheel Drive", "Rear Wheel Drive"
- features (array of strings)
- payment_method (string) - values: "cash" or "finance"
- down_payment (number) - dollars, only if financing
- loan_term_months (number) - typically 36, 48, 60, or 72, only if financing
- credit_score (number) - 300-850, only if financing
- max_monthly_payment (number) - dollars, only if user specifies a strict monthly limit

Rules:
- Normalize brands and models to proper capitalization.
- Normalize features to lowercase canonical labels.
- If nothing relevant is mentioned, output {}.
- When user mentions multiple options for the same parameter, use an array:
  * "red or silver" → exterior_color: ["red", "silver"]
  * "truck or SUV" → body_type: ["truck", "SUV"]
  * "sedan, coupe, or hatchback" → body_type: ["sedan", "coupe", "hatchback"]
- IMPORTANT: Expand abstract/vague terms into concrete features:
  * "premium interior" → ["leather upholstery", "heated front seats", "power driver seat", "navigation system"]
  * "luxury features" → ["leather upholstery", "heated front seats", "ventilated front seats", "power moonroof", "navigation system", "memory seat"]
  * "tech features" → ["navigation system", "wireless phone connectivity: bluetooth", "blind spot sensor: warning", "parking sensors: front and rear w/rear camera"]
  * "safety features" → ["blind spot sensor: warning", "parking sensors: front and rear w/rear camera", "distance pacing cruise control", "exterior parking camera rear"]
  * "comfort features" → ["heated front seats", "automatic temperature control", "power driver seat", "leather upholstery"]
  * "family friendly" → ["3rd row seats: split-bench", "rear air conditioning", "entertainment system"]
  * "off-road" / "adventure" → set drivetrain to "AWD" or "4WD" AND add features: ["roof rack", "trailer hitch receiver"]
  * "sporty" / "performance" → set higher horsepower requirement AND add features: ["spoiler", "alloy wheels"]

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

# Bryan/College Station area zip codes
BRYAN_CSTAT_ZIPS = {
    "77801", "77802", "77803", "77805", "77806", "77807", "77808",  # Bryan
    "77840", "77841", "77842", "77843", "77844", "77845"             # College Station
}

# TODO(Phase 3/4): replace this single hardcoded dealership with real
# zip-based dealer discovery (Google Places) + per-dealer inventory.
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
    "min_price": int,
    "max_price": int,
    "max_mileage": int,
    "exterior_color": (str, list),  # Can be string or list
    "body_type": (str, list),       # Can be string or list
    "seating_capacity": int,
    "horsepower": int,
    "interior_color": (str, list),  # Can be string or list
    "drivetrain": str,
    "features": list,
    "payment_method": str,  # "cash" or "finance"
    "down_payment": int,  # dollars
    "loan_term_months": int,  # typically 36, 48, 60, 72
    "credit_score": int,  # 300-850
    "max_monthly_payment": int  # dollars
}

def estimate_apr(credit_score: int) -> float:
    """Estimate APR based on credit score"""
    if credit_score >= 750:
        return 0.045  # 4.5% for excellent credit
    elif credit_score >= 700:
        return 0.065  # 6.5% for good credit
    elif credit_score >= 650:
        return 0.10   # 10% for fair credit
    elif credit_score >= 600:
        return 0.15   # 15% for poor credit
    else:
        return 0.215  # 21.5% for bad credit


def calculate_monthly_payment(price: float, down_payment: float, apr: float, term_months: int) -> float:
    """
    Calculate monthly payment using standard loan formula.
    M = P[r(1+r)^n]/[(1+r)^n-1]

    Where:
    - M = monthly payment
    - P = principal (car price - down payment)
    - r = monthly interest rate (APR/12)
    - n = number of months
    """
    if term_months <= 0 or price <= down_payment:
        return 0

    principal = price - down_payment

    if apr == 0:
        # 0% APR (special financing)
        return principal / term_months

    monthly_rate = apr / 12
    numerator = principal * monthly_rate * ((1 + monthly_rate) ** term_months)
    denominator = ((1 + monthly_rate) ** term_months) - 1

    return numerator / denominator


def calculate_max_affordable_price(monthly_payment: float, down_payment: float, apr: float, term_months: int) -> float:
    """
    Calculate maximum affordable vehicle price given a monthly payment limit.
    Works backwards from the loan payment formula.

    P = M * [(1+r)^n-1] / [r(1+r)^n]

    Then add down payment to get total price.
    """
    if term_months <= 0 or monthly_payment <= 0:
        return down_payment

    if apr == 0:
        # 0% APR
        principal = monthly_payment * term_months
        return principal + down_payment

    monthly_rate = apr / 12
    denominator = monthly_rate * ((1 + monthly_rate) ** term_months)
    numerator = ((1 + monthly_rate) ** term_months) - 1

    principal = monthly_payment * (numerator / denominator)

    return principal + down_payment


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
        "message": f"I found 1 dealership near {zip_clean}."
    }

def load_listings():
    # Inventory data-access seam — static JSON today, Supabase in Phase 3.
    # Callers don't change when the source does; see backend/repository.py.
    return get_listings()

def normalize_text(value: str) -> str:
    return value.strip().lower()

def normalize_list(items):
    return [normalize_text(item) for item in items if isinstance(item, str)]

def score_listing(listing: dict, prefs: dict) -> tuple:
    """Score listing and return (score, explanation)"""
    score = 0  # Start at 0, earn points for matches
    reasons = []
    vehicle = listing.get("vehicle", {})
    features_raw = listing.get("highlighted_features_raw", []) or []

    make = normalize_text(vehicle.get("make", "")) if vehicle.get("make") else ""
    model = normalize_text(vehicle.get("model", "")) if vehicle.get("model") else ""
    year = vehicle.get("year")
    price = vehicle.get("price_usd")
    mileage = vehicle.get("odometer_miles")
    exterior_color = normalize_text(vehicle.get("exterior_color", "")) if vehicle.get("exterior_color") else ""
    interior_color = normalize_text(vehicle.get("interior_color", "")) if vehicle.get("interior_color") else ""

    pref_brands = normalize_list(prefs.get("brand", []))
    pref_models = normalize_list(prefs.get("model", []))
    pref_features = normalize_list(prefs.get("features", []))
    listing_features = normalize_list(features_raw)

    # Brand matching (CRITICAL - required field)
    if pref_brands:
        if make in pref_brands:
            score += 25
            reasons.append(f"✓ Matches brand: {vehicle.get('make', '')}")
        else:
            score -= 40  # Heavy penalty for wrong brand
            reasons.append(f"⚠ Different brand: {vehicle.get('make', '')} (wanted {', '.join(prefs.get('brand', []))})")
    else:
        # No brand preference, give small bonus
        score += 5

    # Model matching (CRITICAL - required field)
    if pref_models:
        if model in pref_models:
            score += 25
            reasons.append(f"✓ Matches model: {vehicle.get('model', '')}")
        else:
            score -= 35  # Heavy penalty for wrong model
            reasons.append(f"⚠ Different model: {vehicle.get('model', '')} (wanted {', '.join(prefs.get('model', []))})")
    else:
        # No model preference, give small bonus
        score += 5

    # Year range (IMPORTANT)
    min_year = prefs.get("min_year")
    max_year = prefs.get("max_year")
    has_year_constraint = isinstance(min_year, int) or isinstance(max_year, int)

    if isinstance(min_year, int) and isinstance(year, int):
        if year >= min_year:
            score += 10
        else:
            score -= 30  # Stricter penalty for being too old
            reasons.append(f"⚠ Older than {min_year} ({year})")

    if isinstance(max_year, int) and isinstance(year, int):
        if year <= max_year:
            score += 10
        else:
            score -= 30  # Stricter penalty for being too new
            reasons.append(f"⚠ Newer than {max_year} ({year})")

    if isinstance(year, int) and has_year_constraint and not any("Year" in r or str(year) in r for r in reasons):
        reasons.append(f"✓ Year: {year}")
    elif isinstance(year, int) and not has_year_constraint:
        score += 3
        reasons.append(f"✓ Year: {year}")

    # Price constraint (CRITICAL - hard constraint)
    min_price = prefs.get("min_price")
    max_price = prefs.get("max_price")

    # Check minimum price first
    if isinstance(min_price, int) and isinstance(price, (int, float)):
        if price < min_price:
            under_minimum = min_price - price
            score -= 50  # CRITICAL penalty for below minimum
            reasons.append(f"⚠ Below minimum price by ${int(under_minimum):,} (${int(price):,} vs min ${min_price:,})")

    # Check maximum price
    if isinstance(max_price, int) and isinstance(price, (int, float)):
        if price <= max_price:
            # Bonus for being cheaper within budget
            savings_ratio = 1 - (price / max_price)
            bonus = int(15 * savings_ratio)  # Increased bonus for better value
            score += bonus
            reasons.append(f"✓ Within budget: ${int(price):,} (max ${max_price:,})")
        else:
            over_budget = price - max_price
            score -= 50  # CRITICAL penalty for over budget
            reasons.append(f"⚠ Over budget by ${int(over_budget):,} (${int(price):,} vs ${max_price:,})")
    elif isinstance(price, (int, float)) and not min_price:
        # No price constraint at all
        score += 5

    # Mileage constraint (IMPORTANT)
    max_mileage = prefs.get("max_mileage")
    if isinstance(max_mileage, int) and isinstance(mileage, (int, float)):
        if mileage <= max_mileage:
            # Bonus for lower mileage
            mileage_ratio = 1 - (mileage / max_mileage)
            bonus = int(10 * mileage_ratio)
            score += bonus
            reasons.append(f"✓ Mileage: {int(mileage):,} miles")
        else:
            over_miles = mileage - max_mileage
            score -= 35  # Significant penalty for high mileage
            reasons.append(f"⚠ {int(over_miles):,} miles over limit ({int(mileage):,} vs {max_mileage:,})")
    elif isinstance(mileage, (int, float)):
        # No mileage constraint
        score += 3

    # Body type constraint (SUV, Sedan, Truck, etc.) - CRITICAL
    pref_body_type = prefs.get("body_type")
    listing_body_type = normalize_text(vehicle.get("body_style", "")) if vehicle.get("body_style") else ""
    listing_normal_body = normalize_text(vehicle.get("normal_body_style", "")) if vehicle.get("normal_body_style") else ""
    if pref_body_type:
        # Handle both single string and array of body types
        pref_body_types = [pref_body_type] if isinstance(pref_body_type, str) else pref_body_type
        pref_body_types_normalized = [normalize_text(bt) for bt in pref_body_types]

        # Check if listing matches any of the preferred body types
        match_found = False
        for pref_body_normalized in pref_body_types_normalized:
            if (listing_body_type and pref_body_normalized in listing_body_type) or \
               (listing_normal_body and pref_body_normalized in listing_normal_body):
                match_found = True
                break

        if match_found:
            score += 20
            body_display = vehicle.get("body_style", "") or vehicle.get("normal_body_style", "")
            reasons.append(f"✓ Matches body type: {body_display}")
        else:
            score -= 50  # CRITICAL penalty for wrong body type
            body_display = vehicle.get("body_style", "") or vehicle.get("normal_body_style", "") or "Unknown"
            wanted = ", ".join(pref_body_types) if len(pref_body_types) > 1 else pref_body_types[0]
            reasons.append(f"⚠ Different body type: {body_display} (wanted {wanted})")
    else:
        # No body type preference
        score += 5

    # Drivetrain constraint (AWD, FWD, 4WD, RWD) - IMPORTANT
    pref_drivetrain = prefs.get("drivetrain")
    listing_drivetrain = normalize_text(vehicle.get("drivetrain", "")) if vehicle.get("drivetrain") else ""
    if pref_drivetrain:
        pref_drivetrain_normalized = normalize_text(pref_drivetrain)
        # Normalize common variations (AWD = All Wheel Drive, etc.)
        drivetrain_matches = False
        if pref_drivetrain_normalized in listing_drivetrain:
            drivetrain_matches = True
        elif ("awd" in pref_drivetrain_normalized or "all wheel" in pref_drivetrain_normalized) and \
             ("awd" in listing_drivetrain or "all wheel" in listing_drivetrain):
            drivetrain_matches = True
        elif ("4wd" in pref_drivetrain_normalized or "four wheel" in pref_drivetrain_normalized) and \
             ("4wd" in listing_drivetrain or "four wheel" in listing_drivetrain):
            drivetrain_matches = True
        elif ("fwd" in pref_drivetrain_normalized or "front wheel" in pref_drivetrain_normalized) and \
             ("fwd" in listing_drivetrain or "front wheel" in listing_drivetrain):
            drivetrain_matches = True
        elif ("rwd" in pref_drivetrain_normalized or "rear wheel" in pref_drivetrain_normalized) and \
             ("rwd" in listing_drivetrain or "rear wheel" in listing_drivetrain):
            drivetrain_matches = True

        if drivetrain_matches:
            score += 18
            reasons.append(f"✓ Matches drivetrain: {vehicle.get('drivetrain', '')}")
        else:
            score -= 25  # Significant penalty for wrong drivetrain
            drivetrain_display = vehicle.get("drivetrain", "") or "Unknown"
            reasons.append(f"⚠ Different drivetrain: {drivetrain_display} (wanted {pref_drivetrain})")
    else:
        # No drivetrain preference
        score += 3

    # Exterior color constraint (preference, not critical)
    pref_exterior_color = prefs.get("exterior_color")
    if pref_exterior_color:
        # Handle both single string and array of colors
        pref_colors = [pref_exterior_color] if isinstance(pref_exterior_color, str) else pref_exterior_color
        pref_colors_normalized = [normalize_text(c) for c in pref_colors]

        # Check if listing matches any of the preferred colors
        match_found = False
        for pref_color_normalized in pref_colors_normalized:
            if exterior_color and pref_color_normalized in exterior_color:
                match_found = True
                break

        if match_found:
            score += 15
            reasons.append(f"✓ Matches exterior color: {vehicle.get('exterior_color', '')}")
        else:
            score -= 12  # Moderate penalty for wrong color (reduced from -30)
            actual_color = vehicle.get('exterior_color', 'Unknown')
            wanted = " or ".join(pref_colors) if len(pref_colors) > 1 else pref_colors[0]
            reasons.append(f"⚠ Different exterior color: {actual_color} (wanted {wanted})")
    else:
        # No color preference
        score += 2

    # Interior color constraint (preference, not critical)
    pref_interior_color = prefs.get("interior_color")
    if pref_interior_color:
        # Handle both single string and array of colors
        pref_int_colors = [pref_interior_color] if isinstance(pref_interior_color, str) else pref_interior_color
        pref_int_colors_normalized = [normalize_text(c) for c in pref_int_colors]

        # Check if listing matches any of the preferred interior colors
        match_found = False
        for pref_int_color_normalized in pref_int_colors_normalized:
            if interior_color and pref_int_color_normalized in interior_color:
                match_found = True
                break

        if match_found:
            score += 10
            reasons.append(f"✓ Matches interior color: {vehicle.get('interior_color', '')}")
        else:
            score -= 8  # Light penalty for wrong interior color (reduced from -20)
            actual_int_color = vehicle.get('interior_color', 'Unknown')
            wanted = " or ".join(pref_int_colors) if len(pref_int_colors) > 1 else pref_int_colors[0]
            reasons.append(f"⚠ Different interior color: {actual_int_color} (wanted {wanted})")
    else:
        # No interior color preference
        score += 2

    # Horsepower constraint (CRITICAL - hard requirement)
    min_horsepower = prefs.get("horsepower")
    listing_horsepower = vehicle.get("horsepower_hp")  # Fixed: use correct field name
    if isinstance(min_horsepower, int) and isinstance(listing_horsepower, (int, float)):
        if listing_horsepower >= min_horsepower:
            score += 20
            reasons.append(f"✓ Horsepower: {int(listing_horsepower)}hp (meets {min_horsepower}+ requirement)")
        else:
            deficit = min_horsepower - listing_horsepower
            score -= 40  # CRITICAL penalty for underpowered
            reasons.append(f"⚠ Underpowered: {int(listing_horsepower)}hp (need {min_horsepower}+, short by {int(deficit)}hp)")
    elif isinstance(min_horsepower, int) and not listing_horsepower:
        # If horsepower is required but not listed, penalize heavily
        score -= 25
        reasons.append(f"⚠ Horsepower not listed (need {min_horsepower}+)")
    else:
        # No horsepower constraint
        score += 3

    # Feature matching (IMPORTANT - worth significant points)
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

        # More aggressive scoring: +40 points max for features, but penalty for missing
        feature_score = int(40 * match_ratio)
        score += feature_score

        # Additional penalty for poor feature matching
        missing_ratio = 1 - match_ratio
        missing_penalty = int(20 * missing_ratio)
        score -= missing_penalty

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
    else:
        # No features requested, small bonus
        score += 5

    # Clamp score to 0-100
    # Since we start at 0, a perfect match can go over 100, so normalize it
    final_score = max(0, min(100, score))

    return (final_score, reasons)

def relax_constraints(prefs: dict, level: int) -> tuple:
    """Progressively relax constraints. Returns (relaxed_prefs, relaxations_applied)"""
    relaxed = prefs.copy()
    relaxations = []

    if level >= 1:
        # Level 1: Remove least important features (keep top 5)
        features = relaxed.get("features", [])
        if len(features) > 5:
            keep_count = max(5, len(features) // 2)
            relaxed["features"] = features[:keep_count]
            relaxations.append(f"Focused on {keep_count} key features")

    if level >= 2:
        # Level 2: Remove color preferences (not critical)
        if relaxed.get("exterior_color"):
            del relaxed["exterior_color"]
            relaxations.append("Removed exterior color preference")
        if relaxed.get("interior_color"):
            del relaxed["interior_color"]
            relaxations.append("Removed interior color preference")

    if level >= 3:
        # Level 3: Expand year range by ±1 year
        if "min_year" in relaxed:
            relaxed["min_year"] -= 1
            relaxations.append(f"Expanded min year to {relaxed['min_year']}")
        if "max_year" in relaxed:
            relaxed["max_year"] += 1
            relaxations.append(f"Expanded max year to {relaxed['max_year']}")

    if level >= 4:
        # Level 4: Increase mileage by 20k
        max_mileage = relaxed.get("max_mileage")
        if max_mileage:
            new_mileage = max_mileage + 20000
            relaxed["max_mileage"] = new_mileage
            relaxations.append(f"Increased mileage limit to {new_mileage:,}")

    if level >= 5:
        # Level 5: Drop the specific-model constraint (brand/model-agnostic)
        if relaxed.get("model"):
            relaxed = {**relaxed}
            relaxed.pop("model", None)
            relaxations.append("Broadened beyond specific models")

    if level >= 6:
        # Level 6: Increase price by 15%
        max_price = relaxed.get("max_price")
        if max_price:
            new_price = int(max_price * 1.15)
            relaxed["max_price"] = new_price
            relaxations.append(f"Increased budget to ${new_price:,}")

    if level >= 7:
        # Level 7: Remove drivetrain requirement
        if relaxed.get("drivetrain"):
            del relaxed["drivetrain"]
            relaxations.append("Removed drivetrain requirement")

    if level >= 8:
        # Level 8: Expand year range further by ±2 years
        if "min_year" in relaxed:
            relaxed["min_year"] -= 2
            relaxations.append(f"Further expanded min year to {relaxed['min_year']}")
        if "max_year" in relaxed:
            relaxed["max_year"] += 2
            relaxations.append(f"Further expanded max year to {relaxed['max_year']}")

    if level >= 9:
        # Level 9: Remove all features
        if relaxed.get("features"):
            relaxed["features"] = []
            relaxations.append("Removed all feature requirements")

    if level >= 10:
        # Level 10: Increase price further by another 20%
        max_price = relaxed.get("max_price")
        if max_price:
            new_price = int(max_price * 1.2)
            relaxed["max_price"] = new_price
            relaxations.append(f"Further increased budget to ${new_price:,}")

    return (relaxed, relaxations)

def rank_listings(prefs: dict, limit: int = 25):
    """Rank listings with zero-match detection and constraint relaxation"""
    # Build financing parameters if user is financing
    financing_params = None
    if prefs.get("payment_method") == "finance":
        down_payment = prefs.get("down_payment", 0)
        loan_term = prefs.get("loan_term_months", 60)  # Default to 60 months if not specified
        credit_score = prefs.get("credit_score", 700)  # Default to 700 if not specified
        apr = estimate_apr(credit_score)

        financing_params = {
            "down_payment": down_payment,
            "loan_term_months": loan_term,
            "apr": apr,
            "credit_score": credit_score
        }

        # If max_monthly_payment is specified, calculate max affordable price
        if prefs.get("max_monthly_payment"):
            max_monthly = prefs.get("max_monthly_payment")
            max_price = calculate_max_affordable_price(max_monthly, down_payment, apr, loan_term)

            print(f"[rank_listings] Financing mode: max_monthly=${max_monthly}, calculated max_price=${max_price:.2f}", flush=True)

            # Override max_price constraint
            prefs["max_price"] = int(max_price)

    listings = load_listings()
    scored = []

    for listing in listings:
        score, reasons = score_listing(listing, prefs)
        scored.append((score, reasons, listing))

    scored.sort(key=lambda item: item[0], reverse=True)

    # Zero-match detection - stricter threshold now
    GOOD_MATCH_THRESHOLD = 60  # Raised from 50 due to stricter scoring
    top_score = scored[0][0] if scored else 0

    if top_score < GOOD_MATCH_THRESHOLD:
        print(f"[rank_listings] Zero matches detected (top score: {top_score}). Trying constraint relaxation...", flush=True)

        # Try progressive relaxation (up to 10 levels with larger database)
        for level in range(1, 11):
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
                return format_results(scored, limit, relaxations, financing_params)

        # If still no good matches, return best available with all relaxations
        print(f"[rank_listings] No good matches even after full relaxation", flush=True)
        _, final_relaxations = relax_constraints(prefs, 10)
        return format_results(scored, limit, final_relaxations, financing_params)

    # Good matches found, return normally
    return format_results(scored, limit, [], financing_params)

def format_results(scored, limit, relaxations, financing_params=None):
    """Format scored listings into result objects with diversity filter"""
    top = []
    seen_models = {}
    MAX_PER_MODEL = 5  # Increased from 3 to allow more variety with larger database

    for score, reasons, listing in scored:
        if len(top) >= limit:
            break

        vehicle = listing.get("vehicle", {})
        model = vehicle.get("model", "Unknown")

        # Diversity filter: max 5 of same model
        if seen_models.get(model, 0) >= MAX_PER_MODEL:
            continue

        seen_models[model] = seen_models.get(model, 0) + 1

        image_urls = listing.get("image_urls", []) or []
        features = listing.get("highlighted_features_raw", []) or []

        result_item = {
            "id": listing.get("id"),
            "source_url": listing.get("source_url"),
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
            "transmission": vehicle.get("transmission"),
            "fuel_type": vehicle.get("fuel_type"),
            "mpg_city": vehicle.get("mpg_city"),
            "mpg_highway": vehicle.get("mpg_highway"),
            "seating_capacity": vehicle.get("seating_capacity"),
            "torque_lbft": vehicle.get("torque_lbft"),
            "features": features[:5],  # Top 5 features
            "all_features": features,  # All features for comparison
            "image_urls": image_urls,  # Send all images for gallery
            "dealer_notes": listing.get("dealer_notes"),
            "spec_sections": listing.get("spec_sections"),
            "score": score,
            "match_score_percent": score,
            "match_reasons": reasons,
            "relaxations": relaxations if relaxations else None
        }

        # Add monthly payment calculation if financing
        if financing_params:
            price = vehicle.get("price_usd")
            if price:
                down_payment = financing_params.get("down_payment", 0)
                apr = financing_params.get("apr")
                term_months = financing_params.get("loan_term_months")

                monthly_payment = calculate_monthly_payment(price, down_payment, apr, term_months)
                result_item["monthly_payment"] = round(monthly_payment, 2)
                result_item["financing_info"] = {
                    "down_payment": down_payment,
                    "apr_percent": round(apr * 100, 2),
                    "term_months": term_months
                }

        top.append(result_item)

    return top


def extract_labels(user_text: str) -> dict:
    print(f"[extract_labels] input={user_text!r}", flush=True)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_text}
    ]

    print("[extract_labels] sending request to model...", flush=True)
    response = client.chat.completions.create(
        model="gpt-4o",  # Precise model for backend preference extraction
        messages=messages,
        temperature=0
    )

    raw = response.choices[0].message.content.strip()
    print(f"[extract_labels] raw response={raw!r}", flush=True)

    # Strip markdown code fences if present
    if raw.startswith("```"):
        # Remove opening fence
        raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
        # Remove closing fence
        if raw.endswith("```"):
            raw = raw.rsplit("\n```", 1)[0]
        raw = raw.strip()
        print(f"[extract_labels] stripped markdown, cleaned={raw!r}", flush=True)

    data = json.loads(raw)
    print(f"[extract_labels] parsed data={data!r}", flush=True)

    cleaned = sanitize_output(data)
    print(f"[extract_labels] cleaned={cleaned!r}", flush=True)
    return cleaned

def check_inventory_availability(current_state: dict) -> dict:
    """Check how many good matches exist with current preferences"""
    if not current_state:
        # No preferences yet, assume full inventory available
        return {"match_count": 1000, "status": "abundant"}

    listings = load_listings()
    scored = []

    for listing in listings:
        score, _ = score_listing(listing, current_state)
        if score >= 60:  # Good match threshold
            scored.append(score)

    match_count = len(scored)
    print(f"[check_inventory] {match_count} good matches with current preferences", flush=True)

    # Classify inventory status (updated thresholds for larger database)
    if match_count >= 30:
        status = "abundant"  # Plenty of options, can ask for more details
    elif match_count >= 15:
        status = "moderate"  # Some options, suggest showing results soon
    elif match_count >= 5:
        status = "limited"  # Very few options, stop asking for more details
    else:
        status = "none"  # No good matches, need to relax constraints

    return {"match_count": match_count, "status": status}

def generate_bot_response(user_text: str, current_state: dict, stage: str) -> str:
    """Generate contextual, inventory-aware bot response based on user input and current state"""
    print(f"[generate_bot_response] user_text={user_text!r}, stage={stage}, state={current_state!r}", flush=True)

    # Check inventory availability with current preferences
    inventory_info = check_inventory_availability(current_state)
    print(f"[generate_bot_response] inventory_info={inventory_info!r}", flush=True)

    # Build context about what we know so far
    context_parts = []
    if current_state.get("brand"):
        context_parts.append(f"Brand preferences: {', '.join(current_state['brand'])}")
    if current_state.get("model"):
        context_parts.append(f"Model preferences: {', '.join(current_state['model'])}")
    if current_state.get("min_price") or current_state.get("max_price"):
        min_p = current_state.get("min_price")
        max_p = current_state.get("max_price")
        if min_p and max_p:
            context_parts.append(f"Budget: ${min_p:,} - ${max_p:,}")
        elif max_p:
            context_parts.append(f"Budget: Up to ${max_p:,}")
        elif min_p:
            context_parts.append(f"Budget: At least ${min_p:,}")
    if current_state.get("max_mileage"):
        context_parts.append(f"Max mileage: {current_state['max_mileage']:,}")
    if current_state.get("body_type"):
        body_type = current_state['body_type']
        body_type_str = ', '.join(body_type) if isinstance(body_type, list) else body_type
        context_parts.append(f"Body type: {body_type_str}")
    if current_state.get("exterior_color"):
        ext_color = current_state['exterior_color']
        ext_color_str = ', '.join(ext_color) if isinstance(ext_color, list) else ext_color
        context_parts.append(f"Exterior color: {ext_color_str}")
    if current_state.get("interior_color"):
        int_color = current_state['interior_color']
        int_color_str = ', '.join(int_color) if isinstance(int_color, list) else int_color
        context_parts.append(f"Interior color: {int_color_str}")
    if current_state.get("drivetrain"):
        context_parts.append(f"Drivetrain: {current_state['drivetrain']}")
    if current_state.get("min_year") or current_state.get("max_year"):
        year_str = ""
        if current_state.get("min_year"):
            year_str += f"{current_state['min_year']}+"
        if current_state.get("max_year"):
            year_str = f"{current_state.get('min_year', 'any')}-{current_state['max_year']}"
        context_parts.append(f"Year range: {year_str}")
    if current_state.get("features"):
        features_str = ', '.join(current_state['features'][:3])
        if len(current_state['features']) > 3:
            features_str += f" (+{len(current_state['features']) - 3} more)"
        context_parts.append(f"Features: {features_str}")

    context_summary = "\n".join(context_parts) if context_parts else "No preferences captured yet"

    # Tailor the prompt based on inventory availability
    if inventory_info["status"] == "abundant":
        # Plenty of matches - can ask for more details, but focus on important filters
        inventory_guidance = f"""INVENTORY STATUS: {inventory_info['match_count']} vehicles match their current preferences.

You can ask for ONE more important detail, but focus on the most impactful filters:
- Budget/price range (if not specified)
- Body type (sedan, SUV, truck) (if not specified)
- Model preference (if only brand specified)
- Year range (if not specified)

DO NOT ask about:
- Minor features like color preferences or interior details
- Multiple questions at once
- Details that won't significantly narrow results"""

    elif inventory_info["status"] == "moderate":
        # Moderate matches - suggest showing results or ONE final detail
        inventory_guidance = f"""INVENTORY STATUS: {inventory_info['match_count']} vehicles match their current preferences.

This is a good number of matches! You should:
- Acknowledge what they said
- Suggest they're ready to see results OR ask for ONE final important detail ONLY if a critical filter is missing (budget, body type, or model)
- Keep it brief and encouraging
- Don't push for minor details"""

    elif inventory_info["status"] == "limited":
        # Very few matches - stop asking questions, suggest showing results
        inventory_guidance = f"""INVENTORY STATUS: Only {inventory_info['match_count']} vehicles match their current preferences.

IMPORTANT: The inventory is getting LIMITED. You MUST:
- Acknowledge what they said
- Gently suggest showing them the available options now
- DO NOT ask for more details - this will further limit matches
- Be positive about the matches found
- Example: "Great! I found {inventory_info['match_count']} vehicles that match your preferences. Would you like to see them?"
"""

    else:  # status == "none"
        # No good matches - need to suggest relaxing constraints
        inventory_guidance = """INVENTORY STATUS: No vehicles match their current preferences well.

You should:
- Acknowledge their preferences
- Gently suggest they might want to adjust one constraint slightly
- Offer to show the closest matches available
- Be encouraging, not discouraging"""

    BOT_RESPONSE_PROMPT = f"""You are an expert car salesman having a friendly conversation with a customer.

User just said: "{user_text}"

What we know about their preferences so far:
{context_summary}

{inventory_guidance}

Your task:
1. Acknowledge what they just mentioned SPECIFICALLY (don't be generic)
2. Follow the inventory guidance above - respect the match count
3. Be conversational, friendly, and helpful - like a real salesperson building rapport
4. Keep it concise (1-2 sentences max)

CRITICAL RULES:
- NEVER ask more than ONE follow-up question
- If inventory is limited or moderate, strongly encourage showing results
- Only ask about filters the backend actually supports: brand, model, budget, body type, drivetrain, year range
- Be genuinely helpful, not pushy

Output ONLY your response text. No preamble, no "Here's my response:", just the conversational text."""

    messages = [
        {"role": "system", "content": BOT_RESPONSE_PROMPT},
        {"role": "user", "content": "Generate the response."}
    ]

    print("[generate_bot_response] sending request to model...", flush=True)
    response = client.chat.completions.create(
        model="gpt-4o-mini",  # Faster model for frontend chatbot responses
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

app = FastAPI(title="CarScout API")

# CORS origins are configurable via ALLOWED_ORIGINS (comma-separated).
# Defaults to "*" for local dev; lock down in production.
_allowed = os.getenv("ALLOWED_ORIGINS")
_origins = [o.strip() for o in _allowed.split(",") if o.strip()] if _allowed else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PreferenceInput(BaseModel):
    text: str
    stage: Optional[str] = None
    zip: Optional[str] = None
    state: Optional[dict] = None  # Allow frontend to override backend state


@app.get("/")
def health():
    print("[health] ok", flush=True)
    return {"status": "ok"}


@app.post("/preferences")
def update_preferences(payload: PreferenceInput):
    # Stateless: the client owns conversation state and sends it on every call.
    # (A module-global would leak across users and break on serverless.)
    state = dict(payload.state) if payload.state else {}
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

        bot_response = f"Perfect! I'll search the inventory at {DEALERSHIP_INFO['name']}. Now, what kind of car are you looking for? Tell me about your budget, preferred features, or any specific models you have in mind."
        return {"state": state, "bot_response": bot_response}

    if payload.stage == "done":
        print(f"[preferences] done stage, state={state!r}", flush=True)

        # Check if user is sending new preferences or just triggering results display
        if payload.text and payload.text.strip().lower() != "show_results":
            print(f"[preferences] extracting new preferences from text: {payload.text!r}", flush=True)
            # User is updating preferences while viewing results
            try:
                update = extract_labels(payload.text)
                print(f"[preferences] extracted update={update!r}", flush=True)

                if update:  # Only update if we found new preferences
                    state = merge_state(state, update)
                    print(f"[preferences] merged state={state!r}", flush=True)
            except Exception as e:
                print(f"[preferences] extract_labels failed: {e}", flush=True)

        # Re-rank with current (possibly updated) state
        results = rank_listings(state)
        print(f"[preferences] results_count={len(results)}", flush=True)

        # Generate appropriate bot response
        if payload.text and payload.text.strip().lower() != "show_results":
            try:
                bot_response = generate_bot_response(payload.text, state, "done")
            except Exception as e:
                print(f"[preferences] generate_bot_response failed: {e}", flush=True)
                bot_response = f"Got it! I've updated your results. I found {len(results)} vehicles that match your preferences."
        else:
            bot_response = f"Excellent! I've found {len(results)} great matches for you. Let me show you the best options that fit your preferences."

        return {"state": state, "results": results, "bot_response": bot_response}

    try:
        update = extract_labels(payload.text)
        print(f"[preferences] extracted update={update!r}", flush=True)
    except Exception as e:
        print(f"[preferences] extract_labels failed with error: {e}, returning empty update", flush=True)
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


@app.post("/compare")
def compare_vehicles(payload: dict):
    """
    Generate AI-powered comparison insight for two vehicles.
    Analyzes specs, pricing, value, and provides recommendation.
    """
    car1 = payload.get("car1", {})
    car2 = payload.get("car2", {})

    print(f"[compare] Comparing {car1.get('year')} {car1.get('make')} {car1.get('model')} vs {car2.get('year')} {car2.get('make')} {car2.get('model')}", flush=True)

    # Build detailed prompt for comparison
    comparison_prompt = f"""You are an expert automotive analyst. Compare these two vehicles and provide a comprehensive analysis.

Vehicle 1: {car1.get('year')} {car1.get('make')} {car1.get('model')} {car1.get('trim', '')}
- Price: ${car1.get('price', 0):,}
- Mileage: {car1.get('mileage', 0):,} miles
- Drivetrain: {car1.get('drivetrain', 'N/A')}
- Body Style: {car1.get('body_style', 'N/A')}
- Horsepower: {car1.get('horsepower', 'N/A')} hp
- Torque: {car1.get('torque_lbft', 'N/A')} lb-ft
- Engine: {car1.get('engine', 'N/A')}
- Transmission: {car1.get('transmission', 'N/A')}
- Fuel Type: {car1.get('fuel_type', 'N/A')}
- MPG: {car1.get('mpg_city', 'N/A')} city / {car1.get('mpg_highway', 'N/A')} highway
- Seating: {car1.get('seating_capacity', 'N/A')} passengers
- Exterior Color: {car1.get('exterior_color', 'N/A')}
- Interior Color: {car1.get('interior_color', 'N/A')}

Vehicle 2: {car2.get('year')} {car2.get('make')} {car2.get('model')} {car2.get('trim', '')}
- Price: ${car2.get('price', 0):,}
- Mileage: {car2.get('mileage', 0):,} miles
- Drivetrain: {car2.get('drivetrain', 'N/A')}
- Body Style: {car2.get('body_style', 'N/A')}
- Horsepower: {car2.get('horsepower', 'N/A')} hp
- Torque: {car2.get('torque_lbft', 'N/A')} lb-ft
- Engine: {car2.get('engine', 'N/A')}
- Transmission: {car2.get('transmission', 'N/A')}
- Fuel Type: {car2.get('fuel_type', 'N/A')}
- MPG: {car2.get('mpg_city', 'N/A')} city / {car2.get('mpg_highway', 'N/A')} highway
- Seating: {car2.get('seating_capacity', 'N/A')} passengers
- Exterior Color: {car2.get('exterior_color', 'N/A')}
- Interior Color: {car2.get('interior_color', 'N/A')}

Provide a CONCISE comparison in this format (keep it brief, use bullet points):

**Value Analysis**
- Quick comparison of price-to-value ratio
- Note typical market values if relevant

**Performance & Efficiency**
- Key performance differences (power, mpg)

**Best For**
- 1-2 sentence recommendation for each buyer type

Keep the entire response under 300 words. Be specific with numbers but avoid long paragraphs."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert automotive analyst who provides CONCISE, data-driven vehicle comparisons. Keep responses brief and to the point using bullet points. Use actual market knowledge and reference sources like Kelley Blue Book when discussing values."},
                {"role": "user", "content": comparison_prompt}
            ],
            temperature=0.7
        )

        insight = response.choices[0].message.content.strip()
        print(f"[compare] Generated insight of {len(insight)} characters", flush=True)

        return {"insight": insight}

    except Exception as e:
        print(f"[compare] Error generating insight: {e}", flush=True)
        return {
            "insight": "I apologize, but I'm unable to generate a detailed comparison at this time. However, based on the specs:\n\n" +
                      f"Vehicle 1 ({car1.get('year')} {car1.get('model')}): ${car1.get('price', 0):,} with {car1.get('mileage', 0):,} miles\n" +
                      f"Vehicle 2 ({car2.get('year')} {car2.get('model')}): ${car2.get('price', 0):,} with {car2.get('mileage', 0):,} miles\n\n" +
                      "Consider factors like price-per-mile ratio, fuel efficiency, and your specific needs when making your decision."
        }


@app.post("/compare-chat")
def compare_chat(payload: dict):
    """
    Answer questions about two specific vehicles being compared.
    """
    car1 = payload.get("car1", {})
    car2 = payload.get("car2", {})
    question = payload.get("question", "")
    chat_history = payload.get("chat_history", [])

    print(f"[compare-chat] Question: {question}", flush=True)

    # Build context about both vehicles
    context = f"""You are helping a user compare two vehicles. Answer their question accurately based on the vehicle specifications provided.

Vehicle 1: {car1.get('year')} {car1.get('make')} {car1.get('model')} {car1.get('trim', '')}
Full Specs:
- Price: ${car1.get('price', 0):,}
- Mileage: {car1.get('mileage', 0):,} miles
- Drivetrain: {car1.get('drivetrain', 'N/A')}
- Body Style: {car1.get('body_style', 'N/A')}
- Horsepower: {car1.get('horsepower', 'N/A')} hp
- Torque: {car1.get('torque_lbft', 'N/A')} lb-ft
- Engine: {car1.get('engine', 'N/A')}
- Transmission: {car1.get('transmission', 'N/A')}
- Fuel Type: {car1.get('fuel_type', 'N/A')}
- MPG: {car1.get('mpg_city', 'N/A')} city / {car1.get('mpg_highway', 'N/A')} highway
- Seating: {car1.get('seating_capacity', 'N/A')} passengers
- Colors: {car1.get('exterior_color', 'N/A')} exterior, {car1.get('interior_color', 'N/A')} interior
- Features: {', '.join(car1.get('all_features', [])[:10]) if car1.get('all_features') else 'N/A'}

Vehicle 2: {car2.get('year')} {car2.get('make')} {car2.get('model')} {car2.get('trim', '')}
Full Specs:
- Price: ${car2.get('price', 0):,}
- Mileage: {car2.get('mileage', 0):,} miles
- Drivetrain: {car2.get('drivetrain', 'N/A')}
- Body Style: {car2.get('body_style', 'N/A')}
- Horsepower: {car2.get('horsepower', 'N/A')} hp
- Torque: {car2.get('torque_lbft', 'N/A')} lb-ft
- Engine: {car2.get('engine', 'N/A')}
- Transmission: {car2.get('transmission', 'N/A')}
- Fuel Type: {car2.get('fuel_type', 'N/A')}
- MPG: {car2.get('mpg_city', 'N/A')} city / {car2.get('mpg_highway', 'N/A')} highway
- Seating: {car2.get('seating_capacity', 'N/A')} passengers
- Colors: {car2.get('exterior_color', 'N/A')} exterior, {car2.get('interior_color', 'N/A')} interior
- Features: {', '.join(car2.get('all_features', [])[:10]) if car2.get('all_features') else 'N/A'}

Answer the user's question based on these specifications. Be specific and reference the actual data."""

    try:
        # Build message history
        messages = [
            {"role": "system", "content": context}
        ]

        # Add chat history
        for msg in chat_history:
            messages.append({
                "role": "assistant" if msg["role"] == "bot" else "user",
                "content": msg["text"]
            })

        # Add current question
        messages.append({"role": "user", "content": question})

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0.7
        )

        answer = response.choices[0].message.content.strip()
        print(f"[compare-chat] Generated answer of {len(answer)} characters", flush=True)

        return {"answer": answer}

    except Exception as e:
        print(f"[compare-chat] Error generating answer: {e}", flush=True)
        return {
            "answer": "I apologize, but I'm having trouble processing that question right now. Please try rephrasing or ask something else about these vehicles."
        }
