"""Population and workforce management."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class WorkforceTask(Enum):
    """Different tasks that population can be assigned to."""
    IDLE = "idle"
    RESOURCE_EXTRACTION = "resource_extraction"
    RESEARCH = "research"
    CONSTRUCTION = "construction"
    SERVICE = "service"
    MILITARY = "military"


@dataclass
class WorkforceAllocation:
    """Tracks allocation of population to different tasks."""
    task: WorkforceTask
    resource_id: Optional[str] = None  # For resource extraction tasks
    building_id: Optional[str] = None  # For building-specific tasks
    count: int = 0

    def __hash__(self):
        return hash((self.task, self.resource_id, self.building_id))


@dataclass
class Population:
    """Manages population and workforce."""
    total: int = 10  # Starting population
    growth_rate: float = 0.1  # Base growth rate per day
    happiness: float = 1.0  # 0.0 to 1.0+
    literacy: float = 0.0  # 0.0 to 1.0

    # Workforce allocations
    allocations: list[WorkforceAllocation] = field(default_factory=list)

    # Population capacity and housing
    housing_capacity: int = 10

    # Food consumption
    food_consumption_per_capita: float = 0.5  # Per day

    @property
    def allocated_workers(self) -> int:
        """Total number of allocated workers."""
        return sum(allocation.count for allocation in self.allocations)

    @property
    def idle_workers(self) -> int:
        """Number of unallocated workers."""
        return max(0, self.total - self.allocated_workers)

    @property
    def can_grow(self) -> bool:
        """Check if population can grow (has housing capacity)."""
        return self.total < self.housing_capacity

    @property
    def is_overcrowded(self) -> bool:
        """Check if population exceeds housing capacity."""
        return self.total > self.housing_capacity

    def get_allocation(self, task: WorkforceTask, resource_id: Optional[str] = None,
                      building_id: Optional[str] = None) -> Optional[WorkforceAllocation]:
        """Get a specific workforce allocation."""
        for allocation in self.allocations:
            if (allocation.task == task and
                allocation.resource_id == resource_id and
                allocation.building_id == building_id):
                return allocation
        return None

    def allocate_workers(self, task: WorkforceTask, count: int,
                        resource_id: Optional[str] = None,
                        building_id: Optional[str] = None) -> int:
        """Allocate workers to a task. Returns actual number allocated."""
        if count <= 0:
            return 0

        available = self.idle_workers
        actual_count = min(count, available)

        if actual_count <= 0:
            return 0

        # Find or create allocation
        allocation = self.get_allocation(task, resource_id, building_id)
        if allocation is None:
            allocation = WorkforceAllocation(
                task=task,
                resource_id=resource_id,
                building_id=building_id,
                count=0
            )
            self.allocations.append(allocation)

        allocation.count += actual_count
        return actual_count

    def deallocate_workers(self, task: WorkforceTask, count: int,
                          resource_id: Optional[str] = None,
                          building_id: Optional[str] = None) -> int:
        """Remove workers from a task. Returns actual number deallocated."""
        allocation = self.get_allocation(task, resource_id, building_id)
        if allocation is None:
            return 0

        actual_count = min(count, allocation.count)
        allocation.count -= actual_count

        # Remove allocation if empty
        if allocation.count <= 0:
            self.allocations.remove(allocation)

        return actual_count

    def get_workers_on_task(self, task: WorkforceTask,
                           resource_id: Optional[str] = None,
                           building_id: Optional[str] = None) -> int:
        """Get number of workers assigned to a specific task."""
        allocation = self.get_allocation(task, resource_id, building_id)
        return allocation.count if allocation else 0

    def get_workers_on_resource(self, resource_id: str) -> int:
        """Get number of workers extracting a specific resource."""
        return self.get_workers_on_task(WorkforceTask.RESOURCE_EXTRACTION, resource_id=resource_id)

    def update_growth(self, delta_time: float, food_surplus: float) -> int:
        """Update population growth based on conditions. Returns population change."""
        if not self.can_grow:
            return 0

        if food_surplus <= 0:
            # Famine - population decline
            decline_rate = abs(food_surplus) / (self.total * self.food_consumption_per_capita)
            decline = max(1, int(self.total * decline_rate * delta_time))
            self.total = max(1, self.total - decline)
            return -decline

        # Growth based on food surplus and happiness
        growth_modifier = self.happiness * (1.0 + food_surplus / 100.0)
        growth_chance = self.growth_rate * growth_modifier * delta_time

        # Simple growth model
        if growth_chance > 0:
            growth = int(growth_chance * self.total)
            if growth > 0 and self.can_grow:
                actual_growth = min(growth, self.housing_capacity - self.total)
                self.total += actual_growth
                return actual_growth

        return 0

    def update_happiness(self) -> None:
        """Update happiness based on various factors."""
        base_happiness = 0.5

        # Overcrowding penalty
        if self.is_overcrowded:
            overcrowding_penalty = (self.total - self.housing_capacity) / self.housing_capacity
            base_happiness -= overcrowding_penalty * 0.5

        # Ensure happiness stays in valid range
        self.happiness = max(0.0, min(2.0, base_happiness))

    def calculate_food_consumption(self) -> float:
        """Calculate total food consumption per time unit."""
        return self.total * self.food_consumption_per_capita

    def calculate_research_output(self, base_rate: float = 1.0) -> float:
        """Calculate research points generated by research workers."""
        research_workers = self.get_workers_on_task(WorkforceTask.RESEARCH)
        literacy_bonus = 1.0 + self.literacy
        return research_workers * base_rate * literacy_bonus
