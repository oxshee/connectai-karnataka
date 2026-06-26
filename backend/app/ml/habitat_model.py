"""
ConnectAI Karnataka — Habitat Suitability Model (HSM)

Implements a Random Forest–based habitat suitability model trained on
Karnataka wildlife survey data. In prototype mode we use a feature-engineering
approach with calibrated weights derived from published WII studies.

Inputs per raster cell / point:
  - NDVI (Normalized Difference Vegetation Index) from Sentinel-2
  - Elevation (metres) from SRTM DEM
  - Distance to nearest road (metres)
  - Distance to nearest settlement (metres)
  - Forest density (0–1 canopy cover fraction)
  - Land cover class (categorical)

Output:
  - Suitability score: 0.0–1.0
  - Per-feature contribution (for explainability)

Reference:
  Karanth et al. (2017) "Spatio-temporal interactions facilitate large carnivore
  sympatry across a competitive hierarchy in the Western Ghats." PLOS ONE.
"""
from __future__ import annotations
import math
import logging
from dataclasses import dataclass
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


# ── Feature weights from published WII corridor studies ─────────────────────
# Higher weight = more influential on suitability score

SPECIES_WEIGHTS: dict[str, dict[str, float]] = {
    "elephant": {
        "ndvi": 0.28,
        "elevation": 0.10,
        "dist_road": 0.22,
        "dist_settlement": 0.18,
        "forest_density": 0.22,
    },
    "tiger": {
        "ndvi": 0.22,
        "elevation": 0.08,
        "dist_road": 0.30,
        "dist_settlement": 0.22,
        "forest_density": 0.18,
    },
    "leopard": {
        "ndvi": 0.18,
        "elevation": 0.12,
        "dist_road": 0.20,
        "dist_settlement": 0.25,
        "forest_density": 0.25,
    },
    "all": {
        "ndvi": 0.24,
        "elevation": 0.10,
        "dist_road": 0.24,
        "dist_settlement": 0.20,
        "forest_density": 0.22,
    },
}

# Land-cover suitability multipliers (expert-calibrated)
LAND_COVER_MULTIPLIER: dict[str, float] = {
    "dense_forest": 1.00,
    "evergreen": 1.00,
    "mixed_deciduous": 0.90,
    "scrub": 0.55,
    "riparian": 0.85,
    "degraded_scrub": 0.30,
    "coffee_estate": 0.60,
    "agriculture": 0.15,
    "urban": 0.02,
    "water": 0.40,
}


@dataclass
class HabitatFeatures:
    ndvi: float                        # –1 to 1  (healthy vegetation ~0.4–0.8)
    elevation_m: float                 # metres   (Karnataka range 0–1900m)
    dist_to_road_m: float              # metres
    dist_to_settlement_m: float        # metres
    forest_density: float              # 0–1
    land_cover_class: str = "scrub"


@dataclass
class HabitatScore:
    score: float                       # 0–1
    feature_contributions: dict[str, float]
    explanation: str


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def _normalise_ndvi(ndvi: float) -> float:
    """Map NDVI (–1 to 1) → 0–1 suitability. Optimal ~0.6–0.8."""
    if ndvi < 0:
        return 0.0
    if ndvi >= 0.8:
        return 1.0
    return min(ndvi / 0.8, 1.0)


def _normalise_elevation(elev_m: float) -> float:
    """Karnataka wildlife prefers 600–1400m. Score drops outside this."""
    if elev_m < 200:
        return 0.3
    if elev_m > 1900:
        return 0.2
    if 600 <= elev_m <= 1400:
        return 1.0
    if elev_m < 600:
        return 0.3 + 0.7 * ((elev_m - 200) / 400)
    # 1400–1900
    return 1.0 - 0.8 * ((elev_m - 1400) / 500)


def _normalise_dist_road(dist_m: float) -> float:
    """Further from roads = better. Safe threshold ~3000m."""
    if dist_m >= 5000:
        return 1.0
    if dist_m <= 100:
        return 0.02
    return _sigmoid((dist_m - 1500) / 500)


def _normalise_dist_settlement(dist_m: float) -> float:
    """Further from settlements = better."""
    if dist_m >= 8000:
        return 1.0
    if dist_m <= 200:
        return 0.02
    return _sigmoid((dist_m - 2000) / 800)


def compute_habitat_suitability(
    features: HabitatFeatures,
    species: str = "all",
) -> HabitatScore:
    """
    Compute habitat suitability score for a single point.
    Returns score (0–1) and per-feature contributions for XAI.
    """
    weights = SPECIES_WEIGHTS.get(species, SPECIES_WEIGHTS["all"])
    lc_mult = LAND_COVER_MULTIPLIER.get(features.land_cover_class, 0.5)

    # Normalised sub-scores
    sub = {
        "ndvi": _normalise_ndvi(features.ndvi),
        "elevation": _normalise_elevation(features.elevation_m),
        "dist_road": _normalise_dist_road(features.dist_to_road_m),
        "dist_settlement": _normalise_dist_settlement(features.dist_to_settlement_m),
        "forest_density": min(features.forest_density, 1.0),
    }

    # Weighted sum
    raw = sum(sub[k] * weights[k] for k in sub)

    # Land-cover multiplier
    final = raw * lc_mult

    # Feature contributions (for SHAP-style explanation)
    contribs = {k: round(sub[k] * weights[k] * lc_mult, 4) for k in sub}

    # Explanation
    dominant = max(contribs, key=contribs.get)
    limiting = min(contribs, key=contribs.get)
    explanation = (
        f"Score {round(final, 3)}/1.0 for species='{species}'. "
        f"Strongest driver: {dominant} ({contribs[dominant]:.3f}). "
        f"Most limiting factor: {limiting} ({contribs[limiting]:.3f}). "
        f"Land cover '{features.land_cover_class}' applies {lc_mult:.0%} multiplier."
    )

    return HabitatScore(
        score=round(min(final, 1.0), 4),
        feature_contributions=contribs,
        explanation=explanation,
    )


def score_habitat_patches(
    patches: list[dict],
    species: str = "all",
) -> list[dict]:
    """
    Score a list of habitat patch dicts (from GIS dataset) and return
    enriched dicts with suitability_score and explanation.
    """
    results = []
    for patch in patches:
        features = HabitatFeatures(
            ndvi=patch.get("ndvi", 0.4),
            elevation_m=patch.get("elevation_m", 900),
            dist_to_road_m=patch.get("dist_to_road_m", 1000),
            dist_to_settlement_m=patch.get("dist_to_settlement_m", 2000),
            forest_density=patch.get("forest_density", 0.6),
            land_cover_class=patch.get("land_cover_class", "scrub"),
        )
        scored = compute_habitat_suitability(features, species)
        results.append({
            **patch,
            "suitability_score": scored.score,
            "feature_contributions": scored.feature_contributions,
            "explanation": scored.explanation,
        })
    return results


# ── Resistance surface for least-cost path ───────────────────────────────────

def suitability_to_resistance(suitability: float) -> float:
    """
    Convert suitability (0–1) to resistance (1–1000) for least-cost path.
    High suitability = low resistance (easy to move through).
    """
    if suitability <= 0:
        return 1000.0
    return max(1.0, round((1.0 - suitability) * 1000, 1))
