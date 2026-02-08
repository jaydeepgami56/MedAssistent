"""
DrugBank API client for comprehensive drug information and interaction checking.

This module provides a service class for interacting with the DrugBank API
(https://www.drugbank.com/), a comprehensive pharmaceutical knowledge base.

DrugBank provides:
- Detailed drug information (indications, pharmacology, etc.)
- Drug-drug interactions with clinical significance
- Contraindications and warnings
- Mechanism of action and metabolism

Note: DrugBank API requires an API key which may require institutional access.
For MVP development, mock data fallback is provided.
"""

from typing import Optional
import httpx
from backend.config import settings


class DrugBankClient:
    """
    Service class for DrugBank API operations.

    Handles:
    - Drug search by name
    - Drug-drug interaction checking
    - Contraindication retrieval
    - Error handling and rate limiting
    """

    def __init__(self, api_key: str = None, base_url: str = None):
        """
        Initialize DrugBank client.

        Args:
            api_key: DrugBank API key (defaults to settings.DRUGBANK_API_KEY)
            base_url: DrugBank API base URL (defaults to production API)
        """
        self.api_key = api_key or settings.DRUGBANK_API_KEY
        self.base_url = base_url or "https://api.drugbank.com/v1"

        # Setup HTTP client with authentication headers
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers=headers
        )

        if self.api_key:
            print(f"DrugBank client initialized with API key")
        else:
            print("Warning: DrugBank client initialized without API key - using mock data")

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def search_drug(self, name: str) -> dict:
        """
        Search for a drug by name in DrugBank.

        Args:
            name: Drug name (brand or generic)

        Returns:
            dict with:
                - drugbank_id: str - DrugBank identifier (e.g., "DB00945")
                - name: str - Drug name
                - description: str - Drug description
                - indication: str - Clinical indications
                - pharmacology: str - Mechanism of action
                - found: bool - Whether drug was found
                - error: str - Error message if lookup failed

        Example:
            result = await client.search_drug("aspirin")
            # {'drugbank_id': 'DB00945', 'name': 'Aspirin', 'found': True, ...}
        """
        if not name or not name.strip():
            return {
                "drugbank_id": None,
                "name": name,
                "found": False,
                "error": "Drug name cannot be empty"
            }

        # If no API key, return mock data
        if not self.api_key:
            return self._mock_search_drug(name)

        try:
            url = f"{self.base_url}/drugs"
            params = {"q": name.strip()}

            response = await self.client.get(url, params=params)
            response.raise_for_status()

            data = response.json()

            # DrugBank API returns list of matching drugs
            if not data or not isinstance(data, list) or len(data) == 0:
                return {
                    "drugbank_id": None,
                    "name": name,
                    "found": False,
                    "error": "Drug not found in DrugBank"
                }

            # Use first match (most relevant)
            drug = data[0]

            return {
                "drugbank_id": drug.get("drugbank_id"),
                "name": drug.get("name", name),
                "description": drug.get("description", ""),
                "indication": drug.get("indication", ""),
                "pharmacology": drug.get("pharmacology", ""),
                "found": True
            }

        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
            print(f"DrugBank API error for '{name}': {error_msg}")

            # Fallback to mock data on API errors
            return self._mock_search_drug(name)

        except httpx.RequestError as e:
            error_msg = f"Connection error: {str(e)}"
            print(f"DrugBank API connection error: {error_msg}")

            # Fallback to mock data on connection errors
            return self._mock_search_drug(name)

        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            print(f"DrugBank API unexpected error for '{name}': {error_msg}")

            # Fallback to mock data
            return self._mock_search_drug(name)

    async def get_interactions(self, drugbank_id: str) -> list[dict]:
        """
        Get known drug-drug interactions for a DrugBank drug.

        Args:
            drugbank_id: DrugBank identifier (e.g., "DB00945")

        Returns:
            list of dicts with:
                - drugbank_id: str - Interacting drug's DrugBank ID
                - name: str - Interacting drug name
                - description: str - Interaction description
                - severity: str - Clinical significance (critical/major/moderate/minor)

        Example:
            interactions = await client.get_interactions("DB00945")
            # [{'drugbank_id': 'DB01050', 'name': 'Ibuprofen',
            #   'description': 'Increased bleeding risk', 'severity': 'major'}]
        """
        if not drugbank_id:
            return []

        # If no API key, return mock data
        if not self.api_key:
            return self._mock_get_interactions(drugbank_id)

        try:
            url = f"{self.base_url}/drugs/{drugbank_id}/interactions"

            response = await self.client.get(url)
            response.raise_for_status()

            data = response.json()

            # Parse interaction data
            interactions = []
            for interaction in data:
                interactions.append({
                    "drugbank_id": interaction.get("drugbank_id"),
                    "name": interaction.get("name"),
                    "description": interaction.get("description", ""),
                    "severity": interaction.get("severity", "unknown").lower()
                })

            print(f"Found {len(interactions)} interactions for DrugBank ID {drugbank_id}")
            return interactions

        except httpx.HTTPStatusError as e:
            print(f"DrugBank interaction API error: HTTP {e.response.status_code}")
            return self._mock_get_interactions(drugbank_id)

        except httpx.RequestError as e:
            print(f"DrugBank API connection error: {str(e)}")
            return self._mock_get_interactions(drugbank_id)

        except Exception as e:
            print(f"DrugBank API unexpected error: {str(e)}")
            return self._mock_get_interactions(drugbank_id)

    async def get_contraindications(self, drugbank_id: str) -> list[dict]:
        """
        Get contraindications and warnings for a drug.

        Args:
            drugbank_id: DrugBank identifier (e.g., "DB00945")

        Returns:
            list of dicts with:
                - type: str - Type of contraindication (absolute/relative/warning)
                - condition: str - Condition or situation
                - description: str - Detailed description
                - severity: str - Clinical significance

        Example:
            contras = await client.get_contraindications("DB00945")
            # [{'type': 'absolute', 'condition': 'Hemophilia',
            #   'description': 'Aspirin inhibits platelet function', 'severity': 'critical'}]
        """
        if not drugbank_id:
            return []

        # If no API key, return mock data
        if not self.api_key:
            return self._mock_get_contraindications(drugbank_id)

        try:
            url = f"{self.base_url}/drugs/{drugbank_id}/contraindications"

            response = await self.client.get(url)
            response.raise_for_status()

            data = response.json()

            # Parse contraindication data
            contraindications = []
            for contra in data:
                contraindications.append({
                    "type": contra.get("type", "warning").lower(),
                    "condition": contra.get("condition", ""),
                    "description": contra.get("description", ""),
                    "severity": contra.get("severity", "unknown").lower()
                })

            print(f"Found {len(contraindications)} contraindications for DrugBank ID {drugbank_id}")
            return contraindications

        except httpx.HTTPStatusError as e:
            print(f"DrugBank contraindication API error: HTTP {e.response.status_code}")
            return self._mock_get_contraindications(drugbank_id)

        except httpx.RequestError as e:
            print(f"DrugBank API connection error: {str(e)}")
            return self._mock_get_contraindications(drugbank_id)

        except Exception as e:
            print(f"DrugBank API unexpected error: {str(e)}")
            return self._mock_get_contraindications(drugbank_id)

    # ==================== Mock Data Methods for Development ====================

    def _mock_search_drug(self, name: str) -> dict:
        """Mock drug search for development without API key."""
        # Common drug mock data
        mock_drugs = {
            "aspirin": {
                "drugbank_id": "DB00945",
                "name": "Aspirin",
                "description": "Nonsteroidal anti-inflammatory drug (NSAID) with analgesic, antipyretic, and antiplatelet properties",
                "indication": "Pain relief, fever reduction, cardiovascular prophylaxis",
                "pharmacology": "Irreversibly inhibits cyclooxygenase (COX-1 and COX-2)"
            },
            "ibuprofen": {
                "drugbank_id": "DB01050",
                "name": "Ibuprofen",
                "description": "Nonsteroidal anti-inflammatory drug (NSAID) with analgesic and antipyretic properties",
                "indication": "Pain, inflammation, fever",
                "pharmacology": "Reversibly inhibits cyclooxygenase (COX-1 and COX-2)"
            },
            "warfarin": {
                "drugbank_id": "DB00682",
                "name": "Warfarin",
                "description": "Anticoagulant that inhibits vitamin K-dependent clotting factors",
                "indication": "Anticoagulation for thromboembolic disorders",
                "pharmacology": "Inhibits vitamin K epoxide reductase"
            },
            "metformin": {
                "drugbank_id": "DB00331",
                "name": "Metformin",
                "description": "Biguanide antidiabetic agent",
                "indication": "Type 2 diabetes mellitus",
                "pharmacology": "Decreases hepatic glucose production and increases insulin sensitivity"
            },
            "lisinopril": {
                "drugbank_id": "DB00722",
                "name": "Lisinopril",
                "description": "ACE inhibitor for hypertension and heart failure",
                "indication": "Hypertension, heart failure, post-MI",
                "pharmacology": "Inhibits angiotensin-converting enzyme (ACE)"
            }
        }

        name_lower = name.strip().lower()
        if name_lower in mock_drugs:
            result = mock_drugs[name_lower].copy()
            result["found"] = True
            result["mock"] = True
            return result

        # Generic mock for unknown drugs
        return {
            "drugbank_id": f"DB{hash(name_lower) % 100000:05d}",
            "name": name.strip().title(),
            "description": f"Mock drug entry for {name}",
            "indication": "Mock indication",
            "pharmacology": "Mock mechanism",
            "found": True,
            "mock": True
        }

    def _mock_get_interactions(self, drugbank_id: str) -> list[dict]:
        """Mock drug interactions for development."""
        # Mock interactions based on DrugBank ID
        mock_interactions = {
            "DB00945": [  # Aspirin
                {
                    "drugbank_id": "DB00682",
                    "name": "Warfarin",
                    "description": "Increased risk of bleeding due to antiplatelet effects of aspirin combined with anticoagulation",
                    "severity": "major"
                },
                {
                    "drugbank_id": "DB01050",
                    "name": "Ibuprofen",
                    "description": "Increased risk of gastrointestinal bleeding and ulceration with combined NSAID use",
                    "severity": "moderate"
                }
            ],
            "DB00682": [  # Warfarin
                {
                    "drugbank_id": "DB00945",
                    "name": "Aspirin",
                    "description": "Increased risk of bleeding",
                    "severity": "major"
                },
                {
                    "drugbank_id": "DB01050",
                    "name": "Ibuprofen",
                    "description": "NSAIDs may increase bleeding risk with warfarin",
                    "severity": "major"
                }
            ]
        }

        interactions = mock_interactions.get(drugbank_id, [])
        for interaction in interactions:
            interaction["mock"] = True

        return interactions

    def _mock_get_contraindications(self, drugbank_id: str) -> list[dict]:
        """Mock contraindications for development."""
        mock_contraindications = {
            "DB00945": [  # Aspirin
                {
                    "type": "absolute",
                    "condition": "Hemophilia or bleeding disorders",
                    "description": "Aspirin inhibits platelet function and increases bleeding risk",
                    "severity": "critical"
                },
                {
                    "type": "relative",
                    "condition": "Active peptic ulcer disease",
                    "description": "NSAIDs increase risk of gastrointestinal bleeding",
                    "severity": "major"
                },
                {
                    "type": "warning",
                    "condition": "Reye syndrome risk in children",
                    "description": "Avoid aspirin in children with viral infections due to Reye syndrome risk",
                    "severity": "major"
                }
            ],
            "DB00682": [  # Warfarin
                {
                    "type": "absolute",
                    "condition": "Pregnancy",
                    "description": "Warfarin is teratogenic and crosses the placenta",
                    "severity": "critical"
                },
                {
                    "type": "absolute",
                    "condition": "Active major bleeding",
                    "description": "Contraindicated in uncontrolled bleeding",
                    "severity": "critical"
                }
            ]
        }

        contras = mock_contraindications.get(drugbank_id, [])
        for contra in contras:
            contra["mock"] = True

        return contras


# Global DrugBank client instance (singleton pattern)
_drugbank_client: Optional[DrugBankClient] = None


async def init_drugbank() -> DrugBankClient:
    """
    Initialize the global DrugBank client.

    Returns:
        DrugBankClient instance
    """
    global _drugbank_client

    try:
        _drugbank_client = DrugBankClient()
        print("DrugBank client initialized successfully")
        return _drugbank_client
    except Exception as e:
        print(f"Warning: Failed to initialize DrugBank client: {e}")
        print("Drug information may be limited to mock data")
        return None


async def close_drugbank():
    """Close the global DrugBank client."""
    global _drugbank_client
    if _drugbank_client:
        await _drugbank_client.close()
        _drugbank_client = None
        print("DrugBank client closed")


def get_drugbank_client() -> Optional[DrugBankClient]:
    """
    Get the global DrugBank client instance.

    Returns:
        DrugBankClient instance or None if not initialized
    """
    return _drugbank_client
