"""City model representing a single settlement."""

from dataclasses import dataclass, field
from typing import Optional
import random

from .resource import ResourceStorage, ResourceType
from .building import BuildingManager
from .population import Population, WorkforceTask


@dataclass
class City:
    """Represents a single city in the civilization."""
    id: str  # Unique identifier
    name: str

    # City-specific systems
    resources: ResourceStorage = field(default_factory=ResourceStorage)
    population: Population = field(default_factory=Population)
    buildings: BuildingManager = field(default_factory=BuildingManager)

    # Available resources for extraction (resource IDs)
    available_resources: set[str] = field(default_factory=set)

    def __post_init__(self):
        """Initialize city with basic resources."""
        if not self.resources.resources:
            self._initialize_basic_resources()

    def _initialize_basic_resources(self) -> None:
        """Set up basic abstract resources for the city."""
        # Add production resource (capacity 0 - can't stockpile)
        production_type = ResourceType(
            id="production",
            name="Production",
            category=ResourceCategory.ABSTRACT,
            description="Work directed towards construction",
            base_storage_cap=0.0,
            can_store=False
        )
        self.resources.add_resource_type(production_type, initial_amount=0.0)

        # Add aggregated food resource (reflects sum of all crops)
        food_type = ResourceType(
            id="food",
            name="Food",
            category=ResourceCategory.ABSTRACT,
            description="Total food from all crop resources",
            base_storage_cap=0.0,
            can_store=True
        )
        self.resources.add_resource_type(food_type, initial_amount=0.0)

        # Add flavor-based abstract resources
        # Military
        military_type = ResourceType(
            id="military",
            name="Military",
            category=ResourceCategory.ABSTRACT,
            description="Military power from buildings",
            base_storage_cap=0.0,
            can_store=False
        )
        self.resources.add_resource_type(military_type, initial_amount=0.0)

        # Currency (Gold)
        currency_type = ResourceType(
            id="currency",
            name="Currency",
            category=ResourceCategory.ABSTRACT,
            description="Economic output from buildings",
            base_storage_cap=0.0,
            can_store=False
        )
        self.resources.add_resource_type(currency_type, initial_amount=0.0)

        # Religion
        religion_type = ResourceType(
            id="religion",
            name="Religion",
            category=ResourceCategory.ABSTRACT,
            description="Religious influence from buildings",
            base_storage_cap=0.0,
            can_store=False
        )
        self.resources.add_resource_type(religion_type, initial_amount=0.0)

        # Espionage
        espionage_type = ResourceType(
            id="espionage",
            name="Espionage",
            category=ResourceCategory.ABSTRACT,
            description="Espionage capability from buildings",
            base_storage_cap=0.0,
            can_store=False
        )
        self.resources.add_resource_type(espionage_type, initial_amount=0.0)

        # Culture
        culture_type = ResourceType(
            id="culture",
            name="Culture",
            category=ResourceCategory.ABSTRACT,
            description="Cultural output from buildings",
            base_storage_cap=0.0,
            can_store=False
        )
        self.resources.add_resource_type(culture_type, initial_amount=0.0)

        # Research (city-level contribution)
        research_type = ResourceType(
            id="research",
            name="Research",
            category=ResourceCategory.ABSTRACT,
            description="Research output from buildings and workers",
            base_storage_cap=0.0,
            can_store=False
        )
        self.resources.add_resource_type(research_type, initial_amount=0.0)

    def initialize_starting_resources(self, all_resources: dict, count: int = 3) -> None:
        """Randomly select starting resources for the city.

        Selects:
        - 1 PRODUCTION resource
        - 1 CROP resource (must require 'scavenging' or 'gathering' tech)
        - (count - 2) random resources

        Args:
            all_resources: Dictionary of resource_id -> ResourceType
            count: Number of starting resources (default 3, range 1-3)
        """
        count = max(1, min(3, count))  # Clamp between 1 and 3

        # Filter resources by bonus class
        production_resources = [r for r in all_resources.values() if r.bonus_class == 'production']

        # Filter crop resources to only those requiring scavenging or gathering
        crop_resources = [
            r for r in all_resources.values()
            if r.bonus_class == 'crop'
            and (r.tech_reveal == 'scavenging' or r.tech_reveal == 'gathering')
        ]

        # Select one from each category
        selected = []

        if production_resources and count >= 1:
            selected.append(random.choice(production_resources))

        if crop_resources and count >= 2:
            selected.append(random.choice(crop_resources))

        # Select random resources for remaining slots
        remaining_slots = count - len(selected)
        if remaining_slots > 0 and all_resources:
            other_resources = [r for r in all_resources.values() if r not in selected]
            if other_resources:
                for _ in range(remaining_slots):
                    if other_resources:
                        random_resource = random.choice(other_resources)
                        selected.append(random_resource)
                        other_resources.remove(random_resource)

        # Add to available resources
        for resource in selected:
            self.available_resources.add(resource.id)
            # Add the resource type to storage if it's not already there
            self.resources.add_resource_type(resource, initial_amount=0.0)

    def get_total_food_from_crops(self) -> float:
        """Calculate total food from all crop resources.

        Returns:
            Total amount of food from all resources with bonus_class='crop'
        """
        total = 0.0
        for resource_qty in self.resources.resources.values():
            if hasattr(resource_qty.resource_type, 'bonus_class') and resource_qty.resource_type.bonus_class == 'crop':
                total += resource_qty.amount
        return total

    def update(self, delta_time: float) -> dict:
        """Update city systems. Returns update summary.

        Args:
            delta_time: Time elapsed in seconds
        """
        update_summary = {
            "city_id": self.id,
            "city_name": self.name,
            "delta_time": delta_time,
            "completed_buildings": [],
            "population_change": 0,
            "resource_changes": {}
        }

        # Calculate and apply crop resource production from workers
        total_crop_production = 0.0
        total_crop_production_rate = 0.0
        for resource_qty in self.resources.resources.values():
            if hasattr(resource_qty.resource_type, 'bonus_class') and resource_qty.resource_type.bonus_class == 'crop':
                crop_workers = self.population.get_workers_on_resource(resource_qty.resource_type.id)
                if crop_workers > 0:
                    # Each worker produces 2.0 units per second
                    crop_production_rate = crop_workers * 2.0 * self.population.happiness
                    resource_qty.production_rate = crop_production_rate
                    total_crop_production_rate += crop_production_rate
                    crop_production = crop_production_rate * delta_time
                    added = resource_qty.add(crop_production)
                    total_crop_production += added
                    update_summary["resource_changes"][resource_qty.resource_type.id] = added
                else:
                    resource_qty.production_rate = 0.0

        # Update population - consume food from crops
        total_food = self.get_total_food_from_crops()
        food_consumption_rate = self.population.calculate_food_consumption()
        food_consumption = food_consumption_rate * delta_time
        food_surplus = total_food - food_consumption

        # Consume crops proportionally from all available crops
        if total_food > 0 and food_consumption > 0:
            for resource_qty in self.resources.resources.values():
                if hasattr(resource_qty.resource_type, 'bonus_class') and resource_qty.resource_type.bonus_class == 'crop':
                    if resource_qty.amount > 0:
                        # Consume proportional to this crop's share of total food
                        proportion = resource_qty.amount / total_food
                        consumption_from_this_crop = food_consumption * proportion
                        resource_qty.consumption_rate = consumption_from_this_crop / delta_time if delta_time > 0 else 0
                        resource_qty.remove(consumption_from_this_crop)

        # Update aggregated food resource
        food_resource = self.resources.get("food")
        if food_resource:
            # Calculate totals from all crop resources
            total_food_amount = 0.0
            total_food_capacity = 0.0

            for resource_qty in self.resources.resources.values():
                if hasattr(resource_qty.resource_type, 'bonus_class') and resource_qty.resource_type.bonus_class == 'crop':
                    total_food_amount += resource_qty.amount
                    total_food_capacity += resource_qty.capacity

            # Update the aggregated food resource
            food_resource.amount = total_food_amount
            food_resource.capacity = total_food_capacity
            food_resource.production_rate = total_crop_production_rate
            food_resource.consumption_rate = food_consumption_rate

        population_change = self.population.update_growth(delta_time, food_surplus)
        self.population.update_happiness()
        update_summary["population_change"] = population_change

        # Update production (workers apply production directly to construction)
        production_workers = self.population.get_workers_on_task(WorkforceTask.CONSTRUCTION)
        production_resource = self.resources.get("production")
        if production_resource:
            # Production rate shown in UI, but not accumulated
            production_resource.production_rate = production_workers * 1.0
            production_resource.amount = 0.0  # Always 0, can't stockpile

        # Calculate production for this tick: workers * rate * time
        production_this_tick = production_workers * 1.0 * delta_time

        # Update building construction (apply production to buildings under construction)
        completed_buildings = self.buildings.update_construction(production_this_tick)
        for building in completed_buildings:
            update_summary["completed_buildings"].append(building.definition.name)
            self._apply_building_effects(building)

        # Update housing capacity from buildings
        self._update_housing_capacity()

        # Update flavor-based abstract resources from buildings
        self._update_flavor_resources()

        return update_summary

    def _apply_building_effects(self, building) -> None:
        """Apply effects when a building is completed."""
        # Buildings apply their effects through the building manager
        pass

    def _update_housing_capacity(self) -> None:
        """Update housing capacity based on buildings."""
        base_capacity = 10
        building_bonus = self.buildings.get_total_effect("housing")
        self.population.housing_capacity = base_capacity + int(building_bonus)

    def _update_flavor_resources(self) -> None:
        """Update abstract resources based on building flavors."""
        # Mapping from flavor types to resource IDs
        flavor_to_resource = {
            'growth': 'food',
            'production': 'production',
            'science': 'research',  # Research is civilization-wide, but we'll track it here
            'military': 'military',
            'gold': 'currency',
            'religion': 'religion',
            'espionage': 'espionage',
            'culture': 'culture'
        }

        # Calculate total flavor bonuses from all buildings
        flavor_totals = {}
        for building in self.buildings.buildings:
            if building.is_active and building.definition.flavors:
                for flavor_type, flavor_value in building.definition.flavors.items():
                    if flavor_type in flavor_totals:
                        flavor_totals[flavor_type] += flavor_value
                    else:
                        flavor_totals[flavor_type] = flavor_value

        # Apply flavor bonuses to abstract resources
        for flavor_type, resource_id in flavor_to_resource.items():
            resource = self.resources.get(resource_id)
            if resource:
                # Set production rate based on flavor value
                # Each flavor point = 1 unit per second
                bonus = flavor_totals.get(flavor_type, 0)
                resource.production_rate = float(bonus)

    def can_afford_costs(self, costs: list) -> bool:
        """Check if city can afford a list of resource costs."""
        for cost in costs:
            if not self.resources.has_resource(cost.resource_id, cost.amount):
                return False
        return True

    def spend_costs(self, costs: list) -> bool:
        """Spend resources for costs. Returns True if successful."""
        if not self.can_afford_costs(costs):
            return False

        for cost in costs:
            self.resources.remove_amount(cost.resource_id, cost.amount)
        return True


# Import here to avoid circular dependency
from .resource import ResourceCategory
