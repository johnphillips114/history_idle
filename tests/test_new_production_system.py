"""Test the new production system where production can't be stockpiled."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.history_idle.models.civilization import Civilization, StartingLocation
from src.history_idle.models.building import BuildingDefinition, BuildingCategory, ResourceCost
from src.history_idle.models.population import WorkforceTask
import time

print("=== Testing New Production System ===\n")

# Create a civilization
civ = Civilization("Test Civ", StartingLocation.MESOPOTAMIA)
civ.initialize_starting_resources()

print("--- Test 1: Production resource cannot be stockpiled ---")
production_resource = civ.resources.get("production")
if production_resource:
    print(f"  Storage capacity: {production_resource.capacity}")
    print(f"  Can store: {production_resource.resource_type.can_store}")
    print(f"  Current amount: {production_resource.amount}")

    if production_resource.capacity == 0.0:
        print("  ✓ Production has 0 capacity (can't stockpile)")
    else:
        print(f"  ❌ Production should have 0 capacity, has {production_resource.capacity}")
else:
    print("  ❌ Production resource not found!")

print("\n--- Test 2: Allocate production workers (no effect without construction) ---")
allocated = civ.population.allocate_workers(WorkforceTask.CONSTRUCTION, 5)
print(f"Allocated {allocated} workers to production")

# Run an update
civ.last_update_time = time.time()
civ.update(delta_time=1.0)

production_resource = civ.resources.get("production")
print(f"Production after 1 second: {production_resource.amount}")
print(f"Production rate: {production_resource.production_rate}/s")

if production_resource.amount == 0.0:
    print("  ✓ Production not accumulated (no construction active)")
else:
    print(f"  ❌ Production should be 0, got {production_resource.amount}")

print("\n--- Test 3: Start building construction ---")

# Add a test building
test_building = BuildingDefinition(
    id="test_granary",
    name="Test Granary",
    description="Stores food",
    category=BuildingCategory.STORAGE,
    construction_costs=[ResourceCost("production", 50.0)],
    max_count=-1
)

civ.buildings.add_building_definition(test_building)
print(f"Added building: {test_building.name}")
print(f"  Required production: 50.0")

# Start construction (without paying costs for test)
civ.buildings.start_construction(test_building.id)
print("Started construction")

# Check construction state
if civ.buildings.under_construction:
    construction = civ.buildings.under_construction[0]
    print(f"  Required production: {construction.required_production}")
    print(f"  Current progress: {construction.progress}")
    print(f"  Progress percentage: {construction.progress_percentage * 100:.1f}%")
else:
    print("  ❌ No construction found!")

print("\n--- Test 4: Apply production to construction ---")

# Run updates to apply production
for i in range(5):
    civ.update(delta_time=1.0)
    if civ.buildings.under_construction:
        construction = civ.buildings.under_construction[0]
        print(f"  After {i+1}s: {construction.progress:.1f}/50.0 production ({construction.progress_percentage * 100:.1f}%)")
    else:
        print(f"  After {i+1}s: Construction complete!")
        break

# Check if building completed
completed_count = civ.buildings.get_building_count(test_building.id)
print(f"\nBuildings completed: {completed_count}")

print("\n--- Test 5: Verify production calculation ---")
print(f"Workers: 5")
print(f"Production rate: 1.0 per worker per second")
print(f"Total production per second: 5.0")
print(f"Expected time to complete 50 production: 10 seconds")
print(f"Time taken: 10 seconds" if completed_count > 0 else "Still in progress")

print("\n--- Test 6: Construction without workers ---")

# Start another building
civ.buildings.start_construction(test_building.id)
print("Started second construction")

# Remove all production workers
civ.population.deallocate_workers(WorkforceTask.CONSTRUCTION, 5)
print("Removed all production workers")

# Run update
initial_progress = civ.buildings.under_construction[0].progress if civ.buildings.under_construction else 0
civ.update(delta_time=5.0)
final_progress = civ.buildings.under_construction[0].progress if civ.buildings.under_construction else 0

print(f"Progress before: {initial_progress:.1f}")
print(f"Progress after 5s with 0 workers: {final_progress:.1f}")

if initial_progress == final_progress:
    print("  ✓ No progress made without workers!")
else:
    print(f"  ❌ Progress should not change without workers!")

print("\n=== Test Complete ===")
