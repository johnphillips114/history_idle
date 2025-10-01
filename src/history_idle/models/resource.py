from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ResourceCategory(Enum):
    FOOD = "food"
    STRATEGIC = "strategic"
    LUXURY = "luxury"
    ABSTRACT = "abstract"


@dataclass
class ResourceType:
    id: str
    name: str
    category: ResourceCategory
    description: str = ""
    can_store: bool = True
    base_storage_cap: float = 100.0
    tech_reveal: Optional[str] = None  # Technology required to reveal this resource
    bonus_class: Optional[str] = (
        None  # C2C bonus class (CROP, PRODUCTION, LUXURY, etc.)
    )
    compatible_terrains: list[str] = field(default_factory=list)  # Terrain IDs where this resource can appear

    def __hash__(self):
        return hash(self.id)


@dataclass
class ResourceQuantity:
    resource_type: ResourceType
    amount: float = 0.0
    capacity: float = 100.0
    production_rate: float = 0.0
    consumption_rate: float = 0.0

    @property
    def net_rate(self) -> float:
        return self.production_rate - self.consumption_rate

    @property
    def is_full(self) -> bool:
        return self.amount >= self.capacity

    @property
    def is_empty(self) -> bool:
        return self.amount <= 0

    @property
    def fill_percentage(self) -> float:
        if self.capacity <= 0:
            return 0.0
        return min(1.0, self.amount / self.capacity)

    def add(self, amount: float) -> float:
        if amount <= 0:
            return 0.0

        space_available = self.capacity - self.amount
        amount_to_add = min(amount, space_available)
        self.amount += amount_to_add
        return amount_to_add

    def remove(self, amount: float) -> float:
        if amount <= 0:
            return 0.0

        amount_to_remove = min(amount, self.amount)
        self.amount -= amount_to_remove
        return amount_to_remove

    def can_afford(self, amount: float) -> bool:
        return self.amount >= amount

    def update(self, delta_time: float) -> None:
        change = self.net_rate * delta_time
        if change > 0:
            self.add(change)
        elif change < 0:
            self.remove(abs(change))


@dataclass
class ResourceStorage:
    resources: dict[str, ResourceQuantity] = field(default_factory=dict)

    def add_resource_type(
        self, resource_type: ResourceType, initial_amount: float = 0.0
    ) -> None:
        if resource_type.id not in self.resources:
            self.resources[resource_type.id] = ResourceQuantity(
                resource_type=resource_type,
                amount=initial_amount,
                capacity=resource_type.base_storage_cap,
            )

    def get(self, resource_id: str) -> Optional[ResourceQuantity]:
        return self.resources.get(resource_id)

    def has_resource(self, resource_id: str, amount: float) -> bool:
        resource = self.get(resource_id)
        return resource is not None and resource.can_afford(amount)

    def add_amount(self, resource_id: str, amount: float) -> float:
        resource = self.get(resource_id)
        if resource is None:
            return 0.0
        return resource.add(amount)

    def remove_amount(self, resource_id: str, amount: float) -> float:
        resource = self.get(resource_id)
        if resource is None:
            return 0.0
        return resource.remove(amount)

    def update_all(self, delta_time: float) -> None:
        for resource in self.resources.values():
            resource.update(delta_time)
