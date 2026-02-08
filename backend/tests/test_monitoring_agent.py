"""
Test suite for Monitoring Agent - MEWS scoring, vital tracking, anomaly detection, alerts.
"""

import pytest
import os
from backend.agents.monitoring_agent import MonitoringAgent, init_monitoring_agent, get_monitoring_agent


# ============================================================================
# Test 1: Agent Initialization
# ============================================================================
def test_monitoring_agent_initialization():
    """Test that Monitoring Agent initializes with correct metadata."""
    api_key = os.getenv("ANTHROPIC_API_KEY", "test-key")
    agent = MonitoringAgent(anthropic_api_key=api_key)

    assert agent.agent_id == "monitoring"
    assert agent.name == "Monitoring Agent"
    assert agent.status == "Active"
    assert agent.color == "#a855f7"
    assert agent.icon == "📊"
    assert "vital_tracking" in agent.skills
    assert "mews_score" in agent.skills
    assert "anomaly_detection" in agent.skills
    assert "alert_gen" in agent.skills
    assert "Time-series ML" in agent.models_used
    assert "Claude API" in agent.models_used


# ============================================================================
# Test 2: get_info() Method
# ============================================================================
def test_get_info():
    """Test that get_info() returns correct metadata dict."""
    api_key = os.getenv("ANTHROPIC_API_KEY", "test-key")
    agent = MonitoringAgent(anthropic_api_key=api_key)

    info = agent.get_info()

    assert info["agent_id"] == "monitoring"
    assert info["name"] == "Monitoring Agent"
    assert len(info["skills"]) == 4
    assert len(info["models_used"]) == 2


# ============================================================================
# Test 3: MEWS Calculation - Normal Vitals (MEWS 0)
# ============================================================================
@pytest.mark.asyncio
async def test_mews_score_normal_vitals():
    """Test MEWS calculation for normal vitals."""
    api_key = os.getenv("ANTHROPIC_API_KEY", "test-key")
    agent = MonitoringAgent(anthropic_api_key=api_key)

    params = {
        "hr": 75,
        "bp_sys": 120,
        "spo2": 98,
        "temp": 37.0,
        "rr": 14
    }

    result = await agent.execute_skill("mews_score", params)

    assert result["mews_total"] == 0
    assert result["alert_level"] == "Normal"
    assert result["component_scores"]["hr_score"] == 0
    assert result["component_scores"]["bp_score"] == 0
    assert result["component_scores"]["rr_score"] == 0
    assert result["component_scores"]["temp_score"] == 0
    assert result["spo2_alert"] is False
    assert "AI-assisted vital sign monitoring" in result["disclaimer"]


# ============================================================================
# Test 4: MEWS Calculation - Critical Vitals (MEWS 6+)
# ============================================================================
@pytest.mark.asyncio
async def test_mews_score_critical_vitals():
    """Test MEWS calculation for critical vitals."""
    api_key = os.getenv("ANTHROPIC_API_KEY", "test-key")
    agent = MonitoringAgent(anthropic_api_key=api_key)

    params = {
        "hr": 125,       # 111-130 = 2 points
        "bp_sys": 85,    # 81-100 = 1 point
        "spo2": 91,      # No MEWS points, but < 92% warning
        "temp": 38.7,    # > 38.5 = 2 points
        "rr": 24         # 21-29 = 2 points
    }

    result = await agent.execute_skill("mews_score", params)

    assert result["mews_total"] == 7  # 2+1+2+2 = 7
    assert result["alert_level"] == "Critical"
    assert result["component_scores"]["hr_score"] == 2
    assert result["component_scores"]["bp_score"] == 1
    assert result["component_scores"]["rr_score"] == 2
    assert result["component_scores"]["temp_score"] == 2
    assert "CRITICAL" in result["recommendations"]
    assert "Attending physician" in result["recommendations"]


