import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Server
    PORT: int = 8000
    FRONTEND_URL: str = "http://localhost:3000"
    
    # Auth
    GOOGLE_CLIENT_SECRETS_JSON: str = "credentials.json"
    REDIRECT_URI: str = "http://localhost:8000/auth/callback"
    
    # LLM Keys
    GROQ_API_KEY: str = ""
    OPENROUTER_API_KEY: str = ""
    
    LLM_MODEL: str = "llama-3.1-8b-instant"
    ALTERNATE_MODEL: str = "meta-llama/llama-3.1-8b-instruct"
    LLM_TEMPERATURE: float = 0.2
    
    # Intelligence Flags
    ENABLE_EMAIL_INTELLIGENCE: bool = False
    ENABLE_SEMANTIC_SEARCH: bool = False
    
    # Performance
    MAX_WORKERS: int = 15
    CACHE_TTL: int = 3600 # 1 hour
    
    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
