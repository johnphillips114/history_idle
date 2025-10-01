import xml.etree.ElementTree as ET
from ..models import (
    ResourceType,
    ResourceCategory,
    TechnologyDefinition,
    TechCategory,
    Era,
    BuildingDefinition,
    BuildingCategory,
    ResourceCost,
    CivilizationDefinition,
    TerrainType,
)


class C2CDataParser:
    @staticmethod
    def parse_bonuses_xml(xml_content: str) -> list[ResourceType]:
        resources = []

        try:
            import re

            xml_content = re.sub(r' xmlns="[^"]+"', "", xml_content)
            root = ET.fromstring(xml_content)

            for bonus_info in root.findall(".//BonusInfo"):
                resource_id = None
                name = None
                description = ""
                tech_reveal = None
                bonus_class = None
                compatible_terrains = []

                type_elem = bonus_info.find("Type")
                if type_elem is not None and type_elem.text:
                    resource_id = type_elem.text.replace("BONUS_", "").lower()

                desc_elem = bonus_info.find("Description")
                if desc_elem is not None and desc_elem.text:
                    name = (
                        desc_elem.text.replace("TXT_KEY_BONUS_", "")
                        .replace("_", " ")
                        .title()
                    )

                help_elem = bonus_info.find("Help")
                if help_elem is not None and help_elem.text:
                    description = help_elem.text

                tech_reveal_elem = bonus_info.find("TechReveal")
                if tech_reveal_elem is not None and tech_reveal_elem.text:
                    tech_reveal = tech_reveal_elem.text.replace("TECH_", "").lower()

                bonus_class_elem = bonus_info.find("BonusClassType")
                if bonus_class_elem is not None and bonus_class_elem.text:
                    bonus_class = bonus_class_elem.text.replace(
                        "BONUSCLASS_", ""
                    ).lower()

                # Extract terrain compatibility
                terrain_booleans_elem = bonus_info.find("TerrainBooleans")
                if terrain_booleans_elem is not None:
                    for terrain_boolean in terrain_booleans_elem.findall("TerrainBoolean"):
                        terrain_type_elem = terrain_boolean.find("TerrainType")
                        b_terrain_elem = terrain_boolean.find("bTerrain")
                        if (terrain_type_elem is not None and terrain_type_elem.text and
                            b_terrain_elem is not None and b_terrain_elem.text == "1"):
                            terrain_id = terrain_type_elem.text.replace("TERRAIN_", "").lower()
                            compatible_terrains.append(terrain_id)

                if resource_id and name:
                    category = C2CDataParser._categorize_resource(resource_id, name)

                    resource = ResourceType(
                        id=resource_id,
                        name=name,
                        category=category,
                        description=description,
                        can_store=True,
                        base_storage_cap=100.0,
                        tech_reveal=tech_reveal,
                        bonus_class=bonus_class,
                        compatible_terrains=compatible_terrains,
                    )
                    resources.append(resource)

        except ET.ParseError as e:
            print(f"Error parsing bonuses XML: {e}")

        return resources

    @staticmethod
    def parse_technologies_xml(xml_content: str) -> list[TechnologyDefinition]:
        technologies = []

        try:
            import re

            xml_content = re.sub(r' xmlns="[^"]+"', "", xml_content)
            root = ET.fromstring(xml_content)

            for tech_info in root.findall(".//TechInfo"):
                tech_id = None
                name = None
                description = ""
                era = Era.PALEOLITHIC
                prerequisites = []
                research_cost = 100.0

                type_elem = tech_info.find("Type")
                if type_elem is not None and type_elem.text:
                    tech_id = type_elem.text.replace("TECH_", "").lower()

                desc_elem = tech_info.find("Description")
                if desc_elem is not None and desc_elem.text:
                    name = (
                        desc_elem.text.replace("TXT_KEY_TECH_", "")
                        .replace("_", " ")
                        .title()
                    )
                else:
                    name = tech_id.replace("_", " ").title() if tech_id else "Unknown"

                civ_elem = tech_info.find("Civilopedia")
                if civ_elem is not None and civ_elem.text:
                    description = civ_elem.text.replace("TXT_KEY_TECH_", "").replace(
                        "_PEDIA", ""
                    )

                era_elem = tech_info.find("Era")
                if era_elem is not None and era_elem.text:
                    era = C2CDataParser._map_era(era_elem.text)

                cost_elem = tech_info.find("iCost")
                if cost_elem is not None and cost_elem.text:
                    try:
                        research_cost = float(cost_elem.text)
                    except ValueError:
                        research_cost = 100.0

                and_prereqs_elem = tech_info.find("AndPreReqs")
                if and_prereqs_elem is not None:
                    for prereq in and_prereqs_elem.findall("PrereqTech"):
                        if prereq.text:
                            prereq_id = prereq.text.replace("TECH_", "").lower()
                            prerequisites.append(prereq_id)

                or_prereqs_elem = tech_info.find("OrPreReqs")
                if or_prereqs_elem is not None:
                    for prereq in or_prereqs_elem.findall("PrereqTech"):
                        if prereq.text:
                            prereq_id = prereq.text.replace("TECH_", "").lower()
                            if prereq_id not in prerequisites:
                                prerequisites.append(prereq_id)
                                break  # Only take first OR prereq for simplicity

                if tech_id and name:
                    tech = TechnologyDefinition(
                        id=tech_id,
                        name=name,
                        description=description,
                        era=era,
                        category=TechCategory.SCIENTIFIC,  # Default category
                        research_cost=research_cost,
                        prerequisites=prerequisites,
                    )
                    technologies.append(tech)

        except ET.ParseError as e:
            print(f"Error parsing technologies XML: {e}")
        except Exception as e:
            print(f"Unexpected error parsing technologies: {e}")

        return technologies

    @staticmethod
    def parse_buildings_xml(xml_content: str) -> list[BuildingDefinition]:
        buildings = []

        try:
            import re

            xml_content = re.sub(r' xmlns="[^"]+"', "", xml_content)
            root = ET.fromstring(xml_content)

            for building_info in root.findall(".//BuildingInfo"):
                building_id = None
                name = None
                description = ""
                construction_costs = []
                required_tech = None
                required_resources = []
                required_buildings = []
                effects = {}
                construction_time = 0.0
                vicinity_bonus = None
                prereq_or_terrain = []

                type_elem = building_info.find("Type")
                if type_elem is not None and type_elem.text:
                    building_id = type_elem.text.replace("BUILDING_", "").lower()

                desc_elem = building_info.find("Description")
                if desc_elem is not None and desc_elem.text:
                    name = (
                        desc_elem.text.replace("TXT_KEY_BUILDING_", "")
                        .replace("_", " ")
                        .title()
                    )
                else:
                    name = (
                        building_id.replace("_", " ").title()
                        if building_id
                        else "Unknown"
                    )

                civ_elem = building_info.find("Civilopedia")
                if civ_elem is not None and civ_elem.text:
                    description = civ_elem.text.replace(
                        "TXT_KEY_BUILDING_", ""
                    ).replace("_PEDIA", "")

                prereq_religion = building_info.find("PrereqReligion")
                if prereq_religion is not None and prereq_religion.text:
                    continue

                tech_elem = building_info.find("PrereqTech")
                if tech_elem is not None and tech_elem.text:
                    required_tech = tech_elem.text.replace("TECH_", "").lower()

                cost_elem = building_info.find("iCost")
                if cost_elem is not None and cost_elem.text:
                    try:
                        cost_value = float(cost_elem.text)
                        construction_costs.append(
                            ResourceCost("production", cost_value)
                        )
                        construction_time = cost_value
                    except ValueError:
                        construction_time = 100.0

                prereq_bonuses = building_info.find("PrereqBonuses")
                if prereq_bonuses is not None:
                    for bonus in prereq_bonuses.findall("Bonus"):
                        if bonus.text:
                            resource_id = bonus.text.replace("BONUS_", "").lower()
                            required_resources.append(resource_id)

                prereq_buildings_elem = building_info.find("PrereqInCityBuildings")
                if prereq_buildings_elem is not None:
                    for building in prereq_buildings_elem.findall("BuildingType"):
                        if building.text:
                            req_building_id = building.text.replace(
                                "BUILDING_", ""
                            ).lower()
                            required_buildings.append(req_building_id)

                yield_mods = building_info.find("YieldModifiers")
                if yield_mods is not None:
                    yields = yield_mods.findall("iYield")
                    if len(yields) > 1 and yields[1].text:
                        try:
                            production_bonus = float(yields[1].text)
                            if production_bonus > 0:
                                effects["production_bonus"] = production_bonus
                        except (ValueError, IndexError):
                            pass

                commerce_changes = building_info.find("CommerceChanges")
                if commerce_changes is not None:
                    commerces = commerce_changes.findall("iCommerce")
                    if commerces and commerces[0].text:
                        try:
                            research_bonus = float(commerces[0].text)
                            if research_bonus > 0:
                                effects["research_bonus"] = research_bonus
                        except (ValueError, IndexError):
                            pass

                specialist_counts = building_info.find("SpecialistCounts")
                if specialist_counts is not None:
                    total_specialists = 0
                    for spec in specialist_counts.findall("SpecialistCount"):
                        count_elem = spec.find("iSpecialistCount")
                        if count_elem is not None and count_elem.text:
                            try:
                                total_specialists += int(count_elem.text)
                            except ValueError:
                                pass
                    if total_specialists > 0:
                        effects["housing"] = float(total_specialists)

                flavors = {}
                flavors_elem = building_info.find("Flavors")
                if flavors_elem is not None:
                    for flavor in flavors_elem.findall("Flavor"):
                        flavor_type_elem = flavor.find("FlavorType")
                        flavor_value_elem = flavor.find("iFlavor")

                        if (
                            flavor_type_elem is not None
                            and flavor_value_elem is not None
                        ):
                            if flavor_type_elem.text and flavor_value_elem.text:
                                try:
                                    flavor_type = flavor_type_elem.text.replace(
                                        "FLAVOR_", ""
                                    ).lower()
                                    flavor_value = int(flavor_value_elem.text)
                                    flavors[flavor_type] = flavor_value
                                except ValueError:
                                    pass

                # Parse vicinity bonus (resource required in city)
                vicinity_elem = building_info.find("VicinityBonus")
                if vicinity_elem is not None and vicinity_elem.text:
                    vicinity_bonus = vicinity_elem.text.replace("BONUS_", "").lower()

                # Parse terrain requirements (city must be on one of these terrains)
                prereq_or_terrain_elem = building_info.find("PrereqOrTerrain")
                if prereq_or_terrain_elem is not None:
                    for prereq_terrain in prereq_or_terrain_elem.findall("PrereqTerrain"):
                        terrain_type_elem = prereq_terrain.find("TerrainType")
                        if terrain_type_elem is not None and terrain_type_elem.text:
                            terrain_id = terrain_type_elem.text.replace("TERRAIN_", "").lower()
                            prereq_or_terrain.append(terrain_id)

                # Hardcoded housing effects for specific buildings
                if building_id == "cave_shelter":
                    effects["housing"] = 5.0

                if building_id and name:
                    category = C2CDataParser._categorize_building(building_id, effects)

                    building = BuildingDefinition(
                        id=building_id,
                        name=name,
                        description=description,
                        category=category,
                        construction_costs=construction_costs,
                        construction_time=construction_time,
                        required_tech=required_tech,
                        required_resources=required_resources,
                        required_buildings=required_buildings,
                        effects=effects,
                        flavors=flavors,
                        vicinity_bonus=vicinity_bonus,
                        prereq_or_terrain=prereq_or_terrain,
                    )
                    buildings.append(building)

        except ET.ParseError as e:
            print(f"Error parsing buildings XML: {e}")
        except Exception as e:
            print(f"Unexpected error parsing buildings: {e}")

        return buildings

    @staticmethod
    def _categorize_building(building_id: str, effects: dict) -> BuildingCategory:
        lower_id = building_id.lower()

        if "production_bonus" in effects:
            return BuildingCategory.PRODUCTION
        elif "research_bonus" in effects:
            return BuildingCategory.RESEARCH
        elif "housing" in effects:
            return BuildingCategory.HOUSING

        if any(word in lower_id for word in ["factory", "mill", "workshop", "forge"]):
            return BuildingCategory.PRODUCTION
        elif any(
            word in lower_id
            for word in ["library", "university", "laboratory", "academy"]
        ):
            return BuildingCategory.RESEARCH
        elif any(word in lower_id for word in ["granary", "warehouse", "silo"]):
            return BuildingCategory.STORAGE
        elif any(
            word in lower_id for word in ["barracks", "fortress", "walls", "castle"]
        ):
            return BuildingCategory.MILITARY
        elif any(
            word in lower_id for word in ["temple", "theater", "monument", "museum"]
        ):
            return BuildingCategory.CULTURAL
        elif any(word in lower_id for word in ["house", "apartment", "shelter"]):
            return BuildingCategory.HOUSING
        elif any(word in lower_id for word in ["park", "garden", "bath", "colosseum"]):
            return BuildingCategory.AMENITY

        return BuildingCategory.INFRASTRUCTURE

    @staticmethod
    def _categorize_resource(resource_id: str, name: str) -> ResourceCategory:
        food_keywords = ["food", "grain", "wheat", "fish", "meat", "fruit", "vegetable"]
        luxury_keywords = [
            "gold",
            "silver",
            "gem",
            "diamond",
            "spice",
            "silk",
            "dye",
            "incense",
        ]

        lower_id = resource_id.lower()
        lower_name = name.lower()

        for keyword in food_keywords:
            if keyword in lower_id or keyword in lower_name:
                return ResourceCategory.FOOD

        for keyword in luxury_keywords:
            if keyword in lower_id or keyword in lower_name:
                return ResourceCategory.LUXURY

        return ResourceCategory.STRATEGIC

    @staticmethod
    def _map_era(era_text: str) -> Era:
        era_mapping = {
            "C2C_ERA_PREHISTORIC": Era.PALEOLITHIC,
            "C2C_ERA_EARLY_ANCIENT": Era.NEOLITHIC,
            "C2C_ERA_ANCIENT": Era.BRONZE,
            "C2C_ERA_CLASSICAL": Era.CLASSICAL,
            "C2C_ERA_MEDIEVAL": Era.MEDIEVAL,
            "C2C_ERA_RENAISSANCE": Era.RENAISSANCE,
            "C2C_ERA_INDUSTRIAL": Era.INDUSTRIAL,
            "C2C_ERA_MODERN": Era.MODERN,
            "C2C_ERA_FUTURE": Era.FUTURE,
            # Fallbacks for old format
            "ERA_PREHISTORIC": Era.PALEOLITHIC,
            "ERA_ANCIENT": Era.BRONZE,
            "ERA_CLASSICAL": Era.CLASSICAL,
            "ERA_MEDIEVAL": Era.MEDIEVAL,
            "ERA_RENAISSANCE": Era.RENAISSANCE,
            "ERA_INDUSTRIAL": Era.INDUSTRIAL,
            "ERA_MODERN": Era.MODERN,
            "ERA_FUTURE": Era.FUTURE,
        }

        return era_mapping.get(era_text, Era.PALEOLITHIC)

    @staticmethod
    def parse_civilizations_xml(xml_content: str) -> list[CivilizationDefinition]:
        civilizations = []

        try:
            import re

            xml_content = re.sub(r' xmlns="[^"]+"', "", xml_content)
            root = ET.fromstring(xml_content)

            for civ_info in root.findall(".//CivilizationInfo"):
                civ_id = None
                name = None
                city_names = []
                leaders = []
                derivative_civ = ""

                type_elem = civ_info.find("Type")
                if type_elem is not None and type_elem.text:
                    civ_id = type_elem.text.replace("CIVILIZATION_", "").lower()

                desc_elem = civ_info.find("Description")
                if desc_elem is not None and desc_elem.text:
                    name = (
                        desc_elem.text.replace("TXT_KEY_CIVILIZATION_", "")
                        .replace("_", " ")
                        .title()
                    )

                cities_elem = civ_info.find("Cities")
                if cities_elem is not None:
                    for city_elem in cities_elem.findall("City"):
                        if city_elem.text:
                            city_names.append(city_elem.text)

                leaders_elem = civ_info.find("Leaders")
                if leaders_elem is not None:
                    for leader_elem in leaders_elem.findall(".//LeaderName"):
                        if leader_elem.text:
                            leaders.append(
                                leader_elem.text.replace("LEADER_", "").lower()
                            )

                derivative_elem = civ_info.find("DerivativeCiv")
                if derivative_elem is not None and derivative_elem.text:
                    derivative_civ = derivative_elem.text.replace(
                        "CIVILIZATION_", ""
                    ).lower()

                if civ_id and name:
                    civilization = CivilizationDefinition(
                        id=civ_id,
                        name=name,
                        city_names=city_names,
                        leaders=leaders,
                        derivative_civ=derivative_civ,
                    )
                    civilizations.append(civilization)

        except Exception as e:
            print(f"Error parsing civilizations XML: {e}")

        return civilizations

    @staticmethod
    def parse_gametext_xml(xml_content: str) -> dict[str, str]:
        """Parse GameText XML and return a mapping of Tag -> English text"""
        text_map = {}

        try:
            import re

            xml_content = re.sub(r' xmlns="[^"]+"', "", xml_content)
            root = ET.fromstring(xml_content)

            for text_elem in root.findall(".//TEXT"):
                tag_elem = text_elem.find("Tag")
                english_elem = text_elem.find("English")

                if tag_elem is not None and tag_elem.text:
                    if english_elem is not None and english_elem.text:
                        text_map[tag_elem.text] = english_elem.text

        except Exception as e:
            print(f"Error parsing GameText XML: {e}")

        return text_map

    @staticmethod
    def parse_terrains_xml(xml_content: str) -> list[TerrainType]:
        terrains = []

        try:
            import re

            xml_content = re.sub(r' xmlns="[^"]+"', "", xml_content)
            root = ET.fromstring(xml_content)

            # Track when we're in the valid range
            in_valid_range = False

            for terrain_info in root.findall(".//TerrainInfo"):
                terrain_id = None
                name = None
                description = ""
                can_found = False
                food_yield = 0.0
                production_yield = 0.0
                currency_yield = 0.0

                type_elem = terrain_info.find("Type")
                if type_elem is not None and type_elem.text:
                    terrain_id = type_elem.text.replace("TERRAIN_", "").lower()

                    # Check if we're entering or exiting the valid range
                    if terrain_id == "grassland":
                        in_valid_range = True
                    elif terrain_id == "muddy":
                        in_valid_range = True  # Include muddy
                    elif in_valid_range and terrain_id not in ["grassland", "lush", "plains", "rocky", "barren", "tundra", "marsh", "cold_marsh", "scrub", "desert", "dunes", "salt_flats", "muddy"]:
                        in_valid_range = False

                desc_elem = terrain_info.find("Description")
                if desc_elem is not None and desc_elem.text:
                    name = (
                        desc_elem.text.replace("TXT_KEY_TERRAIN_", "")
                        .replace("_", " ")
                        .title()
                    )

                civ_elem = terrain_info.find("Civilopedia")
                if civ_elem is not None and civ_elem.text:
                    description = civ_elem.text

                # Check if cities can be founded here
                found_elem = terrain_info.find("bFound")
                if found_elem is not None and found_elem.text == "1":
                    can_found = True

                # Parse yields (order: food, production, currency)
                yields_elem = terrain_info.find("Yields")
                if yields_elem is not None:
                    yield_values = yields_elem.findall("iYield")
                    if len(yield_values) > 0 and yield_values[0].text:
                        try:
                            food_yield = float(yield_values[0].text)
                        except ValueError:
                            pass
                    if len(yield_values) > 1 and yield_values[1].text:
                        try:
                            production_yield = float(yield_values[1].text)
                        except ValueError:
                            pass
                    if len(yield_values) > 2 and yield_values[2].text:
                        try:
                            currency_yield = float(yield_values[2].text)
                        except ValueError:
                            pass

                if terrain_id and name and in_valid_range and can_found:
                    terrain = TerrainType(
                        id=terrain_id,
                        name=name,
                        description=description,
                        can_found=can_found,
                        food_yield=food_yield,
                        production_yield=production_yield,
                        currency_yield=currency_yield,
                    )
                    terrains.append(terrain)

        except ET.ParseError as e:
            print(f"Error parsing terrains XML: {e}")
        except Exception as e:
            print(f"Unexpected error parsing terrains: {e}")

        return terrains
