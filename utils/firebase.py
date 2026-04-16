import firebase_admin
from firebase_admin import credentials, firestore
import logging
from utils.config import settings
import os

logger = logging.getLogger(__name__)

class FirebaseManager:
    def __init__(self) -> None:
        self.db = None
        self._initialized = False

    def connect(self) -> None:
        if self._initialized:
            return
            
        try:
            cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "service-account.json")
            if os.path.exists(cred_path):
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred, {
                    'projectId': settings.GOOGLE_CLOUD_PROJECT
                })
                self.db = firestore.client()
                self._initialized = True
                logger.info("Firebase Admin SDK initialized successfully.")
            else:
                logger.warning(f"Service account file not found at {cred_path}. Firestore will not be available.")
        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {e}")

    def get_db(self):
        if not self._initialized:
            self.connect()
        return self.db

    async def update_zone_status(self, zone_id: str, congestion_level: int, alert: str = None):
        """
        Updates the congestion level for a specific zone in real-time Firestore.
        Gracefully handles cases where the API is disabled (GCP 403).
        """
        db = self.get_db()
        if not db:
            return

        try:
            doc_ref = db.collection("zones").document(zone_id)
            data = {
                "congestion_level": congestion_level,
                "last_updated": firestore.SERVER_TIMESTAMP
            }
            if alert:
                data["active_alert"] = alert
                
            doc_ref.set(data, merge=True)
        except Exception as e:
            # Catch 403 (Disabled) and 404 (Not Found/Not Initialized) gracefully
            err_msg = str(e).lower()
            if "403" in err_msg or "disabled" in err_msg or "404" in err_msg or "not exist" in err_msg:
                logger.info(f"Cloud Firestore: Database not initialized yet. (Running in Demo Mode for {zone_id})")
            else:
                logger.error(f"Firestore sync failed: {e}")

fb_manager = FirebaseManager()
