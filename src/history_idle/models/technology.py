from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class TechCategory(Enum):
    MILITARY = "military"
    ECONOMIC = "economic"
    CULTURAL = "cultural"
    SCIENTIFIC = "scientific"
    CIVIC = "civic"


class Era(Enum):
    PALEOLITHIC = "paleolithic"
    NEOLITHIC = "neolithic"
    BRONZE = "bronze"
    IRON = "iron"
    CLASSICAL = "classical"
    MEDIEVAL = "medieval"
    RENAISSANCE = "renaissance"
    INDUSTRIAL = "industrial"
    MODERN = "modern"
    FUTURE = "future"


@dataclass
class TechnologyDefinition:
    id: str
    name: str
    description: str
    era: Era
    category: TechCategory
    research_cost: float
    quote: Optional[str] = None
    pedia: Optional[str] = None
    prerequisites: list[str] = field(default_factory=list)
    unlocks_buildings: list[str] = field(default_factory=list)
    unlocks_resources: list[str] = field(default_factory=list)
    effects: dict[str, float] = field(default_factory=dict)

    def __hash__(self):
        return hash(self.id)


@dataclass
class TechnologyProgress:
    tech_def: TechnologyDefinition
    research_points: float = 0.0
    is_completed: bool = False

    @property
    def progress_percentage(self) -> float:
        if self.tech_def.research_cost <= 0:
            return 1.0
        return min(1.0, self.research_points / self.tech_def.research_cost)

    @property
    def remaining_cost(self) -> float:
        return max(0.0, self.tech_def.research_cost - self.research_points)

    def add_research(self, points: float) -> bool:
        if self.is_completed:
            return True

        self.research_points += points
        if self.research_points >= self.tech_def.research_cost:
            self.is_completed = True
            return True
        return False


@dataclass
class TechTree:
    technologies: dict[str, TechnologyDefinition] = field(default_factory=dict)
    researched: set[str] = field(default_factory=set)
    current_research: Optional[TechnologyProgress] = None
    research_queue: list[str] = field(default_factory=list)

    def add_technology(self, tech: TechnologyDefinition) -> None:
        self.technologies[tech.id] = tech

    def get_technology(self, tech_id: str) -> Optional[TechnologyDefinition]:
        return self.technologies.get(tech_id)

    def is_researched(self, tech_id: str) -> bool:
        return tech_id in self.researched

    def can_research(self, tech_id: str) -> bool:
        tech = self.get_technology(tech_id)
        if tech is None or self.is_researched(tech_id):
            return False

        for prereq in tech.prerequisites:
            if not self.is_researched(prereq):
                return False

        return True

    def get_available_technologies(self) -> list[TechnologyDefinition]:
        available = []
        for tech in self.technologies.values():
            if self.can_research(tech.id):
                available.append(tech)
        return available

    def start_research(self, tech_id: str) -> bool:
        if not self.can_research(tech_id):
            return False

        tech = self.get_technology(tech_id)
        if tech is None:
            return False

        self.current_research = TechnologyProgress(tech_def=tech)
        return True

    def add_research_points(self, points: float) -> Optional[TechnologyDefinition]:
        if self.current_research is None:
            return None

        if self.current_research.add_research(points):
            completed_tech = self.current_research.tech_def
            self.researched.add(completed_tech.id)

            if self.research_queue:
                next_tech_id = self.research_queue.pop(0)
                if self.can_research(next_tech_id):
                    self.start_research(next_tech_id)
                else:
                    self.current_research = None
            else:
                self.current_research = None

            return completed_tech

        return None

    def get_technologies_by_era(self, era: Era) -> list[TechnologyDefinition]:
        return [tech for tech in self.technologies.values() if tech.era == era]
