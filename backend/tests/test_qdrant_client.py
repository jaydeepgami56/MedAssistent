"""
Tests for Qdrant vector database client.

Tests collection creation, embedding upsert, and similarity search.
"""

import pytest
from backend.integrations.qdrant_client import QdrantService


@pytest.mark.asyncio
async def test_qdrant_service_create_collection():
    """Test creating a collection."""
    service = QdrantService(host="localhost", port=6333)

    # Create a test collection
    success = await service.create_collection(name="test_collection", vector_size=128)
    assert success is True

    # Creating again should succeed (idempotent)
    success = await service.create_collection(name="test_collection", vector_size=128)
    assert success is True

    service.close()


@pytest.mark.asyncio
async def test_qdrant_service_upsert_embedding():
    """Test upserting an embedding with metadata."""
    service = QdrantService(host="localhost", port=6333)

    # Ensure collection exists
    await service.create_collection(name="test_collection", vector_size=128)

    # Upsert a test embedding
    test_vector = [0.1] * 128  # 128-dimensional vector
    test_metadata = {
        "patient_id": "P001",
        "modality": "CT",
        "findings": "Normal scan"
    }

    success = await service.upsert_embedding(
        collection="test_collection",
        id="test_embedding_1",
        vector=test_vector,
        metadata=test_metadata
    )
    assert success is True

    service.close()


@pytest.mark.asyncio
async def test_qdrant_service_search_similar():
    """Test searching for similar embeddings."""
    service = QdrantService(host="localhost", port=6333)

    # Ensure collection exists
    await service.create_collection(name="test_collection", vector_size=128)

    # Upsert two embeddings
    vector1 = [0.1] * 128
    vector2 = [0.2] * 128

    await service.upsert_embedding(
        collection="test_collection",
        id="embedding_1",
        vector=vector1,
        metadata={"label": "first"}
    )

    await service.upsert_embedding(
        collection="test_collection",
        id="embedding_2",
        vector=vector2,
        metadata={"label": "second"}
    )

    # Search with a query vector similar to vector1
    query_vector = [0.11] * 128
    results = await service.search_similar(
        collection="test_collection",
        query_vector=query_vector,
        top_k=2
    )

    # Should return 2 results
    assert len(results) == 2

    # Each result should have id, score, and payload
    for result in results:
        assert "id" in result
        assert "score" in result
        assert "payload" in result

    # First result should be embedding_1 (most similar)
    assert results[0]["id"] == "embedding_1"
    assert results[0]["payload"]["label"] == "first"

    service.close()


@pytest.mark.asyncio
async def test_medical_images_collection():
    """Test that medical_images collection exists with correct config."""
    service = QdrantService(host="localhost", port=6333)

    # Medical images collection should already exist from init_qdrant()
    collections = service.client.get_collections().collections
    collection_names = [col.name for col in collections]

    assert "medical_images" in collection_names

    # Verify it's configured for 512-dimensional vectors
    collection_info = service.client.get_collection("medical_images")
    assert collection_info.config.params.vectors.size == 512
    assert collection_info.config.params.vectors.distance.name == "COSINE"

    service.close()
