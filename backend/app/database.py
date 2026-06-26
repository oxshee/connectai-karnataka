"""
ConnectAI Karnataka — Database Session Management

Provides:
  engine       — SQLAlchemy async-compatible engine
  SessionLocal — session factory
  get_db()     — FastAPI dependency
  init_db()    — creates tables on startup (falls back gracefully if PostGIS unavailable)
"""
import logging
from contextlib import contextmanager

from sqlalchemy import create_engine, text, event
from sqlalchemy.orm import sessionmaker, Session

from app.config import get_settings
from app.models.db import Base

logger = logging.getLogger(__name__)
settings = get_settings()

# ── Engine ───────────────────────────────────────────────────────────────────

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=settings.debug,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ── PostGIS extension ────────────────────────────────────────────────────────

def _ensure_postgis(conn, branch):
    """Enable PostGIS and PostGIS topology if not already installed."""
    if branch.is_prepared:
        return
    try:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis_topology"))
        logger.info("PostGIS extensions enabled.")
    except Exception as e:
        logger.warning(f"Could not enable PostGIS extensions: {e}")


@event.listens_for(engine, "connect")
def on_connect(dbapi_conn, connection_record):
    pass  # extensions are created via init_db below


# ── Table initialisation ─────────────────────────────────────────────────────

def init_db() -> bool:
    """
    Create PostGIS extension then all tables.
    Returns True if database is available, False if running without DB (dev mode).
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis_topology"))
            conn.commit()
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialised successfully with PostGIS.")
        return True
    except Exception as e:
        logger.warning(
            f"Database unavailable ({e}). "
            "Running in mock-data mode — all endpoints return realistic demo data."
        )
        return False


# ── Dependency ───────────────────────────────────────────────────────────────

def get_db():
    """FastAPI dependency that yields a database session."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def db_session():
    """Context manager for use outside FastAPI request lifecycle."""
    db: Session = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
