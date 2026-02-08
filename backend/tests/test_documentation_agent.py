"""
Test suite for Documentation Agent - SOAP notes, discharge summaries, ICD-10 coding, referral letters.
"""

import pytest
import os
from backend.agents.documentation_agent import DocumentationAgent, init_documentation_agent, get_documentation_agent


# ============================================================================
# Test 1: Agent Initialization
# ============================================================================
def test_documentation_agent_initialization():
    """Test that Documentation Agent initializes with correct metadata."""
    api_key = os.getenv("ANTHROPIC_API_KEY", "test-key")
    agent = DocumentationAgent(anthropic_api_key=api_key)

    assert agent.agent_id == "docs"
    assert agent.name == "Documentation Agent"
    assert agent.status == "Active"
    assert agent.color == "#06b6d4"
    assert agent.icon == "📋"
    assert "soap_notes" in agent.skills
    assert "discharge_summary" in agent.skills
    assert "icd10_coding" in agent.skills
    assert "referral_letter" in agent.skills
    assert "Claude API" in agent.models_used


# ============================================================================
# Test 2: get_info() Method
# ============================================================================
def test_get_info():
    """Test that get_info() returns correct metadata dict."""
    api_key = os.getenv("ANTHROPIC_API_KEY", "test-key")
    agent = DocumentationAgent(anthropic_api_key=api_key)

    info = agent.get_info()

    assert info["agent_id"] == "docs"
    assert info["name"] == "Documentation Agent"
    assert len(info["skills"]) == 4
    assert len(info["models_used"]) == 1


# ============================================================================
# Test 3: Execute Skill - Invalid Skill
# ============================================================================
@pytest.mark.asyncio
async def test_execute_skill_invalid():
    """Test that execute_skill raises ValueError for invalid skill."""
    api_key = os.getenv("ANTHROPIC_API_KEY", "test-key")
    agent = DocumentationAgent(anthropic_api_key=api_key)

    with pytest.raises(ValueError, match="Unknown skill"):
        await agent.execute_skill("invalid_skill", {})


# ============================================================================
# Test 4: SOAP Notes - Basic Generation
# ============================================================================
@pytest.mark.asyncio
@pytest.mark.skipif(not os.getenv("ANTHROPIC_API_KEY"), reason="ANTHROPIC_API_KEY not set")
async def test_soap_notes_basic():
    """Test SOAP note generation with basic encounter data."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    agent = DocumentationAgent(anthropic_api_key=api_key)

    params = {
        "patient_id": "PT-12345",
        "encounter_data": {
            "chief_complaint": "Chest pain",
            "transcript": "Patient reports sharp chest pain for 2 hours, radiating to left arm.",
            "physical_exam": "Alert and oriented. BP 140/90, HR 95, RR 18. Chest clear to auscultation.",
            "triage_output": {
                "esi_level": 2,
                "vital_signs": {"hr": 95, "bp_sys": 140, "bp_dia": 90}
            }
        }
    }

    result = await agent.execute_skill("soap_notes", params)

    assert result["draft_status"] == "pending_review"
    assert "soap_sections" in result
    assert "subjective" in result["soap_sections"]
    assert "objective" in result["soap_sections"]
    assert "assessment" in result["soap_sections"]
    assert "plan" in result["soap_sections"]
    assert "icd10_codes" in result
    assert "Auto-generated — review and edit before finalizing" in result["disclaimer"]
    assert result["confidence"] > 0.0
    assert result["patient_id"] == "PT-12345"


# ============================================================================
# Test 5: SOAP Notes - Comprehensive Encounter Data
# ============================================================================
@pytest.mark.asyncio
@pytest.mark.skipif(not os.getenv("ANTHROPIC_API_KEY"), reason="ANTHROPIC_API_KEY not set")
async def test_soap_notes_comprehensive():
    """Test SOAP note generation with comprehensive encounter data."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    agent = DocumentationAgent(anthropic_api_key=api_key)

    params = {
        "patient_id": "PT-67890",
        "encounter_data": {
            "chief_complaint": "Shortness of breath",
            "transcript": "Patient reports increasing dyspnea over 3 days, worse with exertion.",
            "physical_exam": "Bilateral crackles at lung bases. JVD present. 2+ pitting edema.",
            "triage_output": {
                "esi_level": 3,
                "vital_signs": {"hr": 110, "bp_sys": 160, "bp_dia": 95, "spo2": 91}
            },
            "radiology_output": {
                "study_type": "Chest X-Ray",
                "findings": "Pulmonary edema, cardiomegaly",
                "primary_diagnosis": "Congestive heart failure"
            },
            "monitoring_output": {
                "vitals": {"hr": 110, "bp_sys": 160, "bp_dia": 95, "spo2": 91, "rr": 24, "temp": 37.2},
                "mews_total": 4
            },
            "pharmacy_output": {
                "interactions": []
            }
        }
    }

    result = await agent.execute_skill("soap_notes", params)

    assert result["draft_status"] == "pending_review"
    assert len(result["soap_sections"]["subjective"]) > 0
    assert len(result["soap_sections"]["objective"]) > 0
    assert len(result["soap_sections"]["assessment"]) > 0
    assert len(result["soap_sections"]["plan"]) > 0
    assert isinstance(result["icd10_codes"], list)
    assert result["confidence"] > 0.5  # Should be high with comprehensive data


