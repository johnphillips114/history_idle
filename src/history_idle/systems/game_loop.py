"""Main game loop and update system."""

import time
from typing import Optional
from ..models.civilization import Civilization
from .resource_system import ResourceProductionSystem, ResourceConsumptionSystem


class GameLoop:
    """Manages the main game update loop."""

    def __init__(self, civilization: Civilization):
        self.civilization = civilization
        self.resource_production = ResourceProductionSystem()
        self.resource_consumption = ResourceConsumptionSystem()
        self.is_running = False
        self.last_tick_time = time.time()

    def tick(self, delta_time: Optional[float] = None) -> dict:
        """Perform one game tick update.

        Args:
            delta_time: Time elapsed in seconds. If None, uses real time.

        Returns:
            Dictionary with update information
        """
        if delta_time is None:
            current_time = time.time()
            delta_time = current_time - self.last_tick_time
            self.last_tick_time = current_time

        update_info = self.civilization.update(delta_time)

        return update_info

    def process_offline_time(self, offline_seconds: float) -> dict:
        """Process time that elapsed while the game was closed.

        This simulates the game continuing to run offline.

        Args:
            offline_seconds: Number of seconds elapsed offline

        Returns:
            Summary of what happened during offline time
        """
        # Cap offline time to prevent extreme gains (e.g., max 24 hours)
        max_offline_time = 24 * 60 * 60  # 24 hours
        offline_seconds = min(offline_seconds, max_offline_time)

        # Process in chunks to handle resource caps properly
        chunk_size = 60.0  # 1 minute chunks
        chunks = int(offline_seconds / chunk_size)
        remaining = offline_seconds % chunk_size

        summary = {
            "offline_time": offline_seconds,
            "resources_gained": {},
            "techs_completed": [],
            "buildings_completed": [],
            "population_change": 0
        }

        # Process full chunks
        for _ in range(chunks):
            update = self.tick(chunk_size)
            self._accumulate_summary(summary, update)

        # Process remaining time
        if remaining > 0:
            update = self.tick(remaining)
            self._accumulate_summary(summary, update)

        return summary

    def _accumulate_summary(self, summary: dict, update: dict) -> None:
        """Accumulate update info into summary."""
        summary["techs_completed"].extend(update.get("completed_techs", []))
        summary["buildings_completed"].extend(update.get("completed_buildings", []))
        summary["population_change"] += update.get("population_change", 0)

        # Accumulate resource changes
        for resource_id, change in update.get("resource_changes", {}).items():
            summary["resources_gained"][resource_id] = \
                summary["resources_gained"].get(resource_id, 0.0) + change

    def start(self) -> None:
        """Start the game loop."""
        self.is_running = True
        self.last_tick_time = time.time()

    def stop(self) -> None:
        """Stop the game loop."""
        self.is_running = False
