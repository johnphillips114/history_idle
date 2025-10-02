#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import json
import re
import sys

def clean_text_key(text):
    """Convert TXT_KEY_TECH_GATHERING to 'Gathering'"""
    if not text:
        return text
    text = re.sub(r'^TXT_KEY_TECH_', '', text)
    text = re.sub(r'^TXT_KEY_', '', text)
    text = re.sub(r'^TECH_', '', text)
    text = re.sub(r'^C2C_ERA_', '', text)
    text = re.sub(r'^ERA_', '', text)

    # Replace underscores with spaces
    text = text.replace('_', ' ')

    # Title case each word, but keep numbers uppercase
    words = []
    for word in text.split():
        # If word starts with a digit, uppercase it
        if word and word[0].isdigit():
            words.append(word.upper())
        else:
            words.append(word.capitalize())

    return ' '.join(words)

def get_json_key(tech_type):
    """Convert TECH_GATHERING to 'gathering'"""
    key = re.sub(r'^TECH_', '', tech_type)
    return key.lower()

def get_era_key(era_type):
    """Convert C2C_ERA_PREHISTORIC to 'paleolithic' etc."""
    if not era_type:
        return None

    era = re.sub(r'^C2C_ERA_', '', era_type)
    era = re.sub(r'^ERA_', '', era)

    # Map era names
    era_map = {
        'PREHISTORIC': 'paleolithic',
        'ANCIENT': 'neolithic',
        'CLASSICAL': 'classical',
        'MEDIEVAL': 'medieval',
        'RENAISSANCE': 'renaissance',
        'INDUSTRIAL': 'industrial',
        'MODERN': 'modern',
        'FUTURE': 'future',
        'BRONZE_AGE': 'bronze_age',
        'IRON_AGE': 'iron_age'
    }

    return era_map.get(era, era.lower())

def parse_game_text(xml_file):
    """Parse the GameText XML to extract English PEDIA and QUOTE descriptions"""
    tree = ET.parse(xml_file)
    root = tree.getroot()

    text_map = {}

    # Handle namespace
    namespace = ''
    if root.tag.startswith('{'):
        namespace = root.tag[root.tag.find('{'): root.tag.find('}') + 1]

    # Find all TEXT elements
    for text_elem in root.findall(f'.//{namespace}TEXT'):
        tag_elem = text_elem.find(f'{namespace}Tag')
        if tag_elem is None or not tag_elem.text:
            continue

        # Get the English text
        english_elem = text_elem.find(f'{namespace}English')
        if english_elem is not None and english_elem.text:
            # Clean up the text - remove color tags and other formatting
            text_value = english_elem.text
            # Remove various formatting tags
            text_value = re.sub(r'\[COLOR_[^\]]+\]', '', text_value)
            text_value = re.sub(r'\[/COLOR\]', '', text_value)
            text_value = re.sub(r'\[COLOR_REVERT\]', '', text_value)
            text_value = re.sub(r'\[BOLD\]', '', text_value)
            text_value = re.sub(r'\[\\BOLD\]', '', text_value)
            text_value = re.sub(r'\[\BOLD\]', '', text_value)
            text_value = re.sub(r'\[NEWLINE\]', ' ', text_value)
            text_value = re.sub(r'\[SPACE\]', ' ', text_value)
            text_value = re.sub(r'\[PARAGRAPH:\d+\]', ' ', text_value)
            # Clean up multiple spaces
            text_value = re.sub(r'\s+', ' ', text_value).strip()

            text_map[tag_elem.text] = text_value

    return text_map

def parse_technologies(xml_file, text_map):
    """Parse the technologies XML file and extract technology data"""
    tree = ET.parse(xml_file)
    root = tree.getroot()

    technologies = {}

    # Handle namespace
    namespace = ''
    if root.tag.startswith('{'):
        namespace = root.tag[root.tag.find('{'): root.tag.find('}') + 1]

    # Find all TechInfo elements
    for tech_info in root.findall(f'.//{namespace}TechInfo'):
        tech_type = tech_info.find(f'{namespace}Type')
        if tech_type is None:
            continue

        # Get the JSON key
        json_key = get_json_key(tech_type.text)

        # Get the technology name
        description = tech_info.find(f'{namespace}Description')
        if description is not None and description.text:
            tech_name = clean_text_key(description.text)
        else:
            tech_name = clean_text_key(tech_type.text)

        # Get quote from the game text file
        quote_elem = tech_info.find(f'{namespace}Quote')
        quote = None
        if quote_elem is not None and quote_elem.text:
            quote = text_map.get(quote_elem.text)

        # Get pedia from the game text file
        civilopedia_elem = tech_info.find(f'{namespace}Civilopedia')
        pedia = None
        if civilopedia_elem is not None and civilopedia_elem.text:
            pedia = text_map.get(civilopedia_elem.text)

        # Get research cost
        cost_elem = tech_info.find(f'{namespace}iCost')
        research_cost = int(cost_elem.text) if cost_elem is not None and cost_elem.text else 0

        # Get prerequisites from OrPreReqs
        prerequisites = []
        or_prereqs = tech_info.find(f'{namespace}OrPreReqs')
        if or_prereqs is not None:
            for prereq_tech in or_prereqs.findall(f'{namespace}PrereqTech'):
                if prereq_tech.text:
                    prereq_key = get_json_key(prereq_tech.text)
                    prerequisites.append(prereq_key)

        # Get era
        era_elem = tech_info.find(f'{namespace}Era')
        era = None
        if era_elem is not None and era_elem.text:
            era = get_era_key(era_elem.text)

        # Create the technology entry
        tech_data = {
            "name": tech_name,
            "quote": quote,
            "pedia": pedia,
            "research_cost": research_cost,
            "prerequisites": prerequisites,
            "era": era
        }

        technologies[json_key] = tech_data

    return technologies

if __name__ == '__main__':
    # Parse the game text file first
    print("Parsing game text file...", file=sys.stderr, flush=True)
    text_map = parse_game_text('data/c2c/GameText_Tech_CIV4GameText.xml')
    print(f"Found {len(text_map)} text entries", file=sys.stderr, flush=True)

    # Parse the technologies file
    print("Parsing technologies file...", file=sys.stderr, flush=True)
    technologies = parse_technologies('data/c2c/Technologies_CIV4TechInfos.xml', text_map)
    print(f"Converted {len(technologies)} technologies", file=sys.stderr, flush=True)

    # Print JSON output
    print(json.dumps(technologies, indent=2))
