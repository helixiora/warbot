"""World conflicts tool implementation."""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup

from .base import Tool

logger = logging.getLogger(__name__)

# Cache configuration
CACHE_DIR = Path.home() / ".cache" / "agentic_bot"
CACHE_FILE = CACHE_DIR / "world_conflicts_cache.json"
CACHE_TTL_SECONDS = 3600  # 1 hour


class WorldConflictsTool(Tool):
    name = "get_world_conflicts"
    description = (
        "Fetch current world conflicts from Wikipedia, including Major wars (10,000+ deaths), "
        "Minor wars (1,000-9,999 deaths), Conflicts (100-999 deaths), and Skirmishes "
        "(<100 deaths). Data is cached locally for 1 hour. Use for situational awareness "
        "and preparedness."
    )
    parameters: dict[str, Any] = {
        "type": "object",
        "properties": {
            "region": {
                "type": "string",
                "description": "Optional region filter (e.g., Europe, Middle East, Asia Pacific).",
            }
        },
        "required": [],
    }

    def execute(self, region: str | None = None) -> dict[str, Any]:
        """
        Fetch all world conflicts from Wikipedia.
        Returns Major wars, Minor wars, Conflicts, and Skirmishes.
        """
        logger.debug(f"Executing get_world_conflicts with region={region}")
        try:
            conflicts = self._get_conflicts()
            logger.debug(f"Successfully fetched {len(conflicts)} conflicts")
        except Exception as e:
            logger.error(f"Error fetching conflicts: {e}", exc_info=True)
            return {
                "conflicts": [],
                "note": f"Error fetching conflicts: {str(e)}",
                "error": True,
            }

        if region:
            logger.debug(f"Filtering conflicts by region: {region}")
            filtered = [
                c
                for c in conflicts
                if region.lower() in c.get("continent", "").lower()
                or region.lower() in c.get("location", "").lower()
            ]
            logger.debug(f"Filtered to {len(filtered)} conflicts matching region '{region}'")
            return {
                "conflicts": filtered,
                "note": f"Filtered by region '{region}' (best-effort match). "
                f"Source: Wikipedia List of ongoing armed conflicts",
            }

        return {
            "conflicts": conflicts,
            "note": (
                "Data fetched from Wikipedia: List of ongoing armed conflicts. "
                "Includes Major wars, Minor wars, Conflicts, and Skirmishes."
            ),
        }

    def _get_conflicts(self) -> list[dict[str, Any]]:
        """Get conflicts from cache or fetch from Wikipedia."""
        # Try to load from cache
        cached_data = self._load_cache()
        if cached_data:
            logger.debug(f"Loaded {len(cached_data)} conflicts from cache")
            return cached_data

        # Fetch from Wikipedia
        logger.debug("Cache miss or expired, fetching from Wikipedia")
        conflicts = self._fetch_conflicts_from_wikipedia()

        # Save to cache
        self._save_cache(conflicts)
        logger.debug(f"Cached {len(conflicts)} conflicts")

        return conflicts

    def _load_cache(self) -> list[dict[str, Any]] | None:
        """Load conflicts from cache if valid."""
        if not CACHE_FILE.exists():
            logger.debug("Cache file does not exist")
            return None

        try:
            with open(CACHE_FILE, encoding="utf-8") as f:
                cache_data = json.load(f)

            cache_time = cache_data.get("timestamp", 0)
            current_time = time.time()

            if current_time - cache_time > CACHE_TTL_SECONDS:
                logger.debug("Cache expired")
                return None

            conflicts = cache_data.get("conflicts", [])
            logger.debug(f"Cache valid, loaded {len(conflicts)} conflicts")
            return conflicts
        except Exception as e:
            logger.warning(f"Error loading cache: {e}", exc_info=True)
            return None

    def _save_cache(self, conflicts: list[dict[str, Any]]) -> None:
        """Save conflicts to cache."""
        try:
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            cache_data = {
                "timestamp": time.time(),
                "conflicts": conflicts,
            }
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, indent=2)
            logger.debug(f"Saved {len(conflicts)} conflicts to cache")
        except Exception as e:
            logger.warning(f"Error saving cache: {e}", exc_info=True)

    def _fetch_conflicts_from_wikipedia(self) -> list[dict[str, Any]]:
        """Fetch and parse all conflict categories from Wikipedia."""
        url = "https://en.wikipedia.org/wiki/List_of_ongoing_armed_conflicts"
        logger.debug(f"Fetching conflicts from Wikipedia: {url}")

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/91.0.4472.124 Safari/537.36"
            )
        }

        logger.debug(f"Sending HTTP GET request to {url} with timeout=10s")
        response = requests.get(url, headers=headers, timeout=10)
        logger.debug(
            f"Wikipedia response status: {response.status_code}, "
            f"content length: {len(response.content)} bytes"
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "lxml")
        logger.debug("Parsed Wikipedia HTML with BeautifulSoup")

        # Define all conflict categories
        categories = [
            {
                "id": (
                    "Major_wars_(10,000_or_more_combat-related_deaths_in_current_or_previous_year)"
                ),
                "name": "Major wars",
                "type": "major_war",
            },
            {
                "id": "Minor_wars_(1,000–9,999_combat-related_deaths_in_current_or_previous_year)",
                "name": "Minor wars",
                "type": "minor_war",
            },
            {
                "id": "Conflicts_(100–999_combat-related_deaths_in_current_or_previous_year)",
                "name": "Conflicts",
                "type": "conflict",
            },
            {
                "id": (
                    "Skirmishes_and_clashes_(fewer_than_100_combat-related_deaths_in_"
                    "current_and_previous_year)"
                ),
                "name": "Skirmishes and clashes",
                "type": "skirmish",
            },
        ]

        all_conflicts: list[dict[str, Any]] = []

        for category in categories:
            logger.debug(f"Extracting {category['name']} section")
            conflicts = self._extract_category(soup, category)
            logger.debug(f"Extracted {len(conflicts)} conflicts from {category['name']}")
            all_conflicts.extend(conflicts)

        logger.debug(f"Total conflicts extracted: {len(all_conflicts)}")
        return all_conflicts

    def _extract_category(
        self, soup: BeautifulSoup, category: dict[str, str]
    ) -> list[dict[str, Any]]:
        """Extract conflicts from a specific category section."""
        category_id = category["id"]
        category_name = category["name"]
        category_type = category["type"]

        logger.debug(f"Looking for {category_name} section with id: {category_id}")

        heading = None

        # Strategy 1: Find span with the exact ID, then find parent heading
        span_element = soup.find("span", {"id": category_id})
        if span_element:
            logger.debug(f"Found {category_name} section via span with id")
            heading = span_element.find_parent(["h2", "h3", "h4", "h5"])
            if heading:
                logger.debug(f"Found parent heading: {heading.name}")
            else:
                heading = span_element
                logger.debug("Using span element directly")

        if not heading:
            # Strategy 2: Find any element with the ID
            element_with_id = soup.find(id=category_id)
            if element_with_id:
                logger.debug(f"Found {category_name} section via element with id")
                heading = element_with_id.find_parent(["h2", "h3", "h4", "h5"])
                if not heading:
                    heading = element_with_id

        if not heading:
            # Strategy 3: Search for headings containing category name
            logger.debug(f"Trying to find {category_name} heading by text content")
            for heading_tag in ["h2", "h3", "h4"]:
                headings = soup.find_all(heading_tag)
                for h in headings:
                    heading_text = h.get_text(strip=True)
                    if category_name.lower() in heading_text.lower():
                        heading = h
                        logger.debug(
                            f"Found {category_name} section via {heading_tag} "
                            f"heading: '{heading_text}'"
                        )
                        break
                if heading:
                    break

        if not heading:
            logger.warning(f"Could not find {category_name} section heading")
            return []

        # Find the table after the heading
        table = heading.find_next("table")
        if not table:
            logger.warning(f"Could not find table after {category_name} heading")
            return []

        logger.debug(f"Found {category_name} table, extracting rows")
        return self._parse_table(table, category_type)

    def _parse_table(self, table: Any, category_type: str) -> list[dict[str, Any]]:
        """Parse a conflicts table and return list of conflict dictionaries."""
        conflicts: list[dict[str, Any]] = []

        # Parse table rows (skip header)
        rows = table.find_all("tr")[1:]  # Skip header row
        logger.debug(f"Found {len(rows)} conflict rows to parse")

        for idx, row in enumerate(rows):
            cells = row.find_all(["td", "th"])
            if len(cells) < 4:
                logger.debug(f"Row {idx} has insufficient cells ({len(cells)}), skipping")
                continue

            try:
                logger.debug(f"Parsing row {idx} with {len(cells)} cells")

                # Extract columns according to Wikipedia table structure:
                # 0: Start of conflict
                # 1: Conflict
                # 2: Continent
                # 3: Location
                # 4: Cumulative fatalities
                # 5: 2024 fatalities
                # 6: 2025 fatalities

                # Start of conflict (cell 0)
                start_of_conflict = cells[0].get_text(strip=True) if len(cells) > 0 else "Unknown"

                # Conflict name (cell 1)
                conflict_cell = cells[1] if len(cells) > 1 else None
                if conflict_cell:
                    conflict_link = conflict_cell.find("a")
                    conflict = (
                        conflict_link.get_text(strip=True)
                        if conflict_link
                        else conflict_cell.get_text(strip=True)
                    )
                else:
                    conflict = "Unknown"

                # Continent (cell 2)
                continent = cells[2].get_text(strip=True) if len(cells) > 2 else "Unknown"

                # Location (cell 3)
                location = cells[3].get_text(strip=True) if len(cells) > 3 else "Unknown"

                # Cumulative fatalities (cell 4)
                cumulative_fatalities = cells[4].get_text(strip=True) if len(cells) > 4 else None

                # 2024 fatalities (cell 5)
                fatalities_2024 = cells[5].get_text(strip=True) if len(cells) > 5 else None

                # 2025 fatalities (cell 6)
                fatalities_2025 = cells[6].get_text(strip=True) if len(cells) > 6 else None

                conflict_data = {
                    "category": category_type,
                    "start_of_conflict": start_of_conflict,
                    "conflict": conflict,
                    "continent": continent,
                    "location": location,
                    "cumulative_fatalities": cumulative_fatalities,
                    "fatalities_2024": fatalities_2024,
                    "fatalities_2025": fatalities_2025,
                }
                logger.debug(
                    f"Extracted conflict {idx + 1}/{len(rows)}: '{conflict}' "
                    f"({category_type}, {continent}, {location}), start={start_of_conflict}, "
                    f"cumulative={cumulative_fatalities}, 2024={fatalities_2024}, "
                    f"2025={fatalities_2025}"
                )
                conflicts.append(conflict_data)
            except Exception as e:
                # Skip malformed rows
                logger.warning(f"Error parsing row {idx}: {e}", exc_info=True)
                continue

        logger.debug(
            f"Successfully parsed {len(conflicts)} conflicts from table "
            f"(out of {len(rows)} rows processed)"
        )
        return conflicts
