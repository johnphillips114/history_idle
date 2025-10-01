"""Load and display C2C buildings."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.history_idle.data.c2c_loader import C2CDataLoader
from src.history_idle.data.c2c_parser import C2CDataParser
from collections import defaultdict

print("=== Loading C2C Buildings ===\n")

# Initialize loader
loader = C2CDataLoader()

# Download/load building XML
print("Fetching building data...")
building_xml = loader.get_building_xml()
print(f"Loaded {len(building_xml)} bytes of XML data\n")

# Parse buildings
print("Parsing buildings...")
parser = C2CDataParser()
buildings = parser.parse_buildings_xml(building_xml)

print(f"Parsed {len(buildings)} buildings\n")

# Group by category
from src.history_idle.models import BuildingCategory

buildings_by_category = defaultdict(list)
for building in buildings:
    buildings_by_category[building.category].append(building)

# Display summary
print("=== Buildings by Category ===")
for category in BuildingCategory:
    builds = buildings_by_category.get(category, [])
    print(f"\n{category.value.title()}: {len(builds)} buildings")

    # Show first 5 of each category
    for i, building in enumerate(builds[:5]):
        tech_req = f" (requires: {building.required_tech})" if building.required_tech else ""
        cost = building.construction_costs[0].amount if building.construction_costs else 0
        effects_str = ", ".join([f"{k}: {v}" for k, v in list(building.effects.items())[:2]])
        if effects_str:
            effects_str = f" [{effects_str}]"
        print(f"  {building.id:35} - {building.name:40} Cost: {cost:6.0f}{tech_req}{effects_str}")

    if len(builds) > 5:
        print(f"  ... and {len(builds) - 5} more")

# Show buildings with no tech requirement (starting buildings)
starting_buildings = [b for b in buildings if not b.required_tech]
print(f"\n=== Starting Buildings (no tech requirement): {len(starting_buildings)} ===")
for building in starting_buildings[:15]:
    cost = building.construction_costs[0].amount if building.construction_costs else 0
    effects_str = ", ".join([f"{k}: {v}" for k, v in list(building.effects.items())[:2]])
    if effects_str:
        effects_str = f" [{effects_str}]"
    print(f"  {building.id:35} - {building.name:40} Cost: {cost:6.0f}{effects_str}")

if len(starting_buildings) > 15:
    print(f"  ... and {len(starting_buildings) - 15} more")

# Show some interesting buildings
print(f"\n=== Sample Buildings with Effects ===")
buildings_with_effects = [b for b in buildings if b.effects]
for building in buildings_with_effects[:10]:
    cost = building.construction_costs[0].amount if building.construction_costs else 0
    tech_str = f" (tech: {building.required_tech})" if building.required_tech else ""
    print(f"\n  {building.name} (ID: {building.id})")
    print(f"    Category: {building.category.value}, Cost: {cost:.0f}{tech_str}")
    print(f"    Effects: {building.effects}")
    if building.required_resources:
        print(f"    Required Resources: {', '.join(building.required_resources)}")

print("\n=== Test Complete ===")
