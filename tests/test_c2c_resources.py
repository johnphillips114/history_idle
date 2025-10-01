"""Test loading C2C resources."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.history_idle.data.game_data import GameDataManager

print("=== Testing C2C Resources Loading ===\n")

# Load game data
game_data = GameDataManager()
game_data.load_all()

print(f"\n✓ Successfully loaded {len(game_data.resources)} resources\n")

# Show examples by category
from src.history_idle.models.resource import ResourceCategory

print("Resource breakdown by category:")
for category in ResourceCategory:
    count = sum(1 for r in game_data.resources.values() if r.category == category)
    print(f"  {category.value.upper()}: {count}")

print("\nExample resources:")
print("\nFood resources:")
food_resources = [r for r in game_data.resources.values() if r.category == ResourceCategory.FOOD]
for resource in food_resources[:10]:
    print(f"  - {resource.name} (ID: {resource.id})")

print("\nStrategic resources:")
strategic_resources = [r for r in game_data.resources.values() if r.category == ResourceCategory.STRATEGIC]
for resource in strategic_resources[:10]:
    print(f"  - {resource.name} (ID: {resource.id})")

print("\nLuxury resources:")
luxury_resources = [r for r in game_data.resources.values() if r.category == ResourceCategory.LUXURY]
for resource in luxury_resources[:10]:
    print(f"  - {resource.name} (ID: {resource.id})")

# Check specific well-known resources
print("\n--- Checking Specific Resources ---")
test_resources = ['barley', 'corn', 'wheat', 'iron', 'horse', 'copper', 'gold', 'silver']
for res_id in test_resources:
    resource = game_data.resources.get(res_id)
    if resource:
        print(f"  ✓ {resource.name} ({resource.category.value})")
    else:
        print(f"  ❌ {res_id} - NOT FOUND")

print("\n=== Test Complete ===")
