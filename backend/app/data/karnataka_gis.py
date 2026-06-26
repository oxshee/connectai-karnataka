"""
ConnectAI Karnataka — Karnataka GIS Dataset

Real Karnataka wildlife corridor data based on published research:
  - Wildlife Institute of India corridor reports
  - Karnataka Forest Department boundaries
  - Published Elephant/Tiger corridor studies

All coordinates are in WGS84 (EPSG:4326).
This module provides authoritative seed data that is loaded into PostGIS
on first startup, AND also used as the in-memory fallback when PostGIS
is not available (demo / development mode).
"""
from __future__ import annotations
import json
from dataclasses import dataclass, field


# ── Karnataka's 3 priority corridors ────────────────────────────────────────
# Source: Wildlife Institute of India, Karnataka Forest Dept

CORRIDORS = [
    {
        "id": 1,
        "name": "Bandipur–Nagarhole Corridor",
        "start_name": "Bandipur National Park",
        "end_name": "Nagarhole National Park",
        "description": (
            "Core tiger and elephant corridor connecting two of Karnataka's most "
            "important protected areas. Part of the Nilgiri Biosphere Reserve — "
            "largest contiguous forest block in South Asia."
        ),
        "start_lat": 11.689, "start_lon": 76.634,
        "end_lat": 11.944, "end_lon": 76.095,
        "length_km": 45.2,
        "connectivity_score": 82.0,
        "permeability_score": 0.82,
        "ndvi_mean": 0.61,
        "forest_cover_pct": 68.0,
        "priority": "medium",
        "species_supported": ["Elephas maximus", "Panthera tigris", "Panthera pardus",
                               "Cuon alpinus", "Bos gaurus"],
        # WKT linestring approximation (simplified corridor centerline)
        "geometry_wkt": (
            "MULTILINESTRING((76.634 11.689, 76.550 11.720, 76.480 11.780, "
            "76.380 11.820, 76.250 11.870, 76.150 11.910, 76.095 11.944))"
        ),
        "permeability_zones": [
            {"zone": "Z1-Bandipur core", "score": 85},
            {"zone": "Z2-Highway NH-766 crossing", "score": 62},
            {"zone": "Z3-Maddur scrubland", "score": 80},
            {"zone": "Z4-Gundlupet fringe", "score": 61},
            {"zone": "Z5-Transition forest", "score": 78},
            {"zone": "Z6-Nagarhole core", "score": 90},
        ],
        "alerts": [],
    },
    {
        "id": 2,
        "name": "Bannerghatta–Cauvery Corridor",
        "start_name": "Bannerghatta National Park",
        "end_name": "Cauvery Wildlife Sanctuary",
        "description": (
            "Critically threatened corridor near Bengaluru. Connects urban-edge "
            "Bannerghatta NP to the Cauvery river forests. Faces intense pressure "
            "from Bengaluru's southward expansion, NH-948, and quarrying activity."
        ),
        "start_lat": 12.796, "start_lon": 77.581,
        "end_lat": 12.210, "end_lon": 77.182,
        "length_km": 62.4,
        "connectivity_score": 54.0,
        "permeability_score": 0.54,
        "ndvi_mean": 0.38,
        "forest_cover_pct": 41.0,
        "priority": "critical",
        "species_supported": ["Elephas maximus", "Ursus ursinus", "Canis aureus",
                               "Hystrix indica", "Axis axis"],
        "geometry_wkt": (
            "MULTILINESTRING((77.581 12.796, 77.520 12.710, 77.460 12.620, "
            "77.400 12.530, 77.330 12.440, 77.260 12.360, 77.182 12.210))"
        ),
        "permeability_zones": [
            {"zone": "Z1-Bannerghatta buffer", "score": 48},
            {"zone": "Z2-NH-948 crossing", "score": 28},
            {"zone": "Z3-Anekal scrubland", "score": 51},
            {"zone": "Z4-Kanakapura forest", "score": 70},
            {"zone": "Z5-Malavalli transition", "score": 64},
            {"zone": "Z6-Cauvery riverine", "score": 72},
        ],
        "alerts": [
            "NH-948 expansion proposal threatens Z2 crossing — impact score 73%",
            "Quarrying activity detected within 500m of corridor Z3",
            "Elephant–human conflict events up 34% in Anekal (2024)",
        ],
    },
    {
        "id": 3,
        "name": "Brahmagiri–Wayanad Corridor",
        "start_name": "Brahmagiri Wildlife Sanctuary",
        "end_name": "Wayanad Wildlife Sanctuary",
        "description": (
            "Cross-state corridor linking Karnataka's Brahmagiri hills with Kerala's "
            "Wayanad sanctuary. Critical for maintaining genetic connectivity of "
            "tiger meta-population across the Western Ghats."
        ),
        "start_lat": 12.053, "start_lon": 75.797,
        "end_lat": 11.690, "end_lon": 76.130,
        "length_km": 38.7,
        "connectivity_score": 71.0,
        "permeability_score": 0.71,
        "ndvi_mean": 0.71,
        "forest_cover_pct": 74.0,
        "priority": "high",
        "species_supported": ["Panthera tigris", "Panthera pardus", "Elephas maximus",
                               "Cuon alpinus", "Neofelis nebulosa"],
        "geometry_wkt": (
            "MULTILINESTRING((75.797 12.053, 75.860 11.990, 75.930 11.920, "
            "76.000 11.860, 76.060 11.790, 76.100 11.740, 76.130 11.690))"
        ),
        "permeability_zones": [
            {"zone": "Z1-Brahmagiri core", "score": 82},
            {"zone": "Z2-Thirunelli transition", "score": 68},
            {"zone": "Z3-Coorg coffee estates", "score": 55},
            {"zone": "Z4-Kutta junction", "score": 61},
            {"zone": "Z5-Wayanad buffer", "score": 78},
            {"zone": "Z6-Wayanad core", "score": 88},
        ],
        "alerts": [
            "Coffee estate expansion reducing permeable cover in Z3",
        ],
    },
]

