# 🌿 ConnectAI Karnataka

> **AI-powered ecological corridor intelligence platform for wildlife conservation.**
>
> ConnectAI predicts habitat fragmentation, simulates infrastructure impact, and recommends restoration strategies to support evidence-based conservation planning across Karnataka.

---

## Overview

Habitat fragmentation caused by roads, urbanisation, and land-use change threatens wildlife connectivity.

ConnectAI combines **geospatial analysis**, **machine learning**, **graph neural networks**, and **explainable AI** to help conservation planners evaluate ecological corridors and make informed restoration decisions.

### Key Capabilities

- 🗺️ Corridor discovery using GIS data
- 🐘 Wildlife connectivity analysis
- 🛣️ Highway impact simulation
- 🌱 Habitat suitability prediction
- 📊 Corridor health scoring
- 🤖 AI-generated ecological insights and policy briefs
- 🌳 Restoration planning and budget optimisation

---

## Tech Stack

| Layer | Technologies |
|--------|--------------|
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, Leaflet, React Query, Zustand |
| Backend | FastAPI, SQLAlchemy 2, GeoAlchemy2, Pydantic v2 |
| Database | PostgreSQL + PostGIS |
| Machine Learning | PyTorch, NetworkX, NumPy, Scikit-learn, GeoPandas |
| AI | Google Gemini (Explainable AI) |
| DevOps | Docker, Docker Compose, GitHub Actions |

---

# Quick Start

Clone the repository and launch the complete development environment.

```bash
git clone https://github.com/oxshee/connectai-karnataka.git

cd connectai-karnataka

docker compose up --build
```

Once running:

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Documentation | http://localhost:8000/docs |

---

# Project Structure

```text
connectai-karnataka
│
├── frontend/                 React + TypeScript application
│
├── backend/
│   ├── api/                  REST API endpoints
│   ├── ml/                   Machine learning models
│   ├── models/               Database models & schemas
│   ├── services/             AI & utility services
│   ├── data/                 Karnataka GIS datasets
│   └── tests/
│
├── docker-compose.yml
└── README.md
```

---

# Features

## Corridor Intelligence

Identify ecological corridors and monitor their health using geospatial datasets.

## Infrastructure Impact Simulator

Estimate how proposed roads or highways affect wildlife movement and habitat connectivity.

## Habitat Suitability Analysis

Predict habitat quality using environmental indicators such as vegetation, elevation, and forest density.

## Restoration Engine

Recommend conservation interventions that maximise ecological benefit under budget constraints.

## Explainable AI

Generate natural-language ecological analyses and policy recommendations using Google Gemini.

---

# Machine Learning Components

### Habitat Suitability Model

Predicts habitat quality using:

- NDVI
- Elevation
- Distance from roads
- Forest density

### Graph Neural Network

Models wildlife connectivity using:

- GraphSAGE embeddings
- Least-cost path analysis
- Connectivity bottleneck detection

### Fragmentation Predictor

Estimates connectivity loss caused by new infrastructure.

### Restoration Optimiser

Selects restoration projects that maximise ecological impact within a specified budget.

---

# API

Some of the available endpoints include:

| Method | Endpoint | Description |
|---------|----------|-------------|
| GET | `/v1/corridors` | List corridors |
| GET | `/v1/corridors/{id}` | Corridor details |
| GET | `/v1/corridors/{id}/health` | Corridor health score |
| GET | `/v1/corridors/{id}/gnn` | Connectivity analysis |
| POST | `/v1/simulate/highway` | Highway impact simulation |
| POST | `/v1/habitat/suitability` | Habitat suitability prediction |
| POST | `/v1/restoration/recommend` | Restoration recommendation |
| POST | `/v1/ai/ask` | AI ecological assistant |
| POST | `/v1/ai/policy-brief` | Generate policy brief |

Interactive API documentation is available at:

```
http://localhost:8000/docs
```

---

# Local Development

## Backend

```bash
cd backend

python -m venv venv

source venv/bin/activate

pip install -r requirements.txt

uvicorn app.main:app --reload
```

## Frontend

```bash
cd frontend

npm install

npm run dev
```

---

# Environment Variables

### Backend

| Variable | Description |
|-----------|-------------|
| DATABASE_URL | PostgreSQL/PostGIS connection string |
| GOOGLE_API_KEY | Enables AI-powered ecological explanations |
| LOG_LEVEL | Logging level |

### Frontend

| Variable | Description |
|-----------|-------------|
| VITE_API_URL | Backend API URL |

---

# Testing

Run backend tests:

```bash
cd backend

pytest tests -v
```

---

# Future Improvements

- Satellite imagery integration
- Temporal land-use analysis
- Multi-species corridor modelling
- Real-time environmental monitoring
- Cloud deployment with scalable inference

---

# License

Licensed under the MIT License.
