from app.core.config import Settings
from app.services.providers.base import AIProvider
from app.services.providers.gemini import GeminiProvider
from app.services.providers.groq import GroqProvider


def build_provider_chain(settings: Settings) -> list[AIProvider]:
    providers: list[AIProvider] = []

    for provider_name in settings.provider_order:
        if provider_name == "gemini" and settings.gemini_api_key:
            providers.append(
                GeminiProvider(
                    api_key=settings.gemini_api_key,
                    model_name=settings.gemini_model,
                    timeout_s=settings.request_timeout_s,
                )
            )
        elif provider_name == "groq" and settings.groq_api_key:
            providers.append(
                GroqProvider(
                    api_key=settings.groq_api_key,
                    model_name=settings.groq_model,
                    timeout_s=settings.request_timeout_s,
                )
            )

    return providers
