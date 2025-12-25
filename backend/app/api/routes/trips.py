from fastapi import APIRouter, Depends, status
from fastapi import Query
from fastapi.responses import JSONResponse

from app.core.logging import get_logger, log_event
from app.dependencies import get_orchestrator, get_weather_service
from app.schemas.trips import TripEditRequest, TripPlanRequest, TripPlanResponseEnvelope
from app.schemas.weather import WeatherResponseEnvelope
from app.services.orchestrator import TripPlanningError, TripPlanningOrchestrator
from app.services.weather import WeatherService, WeatherServiceError

router = APIRouter(prefix="/api/trips", tags=["trips"])
logger = get_logger("wanderlust.trips")


@router.post("/plan", response_model=TripPlanResponseEnvelope)
async def plan_trip(
    payload: TripPlanRequest,
    orchestrator: TripPlanningOrchestrator = Depends(get_orchestrator),
) -> TripPlanResponseEnvelope | JSONResponse:
    try:
        result = await orchestrator.plan_trip(payload)
        return TripPlanResponseEnvelope(
            success=True,
            data=result.data,
            error=None,
            meta=result.meta,
        )
    except TripPlanningError as error:
        log_event(
            logger,
            "error",
            "plan_trip_failed",
            status_code=error.status_code,
            detail=error.user_message,
            attempted_providers=error.meta.attempted_providers,
            request_id=error.meta.request_id,
        )
        error_payload = TripPlanResponseEnvelope(
            success=False,
            data=None,
            error=error.user_message,
            meta=error.meta,
        )
        return JSONResponse(
            status_code=error.status_code,
            content=error_payload.model_dump(mode="json"),
        )


@router.post("/edit", response_model=TripPlanResponseEnvelope)
async def edit_trip(
    payload: TripEditRequest,
    orchestrator: TripPlanningOrchestrator = Depends(get_orchestrator),
) -> TripPlanResponseEnvelope | JSONResponse:
    try:
        result = await orchestrator.edit_trip(payload)
        return TripPlanResponseEnvelope(
            success=True,
            data=result.data,
            error=None,
            meta=result.meta,
        )
    except TripPlanningError as error:
        log_event(
            logger,
            "error",
            "edit_trip_failed",
            status_code=error.status_code,
            detail=error.user_message,
            attempted_providers=error.meta.attempted_providers,
            request_id=error.meta.request_id,
        )
        error_payload = TripPlanResponseEnvelope(
            success=False,
            data=None,
            error=error.user_message,
            meta=error.meta,
        )
        return JSONResponse(
            status_code=error.status_code,
            content=error_payload.model_dump(mode="json"),
        )


@router.get("/providers", status_code=status.HTTP_200_OK)
async def list_configured_providers(
    orchestrator: TripPlanningOrchestrator = Depends(get_orchestrator),
) -> dict[str, list[str]]:
    return {"providers": orchestrator.provider_names}


@router.get("/weather", response_model=WeatherResponseEnvelope)
async def get_trip_weather(
    destination: str = Query(min_length=2, max_length=120),
    number_of_days: int = Query(ge=1, le=10),
    trip_start: str | None = Query(default=None),
    weather_service: WeatherService = Depends(get_weather_service),
) -> WeatherResponseEnvelope | JSONResponse:
    try:
        payload = TripPlanRequest(
            destination=destination,
            number_of_days=number_of_days,
            trip_start=trip_start,
            itinerary_type="Weather Preview",
            budget="Medium",
        )
        result = await weather_service.get_weather_for_trip(payload)
        return WeatherResponseEnvelope(
            success=True,
            data=result,
            error=None,
            meta=None,
        )
    except WeatherServiceError as error:
        return JSONResponse(
            status_code=502,
            content=WeatherResponseEnvelope(
                success=False,
                data=None,
                error=str(error),
                meta=None,
            ).model_dump(mode="json"),
        )
