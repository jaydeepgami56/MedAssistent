# MedAssist AI — Implementation Tasks

## Phase 0: Prerequisites & Environment Setup

### 0.1 System Prerequisites
- [ ] Install Node.js >= 22 (required for OpenClaw)
- [ ] Install Python >= 3.10 (required for FastAPI backend)
- [ ] Install Docker Desktop & Docker Compose (required for infrastructure services)
- [ ] Install kubectl and configure access to Kubernetes cluster (required for production deployment)
- [ ] Install Git (required for repo management and model cloning)
- [ ] Install uv (Python package installer, required for MedImageInsight setup)
- [ ] Obtain Anthropic API key for Claude API (`sk-ant-...`)
- [ ] Obtain NCBI API key for PubMed access
- [ ] Obtain DrugBank API key (if using API access)
- [ ] Verify GPU availability (NVIDIA recommended for MedImageInsight + MedGemma inference)

### 0.2 Install OpenClaw
- [ ] Run `npm install -g openclaw@latest`
- [ ] Run `openclaw onboard --install-daemon`
- [ ] Verify OpenClaw daemon is running: `openclaw doctor`
- [ ] Verify gateway is accessible at `ws://127.0.0.1:18789`

### 0.3 Configure OpenClaw LLM Providers
- [ ] Create/edit `~/.openclaw/openclaw.json`
- [ ] Configure `default` provider: set `provider` to `anthropic`, `model` to `claude-sonnet-4-20250514`, add `apiKey`
- [ ] Configure `local` provider: set `provider` to `openai-compatible`, `baseUrl` to `http://127.0.0.1:1234/v1`, set `model` and `contextWindow: 32768`
- [ ] Verify config: `openclaw health`

### 0.4 Install LM Studio (HIPAA-Safe Local Inference)
- [ ] Download and install LM Studio from https://lmstudio.ai
- [ ] Download a medical-capable local model (e.g., Llama-based medical fine-tune)
- [ ] Start LM Studio local server on port 1234
- [ ] Test local inference endpoint: `curl http://127.0.0.1:1234/v1/models`

### 0.5 Initialize Project Repository
- [ ] Initialize git repo: `git init`
- [ ] Create `.gitignore` with entries: `.env`, `__pycache__/`, `*.pyc`, `models/`, `node_modules/`, `.venv/`
- [ ] Create `.env.example` with all required environment variables (see 04-Project-Setup.md)
- [ ] Copy `.env.example` to `.env` and fill in actual values
- [ ] Create initial `README.md`

---

## Phase 1: Foundation (Weeks 1-4)

### 1.1 Scaffold Project Directory Structure
- [ ] Create `config/` directory with `openclaw.json` template
- [ ] Create `skills/` directory with 7 subdirectories: `triage/`, `radiology/`, `diagnostic/`, `pharmacy/`, `monitoring/`, `documentation/`, `research/`
- [ ] Create `a2ui/templates/` directory for JSONL templates
- [ ] Create `a2ui/components/` directory for custom component reference
- [ ] Create `backend/` directory with subdirectories: `agents/`, `models/`, `integrations/`
- [ ] Create `infrastructure/` directory with `k8s/` subdirectory
- [ ] Create `docs/` directory
- [ ] Move existing doc files (`01-MedAssist-AI-Architecture.md`, `02-A2UI-Templates.md`, `03-SKILL-Files.md`, `04-Project-Setup.md`) to `docs/`

### 1.2 FastAPI Backend — Core Setup
- [ ] Create `backend/requirements.txt` with dependencies: `fastapi`, `uvicorn[standard]`, `python-dotenv`, `pydantic`, `httpx`, `anthropic`, `qdrant-client`, `transformers`, `torch`, `Pillow`, `python-multipart`
- [ ] Create Python virtual environment: `python -m venv .venv`
- [ ] Install dependencies: `pip install -r backend/requirements.txt`
- [ ] Create `backend/config.py` — load all env vars using `python-dotenv`, define settings dataclass with: `ANTHROPIC_API_KEY`, `CLAUDE_MODEL`, `QDRANT_HOST`, `QDRANT_PORT`, `ORTHANC_HOST`, `ORTHANC_PORT`, `FHIR_BASE_URL`, `RXNORM_API_URL`, `DRUGBANK_API_KEY`, `PUBMED_API_KEY`, `NEO4J_URI`, `POSTGRES_HOST`, `POSTGRES_DB`, `ENCRYPTION_KEY`
- [ ] Create `backend/main.py` — FastAPI app entry point with CORS middleware, health endpoint (`GET /health`), agent listing endpoint (`GET /agents`), and lifespan startup/shutdown hooks
- [ ] Create `backend/agents/__init__.py`
- [ ] Create `backend/models/__init__.py`
- [ ] Create `backend/integrations/__init__.py`
- [ ] Test: `cd backend && uvicorn main:app --host 0.0.0.0 --port 8000` — verify `GET /health` returns 200

### 1.3 FastAPI Backend — Base Agent Class
- [ ] Create `backend/agents/base_agent.py` — define `BaseAgent` abstract class with:
  - Properties: `agent_id`, `name`, `status` (Active/Idle), `skills` list, `queue` count, `models_used` list, `color` (accent hex)
  - Abstract method: `async execute_skill(skill_name: str, params: dict) -> dict`
  - Abstract method: `async chat(message: str, context: dict) -> AsyncGenerator[str, None]` (streaming)
  - Method: `get_info() -> dict` returning agent metadata
  - Method: `log_audit(request, model, confidence, action)` — write to PostgreSQL audit table
