"""
ConnectAI Karnataka — FastAPI Application Entry Point

Startup sequence:
  1. Connect to PostgreSQL + PostGIS
  2. Run Alembic migrations (or create_all in dev)
  3. Seed Karnataka GIS data if tables are empty
  4. Mount all API routers
  5. Configure CORS for frontend

Run with:
  uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
"""
import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.database import init_db, SessionLocal
from app.api.corridors import router as corridors_router
from app.api.simulate import router as simulate_router
from app.api.habitat_restoration import habitat_router, restoration_router
from app.api.ai_routes import router as ai_router

settings = get_settings()
logging.basicConfig(
    level=getattr(logging, settings.debug and "DEBUG" or "INFO"),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ── Application lifecycle ────────────────────────────────────────────────────

DB_ONLINE = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    global DB_ONLINE
    logger.info("╔══════════════════════════════════════════════╗")
    logger.info("║   ConnectAI Karnataka  —  Starting up...    ║")
    logger.info("╚══════════════════════════════════════════════╝")

    # Try database init
    DB_ONLINE = init_db()

    if DB_ONLINE:
        # Seed Karnataka GIS data
        try:
            from app.services.seeder import seed_database
            db = SessionLocal()
            counts = seed_database(db)
            db.close()
            logger.info(f"GIS data seeded: {counts}")
        except Exception as e:
            logger.warning(f"Seeding skipped: {e}")
    else:
        logger.info("Running in DEMO MODE — all data served from in-memory GIS datasets.")

    logger.info("✅ ConnectAI Karnataka ready.")
    yield

    logger.info("Shutting down ConnectAI Karnataka...")


# ── Application ──────────────────────────────────────────────────────────────

app = FastAPI(
    title="ConnectAI Karnataka",
    description=(
        "AI-Powered Ecological Corridor Intelligence Platform for Karnataka, India.\n\n"
        "Predicts, protects and plans wildlife connectivity across Karnataka's "
        "fragmented landscapes using GIS, Graph Neural Networks, and spatial AI.\n\n"
        "**Key Corridors Monitored:**\n"
        "- Bandipur–Nagarhole (score 82/100)\n"
        "- Bannerghatta–Cauvery (score 54/100 — CRITICAL)\n"
        "- Brahmagiri–Wayanad (score 71/100)\n\n"
        "**Data sources:** Sentinel-2, Landsat, SRTM, OpenStreetMap, GBIF, Karnataka Forest Dept."
    ),
    version="1.0.0",
    contact={
        "name": "Karnataka Forest Department — Digital Cell",
        "email": "connectai@karnataka.gov.in",
    },
    license_info={"name": "MIT"},
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ─────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────

app.include_router(corridors_router, prefix="/v1")
app.include_router(simulate_router, prefix="/v1")
app.include_router(habitat_router, prefix="/v1")
app.include_router(restoration_router, prefix="/v1")
app.include_router(ai_router, prefix="/v1")


# ── Root / health ─────────────────────────────────────────────────────────────

@app.get("/", tags=["System"])
async def root():
    return {
        "name": "ConnectAI Karnataka",
        "version": "1.0.0",
        "tagline": "Predicting, protecting and planning wildlife connectivity across Karnataka.",
        "docs": "/docs",
        "health": "/health",
        "corridors_monitored": 3,
        "corridors": [
            "Bandipur–Nagarhole", "Bannerghatta–Cauvery", "Brahmagiri–Wayanad"
        ],
    }


@app.get("/health", tags=["System"])
async def health():
    from app.data.karnataka_gis import CORRIDORS, HABITAT_PATCHES

    db_status = "online" if DB_ONLINE else "demo_mode"

    return {
        "status": "healthy",
        "version": "1.0.0",
        "database": db_status,
        "models_loaded": {
            "habitat_suitability_model": True,
            "gnn_connectivity_engine": True,
            "fragmentation_predictor": True,
            "restoration_optimizer": True,
        },
        "karnataka_corridors": len(CORRIDORS),
        "habitat_patches": len(HABITAT_PATCHES),
        "ai_explanations": bool(settings.anthropic_api_key),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


# ── Error handlers ────────────────────────────────────────────────────────────

@app.exception_handler(404)
async def not_found(request, exc):
    return JSONResponse(status_code=404, content={"error": "Not found", "path": str(request.url)})


@app.exception_handler(500)
async def server_error(request, exc):
    logger.error(f"Internal error: {exc}")
    return JSONResponse(status_code=500, content={"error": "Internal server error"})
