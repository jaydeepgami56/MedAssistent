"""
Agent REST API Router - Core endpoints for agent interaction and skill execution.

Provides endpoints for:
- Listing all agents and retrieving individual agent details
- Streaming chat conversations with agents
- Executing specific agent skills
- Domain-specific endpoints for triage, radiology, pharmacy, monitoring, documentation, and research
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, Any
import logging

from backend.agents.triage_agent import get_triage_agent
from backend.agents.radiology_agent import get_radiology_agent
from backend.agents.diagnostic_agent import get_diagnostic_agent
from backend.agents.pharmacy_agent import get_pharmacy_agent
from backend.agents.monitoring_agent import get_monitoring_agent
from backend.agents.documentation_agent import get_documentation_agent
from backend.agents.research_agent import get_research_agent
from backend.agents.coordinator_agent import get_coordinator_agent


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents", tags=["agents"])


# Pydantic models for request/response validation
class ChatRequest(BaseModel):
    message: str
    context: Optional[dict] = {}


class ExecuteSkillRequest(BaseModel):
    skill_name: str
    params: dict


class TriageAssessRequest(BaseModel):
    chief_complaint: str
    symptoms: list[str]
    vitals: dict
    history: Optional[dict] = {}
    allergies: Optional[list[str]] = []


class PharmacyCheckRequest(BaseModel):
    drug_names: list[str]
    patient_id: Optional[str] = None
    patient_data: Optional[dict] = {}


class VitalsRequest(BaseModel):
    heart_rate: int
    systolic_bp: int
    diastolic_bp: int
    respiratory_rate: int
    temperature: float
    spo2: int
    avpu: Optional[str] = "Alert"


class DocumentationRequest(BaseModel):
    encounter_data: dict


class ResearchRequest(BaseModel):
    query: str


# Helper function to get all agents
def get_all_agents():
    """Get all registered agents."""
    agents = []

    # Get each agent singleton
    triage = get_triage_agent()
    if triage:
        agents.append(triage)

    radiology = get_radiology_agent()
    if radiology:
        agents.append(radiology)

    diagnostic = get_diagnostic_agent()
    if diagnostic:
        agents.append(diagnostic)

    pharmacy = get_pharmacy_agent()
    if pharmacy:
        agents.append(pharmacy)

    monitoring = get_monitoring_agent()
    if monitoring:
        agents.append(monitoring)

    documentation = get_documentation_agent()
    if documentation:
        agents.append(documentation)

    research = get_research_agent()
    if research:
        agents.append(research)

    coordinator = get_coordinator_agent()
    if coordinator:
        agents.append(coordinator)

    return agents


def get_agent_by_id(agent_id: str):
    """Get a specific agent by ID."""
    agent_getters = {
        "triage": get_triage_agent,
        "radiology": get_radiology_agent,
        "diagnostic": get_diagnostic_agent,
        "pharmacy": get_pharmacy_agent,
        "monitoring": get_monitoring_agent,
        "documentation": get_documentation_agent,
        "research": get_research_agent,
        "coordinator": get_coordinator_agent,
    }

    getter = agent_getters.get(agent_id)
    if not getter:
        return None

    return getter()


# Core agent endpoints
@router.get("")
async def list_agents():
    """
    List all registered agents.

    Returns:
        List of agent info dicts with id, name, status, skills, queue, models_used, color, icon
    """
    agents = get_all_agents()
    return [agent.get_info() for agent in agents]


@router.get("/{agent_id}")
async def get_agent(agent_id: str):
    """
    Get details for a specific agent.

    Args:
        agent_id: Agent identifier (triage, radiology, diagnostic, pharmacy, monitoring, documentation, research, coordinator)

    Returns:
        Agent info dict with id, name, status, skills, queue, models_used, color, icon

    Raises:
        HTTPException: 404 if agent not found
    """
    agent = get_agent_by_id(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")

    return agent.get_info()


@router.post("/{agent_id}/chat")
async def chat_with_agent(agent_id: str, request: ChatRequest):
    """
    Send a message to an agent and receive a streaming response.

    Args:
        agent_id: Agent identifier
        request: ChatRequest with message and optional context

    Returns:
        StreamingResponse with Server-Sent Events (SSE) format

    Raises:
        HTTPException: 404 if agent not found
    """
    agent = get_agent_by_id(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")

    async def generate():
        """Generate SSE stream from agent chat response."""
        try:
            async for chunk in agent.chat(request.message, request.context):
                # SSE format: data: <content>\n\n
                yield f"data: {chunk}\n\n"
        except Exception as e:
            logger.error(f"Error in chat stream for agent {agent_id}: {str(e)}")
            yield f"data: [ERROR] {str(e)}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.post("/{agent_id}/execute")
async def execute_skill(agent_id: str, request: ExecuteSkillRequest):
    """
    Execute a specific skill on an agent.

    Args:
        agent_id: Agent identifier
        request: ExecuteSkillRequest with skill_name and params

    Returns:
        Skill execution result dict

    Raises:
        HTTPException: 404 if agent not found, 400 if skill invalid
    """
    agent = get_agent_by_id(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")

    # Validate skill exists on agent
    if request.skill_name not in agent.skills:
        raise HTTPException(
            status_code=400,
            detail=f"Skill '{request.skill_name}' not available on agent '{agent_id}'. Available skills: {agent.skills}"
        )

    try:
        result = await agent.execute_skill(request.skill_name, request.params)
        return result
    except Exception as e:
        logger.error(f"Error executing skill {request.skill_name} on agent {agent_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Skill execution failed: {str(e)}")


@router.get("/skills/list")
async def list_all_skills():
    """
    List all registered skills across all agents.

    Returns:
        Dict mapping agent_id to list of skill names
    """
    agents = get_all_agents()
    skills_by_agent = {}

    for agent in agents:
        skills_by_agent[agent.agent_id] = agent.skills

    return skills_by_agent


# Domain-specific endpoints
@router.post("/triage/assess")
async def triage_assess(request: TriageAssessRequest):
    """
    Submit patient data for triage assessment and ESI scoring.

    Args:
        request: TriageAssessRequest with chief complaint, symptoms, vitals, history, allergies

    Returns:
        Triage assessment result with ESI level, red flags, routing recommendation

    Raises:
        HTTPException: 503 if triage agent not available
    """
    agent = get_triage_agent()
    if not agent:
        raise HTTPException(status_code=503, detail="Triage agent not available")

    try:
        result = await agent.execute_skill("esi_scoring", {
            "chief_complaint": request.chief_complaint,
            "symptoms": request.symptoms,
            "vitals": request.vitals,
            "history": request.history,
            "allergies": request.allergies,
        })
        return result
    except Exception as e:
        logger.error(f"Error in triage assessment: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Triage assessment failed: {str(e)}")


@router.post("/radiology/analyze")
async def radiology_analyze(
    file: UploadFile = File(...),
    study_type: str = "chest_xray",
    patient_id: Optional[str] = None
):
    """
    Submit an image for radiology analysis.

    Args:
        file: Uploaded image file (DICOM, PNG, JPG)
        study_type: Type of study (chest_xray, mri, ct_scan)
        patient_id: Optional patient identifier

    Returns:
        Analysis result with findings, impressions, confidence, KNN evidence

    Raises:
        HTTPException: 503 if radiology agent not available, 400 if invalid file
    """
    agent = get_radiology_agent()
    if not agent:
        raise HTTPException(status_code=503, detail="Radiology agent not available")

    # Read image bytes
    try:
        image_bytes = await file.read()
        if len(image_bytes) == 0:
            raise HTTPException(status_code=400, detail="Empty file uploaded")
    except Exception as e:
        logger.error(f"Error reading uploaded file: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Failed to read uploaded file: {str(e)}")

    try:
        result = await agent.execute_skill("xray_analysis", {
            "image_bytes": image_bytes,
            "study_type": study_type,
            "patient_id": patient_id or "unknown",
        })
        return result
    except Exception as e:
        logger.error(f"Error in radiology analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Radiology analysis failed: {str(e)}")


@router.post("/pharmacy/check")
async def pharmacy_check(request: PharmacyCheckRequest):
    """
    Check drug interactions and contraindications.

    Args:
        request: PharmacyCheckRequest with drug names, patient ID, patient data

    Returns:
        Drug interaction result with severity, interactions, contraindications

    Raises:
        HTTPException: 503 if pharmacy agent not available
    """
    agent = get_pharmacy_agent()
    if not agent:
        raise HTTPException(status_code=503, detail="Pharmacy agent not available")

    try:
        result = await agent.execute_skill("drug_interaction", {
            "drug_names": request.drug_names,
            "patient_id": request.patient_id,
            "patient_data": request.patient_data,
        })
        return result
    except Exception as e:
        logger.error(f"Error in pharmacy check: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Pharmacy check failed: {str(e)}")


@router.post("/monitoring/vitals")
async def monitoring_vitals(request: VitalsRequest):
    """
    Submit vital signs for monitoring and MEWS score calculation.

    Args:
        request: VitalsRequest with heart rate, BP, respiratory rate, temperature, SpO2, AVPU

    Returns:
        Monitoring result with MEWS score, alert level, trending data

    Raises:
        HTTPException: 503 if monitoring agent not available
    """
    agent = get_monitoring_agent()
    if not agent:
        raise HTTPException(status_code=503, detail="Monitoring agent not available")

    try:
        result = await agent.execute_skill("mews_score", {
            "heart_rate": request.heart_rate,
            "systolic_bp": request.systolic_bp,
            "diastolic_bp": request.diastolic_bp,
            "respiratory_rate": request.respiratory_rate,
            "temperature": request.temperature,
            "spo2": request.spo2,
            "avpu": request.avpu,
        })
        return result
    except Exception as e:
        logger.error(f"Error in vitals monitoring: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Vitals monitoring failed: {str(e)}")


@router.post("/documentation/generate")
async def documentation_generate(request: DocumentationRequest):
    """
    Generate clinical documentation (SOAP notes).

    Args:
        request: DocumentationRequest with encounter data

    Returns:
        Generated SOAP note with Subjective, Objective, Assessment, Plan sections

    Raises:
        HTTPException: 503 if documentation agent not available
    """
    agent = get_documentation_agent()
    if not agent:
        raise HTTPException(status_code=503, detail="Documentation agent not available")

    try:
        result = await agent.execute_skill("soap_notes", request.encounter_data)
        return result
    except Exception as e:
        logger.error(f"Error in documentation generation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Documentation generation failed: {str(e)}")


@router.post("/research/search")
async def research_search(request: ResearchRequest):
    """
    Search clinical evidence and guidelines.

    Args:
        request: ResearchRequest with search query

    Returns:
        Research results with PubMed articles, evidence levels, guideline recommendations

    Raises:
        HTTPException: 503 if research agent not available
    """
    agent = get_research_agent()
    if not agent:
        raise HTTPException(status_code=503, detail="Research agent not available")

    try:
        result = await agent.execute_skill("guideline_search", {"query": request.query})
        return result
    except Exception as e:
        logger.error(f"Error in research search: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Research search failed: {str(e)}")


# Queue/Data endpoints for frontend dashboard
@router.get("/triage/queue")
async def get_triage_queue():
    """
    Get current triage patient queue.

    Returns:
        List of patients in triage queue with ESI levels, complaints, and wait times

    Note:
        This is mock data for now. In production, would query from database.
    """
    # Mock data matching the frontend structure
    return [
        {
            "id": 1,
            "name": "Patient A — 67F",
            "complaint": "Chest pain, shortness of breath",
            "esi": 1,
            "color": "#ef4444",
            "label": "Resuscitation",
            "time": "0 min"
        },
        {
            "id": 2,
            "name": "Patient B — 45M",
            "complaint": "Stroke symptoms (FAST positive)",
            "esi": 2,
            "color": "#f97316",
            "label": "Emergency",
            "time": "< 10 min"
        },
        {
            "id": 3,
            "name": "Patient C — 32F",
            "complaint": "Abdominal pain, fever 39.2°C",
            "esi": 3,
            "color": "#eab308",
            "label": "Urgent",
            "time": "30 min"
        },
        {
            "id": 4,
            "name": "Patient D — 28M",
            "complaint": "Ankle sprain, moderate swelling",
            "esi": 4,
            "color": "#22c55e",
            "label": "Semi-urgent",
            "time": "60 min"
        },
        {
            "id": 5,
            "name": "Patient E — 55F",
            "complaint": "Prescription refill request",
            "esi": 5,
            "color": "#3b82f6",
            "label": "Non-urgent",
            "time": "120 min"
        }
    ]


@router.get("/radiology/reports/latest")
async def get_latest_radiology_report():
    """
    Get the most recent radiology report.

    Returns:
        Latest radiology report with findings, confidence scores, and recommendations

    Note:
        This is mock data for now. In production, would query from database.
    """
    return {
        "patient": "Patient B — 45M",
        "modality": "Chest X-Ray (PA)",
        "findings": [
            {
                "text": "Bilateral infiltrates in lower lobes",
                "confidence": 0.94,
                "severity": "high"
            },
            {
                "text": "Mild cardiomegaly noted",
                "confidence": 0.87,
                "severity": "moderate"
            },
            {
                "text": "No pneumothorax identified",
                "confidence": 0.96,
                "severity": "normal"
            },
            {
                "text": "Costophrenic angles blunted bilaterally",
                "confidence": 0.82,
                "severity": "moderate"
            }
        ],
        "similarCases": 4,
        "recommendation": "Correlate with CT for further evaluation. Suggest cardiology consult."
    }


@router.get("/monitoring/vitals/latest")
async def get_latest_vitals():
    """
    Get the most recent vital signs for monitoring.

    Returns:
        Latest vital signs with heart rate, BP, SpO2, temperature, respiratory rate, and MEWS score

    Note:
        This is mock data for now. In production, would query from database or monitoring system.
    """
    return {
        "hr": 88,
        "bp": "132/84",
        "spo2": 97,
        "temp": 37.1,
        "rr": 18,
        "mews": 2
    }
