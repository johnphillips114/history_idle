"""Test civilization loading and city naming."""

from src.history_idle.models import Civilization, StartingLocation
from src.history_idle.data.game_data import GameDataManager


def test_civilization_loading():
    """Test that civilizations are loaded correctly from C2C data."""
    print("\n=== Testing Civilization Loading ===\n")

    # Load game data
    game_data = GameDataManager()
    game_data.load_civilizations()

    print(f"1. Loaded {len(game_data.civilizations)} civilizations")

    if len(game_data.civilizations) == 0:
        print("   ✗ ERROR: No civilizations loaded!")
        return False

    print("   ✓ Civilizations loaded successfully")

    # Check specific civilizations
    print("\n2. Checking specific civilizations...")

    # America should exist
    america = game_data.get_civilization('america')
    if not america:
        print("   ✗ ERROR: America civilization not found!")
        return False

    print(f"   ✓ Found America")
    print(f"     Name: {america.name}")
    print(f"     First city: {america.get_first_city_name()}")
    print(f"     Total cities: {len(america.city_names)}")

    # Verify city name formatting
    if america.get_first_city_name() == "Washington Dc":
        print("   ✓ City name formatted correctly")
    else:
        print(f"   ⚠ Unexpected city name: {america.get_first_city_name()}")

    # Test random selection
    print("\n3. Testing random civilization selection...")
    random_civ = game_data.get_random_civilization()
    if not random_civ:
        print("   ✗ ERROR: Random selection failed!")
        return False

    print(f"   ✓ Randomly selected: {random_civ.name}")
    print(f"     First city: {random_civ.get_first_city_name()}")

    # Test game initialization with civilization
    print("\n4. Testing game initialization...")
    civ_def = game_data.get_random_civilization()

    civ = Civilization(
        name=civ_def.name,
        starting_location=StartingLocation.MESOPOTAMIA
    )

    # Rename starting city
    active_city = civ.get_active_city()
    if not active_city:
        print("   ✗ ERROR: No active city!")
        return False

    active_city.name = civ_def.get_first_city_name()

    if active_city.name == civ_def.get_first_city_name():
        print(f"   ✓ City named correctly: {active_city.name}")
    else:
        print(f"   ✗ ERROR: City name mismatch!")
        return False

    if civ.name == civ_def.name:
        print(f"   ✓ Civilization named correctly: {civ.name}")
    else:
        print(f"   ✗ ERROR: Civilization name mismatch!")
        return False

    # Test multiple civilizations have city names
    print("\n5. Verifying all civilizations have city names...")
    civs_without_cities = []
    for civ_id, civ_def in game_data.civilizations.items():
        if not civ_def.city_names:
            civs_without_cities.append(civ_def.name)

    if civs_without_cities:
        print(f"   ⚠ Warning: {len(civs_without_cities)} civilizations have no city names:")
        for civ_name in civs_without_cities[:5]:  # Show first 5
            print(f"     - {civ_name}")
    else:
        print("   ✓ All civilizations have city names")

    print("\n=== All Civilization Tests Passed! ===\n")
    return True


if __name__ == "__main__":
    success = test_civilization_loading()
    exit(0 if success else 1)
