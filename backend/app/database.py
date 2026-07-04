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

from sqlalchemy.engine.url import make_url

DATABASE_URL = settings.database_url

if not DATABASE_URL:
    DATABASE_URL = "sqlite:///./connectai_demo.db"
    logger.warning(
        "DATABASE_URL not configured. Using SQLite demo database."
    )

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    echo=settings.debug,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

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


if engine.dialect.name == "postgresql":

    @event.listens_for(engine, "connect")
    def on_connect(dbapi_conn, connection_record):
        pass


# ── Table initialisation ─────────────────────────────────────────────────────

def init_db() -> bool:
    try:
        dialect = engine.dialect.name

        if dialect == "postgresql":
            with engine.connect() as conn:
                conn.execute(text(
                    "CREATE EXTENSION IF NOT EXISTS postgis"
                ))
                conn.execute(text(
                    "CREATE EXTENSION IF NOT EXISTS postgis_topology"
                ))
                conn.commit()

        Base.metadata.create_all(bind=engine)

        logger.info(
            "Database initialised successfully."
        )

        return True

    except Exception as e:
        logger.warning(
            f"Database unavailable ({e}). "
            "Running in mock-data mode."
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
