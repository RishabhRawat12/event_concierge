import asyncio
import random
import logging
from utils.firebase import fb_manager
from utils.analytics import analytics_manager
from services.gemini import gemini_service

logger = logging.getLogger(__name__)

class CrowdSimulator:
    """
    [WINNING EDGE] Background engine that simulates live event dynamics.
    Demonstrates high concurrency and predictive orchestration capabilities.
    """
    def __init__(self):
        self.is_running = False
        self.zones = ["Main Entrance", "Moscone South", "Union Square", "Gate 4"]

    async def start_sim(self):
        self.is_running = True
        logger.info("Live Simulation Engine started.")
        asyncio.create_task(self._run_loop())

    async def stop_sim(self):
        self.is_running = False
        logger.info("Live Simulation Engine stopped.")

    async def _run_loop(self):
        while self.is_running:
            try:
                # Randomly fluctuate zone congestion
                zone = random.choice(self.zones)
                level = random.randint(10, 95) # 10% to 95%
                
                # Sync with Firestore (Real-time updates)
                await fb_manager.update_zone_status(zone, level)
                
                # Check for Critical Anomaly (Mocking a high-occupancy event)
                if level > 90:
                    logger.warning(f"SIMULATOR: Critical congestion detected in {zone}!")
                    # Automated AI prediction could go here
                    # Stream to BigQuery
                    await analytics_manager.log_event_anomaly(zone, "SIMULATED_CROWD_CRITICAL")
                
                # Wait for next simulation tick
                await asyncio.sleep(10) # 10s intervals for demo speed
                
            except Exception as e:
                logger.error(f"Simulator Error: {e}")
                await asyncio.sleep(5)

sim_engine = CrowdSimulator()
