from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class WorkforceTask(Enum):
    IDLE = "idle"
    RESOURCE_EXTRACTION = "resource_extraction"
    RESEARCH = "research"
    CONSTRUCTION = "construction"
    SERVICE = "service"
    MILITARY = "military"


@dataclass
class WorkforceAllocation:
    task: WorkforceTask
    resource_id: Optional[str] = None  # For resource extraction tasks
    building_id: Optional[str] = None  # For building-specific tasks
    count: int = 0

    def __hash__(self):
        return hash((self.task, self.resource_id, self.building_id))


@dataclass
class Population:
    total: int = 10  # Starting population
    growth_rate: float = 0.1  # Base growth rate per day
    happiness: float = 1.0  # 0.0 to 1.0+
    literacy: float = 0.0  # 0.0 to 1.0

    allocations: list[WorkforceAllocation] = field(default_factory=list)

    housing_capacity: int = 10

    food_consumption_per_capita: float = 0.5  # Per day

    @property
    def allocated_workers(self) -> int:
        return sum(allocation.count for allocation in self.allocations)

    @property
    def idle_workers(self) -> int:
        return max(0, self.total - self.allocated_workers)

    @property
    def can_grow(self) -> bool:
        return self.total < self.housing_capacity

    @property
    def is_overcrowded(self) -> bool:
        return self.total > self.housing_capacity

    def get_allocation(
        self,
        task: WorkforceTask,
        resource_id: Optional[str] = None,
        building_id: Optional[str] = None,
    ) -> Optional[WorkforceAllocation]:
        for allocation in self.allocations:
            if (
                allocation.task == task
                and allocation.resource_id == resource_id
                and allocation.building_id == building_id
            ):
                return allocation
        return None

    def allocate_workers(
        self,
        task: WorkforceTask,
        count: int,
        resource_id: Optional[str] = None,
        building_id: Optional[str] = None,
    ) -> int:
        if count <= 0:
            return 0

        available = self.idle_workers
        actual_count = min(count, available)

        if actual_count <= 0:
            return 0

        allocation = self.get_allocation(task, resource_id, building_id)
        if allocation is None:
            allocation = WorkforceAllocation(
                task=task, resource_id=resource_id, building_id=building_id, count=0
            )
            self.allocations.append(allocation)

        allocation.count += actual_count
        return actual_count

    def deallocate_workers(
        self,
        task: WorkforceTask,
        count: int,
        resource_id: Optional[str] = None,
        building_id: Optional[str] = None,
    ) -> int:
        allocation = self.get_allocation(task, resource_id, building_id)
        if allocation is None:
            return 0

        actual_count = min(count, allocation.count)
        allocation.count -= actual_count

        if allocation.count <= 0:
            self.allocations.remove(allocation)

        return actual_count

    def get_workers_on_task(
        self,
        task: WorkforceTask,
        resource_id: Optional[str] = None,
        building_id: Optional[str] = None,
    ) -> int:
        allocation = self.get_allocation(task, resource_id, building_id)
        return allocation.count if allocation else 0

    def get_workers_on_resource(self, resource_id: str) -> int:
        return self.get_workers_on_task(
            WorkforceTask.RESOURCE_EXTRACTION, resource_id=resource_id
        )

    def update_growth(self, delta_time: float, food_surplus: float) -> int:
        if not self.can_grow:
            return 0

        if food_surplus <= 0:
            decline_rate = abs(food_surplus) / (
                self.total * self.food_consumption_per_capita
            )
            decline = max(1, int(self.total * decline_rate * delta_time))
            self.total = max(1, self.total - decline)
            return -decline

        growth_modifier = self.happiness * (1.0 + food_surplus / 100.0)
        growth_chance = self.growth_rate * growth_modifier * delta_time

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

        if self.is_overcrowded:
            overcrowding_penalty = (
                self.total - self.housing_capacity
            ) / self.housing_capacity
            base_happiness -= overcrowding_penalty * 0.5

        self.happiness = max(0.0, min(2.0, base_happiness))

    def calculate_food_consumption(self) -> float:
        return self.total * self.food_consumption_per_capita

    def calculate_research_output(self, base_rate: float = 1.0) -> float:
        research_workers = self.get_workers_on_task(WorkforceTask.RESEARCH)
        literacy_bonus = 1.0 + self.literacy
        return research_workers * base_rate * literacy_bonus
