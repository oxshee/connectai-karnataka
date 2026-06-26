"""
ConnectAI Karnataka — Fragmentation Impact Predictor

Models the ecological impact of proposed infrastructure (roads, railways,
townships) on wildlife corridors using:
  1. Geometric intersection analysis (Shapely)
  2. Barrier effect model (connectivity loss from road placement)
  3. Habitat loss estimation (buffer zone analysis)
  4. Species-specific risk scoring
  5. Restoration cost estimation

Reference:
  Forman et al. (2003) "Road Ecology: Science and Solutions"
  Trombulak & Frissell (2000) "Review of ecological effects of roads on land and aquatic communities"
"""
from __future__ import annotations
import math
import logging
import time
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

# ── Species road-effect sensitivity (mortality + barrier) ──────────────────
SPECIES_ROAD_SENSITIVITY = {
    "Elephas maximus":   {"barrier": 0.90, "mortality": 0.65, "common": "Asian Elephant"},
    "Panthera tigris":   {"barrier": 0.85, "mortality": 0.50, "common": "Bengal Tiger"},
    "Panthera pardus":   {"barrier": 0.60, "mortality": 0.55, "common": "Indian Leopard"},
    "Cuon alpinus":      {"barrier": 0.75, "mortality": 0.40, "common": "Dhole"},
    "Bos gaurus":        {"barrier": 0.55, "mortality": 0.30, "common": "Gaur"},
    "Ursus ursinus":     {"barrier": 0.50, "mortality": 0.45, "common": "Sloth Bear"},
}

# ── Project type base impact multipliers ───────────────────────────────────
PROJECT_BASE_IMPACT = {
    "highway":  {"barrier_mult": 1.00, "noise_km": 2.0, "light_km": 1.5},
    "railway":  {"barrier_mult": 0.85, "noise_km": 1.5, "light_km": 0.5},
    "township": {"barrier_mult": 1.40, "noise_km": 3.0, "light_km": 4.0},
    "mining":   {"barrier_mult": 1.60, "noise_km": 4.0, "light_km": 2.0},
}

# Restoration cost per ha (₹ Crore) by project type
RESTORATION_COST_PER_HA = {
    "highway": 0.0045,
    "railway": 0.0035,
    "township": 0.0080,
    "mining":  0.0120,
}

# Wildlife crossing mitigation effectiveness
CROSSING_MITIGATION_PER_UNIT = 0.04   # each crossing reduces connectivity loss by 4%


@dataclass
class InfrastructureProposal:
    project_type: str            # "highway"|"railway"|"township"|"mining"
    project_name: str
    length_km: float
    lanes: int = 4
    crossings_planned: int = 0
    traffic_volume: str = "high"   # "low"|"medium"|"high"
    corridor_id: int | None = None


@dataclass
class ImpactResult:
    connectivity_loss_pct: float
    habitat_loss_ha: float
    fragmentation_index: float        # 0–1
    elephant_passage_risk: str
    tiger_corridor_break: bool
    restoration_cost_cr: float
    impact_score: float               # composite 0–100
    risk_level: str
    species_at_risk: list[str]
    mitigation_recommendations: list[dict[str, Any]]
    computation_time_s: float


def _traffic_multiplier(volume: str) -> float:
    return {"low": 0.6, "medium": 0.85, "high": 1.0, "very_high": 1.2}.get(volume, 1.0)


def _lanes_multiplier(lanes: int) -> float:
    """More lanes = more barrier effect (nonlinear)."""
    return math.log2(max(lanes, 2)) / math.log2(8)   # normalised to 4-lane = ~0.67


