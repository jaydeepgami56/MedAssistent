"""
Test suite for Radiology Agent.

Comprehensive tests covering initialization, metadata, skill execution,
image analysis pipeline, KNN evidence search, report generation, and chat.
"""

import pytest
import os
from PIL import Image
import numpy as np

from backend.agents.radiology_agent import (
    RadiologyAgent,
    init_radiology_agent,
    get_radiology_agent,
    DISCLAIMER
)


def create_mock_image(size=(512, 512)) -> Image.Image:
    """
    Create a mock medical image for testing.

    Args:
        size: Image dimensions (width, height)

    Returns:
        PIL.Image: Mock grayscale medical image
    """
    # Create random grayscale image
    array = np.random.randint(0, 256, size=size, dtype=np.uint8)
    return Image.fromarray(array, mode='L')


class TestRadiologyAgentInitialization:
    """Test Radiology Agent initialization and metadata."""

    def test_agent_initialization(self):
        """Test that agent initializes with correct properties."""
        api_key = os.environ.get("ANTHROPIC_API_KEY", "test-key")
        agent = RadiologyAgent(anthropic_api_key=api_key)

        assert agent.agent_id == "radiology"
        assert agent.name == "Radiology Agent"
        assert agent.icon == "🩻"
        assert agent.color == "#00b4d8"
        assert agent.status == "Active"
        assert agent.queue == 0

    def test_agent_skills(self):
        """Test that agent has all required skills."""
        api_key = os.environ.get("ANTHROPIC_API_KEY", "test-key")
        agent = RadiologyAgent(anthropic_api_key=api_key)

        expected_skills = [
            "xray_analysis",
            "mri_interpretation",
            "ct_review",
            "report_gen",
            "evidence_search"
        ]
        assert agent.skills == expected_skills

    def test_agent_models_used(self):
        """Test that agent declares correct models."""
        api_key = os.environ.get("ANTHROPIC_API_KEY", "test-key")
        agent = RadiologyAgent(anthropic_api_key=api_key)

        assert "MedImageInsight" in agent.models_used
        assert "MedGemma 4B" in agent.models_used
        assert "Qdrant" in agent.models_used

    def test_get_info(self):
        """Test that get_info returns correct metadata."""
        api_key = os.environ.get("ANTHROPIC_API_KEY", "test-key")
        agent = RadiologyAgent(anthropic_api_key=api_key)

        info = agent.get_info()
        assert info["agent_id"] == "radiology"
        assert info["name"] == "Radiology Agent"
        assert len(info["skills"]) == 5
        assert len(info["models_used"]) == 3


