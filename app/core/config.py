from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore" 
    )
    
    # App
    app_name: str = "AI Career Advisor"
    environment: str = "development"
    log_level: str = "INFO"
    database_url: str | None = None

    # Gemini
    gemini_api_key: str
    gemini_model: str = "gemini-3.5-flash-lite"
    gemini_embedding_model: str = "models/text-embedding-004"

    # Tavily
    tavily_api_key: str

    ## Tavily cache TTL, enforced natively via Redis key expiry (EX)
    cache_ttl_seconds: int = 86400  # 24hr

    # For CORS
    frontend_url: str

    redis_url: str
   

@lru_cache()
def get_settings() -> Settings:
    return Settings()

print("Settings loaded successfully")