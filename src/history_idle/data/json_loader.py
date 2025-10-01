import json
import os
from pathlib import Path
from typing import Optional

from ..models.building import BuildingDefinition, BuildingCategory, ResourceCost
from ..models.technology import TechnologyDefinition, TechCategory, Era
from ..models.resource import ResourceType, ResourceCategory
from ..models.terrain import TerrainType
from ..models.civilization_definition import CivilizationDefinition


class GameDataLoader:
    """Loads game data from JSON files."""

    def __init__(self, data_dir: Optional[str] = None):
        if data_dir is None:
            # Default to data/game/ in the project root
            current_file = Path(__file__)
            project_root = current_file.parent.parent.parent.parent
            data_dir = project_root / "data" / "game"

        self.data_dir = Path(data_dir)

    def _load_json(self, filename: str) -> dict:
        """Load a JSON file from the data directory."""
        filepath = self.data_dir / filename
        if not filepath.exists():
            raise FileNotFoundError(f"Data file not found: {filepath}")

        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    def load_buildings(self) -> dict[str, BuildingDefinition]:
        """Load buildings from buildings.json."""
        data = self._load_json("buildings.json")
        buildings = {}

        for building_id, building_data in data.items():
            # Parse construction costs
            construction_costs = []
            if building_data.get("construction_cost"):
                construction_costs.append(
                    ResourceCost("production", building_data["construction_cost"])
                )

            # Parse category
            category_str = building_data.get("category", "infrastructure")
            try:
                category = BuildingCategory(category_str)
            except ValueError:
                category = BuildingCategory.INFRASTRUCTURE

            # Create building definition
            building = BuildingDefinition(
                id=building_id,
                name=building_data["name"],
                description=building_data.get("description", ""),
                category=category,
                construction_costs=construction_costs,
                construction_time=building_data.get("construction_time", 0.0),
                required_tech=building_data.get("required_tech"),
                required_resources=building_data.get("required_resources", []),
                required_buildings=building_data.get("required_buildings", []),
                max_count=building_data.get("max_count", -1),
                effects={},  # Keep effects empty for now, use flavors
                flavors=building_data.get("bonuses", {}),
                vicinity_bonus=building_data.get("vicinity_bonus"),
                prereq_or_terrain=building_data.get("prereq_terrain", []),
            )

            buildings[building_id] = building

        return buildings

    def load_technologies(self) -> dict[str, TechnologyDefinition]:
        """Load technologies from technologies.json."""
        data = self._load_json("technologies.json")
        technologies = {}

        for tech_id, tech_data in data.items():
            # Parse era
            era_str = tech_data.get("era", "paleolithic")
            try:
                era = Era(era_str)
            except ValueError:
                era = Era.PALEOLITHIC

            # Create technology definition
            tech = TechnologyDefinition(
                id=tech_id,
                name=tech_data["name"],
                description=tech_data.get("description", ""),
                era=era,
                category=TechCategory.SCIENTIFIC,  # Default category
                research_cost=tech_data.get("research_cost", 100.0),
                prerequisites=tech_data.get("prerequisites", []),
                effects=tech_data.get("effects", {}),
            )

            technologies[tech_id] = tech

        return technologies

    def load_resources(self) -> dict[str, ResourceType]:
        """Load resources from resources.json."""
        data = self._load_json("resources.json")
        resources = {}

        for resource_id, resource_data in data.items():
            # Parse category
            category_str = resource_data.get("category", "strategic")
            try:
                category = ResourceCategory(category_str)
            except ValueError:
                category = ResourceCategory.STRATEGIC

            # Create resource type
            resource = ResourceType(
                id=resource_id,
                name=resource_data["name"],
                category=category,
                description=resource_data.get("description", ""),
                can_store=resource_data.get("can_store", True),
                base_storage_cap=resource_data.get("base_storage_cap", 100.0),
                tech_reveal=resource_data.get("tech_reveal"),
                bonus_class=resource_data.get("bonus_class"),
                compatible_terrains=resource_data.get("compatible_terrains", []),
            )

            resources[resource_id] = resource

        return resources

    def load_terrains(self) -> dict[str, TerrainType]:
        """Load terrains from terrains.json."""
        data = self._load_json("terrains.json")
        terrains = {}

        for terrain_id, terrain_data in data.items():
            yields = terrain_data.get("yields", {})

            terrain = TerrainType(
                id=terrain_id,
                name=terrain_data["name"],
                description=terrain_data.get("description", ""),
                can_found=terrain_data.get("can_found", True),
                food_yield=yields.get("food", 0.0),
                production_yield=yields.get("production", 0.0),
                currency_yield=yields.get("currency", 0.0),
            )

            terrains[terrain_id] = terrain

        return terrains

    def load_text_data(self) -> dict[str, dict[str, str]]:
        """
        Load text data for buildings and technologies.
        Returns a dict with 'buildings_text' and 'technologies_text'.
        """
        buildings_data = self._load_json("buildings.json")
        technologies_data = self._load_json("technologies.json")

        buildings_text = {}
        technologies_text = {}

        # Build text mappings similar to C2C GameText format
        for building_id, building_data in buildings_data.items():
            # PEDIA text
            pedia_key = f"TXT_KEY_BUILDING_{building_id.upper()}_PEDIA"
            if building_data.get("pedia"):
                buildings_text[pedia_key] = building_data["pedia"]

            # Quote text (if exists)
            quote_key = f"TXT_KEY_BUILDING_{building_id.upper()}_QUOTE"
            if building_data.get("quote"):
                buildings_text[quote_key] = building_data["quote"]

        for tech_id, tech_data in technologies_data.items():
            # Name
            name_key = f"TXT_KEY_TECH_{tech_id.upper()}"
            technologies_text[name_key] = tech_data["name"]

            # PEDIA text
            pedia_key = f"TXT_KEY_TECH_{tech_id.upper()}_PEDIA"
            if tech_data.get("pedia"):
                technologies_text[pedia_key] = tech_data["pedia"]

            # Quote text
            quote_key = f"TXT_KEY_TECH_{tech_id.upper()}_QUOTE"
            if tech_data.get("quote"):
                technologies_text[quote_key] = tech_data["quote"]

        return {
            "buildings_text": buildings_text,
            "technologies_text": technologies_text,
        }

    def load_civilizations(self) -> dict[str, CivilizationDefinition]:
        """Load civilization definitions from civilizations.json."""
        data = self._load_json("civilizations.json")
        civilizations = {}

        # Extract the civilizations section
        civs_data = data.get("civilizations", {})

        for civ_id, civ_data in civs_data.items():
            civ = CivilizationDefinition(
                id=civ_id,
                name=civ_data["name"],
                city_names=civ_data.get("city_names", []),
                leaders=civ_data.get("leaders", []),
                derivative_civ=civ_data.get("derivative_civ", "")
            )

            civilizations[civ_id] = civ

        return civilizations

    def load_civilization_data(self) -> dict:
        """Load civilization configuration data."""
        return self._load_json("civilizations.json")
