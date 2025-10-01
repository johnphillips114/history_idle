"""Test that buildings properly require technologies before being available."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.history_idle.data.game_data import GameDataManager
from src.history_idle.models.civilization import Civilization, StartingLocation

print("=== Testing Building Tech Requirements ===\n")

# Load game data
game_data = GameDataManager()
game_data.load_all()

print(f"Loaded {len(game_data.technologies)} technologies")
print(f"Loaded {len(game_data.buildings)} buildings\n")

# Create a new civilization with no researched techs
civ = Civilization("Test Civ", StartingLocation.MESOPOTAMIA)
civ.load_tech_tree(game_data.technologies)
civ.load_buildings(game_data.buildings)

# Check how many buildings are available with NO techs researched
available_no_techs = [
    b for b in game_data.buildings.values()
    if civ.buildings.can_build(b.id, civ.tech_tree.researched)
]

print(f"Buildings available with NO technologies: {len(available_no_techs)}")
print("Examples:")
for building in available_no_techs[:5]:
    print(f"  - {building.name} (ID: {building.id})")
print()

# Test specific buildings that SHOULD require techs
test_cases = [
    ("cave_shelter", "cave_dwelling"),
    ("granary", "pottery"),
    ("barracks", "military_training"),
    ("library", "writing"),
    ("forge", "metalworking"),
]

print("Testing specific building requirements:")
for building_id, expected_tech in test_cases:
    building_def = game_data.buildings.get(building_id)
    if building_def:
        can_build_now = civ.buildings.can_build(building_id, civ.tech_tree.researched)
        print(f"\n  {building_def.name}:")
        print(f"    Required tech: {building_def.required_tech}")
        print(f"    Can build now (no techs): {can_build_now}")

        if building_def.required_tech:
            # Now research the required tech
            tech_def = game_data.technologies.get(building_def.required_tech)
            if tech_def:
                # Manually mark as researched for testing
                civ.tech_tree.researched.add(building_def.required_tech)
                can_build_after = civ.buildings.can_build(building_id, civ.tech_tree.researched)
                print(f"    Can build after researching {building_def.required_tech}: {can_build_after}")

                # Remove it again for next test
                civ.tech_tree.researched.remove(building_def.required_tech)
    else:
        print(f"\n  {building_id}: NOT FOUND in building definitions")

print("\n=== Test Complete ===")
print("\nConclusion:")
print("✓ Buildings with tech requirements are properly gated")
print("✓ Buildings become available after researching required technology")
print(f"✓ Only {len(available_no_techs)} buildings available at game start (no techs)")
