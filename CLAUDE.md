# CLAUDE.md - Context Guide for History Idle

## Project Overview

**History Idle** is an incremental civilization game through history built in Python.

- **Language**: Python 3.13+
- **Current Interface**: REPL (Read-Eval-Print Loop) - text-based command interface
- **Future Plan**: Refactor to an interactive graphical interface
- **Game Type**: Incremental/idle game with civilization building mechanics

## Architecture

The project follows a clean separation of concerns with models, systems, UI, data, and utilities:

```
history_idle/
├── main.py                      # Entry point
├── data/game/                   # JSON game data files
│   ├── buildings.json          # All building definitions (~1.9MB)
│   ├── civilizations.json      # Civilization definitions
│   ├── resources.json          # Resource types and properties
│   ├── technologies.json       # Tech tree data (~1.2MB)
│   └── terrains.json           # Terrain types
└── src/history_idle/
    ├── models/                  # Core game entities (dataclasses)
    │   ├── building.py         # Building and BuildingManager
    │   ├── city.py             # City model
    │   ├── civilization.py     # Main civilization model
    │   ├── civilization_definition.py
    │   ├── population.py       # Population and workforce
    │   ├── resource.py         # Resources and storage
    │   ├── technology.py       # TechTree and research
    │   ├── terrain.py          # Terrain types
    │   └── tile.py             # City tiles
    ├── systems/                 # Game logic
    │   ├── game_loop.py        # Main game loop (ticks, updates)
    │   └── resource_system.py  # Resource production/consumption
    ├── ui/                      # Interface layer
    │   └── repl.py             # REPL command interface
    ├── data/                    # Data loading
    │   ├── game_data.py        # GameDataManager
    │   └── json_loader.py      # JSON loading utilities
    └── utils/                   # Utilities
        └── save_system.py      # Save/load functionality
```

## Core Game Concepts

### 1. Civilization
- Main player entity with name and starting location
- Has multiple cities, a tech tree, and civilization-wide resources
- Progresses through eras (Paleolithic → Modern)
- Has a government type (Tribal, Democracy, etc.)
- Tracks prestige points and game time

### 2. Cities
- **Multi-city management**: Players can manage multiple cities
- Each city has:
  - Population (can be allocated to workforce tasks)
  - Buildings (constructed and provide benefits)
  - Resources (local production/storage)
  - Terrain type (affects available resources)
  - Available resources (what can be produced locally)
- One city is "active" at a time for commands

### 3. Resources
- Produced and consumed per second (rate-based)
- Stored in ResourceStorage (with capacity limits)
- Categories: Food, Material, Luxury, Military, Abstract
- Types: Food, Wood, Stone, Gold, Science, Culture, etc.

### 4. Technologies
- Organized in a tech tree by era
- Require science points to research
- Unlock buildings, units, and capabilities
- Have prerequisites (other techs required first)

### 5. Buildings
- Defined in JSON with costs, upkeep, and effects
- Require technologies to unlock
- Consume resources (upkeep) but provide benefits
- Can have build limits (max per city)
- May require other buildings as prerequisites

### 6. Population & Workforce
- Population grows over time
- Can be allocated to tasks:
  - Resource production (gatherers, farmers, etc.)
  - Building construction
  - Settler preparation
- Idle population doesn't contribute

### 7. Game Loop
- Runs continuously with periodic ticks
- Each tick:
  - Updates resource production/consumption
  - Advances research progress
  - Updates population
  - Checks building construction
  - Processes offline time when loading saves

## Game Flow

1. **Initialization** (main.py):
   - Load JSON game data (civilizations, technologies, buildings, resources, terrains)
   - Try to load existing save, or create new civilization
   - Initialize GameLoop and REPL

2. **Game Loop** (systems/game_loop.py):
   - Ticks on a timer (continuous updates)
   - Calls update methods on civilization/cities
   - Handles resource production and consumption
   - Advances research and construction

