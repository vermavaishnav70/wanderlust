import json

from app.services.providers.base import ProviderError


def extract_json_object(raw_text: str) -> dict:
    cleaned_text = raw_text.strip().replace("```json", "").replace("```", "").strip()

    try:
        parsed = json.loads(cleaned_text)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    decoder = json.JSONDecoder()
    for index, character in enumerate(cleaned_text):
        if character != "{":
            continue

        try:
            parsed, _ = decoder.raw_decode(cleaned_text[index:])
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            continue

    raise ProviderError("Provider did not return valid JSON.")
