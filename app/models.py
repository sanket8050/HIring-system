"""Pydantic models for candidate data and API requests/responses."""
from pydantic import BaseModel, Field


class CandidateInfo(BaseModel):
    """Candidate basic information."""

    first_name: str = ""
    last_name: str = ""
    email: str = ""
    location: str = ""
    phone: str = ""
    expected_salary: str = ""
    notice_period: str = ""


class Summary(BaseModel):
    """Candidate summary from resume analysis."""

    years_experience: str = ""
    current_role: str = ""
    key_achievements: list[str] = Field(default_factory=list)
    technical_skills: list[str] = Field(default_factory=list)


class FitScore(BaseModel):
    """Fit score and reasoning."""

    overall: str = ""
    reasoning: list[str] = Field(default_factory=list)


class CandidateOutput(BaseModel):
    """Output object structure from MongoDB."""

    candidate: CandidateInfo | None = None
    summary: Summary | None = None
    fit_score: FitScore | None = None


class CandidateDocument(BaseModel):
    """Full candidate document as stored in MongoDB."""

    id: str = Field(alias="_id")
    output: CandidateOutput | None = None

    class Config:
        populate_by_name = True


class SearchResult(BaseModel):
    """Single search result - candidate ID and key info."""

    id: str
    first_name: str = ""
    last_name: str = ""
    email: str = ""
    location: str = ""
    years_experience: str = ""
    technical_skills: list[str] = Field(default_factory=list)
    fit_score: str = ""


class SearchResponse(BaseModel):
    """Response for candidate search."""

    query: str
    total_matches: int
    candidates: list[SearchResult] = Field(default_factory=list)
    ids_only: list[str] = Field(default_factory=list)


class ParsedQuery(BaseModel):
    """Structured query extracted from natural language using Gemini."""

    skills: list[str] = Field(default_factory=list)
    location: str | None = None
    min_years_experience: int | None = None
    max_years_experience: int | None = None
    current_role: str | None = None
    candidate_name: str | None = None