3. **REPL Interface** (ui/repl.py):
   - Displays status (era, city, resources, population)
   - Accepts commands:
     - `help` - Show available commands
     - `resources` / `res` - View resources
     - `available` / `avail` - Available resources for city
     - `population` / `pop` - View population
     - `allocate` / `alloc` - Assign workers
     - `tech` - View tech tree
     - `research` - Start research
     - `buildings` - List buildings
     - `build` - Construct building
     - `cities` - List cities
     - `switch` - Switch active city
     - `found` - Found new city
     - `status` - Show status
     - `describe` / `desc` - Describe entity
     - `save` - Save game
     - `quit` / `exit` / `q` - Exit

4. **Save/Load** (utils/save_system.py):
   - Autosave on quit
   - Save file: `~/.history_idle/saves/autosave.json`
   - Handles offline time calculation

## Development Patterns

### Dataclasses
Models use `@dataclass` for clean entity definitions:
```python
@dataclass
class Civilization:
    name: str
    starting_location: StartingLocation
    current_era: Era = Era.PALEOLITHIC
    tech_tree: TechTree = field(default_factory=TechTree)
    cities: list[City] = field(default_factory=list)
```

### Enums
Constants use Enum classes:
- `Era`: PALEOLITHIC, NEOLITHIC, BRONZE, etc.
- `GovernmentType`: TRIBAL, DEMOCRACY, MONARCHY, etc.
- `StartingLocation`: MESOPOTAMIA, NILE, YELLOW_RIVER, etc.
- `ResourceType`: FOOD, WOOD, STONE, GOLD, SCIENCE, etc.

### JSON Data
Game content is data-driven via JSON files:
- Allows easy modification without code changes
- Loaded once at startup via GameDataManager
- Technologies, buildings, resources, civilizations all defined in JSON

### Time-based Mechanics
- Game uses real-time seconds for calculations
- Resources have production/consumption rates (per second)
- Research has time-based progress
- Offline time is calculated and applied on load

## Common Development Tasks

| Task | Primary Files |
|------|---------------|
| Add new resource type | `data/game/resources.json`, `models/resource.py` |
| Add new technology | `data/game/technologies.json`, `models/technology.py` |
| Add new building | `data/game/buildings.json`, `models/building.py` |
| Modify game tick logic | `systems/game_loop.py` |
| Add REPL command | `ui/repl.py` (add to `self.commands` dict and create method) |
| Change resource production | `systems/resource_system.py` or `models/city.py` |
| Modify save format | `utils/save_system.py` |
| Add new civilization | `data/game/civilizations.json` |
| Change UI display | `ui/repl.py` display methods |

## Important Context for AI Assistance

1. **Game Loop is Continuous**: The game runs in real-time even when player isn't actively commanding. Resources accumulate/deplete continuously.

2. **Cities are Production Units**: Most game mechanics happen at the city level. Each city produces resources, builds buildings, and manages population independently.

3. **Technology Gates Progress**: Buildings and capabilities are locked behind technologies. Always check tech requirements when adding features.

4. **Resource Balance Matters**: Buildings have upkeep costs. Running out of food can cause starvation. Production/consumption balance is critical.

5. **Population Allocation**: Idle population doesn't contribute. Workers must be allocated to tasks to produce resources or build.

6. **Multi-City Complexity**: With multiple cities, commands affect only the active city. Some resources are city-specific, others civilization-wide.

7. **Save Compatibility**: Changes to model structure may break existing saves. Consider migration when modifying dataclasses.

8. **Data-Driven Design**: Prefer adding to JSON files over hardcoding. The game is designed to be highly moddable.

9. **Future UI Refactor**: Current REPL is temporary. When designing features, consider how they'd work in a graphical interface.

10. **Large Data Files**: technologies.json and buildings.json are very large (1-2MB). They contain extensive historical content from various eras.

## Key Classes Quick Reference

- **Civilization** (models/civilization.py): Top-level player entity, manages cities and civ-wide state
- **City** (models/city.py): Individual city with population, buildings, local resources
- **ResourceStorage** (models/resource.py): Manages resource quantities and rates
- **TechTree** (models/technology.py): Manages research and unlocked technologies
- **BuildingManager** (models/building.py): Manages buildings in a city
- **Population** (models/population.py): Manages population and workforce allocation
- **GameLoop** (systems/game_loop.py): Main game loop, handles ticking and updates
- **GameREPL** (ui/repl.py): REPL interface, command handling
- **SaveSystem** (utils/save_system.py): Save/load functionality
- **GameDataManager** (data/game_data.py): Loads and manages JSON game data