# ============================================================================
# Test 5: MEWS Calculation - Increased Concern (MEWS 3-4)
# ============================================================================
@pytest.mark.asyncio
async def test_mews_score_increased_concern():
    """Test MEWS calculation for increased concern level."""
    api_key = os.getenv("ANTHROPIC_API_KEY", "test-key")
    agent = MonitoringAgent(anthropic_api_key=api_key)

    params = {
        "hr": 105,       # 101-110 = 1 point
        "bp_sys": 95,    # 81-100 = 1 point
        "spo2": 95,
        "temp": 37.5,    # Normal = 0 points
        "rr": 18         # 15-20 = 1 point
    }

    result = await agent.execute_skill("mews_score", params)

    assert result["mews_total"] == 3  # 1+1+1 = 3
    assert result["alert_level"] == "Increased concern"
    assert "INCREASED CONCERN" in result["recommendations"]
    assert "Notify nurse" in result["recommendations"]


# ============================================================================
# Test 6: SpO2 Alert (< 90%)
# ============================================================================
@pytest.mark.asyncio
async def test_spo2_critical_alert():
    """Test that SpO2 < 90% triggers critical alert."""
    api_key = os.getenv("ANTHROPIC_API_KEY", "test-key")
    agent = MonitoringAgent(anthropic_api_key=api_key)

    params = {
        "hr": 80,
        "bp_sys": 120,
        "spo2": 88,      # < 90% = critical alert
        "temp": 37.0,
        "rr": 16
    }

    result = await agent.execute_skill("mews_score", params)

    assert result["spo2_alert"] is True
    assert "CRITICAL: SpO2 < 90%" in result["recommendations"]
    assert "supplemental oxygen" in result["recommendations"]


# ============================================================================
# Test 7: HR Score Calculation (Tachycardia)
# ============================================================================
@pytest.mark.asyncio
async def test_hr_score_tachycardia():
    """Test HR score calculation for tachycardia."""
    api_key = os.getenv("ANTHROPIC_API_KEY", "test-key")
    agent = MonitoringAgent(anthropic_api_key=api_key)

    params = {
        "hr": 135,       # > 130 = 3 points
        "bp_sys": 120,
        "spo2": 98,
        "temp": 37.0,
        "rr": 16
    }

    result = await agent.execute_skill("mews_score", params)

    assert result["component_scores"]["hr_score"] == 3
    assert "Severe tachycardia" in result["details"]


# ============================================================================
# Test 8: BP Score Calculation (Hypotension)
# ============================================================================
@pytest.mark.asyncio
async def test_bp_score_hypotension():
    """Test BP score calculation for hypotension."""
    api_key = os.getenv("ANTHROPIC_API_KEY", "test-key")
    agent = MonitoringAgent(anthropic_api_key=api_key)

    params = {
        "hr": 80,
        "bp_sys": 65,    # < 70 = 3 points
        "spo2": 98,
        "temp": 37.0,
        "rr": 16
    }

    result = await agent.execute_skill("mews_score", params)

    assert result["component_scores"]["bp_score"] == 3
    assert "Severe hypotension" in result["details"]


# ============================================================================
# Test 9: Vital Tracking - Store Reading
# ============================================================================
@pytest.mark.asyncio
async def test_vital_tracking_store():
    """Test vital tracking stores reading correctly."""
    api_key = os.getenv("ANTHROPIC_API_KEY", "test-key")
    agent = MonitoringAgent(anthropic_api_key=api_key)

    params = {
        "patient_id": "PT-12345",
        "hr": 80,
        "bp_sys": 120,
        "bp_dia": 80,
        "spo2": 98,
        "temp": 37.0,
        "rr": 12  # Changed from 16 to 12 (9-14 range = 0 points)
    }

    result = await agent.execute_skill("vital_tracking", params)

    assert result["stored"] is True
    assert result["history_count"] == 1
    assert result["window"] == "6 hours"
    assert result["reading"]["hr"] == 80
    assert result["mews_score"] == 0


