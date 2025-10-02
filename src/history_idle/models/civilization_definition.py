from dataclasses import dataclass, field


@dataclass
class CivilizationDefinition:
    id: str
    name: str
    city_names: list[str] = field(default_factory=list)
    leaders: list[str] = field(default_factory=list)
    derivative_civ: str = ""  # Parent civilization if any

    def __hash__(self):
        return hash(self.id)

    @staticmethod
    def format_city_name(text_key: str) -> str:
        if text_key.startswith("TXT_KEY_CITY_NAME_"):
            name = text_key.replace("TXT_KEY_CITY_NAME_", "")
            name = name.replace("_", " ").title()
            return name
        return text_key

    def get_first_city_name(self) -> str:
        if self.city_names:
            return self.format_city_name(self.city_names[0])
        return "Capital"  # Fallback
