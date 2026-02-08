"""
Tests for Triage Agent - ESI scoring, red flag detection, and patient routing.
"""

import pytest
from backend.agents.triage_agent import TriageAgent, DISCLAIMER
from backend.models.clinical_bert import init_clinical_bert, get_clinical_bert_service
import os


# Fixtures
@pytest.fixture
def api_key():
    """Get Anthropic API key from environment."""
    return os.environ.get("ANTHROPIC_API_KEY")


@pytest.fixture
def triage_agent(api_key):
    """Create Triage Agent instance."""
    if not api_key:
        pytest.skip("ANTHROPIC_API_KEY not set")
    return TriageAgent(api_key)


@pytest.fixture
def clinical_bert_initialized(api_key):
    """Initialize ClinicalBERT service."""
    if not api_key:
        pytest.skip("ANTHROPIC_API_KEY not set")
    init_clinical_bert(api_key)
    return get_clinical_bert_service()


# Test 1: Agent initialization
def test_agent_initialization(triage_agent):
    """Test that Triage Agent initializes correctly."""
    assert triage_agent.agent_id == "triage"
    assert triage_agent.name == "Triage Agent"
    assert triage_agent.status == "Active"
    assert triage_agent.color == "#ef4444"
    assert triage_agent.icon == "🚨"
    assert "esi_scoring" in triage_agent.skills
    assert "red_flag_detection" in triage_agent.skills
    assert "patient_routing" in triage_agent.skills
    assert "emergency_alert" in triage_agent.skills
    assert "ClinicalBERT" in triage_agent.models_used
    assert "Claude API" in triage_agent.models_used


# Test 2: Get agent info
def test_get_info(triage_agent):
    """Test get_info returns correct metadata."""
    info = triage_agent.get_info()
    assert info["agent_id"] == "triage"
    assert info["name"] == "Triage Agent"
    assert len(info["skills"]) == 4
    assert len(info["models_used"]) == 2


# Test 3: Invalid skill execution
@pytest.mark.asyncio
async def test_invalid_skill(triage_agent):
    """Test that invalid skill raises ValueError."""
    with pytest.raises(ValueError, match="Unknown skill"):
        await triage_agent.execute_skill("invalid_skill", {})


# Test 4: Red flag detection - cardiac
def test_red_flag_detection_cardiac(triage_agent):
    """Test cardiac red flag detection."""
    red_flags = triage_agent._detect_red_flags(
        complaint="67yo M with crushing chest pain radiating to left arm",
        vitals={"hr": 110, "bp_sys": 90, "bp_dia": 60, "spo2": 94, "temp": 36.8, "rr": 22},
        entities={"symptoms": ["chest pain", "radiating pain"], "conditions": []},
        pain_scale=9
    )
    assert len(red_flags) > 0
    assert any("cardiac" in flag.lower() for flag in red_flags)
    assert any("spo2" in flag.lower() for flag in red_flags)
    assert any("severe pain" in flag.lower() for flag in red_flags)


# Test 5: Red flag detection - respiratory
def test_red_flag_detection_respiratory(triage_agent):
    """Test respiratory red flag detection."""
    red_flags = triage_agent._detect_red_flags(
        complaint="45yo F with severe shortness of breath",
        vitals={"hr": 120, "bp_sys": 140, "bp_dia": 85, "spo2": 85, "temp": 37.2, "rr": 28},
        entities={"symptoms": ["shortness of breath", "dyspnea"], "conditions": []},
        pain_scale=7
    )
    assert len(red_flags) > 0
    assert any("respiratory" in flag.lower() for flag in red_flags)
    assert any("spo2 < 90%" in flag.lower() for flag in red_flags)
    assert any("tachypnea" in flag.lower() for flag in red_flags)


# Test 6: Red flag detection - neurological
def test_red_flag_detection_neurological(triage_agent):
    """Test neurological red flag detection."""
    red_flags = triage_agent._detect_red_flags(
        complaint="72yo F with sudden weakness and slurred speech",
        vitals={"hr": 88, "bp_sys": 180, "bp_dia": 95, "spo2": 98, "temp": 36.9, "rr": 18, "gcs": 12},
        entities={"symptoms": ["weakness", "slurred speech"], "conditions": []},
        pain_scale=3
    )
    assert len(red_flags) > 0
    assert any("neurological" in flag.lower() for flag in red_flags)


# Test 7: No red flags - stable patient
def test_no_red_flags_stable(triage_agent):
    """Test stable patient with no red flags."""
    red_flags = triage_agent._detect_red_flags(
        complaint="28yo M with minor ankle sprain from playing basketball",
        vitals={"hr": 75, "bp_sys": 125, "bp_dia": 78, "spo2": 99, "temp": 37.0, "rr": 14},
        entities={"symptoms": ["ankle pain"], "conditions": []},
        pain_scale=4
    )
    # Should have no critical red flags (maybe minor pain but that's not life-threatening)
    critical_flags = [f for f in red_flags if any(kw in f.lower() for kw in ["cardiac", "respiratory", "neurological", "trauma"])]
    assert len(critical_flags) == 0


# Test 8: ESI scoring - critical case (ESI-1)
@pytest.mark.asyncio
async def test_esi_scoring_critical(triage_agent, clinical_bert_initialized):
    """Test ESI scoring for critical patient."""
    params = {
        "complaint": "67-year-old female with crushing chest pain radiating to left arm, onset 30 minutes ago",
        "vitals": {"hr": 110, "bp_sys": 90, "bp_dia": 60, "spo2": 94, "temp": 36.8, "rr": 22},
        "pain_scale": 9,
        "duration": "30 minutes",
        "history": "Hypertension, diabetes",
        "allergies": ["Penicillin"],
        "medications": ["Metformin", "Lisinopril"]
    }

    result = await triage_agent.execute_skill("esi_scoring", params)

    assert "esi_score" in result
    assert "esi_label" in result
    assert "red_flags" in result
    assert "routing" in result
    assert "wait_time" in result
    assert "reasoning" in result
    assert "confidence" in result
    assert "disclaimer" in result

    # Critical case should be ESI-1 or ESI-2
    assert result["esi_score"] <= 2
    assert len(result["red_flags"]) > 0
    assert result["disclaimer"] == DISCLAIMER


