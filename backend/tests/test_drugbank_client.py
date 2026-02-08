"""
Tests for DrugBank API client.

Tests cover:
- Drug search by name
- Drug-drug interaction checking
- Contraindication retrieval
- Mock data fallback when no API key
- Error handling
"""

import pytest
from backend.integrations.drugbank_client import DrugBankClient


@pytest.mark.asyncio
async def test_initialization_without_api_key():
    """Test DrugBank client initialization without API key."""
    client = DrugBankClient()

    assert client is not None
    # API key may be None or empty string depending on env config
    assert not client.api_key or client.api_key == ""
    assert client.client is not None

    await client.close()


@pytest.mark.asyncio
async def test_search_drug_aspirin_mock():
    """Test searching for aspirin (should use mock data without API key)."""
    client = DrugBankClient()

    result = await client.search_drug("aspirin")

    assert result is not None
    assert result["found"] is True
    assert result["drugbank_id"] == "DB00945"
    assert "aspirin" in result["name"].lower()
    assert "mock" in result  # Mock data indicator

    await client.close()


@pytest.mark.asyncio
async def test_search_drug_ibuprofen_mock():
    """Test searching for ibuprofen (mock data)."""
    client = DrugBankClient()

    result = await client.search_drug("ibuprofen")

    assert result is not None
    assert result["found"] is True
    assert result["drugbank_id"] == "DB01050"
    assert "ibuprofen" in result["name"].lower()
    assert "mock" in result

    await client.close()


@pytest.mark.asyncio
async def test_search_drug_warfarin_mock():
    """Test searching for warfarin (mock data)."""
    client = DrugBankClient()

    result = await client.search_drug("warfarin")

    assert result is not None
    assert result["found"] is True
    assert result["drugbank_id"] == "DB00682"
    assert "warfarin" in result["name"].lower()
    assert "description" in result
    assert "indication" in result
    assert "pharmacology" in result

    await client.close()


@pytest.mark.asyncio
async def test_search_drug_case_insensitive():
    """Test that drug search is case-insensitive."""
    client = DrugBankClient()

    result1 = await client.search_drug("ASPIRIN")
    result2 = await client.search_drug("aspirin")
    result3 = await client.search_drug("Aspirin")

    assert result1["found"] is True
    assert result2["found"] is True
    assert result3["found"] is True
    assert result1["drugbank_id"] == result2["drugbank_id"] == result3["drugbank_id"]

    await client.close()


@pytest.mark.asyncio
async def test_search_drug_empty():
    """Test error handling for empty drug name."""
    client = DrugBankClient()

    result = await client.search_drug("")

    assert result is not None
    assert result["found"] is False
    assert "error" in result
    assert "empty" in result["error"].lower()

    await client.close()


@pytest.mark.asyncio
async def test_search_drug_unknown_returns_generic_mock():
    """Test that unknown drugs return generic mock data."""
    client = DrugBankClient()

    result = await client.search_drug("unknowndrugxyz123")

    assert result is not None
    assert result["found"] is True
    assert result["drugbank_id"] is not None
    assert "unknowndrugxyz123" in result["name"].lower()
    assert "mock" in result

    await client.close()


@pytest.mark.asyncio
async def test_get_interactions_aspirin_mock():
    """Test getting interactions for aspirin (mock data)."""
    client = DrugBankClient()

    interactions = await client.get_interactions("DB00945")

    assert isinstance(interactions, list)
    assert len(interactions) > 0

    # Verify structure
    interaction = interactions[0]
    assert "drugbank_id" in interaction
    assert "name" in interaction
    assert "description" in interaction
    assert "severity" in interaction
    assert "mock" in interaction

    await client.close()


@pytest.mark.asyncio
async def test_get_interactions_warfarin_mock():
    """Test getting interactions for warfarin (mock data)."""
    client = DrugBankClient()

    interactions = await client.get_interactions("DB00682")

    assert isinstance(interactions, list)
    assert len(interactions) > 0

    # Warfarin should have multiple interactions
    assert any("aspirin" in i["name"].lower() for i in interactions)

    await client.close()


@pytest.mark.asyncio
async def test_get_interactions_empty_id():
    """Test that empty DrugBank ID returns no interactions."""
    client = DrugBankClient()

    interactions = await client.get_interactions("")
    assert interactions == []

    await client.close()


@pytest.mark.asyncio
async def test_get_interactions_unknown_id():
    """Test that unknown DrugBank ID returns empty list."""
    client = DrugBankClient()

    interactions = await client.get_interactions("DB99999")
    assert isinstance(interactions, list)
    assert len(interactions) == 0

    await client.close()


@pytest.mark.asyncio
async def test_get_contraindications_aspirin_mock():
    """Test getting contraindications for aspirin (mock data)."""
    client = DrugBankClient()

    contras = await client.get_contraindications("DB00945")

    assert isinstance(contras, list)
    assert len(contras) > 0

    # Verify structure
    contra = contras[0]
    assert "type" in contra
    assert "condition" in contra
    assert "description" in contra
    assert "severity" in contra
    assert "mock" in contra

    # Aspirin should have bleeding disorder contraindication
    assert any("bleeding" in c["condition"].lower() or "hemophilia" in c["condition"].lower()
               for c in contras)

    await client.close()


@pytest.mark.asyncio
async def test_get_contraindications_warfarin_mock():
    """Test getting contraindications for warfarin (mock data)."""
    client = DrugBankClient()

    contras = await client.get_contraindications("DB00682")

    assert isinstance(contras, list)
    assert len(contras) > 0

    # Warfarin should have pregnancy contraindication
    assert any("pregnancy" in c["condition"].lower() for c in contras)

    # Should have critical severity contraindications
    assert any(c["severity"] == "critical" for c in contras)

    await client.close()


@pytest.mark.asyncio
async def test_get_contraindications_empty_id():
    """Test that empty DrugBank ID returns no contraindications."""
    client = DrugBankClient()

    contras = await client.get_contraindications("")
    assert contras == []

    await client.close()


@pytest.mark.asyncio
async def test_get_contraindications_unknown_id():
    """Test that unknown DrugBank ID returns empty list."""
    client = DrugBankClient()

    contras = await client.get_contraindications("DB99999")
    assert isinstance(contras, list)
    assert len(contras) == 0

    await client.close()


@pytest.mark.asyncio
async def test_multiple_common_drugs():
    """Test searching for multiple common drugs."""
    client = DrugBankClient()

    common_drugs = ["aspirin", "ibuprofen", "warfarin", "metformin", "lisinopril"]

    for drug_name in common_drugs:
        result = await client.search_drug(drug_name)
        assert result is not None
        assert result["found"] is True
        assert result["drugbank_id"] is not None
        assert result["name"] is not None

    await client.close()


@pytest.mark.asyncio
async def test_client_close():
    """Test that client can be closed properly."""
    client = DrugBankClient()

    await client.close()
    # No assertion needed - just verify no exception
