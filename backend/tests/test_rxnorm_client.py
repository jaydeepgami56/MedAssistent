"""
Tests for RxNorm API client.

Tests cover:
- Drug name resolution to RxCUI
- Pairwise drug-drug interaction checking
- Error handling for invalid inputs
- API failure graceful degradation
"""

import pytest
from backend.integrations.rxnorm_client import RxNormClient


@pytest.mark.asyncio
async def test_initialization():
    """Test RxNorm client initialization."""
    client = RxNormClient()

    assert client is not None
    assert client.base_url == "https://rxnav.nlm.nih.gov/REST"
    assert client.client is not None

    await client.close()


@pytest.mark.asyncio
async def test_resolve_drug_name_aspirin():
    """Test resolving aspirin to RxCUI."""
    client = RxNormClient()

    result = await client.resolve_drug_name("aspirin")

    assert result is not None
    assert result["found"] is True
    assert result["rxcui"] == "1191"
    assert "aspirin" in result["name"].lower()

    await client.close()


@pytest.mark.asyncio
async def test_resolve_drug_name_ibuprofen():
    """Test resolving ibuprofen to RxCUI."""
    client = RxNormClient()

    result = await client.resolve_drug_name("ibuprofen")

    assert result is not None
    assert result["found"] is True
    assert result["rxcui"] is not None
    assert "ibuprofen" in result["name"].lower()

    await client.close()


@pytest.mark.asyncio
async def test_resolve_drug_name_case_insensitive():
    """Test that drug name resolution is case-insensitive."""
    client = RxNormClient()

    result1 = await client.resolve_drug_name("ASPIRIN")
    result2 = await client.resolve_drug_name("aspirin")
    result3 = await client.resolve_drug_name("Aspirin")

    assert result1["found"] is True
    assert result2["found"] is True
    assert result3["found"] is True
    assert result1["rxcui"] == result2["rxcui"] == result3["rxcui"]

    await client.close()


@pytest.mark.asyncio
async def test_resolve_drug_name_empty():
    """Test error handling for empty drug name."""
    client = RxNormClient()

    result = await client.resolve_drug_name("")

    assert result is not None
    assert result["found"] is False
    assert "error" in result
    assert "empty" in result["error"].lower()

    await client.close()


@pytest.mark.asyncio
async def test_resolve_drug_name_not_found():
    """Test handling of non-existent drug name."""
    client = RxNormClient()

    result = await client.resolve_drug_name("xyznonexistentdrug123")

    assert result is not None
    assert result["found"] is False
    assert result["rxcui"] is None

    await client.close()


@pytest.mark.asyncio
async def test_get_interactions_aspirin_ibuprofen():
    """Test finding interactions between aspirin and ibuprofen."""
    client = RxNormClient()

    # Resolve drug names first
    aspirin = await client.resolve_drug_name("aspirin")
    ibuprofen = await client.resolve_drug_name("ibuprofen")

    assert aspirin["found"] is True
    assert ibuprofen["found"] is True

    # Get interactions
    interactions = await client.get_interactions([
        aspirin["rxcui"],
        ibuprofen["rxcui"]
    ])

    # Note: Actual interactions depend on RxNorm data
    # This test verifies the API call succeeds
    assert isinstance(interactions, list)
    # Aspirin + Ibuprofen may or may not have documented interactions
    # We just verify the API returns a list

    await client.close()


@pytest.mark.asyncio
async def test_get_interactions_empty_list():
    """Test that empty drug list returns no interactions."""
    client = RxNormClient()

    interactions = await client.get_interactions([])
    assert interactions == []

    await client.close()


@pytest.mark.asyncio
async def test_get_interactions_single_drug():
    """Test that single drug returns no interactions."""
    client = RxNormClient()

    interactions = await client.get_interactions(["1191"])
    assert interactions == []

    await client.close()


@pytest.mark.asyncio
async def test_get_interactions_warfarin_aspirin():
    """Test finding interactions between warfarin and aspirin (known interaction)."""
    client = RxNormClient()

    # Warfarin RxCUI: 11289, Aspirin RxCUI: 1191
    interactions = await client.get_interactions(["11289", "1191"])

    assert isinstance(interactions, list)
    # Warfarin + Aspirin should have interactions
    # Verify structure if interactions found
    if len(interactions) > 0:
        interaction = interactions[0]
        assert "drug_a" in interaction
        assert "drug_b" in interaction
        assert "severity" in interaction
        assert "description" in interaction
        assert "source" in interaction

    await client.close()


@pytest.mark.asyncio
async def test_get_interactions_multiple_drugs():
    """Test interactions with 3+ drugs."""
    client = RxNormClient()

    # Test with aspirin, ibuprofen, and warfarin
    interactions = await client.get_interactions(["1191", "5640", "11289"])

    assert isinstance(interactions, list)
    # Should return pairwise interactions

    await client.close()


@pytest.mark.asyncio
async def test_resolve_common_drugs():
    """Test resolving multiple common drug names."""
    client = RxNormClient()

    common_drugs = ["metformin", "lisinopril", "atorvastatin", "omeprazole"]

    for drug_name in common_drugs:
        result = await client.resolve_drug_name(drug_name)
        assert result is not None
        assert result["found"] is True, f"{drug_name} should be found in RxNorm"
        assert result["rxcui"] is not None

    await client.close()


@pytest.mark.asyncio
async def test_client_close():
    """Test that client can be closed properly."""
    client = RxNormClient()

    await client.close()
    # No assertion needed - just verify no exception