class TestRadiologyAgentSkills:
    """Test Radiology Agent skill execution."""

    @pytest.mark.asyncio
    async def test_xray_analysis_with_mock_image(self):
        """Test X-ray analysis with mock image."""
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            pytest.skip("ANTHROPIC_API_KEY not set")

        agent = RadiologyAgent(anthropic_api_key=api_key)

        # Create mock image
        mock_image = create_mock_image()

        params = {
            "image": mock_image,
            "patient_info": {
                "name": "John Doe",
                "age": 45,
                "gender": "Male"
            },
            "clinical_indication": "Chest pain evaluation",
            "image_id": "test-xray-001"
        }

        result = await agent.execute_skill("xray_analysis", params)

        # Verify result structure
        assert "findings" in result
        assert "similar_cases" in result
        assert "recommendation" in result
        assert "overall_confidence" in result
        assert "requires_review" in result
        assert "report_narrative" in result
        assert "modality" in result
        assert "disclaimer" in result

        # Verify findings structure
        assert isinstance(result["findings"], list)
        if result["findings"]:
            finding = result["findings"][0]
            assert "text" in finding
            assert "confidence" in finding
            assert "severity" in finding

        # Verify disclaimer
        assert result["disclaimer"] == DISCLAIMER

        # Verify modality
        assert result["modality"] == "Chest X-Ray"

    @pytest.mark.asyncio
    async def test_mri_interpretation(self):
        """Test Brain MRI interpretation."""
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            pytest.skip("ANTHROPIC_API_KEY not set")

        agent = RadiologyAgent(anthropic_api_key=api_key)
        mock_image = create_mock_image()

        params = {
            "image": mock_image,
            "patient_info": {
                "name": "Jane Smith",
                "age": 62,
                "gender": "Female"
            },
            "clinical_indication": "Headache and vision changes",
            "image_id": "test-mri-001"
        }

        result = await agent.execute_skill("mri_interpretation", params)

        assert result["modality"] == "Brain MRI"
        assert "findings" in result
        assert "report_narrative" in result
        assert result["disclaimer"] == DISCLAIMER

    @pytest.mark.asyncio
    async def test_ct_review(self):
        """Test Chest CT review."""
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            pytest.skip("ANTHROPIC_API_KEY not set")

        agent = RadiologyAgent(anthropic_api_key=api_key)
        mock_image = create_mock_image()

        params = {
            "image": mock_image,
            "patient_info": {
                "name": "Bob Johnson",
                "age": 58,
                "gender": "Male"
            },
            "clinical_indication": "Suspected pulmonary embolism",
            "image_id": "test-ct-001"
        }

        result = await agent.execute_skill("ct_review", params)

        assert result["modality"] == "Chest CT"
        assert "findings" in result
        assert "report_narrative" in result
        assert result["disclaimer"] == DISCLAIMER

    @pytest.mark.asyncio
    async def test_report_gen(self):
        """Test standalone report generation."""
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            pytest.skip("ANTHROPIC_API_KEY not set")

        agent = RadiologyAgent(anthropic_api_key=api_key)

        findings = [
            {"text": "pneumonia", "confidence": 0.85, "severity": "high"},
            {"text": "pleural effusion", "confidence": 0.72, "severity": "moderate"}
        ]

        params = {
            "findings": findings,
            "modality": "Chest X-Ray",
            "patient_info": {
                "name": "Test Patient",
                "age": 50,
                "gender": "Male"
            }
        }

        result = await agent.execute_skill("report_gen", params)

        assert "report_narrative" in result
        assert result["modality"] == "Chest X-Ray"
        assert result["disclaimer"] == DISCLAIMER
        assert isinstance(result["report_narrative"], str)
        assert len(result["report_narrative"]) > 0

    @pytest.mark.asyncio
    async def test_invalid_skill_name(self):
        """Test that invalid skill name raises ValueError."""
        api_key = os.environ.get("ANTHROPIC_API_KEY", "test-key")
        agent = RadiologyAgent(anthropic_api_key=api_key)

        with pytest.raises(ValueError, match="Unknown skill"):
            await agent.execute_skill("invalid_skill", {})


class TestRadiologyAgentSafetyChecks:
    """Test safety checks and confidence thresholds."""

    @pytest.mark.asyncio
    async def test_low_confidence_flagged_for_review(self):
        """Test that low confidence findings are flagged for mandatory review."""
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            pytest.skip("ANTHROPIC_API_KEY not set")

        agent = RadiologyAgent(anthropic_api_key=api_key)
        mock_image = create_mock_image()

        params = {
            "image": mock_image,
            "patient_info": {"name": "Test", "age": 30, "gender": "Male"}
        }

        result = await agent.execute_skill("xray_analysis", params)

        # Check if requires_review flag is present
        assert "requires_review" in result
        assert isinstance(result["requires_review"], bool)

        # If overall confidence < 0.7, should require review
        if result["overall_confidence"] < 0.7:
            assert result["requires_review"] is True
            assert "MANDATORY HUMAN REVIEW" in result["recommendation"]

    def test_generate_findings_severity_classification(self):
        """Test that findings are correctly classified by severity."""
        api_key = os.environ.get("ANTHROPIC_API_KEY", "test-key")
        agent = RadiologyAgent(anthropic_api_key=api_key)

        # Mock classifications
        classifications = [
            {"label": "normal", "confidence": 0.95},
            {"label": "pneumonia", "confidence": 0.85},
            {"label": "cardiomegaly", "confidence": 0.65},
            {"label": "atelectasis", "confidence": 0.45}
        ]

        findings = agent._generate_findings(classifications)

        # Check normal is classified correctly
        assert findings[0]["severity"] == "normal"
        assert findings[0]["text"] == "normal"

        # Check high severity (pneumonia with confidence > 0.7)
        assert findings[1]["severity"] == "high"
        assert findings[1]["text"] == "pneumonia"

        # Check moderate severity (cardiomegaly with confidence 0.5-0.7)
        assert findings[2]["severity"] == "moderate"

        # Check normal severity (low confidence)
        assert findings[3]["severity"] == "normal"


