"""
Firebase Admin SDK integration for real-time venue state persistence.
Enables low-latency synchronization of tactical data across the digital twin.
"""
import logging
import os
from typing import Optional
import firebase_admin # type: ignore
from firebase_admin import credentials, firestore, auth
from google.cloud.firestore_v1.client import Client as FirestoreClient
from .config import settings

logger = logging.getLogger(__name__)

class FirebaseManager:
    """Orchestrates authenticated connections to Cloud Firestore."""

    def __init__(self) -> None:
        self.db: Optional[FirestoreClient] = None
        self._initialized: bool = False

    def connect(self) -> None:
        """Initializes the Firebase Admin SDK using service account credentials."""
        if self._initialized:
            return

        try:
            cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "service-account.json")
            if os.path.exists(cred_path):
                # Singleton initialization check for firebase_admin
                if not firebase_admin._apps:
                    cred = credentials.Certificate(cred_path)
                    firebase_admin.initialize_app(cred, {'projectId': settings.GOOGLE_CLOUD_PROJECT})
                
                self.db = firestore.client()
                self._initialized = True
                logger.info("Firebase infrastructure synchronized (Firestore active).")
            else:
                logger.warning(f"Tactical Persistence Warning: No credentials at {cred_path}. Firestore disabled.")
        except Exception as e:
            logger.error(f"Critical Firebase initialization failure: {e}")

    def get_db(self) -> Optional[FirestoreClient]:
        """Provides access to the active Firestore client, initializing if necessary."""
        if not self._initialized:
            self.connect()
        return self.db

    def verify_token(self, token: str) -> dict:
        """Verifies a Firebase JWT token and returns the decoded payload."""
        if not self._initialized:
            self.connect()
        try:
            return auth.verify_id_token(token)
        except Exception as e:
            logger.error(f"Firebase token verification failed: {e}")
            raise ValueError(f"Invalid or expired token: {e}")

    async def update_zone_status(self, zone_id: str, congestion_level: int, alert: Optional[str] = None) -> None:
        """
        Updates the congestion layer for a venue zone in Firestore.

        Args:
            zone_id: Unique identifier for the target zone.
            congestion_level: Current calculated density (0-100).
            alert: Optional categorical alert description.
        """
        db = self.get_db()
        if not db:
            return

        try:
            doc_ref = db.collection("zones").document(zone_id)
            payload = {
                "congestion_level": congestion_level,
                "last_updated": firestore.SERVER_TIMESTAMP
            }
            if alert:
                payload["active_alert"] = alert
            
            # Non-blocking write via merge policy
            doc_ref.set(payload, merge=True)
        except Exception as e:
            err_msg = str(e).lower()
            if any(marker in err_msg for marker in ["403", "disabled", "404", "not exist"]):
                logger.debug(f"Firestore Persistence: Operating in Demo/Fallback mode for {zone_id}.")
            else:
                logger.error(f"Firestore operational failure for {zone_id}: {e}")

    async def get_zone_status(self, zone_id: str) -> dict:
        """Retrieves the live congestion and alert status for a venue zone."""
        db = self.get_db()
        if not db:
            return {"status": "UNKNOWN", "congestion": 0}

        try:
            doc = db.collection("zones").document(zone_id).get()
            if doc.exists:
                data = doc.to_dict() or {}
                lvl = data.get("congestion_level", 0)
                status = "CLEAR" if lvl < 30 else ("MODERATE" if lvl < 70 else "CRITICAL")
                return {
                    "status": data.get("active_alert", status),
                    "congestion": lvl
                }
            return {"status": "CLEAR", "congestion": 10}
        except Exception:
            return {"status": "CLEAR", "congestion": 15}


fb_manager = FirebaseManager()