- [ ] Create `backend/agents/coordinator_agent.py` — implement `CoordinatorAgent(BaseAgent)` with:
  - `route_to_agent(message: str) -> str` — analyze message to determine which specialist agent to invoke (uses Claude API)
  - `build_consensus(agent_results: list[dict]) -> dict` — merge results from multiple agents, flag disagreements
  - `safety_check(result: dict) -> dict` — verify confidence > 0.7, check for critical flags, enforce escalation rules
  - `escalate(patient_id: str, reason: str)` — auto-alert attending physician for ESI 1-2 or critical findings

### 1.4 FastAPI Backend — API Endpoints
- [ ] Implement `GET /agents` — return list of all 8 agents with id, name, status, skills, queue, color
- [ ] Implement `GET /agents/{id}` — return single agent detail
- [ ] Implement `POST /agents/{id}/chat` — streaming chat endpoint using SSE (Server-Sent Events), routes through Coordinator first
- [ ] Implement `POST /agents/{id}/execute` — execute a specific skill with JSON params, return structured result
- [ ] Implement `GET /skills` — list all registered SKILL.md files from `~/.openclaw/workspace/skills/`
- [ ] Implement `POST /triage/assess` — accept patient data (complaint, vitals, history), invoke Triage Agent, return ESI score + routing
- [ ] Implement `POST /radiology/analyze` — accept image upload (multipart/form-data), invoke Radiology Agent, return findings + report
- [ ] Implement `POST /health` — return system health with agent statuses, model availability, database connectivity

### 1.5 Triage Agent Implementation
- [ ] Create `backend/agents/triage_agent.py` — implement `TriageAgent(BaseAgent)`:
  - `skills`: `["esi_scoring", "red_flag_detection", "patient_routing", "emergency_alert"]`
  - `models_used`: `["ClinicalBERT", "Claude API"]`
- [ ] Implement `esi_scoring` skill:
  - Accept: chief complaint (str), vitals (dict: hr, bp_sys, bp_dia, spo2, temp, rr), pain_scale (int), duration (str), history (str), allergies (list), medications (list)
  - Call ClinicalBERT NER to extract medical entities (symptoms, conditions, medications, anatomical locations)
  - Check red flags list: cardiac (chest pain, syncope, arrest), respiratory (dyspnea, stridor, SpO2<90%), neurological (altered consciousness, stroke/FAST+, seizure, GCS<9), trauma (hemorrhage, burns>20% BSA), other (anaphylaxis, qSOFA>=2, overdose, obstetric emergency)
  - If ANY red flag detected → minimum ESI-2
  - Call Claude API with extracted entities + vitals + red flags → determine ESI 1-5 with reasoning chain
  - Return: esi_score, esi_label, red_flags[], routing_recommendation, wait_time_estimate, reasoning, confidence
- [ ] Implement `red_flag_detection` skill — extract and return all detected red flags with severity
- [ ] Implement `patient_routing` skill — based on ESI + complaint, recommend department (Resuscitation, Emergency, Urgent Care, General, etc.)
- [ ] Implement `emergency_alert` skill — for ESI 1-2: auto-send alert to attending physician (log + notification)
- [ ] Add safety rules enforcement: never downgrade ESI without clinician override, always include disclaimer, log full reasoning chain

### 1.6 Triage SKILL.md & A2UI Template
- [ ] Create `skills/triage/SKILL.md` — copy from `03-SKILL-Files.md` section 1 (triggers, process, models, safety rules, example)
- [ ] Create `skills/triage/skill.json` — `{"name": "triage", "version": "1.0", "agent": "triage"}`
- [ ] Copy to OpenClaw workspace: `cp -r skills/triage ~/.openclaw/workspace/skills/`
- [ ] Create `a2ui/templates/triage-dashboard.jsonl` — copy JSONL from `02-A2UI-Templates.md` section 1 (root → header → stats → queue → disclaimer)
- [ ] Test: push template to Canvas: `openclaw nodes canvas a2ui push --jsonl a2ui/templates/triage-dashboard.jsonl --node <node-id>`
- [ ] Test: push dynamic update with mock ESI counts via `dataModelUpdate`

### 1.7 MedImageInsight Model Deployment
- [ ] Clone MedImageInsight from HuggingFace: `git clone https://huggingface.co/lion-ai/MedImageInsights`
- [ ] Install dependencies: `cd MedImageInsights && uv sync`
- [ ] Create `backend/models/medimageinsight.py` — wrapper class:
  - `load_model(model_dir: str)` — load MedImageInsight (0.61B params)
  - `classify_image(image: PIL.Image, labels: list[str]) -> list[dict]` — zero-shot classification, return label + confidence pairs
  - `generate_embedding(image: PIL.Image) -> list[float]` — generate 768/1024-dim embedding vector
  - `batch_classify(images: list[PIL.Image], labels: list[str]) -> list[list[dict]]` — batch processing
- [ ] Define modality-specific label sets in config: chest_xray (10 labels), brain_mri (8 labels), chest_ct (8 labels), msk (7 labels), dermatology (7 labels)
- [ ] Test: load model, classify a sample chest X-ray image, verify confidence scores returned

### 1.8 MedSigLIP Model Deployment
- [ ] Create `backend/models/medsiglib.py` — wrapper for MedSigLIP (400M params):
  - `load_model()` — load from HuggingFace
  - `triage_image(image: PIL.Image) -> str` — fast modality classification (X-ray, MRI, CT, ultrasound, dermoscopy, OCT, fundus, histopathology, mammography)
  - `route_to_specialist(modality: str) -> str` — map modality to agent/skill
- [ ] Test: classify a sample image, verify modality detection

### 1.9 Radiology Agent Implementation
- [ ] Create `backend/agents/radiology_agent.py` — implement `RadiologyAgent(BaseAgent)`:
  - `skills`: `["xray_analysis", "mri_interpretation", "ct_review", "report_gen", "evidence_search"]`
  - `models_used`: `["MedSigLIP", "MedImageInsight", "MedGemma 4B", "Qdrant"]`
