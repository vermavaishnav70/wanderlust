from dataclasses import dataclass
from functools import lru_cache
import os

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(usecwd=True), override=False)


def _split_csv(raw_value: str | None) -> list[str]:
    if not raw_value:
        return ["http://localhost:5173"]

    return [value.strip() for value in raw_value.split(",") if value.strip()]


@dataclass(frozen=True)
class Settings:
    api_title: str = "AI Trip Planner API"
    api_version: str = "0.1.0"
    cors_origins: list[str] | None = None
    gemini_api_key: str | None = None
    groq_api_key: str | None = None
    primary_provider: str = "gemini"
    fallback_provider: str = "groq"
    request_timeout_s: float = 35.0
    gemini_model: str = "gemini-2.5-flash"
    groq_model: str = "llama-3.3-70b-versatile"

    def __post_init__(self) -> None:
        if self.cors_origins is None:
            object.__setattr__(
                self,
                "cors_origins",
                _split_csv(os.getenv("CORS_ORIGINS")),
            )

    @property
    def provider_order(self) -> list[str]:
        ordered_names: list[str] = []
        for provider_name in [self.primary_provider, self.fallback_provider]:
            normalized_name = provider_name.strip().lower()
            if normalized_name and normalized_name not in ordered_names:
                ordered_names.append(normalized_name)

        return ordered_names


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(
        gemini_api_key=os.getenv("GEMINI_API_KEY"),
        groq_api_key=os.getenv("GROQ_API_KEY"),
        primary_provider=os.getenv("PRIMARY_PROVIDER", "gemini"),
        fallback_provider=os.getenv("FALLBACK_PROVIDER", "groq"),
        request_timeout_s=float(os.getenv("REQUEST_TIMEOUT_S", "35")),
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
        groq_model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
    )
