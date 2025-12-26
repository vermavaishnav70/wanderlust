import asyncio

from app.schemas.trips import (
    TripEditRequest,
    TripPlanData,
    TripPlanRequest,
    normalize_provider_trip_plan,
)
from app.services.orchestrator import TripPlanningError, TripPlanningOrchestrator
from app.services.providers.base import AIProvider, ProviderError
from app.services.providers.groq import _resolve_structured_output_method
from app.services.weather import WeatherService


class FakeProvider(AIProvider):
    def __init__(self, name: str, model_name: str, payload: dict | None = None, error: Exception | None = None):
        super().__init__(name=name, model_name=model_name)
        self._payload = payload
        self._error = error
        self.last_prompt = ""

    async def generate_itinerary(self, *, system_instruction: str, prompt: str) -> dict:
        self.last_prompt = prompt
        if self._error:
            raise self._error
        return self._payload or {}


class FakeWeatherService(WeatherService):
    async def summarize_weather_for_trip(self, request: TripPlanRequest) -> str:
        return f"{request.destination} will be warm and sunny."


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


def test_orchestrator_includes_weather_context_when_available() -> None:
    request = TripPlanRequest(
        destination="Bangkok",
        number_of_days=3,
        itinerary_type="Adventure",
        budget="Low",
    )
    provider = FakeProvider(
        "gemini",
        "gemini-2.5-flash",
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
    )
    orchestrator = TripPlanningOrchestrator(
        providers=[provider],
        weather_service=FakeWeatherService(),
    )

    asyncio.run(orchestrator.plan_trip(request))

    assert "Weather context:" in provider.last_prompt
    assert "warm and sunny" in provider.last_prompt


def test_orchestrator_edits_trip_with_current_itinerary_context() -> None:
    request = TripEditRequest(
        trip_request=TripPlanRequest(
            destination="Bangkok",
            number_of_days=3,
            itinerary_type="Adventure",
            budget="Low",
        ),
        current_itinerary=TripPlanData(
            itinerary=[
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
        ),
        message="Add an evening market stop",
    )
    provider = FakeProvider(
        "gemini",
        "gemini-2.5-flash",
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
                        },
                        {
                            "time": "07:00 PM",
                            "name": "Night market visit",
                            "location": "Bangkok",
                            "price": 10,
                            "duration": "2 hours",
                            "description": "Browse stalls and eat street food.",
                        },
                    ],
                }
            ]
        },
    )
    orchestrator = TripPlanningOrchestrator(providers=[provider])

    result = asyncio.run(orchestrator.edit_trip(request))

    assert result.data.itinerary[0].activities[-1].name == "Night market visit"
    assert "Current itinerary JSON:" in provider.last_prompt
    assert "Add an evening market stop" in provider.last_prompt


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
        assert (
            error.user_message
            == "We couldn't generate an itinerary right now. Please try again."
        )
    else:
        raise AssertionError("TripPlanningError was not raised")


def test_normalize_provider_trip_plan_coerces_loose_values() -> None:
    normalized = normalize_provider_trip_plan(
        {
            "itinerary": [
                {
                    "day": "2026-04-01",
                    "activities": [
                        {
                            "time": "08:00",
                            "name": " Breakfast ",
                            "location": "",
                            "price": "199.9",
                            "duration": "90 minutes",
                            "description": "",
                        }
                    ],
                }
            ]
        }
    )

    assert normalized.itinerary[0].day == "2026-04-01"
    assert normalized.itinerary[0].activities[0].name == "Breakfast"
    assert normalized.itinerary[0].activities[0].location == "TBD"
    assert normalized.itinerary[0].activities[0].price == 199
    assert normalized.itinerary[0].activities[0].description == "Enjoy this stop as part of the trip."


def test_groq_method_resolution_prefers_json_schema_for_supported_models() -> None:
    assert _resolve_structured_output_method("openai/gpt-oss-120b") == "json_schema"
    assert _resolve_structured_output_method("llama-3.3-70b-versatile") == "json_mode"
