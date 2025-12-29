from datetime import date, timedelta

import httpx

from app.schemas.trips import TripPlanRequest
from app.schemas.weather import WeatherForecast


WEATHER_CODE_MAP = {
    0: "Clear skies",
    1: "Mostly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Foggy",
    48: "Rime fog",
    51: "Light drizzle",
    53: "Drizzle",
    55: "Dense drizzle",
    61: "Light rain",
    63: "Rain showers",
    65: "Heavy rain",
    71: "Light snow",
    73: "Snow",
    75: "Heavy snow",
    80: "Light rain showers",
    81: "Rain showers",
    82: "Heavy rain showers",
    95: "Thunderstorms",
}


class WeatherServiceError(Exception):
    pass


class WeatherService:
    async def get_weather_for_trip(self, request: TripPlanRequest) -> WeatherForecast | None:
        if request.trip_start is None:
            return None

        async with httpx.AsyncClient(timeout=12.0) as client:
            geocode_response = await client.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={
                    "name": request.destination,
                    "count": 1,
                    "language": "en",
                    "format": "json",
                },
            )
            if geocode_response.status_code != 200:
                raise WeatherServiceError("Unable to reach the weather location service.")

            geocode_data = geocode_response.json()
            place = (geocode_data.get("results") or [None])[0]
            if not place:
                raise WeatherServiceError(
                    f"No weather location match found for {request.destination}."
                )

            forecast_response = await client.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": place["latitude"],
                    "longitude": place["longitude"],
                    "daily": "weather_code,temperature_2m_max,temperature_2m_min",
                    "timezone": "auto",
                    "start_date": request.trip_start.isoformat(),
                    "end_date": (
                        request.trip_start + timedelta(days=request.number_of_days - 1)
                    ).isoformat(),
                },
            )
            if forecast_response.status_code != 200:
                raise WeatherServiceError("Unable to fetch the weather forecast.")

        forecast_data = forecast_response.json()
        daily_data = forecast_data.get("daily", {})
        dates = daily_data.get("time", [])
        codes = daily_data.get("weather_code", [])
        highs = daily_data.get("temperature_2m_max", [])
        lows = daily_data.get("temperature_2m_min", [])

        return WeatherForecast.model_validate(
            {
                "location": f"{request.destination}, {place['country_code']}",
                "daily": [
                    {
                        "date": current_date,
                        "summary": WEATHER_CODE_MAP.get(current_code, "Mixed weather"),
                        "temperature_max_c": current_high,
                        "temperature_min_c": current_low,
                    }
                    for current_date, current_code, current_high, current_low in zip(
                        dates, codes, highs, lows
                    )
                ],
            }
        )

    async def summarize_weather_for_trip(self, request: TripPlanRequest) -> str:
        forecast = await self.get_weather_for_trip(request)
        if not forecast or not forecast.daily:
            return ""

        return "; ".join(
            [
                (
                    f"{current_day.date.isoformat()}: {current_day.summary}, "
                    f"highs around {round(current_day.temperature_max_c)}C and "
                    f"lows near {round(current_day.temperature_min_c)}C"
                )
                for current_day in forecast.daily[:3]
            ]
        )
