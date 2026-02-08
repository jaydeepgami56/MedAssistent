"""
Tests for MedImageInsight model wrapper.
"""

import pytest
from PIL import Image
import numpy as np
from backend.models.medimageinsight import (
    MedImageInsightService,
    init_medimageinsight,
    get_medimageinsight_service,
)


def create_test_image(size=(224, 224)):
    """Create a test PIL image (random gray pixels)."""
    # Create random grayscale image
    arr = np.random.randint(0, 256, size, dtype=np.uint8)
    return Image.fromarray(arr, mode="L")


def test_service_initialization():
    """Test MedImageInsight service initialization."""
    service = MedImageInsightService()
    assert service is not None
    assert service.model is None  # Model not loaded yet
    assert service.use_mock is False


def test_load_model_fallback_to_mock():
    """Test model loading falls back to mock when dependencies unavailable."""
    service = MedImageInsightService()

    # Load model (will likely fail and use mock on systems without GPU/transformers)
    success = service.load_model()

    # Should either succeed or gracefully fall back to mock
    assert isinstance(success, bool)

    # If mock, use_mock should be True
    if not success:
        assert service.use_mock is True


def test_classify_image_with_chest_xray_labels():
    """Test image classification with chest X-ray labels."""
    service = MedImageInsightService()
    service.load_model()  # Will use mock if model unavailable

    # Create test image
    image = create_test_image()

    # Classify with chest X-ray labels
    results = service.classify_image(
        image=image,
        labels=MedImageInsightService.CHEST_XRAY_LABELS
    )

    # Verify results structure
    assert isinstance(results, list)
    assert len(results) == len(MedImageInsightService.CHEST_XRAY_LABELS)

    # Verify first result (highest confidence)
    top_result = results[0]
    assert "label" in top_result
    assert "confidence" in top_result
    assert isinstance(top_result["label"], str)
    assert isinstance(top_result["confidence"], float)
    assert 0.0 <= top_result["confidence"] <= 1.0

    # Verify results are sorted by confidence descending
    confidences = [r["confidence"] for r in results]
    assert confidences == sorted(confidences, reverse=True)

    # Verify all labels present
    result_labels = [r["label"] for r in results]
    assert set(result_labels) == set(MedImageInsightService.CHEST_XRAY_LABELS)


def test_classify_image_with_brain_mri_labels():
    """Test image classification with brain MRI labels."""
    service = MedImageInsightService()
    service.load_model()

    image = create_test_image()

    results = service.classify_image(
        image=image,
        labels=MedImageInsightService.BRAIN_MRI_LABELS
    )

    assert isinstance(results, list)
    assert len(results) == len(MedImageInsightService.BRAIN_MRI_LABELS)
    assert results[0]["confidence"] >= results[-1]["confidence"]  # Sorted


def test_classify_image_with_dermatology_labels():
    """Test image classification with dermatology labels."""
    service = MedImageInsightService()
    service.load_model()

    image = create_test_image()

    results = service.classify_image(
        image=image,
        labels=MedImageInsightService.DERMATOLOGY_LABELS
    )

    assert isinstance(results, list)
    assert len(results) == len(MedImageInsightService.DERMATOLOGY_LABELS)


def test_classify_image_invalid_input():
    """Test classification error handling for invalid inputs."""
    service = MedImageInsightService()
    service.load_model()

    # Test None image
    with pytest.raises(ValueError, match="Image cannot be None"):
        service.classify_image(image=None, labels=["normal", "abnormal"])

    # Test empty labels
    image = create_test_image()
    with pytest.raises(ValueError, match="Labels list cannot be empty"):
        service.classify_image(image=image, labels=[])


def test_generate_embedding():
    """Test embedding generation."""
    service = MedImageInsightService()
    service.load_model()

    image = create_test_image()

    embedding = service.generate_embedding(image)

    # Verify embedding structure
    assert isinstance(embedding, list)
    assert len(embedding) == MedImageInsightService.EMBEDDING_DIM  # 512 dimensions

    # Verify all elements are floats
    assert all(isinstance(x, float) for x in embedding)

    # Verify embedding is normalized (unit length)
    magnitude = sum(x * x for x in embedding) ** 0.5
    assert abs(magnitude - 1.0) < 0.01  # Allow small floating point error


def test_generate_embedding_invalid_input():
    """Test embedding generation error handling."""
    service = MedImageInsightService()
    service.load_model()

    with pytest.raises(ValueError, match="Image cannot be None"):
        service.generate_embedding(image=None)


def test_singleton_pattern():
    """Test global service singleton pattern."""
    # Initialize global service
    init_medimageinsight()

    # Get global service
    service = get_medimageinsight_service()

    assert service is not None
    assert isinstance(service, MedImageInsightService)


def test_modality_label_constants():
    """Test that all modality label sets are defined correctly."""
    # Chest X-ray labels
    assert len(MedImageInsightService.CHEST_XRAY_LABELS) == 10
    assert "normal" in MedImageInsightService.CHEST_XRAY_LABELS
    assert "pneumonia" in MedImageInsightService.CHEST_XRAY_LABELS

    # Brain MRI labels
    assert len(MedImageInsightService.BRAIN_MRI_LABELS) == 8
    assert "normal" in MedImageInsightService.BRAIN_MRI_LABELS
    assert "tumor/mass" in MedImageInsightService.BRAIN_MRI_LABELS

    # Dermatology labels
    assert len(MedImageInsightService.DERMATOLOGY_LABELS) == 7
    assert "benign nevus" in MedImageInsightService.DERMATOLOGY_LABELS
    assert "melanoma" in MedImageInsightService.DERMATOLOGY_LABELS

    # Chest CT labels
    assert len(MedImageInsightService.CHEST_CT_LABELS) == 8
    assert "pulmonary embolism" in MedImageInsightService.CHEST_CT_LABELS

    # Musculoskeletal labels
    assert len(MedImageInsightService.MUSCULOSKELETAL_LABELS) == 7
    assert "fracture" in MedImageInsightService.MUSCULOSKELETAL_LABELS


def test_mock_results_consistency():
    """Test that mock results are consistent and valid."""
    service = MedImageInsightService()
    service.use_mock = True  # Force mock mode

    image = create_test_image()
    labels = ["normal", "abnormal", "uncertain"]

    # Get classification results twice
    results1 = service.classify_image(image, labels)
    results2 = service.classify_image(image, labels)

    # Both should be valid
    assert len(results1) == 3
    assert len(results2) == 3

    # Confidences should sum to approximately 1.0
    total1 = sum(r["confidence"] for r in results1)
    total2 = sum(r["confidence"] for r in results2)
    assert abs(total1 - 1.0) < 0.01
    assert abs(total2 - 1.0) < 0.01

    # Get embeddings twice
    emb1 = service.generate_embedding(image)
    emb2 = service.generate_embedding(image)

    # Both should be valid 512-dim vectors
    assert len(emb1) == 512
    assert len(emb2) == 512
