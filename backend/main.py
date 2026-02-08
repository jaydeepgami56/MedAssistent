"""
MedAssist AI FastAPI Backend
Main application entry point with health endpoint and CORS configuration.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from backend.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager for startup and shutdown events.

    This will be used later for:
    - Initializing database connections
    - Loading AI models
    - Setting up Qdrant collections
    """
    # Startup
    print("MedAssist AI Backend starting...")
    print(f"   Claude Model: {settings.CLAUDE_MODEL}")
    print(f"   Qdrant: {settings.QDRANT_HOST}:{settings.QDRANT_PORT}")
    print(f"   PostgreSQL: {settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}")
    print(f"   Orthanc: {settings.ORTHANC_HOST}:{settings.ORTHANC_PORT}")
    print(f"   Neo4j: {settings.NEO4J_URI}")

    yield

    # Shutdown
    print("MedAssist AI Backend shutting down...")


# Initialize FastAPI app
app = FastAPI(
    title="MedAssist AI API",
    description="Multi-agent medical AI platform for clinical decision support",
    version="2.0",
    lifespan=lifespan,
)

# Configure CORS middleware (allow all origins for development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """
    Health check endpoint.

    Returns system status, number of agents online, and API version.
    """
    return {
        "status": "ok",
        "agents_online": 7,
        "version": "2.0"
    }


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "MedAssist AI API",
        "version": "2.0",
        "docs": "/docs",
        "health": "/health"
    }
