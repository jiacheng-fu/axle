# from fastapi import FastAPI
# from routes.compare import router
# from dotenv import load_dotenv

# load_dotenv()

# app = FastAPI(title="Used Car Intelligence API")

# app.include_router(router)

# @app.get("/")
# def health():
#     return {"status": "ok"}

import os
from openai import OpenAI
from dotenv import load_dotenv
import requests
import json

#set up the semantic chatbot client
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
- max_price (number)
- max_mileage (number)
- features (array of strings)

Rules:
- Normalize brands and models to proper capitalization.
- Normalize features to lowercase canonical labels.
- If nothing relevant is mentioned, output {}.
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
    "features": list
}


def extract_labels(user_text: str) -> dict:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_text}
    ]

    response = client.chat.completions.create(
        model="GPT-5.2",
        messages=messages,
        temperature=0
    )

    raw = response.choices[0].message.content.strip()
    data = json.loads(raw)

    return sanitize_output(data)

def sanitize_output(data: dict) -> dict:
    clean = {}

    for key, value in data.items():
        if key not in SCHEMA:
            continue

        if value is None:
            continue

        if isinstance(value, list) and len(value) == 0:
            continue

        clean[key] = value

    if "features" in clean:
        clean["features"] = normalize_features(clean["features"])

    return clean

def normalize_features(features):
    normalized = set()

    for f in features:
        f = f.lower()
        normalized.add(FEATURE_ALIASES.get(f, f))

    return list(normalized)

def merge_state(state: dict, update: dict) -> dict:
    for key, value in update.items():
        if key in ["brand", "model"]:
            state[key] = value  # replace
        elif key == "features":
            state.setdefault("features", [])
            state["features"] = list(set(state["features"]) | set(value))
        else:
            state[key] = value  # last-write-wins

    return state

state = {}

user_inputs = [
    "Something under 15 bands",
    "Prefer Toyota or Honda",
    "Must have Apple CarPlay",
    "I'd like a 2023 or newer",
    "actually I want it under 10k"
]

for text in user_inputs:
    update = extract_labels(text)
    state = merge_state(state, update)

print(state)
