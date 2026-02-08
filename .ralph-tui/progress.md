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

### Coordinator Agent Registration Pattern
- All specialist agents initialized FIRST in main.py lifespan()
- Coordinator agent initialized LAST (after all specialists)
- After coordinator init, call get_*_agent() for each specialist and register with coordinator.register_specialist(agent_id, instance)
- This avoids circular imports while allowing coordinator to hold references for routing
- Pattern: `coordinator = get_coordinator_agent(); if coordinator: coordinator.register_specialist("agent_id", get_agent_instance())`

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

## 2026-02-08 - US-024: Implement Coordinator Agent with routing and consensus

**What was implemented:**
- Created `backend/agents/coordinator_agent.py` with full `CoordinatorAgent` class
- Implemented 4 core skills:
  1. `agent_routing` - Analyzes incoming messages using Claude to determine which specialist agent(s) to invoke. Returns target_agents list, reasoning, and confidence score. Validates routing against available specialists.
  2. `consensus` - Builds multi-agent consensus by analyzing outputs from multiple specialists. Identifies agreements/disagreements, flags conflicts for human review, and enforces confidence < 0.7 automatic review.
  3. `safety_check` - Enforces 6 critical safety rules: confidence threshold (> 0.7), ESI 1-2 escalation, critical drug interactions, MEWS >= 5 alerts, SpO2 < 90% alerts, and red flag detection. Returns pass/fail with recommended action (approve/review/escalate).
  4. `escalation` - Triggers attending physician alerts for critical findings. Generates unique alert IDs, determines notification roles (Attending, Cardiology, Pharmacy, etc.), and logs escalation with full audit trail.
- Implemented streaming chat interface with coordination system prompt
- Integrated into backend/main.py with automatic specialist registration
- Coordinator holds references to all 7 specialist agents (triage, radiology, diagnostic, pharmacy, monitoring, documentation, research) via `register_specialist()` method

**Files changed:**
- `backend/agents/coordinator_agent.py` (new, 660 lines)
- `backend/main.py` (added import, initialization, and specialist registration loop)

**Learnings:**
- **Pattern: Multi-Agent Orchestration** - Coordinator uses a registry pattern (`self.specialist_agents = {}`) to hold references to all specialists. Agents are registered after initialization in main.py using `coordinator.register_specialist(agent_id, agent_instance)`. This allows runtime routing without circular imports.

- **Pattern: Dynamic Agent Selection with Claude** - For routing, Claude analyzes user intent against a structured list of agent capabilities. Prompt includes available agents with their skills, routing rules (single vs. multi-agent), and JSON response format. Always validate Claude's selected agents against the actual registry before returning.

- **Pattern: Consensus Building** - When combining results from multiple agents, use Claude to analyze agreement/disagreement rather than rule-based merging. Pass all agent outputs with confidence scores, ask Claude to identify common ground and conflicts, then enforce minimum confidence rule (min of all agents).

- **Pattern: Layered Safety Checks** - Safety checks are rule-based (NOT LLM-based) for reliability. Implement as a series of independent checks with failure accumulation: confidence threshold, ESI scoring, drug interactions, vital signs, MEWS, red flags. Each check appends to `failures` list and sets flags (`requires_review`, `requires_escalation`). Final action determined by flag priority: escalate > review > approve.

- **Pattern: Escalation Alerts** - Generate unique alert IDs with timestamp format (`ALERT-YYYYMMDD-HHMMSS`). Determine notification roles based on reason keywords (cardiac → Cardiology, drug → Pharmacy, etc.). In production, this would trigger actual notifications (pager, SMS, EMR alert); for now, uses `logger.warning()` for audit trail.

- **Gotcha: Initialization Order** - Coordinator MUST be initialized AFTER all specialist agents, otherwise `get_*_agent()` calls will return None. In main.py lifespan, the order is: init all specialists → init coordinator → register specialists with coordinator.

