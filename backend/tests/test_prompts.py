from datetime import date

from app.schemas.trips import TripPlanRequest
from app.services.prompts import build_trip_prompt


def test_build_trip_prompt_includes_normalized_fields() -> None:
    request = TripPlanRequest(
        destination="Bangkok",
        number_of_days=4,
        trip_start=date(2026, 4, 1),
        itinerary_type="Foodie",
        budget="Medium",
    )

    prompt = build_trip_prompt(request)

    assert "Destination: Bangkok" in prompt
    assert "Number of days: 4" in prompt
    assert "Trip start: 2026-04-01" in prompt
    assert "Budget: Medium" in prompt
    assert "JSON schema:" in prompt
