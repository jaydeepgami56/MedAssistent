"""
MedAssist AI FastAPI Backend
Main application entry point with health endpoint and CORS configuration.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from backend.config import settings
from backend.integrations.database import init_db, close_db_pool
from backend.integrations.qdrant_client import init_qdrant, close_qdrant
from backend.models.clinical_bert import init_clinical_bert
from backend.models.medimageinsight import init_medimageinsight
from backend.models.medgemma import init_medgemma
from backend.agents.triage_agent import init_triage_agent, get_triage_agent
from backend.agents.radiology_agent import init_radiology_agent, get_radiology_agent
from backend.agents.diagnostic_agent import init_diagnostic_agent, get_diagnostic_agent
from backend.agents.pharmacy_agent import init_pharmacy_agent, get_pharmacy_agent
from backend.agents.monitoring_agent import init_monitoring_agent, get_monitoring_agent
from backend.agents.documentation_agent import init_documentation_agent, get_documentation_agent
from backend.agents.research_agent import init_research_agent, get_research_agent
from backend.agents.coordinator_agent import init_coordinator_agent, get_coordinator_agent
from backend.integrations.rxnorm_client import init_rxnorm, close_rxnorm
from backend.integrations.drugbank_client import init_drugbank, close_drugbank
from backend.integrations.pubmed_client import init_pubmed, close_pubmed
from backend.integrations.fhir_client import init_fhir, close_fhir
from backend.integrations.dicom_client import init_dicom, close_dicom
from backend.routers import agents_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager for startup and shutdown events.

    Handles:
    - Database connection pool creation and schema initialization
    - Resource cleanup on shutdown
    """
    # Startup
    print("MedAssist AI Backend starting...")
    print(f"   LM Studio Model: {settings.LM_STUDIO_MODEL}")
    print(f"   Qdrant: {settings.QDRANT_HOST}:{settings.QDRANT_PORT}")
    print(f"   PostgreSQL: {settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}")
    print(f"   Orthanc: {settings.ORTHANC_HOST}:{settings.ORTHANC_PORT}")
    print(f"   Neo4j: {settings.NEO4J_URI}")

    # Initialize database schema
    await init_db()

    # Initialize Qdrant vector database
    await init_qdrant()

    # Initialize ClinicalBERT service
    init_clinical_bert()

    # Initialize MedImageInsight service
    init_medimageinsight(model_dir=settings.MEDIMAGEINSIGHT_MODEL_DIR)

    # Initialize MedGemma service
    init_medgemma(model_dir=None)

    # Initialize Triage Agent
    init_triage_agent()

    # Initialize Radiology Agent
    init_radiology_agent()

    # Initialize RxNorm, DrugBank, PubMed, FHIR, and DICOM clients
    await init_rxnorm()
    await init_drugbank()
    await init_pubmed()
    await init_fhir()
    await init_dicom()

    # Initialize Pharmacy Agent
    await init_pharmacy_agent()

    # Initialize Monitoring Agent
    init_monitoring_agent()

    # Initialize Documentation Agent
    init_documentation_agent()

    # Initialize Research Agent
    init_research_agent()

    # Initialize Diagnostic Agent
    init_diagnostic_agent()

    # Initialize Coordinator Agent
    init_coordinator_agent()

    # Register all specialist agents with the coordinator
    coordinator = get_coordinator_agent()
    if coordinator:
        # Register each specialist agent for routing
        triage = get_triage_agent()
        if triage:
            coordinator.register_specialist("triage", triage)

        radiology = get_radiology_agent()
        if radiology:
            coordinator.register_specialist("radiology", radiology)

        diagnostic = get_diagnostic_agent()
        if diagnostic:
            coordinator.register_specialist("diagnostic", diagnostic)

        pharmacy = get_pharmacy_agent()
        if pharmacy:
            coordinator.register_specialist("pharmacy", pharmacy)

        monitoring = get_monitoring_agent()
        if monitoring:
            coordinator.register_specialist("monitoring", monitoring)

        documentation = get_documentation_agent()
        if documentation:
            coordinator.register_specialist("documentation", documentation)

        research = get_research_agent()
        if research:
            coordinator.register_specialist("research", research)

        print(f"   Coordinator Agent registered {len(coordinator.specialist_agents)} specialists")

    yield

    # Shutdown
    print("MedAssist AI Backend shutting down...")
    await close_db_pool()
    await close_qdrant()
    await close_rxnorm()
    await close_drugbank()
    await close_pubmed()
    await close_fhir()
    await close_dicom()


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

# Include routers
app.include_router(agents_router)


@app.get("/health")
async def health_check():
    """
    Health check endpoint.

    Returns system status, number of agents online, and API version.
    """
    return {
        "status": "ok",
        "agents_online": 8,
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
