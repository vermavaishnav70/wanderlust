from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from app.core.logging import get_logger, log_event
from app.dependencies import (
    get_access_token,
    get_current_user,
    get_itinerary_store,
    get_orchestrator,
)
from app.schemas.auth import AuthenticatedUser
from app.schemas.itineraries import (
    DeleteItineraryData,
    DeleteItineraryResponseEnvelope,
    SavedItineraryEditRequest,
    SavedItineraryListResponseEnvelope,
    SavedItineraryResponseEnvelope,
    SavedItineraryVersionPreviewResponseEnvelope,
    SaveItineraryRequest,
)
from app.schemas.trips import TripEditRequest, TripPlanMeta
from app.services.itinerary_store import ItineraryStoreError, SupabaseItineraryStore
from app.services.orchestrator import TripPlanningError, TripPlanningOrchestrator

router = APIRouter(prefix="/api/itineraries", tags=["itineraries"])
logger = get_logger("wanderlust.itineraries")


@router.post(
    "",
    response_model=SavedItineraryResponseEnvelope,
    status_code=status.HTTP_201_CREATED,
)
async def create_saved_itinerary(
    payload: SaveItineraryRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    access_token: str = Depends(get_access_token),
    itinerary_store: SupabaseItineraryStore = Depends(get_itinerary_store),
) -> SavedItineraryResponseEnvelope | JSONResponse:
    try:
        result = await itinerary_store.create_itinerary(
            user=current_user,
            access_token=access_token,
            payload=payload,
        )
        return SavedItineraryResponseEnvelope(
            success=True,
            data=result,
            error=None,
            meta=None,
        )
    except ItineraryStoreError as error:
        log_event(
            logger,
            "error",
            "create_saved_itinerary_failed",
            status_code=error.status_code,
            detail=error.user_message,
        )
        return JSONResponse(
            status_code=error.status_code,
            content=SavedItineraryResponseEnvelope(
                success=False,
                data=None,
                error=error.user_message,
                meta=None,
            ).model_dump(mode="json"),
        )


@router.delete("/{itinerary_id}", response_model=DeleteItineraryResponseEnvelope)
async def delete_saved_itinerary(
    itinerary_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    access_token: str = Depends(get_access_token),
    itinerary_store: SupabaseItineraryStore = Depends(get_itinerary_store),
) -> DeleteItineraryResponseEnvelope | JSONResponse:
    try:
        deleted = await itinerary_store.delete_itinerary(
            user=current_user,
            access_token=access_token,
            itinerary_id=itinerary_id,
        )
        if not deleted:
            return JSONResponse(
                status_code=404,
                content=DeleteItineraryResponseEnvelope(
                    success=False,
                    data=None,
                    error="Saved itinerary not found.",
                    meta=None,
                ).model_dump(mode="json"),
            )
        return DeleteItineraryResponseEnvelope(
            success=True,
            data=DeleteItineraryData(
                deleted=True,
                itinerary_id=itinerary_id,
            ),
            error=None,
            meta=None,
        )
    except ItineraryStoreError as error:
        log_event(
            logger,
            "error",
            "delete_saved_itinerary_failed",
            status_code=error.status_code,
            itinerary_id=itinerary_id,
            detail=error.user_message,
        )
        return JSONResponse(
            status_code=error.status_code,
            content=DeleteItineraryResponseEnvelope(
                success=False,
                data=None,
                error=error.user_message,
                meta=None,
            ).model_dump(mode="json"),
        )


@router.get("", response_model=SavedItineraryListResponseEnvelope)
async def list_saved_itineraries(
    current_user: AuthenticatedUser = Depends(get_current_user),
    access_token: str = Depends(get_access_token),
    itinerary_store: SupabaseItineraryStore = Depends(get_itinerary_store),
) -> SavedItineraryListResponseEnvelope | JSONResponse:
    try:
        result = await itinerary_store.list_itineraries(
            user=current_user,
            access_token=access_token,
        )
        return SavedItineraryListResponseEnvelope(
            success=True,
            data=result,
            error=None,
            meta=None,
        )
    except ItineraryStoreError as error:
        log_event(
            logger,
            "error",
            "list_saved_itineraries_failed",
            status_code=error.status_code,
            detail=error.user_message,
        )
        return JSONResponse(
            status_code=error.status_code,
            content=SavedItineraryListResponseEnvelope(
                success=False,
                data=None,
                error=error.user_message,
                meta=None,
            ).model_dump(mode="json"),
        )


@router.get("/{itinerary_id}", response_model=SavedItineraryResponseEnvelope)
async def get_saved_itinerary(
    itinerary_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    access_token: str = Depends(get_access_token),
    itinerary_store: SupabaseItineraryStore = Depends(get_itinerary_store),
) -> SavedItineraryResponseEnvelope | JSONResponse:
    try:
        result = await itinerary_store.get_itinerary(
            user=current_user,
            access_token=access_token,
            itinerary_id=itinerary_id,
        )
        if not result:
            return JSONResponse(
                status_code=404,
                content=SavedItineraryResponseEnvelope(
                    success=False,
                    data=None,
                    error="Saved itinerary not found.",
                    meta=None,
                ).model_dump(mode="json"),
            )
        return SavedItineraryResponseEnvelope(
            success=True,
            data=result,
            error=None,
            meta=None,
        )
    except ItineraryStoreError as error:
        log_event(
            logger,
            "error",
            "get_saved_itinerary_failed",
            status_code=error.status_code,
            itinerary_id=itinerary_id,
            detail=error.user_message,
        )
        return JSONResponse(
            status_code=error.status_code,
            content=SavedItineraryResponseEnvelope(
                success=False,
                data=None,
                error=error.user_message,
                meta=None,
            ).model_dump(mode="json"),
        )


