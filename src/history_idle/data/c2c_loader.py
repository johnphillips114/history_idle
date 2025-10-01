import urllib.request
from pathlib import Path
from typing import Optional


class C2CDataLoader:
    BASE_URL = "https://raw.githubusercontent.com/caveman2cosmos/Caveman2Cosmos/b0fc0fc72072a1bf72882d733f68baedf763684c/Assets/XML"
    GAMETEXT_BASE_URL = "https://raw.githubusercontent.com/caveman2cosmos/Caveman2Cosmos/refs/heads/master/Assets/XML/GameText"

    def __init__(
        self, cache_dir: Optional[Path] = None, local_data_dir: Optional[Path] = None
    ):
        if cache_dir is None:
            cache_dir = Path.home() / ".history_idle" / "c2c_cache"
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        if local_data_dir is None:
            local_data_dir = Path(__file__).parent.parent.parent.parent / "data" / "c2c"
        self.local_data_dir = Path(local_data_dir)
        self.local_data_dir.mkdir(parents=True, exist_ok=True)

    def get_tech_xml(self) -> str:
        return self._get_cached_file(
            "Technologies/CIV4TechInfos.xml",
            f"{self.BASE_URL}/Technologies/CIV4TechInfos.xml",
        )

    def get_bonus_xml(self) -> str:
        return self._get_cached_file(
            "Terrain/CIV4BonusInfos.xml", f"{self.BASE_URL}/Terrain/CIV4BonusInfos.xml"
        )

    def get_building_xml(self) -> str:
        return self._get_cached_file(
            "Buildings/Regular_CIV4BuildingInfos.xml",
            f"{self.BASE_URL}/Buildings/Regular_CIV4BuildingInfos.xml",
        )

    def get_civilization_xml(self) -> str:
        return self._get_cached_file(
            "Civilizations/CIV4CivilizationInfos.xml",
            f"{self.BASE_URL}/Civilizations/CIV4CivilizationInfos.xml",
        )

    def get_terrain_xml(self) -> str:
        return self._get_cached_file(
            "Terrain/CIV4TerrainInfos.xml",
            f"{self.BASE_URL}/Terrain/CIV4TerrainInfos.xml",
        )

    def get_buildings_gametext_xml(self) -> str:
        return self._get_cached_file(
            "GameText/Buildings_CIV4GameText.xml",
            f"{self.GAMETEXT_BASE_URL}/Buildings_CIV4GameText.xml",
        )

    def get_technologies_gametext_xml(self) -> str:
        return self._get_cached_file(
            "GameText/Tech_CIV4GameText.xml",
            f"{self.GAMETEXT_BASE_URL}/Tech_CIV4GameText.xml",
        )

    def _get_cached_file(self, relative_path: str, url: str) -> str:
        local_path = self.local_data_dir / relative_path.replace("/", "_")
        cache_path = self.cache_dir / relative_path.replace("/", "_")

        if local_path.exists():
            print(f"Loading {relative_path} from local data...")
            with open(local_path, "r", encoding="utf-8") as f:
                return f.read()

        if cache_path.exists():
            print(f"Loading {relative_path} from cache...")
            with open(cache_path, "r", encoding="utf-8") as f:
                content = f.read()

            print("Copying to local data directory for offline access...")
            with open(local_path, "w", encoding="utf-8") as f:
                f.write(content)

            return content

        print(f"Downloading {relative_path} from GitHub...")
        try:
            with urllib.request.urlopen(url) as response:
                content = response.read().decode("utf-8")

            with open(cache_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"Cached to {cache_path}")

            with open(local_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"Saved to local data: {local_path}")

            return content

        except Exception as e:
            print(f"Error downloading {url}: {e}")
            print("Note: Game data not available offline. Please connect to download.")
            raise

    def clear_cache(self):
        import shutil

        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir)
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            print("Cache cleared")