# ============================================================================
# Test 6: SOAP Notes - Minimal Data
# ============================================================================
@pytest.mark.asyncio
@pytest.mark.skipif(not os.getenv("ANTHROPIC_API_KEY"), reason="ANTHROPIC_API_KEY not set")
async def test_soap_notes_minimal():
    """Test SOAP note generation with minimal encounter data."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    agent = DocumentationAgent(anthropic_api_key=api_key)

    params = {
        "patient_id": "PT-MIN-001",
        "encounter_data": {
            "chief_complaint": "Headache"
        }
    }

    result = await agent.execute_skill("soap_notes", params)

    assert result["draft_status"] == "pending_review"
    assert "soap_sections" in result
    assert result["confidence"] < 0.7  # Lower confidence with minimal data


# ============================================================================
# Test 7: SOAP Notes - Error Handling
# ============================================================================
@pytest.mark.asyncio
async def test_soap_notes_error_handling():
    """Test SOAP note generation handles errors gracefully."""
    # Use invalid API key to force error
    agent = DocumentationAgent(anthropic_api_key="invalid-key-for-testing")

    params = {
        "patient_id": "PT-ERROR-001",
        "encounter_data": {
            "chief_complaint": "Test complaint"
        }
    }

    result = await agent.execute_skill("soap_notes", params)

    assert result["draft_status"] == "error"
    assert "error" in result
    assert result["confidence"] == 0.0


# ============================================================================
# Test 8: ICD-10 Coding - From Clinical Text
# ============================================================================
@pytest.mark.asyncio
@pytest.mark.skipif(not os.getenv("ANTHROPIC_API_KEY"), reason="ANTHROPIC_API_KEY not set")
async def test_icd10_coding_clinical_text():
    """Test ICD-10 coding from clinical text."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    agent = DocumentationAgent(anthropic_api_key=api_key)

    params = {
        "clinical_text": "Patient presents with acute myocardial infarction. EKG shows ST elevation in leads II, III, aVF. Troponin elevated.",
        "top_k": 3
    }

    result = await agent.execute_skill("icd10_coding", params)

    assert result["draft_status"] == "pending_review"
    assert "icd10_codes" in result
    assert isinstance(result["icd10_codes"], list)
    assert len(result["icd10_codes"]) <= 3
    assert result["primary_code"] is not None
    assert "code" in result["primary_code"]
    assert "description" in result["primary_code"]
    assert "confidence" in result["primary_code"]


