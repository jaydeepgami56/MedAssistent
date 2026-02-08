# Ralph Progress Log

This file tracks progress across iterations. Agents update this file
after each iteration and it's included in prompts for context.

## Codebase Patterns (Study These First)

### Agent Implementation Pattern
- All agents inherit from `BaseAgent` (backend/agents/base_agent.py)
- Required constructor params: agent_id, name, skills (list), models_used (list), color (hex), icon (emoji)
- Must implement: `execute_skill(skill_name, params)` and `chat(message, context)`
- Use singleton pattern with `init_<agent>_agent()` and `get_<agent>_agent()` functions
- Always include disclaimer in outputs (e.g., "Evidence synthesis — clinician verification required")
- Use `self.log_audit()` to log all operations for HIPAA compliance

### Evidence-Based Output Pattern
- All clinical outputs must present as "evidence suggests..." not as direct recommendations
- Always include citations with PMIDs, authors, journal, year
- Note evidence quality levels (meta-analysis > RCT > cohort > case)
- Include safety disclaimers requiring clinician verification

### Integration Client Pattern
- External API clients use singleton pattern with `get_<service>_client()`
- Initialize clients with `init_<service>()` function
- Implement rate limiting for external APIs (PubMed: 3 req/sec without key, 10 req/sec with key)
- Handle errors gracefully and return empty results rather than raising exceptions

---

## [2026-02-08] - US-022
- **Status**: Already implemented in previous iteration
- Verified Research Agent implementation with PubMed search and evidence synthesis
- All acceptance criteria met:
  - ✅ ResearchAgent class inherits from BaseAgent with correct properties (agent_id='research', icon='📚', color='#10b981')
  - ✅ guideline_search skill uses Claude to formulate optimal PubMed queries, searches literature, and returns results with evidence levels
  - ✅ evidence_synthesis skill uses Claude to synthesize multiple articles with citations
  - ✅ All results include source citations (PMID, authors, journal, year)
  - ✅ Evidence levels properly classified (meta-analysis > RCT > cohort > case)
  - ✅ All outputs use "evidence suggests..." language per safety requirements
  - ✅ trial_match skill implemented as placeholder for future ClinicalTrials.gov integration
  - ✅ literature_review skill combines search and synthesis
  - ✅ Chat interface with research-focused system prompt
- **Files involved:**
  - backend/agents/research_agent.py (652 lines)
  - backend/tests/test_research_agent.py (480 lines, 23 tests)
  - backend/integrations/pubmed_client.py (440 lines)
- **Tests**: All 23 tests passing
- **Learnings:**
  - Research Agent leverages Claude for both query formulation and evidence synthesis, ensuring optimal search strategies
  - Evidence level hierarchy is implemented as a dictionary for efficient sorting (EVIDENCE_LEVELS)
  - PubMed client handles both esearch (for PMIDs) and efetch (for full metadata) in sequence
  - XML parsing is encapsulated in _parse_pubmed_xml() for clean separation of concerns
  - Synthesis prompts explicitly require JSON output format for structured parsing
  - Agent properly handles missing PubMed client gracefully (returns error rather than crashing)
  - All outputs consistently include disclaimer for HIPAA compliance and clinical safety

---

