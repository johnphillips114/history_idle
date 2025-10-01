"""Test building flavor system."""

from src.history_idle.models import Civilization, StartingLocation
from src.history_idle.data.game_data import GameDataManager


def test_building_flavors():
    """Test that building flavors properly affect abstract resources."""
    print("\n=== Testing Building Flavor System ===\n")

    # Load game data
    game_data = GameDataManager()
    game_data.load_all()

    print(f"1. Loaded {len(game_data.buildings)} buildings")

    # Find buildings with flavors
    buildings_with_flavors = []
    for building_id, building_def in game_data.buildings.items():
        if building_def.flavors:
            buildings_with_flavors.append((building_id, building_def))

    print(f"   Found {len(buildings_with_flavors)} buildings with flavors")

    if len(buildings_with_flavors) == 0:
        print("   ✗ ERROR: No buildings with flavors found!")
        return False

    # Show some examples
    print("\n2. Example buildings with flavors:")
    for building_id, building_def in buildings_with_flavors[:5]:
        print(f"   - {building_def.name}: {building_def.flavors}")

    # Create a test civilization
    print("\n3. Testing flavor effects...")
    civ = Civilization(
        name="Test Civilization",
        starting_location=StartingLocation.MESOPOTAMIA
    )

    # Research all techs to unlock buildings
    for tech_id in game_data.technologies.keys():
        civ.tech_tree.researched.add(tech_id)

    city = civ.get_active_city()
    if not city:
        print("   ✗ ERROR: No active city!")
        return False

    # Copy building definitions to city
    for building_id, building_def in game_data.buildings.items():
        city.buildings.add_building_definition(building_def)

    # Find a building with military flavor
    military_building = None
    for building_id, building_def in buildings_with_flavors:
        if 'military' in building_def.flavors:
            military_building = building_def
            break

    if not military_building:
        print("   ⚠ No building with military flavor found, trying other flavors...")
        # Just use the first building with any flavor
        military_building = buildings_with_flavors[0][1]

    print(f"\n4. Testing with building: {military_building.name}")
    print(f"   Flavors: {military_building.flavors}")

    # Check abstract resources before building
    print("\n5. Abstract resources before building:")
    for resource_id in ['military', 'currency', 'religion', 'espionage', 'culture', 'research']:
        resource = city.resources.get(resource_id)
        if resource:
            print(f"   - {resource.resource_type.name}: {resource.production_rate:.1f}/s")

    # Manually add the building (bypass construction)
    from src.history_idle.models.building import Building
    building = Building(definition=military_building, is_active=True)
    city.buildings.buildings.append(building)

    # Update city to recalculate flavor bonuses
    city.update(1.0)

    # Check abstract resources after building
    print("\n6. Abstract resources after building:")
    for resource_id in ['military', 'currency', 'religion', 'espionage', 'culture', 'research']:
        resource = city.resources.get(resource_id)
        if resource:
            print(f"   - {resource.resource_type.name}: {resource.production_rate:.1f}/s")

    # Verify the changes match the flavors
    print("\n7. Verifying flavor effects...")
    all_correct = True
    for flavor_type, flavor_value in military_building.flavors.items():
        # Map flavor type to resource ID
        flavor_to_resource = {
            'growth': 'food',
            'production': 'production',
            'science': 'research',
            'military': 'military',
            'gold': 'currency',
            'religion': 'religion',
            'espionage': 'espionage',
            'culture': 'culture'
        }

        resource_id = flavor_to_resource.get(flavor_type)
        if resource_id:
            resource = city.resources.get(resource_id)
            if resource:
                expected_rate = float(flavor_value)
                actual_rate = resource.production_rate
                if abs(actual_rate - expected_rate) < 0.01:
                    print(f"   ✓ {flavor_type} → {resource.resource_type.name}: {actual_rate:.1f}/s (expected {expected_rate:.1f}/s)")
                else:
                    print(f"   ✗ {flavor_type} → {resource.resource_type.name}: {actual_rate:.1f}/s (expected {expected_rate:.1f}/s)")
                    all_correct = False

    if not all_correct:
        print("\n✗ Some flavor effects don't match!")
        return False

    # Test multiple buildings stacking
    print("\n8. Testing multiple buildings stacking...")
    building2 = Building(definition=military_building, is_active=True)
    city.buildings.buildings.append(building2)
    city.update(1.0)

    print("   Abstract resources with 2 buildings:")
    for flavor_type, flavor_value in military_building.flavors.items():
        flavor_to_resource = {
            'growth': 'food',
            'production': 'production',
            'science': 'research',
            'military': 'military',
            'gold': 'currency',
            'religion': 'religion',
            'espionage': 'espionage',
            'culture': 'culture'
        }

        resource_id = flavor_to_resource.get(flavor_type)
        if resource_id:
            resource = city.resources.get(resource_id)
            if resource:
                expected_rate = float(flavor_value * 2)
                actual_rate = resource.production_rate
                if abs(actual_rate - expected_rate) < 0.01:
                    print(f"   ✓ {resource.resource_type.name}: {actual_rate:.1f}/s (expected {expected_rate:.1f}/s)")
                else:
                    print(f"   ✗ {resource.resource_type.name}: {actual_rate:.1f}/s (expected {expected_rate:.1f}/s)")
                    all_correct = False

    if not all_correct:
        print("\n✗ Stacking doesn't work correctly!")
        return False

    print("\n=== All Building Flavor Tests Passed! ===\n")
    return True


if __name__ == "__main__":
    success = test_building_flavors()
    exit(0 if success else 1)
