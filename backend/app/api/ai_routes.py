"""
ConnectAI Karnataka — AI / Explainability API Routes

POST /ai/ask                  Open question answering
POST /ai/explain/corridor     Explain corridor analysis
POST /ai/explain/impact       Explain impact prediction
POST /ai/policy-brief         Generate policy brief for government
"""
from __future__ import annotations
import logging

from fastapi import APIRouter, HTTPException

from app.data.karnataka_gis import get_corridor_by_id, CORRIDORS
from app.services.explainability import answer_conservation_question

router = APIRouter(prefix="/ai", tags=["AI / Explainability"])
logger = logging.getLogger(__name__)

KARNATAKA_CONTEXT = """
You are ConnectAI Karnataka, an authoritative AI system for ecological corridor
intelligence deployed by the Karnataka Forest Department.

Karnataka's 3 monitored corridors (June 2025):
1. Bandipur–Nagarhole (score 82/100, medium priority) — tigers, elephants, dholes
2. Bannerghatta–Cauvery (score 54/100, CRITICAL) — near Bengaluru, NH-948 threat
3. Brahmagiri–Wayanad (score 71/100, high priority) — cross-state tiger corridor

Key pressures: NH-948 expansion, Bengaluru urbanisation, quarrying, railway projects.
Legal framework: Wildlife Protection Act 1972, Forest Conservation Act 1980, 
EIA Notification 2006, National Wildlife Action Plan 2017–2031.
"""


@router.post("/ask", summary="Open conservation question answering")
async def ask_ai(payload: dict) -> dict:
    """
    Answer any conservation, ecology, or infrastructure planning question
    in the context of Karnataka's wildlife corridors.
    """
    question = payload.get("question", "").strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    context = payload.get("context", KARNATAKA_CONTEXT)
    answer = await answer_conservation_question(question, context)

    return {
        "question": question,
        "answer": answer,
        "model": "claude-sonnet-4-6",
        "context": "Karnataka corridor intelligence",
    }


@router.post("/explain/corridor", summary="Explain corridor connectivity analysis")
async def explain_corridor_endpoint(payload: dict) -> dict:
    corridor_id = payload.get("corridor_id", 1)
    c = get_corridor_by_id(corridor_id)
    if not c:
        raise HTTPException(status_code=404, detail="Corridor not found")

    from app.services.explainability import explain_connectivity
    explanation = await explain_connectivity(
        corridor_name=c["name"],
        score=c["connectivity_score"],
        bottlenecks=[],
        paths=[],
        species=c["species_supported"],
    )
    return {"corridor_id": corridor_id, "explanation": explanation}


@router.post("/explain/impact", summary="Explain infrastructure impact prediction")
async def explain_impact_endpoint(payload: dict) -> dict:
    from app.services.explainability import explain_impact
    explanation = await explain_impact(
        corridor_name=payload.get("corridor_name", "Karnataka corridor"),
        project_type=payload.get("project_type", "highway"),
        project_name=payload.get("project_name", "Unnamed project"),
        metrics=payload.get("metrics", {}),
        recommendations=payload.get("recommendations", []),
    )
    return {"explanation": explanation}


@router.post("/policy-brief", summary="Generate government policy brief")
async def policy_brief(payload: dict) -> dict:
    """
    Generates a formal policy brief for Karnataka Forest Department /
    Ministry of Environment officers summarising corridor status and recommendations.
    """
    corridor_id = payload.get("corridor_id")
    audience = payload.get("audience", "Karnataka Forest Department")

    if corridor_id:
        c = get_corridor_by_id(corridor_id)
        corridor_context = (
            f"Corridor: {c['name']}, Score: {c['connectivity_score']}/100, "
            f"Priority: {c['priority'].upper()}, "
            f"Species: {', '.join(c['species_supported'][:3])}, "
            f"Alerts: {'; '.join(c.get('alerts', ['None']))}"
        ) if c else ""
    else:
        # All corridors summary
        corridor_context = "\n".join(
            f"- {c['name']}: {c['connectivity_score']}/100 ({c['priority']})"
            for c in CORRIDORS
        )

    prompt = (
        f"{KARNATAKA_CONTEXT}\n\n"
        f"Audience: {audience}\n"
        f"Corridor context: {corridor_context}\n\n"
        "Write a formal 200-word policy brief with: Executive Summary, "
        "Current Status, Priority Actions (numbered), Budget Estimate, "
        "and Recommended Next Steps. Use government report style."
    )

    brief = await answer_conservation_question(prompt)

    return {
        "audience": audience,
        "corridor_id": corridor_id,
        "policy_brief": brief,
        "classification": "For Official Use — Karnataka Forest Department",
    }