# Test 9: ESI scoring - urgent case (ESI-3)
@pytest.mark.asyncio
async def test_esi_scoring_urgent(triage_agent, clinical_bert_initialized):
    """Test ESI scoring for urgent patient."""
    params = {
        "complaint": "32-year-old male with fever and cough for 3 days",
        "vitals": {"hr": 95, "bp_sys": 130, "bp_dia": 80, "spo2": 96, "temp": 38.5, "rr": 18},
        "pain_scale": 3,
        "duration": "3 days",
        "history": "No significant history",
        "allergies": [],
        "medications": []
    }

    result = await triage_agent.execute_skill("esi_scoring", params)

    assert result["esi_score"] >= 2  # Should be ESI-2, 3, or 4
    assert result["esi_score"] <= 5
    assert result["disclaimer"] == DISCLAIMER


# Test 10: ESI scoring - non-urgent case (ESI-5)
@pytest.mark.asyncio
async def test_esi_scoring_non_urgent(triage_agent, clinical_bert_initialized):
    """Test ESI scoring for non-urgent patient."""
    params = {
        "complaint": "25-year-old female requesting prescription refill",
        "vitals": {"hr": 72, "bp_sys": 118, "bp_dia": 75, "spo2": 99, "temp": 36.6, "rr": 14},
        "pain_scale": 0,
        "duration": "N/A",
        "history": "No significant history",
        "allergies": [],
        "medications": ["Birth control"]
    }

    result = await triage_agent.execute_skill("esi_scoring", params)

    # Non-urgent case should be ESI-4 or ESI-5
    assert result["esi_score"] >= 4
    assert result["disclaimer"] == DISCLAIMER


# Test 11: Red flag detection skill
@pytest.mark.asyncio
async def test_red_flag_detection_skill(triage_agent, clinical_bert_initialized):
    """Test standalone red flag detection skill."""
    params = {
        "complaint": "Patient with chest pain and shortness of breath",
        "vitals": {"hr": 115, "bp_sys": 95, "bp_dia": 65, "spo2": 91, "temp": 37.0, "rr": 24},
        "pain_scale": 8
    }

    result = await triage_agent.execute_skill("red_flag_detection", params)

    assert "red_flags" in result
    assert "count" in result
    assert "requires_escalation" in result
    assert "disclaimer" in result
    assert result["count"] > 0
    assert result["requires_escalation"] is True


# Test 12: Patient routing skill
@pytest.mark.asyncio
async def test_patient_routing(triage_agent):
    """Test patient routing skill."""
    # ESI-1 routing
    result_esi1 = await triage_agent.execute_skill("patient_routing", {
        "esi_score": 1,
        "red_flags": ["Cardiac arrest"]
    })
    assert result_esi1["routing"] == "Resuscitation bay — IMMEDIATE"
    assert result_esi1["wait_time"] == "0 minutes"
    assert result_esi1["requires_immediate_attention"] is True

    # ESI-5 routing
    result_esi5 = await triage_agent.execute_skill("patient_routing", {
        "esi_score": 5,
        "red_flags": []
    })
    assert "Minor care" in result_esi5["routing"]
    assert result_esi5["requires_immediate_attention"] is False


# Test 13: Emergency alert skill
@pytest.mark.asyncio
async def test_emergency_alert(triage_agent):
    """Test emergency alert generation."""
    # Critical alert (ESI-1)
    result_critical = await triage_agent.execute_skill("emergency_alert", {
        "esi_score": 1,
        "complaint": "Cardiac arrest",
        "red_flags": ["Cardiac: cardiac arrest"]
    })
    assert result_critical["alert_level"] == "CRITICAL"
    assert result_critical["requires_notification"] is True
    assert "Attending Physician" in result_critical["notify_roles"]

    # Urgent alert (ESI-2)
    result_urgent = await triage_agent.execute_skill("emergency_alert", {
        "esi_score": 2,
        "complaint": "Chest pain with hypotension",
        "red_flags": ["Cardiac: chest pain"]
    })
    assert result_urgent["alert_level"] == "URGENT"
    assert result_urgent["requires_notification"] is True

    # No alert (ESI-4)
    result_no_alert = await triage_agent.execute_skill("emergency_alert", {
        "esi_score": 4,
        "complaint": "Minor cut",
        "red_flags": []
    })
    assert result_no_alert["alert_level"] == "NONE"
    assert result_no_alert["requires_notification"] is False


# Test 14: Chat method
@pytest.mark.asyncio
async def test_chat(triage_agent):
    """Test chat streaming."""
    message = "What is the Emergency Severity Index?"
    context = {"patient_id": "P12345"}

    response_text = ""
    async for token in triage_agent.chat(message, context):
        response_text += token

    assert len(response_text) > 0
    assert DISCLAIMER in response_text


# Test 15: Log audit
def test_log_audit(triage_agent, capsys):
    """Test audit logging."""
    triage_agent.log_audit(
        request="ESI scoring for chest pain patient",
        model="ClinicalBERT + Claude API",
        confidence=0.92,
        action="ESI-2 assigned"
    )

    captured = capsys.readouterr()
    assert "[AUDIT]" in captured.out
    assert "triage" in captured.out
    assert "0.920" in captured.out
    assert "ESI-2 assigned" in captured.out


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
