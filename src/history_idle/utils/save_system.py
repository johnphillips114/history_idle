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
                        'base_storage_cap': res.resource_type.base_storage_cap
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
                    'progress': construction.progress
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
                base_storage_cap=rt_data['base_storage_cap']
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

        # Note: Technologies, buildings definitions need to be loaded separately
        # from game data, not from save files

        return civ
