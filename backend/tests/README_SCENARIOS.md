# End-to-End Clinical Scenario Tests

## Overview

`test_scenarios.py` contains comprehensive end-to-end tests for critical clinical workflows in the MedAssist AI system. These tests verify that the complete system (API endpoints → agents → models → integrations) works correctly for real-world clinical scenarios.

## Test Scenarios

### Scenario 1: ESI-1 Triage (Life-Threatening)
**Patient:** 67F with crushing chest pain, BP 90/60, HR 110, SpO2 94%  
**Verifies:** ESI score = 1, red flags detected, routing to resuscitation  
**Clinical Significance:** Validates immediate identification of cardiac emergency

### Scenario 2: ESI-3 Triage (Urgent but Stable)
**Patient:** 32F with abdominal pain, fever 39.2°C  
**Verifies:** ESI score = 3  
**Clinical Significance:** Validates correct prioritization of urgent but stable cases

### Scenario 3: Critical Drug Interaction
**Drugs:** Warfarin + Ibuprofen  
**Verifies:** severity = "Critical", blocked = true  
**Clinical Significance:** Validates detection and blocking of high-risk drug combinations

### Scenario 4: MEWS Critical Alert
**Vitals:** HR=135, BP sys=80, RR=32, Temp=39.5°C  
**Verifies:** MEWS >= 5, alert_level = "Critical"  
**Clinical Significance:** Validates early warning system for patient deterioration

### Scenario 5: Radiology Image Analysis
**Input:** Test PNG image (chest X-ray)  
**Verifies:** Findings list with confidence scores  
**Clinical Significance:** Validates image analysis pipeline end-to-end

### Scenario 6: Coordinator Agent Routing
**Query:** "check drug interaction between warfarin and aspirin"  
**Verifies:** Routes to pharmacy agent  
**Clinical Significance:** Validates intelligent agent routing for clinical queries

### Scenario 7: SOAP Note Generation
**Input:** Mock encounter (STEMI case)  
**Verifies:** All 4 SOAP sections (Subjective, Objective, Assessment, Plan) present  
**Clinical Significance:** Validates clinical documentation generation

## Running the Tests

### Prerequisites
- Backend running with Docker Compose services (PostgreSQL, Qdrant, Orthanc)
- ANTHROPIC_API_KEY set in environment (tests skip gracefully if not set)

### Run All Scenarios
```bash
cd backend
pytest tests/test_scenarios.py -v
```

### Run Specific Scenario
```bash
pytest tests/test_scenarios.py -v -k scenario_1  # Run only Scenario 1
pytest tests/test_scenarios.py -v -k "scenario_3 or scenario_4"  # Run Scenarios 3 and 4
```

### Run with Output
```bash
pytest tests/test_scenarios.py -v -s  # Show print statements for detailed results
```

### Collect Tests Only (No Execution)
```bash
pytest tests/test_scenarios.py --collect-only -v  # Verify test discovery
```

## Test Architecture

- **Framework:** pytest with asyncio support
- **HTTP Client:** httpx.AsyncClient (tests against FastAPI app directly, no server needed)
- **Fixtures:** 
  - `api_key`: Loads ANTHROPIC_API_KEY from environment
  - `client`: Provides configured AsyncClient for all tests
  - `sample_image_bytes`: Generates test PNG images with PIL
- **Skip Strategy:** Tests requiring Claude API skip gracefully if API key not available

## CI/CD Integration

These tests can run in CI pipelines:
1. Without API key: All tests skip with clear messages (shows as "skipped" not "failed")
2. With API key: Full test suite executes and validates all clinical workflows

## Expected Test Output

```
tests/test_scenarios.py::test_scenario_1_esi1_triage PASSED
✓ Scenario 1 PASSED: ESI-1 triage correctly identified
  - ESI Score: 1
  - Red Flags: 3 detected
  - Routing: Resuscitation - ESI Level 1

tests/test_scenarios.py::test_scenario_3_drug_interaction PASSED
✓ Scenario 3 PASSED: Critical drug interaction detected and blocked
  - Severity: Critical
  - Blocked: True
  - Interactions: 1 detected

... (7 scenarios total)

tests/test_scenarios.py::test_all_agents_registered PASSED
✓ All 8 agents registered successfully
  - triage: Triage Agent (4 skills)
  - radiology: Radiology Agent (4 skills)
  - pharmacy: Pharmacy Agent (4 skills)
  ... (8 agents total)

===== 9 passed in 45.32s =====
```

## Troubleshooting

### Tests Skip with "ANTHROPIC_API_KEY not set"
**Cause:** API key not available in environment  
**Solution:** Set API key: `export ANTHROPIC_API_KEY=sk-ant-...`

### Test Fails with "Agent not available"
**Cause:** Agent initialization failed during FastAPI startup  
**Solution:** Check backend logs for initialization errors, verify dependencies are running

### Radiology Test Fails with "Empty file uploaded"
**Cause:** Image generation fixture failed  
**Solution:** Verify PIL (Pillow) is installed: `pip install Pillow`

### All Tests Fail Immediately
**Cause:** Import errors or missing dependencies  
**Solution:** Run `pytest --collect-only -v` to check test collection before execution

## Maintenance

When adding new scenarios:
1. Follow naming convention: `test_scenario_N_<description>`
2. Add comprehensive assertions with descriptive error messages
3. Include print statements for human-readable output
4. Skip gracefully if dependencies unavailable
5. Update this README with scenario details
6. Update `test_all_scenarios_summary` with new scenario description

## Related Documentation

- `backend/routers/agents.py` - API endpoint definitions
- `backend/agents/` - Agent implementations
- `CLAUDE.md` - System architecture and design
- `01-MedAssist-AI-Architecture.md` - Clinical workflows and safety requirements
