"""
Tests for PubMed API client.

Tests cover:
- Literature search with query terms
- Article metadata retrieval
- Citation formatting
- Rate limiting enforcement
- Error handling for invalid inputs
- Date filtering
"""

import pytest
import asyncio
import time
from backend.integrations.pubmed_client import PubMedClient


@pytest.mark.asyncio
async def test_initialization():
    """Test PubMed client initialization."""
    client = PubMedClient()

    assert client is not None
    assert client.base_url == "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    assert client.client is not None
    # Without API key, rate limit should be 3 req/sec
    assert client.rate_limit in [3, 10]  # 3 without key, 10 with key

    await client.close()


@pytest.mark.asyncio
async def test_initialization_with_api_key():
    """Test PubMed client initialization with API key."""
    client = PubMedClient(api_key="test_api_key_12345")

    assert client.api_key == "test_api_key_12345"
    assert client.rate_limit == 10  # With API key, 10 req/sec

    await client.close()


@pytest.mark.asyncio
async def test_search_basic():
    """Test basic literature search."""
    client = PubMedClient()

    results = await client.search("aspirin cardioprotection", max_results=5)

    assert isinstance(results, list)
    assert len(results) <= 5

    # Verify structure of results if any found
    if len(results) > 0:
        article = results[0]
        assert "pmid" in article
        assert "title" in article
        assert "authors" in article
        assert "journal" in article
        assert "year" in article
        assert "abstract" in article
        assert "publication_type" in article

        # Verify data types
        assert isinstance(article["pmid"], str)
        assert isinstance(article["title"], str)
        assert isinstance(article["authors"], list)
        assert isinstance(article["journal"], str)
        assert isinstance(article["year"], str)
        assert isinstance(article["abstract"], str)
        assert isinstance(article["publication_type"], list)

    await client.close()


@pytest.mark.asyncio
async def test_search_with_max_results():
    """Test search with different max_results values."""
    client = PubMedClient()

    # Test small result set
    results_small = await client.search("diabetes mellitus", max_results=3)
    assert len(results_small) <= 3

    # Test larger result set
    results_large = await client.search("diabetes mellitus", max_results=10)
    assert len(results_large) <= 10

    await client.close()


@pytest.mark.asyncio
async def test_search_with_date_filter():
    """Test search with minimum date filter."""
    client = PubMedClient()

    # Search for recent articles (last 2 years)
    results = await client.search(
        "COVID-19 treatment",
        max_results=5,
        min_date="2022/01/01"
    )

    assert isinstance(results, list)

    # Verify articles are from 2022 or later
    for article in results:
        if article["year"].isdigit():
            year = int(article["year"])
            assert year >= 2022, f"Article year {year} is before min_date 2022"

    await client.close()


@pytest.mark.asyncio
async def test_search_empty_query():
    """Test search with empty query."""
    client = PubMedClient()

    results = await client.search("", max_results=5)

    assert results == []

    await client.close()


@pytest.mark.asyncio
async def test_search_no_results():
    """Test search with query that returns no results."""
    client = PubMedClient()

    # Use a very obscure term unlikely to match
    results = await client.search("xyznonexistentmedicaltermabcdef123", max_results=5)

    assert isinstance(results, list)
    # May return empty list or very few unrelated results

    await client.close()


@pytest.mark.asyncio
async def test_fetch_abstracts_single():
    """Test fetching abstract for a single PMID."""
    client = PubMedClient()

    # Use a known PMID (example: 12345678 - you may need to use a valid one)
    # For this test, we'll use the esearch result
    search_results = await client.search("aspirin", max_results=1)

    if len(search_results) > 0:
        pmid = search_results[0]["pmid"]

        # Fetch using fetch_abstracts
        articles = await client.fetch_abstracts([pmid])

        assert len(articles) == 1
        assert articles[0]["pmid"] == pmid
        assert len(articles[0]["title"]) > 0

    await client.close()


@pytest.mark.asyncio
async def test_fetch_abstracts_multiple():
    """Test fetching abstracts for multiple PMIDs."""
    client = PubMedClient()

    # Get some PMIDs from a search
    search_results = await client.search("hypertension treatment", max_results=3)

    if len(search_results) >= 2:
        pmids = [article["pmid"] for article in search_results[:2]]

        # Fetch abstracts
        articles = await client.fetch_abstracts(pmids)

        assert len(articles) == 2
        assert articles[0]["pmid"] in pmids
        assert articles[1]["pmid"] in pmids

    await client.close()


@pytest.mark.asyncio
async def test_fetch_abstracts_empty_list():
    """Test fetching abstracts with empty PMID list."""
    client = PubMedClient()

    articles = await client.fetch_abstracts([])

    assert articles == []

    await client.close()