- **Gotcha: Confidence Threshold Enforcement** - The `consensus` skill must FORCE `requires_review=True` if any agent's confidence < 0.7, even if Claude's analysis doesn't flag it. This is a non-negotiable safety constraint: `if overall_confidence < 0.7: result["requires_review"] = True`. Never trust LLM output alone for safety-critical decisions.

- **Design Choice: Coordinator as Orchestrator, Not Specialist** - The coordinator NEVER performs clinical analysis directly. Its chat interface is for routing questions only. All clinical tasks are delegated to specialists. This keeps the separation of concerns clean and ensures clinical reasoning is always auditable to a specific domain agent.

---

## 2026-02-08 - US-025: Create FHIR R4 EHR integration client

**What was implemented:**
- Created `backend/integrations/fhir_client.py` with full `FHIRClient` class
- Implemented 5 core methods for FHIR R4 resource retrieval:
  1. `get_patient(patient_id)` - Fetches Patient resource and returns simplified demographics (name, age, gender, DOB)
  2. `get_conditions(patient_id)` - Fetches active Condition resources with code, display, status, onset date
  3. `get_medications(patient_id)` - Fetches active MedicationRequest resources with code, display, status, dosage
  4. `get_allergies(patient_id)` - Fetches AllergyIntolerance resources with code, display, status, type, category, criticality, reactions
  5. `get_observations(patient_id, category)` - Fetches Observation resources filtered by category (vital-signs, laboratory, etc.) with code, value, unit, effective date
- All methods parse FHIR R4 JSON resources into simplified dicts for easy consumption by agents
- Integrated FHIR client into backend/main.py startup/shutdown lifecycle
- Added graceful error handling: returns empty results when FHIR server is unavailable or not configured

**Files changed:**
- `backend/integrations/fhir_client.py` (new, 825 lines)
- `backend/integrations/__init__.py` (added FHIR exports)
- `backend/main.py` (added FHIR client initialization and shutdown)
- `backend/config.py` (already had FHIR_BASE_URL setting)

**Learnings:**
- **Pattern: Integration Client Structure** - All external integration clients follow a consistent pattern:
  - Class with `__init__(base_url)` accepting optional base_url (defaults to settings)
  - `httpx.AsyncClient` for async HTTP requests with 30s timeout
  - Public async methods for core operations
  - Private `_parse_*` methods for converting external formats to simplified dicts
  - Global singleton pattern with `init_*()`, `close_*()`, and `get_*_client()` functions
  - Initialization/cleanup in main.py lifespan() startup/shutdown

- **Pattern: Graceful Degradation** - Integration clients MUST handle unavailable external services gracefully:
  - Check if base_url is configured in `__init__()`, log warning if not
  - Return empty results (empty list, dict with `found=False`) instead of raising exceptions
  - Wrap all HTTP calls in try/except with specific handling for `HTTPStatusError`, `RequestError`, and generic exceptions
  - Log errors with `print()` for debugging but don't propagate to API layer

- **Pattern: FHIR R4 Resource Parsing** - FHIR resources have complex nested structures. Simplify for agents:
  - Extract codes from `coding` arrays (first coding is usually most relevant)
  - Fall back to `text` field if no coding available
  - Handle multiple date formats: `effectiveDateTime`, `effectivePeriod.start`, etc. - always extract date part (split on 'T')
  - Parse status/verification from nested CodeableConcept structures
  - Return human-readable `display` names, not just codes

- **Pattern: FHIR Search Parameters** - FHIR APIs use query parameters for filtering:
  - Patient-scoped queries: `?patient={id}` to filter by patient
  - Status filtering: `?status=active` or `?clinical-status=active` for active records only
  - Category filtering: `?category=vital-signs` for Observations
  - Results come wrapped in Bundle resources with `entry` array containing individual resources

