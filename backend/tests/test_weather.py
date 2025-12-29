from datetime import date
import asyncio

from app.schemas.trips import TripPlanRequest
from app.schemas.weather import WeatherForecast
from app.services.weather import WeatherService


class StubWeatherService(WeatherService):
    async def get_weather_for_trip(self, request: TripPlanRequest) -> WeatherForecast | None:
        return WeatherForecast.model_validate(
            {
                "location": f"{request.destination}, IN",
                "daily": [
                    {
                        "date": request.trip_start or date(2026, 4, 1),
                        "summary": "Warm and sunny",
                        "temperature_max_c": 31,
                        "temperature_min_c": 20,
                    }
                ],
            }
        )


def test_weather_service_summary_formats_trip_context() -> None:
    service = StubWeatherService()
    request = TripPlanRequest(
        destination="Jaipur",
        number_of_days=3,
        trip_start=date(2026, 4, 1),
        itinerary_type="Adventure",
        budget="Medium",
    )

    summary = asyncio.run(service.summarize_weather_for_trip(request))

    assert "Warm and sunny" in summary
    assert "31C" in summary
