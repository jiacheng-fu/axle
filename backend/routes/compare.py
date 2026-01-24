from fastapi import APIRouter
from scrapers.nhtsa_decoder import decode_vin
from scrapers.vin_utils import calculate_age
from services.ai_recommendation import generate_recommendation

router = APIRouter()

@router.post("/compare")
def compare_vins(vins: list[str]):
    cars = []

    for vin in vins:
        car = decode_vin(vin)
        car["age"] = calculate_age(car["year"])
        cars.append(car)

    ai_summary = generate_recommendation(cars)

    return {
        "cars": cars,
        "ai_summary": ai_summary
    }
