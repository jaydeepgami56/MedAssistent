"""
Tests for Research Agent.

Tests the ResearchAgent's ability to search medical literature, synthesize
evidence, and provide research assistance to clinicians.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from backend.agents.research_agent import (
    ResearchAgent,
    init_research_agent,
    get_research_agent,
    EVIDENCE_LEVELS
)


@pytest.fixture
def mock_anthropic():
    """Mock Anthropic client."""
    with patch("backend.agents.research_agent.Anthropic") as mock:
        client = Mock()
        mock.return_value = client
        yield client


@pytest.fixture
def mock_pubmed_client():
    """Mock PubMed client."""
    mock_client = Mock()
    mock_client.search = AsyncMock(return_value=[])
    mock_client.format_citation = Mock(return_value="Test citation")
    return mock_client


@pytest.fixture
def research_agent(mock_anthropic, mock_pubmed_client):
    """Create ResearchAgent instance with mocked dependencies."""
    with patch("backend.agents.research_agent.get_pubmed_client", return_value=mock_pubmed_client):
        agent = ResearchAgent(anthropic_api_key="test_key")
        return agent


class TestResearchAgentInitialization:
    """Test Research Agent initialization."""

    def test_init_creates_agent(self, mock_anthropic, mock_pubmed_client):
        """Test that agent initializes with correct properties."""
        with patch("backend.agents.research_agent.get_pubmed_client", return_value=mock_pubmed_client):
            agent = ResearchAgent(anthropic_api_key="test_key")

            assert agent.agent_id == "research"
            assert agent.name == "Research Agent"
            assert agent.icon == "📚"
            assert agent.color == "#10b981"
            assert "guideline_search" in agent.skills
            assert "evidence_synthesis" in agent.skills
            assert "trial_match" in agent.skills
            assert "literature_review" in agent.skills
            assert "Claude API" in agent.models_used
            assert "PubMed API" in agent.models_used

    def test_singleton_pattern(self, mock_anthropic, mock_pubmed_client):
        """Test singleton pattern works."""
        with patch("backend.agents.research_agent.get_pubmed_client", return_value=mock_pubmed_client):
            agent1 = init_research_agent("test_key")
            agent2 = get_research_agent()

            assert agent1 is agent2
            assert agent2.agent_id == "research"


class TestGuidelineSearch:
    """Test guideline_search skill."""

    @pytest.mark.asyncio
    async def test_guideline_search_success(self, research_agent, mock_anthropic, mock_pubmed_client):
        """Test successful guideline search."""
        # Mock Claude response for query formulation
        mock_response = Mock()
        mock_response.content = [Mock(text="diabetes treatment guidelines")]
        mock_anthropic.messages.create.return_value = mock_response

        # Mock PubMed search results
        mock_pubmed_client.search.return_value = [
            {
                "pmid": "12345678",
                "title": "Diabetes Management Guidelines 2024",
                "authors": ["Smith J", "Doe A"],
                "journal": "JAMA",
                "year": "2024",
                "abstract": "Guidelines for diabetes management...",
                "publication_type": ["Guideline", "Review"]
            }
        ]

        # Mock synthesis summary
        mock_summary_response = Mock()
        mock_summary_response.content = [Mock(text="Found 1 article addressing diabetes treatment.")]

        result = await research_agent.execute_skill(
            "guideline_search",
            {
                "clinical_question": "What are the latest guidelines for diabetes treatment?",
                "max_results": 5,
                "min_year": 2020
            }
        )

        assert "results" in result
        assert len(result["results"]) == 1
        assert result["results"][0]["pmid"] == "12345678"
        assert result["results"][0]["evidence_level"] == "Review"
        assert "search_query_used" in result
        assert result["search_query_used"] == "diabetes treatment guidelines"
        assert "disclaimer" in result

    @pytest.mark.asyncio
    async def test_guideline_search_no_question(self, research_agent):
        """Test guideline search with no clinical question."""
        result = await research_agent.execute_skill(
            "guideline_search",
            {}
        )

        assert "error" in result
        assert result["error"] == "clinical_question is required"

    @pytest.mark.asyncio
    async def test_guideline_search_no_pubmed_client(self, mock_anthropic):
        """Test guideline search when PubMed client is not available."""
        with patch("backend.agents.research_agent.get_pubmed_client", return_value=None):
            agent = ResearchAgent(anthropic_api_key="test_key")

            # Mock Claude response
            mock_response = Mock()
            mock_response.content = [Mock(text="diabetes guidelines")]
            mock_anthropic.messages.create.return_value = mock_response

            result = await agent.execute_skill(
                "guideline_search",
                {"clinical_question": "diabetes treatment"}
            )

            assert "error" in result
            assert "PubMed client not available" in result["error"]


class TestEvidenceLevel:
    """Test evidence level determination."""

    def test_meta_analysis_highest(self, research_agent):
        """Test that meta-analysis is recognized as highest evidence."""
        level = research_agent._determine_evidence_level(
            ["Meta-Analysis", "Journal Article"]
        )
        assert level == "Meta-Analysis"

    def test_rct_evidence(self, research_agent):
        """Test RCT evidence level."""
        level = research_agent._determine_evidence_level(
            ["Randomized Controlled Trial", "Clinical Trial"]
        )
        assert level == "Randomized Controlled Trial"

    def test_cohort_study_evidence(self, research_agent):
        """Test cohort study evidence level."""
        level = research_agent._determine_evidence_level(
            ["Cohort Study", "Journal Article"]
        )
        assert level == "Cohort Study"

    def test_case_report_evidence(self, research_agent):
        """Test case report evidence level."""
        level = research_agent._determine_evidence_level(
            ["Case Reports"]
        )
        assert level == "Case Reports"

    def test_review_evidence(self, research_agent):
        """Test review evidence level."""
        level = research_agent._determine_evidence_level(
            ["Review", "Journal Article"]
        )
        assert level == "Review"

    def test_default_journal_article(self, research_agent):
        """Test default evidence level."""
        level = research_agent._determine_evidence_level([])
        assert level == "Journal Article"

    def test_evidence_level_hierarchy(self):
        """Test that evidence levels are properly ordered."""
        assert EVIDENCE_LEVELS["Meta-Analysis"] < EVIDENCE_LEVELS["Randomized Controlled Trial"]
        assert EVIDENCE_LEVELS["Randomized Controlled Trial"] < EVIDENCE_LEVELS["Cohort Study"]
        assert EVIDENCE_LEVELS["Cohort Study"] < EVIDENCE_LEVELS["Case Reports"]
        assert EVIDENCE_LEVELS["Case Reports"] < EVIDENCE_LEVELS["Journal Article"]


class TestEvidenceSynthesis:
    """Test evidence_synthesis skill."""

    @pytest.mark.asyncio
    async def test_evidence_synthesis_success(self, research_agent, mock_anthropic, mock_pubmed_client):
        """Test successful evidence synthesis."""
        articles = [
            {
                "pmid": "11111111",
                "title": "Study 1",
                "authors": ["Author A"],
                "journal": "Journal A",
                "year": "2023",
                "abstract": "Abstract 1...",
                "evidence_level": "Meta-Analysis"
            },
            {
                "pmid": "22222222",
                "title": "Study 2",
                "authors": ["Author B"],
                "journal": "Journal B",
                "year": "2023",
                "abstract": "Abstract 2...",
                "evidence_level": "Randomized Controlled Trial"
            }
        ]

        # Mock Claude response
        mock_response = Mock()
        mock_response.content = [Mock(text='''```json
{
  "synthesis": "Evidence suggests that treatment is effective [PMID: 11111111]. Multiple RCTs confirm this finding [PMID: 22222222].",
  "key_findings": [
    "Finding 1 [PMID: 11111111]",
    "Finding 2 [PMID: 22222222]"
  ]
}
```''')]
        mock_anthropic.messages.create.return_value = mock_response

        result = await research_agent.execute_skill(
            "evidence_synthesis",
            {
                "articles": articles,
                "clinical_question": "Is treatment effective?"
            }
        )

        assert "synthesis" in result
        assert "evidence suggests" in result["synthesis"].lower()
        assert "key_findings" in result
        assert len(result["key_findings"]) == 2
        assert "citations" in result
        assert "disclaimer" in result

    @pytest.mark.asyncio
    async def test_evidence_synthesis_no_articles(self, research_agent):
        """Test evidence synthesis with no articles."""
        result = await research_agent.execute_skill(
            "evidence_synthesis",
            {"articles": []}
        )

        assert "error" in result
        assert "No articles provided" in result["error"]

    @pytest.mark.asyncio
    async def test_synthesis_with_focus(self, research_agent, mock_anthropic, mock_pubmed_client):
        """Test evidence synthesis with specific focus area."""
        articles = [{
            "pmid": "12345678",
            "title": "Test Study",
            "authors": ["Test A"],
            "journal": "Test J",
            "year": "2024",
            "abstract": "Test abstract",
            "evidence_level": "RCT"
        }]

        # Mock Claude response
        mock_response = Mock()
        mock_response.content = [Mock(text='{"synthesis": "Focused synthesis", "key_findings": []}')]
        mock_anthropic.messages.create.return_value = mock_response

        result = await research_agent.execute_skill(
            "evidence_synthesis",
            {
                "articles": articles,
                "clinical_question": "Test question",
                "synthesis_focus": "treatment efficacy"
            }
        )

        assert "synthesis" in result


class TestTrialMatch:
    """Test trial_match skill."""

    @pytest.mark.asyncio
    async def test_trial_match_placeholder(self, research_agent):
        """Test that trial match returns placeholder message."""
        result = await research_agent.execute_skill(
            "trial_match",
            {
                "condition": "diabetes",
                "location": "California",
                "age": 45
            }
        )

        assert "trials" in result
        assert len(result["trials"]) == 0
        assert "message" in result
        assert "not yet implemented" in result["message"]
        assert "disclaimer" in result


class TestLiteratureReview:
    """Test literature_review skill."""

    @pytest.mark.asyncio
    async def test_literature_review_combines_search_and_synthesis(
        self,
        research_agent,
        mock_anthropic,
        mock_pubmed_client
    ):
        """Test that literature review combines search and synthesis."""
        # Mock search results
        mock_pubmed_client.search.return_value = [{
            "pmid": "12345678",
            "title": "Test Article",
            "authors": ["Test A"],
            "journal": "Test J",
            "year": "2024",
            "abstract": "Test abstract",
            "publication_type": ["Meta-Analysis"]
        }]

        # Mock Claude responses
        mock_query_response = Mock()
        mock_query_response.content = [Mock(text="test query")]

        mock_synthesis_response = Mock()
        mock_synthesis_response.content = [Mock(text='{"synthesis": "Test synthesis", "key_findings": ["Finding 1"]}')]

        mock_anthropic.messages.create.side_effect = [
            mock_query_response,
            mock_synthesis_response
        ]

        result = await research_agent.execute_skill(
            "literature_review",
            {"clinical_question": "Test question"}
        )

        assert "search_results" in result
        assert "synthesis" in result
        assert "key_findings" in result
        assert "citations" in result
        assert "disclaimer" in result


class TestChat:
    """Test chat functionality."""

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not pytest.importorskip("anthropic", reason="Anthropic library required"),
        reason="Requires Anthropic API key"
    )
    async def test_chat_streams_response(self, research_agent, mock_anthropic):
        """Test that chat streams response tokens."""
        # Mock streaming response
        mock_stream = Mock()
        mock_stream.__enter__ = Mock(return_value=mock_stream)
        mock_stream.__exit__ = Mock(return_value=None)
        mock_stream.text_stream = ["Hello", " ", "researcher"]

        mock_anthropic.messages.stream.return_value = mock_stream

        tokens = []
        async for token in research_agent.chat(
            "What are the latest diabetes guidelines?",
            {}
        ):
            tokens.append(token)

        response = "".join(tokens)
        assert "Hello researcher" in response
        assert "Evidence synthesis" in response or "clinician verification required" in response

    @pytest.mark.asyncio
    async def test_chat_includes_disclaimer(self, research_agent, mock_anthropic):
        """Test that chat response includes disclaimer."""
        mock_stream = Mock()
        mock_stream.__enter__ = Mock(return_value=mock_stream)
        mock_stream.__exit__ = Mock(return_value=None)
        mock_stream.text_stream = ["Test response"]

        mock_anthropic.messages.stream.return_value = mock_stream

        tokens = []
        async for token in research_agent.chat("Test question", {}):
            tokens.append(token)

        response = "".join(tokens)
        assert "clinician verification required" in response.lower() or "evidence synthesis" in response.lower()


class TestSkillRouting:
    """Test skill routing."""

    @pytest.mark.asyncio
    async def test_unknown_skill_raises_error(self, research_agent):
        """Test that unknown skill raises ValueError."""
        with pytest.raises(ValueError, match="Unknown skill"):
            await research_agent.execute_skill("unknown_skill", {})  # type: ignore

    @pytest.mark.asyncio
    async def test_all_skills_routable(self, research_agent):
        """Test that all declared skills are routable."""
        for skill in research_agent.skills:
            # Should not raise ValueError
            try:
                await research_agent.execute_skill(skill, {"clinical_question": "test"})
            except ValueError as e:
                if "Unknown skill" in str(e):
                    pytest.fail(f"Skill {skill} is declared but not routable")


class TestAuditLogging:
    """Test audit logging."""

    def test_guideline_search_logs_audit(self, research_agent, mock_anthropic, mock_pubmed_client, capsys):
        """Test that guideline search logs audit trail."""
        import asyncio

        # Mock responses
        mock_response = Mock()
        mock_response.content = [Mock(text="test query")]
        mock_anthropic.messages.create.return_value = mock_response

        mock_pubmed_client.search.return_value = [{
            "pmid": "12345",
            "title": "Test",
            "authors": [],
            "journal": "Test J",
            "year": "2024",
            "abstract": "Abstract",
            "publication_type": []
        }]

        asyncio.run(research_agent.execute_skill(
            "guideline_search",
            {"clinical_question": "test question"}
        ))

        captured = capsys.readouterr()
        assert "[AUDIT]" in captured.out
        assert "research" in captured.out
        assert "guideline_search" in captured.out


class TestGetInfo:
    """Test get_info method."""

    def test_get_info_returns_metadata(self, research_agent):
        """Test that get_info returns complete agent metadata."""
        info = research_agent.get_info()

        assert info["agent_id"] == "research"
        assert info["name"] == "Research Agent"
        assert info["icon"] == "📚"
        assert info["color"] == "#10b981"
        assert "guideline_search" in info["skills"]
        assert "Claude API" in info["models_used"]
        assert "status" in info
        assert "queue" in info
