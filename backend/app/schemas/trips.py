from datetime import date, datetime, timezone
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator

TripBudget = Literal["Low", "Medium", "High"]


class Activity(BaseModel):
    model_config = ConfigDict(extra="forbid")

    time: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=200)
    location: str = Field(min_length=1, max_length=200)
    price: int = Field(ge=0)
    duration: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=1, max_length=600)


class DayPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    day: str = Field(min_length=1, max_length=100)
    activities: list[Activity] = Field(min_length=1, max_length=8)


class TripPlanData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    itinerary: list[DayPlan] = Field(min_length=1, max_length=10)


class TripPlanMeta(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: str = Field(default_factory=lambda: str(uuid4()))
    provider: str | None = None
    model: str | None = None
    attempted_providers: list[str] = Field(default_factory=list)
    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc)
    )


class TripPlanRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    destination: str = Field(min_length=2, max_length=120)
    number_of_days: int = Field(ge=1, le=10)
    trip_start: date | None = None
    itinerary_type: str = Field(min_length=2, max_length=80)
    budget: TripBudget

    @field_validator("destination", "itinerary_type", mode="before")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        normalized_value = str(value).strip()
        if not normalized_value:
            raise ValueError("must not be empty")
        return normalized_value


class TripPlanResponseEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool
    data: TripPlanData | None = None
    error: str | None = None
    meta: TripPlanMeta | None = None


class PlannedTripResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    data: TripPlanData
    meta: TripPlanMeta
