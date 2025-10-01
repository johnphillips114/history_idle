"""Resource model and related types."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ResourceCategory(Enum):
    """Categories of resources."""
    FOOD = "food"
    STRATEGIC = "strategic"
    LUXURY = "luxury"
    ABSTRACT = "abstract"


@dataclass
class ResourceType:
    """Defines a type of resource in the game."""
    id: str
    name: str
    category: ResourceCategory
    description: str = ""
    can_store: bool = True
    base_storage_cap: float = 100.0
    tech_reveal: Optional[str] = None  # Technology required to reveal this resource
    bonus_class: Optional[str] = None  # C2C bonus class (CROP, PRODUCTION, LUXURY, etc.)

    def __hash__(self):
        return hash(self.id)


@dataclass
class ResourceQuantity:
    """Represents an amount of a specific resource."""
    resource_type: ResourceType
    amount: float = 0.0
    capacity: float = 100.0
    production_rate: float = 0.0
    consumption_rate: float = 0.0

    @property
    def net_rate(self) -> float:
        """Net production rate (production - consumption)."""
        return self.production_rate - self.consumption_rate

    @property
    def is_full(self) -> bool:
        """Check if resource is at capacity."""
        return self.amount >= self.capacity

    @property
    def is_empty(self) -> bool:
        """Check if resource is depleted."""
        return self.amount <= 0

    @property
    def fill_percentage(self) -> float:
        """Percentage of capacity filled (0.0 to 1.0)."""
        if self.capacity <= 0:
            return 0.0
        return min(1.0, self.amount / self.capacity)

    def add(self, amount: float) -> float:
        """Add resources, respecting capacity. Returns amount actually added."""
        if amount <= 0:
            return 0.0

        space_available = self.capacity - self.amount
        amount_to_add = min(amount, space_available)
        self.amount += amount_to_add
        return amount_to_add

    def remove(self, amount: float) -> float:
        """Remove resources. Returns amount actually removed."""
        if amount <= 0:
            return 0.0

        amount_to_remove = min(amount, self.amount)
        self.amount -= amount_to_remove
        return amount_to_remove

    def can_afford(self, amount: float) -> bool:
        """Check if there are enough resources available."""
        return self.amount >= amount

    def update(self, delta_time: float) -> None:
        """Update resource amount based on production/consumption rates.

        Args:
            delta_time: Time elapsed in seconds.
        """
        change = self.net_rate * delta_time
        if change > 0:
            self.add(change)
        elif change < 0:
            self.remove(abs(change))


@dataclass
class ResourceStorage:
    """Manages multiple resource quantities."""
    resources: dict[str, ResourceQuantity] = field(default_factory=dict)

    def add_resource_type(self, resource_type: ResourceType, initial_amount: float = 0.0) -> None:
        """Add a new resource type to storage."""
        if resource_type.id not in self.resources:
            # Use base_storage_cap, even if can_store=False (e.g., production has 0 cap)
            self.resources[resource_type.id] = ResourceQuantity(
                resource_type=resource_type,
                amount=initial_amount,
                capacity=resource_type.base_storage_cap
            )

    def get(self, resource_id: str) -> Optional[ResourceQuantity]:
        """Get a resource quantity by ID."""
        return self.resources.get(resource_id)

    def has_resource(self, resource_id: str, amount: float) -> bool:
        """Check if storage has at least the specified amount of a resource."""
        resource = self.get(resource_id)
        return resource is not None and resource.can_afford(amount)

    def add_amount(self, resource_id: str, amount: float) -> float:
        """Add amount to a resource. Returns amount actually added."""
        resource = self.get(resource_id)
        if resource is None:
            return 0.0
        return resource.add(amount)

    def remove_amount(self, resource_id: str, amount: float) -> float:
        """Remove amount from a resource. Returns amount actually removed."""
        resource = self.get(resource_id)
        if resource is None:
            return 0.0
        return resource.remove(amount)

    def update_all(self, delta_time: float) -> None:
        """Update all resources based on their production/consumption rates."""
        for resource in self.resources.values():
            resource.update(delta_time)
