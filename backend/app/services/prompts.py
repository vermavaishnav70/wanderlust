import json

from app.schemas.trips import TripPlanData, TripPlanRequest


SYSTEM_INSTRUCTION = """
You are a senior AI travel planner.
Generate personalized, realistic, and budget-aware itineraries.
Return valid JSON only, with no markdown fences or commentary.
Every activity must include a specific time, destination-relevant place, price,
duration, and short explanation.
""".strip()


def build_trip_prompt(request: TripPlanRequest) -> str:
    schema = json.dumps(TripPlanData.model_json_schema(), separators=(",", ":"))
    trip_start = request.trip_start.isoformat() if request.trip_start else "Flexible"

    return (
        "Plan a multi-day trip itinerary.\n"
        f"Destination: {request.destination}\n"
        f"Number of days: {request.number_of_days}\n"
        f"Trip start: {trip_start}\n"
        f"Itinerary style: {request.itinerary_type}\n"
        f"Budget: {request.budget}\n\n"
        "Rules:\n"
        "- Return JSON only.\n"
        "- Match the JSON schema exactly.\n"
        "- Include 4 to 5 activities for each day.\n"
        "- Prices must be integers and use 0 when unknown.\n"
        "- Make activity timing feel realistic for local travel.\n"
        "- Keep descriptions concise and practical.\n\n"
        f"JSON schema: {schema}"
    )
