"""Test saving and loading buildings."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.history_idle.models.civilization import Civilization, StartingLocation
from src.history_idle.models.building import BuildingDefinition, BuildingCategory, ResourceCost
from src.history_idle.utils.save_system import SaveSystem
import tempfile
import shutil

print("=== Testing Building Save/Load ===\n")

# Create temporary directory for saves
temp_dir = tempfile.mkdtemp()
print(f"Using temp directory: {temp_dir}")

# Create save system with temp directory
save_system = SaveSystem(save_directory=temp_dir)

# Create a civilization
civ = Civilization("Test Civ", StartingLocation.MESOPOTAMIA)
civ.initialize_starting_resources()

print("--- Creating buildings ---")

# Add building definition
test_building = BuildingDefinition(
    id="test_granary",
    name="Test Granary",
    description="Stores food",
    category=BuildingCategory.STORAGE,
    construction_costs=[ResourceCost("production", 50.0)],
    max_count=-1  # Unlimited
)

civ.buildings.add_building_definition(test_building)
print(f"Added building definition: {test_building.name}")

# Build one building (completed)
civ.buildings.start_construction(test_building.id)
construction = civ.buildings.under_construction[0]
construction.add_progress(50.0)  # Complete it
completed = civ.buildings.update_construction(0)
print(f"Built {len(completed)} building(s)")

# Start another building (in progress)
civ.buildings.start_construction(test_building.id)
construction = civ.buildings.under_construction[0]
construction.add_progress(25.0)  # 50% complete
print(f"Started construction: {construction.progress}/{construction.required_production} ({construction.progress_percentage*100:.0f}%)")

print(f"\nBefore save:")
print(f"  Completed buildings: {len(civ.buildings.buildings)}")
print(f"  Under construction: {len(civ.buildings.under_construction)}")
if civ.buildings.under_construction:
    c = civ.buildings.under_construction[0]
    print(f"    Progress: {c.progress}/{c.required_production}")

# Save the game
print("\n--- Saving game ---")
save_system.save_game(civ, "test_save")
print("Game saved")

# Load the game
print("\n--- Loading game ---")
loaded_civ = save_system.load_game("test_save")

if loaded_civ:
    print("Game loaded successfully")

    # Reload building definitions (simulating what main.py does)
    loaded_civ.load_buildings({test_building.id: test_building})

    # Restore buildings from save data
    save_system.restore_from_save_data(loaded_civ)

    print(f"\nAfter load:")
    print(f"  Completed buildings: {len(loaded_civ.buildings.buildings)}")
    print(f"  Under construction: {len(loaded_civ.buildings.under_construction)}")

    if loaded_civ.buildings.under_construction:
        c = loaded_civ.buildings.under_construction[0]
        print(f"    Progress: {c.progress}/{c.required_production}")

    # Verify
    print("\n--- Verification ---")

    if len(loaded_civ.buildings.buildings) == 1:
        print("✓ Completed buildings restored correctly")
    else:
        print(f"❌ Expected 1 completed building, got {len(loaded_civ.buildings.buildings)}")

    if len(loaded_civ.buildings.under_construction) == 1:
        print("✓ Under construction buildings restored correctly")
        c = loaded_civ.buildings.under_construction[0]
        if c.progress == 25.0 and c.required_production == 60.0:  # 60 because it's the 2nd building (1.2x multiplier)
            print("✓ Construction progress restored correctly")
        else:
            print(f"❌ Expected progress 25.0/60.0, got {c.progress}/{c.required_production}")
    else:
        print(f"❌ Expected 1 under construction, got {len(loaded_civ.buildings.under_construction)}")

    # Try to build the same building again
    print("\n--- Testing uniqueness ---")
    if loaded_civ.buildings.can_build(test_building.id, set()):
        print("Building can be built (max_count=-1, so this is OK)")

        # Now test with a unique building
        unique_building = BuildingDefinition(
            id="unique_temple",
            name="Unique Temple",
            description="One per civ",
            category=BuildingCategory.CULTURAL,
            construction_costs=[ResourceCost("production", 100.0)],
            max_count=1  # Unique
        )
        loaded_civ.buildings.add_building_definition(unique_building)

        # Build it
        loaded_civ.buildings.start_construction(unique_building.id)
        # Get the unique temple construction (it's the last one added)
        construction = loaded_civ.buildings.under_construction[-1]
        construction.add_progress(construction.required_production)  # Complete it
        completed = loaded_civ.buildings.update_construction(0)
        print(f"Built unique building: {unique_building.name} ({len(completed)} completed)")

        # Save again
        save_system.save_game(loaded_civ, "test_save2")

        # Load again
        loaded_civ2 = save_system.load_game("test_save2")
        loaded_civ2.load_buildings({
            test_building.id: test_building,
            unique_building.id: unique_building
        })
        save_system.restore_from_save_data(loaded_civ2)

        # Try to build unique building again
        can_build = loaded_civ2.buildings.can_build(unique_building.id, set())
        if not can_build:
            print("✓ Unique building cannot be built again after load!")
        else:
            print("❌ Unique building should not be buildable again")

else:
    print("❌ Failed to load game")

# Cleanup
print("\n--- Cleanup ---")
shutil.rmtree(temp_dir)
print("Temp directory removed")

print("\n=== Test Complete ===")
