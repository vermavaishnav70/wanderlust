from functools import lru_cache

from app.core.config import Settings, get_settings as _get_settings
from app.services.orchestrator import TripPlanningOrchestrator
from app.services.providers.factory import build_provider_chain


def get_settings() -> Settings:
    return _get_settings()


@lru_cache(maxsize=1)
def get_orchestrator() -> TripPlanningOrchestrator:
    settings = get_settings()
    providers = build_provider_chain(settings)
    return TripPlanningOrchestrator(providers=providers)