# ── Habitat patches (nodes in the connectivity graph) ───────────────────────

HABITAT_PATCHES = [
    # Corridor 1: Bandipur–Nagarhole
    {"id": 101, "corridor_id": 1, "name": "Bandipur Core Forest", "area_ha": 874.5,
     "centroid_lat": 11.66, "centroid_lon": 76.65, "suitability_score": 0.91,
     "ndvi": 0.72, "elevation_m": 1050, "forest_density": 0.88,
     "dist_to_road_m": 3200, "dist_to_settlement_m": 8400, "land_cover_class": "dense_forest"},
    {"id": 102, "corridor_id": 1, "name": "Gundlupet Scrub Patch", "area_ha": 143.2,
     "centroid_lat": 11.74, "centroid_lon": 76.51, "suitability_score": 0.64,
     "ndvi": 0.44, "elevation_m": 920, "forest_density": 0.52,
     "dist_to_road_m": 480, "dist_to_settlement_m": 2100, "land_cover_class": "scrub"},
    {"id": 103, "corridor_id": 1, "name": "Maddur Forest Block", "area_ha": 312.0,
     "centroid_lat": 11.80, "centroid_lon": 76.40, "suitability_score": 0.78,
     "ndvi": 0.58, "elevation_m": 980, "forest_density": 0.74,
     "dist_to_road_m": 1200, "dist_to_settlement_m": 4500, "land_cover_class": "mixed_deciduous"},
    {"id": 104, "corridor_id": 1, "name": "Nagarhole Buffer", "area_ha": 628.3,
     "centroid_lat": 11.92, "centroid_lon": 76.12, "suitability_score": 0.87,
     "ndvi": 0.68, "elevation_m": 880, "forest_density": 0.84,
     "dist_to_road_m": 2800, "dist_to_settlement_m": 6200, "land_cover_class": "dense_forest"},
    # Corridor 2: Bannerghatta–Cauvery
    {"id": 201, "corridor_id": 2, "name": "Bannerghatta Buffer Zone", "area_ha": 218.6,
     "centroid_lat": 12.74, "centroid_lon": 77.55, "suitability_score": 0.48,
     "ndvi": 0.32, "elevation_m": 780, "forest_density": 0.38,
     "dist_to_road_m": 120, "dist_to_settlement_m": 450, "land_cover_class": "scrub"},
    {"id": 202, "corridor_id": 2, "name": "Anekal Forest Fragment", "area_ha": 89.4,
     "centroid_lat": 12.63, "centroid_lon": 77.46, "suitability_score": 0.31,
     "ndvi": 0.22, "elevation_m": 820, "forest_density": 0.28,
     "dist_to_road_m": 60, "dist_to_settlement_m": 320, "land_cover_class": "degraded_scrub"},
    {"id": 203, "corridor_id": 2, "name": "Kanakapura Forest", "area_ha": 476.8,
     "centroid_lat": 12.41, "centroid_lon": 77.42, "suitability_score": 0.72,
     "ndvi": 0.55, "elevation_m": 740, "forest_density": 0.68,
     "dist_to_road_m": 890, "dist_to_settlement_m": 3200, "land_cover_class": "mixed_deciduous"},
    {"id": 204, "corridor_id": 2, "name": "Cauvery Riverine Forest", "area_ha": 354.1,
     "centroid_lat": 12.23, "centroid_lon": 77.21, "suitability_score": 0.76,
     "ndvi": 0.62, "elevation_m": 680, "forest_density": 0.72,
     "dist_to_road_m": 1400, "dist_to_settlement_m": 2800, "land_cover_class": "riparian"},
    # Corridor 3: Brahmagiri–Wayanad
    {"id": 301, "corridor_id": 3, "name": "Brahmagiri Core", "area_ha": 1124.7,
     "centroid_lat": 12.04, "centroid_lon": 75.82, "suitability_score": 0.88,
     "ndvi": 0.76, "elevation_m": 1420, "forest_density": 0.90,
     "dist_to_road_m": 4200, "dist_to_settlement_m": 9800, "land_cover_class": "evergreen"},
    {"id": 302, "corridor_id": 3, "name": "Coorg Transition Zone", "area_ha": 267.3,
     "centroid_lat": 11.92, "centroid_lon": 75.95, "suitability_score": 0.58,
     "ndvi": 0.48, "elevation_m": 1180, "forest_density": 0.55,
     "dist_to_road_m": 680, "dist_to_settlement_m": 1800, "land_cover_class": "coffee_estate"},
    {"id": 303, "corridor_id": 3, "name": "Wayanad Buffer", "area_ha": 892.6,
     "centroid_lat": 11.73, "centroid_lon": 76.11, "suitability_score": 0.83,
     "ndvi": 0.70, "elevation_m": 960, "forest_density": 0.82,
     "dist_to_road_m": 2100, "dist_to_settlement_m": 5600, "land_cover_class": "dense_forest"},
]

