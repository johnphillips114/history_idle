# Tests and Examples

This directory contains test scripts and examples for History Idle.

## Test Scripts

### Core System Tests
- `test_food_bug.py` - Tests food production calculations
- `test_debug.py` - Tests debug mode calculations
- `test_tech_tree.py` - Tests tech tree integration
- `test_repl.py` - Tests basic gameplay mechanics

### Data Loading Scripts
- `load_c2c_techs.py` - Downloads and displays C2C technology tree
- `load_c2c_buildings.py` - Downloads and displays C2C building tree

## Running Tests

From the project root directory:

```bash
# Test food production
python tests/test_food_bug.py

# Test tech tree
python tests/test_tech_tree.py

# Load and view C2C technologies
python tests/load_c2c_techs.py

# Load and view C2C buildings
python tests/load_c2c_buildings.py
```

## Test Coverage

These tests verify:
- ✅ Resource production and consumption
- ✅ Population and workforce mechanics
- ✅ Technology research system
- ✅ C2C data parsing and integration
- ✅ Building system
- ✅ Game loop and updates
