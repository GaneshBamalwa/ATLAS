from pydantic_settings import BaseSettings

from typing import Optional

class Settings(BaseSettings):
    gmail_mcp_base_url: str = "http://localhost:8000"
    orchestrator_base_url: str = "http://localhost:9000"
    daemon_port: int = 9001
    daemon_host: str = "0.0.0.0"
    llm_model: str = "llama-3.1-8b-instant"
    llm_base_url: str = "https://api.groq.com/openai/v1"
    groq_api_key: Optional[str] = None
    openrouter_api_key: Optional[str] = None
    
    class Config:
        env_file = ".env"

settings = Settings()
