# OpenClaw — MedAssist AI v2.0

## Project Overview

MedAssist AI is a comprehensive medical multi-agent platform built on **OpenClaw** with **A2UI** (Agent-to-User Interface) for intelligent healthcare assistance. It orchestrates 8 specialized AI agents for imaging, triage, clinical decision support, drug interaction, monitoring, documentation, and research—all through a unified, secure, and visually rich interface.

> **Critical**: This is a clinical decision SUPPORT system. ALL outputs require clinician verification. The system assists — it never decides. ESI 1-2 cases auto-escalate to the attending physician.

## Repository Structure

```
openclaw/
├── CLAUDE.md                                # This file
├── medassist-agent-interface.jsx             # React dashboard UI component (interactive mockup)
├── medassist-architecture-diagram.svg        # 9-layer system architecture diagram (SVG)
├── 01-MedAssist-AI-Architecture.md           # Full architecture, agent specs, roadmap, safety
├── 02-A2UI-Templates.md                      # A2UI JSONL templates for all interfaces
├── 03-SKILL-Files.md                         # Complete SKILL.md definitions for all agents
├── 04-Project-Setup.md                       # Project structure, quick start, env vars, API endpoints
└── frontend/                                 # Empty — not yet scaffolded
```

## Architecture (9 Layers)

```
Input Channels → OpenClaw Gateway → Coordinator Agent → Specialist Agents
     → SKILL.md Registry → AI Models → Data Layer → A2UI Canvas → Infrastructure
```

| Layer | Components | Responsibility |
|-------|-----------|----------------|
| 1. Input | WhatsApp, Slack/Teams, WebChat, Mobile, CLI, DICOM, FHIR, IoT | Accept requests |
| 2. Gateway | OpenClaw (`ws://127.0.0.1:18789`) | Auth, routing, rate limiting, HIPAA audit |
| 3. Coordinator | Coordinator Agent | Route to specialist, consensus, safety checks, escalation |
| 4. Specialists | 7 domain agents | Clinical tasks with SKILL.md |
| 5. SKILL.md | `~/.openclaw/workspace/skills/` | Triggers, processes, safety rules, A2UI output |
| 6. AI Models | MedImageInsight, MedGemma, ClinicalBERT, Claude, LM Studio | Inference |
| 7. Data | PostgreSQL, Neo4j, Qdrant, Orthanc, FHIR, RxNorm, PubMed, DrugBank | Storage + APIs |
| 8. A2UI Canvas | JSONL protocol (`surfaceUpdate → beginRendering → dataModelUpdate`) | Visual workspace |
| 9. Infrastructure | Kubernetes, Docker, ArgoCD, Azure, Traefik, OAuth2-Proxy | Deployment |

### Multi-Agent Patterns

- **Sequential** (simple): User → Gateway → Coordinator → Single Agent → A2UI
- **Parallel Consensus** (complex): Coordinator fans out to multiple agents, builds consensus, flags disagreements for human review

## Features

- 8 Medical AI Agents: Triage, Radiology, Diagnostic, Pharmacy, Monitoring, Documentation, Research, Coordinator
- A2UI Templates: JSONL-based UI for clinical workflows
- Multi-Agent Consensus: For complex medical cases
- Real-Time Monitoring: Vitals, alerts, and early warning
- Automated Documentation: SOAP notes, discharge summaries
- Evidence-Based Research: PubMed, guidelines, trial matching

### Data Flow Example (Chest X-Ray)

```
Doctor sends image → Gateway auth/log → Coordinator routes to Radiology →
SKILL.md loads xray_analysis → MedSigLIP (triage) → MedImageInsight (classify + embed) →
Qdrant KNN (evidence) → MedGemma 4B (report) → Safety check (confidence > 0.7?) →
A2UI radiology report → Doctor: Approve | Flag | Reassign → Audit log
```

## Agents

