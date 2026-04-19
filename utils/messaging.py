import logging
import json
from typing import Any, Dict, Optional
from utils.config import settings

# Production-grade Orchestration: Cloud Pub/Sub
try:
    from google.cloud import pubsub_v1
    HAS_PUBSUB = True
except ImportError:
    HAS_PUBSUB = False

logger = logging.getLogger(__name__)

class PubSubManager:
    """
    Manages decoupled event distribution via Google Cloud Pub/Sub.
    Enables highly scalable, event-driven situational awareness.
    """

    def __init__(self):
        self.project_id = settings.GOOGLE_CLOUD_PROJECT
        self._publisher: Optional["pubsub_v1.PublisherClient"] = None
        if HAS_PUBSUB:
            try:
                self._publisher = pubsub_v1.PublisherClient()
            except Exception as e:
                logger.debug(f"Pub/Sub Initialization Bypass: {e}")

    def publish_event(self, topic_id: str, data: Dict[str, Any]) -> bool:
        """
        Publishes a tactical event to a specific Pub/Sub topic.
        Implements a non-blocking safe fallback for local/dev environments.
        """
        if not self._publisher:
            logger.debug(f"Local Event Capture (No Pub/Sub): {topic_id} -> {data}")
            return True

        topic_path = self._publisher.topic_path(self.project_id, topic_id)
        payload = json.dumps(data).encode("utf-8")

        try:
            future = self._publisher.publish(topic_path, payload)
            # We don't block on the future to preserve low-latency responsiveness
            future.add_done_callback(lambda f: self._log_publish_status(topic_id, f))
            return True
        except Exception as e:
            logger.error(f"Pub/Sub Routing Failure ({topic_id}): {e}")
            return False

    def _log_publish_status(self, topic_id: str, future: Any) -> None:
        try:
            message_id = future.result()
            logger.debug(f"Pub/Sub Success: {topic_id} [MsgID: {message_id}]")
        except Exception as e:
            logger.error(f"Async Publish Error for {topic_id}: {e}")

messaging_manager = PubSubManager()
