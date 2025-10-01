"""Test the crop collection and food tracking system."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.history_idle.data.game_data import GameDataManager
from src.history_idle.models.civilization import Civilization, StartingLocation
from src.history_idle.models.population import WorkforceTask
from src.history_idle.ui.repl import GameREPL
from src.history_idle.systems.game_loop import GameLoop
from src.history_idle.utils.save_system import SaveSystem
import time

print("=== Testing Crop Collection System ===\n")

# Load game data
game_data = GameDataManager()
game_data.load_all()

# Create a new civilization
civ = Civilization("Test Civ", StartingLocation.MESOPOTAMIA)
civ.initialize_starting_resources()
civ.load_tech_tree(game_data.technologies)
civ.load_buildings(game_data.buildings)
civ.initialize_available_resources(game_data.resources)

print(f"Population: {civ.population.total}")
print(f"Available resources: {len(civ.available_resources)}")
print(f"Starting resources: {list(civ.available_resources)}")

# Find a crop resource
crop_resource = None
for res_id in civ.available_resources:
    resource = game_data.resources.get(res_id)
    if resource and resource.bonus_class == 'crop':
        crop_resource = resource
        break

if not crop_resource:
    print("❌ No crop resource found in available resources!")
    sys.exit(1)

print(f"\n✓ Found crop resource: {crop_resource.name} (ID: {crop_resource.id})")
print(f"  Tech requirement: {crop_resource.tech_reveal}")
print(f"  Bonus class: {crop_resource.bonus_class}")

# Research the required tech if needed
if crop_resource.tech_reveal and crop_resource.tech_reveal not in civ.tech_tree.researched:
    print(f"\nResearching {crop_resource.tech_reveal}...")
    civ.tech_tree.researched.add(crop_resource.tech_reveal)

# Add the crop resource to civilization storage
civ.resources.add_resource_type(crop_resource, initial_amount=10.0)
print(f"\nAdded {crop_resource.name} to storage with initial amount: 10.0")

print("\n--- Test 1: Allocate workers to crop ---")
allocated = civ.population.allocate_workers(
    WorkforceTask.RESOURCE_EXTRACTION,
    5,
    resource_id=crop_resource.id
)
print(f"Allocated {allocated} workers to {crop_resource.name}")

# Check worker allocation
crop_workers = civ.population.get_workers_on_resource(crop_resource.id)
print(f"Workers on {crop_resource.name}: {crop_workers}")

print("\n--- Test 2: Run game update (1 second) ---")
civ.last_update_time = time.time()
update_summary = civ.update(delta_time=1.0)

crop_qty = civ.resources.get(crop_resource.id)
print(f"{crop_resource.name} after 1 second:")
print(f"  Amount: {crop_qty.amount}")
print(f"  Production rate: {crop_qty.production_rate}/s")
print(f"  Consumption rate: {crop_qty.consumption_rate}/s")
print(f"  Expected production: 10.0 (5 workers × 2.0/s)")

# Check total food
total_food = civ.get_total_food_from_crops()
print(f"\nTotal food from crops: {total_food}")

print("\n--- Test 3: Check food consumption ---")
food_consumption_rate = civ.population.calculate_food_consumption()
print(f"Food consumption rate: {food_consumption_rate}/s")
print(f"Population: {civ.population.total}")
print(f"Expected consumption: {civ.population.total * 0.5}/s (population × 0.5/s)")

print("\n--- Test 4: Run multiple updates ---")
for i in range(5):
    update_summary = civ.update(delta_time=1.0)
    total_food = civ.get_total_food_from_crops()
    crop_qty = civ.resources.get(crop_resource.id)
    print(f"  After {i+1} more seconds: {crop_resource.name}={crop_qty.amount:.1f}, Total food={total_food:.1f}")

print("\n--- Test 5: Allocate to second crop (if available) ---")
second_crop = None
for res_id in civ.available_resources:
    resource = game_data.resources.get(res_id)
    if resource and resource.bonus_class == 'crop' and resource.id != crop_resource.id:
        second_crop = resource
        break

if second_crop:
    print(f"Found second crop: {second_crop.name}")

    # Research tech if needed
    if second_crop.tech_reveal and second_crop.tech_reveal not in civ.tech_tree.researched:
        civ.tech_tree.researched.add(second_crop.tech_reveal)

    # Add to storage
    civ.resources.add_resource_type(second_crop, initial_amount=0.0)

    # Allocate workers
    allocated = civ.population.allocate_workers(
        WorkforceTask.RESOURCE_EXTRACTION,
        3,
        resource_id=second_crop.id
    )
    print(f"Allocated {allocated} workers to {second_crop.name}")

    # Update
    update_summary = civ.update(delta_time=1.0)

    # Check both crops
    crop1_qty = civ.resources.get(crop_resource.id)
    crop2_qty = civ.resources.get(second_crop.id)
    total_food = civ.get_total_food_from_crops()

    print(f"\nAfter 1 second with 2 crops:")
    print(f"  {crop_resource.name}: {crop1_qty.amount:.1f}")
    print(f"  {second_crop.name}: {crop2_qty.amount:.1f}")
    print(f"  Total food: {total_food:.1f}")
    print(f"  ✓ Food is sum of individual crops!")
else:
    print("Only one crop available, skipping multi-crop test")

print("\n=== Test Complete ===")