| Agent | Models | Key Skills | A2UI Screen |
|-------|--------|-----------|-------------|
| **Triage** | ClinicalBERT + Claude | ESI Scoring, Red Flag Detection, Patient Routing | Triage Dashboard |
| **Radiology** | MedImageInsight + MedGemma 4B | X-Ray/MRI/CT, Report Gen, KNN Evidence | Radiology Report |
| **Diagnostic** | MedGemma 27B + Claude | Differential Dx, Test Rec, Pattern Recognition | Diagnosis Panel |
| **Pharmacy** | Claude + RxNorm + DrugBank | Drug Interactions, Dosage Calc, Contraindications | Drug Alert |
| **Monitoring** | Time-Series ML + Claude | Vital Tracking, MEWS Score, Anomaly Detection | Vitals Monitor |
| **Documentation** | Claude API | SOAP Notes, Discharge Summary, ICD-10 Coding | SOAP Editor |
| **Research** | Claude + PubMed API | PubMed Search, Guideline Lookup, Trial Matching | Evidence Panel |
| **Coordinator** | Claude API | Agent Routing, Consensus, Safety Check, Escalation | Control Center |

## AI Models

| Model | Params | Purpose |
|-------|--------|---------|
| MedImageInsight | 0.61B | 14-domain image classification + embedding (HuggingFace: `lion-ai/MedImageInsights`) |
| MedGemma 27B | 27B | Clinical reasoning, EHR + multimodal (complex cases) |
| MedGemma 4B | 4B | CXR report generation, edge/real-time (single GPU) |
| MedSigLIP | 400M | Fast image triage/routing |
| ClinicalBERT | 110M | Medical NER, symptom extraction |
| Claude API | — | Primary LLM: reasoning + NLP (cloud, `claude-sonnet-4-20250514`) |
| LM Studio | — | HIPAA-safe local inference for PHI data |

## SKILL.md System

Each agent has a SKILL.md at `~/.openclaw/workspace/skills/<agent>/SKILL.md` with:

| Section | Purpose |
|---------|---------|
| `# Skill Name` | Title |
| `## When to Use` | Trigger keywords and contexts |
| `## Process` | Step-by-step execution logic |
| `## Models Used` | AI model dependencies |
| `## A2UI Output Format` | A2UI template for rendering |
| `## Safety Rules` | Non-negotiable constraints |
| `## Example` | Sample input/output |

Full definitions in [03-SKILL-Files.md](03-SKILL-Files.md).

## A2UI Interface Templates

Templates use JSONL protocol with three message types:
- `surfaceUpdate` — define components
- `beginRendering` — start rendering
- `dataModelUpdate` — push real-time data updates

6 templates defined in [02-A2UI-Templates.md](02-A2UI-Templates.md):
Triage Dashboard, Radiology Report, Drug Interaction Alert, Patient Vitals Monitor, Clinical Notes (SOAP), Evidence Panel

### CLI Commands

```bash
openclaw nodes canvas a2ui push --jsonl <template>.jsonl --node <node-id>
openclaw nodes canvas a2ui reset --node <node-id>
openclaw nodes canvas a2ui push --node <node-id> --text "Status message"
openclaw nodes list                    # Get node IDs
```

## Frontend (Dashboard UI)

Single React component (`MedAssistDashboard`) in [medassist-agent-interface.jsx](medassist-agent-interface.jsx) with 5 views:

- **Dashboard** — 4-column grid of 8 agent cards (icon, status, skills, queue)
- **Triage** — ESI 1-5 patient queue with color-coded severity and wait times
- **Radiology** — Split-panel report: findings + confidence, KNN cases, approve/flag/reassign
- **Vitals** — 3x2 grid (HR, BP, SpO2, Temp, RR, MEWS) + 6-hour trend chart
- **Agent Chat** — 3-panel: sidebar (skills), chat area, input bar

### UI Conventions

