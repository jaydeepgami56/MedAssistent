"""
Test suite for ClinicalBERT NER service.

Tests both model-based and Claude API fallback entity extraction.
"""

import pytest
from backend.models.clinical_bert import ClinicalBERTService


@pytest.fixture
def sample_clinical_text():
    """Sample clinical text for testing."""
    return (
        "Patient presents with chest pain radiating to left arm, "
        "shortness of breath, and diaphoresis since 3 hours ago. "
        "History of hypertension and diabetes mellitus type 2. "
        "Currently on metformin 1000mg BID and lisinopril 10mg daily. "
        "Allergic to penicillin and sulfa drugs. "
        "Physical exam reveals tenderness in the chest wall."
    )


@pytest.fixture
def empty_text():
    """Empty text for testing error handling."""
    return ""


def test_clinicalbert_service_initialization():
    """Test ClinicalBERT service can be initialized."""
    service = ClinicalBERTService()
    assert service is not None
    assert service.model is None  # Not loaded yet
    assert service.tokenizer is None


def test_clinicalbert_load_model():
    """Test model loading (may use fallback if model not available)."""
    service = ClinicalBERTService()
    result = service.load_model()

    # Result can be True (model loaded) or False (fallback needed)
    assert isinstance(result, bool)

    # If model loaded successfully, verify components exist
    if result:
        assert service.tokenizer is not None
        assert service.model is not None
        assert service.ner_pipeline is not None
    else:
        # Fallback mode
        assert service.use_fallback is True


def test_extract_entities_with_model(sample_clinical_text):
    """Test entity extraction with model (if available)."""
    service = ClinicalBERTService()
    service.load_model()

    # Skip if model not available (fallback mode)
    if service.use_fallback:
        pytest.skip("Model not available, using fallback")

    entities = service.extract_entities(sample_clinical_text)

    # Verify structure
    assert isinstance(entities, dict)
    assert "symptoms" in entities
    assert "conditions" in entities
    assert "medications" in entities
    assert "allergies" in entities
    assert "anatomical_locations" in entities
    assert "temporal_indicators" in entities

    # All values should be lists
    for key, value in entities.items():
        assert isinstance(value, list)

    print("\nExtracted entities (model):")
    for category, items in entities.items():
        if items:
            print(f"  {category}: {items}")


def test_extract_entities_with_claude_fallback(sample_clinical_text):
    """Test entity extraction with Claude API fallback."""
    import os

    # Skip if no API key available
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        pytest.skip("ANTHROPIC_API_KEY not set")

    service = ClinicalBERTService(anthropic_api_key=api_key)
    service.use_fallback = True  # Force fallback mode

    entities = service.extract_entities(sample_clinical_text)

    # Verify structure
    assert isinstance(entities, dict)
    assert "symptoms" in entities
    assert "conditions" in entities
    assert "medications" in entities
    assert "allergies" in entities
    assert "anatomical_locations" in entities
    assert "temporal_indicators" in entities

    # All values should be lists
    for key, value in entities.items():
        assert isinstance(value, list)

    # Verify some expected entities were extracted
    assert len(entities["symptoms"]) > 0  # chest pain, shortness of breath
    assert len(entities["conditions"]) > 0  # hypertension, diabetes
    assert len(entities["medications"]) > 0  # metformin, lisinopril
    assert len(entities["allergies"]) > 0  # penicillin, sulfa
    assert len(entities["anatomical_locations"]) > 0  # chest, left arm
    assert len(entities["temporal_indicators"]) > 0  # 3 hours ago

    print("\nExtracted entities (Claude fallback):")
    for category, items in entities.items():
        if items:
            print(f"  {category}: {items}")


def test_extract_entities_empty_text(empty_text):
    """Test error handling for empty text."""
    service = ClinicalBERTService()
    service.load_model()

    with pytest.raises(ValueError, match="Text cannot be empty"):
        service.extract_entities(empty_text)


def test_extract_entities_no_fallback():
    """Test error handling when model fails and no fallback available."""
    service = ClinicalBERTService()  # No API key
    service.use_fallback = True  # Force fallback mode

    with pytest.raises(RuntimeError, match="no Claude API key provided"):
        service.extract_entities("Patient has chest pain")


def test_clinicalbert_with_real_use_case():
    """Test with a realistic clinical note."""
    import os

    # Skip if no API key available
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        pytest.skip("ANTHROPIC_API_KEY not set")

    service = ClinicalBERTService(anthropic_api_key=api_key)
    service.load_model()

    clinical_note = """
    68 year old male presenting to ED with acute onset chest pain and dyspnea.
    Pain started 2 hours ago while at rest, described as crushing substernal pain
    radiating to left shoulder. Associated symptoms include nausea and diaphoresis.

    PMH: Coronary artery disease, hypertension, hyperlipidemia, type 2 diabetes mellitus
    Medications: Aspirin 81mg daily, Atorvastatin 40mg daily, Metoprolol 50mg BID,
                 Metformin 1000mg BID, Lisinopril 20mg daily
    Allergies: Penicillin (rash), Morphine (respiratory depression)

    Physical Exam:
    - Vitals: BP 160/95, HR 102, RR 22, SpO2 94% on room air, Temp 37.2C
    - General: Anxious, diaphoretic, in moderate distress
    - Cardiovascular: Tachycardic, regular rhythm, no murmurs
    - Respiratory: Mild tachypnea, clear to auscultation bilaterally
    - Extremities: No edema, pulses 2+ bilaterally
    """

    entities = service.extract_entities(clinical_note)

    # Verify comprehensive extraction
    assert len(entities["symptoms"]) >= 3  # chest pain, dyspnea, nausea, etc.
    assert len(entities["conditions"]) >= 3  # CAD, HTN, DM2, etc.
    assert len(entities["medications"]) >= 3  # aspirin, atorvastatin, etc.
    assert len(entities["allergies"]) >= 1  # penicillin, morphine
    assert (
        len(entities["anatomical_locations"]) >= 2
    )  # chest, left shoulder, etc.
    assert len(entities["temporal_indicators"]) >= 1  # 2 hours ago

    print("\nExtracted entities from clinical note:")
    for category, items in entities.items():
        if items:
            print(f"  {category}: {items}")


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
