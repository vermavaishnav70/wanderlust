import asyncio

from app.schemas.trips import TripPlanRequest
from app.services.orchestrator import TripPlanningError, TripPlanningOrchestrator
from app.services.providers.base import AIProvider, ProviderError


class FakeProvider(AIProvider):
    def __init__(self, name: str, model_name: str, payload: dict | None = None, error: Exception | None = None):
        super().__init__(name=name, model_name=model_name)
        self._payload = payload
        self._error = error

    async def generate_itinerary(self, *, system_instruction: str, prompt: str) -> dict:
        if self._error:
            raise self._error
        return self._payload or {}


def test_orchestrator_falls_back_to_secondary_provider() -> None:
    request = TripPlanRequest(
        destination="Bangkok",
        number_of_days=3,
        itinerary_type="Adventure",
        budget="Low",
    )
    providers = [
        FakeProvider("gemini", "gemini-2.5-flash", error=ProviderError("boom")),
        FakeProvider(
            "groq",
            "llama-3.3-70b-versatile",
            payload={
                "itinerary": [
                    {
                        "day": "Day 1",
                        "activities": [
                            {
                                "time": "09:00 AM",
                                "name": "Grand Palace",
                                "location": "Bangkok",
                                "price": 25,
                                "duration": "2 hours",
                                "description": "Explore the historic palace complex.",
                            }
                        ],
                    }
                ]
            },
        ),
    ]
    orchestrator = TripPlanningOrchestrator(providers=providers)

    result = asyncio.run(orchestrator.plan_trip(request))

    assert result.meta.provider == "groq"
    assert result.meta.attempted_providers == ["gemini", "groq"]
    assert result.data.itinerary[0].day == "Day 1"


def test_orchestrator_raises_when_no_provider_succeeds() -> None:
    request = TripPlanRequest(
        destination="Bangkok",
        number_of_days=3,
        itinerary_type="Adventure",
        budget="Low",
    )
    orchestrator = TripPlanningOrchestrator(
        providers=[FakeProvider("gemini", "gemini-2.5-flash", error=ProviderError("boom"))]
    )

    try:
        asyncio.run(orchestrator.plan_trip(request))
    except TripPlanningError as error:
        assert error.status_code == 502
        assert error.meta.attempted_providers == ["gemini"]
    else:
        raise AssertionError("TripPlanningError was not raised")
