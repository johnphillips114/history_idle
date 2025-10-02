from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class BuildingCategory(Enum):
    INFRASTRUCTURE = "infrastructure"
    PRODUCTION = "production"
    STORAGE = "storage"
    CULTURAL = "cultural"
    MILITARY = "military"
    RESEARCH = "research"
    HOUSING = "housing"
    AMENITY = "amenity"


@dataclass
class ResourceCost:
    resource_id: str
    amount: float


@dataclass
class BuildingDefinition:
    id: str
    name: str
    description: str
    pedia: Optional[str] = None
    category: BuildingCategory = BuildingCategory.INFRASTRUCTURE
    construction_costs: list[ResourceCost] = field(default_factory=list)
    construction_time: float = 0.0  # Base construction time in seconds
    maintenance_costs: list[ResourceCost] = field(default_factory=list)
    required_tech: Optional[str] = None
    required_resources: list[str] = field(
        default_factory=list
    )  # Resources that must be available
    required_buildings: list[str] = field(
        default_factory=list
    )  # Buildings that must be constructed first
    max_count: int = (
        1  # Maximum number that can be built (1 = unique building, -1 = unlimited)
    )
    effects: dict[str, float] = field(default_factory=dict)
    worker_slots: int = 0  # Number of workers this building can employ
    flavors: dict[str, int] = field(default_factory=dict)  # FlavorType -> iFlavor value
    vicinity_bonus: Optional[str] = (
        None  # Resource that must be in city vicinity (available_resources)
    )
    prereq_or_terrain: list[str] = field(
        default_factory=list
    )  # List of terrain IDs (city must be on one of them)

    def __hash__(self):
        return hash(self.id)


@dataclass
class Building:
    definition: BuildingDefinition
    is_active: bool = True
    assigned_workers: int = 0

    @property
    def max_workers(self) -> int:
        return self.definition.worker_slots

    def assign_workers(self, count: int) -> int:
        max_assignment = min(count, self.max_workers)
        self.assigned_workers = max_assignment
        return self.assigned_workers

    def remove_workers(self, count: int) -> int:
        removed = min(count, self.assigned_workers)
        self.assigned_workers -= removed
        return removed


@dataclass
class BuildingConstruction:
    building_def: BuildingDefinition
    progress: float = 0.0  # Production applied so far
    required_production: float = (
        0.0  # Total production needed (set when construction starts)
    )
    is_complete: bool = False

    @property
    def progress_percentage(self) -> float:
        if self.required_production <= 0:
            return 1.0
        return min(1.0, self.progress / self.required_production)

    @property
    def remaining_production(self) -> float:
        return max(0.0, self.required_production - self.progress)

    def add_progress(self, production: float) -> bool:
        if self.is_complete:
            return True

        self.progress += production
        if self.progress >= self.required_production:
            self.is_complete = True
            return True
        return False


@dataclass
class BuildingManager:
    building_definitions: dict[str, BuildingDefinition] = field(default_factory=dict)
    buildings: list[Building] = field(default_factory=list)
    under_construction: list[BuildingConstruction] = field(default_factory=list)
    paused_construction: dict[str, BuildingConstruction] = field(
        default_factory=dict
    )  # building_id -> construction progress
    construction_queue: list[str] = field(default_factory=list)

    def add_building_definition(self, building_def: BuildingDefinition) -> None:
        self.building_definitions[building_def.id] = building_def

    def get_building_definition(self, building_id: str) -> Optional[BuildingDefinition]:
        return self.building_definitions.get(building_id)

    def get_building_count(self, building_id: str) -> int:
        return sum(1 for b in self.buildings if b.definition.id == building_id)

    def get_cost_multiplier(self, building_id: str) -> float:
        current_count = self.get_building_count(building_id)
        return 1.2**current_count

    def get_adjusted_costs(self, building_id: str) -> list:
        building_def = self.get_building_definition(building_id)
        if building_def is None:
            return []

        multiplier = self.get_cost_multiplier(building_id)
        adjusted_costs = []

        for cost in building_def.construction_costs:
            from copy import copy

            adjusted_cost = copy(cost)
            adjusted_cost.amount = cost.amount * multiplier
            adjusted_costs.append(adjusted_cost)

        return adjusted_costs

    def can_build(
        self,
        building_id: str,
        researched_techs: set[str],
        city_terrain: Optional[str] = None,
        city_available_resources: Optional[set[str]] = None,
    ) -> bool:
        building_def = self.get_building_definition(building_id)
        if building_def is None:
            return False

        # Check tech requirements
        if (
            building_def.required_tech
            and building_def.required_tech not in researched_techs
        ):
            return False

        # Check building prerequisites
        if building_def.required_buildings:
            for required_building_id in building_def.required_buildings:
                if self.get_building_count(required_building_id) == 0:
                    return False

        # Check max count
        if building_def.max_count >= 0:
            current_count = self.get_building_count(building_id)
            if current_count >= building_def.max_count:
                return False

        # Check required resources (all must be available in city)
        if building_def.required_resources:
            if city_available_resources is None:
                return False
            for required_resource in building_def.required_resources:
                if required_resource not in city_available_resources:
                    return False

        # Check vicinity bonus (resource must be in city's available resources)
        if building_def.vicinity_bonus:
            if city_available_resources is None:
                return False
            if building_def.vicinity_bonus not in city_available_resources:
                return False

        # Check terrain requirements (city must be on one of the listed terrains)
        if building_def.prereq_or_terrain:
            if city_terrain is None:
                return False
            if city_terrain.id not in building_def.prereq_or_terrain:
                return False

        return True

    def start_construction(self, building_id: str) -> bool:
        building_def = self.get_building_definition(building_id)
        if building_def is None:
            return False

        # If something is currently under construction, pause it
        if self.under_construction:
            current_construction = self.under_construction[0]
            current_id = current_construction.building_def.id
            self.paused_construction[current_id] = current_construction
            self.under_construction.clear()

        # Check if this building has saved progress
        if building_id in self.paused_construction:
            # Resume from saved progress
            construction = self.paused_construction.pop(building_id)
            self.under_construction.append(construction)
        else:
            # Start fresh construction
            # Get the required production (from adjusted costs that were already paid)
            adjusted_costs = self.get_adjusted_costs(building_id)
            required_production = 0.0
            for cost in adjusted_costs:
                if cost.resource_id == "production":
                    required_production = cost.amount
                    break

            construction = BuildingConstruction(
                building_def=building_def, required_production=required_production
            )
            self.under_construction.append(construction)

        return True

    def update_construction(self, production_amount: float) -> list[Building]:
        completed = []

        # Only apply production to the first (active) building under construction
        if self.under_construction:
            construction = self.under_construction[0]
            if construction.add_progress(production_amount):
                # Construction complete
                new_building = Building(definition=construction.building_def)
                self.buildings.append(new_building)
                completed.append(new_building)
                self.under_construction.pop(0)

                # Start next in queue if available
                if self.construction_queue:
                    next_building_id = self.construction_queue.pop(0)
                    self.start_construction(next_building_id)

        return completed

    def get_total_effect(self, effect_key: str) -> float:
        total = 0.0
        for building in self.buildings:
            if building.is_active:
                total += building.definition.effects.get(effect_key, 0.0)
        return total

    def get_total_worker_slots(self) -> int:
        return sum(b.definition.worker_slots for b in self.buildings if b.is_active)

    def get_total_assigned_workers(self) -> int:
        return sum(b.assigned_workers for b in self.buildings if b.is_active)
