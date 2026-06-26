# ConnectAI Karnataka — Technical Documentation

> **AI-Powered Ecological Corridor Intelligence Platform**
> *Predicting, protecting and planning wildlife connectivity across Karnataka's fragmented landscapes.*

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [System Architecture](#2-system-architecture)
3. [AI/ML Models](#3-aiml-models)
4. [API Reference](#4-api-reference)
5. [Database Schema (PostGIS)](#5-database-schema-postgis)
6. [GIS Data Sources](#6-gis-data-sources)
7. [Karnataka Corridors](#7-karnataka-corridors)
8. [Deployment Guide](#8-deployment-guide)
9. [Development Setup](#9-development-setup)
10. [Testing](#10-testing)
11. [Explainable AI](#11-explainable-ai)
12. [Roadmap](#12-roadmap)

---

## 1. Project Overview

ConnectAI Karnataka is a decision intelligence platform for wildlife corridor conservation. Unlike tools that simply detect forest loss, ConnectAI provides **predictive and prescriptive intelligence** for conservation planning.

### Core Questions Answered

| Question | Feature |
|----------|---------|
| "If a highway is built here, what happens to elephant movement?" | Impact Simulator |
| "Where should Karnataka invest its conservation budget?" | Restoration Engine |
| "Which corridor is most at risk right now?" | Corridor Intelligence Engine |
| "What is the least-cost wildlife movement path?" | GNN Connectivity |

### Target Users

| User | Need | Primary Feature |
|------|------|----------------|
| Karnataka Forest Department | Corridor prioritisation, evidence for conservation decisions | Dashboard, Corridor Health |
| Infrastructure Planners (NHAI, Railways) | EIA compliance, alternative route analysis | Impact Simulator |
| Conservation NGOs | Restoration targets, funding prioritisation | Restoration Engine |
| Researchers (WII, ATREE) | Spatial analysis, species movement modelling | GNN Analysis, Habitat API |

---

## 2. System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     DATA INGESTION LAYER                        │
├────────────────┬───────────────┬───────────────┬───────────────┤
│ Sentinel-2     │ SRTM DEM      │ OpenStreetMap │ GBIF          │
│ (10m NDVI)     │ (30m elev.)   │ (roads/settle)│ (biodiversity)│
└────────────────┴───────────────┴───────────────┴───────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│              POSTGRESQL + POSTGIS DATABASE                      │
├─────────────────────────────────────────────────────────────────┤
│  corridors │ habitat_patches │ roads │ restoration_zones       │
│  settlements │ species_sightings │ impact_scenarios            │
│                                                                 │
│  ST_Intersection │ ST_Length │ ST_Buffer │ ST_DWithin          │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AI/ML PIPELINE                               │
├─────────────────┬───────────────────┬───────────────────────────┤
│ Habitat         │ GNN Connectivity  │ Fragmentation             │
│ Suitability     │ Engine            │ Predictor                 │
│ Model (HSM)     │ (PyTorch +        │ (Statistical +            │
│                 │  NetworkX)        │  Geometric)               │
│ Input: NDVI,    │                   │                           │
│ elev, roads,    │ Nodes: patches    │ Input: road WKT           │
│ settlements,    │ Edges: movement   │ Output: loss %, cost,     │
│ forest density  │ prob              │ species risk              │
│                 │ Output: LCP,      │                           │
│ Output: 0-1     │ bottlenecks,      │                           │
│ suitability     │ score             │                           │
└─────────────────┴───────────────────┴───────────────────────────┤
│              RESTORATION OPTIMIZER                              │
│  Greedy knapsack: max connectivity gain within ₹ budget        │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                 FASTAPI BACKEND  (Python 3.12)                  │
├─────────────────────────────────────────────────────────────────┤
│  /v1/corridors/*   /v1/simulate/*   /v1/habitat/*              │
│  /v1/restoration/* /v1/ai/*                                    │
│                                                                 │
│  + Claude (Anthropic API) for XAI explanations                 │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│            REACT FRONTEND  (TypeScript + Mapbox GL)            │
├─────────────────────────────────────────────────────────────────┤
│  Dashboard │ Corridor Intelligence │ Impact Simulator           │
│  Restoration Engine │ AI Analysis │ API Reference              │
└─────────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| API Framework | FastAPI 0.115 | Async REST API, auto OpenAPI docs |
| Database | PostgreSQL 15 + PostGIS 3.4 | Spatial data storage and queries |
| ORM | SQLAlchemy 2.0 + GeoAlchemy2 | Python ↔ PostGIS mapping |
| ML — GNN | PyTorch 2.4 + NetworkX 3.3 | Connectivity graph analysis |
| ML — Spatial | GeoPandas, Shapely, Rasterio | GIS processing |
| AI — XAI | Claude (Anthropic API) | Plain-language explanations |
| Frontend | React 18, TypeScript, Mapbox GL | Interactive GIS dashboard |
| Styling | TailwindCSS | UI components |
| Testing | pytest + FastAPI TestClient | 54-test suite |

---

## 3. AI/ML Models

### Model 1: Habitat Suitability Model (HSM)

**Algorithm:** Weighted feature scoring (prototype of Random Forest classifier)

**Inputs per geographic point:**

| Feature | Source | Normalisation |
|---------|--------|--------------|
| NDVI | Sentinel-2 Band 8+4 | 0→0, 0.8→1.0 (sigmoid) |
| Elevation (m) | SRTM 30m DEM | Optimal: 600–1400m = 1.0 |
| Distance to road (m) | OSM + NHDP | >5000m = 1.0, <100m = 0.02 |
| Distance to settlement (m) | OSM + Census | >8000m = 1.0, <200m = 0.02 |
| Forest density (0–1) | Sentinel-2 NDVI thresholding | Direct |

**Species-specific weights (from WII published studies):**

| Feature | Elephant | Tiger | Leopard |
|---------|----------|-------|---------|
| NDVI | 0.28 | 0.22 | 0.18 |
| Distance to road | 0.22 | 0.30 | 0.20 |
| Distance to settlement | 0.18 | 0.22 | 0.25 |
| Forest density | 0.22 | 0.18 | 0.25 |
| Elevation | 0.10 | 0.08 | 0.12 |

**Land cover multipliers:**

| Class | Multiplier |
|-------|-----------|
| Dense forest / Evergreen | 1.00 |
| Mixed deciduous | 0.90 |
| Riparian | 0.85 |
| Coffee estate | 0.60 |
| Scrub | 0.55 |
| Degraded scrub | 0.30 |
| Agriculture | 0.15 |
| Urban | 0.02 |

**Output:** Suitability score 0.0–1.0 + per-feature SHAP-style contributions

---

### Model 2: GNN Corridor Connectivity Engine

**Algorithm:** GraphSAGE-style 1-layer mean neighbourhood aggregation + Dijkstra least-cost paths

**Graph construction:**
- **Nodes:** Habitat patches (each with 5-dimensional feature vector)
- **Edges:** Between patches within dispersal distance, weighted by movement probability
- **Edge weight:** `resistance = 1 / movement_probability`

**Movement probability formula:**
```
P(a→b) = exp(-distance/alpha) × sqrt(suitability_a × suitability_b)

where alpha = species mean dispersal distance / 3
```

**Dispersal distances by species:**

| Species | Max dispersal (km) |
|---------|-------------------|
| Asian Elephant | 40 |
| Bengal Tiger | 50 |
| Indian Leopard | 30 |
| All species | 25 |

**GNN embedding (prototype):**
```
H_v = ReLU(W · mean([X_v, mean(X_neighbours)]))
```
W is a 4×5 learned weight matrix (in production: trained on WII telemetry data).

**Connectivity score formula:**
```
score = 0.25 × graph_density × 100
      + 0.30 × mean_suitability × 100
      + 0.30 × best_path_permeability × 100
      + 0.15 × connected_component_ratio × 100
```

**Bottleneck detection:** Betweenness centrality × (1 − suitability) — patches that are both critical and poor quality.

---

### Model 3: Fragmentation Predictor

**Algorithm:** Physics-inspired barrier model calibrated to road ecology literature.

**Key formulae:**
```
base_loss = min(length_km × 0.70, 60.0)
barrier_loss = base_loss × project_multiplier × traffic_mult × lanes_mult
connectivity_loss = barrier_loss - (crossings × 4.0%)

habitat_loss_ha = direct_footprint_ha + edge_effect_ha × 0.30
fragmentation_index = (connectivity_loss/100) × 0.65 + (habitat_loss/3000) × 0.35
```

**Project type multipliers:**

| Type | Barrier mult | Noise zone (km) |
|------|-------------|----------------|
| Highway | 1.00 | 2.0 |
| Railway | 0.85 | 1.5 |
| Township | 1.40 | 3.0 |
| Mining | 1.60 | 4.0 |

**References:** Forman et al. (2003) "Road Ecology"; Trombulak & Frissell (2000).

---

### Model 4: Restoration Optimizer

**Algorithm:** Greedy knapsack (polynomial-time approximation of NP-hard budget allocation).

```python
# Sort zones by priority method
# ecological_benefit: sort by zone.ecological_benefit_score
# cost_efficiency:    sort by zone.ecological_benefit_score / zone.cost_cr
# connectivity_gain:  sort by zone.connectivity_gain_pct

# Greedily select zones until budget exhausted
for zone in sorted_zones:
    if zone.cost_cr <= remaining_budget:
        select(zone)
        remaining_budget -= zone.cost_cr
```

**ROI metric:** `connectivity_gain_pct / cost_cr`

---

## 4. API Reference

Base URL: `http://localhost:8000/v1`

Interactive docs: `http://localhost:8000/docs`

### Corridors

#### `GET /corridors/`
List all Karnataka wildlife corridors.

**Query params:** `priority` (critical|high|medium|low)

**Response:**
```json
[{
  "id": 1,
  "name": "Bandipur–Nagarhole Corridor",
  "connectivity_score": 82.0,
  "permeability_score": 0.82,
  "priority": "medium",
  "species_supported": ["Elephas maximus", "Panthera tigris", ...]
}]
```

---

#### `GET /corridors/{id}/health`
Real-time health index with alerts and per-zone permeability.

**Response:**
```json
{
  "corridor_id": 2,
  "score": 54.0,
  "trend": "declining",
  "alerts": ["NH-948 expansion threatens Z2 crossing — impact score 73%"],
  "permeability_by_zone": [{"zone": "Z2-NH-948 crossing", "score": 28}]
}
```

---

#### `POST /corridors/generate`
Run GNN corridor discovery on a bounding box.

**Request:**
```json
{
  "bbox": {"min_lon": 76.0, "min_lat": 11.5, "max_lon": 78.0, "max_lat": 13.5},
  "species": "elephant",
  "resolution_m": 100
}
```

**Response:**
```json
{
  "corridor_id": 1,
  "priority_score": 82.0,
  "connectivity_score": 82.1,
  "graph_nodes": 4,
  "graph_edges": 4,
  "computation_time_s": 0.05,
  "explanation": "..."
}
```

---

#### `GET /corridors/{id}/gnn`
Full GNN analysis: least-cost paths, bottleneck detection, centrality scores.

---

### Impact Simulation

#### `POST /simulate/highway`
Predict ecological impact of proposed infrastructure.

**Request:**
```json
{
  "geometry_wkt": "LINESTRING(77.58 12.79, 77.45 12.55, 77.25 12.35)",
  "project_type": "highway",
  "project_name": "NH-948 Extension Phase 2",
  "corridor_id": 2,
  "lanes": 4,
  "crossings_planned": 2,
  "traffic_volume": "high"
}
```

**Response:**
```json
{
  "scenario_id": 1,
  "corridor_affected": "Bannerghatta–Cauvery Corridor",
  "metrics": {
    "connectivity_loss_pct": 37.0,
    "habitat_loss_ha": 1240.0,
    "fragmentation_index": 0.68,
    "elephant_passage_risk": "Severe",
    "tiger_corridor_break": false,
    "restoration_cost_cr": 4.2,
    "impact_score": 58.3,
    "risk_level": "High"
  },
  "mitigation_recommendations": [
    {
      "type": "wildlife_crossing",
      "priority": "critical",
      "description": "Install 4 elephant underpasses (min 8m × 5m clear opening)",
      "cost_cr": 3.2,
      "effectiveness_pct": 16
    }
  ],
  "ai_analysis": "The NH-948 extension..."
}
```

---

### Habitat Suitability

#### `POST /habitat/suitability`

```json
{
  "species": "elephant",
  "points": [{
    "lat": 11.66, "lon": 76.65,
    "ndvi": 0.72,
    "elevation_m": 1050,
    "dist_to_road_m": 3200,
    "dist_to_settlement_m": 8400,
    "forest_density": 0.88,
    "land_cover_class": "dense_forest"
  }]
}
```

**Response includes:** `suitability_score`, `feature_contributions` (SHAP-style), `explanation`

---

### Restoration

#### `POST /restoration/recommend`

```json
{
  "corridor_id": 2,
  "budget_cr": 5.0,
  "priority_method": "ecological_benefit"
}
```

**Response:**
```json
{
  "zones": [...],
  "total_cost_cr": 4.2,
  "total_connectivity_gain_pct": 30.0,
  "roi_score": 7.14,
  "ai_plan": "Optimal restoration plan..."
}
```

---

### AI / Explainability

#### `POST /ai/ask`
Open question answering about Karnataka wildlife corridors.

#### `POST /ai/policy-brief`
Generate formal government policy brief.

---

## 5. Database Schema (PostGIS)

```sql
-- Wildlife corridors
CREATE TABLE corridors (
  id                 SERIAL PRIMARY KEY,
  name               VARCHAR(200) NOT NULL,
  geometry           GEOMETRY(MULTILINESTRING, 4326),
  connectivity_score FLOAT,
  permeability_score FLOAT,
  ndvi_mean          FLOAT,
  forest_cover_pct   FLOAT,
  length_km          FLOAT,
  priority           VARCHAR(20),
  species_supported  JSONB,
  last_analyzed      TIMESTAMP
);

-- Habitat patches (GNN nodes)
CREATE TABLE habitat_patches (
  id                    SERIAL PRIMARY KEY,
  corridor_id           INTEGER REFERENCES corridors(id),
  geometry              GEOMETRY(POLYGON, 4326),
  area_ha               FLOAT,
  suitability_score     FLOAT,
  ndvi                  FLOAT,
  elevation_m           FLOAT,
  forest_density        FLOAT,
  dist_to_road_m        FLOAT,
  dist_to_settlement_m  FLOAT,
  land_cover_class      VARCHAR(50),
  node_embedding        JSONB
);

-- Roads and railways
CREATE TABLE roads (
  id                    SERIAL PRIMARY KEY,
  geometry              GEOMETRY(LINESTRING, 4326),
  road_type             VARCHAR(50),
  highway_class         VARCHAR(20),
  lanes                 INTEGER,
  has_wildlife_crossing BOOLEAN DEFAULT FALSE,
  osm_id                VARCHAR(50)
);

-- Impact scenarios
CREATE TABLE impact_scenarios (
  id                    SERIAL PRIMARY KEY,
  corridor_id           INTEGER REFERENCES corridors(id),
  proposed_geometry     GEOMETRY(LINESTRING, 4326),
  connectivity_loss_pct FLOAT,
  habitat_loss_ha       FLOAT,
  fragmentation_index   FLOAT,
  elephant_passage_risk VARCHAR(20),
  restoration_cost_cr   FLOAT,
  ai_analysis           TEXT,
  mitigation_recommendations JSONB
);

-- Restoration zones
CREATE TABLE restoration_zones (
  id                       SERIAL PRIMARY KEY,
  corridor_id              INTEGER REFERENCES corridors(id),
  geometry                 GEOMETRY(POLYGON, 4326),
  method                   VARCHAR(50),
  area_ha                  FLOAT,
  cost_cr                  FLOAT,
  ecological_benefit_score FLOAT,
  connectivity_gain_pct    FLOAT,
  priority_rank            INTEGER,
  native_species           JSONB
);

-- Useful PostGIS spatial indexes
CREATE INDEX corridors_geom_idx ON corridors USING GIST(geometry);
CREATE INDEX patches_geom_idx   ON habitat_patches USING GIST(geometry);
CREATE INDEX roads_geom_idx     ON roads USING GIST(geometry);

-- Example spatial query: find all habitat patches within 5km of a road
SELECT p.name, p.suitability_score,
       ST_Distance(p.geometry::geography, r.geometry::geography) AS dist_m
FROM habitat_patches p, roads r
WHERE r.highway_class = 'NH'
  AND ST_DWithin(p.geometry::geography, r.geometry::geography, 5000)
ORDER BY dist_m;
```

---

## 6. GIS Data Sources

| Dataset | Source | Format | License |
|---------|--------|--------|---------|
| Satellite imagery (NDVI) | ESA Sentinel-2 via Copernicus Hub | GeoTIFF (10m) | Free / Open |
| Elevation | NASA SRTM v3 | GeoTIFF (30m) | Public domain |
| Roads & settlements | OpenStreetMap | GeoJSON | ODbL |
| Protected area boundaries | Karnataka Forest Dept | Shapefile | Gov open data |
| Wildlife corridor delineations | Wildlife Institute of India | Published reports | Public |
| Biodiversity observations | GBIF (gbif.org) | CSV / DwC | CC BY 4.0 |
| Land use / land cover | ISRO Bhuvan LULC | GeoTIFF (30m) | Gov open data |

### Fetching Sentinel-2 Data (Production)

```python
import requests

# Use Earth Search STAC API (no API key required)
STAC_URL = "https://earth-search.aws.element84.com/v1"

response = requests.post(f"{STAC_URL}/search", json={
    "collections": ["sentinel-2-l2a"],
    "bbox": [74.05, 11.59, 78.57, 18.45],   # Karnataka
    "datetime": "2024-01-01/2024-12-31",
    "query": {"eo:cloud_cover": {"lt": 15}},
    "limit": 10
})
items = response.json()["features"]
# Download B04 (Red) and B08 (NIR) for NDVI computation
# NDVI = (B08 - B04) / (B08 + B04)
```

---

## 7. Karnataka Corridors

### Corridor 1: Bandipur–Nagarhole (Score: 82/100 · Priority: Medium)

- **Length:** ~45 km
- **Forest cover:** 68%
- **NDVI mean:** 0.61
- **Key species:** Asian Elephant, Bengal Tiger, Indian Leopard, Dhole, Gaur
- **Threats:** NH-766 (Mysuru–Kozhikode highway), seasonal agricultural encroachment
- **Key bottleneck:** Gundlupet Scrub Patch (Z4, score 61) — 480m from NH-766
- **Status:** Relatively intact; tiger and elephant populations stable

### Corridor 2: Bannerghatta–Cauvery (Score: 54/100 · Priority: CRITICAL)

- **Length:** ~62 km
- **Forest cover:** 41%
- **NDVI mean:** 0.38
- **Key species:** Asian Elephant, Sloth Bear, Jackal, Porcupine, Spotted Deer
- **Threats:** NH-948 expansion, Bengaluru southward urbanisation, quarrying, human-wildlife conflict
- **Key bottleneck:** NH-948 Crossing Zone (Z2, score 28) — existential pinch point
- **Status:** CRITICAL — connectivity collapse imminent without intervention

### Corridor 3: Brahmagiri–Wayanad (Score: 71/100 · Priority: High)

- **Length:** ~38 km
- **Forest cover:** 74%
- **NDVI mean:** 0.71
- **Key species:** Bengal Tiger, Indian Leopard, Asian Elephant, Dhole, Clouded Leopard
- **Threats:** Coffee estate expansion in Coorg transition zone (Z3), SH-17 traffic
- **Status:** Cross-state corridor (Karnataka↔Kerala); tiger meta-population connectivity at stake

---

## 8. Deployment Guide

### Production Docker Compose

```yaml
version: "3.9"

services:
  db:
    image: postgis/postgis:15-3.4
    environment:
      POSTGRES_DB: connectai_karnataka
      POSTGRES_USER: connectai
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - pgdata:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U connectai"]
      interval: 10s
      retries: 5

  api:
    build: ./backend
    environment:
      DATABASE_URL: postgresql://connectai:${DB_PASSWORD}@db:5432/connectai_karnataka
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
      LOG_LEVEL: INFO
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    depends_on:
      - api

volumes:
  pgdata:
```

### Dockerfile (Backend)

```dockerfile
FROM python:3.12-slim

# Install GDAL system dependencies
RUN apt-get update && apt-get install -y \
    gdal-bin libgdal-dev libgeos-dev libproj-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt --no-cache-dir

COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes (prod) | PostgreSQL + PostGIS connection string |
| `ANTHROPIC_API_KEY` | Optional | Enables AI explanations (falls back to templates) |
| `API_HOST` | No | Default: 0.0.0.0 |
| `API_PORT` | No | Default: 8000 |
| `LOG_LEVEL` | No | Default: INFO |

---

## 9. Development Setup

```bash
# Clone repository
git clone https://github.com/karnataka-forest-dept/connectai-karnataka
cd connectai-karnataka

# Backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env: set DATABASE_URL and ANTHROPIC_API_KEY

# Start PostgreSQL + PostGIS (Docker)
docker run -d \
  --name connectai-postgres \
  -e POSTGRES_DB=connectai_karnataka \
  -e POSTGRES_USER=connectai \
  -e POSTGRES_PASSWORD=connectai \
  -p 5432:5432 \
  postgis/postgis:15-3.4

# Start API server (auto-seeds data on first run)
uvicorn app.main:app --reload --port 8000

# API docs available at:
# http://localhost:8000/docs   (Swagger UI)
# http://localhost:8000/redoc  (ReDoc)

# Frontend
cd ../frontend
npm install
npm run dev   # http://localhost:5173

# Configure frontend API URL
echo "VITE_API_URL=http://localhost:8000/v1" > .env
```

---

## 10. Testing

```bash
cd backend

# Run all tests
pytest tests/ -v

# Run specific test class
pytest tests/test_all.py::TestHabitatModel -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Run only fast unit tests (skip API integration)
pytest tests/ -v -k "not TestAPIEndpoints"
```

### Test Coverage: 54 Tests

| Module | Tests | Status |
|--------|-------|--------|
| Habitat Suitability Model | 9 | ✅ |
| GNN Connectivity Engine | 9 | ✅ |
| Fragmentation Predictor | 7 | ✅ |
| Restoration Optimizer | 5 | ✅ |
| GIS Data Integrity | 9 | ✅ |
| FastAPI Endpoints | 15 | ✅ |
| **Total** | **54** | **✅ 54/54** |

---

## 11. Explainable AI

ConnectAI integrates Claude (claude-sonnet-4-6) for plain-language explanations targeted at:

- **Karnataka Forest Department officers** — actionable corridor health summaries
- **Environmental regulators** — EIA-compliant impact assessments
- **Researchers** — technical GNN and model explanations

### Explanation Types

| Endpoint | Explanation |
|----------|-------------|
| `GET /corridors/{id}/gnn` | Corridor health + bottleneck interventions |
| `POST /simulate/highway` | Impact analysis with WPA 1972 / EIA 2006 references |
| `POST /restoration/recommend` | Planting seasons, species, monitoring milestones |
| `POST /ai/ask` | Free-form conservation question answering |
| `POST /ai/policy-brief` | Formal government policy brief (200 words) |

### Fallback Behaviour

When `ANTHROPIC_API_KEY` is not configured, all endpoints return structured template-based explanations. The platform is fully functional without the AI key — explanations are less nuanced but still accurate.

---

## 12. Roadmap

### V1 (Current — MVP)
- ✅ Corridor Intelligence Engine (GNN + Least-Cost Path)
- ✅ Infrastructure Impact Simulator
- ✅ Restoration Recommendation Engine
- ✅ Interactive GIS Dashboard
- ✅ FastAPI Backend + PostGIS
- ✅ Explainable AI (Claude)
- ✅ 54-test suite

### V2 — Real-time Monitoring
- Camera trap integration (EXIF + species detection)
- Animal detection using YOLOv11 (Ultralytics)
- Acoustic monitoring (bird/elephant call detection)
- Automated NDVI trend alerts (Sentinel-2 monthly)

### V3 — Operational Intelligence
- Real-time human-wildlife conflict alerts (SMS → forest rangers)
- Drone waypoint planning for corridor surveys
- Poaching risk heatmaps

### V4 — Community Engagement
- Citizen science species reporting app (React Native)
- Community corridor guardian programme dashboard

### V5 — Genetic Diversity
- Population genetics modelling (landscape genetics)
- Gene flow forecasting from corridor connectivity
- Metapopulation viability analysis

---

## Legal & Compliance

This system supports compliance with:
- **Wildlife Protection Act 1972** (MoEFCC) — schedule I/II species protection
- **Forest Conservation Act 1980** — forest diversion assessment
- **EIA Notification 2006** — environmental impact assessment for linear projects
- **National Wildlife Action Plan 2017–2031** — corridor conservation priorities
- **Convention on Biological Diversity** — Aichi Target 11 (protected area connectivity)

---

*Built for Karnataka Forest Department and conservation stakeholders. Open source (MIT).*
*For deployment support: connectai@karnataka.gov.in*
