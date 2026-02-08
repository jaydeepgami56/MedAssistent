"""
PubMed API client for medical literature search.

This module provides a service class for interacting with the NCBI E-utilities API
(https://eutils.ncbi.nlm.nih.gov/entrez/eutils/) for PubMed literature search.

PubMed provides:
- Medical literature search across millions of biomedical citations
- Full article metadata including abstracts, authors, journals
- Citation formatting for clinical documentation
"""

from typing import Optional, Any
import asyncio
import httpx
from backend.config import settings


class PubMedClient:
    """
    Service class for PubMed API operations.

    Handles:
    - Literature search using esearch.fcgi and efetch.fcgi
    - Article metadata retrieval (title, authors, abstract, journal, year)
    - Citation formatting
    - NCBI rate limiting (3 req/sec without API key, 10 req/sec with key)
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize PubMed client.

        Args:
            api_key: NCBI API key (defaults to settings.PUBMED_API_KEY)
        """
        self.api_key = api_key or settings.PUBMED_API_KEY
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
        self.client = httpx.AsyncClient(timeout=30.0)

        # Rate limiting: 3 req/sec without key, 10 req/sec with key
        self.rate_limit = 10 if self.api_key else 3
        self.min_delay = 1.0 / self.rate_limit  # Minimum seconds between requests
        self.last_request_time: float = 0.0

        print(f"PubMed client initialized (rate limit: {self.rate_limit} req/sec)")

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def _rate_limit_delay(self):
        """
        Enforce rate limiting between API requests.

        Waits if necessary to maintain the rate limit.
        """
        import time
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time

        if time_since_last_request < self.min_delay:
            wait_time = self.min_delay - time_since_last_request
            await asyncio.sleep(wait_time)

        self.last_request_time = time.time()

    async def search(
        self,
        query: str,
        max_results: int = 10,
        min_date: Optional[str] = None
    ) -> list[dict]:
        """
        Search PubMed for articles matching the query.

        Calls NCBI esearch.fcgi to get PMIDs, then efetch.fcgi to get article metadata.

        Args:
            query: Search query (e.g., "diabetes treatment guidelines")
            max_results: Maximum number of results to return (default: 10)
            min_date: Minimum publication date in YYYY/MM/DD format (e.g., "2020/01/01")

        Returns:
            list of dicts with:
                - pmid: str - PubMed ID
                - title: str - Article title
                - authors: list[str] - List of author names
                - journal: str - Journal name
                - year: str - Publication year
                - abstract: str - Article abstract
                - publication_type: list[str] - Publication types

        Example:
            articles = await client.search("aspirin cardioprotection", max_results=5)
            # [{'pmid': '12345678', 'title': 'Aspirin for cardiovascular disease',
            #   'authors': ['Smith J', 'Doe A'], 'journal': 'JAMA', 'year': '2023',
            #   'abstract': '...', 'publication_type': ['Journal Article', 'Review']}]
        """
        if not query or not query.strip():
            return []

        try:
            # Step 1: Search for PMIDs using esearch
            pmids = await self._esearch(query, max_results, min_date)

            if not pmids:
                print(f"No results found for query: '{query}'")
                return []

            # Step 2: Fetch article metadata using efetch
            articles = await self.fetch_abstracts(pmids)

            print(f"Found {len(articles)} articles for query: '{query}'")
            return articles

        except Exception as e:
            print(f"PubMed search error for '{query}': {str(e)}")
            return []

    async def _esearch(
        self,
        query: str,
        max_results: int,
        min_date: Optional[str]
    ) -> list[str]:
        """
        Search PubMed and retrieve PMIDs.

        Args:
            query: Search query
            max_results: Maximum number of PMIDs to return
            min_date: Minimum publication date (YYYY/MM/DD)

        Returns:
            List of PMIDs as strings
        """
        await self._rate_limit_delay()

        url = f"{self.base_url}/esearch.fcgi"
        params: dict[str, str | int] = {
            "db": "pubmed",
            "term": query,
            "retmax": max_results,
            "retmode": "json"
        }

        # Add API key if available
        if self.api_key:
            params["api_key"] = self.api_key

        # Add date filter if specified
        if min_date:
            params["mindate"] = min_date
            params["datetype"] = "pdat"  # Publication date

        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()

            data = response.json()

            # Extract PMIDs from response
            esearch_result = data.get("esearchresult", {})
            pmids = esearch_result.get("idlist", [])

            return pmids

        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
            print(f"PubMed esearch API error: {error_msg}")
            return []
        except httpx.RequestError as e:
            print(f"PubMed esearch connection error: {str(e)}")
            return []
        except Exception as e:
            print(f"PubMed esearch unexpected error: {str(e)}")
            return []

    async def fetch_abstracts(self, pmids: list[str]) -> list[dict]:
        """
        Fetch full article metadata for a list of PMIDs.

        Calls NCBI efetch.fcgi to retrieve complete article information.

        Args:
            pmids: List of PubMed IDs

        Returns:
            list of dicts with article metadata:
                - pmid: str
                - title: str
                - authors: list[str]
                - journal: str
                - year: str
                - abstract: str
                - publication_type: list[str]

        Example:
            articles = await client.fetch_abstracts(["12345678", "87654321"])
        """
        if not pmids:
            return []

        await self._rate_limit_delay()

        url = f"{self.base_url}/efetch.fcgi"
        params: dict[str, str] = {
            "db": "pubmed",
            "id": ",".join(pmids),
            "retmode": "xml",
            "rettype": "abstract"
        }

        # Add API key if available
        if self.api_key:
            params["api_key"] = self.api_key

        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()

            # Parse XML response
            articles = self._parse_pubmed_xml(response.text)

            return articles

        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
            print(f"PubMed efetch API error: {error_msg}")
            return []
        except httpx.RequestError as e:
            print(f"PubMed efetch connection error: {str(e)}")
            return []
        except Exception as e:
            print(f"PubMed efetch unexpected error: {str(e)}")
            return []

    def _parse_pubmed_xml(self, xml_text: str) -> list[dict]:
        """
        Parse PubMed XML response to extract article metadata.

        Args:
            xml_text: Raw XML response from efetch

        Returns:
            List of article dictionaries
        """
        import xml.etree.ElementTree as ET

        articles = []

        try:
            root = ET.fromstring(xml_text)

            # Iterate through each PubmedArticle
            for article_elem in root.findall(".//PubmedArticle"):
                article_data: dict[str, Any] = {}

                # Extract PMID
                pmid_elem = article_elem.find(".//PMID")
                article_data["pmid"] = pmid_elem.text if pmid_elem is not None else ""

                # Extract title
                title_elem = article_elem.find(".//ArticleTitle")
                article_data["title"] = title_elem.text if title_elem is not None else ""

                # Extract authors
                authors = []
                author_list = article_elem.find(".//AuthorList")
                if author_list is not None:
                    for author_elem in author_list.findall("Author"):
                        last_name_elem = author_elem.find("LastName")
                        fore_name_elem = author_elem.find("ForeName")
                        initials_elem = author_elem.find("Initials")

                        if last_name_elem is not None and last_name_elem.text:
                            last_name = last_name_elem.text
                            initials = (initials_elem.text if initials_elem is not None
                                      else (fore_name_elem.text[0] if fore_name_elem is not None and fore_name_elem.text else ""))
                            authors.append(f"{last_name} {initials}".strip())
                        else:
                            collective_name_elem = author_elem.find("CollectiveName")
                            if collective_name_elem is not None and collective_name_elem.text:
                                authors.append(collective_name_elem.text)

                article_data["authors"] = authors

                # Extract journal
                journal_elem = article_elem.find(".//Journal/Title")
                article_data["journal"] = journal_elem.text if journal_elem is not None else ""

                # Extract year
                year_elem = article_elem.find(".//PubDate/Year")
                if year_elem is None:
                    # Try MedlineDate format (e.g., "2023 Jan-Feb")
                    medline_date_elem = article_elem.find(".//PubDate/MedlineDate")
                    if medline_date_elem is not None and medline_date_elem.text:
                        year_text = medline_date_elem.text.split()[0]
                        article_data["year"] = year_text
                    else:
                        article_data["year"] = ""
                else:
                    article_data["year"] = year_elem.text if year_elem.text else ""

                # Extract abstract
                abstract_texts = []
                abstract_elem = article_elem.find(".//Abstract")
                if abstract_elem is not None:
                    for abstract_text_elem in abstract_elem.findall("AbstractText"):
                        # Handle structured abstracts with labels
                        label = abstract_text_elem.get("Label", "")
                        text = abstract_text_elem.text or ""

                        if label:
                            abstract_texts.append(f"{label}: {text}")
                        else:
                            abstract_texts.append(text)

                article_data["abstract"] = " ".join(abstract_texts).strip()

                # Extract publication types
                pub_types = []
                pub_type_list = article_elem.find(".//PublicationTypeList")
                if pub_type_list is not None:
                    for pub_type_elem in pub_type_list.findall("PublicationType"):
                        if pub_type_elem.text:
                            pub_types.append(pub_type_elem.text)

                article_data["publication_type"] = pub_types

                articles.append(article_data)

        except ET.ParseError as e:
            print(f"XML parsing error: {str(e)}")
            return []
        except Exception as e:
            print(f"Error parsing PubMed XML: {str(e)}")
            return []

        return articles

    def format_citation(self, article: dict) -> str:
        """
        Format article metadata as a standard citation string.

        Uses Vancouver citation style commonly used in medical literature.

        Args:
            article: Article dict with pmid, title, authors, journal, year

        Returns:
            Formatted citation string

        Example:
            citation = client.format_citation({
                'authors': ['Smith J', 'Doe A'],
                'title': 'Aspirin for cardiovascular disease prevention',
                'journal': 'JAMA',
                'year': '2023',
                'pmid': '12345678'
            })
            # "Smith J, Doe A. Aspirin for cardiovascular disease prevention.
            #  JAMA. 2023. PMID: 12345678"
        """
        try:
            # Format authors (first 6, then "et al." if more)
            authors = article.get("authors", [])
            if not authors:
                author_str = "[No authors listed]"
            elif len(authors) <= 6:
                author_str = ", ".join(authors)
            else:
                author_str = ", ".join(authors[:6]) + ", et al"

            # Get other fields
            title = article.get("title", "[No title]")
            journal = article.get("journal", "[No journal]")
            year = article.get("year", "[No year]")
            pmid = article.get("pmid", "")

            # Build citation (Vancouver style)
            citation_parts = [
                f"{author_str}.",
                f"{title}.",
                f"{journal}.",
                f"{year}."
            ]

            if pmid:
                citation_parts.append(f"PMID: {pmid}")

            return " ".join(citation_parts)

        except Exception as e:
            print(f"Error formatting citation: {str(e)}")
            return f"[Citation formatting error for PMID: {article.get('pmid', 'unknown')}]"


# Global PubMed client instance (singleton pattern)
_pubmed_client: Optional[PubMedClient] = None


async def init_pubmed() -> Optional[PubMedClient]:
    """
    Initialize the global PubMed client.

    Returns:
        PubMedClient instance or None if initialization fails
    """
    global _pubmed_client

    try:
        _pubmed_client = PubMedClient()
        print("PubMed client initialized successfully")
        return _pubmed_client
    except Exception as e:
        print(f"Warning: Failed to initialize PubMed client: {e}")
        print("Literature search may be limited")
        return None


async def close_pubmed():
    """Close the global PubMed client."""
    global _pubmed_client
    if _pubmed_client:
        await _pubmed_client.close()
        _pubmed_client = None
        print("PubMed client closed")


def get_pubmed_client() -> Optional[PubMedClient]:
    """
    Get the global PubMed client instance.

    Returns:
        PubMedClient instance or None if not initialized
    """
    return _pubmed_client
