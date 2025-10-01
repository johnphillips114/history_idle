"""Main entry point for History Idle game."""

import sys
from src.history_idle.models import Civilization, StartingLocation
from src.history_idle.systems.game_loop import GameLoop
from src.history_idle.utils.save_system import SaveSystem
from src.history_idle.ui.repl import GameREPL
from src.history_idle.data.game_data import GameDataManager


def main():
    """Main game entry point."""
    # Load game data
    print("Loading game data...")
    game_data = GameDataManager()
    game_data.load_all()

    # Initialize save system
    save_system = SaveSystem()

    # Try to load existing save or create new game
    civ = save_system.load_game("autosave")

    if civ is None:
        print("\n=== History Idle - New Game ===\n")
        civ = Civilization(
            name="Test Civilization",
            starting_location=StartingLocation.MESOPOTAMIA
        )
        civ.initialize_starting_resources()
        civ.load_tech_tree(game_data.technologies)
        civ.load_buildings(game_data.buildings)
        civ.initialize_available_resources(game_data.resources)
        print(f"Loaded {len(civ.tech_tree.technologies)} technologies into tech tree")
        print(f"Loaded {len(civ.buildings.building_definitions)} buildings")
        print(f"Selected {len(civ.available_resources)} starting resources")
    else:
        print("\n=== History Idle - Loaded Game ===\n")
        # Load tech tree and buildings definitions for existing save
        civ.load_tech_tree(game_data.technologies)
        civ.load_buildings(game_data.buildings)

        # Restore buildings and research from save data
        save_system.restore_from_save_data(civ)

        print(f"Restored {len(civ.buildings.buildings)} buildings")
        if civ.buildings.under_construction:
            print(f"Restored {len(civ.buildings.under_construction)} buildings under construction")
        if civ.tech_tree.current_research:
            print(f"Restored current research: {civ.tech_tree.current_research.tech_def.name}")

    # Initialize game loop
    game_loop = GameLoop(civ)

    # Start REPL interface
    repl = GameREPL(civ, game_loop, save_system, game_data)
    repl.start()


if __name__ == "__main__":
    main()