- [ ] Implement `xray_analysis` skill:
  - Accept: image (file upload), patient_info (dict: name, age, gender)
  - Step 1: MedSigLIP → identify modality, confirm chest X-ray
  - Step 2: MedImageInsight → zero-shot classify against chest_xray labels, generate embedding
  - Step 3: Store embedding in Qdrant, query KNN for 3-5 similar historical cases
  - Step 4: MedGemma 4B → generate structured findings narrative from classification results
  - Step 5: Safety check — flag any finding with confidence < 0.7 for mandatory review
  - Return: findings[] (text, confidence, severity), similar_cases[] (id, similarity_score), recommendation, overall_confidence
- [ ] Implement `evidence_search` skill — KNN query in Qdrant for similar cases by embedding
- [ ] Implement `report_gen` skill — call MedGemma 4B with findings to generate full radiology report text
- [ ] Add safety: auto-alert for critical findings (pneumothorax, stroke, hemorrhage), always include confidence scores, log all analyses

### 1.10 Radiology SKILL.md & A2UI Template
- [ ] Create `skills/radiology/SKILL.md` — copy from `03-SKILL-Files.md` section 2
- [ ] Create `skills/radiology/skill.json` — `{"name": "radiology", "version": "1.0", "agent": "radiology"}`
- [ ] Copy to OpenClaw workspace: `cp -r skills/radiology ~/.openclaw/workspace/skills/`
- [ ] Create `a2ui/templates/radiology-report.jsonl` — copy JSONL from `02-A2UI-Templates.md` section 2 (split-panel: left=patient+findings+classification, right=evidence+recommendation+actions)
- [ ] Test: push template and verify rendering

### 1.11 Qdrant Vector Database Setup
- [ ] Add Qdrant to `docker-compose.yml`: image `qdrant/qdrant:latest`, port `6333`, volume `qdrant_data`
- [ ] Start Qdrant: `docker-compose up -d qdrant`
- [ ] Create `backend/integrations/qdrant_client.py` — wrapper:
  - `connect(host, port)` — initialize Qdrant client
  - `create_collection(name: str, vector_size: int)` — create collection with cosine distance
  - `upsert_embedding(collection: str, id: str, vector: list[float], metadata: dict)` — store image embedding with metadata (patient_id, modality, findings, diagnosis)
  - `search_similar(collection: str, query_vector: list[float], top_k: int) -> list[dict]` — KNN search, return matches with similarity scores
- [ ] Create collection `medical_images` with vector size matching MedImageInsight embedding dimension
- [ ] Test: insert a sample embedding, query KNN, verify results returned

### 1.12 PostgreSQL Database Setup
- [ ] Add PostgreSQL 16 to `docker-compose.yml`: port `5432`, env `POSTGRES_DB=medassist`, volume `pgdata`
- [ ] Start PostgreSQL: `docker-compose up -d postgres`
- [ ] Create database schema — tables:
  - `audit_log` (id, timestamp, agent_id, skill_name, request_summary, model_used, confidence, clinician_action, clinician_id, response_time_ms)
  - `patients` (id, name, age, gender, medical_history_json, allergies_json, medications_json, created_at)
  - `triage_assessments` (id, patient_id, esi_score, red_flags_json, routing, reasoning, confidence, clinician_override, created_at)
  - `radiology_reports` (id, patient_id, modality, findings_json, similar_cases_json, recommendation, overall_confidence, clinician_action, created_at)
- [ ] Create database connection utility in `backend/config.py` using `asyncpg` or `sqlalchemy[asyncio]`
- [ ] Test: connect, create tables, insert/query test record

### 1.13 Docker & Infrastructure Setup
- [ ] Create `infrastructure/docker-compose.yml` with services: `api` (FastAPI), `postgres`, `qdrant`, `orthanc`, `neo4j` (see 04-Project-Setup.md for full config)
- [ ] Create `infrastructure/Dockerfile` for FastAPI app: Python 3.10 base, copy backend/, install requirements, expose 8000, CMD uvicorn
- [ ] Create `infrastructure/Dockerfile.models` for model serving: NVIDIA CUDA base, install torch + transformers, copy model wrappers, expose inference port
- [ ] Test: `docker-compose up -d` — verify all services start and are reachable
- [ ] Create `infrastructure/k8s/namespace.yaml` — namespace `medassist`
- [ ] Create `infrastructure/k8s/deployment-api.yaml` — FastAPI deployment with 2 replicas, resource limits, health probes
- [ ] Create `infrastructure/k8s/deployment-qdrant.yaml` — Qdrant StatefulSet with persistent volume
- [ ] Create `infrastructure/k8s/service.yaml` — ClusterIP services for api, qdrant, postgres
- [ ] Create `infrastructure/k8s/ingress.yaml` — Traefik ingress rules for external access

### 1.14 ClinicalBERT NER Setup
- [ ] Create `backend/models/clinical_bert.py` — wrapper for ClinicalBERT (110M params):
  - `load_model()` — load from HuggingFace (`emilyalsentzer/Bio_ClinicalBERT` or medical NER variant)
  - `extract_entities(text: str) -> dict` — return extracted: symptoms[], conditions[], medications[], allergies[], anatomical_locations[], temporal_indicators[]
  - `extract_symptoms(text: str) -> list[dict]` — focused symptom extraction with spans
- [ ] Test: pass sample clinical text, verify entity extraction output

