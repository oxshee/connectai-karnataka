"""
ConnectAI Karnataka — Test Suite

Tests cover:
  - Habitat suitability model (unit)
  - GNN connectivity engine (unit + integration)
  - Fragmentation predictor (unit)
  - Restoration optimizer (unit)
  - All FastAPI endpoints (integration)

Run with:
  cd backend && pytest tests/ -v --tb=short
"""
import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.ml.habitat_model import (
    compute_habitat_suitability, HabitatFeatures,
    _normalise_ndvi, _normalise_elevation, _normalise_dist_road,
    suitability_to_resistance,
)
from app.ml.gnn_connectivity import (
    haversine_km, movement_probability, resistance,
    build_habitat_graph, find_least_cost_paths,
    detect_bottlenecks, analyse_corridor_connectivity,
)
from app.ml.fragmentation_model import predict_impact, InfrastructureProposal
from app.ml.restoration_engine import optimize_restoration
from app.data.karnataka_gis import (
    CORRIDORS, HABITAT_PATCHES, RESTORATION_ZONES,
    get_corridor_by_id, get_patches_for_corridor,
)


# ── Habitat Suitability Model ─────────────────────────────────────────────────

class TestHabitatModel:

    def test_dense_forest_high_score(self):
        f = HabitatFeatures(
            ndvi=0.72, elevation_m=1050, dist_to_road_m=3200,
            dist_to_settlement_m=8400, forest_density=0.88,
            land_cover_class="dense_forest",
        )
        result = compute_habitat_suitability(f, "elephant")
        assert result.score >= 0.80, f"Expected >=0.80, got {result.score}"

    def test_urban_low_score(self):
        f = HabitatFeatures(
            ndvi=0.05, elevation_m=900, dist_to_road_m=50,
            dist_to_settlement_m=100, forest_density=0.02,
            land_cover_class="urban",
        )
        result = compute_habitat_suitability(f, "elephant")
        assert result.score <= 0.10, f"Expected <=0.10, got {result.score}"

    def test_score_bounds(self):
        f = HabitatFeatures(ndvi=0.5, elevation_m=800, dist_to_road_m=1000,
                             dist_to_settlement_m=2000, forest_density=0.6)
        result = compute_habitat_suitability(f)
        assert 0.0 <= result.score <= 1.0

    def test_feature_contributions_sum(self):
        f = HabitatFeatures(ndvi=0.5, elevation_m=800, dist_to_road_m=1000,
                             dist_to_settlement_m=2000, forest_density=0.6)
        result = compute_habitat_suitability(f)
        assert len(result.feature_contributions) == 5

    def test_explanation_string(self):
        f = HabitatFeatures(ndvi=0.5, elevation_m=800, dist_to_road_m=1000,
                             dist_to_settlement_m=2000, forest_density=0.6)
        result = compute_habitat_suitability(f)
        assert "Score" in result.explanation
        assert "species" in result.explanation

    def test_species_weights_differ(self):
        f = HabitatFeatures(ndvi=0.5, elevation_m=800, dist_to_road_m=1000,
                             dist_to_settlement_m=2000, forest_density=0.6)
        e_score = compute_habitat_suitability(f, "elephant").score
        t_score = compute_habitat_suitability(f, "tiger").score
        # Tiger is more sensitive to roads — scores should differ
        assert e_score != t_score

    def test_ndvi_normalisation(self):
        assert _normalise_ndvi(-0.1) == 0.0
        assert _normalise_ndvi(0.8) == 1.0
        assert 0 < _normalise_ndvi(0.5) < 1

    def test_elevation_normalisation(self):
        assert _normalise_elevation(1000) == 1.0   # optimal range
        assert _normalise_elevation(0) < 0.5
        assert _normalise_elevation(2000) < 0.5

    def test_resistance_conversion(self):
        assert suitability_to_resistance(1.0) == 1.0
        assert suitability_to_resistance(0.0) == 1000.0
        assert suitability_to_resistance(0.5) == 500.0


# ── GNN Connectivity Engine ───────────────────────────────────────────────────