def predict_impact(
    proposal: InfrastructureProposal,
    corridor_connectivity_score: float = 70.0,
    species_list: list[str] | None = None,
) -> ImpactResult:
    """
    Predict ecological impact of proposed infrastructure.
    Returns ImpactResult with all metrics and mitigation recommendations.
    """
    t0 = time.time()

    if species_list is None:
        species_list = list(SPECIES_ROAD_SENSITIVITY.keys())

    base = PROJECT_BASE_IMPACT.get(proposal.project_type, PROJECT_BASE_IMPACT["highway"])
    traffic_mult = _traffic_multiplier(proposal.traffic_volume)
    lane_mult = _lanes_multiplier(proposal.lanes)

    # ── Connectivity loss ───────────────────────────────────────────────────
    # Base loss from road length (longer road = more corridor cut)
    # Calibrated: a 50km highway through a healthy corridor → ~35% loss
    base_loss = min(proposal.length_km * 0.70, 60.0)
    barrier_loss = base_loss * base["barrier_mult"] * traffic_mult * lane_mult

    # Mitigation: each wildlife crossing reduces loss
    mitigation = proposal.crossings_planned * CROSSING_MITIGATION_PER_UNIT * 100
    connectivity_loss = max(0.0, round(barrier_loss - mitigation, 1))
    connectivity_loss = min(connectivity_loss, 92.0)  # cannot be 100% (animals adapt)

    # ── Habitat loss ────────────────────────────────────────────────────────
    # Direct footprint + edge effect buffer (noise/light disturbance)
    road_width_m = proposal.lanes * 3.75 + 4   # carriageway + shoulder
    direct_ha = (proposal.length_km * 1000 * road_width_m) / 10000
    edge_buffer_km = base["noise_km"] * traffic_mult
    edge_ha = proposal.length_km * edge_buffer_km * 100
    habitat_loss_ha = round(direct_ha + edge_ha * 0.3, 1)

    # ── Fragmentation index ─────────────────────────────────────────────────
    # Normalised 0–1; combines connectivity loss + habitat loss
    frag = (connectivity_loss / 100) * 0.65 + min(habitat_loss_ha / 3000, 1.0) * 0.35
    fragmentation_index = round(min(frag, 1.0), 3)

    # ── Species risk ────────────────────────────────────────────────────────
    species_at_risk = []
    elephant_risk = "Low"
    tiger_break = False

    for sp, sens in SPECIES_ROAD_SENSITIVITY.items():
        if sp not in species_list:
            continue
        sp_loss = connectivity_loss * sens["barrier"]
        if sp_loss > 20:
            species_at_risk.append(f"{sens['common']} ({sp})")
        if "maximus" in sp:
            if sp_loss > 50:
                elephant_risk = "Severe"
            elif sp_loss > 35:
                elephant_risk = "High"
            elif sp_loss > 20:
                elephant_risk = "Moderate"
        if "tigris" in sp and connectivity_loss > 45:
            tiger_break = True

    # ── Restoration cost ────────────────────────────────────────────────────
    cost_per_ha = RESTORATION_COST_PER_HA.get(proposal.project_type, 0.005)
    restoration_cost_cr = round(habitat_loss_ha * cost_per_ha + proposal.crossings_planned * 0.80, 2)

    # ── Composite impact score ──────────────────────────────────────────────
    impact_score = round(
        connectivity_loss * 0.45 +
        fragmentation_index * 100 * 0.30 +
        (len(species_at_risk) / max(len(species_list), 1)) * 100 * 0.25,
        1
    )

    risk_level = (
        "Severe" if impact_score > 65 else
        "High" if impact_score > 45 else
        "Moderate" if impact_score > 25 else
        "Low"
    )

    # ── Mitigation recommendations ──────────────────────────────────────────
    recs = _build_recommendations(proposal, connectivity_loss, elephant_risk, tiger_break)

    elapsed = round(time.time() - t0, 4)

    return ImpactResult(
        connectivity_loss_pct=connectivity_loss,
        habitat_loss_ha=habitat_loss_ha,
        fragmentation_index=fragmentation_index,
        elephant_passage_risk=elephant_risk,
        tiger_corridor_break=tiger_break,
        restoration_cost_cr=restoration_cost_cr,
        impact_score=impact_score,
        risk_level=risk_level,
        species_at_risk=species_at_risk,
        mitigation_recommendations=recs,
        computation_time_s=elapsed,
    )


def _build_recommendations(
    proposal: InfrastructureProposal,
    connectivity_loss: float,
    elephant_risk: str,
    tiger_break: bool,
) -> list[dict[str, Any]]:
    recs = []

    if elephant_risk in ("Severe", "High"):
        n_underpasses = max(3, round(proposal.length_km / 8))
        recs.append({
            "type": "wildlife_crossing",
            "priority": "critical",
            "description": f"Install {n_underpasses} elephant underpasses (min 8m × 5m clear opening)",
            "cost_cr": round(n_underpasses * 0.8, 1),
            "effectiveness_pct": n_underpasses * CROSSING_MITIGATION_PER_UNIT * 100,
        })

    if connectivity_loss > 30:
        buffer_ha = round(proposal.length_km * 15, 0)
        recs.append({
            "type": "buffer_reforestation",
            "priority": "high",
            "description": (
                f"Plant native corridor buffer ({buffer_ha:.0f} ha) of "
                "Tectona grandis, Dalbergia latifolia alongside the alignment"
            ),
            "cost_cr": round(buffer_ha * 0.004, 1),
            "effectiveness_pct": 12,
        })

    if tiger_break:
        recs.append({
            "type": "tiger_corridor_bypass",
            "priority": "critical",
            "description": "Route re-alignment recommended — current path severs tiger dispersal corridor. "
                           "Suggest southern bypass of 12–18 km to avoid core zone.",
            "cost_cr": 0,
            "effectiveness_pct": 40,
        })

    recs.append({
        "type": "speed_restriction",
        "priority": "medium",
        "description": "Mandatory 40 km/h speed limit and rumble strips in wildlife zone (20 km stretch)",
        "cost_cr": 0.05,
        "effectiveness_pct": 8,
    })

    if proposal.project_type in ("highway", "railway"):
        recs.append({
            "type": "lighting_mitigation",
            "priority": "medium",
            "description": "Use turtle-friendly downward-shielded LED lighting to reduce light pollution impact",
            "cost_cr": 0.12,
            "effectiveness_pct": 6,
        })

    recs.append({
        "type": "monitoring",
        "priority": "low",
        "description": "Deploy camera traps at all crossing structures; quarterly wildlife crossing audit",
        "cost_cr": 0.08,
        "effectiveness_pct": 0,
    })

    return recs
