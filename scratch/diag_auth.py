from utils.config import settings
import os

print(f"--- AUTH DIAGNOSTICS ---")
print(f"GOOGLE_CLOUD_PROJECT: {settings.GOOGLE_CLOUD_PROJECT}")
print(f"ACTIVE STAFF TOKEN: {settings.STAFF_SECRET_TOKEN}")
print(f"GCP CREDENTIALS SET: {bool(os.getenv('GOOGLE_APPLICATION_CREDENTIALS'))}")
print(f"--- END DIAGNOSTICS ---")
