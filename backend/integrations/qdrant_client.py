"""
Qdrant vector database client for medical image embeddings.

This module provides a service class for interacting with Qdrant vector database,
specifically for storing and searching medical image embeddings from MedImageInsight.
"""

from typing import Optional
import uuid
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from qdrant_client.http.exceptions import UnexpectedResponse

from backend.config import settings


class QdrantService:
    """
    Service class for Qdrant vector database operations.

    Handles:
    - Connection to Qdrant server
    - Collection creation with cosine distance metric
    - Embedding storage with metadata payload
    - Similarity search for medical images
    """

    def __init__(self, host: str = None, port: int = None):
        """
        Initialize Qdrant client.

        Args:
            host: Qdrant server host (defaults to settings.QDRANT_HOST)
            port: Qdrant server port (defaults to settings.QDRANT_PORT)
        """
        self.host = host or settings.QDRANT_HOST
        self.port = port or settings.QDRANT_PORT
        self.client = QdrantClient(host=self.host, port=self.port)
        print(f"Qdrant client initialized: {self.host}:{self.port}")

    async def create_collection(self, name: str, vector_size: int) -> bool:
        """
        Create a collection with cosine distance metric if it doesn't exist.

        Args:
            name: Collection name
            vector_size: Dimension of embedding vectors (e.g., 512 for MedImageInsight)

        Returns:
            True if collection was created or already exists

        Raises:
            Exception: If collection creation fails
        """
        try:
            # Check if collection already exists
            collections = self.client.get_collections().collections
            if any(col.name == name for col in collections):
                print(f"Qdrant collection '{name}' already exists")
                return True

            # Create new collection with cosine distance
            self.client.create_collection(
                collection_name=name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=Distance.COSINE
                )
            )
            print(f"Qdrant collection '{name}' created successfully (vector_size={vector_size}, distance=COSINE)")
            return True

        except UnexpectedResponse as e:
            # Qdrant already exists error is safe to ignore
            if "already exists" in str(e).lower():
                print(f"Qdrant collection '{name}' already exists")
                return True
            raise
        except Exception as e:
            print(f"Failed to create Qdrant collection '{name}': {e}")
            raise

    async def upsert_embedding(
        self,
        collection: str,
        id: str,
        vector: list[float],
        metadata: dict
    ) -> bool:
        """
        Store an embedding with metadata payload (creates or updates).

        Args:
            collection: Collection name
            id: Unique identifier for this embedding (can be string, will be converted to UUID)
            vector: Embedding vector (list of floats)
            metadata: Metadata payload (e.g., patient_id, modality, findings)

        Returns:
            True if upsert succeeded

        Raises:
            Exception: If upsert fails
        """
        try:
            # Convert string ID to UUID if necessary
            # Qdrant requires IDs to be either unsigned integers or UUIDs
            try:
                point_id = uuid.UUID(id)
            except ValueError:
                # If not a valid UUID, generate UUID from string hash
                point_id = uuid.uuid5(uuid.NAMESPACE_DNS, id)

            # Store original ID in payload for retrieval
            payload_with_id = {**metadata, "_original_id": id}

            point = PointStruct(
                id=str(point_id),
                vector=vector,
                payload=payload_with_id
            )

            self.client.upsert(
                collection_name=collection,
                points=[point]
            )

            print(f"Qdrant: Upserted embedding {id} (UUID: {point_id}) to collection '{collection}'")
            return True

        except Exception as e:
            print(f"Failed to upsert embedding {id} to collection '{collection}': {e}")
            raise

    async def search_similar(
        self,
        collection: str,
        query_vector: list[float],
        top_k: int = 5
    ) -> list[dict]:
        """
        Search for similar embeddings using cosine similarity.

        Args:
            collection: Collection name to search
            query_vector: Query embedding vector
            top_k: Number of top results to return (default: 5)

        Returns:
            List of dicts with keys: id (str), score (float), payload (dict)

        Raises:
            Exception: If search fails
        """
        try:
            results = self.client.query_points(
                collection_name=collection,
                query=query_vector,
                limit=top_k
            )

            # Format results as list of dicts
            # results.points contains the actual search results
            formatted_results = []
            for point in results.points:
                # Extract original ID from payload if available
                original_id = point.payload.get("_original_id", str(point.id))
                # Create clean payload without internal fields
                clean_payload = {k: v for k, v in point.payload.items() if not k.startswith("_")}

                formatted_results.append({
                    "id": original_id,
                    "score": point.score,
                    "payload": clean_payload
                })

            print(f"Qdrant: Found {len(formatted_results)} similar embeddings in collection '{collection}'")
            return formatted_results

        except Exception as e:
            print(f"Failed to search collection '{collection}': {e}")
            raise

    def close(self):
        """Close Qdrant client connection."""
        try:
            self.client.close()
            print("Qdrant client connection closed")
        except Exception as e:
            print(f"Error closing Qdrant client: {e}")


# Global QdrantService instance (singleton)
_qdrant_service: Optional[QdrantService] = None


def get_qdrant_service() -> QdrantService:
    """
    Get the global QdrantService instance (singleton pattern).

    Returns:
        QdrantService instance

    Raises:
        RuntimeError: If service hasn't been initialized
    """
    global _qdrant_service
    if _qdrant_service is None:
        raise RuntimeError("QdrantService not initialized. Call init_qdrant() first.")
    return _qdrant_service


async def init_qdrant():
    """
    Initialize Qdrant service and create medical_images collection.

    Called during FastAPI startup to:
    1. Create global QdrantService instance
    2. Create medical_images collection with 512-dimensional vectors

    The medical_images collection stores embeddings from MedImageInsight
    with metadata like patient_id, modality, findings, confidence.
    """
    global _qdrant_service

    try:
        print("Initializing Qdrant service...")
        _qdrant_service = QdrantService()

        # Create medical_images collection (MedImageInsight embedding dimension is 512)
        await _qdrant_service.create_collection(
            name="medical_images",
            vector_size=512  # MedImageInsight default embedding dimension
        )

        print("Qdrant service initialized successfully")

    except Exception as e:
        print(f"WARNING: Failed to initialize Qdrant service: {e}")
        print("Qdrant features will be unavailable. Check that Qdrant is running on {settings.QDRANT_HOST}:{settings.QDRANT_PORT}")
        # Don't raise - allow backend to start even if Qdrant is unavailable


async def close_qdrant():
    """
    Close Qdrant service connection.

    Called during FastAPI shutdown to clean up resources.
    """
    global _qdrant_service
    if _qdrant_service is not None:
        _qdrant_service.close()
        _qdrant_service = None
