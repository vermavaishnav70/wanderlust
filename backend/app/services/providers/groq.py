from typing import Any

from langchain_groq import ChatGroq

from app.schemas.trips import ProviderTripPlanData
from app.services.providers.base import AIProvider, ProviderError


class GroqProvider(AIProvider):
    def __init__(self, api_key: str, model_name: str, timeout_s: float):
        super().__init__(name="groq", model_name=model_name)
        self._method = _resolve_structured_output_method(model_name)
        self._structured_model = ChatGroq(
            model=model_name,
            api_key=api_key,
            temperature=0.2,
            timeout=timeout_s,
        ).with_structured_output(
            ProviderTripPlanData,
            method=self._method,
        )

    async def generate_itinerary(
        self,
        *,
        system_instruction: str,
        prompt: str,
    ) -> dict[str, Any]:
        try:
            response = await self._structured_model.ainvoke(
                [
                    ("system", system_instruction),
                    ("human", prompt),
                ]
            )
        except Exception as error:  # noqa: BLE001
            raise ProviderError(f"Groq request failed: {error}") from error

        if hasattr(response, "model_dump"):
            return response.model_dump(mode="json")
        if isinstance(response, dict):
            return response

        raise ProviderError("Groq returned an invalid structured response.")


def _resolve_structured_output_method(model_name: str) -> str:
    normalized_name = model_name.strip().lower()
    if (
        normalized_name.startswith("openai/gpt-oss")
        or normalized_name.startswith("moonshotai/kimi-k2")
        or normalized_name.startswith("meta-llama/llama-4")
    ):
        return "json_schema"

    return "json_mode"
