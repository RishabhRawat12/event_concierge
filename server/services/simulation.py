"""
Background crowd simulation engine for real-time venue dynamics.
Demonstrates concurrent tactical Twin orchestration and predictive alerting.
"""
import asyncio
import logging
import random
from typing import List, Optional
from infrastructure.firebase import fb_manager
from infrastructure.analytics import analytics_manager

logger = logging.getLogger(__name__)

class CrowdSimulator:
    """Simulates dynamic attendee movement and architectural congestion."""

    def __init__(self) -> None:
        self._zones: List[str] = ["Main Entrance", "Moscone South", "Union Square", "Gate 4"]
        self._running_event: asyncio.Event = asyncio.Event()
        self._task: Optional[asyncio.Task] = None

    async def start_sim(self) -> None:
        """Starts the background orchestration loop if not already active."""
        if self._task and not self._task.done():
            return
            
        self._running_event.set()
        self._task = asyncio.create_task(self._run_loop())
        logger.info("Simulation Engine synchronized (Tactical Dynamics active).")

    async def stop_sim(self) -> None:
        """Gracefully terminates the background simulation loop."""
        self._running_event.clear()
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            finally:
                self._task = None
        logger.info("Simulation Engine released.")

    async def _run_loop(self) -> None:
        """The core simulation kernel; fluctuates zone data every 10 seconds."""
        while self._running_event.is_set():
            try:
                zone = random.choice(self._zones)
                level = random.randint(10, 95)
                
                # Bi-directional sync with digital twin persistence
                await fb_manager.update_zone_status(zone, level)
                
                if level > 90:
                    logger.debug(f"SIMULATOR: Tactical Anomaly detected in {zone} ({level}%).")
                    await analytics_manager.log_event_anomaly(zone, "SIMULATED_CROWD_CRITICAL")
                
                await asyncio.sleep(10)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Simulator Orchestration failure: {e}")
                await asyncio.sleep(5)

sim_engine = CrowdSimulator()

