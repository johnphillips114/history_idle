from dataclasses import dataclass, field
from typing import Optional
import random

from .resource import ResourceStorage, ResourceType
from .building import BuildingManager
from .population import Population, WorkforceTask


@dataclass
class City:
    id: str  # Unique identifier
    name: str
    resources: ResourceStorage = field(default_factory=ResourceStorage)
    population: Population = field(default_factory=Population)
    buildings: BuildingManager = field(default_factory=BuildingManager)
    available_resources: set[str] = field(default_factory=set)

    def __post_init__(self):
        if not self.resources.resources:
            self._initialize_basic_resources()

    def _initialize_basic_resources(self) -> None:
        production_type = ResourceType(
            id="production",
            name="Production",
            category=ResourceCategory.ABSTRACT,
            description="Work directed towards construction",
            base_storage_cap=0.0,
            can_store=False,
        )
        self.resources.add_resource_type(production_type, initial_amount=0.0)

        food_type = ResourceType(
            id="food",
            name="Food",
            category=ResourceCategory.ABSTRACT,
            description="Total food from all crop resources",
            base_storage_cap=0.0,
            can_store=True,
        )
        self.resources.add_resource_type(food_type, initial_amount=0.0)

        military_type = ResourceType(
            id="military",
            name="Military",
            category=ResourceCategory.ABSTRACT,
            description="Military power from buildings",
            base_storage_cap=0.0,
            can_store=False,
        )
        self.resources.add_resource_type(military_type, initial_amount=0.0)

        currency_type = ResourceType(
            id="currency",
            name="Currency",
            category=ResourceCategory.ABSTRACT,
            description="Economic output from buildings",
            base_storage_cap=0.0,
            can_store=False,
        )
        self.resources.add_resource_type(currency_type, initial_amount=0.0)

        religion_type = ResourceType(
            id="religion",
            name="Religion",
            category=ResourceCategory.ABSTRACT,
            description="Religious influence from buildings",
            base_storage_cap=0.0,
            can_store=False,
        )
        self.resources.add_resource_type(religion_type, initial_amount=0.0)

        espionage_type = ResourceType(
            id="espionage",
            name="Espionage",
            category=ResourceCategory.ABSTRACT,
            description="Espionage capability from buildings",
            base_storage_cap=0.0,
            can_store=False,
        )
        self.resources.add_resource_type(espionage_type, initial_amount=0.0)

        culture_type = ResourceType(
            id="culture",
            name="Culture",
            category=ResourceCategory.ABSTRACT,
            description="Cultural output from buildings",
            base_storage_cap=0.0,
            can_store=False,
        )
        self.resources.add_resource_type(culture_type, initial_amount=0.0)

        research_type = ResourceType(
            id="research",
            name="Research",
            category=ResourceCategory.ABSTRACT,
            description="Research output from buildings and workers",
            base_storage_cap=0.0,
            can_store=False,
        )
        self.resources.add_resource_type(research_type, initial_amount=0.0)

    def initialize_starting_resources(
        self, all_resources: dict, count: int = 3
    ) -> None:
        count = max(1, min(3, count))  # Clamp between 1 and 3
        production_resources = [
            r for r in all_resources.values() if r.bonus_class == "production"
        ]
        crop_resources = [
            r
            for r in all_resources.values()
            if r.bonus_class == "crop"
            and (r.tech_reveal == "scavenging" or r.tech_reveal == "gathering")
        ]

        selected = []
        if production_resources and count >= 1:
            selected.append(random.choice(production_resources))

        if crop_resources and count >= 2:
            selected.append(random.choice(crop_resources))

        remaining_slots = count - len(selected)
        if remaining_slots > 0 and all_resources:
            other_resources = [r for r in all_resources.values() if r not in selected]
            if other_resources:
                for _ in range(remaining_slots):
                    if other_resources:
                        random_resource = random.choice(other_resources)
                        selected.append(random_resource)
                        other_resources.remove(random_resource)

        for resource in selected:
            self.available_resources.add(resource.id)
            self.resources.add_resource_type(resource, initial_amount=0.0)

    def get_total_food_from_crops(self) -> float:
        total = 0.0
        for resource_qty in self.resources.resources.values():
            if (
                hasattr(resource_qty.resource_type, "bonus_class")
                and resource_qty.resource_type.bonus_class == "crop"
            ):
                total += resource_qty.amount
        return total

    def update(self, delta_time: float) -> dict:
        update_summary = {
            "city_id": self.id,
            "city_name": self.name,
            "delta_time": delta_time,
            "completed_buildings": [],
            "population_change": 0,
            "resource_changes": {},
        }

        total_crop_production = 0.0
        total_crop_production_rate = 0.0
        growth_flavor_bonus = self._get_flavor_bonus("growth")

        for resource_qty in self.resources.resources.values():
            if (
                hasattr(resource_qty.resource_type, "bonus_class")
                and resource_qty.resource_type.bonus_class == "crop"
            ):
                crop_workers = self.population.get_workers_on_resource(
                    resource_qty.resource_type.id
                )
                if crop_workers > 0:
                    crop_production_rate = (
                        crop_workers * 2.0 * self.population.happiness
                    )
                    resource_qty.production_rate = crop_production_rate
                    total_crop_production_rate += crop_production_rate
                    crop_production = crop_production_rate * delta_time
                    added = resource_qty.add(crop_production)
                    total_crop_production += added
                    update_summary["resource_changes"][
                        resource_qty.resource_type.id
                    ] = added
                else:
                    resource_qty.production_rate = 0.0

        if growth_flavor_bonus > 0:
            crop_resources = [
                rq
                for rq in self.resources.resources.values()
                if hasattr(rq.resource_type, "bonus_class")
                and rq.resource_type.bonus_class == "crop"
            ]
            if crop_resources:
                bonus_per_crop = growth_flavor_bonus / len(crop_resources)
                for resource_qty in crop_resources:
                    bonus_production = bonus_per_crop * delta_time
                    added = resource_qty.add(bonus_production)
                    total_crop_production += added
                    if (
                        resource_qty.resource_type.id
                        in update_summary["resource_changes"]
                    ):
                        update_summary["resource_changes"][
                            resource_qty.resource_type.id
                        ] += added
                    else:
                        update_summary["resource_changes"][
                            resource_qty.resource_type.id
                        ] = added

                total_crop_production_rate += growth_flavor_bonus

        total_food = self.get_total_food_from_crops()
        food_consumption_rate = self.population.calculate_food_consumption()
        food_consumption = food_consumption_rate * delta_time
        food_surplus = total_food - food_consumption

        if total_food > 0 and food_consumption > 0:
            for resource_qty in self.resources.resources.values():
                if (
                    hasattr(resource_qty.resource_type, "bonus_class")
                    and resource_qty.resource_type.bonus_class == "crop"
                ):
                    if resource_qty.amount > 0:
                        proportion = resource_qty.amount / total_food
                        consumption_from_this_crop = food_consumption * proportion
                        resource_qty.consumption_rate = (
                            consumption_from_this_crop / delta_time
                            if delta_time > 0
                            else 0
                        )
                        resource_qty.remove(consumption_from_this_crop)

        food_resource = self.resources.get("food")
        if food_resource:
            total_food_amount = 0.0
            total_food_capacity = 0.0

            for resource_qty in self.resources.resources.values():
                if (
                    hasattr(resource_qty.resource_type, "bonus_class")
                    and resource_qty.resource_type.bonus_class == "crop"
                ):
                    total_food_amount += resource_qty.amount
                    total_food_capacity += resource_qty.capacity

            food_resource.amount = total_food_amount
            food_resource.capacity = total_food_capacity
            food_resource.production_rate = total_crop_production_rate
            food_resource.consumption_rate = food_consumption_rate

        population_change = self.population.update_growth(delta_time, food_surplus)
        self.population.update_happiness()
        update_summary["population_change"] = population_change

        self._update_flavor_resources()

        production_workers = self.population.get_workers_on_task(
            WorkforceTask.CONSTRUCTION
        )
        production_from_workers = production_workers * 1.0

        production_from_flavors = self._get_flavor_bonus("production")

        production_resource = self.resources.get("production")
        if production_resource:
            production_resource.production_rate = (
                production_from_workers + production_from_flavors
            )
            production_resource.amount = 0.0  # Always 0, can't stockpile

        production_this_tick = (
            production_from_workers + production_from_flavors
        ) * delta_time

        completed_buildings = self.buildings.update_construction(production_this_tick)
        for building in completed_buildings:
            update_summary["completed_buildings"].append(building.definition.name)
            self._apply_building_effects(building)

        self._update_housing_capacity()

        return update_summary

    def _apply_building_effects(self, building) -> None:
        """Apply effects when a building is completed."""
        # Buildings apply their effects through the building manager
        pass

    def _update_housing_capacity(self) -> None:
        base_capacity = 10
        building_bonus = self.buildings.get_total_effect("housing")
        self.population.housing_capacity = base_capacity + int(building_bonus)

    def _get_flavor_bonus(self, flavor_type: str) -> float:
        total = 0.0
        for building in self.buildings.buildings:
            if building.is_active and building.definition.flavors:
                total += building.definition.flavors.get(flavor_type, 0)
        return float(total)

    def _update_flavor_resources(self) -> None:
        flavor_to_resource = {
            "science": "research",  # Research is civilization-wide, but we'll track it here
            "military": "military",
            "gold": "currency",
            "religion": "religion",
            "espionage": "espionage",
            "culture": "culture",
        }

        flavor_totals = {}
        for building in self.buildings.buildings:
            if building.is_active and building.definition.flavors:
                for flavor_type, flavor_value in building.definition.flavors.items():
                    if flavor_type in flavor_totals:
                        flavor_totals[flavor_type] += flavor_value
                    else:
                        flavor_totals[flavor_type] = flavor_value

        for flavor_type, resource_id in flavor_to_resource.items():
            resource = self.resources.get(resource_id)
            if resource:
                bonus = flavor_totals.get(flavor_type, 0)
                resource.production_rate = float(bonus)

    def can_afford_costs(self, costs: list) -> bool:
        for cost in costs:
            if not self.resources.has_resource(cost.resource_id, cost.amount):
                return False
        return True

    def spend_costs(self, costs: list) -> bool:
        if not self.can_afford_costs(costs):
            return False

        for cost in costs:
            self.resources.remove_amount(cost.resource_id, cost.amount)
        return True


# Import here to avoid circular dependency
from .resource import ResourceCategory
