from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.trips import TripBudget, TripPlanData, TripPlanMeta, TripPlanRequest

SavedItineraryStatus = Literal["saved"]
SavedMessageRole = Literal["user", "assistant"]


class SavedItineraryMessageInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: SavedMessageRole
    content: str = Field(min_length=1, max_length=2000)

    @field_validator("content", mode="before")
    @classmethod
    def normalize_content(cls, value: str) -> str:
        normalized_value = str(value).strip()
        if not normalized_value:
            raise ValueError("must not be empty")
        return normalized_value


class SavedItineraryMessage(SavedItineraryMessageInput):
    created_at: datetime


class SaveItineraryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    trip_request: TripPlanRequest
    current_itinerary: TripPlanData
    client_request_id: str = Field(min_length=1, max_length=128)
    title: str | None = Field(default=None, min_length=1, max_length=140)
    summary: str | None = Field(default=None, min_length=1, max_length=400)
    messages: list[SavedItineraryMessageInput] = Field(default_factory=list, max_length=50)

    @field_validator("client_request_id", "title", "summary", mode="before")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized_value = str(value).strip()
        if not normalized_value:
            return None
        return normalized_value


class SavedItinerarySummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1, max_length=128)
    destination: str = Field(min_length=2, max_length=120)
    number_of_days: int = Field(ge=1, le=10)
    trip_start: date | None = None
    itinerary_type: str = Field(min_length=2, max_length=80)
    budget: TripBudget
    title: str = Field(min_length=1, max_length=140)
    summary: str | None = Field(default=None, max_length=400)
    status: SavedItineraryStatus = "saved"
    current_version: int = Field(ge=1)
    created_at: datetime
    updated_at: datetime


class SavedItineraryDetail(SavedItinerarySummary):
    trip_request: TripPlanRequest
    current_itinerary: TripPlanData
    messages: list[SavedItineraryMessage] = Field(default_factory=list)
    versions: list["SavedItineraryVersion"] = Field(default_factory=list)


class SavedItineraryVersion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version_number: int = Field(ge=1)
    created_at: datetime


class SavedItineraryVersionPreview(BaseModel):
    model_config = ConfigDict(extra="forbid")

    itinerary_id: str = Field(min_length=1, max_length=128)
    version_number: int = Field(ge=1)
    created_at: datetime
    itinerary: TripPlanData


class SavedItineraryEditRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str = Field(min_length=1, max_length=2000)

    @field_validator("message", mode="before")
    @classmethod
    def normalize_message(cls, value: str) -> str:
        normalized_value = str(value).strip()
        if not normalized_value:
            raise ValueError("must not be empty")
        return normalized_value


class SavedItineraryResponseEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool
    data: SavedItineraryDetail | None = None
    error: str | None = None
    meta: TripPlanMeta | None = None


class SavedItineraryListResponseEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool
    data: list[SavedItinerarySummary] | None = None
    error: str | None = None
    meta: TripPlanMeta | None = None


class DeleteItineraryData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    deleted: bool
    itinerary_id: str = Field(min_length=1, max_length=128)


class DeleteItineraryResponseEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool
    data: DeleteItineraryData | None = None
    error: str | None = None
    meta: TripPlanMeta | None = None


class SavedItineraryVersionPreviewResponseEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool
    data: SavedItineraryVersionPreview | None = None
    error: str | None = None
    meta: TripPlanMeta | None = None
