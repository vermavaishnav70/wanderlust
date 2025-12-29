from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class WeatherDay(BaseModel):
    model_config = ConfigDict(extra="forbid")

    date: date
    summary: str = Field(min_length=1, max_length=120)
    temperature_max_c: float
    temperature_min_c: float


class WeatherForecast(BaseModel):
    model_config = ConfigDict(extra="forbid")

    location: str = Field(min_length=1, max_length=120)
    daily: list[WeatherDay] = Field(default_factory=list, max_length=10)


class WeatherResponseEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool
    data: WeatherForecast | None = None
    error: str | None = None
    meta: dict | None = None