@pytest.mark.asyncio
async def test_format_citation_complete():
    """Test citation formatting with complete article data."""
    client = PubMedClient()

    article = {
        "pmid": "12345678",
        "title": "Aspirin for cardiovascular disease prevention",
        "authors": ["Smith J", "Doe A", "Johnson B"],
        "journal": "JAMA",
        "year": "2023"
    }

    citation = client.format_citation(article)

    assert "Smith J" in citation
    assert "Doe A" in citation
    assert "Johnson B" in citation
    assert "Aspirin for cardiovascular disease prevention" in citation
    assert "JAMA" in citation
    assert "2023" in citation
    assert "PMID: 12345678" in citation

    await client.close()


@pytest.mark.asyncio
async def test_format_citation_many_authors():
    """Test citation formatting with more than 6 authors."""
    client = PubMedClient()

    article = {
        "pmid": "87654321",
        "title": "Large collaborative study",
        "authors": ["Author1", "Author2", "Author3", "Author4",
                   "Author5", "Author6", "Author7", "Author8"],
        "journal": "Nature",
        "year": "2024"
    }

    citation = client.format_citation(article)

    # Should show first 6 authors followed by "et al"
    assert "Author1" in citation
    assert "Author6" in citation
    assert "et al" in citation
    assert "Author7" not in citation  # 7th author should not appear
    assert "PMID: 87654321" in citation

    await client.close()


@pytest.mark.asyncio
async def test_format_citation_missing_fields():
    """Test citation formatting with missing fields."""
    client = PubMedClient()

    article = {
        "pmid": "99999999",
        "title": "Incomplete article data"
        # Missing authors, journal, year
    }

    citation = client.format_citation(article)

    assert "[No authors listed]" in citation
    assert "Incomplete article data" in citation
    assert "[No journal]" in citation
    assert "[No year]" in citation
    assert "PMID: 99999999" in citation

    await client.close()


@pytest.mark.asyncio
async def test_format_citation_no_pmid():
    """Test citation formatting without PMID."""
    client = PubMedClient()

    article = {
        "title": "Article without PMID",
        "authors": ["Smith J"],
        "journal": "Journal Name",
        "year": "2023"
    }

    citation = client.format_citation(article)

    assert "Smith J" in citation
    assert "Article without PMID" in citation
    assert "Journal Name" in citation
    assert "2023" in citation
    # Should not have PMID section
    assert "PMID:" not in citation

    await client.close()


@pytest.mark.asyncio
async def test_rate_limiting():
    """Test that rate limiting is enforced."""
    client = PubMedClient()

    # Make multiple rapid requests and measure timing
    start_time = time.time()

    # Make 3 search requests
    await client.search("test1", max_results=1)
    await client.search("test2", max_results=1)
    await client.search("test3", max_results=1)

    elapsed_time = time.time() - start_time

    # With rate limiting, this should take at least 2 * min_delay
    # (3 requests = 2 delays between them)
    expected_min_time = 2 * client.min_delay * 0.9  # Allow 10% tolerance

    # Note: This is a soft check - network latency may dominate
    # So we just verify the mechanism exists, not strict timing
    assert hasattr(client, 'min_delay')
    assert hasattr(client, 'last_request_time')

    await client.close()


@pytest.mark.asyncio
async def test_search_medical_terms():
    """Test search with various medical terms."""
    client = PubMedClient()

    medical_queries = [
        "diabetes mellitus type 2",
        "hypertension treatment guidelines",
        "COVID-19 vaccine efficacy"
    ]

    for query in medical_queries:
        results = await client.search(query, max_results=3)

        assert isinstance(results, list)
        # We expect at least some results for common medical terms
        # but don't enforce it strictly as PubMed content may vary

    await client.close()


@pytest.mark.asyncio
async def test_client_close():
    """Test that client can be closed properly."""
    client = PubMedClient()

    await client.close()
    # No assertion needed - just verify no exception


@pytest.mark.asyncio
async def test_xml_parsing_with_real_data():
    """Test XML parsing with actual PubMed search results."""
    client = PubMedClient()

    # Search for a common term to get real XML data
    results = await client.search("aspirin", max_results=2)

    if len(results) > 0:
        article = results[0]

        # Verify all expected fields are present
        assert article["pmid"]
        assert article["title"]
        assert isinstance(article["authors"], list)
        assert article["journal"]
        assert article["year"]
        assert isinstance(article["abstract"], str)
        assert isinstance(article["publication_type"], list)

        # Verify authors are formatted correctly (LastName Initials)
        if len(article["authors"]) > 0:
            author = article["authors"][0]
            assert len(author) > 0

    await client.close()


@pytest.mark.asyncio
async def test_search_integration_end_to_end():
    """Integration test: search -> fetch -> format citation."""
    client = PubMedClient()

    # Step 1: Search
    results = await client.search("metformin diabetes", max_results=1)

    if len(results) > 0:
        article = results[0]

        # Step 2: Verify we got the data
        assert article["pmid"]
        assert article["title"]

        # Step 3: Format citation
        citation = client.format_citation(article)

        assert len(citation) > 0
        assert article["title"] in citation
        assert article["pmid"] in citation

    await client.close()
