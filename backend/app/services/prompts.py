import json

from app.schemas.trips import ProviderTripPlanData, TripEditRequest, TripPlanData, TripPlanRequest


SYSTEM_INSTRUCTION = """
You are a senior AI travel planner.
Generate personalized, realistic, and budget-aware itineraries.
Return valid JSON only, with no markdown fences or commentary.
Every activity must include a specific time, destination-relevant place, price,
duration, and short explanation.
""".strip()


def build_trip_prompt(request: TripPlanRequest, weather_summary: str = "") -> str:
    schema = json.dumps(ProviderTripPlanData.model_json_schema(), separators=(",", ":"))
    trip_start = request.trip_start.isoformat() if request.trip_start else "Flexible"

    sections = [
        "Plan a multi-day trip itinerary.\n"
        f"Destination: {request.destination}\n"
        f"Number of days: {request.number_of_days}\n"
        f"Trip start: {trip_start}\n"
        f"Itinerary style: {request.itinerary_type}\n"
        f"Budget: {request.budget}\n",
    ]

    if weather_summary:
        sections.append(f"Weather context: {weather_summary}\n")

    sections.append(
        "\n"
        "Rules:\n"
        "- Return JSON only.\n"
        "- Match the JSON schema exactly.\n"
        '- Use a top-level object with an "itinerary" array.\n'
        "- Include 4 to 5 activities for each day.\n"
        '- Prefer day labels like "Day 1", "Day 2", and so on.\n'
        "- Prices must be integers and use 0 when unknown.\n"
        "- Make activity timing feel realistic for local travel.\n"
        "- Keep descriptions concise and practical.\n\n"
        f"JSON schema: {schema}"
    )

    return "".join(sections)


def build_trip_edit_prompt(request: TripEditRequest, weather_summary: str = "") -> str:
    current_itinerary_json = json.dumps(
        request.current_itinerary.model_dump(mode="json"),
        separators=(",", ":"),
    )
    trip_request_json = json.dumps(
        request.trip_request.model_dump(mode="json"),
        separators=(",", ":"),
    )
    schema = json.dumps(ProviderTripPlanData.model_json_schema(), separators=(",", ":"))

    sections = [
        "Edit an existing trip itinerary.\n",
        f"Original trip request: {trip_request_json}\n",
        f"Current itinerary JSON: {current_itinerary_json}\n",
        f"User edit request: {request.message}\n",
    ]

    if weather_summary:
        sections.append(f"Weather context: {weather_summary}\n")

    sections.append(
        "\nRules:\n"
        "- Return JSON only.\n"
        "- Match the JSON schema exactly.\n"
        '- Use a top-level object with an "itinerary" array.\n'
        "- Preserve unaffected days and activities whenever possible.\n"
        "- Apply the user's request faithfully.\n"
        "- Keep times realistic and prices as integers.\n"
        "- Use 0 when a price is unknown.\n\n"
        f"JSON schema: {schema}"
    )

    return "".join(sections)