- **Gotcha: FHIR Bundle Responses** - Most FHIR queries return Bundle resources, not individual resources:
  - Iterate through `data.get("entry", [])` to extract resources
  - Each entry has `resource` field containing the actual resource
  - Always check `resourceType` to ensure correct parsing
  - Empty results return Bundle with no entries (not 404)

- **Gotcha: FHIR Value Polymorphism** - Observation values can be Quantity, String, CodeableConcept, etc.:
  - Try `valueQuantity` first (most common for vitals/labs) - extract `value` and `unit`
  - Fall back to `valueString` for text values
  - Fall back to `valueCodeableConcept` for coded values
  - Always handle None cases gracefully

- **Design Choice: httpx Over requests** - Using `httpx.AsyncClient` for async compatibility:
  - Matches async pattern used in RxNorm/DrugBank/PubMed clients
  - Allows concurrent requests in future (parallel patient data fetching)
  - 30s timeout balances responsiveness vs. EHR system latency

- **Design Choice: Simplified Data Models** - FHIR resources are verbose. Agents don't need full resources:
  - Extract only clinically relevant fields (code, display, value, date, status)
  - Flatten nested structures (e.g., `coding[0].code` → `code`)
  - Convert dates to simple YYYY-MM-DD strings
  - Focus on human-readable `display` names over machine codes

---

## 2026-02-08 - US-026: Create Orthanc DICOM integration client

**What was implemented:**
- Created `backend/integrations/dicom_client.py` with full `DicomClient` class
- Implemented 4 core methods for Orthanc DICOM REST API operations:
  1. `upload_study(dicom_bytes)` - Uploads DICOM file to Orthanc via POST /instances, returns instance ID
  2. `get_study(study_id)` - Retrieves study metadata including patient info, study date, modality, series, and instances
  3. `get_image(instance_id)` - Retrieves rendered PNG preview from GET /instances/{id}/preview and converts to PIL.Image for model inference
  4. `list_studies(patient_id)` - Lists all studies for a patient by querying patient metadata and fetching each study's details
- All methods use `httpx.AsyncClient` with 30s timeout for async HTTP requests
- Integrated DICOM client into backend/main.py startup/shutdown lifecycle
- Added exports to backend/integrations/__init__.py

**Files changed:**
- `backend/integrations/dicom_client.py` (new, 436 lines)
- `backend/integrations/__init__.py` (added DICOM exports)
- `backend/main.py` (added DICOM client initialization and shutdown)

**Learnings:**
- **Pattern: Orthanc REST API Structure** - Orthanc uses a hierarchical resource structure:
  - `/patients/{id}` returns patient metadata with list of study IDs in `Studies` array
  - `/studies/{id}` returns study metadata with `MainDicomTags` (study-level) and `PatientMainDicomTags` (patient demographics)
  - `/instances/{id}/preview` returns PNG preview image (not raw DICOM), perfect for model input
  - POST `/instances` accepts raw DICOM bytes with `Content-Type: application/dicom`, returns JSON with instance `ID`

- **Pattern: PIL.Image from HTTP Response** - Converting image bytes to PIL.Image for model inference:
  ```python
  image_bytes = response.content
  image = Image.open(io.BytesIO(image_bytes))
  ```
  This pattern allows models like MedImageInsight to directly consume images from Orthanc.

- **Pattern: DICOM Upload Error Handling** - Unlike retrieval methods that return error dicts, `upload_study` raises exceptions on failure:
  - Validates input is non-empty before attempting upload
  - Propagates `HTTPStatusError` and `RequestError` to caller for proper error handling
  - This matches the "fail fast" pattern for write operations vs. "graceful degradation" for reads

- **Gotcha: Orthanc Metadata Structure** - Orthanc uses nested DICOM tag structures:
  - Study-level tags in `MainDicomTags` (StudyDate, StudyDescription, Modality)
  - Patient-level tags in `PatientMainDicomTags` (PatientName, PatientID)
  - Must access correct dict for each metadata field
  - Series and Instances returned as arrays of IDs, not full resources

