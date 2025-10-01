"""Test production accumulation for buildings."""

from src.history_idle.models import Civilization, StartingLocation
from src.history_idle.models.building import BuildingDefinition, BuildingCategory, ResourceCost
from src.history_idle.models.population import WorkforceTask


def test_production_accumulation():
    """Test that production accumulates correctly towards buildings."""
    print("\n=== Testing Production Accumulation ===\n")

    # Create a test civilization
    civ = Civilization(
        name="Test Civilization",
        starting_location=StartingLocation.MESOPOTAMIA
    )

    city = civ.get_active_city()
    if not city:
        print("✗ ERROR: No active city!")
        return False

    # Add a simple test building definition
    test_building = BuildingDefinition(
        id="test_building",
        name="Test Building",
        description="A test building",
        category=BuildingCategory.INFRASTRUCTURE,
        construction_costs=[ResourceCost(resource_id="production", amount=100.0)],
        construction_time=0.0,
        max_count=-1
    )
    city.buildings.add_building_definition(test_building)

    print("1. Setup:")
    print(f"   City: {city.name}")
    print(f"   Population: {city.population.total}")
    print(f"   Test building requires: 100 production")

    # Allocate 5 workers to construction
    city.population.allocate_workers(WorkforceTask.CONSTRUCTION, 5)
    construction_workers = city.population.get_workers_on_task(WorkforceTask.CONSTRUCTION)
    print(f"\n2. Allocated {construction_workers} workers to construction")

    # Start building construction
    print("\n3. Starting construction...")
    if city.buildings.start_construction("test_building"):
        print(f"   ✓ Construction started")
    else:
        print(f"   ✗ Failed to start construction!")
        return False

    # Check under_construction list
    print(f"\n4. Buildings under construction: {len(city.buildings.under_construction)}")
    if city.buildings.under_construction:
        for construction in city.buildings.under_construction:
            print(f"   - {construction.building_def.name}")
            print(f"     Required production: {construction.required_production}")
            print(f"     Current progress: {construction.progress}")
    else:
        print("   ✗ ERROR: No buildings in under_construction list!")
        return False

    # Simulate 10 seconds of production
    print("\n5. Simulating 10 seconds of game time...")
    for i in range(10):
        print(f"\n   Tick {i+1}:")
        update_result = city.update(1.0)  # 1 second per tick

        # Check production rate
        production_resource = city.resources.get("production")
        if production_resource:
            print(f"     Production rate: {production_resource.production_rate:.1f}/s")

        # Check building progress
        if city.buildings.under_construction:
            construction = city.buildings.under_construction[0]
            print(f"     Building progress: {construction.progress:.1f}/{construction.required_production:.1f} ({construction.progress_percentage*100:.1f}%)")
        else:
            print(f"     Building completed!")
            break

    # Final check
    print("\n6. Final state:")
    if city.buildings.under_construction:
        construction = city.buildings.under_construction[0]
        print(f"   Building still under construction")
        print(f"   Progress: {construction.progress:.1f}/{construction.required_production:.1f}")
        if construction.progress == 0:
            print("   ✗ ERROR: No progress made!")
            return False
        else:
            print(f"   ✓ Progress made: {construction.progress:.1f} production accumulated")
    else:
        print(f"   ✓ Building completed!")
        print(f"   Completed buildings: {len(city.buildings.buildings)}")

    print("\n=== Test Complete ===\n")
    return True


if __name__ == "__main__":
    success = test_production_accumulation()
    exit(0 if success else 1)