# ============================================================================
# Test 10: Vital Tracking - Trend Analysis (Insufficient Data)
# ============================================================================
@pytest.mark.asyncio
async def test_vital_tracking_trend_insufficient_data():
    """Test trend analysis with insufficient data."""
    api_key = os.getenv("ANTHROPIC_API_KEY", "test-key")
    agent = MonitoringAgent(anthropic_api_key=api_key)

    # Store one reading
    params = {
        "patient_id": "PT-TREND-1",
        "hr": 80,
        "bp_sys": 120,
        "bp_dia": 80,
        "spo2": 98,
        "temp": 37.0,
        "rr": 16
    }

    result = await agent.execute_skill("vital_tracking", params)

    assert result["trend_analysis"]["trend"] == "insufficient_data"


# ============================================================================
# Test 11: Vital Tracking - Deteriorating Trend
# ============================================================================
@pytest.mark.asyncio
async def test_vital_tracking_deteriorating_trend():
    """Test trend analysis for deteriorating patient."""
    api_key = os.getenv("ANTHROPIC_API_KEY", "test-key")
    agent = MonitoringAgent(anthropic_api_key=api_key)

    patient_id = "PT-TREND-2"

    # Store 3 readings with worsening MEWS
    for hr in [80, 110, 130]:
        params = {
            "patient_id": patient_id,
            "hr": hr,
            "bp_sys": 120,
            "bp_dia": 80,
            "spo2": 98,
            "temp": 37.0,
            "rr": 16
        }
        result = await agent.execute_skill("vital_tracking", params)

    assert result["trend_analysis"]["trend"] == "deteriorating"


# ============================================================================
# Test 12: Anomaly Detection - Insufficient Baseline
# ============================================================================
@pytest.mark.asyncio
async def test_anomaly_detection_insufficient_baseline():
    """Test anomaly detection with insufficient baseline data."""
    api_key = os.getenv("ANTHROPIC_API_KEY", "test-key")
    agent = MonitoringAgent(anthropic_api_key=api_key)

    params = {
        "patient_id": "PT-ANOMALY-1",
        "hr": 80,
        "bp_sys": 120,
        "spo2": 98,
        "temp": 37.0,
        "rr": 16
    }

    result = await agent.execute_skill("anomaly_detection", params)

    assert result["anomalies_detected"] is False
    assert "Insufficient baseline data" in result["message"]


# ============================================================================
# Test 13: Anomaly Detection - Sudden HR Change
# ============================================================================
@pytest.mark.asyncio
async def test_anomaly_detection_hr_change():
    """Test anomaly detection for sudden HR change."""
    api_key = os.getenv("ANTHROPIC_API_KEY", "test-key")
    agent = MonitoringAgent(anthropic_api_key=api_key)

    patient_id = "PT-ANOMALY-2"

    # Establish baseline (3 normal readings)
    for _ in range(3):
        params = {
            "patient_id": patient_id,
            "hr": 75,
            "bp_sys": 120,
            "bp_dia": 80,
            "spo2": 98,
            "temp": 37.0,
            "rr": 16
        }
        await agent.execute_skill("vital_tracking", params)

    # Sudden HR spike
    params = {
        "patient_id": patient_id,
        "hr": 130,  # Sudden change from 75
        "bp_sys": 120,
        "spo2": 98,
        "temp": 37.0,
        "rr": 16
    }

    result = await agent.execute_skill("anomaly_detection", params)

    assert result["anomalies_detected"] is True
    assert len(result["anomalies"]) > 0
    assert any("HR" in anomaly for anomaly in result["anomalies"])


# ============================================================================
# Test 14: Alert Generation - MEWS Critical
# ============================================================================
@pytest.mark.asyncio
async def test_alert_gen_mews_critical():
    """Test alert generation for MEWS >= 5."""
    api_key = os.getenv("ANTHROPIC_API_KEY", "test-key")
    agent = MonitoringAgent(anthropic_api_key=api_key)

    params = {
        "patient_id": "PT-ALERT-1",
        "mews_total": 6,
        "spo2": 95
    }

    result = await agent.execute_skill("alert_gen", params)

    assert result["alert_level"] == "CRITICAL"
    assert result["requires_notification"] is True
    assert "Attending Physician" in result["notify_roles"]
    assert "Rapid Response Team" in result["notify_roles"]
    assert any(alert["type"] == "MEWS_CRITICAL" for alert in result["alerts"])