# ── Roads affecting corridors ────────────────────────────────────────────────

ROADS = [
    {"id": 1, "name": "NH-766 (Mysuru–Kozhikode)", "road_type": "national_highway",
     "highway_class": "NH", "lanes": 4, "traffic_volume": "high",
     "has_wildlife_crossing": False,
     "geometry_wkt": "LINESTRING(76.634 11.689, 76.400 11.750, 76.200 11.830, 76.095 11.944)"},
    {"id": 2, "name": "NH-948 (Bengaluru–Kanakapura)", "road_type": "national_highway",
     "highway_class": "NH", "lanes": 4, "traffic_volume": "high",
     "has_wildlife_crossing": False,
     "geometry_wkt": "LINESTRING(77.581 12.796, 77.480 12.600, 77.350 12.420, 77.182 12.210)"},
    {"id": 3, "name": "SH-17 (Mysuru–Coorg)", "road_type": "state_highway",
     "highway_class": "SH", "lanes": 2, "traffic_volume": "medium",
     "has_wildlife_crossing": False,
     "geometry_wkt": "LINESTRING(76.634 11.689, 75.980 11.800, 75.797 12.053)"},
    {"id": 4, "name": "Mysuru–Bengaluru Railway", "road_type": "railway",
     "highway_class": "railway", "lanes": 2, "traffic_volume": "medium",
     "has_wildlife_crossing": False,
     "geometry_wkt": "LINESTRING(77.581 12.796, 77.100 12.400, 76.650 12.100, 76.634 11.689)"},
]

# ── Restoration zones ────────────────────────────────────────────────────────

