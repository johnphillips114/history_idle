from typing import Optional
from pathlib import Path

from .json_loader import GameDataLoader
from ..models import (
    TechnologyDefinition,
    ResourceType,
    BuildingDefinition,
    CivilizationDefinition,
    TerrainType,
)


class GameDataManager:
    def __init__(self, cache_dir: Optional[Path] = None, use_json: bool = True):
        self.use_json = use_json

        if use_json:
            self.json_loader = GameDataLoader()
            self.loader = None
            self.parser = None

        self.technologies: dict[str, TechnologyDefinition] = {}
        self.resources: dict[str, ResourceType] = {}
        self.buildings: dict[str, BuildingDefinition] = {}
        self.civilizations: dict[str, CivilizationDefinition] = {}
        self.terrains: dict[str, TerrainType] = {}

        self.buildings_text: dict[str, str] = {}
        self.technologies_text: dict[str, str] = {}

        self._loaded = False

    def load_all(self):
        print("Loading game data...")
        self.load_technologies()
        print(f"Loaded {len(self.technologies)} technologies")
        self.load_resources()
        print(f"Loaded {len(self.resources)} resources")
        self.load_buildings()
        print(f"Loaded {len(self.buildings)} buildings")
        self.add_custom_buildings()
        print(f"Total buildings with custom: {len(self.buildings)}")
        self.load_civilizations()
        print(f"Loaded {len(self.civilizations)} civilizations")
        self.load_terrains()
        print(f"Loaded {len(self.terrains)} terrains")
        self.load_gametext()
        print(
            f"Loaded {len(self.buildings_text)} building texts and {len(self.technologies_text)} technology texts"
        )

    def load_technologies(self):
        self.technologies = self.json_loader.load_technologies()
        self._loaded = True

    def load_resources(self):
        self.resources = self.json_loader.load_resources()

    def load_buildings(self):
        self.buildings = self.json_loader.load_buildings()

    def get_technology(self, tech_id: str) -> Optional[TechnologyDefinition]:
        return self.technologies.get(tech_id)

    def get_starting_technologies(self) -> list[TechnologyDefinition]:
        return [tech for tech in self.technologies.values() if not tech.prerequisites]

    def get_resource(self, resource_id: str) -> Optional[ResourceType]:
        return self.resources.get(resource_id)

    def get_building(self, building_id: str) -> Optional[BuildingDefinition]:
        return self.buildings.get(building_id)

    def load_civilizations(self):
        self.civilizations = self.json_loader.load_civilizations()

    def get_civilization(self, civ_id: str) -> Optional[CivilizationDefinition]:
        return self.civilizations.get(civ_id)

    def get_random_civilization(self) -> Optional[CivilizationDefinition]:
        import random

        if self.civilizations:
            return random.choice(list(self.civilizations.values()))
        return None

    def register_building(self, building: BuildingDefinition):
        self.buildings[building.id] = building

    def load_terrains(self):
        self.terrains = self.json_loader.load_terrains()

    def get_terrain(self, terrain_id: str) -> Optional[TerrainType]:
        return self.terrains.get(terrain_id)

    def get_random_suitable_terrain(self) -> Optional[TerrainType]:
        import random

        suitable_terrains = [t for t in self.terrains.values() if t.can_found]
        if suitable_terrains:
            return random.choice(suitable_terrains)
        return None

    def load_gametext(self):
        text_data = self.json_loader.load_text_data()
        self.buildings_text = text_data["buildings_text"]
        self.technologies_text = text_data["technologies_text"]
