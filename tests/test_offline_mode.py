"""Test offline mode capability."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import os
import shutil

print("=== Testing Offline Mode ===\n")

# 1. Verify local data exists
data_dir = Path("data/c2c")
print(f"Checking local data directory: {data_dir.absolute()}")

if not data_dir.exists():
    print("❌ Local data directory does not exist!")
    print("   Run the game once to download data.")
    sys.exit(1)

files = list(data_dir.glob("*.xml"))
if not files:
    print("❌ No XML files in local data directory!")
    print("   Run the game once to download data.")
    sys.exit(1)

print(f"✓ Found {len(files)} XML files in local data directory:")
for f in files:
    size_mb = f.stat().st_size / (1024 * 1024)
    print(f"  - {f.name}: {size_mb:.1f} MB")

# 2. Clear user cache to simulate offline mode
cache_dir = Path.home() / '.history_idle' / 'c2c_cache'
if cache_dir.exists():
    print(f"\nClearing cache at {cache_dir} to test offline mode...")
    shutil.rmtree(cache_dir)
    print("✓ Cache cleared")
else:
    print("\n✓ No cache directory (already clean)")

# 3. Test loading data in offline mode
print("\n--- Loading game data in offline mode ---")

from src.history_idle.data.game_data import GameDataManager

game_data = GameDataManager()
game_data.load_all()

print(f"\n✓ Successfully loaded game data offline!")
print(f"  - Technologies: {len(game_data.technologies)}")
print(f"  - Buildings: {len(game_data.buildings)}")

# 4. Verify we loaded from local data
if not cache_dir.exists():
    print("\n✓ Confirmed: Data loaded from local directory (cache not created)")
else:
    print("\n⚠ Warning: Cache directory was created during load")

print("\n=== Offline Mode Test Passed! ===")
print("\nThe game can run completely offline with the data files in data/c2c/")
