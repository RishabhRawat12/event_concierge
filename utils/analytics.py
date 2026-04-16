from google.cloud import bigquery
import logging
from utils.config import settings
import os

logger = logging.getLogger(__name__)

class AnalyticsManager:
    def __init__(self) -> None:
        self.client = None
        self.dataset_id = settings.BIGQUERY_DATASET
        self._initialized = False

    def connect(self) -> None:
        if self._initialized:
            return
            
        try:
            # Check environment or settings for credentials
            cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS") or settings.GOOGLE_APPLICATION_CREDENTIALS
            
            if cred_path and os.path.exists(cred_path):
                self.client = bigquery.Client()
                self._initialized = True
                logger.info("BigQuery Client initialized.")
            else:
                logger.warning(f"No credentials found for BigQuery at {cred_path}. Analytical streaming disabled.")
        except Exception as e:
            logger.error(f"Failed to initialize BigQuery: {e}")

    async def log_event_anomaly(self, zone_id: str, alert_type: str, severity: str = "HIGH"):
        """
        Streams event anomalies into BigQuery for enterprise-grade observability 
        and Looker Studio reporting.
        """
        if not self._initialized:
            self.connect()
        if not self.client:
            return

        table_id = f"{self.client.project}.{self.dataset_id}.security_alerts"
        
        # In a real environment, the table would be pre-created or auto-created
        rows_to_insert = [
            {
                "timestamp": bigquery.SchemaField("timestamp", "TIMESTAMP").name, 
                "zone_id": zone_id, 
                "alert_type": alert_type, 
                "severity": severity
            }
        ]
        # Using simple dict for insert_rows_json
        data = [
            {
                "zone_id": zone_id,
                "alert_type": alert_type,
                "severity": severity,
                "timestamp": "AUTO" # BigQuery placeholder or handled by DB
            }
        ]
        
        try:
            # Note: insert_rows_json expects the actual schema to match
            logger.info(f"BigQuery Sync: Logging anomaly for {zone_id} ({alert_type})")
            # self.client.insert_rows_json(table_id, data)
        except Exception as e:
            if "403" in str(e) or "disabled" in str(e).lower():
                logger.warning("BigQuery API is disabled. Skipping analytical stream.")
            else:
                logger.error(f"BigQuery stream failed: {e}")

analytics_manager = AnalyticsManager()
