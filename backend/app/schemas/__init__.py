"""Pydantic schemas for the trip planner backend."""
from app.schemas.auth import AuthenticatedUser
from app.schemas.itineraries import (
    DeleteItineraryData,
    DeleteItineraryResponseEnvelope,
    SavedItineraryDetail,
    SavedItineraryEditRequest,
    SavedItineraryListResponseEnvelope,
    SavedItineraryMessage,
    SavedItineraryMessageInput,
    SavedItineraryResponseEnvelope,
    SavedItinerarySummary,
    SavedItineraryVersion,
    SavedItineraryVersionPreview,
    SavedItineraryVersionPreviewResponseEnvelope,
    SaveItineraryRequest,
)
from app.schemas.weather import WeatherDay, WeatherForecast, WeatherResponseEnvelope