- **Gotcha: Patient Name Format** - DICOM PatientName uses caret-separated format (`DOE^JOHN`), not space-separated. Leave as-is for agents to parse if needed, don't auto-convert.

- **Design Choice: httpx Over requests** - Consistent with other integration clients (FHIR, RxNorm, DrugBank, PubMed), using `httpx.AsyncClient` for:
  - Async compatibility with FastAPI
  - Consistent timeout handling (30s)
  - Future support for concurrent uploads/retrievals

- **Design Choice: PNG Preview vs Raw DICOM** - Using `/instances/{id}/preview` endpoint instead of raw DICOM retrieval:
  - Returns PNG image that PIL.Image can directly consume
  - No need for complex DICOM parsing libraries (pydicom)
  - Sufficient for model inference (MedImageInsight, MedGemma)
  - Simplifies the integration and reduces dependencies

---

## 2026-02-08 - US-027: Implement all REST API endpoints for agents and skills

**What was implemented:**
- Created `backend/routers/agents.py` with complete REST API router containing 11 endpoints
- Core agent endpoints:
  1. `GET /agents` - List all registered agents with full metadata
  2. `GET /agents/{agent_id}` - Get single agent details with 404 handling
  3. `POST /agents/{agent_id}/chat` - Stream chat responses via Server-Sent Events (SSE)
  4. `POST /agents/{agent_id}/execute` - Execute specific agent skills with validation
  5. `GET /agents/skills/list` - List all skills across all agents
- Domain-specific endpoints:
  6. `POST /agents/triage/assess` - ESI scoring and triage assessment
  7. `POST /agents/radiology/analyze` - Image upload and analysis (multipart/form-data)
  8. `POST /agents/pharmacy/check` - Drug interaction checking
  9. `POST /agents/monitoring/vitals` - MEWS score calculation
  10. `POST /agents/documentation/generate` - SOAP note generation
  11. `POST /agents/research/search` - PubMed and guideline search
- Created Pydantic request models for all domain endpoints with proper validation and optional fields
- Integrated router into `backend/main.py` via `app.include_router(agents_router)`
- Created comprehensive test suite to verify endpoint registration, signatures, and error handling

**Files changed:**
- `backend/routers/agents.py` (new, 541 lines)
- `backend/routers/__init__.py` (new, exports router)
- `backend/main.py` (added router import and registration)
- `backend/routers/README.md` (new, comprehensive API documentation)
- `test_endpoints.py` (new, endpoint registration verification)
- `test_api_signatures.py` (new, Pydantic model validation)
- `test_api_integration.py` (new, integration tests)

**Learnings:**

- **Pattern: FastAPI Router Organization** - Use `APIRouter` with prefix and tags for clean separation of concerns:
  ```python
  router = APIRouter(prefix="/agents", tags=["agents"])
  ```
  Then include in main app with `app.include_router(agents_router)`. This keeps main.py clean and routes organized by domain.

- **Pattern: Pydantic Request Models** - Define request models with `BaseModel` for automatic validation, serialization, and OpenAPI docs:
  ```python
  class ChatRequest(BaseModel):
      message: str
      context: Optional[dict] = {}  # Optional with default
  ```
  FastAPI automatically validates request bodies, generates API docs, and provides type hints.

- **Pattern: Streaming SSE Responses** - For streaming chat, use `StreamingResponse` with async generator:
  ```python
  async def generate():
      async for chunk in agent.chat(message, context):
          yield f"data: {chunk}\n\n"  # SSE format
  return StreamingResponse(generate(), media_type="text/event-stream")
  ```
  SSE format requires `data: <content>\n\n` for each message.

- **Pattern: File Upload Handling** - Use `UploadFile = File(...)` for multipart uploads:
  ```python
  async def endpoint(file: UploadFile = File(...), param: str = "default"):
      image_bytes = await file.read()
  ```
  Always validate file is non-empty before processing. `UploadFile` is async-friendly and handles large files efficiently.

