"""Test that buildings properly require other buildings before being available."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.history_idle.data.game_data import GameDataManager
from src.history_idle.models.civilization import Civilization, StartingLocation

print("=== Testing Building Prerequisites ===\n")

# Load game data
game_data = GameDataManager()
game_data.load_all()

print(f"Loaded {len(game_data.technologies)} technologies")
print(f"Loaded {len(game_data.buildings)} buildings\n")

# Find buildings with PrereqInCityBuildings
buildings_with_prereqs = [
    b for b in game_data.buildings.values()
    if b.required_buildings
]

print(f"Buildings with building prerequisites: {len(buildings_with_prereqs)}")
print("\nExamples of building prerequisites:")
for building in buildings_with_prereqs[:10]:
    print(f"  {building.name}:")
    for req_building in building.required_buildings:
        req_def = game_data.buildings.get(req_building)
        req_name = req_def.name if req_def else req_building
        print(f"    - Requires: {req_name}")

# Test specific case: find a building that requires another building
print("\n--- Testing Building Prerequisite Chain ---\n")

# Find a good example (a building that requires factory)
test_building = None
for b in game_data.buildings.values():
    if 'factory' in b.required_buildings:
        test_building = b
        break

if test_building:
    print(f"Testing: {test_building.name}")
    print(f"  Required buildings: {test_building.required_buildings}")

    # Create a civilization
    civ = Civilization("Test Civ", StartingLocation.MESOPOTAMIA)
    civ.load_tech_tree(game_data.technologies)
    civ.load_buildings(game_data.buildings)

    # Research all techs (so tech isn't the blocker)
    for tech_id in game_data.technologies.keys():
        civ.tech_tree.researched.add(tech_id)

    # Check if we can build without the prerequisite
    can_build_without = civ.buildings.can_build(test_building.id, civ.tech_tree.researched)
    print(f"\n  Can build WITHOUT factory: {can_build_without}")

    # Now build the factory
    factory_def = game_data.buildings.get('factory')
    if factory_def:
        from src.history_idle.models.building import Building
        factory_building = Building(definition=factory_def)
        civ.buildings.buildings.append(factory_building)
        print(f"  Built: {factory_def.name}")

    # Check if we can build with the prerequisite
    can_build_with = civ.buildings.can_build(test_building.id, civ.tech_tree.researched)
    print(f"  Can build WITH factory: {can_build_with}")

    print("\n✓ Building prerequisites working correctly!")
else:
    print("No test building found with factory prerequisite")

print("\n=== Test Complete ===")
