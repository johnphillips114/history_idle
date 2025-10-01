"""Test the resource availability system."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.history_idle.data.game_data import GameDataManager
from src.history_idle.models.civilization import Civilization, StartingLocation

print("=== Testing Resource Availability System ===\n")

# Load game data
game_data = GameDataManager()
game_data.load_all()

print(f"Total resources in C2C: {len(game_data.resources)}\n")

# Check bonus class distribution
bonus_classes = {}
for resource in game_data.resources.values():
    bc = resource.bonus_class or 'none'
    bonus_classes[bc] = bonus_classes.get(bc, 0) + 1

print("Bonus class distribution:")
for bc, count in sorted(bonus_classes.items()):
    print(f"  {bc}: {count}")

# Check crop resources with scavenging/gathering tech
crop_early_tech = [
    r for r in game_data.resources.values()
    if r.bonus_class == 'crop'
    and (r.tech_reveal == 'scavenging' or r.tech_reveal == 'gathering')
]

print(f"\nCrop resources with scavenging/gathering tech: {len(crop_early_tech)}")
for resource in crop_early_tech:
    print(f"  - {resource.name} (tech: {resource.tech_reveal})")

# Test multiple game initializations
print("\n--- Testing Starting Resource Selection (5 trials) ---\n")

for i in range(5):
    civ = Civilization(f"Test Civ {i+1}", StartingLocation.MESOPOTAMIA)
    civ.initialize_starting_resources()
    civ.load_tech_tree(game_data.technologies)
    civ.load_buildings(game_data.buildings)
    civ.initialize_available_resources(game_data.resources)

    print(f"Trial {i+1}: {len(civ.available_resources)} resources selected")

    for res_id in civ.available_resources:
        resource = game_data.resources.get(res_id)
        if resource:
            tech_str = f"tech: {resource.tech_reveal}" if resource.tech_reveal else "no tech"
            bonus_class_str = f"[{resource.bonus_class}]" if resource.bonus_class else ""
            print(f"  - {resource.name} {bonus_class_str} ({tech_str})")

    # Verify the crop resource has early tech
    crop_found = False
    for res_id in civ.available_resources:
        resource = game_data.resources.get(res_id)
        if resource and resource.bonus_class == 'crop':
            crop_found = True
            if resource.tech_reveal not in ['scavenging', 'gathering']:
                print(f"  ❌ ERROR: Crop resource {resource.name} requires {resource.tech_reveal}, not scavenging/gathering!")
            else:
                print(f"  ✓ Crop resource has early tech requirement: {resource.tech_reveal}")

    if not crop_found:
        print(f"  ⚠ WARNING: No crop resource selected!")

    print()

print("=== Test Complete ===")
