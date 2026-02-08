# Ralph Progress Log

This file tracks progress across iterations. Agents update this file
after each iteration and it's included in prompts for context.

## Codebase Patterns (Study These First)

### Agent Implementation Pattern
All specialist agents follow a consistent pattern:
1. Inherit from `BaseAgent` (backend/agents/base_agent.py)
2. Initialize with: agent_id, name, skills[], models_used[], color, icon
3. Implement `execute_skill(skill_name, params)` method that routes to private skill methods
4. Implement `chat(message, context)` method with streaming Claude responses
5. Include DISCLAIMER constant: "AI-assisted — requires [agent-specific verification]"
6. Use `self.log_audit()` for all skill executions
7. Create global singleton with init_*_agent() and get_*_agent() functions
8. Register in backend/main.py lifespan() startup

### Claude API Usage Pattern
- Use Anthropic client initialized with API key
- Model: "claude-sonnet-4-20250514" (from settings.CLAUDE_MODEL)
- Streaming chat: `with self.client.messages.stream(...) as stream: for text in stream.text_stream: yield text`
- Non-streaming: `response = self.client.messages.create(...); content = response.content[0].text`
- JSON prompt pattern: Request JSON in prompt, parse with try/except, handle markdown code blocks
- Always add disclaimer after streaming responses

### Error Handling Pattern
- Wrap skill methods in try/except blocks
- Return dict with "error" key on failure
- Log errors with logger.error()
- Return safe fallback data structure (empty lists/dicts, requires_review=True)
- Never propagate exceptions to API layer - return error dict instead

---

## 2026-02-08 - US-023: Implement Diagnostic Agent with differential diagnosis

**What was implemented:**
- Created `backend/agents/diagnostic_agent.py` with full `DiagnosticAgent` class
- Implemented 4 core skills:
  1. `differential_dx` - Generate ranked differential diagnoses from clinical data (symptoms, vitals, labs, imaging, history)
  2. `test_recommendation` - Suggest diagnostic tests with rationale and priority based on differentials
  3. `pattern_recognition` - Rule-based matching against 6 critical patterns (ACS, sepsis, PE, stroke, DKA, meningitis)
  4. `rare_disease` - Placeholder for future GARD/Orphanet integration
- Implemented streaming chat interface with diagnostic system prompt
- Integrated agent into backend/main.py startup sequence

**Files changed:**
- `backend/agents/diagnostic_agent.py` (new, 821 lines)
- `backend/main.py` (added import and initialization)

**Learnings:**
- **Pattern: JSON Response Parsing** - Claude API returns JSON embedded in markdown code blocks. Standard pattern:
  ```python
  if "```json" in content:
      content = content.split("```json")[1].split("```")[0].strip()
  elif "```" in content:
      content = content.split("```")[1].split("```")[0].strip()
  diagnosis_data = json.loads(content)
  ```
  Always wrap in try/except with fallback to empty structure.

- **Pattern: Clinical Summary Building** - Breaking clinical data into structured sections (SYMPTOMS, VITAL SIGNS, LABORATORY RESULTS, IMAGING FINDINGS, PATIENT HISTORY) improves Claude's diagnostic reasoning quality.

- **Pattern: Confidence-Based Safety Checks** - All agents use `confidence < 0.7` threshold to flag outputs for mandatory human review (`requires_review=True`). This is a critical safety feature across the platform.

- **Pattern: Audit Logging** - Every skill execution must call `self.log_audit(request, model, confidence, action)` for HIPAA compliance and debugging.

- **Gotcha: Rule-Based Pattern Matching** - For critical pattern recognition (sepsis, stroke, ACS), rule-based matching is MORE reliable than LLM-based detection for real-time alerts. Store patterns as constants with symptom lists, vital criteria, and red flags.

- **Gotcha: Streaming Disclaimer** - When using `messages.stream()`, the disclaimer must be yielded AFTER the stream completes, not before. Pattern: `yield text` in loop, then `yield f"\n\n---\n{DISCLAIMER}"` after.

- **Design Choice: Claude API Primary, MedGemma Fallback** - Diagnostic reasoning is currently Claude-only. MedGemma 27B listed in models_used for future fallback implementation when self-hosted LLM infrastructure is ready.

---