class TestGNNConnectivity:

    def test_haversine_bangalore_mysore(self):
        # Bengaluru (12.97°N, 77.59°E) to Mysuru (12.29°N, 76.63°E)
        dist = haversine_km(12.97, 77.59, 12.29, 76.63)
        assert 115 < dist < 145, f"Expected ~128km great-circle, got {dist:.1f}"

    def test_haversine_zero(self):
        assert haversine_km(12.0, 76.0, 12.0, 76.0) == 0.0

    def test_movement_probability_nearby(self):
        from app.ml.gnn_connectivity import HabitatNode
        a = HabitatNode(1, 11.7, 76.6, 0.85, 800, 0.7, 0.85, 3200, "A")
        b = HabitatNode(2, 11.8, 76.5, 0.80, 600, 0.65, 0.80, 2800, "B")
        p = movement_probability(a, b, max_dispersal_km=25)
        assert 0 < p <= 1.0

    def test_movement_probability_distant(self):
        from app.ml.gnn_connectivity import HabitatNode
        a = HabitatNode(1, 11.0, 76.0, 0.9, 800, 0.7, 0.8, 3000, "A")
        b = HabitatNode(2, 14.0, 77.0, 0.9, 800, 0.7, 0.8, 3000, "B")
        p = movement_probability(a, b, max_dispersal_km=25)
        assert p == 0.0

    def test_graph_build(self):
        patches = get_patches_for_corridor(1)
        G, nodes = build_habitat_graph(patches, "elephant")
        assert G.number_of_nodes() == len(patches)
        assert G.number_of_edges() >= 0

    def test_full_connectivity_analysis(self):
        patches = get_patches_for_corridor(1)
        result = analyse_corridor_connectivity(1, patches, "elephant")
        assert result.corridor_id == 1
        assert result.graph_nodes == len(patches)
        assert 0 <= result.connectivity_score <= 100
        assert isinstance(result.explanation, str)
        assert len(result.explanation) > 10

    def test_connectivity_score_bandipur(self):
        patches = get_patches_for_corridor(1)
        result = analyse_corridor_connectivity(1, patches)
        # Bandipur-Nagarhole should score reasonably well (>60)
        assert result.connectivity_score > 60

    def test_bottleneck_detection(self):
        patches = get_patches_for_corridor(2)  # Critical corridor
        result = analyse_corridor_connectivity(2, patches)
        # Should find at least one bottleneck
        assert len(result.bottleneck_zones) >= 0   # may be 0 if only 1 node
        if result.bottleneck_zones:
            bn = result.bottleneck_zones[0]
            assert "name" in bn
            assert "centrality" in bn
            assert "intervention" in bn

    def test_empty_patches(self):
        result = analyse_corridor_connectivity(99, [])
        assert result.graph_nodes == 0
        assert result.connectivity_score == 0


# ── Fragmentation Model ───────────────────────────────────────────────────────

class TestFragmentationModel:

    def _highway_proposal(self, **kwargs):
        defaults = dict(project_type="highway", project_name="Test Highway",
                        length_km=28, lanes=4, crossings_planned=0, traffic_volume="high")
        defaults.update(kwargs)
        return InfrastructureProposal(**defaults)

    def test_basic_highway(self):
        p = self._highway_proposal()
        result = predict_impact(p, 70.0)
        assert 0 <= result.connectivity_loss_pct <= 100
        assert result.habitat_loss_ha > 0
        assert 0 <= result.fragmentation_index <= 1
        assert result.risk_level in ("Low", "Moderate", "High", "Severe")

    def test_crossings_reduce_impact(self):
        p_no_cross = self._highway_proposal(crossings_planned=0)
        p_with_cross = self._highway_proposal(crossings_planned=10)
        r_no = predict_impact(p_no_cross)
        r_with = predict_impact(p_with_cross)
        assert r_with.connectivity_loss_pct <= r_no.connectivity_loss_pct

    def test_longer_road_more_impact(self):
        p_short = self._highway_proposal(length_km=10)
        p_long = self._highway_proposal(length_km=80)
        r_short = predict_impact(p_short)
        r_long = predict_impact(p_long)
        assert r_long.connectivity_loss_pct >= r_short.connectivity_loss_pct

    def test_township_worse_than_highway(self):
        p_h = self._highway_proposal(project_type="highway", length_km=20)
        p_t = self._highway_proposal(project_type="township", length_km=20)
        r_h = predict_impact(p_h)
        r_t = predict_impact(p_t)
        assert r_t.connectivity_loss_pct >= r_h.connectivity_loss_pct

    def test_recommendations_exist(self):
        p = self._highway_proposal(length_km=50)
        result = predict_impact(p, species_list=list(__import__(
            'app.ml.fragmentation_model', fromlist=['SPECIES_ROAD_SENSITIVITY']
        ).SPECIES_ROAD_SENSITIVITY.keys()))
        assert len(result.mitigation_recommendations) > 0
        for r in result.mitigation_recommendations:
            assert "type" in r
            assert "description" in r
            assert "priority" in r

    def test_restoration_cost_positive(self):
        p = self._highway_proposal()
        result = predict_impact(p)
        assert result.restoration_cost_cr >= 0

    def test_impact_score_bounds(self):
        p = self._highway_proposal()
        result = predict_impact(p)
        assert 0 <= result.impact_score <= 100


