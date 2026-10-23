"""AI provider package with factory loader."""

import logging
from typing import Optional
from ai.provider import AIProvider
from ai.gemini_provider import GeminiProvider
from ai.mock_provider import MockAIProvider
from config.settings import settings

logger = logging.getLogger(__name__)


def get_ai_provider(provider_type: Optional[str] = None) -> AIProvider:
    """Instantiate and return the configured AI provider."""
    selected_type = (provider_type or settings.ai_provider).lower()

    if selected_type == "gemini":
        if settings.gemini_api_key:
            return GeminiProvider(api_key=settings.gemini_api_key, model=settings.gemini_model)
        else:
            logger.warning(
                "GEMINI_API_KEY is not configured in .env. Falling back to MockAIProvider for dry run / test."
            )
            return MockAIProvider()
    elif selected_type == "mock":
        return MockAIProvider()
    else:
        logger.warning(f"Unknown AI provider '{selected_type}'. Defaulting to MockAIProvider.")
        return MockAIProvider()


__all__ = ["AIProvider", "GeminiProvider", "MockAIProvider", "get_ai_provider"]
