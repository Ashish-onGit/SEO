"""Abstract AI provider interface."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class AIProvider(ABC):
    """Base interface for all AI generation providers."""

    @abstractmethod
    def generate_text(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        """Generate a text completion for a prompt."""
        pass

    @abstractmethod
    def generate_structured_json(self, prompt: str, schema_description: str) -> Dict[str, Any]:
        """Generate structured JSON output adhering to a schema."""
        pass
