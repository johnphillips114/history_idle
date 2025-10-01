"""Load and display C2C technologies."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.history_idle.data.c2c_loader import C2CDataLoader
from src.history_idle.data.c2c_parser import C2CDataParser

print("=== Loading C2C Tech Tree ===\n")

# Initialize loader
loader = C2CDataLoader()

# Download/load tech XML
print("Fetching technology data...")
tech_xml = loader.get_tech_xml()
print(f"Loaded {len(tech_xml)} bytes of XML data\n")

# Parse technologies
print("Parsing technologies...")
parser = C2CDataParser()
technologies = parser.parse_technologies_xml(tech_xml)

print(f"Parsed {len(technologies)} technologies\n")

# Group by era
from collections import defaultdict
from src.history_idle.models import Era

techs_by_era = defaultdict(list)
for tech in technologies:
    techs_by_era[tech.era].append(tech)

# Display summary
print("=== Technologies by Era ===")
for era in Era:
    techs = techs_by_era.get(era, [])
    print(f"\n{era.value.title()}: {len(techs)} technologies")

    # Show first 5 of each era
    for i, tech in enumerate(techs[:5]):
        prereqs = f" (requires: {', '.join(tech.prerequisites[:3])})" if tech.prerequisites else ""
        print(f"  {tech.id:30} - {tech.name:40} Cost: {tech.research_cost:6.0f}{prereqs}")

    if len(techs) > 5:
        print(f"  ... and {len(techs) - 5} more")

# Show technologies with no prerequisites (starting techs)
starting_techs = [t for t in technologies if not t.prerequisites]
print(f"\n=== Starting Technologies (no prerequisites): {len(starting_techs)} ===")
for tech in starting_techs[:10]:
    print(f"  {tech.id:30} - {tech.name:40} Era: {tech.era.value:15} Cost: {tech.research_cost:6.0f}")

if len(starting_techs) > 10:
    print(f"  ... and {len(starting_techs) - 10} more")
