import logging
import os
import asyncio
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from google.cloud import bigquery
from google.cloud import logging as cloud_logging
from .config import settings

logger = logging.getLogger(__name__)

class AnalyticsManager:
    """
    Orchestrates ingestion into BigQuery and Cloud Logging.
    Implements a background-flushed buffer to maintain low-latency tactical flows.
    """

    def __init__(self) -> None:
        self._bq_client: Optional[bigquery.Client] = None
        self._logging_client: Optional[cloud_logging.Client] = None
        self.dataset_id: str = settings.BIGQUERY_DATASET
        self._queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()
        self._initialized: bool = False
        self._flush_task: Optional[asyncio.Task] = None

        try:
            # Production-grade Orchestration: SDK setup
            self._logging_client = cloud_logging.Client()
            self._logging_client.setup_logging()
            self._bq_client = bigquery.Client()
            self._initialized = True
            self._flush_task = asyncio.create_task(self._periodic_flush())
            logger.info("GCP Analytics synchronized: BigQuery + Cloud Logging active.")
        except Exception as e:
            logger.debug(f"GCP Analytics Bypass: Falling back to local logging ({e})")

    async def log_event_anomaly(self, zone_id: str, alert_type: str, severity: str = "HIGH", metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Streams event anomalies into the analytical landscape.
        Narrates to Cloud Logging (structured) and buffers for BigQuery.
        """
        entry = {
            "zone_id": zone_id,
            "alert_type": alert_type,
            "severity": severity,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": json.dumps(metadata or {}),
            "environment": os.getenv("ENV", "production")
        }

        # Structured Cloud Logging: Automated ingestion for Cloud Operations
        logger.info(
            f"Tactical Anomaly: {alert_type} in {zone_id}",
            extra={"json_fields": entry}
        )

        await self._queue.put(entry)

    async def _periodic_flush(self) -> None:
        """Background task that flushes the analytical buffer periodically."""
        while True:
            try:
                await asyncio.sleep(5) # 5-second tactical batch window
                if self._queue.empty() or not self._bq_client:
                    continue

                batch: List[Dict[str, Any]] = []
                while not self._queue.empty() and len(batch) < 20:
                    batch.append(await self._queue.get())
                
                if batch:
                    table_id = f"{self._bq_client.project}.{self.dataset_id}.security_alerts"
                    # Batch injection with situational error handling
                    errors = self._bq_client.insert_rows_json(table_id, batch)
                    if errors:
                        logger.error(f"BigQuery persistence anomaly: {errors}")
                    else:
                        logger.debug(f"BigQuery Sync: {len(batch)} rows persisted to {table_id}")
            except Exception as e:
                logger.warning(f"Analytical flush bypass: {e}")
            except asyncio.CancelledError:
                break

analytics_manager = AnalyticsManager()

