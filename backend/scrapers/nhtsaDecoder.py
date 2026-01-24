import requests

NHTSA_URL = "https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVinValuesExtended/{}?format=json"

def decode_vin(vin: str):
    response = requests.get(NHTSA_URL.format(vin))
    data = response.json()["Results"][0]

    return {
        "vin": vin,
        "make": data.get("Make"),
        "model": data.get("Model"),
        "year": data.get("ModelYear"),
        "body_type": data.get("BodyClass"),
        "engine": data.get("EngineModel"),
        "fuel_type": data.get("FuelTypePrimary"),
        "plant_country": data.get("PlantCountry"),
    }
