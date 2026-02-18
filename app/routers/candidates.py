"""Candidate search API routes."""
from fastapi import APIRouter, HTTPException, Query

from app.models import SearchResponse
from app.services.search_service import search_candidates

router = APIRouter(prefix="/candidates", tags=["candidates"])


@router.get("/search", response_model=SearchResponse)
async def search(
    q: str = Query(..., description="Natural language query, e.g. 'Python developer from Pune with 2 years experience'"),
    ids_only: bool = Query(False, description="Return only list of candidate IDs"),
    skills: str | None = Query(None, description="Comma-separated skills (overrides query parsing)"),
    location: str | None = Query(None, description="Location filter (overrides query parsing)"),
    min_years: int | None = Query(None, description="Minimum years of experience"),
    max_years: int | None = Query(None, description="Maximum years of experience"),
    name: str | None = Query(None, description="Search by candidate name (e.g. 'Rahul Mehra' or 'Rahul')"),
    use_gemini: bool = Query(True, description="Use Gemini to parse natural language query"),
):
    """
    Search candidates by natural language or explicit filters.

    **Examples:**
    - `?q=penetration testing skilled person from Chennai with 6 years`
    - `?q=Python developer from Pune&min_years=2`
    - `?q=xyz skilled person from pune with 2 years&ids_only=true`
    - `?q=test&name=Rahul Mehra` - search by candidate name
    """
    skills_list = [s.strip() for s in skills.split(",")] if skills else None
    result = await search_candidates(
        query=q,
        ids_only=ids_only,
        skills=skills_list,
        location=location,
        min_years=min_years,
        max_years=max_years,
        name=name,
        use_gemini=use_gemini,
    )
    return result


@router.get("/search/ids", response_model=list[str])
async def search_ids(
    q: str = Query(..., description="Natural language search query"),
    skills: str | None = Query(None),
    location: str | None = Query(None),
    min_years: int | None = Query(None),
    max_years: int | None = Query(None),
    name: str | None = Query(None, description="Search by candidate name"),
):
    """Convenience endpoint - returns only array of candidate IDs."""
    result = await search_candidates(
        query=q,
        ids_only=True,
        skills=[s.strip() for s in skills.split(",")] if skills else None,
        location=location,
        min_years=min_years,
        max_years=max_years,
        name=name,
    )
    return result.ids_only