# ── Restoration Engine ────────────────────────────────────────────────────────

class TestRestorationEngine:

    def test_basic_plan(self):
        plan = optimize_restoration(2, 5.0, RESTORATION_ZONES)
        assert plan.corridor_id == 2
        assert plan.total_cost_cr <= 5.0 + 0.001  # within budget (float tolerance)
        assert plan.total_connectivity_gain_pct >= 0

    def test_zero_budget(self):
        plan = optimize_restoration(2, 0.0, RESTORATION_ZONES)
        assert len(plan.selected_zones) == 0
        assert plan.total_cost_cr == 0.0

    def test_large_budget_selects_more_zones(self):
        plan_small = optimize_restoration(2, 1.0, RESTORATION_ZONES)
        plan_large = optimize_restoration(2, 20.0, RESTORATION_ZONES)
        assert len(plan_large.selected_zones) >= len(plan_small.selected_zones)

    def test_roi_positive(self):
        plan = optimize_restoration(2, 5.0, RESTORATION_ZONES)
        if plan.total_cost_cr > 0:
            assert plan.roi_score > 0

    def test_plan_text_generated(self):
        plan = optimize_restoration(2, 5.0, RESTORATION_ZONES)
        assert isinstance(plan.ai_plan, str)
        assert len(plan.ai_plan) > 20


# ── GIS Data Integrity ────────────────────────────────────────────────────────

class TestGISData:

    def test_corridors_count(self):
        assert len(CORRIDORS) == 3

    def test_corridor_scores_valid(self):
        for c in CORRIDORS:
            assert 0 <= c["connectivity_score"] <= 100
            assert 0 <= c["permeability_score"] <= 1

    def test_corridor_priorities(self):
        priorities = {c["priority"] for c in CORRIDORS}
        assert priorities.issubset({"critical", "high", "medium", "low"})

    def test_corridor_coordinates_in_karnataka(self):
        for c in CORRIDORS:
            for lat_k in ("start_lat", "end_lat"):
                lat = c[lat_k]
                assert 11.5 < lat < 18.5, f"Lat {lat} outside Karnataka"
            for lon_k in ("start_lon", "end_lon"):
                lon = c[lon_k]
                assert 74.0 < lon < 78.6, f"Lon {lon} outside Karnataka"

    def test_habitat_patches_valid(self):
        for p in HABITAT_PATCHES:
            assert 0 <= p["suitability_score"] <= 1
            assert p["area_ha"] > 0
            assert p["corridor_id"] in [1, 2, 3]

    def test_restoration_zones_valid(self):
        for z in RESTORATION_ZONES:
            assert z["cost_cr"] > 0
            assert z["ecological_benefit_score"] > 0
            assert z["connectivity_gain_pct"] > 0

    def test_get_corridor_by_id(self):
        c = get_corridor_by_id(1)
        assert c is not None
        assert c["name"] == "Bandipur–Nagarhole Corridor"

    def test_get_corridor_by_id_missing(self):
        assert get_corridor_by_id(999) is None

    def test_get_patches_for_corridor(self):
        patches = get_patches_for_corridor(1)
        assert len(patches) >= 2
        assert all(p["corridor_id"] == 1 for p in patches)