class TestRadiologyAgentChat:
    """Test Radiology Agent chat functionality."""

    @pytest.mark.asyncio
    async def test_chat_streaming(self):
        """Test that chat returns streaming responses."""
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            pytest.skip("ANTHROPIC_API_KEY not set")

        agent = RadiologyAgent(anthropic_api_key=api_key)

        context = {
            "patient_id": "12345",
            "recent_imaging": "Chest X-Ray showing pneumonia"
        }

        message = "What are the typical findings of pneumonia on chest X-ray?"

        # Collect streaming tokens
        tokens = []
        async for token in agent.chat(message, context):
            tokens.append(token)

        response = "".join(tokens)

        # Verify response
        assert len(response) > 0
        assert DISCLAIMER in response

    @pytest.mark.asyncio
    async def test_chat_includes_disclaimer(self):
        """Test that chat always includes disclaimer."""
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            pytest.skip("ANTHROPIC_API_KEY not set")

        agent = RadiologyAgent(anthropic_api_key=api_key)

        tokens = []
        async for token in agent.chat("Explain chest X-ray findings", {}):
            tokens.append(token)

        response = "".join(tokens)
        assert DISCLAIMER in response


class TestRadiologyAgentSingleton:
    """Test global singleton pattern."""

    def test_init_radiology_agent(self):
        """Test global agent initialization."""
        api_key = os.environ.get("ANTHROPIC_API_KEY", "test-key")
        init_radiology_agent(api_key)

        agent = get_radiology_agent()
        assert agent is not None
        assert isinstance(agent, RadiologyAgent)
        assert agent.agent_id == "radiology"

    def test_get_radiology_agent_before_init(self):
        """Test that get_radiology_agent returns None before initialization."""
        # Reset global agent
        import backend.agents.radiology_agent as radiology_module
        radiology_module._radiology_agent = None

        agent = get_radiology_agent()
        assert agent is None


class TestRadiologyAgentEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_xray_analysis_missing_image(self):
        """Test that missing image raises ValueError."""
        api_key = os.environ.get("ANTHROPIC_API_KEY", "test-key")
        agent = RadiologyAgent(anthropic_api_key=api_key)

        params = {
            "patient_info": {"name": "Test", "age": 30, "gender": "Male"}
        }

        with pytest.raises(ValueError, match="image parameter is required"):
            await agent.execute_skill("xray_analysis", params)

    @pytest.mark.asyncio
    async def test_report_gen_missing_findings(self):
        """Test that missing findings raises ValueError."""
        api_key = os.environ.get("ANTHROPIC_API_KEY", "test-key")
        agent = RadiologyAgent(anthropic_api_key=api_key)

        params = {
            "modality": "Chest X-Ray",
            "patient_info": {"name": "Test", "age": 30, "gender": "Male"}
        }

        with pytest.raises(ValueError, match="findings parameter is required"):
            await agent.execute_skill("report_gen", params)

    @pytest.mark.asyncio
    async def test_xray_analysis_with_bytes_image(self):
        """Test X-ray analysis with image as bytes."""
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            pytest.skip("ANTHROPIC_API_KEY not set")

        agent = RadiologyAgent(anthropic_api_key=api_key)

        # Create mock image and convert to bytes
        mock_image = create_mock_image()
        from io import BytesIO
        buffer = BytesIO()
        mock_image.save(buffer, format='PNG')
        image_bytes = buffer.getvalue()

        params = {
            "image": image_bytes,
            "patient_info": {"name": "Test", "age": 30, "gender": "Male"}
        }

        result = await agent.execute_skill("xray_analysis", params)

        # Should successfully process bytes image
        assert "findings" in result
        assert result["disclaimer"] == DISCLAIMER


# Run tests with: pytest backend/tests/test_radiology_agent.py -v
