from __future__ import annotations

import os
from typing import Any, Dict, Optional

from openai import AsyncOpenAI

from app.utils.logger import logger


class MistralReasoner:
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 60.0,
    ) -> None:
        self.api_key = (api_key or os.getenv("MISTRAL_API_KEY") or "").strip()
        self.model = model or os.getenv("MISTRAL_MODEL") or "mistral-large-latest"
        self.base_url = (base_url or os.getenv("MISTRAL_API_URL") or "https://api.mistral.ai/v1").rstrip("/")
        self.client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url, timeout=timeout) if self.api_key else None

    async def reason(self, context: Dict[str, Any]) -> str:
        if not self.api_key:
            raise ValueError("Mistral API key is missing.")
        if self.client is None:
            self.client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are ATLAS's fallback reasoning engine."},
                {"role": "user", "content": str(context)},
            ],
            temperature=0.2,
            max_tokens=512,
        )
        return (response.choices[0].message.content or "").strip()

    async def health_check(self) -> bool:
        if not self.api_key:
            return False
        try:
            if self.client is None:
                self.client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
            await self.client.models.list()
            return True
        except Exception as exc:
            logger.warning("[MISTRAL] health check failed: %s", exc)
            return False
