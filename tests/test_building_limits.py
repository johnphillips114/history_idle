"""Test that buildings can only be built once."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.history_idle.models.building import BuildingDefinition, BuildingCategory, BuildingManager, Building
from src.history_idle.models.resource import ResourceType, ResourceCategory

print("=== Testing Building Construction Limits ===\n")

# Create a building manager
manager = BuildingManager()

# Add a test building definition
test_building = BuildingDefinition(
    id="test_granary",
    name="Test Granary",
    description="Stores food",
    category=BuildingCategory.STORAGE,
    max_count=1  # Should only be buildable once
)

manager.add_building_definition(test_building)

print(f"Added building: {test_building.name}")
print(f"  Max count: {test_building.max_count}")
print(f"  Current count: {manager.get_building_count(test_building.id)}")

print("\n--- Test 1: Check if building can be built (first time) ---")
can_build_first = manager.can_build(test_building.id, set())
print(f"Can build (first time): {can_build_first}")
if can_build_first:
    print("  ✓ Building is available for first construction")
else:
    print("  ❌ Building should be available!")

print("\n--- Test 2: Build the building ---")
# Manually add a completed building
completed_building = Building(definition=test_building)
manager.buildings.append(completed_building)
print(f"Built {test_building.name}")
print(f"  Current count: {manager.get_building_count(test_building.id)}")

print("\n--- Test 3: Check if building can be built again ---")
can_build_second = manager.can_build(test_building.id, set())
print(f"Can build (second time): {can_build_second}")
if not can_build_second:
    print("  ✓ Building correctly blocked (already built)")
else:
    print("  ❌ Building should NOT be available (already built)!")

print("\n--- Test 4: Test building with max_count=-1 (unlimited) ---")
unlimited_building = BuildingDefinition(
    id="test_farm",
    name="Test Farm",
    description="Produces food",
    category=BuildingCategory.PRODUCTION,
    max_count=-1  # Unlimited
)
manager.add_building_definition(unlimited_building)

# Build one
manager.buildings.append(Building(definition=unlimited_building))
print(f"Built first {unlimited_building.name}")
print(f"  Current count: {manager.get_building_count(unlimited_building.id)}")

can_build_unlimited = manager.can_build(unlimited_building.id, set())
print(f"Can build another: {can_build_unlimited}")
if can_build_unlimited:
    print("  ✓ Unlimited building can be built multiple times")
else:
    print("  ❌ Unlimited building should be available!")

print("\n--- Test 5: Test building with max_count=3 ---")
limited_building = BuildingDefinition(
    id="test_house",
    name="Test House",
    description="Houses population",
    category=BuildingCategory.HOUSING,
    max_count=3  # Can build up to 3
)
manager.add_building_definition(limited_building)

for i in range(3):
    can_build = manager.can_build(limited_building.id, set())
    print(f"Can build house #{i+1}: {can_build}")
    if can_build:
        manager.buildings.append(Building(definition=limited_building))
        print(f"  Built house #{i+1}, current count: {manager.get_building_count(limited_building.id)}")

can_build_fourth = manager.can_build(limited_building.id, set())
print(f"Can build house #4: {can_build_fourth}")
if not can_build_fourth:
    print("  ✓ Correctly blocked after reaching max_count")
else:
    print("  ❌ Should be blocked after max_count reached!")

print("\n=== Test Complete ===")
