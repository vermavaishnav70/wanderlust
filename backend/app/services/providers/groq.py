from typing import Any

import httpx

from app.services.providers.base import AIProvider, ProviderError
from app.services.providers.utils import extract_json_object


class GroqProvider(AIProvider):
    def __init__(self, api_key: str, model_name: str, timeout_s: float):
        super().__init__(name="groq", model_name=model_name)
        self._api_key = api_key
        self._timeout_s = timeout_s

    async def generate_itinerary(
        self,
        *,
        system_instruction: str,
        prompt: str,
    ) -> dict[str, Any]:
        payload = {
            "model": self.model_name,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.4,
        }
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=self._timeout_s) as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                json=payload,
                headers=headers,
            )

        if response.status_code >= 400:
            raise ProviderError("Groq request failed.")

        payload = response.json()
        raw_text = (
            payload.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
        )
        if not raw_text:
            raise ProviderError("Groq returned an empty response.")

        return extract_json_object(raw_text)
