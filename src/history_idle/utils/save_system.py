"""Save and load system for game state."""

import json
import os
from pathlib import Path
from typing import Optional
from datetime import datetime

from ..models import Civilization, StartingLocation, GovernmentType, Era, WorkforceTask


class SaveSystem:
    """Handles saving and loading game state."""

    def __init__(self, save_directory: Optional[Path] = None):
        if save_directory is None:
            # Default to user's home directory
            home = Path.home()
            self.save_directory = home / '.history_idle' / 'saves'
        else:
            self.save_directory = Path(save_directory)

        # Create directory if it doesn't exist
        self.save_directory.mkdir(parents=True, exist_ok=True)

    def save_game(self, civilization: Civilization, save_name: str = "autosave") -> bool:
        """Save the game state to a file.

        Args:
            civilization: The civilization to save
            save_name: Name for the save file

        Returns:
            True if save was successful
        """
        try:
            save_data = self._serialize_civilization(civilization)

            # Add metadata
            save_data['metadata'] = {
                'save_name': save_name,
                'timestamp': datetime.now().isoformat(),
                'version': '0.1.0'
            }

            # Write to file
            save_path = self.save_directory / f"{save_name}.json"
            with open(save_path, 'w') as f:
                json.dump(save_data, f, indent=2)

            return True

        except Exception as e:
            print(f"Error saving game: {e}")
            return False

    def load_game(self, save_name: str = "autosave") -> Optional[Civilization]:
        """Load a game state from a file.

        Args:
            save_name: Name of the save file to load

        Returns:
            Loaded Civilization or None if load failed
        """
        try:
            save_path = self.save_directory / f"{save_name}.json"

            if not save_path.exists():
                print(f"Save file not found: {save_path}")
                return None

            with open(save_path, 'r') as f:
                save_data = json.load(f)

            civilization = self._deserialize_civilization(save_data)
            return civilization

        except Exception as e:
            print(f"Error loading game: {e}")
            return None

    def list_saves(self) -> list[dict]:
        """List all available save files.

        Returns:
            List of dictionaries with save information
        """
        saves = []

        for save_file in self.save_directory.glob("*.json"):
            try:
                with open(save_file, 'r') as f:
                    data = json.load(f)
                    metadata = data.get('metadata', {})

                    saves.append({
                        'name': save_file.stem,
                        'timestamp': metadata.get('timestamp', 'Unknown'),
                        'civilization_name': data.get('name', 'Unknown'),
                        'era': data.get('current_era', 'Unknown'),
                        'population': data.get('population', {}).get('total', 0)
                    })
            except Exception:
                continue

        return sorted(saves, key=lambda x: x['timestamp'], reverse=True)

    def delete_save(self, save_name: str) -> bool:
        """Delete a save file.

        Args:
            save_name: Name of the save to delete

        Returns:
            True if deletion was successful
        """
        try:
            save_path = self.save_directory / f"{save_name}.json"
            if save_path.exists():
                save_path.unlink()
                return True
            return False
        except Exception as e:
            print(f"Error deleting save: {e}")
            return False

    def _serialize_civilization(self, civ: Civilization) -> dict:
        """Convert civilization to JSON-serializable dictionary."""
        return {
            'name': civ.name,
            'starting_location': civ.starting_location.value,
            'current_era': civ.current_era.value,
            'government': civ.government.value,
            'game_time': civ.game_time,
            'prestige_points': civ.prestige_points,
            'prestige_count': civ.prestige_count,
            'available_resources': list(civ.available_resources),

            'resources': self._serialize_resources(civ.resources),
            'population': self._serialize_population(civ.population),
            'tech_tree': self._serialize_tech_tree(civ.tech_tree),
            'buildings': self._serialize_buildings(civ.buildings),
        }

    def _serialize_resources(self, resources) -> dict:
        """Serialize resource storage."""
        return {
            'resources': {
                res_id: {
                    'amount': res.amount,
                    'capacity': res.capacity,
                    'production_rate': res.production_rate,
                    'consumption_rate': res.consumption_rate,
                    'resource_type': {
                        'id': res.resource_type.id,
                        'name': res.resource_type.name,
                        'category': res.resource_type.category.value,
                        'description': res.resource_type.description,
                        'can_store': res.resource_type.can_store,
                        'base_storage_cap': res.resource_type.base_storage_cap,
                        'tech_reveal': res.resource_type.tech_reveal,
                        'bonus_class': res.resource_type.bonus_class
                    }
                }
                for res_id, res in resources.resources.items()
            }
        }

    def _serialize_population(self, pop) -> dict:
        """Serialize population."""
        return {
            'total': pop.total,
            'growth_rate': pop.growth_rate,
            'happiness': pop.happiness,
            'literacy': pop.literacy,
            'housing_capacity': pop.housing_capacity,
            'food_consumption_per_capita': pop.food_consumption_per_capita,
            'allocations': [
                {
                    'task': alloc.task.value,
                    'resource_id': alloc.resource_id,
                    'building_id': alloc.building_id,
                    'count': alloc.count
                }
                for alloc in pop.allocations
            ]
        }

    def _serialize_tech_tree(self, tech_tree) -> dict:
        """Serialize technology tree."""
        return {
            'researched': list(tech_tree.researched),
            'current_research': {
                'tech_id': tech_tree.current_research.tech_def.id,
                'research_points': tech_tree.current_research.research_points
            } if tech_tree.current_research else None,
            'research_queue': tech_tree.research_queue
        }

    def _serialize_buildings(self, buildings) -> dict:
        """Serialize building manager."""
        return {
            'buildings': [
                {
                    'definition_id': building.definition.id,
                    'is_active': building.is_active,
                    'assigned_workers': building.assigned_workers
                }
                for building in buildings.buildings
            ],
            'under_construction': [
                {
                    'building_id': construction.building_def.id,
                    'progress': construction.progress,
                    'required_production': construction.required_production
                }
                for construction in buildings.under_construction
            ],
            'construction_queue': buildings.construction_queue
        }

    def _deserialize_civilization(self, data: dict) -> Civilization:
        """Convert dictionary to Civilization object."""
        from ..models import Civilization, ResourceStorage, Population, TechTree, BuildingManager
        from ..models.resource import ResourceType, ResourceQuantity, ResourceCategory
        from ..models.population import WorkforceAllocation

        civ = Civilization(
            name=data['name'],
            starting_location=StartingLocation(data['starting_location']),
            current_era=Era(data['current_era']),
            government=GovernmentType(data['government'])
        )

        civ.game_time = data['game_time']
        civ.prestige_points = data['prestige_points']
        civ.prestige_count = data['prestige_count']
        civ.available_resources = set(data.get('available_resources', []))

        # Deserialize resources
        resources_data = data['resources']['resources']
        for res_id, res_data in resources_data.items():
            rt_data = res_data['resource_type']
            resource_type = ResourceType(
                id=rt_data['id'],
                name=rt_data['name'],
                category=ResourceCategory(rt_data['category']),
                description=rt_data['description'],
                can_store=rt_data['can_store'],
                base_storage_cap=rt_data['base_storage_cap'],
                tech_reveal=rt_data.get('tech_reveal'),
                bonus_class=rt_data.get('bonus_class')
            )

            civ.resources.add_resource_type(resource_type, initial_amount=res_data['amount'])
            resource = civ.resources.get(res_id)
            if resource:
                resource.capacity = res_data['capacity']
                resource.production_rate = res_data['production_rate']
                resource.consumption_rate = res_data['consumption_rate']

        # Deserialize population
        pop_data = data['population']
        civ.population.total = pop_data['total']
        civ.population.growth_rate = pop_data['growth_rate']
        civ.population.happiness = pop_data['happiness']
        civ.population.literacy = pop_data['literacy']
        civ.population.housing_capacity = pop_data['housing_capacity']

        # Fix old saves that had food_consumption_per_capita = 1.0
        # New default is 0.5 per second
        if pop_data.get('food_consumption_per_capita', 1.0) == 1.0:
            civ.population.food_consumption_per_capita = 0.5
        else:
            civ.population.food_consumption_per_capita = pop_data['food_consumption_per_capita']

        for alloc_data in pop_data['allocations']:
            allocation = WorkforceAllocation(
                task=WorkforceTask(alloc_data['task']),
                resource_id=alloc_data['resource_id'],
                building_id=alloc_data['building_id'],
                count=alloc_data['count']
            )
            civ.population.allocations.append(allocation)

        # Deserialize tech tree
        tech_data = data['tech_tree']
        civ.tech_tree.researched = set(tech_data['researched'])
        civ.tech_tree.research_queue = tech_data['research_queue']

        # Store buildings and tech tree data for restoration after definitions are loaded
        # (definitions need to be loaded from game data first)
        civ._saved_buildings_data = data.get('buildings', {})
        civ._saved_tech_data = tech_data

        return civ

    def restore_from_save_data(self, civilization: Civilization) -> None:
        """Restore buildings and current research from saved data.

        Must be called AFTER load_tech_tree() and load_buildings() have been called
        to load the definitions.

        Args:
            civilization: The civilization to restore
        """
        # Restore buildings from saved data
        if hasattr(civilization, '_saved_buildings_data'):
            buildings_data = civilization._saved_buildings_data

            # Restore completed buildings
            for building_data in buildings_data.get('buildings', []):
                building_def = civilization.buildings.get_building_definition(building_data['definition_id'])
                if building_def:
                    from ..models.building import Building
                    building = Building(
                        definition=building_def,
                        is_active=building_data['is_active'],
                        assigned_workers=building_data['assigned_workers']
                    )
                    civilization.buildings.buildings.append(building)

            # Restore buildings under construction
            for construction_data in buildings_data.get('under_construction', []):
                building_def = civilization.buildings.get_building_definition(construction_data['building_id'])
                if building_def:
                    from ..models.building import BuildingConstruction
                    construction = BuildingConstruction(
                        building_def=building_def,
                        progress=construction_data['progress'],
                        required_production=construction_data['required_production']
                    )
                    civilization.buildings.under_construction.append(construction)

            # Restore construction queue
            civilization.buildings.construction_queue = buildings_data.get('construction_queue', [])

            # Clean up temporary data
            del civilization._saved_buildings_data

        # Restore current research from saved data
        if hasattr(civilization, '_saved_tech_data'):
            tech_data = civilization._saved_tech_data

            if tech_data.get('current_research'):
                from ..models.technology import ResearchProgress
                tech_id = tech_data['current_research']['tech_id']
                tech_def = civilization.tech_tree.get_technology(tech_id)

                if tech_def:
                    research = ResearchProgress(
                        tech_def=tech_def,
                        research_points=tech_data['current_research']['research_points']
                    )
                    civilization.tech_tree.current_research = research

            # Clean up temporary data
            del civilization._saved_tech_data