### 1.15 Phase 1 Integration Testing
- [ ] End-to-end test: POST patient data to `/triage/assess` → verify ESI score, red flags, routing returned
- [ ] End-to-end test: POST chest X-ray to `/radiology/analyze` → verify findings with confidence scores, KNN results, report text returned
- [ ] Verify audit log entries written to PostgreSQL for both operations
- [ ] Verify A2UI templates push correctly to OpenClaw Canvas
- [ ] Test Coordinator routing: send ambiguous message → verify correct agent selected

---

## Phase 2: Core Agents (Weeks 5-8)

### 2.1 Pharmacy Agent Implementation
- [ ] Create `backend/agents/pharmacy_agent.py` — implement `PharmacyAgent(BaseAgent)`:
  - `skills`: `["drug_interaction", "dosage_calc", "contraindication", "med_reconciliation"]`
  - `models_used`: `["Claude API", "RxNorm API", "DrugBank API", "FHIR R4"]`
- [ ] Implement `drug_interaction` skill:
  - Accept: drug_names (list[str]), patient_id (optional, for FHIR lookup)
  - Step 1: Resolve each drug name to RxNorm CUI via RxNorm API (`/rxcui.json?name=...`)
  - Step 2: Query DrugBank API for known interactions between all drug pairs
  - Step 3: If patient_id provided, cross-reference with FHIR patient data (allergies, conditions, age, pregnancy status)
  - Step 4: Classify each interaction severity: Critical (life-threatening, contraindicated), Major (significant risk), Moderate (dose adjustment), Minor (awareness only)
  - Step 5: For Critical interactions: set `blocked: true` — requires physician override with documented reason
  - Return: interactions[] (drug_a, drug_b, severity, description, evidence_source, blocked), alternatives[] (suggested safe substitutes)
- [ ] Implement `dosage_calc` skill — accept drug, patient weight/age/renal function → calculate appropriate dose range
- [ ] Implement `contraindication` skill — check drug against patient conditions, allergies, pregnancy status
- [ ] Implement `med_reconciliation` skill — compare current meds list vs new prescription, flag duplicates, interactions, gaps
- [ ] Add safety: critical interactions BLOCK workflow, log all checks, flag polypharmacy (5+ medications)

### 2.2 RxNorm Integration
- [ ] Create `backend/integrations/rxnorm_client.py`:
  - `resolve_drug_name(name: str) -> dict` — call RxNorm REST API (`https://rxnav.nlm.nih.gov/REST/rxcui.json`), return CUI + normalized name
  - `get_drug_info(rxcui: str) -> dict` — get drug properties, ingredients, dose forms
  - `find_interactions(rxcui_list: list[str]) -> list[dict]` — call `/interaction/list.json`, return all pairwise interactions
- [ ] Test: resolve "warfarin" → CUI, query interaction with "ibuprofen", verify critical interaction returned

### 2.3 DrugBank Integration
- [ ] Create `backend/integrations/drugbank_client.py`:
  - `search_drug(name: str) -> dict` — search DrugBank by name
  - `get_interactions(drugbank_id: str) -> list[dict]` — get all known interactions for a drug
  - `get_contraindications(drugbank_id: str) -> list[dict]` — get contraindication list
- [ ] Test: lookup warfarin, verify interaction data returned

### 2.4 Pharmacy SKILL.md & A2UI Template
- [ ] Create `skills/pharmacy/SKILL.md` — copy from `03-SKILL-Files.md` section 3
- [ ] Create `skills/pharmacy/skill.json`
- [ ] Copy to OpenClaw workspace
- [ ] Create `a2ui/templates/drug-alert.jsonl` — copy from `02-A2UI-Templates.md` section 3 (drug pair display, severity badge, interaction detail, evidence card, override/alternative/cancel buttons)
- [ ] Implement `POST /pharmacy/check` API endpoint
- [ ] Test: check warfarin + ibuprofen → verify Critical alert with block

### 2.5 Documentation Agent Implementation
- [ ] Create `backend/agents/documentation_agent.py` — implement `DocumentationAgent(BaseAgent)`:
  - `skills`: `["soap_notes", "discharge_summary", "icd10_coding", "referral_letter"]`
  - `models_used`: `["Claude API"]`
