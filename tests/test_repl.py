"""Test script to demonstrate the REPL interface."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import time
from src.history_idle.models import Civilization, StartingLocation
from src.history_idle.systems.game_loop import GameLoop
from src.history_idle.utils.save_system import SaveSystem

# Create a new civilization
civ = Civilization(
    name="Test Civilization",
    starting_location=StartingLocation.MESOPOTAMIA
)
civ.initialize_starting_resources()

# Create game loop
game_loop = GameLoop(civ)

print("=== Testing Basic Gameplay ===\n")

# Show initial state
print("Initial State:")
print(f"  Population: {civ.population.total}")
print(f"  Food: {civ.resources.get('food').amount:.1f}")
print(f"  Research: {civ.resources.get('research').amount:.1f}")

# Allocate 5 workers to food
print("\n--- Allocating 5 workers to food extraction ---")
from src.history_idle.models import WorkforceTask
allocated = civ.population.allocate_workers(WorkforceTask.RESOURCE_EXTRACTION, 5, resource_id="food")
print(f"Allocated {allocated} workers")

# Allocate 3 workers to research
print("\n--- Allocating 3 workers to research ---")
allocated = civ.population.allocate_workers(WorkforceTask.RESEARCH, 3)
print(f"Allocated {allocated} workers")

# Show allocations
print(f"\nIdle workers: {civ.population.idle_workers}")
print(f"Total allocated: {civ.population.allocated_workers}")

# Simulate 10 seconds
print("\n--- Simulating 10 seconds ---")
update = game_loop.tick(10.0)

# Show results
print(f"\nAfter 10 seconds:")
print(f"  Food: {civ.resources.get('food').amount:.1f} (Rate: {civ.resources.get('food').net_rate:+.2f}/s)")
print(f"  Research: {civ.resources.get('research').amount:.1f} (Rate: {civ.resources.get('research').production_rate:+.2f}/s)")
print(f"  Population: {civ.population.total}")

# Simulate another 30 seconds
print("\n--- Simulating 30 more seconds ---")
update = game_loop.tick(30.0)

print(f"\nAfter 40 seconds total:")
print(f"  Food: {civ.resources.get('food').amount:.1f} (Rate: {civ.resources.get('food').net_rate:+.2f}/s)")
print(f"  Research: {civ.resources.get('research').amount:.1f}")
print(f"  Population: {civ.population.total}")

print("\n=== Test Complete ===")
print("\nNow run 'python main.py' to play with the interactive REPL!")
