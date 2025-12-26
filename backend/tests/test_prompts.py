from datetime import date

from app.schemas.trips import TripEditRequest, TripPlanData, TripPlanRequest
from app.services.prompts import build_trip_edit_prompt, build_trip_prompt


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


def test_build_trip_prompt_includes_weather_when_available() -> None:
    request = TripPlanRequest(
        destination="Bangkok",
        number_of_days=4,
        trip_start=date(2026, 4, 1),
        itinerary_type="Foodie",
        budget="Medium",
    )

    prompt = build_trip_prompt(request, "2026-04-01: Warm and sunny, highs around 31C")

    assert "Weather context:" in prompt
    assert "Warm and sunny" in prompt


def test_build_trip_edit_prompt_includes_current_itinerary_and_message() -> None:
    request = TripEditRequest(
        trip_request=TripPlanRequest(
            destination="Bangkok",
            number_of_days=4,
            trip_start=date(2026, 4, 1),
            itinerary_type="Foodie",
            budget="Medium",
        ),
        current_itinerary=TripPlanData(
            itinerary=[
                {
                    "day": "Day 1",
                    "activities": [
                        {
                            "time": "09:00 AM",
                            "name": "Breakfast",
                            "location": "Bangkok",
                            "price": 0,
                            "duration": "1 hour",
                            "description": "Start the day",
                        }
                    ],
                }
            ]
        ),
        message="Make day 1 more indoor",
    )

    prompt = build_trip_edit_prompt(request, "Warm and sunny")

    assert "Current itinerary JSON:" in prompt
    assert "Make day 1 more indoor" in prompt
    assert "Weather context:" in prompt
