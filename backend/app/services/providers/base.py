from abc import ABC, abstractmethod
from typing import Any


class ProviderError(RuntimeError):
    """Raised when an upstream provider fails or returns invalid data."""
    


class AIProvider(ABC):
    def __init__(self, name: str, model_name: str):
        self.name = name
        self.model_name = model_name

    @abstractmethod
    async def generate_itinerary(
        self,
        *,
        system_instruction: str,
        prompt: str,
    ) -> dict[str, Any]:
        raise NotImplementedError
