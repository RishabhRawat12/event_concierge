import os
import logging
from typing import List, Any
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Production-grade Orchestration: GCP Secret Manager
try:
    from google.cloud import secretmanager
    HAS_SECRET_MANAGER = True
except ImportError:
    HAS_SECRET_MANAGER = False

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    GEMINI_API_KEY: str = ""
    GOOGLE_MAPS_API_KEY: str = ""
    OPENWEATHER_API_KEY: str = ""
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_TIMEOUT_SECONDS: int = 2
    STAFF_SECRET_TOKEN: str = "SUPER_SECRET_STAFF_TOKEN"
    
    # GCP Production Infrastructure
    GOOGLE_CLOUD_PROJECT: str = "promptwars-concierge"
    GOOGLE_APPLICATION_CREDENTIALS: str = "service-account.json"
    FIREBASE_PROJECT_ID: str = "promptwars-concierge"
    BIGQUERY_DATASET: str = "event_analytics"

    # Infrastructure & Access Control
    ALLOWED_ORIGINS: Any = ["http://localhost:3000", "http://127.0.0.1:3000"]
    TRUSTED_PROXIES: Any = ["127.0.0.1"]

    @field_validator("ALLOWED_ORIGINS", "TRUSTED_PROXIES", mode="before")
    @classmethod
    def parse_lists(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            return [x.strip() for x in v.split(",") if x.strip()]
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow"
    )

    def fetch_gcp_secrets(self) -> None:
        """
        Synchronizes critical credentials from GCP Secret Manager.
        Ensures production-grade security handling with local fallback redundancy.
        """
        if not HAS_SECRET_MANAGER:
            return

        client = secretmanager.SecretManagerServiceClient()
        # Mapping of local setting name to Secret Manager secret ID
        secret_map = {
            "GEMINI_API_KEY": "gemini-api-key",
            "STAFF_SECRET_TOKEN": "staff-secret-token",
            "OPENWEATHER_API_KEY": "openweather-api-key"
        }

        for setting_key, secret_id in secret_map.items():
            try:
                name = f"projects/{self.GOOGLE_CLOUD_PROJECT}/secrets/{secret_id}/versions/latest"
                response = client.access_secret_version(request={"name": name})
                secret_value = response.payload.data.decode("UTF-8")
                setattr(self, setting_key, secret_value)
                logger.info(f"GCP Synchronization: {setting_key} fetched from Secret Manager.")
            except Exception as e:
                logger.debug(f"Secret Manager Bypass: {setting_key} using local/env provider ({e}).")

settings = Settings()

# Bootstrap GCP credentials into environment for SDK usage
if settings.GOOGLE_APPLICATION_CREDENTIALS and os.path.exists(settings.GOOGLE_APPLICATION_CREDENTIALS):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = settings.GOOGLE_APPLICATION_CREDENTIALS

# Production Orchestration: Attempt secret synchronization
settings.fetch_gcp_secrets()