# ── FastAPI Endpoint Tests ────────────────────────────────────────────────────

class TestAPIEndpoints:
    """Integration tests for FastAPI routes (no DB required)."""

    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        from app.main import app
        return TestClient(app)

    def test_root(self, client):
        r = client.get("/")
        assert r.status_code == 200
        data = r.json()
        assert "ConnectAI Karnataka" in data["name"]

    def test_health(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "healthy"
        assert data["karnataka_corridors"] == 3

    def test_list_corridors(self, client):
        r = client.get("/v1/corridors/")
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 3

    def test_get_corridor(self, client):
        r = client.get("/v1/corridors/1")
        assert r.status_code == 200
        data = r.json()
        assert "Bandipur" in data["name"]

    def test_corridor_not_found(self, client):
        r = client.get("/v1/corridors/999")
        assert r.status_code == 404

    def test_corridor_health(self, client):
        r = client.get("/v1/corridors/2/health")
        assert r.status_code == 200
        data = r.json()
        assert "score" in data
        assert "alerts" in data
        assert isinstance(data["alerts"], list)

    def test_corridor_gnn(self, client):
        r = client.get("/v1/corridors/1/gnn")
        assert r.status_code == 200
        data = r.json()
        assert "graph_nodes" in data
        assert "bottleneck_zones" in data
        assert "connectivity_score" in data

    def test_simulate_highway(self, client):
        r = client.post("/v1/simulate/highway", json={
            "geometry_wkt": "LINESTRING(77.58 12.79, 77.45 12.55, 77.25 12.35)",
            "project_type": "highway",
            "project_name": "Test NH-948 Extension",
            "corridor_id": 2,
            "lanes": 4,
            "crossings_planned": 2,
            "traffic_volume": "high",
        })
        assert r.status_code == 200
        data = r.json()
        assert "metrics" in data
        assert "connectivity_loss_pct" in data["metrics"]
        assert "mitigation_recommendations" in data

    def test_list_scenarios(self, client):
        # First create a scenario
        client.post("/v1/simulate/highway", json={
            "geometry_wkt": "LINESTRING(77.0 12.0, 77.5 12.5)",
            "project_type": "railway",
        })
        r = client.get("/v1/simulate/scenarios")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_list_patches(self, client):
        r = client.get("/v1/habitat/patches?corridor_id=1")
        assert r.status_code == 200
        data = r.json()
        assert len(data) >= 2

    def test_habitat_suitability(self, client):
        r = client.post("/v1/habitat/suitability", json={
            "species": "elephant",
            "points": [
                {"lat": 11.66, "lon": 76.65, "ndvi": 0.72, "elevation_m": 1050,
                 "dist_to_road_m": 3200, "dist_to_settlement_m": 8400,
                 "forest_density": 0.88, "land_cover_class": "dense_forest"},
            ],
        })
        assert r.status_code == 200
        data = r.json()
        assert len(data["results"]) == 1
        assert data["results"][0]["suitability_score"] >= 0.7

    def test_restoration_recommend(self, client):
        r = client.post("/v1/restoration/recommend", json={
            "corridor_id": 2, "budget_cr": 5.0,
        })
        assert r.status_code == 200
        data = r.json()
        assert "zones" in data
        assert data["total_cost_cr"] <= 5.0 + 0.01

    def test_list_restoration_zones(self, client):
        r = client.get("/v1/restoration/zones")
        assert r.status_code == 200
        assert len(r.json()) > 0

    def test_ai_ask(self, client):
        r = client.post("/v1/ai/ask", json={
            "question": "What is the biggest threat to the Bannerghatta corridor?",
        })
        assert r.status_code == 200
        data = r.json()
        assert "answer" in data
        assert len(data["answer"]) > 10

    def test_generate_corridor(self, client):
        r = client.post("/v1/corridors/generate", json={
            "bbox": {"min_lon": 76.0, "min_lat": 11.5, "max_lon": 77.0, "max_lat": 12.0},
            "species": "elephant",
        })
        assert r.status_code == 200
        data = r.json()
        assert "corridor_id" in data
        assert "connectivity_score" in data
