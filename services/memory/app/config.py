import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    CHROMA_HOST: str = os.getenv("CHROMA_HOST", "localhost")
    CHROMA_PORT: int = int(os.getenv("CHROMA_PORT", 8001))
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", 6379))
    
    # Embedding model
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    
    # Memory thresholds
    TOP_K: int = 5
    SIMILARITY_THRESHOLD: float = 0.5

    class Config:
        env_file = ".env"

settings = Settings()
