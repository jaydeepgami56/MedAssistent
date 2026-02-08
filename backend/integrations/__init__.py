"""External API and database integrations"""

from .fhir_client import FHIRClient, get_fhir_client, init_fhir, close_fhir

__all__ = [
    "FHIRClient",
    "get_fhir_client",
    "init_fhir",
    "close_fhir",
]
