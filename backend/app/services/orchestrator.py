from dataclasses import dataclass
from pydantic import ValidationError

from app.core.logging import get_logger, log_event
from app.schemas.trips import (
    PlannedTripResult,
    TripEditRequest,
    TripPlanMeta,
    TripPlanRequest,
    normalize_provider_trip_plan,
)
from app.services.prompts import SYSTEM_INSTRUCTION, build_trip_edit_prompt, build_trip_prompt
from app.services.providers.base import AIProvider, ProviderError
from app.services.weather import WeatherService, WeatherServiceError

logger = get_logger("wanderlust.orchestrator")


@dataclass(frozen=True)
class TripPlanningError(Exception):
    user_message: str
    status_code: int
    meta: TripPlanMeta


class TripPlanningOrchestrator:
    def __init__(self, providers: list[AIProvider], weather_service: WeatherService | None = None):
        self._providers = providers
        self._weather_service = weather_service

    @property
    def provider_names(self) -> list[str]:
        return [provider.name for provider in self._providers]

    async def plan_trip(self, request: TripPlanRequest) -> PlannedTripResult:
        if not self._providers:
            raise TripPlanningError(
                user_message="No AI providers are configured on the backend.",
                status_code=503,
                meta=TripPlanMeta(attempted_providers=[]),
            )

        weather_summary = ""
        if self._weather_service:
            try:
                weather_summary = await self._weather_service.summarize_weather_for_trip(
                    request
                )
            except WeatherServiceError as error:
                log_event(
                    logger,
                    "warning",
                    "weather_context_unavailable",
                    destination=request.destination,
                    detail=str(error),
                )

        prompt = build_trip_prompt(request, weather_summary)
        attempted_providers: list[str] = []
        provider_failures: list[str] = []
        request_id = TripPlanMeta().request_id
        last_error: Exception | None = None

        for provider in self._providers:
            attempted_providers.append(provider.name)
            try:
                provider_response = await provider.generate_itinerary(
                    system_instruction=SYSTEM_INSTRUCTION,
                    prompt=prompt,
                )
                data = normalize_provider_trip_plan(provider_response)
                meta = TripPlanMeta(
                    request_id=request_id,
                    provider=provider.name,
                    model=provider.model_name,
                    attempted_providers=attempted_providers,
                )
                return PlannedTripResult(data=data, meta=meta)
            except (ProviderError, ValidationError, ValueError) as error:
                last_error = error
                provider_failures.append(f"{provider.name}: {error}")
                log_event(
                    logger,
                    "error",
                    "trip_provider_failed",
                    provider=provider.name,
                    detail=str(error),
                )

        raise TripPlanningError(
            user_message="We couldn't generate an itinerary right now. Please try again.",
            status_code=502,
            meta=TripPlanMeta(
                request_id=request_id,
                attempted_providers=attempted_providers,
            ),
        ) from last_error

    async def edit_trip(self, request: TripEditRequest) -> PlannedTripResult:
        if not self._providers:
            raise TripPlanningError(
                user_message="No AI providers are configured on the backend.",
                status_code=503,
                meta=TripPlanMeta(attempted_providers=[]),
            )

        weather_summary = ""
        if self._weather_service:
            try:
                weather_summary = await self._weather_service.summarize_weather_for_trip(
                    request.trip_request
                )
            except WeatherServiceError as error:
                log_event(
                    logger,
                    "warning",
                    "weather_context_unavailable",
                    destination=request.trip_request.destination,
                    detail=str(error),
                )

        prompt = build_trip_edit_prompt(request, weather_summary)
        attempted_providers: list[str] = []
        provider_failures: list[str] = []
        request_id = TripPlanMeta().request_id
        last_error: Exception | None = None

        for provider in self._providers:
            attempted_providers.append(provider.name)
            try:
                provider_response = await provider.generate_itinerary(
                    system_instruction=SYSTEM_INSTRUCTION,
                    prompt=prompt,
                )
                data = normalize_provider_trip_plan(provider_response)
                meta = TripPlanMeta(
                    request_id=request_id,
                    provider=provider.name,
                    model=provider.model_name,
                    attempted_providers=attempted_providers,
                )
                return PlannedTripResult(data=data, meta=meta)
            except (ProviderError, ValidationError, ValueError) as error:
                last_error = error
                provider_failures.append(f"{provider.name}: {error}")
                log_event(
                    logger,
                    "error",
                    "trip_edit_provider_failed",
                    provider=provider.name,
                    detail=str(error),
                )

        raise TripPlanningError(
            user_message="We couldn't update the itinerary right now. Please try again.",
            status_code=502,
            meta=TripPlanMeta(
                request_id=request_id,
                attempted_providers=attempted_providers,
            ),
        ) from last_error
