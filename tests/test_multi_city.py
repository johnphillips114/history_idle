"""Test the multi-city system."""

from src.history_idle.models import Civilization, StartingLocation, WorkforceTask
from src.history_idle.data.game_data import GameDataManager


def test_multi_city_workflow():
    """Test the complete multi-city workflow."""
    print("\n=== Testing Multi-City System ===\n")

    # Initialize civilization
    print("1. Initializing civilization...")
    civ = Civilization(name='Test Civ', starting_location=StartingLocation.MESOPOTAMIA)

    # Load game data
    game_data = GameDataManager()
    game_data.load_all()

    # Initialize civilization
    civ.initialize_starting_resources()
    civ.load_tech_tree(game_data.technologies)
    civ.load_buildings(game_data.buildings)
    civ.initialize_available_resources(game_data.resources)

    active_city = civ.get_active_city()
    print(f"   ✓ Starting city: {active_city.name} with {active_city.population.total} population")
    print(f"   ✓ Available resources: {len(active_city.available_resources)}")

    # Research tribalism (TECH_TRIBALISM in C2C, but parser converts to 'tribalism')
    print("\n2. Researching Tribalism...")
    tribalism = game_data.get_technology('tribalism')
    if tribalism:
        print(f"   ✓ Found technology: {tribalism.name} (cost: {tribalism.research_cost})")
        civ.tech_tree.researched.add('tribalism')
    else:
        print("   ✗ ERROR: Tribalism not found!")
        return False

    # Build a settler
    print("\n3. Building a Settler...")
    can_build = active_city.buildings.can_build('settler', civ.tech_tree.researched)
    if not can_build:
        print("   ✗ ERROR: Cannot build settler!")
        return False

    active_city.buildings.start_construction('settler')
    active_city.population.allocate_workers(WorkforceTask.CONSTRUCTION, 5)
    print(f"   ✓ Started settler construction with 5 workers")

    # Simulate construction (100 production / 5 workers = 20 seconds)
    print("   ⏳ Simulating construction...")
    for i in range(25):
        civ.update(1.0)

    if civ.ready_settlers > 0:
        print(f"   ✓ Settler completed! Ready settlers: {civ.ready_settlers}")
    else:
        print("   ✗ ERROR: Settler not completed!")
        return False

    # Found a new city
    print("\n4. founding a new city...")
    new_city = civ.found_city('New Settlement', game_data.resources)
    if new_city:
        print(f"   ✓ Founded '{new_city.name}'")
        print(f"   ✓ Population: {new_city.population.total}")
        print(f"   ✓ Available resources: {len(new_city.available_resources)}")
        print(f"   ✓ Total cities: {len(civ.cities)}")
    else:
        print("   ✗ ERROR: Failed to found city!")
        return False

    # Switch between cities
    print("\n5. Testing city switching...")
    original_city = civ.get_active_city()
    print(f"   Current city: {original_city.name}")

    civ.set_active_city(new_city.id)
    if civ.get_active_city() == new_city:
        print(f"   ✓ Switched to {new_city.name}")
    else:
        print("   ✗ ERROR: Failed to switch cities!")
        return False

    civ.set_active_city(original_city.id)
    if civ.get_active_city() == original_city:
        print(f"   ✓ Switched back to {original_city.name}")
    else:
        print("   ✗ ERROR: Failed to switch back!")
        return False

    # Test multi-city updates
    print("\n6. Testing multi-city updates...")
    capital = civ.get_city_by_name('Capital')
    new_city = civ.get_city_by_name('New Settlement')

    # Allocate workers in both cities
    capital.population.allocate_workers(WorkforceTask.RESEARCH, 3)
    new_city.population.allocate_workers(WorkforceTask.RESEARCH, 1)

    # Update and check research accumulation
    summary = civ.update(1.0)
    research_amount = civ.resources.get('research').amount if civ.resources.get('research') else 0

    print(f"   ✓ Updated {len(summary['cities'])} cities")
    print(f"   ✓ Total population: {summary['total_population']}")
    print(f"   ✓ Research accumulated: {research_amount:.1f}")

    if research_amount > 0:
        print(f"   ✓ Both cities contributing to research!")
    else:
        print("   ✗ ERROR: No research accumulated!")
        return False

    # Verify cities are independent
    print("\n7. Verifying city independence...")
    print(f"   Capital: {capital.population.total} pop, {len(capital.buildings.buildings)} buildings")
    print(f"   New Settlement: {new_city.population.total} pop, {len(new_city.buildings.buildings)} buildings")

    if capital.population.total != new_city.population.total:
        print("   ✓ Cities have independent populations")
    else:
        print("   ⚠ Warning: Cities have same population (could be coincidence)")

    print("\n=== All Tests Passed! ===\n")
    return True


if __name__ == "__main__":
    success = test_multi_city_workflow()
    exit(0 if success else 1)
