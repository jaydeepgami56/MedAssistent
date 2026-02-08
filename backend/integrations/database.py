"""
PostgreSQL database integration using asyncpg.
Provides connection pool and schema initialization for audit logs and patient data.
"""

import asyncpg
from typing import Optional
from backend.config import settings


# Global connection pool
_pool: Optional[asyncpg.Pool] = None


async def get_db_pool() -> asyncpg.Pool:
    """
    Get or create the asyncpg connection pool.

    Returns:
        asyncpg.Pool: The database connection pool.

    Raises:
        Exception: If database connection fails.
    """
    global _pool

    if _pool is None:
        _pool = await asyncpg.create_pool(
            host=settings.POSTGRES_HOST,
            port=settings.POSTGRES_PORT,
            database=settings.POSTGRES_DB,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            min_size=2,
            max_size=10,
            command_timeout=60,
        )
        print(f"[DATABASE] Connection pool created: {settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}")

    return _pool


async def close_db_pool():
    """Close the database connection pool."""
    global _pool

    if _pool is not None:
        await _pool.close()
        _pool = None
        print("[DATABASE] Connection pool closed")


async def init_db():
    """
    Initialize database schema by creating all required tables.

    Creates four tables:
    - audit_log: Agent execution audit trail
    - patients: Patient demographic and clinical data
    - triage_assessments: Emergency triage assessment results
    - radiology_reports: Medical imaging analysis results

    This function is idempotent - safe to call multiple times.
    """
    pool = await get_db_pool()

    async with pool.acquire() as conn:
        # Create audit_log table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMPTZ DEFAULT NOW(),
                agent_id VARCHAR(50) NOT NULL,
                skill_name VARCHAR(100) NOT NULL,
                request_summary TEXT,
                model_used VARCHAR(100),
                confidence FLOAT,
                clinician_action VARCHAR(50),
                clinician_id VARCHAR(50),
                response_time_ms INT
            )
        """)
        print("[DATABASE] Table 'audit_log' ready")

        # Create patients table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS patients (
                id SERIAL PRIMARY KEY,
                external_id VARCHAR(100) UNIQUE,
                name VARCHAR(200),
                age INT,
                gender VARCHAR(20),
                medical_history JSONB,
                allergies JSONB,
                medications JSONB,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        print("[DATABASE] Table 'patients' ready")

        # Create triage_assessments table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS triage_assessments (
                id SERIAL PRIMARY KEY,
                patient_id INT REFERENCES patients(id),
                esi_score INT CHECK (esi_score >= 1 AND esi_score <= 5),
                red_flags JSONB,
                routing VARCHAR(200),
                reasoning TEXT,
                confidence FLOAT,
                clinician_override BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        print("[DATABASE] Table 'triage_assessments' ready")

        # Create radiology_reports table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS radiology_reports (
                id SERIAL PRIMARY KEY,
                patient_id INT REFERENCES patients(id),
                modality VARCHAR(100),
                findings JSONB,
                similar_cases JSONB,
                recommendation TEXT,
                overall_confidence FLOAT,
                clinician_action VARCHAR(50),
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        print("[DATABASE] Table 'radiology_reports' ready")

        print("[DATABASE] Schema initialization complete")


async def test_connection():
    """
    Test database connectivity by running a simple query.

    Returns:
        bool: True if connection successful, False otherwise.
    """
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            version = await conn.fetchval("SELECT version()")
            print(f"[DATABASE] Connection test successful: {version[:50]}...")
            return True
    except Exception as e:
        print(f"[DATABASE] Connection test failed: {e}")
        return False
