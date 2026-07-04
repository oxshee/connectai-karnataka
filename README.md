# ConnectAI Karnataka

> **AI-Powered Ecological Corridor Intelligence Platform**
> *Predicting, protecting and planning wildlife connectivity across Karnataka's fragmented landscapes.*



---

## Quick Start (3 commands)

```bash
git clone https://github.com/oxshee/connectai-karnataka
cd connectai-karnataka
docker compose up --build
```

- **Frontend:** http://localhost:3000
- **API:**      http://localhost:8000
- **API Docs:** http://localhost:8000/docs

---

## What It Does

ConnectAI Karnataka is a full-stack platform for wildlife corridor conservation intelligence. It answers:

- *"If a highway is built here, what happens to elephant movement?"*
- *"Where should Karnataka invest its conservation budget?"*
- *"Which corridor is most at risk right now?"*

---

## Architecture

```
frontend/          React 18 + TypeScript + Vite + Tailwind + Leaflet
backend/           FastAPI + SQLAlchemy + PostGIS + PyTorch
  app/
    api/           REST endpoints (corridors, simulate, habitat, restoration, ai)
    ml/            Habitat model, GNN connectivity, fragmentation predictor, restoration optimizer
    models/        SQLAlchemy DB models + Pydantic schemas
    data/          Karnataka GIS seed data (real coordinates)
    services/      Explainable AI (Claude), data seeder
docker-compose.yml PostgreSQL/PostGIS + API + Frontend
```

---

## Development Setup

### Prerequisites
- Python 3.12+
- Node 22+
- Docker (optional, for PostGIS)

### Backend

```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Optional: start PostGIS
docker run -d --name connectai-db \
  -e POSTGRES_DB=connectai_karnataka \
  -e POSTGRES_USER=connectai \
  -e POSTGRES_PASSWORD=connectai_dev \
  -p 5432:5432 postgis/postgis:15-3.4

# Copy and configure env
cp .env.example .env
# Edit .env: set ANTHROPIC_API_KEY for AI explanations

uvicorn app.main:app --reload --port 8000
```

The backend starts in **Demo Mode** if PostgreSQL is unavailable — all endpoints work using in-memory Karnataka GIS data.

### Frontend

```bash
cd frontend
npm install --legacy-peer-deps
cp .env.example .env          # VITE_API_URL=http://localhost:8000/v1
npm run dev                   # http://localhost:5173
```

### Tests

```bash
cd backend && python -m pytest tests/ -v   # 54 tests, all passing
```

---

## Environment Variables

### Backend (`backend/.env`)

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | No | PostgreSQL+PostGIS URL. Omit for Demo Mode |
| `ANTHROPIC_API_KEY` | No | Enables Claude AI explanations |
| `LOG_LEVEL` | No | `INFO` (default) |

### Frontend (`frontend/.env`)

| Variable | Required | Description |
|---|---|---|
| `VITE_API_URL` | Yes | Backend URL e.g. `http://localhost:8000/v1` |

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/v1/corridors/` | List all corridors |
| GET | `/v1/corridors/{id}` | Corridor detail |
| GET | `/v1/corridors/{id}/health` | Live health index |
| GET | `/v1/corridors/{id}/gnn` | GNN analysis + bottlenecks |
| POST | `/v1/corridors/generate` | Discover corridors in bbox |
| POST | `/v1/simulate/highway` | Infrastructure impact simulation |
| GET | `/v1/simulate/scenarios` | Saved scenarios |
| POST | `/v1/habitat/suitability` | Score habitat points |
| GET | `/v1/habitat/patches` | List habitat patches |
| POST | `/v1/restoration/recommend` | Optimise restoration plan |
| GET | `/v1/restoration/zones` | List restoration zones |
| POST | `/v1/ai/ask` | Open AI question answering |
| POST | `/v1/ai/policy-brief` | Generate government policy brief |
| GET | `/health` | System health check |

Full interactive docs at **http://localhost:8000/docs**

---

## Karnataka Corridors Monitored

| Corridor | Score | Priority |
|---|---|---|
| Bandipur–Nagarhole | 82/100 | Medium |
| Bannerghatta–Cauvery | 54/100 | **Critical** |
| Brahmagiri–Wayanad | 71/100 | High |

---

## ML Models

- **Habitat Suitability Model** — NDVI, elevation, road distance, forest density → 0–1 score
- **GNN Connectivity Engine** — GraphSAGE node embeddings + Dijkstra least-cost paths
- **Fragmentation Predictor** — Road geometry → connectivity loss %, species risk
- **Restoration Optimizer** — Greedy knapsack maximising ecological gain within budget

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, Leaflet, Recharts, Framer Motion, Zustand, React Query |
| Backend | FastAPI, SQLAlchemy 2, GeoAlchemy2, Pydantic v2 |
| Database | PostgreSQL 15 + PostGIS 3.4 |
| ML | PyTorch, NetworkX, NumPy, Scikit-learn, GeoPandas |
| AI | Claude (Anthropic API) for XAI explanations |
| DevOps | Docker, Docker Compose, GitHub Actions |

---

## License

MIT — Built for Karnataka Forest Department and conservation stakeholders.