# ============================================================================
# Test 9: ICD-10 Coding - From Diagnosis List
# ============================================================================
@pytest.mark.asyncio
@pytest.mark.skipif(not os.getenv("ANTHROPIC_API_KEY"), reason="ANTHROPIC_API_KEY not set")
async def test_icd10_coding_diagnosis_list():
    """Test ICD-10 coding from diagnosis list."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    agent = DocumentationAgent(anthropic_api_key=api_key)

    params = {
        "diagnosis_list": [
            "Type 2 diabetes mellitus",
            "Essential hypertension",
            "Hyperlipidemia"
        ],
        "top_k": 5
    }

    result = await agent.execute_skill("icd10_coding", params)

    assert result["draft_status"] == "pending_review"
    assert len(result["icd10_codes"]) > 0
    assert len(result["icd10_codes"]) <= 5


# ============================================================================
# Test 10: ICD-10 Coding - Missing Input
# ============================================================================
@pytest.mark.asyncio
async def test_icd10_coding_missing_input():
    """Test ICD-10 coding with missing input."""
    api_key = os.getenv("ANTHROPIC_API_KEY", "test-key")
    agent = DocumentationAgent(anthropic_api_key=api_key)

    params = {}  # No clinical_text or diagnosis_list

    result = await agent.execute_skill("icd10_coding", params)

    assert result["draft_status"] == "error"
    assert "error" in result
    assert result["icd10_codes"] == []
    assert result["primary_code"] is None


# ============================================================================
# Test 11: Discharge Summary - Complete Data
# ============================================================================
@pytest.mark.asyncio
@pytest.mark.skipif(not os.getenv("ANTHROPIC_API_KEY"), reason="ANTHROPIC_API_KEY not set")
async def test_discharge_summary_complete():
    """Test discharge summary generation with complete data."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    agent = DocumentationAgent(anthropic_api_key=api_key)

    params = {
        "patient_id": "PT-DISCHARGE-001",
        "admission_date": "2025-02-01",
        "discharge_date": "2025-02-05",
        "hospital_course": "Patient admitted with pneumonia, treated with antibiotics. Improved over 4 days.",
        "encounter_history": [
            {"day": 1, "note": "Admitted with fever, cough, hypoxia"},
            {"day": 3, "note": "Improving, fever resolved"},
            {"day": 5, "note": "SpO2 normal on room air, ready for discharge"}
        ],
        "discharge_medications": ["Amoxicillin 500mg TID x 7 days", "Albuterol inhaler PRN"],
        "follow_up_plan": "Follow up with PCP in 1 week. Return if fever recurs."
    }

    result = await agent.execute_skill("discharge_summary", params)

    assert result["draft_status"] == "pending_review"
    assert "summary" in result
    assert "sections" in result
    assert len(result["summary"]) > 0
    assert "DISCHARGE SUMMARY" in result["summary"]
    assert result["patient_id"] == "PT-DISCHARGE-001"
    assert "admission_diagnosis" in result["sections"]
    assert "discharge_diagnosis" in result["sections"]


# ============================================================================
# Test 12: Discharge Summary - Minimal Data
# ============================================================================
@pytest.mark.asyncio
@pytest.mark.skipif(not os.getenv("ANTHROPIC_API_KEY"), reason="ANTHROPIC_API_KEY not set")
async def test_discharge_summary_minimal():
    """Test discharge summary generation with minimal data."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    agent = DocumentationAgent(anthropic_api_key=api_key)

    params = {
        "patient_id": "PT-DISCHARGE-002",
        "admission_date": "2025-02-01",
        "discharge_date": "2025-02-02",
        "hospital_course": "Brief admission for observation"
    }

    result = await agent.execute_skill("discharge_summary", params)

    assert result["draft_status"] == "pending_review"
    assert "summary" in result
    assert len(result["summary"]) > 0


# ============================================================================
# Test 13: Referral Letter - Complete
# ============================================================================
@pytest.mark.asyncio
@pytest.mark.skipif(not os.getenv("ANTHROPIC_API_KEY"), reason="ANTHROPIC_API_KEY not set")
async def test_referral_letter_complete():
    """Test referral letter generation with complete data."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    agent = DocumentationAgent(anthropic_api_key=api_key)

    params = {
        "patient_id": "PT-REF-001",
        "patient_name": "John Doe",
        "referring_provider": "Dr. Jane Smith",
        "specialist_type": "Cardiology",
        "reason_for_referral": "Evaluation of chest pain and abnormal EKG",
        "relevant_history": "62 yo male with HTN, DM. Recent episodes of chest pain on exertion. EKG shows ST changes.",
        "current_medications": ["Metoprolol 50mg BID", "Lisinopril 20mg daily", "Metformin 1000mg BID"],
        "attachments": ["EKG (02/05/2025)", "Lipid panel results"]
    }

    result = await agent.execute_skill("referral_letter", params)

    assert result["draft_status"] == "pending_review"
    assert "letter" in result
    assert len(result["letter"]) > 0
    assert result["patient_id"] == "PT-REF-001"
    assert result["specialist_type"] == "Cardiology"
    assert "Cardiology" in result["letter"]
    assert "John Doe" in result["letter"]