# ============================================================================
# Test 15: Alert Generation - SpO2 Critical
# ============================================================================
@pytest.mark.asyncio
async def test_alert_gen_spo2_critical():
    """Test alert generation for SpO2 < 90%."""
    api_key = os.getenv("ANTHROPIC_API_KEY", "test-key")
    agent = MonitoringAgent(anthropic_api_key=api_key)

    params = {
        "patient_id": "PT-ALERT-2",
        "mews_total": 2,  # Normal MEWS
        "spo2": 87        # But critical SpO2
    }

    result = await agent.execute_skill("alert_gen", params)

    assert result["alert_level"] == "CRITICAL"
    assert result["requires_notification"] is True
    assert "Respiratory Therapy" in result["notify_roles"]
    assert any(alert["type"] == "SPO2_CRITICAL" for alert in result["alerts"])


# ============================================================================
# Test 16: Execute Skill - Invalid Skill
# ============================================================================
@pytest.mark.asyncio
async def test_execute_skill_invalid():
    """Test that execute_skill raises ValueError for invalid skill."""
    api_key = os.getenv("ANTHROPIC_API_KEY", "test-key")
    agent = MonitoringAgent(anthropic_api_key=api_key)

    with pytest.raises(ValueError, match="Unknown skill"):
        await agent.execute_skill("invalid_skill", {})


# ============================================================================
# Test 17: Singleton Pattern
# ============================================================================
def test_singleton_pattern():
    """Test that init_monitoring_agent and get_monitoring_agent work correctly."""
    api_key = os.getenv("ANTHROPIC_API_KEY", "test-key")

    init_monitoring_agent(anthropic_api_key=api_key)
    agent = get_monitoring_agent()

    assert agent is not None
    assert agent.agent_id == "monitoring"


# ============================================================================
# Test 18: Chat Method (Skipped if no API key)
# ============================================================================
@pytest.mark.asyncio
@pytest.mark.skipif(not os.getenv("ANTHROPIC_API_KEY"), reason="ANTHROPIC_API_KEY not set")
async def test_chat_streaming():
    """Test chat method returns streaming response."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    agent = MonitoringAgent(anthropic_api_key=api_key)

    message = "What does a MEWS score of 5 mean?"
    context = {"patient_id": "PT-001"}

    chunks = []
    async for chunk in agent.chat(message, context):
        chunks.append(chunk)

    response = "".join(chunks)
    assert len(response) > 0
    assert "AI-assisted vital sign monitoring" in response


# ============================================================================
# Test 19: MEWS Edge Cases - All Zero Scores
# ============================================================================
@pytest.mark.asyncio
async def test_mews_edge_case_all_zero():
    """Test MEWS calculation with all zero-score vitals."""
    api_key = os.getenv("ANTHROPIC_API_KEY", "test-key")
    agent = MonitoringAgent(anthropic_api_key=api_key)

    params = {
        "hr": 75,        # 0 points
        "bp_sys": 120,   # 0 points
        "spo2": 98,
        "temp": 37.0,    # 0 points
        "rr": 12         # 0 points
    }

    result = await agent.execute_skill("mews_score", params)

    assert result["mews_total"] == 0
    assert result["alert_level"] == "Normal"
    assert "routine monitoring" in result["recommendations"].lower()


# ============================================================================
# Test 20: MEWS Edge Cases - Bradycardia
# ============================================================================
@pytest.mark.asyncio
async def test_mews_bradycardia():
    """Test MEWS calculation for bradycardia."""
    api_key = os.getenv("ANTHROPIC_API_KEY", "test-key")
    agent = MonitoringAgent(anthropic_api_key=api_key)

    params = {
        "hr": 35,        # < 40 = 3 points
        "bp_sys": 120,
        "spo2": 98,
        "temp": 37.0,
        "rr": 14
    }

    result = await agent.execute_skill("mews_score", params)

    assert result["component_scores"]["hr_score"] == 3
    assert "bradycardia" in result["details"].lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
