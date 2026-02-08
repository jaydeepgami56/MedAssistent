"""
Backend configuration using pydantic-settings.
Loads all environment variables from .env file with sensible defaults.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Anthropic / Claude API
    ANTHROPIC_API_KEY: Optional[str] = None
    CLAUDE_MODEL: str = "claude-sonnet-4-20250514"

    # Qdrant Vector Database
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333

    # Orthanc DICOM Server
    ORTHANC_HOST: str = "localhost"
    ORTHANC_PORT: int = 8042

    # FHIR EHR Integration
    FHIR_BASE_URL: Optional[str] = None

    # RxNorm API
    RXNORM_API_URL: str = "https://rxnav.nlm.nih.gov/REST"

    # DrugBank API
    DRUGBANK_API_KEY: Optional[str] = None

    # PubMed / NCBI API
    PUBMED_API_KEY: Optional[str] = None

    # Neo4j Knowledge Graph
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "dev-password"

    # PostgreSQL Database
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "medassist"
    POSTGRES_USER: str = "medassist"
    POSTGRES_PASSWORD: str = "dev-password"

    # Model Directories
    MEDIMAGEINSIGHT_MODEL_DIR: Optional[str] = None

    # Encryption (for HIPAA compliance in production)
    ENCRYPTION_KEY: Optional[str] = None

    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # Ignore extra env vars not defined in Settings


# Global settings instance
settings = Settings()
