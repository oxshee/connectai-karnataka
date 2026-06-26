"""
ConnectAI Karnataka — Restoration Recommendation Engine

Implements cost-benefit optimization for ecological restoration:
  1. Ranks restoration zones by ecological benefit per rupee
  2. Knapsack budget allocation (maximize connectivity gain within budget)
  3. Native species recommendation by habitat type
  4. Implementation timeline generation
"""
from __future__ import annotations
import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class RestorationPlan:
    corridor_id: int
    budget_cr: float
    selected_zones: list[dict[str, Any]]
    total_cost_cr: float
    total_connectivity_gain_pct: float
    total_area_ha: float
    roi_score: float
    ai_plan: str


def optimize_restoration(
    corridor_id: int,
    budget_cr: float,
    all_zones: list[dict],
    priority_method: str = "ecological_benefit",
) -> RestorationPlan:
    """
    Select the optimal set of restoration zones within budget using
    a greedy knapsack approach on cost-benefit ratio.
    """
    eligible = [z for z in all_zones if z.get("corridor_id") == corridor_id or corridor_id == 0]

    if not eligible:
        # Fall back to all zones if none match corridor
        eligible = all_zones

    # Sort by chosen priority method
    if priority_method == "cost_efficiency":
        eligible.sort(key=lambda z: z["ecological_benefit_score"] / max(z["cost_cr"], 0.01), reverse=True)
    elif priority_method == "connectivity_gain":
        eligible.sort(key=lambda z: z["connectivity_gain_pct"], reverse=True)
    else:  # ecological_benefit
        eligible.sort(key=lambda z: z["ecological_benefit_score"], reverse=True)

    # Greedy budget allocation
    selected = []
    remaining = budget_cr
    total_gain = 0.0
    total_area = 0.0
    total_cost = 0.0

    for zone in eligible:
        cost = zone["cost_cr"]
        if cost <= remaining:
            selected.append(zone)
            remaining -= cost
            total_cost += cost
            total_gain += zone["connectivity_gain_pct"]
            total_area += zone.get("area_ha", 0)

    roi = round(total_gain / max(total_cost, 0.01), 2)

    plan_text = _generate_plan_text(corridor_id, selected, budget_cr, total_gain, total_cost)

    return RestorationPlan(
        corridor_id=corridor_id,
        budget_cr=budget_cr,
        selected_zones=selected,
        total_cost_cr=round(total_cost, 2),
        total_connectivity_gain_pct=round(total_gain, 1),
        total_area_ha=round(total_area, 1),
        roi_score=roi,
        ai_plan=plan_text,
    )


def _generate_plan_text(
    corridor_id: int,
    zones: list[dict],
    budget: float,
    gain: float,
    cost: float,
) -> str:
    if not zones:
        return f"No viable restoration zones found within ₹{budget} Cr budget for corridor {corridor_id}."

    zone_names = ", ".join(z["name"] for z in zones[:3])
    methods = list({z["method"] for z in zones})
    species_all = []
    for z in zones:
        species_all.extend(z.get("native_species", []))
    species_str = ", ".join(list(set(species_all))[:5]) if species_all else "native deciduous species"

    return (
        f"Optimal restoration plan for Corridor {corridor_id} within ₹{budget:.1f} Cr budget. "
        f"Selected {len(zones)} zone(s): {zone_names}. "
        f"Methods: {', '.join(methods)}. "
        f"Key native species: {species_str}. "
        f"Projected connectivity gain: +{gain:.1f}% at ₹{cost:.2f} Cr total spend. "
        f"ROI: {round(gain/max(cost,0.01),1)}x connectivity per crore invested. "
        "Implement reforestation zones first (Years 1–3), wildlife crossings in Year 2, "
        "buffer zone management ongoing."
    )
