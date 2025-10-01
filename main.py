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

        # Select a random civilization
        civ_def = game_data.get_random_civilization()
        if not civ_def:
            print("ERROR: No civilizations loaded!")
            return

        print(f"Civilization: {civ_def.name}")
        first_city_name = civ_def.get_first_city_name()
        print(f"Starting city: {first_city_name}")

        civ = Civilization(
            name=civ_def.name,
            starting_location=StartingLocation.MESOPOTAMIA
        )

        # Rename the starting city to use the civilization's first city name
        active_city = civ.get_active_city()
        if active_city:
            active_city.name = first_city_name

        civ.initialize_starting_resources()
        civ.load_tech_tree(game_data.technologies)
        civ.load_buildings(game_data.buildings)
        civ.initialize_available_resources(game_data.resources)
        print(f"Loaded {len(civ.tech_tree.technologies)} technologies into tech tree")

        if active_city:
            print(f"Loaded {len(active_city.buildings.building_definitions)} buildings")
            print(f"Selected {len(active_city.available_resources)} starting resources for {active_city.name}")
    else:
        print("\n=== History Idle - Loaded Game ===\n")
        # Load tech tree and buildings definitions for existing save
        civ.load_tech_tree(game_data.technologies)
        civ.load_buildings(game_data.buildings)

        # Restore buildings and research from save data
        save_system.restore_from_save_data(civ)

        # Show info about restored cities
        print(f"Restored {len(civ.cities)} cities")
        for city in civ.cities:
            print(f"  {city.name}: {city.population.total} population, {len(city.buildings.buildings)} buildings")
        if civ.tech_tree.current_research:
            print(f"Restored current research: {civ.tech_tree.current_research.tech_def.name}")

    # Initialize game loop
    game_loop = GameLoop(civ)

    # Start REPL interface
    repl = GameREPL(civ, game_loop, save_system, game_data)
    repl.start()


if __name__ == "__main__":
    main()
