"""Test the save/load system with multiple cities."""

from src.history_idle.models import Civilization, StartingLocation, WorkforceTask
from src.history_idle.data.game_data import GameDataManager
from src.history_idle.utils.save_system import SaveSystem
from pathlib import Path
import tempfile


def test_save_and_load_multicity():
    """Test saving and loading a multi-city civilization."""
    print("\n=== Testing Multi-City Save/Load ===\n")

    # Create a temporary save directory
    with tempfile.TemporaryDirectory() as tmpdir:
        save_system = SaveSystem(save_directory=Path(tmpdir))

        # Initialize civilization
        print("1. Creating test civilization...")
        civ = Civilization(name='Test Civ', starting_location=StartingLocation.MESOPOTAMIA)

        # Load game data
        game_data = GameDataManager()
        game_data.load_all()

        # Initialize civilization
        civ.initialize_starting_resources()
        civ.load_tech_tree(game_data.technologies)
        civ.load_buildings(game_data.buildings)
        civ.initialize_available_resources(game_data.resources)

        # Add a second city
        print("2. Founding a second city...")
        civ.ready_settlers = 1
        second_city = civ.found_city('Second City', game_data.resources)

        # Allocate workers in both cities
        capital = civ.get_city_by_name('Capital')
        capital.population.allocate_workers(WorkforceTask.RESEARCH, 3)
        second_city.population.allocate_workers(WorkforceTask.RESEARCH, 1)

        # Research a tech
        civ.tech_tree.researched.add('tribalism')

        # Update to generate some state
        civ.update(1.0)

        print(f"   Before save:")
        print(f"   - Cities: {len(civ.cities)}")
        print(f"   - Capital population: {capital.population.total}")
        print(f"   - Second city population: {second_city.population.total}")
        print(f"   - Active city: {civ.get_active_city().name}")
        print(f"   - Settlers ready: {civ.ready_settlers}")
        print(f"   - Techs researched: {len(civ.tech_tree.researched)}")

        # Save the game
        print("\n3. Saving game...")
        if save_system.save_game(civ, 'test_multicity'):
            print("   ✓ Save successful")
        else:
            print("   ✗ Save failed!")
            return False

        # Load the game
        print("\n4. Loading game...")
        loaded_civ = save_system.load_game('test_multicity')

        if not loaded_civ:
            print("   ✗ Load failed!")
            return False

        print("   ✓ Load successful")

        # Restore building definitions
        loaded_civ.load_tech_tree(game_data.technologies)
        loaded_civ.load_buildings(game_data.buildings)
        save_system.restore_from_save_data(loaded_civ)

        # Verify the loaded civilization
        print("\n5. Verifying loaded data...")
        print(f"   After load:")
        print(f"   - Cities: {len(loaded_civ.cities)}")

        loaded_capital = loaded_civ.get_city_by_name('Capital')
        loaded_second = loaded_civ.get_city_by_name('Second City')

        if not loaded_capital:
            print("   ✗ Capital city not found!")
            return False

        if not loaded_second:
            print("   ✗ Second city not found!")
            return False

        print(f"   - Capital population: {loaded_capital.population.total}")
        print(f"   - Second city population: {loaded_second.population.total}")
        print(f"   - Active city: {loaded_civ.get_active_city().name}")
        print(f"   - Settlers ready: {loaded_civ.ready_settlers}")
        print(f"   - Techs researched: {len(loaded_civ.tech_tree.researched)}")

        # Verify values match
        errors = []

        if len(loaded_civ.cities) != 2:
            errors.append(f"City count mismatch: expected 2, got {len(loaded_civ.cities)}")

        if loaded_capital.population.total != capital.population.total:
            errors.append(f"Capital population mismatch")

        if loaded_second.population.total != second_city.population.total:
            errors.append(f"Second city population mismatch")

        if loaded_civ.ready_settlers != civ.ready_settlers:
            errors.append(f"Settlers ready mismatch")

        if loaded_civ.get_active_city().name != civ.get_active_city().name:
            errors.append(f"Active city mismatch")

        if len(loaded_civ.tech_tree.researched) != len(civ.tech_tree.researched):
            errors.append(f"Tech count mismatch")

        # Check worker allocations
        capital_research_workers = loaded_capital.population.get_workers_on_task(WorkforceTask.RESEARCH)
        second_research_workers = loaded_second.population.get_workers_on_task(WorkforceTask.RESEARCH)

        if capital_research_workers != 3:
            errors.append(f"Capital research workers mismatch: expected 3, got {capital_research_workers}")

        if second_research_workers != 1:
            errors.append(f"Second city research workers mismatch: expected 1, got {second_research_workers}")

        if errors:
            print("\n   ✗ Verification failed:")
            for error in errors:
                print(f"     - {error}")
            return False

        print("   ✓ All data verified correctly!")

        # Test that loaded civ can be updated
        print("\n6. Testing loaded civilization updates...")
        summary = loaded_civ.update(1.0)
        print(f"   ✓ Updated {len(summary['cities'])} cities")
        print(f"   ✓ Total population: {summary['total_population']}")

        print("\n=== All Save/Load Tests Passed! ===\n")
        return True


if __name__ == "__main__":
    success = test_save_and_load_multicity()
    exit(0 if success else 1)
