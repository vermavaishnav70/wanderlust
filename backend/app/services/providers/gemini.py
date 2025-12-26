from typing import Any

from langchain_google_genai import ChatGoogleGenerativeAI

from app.schemas.trips import ProviderTripPlanData
from app.services.providers.base import AIProvider, ProviderError


class GeminiProvider(AIProvider):
    def __init__(self, api_key: str, model_name: str, timeout_s: float):
        super().__init__(name="gemini", model_name=model_name)
        self._structured_model = ChatGoogleGenerativeAI(
            model=model_name,
            api_key=api_key,
            temperature=0.4,
            request_timeout=timeout_s,
        ).with_structured_output(
            ProviderTripPlanData,
            method="json_schema",
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
            raise ProviderError(f"Gemini request failed: {error}") from error

        if hasattr(response, "model_dump"):
            return response.model_dump(mode="json")
        if isinstance(response, dict):
            return response

        raise ProviderError("Gemini returned an invalid structured response.")
