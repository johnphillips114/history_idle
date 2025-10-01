from dataclasses import dataclass


@dataclass
class TerrainType:
    id: str
    name: str
    description: str
    can_found: bool  # Whether cities can be founded on this terrain
    food_yield: float = 0.0  # Food per second bonus
    production_yield: float = 0.0  # Production per second bonus
    currency_yield: float = 0.0  # Currency per second bonus

    def __hash__(self):
        return hash(self.id)
