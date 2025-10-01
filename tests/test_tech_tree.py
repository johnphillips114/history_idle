"""Test tech tree integration."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.history_idle.models import Civilization, StartingLocation
from src.history_idle.data.game_data import GameDataManager

print("=== Testing Tech Tree Integration ===\n")

# Load game data
print("Loading game data...")
game_data = GameDataManager()
game_data.load_all()

# Create civilization
civ = Civilization(
    name="Test Civilization",
    starting_location=StartingLocation.MESOPOTAMIA
)
civ.initialize_starting_resources()
civ.load_tech_tree(game_data.technologies)

print(f"\nTech tree has {len(civ.tech_tree.technologies)} technologies")

# Get starting techs
starting_techs = civ.tech_tree.get_available_technologies()
print(f"\nAvailable technologies (no prerequisites): {len(starting_techs)}")

for tech in starting_techs[:10]:
    print(f"  {tech.id:30} - {tech.name:40} Cost: {tech.research_cost:6.0f}")

# Test researching a tech
print("\n--- Testing Research ---")
cave_dwelling = civ.tech_tree.get_technology('cave_dwelling')
if cave_dwelling:
    print(f"\nTrying to research: {cave_dwelling.name} (Cost: {cave_dwelling.research_cost})")

    if civ.tech_tree.start_research('cave_dwelling'):
        print("✓ Started research")
        print(f"  Current research: {civ.tech_tree.current_research.tech_def.name}")
        print(f"  Progress: {civ.tech_tree.current_research.research_points}/{civ.tech_tree.current_research.tech_def.research_cost}")

        # Add research points
        print("\n  Adding 3 research points...")
        completed = civ.tech_tree.add_research_points(3.0)

        if completed:
            print(f"✓ Completed tech: {completed.name}")
            print(f"  Total researched: {len(civ.tech_tree.researched)}")

            # Check what's newly available
            new_available = civ.tech_tree.get_available_technologies()
            print(f"\n  Newly available technologies: {len(new_available)}")
            for tech in new_available[:5]:
                prereq_str = f" (requires: {', '.join(tech.prerequisites)})" if tech.prerequisites else ""
                print(f"    {tech.id:30} - {tech.name}{prereq_str}")
    else:
        print("✗ Failed to start research")
else:
    print("Could not find 'cave_dwelling' technology")

print("\n=== Test Complete ===")
