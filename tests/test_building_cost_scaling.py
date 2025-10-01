"""Test exponential cost scaling for buildings."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.history_idle.models.building import BuildingDefinition, BuildingCategory, BuildingManager, Building, ResourceCost

print("=== Testing Building Cost Scaling ===\n")

# Create a building manager
manager = BuildingManager()

# Add a test building that can be built multiple times
cave_shelter = BuildingDefinition(
    id="cave_shelter",
    name="Cave Shelter",
    description="Basic housing",
    category=BuildingCategory.HOUSING,
    construction_costs=[ResourceCost("production", 20.0)],
    max_count=-1  # Unlimited
)

manager.add_building_definition(cave_shelter)

print(f"Building: {cave_shelter.name}")
print(f"Base cost: {cave_shelter.construction_costs[0].amount} production")
print(f"Max count: {cave_shelter.max_count} (unlimited)")

print("\n--- Testing Cost Scaling ---\n")

# Track costs for first 5 builds
expected_multipliers = [1.0, 1.2, 1.44, 1.728, 2.0736]
expected_costs = [20.0, 24.0, 28.8, 34.56, 41.472]

for i in range(5):
    current_count = manager.get_building_count(cave_shelter.id)
    multiplier = manager.get_cost_multiplier(cave_shelter.id)
    adjusted_costs = manager.get_adjusted_costs(cave_shelter.id)
    adjusted_amount = adjusted_costs[0].amount if adjusted_costs else 0.0

    print(f"Building #{i+1}:")
    print(f"  Buildings already built: {current_count}")
    print(f"  Cost multiplier: {multiplier:.4f} (expected: {expected_multipliers[i]:.4f})")
    print(f"  Adjusted cost: {adjusted_amount:.2f} production (expected: {expected_costs[i]:.2f})")

    # Check if multiplier is correct
    if abs(multiplier - expected_multipliers[i]) < 0.0001:
        print(f"  ✓ Multiplier correct!")
    else:
        print(f"  ❌ Multiplier incorrect!")

    # Check if cost is correct
    if abs(adjusted_amount - expected_costs[i]) < 0.01:
        print(f"  ✓ Cost correct!")
    else:
        print(f"  ❌ Cost incorrect!")

    # "Build" the building
    manager.buildings.append(Building(definition=cave_shelter))
    print()

print("--- Summary ---")
print("\nCost progression:")
print("  1st: 20.0  (1.0x)")
print("  2nd: 24.0  (1.2x)")
print("  3rd: 28.8  (1.44x)")
print("  4th: 34.56 (1.728x)")
print("  5th: 41.47 (2.074x)")
print("\nFormula: base_cost × (1.2^buildings_already_built)")

print("\n--- Testing with Different Base Cost ---")

expensive_building = BuildingDefinition(
    id="laboratory",
    name="Laboratory",
    description="Research facility",
    category=BuildingCategory.RESEARCH,
    construction_costs=[ResourceCost("production", 100.0)],
    max_count=-1
)

manager.add_building_definition(expensive_building)

print(f"\nBuilding: {expensive_building.name}")
print(f"Base cost: 100 production")

# Build first one
manager.buildings.append(Building(definition=expensive_building))

# Check cost for second one
multiplier = manager.get_cost_multiplier(expensive_building.id)
adjusted_costs = manager.get_adjusted_costs(expensive_building.id)
adjusted_amount = adjusted_costs[0].amount

print(f"\nFor 2nd {expensive_building.name}:")
print(f"  Multiplier: {multiplier:.2f}x")
print(f"  Cost: {adjusted_amount:.1f} production")
print(f"  Expected: 120.0 production")

if abs(adjusted_amount - 120.0) < 0.1:
    print("  ✓ Cost scaling works for different base costs!")
else:
    print("  ❌ Cost scaling broken!")

print("\n=== Test Complete ===")
