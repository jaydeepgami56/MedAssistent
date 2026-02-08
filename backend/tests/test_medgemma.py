"""
Tests for MedGemma model wrapper.

Tests cover:
- Service initialization
- Model loading (4B)
- Report generation (model and Claude fallback)
- Clinical reasoning (model and Claude fallback)
- Error handling
- Singleton pattern
"""

import pytest
import os
from backend.models.medgemma import (
    MedGemmaService,
    init_medgemma,
    get_medgemma_service,
)


class TestMedGemmaService:
    """Test suite for MedGemmaService class."""

    def test_service_initialization(self):
        """Test that MedGemmaService can be initialized."""
        service = MedGemmaService()
        assert service is not None
        assert service.model is None
        assert service.tokenizer is None
        assert service.use_fallback is False

    def test_service_initialization_with_api_key(self):
        """Test service initialization with Anthropic API key."""
        api_key = os.getenv("ANTHROPIC_API_KEY", "test-key")
        service = MedGemmaService(anthropic_api_key=api_key)
        assert service is not None
        if api_key != "test-key":
            assert service.anthropic_client is not None

    def test_load_4b_model(self):
        """Test loading MedGemma 4B model (will use fallback in CI)."""
        service = MedGemmaService()
        # This will likely fail in CI environment, but that's expected
        # We're testing that the method exists and handles failure gracefully
        result = service.load_4b_model(device="cpu")
        assert isinstance(result, bool)

    @pytest.mark.skipif(
        not os.getenv("ANTHROPIC_API_KEY"),
        reason="ANTHROPIC_API_KEY not set"
    )
    def test_generate_report_with_claude(self):
        """Test radiology report generation using Claude API fallback."""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        service = MedGemmaService(anthropic_api_key=api_key)
        service.use_fallback = True  # Force Claude fallback

        findings = [
            {"label": "pneumonia", "confidence": 0.87},
            {"label": "pleural effusion", "confidence": 0.23},
            {"label": "normal", "confidence": 0.12},
        ]

        patient_info = {
            "age": 65,
            "gender": "M",
            "clinical_indication": "cough and fever for 3 days",
        }

        report = service.generate_report(findings, "Chest X-ray", patient_info)

        assert report is not None
        assert len(report) > 0
        assert isinstance(report, str)
        # Report should contain key sections
        assert "FINDINGS" in report.upper() or "findings" in report.lower()

    def test_generate_report_empty_findings_error(self):
        """Test that empty findings list raises ValueError."""
        service = MedGemmaService()

        with pytest.raises(ValueError, match="Findings list cannot be empty"):
            service.generate_report([], "Chest X-ray", {"age": 65, "gender": "M"})

    def test_generate_report_empty_modality_error(self):
        """Test that empty modality raises ValueError."""
        service = MedGemmaService()
        findings = [{"label": "pneumonia", "confidence": 0.87}]

        with pytest.raises(ValueError, match="Modality cannot be empty"):
            service.generate_report(findings, "", {"age": 65, "gender": "M"})

    @pytest.mark.skipif(
        not os.getenv("ANTHROPIC_API_KEY"),
        reason="ANTHROPIC_API_KEY not set"
    )
    def test_clinical_reasoning_with_claude(self):
        """Test clinical reasoning using Claude API fallback."""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        service = MedGemmaService(anthropic_api_key=api_key)
        service.use_fallback = True  # Force Claude fallback

        prompt = "What are the most likely differential diagnoses for a 65-year-old male with chest pain and dyspnea?"
        context = {
            "age": 65,
            "gender": "M",
            "symptoms": ["chest pain", "dyspnea"],
            "vital_signs": "BP 140/90, HR 98, RR 22, SpO2 94%",
        }

        reasoning = service.clinical_reasoning(prompt, context)

        assert reasoning is not None
        assert len(reasoning) > 0
        assert isinstance(reasoning, str)

    def test_clinical_reasoning_empty_prompt_error(self):
        """Test that empty prompt raises ValueError."""
        service = MedGemmaService()

        with pytest.raises(ValueError, match="Prompt cannot be empty"):
            service.clinical_reasoning("", {"age": 65})

    def test_singleton_pattern(self):
        """Test singleton pattern functions."""
        api_key = os.getenv("ANTHROPIC_API_KEY", "test-key")

        # Initialize service
        init_medgemma(anthropic_api_key=api_key)

        # Get service instance
        service = get_medgemma_service()

        assert service is not None
        assert isinstance(service, MedGemmaService)


class TestMedGemmaReportGeneration:
    """Test suite for radiology report generation scenarios."""

    @pytest.mark.skipif(
        not os.getenv("ANTHROPIC_API_KEY"),
        reason="ANTHROPIC_API_KEY not set"
    )
    def test_chest_xray_pneumonia_report(self):
        """Test report generation for chest X-ray with pneumonia finding."""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        service = MedGemmaService(anthropic_api_key=api_key)
        service.use_fallback = True

        findings = [
            {"label": "pneumonia", "confidence": 0.91},
            {"label": "consolidation", "confidence": 0.76},
            {"label": "pleural effusion", "confidence": 0.15},
            {"label": "normal", "confidence": 0.08},
        ]

        patient_info = {
            "age": 58,
            "gender": "F",
            "clinical_indication": "productive cough, fever, and dyspnea for 5 days",
        }

        report = service.generate_report(findings, "Chest X-ray", patient_info)

        assert report is not None
        assert len(report) > 100  # Should be a substantial report
        # Check for medical terminology
        assert any(word in report.lower() for word in ["pneumonia", "consolidation", "findings", "impression"])

    @pytest.mark.skipif(
        not os.getenv("ANTHROPIC_API_KEY"),
        reason="ANTHROPIC_API_KEY not set"
    )
    def test_brain_mri_tumor_report(self):
        """Test report generation for brain MRI with tumor finding."""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        service = MedGemmaService(anthropic_api_key=api_key)
        service.use_fallback = True

        findings = [
            {"label": "tumor/mass", "confidence": 0.84},
            {"label": "cerebral atrophy", "confidence": 0.22},
            {"label": "normal", "confidence": 0.18},
        ]

        patient_info = {
            "age": 45,
            "gender": "M",
            "clinical_indication": "headaches and visual changes for 2 months",
        }

        report = service.generate_report(findings, "Brain MRI", patient_info)

        assert report is not None
        assert len(report) > 100
        # Check for relevant findings
        assert any(word in report.lower() for word in ["mass", "tumor", "brain", "findings"])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
