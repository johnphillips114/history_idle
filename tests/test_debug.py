"""Test debug mode manually."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.history_idle.models import Civilization, StartingLocation, WorkforceTask
from src.history_idle.systems.game_loop import GameLoop
from src.history_idle.utils.save_system import SaveSystem

# Create a new civilization
civ = Civilization(
    name="Debug Test Civilization",
    starting_location=StartingLocation.MESOPOTAMIA
)
civ.initialize_starting_resources()

print("=== Initial State ===")
print(f"Population: {civ.population.total}")
print(f"Happiness: {civ.population.happiness:.2f}")
print(f"Food consumption per capita: {civ.population.food_consumption_per_capita:.2f}")
print(f"Total food consumption: {civ.population.calculate_food_consumption():.2f}/s")
print(f"Food: {civ.resources.get('food').amount:.1f}")

# Allocate workers
print("\n=== Allocating Workers ===")
civ.population.allocate_workers(WorkforceTask.RESOURCE_EXTRACTION, 6, resource_id="food")
print(f"Allocated 6 workers to food")

food_workers = civ.population.get_workers_on_resource("food")
print(f"\nFood workers: {food_workers}")
print(f"Expected production: {food_workers * 2.0 * civ.population.happiness:.2f}/s")
print(f"Expected consumption: {civ.population.calculate_food_consumption():.2f}/s")
print(f"Expected net: {(food_workers * 2.0 * civ.population.happiness) - civ.population.calculate_food_consumption():.2f}/s")

# Run one update
print("\n=== Running Update (10s) ===")
game_loop = GameLoop(civ)
update = game_loop.tick(10.0)

print(f"\nUpdate results:")
print(f"  Delta time: {update['delta_time']:.2f}s")
print(f"  Resource changes: {update['resource_changes']}")
print(f"  Population change: {update['population_change']}")

print(f"\nAfter update:")
food_res = civ.resources.get('food')
print(f"Food: {food_res.amount:.1f}/{food_res.capacity:.1f}")
print(f"  Production rate: {food_res.production_rate:.2f}/s")
print(f"  Consumption rate: {food_res.consumption_rate:.2f}/s")
print(f"  Net rate: {food_res.net_rate:.2f}/s")
