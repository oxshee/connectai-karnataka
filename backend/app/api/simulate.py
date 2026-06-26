"""
ConnectAI Karnataka — Impact Simulation API Routes

POST /simulate/highway        Predict impact of road/railway/township
GET  /simulate/scenarios      List saved impact scenarios
GET  /simulate/scenarios/{id} Get saved scenario detail
"""
from __future__ import annotations
import time
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.schemas import HighwaySimulateRequest, HighwaySimulateResponse
from app.data.karnataka_gis import CORRIDORS, get_corridor_by_id
from app.ml.fragmentation_model import predict_impact, InfrastructureProposal
from app.services.explainability import explain_impact

router = APIRouter(prefix="/simulate", tags=["Impact Simulation"])
logger = logging.getLogger(__name__)

# In-memory scenario store (replaced by DB in production)
_scenario_store: list[dict] = []
_scenario_counter = 1


@router.post("/highway", summary="Simulate infrastructure impact on wildlife corridor")
async def simulate_highway(
    request: HighwaySimulateRequest,
    db: Session = Depends(get_db),
) -> dict:
    """
    Runs the fragmentation prediction model on a proposed infrastructure project.

    Input: WKT LINESTRING geometry of the proposed road/railway/township boundary.
    Output: Connectivity loss %, habitat loss ha, species risk, restoration cost,
            AI-generated impact analysis, and mitigation recommendations.

    Compliant with EIA Notification 2006 (MoEFCC) reporting requirements.
    """
    global _scenario_counter
    t0 = time.time()

    # Resolve target corridor
    corridor = None
    if request.corridor_id:
        corridor = get_corridor_by_id(request.corridor_id)
    if not corridor:
        # Default to most critical corridor (Bannerghatta-Cauvery)
        corridor = get_corridor_by_id(2)

    proposal = InfrastructureProposal(
        project_type=request.project_type,
        project_name=request.project_name,
        length_km=_estimate_length_from_wkt(request.geometry_wkt),
        lanes=request.lanes,
        crossings_planned=request.crossings_planned,
        traffic_volume=request.traffic_volume,
        corridor_id=corridor["id"] if corridor else None,
    )

    # Run fragmentation model
    impact = predict_impact(
        proposal,
        corridor_connectivity_score=corridor["connectivity_score"] if corridor else 70.0,
        species_list=corridor["species_supported"] if corridor else None,
    )

    # Generate AI explanation
    metrics_dict = {
        "connectivity_loss_pct": impact.connectivity_loss_pct,
        "habitat_loss_ha": impact.habitat_loss_ha,
        "fragmentation_index": impact.fragmentation_index,
        "elephant_passage_risk": impact.elephant_passage_risk,
        "tiger_corridor_break": impact.tiger_corridor_break,
        "restoration_cost_cr": impact.restoration_cost_cr,
        "impact_score": impact.impact_score,
    }

    ai_analysis = await explain_impact(
        corridor_name=corridor["name"] if corridor else "Karnataka corridor",
        project_type=request.project_type,
        project_name=request.project_name,
        metrics=metrics_dict,
        recommendations=impact.mitigation_recommendations,
    )

    elapsed = round(time.time() - t0, 3)

    scenario = {
        "scenario_id": _scenario_counter,
        "corridor_affected": corridor["name"] if corridor else None,
        "metrics": {
            "connectivity_loss_pct": impact.connectivity_loss_pct,
            "habitat_loss_ha": impact.habitat_loss_ha,
            "fragmentation_index": impact.fragmentation_index,
            "elephant_passage_risk": impact.elephant_passage_risk,
            "tiger_corridor_break": impact.tiger_corridor_break,
            "restoration_cost_cr": impact.restoration_cost_cr,
            "impact_score": impact.impact_score,
            "risk_level": impact.risk_level,
        },
        "mitigation_recommendations": impact.mitigation_recommendations,
        "ai_analysis": ai_analysis,
        "species_at_risk": impact.species_at_risk,
        "computation_time_s": elapsed,
        "project_name": request.project_name,
        "project_type": request.project_type,
    }

    _scenario_store.append(scenario)
    _scenario_counter += 1

    return scenario


@router.get("/scenarios", summary="List all saved impact scenarios")
async def list_scenarios() -> list[dict]:
    """Returns all previously computed infrastructure impact scenarios."""
    return [
        {
            "scenario_id": s["scenario_id"],
            "project_name": s.get("project_name", "Unnamed"),
            "project_type": s.get("project_type"),
            "corridor_affected": s["corridor_affected"],
            "impact_score": s["metrics"]["impact_score"],
            "risk_level": s["metrics"]["risk_level"],
            "connectivity_loss_pct": s["metrics"]["connectivity_loss_pct"],
        }
        for s in _scenario_store
    ]


@router.get("/scenarios/{scenario_id}", summary="Get saved scenario detail")
async def get_scenario(scenario_id: int) -> dict:
    for s in _scenario_store:
        if s["scenario_id"] == scenario_id:
            return s
    raise HTTPException(status_code=404, detail=f"Scenario {scenario_id} not found")


def _estimate_length_from_wkt(wkt: str) -> float:
    """
    Quick approximation of linestring length from WKT coordinates.
    Proper calculation uses PostGIS ST_Length in production.
    """
    try:
        from app.ml.gnn_connectivity import haversine_km
        coords_str = wkt.replace("LINESTRING(", "").replace(")", "").strip()
        pairs = [p.strip().split() for p in coords_str.split(",")]
        points = [(float(p[1]), float(p[0])) for p in pairs if len(p) >= 2]
        total = 0.0
        for i in range(len(points) - 1):
            total += haversine_km(*points[i], *points[i + 1])
        return round(total, 2) if total > 0 else 28.0
    except Exception:
        return 28.0  # default 28km
