"""Main civilization model that ties all systems together."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import time

from .resource import ResourceStorage, ResourceType, ResourceCategory
from .technology import TechTree, Era
from .building import BuildingManager
from .population import Population, WorkforceTask


class GovernmentType(Enum):
    """Government types available in the game."""
    TRIBAL = "tribal"
    CHIEFDOM = "chiefdom"
    DEMOCRACY = "democracy"
    MONARCHY = "monarchy"
    REPUBLIC = "republic"
    TECHNOCRACY = "technocracy"
    OLIGARCHY = "oligarchy"
    AUTOCRACY = "autocracy"
    ANARCHY = "anarchy"
    CORPOCRACY = "corpocracy"


class StartingLocation(Enum):
    """Starting locations for civilizations."""
    WESTERN_EUROPE = "western_europe"
    NORTHERN_EUROPE = "northern_europe"
    WEST_MEDITERRANEAN = "west_mediterranean"
    EAST_MEDITERRANEAN = "east_mediterranean"
    EUROPEAN_STEPPES = "european_steppes"
    LEVANT = "levant"
    MESOPOTAMIA = "mesopotamia"
    NILE = "nile"
    MAGHREB = "maghreb"
    PERSIAN = "persian"
    INDUS = "indus"
    ASIAN_STEPPES = "asian_steppes"
    SOUTHEAST_ASIA = "southeast_asia"
    INDONESIA = "indonesia"
    AUSTRALIA = "australia"
    POLYNESIA = "polynesia"
    YELLOW_RIVER = "yellow_river"
    JAPAN = "japan"
    CASCADIA = "cascadia"
    PRAIRIE_STEPPES = "prairie_steppes"
    GREAT_LAKES = "great_lakes"
    EAST_COAST = "east_coast"
    MISSISSIPPI = "mississippi"
    SOUTHWEST = "southwest"
    MESOAMERICAN = "mesoamerican"
    CENTRAL_AMERICAN = "central_american"
    CARIBBEAN = "caribbean"
    ANDES = "andes"
    LA_PLATA = "la_plata"
    AMAZONIAN = "amazonian"
    SERENGETI = "serengeti"
    CONGO = "congo"
    AFRICAN_GREAT_LAKES = "african_great_lakes"
    ETHIOPIAN_HIGHLANDS = "ethiopian_highlands"


@dataclass
class Civilization:
    """Main civilization class that represents the player's state."""
    name: str
    starting_location: StartingLocation
    current_era: Era = Era.PALEOLITHIC
    government: GovernmentType = GovernmentType.TRIBAL

    # Core systems
    resources: ResourceStorage = field(default_factory=ResourceStorage)
    population: Population = field(default_factory=Population)
    tech_tree: TechTree = field(default_factory=TechTree)
    buildings: BuildingManager = field(default_factory=BuildingManager)

    # Available resources for extraction (resource IDs)
    available_resources: set[str] = field(default_factory=set)

    # Game time tracking
    game_time: float = 0.0  # Total game time in seconds
    last_update_time: float = field(default_factory=time.time)

    # Prestige tracking
    prestige_points: int = 0
    prestige_count: int = 0

    def initialize_starting_resources(self) -> None:
        """Set up initial resources for a new game."""
        # Note: Food is now tracked via individual crop resources, not a generic "food" resource
        # Players allocate workers to specific crops (e.g., wheat, barley)
        # Total food = sum of all crop resources

        # Add basic research points
        research_type = ResourceType(
            id="research",
            name="Research Points",
            category=ResourceCategory.ABSTRACT,
            description="Used to unlock technologies",
            base_storage_cap=1000.0
        )
        self.resources.add_resource_type(research_type, initial_amount=0.0)

        # Add production resource (capacity 0 - can't stockpile, only applies when building)
        production_type = ResourceType(
            id="production",
            name="Production",
            category=ResourceCategory.ABSTRACT,
            description="Work directed towards construction",
            base_storage_cap=0.0,  # Can't store production
            can_store=False
        )
        self.resources.add_resource_type(production_type, initial_amount=0.0)

    def load_tech_tree(self, technologies: dict):
        """Load technology definitions into the tech tree.

        Args:
            technologies: Dictionary of tech_id -> TechnologyDefinition
        """
        for tech_id, tech_def in technologies.items():
            self.tech_tree.add_technology(tech_def)

    def load_buildings(self, buildings: dict):
        """Load building definitions into the building manager.

        Args:
            buildings: Dictionary of building_id -> BuildingDefinition
        """
        for building_id, building_def in buildings.items():
            self.buildings.add_building_definition(building_def)

    def initialize_available_resources(self, all_resources: dict):
        """Randomly select 3 starting resources for the civilization.

        Selects:
        - 1 PRODUCTION resource
        - 1 CROP resource (must require 'scavenging' or 'gathering' tech)
        - 1 random resource (any type)

        Args:
            all_resources: Dictionary of resource_id -> ResourceType
        """
        import random

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

        if production_resources:
            selected.append(random.choice(production_resources))

        if crop_resources:
            selected.append(random.choice(crop_resources))

        # Select one random resource from all available
        if all_resources:
            random_resource = random.choice(list(all_resources.values()))
            # Make sure it's not already selected
            if random_resource not in selected:
                selected.append(random_resource)
            else:
                # Try to find a different one
                other_resources = [r for r in all_resources.values() if r not in selected]
                if other_resources:
                    selected.append(random.choice(other_resources))

        # Add to available resources
        for resource in selected:
            self.available_resources.add(resource.id)

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

    def get_time_since_last_update(self) -> float:
        """Calculate time elapsed since last update."""
        current_time = time.time()
        delta = current_time - self.last_update_time
        return delta

    def update(self, delta_time: Optional[float] = None) -> dict:
        """Update all game systems. Returns update summary.

        Args:
            delta_time: Time elapsed in seconds. If None, calculated from real time.
        """
        if delta_time is None:
            delta_time = self.get_time_since_last_update()

        self.last_update_time = time.time()
        self.game_time += delta_time

        update_summary = {
            "delta_time": delta_time,
            "completed_techs": [],
            "completed_buildings": [],
            "population_change": 0,
            "resource_changes": {}
        }

        # Calculate and apply crop resource production from workers
        # Each crop resource with allocated workers produces crops
        total_crop_production = 0.0
        for resource_qty in self.resources.resources.values():
            if hasattr(resource_qty.resource_type, 'bonus_class') and resource_qty.resource_type.bonus_class == 'crop':
                crop_workers = self.population.get_workers_on_resource(resource_qty.resource_type.id)
                if crop_workers > 0:
                    # Each worker produces 2.0 units per second (enough to feed 2 people at 0.5/s consumption)
                    crop_production_rate = crop_workers * 2.0 * self.population.happiness
                    resource_qty.production_rate = crop_production_rate
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

        population_change = self.population.update_growth(delta_time, food_surplus)
        self.population.update_happiness()
        update_summary["population_change"] = population_change

        # Update research
        research_output = self.population.calculate_research_output() * delta_time
        research_resource = self.resources.get("research")
        if research_resource:
            research_workers = self.population.get_workers_on_task(WorkforceTask.RESEARCH)
            research_resource.production_rate = research_workers * 1.0 * (1.0 + self.population.literacy)
            research_resource.add(research_output)

        if self.tech_tree.current_research:
            completed_tech = self.tech_tree.add_research_points(research_output)
            if completed_tech:
                update_summary["completed_techs"].append(completed_tech.name)
                self._apply_tech_effects(completed_tech.id)

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

        return update_summary

    def _apply_tech_effects(self, tech_id: str) -> None:
        """Apply effects when a technology is completed."""
        tech = self.tech_tree.get_technology(tech_id)
        if not tech:
            return

        # Apply any direct effects from the technology
        for effect_key, value in tech.effects.items():
            if effect_key == "literacy_bonus":
                self.population.literacy += value
            elif effect_key == "housing_capacity":
                self.population.housing_capacity += int(value)

    def _apply_building_effects(self, building) -> None:
        """Apply effects when a building is completed."""
        # Buildings apply their effects through the building manager
        pass

    def _update_housing_capacity(self) -> None:
        """Update housing capacity based on buildings."""
        base_capacity = 10
        building_bonus = self.buildings.get_total_effect("housing")
        self.population.housing_capacity = base_capacity + int(building_bonus)

    def can_afford_costs(self, costs: list) -> bool:
        """Check if civilization can afford a list of resource costs."""
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

    def get_current_era(self) -> Era:
        """Get the current era based on researched technologies."""
        # Simple implementation - can be enhanced
        return self.current_era

    def advance_era(self) -> None:
        """Advance to the next era."""
        eras = list(Era)
        current_index = eras.index(self.current_era)
        if current_index < len(eras) - 1:
            self.current_era = eras[current_index + 1]