@router.post("/{itinerary_id}/edit", response_model=SavedItineraryResponseEnvelope)
async def edit_saved_itinerary(
    itinerary_id: str,
    payload: SavedItineraryEditRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    access_token: str = Depends(get_access_token),
    itinerary_store: SupabaseItineraryStore = Depends(get_itinerary_store),
    orchestrator: TripPlanningOrchestrator = Depends(get_orchestrator),
) -> SavedItineraryResponseEnvelope | JSONResponse:
    try:
        current_detail = await itinerary_store.get_itinerary(
            user=current_user,
            access_token=access_token,
            itinerary_id=itinerary_id,
        )
        if not current_detail:
            return JSONResponse(
                status_code=404,
                content=SavedItineraryResponseEnvelope(
                    success=False,
                    data=None,
                    error="Saved itinerary not found.",
                    meta=None,
                ).model_dump(mode="json"),
            )

        updated_result = await orchestrator.edit_trip(
            TripEditRequest(
                trip_request=current_detail.trip_request,
                current_itinerary=current_detail.current_itinerary,
                message=payload.message,
            )
        )
        saved_detail = await itinerary_store.save_edit(
            user=current_user,
            access_token=access_token,
            itinerary_id=itinerary_id,
            message=payload.message,
            updated_itinerary=updated_result.data,
        )
        return SavedItineraryResponseEnvelope(
            success=True,
            data=saved_detail,
            error=None,
            meta=updated_result.meta,
        )
    except TripPlanningError as error:
        log_event(
            logger,
            "error",
            "edit_saved_itinerary_failed",
            status_code=error.status_code,
            itinerary_id=itinerary_id,
            detail=error.user_message,
            attempted_providers=error.meta.attempted_providers,
            request_id=error.meta.request_id,
        )
        return JSONResponse(
            status_code=error.status_code,
            content=SavedItineraryResponseEnvelope(
                success=False,
                data=None,
                error=error.user_message,
                meta=error.meta,
            ).model_dump(mode="json"),
        )
    except ItineraryStoreError as error:
        log_event(
            logger,
            "error",
            "saved_itinerary_store_failed",
            status_code=error.status_code,
            itinerary_id=itinerary_id,
            detail=error.user_message,
        )
        return JSONResponse(
            status_code=error.status_code,
            content=SavedItineraryResponseEnvelope(
                success=False,
                data=None,
                error=error.user_message,
                meta=TripPlanMeta(attempted_providers=[]),
            ).model_dump(mode="json"),
        )


@router.get(
    "/{itinerary_id}/versions/{version_number}",
    response_model=SavedItineraryVersionPreviewResponseEnvelope,
)
async def get_saved_itinerary_version(
    itinerary_id: str,
    version_number: int,
    current_user: AuthenticatedUser = Depends(get_current_user),
    access_token: str = Depends(get_access_token),
    itinerary_store: SupabaseItineraryStore = Depends(get_itinerary_store),
) -> SavedItineraryVersionPreviewResponseEnvelope | JSONResponse:
    try:
        preview = await itinerary_store.get_version_preview(
            user=current_user,
            access_token=access_token,
            itinerary_id=itinerary_id,
            version_number=version_number,
        )
        return SavedItineraryVersionPreviewResponseEnvelope(
            success=True,
            data=preview,
            error=None,
            meta=None,
        )
    except ItineraryStoreError as error:
        log_event(
            logger,
            "error",
            "get_saved_itinerary_version_failed",
            status_code=error.status_code,
            itinerary_id=itinerary_id,
            version_number=version_number,
            detail=error.user_message,
        )
        return JSONResponse(
            status_code=error.status_code,
            content=SavedItineraryVersionPreviewResponseEnvelope(
                success=False,
                data=None,
                error=error.user_message,
                meta=None,
            ).model_dump(mode="json"),
        )


@router.post(
    "/{itinerary_id}/versions/{version_number}/restore",
    response_model=SavedItineraryResponseEnvelope,
)
async def restore_saved_itinerary_version(
    itinerary_id: str,
    version_number: int,
    current_user: AuthenticatedUser = Depends(get_current_user),
    access_token: str = Depends(get_access_token),
    itinerary_store: SupabaseItineraryStore = Depends(get_itinerary_store),
) -> SavedItineraryResponseEnvelope | JSONResponse:
    try:
        restored_detail = await itinerary_store.restore_version(
            user=current_user,
            access_token=access_token,
            itinerary_id=itinerary_id,
            version_number=version_number,
        )
        return SavedItineraryResponseEnvelope(
            success=True,
            data=restored_detail,
            error=None,
            meta=None,
        )
    except ItineraryStoreError as error:
        log_event(
            logger,
            "error",
            "restore_saved_itinerary_version_failed",
            status_code=error.status_code,
            itinerary_id=itinerary_id,
            version_number=version_number,
            detail=error.user_message,
        )
        return JSONResponse(
            status_code=error.status_code,
            content=SavedItineraryResponseEnvelope(
                success=False,
                data=None,
                error=error.user_message,
                meta=None,
            ).model_dump(mode="json"),
        )
