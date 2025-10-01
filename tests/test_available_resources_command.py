"""Test the available_resources command."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.history_idle.data.game_data import GameDataManager
from src.history_idle.models.civilization import Civilization, StartingLocation
from src.history_idle.systems.game_loop import GameLoop
from src.history_idle.utils.save_system import SaveSystem
from src.history_idle.ui.repl import GameREPL

print("=== Testing Available Resources Command ===\n")

# Load game data
game_data = GameDataManager()
game_data.load_all()

# Create a new civilization
civ = Civilization("Test Civ", StartingLocation.MESOPOTAMIA)
civ.initialize_starting_resources()
civ.load_tech_tree(game_data.technologies)
civ.load_buildings(game_data.buildings)

# Create REPL
game_loop = GameLoop(civ)
save_system = SaveSystem()
repl = GameREPL(civ, game_loop, save_system, game_data)

print("Test 1: No technologies researched")
print("-" * 50)
repl.cmd_available_resources([])

print("\n\nTest 2: After researching 'gathering' tech")
print("-" * 50)
# Research gathering tech (should unlock some basic resources)
civ.tech_tree.researched.add('gathering')
repl.cmd_available_resources([])

print("\n\nTest 3: Check specific resource tech requirements")
print("-" * 50)
test_resources = ['barley', 'wheat', 'iron_ore', 'copper_ore']
for res_id in test_resources:
    resource = game_data.resources.get(res_id)
    if resource:
        print(f"  {resource.name}:")
        print(f"    Tech required: {resource.tech_reveal}")
        if resource.tech_reveal is None or resource.tech_reveal in civ.tech_tree.researched:
            print(f"    Status: AVAILABLE")
        else:
            print(f"    Status: LOCKED")

print("\n=== Test Complete ===")
