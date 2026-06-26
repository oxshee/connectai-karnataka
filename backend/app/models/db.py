"""
ConnectAI Karnataka — Database Models (SQLAlchemy + PostGIS)

Tables:
  corridors          Wildlife corridors with geometry
  habitat_patches    Discrete forest / habitat polygons
  roads              Road network (highways, railways)
  settlements        Urban areas and villages
  impact_scenarios   Stored simulation results
  species_sightings  Biodiversity observations
  restoration_zones  Recommended restoration areas
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Text,
    Boolean, ForeignKey, JSON, Enum as SAEnum
)
from sqlalchemy.orm import DeclarativeBase, relationship
from geoalchemy2 import Geometry
import enum


class Base(DeclarativeBase):
    pass


# ── Enumerations ────────────────────────────────────────────────────────────

class PriorityLevel(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ProjectType(str, enum.Enum):
    HIGHWAY = "highway"
    RAILWAY = "railway"
    TOWNSHIP = "township"
    MINING = "mining"


class RestorationMethod(str, enum.Enum):
    REFORESTATION = "reforestation"
    WILDLIFE_CROSSING = "wildlife_crossing"
    BUFFER_ZONE = "buffer_zone"
    RIPARIAN = "riparian"


# ── Core spatial tables ─────────────────────────────────────────────────────

class Corridor(Base):
    """Wildlife ecological corridor."""
    __tablename__ = "corridors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text)

    # Spatial — stored as WGS84 (EPSG:4326) linestring or polygon
    geometry = Column(Geometry("MULTILINESTRING", srid=4326))

    # Endpoints (for display)
    start_name = Column(String(100))
    end_name = Column(String(100))
    start_lat = Column(Float)
    start_lon = Column(Float)
    end_lat = Column(Float)
    end_lon = Column(Float)

    # Connectivity metrics
    connectivity_score = Column(Float, default=0.0)   # 0–100
    permeability_score = Column(Float, default=0.0)   # 0–1
    ndvi_mean = Column(Float)                          # –1 to 1
    forest_cover_pct = Column(Float)                  # 0–100
    length_km = Column(Float)

    # Classification
    priority = Column(SAEnum(PriorityLevel), default=PriorityLevel.MEDIUM)
    species_supported = Column(JSON, default=list)    # ["elephant","tiger",…]

    # Status
    is_active = Column(Boolean, default=True)
    last_analyzed = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    habitat_patches = relationship("HabitatPatch", back_populates="corridor")
    impact_scenarios = relationship("ImpactScenario", back_populates="corridor")
    restoration_zones = relationship("RestorationZone", back_populates="corridor")


class HabitatPatch(Base):
    """Discrete habitat polygon — node in the connectivity graph."""
    __tablename__ = "habitat_patches"

    id = Column(Integer, primary_key=True, index=True)
    corridor_id = Column(Integer, ForeignKey("corridors.id"), nullable=True)
    name = Column(String(200))

    # Spatial — polygon in WGS84
    geometry = Column(Geometry("POLYGON", srid=4326))
    centroid_lat = Column(Float)
    centroid_lon = Column(Float)

    # Habitat attributes
    area_ha = Column(Float)
    suitability_score = Column(Float)   # 0–1 from habitat model
    ndvi = Column(Float)
    elevation_m = Column(Float)
    forest_density = Column(Float)      # 0–1
    dist_to_road_m = Column(Float)
    dist_to_settlement_m = Column(Float)
    land_cover_class = Column(String(50))  # "dense_forest","scrub","agriculture"…

    # GNN node features (computed)
    node_embedding = Column(JSON)       # [float, …] from GNN

    created_at = Column(DateTime, default=datetime.utcnow)
    corridor = relationship("Corridor", back_populates="habitat_patches")


class Road(Base):
    """Road / railway infrastructure."""
    __tablename__ = "roads"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200))
    road_type = Column(String(50))    # "national_highway","state_highway","railway"
    highway_class = Column(String(20))  # "NH","SH","MDR","railway"
    geometry = Column(Geometry("LINESTRING", srid=4326))
    lanes = Column(Integer)
    traffic_volume = Column(String(20))  # "high","medium","low"
    has_wildlife_crossing = Column(Boolean, default=False)
    osm_id = Column(String(50))       # OpenStreetMap ID for reference


class Settlement(Base):
    """Urban area / village."""
    __tablename__ = "settlements"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), index=True)
    settlement_type = Column(String(50))  # "city","town","village","forest_camp"
    population = Column(Integer)
    geometry = Column(Geometry("POINT", srid=4326))
    district = Column(String(100))


class ImpactScenario(Base):
    """Stored infrastructure impact simulation result."""
    __tablename__ = "impact_scenarios"

    id = Column(Integer, primary_key=True, index=True)
    corridor_id = Column(Integer, ForeignKey("corridors.id"))
    project_name = Column(String(200))
    project_type = Column(SAEnum(ProjectType))

    # Proposed geometry (road/railway linestring)
    proposed_geometry = Column(Geometry("LINESTRING", srid=4326))
    length_km = Column(Float)
    crossings_planned = Column(Integer, default=0)

    # Computed impact metrics
    connectivity_loss_pct = Column(Float)
    habitat_loss_ha = Column(Float)
    fragmentation_index = Column(Float)   # 0–1 (higher = more fragmented)
    elephant_passage_risk = Column(String(20))  # severe/high/moderate/low
    tiger_corridor_break = Column(Boolean, default=False)
    restoration_cost_cr = Column(Float)    # ₹ Crore
    impact_score = Column(Float)           # composite 0–100

    # AI explanation
    ai_analysis = Column(Text)
    mitigation_recommendations = Column(JSON)

    created_at = Column(DateTime, default=datetime.utcnow)
    corridor = relationship("Corridor", back_populates="impact_scenarios")


class SpeciesSighting(Base):
    """Biodiversity / species observation (GBIF-compatible)."""
    __tablename__ = "species_sightings"

    id = Column(Integer, primary_key=True, index=True)
    species_name = Column(String(200), index=True)
    common_name = Column(String(200))
    family = Column(String(100))
    observed_at = Column(DateTime)
    geometry = Column(Geometry("POINT", srid=4326))
    source = Column(String(100))       # "gbif","camera_trap","field_survey"
    confidence = Column(Float, default=1.0)
    corridor_id = Column(Integer, ForeignKey("corridors.id"), nullable=True)


class RestorationZone(Base):
    """Recommended restoration area with cost-benefit data."""
    __tablename__ = "restoration_zones"

    id = Column(Integer, primary_key=True, index=True)
    corridor_id = Column(Integer, ForeignKey("corridors.id"))
    name = Column(String(200))
    method = Column(SAEnum(RestorationMethod))
    geometry = Column(Geometry("POLYGON", srid=4326))

    # Metrics
    area_ha = Column(Float)
    cost_cr = Column(Float)               # ₹ Crore
    ecological_benefit_score = Column(Float)  # 0–10
    connectivity_gain_pct = Column(Float)
    priority_rank = Column(Integer)

    # Details
    native_species = Column(JSON)         # ["teak","rosewood",…]
    implementation_years = Column(Integer)
    notes = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)
    corridor = relationship("Corridor", back_populates="restoration_zones")
