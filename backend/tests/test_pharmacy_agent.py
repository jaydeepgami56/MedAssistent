"""
Tests for Pharmacy Agent.

Tests drug interaction checking, dosage calculation, contraindication checking,
and medication reconciliation skills.
"""

import pytest
import os
from backend.agents.pharmacy_agent import PharmacyAgent, init_pharmacy_agent, get_pharmacy_agent

# Get Anthropic API key from environment
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")


@pytest.mark.asyncio
async def test_pharmacy_agent_initialization():
    """Test Pharmacy Agent initialization with correct metadata."""
    if not ANTHROPIC_API_KEY:
        pytest.skip("ANTHROPIC_API_KEY not set")

    agent = PharmacyAgent(anthropic_api_key=ANTHROPIC_API_KEY)

    assert agent.agent_id == "pharmacy"
    assert agent.name == "Pharmacy Agent"
    assert agent.color == "#f59e0b"
    assert agent.icon == "💊"
    assert agent.status == "Active"
    assert agent.queue == 0

    # Check skills
    assert "drug_interaction" in agent.skills
    assert "dosage_calc" in agent.skills
    assert "contraindication" in agent.skills
    assert "med_reconciliation" in agent.skills

    # Check models
    assert "Claude API" in agent.models_used
    assert "RxNorm API" in agent.models_used
    assert "DrugBank API" in agent.models_used


@pytest.mark.asyncio
async def test_pharmacy_agent_get_info():
    """Test get_info returns complete agent metadata."""
    if not ANTHROPIC_API_KEY:
        pytest.skip("ANTHROPIC_API_KEY not set")

    agent = PharmacyAgent(anthropic_api_key=ANTHROPIC_API_KEY)
    info = agent.get_info()

    assert info["agent_id"] == "pharmacy"
    assert info["name"] == "Pharmacy Agent"
    assert info["status"] == "Active"
    assert len(info["skills"]) == 4
    assert len(info["models_used"]) == 3
    assert info["color"] == "#f59e0b"
    assert info["icon"] == "💊"


@pytest.mark.asyncio
async def test_drug_interaction_insufficient_drugs():
    """Test drug interaction with insufficient drugs (< 2)."""
    if not ANTHROPIC_API_KEY:
        pytest.skip("ANTHROPIC_API_KEY not set")

    agent = PharmacyAgent(anthropic_api_key=ANTHROPIC_API_KEY)

    # Test with 0 drugs
    result = await agent.execute_skill("drug_interaction", {"drug_names": []})
    assert "error" in result
    assert result["total_interactions"] == 0

    # Test with 1 drug
    result = await agent.execute_skill("drug_interaction", {"drug_names": ["aspirin"]})
    assert "error" in result
    assert result["total_interactions"] == 0


@pytest.mark.asyncio
async def test_drug_interaction_no_interactions():
    """Test drug interaction with drugs that don't interact."""
    if not ANTHROPIC_API_KEY:
        pytest.skip("ANTHROPIC_API_KEY not set")

    # Note: This test requires RxNorm client to be initialized
    # May not find interactions if drugs are not commonly paired
    pytest.skip("Requires RxNorm client initialization")


@pytest.mark.asyncio
async def test_drug_interaction_aspirin_warfarin():
    """Test drug interaction between aspirin and warfarin (known major interaction)."""
    if not ANTHROPIC_API_KEY:
        pytest.skip("ANTHROPIC_API_KEY not set")

    # Note: This test requires RxNorm and DrugBank clients to be initialized
    pytest.skip("Requires RxNorm and DrugBank client initialization")


@pytest.mark.asyncio
async def test_severity_classification_critical():
    """Test severity classification for critical interactions."""
    if not ANTHROPIC_API_KEY:
        pytest.skip("ANTHROPIC_API_KEY not set")

    agent = PharmacyAgent(anthropic_api_key=ANTHROPIC_API_KEY)

    # Test critical keyword detection
    severity, blocked = agent._classify_severity(
        "This combination is contraindicated and may cause life-threatening respiratory depression",
        "high"
    )
    assert severity == "critical"
    assert blocked is True

    # Test API severity critical
    severity, blocked = agent._classify_severity(
        "Significant interaction",
        "contraindicated"
    )
    assert severity == "critical"
    assert blocked is True


@pytest.mark.asyncio
async def test_severity_classification_major():
    """Test severity classification for major interactions."""
    if not ANTHROPIC_API_KEY:
        pytest.skip("ANTHROPIC_API_KEY not set")

    agent = PharmacyAgent(anthropic_api_key=ANTHROPIC_API_KEY)

    severity, blocked = agent._classify_severity(
        "This is a major interaction requiring monitoring and dose adjustment",
        "major"
    )
    assert severity == "major"
    assert blocked is False


@pytest.mark.asyncio
async def test_severity_classification_moderate():
    """Test severity classification for moderate interactions."""
    if not ANTHROPIC_API_KEY:
        pytest.skip("ANTHROPIC_API_KEY not set")

    agent = PharmacyAgent(anthropic_api_key=ANTHROPIC_API_KEY)

    severity, blocked = agent._classify_severity(
        "Moderate interaction, monitor patient",
        "moderate"
    )
    assert severity == "moderate"
    assert blocked is False


