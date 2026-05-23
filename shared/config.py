"""
shared/config.py - Centralized, type-safe configuration management
Loads environment variables for all ATLAS services using Pydantic Settings.
"""

import os
from typing import Literal, Optional, List
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings

ROOT_DOTENV = str(Path(__file__).resolve().parents[1] / ".env")

class LLMConfig(BaseSettings):
    """LLM settings for cloud-first configuration"""
    # Routing (fast intent classification)
    routing_model: str = "llama-3.1-70b-versatile"
    routing_api_key: Optional[str] = None
    openrouter_api_key: Optional[str] = None
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    # Reasoning / fallback provider (Mistral)
    reasoning_model: str = "mistral-large"
    mistral_api_key: Optional[str] = None

    # Embeddings provider (for memory service)
    embedding_provider: Literal["openai", "cohere", "huggingface"] = "openai"
    openai_api_key: Optional[str] = None

    class Config:
        env_prefix = "LLM_"
        env_file = ROOT_DOTENV
        extra = "ignore"


class SharedConfig(BaseSettings):
    """Application-wide global configuration"""
    env: Literal["dev", "staging", "prod"] = "dev"
    log_level: str = "INFO"
    debug: bool = False
    
    # LLM Settings Nested Configuration
    llm: LLMConfig = Field(default_factory=LLMConfig)
    
    # Centralized Port Assignments & Paths
    orchestrator_host: str = "0.0.0.0"
    orchestrator_port: int = 9000
    orchestrator_url: str = "http://localhost:9000"
    
    google_mcp_host: str = "0.0.0.0"
    google_mcp_port: int = 8000
    google_mcp_url: str = "http://localhost:8000"
    google_mcp_api_prefix: str = "/api"
    
    memory_host: str = "0.0.0.0"
    memory_port: int = 8002
    memory_url: str = "http://localhost:8002"
    
    sentinel_host: str = "0.0.0.0"
    sentinel_port: int = 9001
    sentinel_url: str = "http://localhost:9001"
    
    # Integrations Config
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None
    google_redirect_uri: str = "http://localhost:8000/auth/callback"
    frontend_url: str = "http://localhost:3000"
    
    # DB configurations
    redis_host: str = "localhost"
    redis_port: int = 6379
    
    chroma_host: str = "localhost"
    chroma_port: int = 8001
    
    # Service specific parameters (Backward-compatibility)
    allowed_origins: str = "http://localhost:5173,http://localhost:3000,http://localhost:8000"
    max_workers: int = 15
    cache_ttl: int = 3600
    
    class Config:
        env_file = ROOT_DOTENV
        case_sensitive = False
        extra = "ignore"

    @property
    def allowed_origins_list(self) -> List[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]

    @property
    def gmail_api_base(self) -> str:
        return f"{self.google_mcp_url.strip()}{self.google_mcp_api_prefix.strip()}"

# Global Config Singleton
global_config = SharedConfig()
