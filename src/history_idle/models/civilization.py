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
    name: str
    starting_location: StartingLocation
    current_era: Era = Era.PALEOLITHIC
    government: GovernmentType = GovernmentType.TRIBAL

    tech_tree: TechTree = field(default_factory=TechTree)
    resources: ResourceStorage = field(
        default_factory=ResourceStorage
    )  # Civilization-wide abstract resources (research)

    cities: list[City] = field(default_factory=list)
    active_city_id: Optional[str] = None
    ready_settlers: int = 0  # Number of settlers ready to found cities

    game_time: float = 0.0  # Total game time in seconds
    last_update_time: float = field(default_factory=time.time)

    prestige_points: int = 0
    prestige_count: int = 0

    # References to game data for tile generation
    _all_resources: dict = field(default_factory=dict)
    _all_terrains: dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.cities:
            self.add_city("Capital", starting_city=True)

    def add_city(
        self,
        name: str,
        starting_city: bool = False,
        starting_population: int = 10,
        starting_resource_count: int = 3,
        terrain: Optional[str] = None,
    ) -> City:
        city_id = str(uuid.uuid4())
        city = City(
            id=city_id,
            name=name,
            terrain=terrain,
        )
        city.population.total = starting_population
        city.population.housing_capacity = starting_population

        self.cities.append(city)

        if self.active_city_id is None:
            self.active_city_id = city_id

        return city

    def found_city(
        self, name: str, all_resources: dict, terrain: Optional[str] = None
    ) -> Optional[City]:
        if self.ready_settlers <= 0:
            return None

        import random

        starting_pop = random.randint(1, 3)
        resource_count = random.randint(1, 3)

        city = self.add_city(
            name,
            starting_city=False,
            starting_population=starting_pop,
            starting_resource_count=resource_count,
            terrain=terrain,
        )

        city.initialize_starting_resources(
            all_resources, self._all_terrains, count=resource_count
        )

        if self.cities and len(self.cities) > 1:
            source_city = self.cities[0]
            for (
                building_id,
                building_def,
            ) in source_city.buildings.building_definitions.items():
                city.buildings.add_building_definition(building_def)

        self.ready_settlers -= 1

        return city

    def get_city(self, city_id: str) -> Optional[City]:
        for city in self.cities:
            if city.id == city_id:
                return city
        return None

    def get_city_by_name(self, name: str) -> Optional[City]:
        for city in self.cities:
            if city.name.lower() == name.lower():
                return city
        return None

    def get_active_city(self) -> Optional[City]:
        if self.active_city_id is None and self.cities:
            self.active_city_id = self.cities[0].id
        return self.get_city(self.active_city_id) if self.active_city_id else None

    def set_active_city(self, city_id: str) -> bool:
        if self.get_city(city_id) is not None:
            self.active_city_id = city_id
            return True
        return False

    def remove_city(self, city_id: str) -> bool:
        city = self.get_city(city_id)
        if city is None:
            return False

        self.cities.remove(city)

        if self.active_city_id == city_id:
            self.active_city_id = self.cities[0].id if self.cities else None

        return True

    def get_total_population(self) -> int:
        return sum(city.population.total for city in self.cities)

    def initialize_starting_resources(self) -> None:
        research_type = ResourceType(
            id="research",
            name="Research Points",
            category=ResourceCategory.ABSTRACT,
            description="Used to unlock technologies",
            base_storage_cap=1000.0,
        )
        self.resources.add_resource_type(research_type, initial_amount=0.0)

    def load_tech_tree(self, technologies: dict):
        for tech_id, tech_def in technologies.items():
            self.tech_tree.add_technology(tech_def)

    def load_buildings(self, buildings: dict):
        for city in self.cities:
            for building_id, building_def in buildings.items():
                city.buildings.add_building_definition(building_def)

    def initialize_available_resources(self, all_resources: dict):
        self._all_resources = all_resources
        capital = self.get_active_city()
        if capital:
            capital.initialize_starting_resources(
                all_resources, self._all_terrains, count=3
            )

    def set_terrains(self, all_terrains: dict):
        """Store reference to all terrains for tile generation"""
        self._all_terrains = all_terrains

    def get_time_since_last_update(self) -> float:
        current_time = time.time()
        delta = current_time - self.last_update_time
        return delta

    def update(self, delta_time: Optional[float] = None) -> dict:
        if delta_time is None:
            delta_time = self.get_time_since_last_update()

        self.last_update_time = time.time()
        self.game_time += delta_time

        update_summary = {
            "delta_time": delta_time,
            "completed_techs": [],
            "completed_buildings": [],
            "cities": {},
            "total_population": 0,
            "total_population_change": 0,
        }

        total_research_output = 0.0
        settlers_completed = 0
        for city in self.cities:
            city_summary = city.update(delta_time)
            update_summary["cities"][city.id] = city_summary
            update_summary["total_population"] += city.population.total
            update_summary["total_population_change"] += city_summary.get(
                "population_change", 0
            )

            completed_buildings_to_keep = []
            for completed_building_id in city_summary.get("completed_buildings", []):
                matching_buildings = [
                    b
                    for b in city.buildings.buildings
                    if b.definition.id == completed_building_id
                ]
                if matching_buildings:
                    building = matching_buildings[-1]  # Get the most recently added
                    if building.definition.id == "settler":
                        city.buildings.buildings.remove(building)
                        settlers_completed += 1
                    else:
                        completed_buildings_to_keep.append(completed_building_id)
                        # Add to civilization-level completed buildings list for notifications
                        update_summary["completed_buildings"].append(
                            completed_building_id
                        )
                else:
                    completed_buildings_to_keep.append(completed_building_id)
                    # Add to civilization-level completed buildings list for notifications
                    update_summary["completed_buildings"].append(completed_building_id)

            city_summary["completed_buildings"] = completed_buildings_to_keep

            # Handle culture level-ups and generate tiles
            if city_summary.get("culture_level_up"):
                if self._all_terrains and self._all_resources:
                    new_tiles = city.generate_tiles(
                        self._all_terrains, self._all_resources, count=3
                    )
                    city_summary["new_tiles_count"] = len(new_tiles)

            research_workers = city.population.get_workers_on_task(
                WorkforceTask.RESEARCH
            )
            city_research = (
                research_workers * 1.0 * (1.0 + city.population.literacy) * delta_time
            )
            total_research_output += city_research

        if settlers_completed > 0:
            self.ready_settlers += settlers_completed
            update_summary["settlers_completed"] = settlers_completed

        research_resource = self.resources.get("research")
        if research_resource:
            total_research_workers = sum(
                city.population.get_workers_on_task(WorkforceTask.RESEARCH)
                for city in self.cities
            )
            avg_literacy = (
                sum(city.population.literacy for city in self.cities) / len(self.cities)
                if self.cities
                else 0
            )
            research_resource.production_rate = (
                total_research_workers * 1.0 * (1.0 + avg_literacy)
            )
            research_resource.add(total_research_output)

        if self.tech_tree.current_research:
            completed_tech = self.tech_tree.add_research_points(total_research_output)
            if completed_tech:
                update_summary["completed_techs"].append(completed_tech.id)
                self._apply_tech_effects(completed_tech.id)

        return update_summary

    def _apply_tech_effects(self, tech_id: str) -> None:
        tech = self.tech_tree.get_technology(tech_id)
        if not tech:
            return

        for city in self.cities:
            for effect_key, value in tech.effects.items():
                if effect_key == "literacy_bonus":
                    city.population.literacy += value
                elif effect_key == "housing_capacity":
                    city.population.housing_capacity += int(value)

    def get_current_era(self) -> Era:
        return self.current_era

    def advance_era(self) -> None:
        eras = list(Era)
        current_index = eras.index(self.current_era)
        if current_index < len(eras) - 1:
            self.current_era = eras[current_index + 1]

    @property
    def population(self):
        city = self.get_active_city()
        return city.population if city else None

    @property
    def buildings(self):
        city = self.get_active_city()
        return city.buildings if city else None

    @property
    def available_resources(self):
        city = self.get_active_city()
        return city.available_resources if city else set()

    def get_total_food_from_crops(self) -> float:
        city = self.get_active_city()
        return city.get_total_food_from_crops() if city else 0.0

    def can_afford_costs(self, costs: list) -> bool:
        city = self.get_active_city()
        return city.can_afford_costs(costs) if city else False

    def spend_costs(self, costs: list) -> bool:
        city = self.get_active_city()
        return city.spend_costs(costs) if city else False
