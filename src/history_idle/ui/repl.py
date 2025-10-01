"""REPL interface for History Idle game."""

import time
import sys
import os
import select
import tty
import termios
from typing import Optional
from ..models import Civilization, WorkforceTask
from ..systems.game_loop import GameLoop
from ..utils.save_system import SaveSystem


class GameREPL:
    """Interactive REPL interface for the game."""

    def __init__(self, civilization: Civilization, game_loop: GameLoop, save_system: SaveSystem, game_data_manager=None):
        self.civilization = civilization
        self.game_loop = game_loop
        self.save_system = save_system
        self.game_data = game_data_manager
        self.running = True
        self.last_display_time = time.time()
        self.debug_mode = False

        # Track resource states for notifications
        self.last_resource_states = {}

        # Terminal settings (for Unix-like systems)
        self.old_terminal_settings = None

        # Command mapping
        self.commands = {
            'help': self.cmd_help,
            'h': self.cmd_help,
            'resources': self.cmd_resources,
            'res': self.cmd_resources,
            'available': self.cmd_available_resources,
            'avail': self.cmd_available_resources,
            'population': self.cmd_population,
            'pop': self.cmd_population,
            'allocate': self.cmd_allocate,
            'alloc': self.cmd_allocate,
            'deallocate': self.cmd_deallocate,
            'dealloc': self.cmd_deallocate,
            'technologies': self.cmd_technologies,
            'tech': self.cmd_technologies,
            'research': self.cmd_research,
            'buildings': self.cmd_buildings,
            'build': self.cmd_build,
            'cities': self.cmd_cities,
            'switch': self.cmd_switch_city,
            'found': self.cmd_found_city,
            'status': self.cmd_status,
            'save': self.cmd_save,
            'quit': self.cmd_quit,
            'exit': self.cmd_quit,
            'q': self.cmd_quit,
            'debug': self.cmd_debug,
        }

    def clear_screen(self):
        """Clear the terminal screen."""
        os.system('clear' if os.name != 'nt' else 'cls')

    def display_status(self):
        """Display current civilization status (persistent UI)."""
        print("=" * 60)
        print("HISTORY IDLE")
        print("=" * 60)

        # Get active city
        active_city = self.civilization.get_active_city()
        city_name = active_city.name if active_city else "None"
        num_cities = len(self.civilization.cities)
        city_display = f"{city_name} ({num_cities} {'city' if num_cities == 1 else 'cities'})"

        print(f"Civilization: {self.civilization.name} | Era: {self.civilization.current_era.value.title()}")
        print(f"City: {city_display} | Settlers Ready: {self.civilization.ready_settlers}")

        if not active_city:
            print("No active city!")
            return

        # Population summary
        pop = active_city.population
        print(f"Population: {pop.total} (Idle: {pop.idle_workers}, Working: {pop.allocated_workers})")

        # Key resources summary (food, research, production rate) - city resources
        total_food = active_city.get_total_food_from_crops()
        food_rate = sum(r.net_rate for r in active_city.resources.resources.values()
                       if hasattr(r.resource_type, 'bonus_class') and r.resource_type.bonus_class == 'crop')

        # Research is civilization-wide
        research_res = self.civilization.resources.get("research")
        research_str = f"{research_res.amount:.1f}" if research_res else "0.0"
        research_rate_str = f"{research_res.net_rate:+.1f}/s" if research_res and research_res.net_rate != 0 else ""

        # Production is per-city
        production_res = active_city.resources.get("production")
        production_rate_str = f"{production_res.production_rate:.1f}/s" if production_res and production_res.production_rate > 0 else "0.0/s"

        print(f"Food: {total_food:.1f} [{food_rate:+.1f}/s] | Research: {research_str} {research_rate_str} | Production: {production_rate_str}")

        # Current research
        if self.civilization.tech_tree.current_research:
            current = self.civilization.tech_tree.current_research
            progress = current.progress_percentage * 100
            print(f"Researching: {current.tech_def.name} ({progress:.0f}%)")

        # Buildings under construction
        if self.civilization.buildings.under_construction:
            construction = self.civilization.buildings.under_construction[0]
            progress = construction.progress_percentage * 100
            print(f"Building: {construction.building_def.name} ({progress:.0f}%)")

        print("=" * 60)

    def start(self):
        """Start the REPL loop."""
        self.clear_screen()
        self.display_status()
        print("\nType 'help' for available commands.")
        self.game_loop.start()

        # Set terminal to raw mode on Unix for character-by-character input
        if sys.platform != 'win32' and sys.stdin.isatty():
            try:
                self.old_terminal_settings = termios.tcgetattr(sys.stdin)
                tty.setcbreak(sys.stdin.fileno())
            except:
                pass  # Fall back to line mode if raw mode fails

        # Input buffer for accumulating typed characters
        input_buffer = ""

        # Show initial prompt
        print("\n> ", end='', flush=True)

        try:
            while self.running:
                try:
                    # Auto-update every second
                    current_time = time.time()
                    if current_time - self.last_display_time > 1.0:
                        update = self.game_loop.tick()
                        self.last_display_time = current_time

                        # Check for notifications
                        notifications = []
                        if update.get('completed_techs'):
                            for tech_name in update['completed_techs']:
                                notifications.append(f"🎓 Technology completed: {tech_name}!")

                        if update.get('completed_buildings'):
                            for building_name in update['completed_buildings']:
                                notifications.append(f"🏗️  Building completed: {building_name}!")

                        # Check for resource state changes
                        had_notification = self._check_resource_notifications_silent()

                        # If any notifications, redraw everything
                        if notifications or had_notification or self.debug_mode:
                            self.clear_screen()
                            self.display_status()
                            print()

                            # Print notifications
                            for notification in notifications:
                                print(notification)

                            # Print debug info if enabled
                            if self.debug_mode:
                                self._print_debug_update(update)

                            # Redraw prompt with current buffer
                            print(f"\n> {input_buffer}", end='', flush=True)

                    # Check for input without blocking
                    if sys.platform != 'win32' and self.old_terminal_settings:
                        # Use select on Unix-like systems with raw terminal
                        if select.select([sys.stdin], [], [], 0.1)[0]:
                            char = sys.stdin.read(1)
                            if char == '\n' or char == '\r':
                                # Process command
                                command = input_buffer.strip()
                                input_buffer = ""
                                print()  # New line after command

                                if command:
                                    self.process_command(command)

                                if self.running:
                                    print("> ", end='', flush=True)
                            elif char == '\x7f' or char == '\x08':  # Backspace
                                if input_buffer:
                                    input_buffer = input_buffer[:-1]
                                    print('\b \b', end='', flush=True)
                            elif char == '\x03':  # Ctrl+C
                                raise KeyboardInterrupt()
                            elif ord(char) >= 32:  # Printable characters
                                input_buffer += char
                                print(char, end='', flush=True)
                    else:
                        # Fallback for Windows or non-TTY - use blocking input with timeout
                        time.sleep(0.1)

                except KeyboardInterrupt:
                    print("\n\nUse 'quit' to exit.")
                    input_buffer = ""
                    print("> ", end='', flush=True)
                    continue
                except EOFError:
                    break

        finally:
            self.cleanup()

    def process_command(self, command_line: str):
        """Process a command from user input."""
        parts = command_line.split()
        if not parts:
            return

        command = parts[0].lower()
        args = parts[1:]

        # Clear screen and show status before command output
        self.clear_screen()
        self.display_status()
        print()  # Separator line

        if command in self.commands:
            try:
                self.commands[command](args)
            except Exception as e:
                print(f"Error executing command: {e}")
        else:
            print(f"Unknown command: {command}. Type 'help' for available commands.")

    def cmd_help(self, args):
        """Display help information."""
        print("\n=== Available Commands ===")
        print("\nGeneral:")
        print("  help, h                  - Show this help message")
        print("  status                   - Show overall civilization status")
        print("  debug                    - Toggle debug mode on/off")
        print("  save                     - Save the game")
        print("  quit, exit, q            - Save and exit the game")

        print("\nResources:")
        print("  resources, res           - Display current resources")
        print("  available, avail         - List all extractable resources")

        print("\nPopulation:")
        print("  population, pop          - Display population and workforce info")
        print("  allocate <resource> <count> - Allocate workers to extract a resource")
        print("    Tasks: research, production")
        print("    Resources: use resource ID from 'available' command")
        print("    Example: allocate wheat 5")
        print("  deallocate <resource> <count> - Remove workers from a task")

        print("\nTechnology:")
        print("  technologies, tech       - List available technologies")
        print("  research <tech_id>       - Start researching a technology")

        print("\nBuildings:")
        print("  buildings                - List available buildings")
        print("  build <building_id>      - Start constructing a building")

        print("\nCities:")
        print("  cities                   - List all cities")
        print("  switch <city_name>       - Switch to a different city")
        print("  found <city_name>        - Found a new city (requires settler)")

    def cmd_status(self, args):
        """Display overall status."""
        print("\n=== Civilization Status ===")
        print(f"Name: {self.civilization.name}")
        print(f"Era: {self.civilization.current_era.value.title()}")
        print(f"Government: {self.civilization.government.value.title()}")
        print(f"Game Time: {self.civilization.game_time:.1f}s")

        # Show totals across all cities
        total_pop = self.civilization.get_total_population()
        print(f"\nTotal Population: {total_pop} across {len(self.civilization.cities)} cities")

        active_city = self.civilization.get_active_city()
        if active_city:
            print(f"Active City: {active_city.name}")
            print(f"  Population: {active_city.population.total}")
            print(f"  Happiness: {active_city.population.happiness:.2f}")
            print(f"  Literacy: {active_city.population.literacy:.2%}")
            print(f"  Buildings: {len(active_city.buildings.buildings)}")

        print(f"\nTechnologies: {len(self.civilization.tech_tree.researched)}")
        print(f"Settlers Ready: {self.civilization.ready_settlers}")
        print(f"Prestige Points: {self.civilization.prestige_points}")

    def cmd_resources(self, args):
        """Display current resources."""
        active_city = self.civilization.get_active_city()
        if not active_city:
            print("No active city!")
            return

        print(f"\n=== Resources ({active_city.name}) ===")

        # Show city resources
        has_resources = False
        if active_city.resources.resources:
            has_resources = True
            for res_id, resource in sorted(active_city.resources.resources.items()):
                # Calculate time to full/empty
                status = ""
                remaining_to_cap = resource.capacity - resource.amount
                if resource.net_rate > 0 and not resource.is_full:
                    time_to_full = remaining_to_cap / resource.net_rate
                    status = f" (Full in {self._format_time(time_to_full)})"
                elif resource.net_rate < 0 and not resource.is_empty:
                    time_to_empty = resource.amount / abs(resource.net_rate)
                    status = f" (Empty in {self._format_time(time_to_empty)})"

                rate_str = ""
                if resource.net_rate != 0:
                    rate_str = f" [{resource.net_rate:+.2f}/s]"

                print(f"  {resource.resource_type.name:20} {resource.amount:8.1f}/{resource.capacity:.1f}{rate_str}{status}")

        # Show civilization-wide resources (research)
        print("\n=== Civilization Resources ===")
        if self.civilization.resources.resources:
            has_resources = True
            for res_id, resource in sorted(self.civilization.resources.resources.items()):
                rate_str = ""
                if resource.net_rate != 0:
                    rate_str = f" [{resource.net_rate:+.2f}/s]"
                print(f"  {resource.resource_type.name:20} {resource.amount:8.1f}/{resource.capacity:.1f}{rate_str}")

        if not has_resources:
            print("No resources available.")

    def cmd_available_resources(self, args):
        """Display all extractable resources available based on researched technologies."""
        if self.game_data is None:
            print("Game data not available.")
            return

        print("\n=== Available Resources ===")

        # Get researched tech IDs
        researched_techs = self.civilization.tech_tree.researched

        # Filter resources by:
        # 1. Must be in civilization's available_resources set
        # 2. Must have required tech researched (or no tech required)
        available = []
        locked_by_availability = []
        locked_by_tech = []

        for resource in self.game_data.resources.values():
            # Check if resource is in the civilization's available resources
            if resource.id not in self.civilization.available_resources:
                locked_by_availability.append(resource)
                continue

            # Check tech requirements
            if resource.tech_reveal is None or resource.tech_reveal in researched_techs:
                available.append(resource)
            else:
                locked_by_tech.append(resource)

        if available:
            print(f"\n{len(available)} resources available for extraction:")
            # Group by category
            from ..models.resource import ResourceCategory
            for category in ResourceCategory:
                category_resources = [r for r in available if r.category == category]
                if category_resources:
                    print(f"\n  {category.value.upper()}:")
                    for resource in sorted(category_resources, key=lambda r: r.name):
                        bonus_class_str = f" [{resource.bonus_class}]" if resource.bonus_class else ""
                        print(f"    - {resource.name}{bonus_class_str} (ID: {resource.id})")
        else:
            print("\nNo resources available yet.")

        if locked_by_tech:
            print(f"\n{len(locked_by_tech)} resources in your territory but locked (require technology):")
            for resource in sorted(locked_by_tech, key=lambda r: r.name):
                tech_name = resource.tech_reveal.replace('_', ' ').title() if resource.tech_reveal else "Unknown"
                print(f"  - {resource.name} (requires: {tech_name})")

    def cmd_population(self, args):
        """Display population information."""
        pop = self.civilization.population

        print("\n=== Population ===")
        print(f"Total Population: {pop.total}")
        print(f"Housing Capacity: {pop.housing_capacity}")
        print(f"Happiness: {pop.happiness:.2f}")
        print(f"Literacy: {pop.literacy:.2%}")
        print(f"Growth Rate: {pop.growth_rate:.2%}/day")
        print(f"\nIdle Workers: {pop.idle_workers}")
        print(f"Allocated Workers: {pop.allocated_workers}")

        if pop.allocations:
            print("\n--- Workforce Allocation ---")
            for allocation in pop.allocations:
                task_name = allocation.task.value.replace('_', ' ').title()
                detail = ""
                if allocation.resource_id:
                    detail = f" ({allocation.resource_id})"
                elif allocation.building_id:
                    detail = f" ({allocation.building_id})"
                print(f"  {task_name}{detail}: {allocation.count} workers")

    def cmd_allocate(self, args):
        """Allocate workers to a task."""
        if len(args) < 2:
            print("Usage: allocate <resource_id> <count>")
            print("Tasks: research, production")
            print("Resources: any available crop resource (use 'available' to see list)")
            return

        task_name = args[0].lower()
        try:
            count = int(args[1])
        except ValueError:
            print("Count must be a number.")
            return

        # Check if it's a special task
        if task_name == "research":
            allocated = self.civilization.population.allocate_workers(
                WorkforceTask.RESEARCH,
                count
            )
            print(f"Allocated {allocated} workers to research.")
        elif task_name == "production":
            allocated = self.civilization.population.allocate_workers(
                WorkforceTask.CONSTRUCTION,
                count
            )
            print(f"Allocated {allocated} workers to production.")
        else:
            # Check if it's a resource from game data
            if self.game_data is None:
                print("Game data not available.")
                return

            resource = self.game_data.resources.get(task_name)
            if resource is None:
                print(f"Unknown resource or task: {task_name}")
                print("Use 'available' to see available resources")
                return

            # Get active city
            active_city = self.civilization.get_active_city()
            if not active_city:
                print("No active city!")
                return

            # Check if resource is available to this city
            if resource.id not in active_city.available_resources:
                print(f"Resource '{resource.name}' is not available in this city.")
                return

            # Check if tech requirement is met
            researched_techs = self.civilization.tech_tree.researched
            if resource.tech_reveal and resource.tech_reveal not in researched_techs:
                tech_name = resource.tech_reveal.replace('_', ' ').title()
                print(f"Resource '{resource.name}' requires technology: {tech_name}")
                return

            # Add resource to city's storage if not already there
            if active_city.resources.get(resource.id) is None:
                active_city.resources.add_resource_type(resource, initial_amount=0.0)

            # Allocate workers to this resource
            allocated = self.civilization.population.allocate_workers(
                WorkforceTask.RESOURCE_EXTRACTION,
                count,
                resource_id=resource.id
            )
            print(f"Allocated {allocated} workers to {resource.name} extraction.")

    def cmd_deallocate(self, args):
        """Remove workers from a task."""
        if len(args) < 2:
            print("Usage: deallocate <resource_id_or_task> <count>")
            print("Tasks: research, production")
            print("Resources: any resource you've allocated workers to")
            return

        task_name = args[0].lower()
        try:
            count = int(args[1])
        except ValueError:
            print("Count must be a number.")
            return

        # Check if it's a special task
        if task_name == "research":
            deallocated = self.civilization.population.deallocate_workers(
                WorkforceTask.RESEARCH,
                count
            )
            print(f"Deallocated {deallocated} workers from research.")
        elif task_name == "production":
            deallocated = self.civilization.population.deallocate_workers(
                WorkforceTask.CONSTRUCTION,
                count
            )
            print(f"Deallocated {deallocated} workers from production.")
        else:
            # Try to deallocate from a resource
            deallocated = self.civilization.population.deallocate_workers(
                WorkforceTask.RESOURCE_EXTRACTION,
                count,
                resource_id=task_name
            )
            if deallocated > 0:
                print(f"Deallocated {deallocated} workers from {task_name} extraction.")
            else:
                print(f"No workers allocated to {task_name}.")

    def cmd_technologies(self, args):
        """List technologies."""
        print("\n=== Technologies ===")

        # Current research
        if self.civilization.tech_tree.current_research:
            current = self.civilization.tech_tree.current_research
            progress = current.progress_percentage * 100
            print(f"\nCurrently Researching: {current.tech_def.name}")
            print(f"Progress: {progress:.1f}% ({current.research_points:.1f}/{current.tech_def.research_cost:.1f})")
        else:
            print("\nNo active research.")

        # Available technologies
        available = self.civilization.tech_tree.get_available_technologies()
        if available:
            print(f"\n--- Available Technologies ({len(available)}) ---")
            for tech in available[:10]:  # Show first 10
                print(f"  {tech.id:20} - {tech.name} (Cost: {tech.research_cost:.0f})")
        else:
            print("\nNo technologies available to research.")

        # Researched count
        researched_count = len(self.civilization.tech_tree.researched)
        print(f"\nTotal Researched: {researched_count}")

    def cmd_research(self, args):
        """Start researching a technology."""
        if len(args) < 1:
            print("Usage: research <tech_id>")
            return

        tech_id = args[0].lower()

        if self.civilization.tech_tree.start_research(tech_id):
            tech = self.civilization.tech_tree.get_technology(tech_id)
            print(f"Started researching: {tech.name}")
        else:
            print(f"Cannot research '{tech_id}'. Check prerequisites or if already researched.")

    def cmd_buildings(self, args):
        """List buildings."""
        print("\n=== Buildings ===")

        # Existing buildings
        if self.civilization.buildings.buildings:
            print(f"\n--- Constructed Buildings ({len(self.civilization.buildings.buildings)}) ---")
            for building in self.civilization.buildings.buildings:
                active = "Active" if building.is_active else "Inactive"
                if building.max_workers > 0:
                    workers = f"{building.assigned_workers}/{building.max_workers}"
                    print(f"  {building.definition.name} [{active}] Workers: {workers}")
                else:
                    print(f"  {building.definition.name} [{active}]")
        else:
            print("\nNo buildings constructed yet.")

        # Under construction
        if self.civilization.buildings.under_construction:
            print(f"\n--- Under Construction ({len(self.civilization.buildings.under_construction)}) ---")
            production_workers = self.civilization.population.get_workers_on_task(WorkforceTask.CONSTRUCTION)
            for construction in self.civilization.buildings.under_construction:
                progress = construction.progress_percentage * 100
                remaining = construction.remaining_production
                print(f"  {construction.building_def.name}: {progress:.1f}% ({construction.progress:.1f}/{construction.required_production:.1f} production)")
                if production_workers > 0:
                    time_remaining = remaining / (production_workers * 1.0) if production_workers > 0 else float('inf')
                    print(f"    {production_workers} workers assigned, ~{time_remaining:.1f}s remaining")
                else:
                    print(f"    No workers assigned (construction paused)")

        # Available to build
        available = []
        for building_def in self.civilization.buildings.building_definitions.values():
            if self.civilization.buildings.can_build(building_def.id, self.civilization.tech_tree.researched):
                available.append(building_def)

        if available:
            print(f"\n--- Available to Build ({len(available)}) ---")
            for building_def in available[:10]:  # Show first 10
                # Get adjusted costs based on how many have been built
                adjusted_costs = self.civilization.buildings.get_adjusted_costs(building_def.id)
                current_count = self.civilization.buildings.get_building_count(building_def.id)
                costs_str = ", ".join([f"{cost.resource_id}: {cost.amount:.1f}" for cost in adjusted_costs])

                print(f"  {building_def.id:20} - {building_def.name}")
                if costs_str:
                    print(f"    Cost: {costs_str}", end="")
                    if current_count > 0:
                        multiplier = self.civilization.buildings.get_cost_multiplier(building_def.id)
                        print(f" ({multiplier:.2f}x multiplier, {current_count} built)")
                    else:
                        print()

    def cmd_build(self, args):
        """Start building construction."""
        if len(args) < 1:
            print("Usage: build <building_id>")
            return

        building_id = args[0].lower()

        # Check if can build
        if not self.civilization.buildings.can_build(building_id, self.civilization.tech_tree.researched):
            print(f"Cannot build '{building_id}'. Check requirements.")
            return

        # Get building definition
        building_def = self.civilization.buildings.get_building_definition(building_id)
        if not building_def:
            print(f"Unknown building: {building_id}")
            return

        # Get adjusted costs (accounts for multiple copies already built)
        adjusted_costs = self.civilization.buildings.get_adjusted_costs(building_id)
        current_count = self.civilization.buildings.get_building_count(building_id)
        multiplier = self.civilization.buildings.get_cost_multiplier(building_id)

        # Separate production costs from other costs (production is applied during construction, not upfront)
        upfront_costs = [cost for cost in adjusted_costs if cost.resource_id != "production"]
        production_costs = [cost for cost in adjusted_costs if cost.resource_id == "production"]

        # Check and spend upfront costs (everything except production)
        if upfront_costs and not self.civilization.can_afford_costs(upfront_costs):
            print("Not enough resources!")
            costs_str = ", ".join([f"{cost.resource_id}: {cost.amount:.1f}" for cost in upfront_costs])
            print(f"Required: {costs_str}")
            if current_count > 0:
                print(f"(Cost increased by {multiplier:.2f}x due to {current_count} already built)")
            return

        if upfront_costs:
            self.civilization.spend_costs(upfront_costs)

        # Start construction
        if self.civilization.buildings.start_construction(building_id):
            print(f"Started construction: {building_def.name}")
            if production_costs:
                prod_amount = production_costs[0].amount
                print(f"  Requires {prod_amount:.1f} production to complete")
                production_workers = self.civilization.population.get_workers_on_task(WorkforceTask.CONSTRUCTION)
                if production_workers > 0:
                    time_estimate = prod_amount / (production_workers * 1.0)
                    print(f"  Estimated time: {time_estimate:.1f}s with {production_workers} workers")
                else:
                    print(f"  (Assign workers to production to make progress)")
            if current_count > 0:
                print(f"  (This is copy #{current_count + 1})")
        else:
            print("Failed to start construction.")

    def cmd_cities(self, args):
        """List all cities."""
        print("\n=== Cities ===")

        if not self.civilization.cities:
            print("No cities exist!")
            return

        active_city = self.civilization.get_active_city()
        for city in self.civilization.cities:
            is_active = "*" if city == active_city else " "
            pop = city.population.total
            buildings = len(city.buildings.buildings)
            resources = len(city.available_resources)
            print(f"{is_active} {city.name:15} Pop: {pop:3} | Buildings: {buildings:2} | Resources: {resources:2}")

        print(f"\nTotal cities: {len(self.civilization.cities)}")
        print(f"Settlers ready: {self.civilization.ready_settlers}")

    def cmd_switch_city(self, args):
        """Switch to a different city."""
        if len(args) < 1:
            print("Usage: switch <city_name>")
            return

        city_name = " ".join(args)
        city = self.civilization.get_city_by_name(city_name)

        if not city:
            print(f"City '{city_name}' not found.")
            print("\nAvailable cities:")
            for c in self.civilization.cities:
                print(f"  - {c.name}")
            return

        if self.civilization.set_active_city(city.id):
            print(f"Switched to {city.name}")
        else:
            print(f"Failed to switch to {city.name}")

    def cmd_found_city(self, args):
        """Found a new city using a settler."""
        if len(args) < 1:
            print("Usage: found <city_name>")
            return

        if self.civilization.ready_settlers <= 0:
            print("No settlers available!")
            print("Build a Settler (requires Tribalism technology) to found new cities.")
            return

        city_name = " ".join(args)

        # Check if city name already exists
        if self.civilization.get_city_by_name(city_name):
            print(f"A city named '{city_name}' already exists!")
            return

        # Found the city
        if self.game_data is None:
            print("Game data not available.")
            return

        new_city = self.civilization.found_city(city_name, self.game_data.resources)

        if new_city:
            print(f"🏙️  Founded {city_name}!")
            print(f"  Starting population: {new_city.population.total}")
            print(f"  Starting resources: {len(new_city.available_resources)}")
            print(f"  Settlers remaining: {self.civilization.ready_settlers}")
            print(f"\nUse 'switch {city_name}' to manage the new city.")
        else:
            print("Failed to found city.")

    def cmd_save(self, args):
        """Save the game."""
        if self.save_system.save_game(self.civilization, "autosave"):
            print("Game saved successfully!")
        else:
            print("Failed to save game.")

    def cmd_quit(self, args):
        """Quit the game."""
        print("\nSaving game...")
        self.save_system.save_game(self.civilization, "autosave")
        print("Goodbye!")
        self.running = False

    def cmd_debug(self, args):
        """Toggle debug mode."""
        self.debug_mode = not self.debug_mode
        status = "enabled" if self.debug_mode else "disabled"
        print(f"Debug mode {status}")

        if self.debug_mode:
            # Print current debug state immediately
            self._print_debug_state()

    def _print_debug_state(self):
        """Print current debug state information."""
        active_city = self.civilization.get_active_city()
        if not active_city:
            print("\n=== Debug State ===")
            print("No active city!")
            return

        print(f"\n=== Debug State ({active_city.name}) ===")

        # Population info
        pop = active_city.population
        print(f"Population: {pop.total}")
        print(f"Happiness: {pop.happiness:.2f}")
        print(f"Literacy: {pop.literacy:.2%}")

        # Worker allocations
        print("\nWorker Allocations:")
        for allocation in pop.allocations:
            task_name = allocation.task.value
            detail = f" (resource: {allocation.resource_id})" if allocation.resource_id else ""
            print(f"  {task_name}{detail}: {allocation.count} workers")

        # Calculate expected production rates
        print("\nExpected Production Rates:")

        # Check for crop workers (not generic "food")
        total_crop_workers = sum(1 for alloc in pop.allocations
                                 if alloc.task == WorkforceTask.RESOURCE_EXTRACTION
                                 and alloc.resource_id)
        if total_crop_workers > 0:
            food_production_rate = total_crop_workers * 2.0 * pop.happiness
            print(f"  Crop production: {food_production_rate:.2f}/s ({total_crop_workers} workers × 2.0 × {pop.happiness:.2f} happiness)")
        else:
            print(f"  Crop production: 0.00/s (no workers)")

        food_consumption_rate = pop.calculate_food_consumption()
        print(f"  Food consumption: {food_consumption_rate:.2f}/s ({pop.total} pop × {pop.food_consumption_per_capita:.2f})")

        research_workers = pop.get_workers_on_task(WorkforceTask.RESEARCH)
        if research_workers > 0:
            research_rate = research_workers * 1.0 * (1.0 + pop.literacy)
            print(f"  Research production: {research_rate:.2f}/s ({research_workers} workers × 1.0 × {1.0 + pop.literacy:.2f})")
        else:
            print(f"  Research production: 0.00/s (no workers)")

        # Current resource state (city resources)
        print(f"\nCurrent City Resources:")
        for res_id, resource in active_city.resources.resources.items():
            print(f"  {resource.resource_type.name}: {resource.amount:.2f}/{resource.capacity:.2f}")
            print(f"    Production: {resource.production_rate:.2f}/s, Consumption: {resource.consumption_rate:.2f}/s, Net: {resource.net_rate:.2f}/s")

        # Civilization resources
        print(f"\nCivilization Resources:")
        for res_id, resource in self.civilization.resources.resources.items():
            print(f"  {resource.resource_type.name}: {resource.amount:.2f}/{resource.capacity:.2f}")
            print(f"    Rate: {resource.production_rate:.2f}/s")

    def _check_resource_notifications(self):
        """Check for resource state changes and notify user."""
        self._check_resource_notifications_silent()

    def _check_resource_notifications_silent(self) -> bool:
        """Check for resource state changes and notify user. Returns True if notification was printed."""
        food_resource = self.civilization.resources.get("food")
        if not food_resource:
            return False

        # Get previous state
        prev_state = self.last_resource_states.get("food", {})
        prev_empty = prev_state.get("empty", False)
        prev_full = prev_state.get("full", False)

        # Check current state
        current_empty = food_resource.is_empty
        current_full = food_resource.is_full

        notification_printed = False

        # Notify on state changes
        if current_empty and not prev_empty:
            print(f"\r\033[K⚠️  WARNING: Food storage is empty! ({food_resource.amount:.1f}/{food_resource.capacity:.1f})")
            if food_resource.net_rate < 0:
                print(f"\r\033[K   Your population is starving! (Consumption: {food_resource.consumption_rate:.1f}/s, Production: {food_resource.production_rate:.1f}/s)")
            notification_printed = True
        elif current_full and not prev_full:
            print(f"\r\033[K📦 Food storage is full! ({food_resource.amount:.1f}/{food_resource.capacity:.1f})")
            if food_resource.production_rate > 0:
                print(f"\r\033[K   Consider building more storage or reducing food production.")
            notification_printed = True

        # Update tracked state
        self.last_resource_states["food"] = {
            "empty": current_empty,
            "full": current_full
        }

        return notification_printed

    def _print_debug_update(self, update: dict):
        """Print debug information after a game tick."""
        delta = update.get('delta_time', 0.0)
        print(f"\n[DEBUG] Tick: {delta:.3f}s elapsed")
        print(f"  Happiness: {self.civilization.population.happiness:.2f}")

        if update.get('resource_changes'):
            print("  Resource changes:")
            for res_id, change in update['resource_changes'].items():
                print(f"    {res_id}: {change:+.2f}")

        if update.get('population_change', 0) != 0:
            print(f"  Population: {update['population_change']:+d}")

        if update.get('completed_techs'):
            print(f"  Completed techs: {', '.join(update['completed_techs'])}")

        if update.get('completed_buildings'):
            print(f"  Completed buildings: {', '.join(update['completed_buildings'])}")

    def cleanup(self):
        """Clean up before exit."""
        self.game_loop.stop()

        # Restore terminal settings
        if self.old_terminal_settings and sys.stdin.isatty():
            try:
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.old_terminal_settings)
            except:
                pass

    def _format_time(self, seconds: float) -> str:
        """Format seconds into human-readable time."""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            return f"{seconds/60:.1f}m"
        else:
            return f"{seconds/3600:.1f}h"
