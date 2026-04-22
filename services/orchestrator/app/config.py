"""
config.py - Central configuration management
Loads all environment variables via pydantic-settings.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


import os

class Settings(BaseSettings):
    # LLM
    openrouter_api_key: str = ""
    groq_api_key: str = ""
    llm_model: str = "meta-llama/llama-3.3-70b-instruct"
    llm_base_url: str = "https://openrouter.ai/api/v1"
    llm_call_timeout: int = 60

    # Unified MCP Backend
    gmail_mcp_base_url: str = "http://localhost:8000"
    gmail_mcp_api_prefix: str = "/api"

    # Memory Service
    memory_service_url: str = "http://localhost:8002"

    # Orchestrator Server
    orchestrator_port: int = 9000
    orchestrator_host: str = "0.0.0.0"

    # CORS
    allowed_origins: str = "http://localhost:5173,http://localhost:3000,http://localhost:8000"

    # HTTP / Retry
    mcp_call_timeout: int = 90
    max_retries: int = 3
    retry_backoff: float = 1.5

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]

    @property
    def llm_api_key(self) -> str:
        key = self.openrouter_api_key or os.environ.get("OPENROUTER_API_KEY", "")
        if not key:
            key = self.groq_api_key or os.environ.get("GROQ_API_KEY", "")
        return key.strip()

    @property
    def gmail_api_base(self) -> str:
        return f"{self.gmail_mcp_base_url.strip()}{self.gmail_mcp_api_prefix.strip()}"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
