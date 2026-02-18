"""Candidate search service - parses natural language and queries MongoDB."""
import json
import re
from typing import Any

import google.generativeai as genai
from pymongo import DESCENDING

from app.config import settings
from app.database import get_candidates_collection
from app.models import ParsedQuery, SearchResult, SearchResponse


def _parse_years_from_string(years_str: str) -> int | None:
    """Extract years as integer from strings like '6 years', '2+ years', etc."""
    if not years_str:
        return None
    match = re.search(r"(\d+)", str(years_str))
    return int(match.group(1)) if match else None


def _parse_query_with_gemini(natural_query: str) -> ParsedQuery:
    """Use Gemini 2.5 Flash to extract structured search criteria from natural language."""
    if not settings.gemini_api_key:
        return ParsedQuery()

    genai.configure(api_key=settings.gemini_api_key)
    model = genai.GenerativeModel(settings.gemini_model)

    prompt = f"""
You are a hiring search assistant. Extract search criteria from this HR query.

Query: "{natural_query}"

Return a JSON object with these fields (use null for missing):
- skills: list of technical skills (e.g. ["Python", "Penetration Testing"])
- location: city name or null
- min_years_experience: integer or null (e.g. 2)
- max_years_experience: integer or null
- current_role: job title or null
- candidate_name: person's first/last name if searching by name (e.g. "Rahul Mehra" or "Rahul") or null

Return ONLY valid JSON, no other text.
Example: {{"skills": ["Python"], "location": "Pune", "min_years_experience": 2, "max_years_experience": null, "current_role": null, "candidate_name": "Rahul Mehra"}}
"""
    try:
        response = model.generate_content(prompt)
        text = (response.text or "").strip()
        # Remove markdown code blocks if present
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*", "", text)
            text = re.sub(r"\s*```\s*$", "", text)
        data = json.loads(text)
        return ParsedQuery(
            skills=data.get("skills", []),
            location=data.get("location"),
            min_years_experience=data.get("min_years_experience"),
            max_years_experience=data.get("max_years_experience"),
            current_role=data.get("current_role"),
            candidate_name=data.get("candidate_name"),
        )
    except Exception:
        return ParsedQuery()


def _build_mongo_query(parsed: ParsedQuery) -> dict[str, Any]:
    """Build MongoDB query from parsed criteria."""
    conditions: list[dict[str, Any]] = []

    # Skills: match any of the requested skills (case-insensitive)
    if parsed.skills:
        skills_regex = [re.compile(re.escape(s), re.IGNORECASE) for s in parsed.skills]
        conditions.append({"output.summary.technical_skills": {"$in": skills_regex}})

    # Location: case-insensitive
    if parsed.location:
        conditions.append(
            {
                "output.candidate.location": {
                    "$regex": re.escape(parsed.location),
                    "$options": "i",
                }
            }
        )

    # Years of experience: stored as "6 years" etc.
    if parsed.min_years_experience is not None or parsed.max_years_experience is not None:
        # We'll filter in Python after fetch since years_experience is a string
        pass

    # Current role
    if parsed.current_role:
        conditions.append(
            {
                "output.summary.current_role": {
                    "$regex": re.escape(parsed.current_role),
                    "$options": "i",
                }
            }
        )

    # Candidate name: match first_name + last_name (case-insensitive)
    if parsed.candidate_name and parsed.candidate_name.strip():
        name_pattern = re.escape(parsed.candidate_name.strip())
        conditions.append(
            {
                "$expr": {
                    "$regexMatch": {
                        "input": {
                            "$concat": [
                                {"$ifNull": ["$output.candidate.first_name", ""]},
                                " ",
                                {"$ifNull": ["$output.candidate.last_name", ""]},
                            ]
                        },
                        "regex": name_pattern,
                        "options": "i",
                    }
                }
            }
        )

    if not conditions:
        return {}
    return {"$and": conditions} if len(conditions) > 1 else conditions[0]


def _doc_to_search_result(doc: dict) -> SearchResult:
    """Convert MongoDB document to SearchResult."""
    output = doc.get("output") or {}
    candidate = output.get("candidate") or {}
    summary = output.get("summary") or {}
    fit_score = output.get("fit_score") or {}

    return SearchResult(
        id=str(doc["_id"]),
        first_name=candidate.get("first_name", ""),
        last_name=candidate.get("last_name", ""),
        email=candidate.get("email", ""),
        location=candidate.get("location", ""),
        years_experience=summary.get("years_experience", ""),
        technical_skills=summary.get("technical_skills", []),
        fit_score=fit_score.get("overall", ""),
    )


def _filter_by_experience(
    results: list[SearchResult],
    min_years: int | None,
    max_years: int | None,
) -> list[SearchResult]:
    """Filter results by years of experience."""
    if min_years is None and max_years is None:
        return results
    filtered = []
    for r in results:
        y = _parse_years_from_string(r.years_experience)
        if y is None:
            continue
        if min_years is not None and y < min_years:
            continue
        if max_years is not None and y > max_years:
            continue
        filtered.append(r)
    return filtered


async def search_candidates(
    query: str,
    ids_only: bool = False,
    skills: list[str] | None = None,
    location: str | None = None,
    min_years: int | None = None,
    max_years: int | None = None,
    name: str | None = None,
    use_gemini: bool = True,
) -> SearchResponse:
    """
    Search candidates by natural language or explicit criteria.

    - query: Natural language (e.g. "Python developer from Pune with 2 years experience")
    - ids_only: If True, return only list of IDs
    - skills, location, min_years, max_years, name: Override parsed criteria
    - use_gemini: Use Gemini to parse natural language (requires API key)
    """
    parsed = ParsedQuery()

    if use_gemini and settings.gemini_api_key and query:
        parsed = _parse_query_with_gemini(query)

    # Override with explicit params if provided
    if skills:
        parsed.skills = skills
    if location:
        parsed.location = location
    if min_years is not None:
        parsed.min_years_experience = min_years
    if max_years is not None:
        parsed.max_years_experience = max_years
    if name:
        parsed.candidate_name = name

    mongo_query = _build_mongo_query(parsed)
    coll = get_candidates_collection()

    cursor = coll.find(mongo_query).sort("output.fit_score.overall", DESCENDING)
    raw_docs = await cursor.to_list(length=100)

    results = [_doc_to_search_result(d) for d in raw_docs]
    results = _filter_by_experience(
        results, parsed.min_years_experience, parsed.max_years_experience
    )

    ids = [r.id for r in results]

    return SearchResponse(
        query=query or "manual search",
        total_matches=len(results),
        candidates=[] if ids_only else results,
        ids_only=ids,
    )
