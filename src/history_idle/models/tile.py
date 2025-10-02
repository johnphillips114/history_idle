from dataclasses import dataclass
from typing import Optional
from enum import Enum


class CultureLevel(Enum):
    """Culture levels and their thresholds"""
    NONE = 0
    POOR = 200
    FLEDGLING = 1300
    DEVELOPING = 5200
    REFINED = 20800
    INFLUENTIAL = 83200
    LEGENDARY = 332800
    ILLUSTRIOUS = 1331200
    PHENOMENAL = 5324800
    MONUMENTAL = 21299200

    @classmethod
    def get_level_for_culture(cls, culture: float) -> "CultureLevel":
        """Get the culture level for a given culture amount"""
        levels = sorted(cls, key=lambda x: x.value, reverse=True)
        for level in levels:
            if culture >= level.value:
                return level
        return cls.NONE

    @classmethod
    def get_next_level(cls, current_level: "CultureLevel") -> Optional["CultureLevel"]:
        """Get the next culture level after the current one"""
        levels = sorted(cls, key=lambda x: x.value)
        try:
            current_index = levels.index(current_level)
            if current_index < len(levels) - 1:
                return levels[current_index + 1]
        except ValueError:
            pass
        return None


@dataclass
class Tile:
    """Represents a tile in a city's territory"""
    terrain: "TerrainType"  # The terrain type of this tile
    resource: Optional["ResourceType"] = None  # Optional resource on this tile

    def __hash__(self):
        return hash((self.terrain.id, self.resource.id if self.resource else None))