RESTORATION_ZONES = [
    {"id": 1, "corridor_id": 2, "name": "Bannerghatta Buffer Reforestation",
     "method": "reforestation", "area_ha": 340.0, "cost_cr": 1.8,
     "ecological_benefit_score": 9.2, "connectivity_gain_pct": 12.0, "priority_rank": 1,
     "native_species": ["Tectona grandis", "Dalbergia latifolia", "Terminalia bellirica",
                        "Ficus benghalensis", "Grewia tiliaefolia"],
     "implementation_years": 5,
     "notes": "Plant native dry deciduous species. Focus on Z1-Z2 bottleneck area.",
     "geometry_wkt": "POLYGON((77.56 12.78, 77.58 12.78, 77.58 12.76, 77.56 12.76, 77.56 12.78))"},
    {"id": 2, "corridor_id": 2, "name": "NH-948 Elephant Underpasses",
     "method": "wildlife_crossing", "area_ha": 0.5, "cost_cr": 2.4,
     "ecological_benefit_score": 8.7, "connectivity_gain_pct": 18.0, "priority_rank": 2,
     "native_species": [],
     "implementation_years": 2,
     "notes": "3 underpasses of 10m width × 5m height at km 28, 34, 41. Lighting-free zones.",
     "geometry_wkt": "POLYGON((77.48 12.61, 77.50 12.61, 77.50 12.60, 77.48 12.60, 77.48 12.61))"},
    {"id": 3, "corridor_id": 2, "name": "Cauvery River Riparian Restoration",
     "method": "riparian", "area_ha": 680.0, "cost_cr": 0.9,
     "ecological_benefit_score": 7.9, "connectivity_gain_pct": 8.0, "priority_rank": 3,
     "native_species": ["Phoenix loureiroi", "Bambusa bambos", "Acacia chundra",
                        "Diospyros melanoxylon"],
     "implementation_years": 3,
     "notes": "Riparian strip restoration along Cauvery tributaries for movement continuity.",
     "geometry_wkt": "POLYGON((77.19 12.22, 77.21 12.22, 77.21 12.20, 77.19 12.20, 77.19 12.22))"},
    {"id": 4, "corridor_id": 3, "name": "Brahmagiri–Wayanad Corridor Fencing",
     "method": "buffer_zone", "area_ha": 0.0, "cost_cr": 0.6,
     "ecological_benefit_score": 8.1, "connectivity_gain_pct": 6.0, "priority_rank": 4,
     "native_species": [],
     "implementation_years": 1,
     "notes": "12km solar-powered electric fence to reduce human–wildlife conflict in Z3.",
     "geometry_wkt": "POLYGON((75.93 11.93, 75.96 11.93, 75.96 11.91, 75.93 11.91, 75.93 11.93))"},
    {"id": 5, "corridor_id": 1, "name": "Gundlupet Scrub Corridor Enhancement",
     "method": "reforestation", "area_ha": 143.2, "cost_cr": 0.7,
     "ecological_benefit_score": 7.4, "connectivity_gain_pct": 5.0, "priority_rank": 5,
     "native_species": ["Acacia chundra", "Hardwickia binata", "Chloroxylon swietenia"],
     "implementation_years": 4,
     "notes": "Plant drought-tolerant native species in Z4 scrubland to improve permeability.",
     "geometry_wkt": "POLYGON((76.50 11.73, 76.52 11.73, 76.52 11.71, 76.50 11.71, 76.50 11.73))"},
]

# ── Species reference data ───────────────────────────────────────────────────

SPECIES_PROFILES = {
    "Elephas maximus": {
        "common": "Asian Elephant", "family": "Elephantidae",
        "min_habitat_area_ha": 100, "movement_range_km": 80,
        "road_sensitivity": "high", "corridors": [1, 2, 3],
        "iucn": "EN",
    },
    "Panthera tigris": {
        "common": "Bengal Tiger", "family": "Felidae",
        "min_habitat_area_ha": 500, "movement_range_km": 120,
        "road_sensitivity": "very_high", "corridors": [1, 3],
        "iucn": "EN",
    },
    "Panthera pardus": {
        "common": "Indian Leopard", "family": "Felidae",
        "min_habitat_area_ha": 50, "movement_range_km": 60,
        "road_sensitivity": "medium", "corridors": [1, 2, 3],
        "iucn": "VU",
    },
    "Cuon alpinus": {
        "common": "Dhole (Wild Dog)", "family": "Canidae",
        "min_habitat_area_ha": 200, "movement_range_km": 50,
        "road_sensitivity": "high", "corridors": [1, 3],
        "iucn": "EN",
    },
}


def get_corridor_by_id(corridor_id: int) -> dict | None:
    for c in CORRIDORS:
        if c["id"] == corridor_id:
            return c
    return None


def get_patches_for_corridor(corridor_id: int) -> list[dict]:
    return [p for p in HABITAT_PATCHES if p["corridor_id"] == corridor_id]
