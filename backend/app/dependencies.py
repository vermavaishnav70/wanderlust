from functools import lru_cache

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import Settings, get_settings as _get_settings
from app.core.logging import get_logger, log_event
from app.schemas.auth import AuthenticatedUser
from app.services.orchestrator import TripPlanningOrchestrator
from app.services.auth import AuthServiceError, SupabaseAuthService
from app.services.itinerary_store import SupabaseItineraryStore
from app.services.providers.factory import build_provider_chain
from app.services.weather import WeatherService

_bearer_scheme = HTTPBearer(auto_error=False)
logger = get_logger("wanderlust.auth")


def get_settings() -> Settings:
    return _get_settings()


@lru_cache(maxsize=1)
def get_orchestrator() -> TripPlanningOrchestrator:
    settings = get_settings()
    providers = build_provider_chain(settings)
    return TripPlanningOrchestrator(
        providers=providers,
        weather_service=WeatherService(),
    )


@lru_cache(maxsize=1)
def get_weather_service() -> WeatherService:
    return WeatherService()


@lru_cache(maxsize=1)
def get_auth_service() -> SupabaseAuthService:
    settings = get_settings()
    return SupabaseAuthService(
        supabase_url=settings.supabase_url,
        supabase_anon_key=settings.supabase_anon_key,
    )


@lru_cache(maxsize=1)
def get_itinerary_store() -> SupabaseItineraryStore:
    settings = get_settings()
    return SupabaseItineraryStore(
        supabase_url=settings.supabase_url,
        supabase_anon_key=settings.supabase_anon_key,
    )


def get_access_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> str:
    if not credentials or credentials.scheme.lower() != "bearer":
        log_event(
            logger,
            "warning",
            "missing_bearer_token",
        )
        raise HTTPException(status_code=401, detail="Authentication required.")
    return credentials.credentials


def get_current_user(
    access_token: str = Depends(get_access_token),
    auth_service: SupabaseAuthService = Depends(get_auth_service),
) -> AuthenticatedUser:
    try:
        return auth_service.get_user_for_token(access_token)
    except AuthServiceError as error:
        log_event(
            logger,
            "warning",
            "auth_verification_failed",
            status_code=error.status_code,
            detail=error.user_message,
        )
        raise HTTPException(status_code=error.status_code, detail=error.user_message) from error
