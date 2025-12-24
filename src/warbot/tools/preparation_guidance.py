from __future__ import annotations

"""Preparation guidance tool for emergency scenarios."""

from typing import Any, Dict

from .base import Tool


class PreparationGuidanceTool(Tool):
    name = "get_preparation_guidance"
    description = (
        "Provide preparation guidance for specific scenarios such as utilities interruption, "
        "internet loss, armed conflict, or natural disasters."
    )
    parameters: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "scenario": {
                "type": "string",
                "description": "Scenario type (utilities interruption, internet loss, armed conflict, natural disaster, etc.).",
            },
            "location": {
                "type": "string",
                "description": "Optional location context to tailor guidance.",
            },
        },
        "required": ["scenario"],
    }

    def execute(self, scenario: str, location: str | None = None) -> Dict[str, Any]:
        """Return structured preparation guidance for the scenario."""
        base = {
            "scenario": scenario,
            "location": location,
            "immediate_actions": [
                "Ensure communication plan with household.",
                "Charge essential devices and prepare backup power if available.",
            ],
            "short_term": [
                "Stock 72-hour supply of water and non-perishable food.",
                "Maintain basic medical kit and necessary prescriptions.",
            ],
            "long_term": [
                "Establish redundant communication channels (offline copies, radio).",
                "Diversify critical supplies and consider community coordination.",
            ],
            "supplies": [
                "Water, food, first aid, power banks, flashlights, radio, copies of documents.",
            ],
            "communication": [
                "Predefine meet-up points and check-in cadence.",
                "Keep written contact lists and offline maps.",
            ],
            "evacuation": [
                "Identify evacuation routes and transportation options.",
                "Prepare a go-bag with essentials and documents.",
            ],
            "note": "Stub guidance; refine with scenario-specific and location-specific intelligence.",
        }

        scenario_lower = scenario.lower()
        if "utilities" in scenario_lower:
            base["immediate_actions"].append(
                "Fill bathtubs and containers with water if safe to do so."
            )
        if "internet" in scenario_lower:
            base["communication"].append("Prepare offline backups of critical info and contacts.")
        if "conflict" in scenario_lower or "armed" in scenario_lower:
            base["evacuation"].append("Stay informed on local advisories; avoid high-risk areas.")
        return base
