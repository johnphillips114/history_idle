"""Test food production bug."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.history_idle.models import Civilization, StartingLocation, WorkforceTask
from src.history_idle.systems.game_loop import GameLoop
from src.history_idle.data.game_data import GameDataManager

# Load game data
game_data = GameDataManager()
game_data.load_all()

# Create civilization
civ = Civilization(
    name="Test",
    starting_location=StartingLocation.MESOPOTAMIA
)
civ.initialize_starting_resources()
civ.load_tech_tree(game_data.technologies)
civ.load_buildings(game_data.buildings)
civ.initialize_available_resources(game_data.resources)

city = civ.get_active_city()

print("=== Testing Food Production Bug ===\n")
print(f"Initial state:")
print(f"  Population: {civ.population.total}")
print(f"  Happiness: {civ.population.happiness}")
print(f"  Food consumption per capita: {civ.population.food_consumption_per_capita}")
print(f"  Total food consumption: {civ.population.calculate_food_consumption():.2f}/s")

food_res = city.resources.get('food')
print(f"  Food: {food_res.amount if food_res else 0.0:.1f}")

# Find a crop resource and allocate workers to it
crop_resource = None
for res_id in city.available_resources:
    resource = game_data.resources.get(res_id)
    if resource and resource.bonus_class == 'crop':
        crop_resource = resource
        break

if not crop_resource:
    print("❌ No crop resource found!")
    sys.exit(1)

print(f"\nFound crop resource: {crop_resource.name} (ID: {crop_resource.id})")

# Research the required tech if needed
if crop_resource.tech_reveal and crop_resource.tech_reveal not in civ.tech_tree.researched:
    civ.tech_tree.researched.add(crop_resource.tech_reveal)

# Add the crop resource to city storage
city.resources.add_resource_type(crop_resource, initial_amount=0.0)

# Allocate 9 workers to crop
print(f"\nAllocating 9 workers to {crop_resource.name}...")
civ.population.allocate_workers(WorkforceTask.RESOURCE_EXTRACTION, 9, resource_id=crop_resource.id)

crop_workers = civ.population.get_workers_on_resource(crop_resource.id)
print(f"  {crop_resource.name} workers: {crop_workers}")

# Calculate expected rates
expected_production = crop_workers * 2.0 * civ.population.happiness
expected_consumption = civ.population.calculate_food_consumption()
expected_net = expected_production - expected_consumption

print(f"\nExpected rates:")
print(f"  Production: {expected_production:.2f}/s ({crop_workers} workers × 2.0 × {civ.population.happiness} happiness)")
print(f"  Consumption: {expected_consumption:.2f}/s ({civ.population.total} pop × {civ.population.food_consumption_per_capita})")
print(f"  Net: {expected_net:.2f}/s")

# Run one update
print(f"\n--- Running update for 10 seconds ---")
game_loop = GameLoop(civ)
update = game_loop.tick(10.0)

food_res = city.resources.get('food')
print(f"\nAfter update:")
print(f"  Food: {food_res.amount:.2f}/{food_res.capacity:.2f}")
print(f"  Actual production rate: {food_res.production_rate:.2f}/s")
print(f"  Actual consumption rate: {food_res.consumption_rate:.2f}/s")
print(f"  Actual net rate: {food_res.net_rate:.2f}/s")

# Check if rates match
print(f"\n--- Verification ---")
if abs(food_res.production_rate - expected_production) < 0.01:
    print(f"✓ Production rate matches expected")
else:
    print(f"✗ Production rate mismatch! Expected {expected_production:.2f}, got {food_res.production_rate:.2f}")

if abs(food_res.consumption_rate - expected_consumption) < 0.01:
    print(f"✓ Consumption rate matches expected")
else:
    print(f"✗ Consumption rate mismatch! Expected {expected_consumption:.2f}, got {food_res.consumption_rate:.2f}")

if abs(food_res.net_rate - expected_net) < 0.01:
    print(f"✓ Net rate matches expected")
else:
    print(f"✗ Net rate mismatch! Expected {expected_net:.2f}, got {food_res.net_rate:.2f}")

# Run more updates to see if food accumulates
print(f"\n--- Running 5 more updates (50 seconds total) ---")
for i in range(5):
    update = game_loop.tick(10.0)
    print(f"  Tick {i+1}: Food = {food_res.amount:.2f}, Net = {food_res.net_rate:.2f}/s")
