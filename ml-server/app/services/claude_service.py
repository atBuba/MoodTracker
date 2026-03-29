import json
import logging
import re
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class ClaudeService:
    """Wrapper over OpenRouter API (OpenAI-compatible chat completions)."""

    def __init__(self) -> None:
        self._base_url = settings.openrouter_base_url
        self._api_key = settings.openrouter_api_key
        self._model = settings.openrouter_llm_model
        self._max_tokens = settings.openrouter_max_tokens

    async def analyze(self, system_prompt: str, user_message: str) -> str:
        """Send a prompt via OpenRouter and return the raw text response."""
        logger.info(
            "OpenRouter API call: model=%s, message_len=%d",
            self._model,
            len(user_message),
        )

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self._base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self._model,
                    "max_tokens": self._max_tokens,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message},
                    ],
                },
            )
            response.raise_for_status()
            data = response.json()

        text = data["choices"][0]["message"]["content"]
        logger.info("OpenRouter API response received, length=%d", len(text))
        return text

    async def analyze_json(self, system_prompt: str, user_message: str) -> Any:
        """Send a prompt and parse the response as JSON."""
        raw = await self.analyze(system_prompt, user_message)
        return self._extract_json(raw)

    @staticmethod
    def _extract_json(text: str) -> Any:
        """Extract JSON from text that may be wrapped in markdown code fences."""
        match = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", text, re.DOTALL)
        if match:
            text = match.group(1).strip()
        return json.loads(text)


claude_service = ClaudeService()
