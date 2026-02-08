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

