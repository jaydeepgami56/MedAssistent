"""
Research Agent - Medical literature search and evidence synthesis.

Implements PubMed literature search, guideline retrieval, and evidence synthesis
using MedGemma 27B for query formulation and summarization. Provides clinicians with
up-to-date research evidence and clinical trial information.
"""

import logging
import json
from typing import AsyncIterator, Optional, Any
from backend.llm_client import get_llm_client, LLM_MODEL

from backend.agents.base_agent import BaseAgent
from backend.integrations.pubmed_client import get_pubmed_client

logger = logging.getLogger(__name__)

# DISCLAIMER - MUST be included in ALL outputs
DISCLAIMER = "Evidence synthesis — clinician verification required"

# Evidence level hierarchy for filtering
EVIDENCE_LEVELS = {
    "Meta-Analysis": 1,
    "Systematic Review": 2,
    "Randomized Controlled Trial": 3,
    "Clinical Trial": 4,
    "Observational Study": 5,
    "Cohort Study": 6,
    "Case-Control Study": 7,
    "Case Reports": 8,
    "Review": 9,
    "Journal Article": 10
}


class ResearchAgent(BaseAgent):
    """
    Research Agent for medical literature search and evidence synthesis.

    Provides PubMed literature search, guideline retrieval, evidence synthesis,
    and clinical trial matching. Uses MedGemma 27B via LM Studio for query formulation and synthesis,
    PubMed API for literature retrieval.
    """

    def __init__(self):
        """
        Initialize Research Agent.
        """
        super().__init__(
            agent_id="research",
            name="Research Agent",
            skills=[
                "guideline_search",
                "evidence_synthesis",
                "trial_match",
                "literature_review"
            ],
            models_used=["MedGemma 27B (LM Studio)", "PubMed API"],
            color="#10b981",  # Green
            icon="📚",
            status="Active",
            queue=0
        )

        self.llm_client = get_llm_client()
        self._pubmed_client = get_pubmed_client()

        if not self._pubmed_client:
            logger.warning("PubMed client not available - literature search will be limited")

        logger.info("Research Agent initialized successfully")

    async def execute_skill(self, skill_name: str, params: dict) -> dict:
        """
        Execute a specific research skill.

        Args:
            skill_name: One of: guideline_search, evidence_synthesis, trial_match, literature_review
            params: Skill-specific parameters

        Returns:
            dict: Skill execution result

        Raises:
            ValueError: If skill_name is not recognized
        """
        if skill_name not in self.skills:
            raise ValueError(f"Unknown skill: {skill_name}. Available: {self.skills}")

        if skill_name == "guideline_search":
            return await self._guideline_search(params)
        elif skill_name == "evidence_synthesis":
            return await self._evidence_synthesis(params)
        elif skill_name == "trial_match":
            return await self._trial_match(params)
        elif skill_name == "literature_review":
            return await self._literature_review(params)
        else:
            raise ValueError(f"Skill not implemented: {skill_name}")

    async def _guideline_search(self, params: dict) -> dict:
        """
        Search medical literature for clinical guidelines and evidence.

        Uses Claude to formulate optimal PubMed search query, then searches
        PubMed and filters results by recency and evidence level.

        Args:
            params: dict with:
                - clinical_question: str - Clinical question to research
                - max_results: int - Maximum results to return (default: 10)
                - min_year: int - Minimum publication year (default: 2019)

        Returns:
            dict with:
                - results: list of article dicts with evidence_level
                - search_query_used: str - The PubMed query that was executed
                - summary: str - Brief summary of findings
                - disclaimer: str
        """
        clinical_question = params.get("clinical_question", "")
        max_results = params.get("max_results", 10)
        min_year = params.get("min_year", 2019)

        if not clinical_question:
            return {
                "error": "clinical_question is required",
                "results": [],
                "search_query_used": "",
                "summary": "",
                "disclaimer": DISCLAIMER
            }

        try:
            # Step 1: Use MedGemma 27B to formulate optimal PubMed search query
            search_query = await self._formulate_search_query(clinical_question)

            # Step 2: Search PubMed
            if not self._pubmed_client:
                return {
                    "error": "PubMed client not available",
                    "results": [],
                    "search_query_used": search_query,
                    "summary": "PubMed API is not configured. Please check PUBMED_API_KEY.",
                    "disclaimer": DISCLAIMER
                }

            min_date = f"{min_year}/01/01"
            raw_articles = await self._pubmed_client.search(
                query=search_query,
                max_results=max_results,
                min_date=min_date
            )

            # Step 3: Add evidence levels and filter
            articles_with_evidence = []
            for article in raw_articles:
                evidence_level = self._determine_evidence_level(
                    article.get("publication_type", [])
                )
                article_with_level = {
                    "pmid": article.get("pmid", ""),
                    "title": article.get("title", ""),
                    "authors": article.get("authors", []),
                    "journal": article.get("journal", ""),
                    "year": article.get("year", ""),
                    "abstract": article.get("abstract", ""),
                    "evidence_level": evidence_level,
                    "publication_type": article.get("publication_type", [])
                }
                articles_with_evidence.append(article_with_level)

            # Step 4: Sort by evidence level (lower number = higher quality)
            articles_with_evidence.sort(
                key=lambda x: EVIDENCE_LEVELS.get(x["evidence_level"], 999)
            )

            # Step 5: Generate brief summary
            summary = await self._generate_search_summary(
                clinical_question,
                articles_with_evidence
            )

            # Log audit trail
            self.log_audit(
                request=f"guideline_search: {clinical_question}",
                model="MedGemma 27B + PubMed API",
                confidence=0.85,
                action=f"found_{len(articles_with_evidence)}_articles"
            )

            return {
                "results": articles_with_evidence,
                "search_query_used": search_query,
                "summary": summary,
                "disclaimer": DISCLAIMER
            }

        except Exception as e:
            logger.error(f"Error in guideline_search: {str(e)}")
            return {
                "error": str(e),
                "results": [],
                "search_query_used": "",
                "summary": "",
                "disclaimer": DISCLAIMER
            }

    async def _formulate_search_query(self, clinical_question: str) -> str:
        """
        Use MedGemma 27B to formulate optimal PubMed search query.

        Args:
            clinical_question: Clinical question in plain language

        Returns:
            Optimized PubMed search query string
        """
        prompt = f"""You are a medical librarian expert in PubMed search strategies.

Given this clinical question:
"{clinical_question}"

Generate an optimal PubMed search query that will retrieve the most relevant, high-quality evidence.

Requirements:
- Use MeSH terms where appropriate
- Include relevant keywords and synonyms
- Prioritize guidelines, meta-analyses, and RCTs
- Use PubMed search syntax (AND, OR, [MeSH], etc.)

Return ONLY the search query string, no explanation."""

        try:
            response = self.llm_client.chat.completions.create(
                model=LLM_MODEL,
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )

            # Extract query from response
            query = response.choices[0].message.content.strip()  # type: ignore

            # Remove quotes if present
            query = query.strip('"\'')

            logger.info(f"Formulated PubMed query: {query}")
            return query

        except Exception as e:
            logger.error(f"Error formulating search query: {str(e)}")
            # Fallback to simple query
            return clinical_question

    def _determine_evidence_level(self, publication_types: list[str]) -> str:
        """
        Determine evidence level based on publication types.

        Args:
            publication_types: List of publication type strings from PubMed

        Returns:
            Evidence level string (e.g., "Meta-Analysis", "RCT", etc.)
        """
        if not publication_types:
            return "Journal Article"

        # Check for highest quality evidence first
        for pub_type in publication_types:
            if "Meta-Analysis" in pub_type:
                return "Meta-Analysis"
            elif "Systematic Review" in pub_type:
                return "Systematic Review"
            elif "Randomized Controlled Trial" in pub_type:
                return "Randomized Controlled Trial"
            elif "Clinical Trial" in pub_type:
                return "Clinical Trial"
            elif "Observational Study" in pub_type:
                return "Observational Study"
            elif "Cohort Study" in pub_type or "Cohort Studies" in pub_type:
                return "Cohort Study"
            elif "Case-Control Study" in pub_type or "Case-Control Studies" in pub_type:
                return "Case-Control Study"
            elif "Case Reports" in pub_type:
                return "Case Reports"
            elif "Review" in pub_type:
                return "Review"

        return "Journal Article"

    async def _generate_search_summary(
        self,
        clinical_question: str,
        articles: list[dict]
    ) -> str:
        """
        Generate brief summary of search results.

        Args:
            clinical_question: Original clinical question
            articles: List of articles with evidence levels

        Returns:
            Brief summary string
        """
        if not articles:
            return "No recent articles found matching the search criteria."

        # Count by evidence level
        evidence_counts: dict[str, int] = {}
        for article in articles:
            level = article["evidence_level"]
            evidence_counts[level] = evidence_counts.get(level, 0) + 1

        # Build summary
        summary_parts = [
            f"Found {len(articles)} articles addressing: {clinical_question}."
        ]

        # Add evidence breakdown
        if evidence_counts:
            evidence_breakdown = ", ".join([
                f"{count} {level}" for level, count in evidence_counts.items()
            ])
            summary_parts.append(f"Evidence includes: {evidence_breakdown}.")

        return " ".join(summary_parts)

    async def _evidence_synthesis(self, params: dict) -> dict:
        """
        Synthesize findings from multiple articles into concise summary.

        Uses Claude to analyze multiple PubMed results and create a coherent
        synthesis with citations.

        Args:
            params: dict with:
                - articles: list of article dicts (from guideline_search)
                - clinical_question: str - Original clinical question
                - synthesis_focus: str - Optional focus area (e.g., "treatment efficacy")

        Returns:
            dict with:
                - synthesis: str - Synthesized summary with citations
                - key_findings: list[str] - Bullet point key findings
                - citations: list[str] - Formatted citations
                - disclaimer: str
        """
        articles = params.get("articles", [])
        clinical_question = params.get("clinical_question", "")
        synthesis_focus = params.get("synthesis_focus", "")

        if not articles:
            return {
                "error": "No articles provided for synthesis",
                "synthesis": "",
                "key_findings": [],
                "citations": [],
                "disclaimer": DISCLAIMER
            }

        try:
            # Step 1: Build synthesis prompt with article summaries
            synthesis_prompt = self._build_synthesis_prompt(
                articles,
                clinical_question,
                synthesis_focus
            )

            # Step 2: Use Claude to synthesize evidence
            response = self.llm_client.chat.completions.create(
                model=LLM_MODEL,
                max_tokens=2000,
                messages=[{"role": "user", "content": synthesis_prompt}]
            )

            content = response.choices[0].message.content  # type: ignore

            # Step 3: Parse JSON response
            synthesis_data = self._parse_synthesis_response(content)

            # Step 4: Format citations
            citations = []
            if self._pubmed_client:
                for article in articles[:10]:  # Limit to first 10
                    citation = self._pubmed_client.format_citation(article)
                    citations.append(citation)

            # Log audit trail
            self.log_audit(
                request=f"evidence_synthesis: {len(articles)} articles",
                model="MedGemma 27B",
                confidence=0.80,
                action="synthesis_complete"
            )

            return {
                "synthesis": synthesis_data.get("synthesis", ""),
                "key_findings": synthesis_data.get("key_findings", []),
                "citations": citations,
                "disclaimer": DISCLAIMER
            }

        except Exception as e:
            logger.error(f"Error in evidence_synthesis: {str(e)}")
            return {
                "error": str(e),
                "synthesis": "",
                "key_findings": [],
                "citations": [],
                "disclaimer": DISCLAIMER
            }

    def _build_synthesis_prompt(
        self,
        articles: list[dict],
        clinical_question: str,
        synthesis_focus: str
    ) -> str:
        """
        Build prompt for evidence synthesis.

        Args:
            articles: List of article dicts
            clinical_question: Original question
            synthesis_focus: Optional focus area

        Returns:
            Prompt string for Claude
        """
        # Build article summaries
        article_summaries = []
        for i, article in enumerate(articles[:10], 1):  # Limit to first 10
            summary = f"""
Article {i} (PMID: {article.get('pmid', 'N/A')}, Evidence: {article.get('evidence_level', 'N/A')}):
Title: {article.get('title', 'N/A')}
Authors: {', '.join(article.get('authors', [])[:3])}
Year: {article.get('year', 'N/A')}
Abstract: {article.get('abstract', 'N/A')[:500]}...
""".strip()
            article_summaries.append(summary)

        articles_text = "\n\n".join(article_summaries)

        focus_instruction = ""
        if synthesis_focus:
            focus_instruction = f"\nFocus specifically on: {synthesis_focus}"

        prompt = f"""You are a medical research analyst synthesizing evidence from multiple studies.

Clinical Question: {clinical_question}{focus_instruction}

Review these articles and synthesize the key findings:

{articles_text}

Provide a synthesis in JSON format:
{{
  "synthesis": "A 2-3 paragraph synthesis of the evidence. Use citations like [PMID: 12345678]. Present findings as 'evidence suggests...' not as direct recommendations. Note areas of consensus and disagreement.",
  "key_findings": [
    "Key finding 1 with citation [PMID: xxx]",
    "Key finding 2 with citation [PMID: xxx]",
    "Key finding 3 with citation [PMID: xxx]"
  ]
}}

Requirements:
- Cite PMIDs for all claims
- Note evidence quality (meta-analysis > RCT > cohort > case)
- Present as "evidence suggests..." not as recommendations
- Identify consensus and conflicting findings
- Be objective and balanced

Return ONLY the JSON, no other text."""

        return prompt

    def _parse_synthesis_response(self, content: str) -> dict[str, Any]:
        """
        Parse synthesis response from Claude.

        Args:
            content: Raw response text

        Returns:
            Parsed synthesis dict
        """
        try:
            # Extract JSON from markdown if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            synthesis_data = json.loads(content)
            return synthesis_data

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse synthesis JSON: {str(e)}")
            # Fallback: return content as synthesis
            return {
                "synthesis": content,
                "key_findings": []
            }

    async def _trial_match(self, params: dict) -> dict:
        """
        Match patient to relevant clinical trials (placeholder).

        Future implementation will search ClinicalTrials.gov API.

        Args:
            params: dict with:
                - condition: str - Medical condition
                - location: str - Geographic location (optional)
                - age: int - Patient age (optional)

        Returns:
            dict with:
                - trials: list of trial dicts
                - message: str
                - disclaimer: str
        """
        return {
            "trials": [],
            "message": "Clinical trial matching is not yet implemented. Future versions will integrate with ClinicalTrials.gov API.",
            "disclaimer": DISCLAIMER
        }

    async def _literature_review(self, params: dict) -> dict:
        """
        Perform comprehensive literature review (combines search + synthesis).

        Args:
            params: dict with:
                - clinical_question: str
                - max_results: int (default: 10)
                - min_year: int (default: 2019)

        Returns:
            dict with both search results and synthesis
        """
        # Step 1: Search
        search_result = await self._guideline_search(params)

        if "error" in search_result or not search_result.get("results"):
            return search_result

        # Step 2: Synthesize
        synthesis_params = {
            "articles": search_result["results"],
            "clinical_question": params.get("clinical_question", "")
        }
        synthesis_result = await self._evidence_synthesis(synthesis_params)

        # Step 3: Combine
        return {
            "search_results": search_result["results"],
            "search_query_used": search_result["search_query_used"],
            "search_summary": search_result["summary"],
            "synthesis": synthesis_result.get("synthesis", ""),
            "key_findings": synthesis_result.get("key_findings", []),
            "citations": synthesis_result.get("citations", []),
            "disclaimer": DISCLAIMER
        }

    async def chat(self, message: str, context: dict) -> AsyncIterator[str]:
        """
        Stream chat responses for research questions.

        Args:
            message: User message
            context: Conversation context

        Yields:
            str: Response tokens
        """
        system_prompt = """You are the Research Agent in MedAssist AI, a clinical decision support system.

Your role:
- Search medical literature using PubMed
- Synthesize evidence from multiple studies
- Provide evidence-based summaries with citations
- Help clinicians find clinical guidelines and research

Guidelines:
- Always cite sources with PMIDs
- Present evidence as "evidence suggests..." not as direct recommendations
- Note the quality of evidence (meta-analysis > RCT > cohort > case)
- Identify areas of consensus and conflicting findings
- Be objective and balanced
- Include disclaimer: "Evidence synthesis — clinician verification required"

Available skills:
- guideline_search: Search PubMed for clinical guidelines
- evidence_synthesis: Synthesize findings from multiple articles
- literature_review: Comprehensive search + synthesis
- trial_match: Match patients to clinical trials (coming soon)

You assist clinicians with research — you never make clinical decisions."""

        try:
            # Stream response from LLM
            stream = self.llm_client.chat.completions.create(
                model=LLM_MODEL,
                max_tokens=2000,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                stream=True,
            )
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

            # Add disclaimer at the end
            yield f"\n\n---\n{DISCLAIMER}"

        except Exception as e:
            logger.error(f"Error in research chat: {str(e)}")
            yield f"Error: {str(e)}\n\n{DISCLAIMER}"


# Global Research Agent instance (singleton pattern)
_research_agent: Optional[ResearchAgent] = None


def init_research_agent() -> ResearchAgent:
    """
    Initialize the global Research Agent.

    Returns:
        ResearchAgent instance
    """
    global _research_agent
    _research_agent = ResearchAgent()
    return _research_agent


def get_research_agent() -> Optional[ResearchAgent]:
    """
    Get the global Research Agent instance.

    Returns:
        ResearchAgent instance or None if not initialized
    """
    return _research_agent
