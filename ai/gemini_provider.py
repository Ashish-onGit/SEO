"""Gemini AI Provider implementation with retries, exponential backoff, and JSON mode."""

import json
import time
import random
import logging
from typing import Dict, Any, Optional
import requests

from ai.provider import AIProvider
from config.settings import settings

logger = logging.getLogger(__name__)


class GeminiAPIError(Exception):
    """Raised when Gemini API encounters an unrecoverable error."""
    pass


class GeminiProvider(AIProvider):
    """Gemini AI Provider using official Google Generative Language REST API."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.gemini_api_key
        self.model = model or settings.gemini_model
        self.base_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"

    def _execute_with_retry(self, payload: Dict[str, Any], max_retries: int = 3) -> Dict[str, Any]:
        """Send request to Gemini API with exponential backoff and jitter."""
        if not self.api_key:
            raise GeminiAPIError("GEMINI_API_KEY is not configured in environment or settings.")

        url = f"{self.base_url}?key={self.api_key}"
        headers = {"Content-Type": "application/json"}

        for attempt in range(1, max_retries + 1):
            try:
                resp = requests.post(url, headers=headers, json=payload, timeout=60.0)
                if resp.status_code == 200:
                    return resp.json()

                # Handle rate limits (429) or transient server errors (500, 503)
                if resp.status_code in (429, 500, 502, 503, 504):
                    wait_time = (2 ** attempt) + random.uniform(0.5, 1.5)
                    logger.warning(
                        f"Gemini API returned status {resp.status_code}. "
                        f"Attempt {attempt}/{max_retries}. Backing off for {wait_time:.1f}s."
                    )
                    time.sleep(wait_time)
                    continue

                # Permanent client error (e.g. 400 Bad Request, 401 Unauthorized)
                error_body = resp.text[:400]
                raise GeminiAPIError(f"Gemini API error (HTTP {resp.status_code}): {error_body}")

            except requests.RequestException as e:
                wait_time = (2 ** attempt) + random.uniform(0.5, 1.5)
                logger.warning(f"Network error calling Gemini: {e}. Retrying in {wait_time:.1f}s...")
                time.sleep(wait_time)

        raise GeminiAPIError(f"Gemini API failed after {max_retries} attempts.")

    def generate_text(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        """Generate text using Gemini."""
        payload: Dict[str, Any] = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": 0.7,
                "topP": 0.9,
                "maxOutputTokens": 4096,
            },
        }

        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }

        response = self._execute_with_retry(payload)
        try:
            candidates = response.get("candidates", [])
            if not candidates:
                raise GeminiAPIError("No response candidates returned from Gemini.")

            content_parts = candidates[0].get("content", {}).get("parts", [])
            if not content_parts:
                raise GeminiAPIError("Empty content parts in Gemini response.")

            text = content_parts[0].get("text", "")
            return text.strip()
        except Exception as e:
            raise GeminiAPIError(f"Failed to parse Gemini response: {e}")

    def generate_structured_json(self, prompt: str, schema_description: str) -> Dict[str, Any]:
        """Generate structured JSON adhering to the specified schema."""
        augmented_prompt = (
            f"{prompt}\n\n"
            f"CRITICAL: Your output MUST be strict, valid JSON matching this schema:\n"
            f"{schema_description}\n"
            f"Do not include markdown fences, comments, or extra text."
        )

        payload: Dict[str, Any] = {
            "contents": [
                {
                    "parts": [{"text": augmented_prompt}]
                }
            ],
            "generationConfig": {
                "temperature": 0.2,  # Low temperature for strict compliance
                "responseMimeType": "application/json",
            },
        }

        response = self._execute_with_retry(payload)
        try:
            candidates = response.get("candidates", [])
            content_parts = candidates[0].get("content", {}).get("parts", [])
            text = content_parts[0].get("text", "").strip()

            # Clean any accidental code fences
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()

            return json.loads(text)
        except json.JSONDecodeError as je:
            logger.error(f"Failed to parse JSON from Gemini response: {je}\nRaw output: {text[:200]}")
            raise GeminiAPIError(f"Malformed JSON returned by Gemini: {je}")
        except Exception as e:
            raise GeminiAPIError(f"Structured JSON generation failed: {e}")