# ============================================================================
# Test 14: Referral Letter - Minimal
# ============================================================================
@pytest.mark.asyncio
@pytest.mark.skipif(not os.getenv("ANTHROPIC_API_KEY"), reason="ANTHROPIC_API_KEY not set")
async def test_referral_letter_minimal():
    """Test referral letter generation with minimal data."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    agent = DocumentationAgent(anthropic_api_key=api_key)

    params = {
        "patient_id": "PT-REF-002",
        "patient_name": "Jane Smith",
        "referring_provider": "Dr. Brown",
        "specialist_type": "Neurology",
        "reason_for_referral": "Evaluation of headaches",
        "relevant_history": "Recurrent migraine headaches"
    }

    result = await agent.execute_skill("referral_letter", params)

    assert result["draft_status"] == "pending_review"
    assert len(result["letter"]) > 0


# ============================================================================
# Test 15: Singleton Pattern
# ============================================================================
def test_singleton_pattern():
    """Test that init_documentation_agent and get_documentation_agent work correctly."""
    api_key = os.getenv("ANTHROPIC_API_KEY", "test-key")

    init_documentation_agent(anthropic_api_key=api_key)
    agent = get_documentation_agent()

    assert agent is not None
    assert agent.agent_id == "docs"


# ============================================================================
# Test 16: Singleton - Missing API Key
# ============================================================================
def test_singleton_missing_api_key():
    """Test that init_documentation_agent raises error with missing API key."""
    with pytest.raises(ValueError, match="ANTHROPIC_API_KEY required"):
        init_documentation_agent(anthropic_api_key="")


# ============================================================================
# Test 17: Chat Method
# ============================================================================
@pytest.mark.asyncio
@pytest.mark.skipif(not os.getenv("ANTHROPIC_API_KEY"), reason="ANTHROPIC_API_KEY not set")
async def test_chat_streaming():
    """Test chat method returns streaming response."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    agent = DocumentationAgent(anthropic_api_key=api_key)

    message = "What is a SOAP note?"
    context = {"patient_id": "PT-001", "doc_type": "SOAP"}

    chunks = []
    async for chunk in agent.chat(message, context):
        chunks.append(chunk)

    response = "".join(chunks)
    assert len(response) > 0
    assert "Auto-generated — review and edit before finalizing" in response


# ============================================================================
# Test 18: SOAP Confidence Calculation
# ============================================================================
def test_soap_confidence_calculation():
    """Test SOAP confidence calculation logic."""
    api_key = os.getenv("ANTHROPIC_API_KEY", "test-key")
    agent = DocumentationAgent(anthropic_api_key=api_key)

    # All sections populated, comprehensive data
    soap_sections = {
        "subjective": "Patient reports chest pain radiating to left arm for 2 hours.",
        "objective": "BP 140/90, HR 95, EKG shows ST elevation.",
        "assessment": "Acute myocardial infarction",
        "plan": "Transfer to cath lab, aspirin, heparin, cardiology consult"
    }

    encounter_data = {
        "transcript": "Patient interview transcript",
        "triage_output": {"esi_level": 1},
        "physical_exam": "Exam findings",
        "radiology_output": {"findings": "ST elevation"}
    }

    confidence = agent._calculate_soap_confidence(soap_sections, encounter_data)

    assert confidence > 0.7  # Should be high with complete data


# ============================================================================
# Test 19: SOAP Confidence - Minimal Data
# ============================================================================
def test_soap_confidence_minimal():
    """Test SOAP confidence with minimal data."""
    api_key = os.getenv("ANTHROPIC_API_KEY", "test-key")
    agent = DocumentationAgent(anthropic_api_key=api_key)

    # Only one section populated
    soap_sections = {
        "subjective": "Patient reports headache",
        "objective": "",
        "assessment": "",
        "plan": ""
    }

    encounter_data = {}

    confidence = agent._calculate_soap_confidence(soap_sections, encounter_data)

    assert confidence < 0.5  # Should be low with minimal data


# ============================================================================
# Test 20: All Skills Return Draft Status
# ============================================================================
@pytest.mark.asyncio
@pytest.mark.skipif(not os.getenv("ANTHROPIC_API_KEY"), reason="ANTHROPIC_API_KEY not set")
async def test_all_skills_return_draft_status():
    """Test that all skills return draft_status='pending_review'."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    agent = DocumentationAgent(anthropic_api_key=api_key)

    # Test SOAP notes
    soap_result = await agent.execute_skill("soap_notes", {
        "patient_id": "PT-001",
        "encounter_data": {"chief_complaint": "Test"}
    })
    assert soap_result["draft_status"] == "pending_review"

    # Test ICD-10 coding
    icd10_result = await agent.execute_skill("icd10_coding", {
        "diagnosis_list": ["Diabetes"]
    })
    assert icd10_result["draft_status"] == "pending_review"

    # Test discharge summary
    discharge_result = await agent.execute_skill("discharge_summary", {
        "patient_id": "PT-002",
        "admission_date": "2025-02-01",
        "discharge_date": "2025-02-05",
        "hospital_course": "Test course"
    })
    assert discharge_result["draft_status"] == "pending_review"

    # Test referral letter
    referral_result = await agent.execute_skill("referral_letter", {
        "patient_id": "PT-003",
        "patient_name": "Test Patient",
        "referring_provider": "Dr. Test",
        "specialist_type": "Cardiology",
        "reason_for_referral": "Test reason",
        "relevant_history": "Test history"
    })
    assert referral_result["draft_status"] == "pending_review"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
