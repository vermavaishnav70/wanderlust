from typing import Any

import httpx

from app.services.providers.base import AIProvider, ProviderError
from app.services.providers.utils import extract_json_object


class GeminiProvider(AIProvider):
    def __init__(self, api_key: str, model_name: str, timeout_s: float):
        super().__init__(name="gemini", model_name=model_name)
        self._api_key = api_key
        self._timeout_s = timeout_s
    async def generate_itinerary(
        self,
        *,
        system_instruction: str,
        prompt: str,
    ) -> dict[str, Any]:
        endpoint = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model_name}:generateContent?key={self._api_key}"
        )
        payload = {
            "system_instruction": {
                "parts": [{"text": system_instruction}],
            },
            "contents": [
                {
                    "parts": [{"text": prompt}],
                }
            ],
            "generationConfig": {
                "temperature": 0.4,
                "responseMimeType": "application/json",
            },
        }

        async with httpx.AsyncClient(timeout=self._timeout_s) as client:
            response = await client.post(endpoint, json=payload)

        if response.status_code >= 400:
            print(response.text)
            raise ProviderError("Gemini request failed.")

        payload = response.json()
        text_parts = (
            payload.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [])
        )
        raw_text = "".join(
            part.get("text", "")
            for part in text_parts
            if isinstance(part, dict)
        )
        if not raw_text:
            raise ProviderError("Gemini returned an empty response.")

        return extract_json_object(raw_text)
