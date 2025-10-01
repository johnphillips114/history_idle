"""Test that both workers and building flavors contribute to production."""

from src.history_idle.models import Civilization, StartingLocation
from src.history_idle.models.building import BuildingDefinition, Building, BuildingCategory, ResourceCost
from src.history_idle.models.population import WorkforceTask


def test_production_with_flavors():
    """Test that workers and building flavors both contribute to production."""
    print("\n=== Testing Production with Building Flavors ===\n")

    # Create a test civilization
    civ = Civilization(
        name="Test Civilization",
        starting_location=StartingLocation.MESOPOTAMIA
    )

    city = civ.get_active_city()
    if not city:
        print("✗ ERROR: No active city!")
        return False

    # Add a test building with production flavor
    production_building = BuildingDefinition(
        id="production_boost",
        name="Production Boost Building",
        description="Provides +10 production",
        category=BuildingCategory.INFRASTRUCTURE,
        construction_costs=[],
        max_count=-1,
        flavors={'production': 10}  # +10 production per second
    )
    city.buildings.add_building_definition(production_building)

    # Add a test building to construct
    test_building = BuildingDefinition(
        id="test_building",
        name="Test Building",
        description="A test building",
        category=BuildingCategory.INFRASTRUCTURE,
        construction_costs=[ResourceCost(resource_id="production", amount=100.0)],
        max_count=-1
    )
    city.buildings.add_building_definition(test_building)

    print("1. Initial state:")
    print(f"   Population: {city.population.total}")

    # Test 1: Workers only
    print("\n2. Test with 5 workers only:")
    city.population.allocate_workers(WorkforceTask.CONSTRUCTION, 5)

    # Update to set production rate
    city.update(0.1)

    production_resource = city.resources.get("production")
    if production_resource:
        print(f"   Production rate: {production_resource.production_rate:.1f}/s")
        if abs(production_resource.production_rate - 5.0) < 0.01:
            print("   ✓ Correct: 5 workers = 5.0/s")
        else:
            print(f"   ✗ ERROR: Expected 5.0/s, got {production_resource.production_rate:.1f}/s")
            return False

    # Deallocate workers
    city.population.deallocate_workers(WorkforceTask.CONSTRUCTION, 5)

    # Test 2: Building flavor only
    print("\n3. Test with building flavor only:")
    building_instance = Building(definition=production_building, is_active=True)
    city.buildings.buildings.append(building_instance)

    # Update to recalculate production
    city.update(0.1)

    production_resource = city.resources.get("production")
    if production_resource:
        print(f"   Production rate: {production_resource.production_rate:.1f}/s")
        if abs(production_resource.production_rate - 10.0) < 0.01:
            print("   ✓ Correct: Building with 10 production flavor = 10.0/s")
        else:
            print(f"   ✗ ERROR: Expected 10.0/s, got {production_resource.production_rate:.1f}/s")
            return False

    # Test 3: Workers + Building flavor combined
    print("\n4. Test with 5 workers + building flavor:")
    city.population.allocate_workers(WorkforceTask.CONSTRUCTION, 5)

    # Update to recalculate production
    city.update(0.1)

    production_resource = city.resources.get("production")
    if production_resource:
        print(f"   Production rate: {production_resource.production_rate:.1f}/s")
        expected = 15.0  # 5 from workers + 10 from building
        if abs(production_resource.production_rate - expected) < 0.01:
            print(f"   ✓ Correct: 5 workers + 10 flavor = {expected:.1f}/s")
        else:
            print(f"   ✗ ERROR: Expected {expected:.1f}/s, got {production_resource.production_rate:.1f}/s")
            return False

    # Test 4: Building construction with combined production
    print("\n5. Test building construction with combined production:")
    city.buildings.start_construction("test_building")

    print(f"   Building requires: 100 production")
    print(f"   Production rate: {production_resource.production_rate:.1f}/s")

    # Simulate 10 seconds
    for i in range(10):
        city.update(1.0)

    # Check progress
    if city.buildings.under_construction:
        construction = city.buildings.under_construction[0]
        print(f"   Progress after 10s: {construction.progress:.1f}/100.0")
        expected_progress = 150.0  # 15/s * 10s
        # Progress should be 100 (complete) since we produce 15/s * 10s = 150
        if construction.is_complete or abs(construction.progress - 100.0) < 0.01:
            print("   ✓ Building completed!")
        else:
            print(f"   Progress: {construction.progress:.1f} (expected completion at 100)")
    else:
        print("   ✓ Building completed and added to city!")

    # Verify completed building is in the buildings list
    completed_count = sum(1 for b in city.buildings.buildings if b.definition.id == "test_building")
    if completed_count > 0:
        print(f"   ✓ Test building found in completed buildings")
    else:
        print(f"   ✗ ERROR: Test building not found in completed buildings!")
        return False

    print("\n=== All Tests Passed! ===\n")
    return True


if __name__ == "__main__":
    success = test_production_with_flavors()
    exit(0 if success else 1)
