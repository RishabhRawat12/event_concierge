from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    GEMINI_API_KEY: str
    GOOGLE_MAPS_API_KEY: str
    REDIS_URL: str = "redis://localhost:6379"  # Will be replaced with Upstash url in prod
    REDIS_TIMEOUT_SECONDS: int = 2

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