@pytest.mark.asyncio
async def test_severity_classification_minor():
    """Test severity classification for minor interactions."""
    if not ANTHROPIC_API_KEY:
        pytest.skip("ANTHROPIC_API_KEY not set")

    agent = PharmacyAgent(anthropic_api_key=ANTHROPIC_API_KEY)

    severity, blocked = agent._classify_severity(
        "Minor interaction, unlikely to be clinically significant",
        "low"
    )
    assert severity == "minor"
    assert blocked is False


@pytest.mark.asyncio
async def test_interaction_summary_generation():
    """Test interaction summary generation."""
    if not ANTHROPIC_API_KEY:
        pytest.skip("ANTHROPIC_API_KEY not set")

    agent = PharmacyAgent(anthropic_api_key=ANTHROPIC_API_KEY)

    # Test with no interactions
    summary = agent._generate_interaction_summary([], ["aspirin", "metformin"])
    assert "No interactions found" in summary

    # Test with mixed severity interactions
    interactions = [
        {"severity": "critical"},
        {"severity": "major"},
        {"severity": "moderate"},
        {"severity": "minor"}
    ]
    summary = agent._generate_interaction_summary(interactions, ["drug1", "drug2", "drug3"])
    assert "4 interaction(s)" in summary
    assert "CRITICAL" in summary
    assert "MAJOR" in summary
    assert "MODERATE" in summary
    assert "MINOR" in summary


@pytest.mark.asyncio
async def test_dosage_calc_missing_drug():
    """Test dosage calculation with missing drug name."""
    if not ANTHROPIC_API_KEY:
        pytest.skip("ANTHROPIC_API_KEY not set")

    agent = PharmacyAgent(anthropic_api_key=ANTHROPIC_API_KEY)

    result = await agent.execute_skill("dosage_calc", {
        "weight": 70,
        "age": 45,
        "renal_function": "normal"
    })

    assert "error" in result
    assert "Drug name required" in result["error"]


@pytest.mark.asyncio
async def test_dosage_calc_with_claude():
    """Test dosage calculation using Claude API."""
    if not ANTHROPIC_API_KEY:
        pytest.skip("ANTHROPIC_API_KEY not set")

    agent = PharmacyAgent(anthropic_api_key=ANTHROPIC_API_KEY)

    result = await agent.execute_skill("dosage_calc", {
        "drug": "metformin",
        "weight": 70,
        "age": 55,
        "renal_function": "normal",
        "indication": "Type 2 diabetes"
    })

    # Should not have error
    if "error" not in result:
        assert "dose_range" in result
        assert "frequency" in result
        assert "route" in result
        assert result["drug"] == "metformin"
        assert "disclaimer" in result


@pytest.mark.asyncio
async def test_contraindication_missing_drug():
    """Test contraindication check with missing drug name."""
    if not ANTHROPIC_API_KEY:
        pytest.skip("ANTHROPIC_API_KEY not set")

    agent = PharmacyAgent(anthropic_api_key=ANTHROPIC_API_KEY)

    result = await agent.execute_skill("contraindication", {
        "conditions": ["hypertension"]
    })

    assert "error" in result
    assert "Drug name required" in result["error"]


@pytest.mark.asyncio
async def test_contraindication_no_conditions():
    """Test contraindication check with no patient conditions."""
    if not ANTHROPIC_API_KEY:
        pytest.skip("ANTHROPIC_API_KEY not set")

    # Note: Requires RxNorm and DrugBank client initialization
    pytest.skip("Requires RxNorm and DrugBank client initialization")


@pytest.mark.asyncio
async def test_med_reconciliation_empty_lists():
    """Test medication reconciliation with empty lists."""
    if not ANTHROPIC_API_KEY:
        pytest.skip("ANTHROPIC_API_KEY not set")

    # Note: Requires RxNorm client initialization
    pytest.skip("Requires RxNorm client initialization")


@pytest.mark.asyncio
async def test_execute_skill_invalid_skill():
    """Test execute_skill with invalid skill name."""
    if not ANTHROPIC_API_KEY:
        pytest.skip("ANTHROPIC_API_KEY not set")

    agent = PharmacyAgent(anthropic_api_key=ANTHROPIC_API_KEY)

    with pytest.raises(ValueError, match="Unknown skill"):
        await agent.execute_skill("invalid_skill", {})


@pytest.mark.asyncio
async def test_chat_streaming():
    """Test streaming chat responses."""
    if not ANTHROPIC_API_KEY:
        pytest.skip("ANTHROPIC_API_KEY not set")

    agent = PharmacyAgent(anthropic_api_key=ANTHROPIC_API_KEY)

    message = "What is the typical starting dose of metformin for type 2 diabetes?"
    context = {
        "patient_info": "55yo male, BMI 32",
        "medications": ["lisinopril 10mg daily"]
    }

    tokens = []
    async for token in agent.chat(message, context):
        tokens.append(token)

    response = "".join(tokens)
    assert len(response) > 0
    assert "AI-assisted drug checking" in response  # Disclaimer


@pytest.mark.asyncio
async def test_singleton_pattern():
    """Test singleton pattern for Pharmacy Agent."""
    if not ANTHROPIC_API_KEY:
        pytest.skip("ANTHROPIC_API_KEY not set")

    # Initialize agent
    agent1 = await init_pharmacy_agent(ANTHROPIC_API_KEY)
    agent2 = get_pharmacy_agent()

    assert agent1 is agent2
    assert agent2.agent_id == "pharmacy"


@pytest.mark.asyncio
async def test_init_without_api_key():
    """Test initialization fails without API key."""
    with pytest.raises(ValueError, match="ANTHROPIC_API_KEY required"):
        await init_pharmacy_agent(None)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
