"""Resource production and extraction system."""

from typing import Optional
from ..models.resource import ResourceStorage, ResourceType
from ..models.population import Population, WorkforceTask


class ResourceProductionSystem:
    """Manages resource production from workforce allocation."""

    def __init__(self):
        self.base_extraction_rate = 1.0  # Base rate per worker per second

    def calculate_resource_production(
        self,
        resource_storage: ResourceStorage,
        population: Population,
        delta_time: float
    ) -> dict[str, float]:
        """Calculate production for all resources based on worker allocation.

        Returns:
            Dictionary of resource_id -> production amount
        """
        production = {}

        # Calculate production from workers assigned to resource extraction
        for allocation in population.allocations:
            if allocation.task == WorkforceTask.RESOURCE_EXTRACTION and allocation.resource_id:
                resource_id = allocation.resource_id
                workers = allocation.count

                # Calculate base production
                base_production = workers * self.base_extraction_rate * delta_time

                # Apply any modifiers (happiness, technology bonuses, etc.)
                happiness_modifier = population.happiness
                total_production = base_production * happiness_modifier

                production[resource_id] = production.get(resource_id, 0.0) + total_production

        return production

    def apply_production(
        self,
        resource_storage: ResourceStorage,
        production: dict[str, float]
    ) -> dict[str, float]:
        """Apply calculated production to resource storage.

        Returns:
            Dictionary of resource_id -> actual amount added (after caps)
        """
        actual_added = {}

        for resource_id, amount in production.items():
            added = resource_storage.add_amount(resource_id, amount)
            actual_added[resource_id] = added

        return actual_added

    def update(
        self,
        resource_storage: ResourceStorage,
        population: Population,
        delta_time: float
    ) -> dict[str, float]:
        """Update resource production for a game tick.

        Returns:
            Dictionary of resource_id -> production amount
        """
        production = self.calculate_resource_production(resource_storage, population, delta_time)
        actual = self.apply_production(resource_storage, production)
        return actual


class ResourceConsumptionSystem:
    """Manages resource consumption."""

    def calculate_food_consumption(
        self,
        population: Population,
        delta_time: float
    ) -> float:
        """Calculate food consumption for the population."""
        return population.calculate_food_consumption() * delta_time

    def calculate_maintenance_costs(
        self,
        buildings,
        delta_time: float
    ) -> dict[str, float]:
        """Calculate maintenance costs for all buildings.

        Args:
            buildings: BuildingManager instance
            delta_time: Time elapsed in seconds

        Returns:
            Dictionary of resource_id -> consumption amount
        """
        consumption = {}

        for building in buildings.buildings:
            if not building.is_active:
                continue

            for cost in building.definition.maintenance_costs:
                resource_id = cost.resource_id
                amount = cost.amount * delta_time
                consumption[resource_id] = consumption.get(resource_id, 0.0) + amount

        return consumption

    def apply_consumption(
        self,
        resource_storage: ResourceStorage,
        consumption: dict[str, float]
    ) -> dict[str, float]:
        """Apply consumption to resource storage.

        Returns:
            Dictionary of resource_id -> actual amount consumed
        """
        actual_consumed = {}

        for resource_id, amount in consumption.items():
            consumed = resource_storage.remove_amount(resource_id, amount)
            actual_consumed[resource_id] = consumed

        return actual_consumed
