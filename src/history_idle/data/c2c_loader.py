"""Loader for Caveman2Cosmos data from GitHub."""

import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional
import shutil


class C2CDataLoader:
    """Downloads and caches C2C data files from GitHub."""

    BASE_URL = "https://raw.githubusercontent.com/caveman2cosmos/Caveman2Cosmos/b0fc0fc72072a1bf72882d733f68baedf763684c/Assets/XML"

    def __init__(self, cache_dir: Optional[Path] = None, local_data_dir: Optional[Path] = None):
        if cache_dir is None:
            cache_dir = Path.home() / '.history_idle' / 'c2c_cache'
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Local data directory for offline access
        if local_data_dir is None:
            # Default to project's data directory
            local_data_dir = Path(__file__).parent.parent.parent.parent / 'data' / 'c2c'
        self.local_data_dir = Path(local_data_dir)
        self.local_data_dir.mkdir(parents=True, exist_ok=True)

    def get_tech_xml(self) -> str:
        """Get the technology XML file content."""
        return self._get_cached_file(
            "Technologies/CIV4TechInfos.xml",
            f"{self.BASE_URL}/Technologies/CIV4TechInfos.xml"
        )

    def get_bonus_xml(self) -> str:
        """Get the bonus/resource XML file content."""
        return self._get_cached_file(
            "Terrain/CIV4BonusInfos.xml",
            f"{self.BASE_URL}/Terrain/CIV4BonusInfos.xml"
        )

    def get_building_xml(self) -> str:
        """Get the building XML file content."""
        return self._get_cached_file(
            "Buildings/Regular_CIV4BuildingInfos.xml",
            f"{self.BASE_URL}/Buildings/Regular_CIV4BuildingInfos.xml"
        )

    def get_civilization_xml(self) -> str:
        """Get the civilization XML file content."""
        return self._get_cached_file(
            "Civilizations/CIV4CivilizationInfos.xml",
            f"{self.BASE_URL}/Civilizations/CIV4CivilizationInfos.xml"
        )

    def _get_cached_file(self, relative_path: str, url: str) -> str:
        """Get file content from local data, cache, or download if not available."""
        local_path = self.local_data_dir / relative_path.replace('/', '_')
        cache_path = self.cache_dir / relative_path.replace('/', '_')

        # Check local data directory first (for offline access)
        if local_path.exists():
            print(f"Loading {relative_path} from local data...")
            with open(local_path, 'r', encoding='utf-8') as f:
                return f.read()

        # Check user cache directory
        if cache_path.exists():
            print(f"Loading {relative_path} from cache...")
            with open(cache_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Copy to local data directory for offline access
            print(f"Copying to local data directory for offline access...")
            with open(local_path, 'w', encoding='utf-8') as f:
                f.write(content)

            return content

        # Download from GitHub
        print(f"Downloading {relative_path} from GitHub...")
        try:
            with urllib.request.urlopen(url) as response:
                content = response.read().decode('utf-8')

            # Save to both cache and local data directory
            with open(cache_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Cached to {cache_path}")

            with open(local_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Saved to local data: {local_path}")

            return content

        except Exception as e:
            print(f"Error downloading {url}: {e}")
            print(f"Note: Game data not available offline. Please connect to download.")
            raise

    def clear_cache(self):
        """Clear all cached files."""
        import shutil
        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir)
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            print("Cache cleared")
