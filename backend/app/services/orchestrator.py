from dataclasses import dataclass
from pydantic import ValidationError

from app.schemas.trips import PlannedTripResult, TripPlanData, TripPlanMeta, TripPlanRequest
from app.services.prompts import SYSTEM_INSTRUCTION, build_trip_prompt
from app.services.providers.base import AIProvider, ProviderError


@dataclass(frozen=True)
class TripPlanningError(Exception):
    user_message: str
    status_code: int
    meta: TripPlanMeta


class TripPlanningOrchestrator:
    def __init__(self, providers: list[AIProvider]):
        self._providers = providers

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

        prompt = build_trip_prompt(request)
        attempted_providers: list[str] = []
        request_id = TripPlanMeta().request_id
        last_error: Exception | None = None

        for provider in self._providers:
            attempted_providers.append(provider.name)
            try:
                provider_response = await provider.generate_itinerary(
                    system_instruction=SYSTEM_INSTRUCTION,
                    prompt=prompt,
                )
                data = TripPlanData.model_validate(provider_response)
                meta = TripPlanMeta(
                    request_id=request_id,
                    provider=provider.name,
                    model=provider.model_name,
                    attempted_providers=attempted_providers,
                )
                return PlannedTripResult(data=data, meta=meta)
            except (ProviderError, ValidationError, ValueError) as error:
                last_error = error
                print(last_error)

        raise TripPlanningError(
            user_message="We couldn't generate an itinerary right now. Please try again.",
            status_code=502,
            meta=TripPlanMeta(
                request_id=request_id,
                attempted_providers=attempted_providers,
            ),
        ) from last_error
