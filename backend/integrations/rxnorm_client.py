"""
RxNorm API client for drug name resolution and drug-drug interaction checking.

This module provides a service class for interacting with the RxNorm REST API
(https://rxnav.nlm.nih.gov/REST) maintained by the National Library of Medicine.

RxNorm provides:
- Drug name normalization and CUI (Concept Unique Identifier) resolution
- Drug-drug interaction detection
- Drug relationships and ingredient information
"""

from typing import Optional
import httpx
from backend.config import settings


class RxNormClient:
    """
    Service class for RxNorm API operations.

    Handles:
    - Drug name resolution to RxCUI (RxNorm Concept Unique Identifier)
    - Drug-drug interaction checking
    - Error handling for API failures and rate limiting
    """

    def __init__(self, base_url: str = None):
        """
        Initialize RxNorm client.

        Args:
            base_url: RxNorm API base URL (defaults to settings.RXNORM_API_URL)
        """
        self.base_url = (base_url or settings.RXNORM_API_URL).rstrip('/')
        self.client = httpx.AsyncClient(timeout=30.0)
        print(f"RxNorm client initialized: {self.base_url}")

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def resolve_drug_name(self, name: str) -> dict:
        """
        Resolve a drug name to RxCUI and normalized name.

        Calls GET /rxcui.json?name={name} to find RxNorm concept identifier.

        Args:
            name: Drug name (brand or generic, e.g., "aspirin", "Tylenol")

        Returns:
            dict with:
                - rxcui: str - RxNorm Concept Unique Identifier (e.g., "1191")
                - name: str - Normalized drug name
                - found: bool - Whether drug was found in RxNorm
                - error: str - Error message if lookup failed

        Example:
            result = await client.resolve_drug_name("aspirin")
            # {'rxcui': '1191', 'name': 'aspirin', 'found': True}
        """
        if not name or not name.strip():
            return {
                "rxcui": None,
                "name": name,
                "found": False,
                "error": "Drug name cannot be empty"
            }

        try:
            url = f"{self.base_url}/rxcui.json"
            params = {"name": name.strip()}

            response = await self.client.get(url, params=params)
            response.raise_for_status()

            data = response.json()

            # RxNorm API response format: {"idGroup": {"rxnormId": ["1191"]}}
            id_group = data.get("idGroup", {})
            rxcui_list = id_group.get("rxnormId", [])

            if not rxcui_list:
                return {
                    "rxcui": None,
                    "name": name,
                    "found": False,
                    "error": "Drug not found in RxNorm"
                }

            # Use first RxCUI (most relevant match)
            rxcui = rxcui_list[0]

            # Get normalized name by looking up the RxCUI
            normalized_name = await self._get_drug_name(rxcui)

            return {
                "rxcui": rxcui,
                "name": normalized_name or name,
                "found": True
            }

        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
            print(f"RxNorm API error for '{name}': {error_msg}")
            return {
                "rxcui": None,
                "name": name,
                "found": False,
                "error": error_msg
            }
        except httpx.RequestError as e:
            error_msg = f"Connection error: {str(e)}"
            print(f"RxNorm API connection error: {error_msg}")
            return {
                "rxcui": None,
                "name": name,
                "found": False,
                "error": error_msg
            }
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            print(f"RxNorm API unexpected error for '{name}': {error_msg}")
            return {
                "rxcui": None,
                "name": name,
                "found": False,
                "error": error_msg
            }

    async def _get_drug_name(self, rxcui: str) -> Optional[str]:
        """
        Get normalized drug name for an RxCUI.

        Args:
            rxcui: RxNorm Concept Unique Identifier

        Returns:
            Normalized drug name or None if not found
        """
        try:
            url = f"{self.base_url}/rxcui/{rxcui}/property.json"
            params = {"propName": "RxNorm Name"}

            response = await self.client.get(url, params=params)
            response.raise_for_status()

            data = response.json()
            prop_concept = data.get("propConceptGroup", {})
            prop_concept_list = prop_concept.get("propConcept", [])

            if prop_concept_list:
                return prop_concept_list[0].get("propValue")

            return None

        except Exception as e:
            print(f"Failed to get drug name for RxCUI {rxcui}: {e}")
            return None

    async def get_interactions(self, rxcui_list: list[str]) -> list[dict]:
        """
        Get pairwise drug-drug interactions for a list of RxCUIs.

        Calls GET /interaction/list.json to find interactions between drugs.

        Args:
            rxcui_list: List of RxNorm Concept Unique Identifiers

        Returns:
            list of dicts with:
                - drug_a: dict - {rxcui, name}
                - drug_b: dict - {rxcui, name}
                - severity: str - Severity level from RxNorm
                - description: str - Interaction description
                - source: str - Data source (e.g., "ONCHigh")

        Example:
            interactions = await client.get_interactions(["1191", "5640"])
            # [{'drug_a': {'rxcui': '1191', 'name': 'aspirin'},
            #   'drug_b': {'rxcui': '5640', 'name': 'ibuprofen'},
            #   'severity': 'high',
            #   'description': 'Increased risk of bleeding',
            #   'source': 'ONCHigh'}]
        """
        if not rxcui_list or len(rxcui_list) < 2:
            return []

        try:
            # RxNorm interaction API expects space-separated list of RxCUIs
            rxcuis = "+".join(rxcui_list)
            url = f"{self.base_url}/interaction/list.json"
            params = {"rxcuis": rxcuis}

            response = await self.client.get(url, params=params)
            response.raise_for_status()

            data = response.json()

            # Parse interaction data
            interactions = []
            full_interaction_list = data.get("fullInteractionTypeGroup", [])

            for interaction_type in full_interaction_list:
                source_name = interaction_type.get("sourceName", "Unknown")
                full_interaction = interaction_type.get("fullInteractionType", [])

                for interaction in full_interaction:
                    # Get drug pair info
                    min_concepts = interaction.get("minConcept", [])
                    if len(min_concepts) < 2:
                        continue

                    drug_a = {
                        "rxcui": min_concepts[0].get("rxcui"),
                        "name": min_concepts[0].get("name")
                    }
                    drug_b = {
                        "rxcui": min_concepts[1].get("rxcui"),
                        "name": min_concepts[1].get("name")
                    }

                    # Get interaction details
                    interaction_pairs = interaction.get("interactionPair", [])
                    for pair in interaction_pairs:
                        description = pair.get("description", "")
                        severity = pair.get("severity", "N/A")

                        interactions.append({
                            "drug_a": drug_a,
                            "drug_b": drug_b,
                            "severity": severity.lower() if severity != "N/A" else "unknown",
                            "description": description,
                            "source": source_name
                        })

            print(f"Found {len(interactions)} interactions for {len(rxcui_list)} drugs")
            return interactions

        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
            print(f"RxNorm interaction API error: {error_msg}")
            return []
        except httpx.RequestError as e:
            print(f"RxNorm API connection error: {str(e)}")
            return []
        except Exception as e:
            print(f"RxNorm API unexpected error: {str(e)}")
            return []


# Global RxNorm client instance (singleton pattern)
_rxnorm_client: Optional[RxNormClient] = None


async def init_rxnorm() -> RxNormClient:
    """
    Initialize the global RxNorm client.

    Returns:
        RxNormClient instance
    """
    global _rxnorm_client

    try:
        _rxnorm_client = RxNormClient()
        print("RxNorm client initialized successfully")
        return _rxnorm_client
    except Exception as e:
        print(f"Warning: Failed to initialize RxNorm client: {e}")
        print("Drug interaction checking may be limited")
        return None


async def close_rxnorm():
    """Close the global RxNorm client."""
    global _rxnorm_client
    if _rxnorm_client:
        await _rxnorm_client.close()
        _rxnorm_client = None
        print("RxNorm client closed")


def get_rxnorm_client() -> Optional[RxNormClient]:
    """
    Get the global RxNorm client instance.

    Returns:
        RxNormClient instance or None if not initialized
    """
    return _rxnorm_client
