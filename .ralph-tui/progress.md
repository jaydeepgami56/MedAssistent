# Ralph Progress Log

This file tracks progress across iterations. Agents update this file
after each iteration and it's included in prompts for context.

## Codebase Patterns (Study These First)

### Agent Implementation Pattern
All specialist agents follow a consistent pattern:
1. Inherit from `BaseAgent` with required metadata (agent_id, name, skills, models_used, color, icon)
2. Initialize with Anthropic API key
3. Implement `execute_skill()` method with skill routing
4. Implement `chat()` as async generator yielding str tokens
5. Include DISCLAIMER constant in all outputs
6. Use `log_audit()` for compliance tracking
7. Provide singleton pattern with `init_<agent>_agent()` and `get_<agent>_agent()`

### MEWS Scoring Pattern
Modified Early Warning Score (MEWS) implementation:
- HR: <40 or >130=3, 41-50 or 111-130=2, 101-110=1, 51-100=0
- BP systolic: <70=3, 71-80=2, >200=2, 81-100=1, 101-199=0
- RR: <9=2, >29=3, 21-29=2, 15-20=1, 9-14=0
- Temp (°C): <35=2, >38.5=2, 35-38.4=0
- Alert levels: Normal (0-2), Increased concern (3-4), Critical (5+)
- SpO2 < 90% triggers immediate critical alert regardless of MEWS

### Type Annotations Pattern
- Use explicit type hints for instance variables: `self._vital_history: dict[str, list[dict]] = {}`
- Async generators should be typed as `async def method() -> AsyncIterator[Type]`
- Use `--ignore-missing-imports` with mypy for third-party libraries

### Claude API Response Handling Pattern
- Extract JSON from Claude responses using markdown block detection:
  ```python
  if "```json" in content:
      content = content.split("```json")[1].split("```")[0].strip()
  elif "```" in content:
      content = content.split("```")[1].split("```")[0].strip()
  json_data = json.loads(content)
  ```
- Mypy union-attr warnings for `response.content[0].text` are expected (Anthropic library types)
- All generated documentation must include `draft_status='pending_review'` to enforce human review

### API Client Integration Pattern
All integration clients (RxNorm, DrugBank, PubMed) follow a consistent pattern:
1. Use `httpx.AsyncClient` with timeout configuration (typically 30s)
2. Initialize from settings: `api_key or settings.API_KEY_NAME`
3. Implement `async def close()` to cleanup HTTP client
4. Use explicit type hints for params: `dict[str, str | int]` for httpx compatibility
5. Use `dict[str, Any]` for dynamic response data structures to satisfy mypy
6. Include comprehensive error handling: HTTPStatusError, RequestError, generic Exception
7. Print informative logs for debugging (initialization, errors, result counts)
8. Provide singleton pattern: `init_client()`, `close_client()`, `get_client()`
9. Return empty lists/dicts on errors rather than raising exceptions (graceful degradation)
10. For rate-limited APIs: implement `_rate_limit_delay()` with async sleep and time tracking

---

## [2026-02-08] - US-019
- **What was implemented:** Monitoring Agent with MEWS scoring, vital tracking, anomaly detection, and auto-alerting
- **Files changed:**
  - `backend/agents/monitoring_agent.py` - Full implementation (already existed, verified)
  - `backend/tests/test_monitoring_agent.py` - Fixed test case for RR scoring (RR=16 yields MEWS=1, not 0)
- **Learnings:**
  - MEWS scoring ranges are precisely defined - RR 15-20 = 1 point, not 0
  - The agent correctly implements all acceptance criteria including:
    - Standard MEWS calculation for HR, BP, RR, Temp
    - Alert levels: Normal (0-2), Increased (3-4), Critical (5+)
    - SpO2 < 90% triggers critical alert independently
    - Vital tracking with 6-hour rolling window
    - MEWS >= 5 auto-generates critical alert for attending physician
  - Type annotation for dict instance variables must be explicit for mypy
  - All 19 tests pass (1 skipped due to missing API key)
  - Agent already registered in main.py startup sequence

---

## [2026-02-08] - US-020
- **What was implemented:** Documentation Agent with SOAP notes, discharge summaries, ICD-10 coding, and referral letters
- **Files changed:**
  - `backend/agents/documentation_agent.py` - Full implementation (new file)
  - `backend/tests/test_documentation_agent.py` - Comprehensive test suite with 20 tests (new file)
  - `backend/main.py` - Added Documentation Agent initialization
- **Learnings:**
  - SOAP note generation requires comprehensive prompt engineering to extract all 4 sections (S, O, A, P)
  - ICD-10 code suggestions should include confidence scores and be ordered by likelihood
  - All documentation outputs MUST return `draft_status='pending_review'` to ensure clinician approval
  - JSON extraction from Claude responses requires handling both ```json and ``` markdown formats
  - Confidence scoring for SOAP notes based on section completeness and data source availability
  - Discharge summaries need structured sections: admission/discharge diagnosis, hospital course, procedures, complications, condition, medications, follow-up, education
  - Referral letters should be formatted professionally with clear reason for referral and relevant clinical context
  - The `_build_soap_prompt()` helper consolidates multiple data sources (triage, radiology, pharmacy, monitoring) into comprehensive clinical context
  - All 20 tests pass (11 skipped due to missing API key, which is expected)
  - Mypy shows union-attr warnings for Anthropic library response types - these are third-party library issues, consistent with other agents, acceptable per `--ignore-missing-imports` guidance
  - Agent successfully registered in main.py startup sequence

---

## [2026-02-08] - US-021
- **What was implemented:** PubMed integration client for medical literature search with NCBI E-utilities API
- **Files changed:**
  - `backend/integrations/pubmed_client.py` - Full implementation with search, fetch_abstracts, format_citation methods (new file)
  - `backend/tests/test_pubmed_client.py` - Comprehensive test suite with 19 tests (new file)
- **Learnings:**
  - PubMed API uses two-step process: esearch.fcgi (get PMIDs) → efetch.fcgi (get full metadata)
  - NCBI rate limiting is strictly enforced: 3 req/sec without API key, 10 req/sec with key
  - Rate limiting implementation uses async sleep with time tracking between requests
  - XML parsing with ElementTree requires careful null checks for all elements and text content
  - Vancouver citation style is standard for medical literature: "Authors. Title. Journal. Year. PMID: xxx"
  - Author formatting handles both individual authors (LastName + Initials) and CollectiveName elements
  - PubDate can be in multiple formats: Year element or MedlineDate text (e.g., "2023 Jan-Feb")
  - Structured abstracts have Label attributes on AbstractText elements (e.g., "BACKGROUND:", "METHODS:")
  - Type annotations for dict params require explicit types: `dict[str, str | int]` for httpx params compatibility
  - Using `dict[str, Any]` for article_data dict silences mypy warnings about dynamic key assignments
  - All 19 tests pass including live API integration tests (search, fetch, citation formatting)
  - Mypy type checking passes with `--ignore-missing-imports` flag
  - Rate limiting test verifies mechanism existence rather than strict timing due to network latency variability

---

