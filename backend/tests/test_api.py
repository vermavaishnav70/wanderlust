from fastapi.testclient import TestClient

from app.dependencies import get_orchestrator
from app.main import create_app
from app.schemas.trips import PlannedTripResult, TripPlanData, TripPlanMeta


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