- React JSX with `useState` hooks, inline CSS styles
- Dark theme: `#0a1628` background, Inter/SF Pro/Arial fonts
- ESI color coding: `#ef4444` (Red/ESI-1) → `#f97316` (Orange/ESI-2) → `#eab308` (Yellow/ESI-3) → `#22c55e` (Green/ESI-4) → `#3b82f6` (Blue/ESI-5)
- Each agent has a unique accent color used consistently
- Mock data defined as static arrays/objects at module level
- Chat responses simulated with 500ms `setTimeout`
- All views include clinician verification disclaimer

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Agent Platform | OpenClaw (`npm install -g openclaw@latest`) |
| Agentic UI | A2UI v0.8 (built into OpenClaw Canvas) |
| Backend | Python + FastAPI (`uvicorn main:app --port 8000`) |
| LLM (Cloud) | Claude API (`claude-sonnet-4-20250514`) |
| LLM (Local) | LM Studio (HIPAA-safe PHI) |
| Database | PostgreSQL 16 |
| Knowledge Graph | Neo4j 5 (SNOMED-CT + ICD-10/11) |
| Vectors | Qdrant |
| DICOM | Orthanc |
| EHR | FHIR R4 APIs (Epic/Cerner) |
| Drugs | RxNorm + DrugBank APIs |
| Auth | OAuth2-Proxy + Azure AD |
| Encryption | AES-256 at rest, TLS 1.3 in transit |
| Deployment | Kubernetes + Docker + ArgoCD on Azure |

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/agents` | GET | List all agents with status and skills |
| `/agents/{id}` | GET | Get single agent details |
| `/agents/{id}/chat` | POST | Send message to agent (streaming) |
| `/agents/{id}/execute` | POST | Execute a specific skill |
| `/triage/assess` | POST | Submit patient for triage |
| `/radiology/analyze` | POST | Submit image for analysis |
| `/pharmacy/check` | POST | Check drug interactions |
| `/monitoring/vitals` | POST | Submit vital signs |
| `/documentation/generate` | POST | Generate clinical note |
| `/research/search` | POST | Search clinical evidence |
| `/health` | GET | System health check |

## Implementation Roadmap

- **Phase 1 (Weeks 1-4):** OpenClaw + Claude on K8s, Triage + Radiology skills, MedImageInsight, FastAPI + Qdrant
- **Phase 2 (Weeks 5-8):** Pharmacy + Documentation agents, MedGemma 4B, Orthanc, drug alert + vitals UI
- **Phase 3 (Weeks 9-12):** Monitoring + Research agents, FHIR, MedGemma 27B, Neo4j, Coordinator consensus
- **Phase 4 (Weeks 13-16):** HIPAA encryption, LM Studio, clinical testing, EHR sandbox, UAT, production deploy

## Safety & Compliance

| Requirement | Implementation |
|------------|----------------|
| Human-in-the-Loop | Every output has Approve/Flag/Escalate buttons. No auto-clinical actions. |
| Disclaimer | All responses: "AI-assisted — requires clinician verification" |
| Fail-Safe | ESI 1-2 auto-alert attending. Confidence < 0.7 = mandatory human review. |
| Critical Drug Interactions | BLOCK workflow until physician override with documented reason. |
| MEWS Alerts | MEWS >= 5 triggers automatic attending notification. SpO2 < 90% = immediate alert. |
| Audit Trail | PostgreSQL log: request, agent, model, confidence, clinician action, timestamp |
| PHI Protection | No PHI to cloud LLMs. PHI routed to LM Studio (local, encrypted). |
| HIPAA | AES-256 at rest, TLS 1.3 in transit, BAA signed |
| Bias Monitoring | MedImageInsight fairness metrics. Quarterly evaluation. |
| Regulatory | Decision support only. Not for diagnosis without FDA clearance. |

## Quick Start

```bash
npm install -g openclaw@latest
openclaw onboard --install-daemon
# Configure ~/.openclaw/openclaw.json with Anthropic API key
# See 04-Project-Setup.md for full setup guide
```
