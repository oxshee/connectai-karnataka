"""
ConnectAI Karnataka — Explainable AI Service

Uses Claude (Anthropic API) to generate plain-language explanations of:
  - Corridor connectivity analysis results
  - Infrastructure impact predictions
  - Restoration recommendations
  - Policy briefs for Karnataka Forest Department

Falls back to structured template-based explanations when API unavailable.
"""
from __future__ import annotations
import logging
import httpx
from typing import Any

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

SYSTEM_PROMPT = """You are ConnectAI Karnataka, an expert AI system for ecological 
corridor intelligence. You have deep knowledge of:
- Karnataka's wildlife (Asian elephants, Bengal tigers, leopards, dholes)
- Western Ghats and Deccan Plateau ecosystems  
- Wildlife corridor science and landscape ecology
- Karnataka Forest Department policies and protected areas
- Infrastructure impact assessment (roads, railways, townships)
- Ecological restoration methods for dry deciduous and evergreen forests

Always be specific to Karnataka geography. Use scientific names when relevant.
Be concise (3–5 sentences) unless asked for a detailed report.
Cite approximate figures where known. Use ₹ for costs.
"""


async def explain_connectivity(
    corridor_name: str,
    score: float,
    bottlenecks: list[dict],
    paths: list[Any],
    species: list[str],
) -> str:
    """Generate plain-language explanation of corridor connectivity analysis."""
    bn_desc = "; ".join(
        f"{b['name']} (centrality {b['centrality']:.3f})" for b in bottlenecks[:3]
    ) if bottlenecks else "none identified"

    prompt = (
        f"Corridor: {corridor_name}\n"
        f"Connectivity score: {score}/100\n"
        f"Species supported: {', '.join(species[:4])}\n"
        f"Top bottleneck zones: {bn_desc}\n"
        f"Paths found: {len(paths)}\n\n"
        "Explain this corridor's ecological health in 4 sentences for a Karnataka Forest "
        "Department officer. Mention specific intervention priorities."
    )
    return await _call_claude(prompt, fallback=_fallback_connectivity(corridor_name, score, bottlenecks))


async def explain_impact(
    corridor_name: str,
    project_type: str,
    project_name: str,
    metrics: dict,
    recommendations: list[dict],
) -> str:
    """Generate impact analysis explanation."""
    recs_text = "; ".join(r["description"][:80] for r in recommendations[:3])
    prompt = (
        f"Project: {project_name} ({project_type}) through {corridor_name}\n"
        f"Connectivity loss: {metrics.get('connectivity_loss_pct')}%\n"
        f"Habitat loss: {metrics.get('habitat_loss_ha')} ha\n"
        f"Elephant passage risk: {metrics.get('elephant_passage_risk')}\n"
        f"Tiger corridor break: {metrics.get('tiger_corridor_break')}\n"
        f"Restoration cost: ₹{metrics.get('restoration_cost_cr')} Cr\n"
        f"Top mitigations: {recs_text}\n\n"
        "Write a 4-sentence impact assessment for Karnataka environmental regulators. "
        "Be specific about wildlife consequences and legally required mitigations under "
        "the Wildlife Protection Act 1972 and EIA Notification 2006."
    )
    return await _call_claude(prompt, fallback=_fallback_impact(project_name, metrics))


async def explain_restoration(
    corridor_name: str,
    zones: list[dict],
    budget_cr: float,
    connectivity_gain: float,
) -> str:
    """Generate restoration plan explanation."""
    zone_names = ", ".join(z["name"] for z in zones[:4])
    all_species = []
    for z in zones:
        all_species.extend(z.get("native_species", []))
    species_str = ", ".join(list(set(all_species))[:6])

    prompt = (
        f"Corridor: {corridor_name}\n"
        f"Budget: ₹{budget_cr} Cr\n"
        f"Restoration zones: {zone_names}\n"
        f"Projected connectivity gain: +{connectivity_gain}%\n"
        f"Native species to plant: {species_str}\n\n"
        "Write a 5-sentence restoration action plan for Karnataka Forest Department "
        "including planting seasons, monitoring milestones, and expected wildlife response timeline."
    )
    return await _call_claude(prompt, fallback=_fallback_restoration(corridor_name, budget_cr, connectivity_gain))


async def answer_conservation_question(question: str, context: str = "") -> str:
    """Answer an open conservation/ecology question in Karnataka context."""
    prompt = f"{context}\n\nQuestion: {question}" if context else question
    return await _call_claude(prompt, fallback="AI analysis unavailable. Please configure ANTHROPIC_API_KEY.")


async def _call_claude(prompt: str, fallback: str = "") -> str:
    """Call Anthropic Messages API. Returns fallback string on any error."""
    api_key = settings.anthropic_api_key
    if not api_key:
        logger.info("No Anthropic API key configured — using template fallback.")
        return fallback or "Configure ANTHROPIC_API_KEY for AI-powered explanations."

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-sonnet-4-6",
                    "max_tokens": 600,
                    "system": SYSTEM_PROMPT,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["content"][0]["text"]
    except httpx.HTTPStatusError as e:
        logger.error(f"Claude API HTTP error: {e.response.status_code}")
        return fallback
    except Exception as e:
        logger.error(f"Claude API error: {e}")
        return fallback


# ── Template fallbacks (used when no API key is configured) ─────────────────

def _fallback_connectivity(name: str, score: float, bottlenecks: list) -> str:
    level = "critically fragmented" if score < 60 else "moderately connected" if score < 75 else "well connected"
    bn = bottlenecks[0]["name"] if bottlenecks else "multiple zones"
    return (
        f"The {name} is {level} with a connectivity score of {score}/100. "
        f"The primary bottleneck is at {bn}, requiring immediate intervention. "
        "Habitat fragmentation from encroachment and road traffic are the dominant stressors. "
        "Priority actions: wildlife crossings, buffer reforestation, and traffic speed restrictions."
    )


def _fallback_impact(project_name: str, metrics: dict) -> str:
    loss = metrics.get("connectivity_loss_pct", 0)
    risk = metrics.get("elephant_passage_risk", "Unknown")
    return (
        f"{project_name} is projected to cause {loss}% connectivity loss to the affected corridor. "
        f"Elephant passage risk is rated {risk}, requiring mandatory wildlife underpasses. "
        f"Estimated restoration cost: ₹{metrics.get('restoration_cost_cr', 0)} Cr. "
        "Under EIA Notification 2006, a comprehensive wildlife impact assessment and "
        "mitigation plan must be submitted before environmental clearance."
    )


def _fallback_restoration(corridor: str, budget: float, gain: float) -> str:
    return (
        f"The restoration plan for {corridor} allocates ₹{budget:.1f} Cr across "
        "reforestation, wildlife crossing infrastructure, and riparian buffer zones. "
        f"Projected connectivity gain of +{gain:.1f}% is achievable within 5 years. "
        "Plant native dry deciduous species (Tectona grandis, Dalbergia latifolia) "
        "in Year 1–2; commission underpasses in Year 2; monitor wildlife crossings annually."
    )
