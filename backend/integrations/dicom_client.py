"""
Orthanc DICOM Integration Client.

This module provides a service class for interacting with Orthanc DICOM server
to upload, retrieve, and manage medical imaging studies.

Orthanc REST API provides:
- DICOM file upload (POST /instances)
- Study metadata retrieval (GET /studies/{id})
- Image preview retrieval (GET /instances/{id}/preview)
- Patient study listing (GET /patients/{id}/studies)
"""

from typing import Optional, Any
import io
import httpx
from PIL import Image
from backend.config import settings


class DicomClient:
    """
    Service class for Orthanc DICOM REST API operations.

    Handles:
    - DICOM file upload to Orthanc
    - Study metadata retrieval
    - Rendered image retrieval for model inference
    - Patient study listing
    - Error handling for DICOM server unavailability
    """

    def __init__(self, host: Optional[str] = None, port: Optional[int] = None):
        """
        Initialize DICOM client.

        Args:
            host: Orthanc server host (defaults to settings.ORTHANC_HOST)
            port: Orthanc server port (defaults to settings.ORTHANC_PORT)
        """
        self.host = host or settings.ORTHANC_HOST or "localhost"
        self.port = port or settings.ORTHANC_PORT or 8042
        self.base_url = f"http://{self.host}:{self.port}"
        self.client = httpx.AsyncClient(timeout=30.0)

        print(f"DICOM client initialized: {self.base_url}")

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def upload_study(self, dicom_bytes: bytes) -> str:
        """
        Upload DICOM file to Orthanc server.

        Calls POST /instances to upload a DICOM file and store it in Orthanc.

        Args:
            dicom_bytes: Raw DICOM file bytes

        Returns:
            str: Orthanc instance ID (UUID) of the uploaded DICOM instance

        Raises:
            httpx.HTTPStatusError: If upload fails
            ValueError: If dicom_bytes is empty or invalid

        Example:
            with open("chest_xray.dcm", "rb") as f:
                instance_id = await client.upload_study(f.read())
            # Returns: "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        """
        if not dicom_bytes or len(dicom_bytes) == 0:
            raise ValueError("DICOM bytes cannot be empty")

        try:
            url = f"{self.base_url}/instances"

            response = await self.client.post(
                url,
                content=dicom_bytes,
                headers={"Content-Type": "application/dicom"}
            )
            response.raise_for_status()

            data = response.json()

            # Orthanc returns JSON with ID field containing the instance ID
            instance_id = data.get("ID")
            if not instance_id:
                raise ValueError("Orthanc response missing instance ID")

            print(f"DICOM uploaded successfully: {instance_id}")
            return instance_id

        except httpx.HTTPStatusError as e:
            print(f"HTTP error uploading DICOM: {e.response.status_code} - {e.response.text}")
            raise
        except httpx.RequestError as e:
            print(f"Network error uploading DICOM: {str(e)}")
            raise
        except Exception as e:
            print(f"Unexpected error uploading DICOM: {str(e)}")
            raise

    async def get_study(self, study_id: str) -> dict:
        """
        Retrieve study metadata from Orthanc.

        Calls GET /studies/{id} to retrieve study-level metadata including
        patient info, study description, modality, series, and instances.

        Args:
            study_id: Orthanc study ID (UUID)

        Returns:
            dict with:
                - id: str - Study ID
                - patient_id: str - Patient ID
                - patient_name: str - Patient name
                - study_date: str - Study date (YYYY-MM-DD)
                - study_description: str - Study description
                - modality: str - Primary modality (CT, MR, CR, etc.)
                - series: list[dict] - Series metadata
                - instances: list[str] - Instance IDs
                - found: bool - Whether study was found
                - error: str - Error message if lookup failed

        Example:
            study = await client.get_study("abc123...")
            # {'id': 'abc123...', 'patient_name': 'DOE^JOHN', 'modality': 'CR',
            #  'study_date': '2024-01-15', 'series': [...], 'found': True}
        """
        if not study_id or not study_id.strip():
            return {
                "id": None,
                "patient_id": None,
                "patient_name": None,
                "study_date": None,
                "study_description": None,
                "modality": None,
                "series": [],
                "instances": [],
                "found": False,
                "error": "Study ID cannot be empty"
            }

        try:
            url = f"{self.base_url}/studies/{study_id.strip()}"

            response = await self.client.get(
                url,
                headers={"Accept": "application/json"}
            )
            response.raise_for_status()

            data = response.json()

            # Parse study metadata
            main_tags = data.get("MainDicomTags", {})
            patient_tags = data.get("PatientMainDicomTags", {})

            return {
                "id": data.get("ID"),
                "patient_id": data.get("ParentPatient"),
                "patient_name": patient_tags.get("PatientName", "Unknown"),
                "study_date": main_tags.get("StudyDate", ""),
                "study_description": main_tags.get("StudyDescription", ""),
                "modality": main_tags.get("Modality", ""),
                "series": data.get("Series", []),
                "instances": data.get("Instances", []),
                "found": True
            }

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return {
                    "id": study_id,
                    "patient_id": None,
                    "patient_name": None,
                    "study_date": None,
                    "study_description": None,
                    "modality": None,
                    "series": [],
                    "instances": [],
                    "found": False,
                    "error": f"Study not found: {study_id}"
                }
            else:
                print(f"HTTP error retrieving study: {e.response.status_code}")
                return {
                    "id": study_id,
                    "patient_id": None,
                    "patient_name": None,
                    "study_date": None,
                    "study_description": None,
                    "modality": None,
                    "series": [],
                    "instances": [],
                    "found": False,
                    "error": f"HTTP error: {e.response.status_code}"
                }

        except httpx.RequestError as e:
            print(f"Network error retrieving study: {str(e)}")
            return {
                "id": study_id,
                "patient_id": None,
                "patient_name": None,
                "study_date": None,
                "study_description": None,
                "modality": None,
                "series": [],
                "instances": [],
                "found": False,
                "error": f"Network error: {str(e)}"
            }

        except Exception as e:
            print(f"Unexpected error retrieving study: {str(e)}")
            return {
                "id": study_id,
                "patient_id": None,
                "patient_name": None,
                "study_date": None,
                "study_description": None,
                "modality": None,
                "series": [],
                "instances": [],
                "found": False,
                "error": f"Unexpected error: {str(e)}"
            }

    async def get_image(self, instance_id: str) -> Optional[Image.Image]:
        """
        Retrieve rendered image from Orthanc for model inference.

        Calls GET /instances/{id}/preview to retrieve a PNG preview of the DICOM instance,
        then converts it to a PIL.Image for use with MedImageInsight or other models.

        Args:
            instance_id: Orthanc instance ID (UUID)

        Returns:
            PIL.Image.Image object or None if retrieval fails

        Example:
            image = await client.get_image("xyz789...")
            if image:
                # Use with MedImageInsight
                result = model.predict(image)
        """
        if not instance_id or not instance_id.strip():
            print("Error: Instance ID cannot be empty")
            return None

        try:
            url = f"{self.base_url}/instances/{instance_id.strip()}/preview"

            response = await self.client.get(url)
            response.raise_for_status()

            # Orthanc returns PNG image bytes
            image_bytes = response.content

            # Convert to PIL Image
            image = Image.open(io.BytesIO(image_bytes))
            print(f"Image retrieved successfully: {instance_id} ({image.size})")
            return image

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                print(f"Instance not found: {instance_id}")
            else:
                print(f"HTTP error retrieving image: {e.response.status_code}")
            return None

        except httpx.RequestError as e:
            print(f"Network error retrieving image: {str(e)}")
            return None

        except Exception as e:
            print(f"Unexpected error retrieving image: {str(e)}")
            return None

    async def list_studies(self, patient_id: str) -> list[dict]:
        """
        List all studies for a given patient.

        Retrieves patient metadata from Orthanc, then fetches study details
        for each study associated with the patient.

        Args:
            patient_id: Orthanc patient ID (UUID)

        Returns:
            list[dict]: List of study metadata dicts (same format as get_study)

        Example:
            studies = await client.list_studies("patient123...")
            # [
            #   {'id': 'study1...', 'study_date': '2024-01-15', 'modality': 'CR', ...},
            #   {'id': 'study2...', 'study_date': '2024-01-20', 'modality': 'CT', ...}
            # ]
        """
        if not patient_id or not patient_id.strip():
            print("Error: Patient ID cannot be empty")
            return []

        try:
            # First, get patient metadata to retrieve list of study IDs
            url = f"{self.base_url}/patients/{patient_id.strip()}"

            response = await self.client.get(
                url,
                headers={"Accept": "application/json"}
            )
            response.raise_for_status()

            patient_data = response.json()
            study_ids = patient_data.get("Studies", [])

            if not study_ids:
                print(f"No studies found for patient: {patient_id}")
                return []

            # Fetch metadata for each study
            studies = []
            for study_id in study_ids:
                study = await self.get_study(study_id)
                if study.get("found"):
                    studies.append(study)

            print(f"Retrieved {len(studies)} studies for patient {patient_id}")
            return studies

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                print(f"Patient not found: {patient_id}")
            else:
                print(f"HTTP error listing studies: {e.response.status_code}")
            return []

        except httpx.RequestError as e:
            print(f"Network error listing studies: {str(e)}")
            return []

        except Exception as e:
            print(f"Unexpected error listing studies: {str(e)}")
            return []


# Global DICOM client instance (singleton pattern)
_dicom_client: Optional[DicomClient] = None


async def init_dicom() -> Optional[DicomClient]:
    """
    Initialize the global DICOM client.

    Returns:
        DicomClient instance or None if initialization fails
    """
    global _dicom_client

    try:
        _dicom_client = DicomClient()
        print("DICOM client initialized successfully")
        return _dicom_client
    except Exception as e:
        print(f"Warning: Failed to initialize DICOM client: {e}")
        print("DICOM integration may be limited")
        return None


async def close_dicom():
    """Close the global DICOM client."""
    global _dicom_client
    if _dicom_client:
        await _dicom_client.close()
        _dicom_client = None
        print("DICOM client closed")


def get_dicom_client() -> Optional[DicomClient]:
    """
    Get the global DICOM client instance.

    Returns:
        DicomClient instance or None if not initialized
    """
    return _dicom_client
