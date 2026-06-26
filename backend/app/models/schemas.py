"""
ConnectAI Karnataka — Pydantic Schemas (API request/response models)
"""
from __future__ import annotations
from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field, field_validator


# ── Geometry helpers ─────────────────────────────────────────────────────────

class GeoPoint(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)


class BoundingBox(BaseModel):
    min_lon: float
    min_lat: float
    max_lon: float
    max_lat: float

    @field_validator("max_lon")
    @classmethod
    def lon_order(cls, v, info):
        if "min_lon" in info.data and v <= info.data["min_lon"]:
            raise ValueError("max_lon must be > min_lon")
        return v


# ── Corridor schemas ─────────────────────────────────────────────────────────

class CorridorBase(BaseModel):
    name: str
    start_name: str
    end_name: str
    description: str | None = None
    species_supported: list[str] = []


class CorridorResponse(CorridorBase):
    id: int
    connectivity_score: float
    permeability_score: float
    ndvi_mean: float | None
    forest_cover_pct: float | None
    length_km: float | None
    priority: str
    start_lat: float | None
    start_lon: float | None
    end_lat: float | None
    end_lon: float | None
    last_analyzed: datetime | None
    geometry_wkt: str | None = None   # returned when ?include_geometry=true

    model_config = {"from_attributes": True}


class CorridorHealthResponse(BaseModel):
    corridor_id: int
    name: str
    score: float
    ndvi: float | None
    forest_cover_pct: float | None
    trend: str                           # "improving"|"stable"|"declining"
    priority: str
    alerts: list[str]
    permeability_by_zone: list[dict[str, Any]]
    species_at_risk: list[str]
    last_updated: datetime


# ── Corridor generation ──────────────────────────────────────────────────────

class CorridorGenerateRequest(BaseModel):
    bbox: BoundingBox
    species: str = Field(default="all", description="Target species filter")
    resolution_m: int = Field(default=100, ge=30, le=1000)
    include_geometry: bool = True


class CorridorGenerateResponse(BaseModel):
    corridor_id: int
    priority_score: float
    connectivity_score: float
    permeability_score: float
    path_wkt: str | None
    habitat_patches_count: int
    graph_nodes: int
    graph_edges: int
    computation_time_s: float
    explanation: str


# ── Impact simulation ────────────────────────────────────────────────────────

class HighwaySimulateRequest(BaseModel):
    geometry_wkt: str = Field(
        ...,
        description="WKT LINESTRING of proposed road/railway",
        example="LINESTRING(77.5 12.0, 77.8 12.3, 78.0 12.5)",
    )
    project_type: str = Field(default="highway")
    project_name: str = Field(default="Unnamed project")
    corridor_id: int | None = None
    lanes: int = Field(default=4, ge=2, le=8)
    crossings_planned: int = Field(default=0, ge=0)
    traffic_volume: str = Field(default="high")


class ImpactMetrics(BaseModel):
    connectivity_loss_pct: float
    habitat_loss_ha: float
    fragmentation_index: float          # 0–1
    elephant_passage_risk: str
    tiger_corridor_break: bool
    restoration_cost_cr: float
    impact_score: float                 # composite 0–100
    risk_level: str                     # "Severe"|"High"|"Moderate"|"Low"


class HighwaySimulateResponse(BaseModel):
    scenario_id: int
    corridor_affected: str | None
    metrics: ImpactMetrics
    mitigation_recommendations: list[dict[str, Any]]
    ai_analysis: str
    species_at_risk: list[str]
    computation_time_s: float


# ── Habitat suitability ──────────────────────────────────────────────────────

class HabitatSuitabilityRequest(BaseModel):
    points: list[GeoPoint]
    species: str = "elephant"


class HabitatSuitabilityResult(BaseModel):
    lat: float
    lon: float
    suitability_score: float            # 0–1
    ndvi: float | None
    elevation_m: float | None
    dist_to_road_m: float | None
    land_cover: str | None
    explanation: str


class HabitatSuitabilityResponse(BaseModel):
    species: str
    results: list[HabitatSuitabilityResult]
    model_version: str
    model_accuracy: float


# ── Restoration ──────────────────────────────────────────────────────────────

class RestorationRequest(BaseModel):
    corridor_id: int
    budget_cr: float = Field(..., ge=0.1, le=500)
    priority_method: str = Field(
        default="ecological_benefit",
        description="'ecological_benefit'|'cost_efficiency'|'connectivity_gain'",
    )


class RestorationZoneOut(BaseModel):
    id: int
    name: str
    method: str
    area_ha: float
    cost_cr: float
    ecological_benefit_score: float
    connectivity_gain_pct: float
    priority_rank: int
    native_species: list[str]
    implementation_years: int
    geometry_wkt: str | None = None

    model_config = {"from_attributes": True}


class RestorationResponse(BaseModel):
    corridor_id: int
    budget_cr: float
    zones: list[RestorationZoneOut]
    total_cost_cr: float
    total_connectivity_gain_pct: float
    total_area_ha: float
    ai_plan: str
    roi_score: float                    # benefit / cost


# ── GNN model info ───────────────────────────────────────────────────────────

class GNNAnalysisResponse(BaseModel):
    corridor_id: int
    habitat_patches: int
    graph_nodes: int
    graph_edges: int
    least_cost_paths: list[dict[str, Any]]
    bottleneck_zones: list[dict[str, Any]]
    model_accuracy: float
    explanation: str


# ── System health ────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    version: str
    database: str
    models_loaded: dict[str, bool]
    karnataka_corridors: int
    habitat_patches: int
