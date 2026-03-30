from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from app.dependencies import get_orchestrator
from app.schemas.trips import TripPlanRequest, TripPlanResponseEnvelope
from app.services.orchestrator import TripPlanningError, TripPlanningOrchestrator

router = APIRouter(prefix="/api/trips", tags=["trips"])


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
        print(error)
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
