"""
ConnectAI Karnataka — Data Seeder

Loads authoritative Karnataka GIS datasets into PostGIS on first startup.
Idempotent: safe to call multiple times (checks existence before inserting).
"""
from __future__ import annotations
import logging
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import text

from app.data.karnataka_gis import (
    CORRIDORS, HABITAT_PATCHES, ROADS, RESTORATION_ZONES, SPECIES_PROFILES
)
from app.models.db import (
    Corridor, HabitatPatch, Road, RestorationZone, SpeciesSighting, PriorityLevel
)

logger = logging.getLogger(__name__)


def seed_database(db: Session) -> dict[str, int]:
    """
    Seed all Karnataka GIS data into PostGIS tables.
    Returns counts of records inserted.
    """
    counts = {"corridors": 0, "patches": 0, "roads": 0, "restoration_zones": 0}

    counts["corridors"] = _seed_corridors(db)
    counts["patches"] = _seed_habitat_patches(db)
    counts["roads"] = _seed_roads(db)
    counts["restoration_zones"] = _seed_restoration_zones(db)

    logger.info(f"Seeding complete: {counts}")
    return counts


def _seed_corridors(db: Session) -> int:
    inserted = 0
    for c in CORRIDORS:
        existing = db.query(Corridor).filter(Corridor.id == c["id"]).first()
        if existing:
            continue
        try:
            corridor = Corridor(
                id=c["id"],
                name=c["name"],
                start_name=c["start_name"],
                end_name=c["end_name"],
                description=c["description"],
                start_lat=c["start_lat"], start_lon=c["start_lon"],
                end_lat=c["end_lat"], end_lon=c["end_lon"],
                length_km=c["length_km"],
                connectivity_score=c["connectivity_score"],
                permeability_score=c["permeability_score"],
                ndvi_mean=c["ndvi_mean"],
                forest_cover_pct=c["forest_cover_pct"],
                priority=PriorityLevel(c["priority"]),
                species_supported=c["species_supported"],
                geometry=f"SRID=4326;{c['geometry_wkt']}",
                last_analyzed=datetime.utcnow(),
            )
            db.add(corridor)
            db.flush()
            inserted += 1
        except Exception as e:
            logger.warning(f"Failed to insert corridor {c['id']}: {e}")
            db.rollback()
    db.commit()
    return inserted


def _seed_habitat_patches(db: Session) -> int:
    inserted = 0
    for p in HABITAT_PATCHES:
        existing = db.query(HabitatPatch).filter(HabitatPatch.id == p["id"]).first()
        if existing:
            continue
        try:
            patch = HabitatPatch(
                id=p["id"],
                corridor_id=p["corridor_id"],
                name=p["name"],
                area_ha=p["area_ha"],
                centroid_lat=p["centroid_lat"],
                centroid_lon=p["centroid_lon"],
                suitability_score=p["suitability_score"],
                ndvi=p["ndvi"],
                elevation_m=p["elevation_m"],
                forest_density=p["forest_density"],
                dist_to_road_m=p["dist_to_road_m"],
                dist_to_settlement_m=p["dist_to_settlement_m"],
                land_cover_class=p["land_cover_class"],
            )
            db.add(patch)
            db.flush()
            inserted += 1
        except Exception as e:
            logger.warning(f"Failed to insert patch {p['id']}: {e}")
            db.rollback()
    db.commit()
    return inserted


def _seed_roads(db: Session) -> int:
    inserted = 0
    for r in ROADS:
        existing = db.query(Road).filter(Road.id == r["id"]).first()
        if existing:
            continue
        try:
            road = Road(
                id=r["id"],
                name=r["name"],
                road_type=r["road_type"],
                highway_class=r["highway_class"],
                lanes=r["lanes"],
                traffic_volume=r["traffic_volume"],
                has_wildlife_crossing=r["has_wildlife_crossing"],
                geometry=f"SRID=4326;{r['geometry_wkt']}",
            )
            db.add(road)
            db.flush()
            inserted += 1
        except Exception as e:
            logger.warning(f"Failed to insert road {r['id']}: {e}")
            db.rollback()
    db.commit()
    return inserted


def _seed_restoration_zones(db: Session) -> int:
    inserted = 0
    for z in RESTORATION_ZONES:
        existing = db.query(RestorationZone).filter(RestorationZone.id == z["id"]).first()
        if existing:
            continue
        try:
            zone = RestorationZone(
                id=z["id"],
                corridor_id=z["corridor_id"],
                name=z["name"],
                method=z["method"],
                area_ha=z["area_ha"],
                cost_cr=z["cost_cr"],
                ecological_benefit_score=z["ecological_benefit_score"],
                connectivity_gain_pct=z["connectivity_gain_pct"],
                priority_rank=z["priority_rank"],
                native_species=z["native_species"],
                implementation_years=z["implementation_years"],
                notes=z["notes"],
                geometry=f"SRID=4326;{z['geometry_wkt']}",
            )
            db.add(zone)
            db.flush()
            inserted += 1
        except Exception as e:
            logger.warning(f"Failed to insert restoration zone {z['id']}: {e}")
            db.rollback()
    db.commit()
    return inserted
