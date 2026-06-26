"""
ConnectAI Karnataka — Habitat Suitability & Restoration API Routes

POST /habitat/suitability       Score habitat points
GET  /habitat/patches           List all habitat patches
GET  /habitat/patches/{id}      Get patch detail

POST /restoration/recommend     Optimise restoration plan
GET  /restoration/zones         List all restoration zones
GET  /restoration/zones/{id}    Get zone detail
"""
from __future__ import annotations
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.data.karnataka_gis import HABITAT_PATCHES, RESTORATION_ZONES, get_corridor_by_id
from app.ml.habitat_model import compute_habitat_suitability, HabitatFeatures
from app.ml.restoration_engine import optimize_restoration
from app.services.explainability import explain_restoration

logger = logging.getLogger(__name__)

# ── Habitat Router ───────────────────────────────────────────────────────────

habitat_router = APIRouter(prefix="/habitat", tags=["Habitat Suitability"])


@habitat_router.post("/suitability", summary="Score habitat suitability at given points")
async def habitat_suitability(payload: dict, db: Session = Depends(get_db)) -> dict:
    """
    Computes habitat suitability score for one or more geographic points.
    Uses the Random Forest–based model with NDVI, elevation, road distance inputs.
    Returns per-feature SHAP-style contributions for explainability.
    """
    points = payload.get("points", [])
    species = payload.get("species", "all")

    results = []
    for pt in points:
        features = HabitatFeatures(
            ndvi=pt.get("ndvi", 0.4),
            elevation_m=pt.get("elevation_m", 900),
            dist_to_road_m=pt.get("dist_to_road_m", 1000),
            dist_to_settlement_m=pt.get("dist_to_settlement_m", 2000),
            forest_density=pt.get("forest_density", 0.5),
            land_cover_class=pt.get("land_cover_class", "scrub"),
        )
        scored = compute_habitat_suitability(features, species)
        results.append({
            "lat": pt.get("lat"),
            "lon": pt.get("lon"),
            "suitability_score": scored.score,
            "feature_contributions": scored.feature_contributions,
            "explanation": scored.explanation,
            "land_cover": pt.get("land_cover_class", "scrub"),
        })

    return {
        "species": species,
        "results": results,
        "model_version": "HSM-v1.0-Karnataka",
        "model_accuracy": 0.84,
    }


@habitat_router.get("/patches", summary="List habitat patches")
async def list_patches(
    corridor_id: int | None = Query(None),
    min_suitability: float = Query(0.0, ge=0, le=1),
    db: Session = Depends(get_db),
) -> list[dict]:
    patches = HABITAT_PATCHES
    if corridor_id:
        patches = [p for p in patches if p["corridor_id"] == corridor_id]
    patches = [p for p in patches if p["suitability_score"] >= min_suitability]
    return patches


@habitat_router.get("/patches/{patch_id}", summary="Get habitat patch detail")
async def get_patch(patch_id: int, db: Session = Depends(get_db)) -> dict:
    patch = next((p for p in HABITAT_PATCHES if p["id"] == patch_id), None)
    if not patch:
        raise HTTPException(status_code=404, detail=f"Patch {patch_id} not found")

    features = HabitatFeatures(
        ndvi=patch["ndvi"],
        elevation_m=patch["elevation_m"],
        dist_to_road_m=patch["dist_to_road_m"],
        dist_to_settlement_m=patch["dist_to_settlement_m"],
        forest_density=patch["forest_density"],
        land_cover_class=patch["land_cover_class"],
    )
    scored = compute_habitat_suitability(features)
    return {
        **patch,
        "computed_suitability": scored.score,
        "feature_contributions": scored.feature_contributions,
        "explanation": scored.explanation,
    }


# ── Restoration Router ───────────────────────────────────────────────────────

restoration_router = APIRouter(prefix="/restoration", tags=["Restoration"])


@restoration_router.post("/recommend", summary="Optimise restoration plan within budget")
async def recommend_restoration(payload: dict, db: Session = Depends(get_db)) -> dict:
    """
    Returns a cost-benefit optimised list of restoration zones within the given budget.
    Uses a greedy knapsack algorithm maximising ecological benefit per rupee.
    Includes AI-generated restoration action plan with planting recommendations.
    """
    corridor_id = payload.get("corridor_id", 2)
    budget_cr = float(payload.get("budget_cr", 5.0))
    priority_method = payload.get("priority_method", "ecological_benefit")

    corridor = get_corridor_by_id(corridor_id)
    if not corridor:
        raise HTTPException(status_code=404, detail=f"Corridor {corridor_id} not found")

    plan = optimize_restoration(corridor_id, budget_cr, RESTORATION_ZONES, priority_method)

    # AI restoration plan
    ai_plan = await explain_restoration(
        corridor_name=corridor["name"],
        zones=plan.selected_zones,
        budget_cr=budget_cr,
        connectivity_gain=plan.total_connectivity_gain_pct,
    )

    return {
        "corridor_id": corridor_id,
        "budget_cr": budget_cr,
        "zones": plan.selected_zones,
        "total_cost_cr": plan.total_cost_cr,
        "total_connectivity_gain_pct": plan.total_connectivity_gain_pct,
        "total_area_ha": plan.total_area_ha,
        "ai_plan": ai_plan,
        "roi_score": plan.roi_score,
    }


@restoration_router.get("/zones", summary="List all restoration zones")
async def list_zones(
    corridor_id: int | None = Query(None),
    method: str | None = Query(None),
    db: Session = Depends(get_db),
) -> list[dict]:
    zones = RESTORATION_ZONES
    if corridor_id:
        zones = [z for z in zones if z["corridor_id"] == corridor_id]
    if method:
        zones = [z for z in zones if z["method"] == method]
    return sorted(zones, key=lambda z: z["priority_rank"])


@restoration_router.get("/zones/{zone_id}", summary="Get restoration zone detail")
async def get_zone(zone_id: int, db: Session = Depends(get_db)) -> dict:
    zone = next((z for z in RESTORATION_ZONES if z["id"] == zone_id), None)
    if not zone:
        raise HTTPException(status_code=404, detail=f"Zone {zone_id} not found")
    return zone
