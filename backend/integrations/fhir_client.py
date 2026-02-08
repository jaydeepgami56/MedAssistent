"""
FHIR R4 EHR Integration Client.

This module provides a service class for interacting with FHIR R4 compliant EHR systems
(Epic, Cerner, etc.) to retrieve patient clinical data.

FHIR (Fast Healthcare Interoperability Resources) provides:
- Standardized patient demographics (Patient resource)
- Active medical conditions (Condition resource)
- Current medications (MedicationRequest resource)
- Allergies and intolerances (AllergyIntolerance resource)
- Vital signs and lab results (Observation resource)
"""

from typing import Optional, Any
from datetime import datetime
import httpx
from backend.config import settings


class FHIRClient:
    """
    Service class for FHIR R4 API operations.

    Handles:
    - Patient demographics retrieval
    - Active conditions query
    - Current medications query
    - Allergy/intolerance query
    - Vital signs and lab observation query
    - Error handling for EHR system unavailability
    """

    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize FHIR client.

        Args:
            base_url: FHIR R4 API base URL (defaults to settings.FHIR_BASE_URL)
        """
        self.base_url = (base_url or settings.FHIR_BASE_URL or "").rstrip('/')
        self.client = httpx.AsyncClient(timeout=30.0)

        if not self.base_url:
            print("Warning: FHIR_BASE_URL not configured. FHIR client will return empty results.")
        else:
            print(f"FHIR client initialized: {self.base_url}")

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def get_patient(self, patient_id: str) -> dict:
        """
        Fetch patient demographics from FHIR Patient resource.

        Calls GET /Patient/{id} to retrieve patient information.

        Args:
            patient_id: FHIR Patient resource ID

        Returns:
            dict with:
                - id: str - Patient ID
                - name: str - Full name (formatted)
                - age: int - Age in years
                - gender: str - Gender (male, female, other, unknown)
                - date_of_birth: str - DOB in YYYY-MM-DD format
                - found: bool - Whether patient was found
                - error: str - Error message if lookup failed

        Example:
            patient = await client.get_patient("12345")
            # {'id': '12345', 'name': 'John Doe', 'age': 45, 'gender': 'male',
            #  'date_of_birth': '1978-03-15', 'found': True}
        """
        if not patient_id or not patient_id.strip():
            return {
                "id": None,
                "name": None,
                "age": None,
                "gender": None,
                "date_of_birth": None,
                "found": False,
                "error": "Patient ID cannot be empty"
            }

        if not self.base_url:
            return self._empty_patient_result(patient_id, "FHIR server not configured")

        try:
            url = f"{self.base_url}/Patient/{patient_id.strip()}"

            response = await self.client.get(
                url,
                headers={"Accept": "application/fhir+json"}
            )
            response.raise_for_status()

            data = response.json()

            # Parse FHIR Patient resource
            return self._parse_patient(data)

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                error_msg = f"Patient {patient_id} not found"
            else:
                error_msg = f"HTTP {e.response.status_code}"
            print(f"FHIR Patient API error: {error_msg}")
            return self._empty_patient_result(patient_id, error_msg)
        except httpx.RequestError as e:
            error_msg = f"Connection error: {str(e)}"
            print(f"FHIR Patient connection error: {error_msg}")
            return self._empty_patient_result(patient_id, error_msg)
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            print(f"FHIR Patient unexpected error: {error_msg}")
            return self._empty_patient_result(patient_id, error_msg)

    def _parse_patient(self, resource: dict) -> dict:
        """
        Parse FHIR Patient resource to simplified dict.

        Args:
            resource: FHIR Patient resource JSON

        Returns:
            Simplified patient dict
        """
        try:
            patient_id = resource.get("id", "")

            # Extract name (use first official/usual name)
            name_str = None
            name_list = resource.get("name", [])
            for name_obj in name_list:
                use = name_obj.get("use", "")
                if use in ["official", "usual", ""]:
                    # Build full name from given + family
                    given = name_obj.get("given", [])
                    family = name_obj.get("family", "")

                    if given or family:
                        name_parts = given + ([family] if family else [])
                        name_str = " ".join(name_parts)
                        break

            # Extract date of birth and calculate age
            birth_date_str = resource.get("birthDate", "")
            age = None
            if birth_date_str:
                try:
                    birth_date = datetime.strptime(birth_date_str, "%Y-%m-%d")
                    today = datetime.now()
                    age = today.year - birth_date.year
                    # Adjust if birthday hasn't occurred this year
                    if (today.month, today.day) < (birth_date.month, birth_date.day):
                        age -= 1
                except ValueError:
                    pass

            # Extract gender
            gender = resource.get("gender", "unknown")

            return {
                "id": patient_id,
                "name": name_str,
                "age": age,
                "gender": gender,
                "date_of_birth": birth_date_str,
                "found": True
            }

        except Exception as e:
            print(f"Error parsing Patient resource: {str(e)}")
            return self._empty_patient_result(
                resource.get("id", "unknown"),
                "Parsing error"
            )

    def _empty_patient_result(self, patient_id: str, error: str) -> dict:
        """Return empty patient result with error."""
        return {
            "id": patient_id,
            "name": None,
            "age": None,
            "gender": None,
            "date_of_birth": None,
            "found": False,
            "error": error
        }

    async def get_conditions(self, patient_id: str) -> list[dict]:
        """
        Fetch active conditions from FHIR Condition resources.

        Calls GET /Condition?patient={id}&clinical-status=active to retrieve
        active medical conditions.

        Args:
            patient_id: FHIR Patient resource ID

        Returns:
            list of dicts with:
                - id: str - Condition resource ID
                - code: str - Condition code (SNOMED, ICD-10, etc.)
                - display: str - Human-readable condition name
                - clinical_status: str - Status (active, recurrence, etc.)
                - onset_date: str - When condition started (if available)
                - recorded_date: str - When condition was recorded

        Example:
            conditions = await client.get_conditions("12345")
            # [{'id': 'c1', 'code': '73211009', 'display': 'Diabetes mellitus',
            #   'clinical_status': 'active', 'onset_date': '2020-01-15'}]
        """
        if not patient_id or not patient_id.strip():
            return []

        if not self.base_url:
            print("FHIR server not configured - returning empty conditions list")
            return []

        try:
            url = f"{self.base_url}/Condition"
            params = {
                "patient": patient_id.strip(),
                "clinical-status": "active"
            }

            response = await self.client.get(
                url,
                params=params,
                headers={"Accept": "application/fhir+json"}
            )
            response.raise_for_status()

            data = response.json()

            # Parse Bundle of Condition resources
            conditions = []
            entries = data.get("entry", [])

            for entry in entries:
                resource = entry.get("resource", {})
                if resource.get("resourceType") == "Condition":
                    condition = self._parse_condition(resource)
                    if condition:
                        conditions.append(condition)

            print(f"Found {len(conditions)} active conditions for patient {patient_id}")
            return conditions

        except httpx.HTTPStatusError as e:
            print(f"FHIR Condition API error: HTTP {e.response.status_code}")
            return []
        except httpx.RequestError as e:
            print(f"FHIR Condition connection error: {str(e)}")
            return []
        except Exception as e:
            print(f"FHIR Condition unexpected error: {str(e)}")
            return []

    def _parse_condition(self, resource: dict) -> Optional[dict]:
        """
        Parse FHIR Condition resource to simplified dict.

        Args:
            resource: FHIR Condition resource JSON

        Returns:
            Simplified condition dict or None if parsing fails
        """
        try:
            condition_id = resource.get("id", "")

            # Extract condition code and display
            code_obj = resource.get("code", {})
            coding_list = code_obj.get("coding", [])

            code = None
            display = None
            if coding_list:
                code = coding_list[0].get("code", "")
                display = coding_list[0].get("display", "")

            # Fallback to text if no coding
            if not display:
                display = code_obj.get("text", "Unknown condition")

            # Extract clinical status
            clinical_status_obj = resource.get("clinicalStatus", {})
            clinical_status_coding = clinical_status_obj.get("coding", [])
            clinical_status = "unknown"
            if clinical_status_coding:
                clinical_status = clinical_status_coding[0].get("code", "unknown")

            # Extract onset date (multiple formats possible)
            onset_date = None
            onset_datetime = resource.get("onsetDateTime")
            if onset_datetime:
                onset_date = onset_datetime.split("T")[0]  # Extract date part
            else:
                onset_period = resource.get("onsetPeriod", {})
                onset_start = onset_period.get("start")
                if onset_start:
                    onset_date = onset_start.split("T")[0]

            # Extract recorded date
            recorded_date = resource.get("recordedDate", "")
            if recorded_date:
                recorded_date = recorded_date.split("T")[0]

            return {
                "id": condition_id,
                "code": code,
                "display": display,
                "clinical_status": clinical_status,
                "onset_date": onset_date,
                "recorded_date": recorded_date
            }

        except Exception as e:
            print(f"Error parsing Condition resource: {str(e)}")
            return None

    async def get_medications(self, patient_id: str) -> list[dict]:
        """
        Fetch active medications from FHIR MedicationRequest resources.

        Calls GET /MedicationRequest?patient={id}&status=active to retrieve
        current medication orders.

        Args:
            patient_id: FHIR Patient resource ID

        Returns:
            list of dicts with:
                - id: str - MedicationRequest resource ID
                - code: str - Medication code (RxNorm preferred)
                - display: str - Medication name
                - status: str - Status (active, completed, etc.)
                - dosage_text: str - Dosage instructions
                - authored_on: str - When prescription was written

        Example:
            medications = await client.get_medications("12345")
            # [{'id': 'm1', 'code': '197361', 'display': 'Metformin 500mg',
            #   'status': 'active', 'dosage_text': 'Take 1 tablet twice daily'}]
        """
        if not patient_id or not patient_id.strip():
            return []

        if not self.base_url:
            print("FHIR server not configured - returning empty medications list")
            return []

        try:
            url = f"{self.base_url}/MedicationRequest"
            params = {
                "patient": patient_id.strip(),
                "status": "active"
            }

            response = await self.client.get(
                url,
                params=params,
                headers={"Accept": "application/fhir+json"}
            )
            response.raise_for_status()

            data = response.json()

            # Parse Bundle of MedicationRequest resources
            medications = []
            entries = data.get("entry", [])

            for entry in entries:
                resource = entry.get("resource", {})
                if resource.get("resourceType") == "MedicationRequest":
                    medication = self._parse_medication_request(resource)
                    if medication:
                        medications.append(medication)

            print(f"Found {len(medications)} active medications for patient {patient_id}")
            return medications

        except httpx.HTTPStatusError as e:
            print(f"FHIR MedicationRequest API error: HTTP {e.response.status_code}")
            return []
        except httpx.RequestError as e:
            print(f"FHIR MedicationRequest connection error: {str(e)}")
            return []
        except Exception as e:
            print(f"FHIR MedicationRequest unexpected error: {str(e)}")
            return []

    def _parse_medication_request(self, resource: dict) -> Optional[dict]:
        """
        Parse FHIR MedicationRequest resource to simplified dict.

        Args:
            resource: FHIR MedicationRequest resource JSON

        Returns:
            Simplified medication dict or None if parsing fails
        """
        try:
            medication_id = resource.get("id", "")

            # Extract medication code and display
            # Can be in medicationCodeableConcept or medicationReference
            code = None
            display = None

            med_codeable = resource.get("medicationCodeableConcept")
            if med_codeable:
                coding_list = med_codeable.get("coding", [])
                if coding_list:
                    code = coding_list[0].get("code", "")
                    display = coding_list[0].get("display", "")

                if not display:
                    display = med_codeable.get("text", "Unknown medication")
            else:
                # Handle medicationReference (would need additional lookup)
                med_ref = resource.get("medicationReference", {})
                display = med_ref.get("display", "Unknown medication")

            # Extract status
            status = resource.get("status", "unknown")

            # Extract dosage instructions
            dosage_text = None
            dosage_instructions = resource.get("dosageInstruction", [])
            if dosage_instructions:
                dosage_text = dosage_instructions[0].get("text", "")

            # Extract authored date
            authored_on = resource.get("authoredOn", "")
            if authored_on:
                authored_on = authored_on.split("T")[0]

            return {
                "id": medication_id,
                "code": code,
                "display": display,
                "status": status,
                "dosage_text": dosage_text,
                "authored_on": authored_on
            }

        except Exception as e:
            print(f"Error parsing MedicationRequest resource: {str(e)}")
            return None

    async def get_allergies(self, patient_id: str) -> list[dict]:
        """
        Fetch allergies and intolerances from FHIR AllergyIntolerance resources.

        Calls GET /AllergyIntolerance?patient={id} to retrieve patient allergies.

        Args:
            patient_id: FHIR Patient resource ID

        Returns:
            list of dicts with:
                - id: str - AllergyIntolerance resource ID
                - code: str - Allergen code
                - display: str - Allergen name
                - clinical_status: str - Status (active, inactive, resolved)
                - verification_status: str - Verification (confirmed, unconfirmed)
                - type: str - Type (allergy, intolerance)
                - category: list[str] - Categories (food, medication, environment, etc.)
                - criticality: str - Criticality (low, high, unable-to-assess)
                - reaction: list[str] - Reaction manifestations

        Example:
            allergies = await client.get_allergies("12345")
            # [{'id': 'a1', 'code': '387207008', 'display': 'Penicillin',
            #   'clinical_status': 'active', 'type': 'allergy',
            #   'category': ['medication'], 'criticality': 'high',
            #   'reaction': ['Anaphylaxis']}]
        """
        if not patient_id or not patient_id.strip():
            return []

        if not self.base_url:
            print("FHIR server not configured - returning empty allergies list")
            return []

        try:
            url = f"{self.base_url}/AllergyIntolerance"
            params = {
                "patient": patient_id.strip()
            }

            response = await self.client.get(
                url,
                params=params,
                headers={"Accept": "application/fhir+json"}
            )
            response.raise_for_status()

            data = response.json()

            # Parse Bundle of AllergyIntolerance resources
            allergies = []
            entries = data.get("entry", [])

            for entry in entries:
                resource = entry.get("resource", {})
                if resource.get("resourceType") == "AllergyIntolerance":
                    allergy = self._parse_allergy_intolerance(resource)
                    if allergy:
                        allergies.append(allergy)

            print(f"Found {len(allergies)} allergies/intolerances for patient {patient_id}")
            return allergies

        except httpx.HTTPStatusError as e:
            print(f"FHIR AllergyIntolerance API error: HTTP {e.response.status_code}")
            return []
        except httpx.RequestError as e:
            print(f"FHIR AllergyIntolerance connection error: {str(e)}")
            return []
        except Exception as e:
            print(f"FHIR AllergyIntolerance unexpected error: {str(e)}")
            return []

    def _parse_allergy_intolerance(self, resource: dict) -> Optional[dict]:
        """
        Parse FHIR AllergyIntolerance resource to simplified dict.

        Args:
            resource: FHIR AllergyIntolerance resource JSON

        Returns:
            Simplified allergy dict or None if parsing fails
        """
        try:
            allergy_id = resource.get("id", "")

            # Extract allergen code and display
            code_obj = resource.get("code", {})
            coding_list = code_obj.get("coding", [])

            code = None
            display = None
            if coding_list:
                code = coding_list[0].get("code", "")
                display = coding_list[0].get("display", "")

            if not display:
                display = code_obj.get("text", "Unknown allergen")

            # Extract clinical status
            clinical_status_obj = resource.get("clinicalStatus", {})
            clinical_status_coding = clinical_status_obj.get("coding", [])
            clinical_status = "unknown"
            if clinical_status_coding:
                clinical_status = clinical_status_coding[0].get("code", "unknown")

            # Extract verification status
            verification_status_obj = resource.get("verificationStatus", {})
            verification_status_coding = verification_status_obj.get("coding", [])
            verification_status = "unknown"
            if verification_status_coding:
                verification_status = verification_status_coding[0].get("code", "unknown")

            # Extract type (allergy vs intolerance)
            allergy_type = resource.get("type", "unknown")

            # Extract categories
            categories = resource.get("category", [])

            # Extract criticality
            criticality = resource.get("criticality", "unable-to-assess")

            # Extract reactions
            reactions = []
            reaction_list = resource.get("reaction", [])
            for reaction_obj in reaction_list:
                manifestations = reaction_obj.get("manifestation", [])
                for manifestation in manifestations:
                    manifestation_coding = manifestation.get("coding", [])
                    if manifestation_coding:
                        reaction_display = manifestation_coding[0].get("display", "")
                        if reaction_display:
                            reactions.append(reaction_display)
                    else:
                        reaction_text = manifestation.get("text", "")
                        if reaction_text:
                            reactions.append(reaction_text)

            return {
                "id": allergy_id,
                "code": code,
                "display": display,
                "clinical_status": clinical_status,
                "verification_status": verification_status,
                "type": allergy_type,
                "category": categories,
                "criticality": criticality,
                "reaction": reactions
            }

        except Exception as e:
            print(f"Error parsing AllergyIntolerance resource: {str(e)}")
            return None

    async def get_observations(
        self,
        patient_id: str,
        category: str = "vital-signs"
    ) -> list[dict]:
        """
        Fetch observations (vitals, labs) from FHIR Observation resources.

        Calls GET /Observation?patient={id}&category={category} to retrieve
        patient observations filtered by category.

        Args:
            patient_id: FHIR Patient resource ID
            category: Observation category (vital-signs, laboratory, imaging, etc.)

        Returns:
            list of dicts with:
                - id: str - Observation resource ID
                - code: str - LOINC code
                - display: str - Observation name
                - value: Any - Observation value
                - unit: str - Unit of measure
                - effective_date: str - When observation was made
                - status: str - Status (final, preliminary, etc.)

        Example:
            vitals = await client.get_observations("12345", category="vital-signs")
            # [{'id': 'o1', 'code': '8867-4', 'display': 'Heart rate',
            #   'value': 72, 'unit': 'bpm', 'effective_date': '2024-02-01',
            #   'status': 'final'}]
        """
        if not patient_id or not patient_id.strip():
            return []

        if not self.base_url:
            print("FHIR server not configured - returning empty observations list")
            return []

        try:
            url = f"{self.base_url}/Observation"
            params = {
                "patient": patient_id.strip(),
                "category": category
            }

            response = await self.client.get(
                url,
                params=params,
                headers={"Accept": "application/fhir+json"}
            )
            response.raise_for_status()

            data = response.json()

            # Parse Bundle of Observation resources
            observations = []
            entries = data.get("entry", [])

            for entry in entries:
                resource = entry.get("resource", {})
                if resource.get("resourceType") == "Observation":
                    observation = self._parse_observation(resource)
                    if observation:
                        observations.append(observation)

            print(f"Found {len(observations)} {category} observations for patient {patient_id}")
            return observations

        except httpx.HTTPStatusError as e:
            print(f"FHIR Observation API error: HTTP {e.response.status_code}")
            return []
        except httpx.RequestError as e:
            print(f"FHIR Observation connection error: {str(e)}")
            return []
        except Exception as e:
            print(f"FHIR Observation unexpected error: {str(e)}")
            return []

    def _parse_observation(self, resource: dict) -> Optional[dict]:
        """
        Parse FHIR Observation resource to simplified dict.

        Args:
            resource: FHIR Observation resource JSON

        Returns:
            Simplified observation dict or None if parsing fails
        """
        try:
            observation_id = resource.get("id", "")

            # Extract code and display
            code_obj = resource.get("code", {})
            coding_list = code_obj.get("coding", [])

            code = None
            display = None
            if coding_list:
                code = coding_list[0].get("code", "")
                display = coding_list[0].get("display", "")

            if not display:
                display = code_obj.get("text", "Unknown observation")

            # Extract value (can be Quantity, String, CodeableConcept, etc.)
            value = None
            unit = None

            value_quantity = resource.get("valueQuantity")
            if value_quantity:
                value = value_quantity.get("value")
                unit = value_quantity.get("unit", "")
            else:
                value_string = resource.get("valueString")
                if value_string:
                    value = value_string
                else:
                    value_codeable = resource.get("valueCodeableConcept")
                    if value_codeable:
                        value_coding = value_codeable.get("coding", [])
                        if value_coding:
                            value = value_coding[0].get("display", "")
                        else:
                            value = value_codeable.get("text", "")

            # Extract effective date/time
            effective_date = None
            effective_datetime = resource.get("effectiveDateTime")
            if effective_datetime:
                effective_date = effective_datetime.split("T")[0]
            else:
                effective_period = resource.get("effectivePeriod", {})
                effective_start = effective_period.get("start")
                if effective_start:
                    effective_date = effective_start.split("T")[0]

            # Extract status
            status = resource.get("status", "unknown")

            return {
                "id": observation_id,
                "code": code,
                "display": display,
                "value": value,
                "unit": unit,
                "effective_date": effective_date,
                "status": status
            }

        except Exception as e:
            print(f"Error parsing Observation resource: {str(e)}")
            return None


# Global FHIR client instance (singleton pattern)
_fhir_client: Optional[FHIRClient] = None


async def init_fhir() -> Optional[FHIRClient]:
    """
    Initialize the global FHIR client.

    Returns:
        FHIRClient instance or None if initialization fails
    """
    global _fhir_client

    try:
        _fhir_client = FHIRClient()
        print("FHIR client initialized successfully")
        return _fhir_client
    except Exception as e:
        print(f"Warning: Failed to initialize FHIR client: {e}")
        print("EHR integration may be limited")
        return None


async def close_fhir():
    """Close the global FHIR client."""
    global _fhir_client
    if _fhir_client:
        await _fhir_client.close()
        _fhir_client = None
        print("FHIR client closed")


def get_fhir_client() -> Optional[FHIRClient]:
    """
    Get the global FHIR client instance.

    Returns:
        FHIRClient instance or None if not initialized
    """
    return _fhir_client