## Testing

Test files are in `tests/` directory covering:
- Tech tree functionality
- Building prerequisites and requirements
- Resource availability and production
- Save/load system
- Multi-city management
- Civilization mechanics

Run tests with: `pytest tests/`

## Building Effects System

Buildings use a dual system for bonuses:

1. **JSON Format** (`data/game/buildings.json`):
   - Buildings have a `"bonuses"` field with key-value pairs
   - Example: `"bonuses": {"military": 10, "housing": 5}`

2. **Code Mapping** (`src/history_idle/data/json_loader.py`):
   - The `load_buildings()` method converts JSON to BuildingDefinition objects
   - Some bonuses are mapped to `effects` dict for gameplay mechanics
   - Currently housing bonuses are mapped: `effects["housing"] = bonuses["housing"]`
   - Other bonuses remain in `flavors` dict for AI/flavor purposes

3. **Usage in Game**:
   - `BuildingManager.get_total_effect(effect_key)` sums effects from all active buildings
   - City housing capacity: `base_capacity (10) + building housing effects`
   - See `City._update_housing_capacity()` in models/city.py:324

**Adding new building effect types**: Add mapping in json_loader.py, then use `get_total_effect()` where needed.

## Resource System Details

### Resource Storage Layers

1. **City Resources** (`city.resources`):
   - Local storage for physical resources (food, wood, stone, etc.)
   - Each city auto-initializes abstract resources: production, currency, religion, espionage, culture, research
   - Abstract resources typically have `can_store=False` and `capacity=0`

2. **Civilization Resources** (`civilization.resources`):
   - Civ-wide abstract resources (mainly research points)
   - Shared across all cities

3. **ResourceQuantity** (models/resource.py):
   - Each resource has: `amount`, `capacity`, `production_rate`, `consumption_rate`
   - `net_rate = production_rate - consumption_rate`
   - Updates happen automatically via `resource.update(delta_time)`

### Resource Display

The `resources` command (ui/repl.py:502) shows:
- City resources (excludes production/research, only shows amount > 0)
- Civilization resources (same filtering)
- Displays: name, amount/capacity, net rate, time to full/empty

## Save System Details

### Save File Location
- Default: `~/.history_idle/saves/autosave.json`
- Auto-saves on quit

### Common Save/Load Issues

1. **Initialization Order Matters**:
   - Cities auto-initialize default resources in `__post_init__`
   - Save system must explicitly set amounts after initialization
   - Both `add_resource_type(initial_amount)` AND `resource.amount = value` are needed

2. **Reference Attributes** (`_all_resources`, `_all_terrains`):
   - Not serialized in save files
   - Must be restored from GameDataManager on load
   - Check with `hasattr()` before accessing in old saves
   - See main.py:67-70 for load-time initialization

3. **Building/Tech Definitions**:
   - Only IDs are saved, not full definitions
   - Definitions loaded fresh from JSON on each load
   - Changes to JSON affect loaded saves

### Save Format Changes

When modifying dataclass structure:
- Old saves may be missing new attributes
- Use `data.get("key", default_value)` for backward compatibility
- Consider if migration logic is needed in SaveSystem

## Common Gotchas

1. **Resources showing only Food**: Save system wasn't restoring resource amounts. Fixed in save_system.py by explicitly setting `resource.amount`.

2. **AttributeError on _all_resources**: Old saves don't have this attribute. Always check with `hasattr()` or initialize in main.py on load.

3. **Housing Capacity**: Calculated from base (10) + building effects. Must call `_update_housing_capacity()` after building changes.

4. **Population can't grow**: Check housing capacity. Population stops growing at `housing_capacity`. Build housing-bonus buildings to expand.

5. **Resource production rates**: Set per resource instance, not per type. When loading saves, restore all four fields: amount, capacity, production_rate, consumption_rate.

6. **Building bonuses vs effects**: Bonuses are in JSON for data, effects are in code for mechanics. Add mapping in json_loader.py to make bonuses functional.