- [ ] Implement `soap_notes` skill:
  - Accept: patient_id, encounter_data (dict with transcript, triage_output, radiology_output, pharmacy_output, monitoring_output)
  - Collect data from all contributing agents
  - Call Claude API to generate SOAP note: S (patient's words, HPI), O (vitals, exam, labs, imaging), A (diagnosis, differentials), P (treatment, meds, follow-up)
  - Auto-suggest ICD-10 codes from Assessment section
  - Return: soap_sections (dict with s, o, a, p text), icd10_codes[] (code, description, confidence), draft_status: "pending_review"
- [ ] Implement `discharge_summary` skill — generate from full encounter history
- [ ] Implement `icd10_coding` skill — extract ICD-10 codes from clinical text using Claude
- [ ] Implement `referral_letter` skill — generate formatted referral letter
- [ ] Add safety: always present as draft, never finalize without clinician approval, include all agent sources

### 2.6 Documentation SKILL.md & A2UI Template
- [ ] Create `skills/documentation/SKILL.md` — copy from `03-SKILL-Files.md` section 5
- [ ] Create `skills/documentation/skill.json`
- [ ] Copy to OpenClaw workspace
- [ ] Create `a2ui/templates/clinical-notes.jsonl` — copy from `02-A2UI-Templates.md` section 5 (SOAP sections as editable TextFields, ICD-10 codes list, finalize/draft/export buttons)
- [ ] Implement `POST /documentation/generate` API endpoint
- [ ] Test: generate SOAP note from mock encounter data

### 2.7 MedGemma 4B Model Deployment
- [ ] Create `backend/models/medgemma.py` — wrapper for MedGemma 4B:
  - `load_model(model_name: str, device: str)` — load MedGemma 4B from HuggingFace (Google)
  - `generate_report(findings: list[dict], modality: str, patient_info: dict) -> str` — generate radiology report narrative
  - `clinical_reasoning(prompt: str, context: dict) -> str` — general clinical reasoning (for 27B, added later)
- [ ] Configure GPU memory allocation for 4B model (single GPU sufficient)
- [ ] Test: pass sample findings → verify structured report text generated

### 2.8 Orthanc DICOM Server Setup
- [ ] Add Orthanc to `docker-compose.yml`: image `orthancteam/orthanc:latest`, ports `8042` (web) + `4242` (DICOM), volume `orthanc_data`
- [ ] Start Orthanc: `docker-compose up -d orthanc`
- [ ] Create `backend/integrations/dicom_client.py`:
  - `upload_study(dicom_file: bytes) -> str` — upload DICOM to Orthanc, return study ID
  - `get_study(study_id: str) -> dict` — retrieve study metadata
  - `get_image(instance_id: str) -> PIL.Image` — retrieve image as PIL for model input
  - `list_studies(patient_id: str) -> list[dict]` — list all studies for a patient
- [ ] Test: upload a sample DICOM file, retrieve it, convert to image for classification

### 2.9 Drug Alert & Vitals A2UI Interfaces
- [ ] Verify drug-alert.jsonl renders correctly with dynamic data binding
- [ ] Create `a2ui/templates/patient-vitals.jsonl` — copy from `02-A2UI-Templates.md` section 4 (6 vital cards: HR, BP, SpO2, Temp, RR, MEWS + trend + alert + actions)
- [ ] Test real-time vitals update via `dataModelUpdate` every 30 seconds with sample data
- [ ] Test alert card visibility when MEWS > 3

### 2.10 Human-in-the-Loop Approval Workflows
- [ ] Implement approval action handlers in FastAPI:
  - `POST /actions/approve` — clinician approves AI output, log to audit trail
  - `POST /actions/flag` — clinician flags for senior review, escalate
  - `POST /actions/escalate` — immediate escalation to attending
  - `POST /actions/override` — physician overrides drug block with documented reason
- [ ] Create `approval_log` database table: id, action_type, agent_id, clinician_id, reason, original_output_json, timestamp
- [ ] Wire A2UI button actions to API endpoints
- [ ] Test: approve a radiology report → verify audit log entry; override a drug interaction → verify reason captured

### 2.11 Phase 2 Integration Testing
- [ ] End-to-end: POST drug list to `/pharmacy/check` → verify interaction alerts with severity classification
- [ ] End-to-end: POST encounter data to `/documentation/generate` → verify SOAP note with ICD-10 codes
- [ ] Test critical drug interaction blocking: verify workflow blocked, override requires reason
- [ ] Test DICOM upload → radiology analysis pipeline
- [ ] Verify all A2UI templates render and update dynamically

---

## Phase 3: Advanced Agents (Weeks 9-12)

### 3.1 Monitoring Agent Implementation
- [ ] Create `backend/agents/monitoring_agent.py` — implement `MonitoringAgent(BaseAgent)`:
  - `skills`: `["vital_tracking", "mews_score", "anomaly_detection", "alert_gen"]`
  - `models_used`: `["Time-series ML", "Claude API"]`
- [ ] Implement `mews_score` skill:
  - Accept: vitals (hr, bp_sys, bp_dia, spo2, temp, rr)
  - Calculate MEWS per standard scoring: HR (<40 or >130 = 3pts, 41-50 or 111-130 = 2pts, 51-100 = 0pts, 101-110 = 1pt), BP systolic (<70 = 3pts, 71-80 = 2pts, 81-100 = 1pt, 101-199 = 0pts, >200 = 2pts), RR (<9 = 2pts, 9-14 = 0pts, 15-20 = 1pt, 21-29 = 2pts, >29 = 3pts), Temp (<35 = 2pts, 35-38.4 = 0pts, >38.5 = 2pts)
  - Return: mews_total, component_scores, alert_level (Normal 0-2, Increased 3-4, Critical 5+)
- [ ] Implement `vital_tracking` skill:
  - Accept: patient_id, vitals, timestamp
  - Store in time-series table (PostgreSQL or dedicated TSDB)
  - Maintain 6-hour rolling window
  - Return: current_vitals, trend_data (last 6 hours), baseline_comparison
- [ ] Implement `anomaly_detection` skill:
  - Compare current readings against patient baseline (rolling average)
  - Detect sudden changes: HR change > 30bpm, BP change > 30mmHg, SpO2 drop > 5%, Temp change > 1.5C
  - Return: anomalies[] (vital, current_value, baseline, deviation, severity)
- [ ] Implement `alert_gen` skill:
  - MEWS 0-2: return status "Normal", action "Routine monitoring"
  - MEWS 3-4: return status "Increased concern", action "Notify nurse, increase monitoring frequency"
  - MEWS >= 5: return status "CRITICAL", action "Immediate medical review", trigger auto-alert to attending
  - SpO2 < 90%: return status "CRITICAL" regardless of MEWS
- [ ] Add safety: never reduce alert level without clinician acknowledgment, auto-escalate MEWS >= 5

### 3.2 Monitoring SKILL.md & A2UI
- [ ] Create `skills/monitoring/SKILL.md` — copy from `03-SKILL-Files.md` section 4
- [ ] Create `skills/monitoring/skill.json`
- [ ] Copy to OpenClaw workspace
- [ ] Implement `POST /monitoring/vitals` API endpoint — accept vitals, calculate MEWS, store, check alerts
- [ ] Test: submit vitals with MEWS=5 → verify auto-alert triggered
- [ ] Test: submit SpO2=88% → verify immediate alert regardless of MEWS

### 3.3 Research Agent Implementation
- [ ] Create `backend/agents/research_agent.py` — implement `ResearchAgent(BaseAgent)`:
  - `skills`: `["guideline_search", "evidence_synthesis", "trial_match", "literature_review"]`
  - `models_used`: `["Claude API", "PubMed API"]`
- [ ] Implement `guideline_search` skill:
  - Accept: clinical_question (str), condition (str, optional)
  - Formulate PubMed search query from clinical question using Claude
  - Search PubMed API: `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi` + `efetch.fcgi`
  - Filter by: recency (prefer last 5 years), evidence level (meta-analysis > RCT > cohort > case), relevance score
  - Return: results[] (title, authors, journal, year, pmid, abstract, evidence_level), search_query_used
- [ ] Implement `evidence_synthesis` skill — use Claude to synthesize findings from multiple PubMed results into concise summary with citations
- [ ] Implement `trial_match` skill — search ClinicalTrials.gov API for active/recruiting trials matching patient demographics (age, condition, location)
- [ ] Implement `literature_review` skill — comprehensive search + synthesis for a specific topic
- [ ] Add safety: always cite sources, note evidence level, present as "evidence suggests..." not recommendation, flag conflicting evidence

### 3.4 PubMed Integration
- [ ] Create `backend/integrations/pubmed_client.py`:
  - `search(query: str, max_results: int, min_date: str) -> list[dict]` — search PubMed, return PMIDs + metadata
  - `fetch_abstracts(pmids: list[str]) -> list[dict]` — fetch full abstracts for list of PMIDs
  - `format_citation(article: dict) -> str` — format as standard citation
- [ ] Test: search "chest x-ray pneumonia treatment guidelines" → verify relevant results returned

### 3.5 Research SKILL.md & A2UI
- [ ] Create `skills/research/SKILL.md` — copy from `03-SKILL-Files.md` section 6
- [ ] Create `skills/research/skill.json`
- [ ] Copy to OpenClaw workspace
- [ ] Create `a2ui/templates/evidence-panel.jsonl` — evidence cards with title, citation, evidence level badge, abstract summary
- [ ] Implement `POST /research/search` API endpoint
- [ ] Test: search clinical question → verify evidence panel with citations

### 3.6 Diagnostic Agent Implementation
- [ ] Create `backend/agents/diagnostic_agent.py` — implement `DiagnosticAgent(BaseAgent)`:
  - `skills`: `["differential_dx", "test_recommendation", "pattern_recognition", "rare_disease"]`
  - `models_used`: `["MedGemma 27B", "Claude API"]`
- [ ] Implement `differential_dx` skill:
  - Accept: symptoms[] (from ClinicalBERT), vitals, lab_results, imaging_results, patient_history
  - Call MedGemma 27B for clinical reasoning: generate ranked differential diagnosis list
  - Cross-reference with Claude API for reasoning verification
  - Return: differentials[] (diagnosis, probability, supporting_evidence[], contradicting_evidence[]), recommended_tests[]
- [ ] Implement `test_recommendation` skill — based on differential list, recommend appropriate lab/imaging tests
- [ ] Implement `pattern_recognition` skill — identify symptom patterns matching known conditions
- [ ] Implement `rare_disease` skill — use MedGemma 27B for rare disease consideration when common diagnoses don't fit

### 3.7 FHIR R4 EHR Integration
- [ ] Create `backend/integrations/fhir_client.py`:
  - `get_patient(patient_id: str) -> dict` — fetch patient demographics from FHIR R4 API
  - `get_conditions(patient_id: str) -> list[dict]` — fetch active conditions
  - `get_medications(patient_id: str) -> list[dict]` — fetch current medications
  - `get_allergies(patient_id: str) -> list[dict]` — fetch allergy/intolerance list
  - `get_observations(patient_id: str, category: str) -> list[dict]` — fetch vitals, labs
  - `create_observation(patient_id: str, observation: dict) -> str` — write vital signs back to EHR
  - `create_document_reference(patient_id: str, note: dict) -> str` — write clinical note to EHR
- [ ] Configure FHIR base URL and auth (OAuth2 token exchange)
- [ ] Test with FHIR sandbox (HAPI FHIR or Epic sandbox): query patient, verify data returned

### 3.8 MedGemma 27B Model Deployment
- [ ] Extend `backend/models/medgemma.py` — add MedGemma 27B support:
  - `load_27b_model(device_map: str)` — load with multi-GPU device mapping
  - `clinical_reasoning(patient_data: dict, question: str) -> dict` — complex clinical reasoning with EHR + multimodal context
  - `differential_diagnosis(symptoms: list, vitals: dict, history: dict) -> list[dict]` — ranked differential dx
- [ ] Configure GPU memory allocation for 27B model (requires multi-GPU or quantization)
- [ ] Test: pass complex case → verify differential diagnosis list

### 3.9 Neo4j Knowledge Graph Setup
- [ ] Add Neo4j 5 to `docker-compose.yml`: ports `7474` (web) + `7687` (bolt), env `NEO4J_AUTH`, volume `neo4j_data`
- [ ] Start Neo4j: `docker-compose up -d neo4j`
- [ ] Design graph schema:
  - Nodes: `Disease` (ICD-10 code, name, synonyms), `Symptom` (SNOMED code, name), `Drug` (RxNorm CUI, name), `LabTest` (LOINC code, name), `Procedure` (CPT code, name)
  - Relationships: `(:Symptom)-[:INDICATES]->(:Disease)`, `(:Drug)-[:TREATS]->(:Disease)`, `(:Drug)-[:INTERACTS_WITH]->(:Drug)`, `(:Disease)-[:REQUIRES_TEST]->(:LabTest)`, `(:Disease)-[:CLASSIFIED_AS {system: "ICD-10"}]->(:Code)`
- [ ] Load SNOMED-CT terminology subset (common clinical terms)
- [ ] Load ICD-10/ICD-11 code hierarchy
- [ ] Create Neo4j client utility for graph queries
- [ ] Test: query symptoms → matching diseases, verify graph traversal

### 3.10 Coordinator Agent — Consensus Building
- [ ] Enhance `coordinator_agent.py` with parallel consensus:
  - `fan_out(message: str, agents: list[str]) -> list[dict]` — send request to multiple agents concurrently (asyncio.gather)
  - `build_consensus(results: list[dict]) -> dict` — analyze agreement/disagreement across agent outputs
  - `resolve_disagreement(results: list[dict]) -> dict` — if agents disagree, present both findings with confidence scores, flag for human review
  - `generate_combined_report(consensus: dict) -> dict` — merge into unified report for A2UI
- [ ] Test: send complex case to Radiology + Diagnostic + Research → verify consensus report with disagreement flagging

### 3.11 Phase 3 Integration Testing
- [ ] End-to-end: submit vitals stream → verify MEWS calculation, trend tracking, auto-alerts
- [ ] End-to-end: clinical research query → verify evidence panel with PubMed citations
- [ ] End-to-end: complex case → Coordinator fans out to 3 agents → consensus report generated
- [ ] Verify FHIR patient data flows through to all agents that need it
- [ ] Verify Neo4j knowledge graph queries return relevant clinical relationships

---

## Phase 4: Production & Compliance (Weeks 13-16)

### 4.1 HIPAA Encryption & Data Security
- [ ] Implement AES-256 encryption at rest for PostgreSQL (use `pgcrypto` extension or application-level encryption)
- [ ] Configure TLS 1.3 for all service-to-service communication
- [ ] Implement PHI detection in requests — route PHI-containing data to LM Studio (local) instead of Claude API (cloud)
- [ ] Create PHI filter utility: scan text for patient identifiers (name, DOB, SSN, MRN) before sending to cloud LLMs
- [ ] Configure PostgreSQL SSL connections
- [ ] Enable Qdrant TLS
- [ ] Enable Orthanc DICOM TLS (port 4242)
- [ ] Generate and manage TLS certificates (use cert-manager in K8s or manual provisioning)
- [ ] Document BAA (Business Associate Agreement) requirements for cloud services

### 4.2 Audit Trail System
- [ ] Enhance audit logging to capture ALL operations:
  - Every agent invocation: timestamp, agent_id, skill_name, model_used, input_hash (not raw PHI), confidence_score, response_time_ms
  - Every clinician action: approve/flag/escalate/override with clinician_id, reason, timestamp
  - Every data access: patient_id, data_type accessed, accessor_id, timestamp
- [ ] Create audit dashboard query endpoints:
  - `GET /audit/agent/{id}` — audit trail for specific agent
  - `GET /audit/patient/{id}` — all AI interactions for a patient
  - `GET /audit/clinician/{id}` — all actions by a clinician
  - `GET /audit/export` — export audit log (CSV/JSON) for compliance reporting
- [ ] Implement audit log retention policy (minimum 6 years for HIPAA)
- [ ] Test: run full workflow → verify complete audit trail captured

### 4.3 LM Studio PHI Integration
- [ ] Implement PHI routing logic in Coordinator Agent:
  - If request contains PHI → route to LM Studio local model
  - If request is de-identified → allow Claude API (cloud)
  - Log routing decision in audit trail
- [ ] Create `backend/models/lm_studio_client.py`:
  - `chat(messages: list[dict], model: str) -> str` — call LM Studio OpenAI-compatible API at `http://127.0.0.1:1234/v1/chat/completions`
  - `stream_chat(messages: list[dict], model: str) -> AsyncGenerator[str, None]` — streaming response
- [ ] Test: send PHI request → verify routed to local model, NOT to cloud

### 4.4 OAuth2 Authentication & Authorization
- [ ] Configure OAuth2-Proxy with Azure AD for API authentication
- [ ] Implement role-based access control (RBAC):
  - `physician` — full access, can override drug blocks, approve reports
  - `nurse` — read access, can acknowledge alerts, cannot override drug blocks
  - `technician` — limited access to radiology upload and DICOM
  - `admin` — system configuration, audit access
- [ ] Add auth middleware to all FastAPI endpoints
- [ ] Configure JWT token validation
- [ ] Test: authenticate as each role → verify correct access permissions

### 4.5 Kubernetes Production Deployment
- [ ] Finalize all K8s manifests in `infrastructure/k8s/`:
  - `namespace.yaml` — namespace `medassist`
  - `deployment-api.yaml` — FastAPI: 3 replicas, resource limits (CPU/memory), readiness/liveness probes on `/health`, rolling update strategy
  - `deployment-models.yaml` — model server: GPU node selector, resource limits with GPU requests, health probes
  - `deployment-qdrant.yaml` — Qdrant StatefulSet: persistent volume claim, single replica
  - `deployment-orthanc.yaml` — Orthanc: persistent volume for DICOM storage
  - `service.yaml` — ClusterIP services for all deployments
  - `ingress.yaml` — Traefik IngressRoute with TLS termination, rate limiting annotations
  - `argocd-app.yaml` — ArgoCD Application for GitOps deployment
- [ ] Create Kubernetes secrets for all credentials: `ANTHROPIC_API_KEY`, `POSTGRES_PASSWORD`, `NEO4J_PASSWORD`, `ENCRYPTION_KEY`, `DRUGBANK_API_KEY`, `PUBMED_API_KEY`
- [ ] Configure Horizontal Pod Autoscaler (HPA) for FastAPI deployment
- [ ] Configure persistent volumes for PostgreSQL, Qdrant, Orthanc, Neo4j
- [ ] Deploy to K8s cluster: `kubectl apply -f infrastructure/k8s/`
- [ ] Verify all pods running: `kubectl get pods -n medassist`
- [ ] Configure ArgoCD for automated GitOps deployments

### 4.6 Bias Monitoring & Fairness
- [ ] Implement MedImageInsight fairness metrics collection:
  - Track classification accuracy by demographic: age groups, gender, ethnicity (where available)
  - Log model predictions with anonymized demographic data
- [ ] Create bias monitoring dashboard/report:
  - `GET /monitoring/fairness` — return accuracy metrics by demographic group
  - Flag if accuracy variance > 5% between groups
- [ ] Schedule quarterly evaluation process (documented procedure)

### 4.7 Frontend React Application Scaffold
- [ ] Initialize React app in `frontend/`: `npx create-react-app frontend` or Vite setup
- [ ] Install dependencies: `react-router-dom`, `axios`, `recharts` (for vitals charts)
- [ ] Move `medassist-agent-interface.jsx` component into `frontend/src/components/MedAssistDashboard.jsx`
- [ ] Replace mock data with API calls to FastAPI backend:
  - Fetch agents from `GET /agents`
  - Fetch triage queue from `GET /triage/queue`
  - Fetch radiology reports from `GET /radiology/reports`
  - Fetch vitals from `GET /monitoring/vitals`
  - Connect chat to `POST /agents/{id}/chat` with SSE streaming
- [ ] Add authentication flow (OAuth2 redirect to Azure AD)
- [ ] Add real-time vitals chart using Recharts (replace static bar chart)
- [ ] Build and test: `npm run build`

### 4.8 Clinical Scenario Testing
- [ ] Create test suite with clinical scenarios:
  - **Scenario 1 (ESI-1):** 67F, crushing chest pain, diaphoretic, BP 90/60, HR 110, SpO2 94% → Expected: ESI-1, auto-alert, resuscitation routing
  - **Scenario 2 (ESI-2):** 45M, stroke symptoms FAST+, onset 2hr → Expected: ESI-2, auto-alert, neurology routing
  - **Scenario 3 (ESI-3):** 32F, abdominal pain, fever 39.2C → Expected: ESI-3, labs + imaging needed, surgical consult
  - **Scenario 4 (Drug block):** Prescribe ibuprofen to patient on warfarin → Expected: Critical interaction, workflow BLOCKED, override required
  - **Scenario 5 (Radiology):** Chest X-ray with bilateral infiltrates → Expected: Findings with confidence, KNN cases, CT recommendation
  - **Scenario 6 (MEWS critical):** HR 135, BP 80/50, RR 32, Temp 39.5 → Expected: MEWS >= 7, immediate attending alert
  - **Scenario 7 (Consensus):** Complex case → 3 agents → verify consensus report with disagreement flagging
  - **Scenario 8 (PHI routing):** Request with patient name → verify routed to LM Studio NOT cloud
- [ ] Run all scenarios, document results, fix failures

### 4.9 EHR Sandbox Integration Testing
- [ ] Set up FHIR sandbox environment (Epic sandbox or HAPI FHIR test server)
- [ ] Test patient data retrieval: demographics, conditions, medications, allergies, observations
- [ ] Test data write-back: observations (vitals), document references (SOAP notes)
- [ ] Test with realistic patient data (synthetic, not real PHI)
- [ ] Document FHIR API compatibility notes for Epic and Cerner

### 4.10 Clinical Staff UAT (User Acceptance Testing)
- [ ] Prepare UAT test plan with 8-10 clinical scenarios
- [ ] Set up UAT environment (staging K8s namespace or dedicated docker-compose stack)
- [ ] Conduct UAT sessions with clinical staff:
  - Emergency physicians (triage + radiology)
  - Pharmacists (drug interaction checking)
  - Nurses (vitals monitoring + alerts)
  - Medical records staff (documentation + SOAP notes)
- [ ] Collect feedback: usability issues, clinical accuracy, missing features, safety concerns
- [ ] Create issue tickets for all UAT findings
- [ ] Address critical UAT findings before production

### 4.11 Production Go-Live
- [ ] Final security review: all endpoints authenticated, PHI encrypted, audit logging verified
- [ ] Performance load testing: simulate concurrent users, verify response times < 2s for standard queries
- [ ] Create production runbook: deployment steps, rollback procedure, monitoring alerts, on-call contacts
- [ ] Configure production monitoring: uptime checks on `/health`, alert on agent failures, alert on high MEWS scores
- [ ] Deploy to production K8s cluster via ArgoCD
- [ ] Verify all services healthy: `kubectl get pods -n medassist-prod`
- [ ] Conduct smoke test: run 2-3 clinical scenarios on production
- [ ] Announce go-live to clinical staff with training documentation

---

## Ongoing Maintenance

### M.1 Monitoring & Observability
- [ ] Set up centralized logging (ELK stack or Azure Monitor)
- [ ] Set up metrics collection (Prometheus + Grafana)
- [ ] Create dashboards: agent response times, model inference latency, error rates, queue depths
- [ ] Configure alerts: agent down > 5min, response time > 5s, error rate > 1%, disk usage > 80%

### M.2 Model Updates
- [ ] Track MedImageInsight model updates on HuggingFace
- [ ] Track MedGemma model updates from Google
- [ ] Track Claude API model version updates from Anthropic
- [ ] Establish model update testing procedure: test on clinical scenarios before production deployment

### M.3 Quarterly Reviews
- [ ] Quarterly bias evaluation (MedImageInsight fairness metrics across demographics)
- [ ] Quarterly audit log review for compliance
- [ ] Quarterly clinical accuracy review with medical staff
- [ ] Update SKILL.md files based on clinical feedback
