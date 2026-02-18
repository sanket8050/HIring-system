"""Hiring Search Service - FastAPI application."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import close_database
from app.routers import candidates


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown."""
    yield
    await close_database()


app = FastAPI(
    title="Hiring Search Service",
    description="Search candidates from resume analysis data stored in MongoDB. "
    "HR can query in natural language: e.g. 'Python developer from Pune with 2 years experience'.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(candidates.router, prefix="/api")


@app.get("/")
async def root():
    """Health check and API info."""
    return {
        "service": "Hiring Search Service",
        "status": "running",
        "docs": "/docs",
        "search": "/api/candidates/search",
    }


@app.get("/health")
async def health():
    """Health check endpoint for monitoring."""
    return {"status": "ok"}