- **Pattern: Agent Registry Pattern** - Create helper functions to get all agents or specific agent by ID:
  ```python
  def get_all_agents():
      return [get_triage_agent(), get_radiology_agent(), ...]
  
  def get_agent_by_id(agent_id: str):
      agent_getters = {"triage": get_triage_agent, ...}
      return agent_getters.get(agent_id)()
  ```
  This centralizes agent lookup logic and makes it easy to iterate over all agents.

- **Pattern: Consistent Error Handling** - Use HTTPException with appropriate status codes:
  - 404: Resource not found (agent doesn't exist)
  - 400: Invalid input (missing skill, empty file, validation error)
  - 500: Execution failed (wrapped exception)
  - 503: Service unavailable (agent not initialized)
  
  Always include descriptive `detail` message for debugging.

- **Pattern: Domain Endpoint Mapping** - Map domain endpoints directly to agent skills:
  ```python
  @router.post("/triage/assess")
  async def triage_assess(request: TriageAssessRequest):
      return await agent.execute_skill("esi_scoring", request.dict())
  ```
  This provides a clean, domain-specific API while delegating to the underlying agent system.

- **Gotcha: Agent Initialization Order** - Endpoints can import agent getter functions safely because they're called at request time, not module load time. The agents are initialized in main.py lifespan() before any requests are handled.

- **Gotcha: Optional Fields in Pydantic** - Use `Optional[T] = default` for optional fields:
  ```python
  history: Optional[dict] = {}
  patient_id: Optional[str] = None
  ```
  Without the default value, the field is still required even with `Optional`.

- **Gotcha: UploadFile vs File Parameter** - `UploadFile = File(...)` allows additional parameters (study_type, patient_id), while `file: UploadFile` alone requires the file to be the only parameter. Use `= File(...)` syntax for flexibility.

- **Design Choice: Path Parameters** - Used `{agent_id}` instead of `{id}` for clarity. More explicit path parameters improve API self-documentation and reduce ambiguity.

- **Design Choice: Skill Validation** - Validate requested skill exists on agent before execution:
  ```python
  if skill_name not in agent.skills:
      raise HTTPException(400, detail=f"Skill '{skill_name}' not available")
  ```
  This provides immediate feedback rather than waiting for the agent's execute_skill to fail.

- **Design Choice: StreamingResponse for Chat** - Used SSE (Server-Sent Events) instead of WebSockets for chat streaming. SSE is simpler (HTTP-based), works with standard HTTP clients (curl, requests), and is sufficient for one-way streaming from agent to client.

---

## 2026-02-08 - US-028: Integrate frontend React dashboard with backend API

**What was implemented:**
- Added 3 new GET endpoints to `backend/routers/agents.py`:
  - `GET /agents/triage/queue` - Returns mock triage patient queue with ESI levels
  - `GET /agents/radiology/reports/latest` - Returns latest radiology report with findings
  - `GET /agents/monitoring/vitals/latest` - Returns latest vital signs with MEWS score
- Created complete frontend directory structure at `frontend/`
- Created `frontend/src/services/api.js` - Comprehensive API client with:
  - Generic `fetchJSON()` wrapper with error handling
  - Agent methods: `getAgents()`, `getAgent()`, `executeSkill()`
  - SSE streaming: `chatWithAgent()` with onChunk/onError callbacks
  - Domain methods: `getTriageQueue()`, `getLatestRadiologyReport()`, `getLatestVitals()`
  - All POST endpoints: triage, radiology, pharmacy, monitoring, documentation, research
- Created `frontend/src/components/MedAssistDashboard.jsx` - Fully integrated React dashboard:
  - Replaced static mock data with API calls using `useState`/`useEffect` hooks
  - Dashboard view fetches agents from `GET /agents` on mount
  - Triage view fetches queue from `GET /agents/triage/queue` when activated
  - Radiology view fetches report from `GET /agents/radiology/reports/latest` when activated
  - Vitals view fetches vitals from `GET /agents/monitoring/vitals/latest` when activated
  - Agent chat uses SSE streaming from `POST /agents/{id}/chat` with real-time chunk rendering
  - Error handling: Shows red banner when backend unreachable, graceful error states in views
  - Preserved all original UI design, colors, layout, and styling
- Created frontend configuration files:
  - `package.json` - React 18 + Vite 6 dependencies
  - `vite.config.js` - Dev server with proxy to backend
  - `index.html` - HTML template with root div
  - `src/main.jsx` - App entry point with StrictMode
  - `.env.example` - Configurable API base URL
  - `README.md` - Comprehensive frontend documentation
- Created `FRONTEND_INTEGRATION.md` - Full integration guide with architecture, data flow, troubleshooting

**Files changed:**
- `backend/routers/agents.py` (added 3 GET endpoints for queue data, +120 lines)
- `frontend/src/services/api.js` (new, 281 lines)
- `frontend/src/components/MedAssistDashboard.jsx` (new, 565 lines - migrated from root, integrated with API)
- `frontend/package.json` (new)
- `frontend/vite.config.js` (new)
- `frontend/index.html` (new)
- `frontend/src/main.jsx` (new)
- `frontend/.env.example` (new)
- `frontend/README.md` (new, comprehensive docs)
- `FRONTEND_INTEGRATION.md` (new, 500+ line integration guide)
- `medassist-agent-interface.jsx` → `medassist-agent-interface-ORIGINAL.jsx` (renamed, deprecated)

**Learnings:**

- **Pattern: React API Integration with Hooks** - Use `useEffect` with dependency array to fetch data on mount or view change:
  ```javascript
  useEffect(() => {
    async function fetchData() {
      try {
        const data = await api.getAgents();
        setAgents(data);
      } catch (err) {
        setError(err.message);
      }
    }
    fetchData();
  }, []); // Empty array = run once on mount
  ```
  For view-dependent fetches, use `[activeView]` as dependency.

- **Pattern: SSE Streaming in React** - Parse Server-Sent Events using ReadableStream:
  ```javascript
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";
    for (const line of lines) {
      if (line.startsWith("data: ")) {
        const chunk = line.slice(6);
        onChunk(chunk); // Update UI with each chunk
      }
    }
  }
  ```
  Accumulate chunks in state for real-time message rendering.

- **Pattern: Configurable API Base URL** - Support multiple environment variable formats:
  ```javascript
  export const API_BASE_URL = import.meta.env?.VITE_API_BASE_URL ||  // Vite
                              process.env.REACT_APP_API_BASE_URL ||   // CRA
                              "http://localhost:8000";                 // Default
  ```
  This works across Vite, Create React App, and bare Node.js environments.

- **Pattern: Centralized Error Handling** - Wrap fetch in try/catch, detect network errors:
  ```javascript
  if (error.message.includes("Failed to fetch") || error.message.includes("NetworkError")) {
    throw new Error("Backend is unreachable. Please ensure the server is running at " + API_BASE_URL);
  }
  ```
  Provide clear, actionable error messages for users.

- **Pattern: Error State UI** - Show banner at top + status indicator in navbar:
  ```javascript
  const ErrorBanner = () => error && (
    <div style={{ background: "#1a0505", border: "1px solid #ef444433" }}>
      <span>⚠️ {error}</span>
      <button onClick={() => setError(null)}>×</button>
    </div>
  );
  ```
  Make errors visible but dismissible. Update status dot color in navbar to reflect connection state.

- **Pattern: Mock Data in Backend** - For endpoints that will query DB in production, return mock data now:
  ```python
  @router.get("/triage/queue")
  async def get_triage_queue():
      # Returns mock data (replace with DB query in production)
      return [{"id": 1, "name": "Patient A", ...}, ...]
  ```
  Document with comments. This unblocks frontend development while DB schema is finalized.

- **Pattern: Loading States** - Show "Loading..." while fetching, hide after data arrives:
  ```javascript
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    setLoading(true);
    const data = await api.getAgents();
    setAgents(data);
    setLoading(false);
  }, []);
  ```
  Prevents showing empty/stale data during fetch.

- **Pattern: Backend Property Mapping** - Backend returns `agent_id`, frontend expects `id`:
  ```javascript
  const mappedAgents = agentsData.map(agent => ({
    ...agent,
    id: agent.agent_id,  // Map backend field to frontend field
    bg: getBgColor(agent.color),  // Add computed fields
  }));
  ```
  Transform data at the API boundary to match UI expectations.

- **Gotcha: SSE Stream Buffering** - SSE messages can arrive split across multiple reads. Always buffer and split by `\n`:
  ```javascript
  buffer += decoder.decode(value, { stream: true });
  const lines = buffer.split("\n");
  buffer = lines.pop() || "";  // Keep incomplete line in buffer
  ```
  Without buffering, you'll miss partial messages or incorrectly parse them.

- **Gotcha: useEffect Dependency Arrays** - Missing dependencies cause stale closures:
  ```javascript
  // WRONG: selectedAgent not in deps, will reference old value
  useEffect(() => {
    console.log(selectedAgent.name);
  }, []);

  // RIGHT: Include all dependencies
  useEffect(() => {
    console.log(selectedAgent.name);
  }, [selectedAgent]);
  ```
  Always include ALL values from outer scope used inside useEffect.

- **Gotcha: Streaming State Updates** - When streaming chat, update last message instead of appending:
  ```javascript
  // Add placeholder message with streaming: true
  setChatMessages(prev => [...prev, { text: "", streaming: true }]);

  // Update last message text as chunks arrive
  onChunk: (chunk) => {
    fullResponse += chunk;
    setChatMessages(prev => {
      const updated = [...prev];
      updated[updated.length - 1].text = fullResponse;
      return updated;
    });
  }
  ```
  Don't append a new message for each chunk - that creates duplicates.

- **Gotcha: Vite vs CRA Environment Variables** - Vite uses `VITE_` prefix, CRA uses `REACT_APP_`:
  - Vite: `import.meta.env.VITE_API_BASE_URL`
  - CRA: `process.env.REACT_APP_API_BASE_URL`

  Support both for portability, or standardize on Vite (modern, faster).

- **Design Choice: Vite Over Create React App** - Vite is faster (esbuild), simpler config, better HMR:
  - Dev server starts in ~200ms vs CRA's ~10s
  - Hot Module Replacement is instant
  - Smaller bundle sizes
  - Native ES modules support

  CRA is deprecated; Vite is the modern standard.

- **Design Choice: Inline Styles Over CSS Modules** - Preserved original inline styles for simplicity:
  - No build step for CSS
  - No class name conflicts
  - Styles colocated with components
  - Easy to theme via color props

  For large-scale production, consider migrating to CSS-in-JS (styled-components) or Tailwind.

- **Design Choice: Mock Data in GET Endpoints** - Queue/report/vitals endpoints return static mock data:
  - Unblocks frontend development
  - Provides realistic data structure for testing
  - Easy to replace with DB queries later
  - Documents expected schema

  In production, replace with queries to PostgreSQL (triage queue, vitals) and Orthanc (radiology reports).

- **Design Choice: SSE Over WebSockets for Chat** - SSE is simpler for unidirectional streaming:
  - HTTP-based (no upgrade negotiation)
  - Works with standard HTTP clients (curl, fetch)
  - Automatic reconnection in browsers
  - Sufficient for agent → user streaming

  WebSockets only needed for bidirectional real-time (e.g., collaborative editing). SSE is perfect for chat.

---

