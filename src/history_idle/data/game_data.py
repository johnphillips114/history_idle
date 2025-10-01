"""Game data manager for loading C2C content."""

from typing import Optional
from pathlib import Path

from .c2c_loader import C2CDataLoader
from .c2c_parser import C2CDataParser
from ..models import TechnologyDefinition, ResourceType, BuildingDefinition


class GameDataManager:
    """Manages loading and accessing game data."""

    def __init__(self, cache_dir: Optional[Path] = None):
        self.loader = C2CDataLoader(cache_dir)
        self.parser = C2CDataParser()

        self.technologies: dict[str, TechnologyDefinition] = {}
        self.resources: dict[str, ResourceType] = {}
        self.buildings: dict[str, BuildingDefinition] = {}

        self._loaded = False

    def load_all(self):
        """Load all game data."""
        print("Loading game data...")
        self.load_technologies()
        print(f"Loaded {len(self.technologies)} technologies")
        self.load_resources()
        print(f"Loaded {len(self.resources)} resources")
        self.load_buildings()
        print(f"Loaded {len(self.buildings)} buildings")

    def load_technologies(self):
        """Load technology tree from C2C data."""
        xml_content = self.loader.get_tech_xml()
        tech_list = self.parser.parse_technologies_xml(xml_content)

        for tech in tech_list:
            self.technologies[tech.id] = tech

        self._loaded = True

    def load_resources(self):
        """Load resources from C2C data."""
        xml_content = self.loader.get_bonus_xml()
        resource_list = self.parser.parse_bonuses_xml(xml_content)

        for resource in resource_list:
            self.resources[resource.id] = resource

    def load_buildings(self):
        """Load buildings from C2C data."""
        xml_content = self.loader.get_building_xml()
        building_list = self.parser.parse_buildings_xml(xml_content)

        for building in building_list:
            self.buildings[building.id] = building

    def get_technology(self, tech_id: str) -> Optional[TechnologyDefinition]:
        """Get a technology by ID."""
        return self.technologies.get(tech_id)

    def get_starting_technologies(self) -> list[TechnologyDefinition]:
        """Get all technologies with no prerequisites."""
        return [tech for tech in self.technologies.values() if not tech.prerequisites]

    def get_resource(self, resource_id: str) -> Optional[ResourceType]:
        """Get a resource by ID."""
        return self.resources.get(resource_id)

    def get_building(self, building_id: str) -> Optional[BuildingDefinition]:
        """Get a building by ID."""
        return self.buildings.get(building_id)
