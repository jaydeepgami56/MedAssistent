"""External API and database integrations"""

from .fhir_client import FHIRClient, get_fhir_client, init_fhir, close_fhir
from .dicom_client import DicomClient, get_dicom_client, init_dicom, close_dicom

__all__ = [
    "FHIRClient",
    "get_fhir_client",
    "init_fhir",
    "close_fhir",
    "DicomClient",
    "get_dicom_client",
    "init_dicom",
    "close_dicom",
]
