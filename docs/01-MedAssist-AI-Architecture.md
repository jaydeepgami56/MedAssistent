# MedAssist AI Platform

## Medical Multi-Agent System — OpenClaw + A2UI + SKILL.md

**Version 2.0 | February 2026**

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [System Architecture](#2-system-architecture)
3. [Agent Interface Design (A2UI)](#3-agent-interface-design-a2ui)
4. [Agent Specifications](#4-agent-specifications)
5. [SKILL.md Definitions](#5-skillmd-definitions)
6. [Technology Stack](#6-technology-stack)
7. [Implementation Roadmap](#7-implementation-roadmap)
8. [Safety & Compliance](#8-safety--compliance)

---

## 1. Executive Summary

MedAssist AI is a comprehensive medical multi-agent platform built on **OpenClaw** with **A2UI** (Agent-to-User Interface) for delivering intelligent healthcare assistance. The platform orchestrates **8 specialized AI agents** for medical imaging analysis, triage prioritization, clinical decision support, drug interaction checking, patient monitoring, documentation, and clinical research — all through a unified, secure, and visually rich interface.

### Key Capabilities

- **MRI/X-Ray/CT report analysis** using MedImageInsight + MedGemma
- **ESI 1-5 triage scoring** with red flag detection and auto-escalation
- **Drug interaction checking** with severity-based workflow blocking
- **Real-time vital sign monitoring** with MEWS early warning
- **Automated clinical documentation** (SOAP notes, discharge summaries)
- **Evidence-based clinical research** (PubMed, guidelines, trial matching)
- **Multi-agent consensus** for complex cases

### Deliverables

- System architecture diagram (9-layer visual)
- Data flow sequences and multi-agent communication patterns
- 6 complete A2UI interface templates with JSONL
- Design system specification
- 8 agent specifications with models and skills
- 3 complete SKILL.md files
- Full technology stack
- 4-phase implementation roadmap
- Safety and compliance requirements

---

## 2. System Architecture

The architecture follows a **9-layer design** where each layer has a clear responsibility. Messages flow from input channels through the OpenClaw Gateway, routed by the Coordinator Agent to specialist agents, which use SKILL.md definitions and AI models to process requests and render results via A2UI Canvas.

### 2.1 Full System Architecture Diagram

> See `medassist-architecture-diagram.svg` for the complete visual diagram.

```
┌─────────────────────────────────────────────────────────────────────┐
│  LAYER 1: INPUT CHANNELS                                           │
│  WhatsApp │ Slack/Teams │ WebChat │ Mobile │ CLI │ DICOM │ FHIR │ IoT │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  LAYER 2: OPENCLAW GATEWAY (Control Plane)                         │
│  ws://127.0.0.1:18789 — Auth │ Routing │ Logging │ HIPAA Audit     │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  LAYER 3: COORDINATOR AGENT                                        │
│  Multi-Agent Orchestration │ Consensus │ Safety Checks │ Escalation │
└──┬──────┬──────┬──────┬──────┬──────┬──────┬────────────────────────┘
   │      │      │      │      │      │      │
   ▼      ▼      ▼      ▼      ▼      ▼      ▼
┌──────┐┌──────┐┌──────┐┌──────┐┌──────┐┌──────┐┌──────┐
│Triage││Radiol││Diagno││Pharma││Monito││ Docs ││Resear│  LAYER 4:
│Agent ││Agent ││Agent ││Agent ││Agent ││Agent ││Agent │  SPECIALIST
└──┬───┘└──┬───┘└──┬───┘└──┬───┘└──┬───┘└──┬───┘└──┬───┘  AGENTS
   │       │       │       │       │       │       │
┌─────────────────────────────────────────────────────────────────────┐
│  LAYER 5: SKILL.md REGISTRY                                        │
│  triage/ │ radiology/ │ diagnostic/ │ pharmacy/ │ monitoring/ │ ... │
│  ~/.openclaw/workspace/skills/                                      │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  LAYER 6: AI MODEL LAYER                                           │
│  MedImageInsight │ MedGemma 27B │ MedGemma 4B │ MedSigLIP │       │
│  ClinicalBERT │ Claude API │ LM Studio (Local/HIPAA)               │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  LAYER 7: DATA & INTEGRATION LAYER                                 │
│  PostgreSQL │ Neo4j │ Qdrant │ Orthanc │ FHIR │ RxNorm │ PubMed   │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  LAYER 8: A2UI CANVAS — Agent-Driven Visual Workspace              │
│  surfaceUpdate → beginRendering → dataModelUpdate │ JSONL Protocol  │
│  [Triage Dashboard] [Radiology Report] [Drug Alert] [Vitals] [SOAP]│
└─────────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────────┐
│  LAYER 9: INFRASTRUCTURE                                           │
│  Kubernetes │ Docker │ ArgoCD │ Azure │ Traefik │ OAuth2-Proxy     │
│  HIPAA Encryption │ Audit Logging                                   │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 Architecture Layer Breakdown

| Layer | Components | Responsibility |
|-------|-----------|----------------|
| 1. Input Channels | WhatsApp, Slack/Teams, WebChat, Mobile, CLI, DICOM, FHIR, IoT | Accept requests from doctors, nurses, patients, devices |
| 2. Gateway | OpenClaw Gateway (`ws://127.0.0.1:18789`) | Auth, routing, rate limiting, HIPAA audit logging |
| 3. Coordinator | Coordinator Agent | Route to specialist, consensus on complex cases, safety checks |
| 4. Specialist Agents | Triage, Radiology, Diagnostic, Pharmacy, Monitoring, Docs, Research | Domain-specific clinical tasks with SKILL.md files |
| 5. SKILL.md Registry | `~/.openclaw/workspace/skills/` | Triggers, processes, safety rules, A2UI output formats |
| 6. AI Models | MedImageInsight, MedGemma, MedSigLIP, ClinicalBERT, Claude, LM Studio | Imaging, reasoning, NER, HIPAA-safe local inference |
| 7. Data Layer | PostgreSQL, Neo4j, Qdrant, Orthanc, FHIR, RxNorm, PubMed, DrugBank | Records, knowledge graphs, vectors, images, drugs, literature |
| 8. A2UI Canvas | JSONL protocol (surfaceUpdate, beginRendering, dataModelUpdate) | Rich medical dashboards and interactive reports |
| 9. Infrastructure | Kubernetes, Docker, ArgoCD, Azure, Traefik, OAuth2-Proxy | Deployment, scaling, CI/CD, security, compliance |

### 2.3 Data Flow Sequence

**Example:** Doctor sends chest X-ray via WhatsApp for analysis.

```
Step 1: INPUT     Doctor sends "Analyze this chest X-ray" + image via WhatsApp
Step 2: GATEWAY   OpenClaw authenticates, logs, routes to agent system
Step 3: COORD     Coordinator identifies imaging task → Radiology Agent
Step 4: SKILL     Radiology Agent loads radiology/SKILL.md → xray_analysis
Step 5: MODELS    MedSigLIP (triage) → MedImageInsight (classify + embed)
                  → Qdrant KNN search (evidence) → MedGemma 4B (report)
Step 6: SAFETY    Coordinator checks: confidence > 0.7? Findings flagged?
Step 7: A2UI      Push radiology report to Canvas (surfaceUpdate + beginRendering)
Step 8: HUMAN     Doctor reviews: Approve | Flag for Review | Reassign
Step 9: AUDIT     Log: request, models, confidence, clinician action, timestamp
```

### 2.4 Multi-Agent Communication Patterns

**Pattern A: Sequential (Simple Cases)**

```
User → Gateway → Coordinator → Single Agent → A2UI
Example: "Side effects of metformin?" → Pharmacy Agent only
```

**Pattern B: Parallel Consensus (Complex Cases)**

```
User → Gateway → Coordinator → [Fan-out to multiple agents]
                                    ├→ Radiology Agent (image)
                                    ├→ Diagnostic Agent (differential)
                                    └→ Research Agent (guidelines)
                              ← Coordinator builds consensus → A2UI combined report
```

If agents disagree, the Coordinator presents both findings with confidence scores and flags for human review rather than making a unilateral decision.

---

## 3. Agent Interface Design (A2UI)

All agent interfaces follow a **medical-grade design system** with color-coded severity, clear data hierarchy, mandatory safety disclaimers, and human-in-the-loop action buttons.

### 3.1 Design System

| Element | Specification | Usage |
|---------|--------------|-------|
| ESI-1 / Critical | `#EF4444` (Red) | Resuscitation, critical drug interactions |
| ESI-2 / Emergency | `#F97316` (Orange) | Emergency, major interactions |
| ESI-3 / Urgent | `#EAB308` (Yellow) | Urgent cases, moderate warnings |
| ESI-4 / Semi-urgent | `#22C55E` (Green) | Semi-urgent, normal findings |
| ESI-5 / Non-urgent | `#3B82F6` (Blue) | Non-urgent, informational |
| Headers | `usageHint: h1, h2, h3` | Titles, section headers |
| Body text | `usageHint: body` | Findings, descriptions |
| Labels | `usageHint: caption` | Confidence, metadata, timestamps |
| Action: Approve | Button (green) | Clinician approves AI output |
| Action: Flag | Button (orange) | Flag for senior review |
| Action: Escalate | Button (red) | Escalate to human immediately |
| Disclaimer | Text (caption) | Always: "AI-assisted — requires clinician verification" |

### 3.2 Triage Dashboard

Primary interface for emergency department staff. Real-time patient queue sorted by ESI priority.

**Layout Specification:**

| Section | A2UI Components | Content |
|---------|----------------|---------|
| Header Bar | `Row > Text(h1) + Button(refresh)` | Title: Emergency Triage Dashboard |
| ESI Summary | `Row > 5x Card > [Text(count), Text(label)]` | ESI-1 through ESI-5 counts with color coding |
| Patient Queue | `List > Card items` | Each: ESI badge, name, complaint, wait time, View button |
| Detail Panel | `Card (expandable)` | Full: vitals, symptoms, red flags, routing recommendation |
| Disclaimer | `Text (caption, red)` | "AI-assisted triage — requires clinician verification" |

> See `02-A2UI-Templates.md` for the complete JSONL template.

### 3.3 Radiology Report Interface

Split-panel design: left shows patient info and findings with confidence bars, right shows KNN evidence and actions.

**Layout Specification:**

| Section | A2UI Components | Content |
|---------|----------------|---------|
| Left: Patient Info | `Card > [Text(h2), Text(body), Text(caption)]` | Name, modality, model used |
| Left: Findings | `Card > List > [Row > dot + text + confidence%]` | Each finding with severity indicator and confidence badge |
| Left: Classification | `Card > Table` | Zero-shot labels with AUC scores |
| Right: Evidence | `Card > [Text(h3), List of cases]` | KNN similar cases from MedImageInsight vectors |
| Right: Recommendation | `Card (green)` | MedGemma-generated clinical recommendation |
| Right: Actions | `Row > 3x Button` | Approve (green), Flag (orange), Reassign (gray) |
| Bottom: Disclaimer | `Text (caption)` | "AI-assisted — requires radiologist review" |

### 3.4 Drug Alert Interface

Color-coded alert cards. Critical interactions block workflow until physician override.

| Severity | Color | Behavior |
|----------|-------|----------|
| Critical | `#EF4444` Red | **BLOCKS** workflow. Requires physician override with documented reason. |
| Major | `#F97316` Orange | Warning. Suggests review before proceeding. |
| Moderate | `#EAB308` Yellow | Informational. Monitoring recommended. |
| Minor | `#22C55E` Green | No action needed. Logged for audit. |

**Layout:** Drug pair display (Drug A ↔ Drug B), severity badge, interaction description, evidence source, three action buttons (Override / Suggest Alternative / Cancel Prescription).

### 3.5 Vitals Monitor Interface

Real-time patient vitals with 6-card grid (HR, BP, SpO2, Temp, RR, MEWS), trend chart, and conditional alert banner when MEWS > 3.

**Dynamic Update Pattern:**

```jsonl
// Initial render
{"surfaceUpdate":{"surfaceId":"vitals","components":[...]}}
{"beginRendering":{"surfaceId":"vitals","root":"root"}}

// Every 30 seconds: push new readings
{"dataModelUpdate":{"surfaceId":"vitals","updates":{
  "hr":"92","bp":"138/88","spo2":"96","temp":"37.4",
  "rr":"20","mews":"3","alert_visible":"true",
  "alert_text":"MEWS elevated (3). Consider clinical review."
}}}
```

### 3.6 Clinical Documentation (SOAP Notes)

| Section | Source | A2UI Component |
|---------|--------|---------------|
| S — Subjective | Chat transcript (ClinicalBERT NER) | TextField (editable) with pre-filled text |
| O — Objective | Monitoring + Radiology + FHIR | TextField (editable) with pre-filled vitals/results |
| A — Assessment | Diagnostic Agent output | TextField (editable) with differential dx |
| P — Plan | Pharmacy + Research agents | TextField (editable) with treatment plan |
| ICD-10 Codes | Auto-generated from Assessment | List of suggested codes with descriptions |
| Actions | Clinician | Finalize \| Save Draft \| Export to EHR |

### 3.7 Agent Chat Interface

Three-panel layout for interacting with any individual agent:

| Panel | Width | Content |
|-------|-------|---------|
| Sidebar | 220px | Agent icon, name, SKILL.md status, skill buttons, queue/status metadata |
| Chat Area | flex | Scrollable messages: system (gray), assistant (dark + agent color), user (right-aligned) |
| Input Bar | bottom | Text input + Send button in agent accent color. Enter to send. |

**Agent Control Center Dashboard:** 4-column grid of 8 agent cards. Each shows icon, name, status dot (green=active, gray=idle), skill tags, queue count. Click opens Agent Chat with SKILL.md loaded.

> See `medassist-agent-interface.jsx` for the interactive React mockup.

---

## 4. Agent Specifications

| Agent | Models | Skills | A2UI Screen |
|-------|--------|--------|-------------|
| **Triage** | ClinicalBERT + Claude | esi_scoring, red_flag_detection, patient_routing, emergency_alert | Triage Dashboard |
| **Radiology** | MedImageInsight + MedGemma 4B | xray_analysis, mri_interpretation, ct_review, report_gen, evidence_search | Radiology Report |
| **Diagnostic** | MedGemma 27B + Claude | differential_dx, test_recommendation, pattern_recognition, rare_disease | Diagnosis Panel |
| **Pharmacy** | Claude + RxNorm + DrugBank | drug_interaction, dosage_calc, contraindication, med_reconciliation | Drug Alert |
| **Monitoring** | Time-series ML + Claude | vital_tracking, mews_score, anomaly_detection, alert_gen | Vitals Monitor |
| **Documentation** | Claude API | soap_notes, discharge_summary, icd10_coding, referral_letter | SOAP Editor |
| **Research** | Claude + PubMed API | guideline_search, evidence_synthesis, trial_match, literature_review | Evidence Panel |
| **Coordinator** | Claude API | agent_routing, consensus, safety_check, escalation | Control Center |

---

## 5. SKILL.md Definitions

> See `03-SKILL-Files.md` for complete SKILL.md definitions.

### SKILL.md File Structure

| Section | Purpose |
|---------|---------|
| `# Skill Name` | Title of the skill capability |
| `## When to Use` | Trigger keywords and contexts for activation |
| `## Process` | Step-by-step execution logic (numbered) |
| `## Models Used` | Which AI models this skill depends on |
| `## A2UI Output Format` | A2UI template for rendering results |
| `## Safety Rules` | Non-negotiable constraints (escalation, disclaimers) |
| `## Example` | Sample input/output pair to guide the agent |

---

## 6. Technology Stack

| Layer | Technology | Notes |
|-------|-----------|-------|
| Agent Platform | **OpenClaw** | `npm install -g openclaw@latest` |
| Agentic UI | **A2UI v0.8** | Built into OpenClaw Canvas |
| LLM (Cloud) | **Claude API** | claude-sonnet-4-20250514 |
| LLM (Local) | **LM Studio** | HIPAA-safe PHI processing |
| Imaging | **MedImageInsight** 0.61B | HuggingFace: `lion-ai/MedImageInsights` |
| Clinical Reasoning | **MedGemma 27B** | Google (complex cases) |
| Radiology Reports | **MedGemma 4B** | Google (lightweight, single GPU) |
| Fast Triage | **MedSigLIP** 400M | Google (image routing) |
| Medical NER | **ClinicalBERT** 110M | Symptom extraction |
| Backend | **Python + FastAPI** | Model inference + skill execution |
| Database | **PostgreSQL** | Existing infrastructure |
| Knowledge Graph | **Neo4j** | SNOMED-CT + ICD-10/11 |
| Vectors | **Qdrant** | Image embeddings for KNN |
| DICOM | **Orthanc** | Medical image storage |
| EHR | **FHIR R4 APIs** | Epic/Cerner compatible |
| Drugs | **RxNorm + DrugBank** | Interactions + dosing |
| Deployment | **Kubernetes + Docker + ArgoCD** | Existing K8s + GitOps |
| Auth | **OAuth2-Proxy + Azure AD** | Existing setup |
| Encryption | **AES-256 + TLS 1.3** | HIPAA compliance |

---

## 7. Implementation Roadmap

### Phase 1: Foundation (Weeks 1–4)

- OpenClaw + Claude API on Kubernetes
- Triage + Radiology SKILL.md files
- MedImageInsight deployment (HuggingFace)
- A2UI templates: triage dashboard + radiology report
- FastAPI backend + Qdrant vector DB
- Docker + ArgoCD pipeline

### Phase 2: Core Agents (Weeks 5–8)

- Pharmacy Agent (RxNorm + DrugBank)
- Documentation Agent (SOAP notes)
- MedGemma 4B for report generation
- Orthanc DICOM server
- Drug alert + vitals A2UI interfaces
- Human-in-the-loop approval workflows

### Phase 3: Advanced (Weeks 9–12)

- Monitoring Agent + real-time vitals
- FHIR integration for EHR
- MedGemma 27B for complex diagnostics
- Research Agent (PubMed + trials)
- Coordinator Agent (consensus)
- Neo4j knowledge graph

### Phase 4: Production (Weeks 13–16)

- HIPAA encryption + audit trails
- LM Studio for PHI-safe local inference
- Clinical scenario testing
- EHR sandbox integration testing
- Clinical staff UAT
- Production deployment + monitoring

---

## 8. Safety & Compliance

> **⚠️ CRITICAL: This is a clinical decision SUPPORT system. ALL outputs require clinician verification. The system assists — it never decides.**

| Requirement | Implementation |
|------------|----------------|
| **Human-in-the-Loop** | Every output has Approve/Flag/Escalate buttons. No auto-clinical actions. |
| **Disclaimer** | All responses include: "AI-assisted — requires clinician verification" |
| **Fail-Safe** | ESI 1-2 auto-alert attending. Confidence < 0.7 = mandatory human review. |
| **Audit Trail** | PostgreSQL log: request, agent, model, confidence, action, timestamp |
| **PHI Protection** | No PHI to cloud LLMs. PHI tasks routed to LM Studio (local, encrypted). |
| **HIPAA** | AES-256 at rest, TLS 1.3 in transit, BAA signed |
| **Bias Monitoring** | MedImageInsight fairness metrics. Quarterly evaluation across age/gender. |
| **Regulatory** | Decision support only. Not for clinical diagnosis without FDA clearance. |

---

*MedAssist AI v2.0 — Complete Architecture & Interface Design Guide*
