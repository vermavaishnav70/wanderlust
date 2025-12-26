from fastapi.testclient import TestClient

from app.dependencies import get_orchestrator, get_weather_service
from app.main import create_app
from app.schemas.trips import PlannedTripResult, TripPlanData, TripPlanMeta
from app.schemas.weather import WeatherForecast


class StubOrchestrator:
    provider_names = ["gemini"]

    async def plan_trip(self, request):
        return PlannedTripResult(
            data=TripPlanData(
                itinerary=[
                    {
                        "day": "Day 1",
                        "activities": [
                            {
                                "time": "09:00 AM",
                                "name": "Wat Arun",
                                "location": "Bangkok",
                                "price": 15,
                                "duration": "2 hours",
                                "description": "Start the trip with a riverside temple visit.",
                            }
                        ],
                    }
                ]
            ),
            meta=TripPlanMeta(
                provider="gemini",
                model="gemini-2.5-flash",
                attempted_providers=["gemini"],
            ),
        )

    async def edit_trip(self, request):
        return PlannedTripResult(
            data=TripPlanData(
                itinerary=[
                    {
                        "day": "Day 1",
                        "activities": [
                            {
                                "time": "09:00 AM",
                                "name": "Wat Arun",
                                "location": "Bangkok",
                                "price": 15,
                                "duration": "2 hours",
                                "description": "Start the trip with a riverside temple visit.",
                            },
                            {
                                "time": "07:00 PM",
                                "name": "Night market",
                                "location": "Bangkok",
                                "price": 10,
                                "duration": "2 hours",
                                "description": "Street food and shopping.",
                            },
                        ],
                    }
                ]
            ),
            meta=TripPlanMeta(
                provider="gemini",
                model="gemini-2.5-flash",
                attempted_providers=["gemini"],
            ),
        )


class StubWeatherService:
    async def get_weather_for_trip(self, request):
        return WeatherForecast.model_validate(
            {
                "location": f"{request.destination}, IN",
                "daily": [
                    {
                        "date": request.trip_start or "2026-04-01",
                        "summary": "Warm and sunny",
                        "temperature_max_c": 31,
                        "temperature_min_c": 20,
                    }
                ],
            }
        )


def test_plan_trip_endpoint_returns_envelope() -> None:
    app = create_app()
    app.dependency_overrides[get_orchestrator] = lambda: StubOrchestrator()
    client = TestClient(app)

    response = client.post(
        "/api/trips/plan",
        json={
            "destination": "Bangkok",
            "number_of_days": 3,
            "trip_start": "2026-04-01",
            "itinerary_type": "Adventure",
            "budget": "Medium",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["itinerary"][0]["day"] == "Day 1"
    assert payload["meta"]["provider"] == "gemini"


def test_weather_endpoint_returns_forecast_envelope() -> None:
    app = create_app()
    app.dependency_overrides[get_weather_service] = lambda: StubWeatherService()
    client = TestClient(app)

    response = client.get(
        "/api/trips/weather",
        params={
            "destination": "Jaipur",
            "number_of_days": 3,
            "trip_start": "2026-04-01",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["location"] == "Jaipur, IN"


def test_edit_trip_endpoint_returns_updated_itinerary() -> None:
    app = create_app()
    app.dependency_overrides[get_orchestrator] = lambda: StubOrchestrator()
    client = TestClient(app)

    response = client.post(
        "/api/trips/edit",
        json={
            "trip_request": {
                "destination": "Bangkok",
                "number_of_days": 3,
                "trip_start": "2026-04-01",
                "itinerary_type": "Adventure",
                "budget": "Medium",
            },
            "current_itinerary": {
                "itinerary": [
                    {
                        "day": "Day 1",
                        "activities": [
                            {
                                "time": "09:00 AM",
                                "name": "Wat Arun",
                                "location": "Bangkok",
                                "price": 15,
                                "duration": "2 hours",
                                "description": "Start the trip with a riverside temple visit.",
                            }
                        ],
                    }
                ]
            },
            "message": "Add an evening market stop",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["itinerary"][0]["activities"][-1]["name"] == "Night market"
