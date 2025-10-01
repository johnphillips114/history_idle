"""Building model and construction system."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class BuildingCategory(Enum):
    """Categories of buildings."""
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
    """Represents a resource cost."""
    resource_id: str
    amount: float


@dataclass
class BuildingDefinition:
    """Defines a building type."""
    id: str
    name: str
    description: str
    category: BuildingCategory
    construction_costs: list[ResourceCost] = field(default_factory=list)
    construction_time: float = 0.0  # Base construction time in seconds
    maintenance_costs: list[ResourceCost] = field(default_factory=list)
    required_tech: Optional[str] = None
    required_resources: list[str] = field(default_factory=list)  # Resources that must be available
    required_buildings: list[str] = field(default_factory=list)  # Buildings that must be constructed first
    max_count: int = 1  # Maximum number that can be built (1 = unique building, -1 = unlimited)
    effects: dict[str, float] = field(default_factory=dict)
    worker_slots: int = 0  # Number of workers this building can employ
    flavors: dict[str, int] = field(default_factory=dict)  # FlavorType -> iFlavor value

    def __hash__(self):
        return hash(self.id)


@dataclass
class Building:
    """An instance of a building."""
    definition: BuildingDefinition
    is_active: bool = True
    assigned_workers: int = 0

    @property
    def max_workers(self) -> int:
        """Maximum workers that can be assigned."""
        return self.definition.worker_slots

    def assign_workers(self, count: int) -> int:
        """Assign workers to the building. Returns actual number assigned."""
        max_assignment = min(count, self.max_workers)
        self.assigned_workers = max_assignment
        return self.assigned_workers

    def remove_workers(self, count: int) -> int:
        """Remove workers from the building. Returns actual number removed."""
        removed = min(count, self.assigned_workers)
        self.assigned_workers -= removed
        return removed


@dataclass
class BuildingConstruction:
    """Tracks construction progress of a building."""
    building_def: BuildingDefinition
    progress: float = 0.0  # Production applied so far
    required_production: float = 0.0  # Total production needed (set when construction starts)
    is_complete: bool = False

    @property
    def progress_percentage(self) -> float:
        """Construction progress as a percentage (0.0 to 1.0)."""
        if self.required_production <= 0:
            return 1.0
        return min(1.0, self.progress / self.required_production)

    @property
    def remaining_production(self) -> float:
        """Remaining production needed."""
        return max(0.0, self.required_production - self.progress)

    def add_progress(self, production: float) -> bool:
        """Add construction progress. Returns True if completed.

        Args:
            production: Amount of production to apply

        Returns:
            True if construction is complete
        """
        if self.is_complete:
            return True

        self.progress += production
        if self.progress >= self.required_production:
            self.is_complete = True
            return True
        return False


@dataclass
class BuildingManager:
    """Manages buildings for a civilization."""
    building_definitions: dict[str, BuildingDefinition] = field(default_factory=dict)
    buildings: list[Building] = field(default_factory=list)
    under_construction: list[BuildingConstruction] = field(default_factory=list)
    construction_queue: list[str] = field(default_factory=list)

    def add_building_definition(self, building_def: BuildingDefinition) -> None:
        """Add a building definition."""
        self.building_definitions[building_def.id] = building_def

    def get_building_definition(self, building_id: str) -> Optional[BuildingDefinition]:
        """Get a building definition by ID."""
        return self.building_definitions.get(building_id)

    def get_building_count(self, building_id: str) -> int:
        """Get count of buildings of a specific type."""
        return sum(1 for b in self.buildings if b.definition.id == building_id)

    def get_cost_multiplier(self, building_id: str) -> float:
        """Calculate cost multiplier based on number of buildings already built.

        Uses exponential scaling: 1.2^count
        - 0 built: 1.0x
        - 1 built: 1.2x
        - 2 built: 1.44x
        - 3 built: 1.728x
        - etc.

        Args:
            building_id: ID of the building type

        Returns:
            Cost multiplier (1.0 or higher)
        """
        current_count = self.get_building_count(building_id)
        return 1.2 ** current_count

    def get_adjusted_costs(self, building_id: str) -> list:
        """Get construction costs with multiplier applied.

        Args:
            building_id: ID of the building type

        Returns:
            List of ResourceCost with adjusted amounts
        """
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

    def can_build(self, building_id: str, researched_techs: set[str]) -> bool:
        """Check if a building can be constructed."""
        building_def = self.get_building_definition(building_id)
        if building_def is None:
            return False

        # Check tech requirements
        if building_def.required_tech and building_def.required_tech not in researched_techs:
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

        return True

    def start_construction(self, building_id: str) -> bool:
        """Start constructing a building. Returns True if successful."""
        building_def = self.get_building_definition(building_id)
        if building_def is None:
            return False

        # Get the required production (from adjusted costs that were already paid)
        adjusted_costs = self.get_adjusted_costs(building_id)
        required_production = 0.0
        for cost in adjusted_costs:
            if cost.resource_id == "production":
                required_production = cost.amount
                break

        construction = BuildingConstruction(
            building_def=building_def,
            required_production=required_production
        )
        self.under_construction.append(construction)
        return True

    def update_construction(self, production_amount: float) -> list[Building]:
        """Update all construction progress using production from workers.

        Args:
            production_amount: Amount of production to apply this tick (workers * rate * time)

        Returns:
            List of completed buildings
        """
        completed = []
        remaining = []

        for construction in self.under_construction:
            # Apply production to this construction
            if construction.add_progress(production_amount):
                # Construction complete
                new_building = Building(definition=construction.building_def)
                self.buildings.append(new_building)
                completed.append(new_building)
            else:
                remaining.append(construction)

        self.under_construction = remaining

        # Start next in queue if construction slots available
        while self.construction_queue:
            next_building_id = self.construction_queue.pop(0)
            if self.start_construction(next_building_id):
                break

        return completed

    def get_total_effect(self, effect_key: str) -> float:
        """Get total effect value from all active buildings."""
        total = 0.0
        for building in self.buildings:
            if building.is_active:
                total += building.definition.effects.get(effect_key, 0.0)
        return total

    def get_total_worker_slots(self) -> int:
        """Get total available worker slots across all buildings."""
        return sum(b.definition.worker_slots for b in self.buildings if b.is_active)

    def get_total_assigned_workers(self) -> int:
        """Get total number of workers assigned to buildings."""
        return sum(b.assigned_workers for b in self.buildings if b.is_active)
