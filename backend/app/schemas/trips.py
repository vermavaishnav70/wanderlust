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


class ProviderActivity(BaseModel):
    model_config = ConfigDict(extra="forbid")

    time: str
    name: str
    location: str
    price: int | float | str
    duration: str
    description: str


class ProviderDayPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    day: str
    activities: list[ProviderActivity]


class ProviderTripPlanData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    itinerary: list[ProviderDayPlan]


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


class TripEditRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    trip_request: TripPlanRequest
    current_itinerary: TripPlanData
    message: str = Field(min_length=1, max_length=2000)

    @field_validator("message", mode="before")
    @classmethod
    def normalize_message(cls, value: str) -> str:
        normalized_value = str(value).strip()
        if not normalized_value:
            raise ValueError("must not be empty")
        return normalized_value


def normalize_provider_trip_plan(payload: ProviderTripPlanData | TripPlanData | dict) -> TripPlanData:
    if isinstance(payload, TripPlanData):
        return payload

    provider_data = (
        payload
        if isinstance(payload, ProviderTripPlanData)
        else ProviderTripPlanData.model_validate(payload)
    )

    normalized_days: list[dict] = []
    for day_index, day in enumerate(provider_data.itinerary[:10], start=1):
        normalized_activities: list[dict] = []
        for activity in day.activities[:8]:
            normalized_activities.append(
                {
                    "time": _normalize_text(activity.time, "09:00 AM"),
                    "name": _normalize_text(activity.name, "Planned activity"),
                    "location": _normalize_text(activity.location, "TBD"),
                    "price": _normalize_price(activity.price),
                    "duration": _normalize_text(activity.duration, "1 hour"),
                    "description": _normalize_text(
                        activity.description,
                        "Enjoy this stop as part of the trip.",
                    ),
                }
            )

        if not normalized_activities:
            normalized_activities.append(
                {
                    "time": "09:00 AM",
                    "name": "Planned activity",
                    "location": "TBD",
                    "price": 0,
                    "duration": "1 hour",
                    "description": "Enjoy this stop as part of the trip.",
                }
            )

        normalized_days.append(
            {
                "day": _normalize_day_label(day.day, day_index),
                "activities": normalized_activities,
            }
        )

    if not normalized_days:
        raise ValueError("Provider returned an empty itinerary.")

    return TripPlanData.model_validate({"itinerary": normalized_days})


def _normalize_text(value: str | None, fallback: str) -> str:
    normalized_value = str(value or "").strip()
    return normalized_value[:600] if normalized_value else fallback


def _normalize_price(value: int | float | str) -> int:
    try:
        normalized_value = int(float(value))
    except (TypeError, ValueError):
        return 0

    return max(normalized_value, 0)


def _normalize_day_label(value: str | None, day_index: int) -> str:
    normalized_value = str(value or "").strip()
    if not normalized_value:
        return f"Day {day_index}"
    if normalized_value.lower().startswith("day "):
        return normalized_value[:100]
    return normalized_value[:100]
