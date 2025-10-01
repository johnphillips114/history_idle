import json
from pathlib import Path
from typing import Optional
from datetime import datetime

from ..models import Civilization, StartingLocation, GovernmentType, Era, WorkforceTask


class SaveSystem:
    def __init__(self, save_directory: Optional[Path] = None):
        if save_directory is None:
            home = Path.home()
            self.save_directory = home / ".history_idle" / "saves"
        else:
            self.save_directory = Path(save_directory)

        self.save_directory.mkdir(parents=True, exist_ok=True)

    def save_game(
        self, civilization: Civilization, save_name: str = "autosave"
    ) -> bool:
        try:
            save_data = self._serialize_civilization(civilization)

            save_data["metadata"] = {
                "save_name": save_name,
                "timestamp": datetime.now().isoformat(),
                "version": "0.1.0",
            }

            save_path = self.save_directory / f"{save_name}.json"
            with open(save_path, "w") as f:
                json.dump(save_data, f, indent=2)

            return True

        except Exception as e:
            print(f"Error saving game: {e}")
            return False

    def load_game(self, save_name: str = "autosave") -> Optional[Civilization]:
        try:
            save_path = self.save_directory / f"{save_name}.json"

            if not save_path.exists():
                print(f"Save file not found: {save_path}")
                return None

            with open(save_path, "r") as f:
                save_data = json.load(f)

            civilization = self._deserialize_civilization(save_data)
            return civilization

        except Exception as e:
            print(f"Error loading game: {e}")
            return None

    def list_saves(self) -> list[dict]:
        saves = []

        for save_file in self.save_directory.glob("*.json"):
            try:
                with open(save_file, "r") as f:
                    data = json.load(f)
                    metadata = data.get("metadata", {})

                    saves.append(
                        {
                            "name": save_file.stem,
                            "timestamp": metadata.get("timestamp", "Unknown"),
                            "civilization_name": data.get("name", "Unknown"),
                            "era": data.get("current_era", "Unknown"),
                            "population": data.get("population", {}).get("total", 0),
                        }
                    )
            except Exception:
                continue

        return sorted(saves, key=lambda x: x["timestamp"], reverse=True)

    def delete_save(self, save_name: str) -> bool:
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
        return {
            "name": civ.name,
            "starting_location": civ.starting_location.value,
            "current_era": civ.current_era.value,
            "government": civ.government.value,
            "game_time": civ.game_time,
            "prestige_points": civ.prestige_points,
            "prestige_count": civ.prestige_count,
            "resources": self._serialize_resources(civ.resources),
            "tech_tree": self._serialize_tech_tree(civ.tech_tree),
            "cities": self._serialize_cities(civ.cities),
            "active_city_id": civ.active_city_id,
            "ready_settlers": civ.ready_settlers,
            "available_resources": list(civ.available_resources)
            if civ.get_active_city()
            else [],
            "population": self._serialize_population(civ.population)
            if civ.get_active_city()
            else {},
            "buildings": self._serialize_buildings(civ.buildings)
            if civ.get_active_city()
            else {},
        }

    def _serialize_resources(self, resources) -> dict:
        return {
            "resources": {
                res_id: {
                    "amount": res.amount,
                    "capacity": res.capacity,
                    "production_rate": res.production_rate,
                    "consumption_rate": res.consumption_rate,
                    "resource_type": {
                        "id": res.resource_type.id,
                        "name": res.resource_type.name,
                        "category": res.resource_type.category.value,
                        "description": res.resource_type.description,
                        "can_store": res.resource_type.can_store,
                        "base_storage_cap": res.resource_type.base_storage_cap,
                        "tech_reveal": res.resource_type.tech_reveal,
                        "bonus_class": res.resource_type.bonus_class,
                    },
                }
                for res_id, res in resources.resources.items()
            }
        }

    def _serialize_population(self, pop) -> dict:
        return {
            "total": pop.total,
            "growth_rate": pop.growth_rate,
            "happiness": pop.happiness,
            "literacy": pop.literacy,
            "housing_capacity": pop.housing_capacity,
            "food_consumption_per_capita": pop.food_consumption_per_capita,
            "allocations": [
                {
                    "task": alloc.task.value,
                    "resource_id": alloc.resource_id,
                    "building_id": alloc.building_id,
                    "count": alloc.count,
                }
                for alloc in pop.allocations
            ],
        }

    def _serialize_tech_tree(self, tech_tree) -> dict:
        return {
            "researched": list(tech_tree.researched),
            "current_research": {
                "tech_id": tech_tree.current_research.tech_def.id,
                "research_points": tech_tree.current_research.research_points,
            }
            if tech_tree.current_research
            else None,
            "research_queue": tech_tree.research_queue,
        }

    def _serialize_buildings(self, buildings) -> dict:
        return {
            "buildings": [
                {
                    "definition_id": building.definition.id,
                    "is_active": building.is_active,
                    "assigned_workers": building.assigned_workers,
                }
                for building in buildings.buildings
            ],
            "under_construction": [
                {
                    "building_id": construction.building_def.id,
                    "progress": construction.progress,
                    "required_production": construction.required_production,
                }
                for construction in buildings.under_construction
            ],
            "construction_queue": buildings.construction_queue,
        }

    def _serialize_cities(self, cities: list) -> list:
        return [
            {
                "id": city.id,
                "name": city.name,
                "resources": self._serialize_resources(city.resources),
                "population": self._serialize_population(city.population),
                "buildings": self._serialize_buildings(city.buildings),
                "available_resources": list(city.available_resources),
            }
            for city in cities
        ]

    def _deserialize_civilization(self, data: dict) -> Civilization:
        from ..models import (
            Civilization,
            ResourceStorage,
            Population,
            TechTree,
            BuildingManager,
            City,
        )
        from ..models.resource import ResourceType, ResourceQuantity, ResourceCategory
        from ..models.population import WorkforceAllocation

        civ = Civilization.__new__(Civilization)
        civ.name = data["name"]
        civ.starting_location = StartingLocation(data["starting_location"])
        civ.current_era = Era(data["current_era"])
        civ.government = GovernmentType(data["government"])
        civ.tech_tree = TechTree()
        civ.resources = ResourceStorage()
        civ.cities = []
        civ.active_city_id = None
        civ.ready_settlers = data.get("ready_settlers", 0)
        civ.game_time = data["game_time"]
        civ.prestige_points = data["prestige_points"]
        civ.prestige_count = data["prestige_count"]
        civ.last_update_time = __import__("time").time()

        resources_data = data["resources"]["resources"]
        for res_id, res_data in resources_data.items():
            rt_data = res_data["resource_type"]
            resource_type = ResourceType(
                id=rt_data["id"],
                name=rt_data["name"],
                category=ResourceCategory(rt_data["category"]),
                description=rt_data["description"],
                can_store=rt_data["can_store"],
                base_storage_cap=rt_data["base_storage_cap"],
                tech_reveal=rt_data.get("tech_reveal"),
                bonus_class=rt_data.get("bonus_class"),
            )

            civ.resources.add_resource_type(
                resource_type, initial_amount=res_data["amount"]
            )
            resource = civ.resources.get(res_id)
            if resource:
                resource.capacity = res_data["capacity"]
                resource.production_rate = res_data["production_rate"]
                resource.consumption_rate = res_data["consumption_rate"]

        tech_data = data["tech_tree"]
        civ.tech_tree.researched = set(tech_data["researched"])
        civ.tech_tree.research_queue = tech_data["research_queue"]

        if "cities" in data and data["cities"]:
            for city_data in data["cities"]:
                city = self._deserialize_city(city_data)
                civ.cities.append(city)
            civ.active_city_id = data.get("active_city_id")
        else:
            print("Loading old save format - migrating to multi-city...")
            city = City(id=str(__import__("uuid").uuid4()), name="Capital")

            if "population" in data:
                pop_data = data["population"]
                city.population.total = pop_data["total"]
                city.population.growth_rate = pop_data["growth_rate"]
                city.population.happiness = pop_data["happiness"]
                city.population.literacy = pop_data["literacy"]
                city.population.housing_capacity = pop_data["housing_capacity"]

                if pop_data.get("food_consumption_per_capita", 1.0) == 1.0:
                    city.population.food_consumption_per_capita = 0.5
                else:
                    city.population.food_consumption_per_capita = pop_data[
                        "food_consumption_per_capita"
                    ]

                for alloc_data in pop_data.get("allocations", []):
                    allocation = WorkforceAllocation(
                        task=WorkforceTask(alloc_data["task"]),
                        resource_id=alloc_data["resource_id"],
                        building_id=alloc_data["building_id"],
                        count=alloc_data["count"],
                    )
                    city.population.allocations.append(allocation)

            city.available_resources = set(data.get("available_resources", []))

            city._saved_buildings_data = data.get("buildings", {})

            civ.cities.append(city)
            civ.active_city_id = city.id

        civ._saved_tech_data = tech_data

        return civ

    def _deserialize_city(self, city_data: dict):
        from ..models import City
        from ..models.resource import ResourceType, ResourceQuantity, ResourceCategory
        from ..models.population import WorkforceAllocation

        city = City(id=city_data["id"], name=city_data["name"])

        if "resources" in city_data:
            resources_data = city_data["resources"]["resources"]
            for res_id, res_data in resources_data.items():
                rt_data = res_data["resource_type"]
                resource_type = ResourceType(
                    id=rt_data["id"],
                    name=rt_data["name"],
                    category=ResourceCategory(rt_data["category"]),
                    description=rt_data["description"],
                    can_store=rt_data["can_store"],
                    base_storage_cap=rt_data["base_storage_cap"],
                    tech_reveal=rt_data.get("tech_reveal"),
                    bonus_class=rt_data.get("bonus_class"),
                )

                city.resources.add_resource_type(
                    resource_type, initial_amount=res_data["amount"]
                )
                resource = city.resources.get(res_id)
                if resource:
                    resource.capacity = res_data["capacity"]
                    resource.production_rate = res_data["production_rate"]
                    resource.consumption_rate = res_data["consumption_rate"]

        if "population" in city_data:
            pop_data = city_data["population"]
            city.population.total = pop_data["total"]
            city.population.growth_rate = pop_data["growth_rate"]
            city.population.happiness = pop_data["happiness"]
            city.population.literacy = pop_data["literacy"]
            city.population.housing_capacity = pop_data["housing_capacity"]
            city.population.food_consumption_per_capita = pop_data.get(
                "food_consumption_per_capita", 0.5
            )

            for alloc_data in pop_data.get("allocations", []):
                allocation = WorkforceAllocation(
                    task=WorkforceTask(alloc_data["task"]),
                    resource_id=alloc_data["resource_id"],
                    building_id=alloc_data["building_id"],
                    count=alloc_data["count"],
                )
                city.population.allocations.append(allocation)

        city.available_resources = set(city_data.get("available_resources", []))

        city._saved_buildings_data = city_data.get("buildings", {})

        return city

    def restore_from_save_data(self, civilization: Civilization) -> None:
        for city in civilization.cities:
            if hasattr(city, "_saved_buildings_data"):
                buildings_data = city._saved_buildings_data

                for building_data in buildings_data.get("buildings", []):
                    building_def = city.buildings.get_building_definition(
                        building_data["definition_id"]
                    )
                    if building_def:
                        from ..models.building import Building

                        building = Building(
                            definition=building_def,
                            is_active=building_data["is_active"],
                            assigned_workers=building_data["assigned_workers"],
                        )
                        city.buildings.buildings.append(building)

                for construction_data in buildings_data.get("under_construction", []):
                    building_def = city.buildings.get_building_definition(
                        construction_data["building_id"]
                    )
                    if building_def:
                        from ..models.building import BuildingConstruction

                        construction = BuildingConstruction(
                            building_def=building_def,
                            progress=construction_data["progress"],
                            required_production=construction_data[
                                "required_production"
                            ],
                        )
                        city.buildings.under_construction.append(construction)

                city.buildings.construction_queue = buildings_data.get(
                    "construction_queue", []
                )

                del city._saved_buildings_data

        if hasattr(civilization, "_saved_tech_data"):
            tech_data = civilization._saved_tech_data

            if tech_data.get("current_research"):
                from ..models.technology import TechnologyProgress

                tech_id = tech_data["current_research"]["tech_id"]
                tech_def = civilization.tech_tree.get_technology(tech_id)

                if tech_def:
                    research = TechnologyProgress(
                        tech_def=tech_def,
                        research_points=tech_data["current_research"][
                            "research_points"
                        ],
                    )
                    civilization.tech_tree.current_research = research

            del civilization._saved_tech_data
