"""Civilization definition model from C2C data."""

from dataclasses import dataclass, field


@dataclass
class CivilizationDefinition:
    """Defines a civilization type with its characteristics."""
    id: str
    name: str
    city_names: list[str] = field(default_factory=list)
    leaders: list[str] = field(default_factory=list)
    derivative_civ: str = ""  # Parent civilization if any

    def __hash__(self):
        return hash(self.id)

    @staticmethod
    def format_city_name(text_key: str) -> str:
        """Convert a C2C text key to a readable city name.

        Example: TXT_KEY_CITY_NAME_WASHINGTON_DC -> Washington DC
        """
        if text_key.startswith("TXT_KEY_CITY_NAME_"):
            # Remove prefix
            name = text_key.replace("TXT_KEY_CITY_NAME_", "")
            # Replace underscores with spaces and title case
            name = name.replace("_", " ").title()
            return name
        return text_key

    def get_first_city_name(self) -> str:
        """Get the formatted name of the first city."""
        if self.city_names:
            return self.format_city_name(self.city_names[0])
        return "Capital"  # Fallback
