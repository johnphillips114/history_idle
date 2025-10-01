import time
from typing import Optional
from ..models.civilization import Civilization
from .resource_system import ResourceProductionSystem, ResourceConsumptionSystem


class GameLoop:
    def __init__(self, civilization: Civilization):
        self.civilization = civilization
        self.resource_production = ResourceProductionSystem()
        self.resource_consumption = ResourceConsumptionSystem()
        self.is_running = False
        self.last_tick_time = time.time()

    def tick(self, delta_time: Optional[float] = None) -> dict:
        if delta_time is None:
            current_time = time.time()
            delta_time = current_time - self.last_tick_time
            self.last_tick_time = current_time

        update_info = self.civilization.update(delta_time)

        return update_info

    def process_offline_time(self, offline_seconds: float) -> dict:
        max_offline_time = 24 * 60 * 60  # 24 hours
        offline_seconds = min(offline_seconds, max_offline_time)

        chunk_size = 60.0  # 1 minute chunks
        chunks = int(offline_seconds / chunk_size)
        remaining = offline_seconds % chunk_size

        summary = {
            "offline_time": offline_seconds,
            "resources_gained": {},
            "techs_completed": [],
            "buildings_completed": [],
            "population_change": 0,
        }

        for _ in range(chunks):
            update = self.tick(chunk_size)
            self._accumulate_summary(summary, update)

        if remaining > 0:
            update = self.tick(remaining)
            self._accumulate_summary(summary, update)

        return summary

    def _accumulate_summary(self, summary: dict, update: dict) -> None:
        summary["techs_completed"].extend(update.get("completed_techs", []))
        summary["buildings_completed"].extend(update.get("completed_buildings", []))
        summary["population_change"] += update.get("population_change", 0)

        for resource_id, change in update.get("resource_changes", {}).items():
            summary["resources_gained"][resource_id] = (
                summary["resources_gained"].get(resource_id, 0.0) + change
            )

    def start(self) -> None:
        self.is_running = True
        self.last_tick_time = time.time()

    def stop(self) -> None:
        self.is_running = False
