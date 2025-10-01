"""Main civilization model that ties all systems together."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import time
import uuid

from .resource import ResourceStorage, ResourceType, ResourceCategory
from .technology import TechTree, Era
from .city import City
from .population import WorkforceTask


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

    # Civilization-wide systems
    tech_tree: TechTree = field(default_factory=TechTree)
    resources: ResourceStorage = field(default_factory=ResourceStorage)  # Civilization-wide abstract resources (research)

    # Cities
    cities: list[City] = field(default_factory=list)
    active_city_id: Optional[str] = None
    ready_settlers: int = 0  # Number of settlers ready to found cities

    # Game time tracking
    game_time: float = 0.0  # Total game time in seconds
    last_update_time: float = field(default_factory=time.time)

    # Prestige tracking
    prestige_points: int = 0
    prestige_count: int = 0

    def __post_init__(self):
        """Initialize with a starting city if no cities exist."""
        if not self.cities:
            self.add_city("Capital", starting_city=True)

    def add_city(self, name: str, starting_city: bool = False, starting_population: int = 10,
                 starting_resource_count: int = 3) -> City:
        """Add a new city to the civilization.

        Args:
            name: Name of the city
            starting_city: Whether this is the starting capital city
            starting_population: Initial population
            starting_resource_count: Number of starting resources (1-3)

        Returns:
            The newly created City
        """
        city_id = str(uuid.uuid4())
        city = City(
            id=city_id,
            name=name,
        )
        city.population.total = starting_population
        city.population.housing_capacity = starting_population

        self.cities.append(city)

        # Set as active if it's the first city
        if self.active_city_id is None:
            self.active_city_id = city_id

        return city

    def found_city(self, name: str, all_resources: dict) -> Optional[City]:
        """Found a new city using a ready settler.

        Args:
            name: Name for the new city
            all_resources: Dictionary of all available resources for initialization

        Returns:
            The newly founded City, or None if no settlers available
        """
        if self.ready_settlers <= 0:
            return None

        # Create the city with reduced starting population (settlers left the original city)
        import random
        starting_pop = random.randint(1, 3)
        resource_count = random.randint(1, 3)

        city = self.add_city(name, starting_city=False, starting_population=starting_pop,
                            starting_resource_count=resource_count)

        # Initialize resources for the new city
        city.initialize_starting_resources(all_resources, count=resource_count)

        # Load building definitions into the new city
        # (We need to copy building definitions from another city or the game data manager)
        if self.cities and len(self.cities) > 1:
            # Copy building definitions from the first city
            source_city = self.cities[0]
            for building_id, building_def in source_city.buildings.building_definitions.items():
                city.buildings.add_building_definition(building_def)

        # Consume the settler
        self.ready_settlers -= 1

        return city

    def get_city(self, city_id: str) -> Optional[City]:
        """Get a city by its ID."""
        for city in self.cities:
            if city.id == city_id:
                return city
        return None

    def get_city_by_name(self, name: str) -> Optional[City]:
        """Get a city by its name."""
        for city in self.cities:
            if city.name.lower() == name.lower():
                return city
        return None

    def get_active_city(self) -> Optional[City]:
        """Get the currently active city."""
        if self.active_city_id is None and self.cities:
            self.active_city_id = self.cities[0].id
        return self.get_city(self.active_city_id) if self.active_city_id else None

    def set_active_city(self, city_id: str) -> bool:
        """Set the active city. Returns True if successful."""
        if self.get_city(city_id) is not None:
            self.active_city_id = city_id
            return True
        return False

    def remove_city(self, city_id: str) -> bool:
        """Remove a city. Returns True if successful."""
        city = self.get_city(city_id)
        if city is None:
            return False

        self.cities.remove(city)

        # Update active city if needed
        if self.active_city_id == city_id:
            self.active_city_id = self.cities[0].id if self.cities else None

        return True

    def get_total_population(self) -> int:
        """Get total population across all cities."""
        return sum(city.population.total for city in self.cities)

    def initialize_starting_resources(self) -> None:
        """Set up initial civilization-wide resources."""
        # Add basic research points (civilization-wide)
        research_type = ResourceType(
            id="research",
            name="Research Points",
            category=ResourceCategory.ABSTRACT,
            description="Used to unlock technologies",
            base_storage_cap=1000.0
        )
        self.resources.add_resource_type(research_type, initial_amount=0.0)

    def load_tech_tree(self, technologies: dict):
        """Load technology definitions into the tech tree.

        Args:
            technologies: Dictionary of tech_id -> TechnologyDefinition
        """
        for tech_id, tech_def in technologies.items():
            self.tech_tree.add_technology(tech_def)

    def load_buildings(self, buildings: dict):
        """Load building definitions into all city building managers.

        Args:
            buildings: Dictionary of building_id -> BuildingDefinition
        """
        for city in self.cities:
            for building_id, building_def in buildings.items():
                city.buildings.add_building_definition(building_def)

    def initialize_available_resources(self, all_resources: dict):
        """Initialize starting resources for the capital city.

        Args:
            all_resources: Dictionary of resource_id -> ResourceType
        """
        capital = self.get_active_city()
        if capital:
            capital.initialize_starting_resources(all_resources, count=3)

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
            "cities": {},
            "total_population": 0,
            "total_population_change": 0,
        }

        # Update all cities
        total_research_output = 0.0
        settlers_completed = 0
        for city in self.cities:
            city_summary = city.update(delta_time)
            update_summary["cities"][city.id] = city_summary
            update_summary["total_population"] += city.population.total
            update_summary["total_population_change"] += city_summary.get("population_change", 0)

            # Check for completed settlers (handle specially)
            completed_buildings_to_keep = []
            for completed_building_name in city_summary.get("completed_buildings", []):
                # Find the actual building in the city
                matching_buildings = [b for b in city.buildings.buildings
                                     if b.definition.name == completed_building_name]
                if matching_buildings:
                    building = matching_buildings[-1]  # Get the most recently added
                    if building.definition.id == "settler":
                        # Remove from buildings list - it doesn't stay in the city
                        city.buildings.buildings.remove(building)
                        settlers_completed += 1
                    else:
                        completed_buildings_to_keep.append(completed_building_name)
                else:
                    completed_buildings_to_keep.append(completed_building_name)

            # Update summary to only show non-settler buildings
            city_summary["completed_buildings"] = completed_buildings_to_keep

            # Calculate research contribution from this city
            research_workers = city.population.get_workers_on_task(WorkforceTask.RESEARCH)
            city_research = research_workers * 1.0 * (1.0 + city.population.literacy) * delta_time
            total_research_output += city_research

        # Add completed settlers to ready count
        if settlers_completed > 0:
            self.ready_settlers += settlers_completed
            update_summary["settlers_completed"] = settlers_completed

        # Update civilization-wide research
        research_resource = self.resources.get("research")
        if research_resource:
            # Calculate total research rate for display
            total_research_workers = sum(city.population.get_workers_on_task(WorkforceTask.RESEARCH)
                                        for city in self.cities)
            avg_literacy = sum(city.population.literacy for city in self.cities) / len(self.cities) if self.cities else 0
            research_resource.production_rate = total_research_workers * 1.0 * (1.0 + avg_literacy)
            research_resource.add(total_research_output)

        # Update tech tree
        if self.tech_tree.current_research:
            completed_tech = self.tech_tree.add_research_points(total_research_output)
            if completed_tech:
                update_summary["completed_techs"].append(completed_tech.name)
                self._apply_tech_effects(completed_tech.id)

        return update_summary

    def _apply_tech_effects(self, tech_id: str) -> None:
        """Apply effects when a technology is completed."""
        tech = self.tech_tree.get_technology(tech_id)
        if not tech:
            return

        # Apply any direct effects from the technology to all cities
        for city in self.cities:
            for effect_key, value in tech.effects.items():
                if effect_key == "literacy_bonus":
                    city.population.literacy += value
                elif effect_key == "housing_capacity":
                    city.population.housing_capacity += int(value)

    def get_current_era(self) -> Era:
        """Get the current era based on researched technologies."""
        return self.current_era

    def advance_era(self) -> None:
        """Advance to the next era."""
        eras = list(Era)
        current_index = eras.index(self.current_era)
        if current_index < len(eras) - 1:
            self.current_era = eras[current_index + 1]

    # Convenience methods that delegate to active city
    @property
    def population(self):
        """Get population of active city (for backwards compatibility)."""
        city = self.get_active_city()
        return city.population if city else None

    @property
    def buildings(self):
        """Get buildings of active city (for backwards compatibility)."""
        city = self.get_active_city()
        return city.buildings if city else None

    @property
    def available_resources(self):
        """Get available resources of active city (for backwards compatibility)."""
        city = self.get_active_city()
        return city.available_resources if city else set()

    def get_total_food_from_crops(self) -> float:
        """Get total food from crops in active city (for backwards compatibility)."""
        city = self.get_active_city()
        return city.get_total_food_from_crops() if city else 0.0

    def can_afford_costs(self, costs: list) -> bool:
        """Check if active city can afford costs (for backwards compatibility)."""
        city = self.get_active_city()
        return city.can_afford_costs(costs) if city else False

    def spend_costs(self, costs: list) -> bool:
        """Spend costs from active city (for backwards compatibility)."""
        city = self.get_active_city()
        return city.spend_costs(costs) if city else False
