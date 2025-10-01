"""Test that buildings requiring religion are excluded."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.history_idle.data.game_data import GameDataManager

print("=== Testing Religion Exclusion ===\n")

# Load game data
game_data = GameDataManager()
game_data.load_all()

print(f"Loaded {len(game_data.buildings)} buildings\n")

# Check for specific religious buildings that should be excluded
religious_building_ids = [
    'andean_cathedral',
    'andean_monastery',
    'andean_temple',
]

print("Checking that religious buildings are excluded:")
excluded_count = 0
for building_id in religious_building_ids:
    if building_id in game_data.buildings:
        print(f"  ❌ {building_id} - FOUND (should be excluded!)")
    else:
        print(f"  ✓ {building_id} - excluded")
        excluded_count += 1

# Search for any remaining buildings with "religion" or "temple" in the name
religious_keywords = ['temple', 'cathedral', 'monastery', 'shrine', 'church', 'mosque', 'synagogue']
found_religious = []

for building in game_data.buildings.values():
    lower_name = building.name.lower()
    lower_id = building.id.lower()
    for keyword in religious_keywords:
        if keyword in lower_name or keyword in lower_id:
            found_religious.append(building)
            break

print(f"\nBuildings with religious keywords in name/id: {len(found_religious)}")
if found_religious:
    print("Examples:")
    for b in found_religious[:10]:
        print(f"  - {b.name} (ID: {b.id})")

print("\n=== Test Complete ===")
print(f"\nBuildings loaded: {len(game_data.buildings)}")
print("Note: Religious buildings with PrereqReligion should be excluded")
