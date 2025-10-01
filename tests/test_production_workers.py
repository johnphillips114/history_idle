"""Test production resource and worker allocation."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.history_idle.models.civilization import Civilization, StartingLocation
from src.history_idle.models.population import WorkforceTask
import time

print("=== Testing Production Workers ===\n")

# Create a new civilization
civ = Civilization("Test Civ", StartingLocation.MESOPOTAMIA)
civ.initialize_starting_resources()

print("Initial state:")
print(f"  Population: {civ.population.total}")
print(f"  Idle workers: {civ.population.idle_workers}")

# Check that production resource exists
production_resource = civ.resources.get("production")
if production_resource:
    print(f"  ✓ Production resource exists")
    print(f"    Amount: {production_resource.amount}")
    print(f"    Production rate: {production_resource.production_rate}/s")
else:
    print(f"  ❌ Production resource not found!")
    sys.exit(1)

print("\n--- Test 1: Allocate 5 workers to production ---")
allocated = civ.population.allocate_workers(WorkforceTask.CONSTRUCTION, 5)
print(f"Allocated: {allocated} workers")
print(f"Idle workers: {civ.population.idle_workers}")

# Get current production count
production_workers = civ.population.get_workers_on_task(WorkforceTask.CONSTRUCTION)
print(f"Production workers: {production_workers}")

print("\n--- Test 2: Run game update (1 second) ---")
civ.last_update_time = time.time()
update_summary = civ.update(delta_time=1.0)

production_resource = civ.resources.get("production")
print(f"Production after 1 second:")
print(f"  Amount: {production_resource.amount}")
print(f"  Production rate: {production_resource.production_rate}/s")
print(f"  Expected: 5.0 (5 workers × 1.0/s)")

if abs(production_resource.amount - 5.0) < 0.01:
    print("  ✓ Production calculation correct!")
else:
    print(f"  ❌ Production calculation incorrect! Expected 5.0, got {production_resource.amount}")

print("\n--- Test 3: Run another update (5 seconds) ---")
update_summary = civ.update(delta_time=5.0)

production_resource = civ.resources.get("production")
print(f"Production after 5 more seconds:")
print(f"  Amount: {production_resource.amount}")
print(f"  Expected: 30.0 (5 + 5×5)")

if abs(production_resource.amount - 30.0) < 0.01:
    print("  ✓ Production accumulation correct!")
else:
    print(f"  ❌ Production accumulation incorrect! Expected 30.0, got {production_resource.amount}")

print("\n--- Test 4: Allocate more workers ---")
allocated = civ.population.allocate_workers(WorkforceTask.CONSTRUCTION, 3)
print(f"Allocated {allocated} more workers")
production_workers = civ.population.get_workers_on_task(WorkforceTask.CONSTRUCTION)
print(f"Total production workers: {production_workers}")

update_summary = civ.update(delta_time=1.0)
production_resource = civ.resources.get("production")
print(f"\nProduction after 1 second with {production_workers} workers:")
print(f"  Amount: {production_resource.amount}")
print(f"  Production rate: {production_resource.production_rate}/s")
print(f"  Expected amount: {30.0 + production_workers * 1.0}")

if abs(production_resource.amount - (30.0 + production_workers * 1.0)) < 0.01:
    print("  ✓ Production scaling correct!")
else:
    print(f"  ❌ Production scaling incorrect!")

print("\n--- Test 5: Deallocate workers ---")
deallocated = civ.population.deallocate_workers(WorkforceTask.CONSTRUCTION, 4)
print(f"Deallocated: {deallocated} workers")
production_workers = civ.population.get_workers_on_task(WorkforceTask.CONSTRUCTION)
print(f"Remaining production workers: {production_workers}")

print("\n=== All Tests Complete ===")
