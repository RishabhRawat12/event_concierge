from pydantic_settings import BaseSettings, SettingsConfigDict

import os

class Settings(BaseSettings):
    GEMINI_API_KEY: str
    GOOGLE_MAPS_API_KEY: str
    OPENWEATHER_API_KEY: str
    REDIS_URL: str = "redis://localhost:6379"  # Will be replaced with Upstash url in prod
    REDIS_TIMEOUT_SECONDS: int = 2
    STAFF_SECRET_TOKEN: str = "SUPER_SECRET_STAFF_TOKEN" # Default for local dev
    
    # Winning Edge Settings
    GOOGLE_CLOUD_PROJECT: str = "promptwars-concierge"
    GOOGLE_APPLICATION_CREDENTIALS: str = "service-account.json"
    FIREBASE_PROJECT_ID: str = "promptwars-concierge"
    BIGQUERY_DATASET: str = "event_analytics"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow" # Permissive for hackathon variables
    )

settings = Settings()

# Ensure credentials are in the environment for official GCP SDKs
if settings.GOOGLE_APPLICATION_CREDENTIALS and os.path.exists(settings.GOOGLE_APPLICATION_CREDENTIALS):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = settings.GOOGLE_APPLICATION_CREDENTIALS
