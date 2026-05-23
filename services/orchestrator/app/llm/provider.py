"""Minimal LLM provider interface placeholder.

The original code used a factory/provider abstraction. During the revert we
removed the full factory but leave a tiny interface so cloud client modules
can import `LLMProvider` without errors. Implementations should provide the
async `generate` / `stream_generate` and `health_check` methods.
"""

from abc import ABC, abstractmethod
from typing import AsyncIterator, Optional


class LLMProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        raise NotImplementedError()

    @abstractmethod
    async def stream_generate(self, prompt: str, **kwargs) -> AsyncIterator[str]:
        raise NotImplementedError()

    @abstractmethod
    async def health_check(self) -> bool:
        raise NotImplementedError()


def deprecated_placeholder():
    raise RuntimeError("LLM provider factory removed. Use GroqRouter or MistralReasoner directly.")
